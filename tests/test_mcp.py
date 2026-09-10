import asyncio

import pytest

from lc_agent.config.utils import DEFAULT_MCP_TOOL_TIMEOUT
from lc_agent.mcp.manager import McpManager, McpServerStatus, resolve_tool_timeout


def test_mcp_manager_init():
    config = {
        "filesystem": {"command": "npx", "args": ["-y", "server-fs"]},
        "github": {"command": "npx", "args": ["-y", "server-github"]},
    }
    manager = McpManager(config)
    assert len(manager.servers) == 2
    assert manager.get_server("filesystem") is not None
    assert manager.get_server("filesystem").status == "disconnected"


def test_mcp_manager_empty():
    manager = McpManager({})
    assert len(manager.servers) == 0


def test_mcp_manager_infers_http_type_when_url_present():
    manager = McpManager({"remote": {"url": "http://localhost:3000/mcp"}})
    server = manager.get_server("remote")
    assert server is not None
    assert server.type == "http"


@pytest.mark.asyncio
async def test_mcp_manager_connects_url_only_config_as_http(monkeypatch):
    manager = McpManager({"remote": {"url": "http://localhost:3000/mcp"}})
    calls = []

    async def fake_http(name, conf):
        calls.append((name, conf))
        manager._servers[name].status = "connected"

    async def fail_stdio(name, conf):
        raise AssertionError("url-only MCP config should not use stdio")

    monkeypatch.setattr(manager, "_connect_http_persistent", fake_http)
    monkeypatch.setattr(manager, "_connect_stdio_persistent", fail_stdio)

    await manager.connect_all()

    assert calls == [("remote", {"url": "http://localhost:3000/mcp"})]
    assert manager.get_server("remote").status == "connected"


def test_mcp_server_status_fields():
    status = McpServerStatus(name="test", command="echo")
    assert status.status == "disconnected"
    assert status.tools == []
    assert status.error is None


def test_mcp_manager_has_tool_schemas():
    """After connect, servers should have tool_schemas."""
    config = {"test": {"command": "echo"}}
    manager = McpManager(config)
    # Before connect, tool_schemas should be empty
    assert manager.get_server("test").tool_schemas == []


def test_mcp_server_status_has_tool_schemas():
    status = McpServerStatus(name="x", command="y")
    assert hasattr(status, 'tool_schemas')
    assert status.tool_schemas == []


@pytest.mark.asyncio
async def test_mcp_manager_registers_tools_after_connect():
    """After connect, tools should be available via get_langchain_tools."""
    config = {}
    manager = McpManager(config)
    # With empty config, should return empty
    tools = manager.get_langchain_tools()
    assert tools == []


@pytest.mark.asyncio
async def test_refresh_server_reconnects_and_replaces_tool_schemas(monkeypatch):
    manager = McpManager({"remote": {"type": "http", "url": "http://example.test/mcp"}})
    server = manager.get_server("remote")
    assert server is not None
    server.status = "connected"
    server.tools = ["old_tool"]
    server.tool_schemas = [{"name": "old_tool", "description": "old", "input_schema": {}}]
    manager._sessions["remote"] = object()
    calls = []

    async def fake_cleanup(name):
        calls.append(("cleanup", name))
        manager._sessions.pop(name, None)

    async def fake_connect(name, conf, **kwargs):
        calls.append(("connect", name, conf, server.tools, server.tool_schemas))
        manager._sessions[name] = object()
        server.status = "connected"
        server.tools = ["new_tool"]
        server.tool_schemas = [{"name": "new_tool", "description": "new", "input_schema": {"q": "string"}}]

    monkeypatch.setattr(manager, "_cleanup_server", fake_cleanup)
    monkeypatch.setattr(manager, "_connect_server", fake_connect)

    refreshed = await manager.refresh_server("remote")

    assert refreshed is server
    assert calls == [
        ("cleanup", "remote"),
        (
            "connect",
            "remote",
            {"type": "http", "url": "http://example.test/mcp"},
            ["old_tool"],
            [{"name": "old_tool", "description": "old", "input_schema": {}}],
        ),
    ]
    assert server.tools == ["new_tool"]
    assert server.tool_schemas[0]["description"] == "new"


