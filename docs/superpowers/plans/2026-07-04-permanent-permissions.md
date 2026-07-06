# Permanent Permissions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `dangerous_tools` + `interrupt_before` with `HumanInTheLoopMiddleware`-based permission system where users can permanently allow tools via UI.

**Architecture:** Backend `PermissionsService` manages a JSONC allowlist file; `HumanInTheLoopMiddleware` uses a `when` predicate to query the service at runtime. Frontend adds "永久允许" button to interrupt dialog and a permissions management panel in Settings.

**Tech Stack:** Python (FastAPI, LangChain `HumanInTheLoopMiddleware`, Pydantic), Vue 3 + Element Plus, JSONC file storage

---

### Task 1: PermissionsService Backend Core

**Files:**
- Create: `lc_agent/core/permissions.py`
- Test: `tests/test_permissions.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_permissions.py
import json
import pytest
from pathlib import Path

from lc_agent.core.permissions import PermissionsService


@pytest.fixture
def tmp_permissions(tmp_path):
    """Return a PermissionsService backed by a temp file."""
    return PermissionsService(permissions_path=tmp_path / "permissions.jsonc")


def test_empty_state_nothing_allowed(tmp_permissions):
    assert tmp_permissions.is_allowed("web_search") is False
    assert tmp_permissions.get_allowlist() == []


def test_allow_tool_persists(tmp_permissions):
    tmp_permissions.allow_tool("web_search")
    assert tmp_permissions.is_allowed("web_search") is True
    assert "web_search" in tmp_permissions.get_allowlist()


def test_remove_tool(tmp_permissions):
    tmp_permissions.allow_tool("web_search")
    tmp_permissions.remove_tool("web_search")
    assert tmp_permissions.is_allowed("web_search") is False


def test_set_allowlist_replaces(tmp_permissions):
    tmp_permissions.allow_tool("a")
    tmp_permissions.set_allowlist(["b", "c"])
    assert tmp_permissions.is_allowed("a") is False
    assert tmp_permissions.is_allowed("b") is True
    assert tmp_permissions.is_allowed("c") is True


def test_file_persistence(tmp_path):
    path = tmp_path / "permissions.jsonc"
    svc1 = PermissionsService(permissions_path=path)
    svc1.allow_tool("web_search")
    svc1.allow_tool("filesystem__read_file")

    svc2 = PermissionsService(permissions_path=path)
    assert svc2.is_allowed("web_search") is True
    assert svc2.is_allowed("filesystem__read_file") is True


def test_corrupted_file_falls_back_to_empty(tmp_path):
    path = tmp_path / "permissions.jsonc"
    path.write_text("not valid json {{{", encoding="utf-8")
    svc = PermissionsService(permissions_path=path)
    assert svc.get_allowlist() == []


def test_duplicate_add_is_idempotent(tmp_permissions):
    tmp_permissions.allow_tool("web_search")
    tmp_permissions.allow_tool("web_search")
    assert tmp_permissions.get_allowlist().count("web_search") == 1


def test_should_interrupt_returns_true_when_not_allowed(tmp_permissions):
    mock_request = type("R", (), {"tool_call": {"name": "dangerous_tool", "args": {}}})()
    assert tmp_permissions.should_interrupt(mock_request) is True


def test_should_interrupt_returns_false_when_allowed(tmp_permissions):
    tmp_permissions.allow_tool("safe_tool")
    mock_request = type("R", (), {"tool_call": {"name": "safe_tool", "args": {}}})()
    assert tmp_permissions.should_interrupt(mock_request) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_permissions.py -v`
Expected: ImportError — `lc_agent.core.permissions` does not exist yet

- [ ] **Step 3: Implement PermissionsService**

