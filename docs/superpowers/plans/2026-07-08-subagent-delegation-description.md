# Subagent Delegation Description Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace plain `subagent_ids` selection with relationship-level subagent links that require a delegation description, and surface those descriptions in the `task` tool seen by the parent agent.

**Architecture:** Introduce a `SubAgentLink` model shared by DB/API/runtime, migrate parent-agent configuration from `subagent_ids` to `subagents`, keep optional default descriptions for code agents/general-purpose as fallback, and have `AgentEngine` build `task` descriptions from the explicit relationship-level descriptions instead of `system_prompt[:200]`.

**Tech Stack:** Python 3.12, Pydantic, SQLModel/SQLite JSON fields, FastAPI, Vue 3 + Pinia + Element Plus, pytest, existing frontend contract scripts.

---

## File Map

**Backend models / persistence**
- Modify: `lc_agent/core/models.py`
- Modify: `lc_agent/db/models.py`
- Modify: `lc_agent/app.py`
- Modify: `lc_agent/server/routes/agents.py`
- Create: `lc_agent/db/migrations/versions/<timestamp>_replace_subagent_ids_with_subagents.py`

**Runtime / registration**
- Modify: `lc_agent/core/engine.py`
- Modify: `lc_agent/app.py`

**Frontend**
- Modify: `frontend/src/stores/agents.ts`
- Modify: `frontend/src/components/dialogs/AgentEditorDialog.vue`
- Modify: `frontend/scripts/check-agent-editor-general-purpose-contract.mjs`

**Tests**
- Modify: `tests/test_engine.py`
- Modify: `tests/test_engine_subagents.py`
- Modify: `tests/test_routes_agents.py`
- Modify: `tests/test_app.py`
- Modify: `frontend/scripts/check-subagent-reducers-contract.mjs` only if task description contract needs updates

---

### Task 1: Introduce `SubAgentLink` in core model and tests

**Files:**
- Modify: `lc_agent/core/models.py`
- Modify: `tests/test_engine.py`

- [ ] **Step 1: Write failing backend model tests**

Add/replace tests in `tests/test_engine.py` to assert:

```python
from lc_agent.core.models import AgentPreset, SubAgentLink


def test_agent_preset_accepts_subagents_links():
    preset = AgentPreset(
        id="p1",
        name="主智能体",
        system_prompt="x",
        default_model="m1",
        subagents=[
            SubAgentLink(
                agent_id="child-1",
                delegation_description="当你需要查询 funboost 知识时调用它",
            )
        ],
    )
    assert preset.subagents[0].agent_id == "child-1"


def test_agent_preset_defaults_subagents_to_none():
    preset = AgentPreset(id="p1", name="n", system_prompt="x", default_model="m1")
    assert preset.subagents is None
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine.py -q
```

Expected: FAIL because `SubAgentLink` / `subagents` do not exist yet.

- [ ] **Step 3: Implement minimal core model changes**

Update `lc_agent/core/models.py` to:

```python
from pydantic import BaseModel, Field


class SubAgentLink(BaseModel):
    agent_id: str
    delegation_description: str = Field(min_length=1)


class AgentPreset(BaseModel):
    ...
    subagents: list[SubAgentLink] | None = None
    enable_general_purpose_subagent: bool = False
```

