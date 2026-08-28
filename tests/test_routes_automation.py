import pytest
from httpx import ASGITransport, AsyncClient

from lc_agent.app import LcAgentApp
from lc_agent.db.engine import init_db, reset_engine
from tests.conftest import setup_test_auth


@pytest.fixture
async def app_and_headers(tmp_path):
    reset_engine()
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'automation-routes.db'}"
    await init_db(db_url)
    config = {
        "provider": {
            "openai": {
                "base_url": "http://fake",
                "api_key": "sk-fake",
                "models": [{"id": "gpt-4"}],
            }
        },
        "agent": {"default_model": "gpt-4", "system_prompt": "You are helpful."},
        "database": {"url": db_url, "checkpoint_path": ":memory:"},
    }
    app = LcAgentApp(config)
    headers = await setup_test_auth(app.fastapi_app, db_url)
    yield app, headers
    reset_engine()


@pytest.mark.asyncio
async def test_automation_task_crud_and_forbidden_duplicate_config(app_and_headers):
    app, headers = app_and_headers
    transport = ASGITransport(app=app.fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/automation/tasks",
            json={
                "name": "每日摘要",
                "agent_id": "power",
                "prompt": "整理今日摘要",
                "schedule_type": "daily",
                "schedule_config": {"time": "09:00"},
                "timezone": "Asia/Shanghai",
                "tools": ["should-not-be-accepted"],
            },
            headers=headers,
        )
        assert response.status_code == 422

        response = await client.post(
            "/api/automation/tasks",
            json={
                "name": "每日摘要",
                "agent_id": "power",
                "prompt": "整理今日摘要",
                "schedule_type": "daily",
                "schedule_config": {"time": "09:00"},
                "timezone": "Asia/Shanghai",
            },
            headers=headers,
        )
        assert response.status_code == 201
        task = response.json()
        assert task["agent_id"] == "power"
        assert task["timezone"] == "Asia/Shanghai"
        assert task["next_run_at"]

        listed = await client.get("/api/automation/tasks", headers=headers)
        assert listed.status_code == 200
        assert listed.json()[0]["id"] == task["id"]

        paused = await client.post(f"/api/automation/tasks/{task['id']}/pause", headers=headers)
        assert paused.status_code == 200
        assert paused.json()["enabled"] is False

        resumed = await client.post(f"/api/automation/tasks/{task['id']}/resume", headers=headers)
        assert resumed.status_code == 200
        assert resumed.json()["enabled"] is True

        deleted = await client.delete(f"/api/automation/tasks/{task['id']}", headers=headers)
        assert deleted.status_code == 204

