# Permanent Permissions (Tool Allowlist) Design

> Date: 2026-07-04  
> Branch: `feat/permanent-permissions`  
> Status: Draft

## Overview

Replace the current crude `dangerous_tools` + `interrupt_before=["tools"]` mechanism with a proper `HumanInTheLoopMiddleware`-based permission system. Users can permanently allow specific tools via the approval dialog or settings page; allowed tools skip human approval automatically.

## Requirements

1. **Global scope** — one permissions file shared across all projects and agents
2. **Per-tool granularity** — allowlist matches by tool name (extensible for future parameter matching)
3. **Replace `dangerous_tools`** — the new system is the sole authority for tool approval
4. **Default policy** — all tools require approval unless in the allowlist
5. **Storage** — JSONC file in the framework data directory
6. **Frontend** — approval dialog "permanently allow" button + Settings page for list management
7. **Backend judgment** — the `when` predicate in `HumanInTheLoopMiddleware` checks the allowlist server-side; frontend communicates via API

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend                                                     │
│                                                               │
│  InterruptDialog                  Settings/Permissions Page    │
│  ┌────────────────────────┐      ┌────────────────────────┐  │
│  │ [允许] [永久允许] [拒绝] │      │ 已允许工具列表 [+] [×] │  │
│  └───────────┬────────────┘      └───────────┬────────────┘  │
│              │                                │               │
└──────────────┼────────────────────────────────┼───────────────┘
               │ POST /api/permissions/allow    │ GET/PUT/DELETE
               ▼                                ▼
┌──────────────────────────────────────────────────────────────┐
│  Backend                                                      │
│                                                               │
│  PermissionsRouter (/api/permissions)                         │
│       │                                                       │
│       ▼                                                       │
│  PermissionsService (singleton)                               │
│       ├─ load()   → parse JSONC → in-memory cache            │
│       ├─ allow_tool(name)   → append + write back            │
│       ├─ remove_tool(name)  → remove + write back            │
│       ├─ is_allowed(name)   → O(1) set lookup               │
│       └─ get_all()          → return full config             │
│                                                               │
│  AgentEngine.build_agent()                                    │
│       └─ HumanInTheLoopMiddleware(                           │
│              interrupt_on={                                    │
│                  tool.name: InterruptOnConfig(                │
│                      allowed_decisions=["approve", "reject"], │
│                      when=lambda req: not svc.is_allowed(...) │
│                  )                                            │
│                  for tool in all_tools                        │
│              }                                                │
│          )                                                    │
└──────────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  <data_dir>/permissions.jsonc                                 │
└──────────────────────────────────────────────────────────────┘
```

## JSONC File Format

Location: `<data_dir>/permissions.jsonc` (alongside existing `settings.json`)

```jsonc
{
  // lc-agent 工具权限配置
  // 在此白名单中的工具将跳过人工审批，自动执行
  "version": 1,

  // 工具白名单 - 精确匹配工具名
  "tool_allowlist": [
    "web_search",
    "filesystem__read_file",
    "filesystem__list_directory"
  ]

  // 预留: 未来支持参数模式匹配
  // "tool_rules": [
  //   { "tool": "execute", "allow_when": { "command_prefix": ["git", "npm"] } }
  // ]
}
```

Default (file not exists or empty): `{ "version": 1, "tool_allowlist": [] }` → all tools need approval.

## Backend Components

### 1. PermissionsService (`lc_agent/core/permissions.py`)

```python
from langchain.agents.middleware import ToolCallRequest

