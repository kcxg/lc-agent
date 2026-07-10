# Long Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit, user-isolated, durable long-term memory to framework-built `lc-agent` agents using LangGraph's SQLite Store integration.

**Architecture:** `LcAgentApp` initializes a separate `AsyncSqliteStore` during lifespan startup and assigns it to `AgentEngine`. `AgentEngine.build_agent()` appends memory instructions, adds CRUD memory tools, passes the memory store and `context_schema=AgentRuntimeContext` into `create_agent()`, while chat execution passes the authenticated `user_id` as runtime context. Memory tools use `ToolRuntime.context.user_id` plus `ToolRuntime.store` to operate inside `("lc-agent", "users", user_id, "memories")`.

**Tech Stack:** Python 3.12, LangChain `create_agent`, LangChain `ToolRuntime`, LangGraph `AsyncSqliteStore`, SQLite, `httpx`, Pydantic, pytest.

---

## Current Code Facts

- The project is on branch `long_memory`; latest `main` is merged at commit `492adf2`.
- `SessionMeta.user_id` and route-level user isolation already exist in `lc_agent/db/models.py`, `lc_agent/server/routes/sessions.py`, and `lc_agent/server/sse.py`.
- `lc_agent/server/sse.py` authenticates the current user in `_send_stream()` and `_resume_stream()`, but does not yet pass `user_id` into `engine.chat_stream()` or LangGraph runtime context.
- `AgentEngine.build_agent()` already passes `checkpointer` through `kwargs`, so memory store support should use the same pattern with `kwargs["store"]`.
- Code-registered agents are returned directly from `_agents` when `preset.source == "code"`, so long memory must stay scoped to agents created by `build_agent()`.
- Existing draft tests currently mention an earlier ambiguous memory write tool; these tests must be updated to the approved CRUD names before implementation is considered passing.

## File Structure

- Create `lc_agent/core/memory.py`: memory config helpers, runtime context dataclass, embedding adapter, SQLite Store factory, memory prompt text, and CRUD memory tool builder.
- Modify `lc_agent/core/engine.py`: accept a store, add memory tools and prompt instructions, pass `store` and `context_schema` into `create_agent()`, and pass runtime context during invoke/stream.
- Modify `lc_agent/app.py`: initialize and retain the memory store in lifespan startup, mirror checkpoint setup style, and avoid in-memory fallback.
- Modify `lc_agent/server/sse.py`: pass `user_id` from authenticated SSE requests into `engine.chat_stream()` and resume config.
- Modify `lc_agent/config/schema.py`: add typed `MemoryConfig` and `MemorySemanticSearchConfig` defaults.
- Modify `lc_agent/config/loader.py`: add the same memory defaults to the no-file fallback config.
- Modify `config.example.jsonc`: document framework memory config with `{env:NBRAG_API_KEY}`.
- Modify `D:\codes\lc-agent-bfzs\config.jsonc`: add matching demo memory config using bfzs-local `./bfzs_memory.db`.
- Modify `tests/test_config.py`: cover memory defaults and `{env:...}` literal behavior.
- Modify `tests/test_engine.py`: update stale draft tests to CRUD names, store parameter behavior, memory prompt behavior, and runtime context passing.
- Modify or create `tests/test_memory.py`: cover store persistence, CRUD semantics, user namespace isolation, and embedding adapter behavior.
- Modify `tests/test_routes_sessions.py` or `tests/test_permissions_integration.py` only if SSE/user context behavior needs a route-level regression test; prefer engine-level tests unless route behavior changes.

## Implementation Tasks

### Task 1: Stabilize Tests Around Approved Memory Semantics

**Files:**
- Modify: `tests/test_config.py`
- Modify: `tests/test_engine.py`
- Modify: `tests/test_memory.py`

- [ ] **Step 1: Rewrite draft config tests to approved defaults**

Replace the current memory assertions in `tests/test_config.py` with tests that verify the exact config structure:

```python
def test_memory_defaults_use_durable_sqlite_store():
    from lc_agent.config.schema import AppConfig

    config = AppConfig()

    assert config.memory.enabled is True
    assert config.memory.type == "sqlite"
    assert config.memory.path == "./lc_agent_memory.db"
    assert config.memory.save_policy == "explicit"
    assert config.memory.retrieval_policy == "manual"
    assert config.memory.semantic_search.enabled is True
    assert config.memory.semantic_search.api_key == "{env:NBRAG_API_KEY}"
    assert config.memory.semantic_search.base_url == "https://api.siliconflow.cn/v1"
    assert config.memory.semantic_search.model == "BAAI/bge-m3"
    assert config.memory.semantic_search.dims == 1024
```

