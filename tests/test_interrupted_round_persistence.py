"""早退轮次（取消 / 前端断开 / 异常）收尾落库的行为契约。

背景：正常结束路径会写 assistant UI 消息；早退路径过去直接 return，导致这一轮
的 usage 与工具调用在 chat_ui_messages 里永久缺失，右侧概览与刷新后的历史都看不到。
"""
import pytest

from lc_agent.server import persistence


@pytest.mark.asyncio
async def test_interrupted_round_writes_message_and_increments(monkeypatch):
    seen: dict = {}

    async def fake_save_ui_message(thread_id, role, content, **kwargs):
        seen["call"] = (thread_id, role, content, kwargs)

    async def fake_increment(thread_id):
        seen["incremented"] = thread_id

    monkeypatch.setattr(persistence, "save_ui_message", fake_save_ui_message)
    monkeypatch.setattr(persistence, "increment_session_message_count", fake_increment)

    await persistence.persist_interrupted_round(
        "t1",
        content_parts=["已经产出的正文"],
        tool_calls=[{"name": "read_file", "status": "done"}],
        usage_rounds=[{"input_tokens": 10, "output_tokens": 2}],
        elapsed_ms=1234,
    )

    thread_id, role, content, kwargs = seen["call"]
    assert (thread_id, role) == ("t1", "assistant")
    assert content == [{"type": "text", "text": "已经产出的正文"}]
    assert kwargs["tool_calls"] == [{"name": "read_file", "status": "done"}]
    assert kwargs["usage"] == {
        "rounds": [{"input_tokens": 10, "output_tokens": 2}],
        "tool_call_count": 1,
        "total_duration_ms": 1234,
    }
    assert seen["incremented"] == "t1"


@pytest.mark.asyncio
async def test_interrupted_round_skips_when_nothing_produced(monkeypatch):
    """一个字、一个工具都没产生时不应该写出一条空消息。"""

    async def fail_save(*args, **kwargs):
        raise AssertionError("不该写入 UI 消息")

    async def fail_increment(*args, **kwargs):
        raise AssertionError("不该递增消息数")

    monkeypatch.setattr(persistence, "save_ui_message", fail_save)
    monkeypatch.setattr(persistence, "increment_session_message_count", fail_increment)

    await persistence.persist_interrupted_round(
        "t1", content_parts=[], tool_calls=[], usage_rounds=[], elapsed_ms=10,
    )


@pytest.mark.asyncio
async def test_interrupted_round_swallows_write_failure(monkeypatch, caplog):
    """落库失败不能打断取消/异常收尾——调用方随后还要给前端发终止事件。"""

    async def fail_save(*args, **kwargs):
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(persistence, "save_ui_message", fail_save)

    await persistence.persist_interrupted_round(
        "t1", content_parts=["x"], tool_calls=[], usage_rounds=[], elapsed_ms=1,
    )

    assert any(record.levelname == "ERROR" for record in caplog.records)


@pytest.mark.asyncio
async def test_interrupted_round_marks_unfinished_tools_as_interrupted(monkeypatch):
    """没跑完的工具在快照里会永远显示"执行中"，落库前必须标成 interrupted。"""
    seen: dict = {}

    async def fake_save_ui_message(thread_id, role, content, **kwargs):
        seen["tool_calls"] = kwargs["tool_calls"]

    async def fake_increment(thread_id):
        pass

    monkeypatch.setattr(persistence, "save_ui_message", fake_save_ui_message)
    monkeypatch.setattr(persistence, "increment_session_message_count", fake_increment)

    tool_calls = [
        {"name": "a", "status": "done"},
        {"name": "b", "status": "running"},
        {"name": "c"},  # 缺 status 同样视为未完成
    ]
    await persistence.persist_interrupted_round(
        "t1", content_parts=["x"], tool_calls=tool_calls, usage_rounds=[], elapsed_ms=1,
    )

    assert [t["status"] for t in seen["tool_calls"]] == ["done", "interrupted", "interrupted"]
    # 不能就地改写调用方的列表
    assert tool_calls[1]["status"] == "running"
    assert "status" not in tool_calls[2]


@pytest.mark.asyncio
async def test_interrupted_resume_round_marks_unfinished_tools_as_interrupted(monkeypatch):
    seen: dict = {}

    async def fake_append(thread_id, new_content, **kwargs):
        seen["tool_calls"] = kwargs["all_tool_calls"]

    monkeypatch.setattr(persistence, "append_to_last_assistant_message", fake_append)

    await persistence.persist_interrupted_resume_round(
        "t1",
        content_parts=["x"],
        tool_calls=[{"name": "b", "status": "running"}],
        usage_rounds=[],
        elapsed_ms=1,
    )

    assert [t["status"] for t in seen["tool_calls"]] == ["interrupted"]


@pytest.mark.asyncio
async def test_interrupted_resume_round_appends_instead_of_creating(monkeypatch):
    """resume 整轮共用同一条 assistant 消息：早退必须追加，不能新建。

    否则续跑被取消/出错会多出一条重复的 assistant 气泡，且消息数被多算。
    """
    calls = {"append": 0, "save": 0, "increment": 0, "appended": None}

    async def spy_save(*args, **kwargs):
        calls["save"] += 1

    async def fake_append(thread_id, new_content, **kwargs):
        calls["append"] += 1
        calls["appended"] = (thread_id, new_content, kwargs)

    async def spy_increment(*args, **kwargs):
        calls["increment"] += 1

    monkeypatch.setattr(persistence, "save_ui_message", spy_save)
    monkeypatch.setattr(persistence, "append_to_last_assistant_message", fake_append)
    monkeypatch.setattr(persistence, "increment_session_message_count", spy_increment)

    await persistence.persist_interrupted_resume_round(
        "t1",
        content_parts=["续跑产出"],
        tool_calls=[{"name": "a"}],
        usage_rounds=[{"input_tokens": 5}],
        elapsed_ms=999,
    )

    assert calls["append"] == 1
    assert calls["save"] == 0
    assert calls["increment"] == 0
    thread_id, new_content, kwargs = calls["appended"]
    assert (thread_id, new_content) == ("t1", "续跑产出")
    assert kwargs["usage_rounds"] == [{"input_tokens": 5}]
    assert kwargs["resume_duration_ms"] == 999
