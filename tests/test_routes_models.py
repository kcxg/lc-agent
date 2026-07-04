import pytest
from httpx import ASGITransport, AsyncClient
from starlette.routing import Mount

from lc_agent.app import LcAgentApp
from lc_agent.db.engine import init_db, reset_engine
from lc_agent.server.routes.models import router as models_router
from lc_agent.tools.registry import ToolRegistry
from tests.conftest import setup_test_auth


@pytest.fixture(autouse=True)
def reset_registry():
    ToolRegistry._global_tools = {}
    ToolRegistry._group_descriptions = {}
    ToolRegistry._instance = None
    yield
    ToolRegistry._global_tools = {}
    ToolRegistry._group_descriptions = {}
    ToolRegistry._instance = None


@pytest.fixture
async def app_with_models(tmp_path):
    reset_engine()
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    await init_db(db_url)

    config = {
        "provider": {
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "api_key": "sk-test",
                "models": [
                    {"id": "gpt-4", "context_limit": 128000},
                    {"id": "gpt-3.5-turbo", "context_limit": 16000},
                ],
            },
            "deepseek": {
                "base_url": "https://api.deepseek.com/v1",
                "api_key": "sk-ds",
                "models": [
                    {"id": "deepseek-chat", "context_limit": 64000},
                ],
            },
        },
        "agent": {"default_model": "gpt-4", "system_prompt": "Test"},
        "database": {"url": db_url, "checkpoint_path": ":memory:"},
    }
    app_instance = LcAgentApp(config)
    headers = await setup_test_auth(app_instance.fastapi_app, db_url)
    # Register before StaticFiles mount so /api/models is reachable in tests
    routes = app_instance.fastapi_app.router.routes
    mounts = [r for r in routes if isinstance(r, Mount)]
    app_instance.fastapi_app.router.routes = [r for r in routes if not isinstance(r, Mount)]
    app_instance.fastapi_app.include_router(models_router, prefix="/api")
    app_instance.fastapi_app.router.routes.extend(mounts)
    yield app_instance, headers
    reset_engine()


@pytest.mark.asyncio
async def test_get_models(app_with_models):
    app, headers = app_with_models
    transport = ASGITransport(app=app.fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/models", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        ids = [m["id"] for m in data]
        assert "gpt-4" in ids
        assert "deepseek-chat" in ids
        gpt4 = next(m for m in data if m["id"] == "gpt-4")
        assert gpt4["provider"] == "openai"
        assert gpt4["context_limit"] == 128000
