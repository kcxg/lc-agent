
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Callable

from lc_agent.config.utils import DEFAULT_MCP_TOOL_TIMEOUT

logger = logging.getLogger(__name__)


class _PerServerRwLock:
    """Per-server reader/writer lock (no third-party dependency).

    - ``read()``: shared — any number of concurrent ``call_tool`` invokes.
    - ``write()``: exclusive — reconnect / refresh / teardown paths.
    - Writer-preferring: once a writer is waiting, new readers queue behind
      it, so a reconnect is never starved by a steady stream of calls.
    - The object itself used as ``async with lock:`` means ``write()``
      (exclusive), keeping one-off external uses safe.
    """

    def __init__(self) -> None:
        self._cond = asyncio.Condition()
        self._readers = 0
        self._writer = False
        self._writers_waiting = 0

    async def _acquire_read(self) -> None:
        async with self._cond:
            while self._writer or self._writers_waiting > 0:
                await self._cond.wait()
            self._readers += 1

    async def _release_read(self) -> None:
        async with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()

    async def _acquire_write(self) -> None:
        async with self._cond:
            self._writers_waiting += 1
            try:
                while self._writer or self._readers > 0:
                    await self._cond.wait()
                self._writer = True
            finally:
                self._writers_waiting -= 1

    async def _release_write(self) -> None:
        async with self._cond:
            self._writer = False
            self._cond.notify_all()

    @asynccontextmanager
    async def read(self):
        await self._acquire_read()
        try:
            yield
        finally:
            await self._release_read()

    @asynccontextmanager
    async def write(self):
        await self._acquire_write()
        try:
            yield
        finally:
            await self._release_write()

    async def __aenter__(self):
        await self._acquire_write()
        return self

    async def __aexit__(self, *exc):
        await self._release_write()
        return None


def resolve_tool_timeout(value: Any) -> float:
    """解析 mcp.tool_timeout 配置值，非法值回落默认 300s。

    接受正数（int/float/数字字符串）；0、负数、非数字、None
    一律回落 DEFAULT_MCP_TOOL_TIMEOUT 并打 warning，不阻断启动。
    """
    try:
        timeout = float(value)
    except (TypeError, ValueError):
        logger.warning(
            "Invalid mcp.tool_timeout=%r, falling back to %ss",
            value, DEFAULT_MCP_TOOL_TIMEOUT,
        )
        return float(DEFAULT_MCP_TOOL_TIMEOUT)
    if timeout <= 0:
        logger.warning(
            "Invalid mcp.tool_timeout=%r (must be > 0), falling back to %ss",
            value, DEFAULT_MCP_TOOL_TIMEOUT,
        )
        return float(DEFAULT_MCP_TOOL_TIMEOUT)
    return timeout


@dataclass
class McpServerStatus:
    name: str
    type: str = "local"
    command: str = ""
    url: str = ""
    enabled: bool = True
    status: str = "disconnected"
    tools: list[str] = field(default_factory=list)
    tool_schemas: list[dict] = field(default_factory=list)
    error: str | None = None


def _resolve_server_type(conf: dict) -> str:
    server_type = conf.get("type")
    if server_type:
        return server_type
    if conf.get("url"):
        return "http"
    return "local"