- [ ] **Step 2: Add config loader tests for environment and literal API keys**

Add these tests to `tests/test_config.py`:

```python
def test_memory_api_key_uses_env_placeholder(monkeypatch, tmp_path):
    from lc_agent.config.loader import load_config_from_file

    monkeypatch.setenv("NBRAG_API_KEY", "env-secret")
    config_path = tmp_path / "config.jsonc"
    config_path.write_text(
        """
        {
          "memory": {
            "semantic_search": {
              "api_key": "{env:NBRAG_API_KEY}"
            }
          }
        }
        """,
        encoding="utf-8",
    )

    config = load_config_from_file(str(config_path))

    assert config["memory"]["semantic_search"]["api_key"] == "env-secret"


def test_memory_api_key_keeps_literal_value(tmp_path):
    from lc_agent.config.loader import load_config_from_file

    config_path = tmp_path / "config.jsonc"
    config_path.write_text(
        """
        {
          "memory": {
            "semantic_search": {
              "api_key": "literal-secret"
            }
          }
        }
        """,
        encoding="utf-8",
    )

    config = load_config_from_file(str(config_path))

    assert config["memory"]["semantic_search"]["api_key"] == "literal-secret"
```

- [ ] **Step 3: Rewrite engine tests to expect CRUD memory tools**

In `tests/test_engine.py`, update the stale memory tool expectation to the approved names:

```python
expected = {
    "memory__insert_memory",
    "memory__update_memory",
    "memory__get_memory",
    "memory__search_memories",
    "memory__list_memories",
    "memory__delete_memory",
}
assert expected.issubset({tool.name for tool in captured["tools"]})
```

- [ ] **Step 4: Add engine test for store and context schema pass-through**

Add this test to `tests/test_engine.py`:

```python
def test_build_agent_passes_memory_store_and_context_schema(sample_config, monkeypatch):
    from lc_agent.core.engine import AgentEngine
    from lc_agent.core.memory import AgentRuntimeContext

    captured = {}
    store = object()
    engine = AgentEngine(sample_config, store=store)

    class FakeAgent:
        pass

    def fake_create_agent(**kwargs):
        captured.update(kwargs)
        return FakeAgent()

    monkeypatch.setattr("langchain.agents.create_agent", fake_create_agent)

    engine.build_agent(cache_key="memory-test")

    assert captured["store"] is store
    assert captured["context_schema"] is AgentRuntimeContext
```

- [ ] **Step 5: Add engine test for per-run user context**

Add this async test to `tests/test_engine.py`:

```python
async def test_chat_stream_passes_user_context(sample_config, monkeypatch):
    from lc_agent.core.engine import AgentEngine
    from lc_agent.core.memory import AgentRuntimeContext

    captured = {}
    engine = AgentEngine(sample_config)

    class FakeAgent:
        async def astream_events(self, payload, *, config, context, version):
            captured["payload"] = payload
            captured["config"] = config
            captured["context"] = context
            captured["version"] = version
            if False:
                yield {}

    monkeypatch.setattr(engine, "_get_or_build_agent", lambda *args, **kwargs: FakeAgent())

    events = [
        event async for event in engine.chat_stream(
            "hello",
            "thread-1",
            user_id="user-123",
        )
    ]

    assert events == []
    assert captured["context"] == AgentRuntimeContext(user_id="user-123")
    assert captured["config"]["configurable"]["thread_id"] == "thread-1"
    assert captured["version"] == "v2"
```

- [ ] **Step 6: Run targeted tests and confirm the intended failures**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_config.py tests/test_engine.py tests/test_memory.py -v
```

Expected: FAIL because `AppConfig.memory`, `lc_agent.core.memory`, the `store` keyword on `AgentEngine`, and runtime context passing are not implemented yet.

- [ ] **Step 7: Commit only test updates**

Run:

```powershell
git add tests/test_config.py tests/test_engine.py tests/test_memory.py
git commit -m "test: define long memory behavior"
```

Expected: commit succeeds with only test files staged.

### Task 2: Add Memory Configuration Models

**Files:**
- Modify: `lc_agent/config/schema.py`
- Modify: `lc_agent/config/loader.py`

- [ ] **Step 1: Add Pydantic memory config classes**

Add these classes after `DatabaseConfig` in `lc_agent/config/schema.py`:

```python
class MemorySemanticSearchConfig(BaseModel):
    enabled: bool = True
    api_key: str = "{env:NBRAG_API_KEY}"
    base_url: str = "https://api.siliconflow.cn/v1"
    model: str = "BAAI/bge-m3"
    dims: int = 1024


