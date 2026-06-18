import pytest
from httpx import ASGITransport, AsyncClient

from lc_agent.app import LcAgentApp
from lc_agent.db.engine import init_db, reset_engine
from lc_agent.tools.registry import ToolRegistry


@pytest.fixture(autouse=True)
async def setup():
    ToolRegistry._global_tools = {}
    ToolRegistry._group_descriptions = {}
    ToolRegistry._instance = None
    reset_engine()
    await init_db("sqlite+aiosqlite:///:memory:")
    yield
    ToolRegistry._global_tools = {}
    ToolRegistry._group_descriptions = {}
    ToolRegistry._instance = None
    reset_engine()


@pytest.fixture
def app():
    config = {
        "provider": {"openai": {"base_url": "http://fake", "api_key": "sk-fake", "models": [{"id": "gpt-4"}]}},
        "agent": {"default_model": "gpt-4", "system_prompt": "Test"},
        "database": {"url": "sqlite+aiosqlite:///:memory:", "checkpoint_path": ":memory:"},
    }
    return LcAgentApp(config)


@pytest.mark.asyncio
async def test_create_and_list_sessions(app):
    transport = ASGITransport(app=app.fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/sessions", json={"title": "Test Chat", "model": "gpt-4"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test Chat"
        assert "id" in data

        list_resp = await client.get("/api/sessions")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1


@pytest.mark.asyncio
async def test_update_session_title(app):
    transport = ASGITransport(app=app.fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/api/sessions", json={"title": "Original"})
        session_id = create_resp.json()["id"]

        update_resp = await client.put(f"/api/sessions/{session_id}", json={"title": "Updated"})
        assert update_resp.status_code == 200
        assert update_resp.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_delete_session(app):
    transport = ASGITransport(app=app.fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/api/sessions", json={"title": "To Delete"})
        session_id = create_resp.json()["id"]

        del_resp = await client.delete(f"/api/sessions/{session_id}")
        assert del_resp.status_code == 204

        list_resp = await client.get("/api/sessions")
        assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_get_session_messages_returns_persisted_ui_metadata(app):
    from lc_agent.db.engine import get_async_session
    from lc_agent.db.repository import ChatUiMessageRepository

    async with get_async_session("sqlite+aiosqlite:///:memory:") as session:
        repo = ChatUiMessageRepository(session)
        await repo.create(session_id="thread-ui", role="user", content="funboost怎么样")
        await repo.create(
            session_id="thread-ui",
            role="assistant",
            content="不错。\n<!--TOOL:0-->\n适合任务队列。",
            tool_calls=[{"name": "nbrag", "runId": "run-1", "status": "done", "result": "资料"}],
            usage={"rounds": [{"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}]},
        )

    transport = ASGITransport(app=app.fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/sessions/thread-ui/messages")

    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["role"] == "user"
    assert data[1]["role"] == "assistant"
    assert data[1]["content"] == "不错。\n<!--TOOL:0-->\n适合任务队列。"
    assert data[1]["tool_calls"][0]["runId"] == "run-1"
    assert data[1]["usage"]["rounds"][0]["total_tokens"] == 15