@pytest.mark.asyncio
async def test_refresh_server_keeps_previous_schemas_until_reconnected(monkeypatch):
    state_changes = []
    manager = McpManager(
        {"remote": {"type": "http", "url": "http://example.test/mcp"}},
        on_state_change=lambda: state_changes.append("changed"),
    )
    server = manager.get_server("remote")
    assert server is not None
    server.status = "connected"
    server.tools = ["old_tool"]
    server.tool_schemas = [{"name": "old_tool", "description": "old", "input_schema": {}}]
    reconnect_started = asyncio.Event()
    finish_reconnect = asyncio.Event()

    async def fake_cleanup(name):
        manager._sessions.pop(name, None)

    async def fake_connect(name, conf, **kwargs):
        assert kwargs == {"notify_connecting": False}
        reconnect_started.set()
        await finish_reconnect.wait()
        manager._sessions[name] = object()
        manager._extract_tools(name, type("Result", (), {"tools": []})())

    monkeypatch.setattr(manager, "_cleanup_server", fake_cleanup)
    monkeypatch.setattr(manager, "_connect_server", fake_connect)

    refresh_task = asyncio.create_task(manager.refresh_server("remote"))
    await reconnect_started.wait()

    assert server.status == "connected"
    assert server.tools == ["old_tool"]
    assert server.tool_schemas[0]["description"] == "old"
    assert state_changes == []

    finish_reconnect.set()
    await refresh_task
    assert state_changes == ["changed"]


class _TextContent:
    def __init__(self, text: str):
        self.text = text


class _ToolResult:
    def __init__(self, text: str):
        self.content = [_TextContent(text)]


class _FailingSession:
    async def call_tool(self, tool_name, arguments):
        raise ConnectionError("connection dropped")


class _SuccessfulSession:
    def __init__(self):
        self.calls = []

    async def call_tool(self, tool_name, arguments):
        self.calls.append((tool_name, arguments))
        return _ToolResult("ok after reconnect")


@pytest.mark.asyncio
async def test_call_tool_reconnects_once_and_retries_after_session_failure(monkeypatch):
    manager = McpManager({"http_test": {"type": "http", "url": "http://example.test/mcp"}})
    manager._servers["http_test"].status = "connected"
    manager._sessions["http_test"] = _FailingSession()

    replacement_session = _SuccessfulSession()
    reconnects = []

    async def fake_connect_server(name, conf, **kwargs):
        reconnects.append((name, conf))
        manager._sessions[name] = replacement_session
        manager._servers[name].status = "connected"
        manager._servers[name].error = None

    monkeypatch.setattr(manager, "_connect_server", fake_connect_server)

    result = await manager.call_tool("http_test", "ping", {"value": 1})

    assert result == "ok after reconnect"
    assert reconnects == [("http_test", {"type": "http", "url": "http://example.test/mcp"})]
    assert replacement_session.calls == [("ping", {"value": 1})]
    assert manager.get_server("http_test").status == "connected"
    assert manager.get_server("http_test").error is None


@pytest.mark.asyncio
async def test_call_tool_reports_reconnect_failure_and_clears_stale_session(monkeypatch):
    manager = McpManager({"http_test": {"type": "http", "url": "http://example.test/mcp"}})
    manager._servers["http_test"].status = "connected"
    manager._sessions["http_test"] = _FailingSession()

    async def fake_connect_server(name, conf, **kwargs):
        manager._servers[name].status = "error"
        manager._servers[name].error = "server still down"

    monkeypatch.setattr(manager, "_connect_server", fake_connect_server)

    result = await manager.call_tool("http_test", "ping", {})

    assert result == "MCP server 'http_test' reconnect failed: server still down"
    assert "http_test" not in manager._sessions
    assert manager.get_server("http_test").status == "error"
    assert manager.get_server("http_test").error == "server still down"