class McpManager:
    """Manages persistent MCP server connections and tool invocation.

    Lock protocol (deadlock avoidance — read before touching):

    - ``_locks[name]`` (per-server reader/writer lock): concurrent
      ``call_tool`` invokes on one server hold the SHARED side, so they
      run in parallel; every path that tears a session down
      (refresh/reconnect/merge/clear/shutdown) takes the EXCLUSIVE side.
      The lock object itself is never replaced, only created once via
      ``_call_lock``.
    - ``_refresh_locks[name]``: serializes concurrent reconnects for one
      server. Acquisition order is ALWAYS call lock → refresh lock,
      never the reverse.
    - Locks are not reentrant: code running under the call lock
      (``call_tool`` → ``_reconnect_server`` → ``_refresh_server_impl``)
      must NEVER acquire the call lock again. That is why ``refresh_server``
      (public, takes the call lock) and ``_refresh_server_impl`` (assumes
      the caller already holds it) are split — routing the reconnect path
      through the public entry would self-deadlock.
    - Session identity is additionally guarded by a generation counter
      (``_generations``): every teardown/establish bumps it, so a caller
      can detect that its snapshot was replaced out from under it and
      retry on the current session instead of reconnecting redundantly.
      This is what makes parallel same-session calls safe when a
      concurrent writer swaps the session mid-flight.
    """

    def __init__(
        self,
        config: dict[str, dict],
        on_state_change: Callable[[], None] | None = None,
        tool_timeout: Any = DEFAULT_MCP_TOOL_TIMEOUT,
    ):
        self._config = config
        self._on_state_change = on_state_change
        self._tool_timeout = resolve_tool_timeout(tool_timeout)
        self._servers: dict[str, McpServerStatus] = {}
        self._sessions: dict[str, Any] = {}
        self._locks: dict[str, _PerServerRwLock] = {}
        self._refresh_locks: dict[str, asyncio.Lock] = {}
        self._generations: dict[str, int] = {}
        self._server_contexts: dict[str, tuple[Any, Any]] = {}
        self._project_server_names: set[str] = set()

        for name, conf in config.items():
            enabled = conf.get("enabled", True)
            server_type = _resolve_server_type(conf)
            command = conf.get("command", "")
            if isinstance(command, list):
                command = " ".join(command)
            self._servers[name] = McpServerStatus(
                name=name,
                type=server_type,
                command=command,
                url=conf.get("url", ""),
                enabled=enabled,
            )

    @property
    def servers(self) -> list[McpServerStatus]:
        return list(self._servers.values())

    def get_server(self, name: str) -> McpServerStatus | None:
        return self._servers.get(name)

    def _call_lock(self, name: str) -> _PerServerRwLock:
        """Return the never-replaced per-server reader/writer lock, creating it once."""
        return self._locks.setdefault(name, _PerServerRwLock())

    def _snapshot(self, name: str) -> tuple[Any | None, int]:
        """Current (session, generation) pair for stale-session comparison."""
        return self._sessions.get(name), self._generations.get(name, 0)

    def _bump_generation(self, name: str) -> None:
        self._generations[name] = self._generations.get(name, 0) + 1

    def _notify_state_change(self) -> None:
        """Notify the owner that MCP state changed without coupling to the engine."""
        if self._on_state_change is None:
            return
        try:
            self._on_state_change()
        except Exception:
            pass

    def _set_server_error(self, name: str, error: str) -> None:
        server = self._servers.get(name)
        if server is None:
            return
        server.status = "error"
        server.tools = []
        server.tool_schemas = []
        server.error = error
        self._notify_state_change()

    async def _cleanup_server(self, name: str) -> None:
        """Close and forget a single server's persistent connection.

        The per-server lock object is intentionally kept: concurrent callers
        may be waiting on it, and destroying it would orphan them onto a dead
        lock while a fresh lock guards the new session (TOCTOU).

        Callers that can run concurrently with in-flight calls must hold the
        EXCLUSIVE side around this (see ``refresh_server``/``shutdown``);
        otherwise ``__aexit__`` may run in a different task than the
        in-flight ``call_tool`` and anyio will refuse to exit its cancel
        scope ("Attempted to exit cancel scope in a different task"),
        leaking the connection.
        """
        had_session = self._sessions.pop(name, None) is not None
        contexts = self._server_contexts.pop(name, None)
        if had_session or contexts is not None:
            self._bump_generation(name)
        if contexts is None:
            return

        cm, session_cm = contexts
        try:
            await session_cm.__aexit__(None, None, None)
        except Exception:
            pass
        try:
            await cm.__aexit__(None, None, None)
        except Exception:
            pass

    async def _reconnect_server(self, name: str) -> bool:
        """Reconnect one enabled configured server after a persistent session fails.

        Must be called WITHOUT holding the call lock: it takes the EXCLUSIVE
        side itself (via ``refresh_server``), which serializes against
        in-flight shared-side ``call_tool`` invokes. Never call this from a
        context that already holds any side of the same per-server lock —
        locks are not reentrant and that would self-deadlock.
        """
        return (await self.refresh_server(name)).status == "connected"

    async def refresh_server(self, name: str) -> McpServerStatus:
        """Reconnect one configured server and refresh its tool schemas.

        Public entry: takes the EXCLUSIVE side of the per-server lock, so
        the teardown below waits for in-flight shared-side ``call_tool``
        invokes to drain (cross-task cancel-scope exit), and new invokes
        queue behind the reconnect instead of racing it.
        """
        async with self._call_lock(name):
            return await self._refresh_server_impl(name)

    async def _refresh_server_impl(self, name: str) -> McpServerStatus:
        """Reconnect internals. Assumes the caller holds the EXCLUSIVE side.

        MUST NOT acquire the per-server lock itself (locks are not
        reentrant — doing so from a locked context deadlocks). Only takes
        the refresh lock, after the call lock: the documented global order.
        """
        server = self._servers.get(name)
        conf = self._config.get(name)
        if server is None or conf is None:
            raise KeyError(f"MCP server '{name}' not found")
        if not server.enabled:
            server.status = "disabled"
            self._notify_state_change()
            return server

        refresh_lock = self._refresh_locks.setdefault(name, asyncio.Lock())
        async with refresh_lock:
            # Keep the last complete schema available until a new tools/list response succeeds.
            # This prevents an agent created during refresh from losing its MCP tools.
            await self._cleanup_server(name)
            await self._connect_server(name, conf, notify_connecting=False)
            return server

    async def refresh_all(self) -> list[McpServerStatus]:
        """Refresh every enabled MCP server in parallel."""
        tasks = [
            self.refresh_server(name)
            for name, server in self._servers.items()
            if server.enabled
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        return self.servers

    async def connect_all(self):
        """Connect to all configured MCP servers in parallel."""
        tasks = []
        for name, conf in self._config.items():
            if not conf.get("enabled", True):
                self._servers[name].status = "disabled"
                continue
            tasks.append(self._connect_server(name, conf))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def merge_project_servers(self, project_config: dict[str, dict]) -> list[str]:
        """Add project-level MCP servers (from .agents/mcp.json).

        Project servers override global servers with the same name.
        Returns list of added/updated server names.
        """
        added: list[str] = []
        for name, conf in project_config.items():
            if name in self._servers and name not in self._project_server_names:
                # Exclusive side: drain in-flight shared-side calls first.
                # Tearing the session down while another task is inside
                # session.call_tool makes anyio refuse the cross-task
                # cancel-scope exit (leaked connection).
                async with self._call_lock(name):
                    await self._cleanup_server(name)
            self._project_server_names.add(name)
            self._config[name] = conf
            server_type = _resolve_server_type(conf)
            command = conf.get("command", "")
            if isinstance(command, list):
                command = " ".join(command)
            self._servers[name] = McpServerStatus(
                name=name,
                type=server_type,
                command=command,
                url=conf.get("url", ""),
                enabled=conf.get("enabled", True),
            )
            added.append(name)

        tasks = [
            self._connect_server(n, self._config[n])
            for n in added
            if self._servers[n].enabled
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        if added:
            self._notify_state_change()
        return added

    async def clear_project_servers(self) -> None:
        """Remove all project-level MCP servers and disconnect them."""
        for name in list(self._project_server_names):
            async with self._call_lock(name):
                await self._cleanup_server(name)
            self._servers.pop(name, None)
            self._config.pop(name, None)
        if self._project_server_names:
            self._notify_state_change()
        self._project_server_names.clear()

    async def _connect_server(self, name: str, conf: dict, *, notify_connecting: bool = True):
        """Establish a persistent connection to a single MCP server."""
        server_type = _resolve_server_type(conf)
        if notify_connecting:
            self._servers[name].status = "connecting"
            self._notify_state_change()

        # HTTP/SSE servers respond quickly; stdio (npx) may need to download packages on first run.
        if server_type in ("http", "sse"):
            default_timeout = 15
        else:
            default_timeout = 90
        connect_timeout = conf.get("connect_timeout", default_timeout)

        try:
            if server_type == "sse":
                await asyncio.wait_for(
                    self._connect_sse_persistent(name, conf), timeout=connect_timeout
                )
            elif server_type == "http":
                await asyncio.wait_for(
                    self._connect_http_persistent(name, conf), timeout=connect_timeout
                )
            else:
                await asyncio.wait_for(
                    self._connect_stdio_persistent(name, conf), timeout=connect_timeout
                )
        except asyncio.TimeoutError:
            await self._cleanup_server(name)
            self._set_server_error(name, f"Connection timed out after {connect_timeout}s")
        except Exception as e:
            await self._cleanup_server(name)
            self._set_server_error(name, str(e))

    async def _connect_stdio_persistent(self, name: str, conf: dict):
        """Keep a stdio MCP server process alive."""
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        command_raw = conf.get("command", "")
        if isinstance(command_raw, list):
            cmd = command_raw[0]
            args = command_raw[1:]
        else:
            cmd = command_raw
            args = conf.get("args", [])

        env = {**os.environ, **conf.get("env", {})}
        params = StdioServerParameters(command=cmd, args=args, env=env)

        cm = stdio_client(params)
        transport = await cm.__aenter__()
        read, write = transport

        session_cm = ClientSession(read, write)
        session = await session_cm.__aenter__()
        await session.initialize()

        self._server_contexts[name] = (cm, session_cm)
        self._sessions[name] = session
        self._extract_tools(name, await session.list_tools())

    async def _connect_sse_persistent(self, name: str, conf: dict):
        """Keep an SSE MCP connection alive."""
        from mcp import ClientSession
        from mcp.client.sse import sse_client

        url = conf.get("url", "")
        if not url:
            raise ValueError(f"SSE server '{name}' requires a 'url' field")

        cm = sse_client(url=url)
        transport = await cm.__aenter__()
        read, write = transport

        session_cm = ClientSession(read, write)
        session = await session_cm.__aenter__()
        await session.initialize()

        self._server_contexts[name] = (cm, session_cm)
        self._sessions[name] = session
        self._extract_tools(name, await session.list_tools())

    async def _connect_http_persistent(self, name: str, conf: dict):
        """Keep a StreamableHTTP MCP connection alive."""
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        url = conf.get("url", "")
        if not url:
            raise ValueError(f"HTTP server '{name}' requires a 'url' field")

        cm = streamable_http_client(url=url)
        transport = await cm.__aenter__()
        read, write = transport[0], transport[1]

        session_cm = ClientSession(read, write)
        session = await session_cm.__aenter__()
        await session.initialize()

        self._server_contexts[name] = (cm, session_cm)
        self._sessions[name] = session
        self._extract_tools(name, await session.list_tools())

    def _extract_tools(self, name: str, tools_result):
        """Extract tool info from list_tools result."""
        tool_names = [t.name for t in tools_result.tools]
        tool_schemas = [
            {
                "name": t.name,
                "description": getattr(t, "description", "") or "",
                "input_schema": getattr(t, "inputSchema", {}) or {},
            }
            for t in tools_result.tools
        ]
        self._servers[name].status = "connected"
        self._servers[name].tools = tool_names
        self._servers[name].tool_schemas = tool_schemas
        self._servers[name].error = None
        self._bump_generation(name)
        self._call_lock(name)
        self._notify_state_change()

    async def _call_tool_once(self, server_name: str, tool_name: str, arguments: dict) -> str:
        """Invoke once on the current session.

        Looks the session up at call time so a concurrent reconnect cannot
        swap it out from under an in-flight call (stale-session TOCTOU).
        May be called without holding the call lock (e.g. in tests); the
        multi-step ``call_tool`` always holds it.
        """
        session = self._sessions.get(server_name)
        if session is None:
            raise RuntimeError(f"MCP server '{server_name}' not connected")
        return await self._invoke_session(session, server_name, tool_name, arguments)

    async def _invoke_session(self, session: Any, server_name: str, tool_name: str, arguments: dict) -> str:
        """Invoke once on an already-resolved session object.

        Bare CancelledError is normalized to RuntimeError: our own
        tool timeout surfaces as TimeoutError, so a bare CancelledError
        here means an inner MCP scope was torn down mid-call — except
        when the outer task itself is being cancelled (user stop), which
        must keep propagating as CancelledError.
        """
        try:
            result = await asyncio.wait_for(
                session.call_tool(tool_name, arguments),
                timeout=self._tool_timeout,
            )
        except asyncio.CancelledError:
            current = asyncio.current_task()
            if current is not None and current.cancelling() > 0:
                raise
            raise RuntimeError(
                f"MCP tool '{tool_name}' was interrupted mid-call "
                f"(connection to '{server_name}' was torn down)"
            ) from None

        parts = []
        for content in result.content:
            if hasattr(content, "text"):
                parts.append(content.text)
            else:
                parts.append(str(content))
        return "\n".join(parts) if parts else "(empty result)"

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> str:
        """Invoke a tool on a connected MCP server, reconnecting once if needed.

        Concurrency: the fast path (snapshot → invoke) holds the SHARED side
        of the per-server lock, so concurrent invokes on one server run in
        parallel. A failed invoke drops the shared side, takes the EXCLUSIVE
        side for reconnect → retry (serialized against other invokes via the
        writer-preferring lock), then releases it.

        Stale-snapshot guard: the (session, generation) pair is captured
        before invoking. If the invoke fails but the pair has since changed,
        someone repaired the connection out-of-band (e.g. a refresh that
        raced us) — retry once on the current session instead of triggering
        a redundant reconnect. Retries always re-snapshot under the shared
        side, never reuse a session object across a lock release.
        """
        lock = self._call_lock(server_name)
        async with lock.read():
            server = self._servers.get(server_name)
            if server is not None and not server.enabled:
                server.status = "disabled"
                return f"MCP server '{server_name}' is disabled"

            session, _ = self._snapshot(server_name)
            if session is None:
                needs_reconnect = server is not None and server_name in self._config
                initial_error = f"MCP server '{server_name}' not connected"
            else:
                try:
                    return await self._invoke_session(session, server_name, tool_name, arguments)
                except asyncio.TimeoutError:
                    initial_error = f"MCP tool '{tool_name}' timed out after {self._tool_timeout:g}s"
                except Exception as e:
                    initial_error = f"MCP tool error: {e}"

                current_session, _ = self._snapshot(server_name)
                if current_session is not None and current_session is not session:
                    # Repaired out from under us — retry on the current
                    # session, no reconnect of our own.
                    try:
                        return await self._invoke_session(
                            current_session, server_name, tool_name, arguments
                        )
                    except Exception as e:
                        initial_error = f"MCP tool error after external reconnect: {e}"

                needs_reconnect = True

        # Shared side released: reconnect (exclusive) + retry, then report.
        if not needs_reconnect:
            return f"MCP server '{server_name}' not connected"

        if not await self._reconnect_server(server_name):
            server = self._servers.get(server_name)
            err = server.error if server and server.error else initial_error
            return f"MCP server '{server_name}' reconnect failed: {err}"

        # Retry on the fresh session under a new shared hold. On failure the
        # session is torn down under the exclusive side so a broken session
        # is never left behind for the next caller.
        async with lock.read():
            try:
                return await self._call_tool_once(server_name, tool_name, arguments)
            except asyncio.TimeoutError:
                final_error = (
                    f"MCP tool '{tool_name}' timed out "
                    f"after {self._tool_timeout:g}s (after reconnect)"
                )
            except Exception as e:
                final_error = f"MCP tool error after reconnect: {e}"

        async with lock:
            self._set_server_error(server_name, final_error)
            await self._cleanup_server(server_name)
        return final_error

    def get_tools_for_server(self, server_name: str) -> list[str]:
        """Get tool names for a given server."""
        server = self._servers.get(server_name)
        return server.tools if server else []

    def get_langchain_tools(self) -> list:
        """Get all connected MCP tools as LangChain StructuredTools."""
        from lc_agent.mcp.tool_adapter import create_langchain_tools_from_schemas

        all_tools = []
        for server in self._servers.values():
            if server.enabled and server.status == "connected" and server.tool_schemas:
                invoke_fn = self._make_invoke_fn(server.name)
                tools = create_langchain_tools_from_schemas(server.name, server.tool_schemas, invoke_fn)
                all_tools.extend(tools)
        return all_tools

    def get_filtered_langchain_tools(self, allowed_servers: list[str] | None) -> list:
        """Get MCP tools filtered by allowed servers (three-value semantics)."""
        from lc_agent.mcp.tool_adapter import create_langchain_tools_from_schemas

        all_tools = []
        for server in self._servers.values():
            if not server.enabled or server.status != "connected" or not server.tool_schemas:
                continue
            if allowed_servers is not None and server.name not in allowed_servers:
                continue
            invoke_fn = self._make_invoke_fn(server.name)
            tools = create_langchain_tools_from_schemas(server.name, server.tool_schemas, invoke_fn)
            all_tools.extend(tools)
        return all_tools

    def _make_invoke_fn(self, server_name: str):
        """Create an async invoke function bound to a specific server."""
        async def invoke(tool_name: str, arguments: dict) -> str:
            return await self.call_tool(server_name, tool_name, arguments)
        return invoke

    async def shutdown(self):
        """Clean up all persistent connections."""
        for name in list(self._server_contexts):
            async with self._call_lock(name):
                await self._cleanup_server(name)