class MemoryConfig(BaseModel):
    enabled: bool = True
    type: str = "sqlite"
    path: str = "./lc_agent_memory.db"
    save_policy: str = "explicit"
    retrieval_policy: str = "manual"
    semantic_search: MemorySemanticSearchConfig = Field(default_factory=MemorySemanticSearchConfig)
```

- [ ] **Step 2: Add memory to `AppConfig`**

Add the field inside `AppConfig`:

```python
memory: MemoryConfig = Field(default_factory=MemoryConfig)
```

- [ ] **Step 3: Add fallback memory config to `load_config()`**

In `lc_agent/config/loader.py`, extend the default returned dictionary:

```python
"memory": {
    "enabled": True,
    "type": "sqlite",
    "path": "./lc_agent_memory.db",
    "save_policy": "explicit",
    "retrieval_policy": "manual",
    "semantic_search": {
        "enabled": True,
        "api_key": "{env:NBRAG_API_KEY}",
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "BAAI/bge-m3",
        "dims": 1024,
    },
},
```

- [ ] **Step 4: Run config tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_config.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit config schema support**

Run:

```powershell
git add lc_agent/config/schema.py lc_agent/config/loader.py tests/test_config.py
git commit -m "feat: add long memory config"
```

Expected: commit succeeds.

### Task 3: Implement Memory Core Module

**Files:**
- Create: `lc_agent/core/memory.py`
- Modify: `tests/test_memory.py`

- [ ] **Step 1: Add failing tests for CRUD and user isolation**

Ensure `tests/test_memory.py` includes these cases:

```python
from dataclasses import dataclass


@dataclass
class FakeRuntime:
    store: object
    context: object


async def test_memory_tools_use_crud_semantics_and_user_namespace():
    from langgraph.store.memory import InMemoryStore

    from lc_agent.core.memory import AgentRuntimeContext, build_memory_tools

    store = InMemoryStore()
    tools = {tool.name: tool for tool in build_memory_tools()}
    user_a = FakeRuntime(store=store, context=AgentRuntimeContext(user_id="user-a"))
    user_b = FakeRuntime(store=store, context=AgentRuntimeContext(user_id="user-b"))

    inserted = await tools["memory__insert_memory"].ainvoke(
        {
            "key": "style",
            "value": "用户喜欢简洁回答",
            "runtime": user_a,
        }
    )
    duplicate = await tools["memory__insert_memory"].ainvoke(
        {
            "key": "style",
            "value": "覆盖尝试",
            "runtime": user_a,
        }
    )
    missing_update = await tools["memory__update_memory"].ainvoke(
        {
            "key": "style",
            "value": "另一个用户尝试更新",
            "runtime": user_b,
        }
    )
    user_a_memory = await tools["memory__get_memory"].ainvoke({"key": "style", "runtime": user_a})
    user_b_memory = await tools["memory__get_memory"].ainvoke({"key": "style", "runtime": user_b})

    assert "Inserted memory 'style'" in inserted
    assert "already exists" in duplicate
    assert "does not exist" in missing_update
    assert "用户喜欢简洁回答" in user_a_memory
    assert "not found" in user_b_memory
```

- [ ] **Step 2: Add failing test for SQLite persistence**

Add:

```python
async def test_sqlite_memory_store_persists_across_connections(tmp_path):
    from lc_agent.core.memory import create_sqlite_memory_store

    memory_path = tmp_path / "memory.db"

    async with create_sqlite_memory_store(str(memory_path)) as first:
        await first.aput(("lc-agent", "users", "user-a", "memories"), "style", {"value": "brief"})

    async with create_sqlite_memory_store(str(memory_path)) as second:
        item = await second.aget(("lc-agent", "users", "user-a", "memories"), "style")

    assert item is not None
    assert item.value["value"] == "brief"
