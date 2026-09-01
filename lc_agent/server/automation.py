"""Scheduling and execution support for persisted automation tasks."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from tzlocal import get_localzone_name

from lc_agent.core.engine import AgentEngine
from lc_agent.db.engine import get_async_session
from lc_agent.db.models import AutomationRun, AutomationTask
from lc_agent.db.models_auth import User, UserAgentAccess
from lc_agent.db.repository import (
    AUTOMATION_ACTIVE_STATUSES,
    AutomationRunRepository,
    AutomationTaskRepository,
    SessionRepository,
)
from lc_agent.server.automation_notifications import (
    AutomationNotificationService,
    NotificationDeliverySummary,
)


logger = logging.getLogger(__name__)

SCHEDULE_TYPES = {"one_time", "interval", "daily", "weekly"}
INTERVAL_UNITS = {"minutes": 60, "hours": 3600, "days": 86400}


class AutomationScheduleError(ValueError):
    """Raised when a task schedule cannot be normalized or constructed."""


def local_timezone_name() -> str:
    try:
        return get_localzone_name()
    except Exception:
        return "UTC"


def resolve_timezone(name: str | None) -> tuple[str, Any]:
    timezone_name = (name or local_timezone_name()).strip() or "UTC"
    try:
        return timezone_name, ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise AutomationScheduleError(f"无效的时区: {timezone_name}") from exc


def _parse_datetime(value: Any, tz: Any, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise AutomationScheduleError(f"{field_name}不能为空")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise AutomationScheduleError(f"{field_name}格式无效") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=tz)
    return parsed.astimezone(tz)


def _parse_time(value: Any) -> tuple[int, int]:
    if not isinstance(value, str):
        raise AutomationScheduleError("执行时间格式无效")
    parts = value.strip().split(":")
    if len(parts) != 2:
        raise AutomationScheduleError("执行时间必须是 HH:MM")
    try:
        hour, minute = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise AutomationScheduleError("执行时间必须是 HH:MM") from exc
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise AutomationScheduleError("执行时间必须是 HH:MM")
    return hour, minute


def normalize_schedule(
    schedule_type: str,
    schedule_config: dict[str, Any] | None,
    timezone_name: str | None,
    *,
    now: datetime | None = None,
) -> tuple[dict[str, Any], str, datetime]:
    """Validate a user schedule and return normalized config, timezone, and next run."""
    if schedule_type not in SCHEDULE_TYPES:
        raise AutomationScheduleError("不支持的执行周期")

    normalized_timezone, tz = resolve_timezone(timezone_name)
    config = dict(schedule_config or {})
    current = now or datetime.now(tz)
    if current.tzinfo is None:
        current = current.replace(tzinfo=tz)
    else:
        current = current.astimezone(tz)

    if schedule_type == "one_time":
        run_at = _parse_datetime(config.get("run_at"), tz, "执行时间")
        if run_at <= current:
            raise AutomationScheduleError("一次性任务的执行时间必须晚于当前时间")
        normalized = {"run_at": run_at.isoformat()}
        trigger = DateTrigger(run_date=run_at, timezone=tz)
    elif schedule_type == "interval":
        try:
            value = int(config.get("value", 0))
        except (TypeError, ValueError) as exc:
            raise AutomationScheduleError("间隔数值必须是正整数") from exc
        unit = config.get("unit", "minutes")
        if value <= 0 or unit not in INTERVAL_UNITS:
            raise AutomationScheduleError("间隔必须是正数，单位支持分钟、小时或天")
        start_at = _parse_datetime(config["start_at"], tz, "开始时间") if config.get("start_at") else current + timedelta(seconds=value * INTERVAL_UNITS[unit])
        normalized = {"value": value, "unit": unit, "start_at": start_at.isoformat()}
        trigger = IntervalTrigger(
            seconds=value * INTERVAL_UNITS[unit],
            start_date=start_at,
            timezone=tz,
        )
    else:
        hour, minute = _parse_time(config.get("time"))
        if schedule_type == "daily":
            normalized = {"time": f"{hour:02d}:{minute:02d}"}
            trigger = CronTrigger(hour=hour, minute=minute, timezone=tz)
        else:
            try:
                day_of_week = int(config.get("day_of_week"))
            except (TypeError, ValueError) as exc:
                raise AutomationScheduleError("每周任务必须选择星期") from exc
            if day_of_week not in range(7):
                raise AutomationScheduleError("每周任务的星期必须是 0 到 6")
            normalized = {
                "day_of_week": day_of_week,
                "time": f"{hour:02d}:{minute:02d}",
            }
            trigger = CronTrigger(
                day_of_week=day_of_week,
                hour=hour,
                minute=minute,
                timezone=tz,
            )

    next_run = trigger.get_next_fire_time(None, current)
    if next_run is None:
        raise AutomationScheduleError("无法计算下一次执行时间")
    return normalized, normalized_timezone, next_run


def trigger_for_task(task: AutomationTask):
    """Build the APScheduler trigger from an already normalized task."""
    timezone_name, tz = resolve_timezone(task.timezone)
    config = task.schedule_config or {}
    if task.schedule_type == "one_time":
        return DateTrigger(run_date=_parse_datetime(config.get("run_at"), tz, "执行时间"), timezone=tz)
    if task.schedule_type == "interval":
        value = int(config["value"])
        return IntervalTrigger(
            seconds=value * INTERVAL_UNITS[config["unit"]],
            start_date=_parse_datetime(config.get("start_at"), tz, "开始时间"),
            timezone=tz,
        )
    hour, minute = _parse_time(config.get("time"))
    if task.schedule_type == "daily":
        return CronTrigger(hour=hour, minute=minute, timezone=tz)
    return CronTrigger(
        day_of_week=int(config["day_of_week"]),
        hour=hour,
        minute=minute,
        timezone=tz,
    )


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def serialize_task(task: AutomationTask, engine: AgentEngine | None = None) -> dict[str, Any]:
    data = {
        "id": task.id,
        "user_id": task.user_id,
        "name": task.name,
        "agent_id": task.agent_id,
        "prompt": task.prompt,
        "schedule_type": task.schedule_type,
        "schedule_config": task.schedule_config,
        "notification_targets": task.notification_targets or [],
        "timezone": task.timezone,
        "enabled": task.enabled,
        "next_run_at": _iso(task.next_run_at),
        "last_run_at": _iso(task.last_run_at),
        "last_status": task.last_status,
        "created_at": _iso(task.created_at),
        "updated_at": _iso(task.updated_at),
    }
    if engine is not None:
        if engine._preset_exists(task.agent_id):
            preset = engine._resolve_preset(task.agent_id)
            data["agent_name"] = preset.display_name or preset.name
        else:
            data["agent_name"] = task.agent_id
    return data


def serialize_run(run: AutomationRun) -> dict[str, Any]:
    return {
        "id": run.id,
        "task_id": run.task_id,
        "user_id": run.user_id,
        "session_id": run.session_id,
        "status": run.status,
        "scheduled_at": _iso(run.scheduled_at),
        "started_at": _iso(run.started_at),
        "finished_at": _iso(run.finished_at),
        "error": run.error,
        "notification_status": run.notification_status,
        "notification_error": run.notification_error,
        "created_at": _iso(run.created_at),
    }


class AutomationRunner:
    def __init__(self, engine: AgentEngine, db_url: str, app):
        self.engine = engine
        self.db_url = db_url
        self.app = app
        self._task_locks: dict[str, asyncio.Lock] = {}

    def _get_task_lock(self, task_id: str) -> asyncio.Lock:
        lock = self._task_locks.get(task_id)
        if lock is None:
            lock = asyncio.Lock()
            self._task_locks[task_id] = lock
        return lock

    async def recover_interrupted_runs(self) -> None:
        db = get_async_session(self.db_url)
        try:
            runs = await AutomationRunRepository(db).list_active()
            if not runs:
                return
            now = datetime.now(timezone.utc)
            repo = AutomationRunRepository(db)
            task_repo = AutomationTaskRepository(db)
            for run in runs:
                await repo.update(
                    run.id,
                    status="failed",
                    finished_at=now,
                    error="后端在任务执行期间重启，原执行已中断",
                )
                task = await task_repo.get_by_id(run.task_id)
                if task and task.last_status in AUTOMATION_ACTIVE_STATUSES:
                    await task_repo.update(task.id, last_status="failed", last_run_at=now)
        finally:
            await db.close()

    async def _user_can_use_agent(self, user_id: str, agent_id: str) -> bool:
        if not getattr(self.app.state, "auth_service", None) or user_id == "__anonymous__":
            return True
        db = get_async_session(self.db_url)
        try:
            user = await db.get(User, user_id)
            if user is None:
                return False
            if user.role == "admin" or agent_id == "chat":
                return True
            access = await db.get(UserAgentAccess, (user_id, agent_id))
            return access is not None
        finally:
            await db.close()

    async def _claim_run(
        self,
        task: AutomationTask,
        scheduled_at: datetime,
        *,
        allow_disabled: bool = False,
    ) -> AutomationRun | None:
        lock = self._get_task_lock(task.id)
        if lock.locked():
            return await self._record_skipped(task, scheduled_at)

        async with lock:
            db = get_async_session(self.db_url)
            try:
                task_repo = AutomationTaskRepository(db)
                run_repo = AutomationRunRepository(db)
                current = await task_repo.get_by_id(task.id)
                if current is None or (not current.enabled and not allow_disabled):
                    return None
                active = await run_repo.list_active_by_task(task.id)
                if active:
                    return await self._record_skipped(task, scheduled_at)
                run = await run_repo.create(
                    task_id=task.id,
                    user_id=task.user_id,
                    status="pending",
                    scheduled_at=scheduled_at,
                )
                if run is None:
                    return await self._record_skipped(task, scheduled_at)
                return run
            finally:
                await db.close()

    async def _record_skipped(self, task: AutomationTask, scheduled_at: datetime) -> AutomationRun:
        db = get_async_session(self.db_url)
        try:
            run = await AutomationRunRepository(db).create(
                task_id=task.id,
                user_id=task.user_id,
                status="skipped",
                scheduled_at=scheduled_at,
                finished_at=datetime.now(timezone.utc),
                error="上一次执行尚未完成",
                notification_status="not_sent" if task.notification_targets else "not_configured",
            )
            await AutomationTaskRepository(db).update(
                task.id,
                last_status="skipped",
                last_run_at=_as_utc(scheduled_at),
            )
            return run
        finally:
            await db.close()

    async def run_scheduled(self, task_id: str, scheduled_at: datetime | None = None) -> AutomationRun | None:
        db = get_async_session(self.db_url)
        try:
            task = await AutomationTaskRepository(db).get_by_id(task_id)
        finally:
            await db.close()
        if task is None or not task.enabled:
            return None
        return await self._run(task, scheduled_at or datetime.now(timezone.utc))

    async def run_now(self, task_id: str) -> AutomationRun:
        db = get_async_session(self.db_url)
        try:
            task = await AutomationTaskRepository(db).get_by_id(task_id)
        finally:
            await db.close()
        if task is None:
            raise ValueError("自动化任务不存在")
        run = await self._run(task, datetime.now(timezone.utc), allow_disabled=True)
        if run is None:
            raise ValueError("自动化任务当前未执行")
        return run

    async def _run(
        self,
        task: AutomationTask,
        scheduled_at: datetime,
        *,
        allow_disabled: bool = False,
    ) -> AutomationRun | None:
        run = await self._claim_run(task, scheduled_at, allow_disabled=allow_disabled)
        if run is None:
            return None
        if run.status == "skipped":
            return run

        now = datetime.now(timezone.utc)
        db = get_async_session(self.db_url)
        session_id = str(uuid4())
        setup_error: str | None = None
        try:
            await AutomationRunRepository(db).update(run.id, status="running", started_at=now)
            task_repo = AutomationTaskRepository(db)
            await task_repo.update(task.id, last_status="running", last_run_at=_as_utc(scheduled_at))

            if not self.engine._preset_exists(task.agent_id):
                raise ValueError(f"绑定的 Agent 不存在: {task.agent_id}")
            if not await self._user_can_use_agent(task.user_id, task.agent_id):
                raise PermissionError("当前用户无权使用绑定的 Agent")

            title = f"[自动化] {task.name} · {scheduled_at.astimezone().strftime('%Y-%m-%d %H:%M')}"
            await SessionRepository(db).create(
                id=session_id,
                title=title,
                agent_id=task.agent_id,
                model="",
                user_id=task.user_id,
                message_count=0,
            )
            await AutomationRunRepository(db).update(run.id, session_id=session_id)
        except Exception as exc:
            setup_error = str(exc)
        finally:
            await db.close()

        if setup_error is not None:
            await self._finish(run.id, task.id, "failed", setup_error, now)
            await self._notify_run(task, run.id, "failed")
            if task.schedule_type == "one_time":
                db = get_async_session(self.db_url)
                try:
                    await AutomationTaskRepository(db).update(task.id, enabled=False, next_run_at=None)
                finally:
                    await db.close()
            return await self._get_run(run.id)

        try:
            from lc_agent.server.agent_runner import AgentRunService

            service = AgentRunService(self.engine, self.db_url)
            result = await service.run(
                session_id=session_id,
                prompt=task.prompt,
                preset_id=task.agent_id,
                user_id=task.user_id or "anonymous",
            )
            await self._finish(
                run.id,
                task.id,
                "failed" if result.error else "success",
                result.error,
                datetime.now(timezone.utc),
            )
            await self._notify_run(
                task,
                run.id,
                "failed" if result.error else "success",
                final_output=result.final_output,
            )
        except Exception as exc:
            logger.exception("Automation run failed: task=%s run=%s", task.id, run.id)
            await self._finish(run.id, task.id, "failed", str(exc), datetime.now(timezone.utc))
            await self._notify_run(task, run.id, "failed")

        if task.schedule_type == "one_time":
            db = get_async_session(self.db_url)
            try:
                await AutomationTaskRepository(db).update(task.id, enabled=False, next_run_at=None)
            finally:
                await db.close()
        return await self._get_run(run.id)

    async def _load_user(self, user_id: str) -> User | None:
        if not getattr(self.app.state, "auth_service", None):
            return None
        db = get_async_session(self.db_url)
        try:
            return await db.get(User, user_id)
        finally:
            await db.close()

    async def _finish(
        self,
        run_id: str,
        task_id: str,
        status: str,
        error: str | None,
        finished_at: datetime,
    ) -> None:
        db = get_async_session(self.db_url)
        try:
            await AutomationRunRepository(db).update(
                run_id,
                status=status,
                finished_at=finished_at,
                error=error,
            )
            await AutomationTaskRepository(db).update(
                task_id,
                last_status=status,
                last_run_at=finished_at,
            )
        finally:
            await db.close()

    async def _notify_run(
        self,
        task: AutomationTask,
        run_id: str,
        run_status: str,
        *,
        final_output: str = "",
    ) -> None:
        try:
            app_config = getattr(self.app, "config", {})
            app_name = app_config.get("ui", {}).get("app_name", "lc-agent")
            summary = await AutomationNotificationService(app_name=app_name).deliver_run(
                task.notification_targets or [],
                task_name=task.name,
                run_status=run_status,
                final_output=final_output,
            )
        except Exception:
            logger.exception("Automation notification failed unexpectedly: task=%s run=%s", task.id, run_id)
            summary = NotificationDeliverySummary(status="failed", error="通知服务异常")
        db = get_async_session(self.db_url)
        try:
            await AutomationRunRepository(db).update(
                run_id,
                notification_status=summary.status,
                notification_error=summary.error,
            )
        finally:
            await db.close()

    async def _get_run(self, run_id: str) -> AutomationRun:
        db = get_async_session(self.db_url)
        try:
            run = await AutomationRunRepository(db).get_by_id(run_id)
            if run is None:
                raise RuntimeError("自动化执行记录丢失")
            return run
        finally:
            await db.close()


class AutomationScheduler:
    def __init__(self, engine: AgentEngine, db_url: str, app):
        self.engine = engine
        self.db_url = db_url
        self.app = app
        self.runner = AutomationRunner(engine, db_url, app)
        self.scheduler = AsyncIOScheduler(timezone=ZoneInfo(local_timezone_name()))
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        await self.runner.recover_interrupted_runs()
        self.scheduler.start()
        self._started = True
        db = get_async_session(self.db_url)
        try:
            tasks = await AutomationTaskRepository(db).list_all()
        finally:
            await db.close()
        for task in tasks:
            if task.enabled:
                try:
                    await self.schedule_task(task)
                except Exception:
                    logger.exception("Failed to restore automation task %s", task.id)

    async def stop(self) -> None:
        if not self._started:
            return
        self.scheduler.shutdown(wait=False)
        await asyncio.sleep(0)
        self._started = False

    async def schedule_task(self, task: AutomationTask) -> None:
        job_id = self._job_id(task.id)
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        if not task.enabled:
            return
        trigger = trigger_for_task(task)
        self.scheduler.add_job(
            self._dispatch,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs={"task_id": task.id},
            max_instances=10,
            coalesce=False,
            misfire_grace_time=3600,
        )
        job = self.scheduler.get_job(job_id)
        next_run_at = getattr(job, "next_run_time", None) if job else None
        if next_run_at:
            db = get_async_session(self.db_url)
            try:
                await AutomationTaskRepository(db).update(
                    task.id,
                    next_run_at=_as_utc(next_run_at),
                )
            finally:
                await db.close()

    async def unschedule_task(self, task_id: str) -> None:
        job_id = self._job_id(task_id)
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        db = get_async_session(self.db_url)
        try:
            await AutomationTaskRepository(db).update(task_id, next_run_at=None)
        finally:
            await db.close()

    async def refresh_task(self, task_id: str) -> None:
        db = get_async_session(self.db_url)
        try:
            task = await AutomationTaskRepository(db).get_by_id(task_id)
        finally:
            await db.close()
        if task is None:
            return
        if task.enabled:
            await self.schedule_task(task)
        else:
            await self.unschedule_task(task.id)

    async def _dispatch(self, task_id: str) -> None:
        try:
            await self.runner.run_scheduled(task_id)
            job = self.scheduler.get_job(self._job_id(task_id))
            next_run_at = getattr(job, "next_run_time", None) if job else None
            db = get_async_session(self.db_url)
            try:
                await AutomationTaskRepository(db).update(
                    task_id,
                    next_run_at=_as_utc(next_run_at),
                )
            finally:
                await db.close()
        except Exception:
            logger.exception("Automation dispatch failed: task=%s", task_id)

    @staticmethod
    def _job_id(task_id: str) -> str:
        return f"automation:{task_id}"
