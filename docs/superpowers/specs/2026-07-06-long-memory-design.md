# Long Memory Design

## Goal

Add durable cross-session long-term memory to `lc-agent` agents built through `AgentEngine.build_agent()`, using LangGraph's native Store integration while keeping memory writes explicit, user-scoped, and safe from accidental upsert behavior.

## Context

`lc-agent` currently passes a LangGraph checkpointer into `langchain.agents.create_agent()` for thread-scoped short-term state. LangGraph separates this from long-term memory: checkpointers persist graph state for one thread, while Stores persist application-defined data across threads.

The project already uses SQLite for application data and LangGraph checkpoints. The current Python environment also includes `langgraph.store.sqlite.aio.AsyncSqliteStore`, so long-term memory can be backed by a separate SQLite database without using `InMemoryStore`.

`nbrag` provides a useful embedding configuration pattern:

- OpenAI-compatible embedding API endpoint.
- SiliconFlow default base URL: `https://api.siliconflow.cn/v1`.
- Default embedding model: `BAAI/bge-m3`.
- API key can come from `NBRAG_API_KEY`.

This design borrows the embedding configuration style from `nbrag`, but does not copy `nbrag`'s ChromaDB/BM25/rerank document-RAG architecture. Personal long-term memory should remain small, direct, and native to LangGraph Store.

## Decisions

### Storage

Use `langgraph.store.sqlite.aio.AsyncSqliteStore` as the long-term memory store.

- Store file defaults to `./lc_agent_memory.db`.
- Store file is separate from `database.checkpoint_path`.
- Store setup runs during `LcAgentApp` startup.
- Store is passed into `AgentEngine`, then into `create_agent(..., store=store)`.
- No `InMemoryStore` fallback is used for enabled durable memory.

### Memory Scope

Memory is isolated by user.

The default namespace shape is:

```python
("lc-agent", "users", user_id, "memories")
```

If no authenticated user is available in the execution path, the framework must use a clear fallback identity such as `"anonymous"` or `"local"` rather than merging it with a real user namespace.

### Write Policy

Memory writes are explicit only.

The agent may insert, update, or delete long-term memory only when the user clearly asks it to remember, update, or forget something. The agent must not automatically infer and store memories from ordinary conversation.

Examples that may write:

- "记住我喜欢简洁回答。"
- "以后记得我用 Python 3.12。"
- "把我的回答风格偏好更新为详细一点。"
- "忘掉我之前说的邮箱。"

Examples that must not write:

- A normal Q&A turn with incidental personal facts.
- Temporary project context.
- Ambiguous statements that do not ask to be remembered.

### Retrieval Policy

Memory retrieval is manual/tool-driven, not automatic every turn.

The agent should call memory search only when:

- The user asks what the agent remembers.
- The user asks the agent to use remembered preferences.
- The current request clearly depends on prior user preferences or facts.

The framework should not inject all memories into every prompt.

### Tool Names

Use explicit CRUD-style names to avoid ambiguous `save` behavior:

- `memory__insert_memory`
- `memory__update_memory`
- `memory__get_memory`
- `memory__search_memories`
- `memory__list_memories`
- `memory__delete_memory`

Tool semantics:

- `insert_memory` creates only. It must fail if the key already exists.
- `update_memory` updates only. It must fail if the key does not exist.
- `get_memory` reads one memory by exact key.
- `search_memories` retrieves relevant memories for the current user.
- `list_memories` lists current user's memory keys and summaries.
- `delete_memory` deletes one memory by exact key.

There is intentionally no upsert tool in the first version.

### Semantic Search

The framework supports configurable semantic search. Example configuration enables it by default.

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
}
```

Rules:

- `api_key` supports existing `{env:VAR_NAME}` substitution through the config loader.
- Any non-`{env:...}` value is treated as a literal API key.
- If semantic search is enabled and the API key is missing, startup should fail or disable memory setup with a clear warning. It must not silently pretend semantic search is active.
- `dims` stays configurable. The example uses `1024` for `BAAI/bge-m3`.

Implementation should expose an embeddings adapter compatible with LangGraph Store's index configuration. It should call the OpenAI-compatible `/embeddings` endpoint with:

```json
{
  "model": "<configured model>",
  "input": ["..."],
  "encoding_format": "float"
}
```

### System Prompt Guidance

Agents built through `AgentEngine.build_agent()` should receive an appended memory instruction when durable memory is enabled.

The instruction must explain:

- Long-term memory is user-scoped and persists across sessions.
- Only write memory when the user explicitly asks.
- Use `insert_memory` for new memory and `update_memory` for changes.
- Search/list memory only when the request depends on remembered information.
- If unsure whether to remember something, ask the user instead of writing.

### Applicability

This feature applies to framework-built agents:

- Built-in presets.
- User-created web presets that go through `AgentEngine.build_agent()`.

Custom code-registered agents added through `app.add_agent(name, graph, description)` remain user-controlled. The framework should not mutate their graph. If a custom agent wants long-term memory, users can compile it with the same store in a separate explicit change.

## Data Flow

1. `load_config()` loads `memory` config and resolves `{env:...}` values.
2. `LcAgentApp._lifespan()` initializes the existing checkpointer and the new SQLite memory store.
3. `LcAgentApp` assigns the memory store to `self.engine._store`.
4. `AgentEngine.build_agent()` detects the store and memory config.
5. `AgentEngine.build_agent()` adds memory tools to the tool list.
6. `AgentEngine.build_agent()` passes `store=...` to `create_agent()`.
7. Chat execution passes user identity into graph runtime context where available.
8. Memory tools use `ToolRuntime.store` and the current user identity to operate inside the user's namespace.

## Error Handling

- Memory disabled: no memory store, no memory tools, no memory prompt.
- Store setup failure: startup should report a clear warning or error; it must not switch to in-memory storage.
- Semantic search enabled without API key: fail clearly or disable semantic indexing clearly.
- Insert existing key: return a clear message telling the agent to use `update_memory`.
- Update missing key: return a clear message telling the agent to use `insert_memory`.
- Delete missing key: return a clear not-found message.
- Missing user identity: use a clearly named fallback namespace and do not mix with real users.

## Testing

Tests should cover:

- `AppConfig` defaults include SQLite memory and semantic search config.
- `load_config()` preserves literal API keys and resolves `{env:...}` keys.
- `AgentEngine` passes `store` into `create_agent()`.
- Memory tools are added only when memory is enabled and a store exists.
- `insert_memory` does not overwrite an existing key.
- `update_memory` does not create a missing key.
- `get/list/search/delete` operate only in the current user's namespace.
- SQLite memory persists across store connections.
- Semantic embedding adapter calls the configured OpenAI-compatible endpoint.
- Existing custom agents registered through `app.add_agent()` are not modified.

## Non-Goals

- No automatic memory extraction in the first version.
- No per-turn automatic retrieval.
- No ChromaDB, BM25, or rerank integration in the first version.
- No memory management UI in the first version.
- No migration compatibility work for older memory schemas.

## Open Decisions Resolved

- Memory scope: user-isolated.
- Write policy: explicit user request only.
- Retrieval policy: manual/tool-driven, not every turn.
- Semantic search: configurable, example config enabled.
- Tool naming: CRUD-style `insert/update/get/search/list/delete`.
