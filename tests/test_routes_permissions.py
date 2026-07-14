import pytest

from pathlib import Path

from httpx import AsyncClient, ASGITransport



from lc_agent.server.app import create_app

from lc_agent.core.permissions import PermissionsService

from lc_agent.core.engine import AgentEngine

from lc_agent.db.engine import init_db, reset_engine

from tests.conftest import setup_test_auth





@pytest.fixture

async def client_and_headers(tmp_path):

    reset_engine()

    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

    await init_db(db_url)



    config = {

        "provider": {},

        "agent": {"default_model": "gpt-4", "system_prompt": "Test"},

        "database": {"url": db_url, "checkpoint_path": ":memory:"},

        "permissions": {"path": str(tmp_path / "permissions.jsonc")},

    }

    app = create_app(config)

    engine = AgentEngine(config)

    app.state.engine = engine

    app.state.permissions = PermissionsService(

        permissions_path=Path(config["permissions"]["path"])

    )

    headers = await setup_test_auth(app, db_url)



    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as c:

        yield c, headers



    reset_engine()





@pytest.mark.anyio

async def test_get_permissions_empty(client_and_headers):

    client, headers = client_and_headers

    resp = await client.get("/api/permissions", headers=headers)

    assert resp.status_code == 200

    data = resp.json()

    assert data["tool_allowlist"] == []





@pytest.mark.anyio

async def test_allow_tool(client_and_headers):

    client, headers = client_and_headers

    resp = await client.post("/api/permissions/allow", json={"tool_name": "web_search"}, headers=headers)

    assert resp.status_code == 200

    assert "web_search" in resp.json()["tool_allowlist"]





@pytest.mark.anyio

async def test_remove_tool(client_and_headers):

    client, headers = client_and_headers

    await client.post("/api/permissions/allow", json={"tool_name": "web_search"}, headers=headers)

    resp = await client.post("/api/permissions/remove", json={"tool_name": "web_search"}, headers=headers)

    assert resp.status_code == 200

    assert "web_search" not in resp.json()["tool_allowlist"]





@pytest.mark.anyio

async def test_put_permissions(client_and_headers):

    client, headers = client_and_headers

    resp = await client.put("/api/permissions", json={"tool_allowlist": ["a", "b"]}, headers=headers)

    assert resp.status_code == 200

    assert sorted(resp.json()["tool_allowlist"]) == ["a", "b"]