Remove `subagent_ids` from the model once all call sites are migrated in later tasks.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine.py -q
```

Expected: PASS.

---

### Task 2: Move DB/API from `subagent_ids` to `subagents`

**Files:**
- Modify: `lc_agent/db/models.py`
- Modify: `lc_agent/server/routes/agents.py`
- Modify: `lc_agent/app.py`
- Modify: `tests/test_routes_agents.py`
- Modify: `tests/test_app.py`
- Create: `lc_agent/db/migrations/versions/<timestamp>_replace_subagent_ids_with_subagents.py`

- [ ] **Step 1: Write failing API tests for `subagents` payload**

Add tests asserting create/update/list payloads use:

```python
{
    "subagents": [
        {
            "agent_id": "funboost-agent",
            "delegation_description": "当你需要查询 funboost 知识时调用它",
        }
    ]
}
```

and that empty descriptions are rejected.

Example test skeleton in `tests/test_routes_agents.py`:

```python
def test_create_agent_preset_accepts_subagents(client):
    payload = {
        "name": "delegator",
        "system_prompt": "你可以委派任务",
        "default_model": "test-model",
        "subagents": [
            {
                "agent_id": "child-agent",
                "delegation_description": "当你需要查询 funboost 知识时调用它",
            }
        ],
    }
    resp = client.post("/api/agents", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["subagents"][0]["agent_id"] == "child-agent"
```

Add rejection test:

```python
def test_create_agent_preset_rejects_blank_subagent_description(client):
    payload = {
        "name": "delegator",
        "system_prompt": "你可以委派任务",
        "default_model": "test-model",
        "subagents": [{"agent_id": "child-agent", "delegation_description": "   "}],
    }
    resp = client.post("/api/agents", json=payload)
    assert resp.status_code == 422
```

- [ ] **Step 2: Run route tests to verify failure**

Run:

```bash
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_routes_agents.py tests/test_app.py -q
```

Expected: FAIL because route/db/app code still uses `subagent_ids`.

- [ ] **Step 3: Update DB model and migration**

Change `lc_agent/db/models.py` from:

```python
subagent_ids: list[str] | None = Field(default=None, sa_column=Column(JSON))
```

to:

```python
subagents: list[dict] | None = Field(default=None, sa_column=Column(JSON))
```

Add migration that renames/replaces the JSON column to `subagents` and converts old rows to:

```python
[{"agent_id": old_id, "delegation_description": ""} for old_id in old_subagent_ids]
```

No historical compatibility helpers beyond the schema/data conversion are needed.

- [ ] **Step 4: Update API schemas and serialization**

In `lc_agent/server/routes/agents.py`:

- Replace request/response `subagent_ids` with `subagents`
- Validate `delegation_description.strip()` is non-empty when subagents are provided
- Update `_preset_to_dict()` to emit `subagents`

Minimal target shape:

```python
class AgentPresetCreate(BaseModel):
    ...
    subagents: list[SubAgentLink] | None = None

class AgentPresetUpdate(BaseModel):
    ...
    subagents: list[SubAgentLink] | None = None
```

- [ ] **Step 5: Update preset loading from DB**

In `lc_agent/app.py`, when loading `AgentPresetDB`, map:

```python
subagents=[SubAgentLink(**item) for item in (row.subagents or [])] or None
```

- [ ] **Step 6: Re-run route/app tests**

Run:

```bash
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_routes_agents.py tests/test_app.py -q
```

Expected: PASS.

---

### Task 3: Add default delegation description support for code agents

**Files:**
- Modify: `lc_agent/app.py`
- Modify: `lc_agent/core/models.py`
- Modify: `tests/test_app.py`

- [ ] **Step 1: Write failing test for code agent default description**

Add a test in `tests/test_app.py` verifying `add_agent()` can register a code agent with a default delegation description and that this metadata is available in engine presets/registry.

Example:

```python
def test_add_agent_supports_default_delegation_description():
    app = LcAgentApp(MINIMAL_CONFIG)
    graph = object()
    app.add_agent(
        name="funboost智能体",
        graph=graph,
        description="Funboost 专家",
        delegation_description="当你需要查询 funboost 知识时调用它",
    )
    preset = app.engine._presets["funboost智能体"]
    assert preset.default_delegation_description == "当你需要查询 funboost 知识时调用它"
```

- [ ] **Step 2: Run app test to verify failure**

Run:

```bash
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_app.py -q
```

Expected: FAIL because `add_agent` does not accept the parameter yet.

- [ ] **Step 3: Implement code-agent default description**

Add optional field to `AgentPreset`:

```python
default_delegation_description: str = ""
```

Update `LcAgentApp.add_agent()` signature to:

```python
def add_agent(self, name: str, graph, description: str = "", delegation_description: str = ""):
```

When creating the in-memory preset for a code agent, set:

```python
default_delegation_description=delegation_description
```

- [ ] **Step 4: Re-run app test**

Run:

```bash
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_app.py -q
```

Expected: PASS.

---

### Task 4: Build runtime registry from `subagents` and explicit descriptions

**Files:**
- Modify: `lc_agent/core/engine.py`
- Modify: `tests/test_engine_subagents.py`

- [ ] **Step 1: Write failing registry tests**

Add tests for `_build_subagent_registry()` asserting:

1. It reads `parent.subagents`, not `subagent_ids`
2. Relationship-level `delegation_description` is used in the descriptor
3. Code-agent default description is used only as fallback
4. It never falls back to `system_prompt[:200]`

Example:

```python
def test_build_subagent_registry_uses_relationship_description():
    engine = AgentEngine(MINIMAL_CONFIG)
    engine._presets["child"] = AgentPreset(
        id="child",
        name="funboost智能体",
        system_prompt="内部 prompt 不应暴露",
        default_model="test-model",
        default_delegation_description="默认说明",
    )
    parent = AgentPreset(
        id="parent",
        name="主智能体",
        system_prompt="x",
        default_model="test-model",
        subagents=[
            SubAgentLink(
                agent_id="child",
                delegation_description="当你需要查询 funboost 知识时调用它",
            )
        ],
    )

    registry = engine._build_subagent_registry(parent, depth=0, building_set=frozenset())
    assert registry["funboost智能体"].delegation_description == "当你需要查询 funboost 知识时调用它"
```

- [ ] **Step 2: Run engine subagent tests to verify failure**

Run:

```bash
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine_subagents.py -q
```

Expected: FAIL because engine still reads `subagent_ids` and uses `description` from prompt/name.

- [ ] **Step 3: Update runtime descriptor and registry builder**

In `lc_agent/core/engine.py`:

- Change `SubAgentDescriptor.description` to `delegation_description`
- Replace loop over `preset.subagent_ids` with loop over `preset.subagents`
- Resolve each `SubAgentLink.agent_id`
- Populate descriptor with:

```python
delegation_description = (
    link.delegation_description.strip()
    or subagent_preset.default_delegation_description.strip()
    or "未提供委派描述，请仅在你明确知道其用途时调用"
)
```

- For `general-purpose`, use explicit default text instead of generic prompt-derived text.

- [ ] **Step 4: Re-run engine subagent tests**

Run:

```bash
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine_subagents.py -q
```

Expected: PASS.

---

### Task 5: Expose delegation descriptions in `task` tool text

**Files:**
- Modify: `lc_agent/core/engine.py`
- Modify: `tests/test_engine_subagents.py`

- [ ] **Step 1: Write failing task-description test**

Add a test asserting the generated `task` tool description contains both the `subagent_type` and the relationship-level description.

Example:

```python
def test_task_tool_description_contains_delegation_descriptions():
    ...
    task_tool = engine._make_task_tool(parent, registry, depth=1, building_set=frozenset({"parent"}))
    assert "funboost智能体: 当你需要查询 funboost 知识时调用它" in task_tool.description
```

- [ ] **Step 2: Run targeted test to verify failure**

Run:

```bash
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine_subagents.py::test_task_tool_description_contains_delegation_descriptions -q
```

Expected: FAIL because current description only lists names.

- [ ] **Step 3: Implement structured task description text**

Change `_make_task_tool()` description generation from simple CSV names to structured bullet text built from the registry:

```python
lines = [
    "Delegate a task to a sub-agent.",
    "",
    "Available subagent_type values:",
]
for key, descriptor in registry.items():
    lines.append(f"- {key}: {descriptor.delegation_description}")
lines.append("")
lines.append("Use description for the complete delegated task.")
description = "\n".join(lines)
```

- [ ] **Step 4: Re-run targeted engine test**

Run:

```bash
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine_subagents.py -q
```

Expected: PASS.

---

### Task 6: Update frontend store types and editor payloads

**Files:**
- Modify: `frontend/src/stores/agents.ts`
- Modify: `frontend/src/components/dialogs/AgentEditorDialog.vue`
- Modify: `frontend/scripts/check-agent-editor-general-purpose-contract.mjs`

- [ ] **Step 1: Write failing frontend contract checks**

Extend `frontend/scripts/check-agent-editor-general-purpose-contract.mjs` to assert the editor now uses `subagents` entries with `agent_id` and `delegation_description`, and blocks saving when a selected subagent has blank description.

Example string checks:

```js
expectIncludes('AgentEditorDialog.vue', content, 'delegation_description')
expectIncludes('AgentEditorDialog.vue', content, 'agent_id')
expectIncludes('AgentEditorDialog.vue', content, "subagents:")
expectIncludes('AgentEditorDialog.vue', content, 'trim()')
```

- [ ] **Step 2: Run contract to verify failure**

Run:

```bash
npm run test:agent-editor-general-purpose
```

Expected: FAIL because editor still uses `subagent_ids`.

- [ ] **Step 3: Update frontend types**

In `frontend/src/stores/agents.ts`, introduce:

```ts
export interface SubAgentLink {
  agent_id: string
  delegation_description: string
}
```

and replace `subagent_ids?: string[]` with `subagents?: SubAgentLink[]` in the agent preset type.

- [ ] **Step 4: Update editor form model and validation**

In `frontend/src/components/dialogs/AgentEditorDialog.vue`:

- Replace checkbox-only `subagent_ids` editing with editable rows storing `{ agent_id, delegation_description }`
- On save, reject rows whose description is blank after `trim()`
- Preserve `enable_general_purpose_subagent`

Keep the UI simple: select child agent + textarea/input for description per row.

- [ ] **Step 5: Re-run editor contract**

Run:

```bash
npm run test:agent-editor-general-purpose
```

Expected: PASS.

---

### Task 7: End-to-end verification

**Files:**
- Modify only if failures require minimal fixes in files above

- [ ] **Step 1: Run backend targeted suite**

Run:

```bash
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine.py tests/test_engine_subagents.py tests/test_routes_agents.py tests/test_app.py -q
```

Expected: PASS.

- [ ] **Step 2: Run frontend validation**

Run:

```bash
cd frontend
npm run test:agent-editor-general-purpose
npm run test:subagent-reducers
npm run build
```

Expected: PASS. Existing third-party build warnings may remain.

- [ ] **Step 3: Run full backend suite**

Run:

```bash
cd d:\codes\lc-agent
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/ -q
```

Expected: PASS.

---

## Self-Review

- Spec coverage: model/API/frontend/runtime/task-description/code-agent fallback all covered.
- No placeholders: every task names exact files, tests, and commands.
- Type consistency: use `SubAgentLink.agent_id`, `delegation_description`, `default_delegation_description`, `SubAgentDescriptor.delegation_description` consistently throughout.
