from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from lc_agent.core.engine import AgentEngine
from lc_agent.db.models import AutomationTask
from lc_agent.db.models_auth import User, UserAgentAccess
from lc_agent.db.repository import AutomationRunRepository, AutomationTaskRepository
from lc_agent.server.auth_middleware import get_current_user
from lc_agent.server.automation import (
    AutomationScheduleError,
    AutomationScheduler,
    _as_utc,
    local_timezone_name,
    normalize_schedule,
    serialize_run,
    serialize_task,
)
from lc_agent.server.dependencies import get_db_session, get_engine


router = APIRouter(prefix="/automation", tags=["automation"])


class AutomationTaskCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    agent_id: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1, max_length=100_000)
    schedule_type: Literal["one_time", "interval", "daily", "weekly"]
    schedule_config: dict[str, Any] = Field(default_factory=dict)
    timezone: str | None = None
    enabled: bool = True

    @field_validator("name", "agent_id", "prompt")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value


class AutomationTaskUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    agent_id: str | None = Field(default=None, min_length=1, max_length=200)
    prompt: str | None = Field(default=None, min_length=1, max_length=100_000)
    schedule_type: Literal["one_time", "interval", "daily", "weekly"] | None = None
    schedule_config: dict[str, Any] | None = None
    timezone: str | None = None
    enabled: bool | None = None

    @field_validator("name", "agent_id", "prompt")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value


def _get_scheduler(request: Request) -> AutomationScheduler:
    scheduler = getattr(request.app.state, "automation_scheduler", None)
    if scheduler is None:
        raise HTTPException(status_code=503, detail="自动化调度器尚未启动")
    return scheduler


def _check_task_access(task: AutomationTask, user: User) -> None:
    if user.role != "admin" and task.user_id != user.id:
        raise HTTPException(status_code=403, detail="权限不足")


async def _check_agent_access(
    agent_id: str,
    user: User,
    engine: AgentEngine,
    db: AsyncSession,
) -> None:
    if not engine._preset_exists(agent_id):
        raise HTTPException(status_code=422, detail=f"Agent 不存在: {agent_id}")
    if user.role == "admin" or agent_id == "chat":
        return
    access = await db.get(UserAgentAccess, (user.id, agent_id))
    if access is None:
        raise HTTPException(status_code=403, detail="无权使用此智能体")


def _normalize_or_raise(
    schedule_type: str,
    schedule_config: dict[str, Any],
    timezone_name: str | None,
) -> tuple[dict[str, Any], str, Any]:
    try:
        return normalize_schedule(schedule_type, schedule_config, timezone_name)
    except AutomationScheduleError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


async def _get_task_or_404(
    task_id: str,
    user: User,
    db: AsyncSession,
) -> AutomationTask:
    task = await AutomationTaskRepository(db).get_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="自动化任务不存在")
    _check_task_access(task, user)
    return task


@router.get("/tasks")
async def list_tasks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    engine: AgentEngine = Depends(get_engine),
):
    user_id = None if user.role == "admin" else user.id
    tasks = await AutomationTaskRepository(db).list_all(user_id=user_id)
    return [serialize_task(task, engine) for task in tasks]


@router.get("/timezone")
async def get_timezone(user: User = Depends(get_current_user)):
    return {"timezone": local_timezone_name()}


