"""流被强行取消（浏览器刷新 / 任务取消）时的兜底收尾。

背景：这类情况下 ASGI 会直接取消 SSE 生成器，循环里的取消/异常分支根本不会执行
（CancelledError 继承 BaseException，except Exception 抓不到），
所以在 finally 里用 create_task 派一个"取消安全"的收尾任务。
"""
import asyncio
import time

import pytest

from lc_agent.server import persistence, sse


async def _drain_teardown_tasks(timeout: float = 2.0) -> None:
    deadline = time.time() + timeout
    while sse._teardown_tasks and time.time() < deadline:
        await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_teardown_records_usage_and_persists_after_cancellation(monkeypatch):
    calls: list[str] = []

    async def fake_record_usage(*args, **kwargs):
        calls.append("usage")

    async def fake_persist(thread_id, **kwargs):
        calls.append("persist")

    monkeypatch.setattr(sse, "record_usage", fake_record_usage)
    monkeypatch.setattr(persistence, "persist_interrupted_round", fake_persist)

    async def streaming():
        try:
            await asyncio.sleep(30)
        finally:
            # 模拟真实 finally：生成器在此刻正处于"被取消"状态
            sse._schedule_round_teardown(
                thread_id="t1",
                user_id="u1",
                preset_id="chat",
                usage_rounds=[{"input_tokens": 7}],
                usage_run_id="run1",
                content_parts=["已产生的正文"],
                tool_calls=[{"name": "read_file"}],
                stream_start_time=time.time(),
                append=False,
            )

    task = asyncio.create_task(streaming())
    await asyncio.sleep(0)          # 让它进入 sleep
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    await _drain_teardown_tasks()
    assert calls == ["usage", "persist"]


@pytest.mark.asyncio
async def test_teardown_append_mode_used_for_resume(monkeypatch):
    calls: list[str] = []

    async def fake_record_usage(*args, **kwargs):
        calls.append("usage")

    async def fake_persist_append(thread_id, **kwargs):
        calls.append("append")

    async def fail_persist_create(thread_id, **kwargs):
        calls.append("create")

    monkeypatch.setattr(sse, "record_usage", fake_record_usage)
    monkeypatch.setattr(persistence, "persist_interrupted_resume_round", fake_persist_append)
    monkeypatch.setattr(persistence, "persist_interrupted_round", fail_persist_create)

    sse._schedule_round_teardown(
        thread_id="t1",
        user_id="u1",
        preset_id="chat",
        usage_rounds=[{"input_tokens": 7}],
        usage_run_id="run1",
        content_parts=["续跑产出"],
        tool_calls=[],
        stream_start_time=time.time(),
        append=True,
    )

    await _drain_teardown_tasks()
    assert calls == ["usage", "append"]


@pytest.mark.asyncio
async def test_is_thread_running_reflects_run_registry():
    """/run-status 的依据：运行会话注册表里有没有活跃运行。"""
    from lc_agent.server import run_session

    session = run_session.try_register("t-lock")
    try:
        assert session is not None
        assert sse._is_thread_running("t-lock") is True
        session.done = True
        assert sse._is_thread_running("t-lock") is False
        assert sse._is_thread_running("no-such-thread") is False
    finally:
        run_session._sessions.pop("t-lock", None)


@pytest.mark.asyncio
async def test_teardown_survives_persist_failure(monkeypatch):
    """兜底收尾里任何一步失败都不能让另一个任务崩掉（后台任务异常会被吞掉）。"""

    async def fail_record_usage(*args, **kwargs):
        raise RuntimeError("billing down")

    async def fake_persist(thread_id, **kwargs):
        pass

    monkeypatch.setattr(sse, "record_usage", fail_record_usage)
    monkeypatch.setattr(persistence, "persist_interrupted_round", fake_persist)

    sse._schedule_round_teardown(
        thread_id="t1",
        user_id="u1",
        preset_id="chat",
        usage_rounds=[],
        usage_run_id="run1",
        content_parts=["x"],
        tool_calls=[],
        stream_start_time=time.time(),
        append=False,
    )

    await _drain_teardown_tasks()
    assert not sse._teardown_tasks