```

- [ ] **Step 3: Add failing test for embedding adapter request shape**

Add:

```python
async def test_openai_compatible_embeddings_uses_configured_endpoint(monkeypatch):
    from lc_agent.core.memory import OpenAICompatibleEmbeddings

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"data": [{"embedding": [0.1, 0.2]}, {"embedding": [0.3, 0.4]}]}

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, *, headers, json):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient", FakeAsyncClient)

    embeddings = OpenAICompatibleEmbeddings(
        api_key="secret",
        base_url="https://example.test/v1",
        model="BAAI/bge-m3",
    )

    vectors = await embeddings.aembed(["a", "b"])

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    assert captured["url"] == "https://example.test/v1/embeddings"
    assert captured["headers"]["Authorization"] == "Bearer secret"
    assert captured["json"] == {
        "model": "BAAI/bge-m3",
        "input": ["a", "b"],
        "encoding_format": "float",
    }
```

- [ ] **Step 4: Create `lc_agent/core/memory.py` with runtime context and namespace helper**

Create the file with:

```python
from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx
from langchain.tools import ToolRuntime, tool
from langgraph.store.sqlite.aio import AsyncSqliteStore


@dataclass(frozen=True)
class AgentRuntimeContext:
    user_id: str = "anonymous"


def normalize_memory_user_id(user_id: str | None) -> str:
    value = (user_id or "").strip()
    return value if value else "anonymous"


def memory_namespace(user_id: str | None) -> tuple[str, str, str, str]:
    return ("lc-agent", "users", normalize_memory_user_id(user_id), "memories")
```

- [ ] **Step 5: Add OpenAI-compatible embedding adapter**

Add to `lc_agent/core/memory.py`:

```python
class OpenAICompatibleEmbeddings:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def aembed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "input": texts,
                    "encoding_format": "float",
                },
            )
            response.raise_for_status()
            payload = response.json()
        return [item["embedding"] for item in payload.get("data", [])]

    def embed(self, texts: list[str]) -> list[list[float]]:
        import anyio

        return anyio.run(self.aembed, texts)
```

- [ ] **Step 6: Add memory store factory**

Add:

```python
def build_store_index(memory_config: dict[str, Any]) -> dict[str, Any] | None:
    semantic = memory_config.get("semantic_search", {})
    if not semantic.get("enabled", False):
        return None

    api_key = semantic.get("api_key", "")
    if not api_key:
        raise ValueError("memory.semantic_search.api_key is required when semantic search is enabled")

    return {
        "embed": OpenAICompatibleEmbeddings(
            api_key=api_key,
            base_url=semantic.get("base_url", "https://api.siliconflow.cn/v1"),
            model=semantic.get("model", "BAAI/bge-m3"),
        ),
        "dims": int(semantic.get("dims", 1024)),
        "fields": ["value", "summary"],
    }


@asynccontextmanager
async def create_sqlite_memory_store(path: str, memory_config: dict[str, Any] | None = None) -> AsyncIterator[AsyncSqliteStore]:
    index = build_store_index(memory_config or {"semantic_search": {"enabled": False}})
    async with AsyncSqliteStore.from_conn_string(path, index=index) as store:
        await store.setup()
        yield store
```

- [ ] **Step 7: Add memory prompt instructions**

Add:

```python
MEMORY_SYSTEM_PROMPT = """# Long-Term Memory

You have access to user-scoped long-term memory that persists across sessions.

Rules:
- Write memory only when the user explicitly asks you to remember, update, or forget something.
- Use memory__insert_memory for new memories.
- Use memory__update_memory only when changing an existing memory.
- Use memory__search_memories or memory__list_memories only when the request depends on remembered information.
- If you are unsure whether something should be remembered, ask the user before writing.
"""
```

- [ ] **Step 8: Add CRUD memory tools**

Add `build_memory_tools()` in `lc_agent/core/memory.py`:

```python
def _runtime_namespace(runtime: ToolRuntime[AgentRuntimeContext]) -> tuple[str, str, str, str]:
    user_id = getattr(getattr(runtime, "context", None), "user_id", None)
    return memory_namespace(user_id)