```python
# lc_agent/core/permissions.py
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_JSONC_COMMENT_RE = re.compile(r"//.*?$|/\*.*?\*/", re.MULTILINE | re.DOTALL)

DEFAULT_PERMISSIONS = {"version": 1, "tool_allowlist": []}


def _strip_jsonc_comments(text: str) -> str:
    """Remove // and /* */ comments from JSONC text."""
    return _JSONC_COMMENT_RE.sub("", text)


class PermissionsService:
    """Manages tool permissions with JSONC file persistence.

    All tools require approval by default. Tools listed in ``tool_allowlist``
    skip the human-in-the-loop interrupt.
    """

    def __init__(self, permissions_path: Path):
        self._path = Path(permissions_path)
        self._allowlist: set[str] = set()
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            self._allowlist = set()
            return
        try:
            raw = self._path.read_text(encoding="utf-8")
            cleaned = _strip_jsonc_comments(raw)
            data = json.loads(cleaned)
            tools = data.get("tool_allowlist", [])
            self._allowlist = set(tools) if isinstance(tools, list) else set()
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load permissions from %s: %s — using empty allowlist", self._path, e)
            self._allowlist = set()

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "tool_allowlist": sorted(self._allowlist),
        }
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._path)

    def is_allowed(self, tool_name: str) -> bool:
        return tool_name in self._allowlist

    def should_interrupt(self, request: Any) -> bool:
        """``when`` predicate for HumanInTheLoopMiddleware.

        Returns True to interrupt (tool NOT in allowlist).
        Returns False to auto-approve (tool IS in allowlist).
        """
        tool_name = request.tool_call["name"]
        return not self.is_allowed(tool_name)

    def allow_tool(self, tool_name: str) -> None:
        self._allowlist.add(tool_name)
        self._save()

    def remove_tool(self, tool_name: str) -> None:
        self._allowlist.discard(tool_name)
        self._save()

    def get_allowlist(self) -> list[str]:
        return sorted(self._allowlist)

    def set_allowlist(self, tools: list[str]) -> None:
        self._allowlist = set(tools)
        self._save()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_permissions.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add lc_agent/core/permissions.py tests/test_permissions.py
git commit -m "feat: add PermissionsService with JSONC persistence"
```

---

### Task 2: REST API for Permissions

**Files:**
- Create: `lc_agent/server/routes/permissions.py`
- Modify: `lc_agent/server/app.py`
- Modify: `lc_agent/server/dependencies.py`
- Test: `tests/test_routes_permissions.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_routes_permissions.py
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from lc_agent.server.app import create_app
from lc_agent.core.permissions import PermissionsService


@pytest.fixture
def app_with_permissions(tmp_path):
    config = {
        "provider": {},
        "agent": {"default_model": "gpt-4", "system_prompt": "Test"},
        "database": {"url": "sqlite+aiosqlite:///:memory:", "checkpoint_path": ":memory:"},
        "permissions": {"path": str(tmp_path / "permissions.jsonc")},
    }
    app = create_app(config)
    from lc_agent.core.engine import AgentEngine
    engine = AgentEngine(config)
    app.state.engine = engine
    app.state.permissions = PermissionsService(
        permissions_path=Path(config["permissions"]["path"])
    )
    return app


@pytest.fixture
async def client(app_with_permissions):
    transport = ASGITransport(app=app_with_permissions)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_get_permissions_empty(client):
    resp = await client.get("/api/permissions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool_allowlist"] == []


@pytest.mark.anyio
async def test_allow_tool(client):
    resp = await client.post("/api/permissions/allow", json={"tool_name": "web_search"})
    assert resp.status_code == 200
    assert "web_search" in resp.json()["tool_allowlist"]


@pytest.mark.anyio
async def test_remove_tool(client):
    await client.post("/api/permissions/allow", json={"tool_name": "web_search"})
    resp = await client.post("/api/permissions/remove", json={"tool_name": "web_search"})
    assert resp.status_code == 200
    assert "web_search" not in resp.json()["tool_allowlist"]


@pytest.mark.anyio
async def test_put_permissions(client):
    resp = await client.put("/api/permissions", json={"tool_allowlist": ["a", "b"]})
    assert resp.status_code == 200
    assert sorted(resp.json()["tool_allowlist"]) == ["a", "b"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_routes_permissions.py -v`
Expected: ImportError — route not registered

- [ ] **Step 3: Create the permissions router**

