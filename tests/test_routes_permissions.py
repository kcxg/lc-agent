import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from lc_agent.server.app import create_app
from lc_agent.core.permissions import PermissionsService
from lc_agent.core.engine import AgentEngine


@pytest.fixture
def app_with_permissions(tmp_path):
    config = {
        "provider": {},
        "agent": {"default_model": "gpt-4", "system_prompt": "Test"},
        "database": {"url": "sqlite+aiosqlite:///:memory:", "checkpoint_path": ":memory:"},
        "permissions": {"path": str(tmp_path / "permissions.jsonc")},
    }
    app = create_app(config)
    engine = AgentEngine(config)
    app.state.engine = engine
    app.state.permissions = PermissionsService(
        permissions_path=Path(config["permissions"]["path"])
    )
    return app


@pytest.fixture
async def client(app_with_permissions):
    transport = ASGITransport(app=app_with_permissions)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_get_permissions_empty(client):
    resp = await client.get("/api/permissions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool_allowlist"] == []


@pytest.mark.anyio
async def test_allow_tool(client):
    resp = await client.post("/api/permissions/allow", json={"tool_name": "web_search"})
    assert resp.status_code == 200
    assert "web_search" in resp.json()["tool_allowlist"]


@pytest.mark.anyio
async def test_remove_tool(client):
    await client.post("/api/permissions/allow", json={"tool_name": "web_search"})
    resp = await client.post("/api/permissions/remove", json={"tool_name": "web_search"})
    assert resp.status_code == 200
    assert "web_search" not in resp.json()["tool_allowlist"]


@pytest.mark.anyio
async def test_put_permissions(client):
    resp = await client.put("/api/permissions", json={"tool_allowlist": ["a", "b"]})
    assert resp.status_code == 200
    assert sorted(resp.json()["tool_allowlist"]) == ["a", "b"]
