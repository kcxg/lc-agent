"""把 agent 运行从 HTTP 请求生命周期里解耦出来。

问题：过去 SSE 生成器**就是**那一轮的运行本体——它由请求任务迭代，客户端一断开
（刷新页面 / 关标签 / 换网络），ASGI 就取消请求任务，连带把这一轮连同工具调用一起拆掉。
实测后果：刷新后这一轮的界面立刻变成"没在跑"，而底下的命令其实还在跑，结果却再没人接收。

方案：每一轮运行都由一个**独立的后台任务**（`RunSession.task`）驱动，它只依赖
"取消标记 / 自己跑完"，与连接无关；SSE 请求退化成**订阅者**，从队列转发事件。
断开只是退订（该队列不再被读取，事件直接丢弃），运行照旧。

本模块只负责"运行的生命周期 + 事件投递"，不掺业务；取消与收尾仍由 sse 侧的
生产者协程自己处理（它本来就是一段完整的 take-care-of-myself 代码）。
"""
import asyncio
import logging
import time
from typing import AsyncIterator, Callable

logger = logging.getLogger(__name__)

# 运行结束后注册表里保留多久：给"刚跑完就查状态 / 刚要订阅"的请求一个缓冲窗口
RUN_TTL_SECONDS = 120.0

# 收到停止请求后，先给生产者多久"优雅收尾"（它会在下一个事件边界自行停下）；
# 超时还没停就取消任务——工具调用可能几分钟不产生事件，不能干等。
CANCEL_GRACE_SECONDS = 0.5

_sessions: dict[str, "RunSession"] = {}
_background_tasks: set[asyncio.Task] = set()


def _spawn(coro) -> asyncio.Task:
    """起一个后台任务并持引用，避免被 GC 回收。"""
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


class RunSession:
    """一条线程上正在进行（或刚结束）的一轮运行。"""

    def __init__(self, thread_id: str) -> None:
        self.thread_id = thread_id
        self.started_at = time.time()
        self.finished_at: float | None = None
        self.done = False
        self.task: asyncio.Task | None = None
        self._queue: asyncio.Queue[str | None] | None = None

    # --- 运行方 ---

    def start(self, producer: AsyncIterator[str]) -> None:
        """把生产者协程放到后台任务里跑；yield 出来的每个事件文本推给订阅者。"""
        self.task = _spawn(self._drain(producer))

    async def _drain(self, producer: AsyncIterator[str]) -> None:
        try:
            async for chunk in producer:
                self.push(chunk)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Run session crashed for thread %s", self.thread_id)
        finally:
            self.mark_finished()

    def mark_finished(self) -> None:
        """收尾：标记结束、收流、安排注册表清理。

        准备阶段就失败（还没真正起跑）时也用它，好让注册表不再拦住下一轮。
        """
        self.done = True
        self.finished_at = time.time()
        self.push(None)  # 结束哨兵：订阅者据此收流
        _schedule_cleanup(self.thread_id, self)

    def push(self, chunk: str | None) -> None:
        """推一个事件给当前订阅者；没有订阅者就直接丢弃（刷新后不留无界缓冲）。"""
        queue = self._queue
        if queue is None:
            return
        try:
            queue.put_nowait(chunk)
        except Exception:
            logger.exception("Failed to push event for thread %s", self.thread_id)

    # --- 订阅方 ---

    def attach(self) -> asyncio.Queue[str | None]:
        """注册订阅队列。必须在 start() 之前调用，否则开头几个事件会丢。"""
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._queue = queue
        return queue

    async def subscribe(self, queue: asyncio.Queue[str | None]) -> AsyncIterator[str]:
        """把事件转发给 SSE 响应；客户端断开时本生成器被关闭，仅退订。"""
        try:
            while True:
                chunk = await queue.get()
                if chunk is None:
                    return
                yield chunk
        finally:
            if self._queue is queue:
                self._queue = None

    def is_running(self) -> bool:
        return not self.done

    # --- 停止 ---

    def request_cancel(self) -> None:
        """请求停止本轮运行。

        调用方（/runs/cancel）会先置取消标记，生产者在下一个事件边界优雅收尾；
        但工具调用可能几分钟都不产生事件，所以这里加个兜底：宽限期一过仍未停
        就取消任务。生产者的 finally 会把已产生的部分落库（含账单）。
        """
        _spawn(self._cancel_watchdog())

    async def _cancel_watchdog(self) -> None:
        try:
            await asyncio.sleep(CANCEL_GRACE_SECONDS)
        except asyncio.CancelledError:
            return
        if self.done or self.task is None or self.task.done():
            return
        logger.info("Cancelling stalled run for thread %s", self.thread_id)
        self.task.cancel()


# --- 注册表 ---


def get_active(thread_id: str) -> RunSession | None:
    return _sessions.get(thread_id)


def is_running(thread_id: str) -> bool:
    session = _sessions.get(thread_id)
    return bool(session is not None and session.is_running())


def try_register(thread_id: str) -> RunSession | None:
    """登记一轮新运行；该线程已有活跃运行时返回 None（调用方据此回 409）。"""
    existing = _sessions.get(thread_id)
    if existing is not None and existing.is_running():
        return None
    session = RunSession(thread_id)
    _sessions[thread_id] = session
    return session


def _schedule_cleanup(thread_id: str, session: RunSession) -> None:
    async def _cleanup() -> None:
        try:
            await asyncio.sleep(RUN_TTL_SECONDS)
        except asyncio.CancelledError:
            return
        # 只清自己：这期间可能已经登记了更新的一轮
        if _sessions.get(thread_id) is session and session.done:
            _sessions.pop(thread_id, None)

    _spawn(_cleanup())


async def shutdown_all() -> None:
    """进程退出前停掉后台运行（让生产者的收尾逻辑有机会落库）。"""
    tasks = [t for t in _background_tasks if not t.done()]
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