def build_memory_tools() -> list[Any]:
    @tool("memory__insert_memory")
    async def insert_memory(key: str, value: str, summary: str = "", runtime: ToolRuntime[AgentRuntimeContext] | None = None) -> str:
        """Insert a new long-term memory for the current user. Fails if the key already exists."""
        if runtime is None or runtime.store is None:
            return "Long-term memory store is not available."
        namespace = _runtime_namespace(runtime)
        existing = await runtime.store.aget(namespace, key)
        if existing is not None:
            return f"Memory '{key}' already exists. Use memory__update_memory to change it."
        await runtime.store.aput(namespace, key, {"value": value, "summary": summary})
        return f"Inserted memory '{key}'."

    @tool("memory__update_memory")
    async def update_memory(key: str, value: str, summary: str = "", runtime: ToolRuntime[AgentRuntimeContext] | None = None) -> str:
        """Update an existing long-term memory for the current user. Fails if the key does not exist."""
        if runtime is None or runtime.store is None:
            return "Long-term memory store is not available."
        namespace = _runtime_namespace(runtime)
        existing = await runtime.store.aget(namespace, key)
        if existing is None:
            return f"Memory '{key}' does not exist. Use memory__insert_memory to create it."
        await runtime.store.aput(namespace, key, {"value": value, "summary": summary})
        return f"Updated memory '{key}'."

    @tool("memory__get_memory")
    async def get_memory(key: str, runtime: ToolRuntime[AgentRuntimeContext] | None = None) -> str:
        """Get one long-term memory by exact key for the current user."""
        if runtime is None or runtime.store is None:
            return "Long-term memory store is not available."
        item = await runtime.store.aget(_runtime_namespace(runtime), key)
        if item is None:
            return f"Memory '{key}' not found."
        return str(item.value)

    @tool("memory__search_memories")
    async def search_memories(query: str, limit: int = 5, runtime: ToolRuntime[AgentRuntimeContext] | None = None) -> str:
        """Search long-term memories for the current user."""
        if runtime is None or runtime.store is None:
            return "Long-term memory store is not available."
        results = await runtime.store.asearch(_runtime_namespace(runtime), query=query, limit=limit)
        if not results:
            return "No matching memories found."
        return "\n".join(f"- {item.key}: {item.value}" for item in results)

    @tool("memory__list_memories")
    async def list_memories(limit: int = 20, runtime: ToolRuntime[AgentRuntimeContext] | None = None) -> str:
        """List memory keys and summaries for the current user."""
        if runtime is None or runtime.store is None:
            return "Long-term memory store is not available."
        results = await runtime.store.asearch(_runtime_namespace(runtime), limit=limit)
        if not results:
            return "No memories found."
        return "\n".join(f"- {item.key}: {item.value}" for item in results)

    @tool("memory__delete_memory")
    async def delete_memory(key: str, runtime: ToolRuntime[AgentRuntimeContext] | None = None) -> str:
        """Delete one long-term memory by exact key for the current user."""
        if runtime is None or runtime.store is None:
            return "Long-term memory store is not available."
        namespace = _runtime_namespace(runtime)
        existing = await runtime.store.aget(namespace, key)
        if existing is None:
            return f"Memory '{key}' not found."
        await runtime.store.adelete(namespace, key)
        return f"Deleted memory '{key}'."

    return [insert_memory, update_memory, get_memory, search_memories, list_memories, delete_memory]
```

- [ ] **Step 9: Run memory tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_memory.py -v
```

Expected: PASS. If `langgraph.store.memory.InMemoryStore` has sync-only methods in the installed version, update tests to use `AsyncSqliteStore` for all tool tests rather than adding an in-memory fallback.

- [ ] **Step 10: Commit memory core**

Run:

```powershell
git add lc_agent/core/memory.py tests/test_memory.py
git commit -m "feat: add long memory tools"
```

Expected: commit succeeds.

### Task 4: Wire Memory Store Into App Lifespan

**Files:**
- Modify: `lc_agent/app.py`
- Modify: `tests/test_engine.py` only if constructor setup tests need adjustment

- [ ] **Step 1: Update `AgentEngine` constructor signature before app wiring**

In `lc_agent/core/engine.py`, change constructor signature and add `_store`:

```python
def __init__(self, config: dict, checkpointer=None, store=None):
    self.config = config
    self.tool_registry = ToolRegistry()
    self._checkpointer = checkpointer
    self._store = store
```

- [ ] **Step 2: Add lifespan memory store context stack**

In `lc_agent/app.py`, import and use `AsyncExitStack` in `_lifespan()`:

```python
from contextlib import AsyncExitStack
```

Then wrap startup resources:

```python
async with AsyncExitStack() as stack:
    await init_db(self._db_url)
    await self._init_auth(app)

    try:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        import aiosqlite

        conn = await aiosqlite.connect(self._checkpoint_path)
        saver = AsyncSqliteSaver(conn)
        await saver.setup()
        self.engine._checkpointer = saver
    except Exception as e:
        print(f"[Warning] Checkpoint saver setup failed, using None: {e}")

    memory_conf = self.config.get("memory", {})
    if memory_conf.get("enabled", True):
        if memory_conf.get("type", "sqlite") != "sqlite":
            raise ValueError("Only sqlite long-term memory is supported")
        from lc_agent.core.memory import create_sqlite_memory_store

        store = await stack.enter_async_context(
            create_sqlite_memory_store(memory_conf.get("path", "./lc_agent_memory.db"), memory_conf)
        )
        self.engine._store = store

    await self._load_presets_from_db()
    yield
```