@pytest.mark.asyncio
async def test_call_tool_reports_reconnect_failure_when_no_session_exists(monkeypatch):
    manager = McpManager({"http_test": {"type": "http", "url": "http://example.test/mcp"}})
    manager._servers["http_test"].status = "error"
    manager._servers["http_test"].error = "previous failure"

    async def fake_connect_server(name, conf, **kwargs):
        manager._servers[name].status = "error"
        manager._servers[name].error = "server still down"

    monkeypatch.setattr(manager, "_connect_server", fake_connect_server)

    result = await manager.call_tool("http_test", "ping", {})

    assert result == "MCP server 'http_test' reconnect failed: server still down"
    assert "http_test" not in manager._sessions
    assert manager.get_server("http_test").status == "error"


@pytest.mark.asyncio
async def test_call_tool_does_not_reconnect_disabled_server(monkeypatch):
    manager = McpManager({"http_test": {"type": "http", "url": "http://example.test/mcp"}})
    server = manager.get_server("http_test")
    server.enabled = False
    server.status = "disabled"
    manager._sessions["http_test"] = _FailingSession()
    reconnects = []

    async def fake_connect_server(name, conf, **kwargs):
        reconnects.append((name, conf))

    monkeypatch.setattr(manager, "_connect_server", fake_connect_server)

    result = await manager.call_tool("http_test", "ping", {})

    assert result == "MCP server 'http_test' is disabled"
    assert reconnects == []
    assert manager.get_server("http_test").status == "disabled"


def test_lc_agent_app_wires_mcp_state_changes_to_generation():
    from lc_agent.app import LcAgentApp

    config = {
        "provider": {"openai": {"base_url": "http://fake", "api_key": "sk-fake", "models": [{"model_id": "gpt-4", "raw_model_id": "gpt-4"}]}},
        "agent": {"default_model": "gpt-4", "system_prompt": "Test"},
        # Key must be `mcpServers`: that is what LcAgentApp reads, and a
        # misspelled key silently registers zero servers (no callback fires).
        "mcpServers": {"http_test": {"type": "http", "url": "http://example.test/mcp"}},
    }
    app = LcAgentApp(config)
    gen_before = app.engine._mcp_generation

    app.mcp_manager._set_server_error("http_test", "connection dropped")

    assert app.engine._mcp_generation == gen_before + 1


class _TornDownSession:
    """Simulates a session torn down mid-call: raises bare CancelledError."""

    def __init__(self):
        self.calls = []

    async def call_tool(self, tool_name, arguments):
        self.calls.append((tool_name, arguments))
        raise asyncio.CancelledError()


class _HangingSession:
    """Never resolves; used to test genuine outer cancellation."""

    def __init__(self):
        self.started = asyncio.Event()

    async def call_tool(self, tool_name, arguments):
        self.started.set()
        await asyncio.Event().wait()
        raise AssertionError("unreachable")


@pytest.mark.asyncio
async def test_call_tool_parallel_callers_share_one_reconnect(monkeypatch):
    """Two concurrent callers, first fails: second must run on the new session.

    Regression test for the stale-session TOCTOU: session lookup used to
    happen before lock acquisition while reconnect tore the session down,
    so the waiter invoked a dead session (bare CancelledError → tools-node
    NodeCancelledError). Exactly one reconnect may happen.
    """
    manager = McpManager({"http_test": {"type": "http", "url": "http://example.test/mcp"}})
    manager._servers["http_test"].status = "connected"

    first_calls = []

    class _FirstFailingSession:
        async def call_tool(self, tool_name, arguments):
            first_calls.append((tool_name, arguments))
            raise ConnectionError("boom")

    manager._sessions["http_test"] = _FirstFailingSession()
    replacement = _SuccessfulSession()
    reconnects = []

    async def fake_connect_server(name, conf, **kwargs):
        reconnects.append(name)
        manager._sessions[name] = replacement
        manager._servers[name].status = "connected"
        manager._servers[name].error = None

    monkeypatch.setattr(manager, "_connect_server", fake_connect_server)

    results = await asyncio.gather(
        manager.call_tool("http_test", "ping", {"n": 1}),
        manager.call_tool("http_test", "ping", {"n": 2}),
    )

    assert results == ["ok after reconnect", "ok after reconnect"]
    assert reconnects == ["http_test"]
    assert len(first_calls) == 1  # only the pre-reconnect caller saw the dead session
    assert replacement.calls == [("ping", {"n": 1}), ("ping", {"n": 2})]