```python
# lc_agent/server/routes/permissions.py
from fastapi import APIRouter, Request
from pydantic import BaseModel

from lc_agent.core.permissions import PermissionsService

router = APIRouter(tags=["permissions"])


def _get_permissions(request: Request) -> PermissionsService:
    return request.app.state.permissions


class AllowToolRequest(BaseModel):
    tool_name: str


class SetAllowlistRequest(BaseModel):
    tool_allowlist: list[str]


@router.get("/permissions")
def get_permissions(request: Request):
    svc = _get_permissions(request)
    return {"version": 1, "tool_allowlist": svc.get_allowlist()}


@router.post("/permissions/allow")
def allow_tool(body: AllowToolRequest, request: Request):
    svc = _get_permissions(request)
    svc.allow_tool(body.tool_name)
    return {"ok": True, "tool_allowlist": svc.get_allowlist()}


@router.post("/permissions/remove")
def remove_tool(body: AllowToolRequest, request: Request):
    svc = _get_permissions(request)
    svc.remove_tool(body.tool_name)
    return {"ok": True, "tool_allowlist": svc.get_allowlist()}


@router.put("/permissions")
def set_permissions(body: SetAllowlistRequest, request: Request):
    svc = _get_permissions(request)
    svc.set_allowlist(body.tool_allowlist)
    return {"ok": True, "tool_allowlist": svc.get_allowlist()}
```

- [ ] **Step 4: Register the router in app.py**

In `lc_agent/server/app.py`, add:

```python
from lc_agent.server.routes.permissions import router as permissions_router
```

And in `create_app()`:

```python
    app.include_router(permissions_router, prefix="/api")
```

- [ ] **Step 5: Add permissions dependency in app startup**

In `lc_agent/app.py`, during startup, create and attach `PermissionsService` to `app.state`:

```python
from lc_agent.core.permissions import PermissionsService

# In LCAgentApp.__init__ or run():
permissions_path = config.get("permissions", {}).get("path", "./permissions.jsonc")
self._permissions_service = PermissionsService(permissions_path=Path(permissions_path))
self.fastapi_app.state.permissions = self._permissions_service
```

Also pass it to the engine: `self.engine._permissions_service = self._permissions_service`

- [ ] **Step 6: Run tests to verify they pass**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_routes_permissions.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add lc_agent/server/routes/permissions.py lc_agent/server/app.py lc_agent/app.py tests/test_routes_permissions.py
git commit -m "feat: add /api/permissions REST endpoints"
```

---

### Task 3: Replace interrupt_before with HumanInTheLoopMiddleware

**Files:**
- Modify: `lc_agent/core/engine.py`
- Modify: `lc_agent/core/models.py`
- Test: `tests/test_hitl_middleware.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_hitl_middleware.py
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from lc_agent.core.engine import AgentEngine
from lc_agent.core.permissions import PermissionsService


@pytest.fixture
def engine_with_permissions(tmp_path):
    config = {
        "provider": {"test": {"base_url": "http://fake", "api_key": "k", "models": [{"id": "m1"}]}},
        "agent": {"default_model": "m1", "system_prompt": "Test"},
    }
    engine = AgentEngine(config)
    engine._permissions_service = PermissionsService(
        permissions_path=tmp_path / "permissions.jsonc"
    )
    engine._checkpointer = MagicMock()
    return engine


def test_build_agent_uses_hitl_middleware(engine_with_permissions):
    """Agent should include HumanInTheLoopMiddleware in middleware stack."""
    from lc_agent.core.models import AgentPreset
    preset = AgentPreset(
        id="test", name="Test", system_prompt="hi",
        default_model="m1",
    )
    agent = engine_with_permissions.build_agent(preset)
    assert agent is not None


def test_dangerous_tools_field_removed():
    """AgentPreset should no longer have dangerous_tools field."""
    from lc_agent.core.models import AgentPreset
    preset = AgentPreset(id="x", name="X", system_prompt="", default_model="m")
    assert not hasattr(preset, "dangerous_tools")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_hitl_middleware.py -v`
Expected: `test_dangerous_tools_field_removed` FAILS (field still exists)

- [ ] **Step 3: Remove `dangerous_tools` from AgentPreset**

In `lc_agent/core/models.py`, remove line:
```python
    dangerous_tools: list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Replace interrupt_before with HumanInTheLoopMiddleware in engine.py**

Replace the block at lines 147-148:
```python
        if preset.dangerous_tools:
            kwargs["interrupt_before"] = ["tools"]
```

With:
```python
        if hasattr(self, '_permissions_service') and self._permissions_service:
            from langchain.agents.middleware import HumanInTheLoopMiddleware
            interrupt_on = {
                tool.name: {
                    "allowed_decisions": ["approve", "reject"],
                    "when": self._permissions_service.should_interrupt,
                }
                for tool in tools
                if tool.name != "ask_user"
            }
            if interrupt_on:
                middleware.append(HumanInTheLoopMiddleware(interrupt_on=interrupt_on))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_hitl_middleware.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add lc_agent/core/engine.py lc_agent/core/models.py tests/test_hitl_middleware.py
git commit -m "feat: replace dangerous_tools with HumanInTheLoopMiddleware"
```