Keep the existing checkpoint setup and MCP startup inside the same stack scope so the SQLite memory connection stays open for the app lifetime.

- [ ] **Step 3: Handle memory setup errors clearly**

Use this behavior:

```python
try:
    store = await stack.enter_async_context(create_sqlite_memory_store(memory_path, memory_conf))
    self.engine._store = store
except Exception as e:
    self.engine._store = None
    raise RuntimeError(f"Long-term memory setup failed: {e}") from e
```

This intentionally fails startup when enabled memory cannot initialize, and avoids silently switching to non-durable storage.

- [ ] **Step 4: Run focused app import tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_custom_agents.py tests/test_permissions_integration.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit app store lifecycle**

Run:

```powershell
git add lc_agent/app.py lc_agent/core/engine.py tests/test_engine.py
git commit -m "feat: initialize long memory store"
```

Expected: commit succeeds.

### Task 5: Wire Memory Into Framework-Built Agents

**Files:**
- Modify: `lc_agent/core/engine.py`
- Modify: `tests/test_engine.py`

- [ ] **Step 1: Add memory tools and prompt in `build_agent()`**

In `AgentEngine.build_agent()`, after existing skill/MCP tools are assembled and before `create_agent()`:

```python
memory_conf = self.config.get("memory", {})
memory_enabled = memory_conf.get("enabled", True) and self._store is not None
if memory_enabled:
    from lc_agent.core.memory import MEMORY_SYSTEM_PROMPT, AgentRuntimeContext, build_memory_tools

    tools = tools + build_memory_tools()
    system_prompt = f"{system_prompt}\n\n{MEMORY_SYSTEM_PROMPT}"
```

- [ ] **Step 2: Pass store and context schema to `create_agent()`**

Extend the existing `kwargs` block:

```python
if self._store is not None and self.config.get("memory", {}).get("enabled", True):
    from lc_agent.core.memory import AgentRuntimeContext

    kwargs["store"] = self._store
    kwargs["context_schema"] = AgentRuntimeContext
```

Keep `checkpointer` unchanged:

```python
if self._checkpointer:
    kwargs["checkpointer"] = self._checkpointer
```

- [ ] **Step 3: Update `chat()` signature and invoke context**

Change:

```python
async def chat(
    self,
    message: str,
    thread_id: str,
    preset_id: str = "__chat__",
    model_id: str = "",
    user_id: str = "anonymous",
) -> str:
```

Then invoke with context:

```python
from lc_agent.core.memory import AgentRuntimeContext, normalize_memory_user_id

result = await agent.ainvoke(
    {"messages": [{"role": "user", "content": message}]},
    config=config,
    context=AgentRuntimeContext(user_id=normalize_memory_user_id(user_id)),
)
```

- [ ] **Step 4: Update `chat_stream()` signature and stream context**

Change:

```python
async def chat_stream(
    self,
    message: str,
    thread_id: str,
    preset_id: str = "__chat__",
    model_id: str = "",
    history: list[dict[str, str]] | None = None,
    llm_params: dict | None = None,
    user_id: str = "anonymous",
) -> AsyncIterator[dict]:
```

Then stream with context:

```python
from lc_agent.core.memory import AgentRuntimeContext, normalize_memory_user_id

async for event in agent.astream_events(
    {"messages": input_messages},
    config=config,
    context=AgentRuntimeContext(user_id=normalize_memory_user_id(user_id)),
    version="v2",
):
    yield event
```

- [ ] **Step 5: Preserve custom code agent behavior**

Do not alter this branch:

```python
if preset.source == "code" or preset_id in self._custom_presets:
    agent = self._agents.get(preset_id)
    if agent is None:
        raise ValueError(f"Code agent '{preset_id}' is registered without a graph")
    return agent
```

The store is only passed when `build_agent()` is called.

- [ ] **Step 6: Run engine tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine.py tests/test_custom_agents.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit engine integration**

Run:

```powershell
git add lc_agent/core/engine.py tests/test_engine.py
git commit -m "feat: wire long memory into agents"
```

Expected: commit succeeds.

### Task 6: Pass Authenticated User Context Through SSE

