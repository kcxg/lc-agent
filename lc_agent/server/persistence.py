"""Database persistence operations for chat sessions and messages.

All functions accept db_url as the first argument and are self-contained —
no dependency on the WebSocket handler class.
"""
import logging
from typing import Any


logger = logging.getLogger(__name__)


async def get_session_message_count(db_url: str, thread_id: str) -> int:
    """Get the current message count for a session. Returns 0 if not found."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import SessionRepository

        session = get_async_session(db_url)
        try:
            repo = SessionRepository(session)
            existing = await repo.get_by_id(thread_id)
            if existing is None:
                return 0
            return existing.message_count or 0
        finally:
            await session.close()
    except Exception:
        return 0


async def ensure_session(
    db_url: str,
    thread_id: str,
    title: str,
    agent_id: str,
    model: str,
    user_id: str = "",
) -> None:
    """Create session metadata if not exists, or update if exists."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import SessionRepository

        session = get_async_session(db_url)
        try:
            repo = SessionRepository(session)
            existing = await repo.get_by_id(thread_id)
            if existing is None:
                await repo.create(
                    id=thread_id,
                    title=title or "新对话",
                    agent_id=agent_id,
                    model=model,
                    message_count=0,
                    user_id=user_id,
                )
            else:
                await repo.update(
                    thread_id,
                    title=title or existing.title,
                    agent_id=agent_id,
                    model=model or existing.model,
                )
        finally:
            await session.close()
    except Exception:
        logger.exception("Failed to ensure session %s", thread_id)
        raise


async def increment_session_message_count(db_url: str, thread_id: str) -> None:
    """Increment persisted session message count after a completed round."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import SessionRepository

        session = get_async_session(db_url)
        try:
            await SessionRepository(session).increment_messages(thread_id)
        finally:
            await session.close()
    except Exception:
        logger.exception("Failed to increment message count for session %s", thread_id)
        raise


async def save_title(db_url: str, thread_id: str, title: str) -> None:
    """Save title to DB."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import SessionRepository

        session = get_async_session(db_url)
        try:
            await SessionRepository(session).update(thread_id, title=title)
        finally:
            await session.close()
    except Exception:
        logger.exception("Failed to save title for session %s", thread_id)
        raise


async def generate_title(
    engine: Any,
    thread_id: str,
    first_message: str,
    preset_id: str = "chat",
    selected_model_id: str = "",
) -> str | None:
    """Generate title from first message using the agent's model.

    Returns the generated title string, or None on failure.
    """
    try:
        model_id = selected_model_id
        if preset_id in engine.BUILTIN_IDS:
            for bp in engine.get_builtin_presets():
                if bp.id == preset_id:
                    model_id = model_id or bp.default_model
                    break
        else:
            preset = engine._presets.get(preset_id) or engine._custom_presets.get(preset_id)
            if preset:
                model_id = model_id or preset.default_model
        return await engine.generate_title(first_message, model_id)
    except Exception:
        logger.exception("Title generation failed for session %s", thread_id)
        return None


async def save_ui_message(
    db_url: str,
    thread_id: str,
    role: str,
    content: list[dict[str, Any]],
    *,
    tool_calls: list[dict[str, Any]] | None = None,
    usage: dict[str, Any] | None = None,
    http_traces: list[dict[str, Any]] | None = None,
) -> None:
    """Persist replay data for the web chat history."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import ChatUiMessageRepository

        session = get_async_session(db_url)
        try:
            repo = ChatUiMessageRepository(session)
            await repo.create(
                session_id=thread_id,
                role=role,
                content=content,
                tool_calls=tool_calls,
                usage=usage,
                http_traces=http_traces,
            )
        finally:
            await session.close()
    except Exception:
        logger.exception("Failed to persist UI message for session %s", thread_id)
        raise


async def truncate_from_message(db_url: str, thread_id: str, message_id: str) -> None:
    """Delete persisted UI messages from the edited anchor onward."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import ChatUiMessageRepository

        session = get_async_session(db_url)
        try:
            repo = ChatUiMessageRepository(session)
            await repo.truncate_from_message(thread_id, message_id)
        finally:
            await session.close()
    except Exception:
        logger.exception("Failed to truncate UI messages for session %s", thread_id)
        raise