class PermissionsService:
    """Manages tool permissions with JSONC file persistence."""

    def __init__(self, data_dir: Path):
        self._file_path = data_dir / "permissions.jsonc"
        self._allowlist: set[str] = set()
        self.load()

    def load(self) -> None:
        """Load permissions from JSONC file."""

    def is_allowed(self, tool_name: str) -> bool:
        """Check if a tool is in the allowlist (O(1) set lookup)."""
        return tool_name in self._allowlist

    def should_interrupt(self, request: ToolCallRequest) -> bool:
        """when predicate for HumanInTheLoopMiddleware.
        Returns True to interrupt, False to auto-approve."""
        return not self.is_allowed(request.tool_call["name"])

    def allow_tool(self, tool_name: str) -> None:
        """Add a tool to the allowlist and persist."""

    def remove_tool(self, tool_name: str) -> None:
        """Remove a tool from the allowlist and persist."""

    def get_allowlist(self) -> list[str]:
        """Return current allowlist as sorted list."""

    def set_allowlist(self, tools: list[str]) -> None:
        """Replace the entire allowlist."""
```

### 2. Engine Integration (`lc_agent/core/engine.py`)

Replace current logic:

```python
# BEFORE (to be removed):
if preset.dangerous_tools:
    kwargs["interrupt_before"] = ["tools"]

# AFTER:
from langchain.agents.middleware import HumanInTheLoopMiddleware

interrupt_on = {
    tool.name: {
        "allowed_decisions": ["approve", "reject"],
        "when": self._permissions_service.should_interrupt,
    }
    for tool in tools
}
middleware.append(HumanInTheLoopMiddleware(interrupt_on=interrupt_on))
```

Key behavior:
- `when` predicate queries `PermissionsService` at **runtime** for each tool call
- Allowlist changes take effect immediately (no agent rebuild needed)
- All tools are registered in `interrupt_on` → default is "interrupt unless allowed"

### 3. REST API (`lc_agent/server/routes/permissions.py`)

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/api/permissions` | — | `{ version, tool_allowlist }` |
| POST | `/api/permissions/allow` | `{ tool_name: str }` | `{ ok: true, tool_allowlist }` |
| POST | `/api/permissions/remove` | `{ tool_name: str }` | `{ ok: true, tool_allowlist }` |
| PUT | `/api/permissions` | `{ tool_allowlist: [...] }` | `{ ok: true, tool_allowlist }` |

### 4. SSE Interrupt Event Format Change

Current interrupt event only sends raw graph interrupt data. With `HumanInTheLoopMiddleware`, the interrupt value is a structured `HITLRequest`:

```json
{
  "type": "interrupt",
  "message": "Tool requires approval",
  "data": [{
    "value": {
      "action_requests": [
        {
          "name": "web_search",
          "args": { "query": "langchain docs" },
          "id": "call_abc123",
          "description": "Tool execution requires approval"
        }
      ],
      "review_configs": [
        { "allowed_decisions": ["approve", "reject"] }
      ]
    },
    "id": "interrupt_xyz"
  }]
}
```

Resume format changes to `HumanInTheLoopMiddleware` expected format:

```json
// Current: { "approved": true }
// New:
{ "decisions": [{ "type": "approve" }] }
// or
{ "decisions": [{ "type": "reject", "message": "用户拒绝" }] }
```

## Frontend Components

### 1. InterruptDialog Changes

Add third button "永久允许" to the approval dialog:

```
┌─────────────────────────────────────────┐
│  🔧 工具调用需要审批                       │
│                                          │
│  工具: web_search                         │
│  参数: { query: "langchain docs" }        │
│                                          │
│  [✓ 允许]  [✓ 永久允许此工具]  [✗ 拒绝]   │
└─────────────────────────────────────────┘
```

"永久允许此工具" click flow:
1. Call `POST /api/permissions/allow { tool_name }` 
2. Simultaneously send resume with `{ decisions: [{ type: "approve" }] }`
3. Future calls to this tool will not trigger interrupts

### 2. Settings Permissions Panel

New tab/section in Settings showing:
- Current `tool_allowlist` as a tag list
- Add tool manually (autocomplete from registered tools)
- Remove tool (click × on tag)
- Reset to empty (clear all)

### 3. Chat Store Changes (`frontend/src/stores/chat.ts`)

- Parse `HITLRequest` format from interrupt events (use `action_requests` / `review_configs`)
- New method `allowToolPermanently(toolName)` → calls permissions API + sends resume
- Update `respondToInterrupt` to use `{ decisions: [...] }` format