@pytest.mark.asyncio
async def test_call_tool_once_converts_inner_cancel_to_readable_error():
    """Bare CancelledError from a torn-down session must not escape.

    Genuine outer cancellation (our own task cancelled) still propagates;
    anything else becomes a RuntimeError so callers see text, never a
    tools-node NodeCancelledError.
    """
    manager = McpManager({"http_test": {"type": "http", "url": "http://example.test/mcp"}})
    manager._sessions["http_test"] = _TornDownSession()

    with pytest.raises(RuntimeError, match="interrupted"):
        await manager._call_tool_once("http_test", "ping", {})


@pytest.mark.asyncio
async def test_call_tool_recovers_from_torn_down_session(monkeypatch):
    """End-to-end of the reported incident: torn session → readable retry."""
    manager = McpManager({"http_test": {"type": "http", "url": "http://example.test/mcp"}})
    manager._servers["http_test"].status = "connected"
    manager._sessions["http_test"] = _TornDownSession()

    replacement = _SuccessfulSession()

    async def fake_connect_server(name, conf, **kwargs):
        manager._sessions[name] = replacement
        manager._servers[name].status = "connected"
        manager._servers[name].error = None

    monkeypatch.setattr(manager, "_connect_server", fake_connect_server)

    result = await manager.call_tool("http_test", "ping", {})
    assert result == "ok after reconnect"
    assert replacement.calls == [("ping", {})]


@pytest.mark.asyncio
async def test_call_tool_propagates_genuine_outer_cancellation():
    """User-stop (outer task.cancel()) must not be swallowed or converted."""
    manager = McpManager({"http_test": {"type": "http", "url": "http://example.test/mcp"}})
    manager._servers["http_test"].status = "connected"
    hanging = _HangingSession()
    manager._sessions["http_test"] = hanging

    task = asyncio.ensure_future(manager.call_tool("http_test", "ping", {}))
    await hanging.started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


def test_tool_timeout_defaults_to_300():
    manager = McpManager({})
    assert manager._tool_timeout == float(DEFAULT_MCP_TOOL_TIMEOUT) == 300.0


def test_tool_timeout_custom_value():
    manager = McpManager({}, tool_timeout=60)
    assert manager._tool_timeout == 60.0


@pytest.mark.parametrize("bad_value", [0, -5, "abc", None, ""])
def test_tool_timeout_invalid_falls_back_to_default(bad_value):
    assert resolve_tool_timeout(bad_value) == float(DEFAULT_MCP_TOOL_TIMEOUT)
    manager = McpManager({}, tool_timeout=bad_value)
    assert manager._tool_timeout == float(DEFAULT_MCP_TOOL_TIMEOUT)