async def load_resume_context(db_url: str, thread_id: str) -> tuple[list[dict[str, Any]], int]:
    """Load tool_calls and http_traces count from the last assistant message for interrupt continuation."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import ChatUiMessageRepository

        session = get_async_session(db_url)
        try:
            repo = ChatUiMessageRepository(session)
            last_msg = await repo.get_last_assistant(thread_id)
            if last_msg is None:
                return [], 0
            return list(last_msg.tool_calls or []), len(last_msg.http_traces or [])
        finally:
            await session.close()
    except Exception:
        return [], 0


async def append_to_last_assistant_message(
    db_url: str,
    thread_id: str,
    content: str,
    *,
    all_tool_calls: list[dict[str, Any]] | None = None,
    usage_rounds: list[dict] | None = None,
    http_traces: list[dict[str, Any]] | None = None,
    resume_duration_ms: int = 0,
) -> None:
    """Update the last assistant message after interrupt resume.

    ``all_tool_calls`` replaces the entire tool_calls array (it already
    contains both pre-interrupt tools with updated statuses and new tools).
    """
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import ChatUiMessageRepository

        session = get_async_session(db_url)
        try:
            repo = ChatUiMessageRepository(session)
            last_msg = await repo.get_last_assistant(thread_id)
            if last_msg is None:
                return

            if content:
                existing = list(last_msg.content) if isinstance(last_msg.content, list) else []
                if existing and isinstance(existing[-1], dict) and existing[-1].get("type") == "text":
                    existing[-1] = {**existing[-1], "text": (existing[-1].get("text") or "") + content}
                else:
                    existing.append({"type": "text", "text": content})
                last_msg.content = existing
            if all_tool_calls is not None:
                last_msg.tool_calls = all_tool_calls
            if usage_rounds:
                old = last_msg.usage or {}
                last_msg.usage = {
                    **old,
                    "rounds": (old.get("rounds") or []) + usage_rounds,
                    "tool_call_count": len(all_tool_calls or []),
                    "total_duration_ms": (old.get("total_duration_ms") or 0) + resume_duration_ms,
                }
            if http_traces:
                last_msg.http_traces = (last_msg.http_traces or []) + list(http_traces)
            session.add(last_msg)
            await session.commit()
        finally:
            await session.close()
    except Exception:
        logger.exception("Failed to update last assistant message for session %s", thread_id)
        raise


async def create_subsession(
    db_url: str,
    sub_session_id: str,
    parent_session_id: str,
    tool_call_id: str,
    agent_id: str,
    title: str,
    user_id: str = "",
) -> None:
    """Create a sub-session record linked to its parent session."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.models import SessionMeta

        session = get_async_session(db_url)
        try:
            new_session = SessionMeta(
                id=sub_session_id,
                title=title,
                agent_id=agent_id,
                model="",
                user_id=user_id,
                message_count=0,
                parent_session_id=parent_session_id,
                tool_call_id=tool_call_id,
            )
            session.add(new_session)
            await session.commit()
        finally:
            await session.close()
    except Exception:
        logger.exception("Failed to create sub-session %s", sub_session_id)
        raise


async def save_subsession_delegation_message(
    db_url: str,
    sub_session_id: str,
    query: str,
) -> None:
    """Insert the synthetic delegation message as the first message in a sub-session."""
    await save_ui_message(
        db_url, sub_session_id, "system", [{"type": "text", "text": f"委托任务: {query}"}],
    )


async def finalize_subsession_message(
    db_url: str,
    sub_session_id: str,
    content: str,
    tool_calls: list[dict] | None = None,
    usage: dict | None = None,
    http_traces: list[dict] | None = None,
) -> None:
    """Save the sub-agent's assistant message and increment message count."""
    await save_ui_message(
        db_url, sub_session_id, "assistant", [{"type": "text", "text": content}],
        tool_calls=tool_calls,
        usage=usage,
        http_traces=http_traces,
    )
    await increment_session_message_count(db_url, sub_session_id)
