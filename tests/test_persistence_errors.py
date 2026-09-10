import pytest

from lc_agent.server import persistence


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("func", "args"),
    [
        (persistence.ensure_session, ("thread1", "title", "agent", "model", "user")),
        (persistence.increment_session_message_count, ("thread1",)),
        (persistence.save_title, ("thread1", "title")),
        (persistence.save_ui_message, ("thread1", "assistant", [{"type": "text", "text": "content"}])),
        (persistence.truncate_from_message, ("thread1", "message1")),
        (persistence.append_to_last_assistant_message, ("thread1", "content")),
        (persistence.create_subsession, ("sub1", "parent1", "tool1", "agent", "title", "user")),
    ],
)
async def test_core_persistence_write_errors_are_logged_and_reraised(monkeypatch, caplog, func, args):
    from lc_agent.db import engine as db_engine

    error = RuntimeError("db unavailable")

    def fail_get_business_async_session():
        raise error

    monkeypatch.setattr(db_engine, "get_business_async_session", fail_get_business_async_session)

    with pytest.raises(RuntimeError, match="db unavailable"):
        await func(*args)

    assert any(record.levelname == "ERROR" for record in caplog.records)


@pytest.mark.asyncio
async def test_finalize_subsession_message_propagates_save_failure(monkeypatch, caplog):
    error = RuntimeError("save failed")

    async def fail_save_ui_message(*args, **kwargs):
        raise error

    monkeypatch.setattr(persistence, "save_ui_message", fail_save_ui_message)

    with pytest.raises(RuntimeError, match="save failed"):
        await persistence.finalize_subsession_message("sub1", "content")

    assert not caplog.records
