import pytest
from httpx import ASGITransport, AsyncClient

from lc_agent.app import LcAgentApp
from lc_agent.db.engine import init_db, reset_engine
from lc_agent.mcp.manager import McpServerStatus
from lc_agent.tools import tool, ToolRegistry
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
async def app_with_tools(tmp_path):
    reset_engine()
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    await init_db(db_url)

    @tool(group="web")
    def search_web(query: str) -> str:
        """Search the web for information."""
        return f"results for {query}"

    @tool(group="web")
    def fetch_page(url: str) -> str:
        """Fetch a webpage."""
        return f"content of {url}"

    @tool(group="filesystem")
    def read_file(path: str) -> str:
        """Read a file from disk."""
        return f"content of {path}"

    config = {
        "provider": {"openai": {"base_url": "http://fake", "api_key": "sk-fake", "models": [{"id": "gpt-4"}]}},
        "agent": {"default_model": "gpt-4", "system_prompt": "Test"},
        "database": {"url": db_url, "checkpoint_path": ":memory:"},
    }
    app = LcAgentApp(config)
    headers = await setup_test_auth(app.fastapi_app, db_url)
    yield app, headers
    reset_engine()


@pytest.mark.asyncio
async def test_get_tools(app_with_tools):
    app, headers = app_with_tools
    transport = ASGITransport(app=app.fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/tools", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        names = [t["name"] for t in data]
        assert "web__search_web" in names
        assert "filesystem__read_file" in names


@pytest.mark.asyncio
async def test_get_tool_groups(app_with_tools):
    app, headers = app_with_tools
    transport = ASGITransport(app=app.fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/tools/groups", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        group_ids = [g["id"] for g in data]
        assert "web" in group_ids
        assert "filesystem" in group_ids
        web_group = next(g for g in data if g["id"] == "web")
        assert len(web_group["tools"]) == 2


@pytest.mark.asyncio
async def test_toggle_tool_group_increments_mcp_generation(app_with_tools):
    """Toggling a tool group must invalidate cached agents by incrementing _mcp_generation."""
    app, headers = app_with_tools
    transport = ASGITransport(app=app.fastapi_app)
    engine = app.engine
    gen_before = engine._mcp_generation

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/tools/groups/web/toggle", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is False

    assert engine._mcp_generation == gen_before + 1

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/tools/groups/web/toggle", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is True

    assert engine._mcp_generation == gen_before + 2


@pytest.mark.asyncio
async def test_toggle_mcp_server_increments_mcp_generation(app_with_tools):
    """Toggling an MCP server must invalidate cached agents."""
    app, headers = app_with_tools
    engine = app.engine

    # Manually inject a fake MCP server status
    from lc_agent.mcp.manager import McpManager
    mcp_manager = McpManager({"fake_server": {"command": "echo", "enabled": True}})
    mcp_manager._servers["fake_server"].status = "connected"
    app.fastapi_app.state.mcp_manager = mcp_manager

    gen_before = engine._mcp_generation

    transport = ASGITransport(app=app.fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/mcp/fake_server/toggle", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is False

    assert engine._mcp_generation == gen_before + 1