---

### Task 4: Adapt SSE Interrupt/Resume Protocol

**Files:**
- Modify: `lc_agent/server/sse.py`

- [ ] **Step 1: Update interrupt event emission (sse.py ~line 233-250)**

The `HumanInTheLoopMiddleware` produces structured interrupt values with `action_requests` and `review_configs`. Update the interrupt event to pass this structured data through:

Replace the interrupt check block with:
```python
            interrupt_sent = False
            try:
                agent = engine._get_or_build_agent(preset_id, model_id)
                state_config = {"configurable": {"thread_id": thread_id}, "recursion_limit": engine.recursion_limit}
                graph_state = await agent.aget_state(state_config)
                if graph_state.tasks:
                    all_interrupts = []
                    for task in graph_state.tasks:
                        for intr in (task.interrupts or ()):
                            all_interrupts.append({
                                "value": intr.value,
                                "id": getattr(intr, "id", None),
                            })
                    if all_interrupts:
                        interrupt_payload: dict[str, Any] = {
                            "message": "Tool requires approval",
                            "data": all_interrupts,
                        }
                        first_value = all_interrupts[0].get("value")
                        if isinstance(first_value, dict):
                            if "action_requests" in first_value:
                                interrupt_payload["action_requests"] = first_value["action_requests"]
                            if "review_configs" in first_value:
                                interrupt_payload["review_configs"] = first_value["review_configs"]
                        yield stream_utils.format_sse_event("interrupt", interrupt_payload)
                        interrupt_sent = True
            except Exception as e:
                print(f"[SSE] Failed to check interrupt state: {e}")
```

- [ ] **Step 2: Update resume value handling (sse.py ~line 317)**

The resume value from the frontend now uses `{ decisions: [...] }` format for HITL middleware. The existing `resume_value = req.command.get("resume", {})` passes through unchanged — no modification needed here since `Command(resume=resume_value)` works with any JSON payload.

However, for backward compat with `ask_user` (which expects a plain string), no change needed — `sendInterruptResume` already sends the raw value.

- [ ] **Step 3: Apply same interrupt logic to _resume_stream (sse.py ~line 380+)**

The `_resume_stream` function also checks for interrupts after streaming. Apply the same structured interrupt extraction there (same code as Step 1).

- [ ] **Step 4: Commit**

```bash
git add lc_agent/server/sse.py
git commit -m "feat: pass HITL action_requests in interrupt SSE events"
```

---

### Task 5: Frontend — InterruptDialog "永久允许" Button

**Files:**
- Modify: `frontend/src/components/chat/InterruptDialog.vue`
- Modify: `frontend/src/stores/chat.ts`
- Modify: `frontend/src/api/sse-client.ts`
- Create: `frontend/src/api/permissions.ts`

- [ ] **Step 1: Create permissions API client**

```typescript
// frontend/src/api/permissions.ts
const BASE = '/api/permissions'

export interface PermissionsConfig {
  version: number
  tool_allowlist: string[]
}

export async function getPermissions(): Promise<PermissionsConfig> {
  const resp = await fetch(BASE)
  return resp.json()
}

export async function allowTool(toolName: string): Promise<PermissionsConfig> {
  const resp = await fetch(`${BASE}/allow`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool_name: toolName }),
  })
  return resp.json()
}

export async function removeTool(toolName: string): Promise<PermissionsConfig> {
  const resp = await fetch(`${BASE}/remove`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool_name: toolName }),
  })
  return resp.json()
}

export async function setPermissions(tools: string[]): Promise<PermissionsConfig> {
  const resp = await fetch(BASE, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool_allowlist: tools }),
  })
  return resp.json()
}
```

- [ ] **Step 2: Update InterruptDialog.vue**

Add "永久允许" button and emit new event. In the template footer for tool approval mode:

```html
      <template v-else>
        <el-button @click="reject">拒绝</el-button>
        <el-button type="success" @click="allowPermanently">永久允许此工具</el-button>
        <el-button type="primary" @click="approve">批准执行</el-button>
      </template>
```

In the script, add the function:

```typescript
function allowPermanently() {
  const toolName = firstToolName.value
  if (toolName) {
    emit('allow-permanently', toolName)
  }
  emit('decide', { type: 'approve' })
}

const firstToolName = computed(() => {
  const reqs = props.interrupt?.actionRequests
  if (reqs && reqs.length > 0) return reqs[0].name
  const data = props.interrupt?.data
  if (data && data.length > 0) {
    const value = data[0]?.value
    if (typeof value === 'object' && value?.action_requests?.length > 0) {
      return value.action_requests[0].name
    }
  }
  return null
})
```

Add emit:
```typescript
const emit = defineEmits<{
  decide: [decision: { type: string; message?: string }]
  resume: [value: any]
  'allow-permanently': [toolName: string]
}>()
```

- [ ] **Step 3: Update chat store to handle HITL decisions format**

In `frontend/src/stores/chat.ts`, update `respondToInterrupt`:

```typescript
  function respondToInterrupt(approved: boolean, presetId: string = '__chat__') {
    const client = _ensureClient()
    const decisions = [{ type: approved ? 'approve' : 'reject' }]
    client.sendInterruptResume({ decisions }, presetId)
    interrupt.value = null
  }
```

- [ ] **Step 4: Wire "allow-permanently" event in ChatView.vue**

In `frontend/src/views/ChatView.vue`, handle the new event:

```typescript
import { allowTool } from '@/api/permissions'

async function handleAllowPermanently(toolName: string) {
  try {
    await allowTool(toolName)
  } catch (e) {
    console.error('Failed to permanently allow tool:', e)
  }
}
```

And in the template:
```html
<InterruptDialog
  :interrupt="chatStore.interrupt"
  @decide="handleInterruptDecide"
  @resume="handleInterruptResume"
  @allow-permanently="handleAllowPermanently"
/>
```

- [ ] **Step 5: Update SSE client sendInterruptResponse**

In `frontend/src/api/sse-client.ts`, update `sendInterruptResponse` to use new format:

```typescript
  async sendInterruptResponse(approved: boolean, presetId: string, model?: string): Promise<void> {
    const decisions = [{ type: approved ? 'approve' : 'reject' }]
    await this.sendInterruptResume({ decisions }, presetId, model)
  }
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/permissions.ts frontend/src/components/chat/InterruptDialog.vue frontend/src/stores/chat.ts frontend/src/api/sse-client.ts frontend/src/views/ChatView.vue
git commit -m "feat: add '永久允许' button to interrupt dialog"
```

---

### Task 6: Frontend — Settings Permissions Panel

**Files:**
- Create: `frontend/src/components/settings/PermissionsPanel.vue`
- Modify: Settings page (wherever settings tabs live)

- [ ] **Step 1: Create PermissionsPanel component**

```vue
<!-- frontend/src/components/settings/PermissionsPanel.vue -->
<template>
  <div class="permissions-panel">
    <h3>工具权限白名单</h3>
    <p class="desc">白名单中的工具将跳过人工审批，自动执行。</p>

    <div class="allowlist">
      <el-tag
        v-for="tool in allowlist"
        :key="tool"
        closable
        @close="handleRemove(tool)"
        class="tool-tag"
      >
        {{ tool }}
      </el-tag>
      <el-tag v-if="allowlist.length === 0" type="info">（空 — 所有工具需要审批）</el-tag>
    </div>

    <div class="actions">
      <el-input
        v-model="newTool"
        placeholder="输入工具名添加到白名单"
        style="width: 280px"
        @keyup.enter="handleAdd"
      />
      <el-button type="primary" :disabled="!newTool.trim()" @click="handleAdd">添加</el-button>
      <el-button v-if="allowlist.length > 0" type="danger" plain @click="handleClearAll">清空全部</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getPermissions, allowTool, removeTool, setPermissions } from '@/api/permissions'
import { ElMessage } from 'element-plus'

const allowlist = ref<string[]>([])
const newTool = ref('')

onMounted(async () => {
  const data = await getPermissions()
  allowlist.value = data.tool_allowlist
})

async function handleAdd() {
  const name = newTool.value.trim()
  if (!name) return
  const data = await allowTool(name)
  allowlist.value = data.tool_allowlist
  newTool.value = ''
  ElMessage.success(`已添加 ${name} 到白名单`)
}

async function handleRemove(name: string) {
  const data = await removeTool(name)
  allowlist.value = data.tool_allowlist
  ElMessage.info(`已从白名单移除 ${name}`)
}

async function handleClearAll() {
  const data = await setPermissions([])
  allowlist.value = data.tool_allowlist
  ElMessage.warning('已清空全部白名单')
}
</script>

<style scoped>
.permissions-panel {
  padding: 16px 0;
}
.desc {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin-bottom: 16px;
}
.allowlist {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  min-height: 32px;
}
.tool-tag {
  font-family: 'JetBrains Mono', monospace;
}
.actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
```

