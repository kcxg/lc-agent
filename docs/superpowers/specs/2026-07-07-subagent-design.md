# Sub-Agent Design

## Goal

Add multi-agent support to `lc-agent` following the LangChain 2026 "subagents as tools" pattern.
A supervisor agent coordinates specialist sub-agents by invoking them as tools.
Each sub-agent run gets its own isolated thread and a dedicated sub-session for UI navigation.
The main chat view stays clean; users can click into a sub-agent card to enter its full conversation view.

## Background

LangChain's current best practice for multi-agent systems is the **subagents-as-tools** pattern:
- Wrap each sub-agent as an async `@tool` that accepts a `query` string and a `RunnableConfig`.
- Pass the `config` through to `ainvoke` so the sub-agent's internal events (tokens, tool calls)
  flow back into the parent's `astream_events` stream under a nested namespace.
- The supervisor (`create_agent`) calls these tools as normal tool calls; the LLM decides
  whether to call one or multiple in parallel.

Nested events are identified by `metadata["langgraph_checkpoint_ns"]`.
A non-empty namespace means the event originated inside a sub-agent.

## Decisions

### Sub-agent configuration

An `AgentPreset` may reference other presets (web-created or code-registered) as sub-agents
via a new `subagent_ids` field.

```python
class AgentPreset(BaseModel):
    # ... existing fields unchanged ...
    subagent_ids: list[str] | None = None
    # None  = no sub-agents
    # ["preset_uuid", "code_agent_name"] = sub-agents by ID
```

`AgentPresetDB` adds a matching `subagent_ids` JSON column; Alembic migrates automatically.

The editor (`AgentEditorDialog`) adds a **Sub-agents** tab with a checkbox list
showing all available presets, excluding the preset being edited and the `__chat__` builtin.

### Nesting depth

Sub-agents can themselves have sub-agents. Maximum nesting depth is configurable in `config.jsonc`:

```jsonc
"agent": {
  "max_subagent_depth": 2  // default; 0 = no sub-agents allowed
}
```

A `_current_depth` counter is tracked during `build_agent` to enforce this limit.
Exceeding the limit logs a warning and skips further nesting rather than erroring.

### Sub-agent memory / thread isolation

Each sub-agent invocation receives its own `thread_id`:

```
sub_thread_id = f"{parent_thread_id}/sa/{tool_call_id}"
```

The sub-agent's LangGraph state is checkpointed under this thread.
It starts with fresh state on every invocation (inherited-checkpointer mode).
If the user navigates back to the same parent session and triggers the same sub-agent again,
a new `tool_call_id` produces a new sub thread, keeping invocations isolated.

### Sub-session persistence

Sub-agent runs are stored as sub-sessions in the existing `sessions` and `chat_ui_messages` tables.
Two new columns are added to `sessions`:

| Column | Type | Purpose |
|---|---|---|
| `parent_session_id` | `str \| None` | Link sub-session to parent for breadcrumb navigation |
| `tool_call_id` | `str \| None` | Link sub-session to the specific tool call that spawned it |

Sub-session `session_id = sub_thread_id`.
Sub-session messages are regular `chat_ui_messages` rows with `session_id = sub_thread_id`.

The first message in a sub-session is a synthetic "delegation" message:
```json
{"role": "system", "content": "Delegated task: <query>"}
```
It is inserted when `subagent_start` is received.

### Main session tool_call entry

Each sub-agent invocation appears as a `tool_call` entry in the parent session's
last `chat_ui_messages.tool_calls` JSON array, extended with:

```json
{
  "name": "research_expert",
  "runId": "...",
  "args": {"query": "..."},
  "status": "running | done | error",
  "is_subagent": true,
  "sub_session_id": "main_xxx/sa/abc123",
  "token_preview": "量子纠错取得重大突破...",
  "tool_call_count": 4,
  "token_count": 1234,
  "duration": 3200
}
```

`is_subagent: true` is stable and set at `subagent_start` time; the other fields update as the run progresses.

### SSE event protocol (new events)

`stream_utils.convert_stream_event()` inspects `metadata["langgraph_checkpoint_ns"]`
to determine event origin. A non-empty namespace containing a `tools:` segment indicates a sub-agent event.

New event types sent to the frontend:

| Event | Trigger | Key fields |
|---|---|---|
| `subagent_start` | `on_tool_start` for a sub-agent tool (empty ns) | `name, tool_call_id, sub_session_id, query` |
| `subagent_token` | `on_chat_model_stream` from sub-agent (non-empty ns) | `tool_call_id, content` |
| `subagent_thinking` | `on_chat_model_stream` reasoning from sub-agent | `tool_call_id, content` |
| `subagent_tool_call` | `on_tool_start` from inside sub-agent (non-empty ns) | `tool_call_id, name, args` |
| `subagent_tool_result` | `on_tool_end` from inside sub-agent (non-empty ns) | `tool_call_id, name, result` |
| `subagent_done` | `on_tool_end` for a sub-agent tool (empty ns) | `tool_call_id, result_preview, tool_count, token_count` |

The existing `tool_call` event for a sub-agent tool carries `"is_subagent": true`
and `"sub_session_id"` in addition to the normal fields.
The existing `tool_result` event is suppressed for sub-agent tools (`subagent_done` replaces it).
`accumulate_display_state()` likewise skips updating `tool_calls` for sub-agent tools on `on_tool_end`,
as the sub-agent's result is tracked separately via `subagent_done`.