@router.post("/tasks", status_code=201)
async def create_task(
    body: AutomationTaskCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    engine: AgentEngine = Depends(get_engine),
    scheduler: AutomationScheduler = Depends(_get_scheduler),
):
    await _check_agent_access(body.agent_id, user, engine, db)
    normalized_config, normalized_timezone, next_run_at = _normalize_or_raise(
        body.schedule_type,
        body.schedule_config,
        body.timezone,
    )
    task = await AutomationTaskRepository(db).create(
        user_id=user.id,
        name=body.name,
        agent_id=body.agent_id,
        prompt=body.prompt,
        schedule_type=body.schedule_type,
        schedule_config=normalized_config,
        timezone=normalized_timezone,
        enabled=body.enabled,
        next_run_at=_as_utc(next_run_at) if body.enabled else None,
    )
    if task.enabled:
        await scheduler.schedule_task(task)
    return serialize_task(task, engine)


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    engine: AgentEngine = Depends(get_engine),
):
    task = await _get_task_or_404(task_id, user, db)
    return serialize_task(task, engine)


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: str,
    body: AutomationTaskUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    engine: AgentEngine = Depends(get_engine),
    scheduler: AutomationScheduler = Depends(_get_scheduler),
):
    task = await _get_task_or_404(task_id, user, db)
    updates = body.model_dump(exclude_unset=True)
    target_agent = updates.get("agent_id", task.agent_id)
    await _check_agent_access(target_agent, user, engine, db)

    schedule_changed = any(key in updates for key in ("schedule_type", "schedule_config", "timezone"))
    enabling = updates.get("enabled") is True and not task.enabled
    if schedule_changed or enabling:
        schedule_type = updates.get("schedule_type", task.schedule_type)
        schedule_config = updates.get("schedule_config", task.schedule_config)
        timezone_name = updates.get("timezone", task.timezone)
        normalized_config, normalized_timezone, next_run_at = _normalize_or_raise(
            schedule_type,
            schedule_config,
            timezone_name,
        )
        updates["schedule_type"] = schedule_type
        updates["schedule_config"] = normalized_config
        updates["timezone"] = normalized_timezone
        updates["next_run_at"] = _as_utc(next_run_at) if updates.get("enabled", task.enabled) else None
    elif updates.get("enabled") is False:
        updates["next_run_at"] = None

    updated = await AutomationTaskRepository(db).update(task_id, **updates)
    if updated is None:
        raise HTTPException(status_code=404, detail="自动化任务不存在")
    await scheduler.refresh_task(task_id)
    return serialize_task(updated, engine)


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    scheduler: AutomationScheduler = Depends(_get_scheduler),
):
    task = await _get_task_or_404(task_id, user, db)
    await scheduler.unschedule_task(task.id)
    if not await AutomationTaskRepository(db).delete(task.id):
        raise HTTPException(status_code=404, detail="自动化任务不存在")


@router.post("/tasks/{task_id}/pause")
async def pause_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    engine: AgentEngine = Depends(get_engine),
    scheduler: AutomationScheduler = Depends(_get_scheduler),
):
    task = await _get_task_or_404(task_id, user, db)
    updated = await AutomationTaskRepository(db).update(task.id, enabled=False, next_run_at=None)
    await scheduler.unschedule_task(task.id)
    return serialize_task(updated, engine)


@router.post("/tasks/{task_id}/resume")
async def resume_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    engine: AgentEngine = Depends(get_engine),
    scheduler: AutomationScheduler = Depends(_get_scheduler),
):
    task = await _get_task_or_404(task_id, user, db)
    normalized_config, normalized_timezone, next_run_at = _normalize_or_raise(
        task.schedule_type,
        task.schedule_config,
        task.timezone,
    )
    updated = await AutomationTaskRepository(db).update(
        task.id,
        enabled=True,
        schedule_config=normalized_config,
        timezone=normalized_timezone,
        next_run_at=_as_utc(next_run_at),
    )
    await scheduler.refresh_task(task.id)
    return serialize_task(updated, engine)


@router.post("/tasks/{task_id}/run")
async def run_task_now(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    scheduler: AutomationScheduler = Depends(_get_scheduler),
):
    await _get_task_or_404(task_id, user, db)
    try:
        run = await scheduler.runner.run_now(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return serialize_run(run)


@router.get("/tasks/{task_id}/runs")
async def list_task_runs(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    task = await _get_task_or_404(task_id, user, db)
    runs = await AutomationRunRepository(db).list_by_task(task.id)
    return [serialize_run(run) for run in runs]


@router.get("/runs")
async def list_runs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_id = None if user.role == "admin" else user.id
    runs = await AutomationRunRepository(db).list_all(user_id=user_id)
    return [serialize_run(run) for run in runs]


@router.post("/runs/{run_id}/rerun")
async def rerun(
    run_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    scheduler: AutomationScheduler = Depends(_get_scheduler),
):
    run = await AutomationRunRepository(db).get_by_id(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    if user.role != "admin" and run.user_id != user.id:
        raise HTTPException(status_code=403, detail="权限不足")
    if run.status != "failed":
        raise HTTPException(status_code=409, detail="只有失败的执行记录可以重新执行")
    try:
        new_run = await scheduler.runner.run_now(run.task_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return serialize_run(new_run)
