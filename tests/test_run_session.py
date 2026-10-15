"""运行会话：把 agent 运行从 HTTP 请求生命周期里解耦。

核心契约（这条不成立，"刷新不结束后端运行"就是空话）：
订阅者（SSE 请求）退订之后，运行必须继续跑完。
"""
import asyncio

import pytest

from lc_agent.server import run_session, sse


@pytest.fixture(autouse=True)
def _clean_registry():
    yield
    run_session._sessions.clear()


def _producer(events: list[str], produced: list[str]):
    async def _gen():
        for evt in events:
            produced.append(evt)
            await asyncio.sleep(0)
            yield evt

    return _gen()


@pytest.mark.asyncio
async def test_subscriber_receives_events_then_ends_on_sentinel():
    session = run_session.try_register("t-events")
    assert session is not None
    queue = session.attach()
    session.start(_producer(["a", "b"], []))

    received = [chunk async for chunk in session.subscribe(queue)]

    assert received == ["a", "b"]
    assert session.done is True


@pytest.mark.asyncio
async def test_run_continues_after_subscriber_detaches():
    """刷新 = 响应生成器被关闭 = 退订；运行必须照旧跑完并落定。"""
    produced: list[str] = []
    session = run_session.try_register("t-detach")
    assert session is not None
    queue = session.attach()
    session.start(_producer(["e0", "e1", "e2", "e3"], produced))

    subscription = session.subscribe(queue)
    assert await subscription.__anext__() == "e0"
    await subscription.aclose()  # 模拟客户端断开
    assert session._queue is None  # 已退订

    await asyncio.sleep(0.05)
    assert produced == ["e0", "e1", "e2", "e3"]  # 生产者没有被一起取消
    assert session.done is True
    # 跑完了：注册表里还在（TTL 窗口内），但不再算"正在运行"
    assert run_session.get_active("t-detach") is session
    assert run_session.is_running("t-detach") is False


@pytest.mark.asyncio
async def test_events_dropped_when_no_subscriber():
    """没有订阅者时事件直接丢弃：刷新后不会留无界缓冲。"""
    session = run_session.try_register("t-drop")
    session.push("lost-1")
    session.push("lost-2")

    queue = session.attach()
    session.push("kept")
    assert await queue.get() == "kept"


@pytest.mark.asyncio
async def test_try_register_rejects_while_another_run_is_active():
    first = run_session.try_register("t-busy")
    assert first is not None
    # 还没结束：不能再起一轮
    assert run_session.try_register("t-busy") is None
    assert run_session.is_running("t-busy") is True

    first.done = True
    second = run_session.try_register("t-busy")
    assert second is not None and second is not first


@pytest.mark.asyncio
async def test_registry_entry_expires_after_ttl(monkeypatch):
    monkeypatch.setattr(run_session, "RUN_TTL_SECONDS", 0.05)
    session = run_session.try_register("t-ttl")
    session.start(_producer([], []))

    await asyncio.sleep(0.2)
    assert run_session.get_active("t-ttl") is None
    assert run_session.is_running("t-ttl") is False


@pytest.mark.asyncio
async def test_cleanup_does_not_drop_a_newer_run(monkeypatch):
    """清理只能清自己：TTL 到期前若已登记更新的一轮，不能把新的删掉。"""
    monkeypatch.setattr(run_session, "RUN_TTL_SECONDS", 0.05)
    old = run_session.try_register("t-newer")
    old.start(_producer([], []))
    await asyncio.sleep(0.02)

    new = run_session.try_register("t-newer")
    assert new is not None and new is not old
    await asyncio.sleep(0.2)
    assert run_session.get_active("t-newer") is new


def test_run_in_progress_response_is_409():
    response = sse._run_in_progress_response("t-409")
    assert response.status_code == 409
    assert b"run_in_progress" in response.body


@pytest.mark.asyncio
async def test_request_cancel_stops_a_stalled_run(monkeypatch):
    """长工具期间没有事件，光靠取消标记要干等到工具结束 —— 宽限期后必须硬取消。"""
    monkeypatch.setattr(run_session, "CANCEL_GRACE_SECONDS", 0.05)
    stalled = asyncio.Event()

    async def producer():
        stalled.set()
        await asyncio.sleep(30)  # 模拟长命令：长时间不产生事件
        yield "never"

    session = run_session.try_register("t-cancel")
    session.start(producer())
    await stalled.wait()

    session.request_cancel()
    await asyncio.sleep(0.2)

    assert session.done is True
    assert run_session.is_running("t-cancel") is False


@pytest.mark.asyncio
async def test_request_cancel_is_noop_for_finished_run(monkeypatch):
    monkeypatch.setattr(run_session, "CANCEL_GRACE_SECONDS", 0.05)
    session = run_session.try_register("t-cancel-done")
    session.start(_producer([], []))
    await asyncio.sleep(0.05)
    assert session.done is True

    session.request_cancel()  # 已结束：不能抛错、不能把状态弄回"运行中"
    await asyncio.sleep(0.1)
    assert session.done is True
    assert run_session.is_running("t-cancel-done") is False
