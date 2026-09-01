from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from lc_agent.db.models import (
    AgentPresetDB,
    AgentPromptBindingDB,
    AutomationRun,
    AutomationTask,
    ChatUiMessage,
    FileChange,
    PromptTemplateDB,
    SessionMeta,
)


AUTOMATION_ACTIVE_STATUSES = ("pending", "running")


class PromptRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> list[PromptTemplateDB]:
        result = await self.session.execute(select(PromptTemplateDB).order_by(PromptTemplateDB.created_at))
        return list(result.scalars().all())

    async def get_by_id(self, prompt_id: str) -> PromptTemplateDB | None:
        return await self.session.get(PromptTemplateDB, prompt_id)

    async def create(self, name: str, content: str) -> PromptTemplateDB:
        pt = PromptTemplateDB(name=name, content=content)
        self.session.add(pt)
        await self.session.commit()
        await self.session.refresh(pt)
        return pt

    async def update(self, prompt_id: str, **kwargs) -> PromptTemplateDB | None:
        pt = await self.get_by_id(prompt_id)
        if pt is None:
            return None
        for key, value in kwargs.items():
            if hasattr(pt, key):
                setattr(pt, key, value)
        pt.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(pt)
        return pt

    async def delete(self, prompt_id: str) -> bool:
        pt = await self.get_by_id(prompt_id)
        if pt is None:
            return False
        await self.session.delete(pt)
        await self.session.commit()
        return True

    async def get_agent_ids_using_prompt(self, prompt_id: str) -> list[str]:
        result = await self.session.execute(
            select(AgentPromptBindingDB.agent_id).where(AgentPromptBindingDB.prompt_id == prompt_id)
        )
        return list(result.scalars().all())

    async def get_bindings_for_agent(self, agent_id: str) -> list[AgentPromptBindingDB]:
        result = await self.session.execute(
            select(AgentPromptBindingDB)
            .where(AgentPromptBindingDB.agent_id == agent_id)
            .order_by(AgentPromptBindingDB.sort_order)
        )
        return list(result.scalars().all())

    async def set_bindings_for_agent(self, agent_id: str, prompt_ids: list[str]) -> None:
        await self.session.execute(
            delete(AgentPromptBindingDB).where(AgentPromptBindingDB.agent_id == agent_id)
        )
        for order, pid in enumerate(prompt_ids):
            self.session.add(AgentPromptBindingDB(agent_id=agent_id, prompt_id=pid, sort_order=order))
        await self.session.commit()

    async def resolve_extra_prompts(self, agent_id: str) -> list[tuple[str, str]]:
        """Return ordered (name, content) pairs for prompts bound to this agent."""
        stmt = (
            select(PromptTemplateDB.name, PromptTemplateDB.content)
            .join(AgentPromptBindingDB, AgentPromptBindingDB.prompt_id == PromptTemplateDB.id)
            .where(AgentPromptBindingDB.agent_id == agent_id)
            .order_by(AgentPromptBindingDB.sort_order)
        )
        result = await self.session.execute(stmt)
        return [(name, content) for name, content in result.all() if content and content.strip()]


class PresetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> list[AgentPresetDB]:
        result = await self.session.execute(select(AgentPresetDB).order_by(AgentPresetDB.created_at))
        return list(result.scalars().all())

    async def get_by_id(self, preset_id: str) -> AgentPresetDB | None:
        return await self.session.get(AgentPresetDB, preset_id)

    async def create(self, **kwargs) -> AgentPresetDB:
        preset = AgentPresetDB(**kwargs)
        self.session.add(preset)
        await self.session.commit()
        await self.session.refresh(preset)
        return preset

    async def update(self, preset_id: str, **kwargs) -> AgentPresetDB | None:
        preset = await self.get_by_id(preset_id)
        if preset is None:
            return None
        for key, value in kwargs.items():
            if hasattr(preset, key):
                setattr(preset, key, value)
        preset.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(preset)
        return preset

    async def delete(self, preset_id: str) -> bool:
        preset = await self.get_by_id(preset_id)
        if preset is None:
            return False
        await self.session.delete(preset)
        await self.session.commit()
        return True


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self, limit: int = 50, user_id: str | None = None) -> list[SessionMeta]:
        stmt = select(SessionMeta).where(~SessionMeta.id.contains("--sa--"))
        if user_id:
            stmt = stmt.where(SessionMeta.user_id == user_id)
        stmt = stmt.order_by(SessionMeta.updated_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_recent_for_sidebar(
        self,
        user_id: str | None = None,
        days: int = 30,
        include_session_id: str | None = None,
    ) -> list[SessionMeta]:
        """List sidebar sessions from a rolling window without a global row cap."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        conditions = [
            ~SessionMeta.id.contains("--sa--"),
            SessionMeta.updated_at >= cutoff,
        ]
        if include_session_id:
            conditions[-1] = or_(
                SessionMeta.updated_at >= cutoff,
                SessionMeta.id == include_session_id,
            )
        stmt = select(SessionMeta).where(*conditions)
        if user_id:
            stmt = stmt.where(SessionMeta.user_id == user_id)
        stmt = stmt.order_by(SessionMeta.updated_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, session_id: str) -> SessionMeta | None:
        return await self.session.get(SessionMeta, session_id)

    async def create(self, **kwargs) -> SessionMeta:
        sess = SessionMeta(**kwargs)
        self.session.add(sess)
        await self.session.commit()
        await self.session.refresh(sess)
        return sess

    async def update(self, session_id: str, **kwargs) -> SessionMeta | None:
        sess = await self.get_by_id(session_id)
        if sess is None:
            return None

        changed = False
        if "is_pinned" in kwargs:
            is_pinned = bool(kwargs.pop("is_pinned"))
            if sess.is_pinned != is_pinned:
                sess.is_pinned = is_pinned
                sess.pinned_at = datetime.now(timezone.utc) if is_pinned else None
                changed = True

        for key, value in kwargs.items():
            if hasattr(sess, key) and getattr(sess, key) != value:
                setattr(sess, key, value)
                changed = True

        if not changed:
            return sess

        sess.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(sess)
        return sess

    async def delete(self, session_id: str) -> bool:
        sess = await self.get_by_id(session_id)
        if sess is None:
            return False
        await self.session.delete(sess)
        await self.session.commit()
        return True

    async def list_children(self, parent_session_id: str) -> list[SessionMeta]:
        result = await self.session.execute(
            select(SessionMeta)
            .where(SessionMeta.parent_session_id == parent_session_id)
            .order_by(SessionMeta.created_at)
        )
        return list(result.scalars().all())

    async def increment_messages(self, session_id: str) -> None:
        sess = await self.get_by_id(session_id)
        if sess:
            sess.message_count += 1
            sess.updated_at = datetime.now(timezone.utc)
            await self.session.commit()


class AutomationTaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self, user_id: str | None = None) -> list[AutomationTask]:
        stmt = select(AutomationTask).order_by(AutomationTask.updated_at.desc())
        if user_id:
            stmt = stmt.where(AutomationTask.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, task_id: str) -> AutomationTask | None:
        return await self.session.get(AutomationTask, task_id)

    async def create(self, **kwargs) -> AutomationTask:
        task = AutomationTask(**kwargs)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def update(self, task_id: str, **kwargs) -> AutomationTask | None:
        task = await self.get_by_id(task_id)
        if task is None:
            return None
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        task.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def delete(self, task_id: str) -> bool:
        task = await self.get_by_id(task_id)
        if task is None:
            return False
        await self.session.delete(task)
        await self.session.commit()
        return True


class AutomationRunRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_task(self, task_id: str, limit: int = 50) -> list[AutomationRun]:
        result = await self.session.execute(
            select(AutomationRun)
            .where(AutomationRun.task_id == task_id)
            .order_by(AutomationRun.scheduled_at.desc(), AutomationRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_task(self, task_id: str) -> int:
        result = await self.session.execute(
            select(func.count(AutomationRun.id)).where(AutomationRun.task_id == task_id)
        )
        return int(result.scalar_one())

    async def list_active(self) -> list[AutomationRun]:
        result = await self.session.execute(
            select(AutomationRun).where(AutomationRun.status.in_(AUTOMATION_ACTIVE_STATUSES))
        )
        return list(result.scalars().all())

    async def list_active_by_task(self, task_id: str) -> list[AutomationRun]:
        result = await self.session.execute(
            select(AutomationRun).where(
                AutomationRun.task_id == task_id,
                AutomationRun.status.in_(AUTOMATION_ACTIVE_STATUSES),
            )
        )
        return list(result.scalars().all())

    async def list_all(self, user_id: str | None = None, limit: int = 100) -> list[AutomationRun]:
        stmt = (
            select(AutomationRun)
            .order_by(AutomationRun.scheduled_at.desc(), AutomationRun.created_at.desc())
            .limit(limit)
        )
        if user_id:
            stmt = stmt.where(AutomationRun.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self, user_id: str | None = None) -> int:
        stmt = select(func.count(AutomationRun.id))
        if user_id:
            stmt = stmt.where(AutomationRun.user_id == user_id)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def get_by_id(self, run_id: str) -> AutomationRun | None:
        return await self.session.get(AutomationRun, run_id)

    async def create(self, **kwargs) -> AutomationRun | None:
        run = AutomationRun(**kwargs)
        self.session.add(run)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            return None
        await self.session.refresh(run)
        return run

    async def update(self, run_id: str, **kwargs) -> AutomationRun | None:
        run = await self.get_by_id(run_id)
        if run is None:
            return None
        for key, value in kwargs.items():
            if hasattr(run, key):
                setattr(run, key, value)
        await self.session.commit()
        await self.session.refresh(run)
        return run


class ChatUiMessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        session_id: str,
        role: str,
        content: list[dict] | None = None,
        tool_calls: list[dict] | None = None,
        usage: dict | None = None,
        http_traces: list[dict] | None = None,
    ) -> ChatUiMessage:
        message = ChatUiMessage(
            session_id=session_id,
            role=role,
            content=content or [],
            tool_calls=tool_calls,
            usage=usage,
            http_traces=http_traces,
        )
        self.session.add(message)
        await self.session.commit()
        try:
            await self.session.refresh(message)
        except Exception:
            pass
        return message

    async def list_by_session(
        self,
        session_id: str,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[ChatUiMessage]:
        stmt = (
            select(ChatUiMessage)
            .where(ChatUiMessage.session_id == session_id)
            .order_by(ChatUiMessage.created_at, ChatUiMessage.id)
        )
        if offset > 0:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, message_id: str) -> ChatUiMessage | None:
        return await self.session.get(ChatUiMessage, message_id)

    async def truncate_from_message(self, session_id: str, message_id: str) -> int:
        anchor = await self.session.get(ChatUiMessage, message_id)
        if anchor is None or anchor.session_id != session_id:
            return 0

        result = await self.session.execute(
            select(ChatUiMessage)
            .where(ChatUiMessage.session_id == session_id)
            .order_by(ChatUiMessage.created_at, ChatUiMessage.id)
        )
        rows = list(result.scalars().all())
        start_idx = next((idx for idx, row in enumerate(rows) if row.id == anchor.id), -1)
        if start_idx < 0:
            return 0

        for row in rows[start_idx:]:
            await self.session.delete(row)
        await self.session.commit()
        return len(rows[start_idx:])

    async def get_last_assistant(self, session_id: str) -> ChatUiMessage | None:
        result = await self.session.execute(
            select(ChatUiMessage)
            .where(ChatUiMessage.session_id == session_id, ChatUiMessage.role == "assistant")
            .order_by(ChatUiMessage.created_at.desc(), ChatUiMessage.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_by_session(self, session_id: str) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(ChatUiMessage).where(ChatUiMessage.session_id == session_id)
        )
        return int(result.scalar_one())


class FileChangeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> FileChange:
        fc = FileChange(**kwargs)
        self.session.add(fc)
        await self.session.commit()
        try:
            await self.session.refresh(fc)
        except Exception:
            pass
        return fc

    async def list_by_session(self, session_id: str) -> list[FileChange]:
        result = await self.session.execute(
            select(FileChange)
            .where(FileChange.session_id == session_id)
            .order_by(FileChange.created_at)
        )
        return list(result.scalars().all())

    async def delete_by_session(self, session_id: str) -> int:
        rows = await self.list_by_session(session_id)
        for row in rows:
            await self.session.delete(row)
        await self.session.commit()
        return len(rows)