## Migration

1. **Remove `dangerous_tools` from `AgentPreset` model** — drop from DB schema, API, frontend editor
2. **Remove `interrupt_before` logic** from `engine.py`
3. **DB migration** — drop `dangerous_tools` column from agents table (no data to migrate, project is early-stage)

## File Changes Summary

| File | Action |
|------|--------|
| `lc_agent/core/permissions.py` | NEW — PermissionsService |
| `lc_agent/server/routes/permissions.py` | NEW — REST API |
| `lc_agent/core/engine.py` | MODIFY — replace interrupt_before with middleware |
| `lc_agent/core/models.py` | MODIFY — remove `dangerous_tools` field |
| `lc_agent/db/models.py` | MODIFY — drop column |
| `lc_agent/server/app.py` | MODIFY — register permissions router |
| `lc_agent/server/sse.py` | MODIFY — adapt interrupt/resume format |
| `frontend/src/api/sse-client.ts` | MODIFY — new resume format |
| `frontend/src/stores/chat.ts` | MODIFY — parse HITLRequest, add allow method |
| `frontend/src/components/chat/InterruptDialog.vue` | MODIFY — add "永久允许" button |
| `frontend/src/views/SettingsView.vue` (or new component) | MODIFY — add permissions panel |
| `frontend/src/components/dialogs/AgentEditorDialog.vue` | MODIFY — remove dangerous_tools UI |
| DB migration | NEW — drop dangerous_tools column |

## Extensibility (Future)

The `version: 1` format and `should_interrupt(request: ToolCallRequest)` predicate naturally support future extensions:

- **Parameter matching**: `tool_rules` with `allow_when` conditions checking `request.tool_call["args"]`
- **Per-agent overrides**: extend JSONC with `agent_overrides` section
- **Session-scoped auto-approve**: add "auto-approve this session" button (stored in memory, not file)
- **Approval modes**: "always_ask" / "granular" / "auto_approve_all" global switch

## Edge Cases & Clarifications

### `ask_user` tool coexistence

The `ask_user` tool uses `interrupt()` directly inside the tool body — this is a **separate mechanism** from `HumanInTheLoopMiddleware`. They coexist naturally:
- `ask_user` → `interrupt()` produces `{ type: "ask_user", question: ... }`
- Other tools → `HumanInTheLoopMiddleware` produces `{ action_requests: [...], review_configs: [...] }`

The `ask_user` tool should be **excluded** from `interrupt_on` (or set to `False`) to avoid double-interrupting:

```python
interrupt_on = {
    tool.name: {
        "allowed_decisions": ["approve", "reject"],
        "when": self._permissions_service.should_interrupt,
    }
    for tool in tools
    if tool.name != "ask_user"  # ask_user handles its own interrupts
}
```

### Data directory location

`data_dir` is resolved from config at startup (same location as existing `settings.json`). For `lc-agent-bfzs`, this would be the project's configured data directory. The `PermissionsService` receives `data_dir` as a `Path` from the application bootstrap.

### File corruption handling

If `permissions.jsonc` is corrupted (invalid JSON):
- Log a warning
- Fall back to empty allowlist (all tools need approval — safe default)
- Do NOT overwrite the corrupted file until user explicitly saves via API

### Resume format backward compatibility

The resume format changes from `{ approved: bool }` to `{ decisions: [{ type: "approve"|"reject" }] }`. This is a **breaking change** in the SSE protocol. Since the project is early-stage with no users, no migration is needed. The frontend and backend must be deployed together.

## Testing

- Unit test `PermissionsService` (load, save, is_allowed, CRUD)
- Unit test `should_interrupt` predicate with mock ToolCallRequest
- Integration test: tool in allowlist → no interrupt event emitted
- Integration test: tool not in allowlist → interrupt + resume flow works
- Frontend: InterruptDialog renders three buttons, "永久允许" calls API