**Files:**
- Modify: `lc_agent/server/sse.py`
- Modify: `tests/test_permissions_integration.py` or `tests/test_engine.py`

- [ ] **Step 1: Pass user id in new-message stream path**

In `_send_stream()`, change:

```python
stream = engine.chat_stream(content, thread_id, preset_id, **stream_kwargs)
```

to:

```python
stream = engine.chat_stream(
    content,
    thread_id,
    preset_id,
    user_id=user.id if user else "anonymous",
    **stream_kwargs,
)
```

- [ ] **Step 2: Pass user id in interrupt resume path**

In `_resume_stream()`, change the config construction:

```python
config = {"configurable": {"thread_id": thread_id}, "recursion_limit": engine.recursion_limit}
```

to:

```python
config = {
    "configurable": {"thread_id": thread_id},
    "recursion_limit": engine.recursion_limit,
}
```

Then update `agent.astream_events` in the resume path to include context:

```python
from lc_agent.core.memory import AgentRuntimeContext, normalize_memory_user_id

async for event in agent.astream_events(
    Command(resume=resume_value),
    config=config,
    context=AgentRuntimeContext(user_id=normalize_memory_user_id(user.id if user else "anonymous")),
    version="v2",
):
    yield event
```

- [ ] **Step 3: Add focused regression test for SSE user context**

If existing SSE route tests can inject a fake engine, add a test with this assertion:

```python
assert captured_user_id == authenticated_user.id
```

If SSE route tests are too broad, keep the route unchanged except for passing `user_id` and rely on the `AgentEngine.chat_stream()` context test from Task 1 plus manual integration verification in Task 9.

- [ ] **Step 4: Run route and permission tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_permissions_integration.py tests/test_routes_sessions.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit SSE context passing**

Run:

```powershell
git add lc_agent/server/sse.py tests/test_permissions_integration.py tests/test_routes_sessions.py
git commit -m "feat: pass user context to agent memory"
```

Expected: commit succeeds. If no tests changed in this task, stage only `lc_agent/server/sse.py`.

### Task 7: Update Example Configs

**Files:**
- Modify: `config.example.jsonc`
- Modify: `D:\codes\lc-agent-bfzs\config.jsonc`

- [ ] **Step 1: Add framework example memory block**

Add this top-level block to `config.example.jsonc` near `database`:

```jsonc
  "memory": {
    "enabled": true,
    "type": "sqlite",
    "path": "./lc_agent_memory.db",
    "save_policy": "explicit",
    "retrieval_policy": "manual",
    "semantic_search": {
      "enabled": true,
      "api_key": "{env:NBRAG_API_KEY}",
      "base_url": "https://api.siliconflow.cn/v1",
      "model": "BAAI/bge-m3",
      "dims": 1024
    }
  },
```

- [ ] **Step 2: Add bfzs demo memory block**

Add this top-level block to `D:\codes\lc-agent-bfzs\config.jsonc`:

```jsonc
  "memory": {
    "enabled": true,
    "type": "sqlite",
    "path": "./bfzs_memory.db",
    "save_policy": "explicit",
    "retrieval_policy": "manual",
    "semantic_search": {
      "enabled": true,
      "api_key": "{env:NBRAG_API_KEY}",
      "base_url": "https://api.siliconflow.cn/v1",
      "model": "BAAI/bge-m3",
      "dims": 1024
    }
  },
```

- [ ] **Step 3: Parse both JSONC files**

Run:

```powershell
@'
from lc_agent.config.loader import load_config_from_file

for path in [
    r"D:\codes\lc-agent\config.example.jsonc",
    r"D:\codes\lc-agent-bfzs\config.jsonc",
]:
    config = load_config_from_file(path)
    print(path, config["memory"]["path"], config["memory"]["semantic_search"]["model"])
'@ | D:\ProgramData\Miniconda3\envs\py312\python.exe -
```

Expected: both files parse, and each prints the expected memory path. If `NBRAG_API_KEY` is not set locally, temporarily set it for this command:

```powershell
$env:NBRAG_API_KEY='test-key'
```

- [ ] **Step 4: Commit config examples**

Run:

```powershell
git add config.example.jsonc
git commit -m "docs: add long memory config example"
```

Expected: lc-agent commit succeeds for `config.example.jsonc`. The bfzs file lives in a separate repository; commit it in `D:\codes\lc-agent-bfzs` only if that repo is intended to receive a paired commit:

```powershell
git -C D:\codes\lc-agent-bfzs commit -m "config: enable long memory"
```

