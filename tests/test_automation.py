from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from lc_agent.db.engine import get_async_session, init_db, reset_engine
from lc_agent.db.repository import AutomationRunRepository, AutomationTaskRepository
from lc_agent.server.agent_runner import AgentRunService
from lc_agent.server.automation import AutomationScheduleError, AutomationScheduler, normalize_schedule


@pytest.fixture
async def db_url(tmp_path):
    reset_engine()
    url = f"sqlite+aiosqlite:///{tmp_path / 'automation.db'}"
    await init_db(url)
    yield url
    reset_engine()


def test_normalize_schedule_variants():
    now = datetime(2026, 8, 27, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    config, timezone_name, next_run = normalize_schedule(
        "daily", {"time": "11:30"}, "Asia/Shanghai", now=now,
    )
    assert config == {"time": "11:30"}
    assert timezone_name == "Asia/Shanghai"
    assert next_run.hour == 11
    assert next_run.minute == 30

    config, _, next_run = normalize_schedule(
        "interval",
        {"value": 2, "unit": "hours", "start_at": "2026-08-27T10:30:00"},
        "Asia/Shanghai",
        now=now,
    )
    assert config["value"] == 2
    assert next_run.isoformat() == "2026-08-27T10:30:00+08:00"


def test_normalize_schedule_rejects_invalid_values():
    now = datetime(2026, 8, 27, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    with pytest.raises(AutomationScheduleError):
        normalize_schedule("daily", {"time": "25:00"}, "Asia/Shanghai", now=now)
    with pytest.raises(AutomationScheduleError):
        normalize_schedule("interval", {"value": 0, "unit": "minutes"}, "Asia/Shanghai", now=now)
    with pytest.raises(AutomationScheduleError):
        normalize_schedule("one_time", {"run_at": "2026-08-27T09:00:00"}, "Asia/Shanghai", now=now)


@pytest.mark.asyncio
async def test_automation_repositories_preserve_task_and_run_history(db_url):
    async with get_async_session(db_url) as db:
        task_repo = AutomationTaskRepository(db)
        run_repo = AutomationRunRepository(db)
        task = await task_repo.create(
            user_id="user-1",
            name="每日摘要",
            agent_id="power",
            prompt="整理今天的摘要",
            schedule_type="daily",
            schedule_config={"time": "09:00"},
            timezone="Asia/Shanghai",
            enabled=True,
        )
        task_id = task.id
        run = await run_repo.create(
            task_id=task_id,
            user_id="user-1",
            status="success",
            scheduled_at=datetime(2026, 8, 27, 9, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
        run_id = run.id
        active_run = await run_repo.create(
            task_id=task_id,
            user_id="user-1",
            status="running",
            scheduled_at=datetime(2026, 8, 27, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
        duplicate_active = await run_repo.create(
            task_id=task_id,
            user_id="user-1",
            status="pending",
            scheduled_at=datetime(2026, 8, 27, 11, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
        assert (await task_repo.get_by_id(task_id)).agent_id == "power"
        assert run_id in {item.id for item in await run_repo.list_by_task(task_id)}
        assert active_run is not None
        assert duplicate_active is None


@pytest.mark.asyncio
async def test_agent_run_service_persists_a_standalone_execution(db_url):
    from types import SimpleNamespace

    class FakeEngine:
        recursion_limit = 50

        class FakeAgent:
            async def aget_state(self, config):
                return SimpleNamespace(tasks=[])

        def _preset_exists(self, preset_id):
            return preset_id == "fake-agent"

        def _get_or_build_agent(self, preset_id, model_id="", llm_params=None):
            return self.FakeAgent()

        def get_subagent_display_name_map(self, preset_id, **kwargs):
            return {}

        def get_subagent_tool_names(self, preset_id, **kwargs):
            return set()

        async def chat_stream(self, *args, **kwargs):
            yield {
                "event": "on_chat_model_stream",
                "metadata": {},
                "data": {"chunk": SimpleNamespace(content="自动化结果", additional_kwargs={})},
            }
            yield {
                "event": "on_chat_model_end",
                "metadata": {},
                "data": {"output": SimpleNamespace(usage_metadata={"input_tokens": 2, "output_tokens": 3, "total_tokens": 5})},
            }

    session_id = "automation-session"
    async with get_async_session(db_url) as db:
        from lc_agent.db.repository import SessionRepository

        await SessionRepository(db).create(
            id=session_id,
            title="自动化测试",
            agent_id="fake-agent",
            model="",
            user_id="user-1",
        )

    result = await AgentRunService(FakeEngine(), db_url).run(
        session_id=session_id,
        prompt="执行测试",
        preset_id="fake-agent",
        user_id="user-1",
    )

    assert result.error is None
    async with get_async_session(db_url) as db:
        from lc_agent.db.repository import ChatUiMessageRepository, SessionRepository

        messages = await ChatUiMessageRepository(db).list_by_session(session_id)
        session = await SessionRepository(db).get_by_id(session_id)
        assert [message.role for message in messages] == ["user", "assistant"]
        assert messages[-1].content[0]["text"] == "自动化结果"
        assert messages[-1].usage["rounds"][0]["total_tokens"] == 5
        assert session.message_count == 1


@pytest.mark.asyncio
async def test_automation_scheduler_starts_and_stops_with_application(db_url):
    from types import SimpleNamespace

    app = SimpleNamespace(state=SimpleNamespace())
    scheduler = AutomationScheduler(object(), db_url, app)
    await scheduler.start()
    assert scheduler.scheduler.running is True
    await scheduler.stop()
    assert scheduler.scheduler.running is False