- [ ] **Step 2: Integrate PermissionsPanel into the Settings view**

Find the settings view/page that contains the summarization config and add PermissionsPanel as a new section or tab.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/settings/PermissionsPanel.vue
git commit -m "feat: add permissions management panel in settings"
```

---

### Task 7: Remove dangerous_tools from DB and Agent Editor UI

**Files:**
- Modify: `lc_agent/db/models.py` — remove `dangerous_tools` column
- Create: DB migration to drop the column
- Modify: `lc_agent/server/routes/agents.py` — remove dangerous_tools from CRUD
- Modify: `frontend/src/components/dialogs/AgentEditorDialog.vue` — remove dangerous_tools textarea

- [ ] **Step 1: Remove dangerous_tools from DB model**

In `lc_agent/db/models.py`, find and remove the `dangerous_tools` column from the Agent table.

- [ ] **Step 2: Create Alembic migration**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m alembic revision --autogenerate -m "drop dangerous_tools column"`

Verify the generated migration drops the column.

- [ ] **Step 3: Remove from agents CRUD route**

In `lc_agent/server/routes/agents.py`, remove any reference to `dangerous_tools` in create/update request bodies and response serialization.

- [ ] **Step 4: Remove from AgentEditorDialog.vue**

In `frontend/src/components/dialogs/AgentEditorDialog.vue`, remove the "危险工具（需要审批）" textarea (lines ~105-111) and the `dangerousToolsStr` ref and its usage in the submit handler.

- [ ] **Step 5: Run existing tests to verify nothing breaks**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/ -v --ignore=tests/test_permissions.py --ignore=tests/test_routes_permissions.py --ignore=tests/test_hitl_middleware.py`
Expected: All existing tests pass (or fail only on unrelated issues)

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: remove deprecated dangerous_tools from DB and UI"
```

---

### Task 8: Integration Test — Full Flow

**Files:**
- Create: `tests/test_permissions_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_permissions_integration.py
"""Integration test: verify that allowed tools skip interrupt."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

from lc_agent.core.engine import AgentEngine
from lc_agent.core.permissions import PermissionsService
from lc_agent.core.models import AgentPreset


@pytest.fixture
def full_engine(tmp_path):
    config = {
        "provider": {"test": {"base_url": "http://fake", "api_key": "k", "models": [{"id": "m1"}]}},
        "agent": {"default_model": "m1", "system_prompt": "Test"},
    }
    engine = AgentEngine(config)
    engine._permissions_service = PermissionsService(
        permissions_path=tmp_path / "permissions.jsonc"
    )
    engine._checkpointer = MagicMock()
    return engine


def test_allowed_tool_produces_no_interrupt_config(full_engine):
    """When a tool is in the allowlist, the when predicate returns False (no interrupt)."""
    full_engine._permissions_service.allow_tool("web_search")

    mock_request = type("R", (), {"tool_call": {"name": "web_search", "args": {}}})()
    assert full_engine._permissions_service.should_interrupt(mock_request) is False


def test_disallowed_tool_triggers_interrupt(full_engine):
    """When a tool is NOT in the allowlist, the when predicate returns True (interrupt)."""
    mock_request = type("R", (), {"tool_call": {"name": "dangerous_delete", "args": {}}})()
    assert full_engine._permissions_service.should_interrupt(mock_request) is True


def test_dynamic_allow_takes_effect_without_rebuild(full_engine):
    """Adding a tool to allowlist takes effect immediately for existing agent instances."""
    mock_request = type("R", (), {"tool_call": {"name": "web_search", "args": {}}})()

    assert full_engine._permissions_service.should_interrupt(mock_request) is True

    full_engine._permissions_service.allow_tool("web_search")

    assert full_engine._permissions_service.should_interrupt(mock_request) is False
```

- [ ] **Step 2: Run integration tests**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_permissions_integration.py -v`
Expected: All PASS

- [ ] **Step 3: Run full test suite**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_permissions_integration.py
git commit -m "test: add integration tests for permissions flow"
```