### Task 8: Verify Full Test Suite

**Files:**
- No planned source changes

- [ ] **Step 1: Run targeted memory tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_config.py tests/test_memory.py tests/test_engine.py -v
```

Expected: PASS.

- [ ] **Step 2: Run full backend test suite**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/ -v
```

Expected: PASS.

- [ ] **Step 3: Inspect git status**

Run:

```powershell
git status --short --branch
```

Expected: only intentional files are modified. Existing frontend dist line-ending noise may remain from the merge; do not stage it unless the user asks for a frontend build.

### Task 9: Manual Integration Check With bfzs

**Files:**
- Runtime DB files may be created: `D:\codes\lc-agent-bfzs\bfzs_memory.db`

- [ ] **Step 1: Confirm API key exists for semantic search**

Run:

```powershell
$env:NBRAG_API_KEY
```

Expected: prints a non-empty key. If empty, set it in the shell for the manual run:

```powershell
$env:NBRAG_API_KEY='the-user-provided-key'
```

- [ ] **Step 2: Start bfzs**

Run:

```powershell
cd D:\codes\lc-agent-bfzs
D:\ProgramData\Miniconda3\envs\py312\python.exe -u -m bfzs.main --port 8001
```

Expected: startup succeeds and creates or opens `bfzs_memory.db`; no warning claims memory is in-memory.

- [ ] **Step 3: Exercise explicit memory write**

In the app, use a framework-built preset such as `__power__` or a web-created preset and send:

```text
记住我的回答偏好：先给结论，再给关键步骤。
```

Expected: the model calls `memory__insert_memory` and reports success.

- [ ] **Step 4: Exercise retrieval in another session**

Start a new session with the same authenticated user and send:

```text
你记得我的回答偏好吗？
```

Expected: the model calls `memory__search_memories` or `memory__list_memories` and returns the stored preference.

- [ ] **Step 5: Exercise update and delete semantics**

Send:

```text
把我的回答偏好更新为：默认详细一点，但先给摘要。
```

Expected: the model calls `memory__update_memory`, not insert.

Then send:

```text
忘掉我的回答偏好。
```

Expected: the model calls `memory__delete_memory`.

- [ ] **Step 6: Stop the server and inspect runtime files**

Run:

```powershell
Get-ChildItem D:\codes\lc-agent-bfzs -Filter '*memory*.db'
```

Expected: `bfzs_memory.db` exists.

### Task 10: Final Review and Cleanup

**Files:**
- No planned source changes unless verification finds a concrete issue

- [ ] **Step 1: Search for stale tool names**

Run:

```powershell
rg "memory__(save|upsert)_memory|save_memory|upsert_memory" D:\codes\lc-agent
```

Expected: no hits except historical design discussion if intentionally kept. If the design spec contains stale memory write names, update it to approved CRUD names.

- [ ] **Step 2: Search for in-memory fallback**

Run:

```powershell
rg "InMemoryStore|in-memory|using None" D:\codes\lc-agent\lc_agent D:\codes\lc-agent\tests
```

Expected: no production memory fallback uses `InMemoryStore`. Test usage is acceptable only if it does not mask durable store behavior.

- [ ] **Step 3: Run formatting checks if available**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m ruff check lc_agent tests
```

Expected: PASS. If `ruff` is not installed, record that it was unavailable and rely on pytest.

- [ ] **Step 4: Produce final git summary**

Run:

```powershell
git log --oneline --decorate -8
git status --short --branch
```

Expected: memory implementation commits are visible on `long_memory`; working tree has no unintended staged files.

## Design Review Checklist

- [ ] Explicit writes only: prompt and tool descriptions tell the model not to write unless the user asks.
- [ ] User isolation: tools derive namespace from `ToolRuntime.context.user_id`, not from thread id or prompt text.
- [ ] Durable storage: enabled memory uses `AsyncSqliteStore`, never an in-memory fallback.
- [ ] CRUD semantics: insert fails on existing key; update fails on missing key; no upsert tool exists.
- [ ] Retrieval policy: memory is searched only by explicit tool call, not injected into every prompt.
- [ ] Custom agents: code-registered graphs are not mutated by framework memory wiring.
- [ ] Config parity: both framework example config and bfzs demo config include the same schema.
- [ ] API key behavior: `{env:NBRAG_API_KEY}` resolves through the existing loader; literal values stay literal.
- [ ] Semantic search: missing API key causes clear startup failure when semantic search is enabled.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-06-long-memory-implementation-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** - execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