`stream_utils` receives a `subagent_tool_names: set[str]` parameter so it can identify which
`on_tool_start` events correspond to sub-agents vs. regular tools.

### Sub-session dual-write

`sse.py`'s `event_stream()` maintains a `_subagent_writers` dict keyed by `tool_call_id`.
On `subagent_start`: create sub-session DB record and insert delegation message.
On `subagent_token` / `subagent_tool_call` / `subagent_tool_result`: buffer for the sub-session's assistant message.
On `subagent_done`: flush buffered content into `chat_ui_messages` for the sub-session; mark sub-session complete.

The parent session's tool_call entry is updated in-place as events arrive.

### Parallel sub-agents

No artificial restriction. If the LLM produces multiple sub-agent tool calls in one turn,
they execute concurrently (standard LangGraph behavior).
The frontend handles multiple simultaneous `SubAgentCard` entries in the same message.

## Data flow

1. User sends message to main agent.
2. `engine.chat_stream()` yields `astream_events v2` events.
3. `sse.py` consumes events; `convert_stream_event()` routes per namespace.
4. Main-agent events → existing SSE types (`token`, `tool_call`, etc.).
5. Sub-agent boundary events → new SSE types (`subagent_start`, `subagent_token`, etc.).
6. Sub-session writer creates/updates sub-session in DB concurrently.
7. Frontend receives all events on the single SSE connection.
8. `SubAgentCard` renders the running card inline in the main message.
9. User clicks ↗ → `sessionNavStack.push(sub_session_id)` → chat view renders sub-session.
10. User clicks ← → `sessionNavStack.pop()` → returns to parent session.

## Frontend components

### `SubAgentCard.vue`

Renders when `toolCall.is_subagent === true`.

**Running state (B+C style):**
- Blue header: agent name + "● 执行中" + tool call count so far.
- Body: real-time streaming token text (fed by `subagent_token` events).
- Inner tool calls: compact list of `subagent_tool_call` entries (collapsible).
- ↗ button navigates into sub-session even while running.

**Completed state:**
- Blue header: agent name + "完成 ✓" + duration.
- Body: `token_preview` (first ≤100 chars of result).
- Footer: 🔧 N · 💬 N tokens · ↗ 查看完整.

**Error state:**
- Red header. Error message in body.

### Navigation stack (Pinia sessions store)

```typescript
const sessionNavStack = ref<Array<{
  session_id: string
  label: string
}>>([])

const effectiveThreadId = computed(
  () => sessionNavStack.value.at(-1)?.session_id ?? selectedSessionId.value
)
```

`pushSubSession(sub_session_id, label)` and `popSubSession()` mutate the stack.
`ChatView` reacts to `effectiveThreadId` for message loading and SSE routing.

### Breadcrumb bar

Rendered at the top of `ChatView` when `sessionNavStack.length > 0`:

```
[← 返回]  主对话  /  research_expert
```

Clicking ← pops the stack. Clicking an intermediate segment pops to that level.

## Engine changes

### `AgentEngine._make_subagent_tool(subagent_id, depth)`

Creates a `langchain_core.tools.StructuredTool` that:
1. Resolves the sub-agent via `_get_or_build_agent(subagent_id)`.
2. Propagates `config` (critical for nested streaming).
3. Sets `sub_thread_id` in `config.configurable`.
4. Uses `ainvoke` (async) to preserve event propagation.

Sub-agent tool names are collected in `build_agent()` and returned as metadata
so `convert_stream_event()` can distinguish sub-agent tools from regular tools.

### Circular dependency protection

`build_agent()` receives a `_building_set: frozenset[str]` parameter that accumulates
preset IDs during recursive builds. If a `subagent_id` is already in `_building_set`, it is
skipped with a warning log rather than causing infinite recursion.

### `AgentEngine.build_agent()` returns subagent_tool_names

`build_agent()` signature is extended to return a `(agent, subagent_tool_names: set[str])` tuple.
Callers in `_get_or_build_agent()` store the names alongside the cached agent.
`chat_stream()` passes them to the SSE layer via `engine.get_subagent_tool_names(preset_id)`.

## API changes

`GET /api/agents` response includes `subagent_ids` for each preset.
`POST /api/agents` and `PUT /api/agents/{id}` accept `subagent_ids`.
`GET /api/agents/available-subagents` returns all presets eligible as sub-agents
(excludes the `__chat__` builtin, used by the editor checkbox list).

## Config

```jsonc
"agent": {
  "max_subagent_depth": 2
}
```

Default `2` means: supervisor (depth 0) → sub-agent (depth 1) → sub-sub-agent (depth 2).
Set to `0` to disable sub-agents entirely at the framework level.

## Error handling

- **Circular reference**: skip with warning, do not add the tool.
- **Max depth exceeded**: skip with warning log; sub-agent's subagents are not added.
- **Sub-agent not found**: `_make_subagent_tool` returns `None`; skipped silently with warning.
- **Sub-agent runtime error**: `subagent_done` with `status: "error"`; sub-session marks error.
- **Sub-session DB write failure**: log warning, continue — the main SSE stream is not interrupted.

## Non-goals (V1)

- No sub-agent history persistence across separate parent-session turns (sub-agent starts fresh each time).
- No "resume interrupted sub-agent" flow (sub-agent interrupt handling is deferred).
- No memory sharing between sub-agent and parent agent (separate namespaces).
- No sub-agent management UI beyond the editor checkbox list (no visual graph editor).
- No migration compatibility for existing `tool_calls` JSON (early-stage project, no legacy data).