@pytest.mark.asyncio
async def test_call_tool_timeout_uses_configured_value(monkeypatch):
    """_invoke_session 必须用配置的超时，而不是写死的 60s。"""
    manager = McpManager(
        {"http_test": {"type": "http", "url": "http://example.test/mcp"}},
        tool_timeout=5,
    )
    manager._servers["http_test"].status = "connected"

    seen_timeouts = []
    real_wait_for = asyncio.wait_for

    async def spy_wait_for(awaitable, *, timeout=None):
        seen_timeouts.append(timeout)
        awaitable.close()
        raise asyncio.TimeoutError()

    async def fake_reconnect(name):
        return False

    monkeypatch.setattr(asyncio, "wait_for", spy_wait_for)
    monkeypatch.setattr(manager, "_reconnect_server", fake_reconnect)

    class _NeverSession:
        async def call_tool(self, tool_name, arguments):
            raise AssertionError("should be wrapped by wait_for spy")

    manager._sessions["http_test"] = _NeverSession()
    result = await manager.call_tool("http_test", "ping", {})

    assert seen_timeouts == [5]
    assert "timed out after 5s" in result


class _SlowSession:
    """Simulates a slow-but-healthy server: tracks max concurrency."""

    def __init__(self, delay: float = 0.2):
        self.delay = delay
        self.in_flight = 0
        self.max_in_flight = 0

    async def call_tool(self, tool_name, arguments):
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(self.delay)
            return _ToolResult(f"ok:{tool_name}")
        finally:
            self.in_flight -= 1


@pytest.mark.asyncio
async def test_call_tool_same_server_runs_in_parallel():
    """同 server 的并发调用必须并行，不再串行排队。

    Regression test for the 24.9s + 41.8s incident: two parallel
    invoke_lca_agent calls on one server were serialized by the old
    exclusive call lock; now they overlap (2 x 0.2s ≈ 0.2s, not 0.4s).
    """
    manager = McpManager({"http_test": {"type": "http", "url": "http://example.test/mcp"}})
    manager._servers["http_test"].status = "connected"
    session = _SlowSession(delay=0.2)
    manager._sessions["http_test"] = session

    start = asyncio.get_running_loop().time()
    results = await asyncio.gather(
        manager.call_tool("http_test", "a", {}),
        manager.call_tool("http_test", "b", {}),
    )
    elapsed = asyncio.get_running_loop().time() - start

    assert sorted(results) == ["ok:a", "ok:b"]
    assert session.max_in_flight == 2
    assert elapsed < 0.35


@pytest.mark.asyncio
async def test_call_tool_reconnect_drains_inflight_calls(monkeypatch):
    """失败触发的重连（独占）必须等 in-flight 调用完成后再 teardown。

    slow 调用占着共享侧 0.2s；fail 调用立即失败 → 走独占重连。
    若重连不等排空就 teardown，slow 的 session 会被换掉导致它报错；
    正确行为：slow 在旧 session 上成功，fail 在新 session 上重试成功。
    """
    manager = McpManager({"http_test": {"type": "http", "url": "http://example.test/mcp"}})
    manager._servers["http_test"].status = "connected"

    slow_done = asyncio.Event()
    reconnect_started = asyncio.Event()

    class _MixedSession:
        async def call_tool(self, tool_name, arguments):
            if tool_name == "slow":
                await asyncio.sleep(0.2)
                slow_done.set()
                return _ToolResult("ok:slow")
            raise ConnectionError("connection dropped")

    manager._sessions["http_test"] = _MixedSession()
    replacement = _SuccessfulSession()

    async def fake_connect_server(name, conf, **kwargs):
        # 重连拿的是独占侧：此时 in-flight 的 slow 必须已完成，
        # 否则就是 teardown 撕了正在跑的调用。
        assert slow_done.is_set(), "reconnect tore down an in-flight call"
        reconnect_started.set()
        manager._sessions[name] = replacement
        manager._servers[name].status = "connected"
        manager._servers[name].error = None

    monkeypatch.setattr(manager, "_connect_server", fake_connect_server)

    slow_result, fail_result = await asyncio.gather(
        manager.call_tool("http_test", "slow", {}),
        manager.call_tool("http_test", "fail", {}),
    )

    assert slow_result == "ok:slow"
    assert fail_result == "ok after reconnect"
    assert reconnect_started.is_set()
    assert replacement.calls == [("fail", {})]
