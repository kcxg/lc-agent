"""lcagent_as_mcp 测试：双工具模式——过滤规则、目录、快照、MCP 端点调用、服务用户。"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from starlette.testclient import TestClient

from lc_agent.config.runtime import reset_config, set_config
from lc_agent.db.engine import reset_engine
from lc_agent.db.models import AgentPresetDB
from lc_agent.db.models_auth import User
from lc_agent.lcagent_as_mcp import mount_lcagent_as_mcp
from lc_agent.lcagent_as_mcp import runner as mcp_runner
from lc_agent.lcagent_as_mcp.service_user import ensure_service_user
from lc_agent.lcagent_as_mcp.tool_builder import (
    INVOKE_TOOL_NAME,
    LIST_TOOL_NAME,
    build_agent_directory,
    build_tools,
    list_exposable_presets,
    resolve_agent,
)

MCP_HEADERS = {"Accept": "application/json, text/event-stream"}


def _rpc(method, id_=1, params=None):
    body = {"jsonrpc": "2.0", "id": id_, "method": method}
    if params is not None:
        body["params"] = params
    return body


@pytest_asyncio.fixture
async def mcp_env(tmp_path):
    """带 5 个不同暴露条件的 preset 的 app + db。"""
    import lc_agent.db.models  # noqa: F401 — 注册全部表
    from lc_agent.server.app import create_app

    reset_engine()
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'lcagent_mcp_test.db'}"
    set_config({"database": {"url": db_url}})
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        s.add(
            AgentPresetDB(
                id="p-search",
                name="search",
                display_name="搜索",
                can_be_subagent=True,
                can_be_mcp=True,
                allowed_tool_groups=["file_read"],
                default_delegation_description="联网搜索资料",
            )
        )
        s.add(
            AgentPresetDB(
                id="p-coder",
                name="coder",
                can_be_subagent=True,
                can_be_mcp=True,
                allowed_tool_groups=["file_write", "command"],
            )
        )
        s.add(
            AgentPresetDB(
                id="p-all",
                name="alltools",
                can_be_subagent=True,
                can_be_mcp=False,  # 未勾 MCP 即使工具组不限也不暴露
                allowed_tool_groups=None,  # None = 全部组
            )
        )
        s.add(
            AgentPresetDB(
                id="p-internal",
                name="internal",
                can_be_subagent=False,
                can_be_mcp=False,
                allowed_tool_groups=["file_read"],
            )
        )
        s.add(
            AgentPresetDB(
                id="p-cn",
                name="chinese_retrieval",
                can_be_subagent=False,  # 仅勾 MCP、不勾内部委派，照样对外暴露
                can_be_mcp=True,
                allowed_tool_groups=[],
                default_delegation_description="中文知识库检索",
            )
        )
        await s.commit()

    app = create_app(
        config={"database": {"url": db_url}, "lcagent_as_mcp": {"enabled": True}}
    )

    class FakeEngine:
        pass

    assert mount_lcagent_as_mcp(app, FakeEngine()) is True
    yield app, db_url
    await engine.dispose()
    reset_engine()
    reset_config()


# ---------- 单元：暴露过滤（安全闸） ----------


@pytest.mark.asyncio
async def test_exposable_filtering(mcp_env):
    _, db_url = mcp_env
    eligible = await list_exposable_presets()
    ids = {p.id for p in eligible}
    # 唯一条件是 can_be_mcp：coder 含危险组照样暴露，alltools/internal 因未勾 MCP 不暴露
    assert ids == {"p-search", "p-coder", "p-cn"}


@pytest.mark.asyncio
async def test_build_tools_fixed_two(mcp_env):
    """工具数固定为 2，不随 agent 数增长。"""
    _, db_url = mcp_env
    tools = await build_tools()
    names = [t.name for t in tools]
    assert names == [LIST_TOOL_NAME, INVOKE_TOOL_NAME]


@pytest.mark.asyncio
async def test_invoke_description_contains_snapshot(mcp_env):
    """invoke 工具描述里嵌入 agent 快照与 prompt 指南。"""
    _, db_url = mcp_env
    tools = await build_tools()
    invoke = next(t for t in tools if t.name == INVOKE_TOOL_NAME)
    assert "<agents>" in invoke.description
    assert "<agent_name>search</agent_name>" in invoke.description
    assert "<delegation_description>联网搜索资料</delegation_description>" in invoke.description
    assert "<agent_name>chinese_retrieval</agent_name>" in invoke.description
    assert "<agent_name>coder</agent_name>" in invoke.description  # 勾了 MCP 就进快照，不查工具组
    assert "<agent_name>alltools</agent_name>" not in invoke.description  # 未勾 MCP 的不进快照
    assert "<agent_name>internal</agent_name>" not in invoke.description
    assert "prompt 写作要求" in invoke.description
    assert "\n\n" in invoke.description  # 段落间用空行分隔，保证换行可读
    # inputSchema：agent_name + prompt 都必填
    assert set(invoke.inputSchema["required"]) == {"agent_name", "prompt"}
    assert "agent_name" in invoke.inputSchema["properties"]


@pytest.mark.asyncio
async def test_directory_and_resolve(mcp_env):
    _, db_url = mcp_env
    presets = await list_exposable_presets()
    directory = build_agent_directory(presets)
    assert "<agent_name>search</agent_name>" in directory
    assert "<delegation_description>联网搜索资料</delegation_description>" in directory
    assert "<agent_name>chinese_retrieval</agent_name>" in directory
    assert "<delegation_description>中文知识库检索</delegation_description>" in directory

    assert resolve_agent(presets, "search").id == "p-search"
    assert resolve_agent(presets, "chinese_retrieval").id == "p-cn"
    assert resolve_agent(presets, "not_exist") is None


def test_agent_preset_name_has_unique_constraint():
    """name 是目录与 invoke 的定位键，数据库必须拒绝重名。"""
    table = AgentPresetDB.__table__
    assert any(
        constraint.columns.keys() == ["name"]
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    )


def test_directory_empty():
    assert build_agent_directory([]) == "<agents />"
    assert resolve_agent([], "any") is None


def test_delegation_description_fallback():
    preset = AgentPresetDB(
        id="x", name="alpha", display_name="甲", can_be_subagent=True
    )
    assert "甲" in build_agent_directory([preset])


# ---------- 集成：MCP 端点 ----------


def test_mcp_handshake_and_tools(mcp_env):
    app, _ = mcp_env
    with TestClient(app) as client:
        init = client.post("/mcp", json=_rpc("initialize", 1, {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "0"},
        }), headers=MCP_HEADERS)
        assert init.status_code == 200
        assert init.json()["result"]["serverInfo"]["name"] == "lc-agent"

        listing = client.post("/mcp", json=_rpc("tools/list", 2), headers=MCP_HEADERS)
        assert listing.status_code == 200
        tools = listing.json()["result"]["tools"]
        assert [t["name"] for t in tools] == [LIST_TOOL_NAME, INVOKE_TOOL_NAME]


def test_mcp_list_tool_returns_directory(mcp_env):
    app, _ = mcp_env
    with TestClient(app) as client:
        call = client.post("/mcp", json=_rpc("tools/call", 1, {
            "name": LIST_TOOL_NAME,
            "arguments": {},
        }), headers=MCP_HEADERS)
        assert call.status_code == 200
        text = call.json()["result"]["content"][0]["text"]
        assert "search" in text
        assert "联网搜索资料" in text
        assert "coder" in text  # 危险工具组不再过滤，勾了 MCP 就出现在目录里
        assert "alltools" not in text  # 未勾 MCP 的不出现在目录里


def test_mcp_invoke_tool(mcp_env, monkeypatch):
    app, db_url = mcp_env
    captured = {}

    async def fake_run(engine, preset_id, prompt):
        captured["preset_id"] = preset_id
        captured["prompt"] = prompt
        return "最终结果文本", None

    monkeypatch.setattr(mcp_runner, "run_agent_once", fake_run)

    with TestClient(app) as client:
        call = client.post("/mcp", json=_rpc("tools/call", 1, {
            "name": INVOKE_TOOL_NAME,
            "arguments": {
                "agent_name": "search",
                "prompt": "帮我搜下 langgraph 最新版本",
            },
        }), headers=MCP_HEADERS)
        assert call.status_code == 200
        assert call.json()["result"]["content"][0]["text"] == "最终结果文本"
        assert captured["preset_id"] == "p-search"
        assert "langgraph" in captured["prompt"]


def test_mcp_invoke_directory_key_without_description(mcp_env, monkeypatch):
    """按目录里的 agent 名调用成功（委派描述为空时兜底显示名不影响调用）。"""
    app, db_url = mcp_env
    captured = {}

    async def fake_run(engine, preset_id, prompt):
        captured["preset_id"] = preset_id
        return "ok", None

    monkeypatch.setattr(mcp_runner, "run_agent_once", fake_run)

    with TestClient(app) as client:
        call = client.post("/mcp", json=_rpc("tools/call", 1, {
            "name": INVOKE_TOOL_NAME,
            "arguments": {"agent_name": "chinese_retrieval", "prompt": "查一下"},
        }), headers=MCP_HEADERS)
        assert call.status_code == 200
        assert call.json()["result"]["content"][0]["text"] == "ok"
        assert captured["preset_id"] == "p-cn"


def test_mcp_invoke_unknown_agent_error_carries_directory(mcp_env):
    """报错 + 最新目录：一次失败调用顺便完成发现。"""
    app, _ = mcp_env
    with TestClient(app) as client:
        call = client.post("/mcp", json=_rpc("tools/call", 1, {
            "name": INVOKE_TOOL_NAME,
            "arguments": {"agent_name": "not_exist", "prompt": "x"},
        }), headers=MCP_HEADERS)
        assert call.status_code == 200
        text = call.json()["result"]["content"][0]["text"]
        assert "不存在" in text
        assert "search" in text  # 错误信息里带最新目录
        assert "联网搜索资料" in text


def test_mcp_invoke_blocked_agent_not_resolvable(mcp_env):
    """未勾 MCP 的 agent 名字走"不存在"报错。"""
    app, _ = mcp_env
    with TestClient(app) as client:
        call = client.post("/mcp", json=_rpc("tools/call", 1, {
            "name": INVOKE_TOOL_NAME,
            "arguments": {"agent_name": "internal", "prompt": "x"},
        }), headers=MCP_HEADERS)
        assert call.status_code == 200
        text = call.json()["result"]["content"][0]["text"]
        assert "不存在" in text
        # 目录部分不出现 internal（只有报错头部的「internal」里出现）
        assert "internal" not in text.split("当前可用 agent：", 1)[1]


def test_mcp_invoke_missing_params(mcp_env):
    app, _ = mcp_env
    with TestClient(app) as client:
        call = client.post("/mcp", json=_rpc("tools/call", 1, {
            "name": INVOKE_TOOL_NAME,
            "arguments": {"prompt": "缺名字"},
        }), headers=MCP_HEADERS)
        assert call.status_code == 200
        assert "agent_name" in call.json()["result"]["content"][0]["text"]

        call2 = client.post("/mcp", json=_rpc("tools/call", 2, {
            "name": INVOKE_TOOL_NAME,
            "arguments": {"agent_name": "search"},
        }), headers=MCP_HEADERS)
        assert call2.status_code == 200
        assert "prompt" in call2.json()["result"]["content"][0]["text"]


def test_mcp_unknown_tool(mcp_env):
    app, _ = mcp_env
    with TestClient(app) as client:
        call = client.post("/mcp", json=_rpc("tools/call", 1, {
            "name": "lcagent__not_exist",
            "arguments": {"prompt": "x"},
        }), headers=MCP_HEADERS)
        assert call.status_code == 200
        assert "未知工具" in call.json()["result"]["content"][0]["text"]


def test_disabled_by_default(tmp_path):
    """未显式配置 enabled=true 时不挂载端点（本期无鉴权，必须显式开启）。"""
    import lc_agent.db.models  # noqa: F401
    from lc_agent.server.app import create_app

    app = create_app(config={"database": {"url": f"sqlite+aiosqlite:///{tmp_path / 'off.db'}"}})
    assert mount_lcagent_as_mcp(app, object()) is False
    client = TestClient(app)
    assert client.post("/mcp", json=_rpc("tools/list", 1), headers=MCP_HEADERS).status_code == 404


# ---------- 服务用户 ----------


@pytest.mark.asyncio
async def test_ensure_service_user(tmp_path):
    import lc_agent.db.models  # noqa: F401
    from lc_agent.lcagent_as_mcp.service_user import service_username

    db_url = f"sqlite+aiosqlite:///{tmp_path / 'svc.db'}"
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as s:
        first = await ensure_service_user(s)
        assert first.username == service_username()
        assert first.role == "user"  # 绝不能是 admin

    async with session_factory() as s:
        again = await ensure_service_user(s)
        assert again.id == first.id  # 幂等，不重复创建

    async with session_factory() as s:
        count = len((await s.execute(__import__("sqlalchemy").select(User))).scalars().all())
        assert count == 1

    await engine.dispose()
