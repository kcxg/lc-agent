# Task Subagent Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace lc-agent's per-subagent `subagent_xxx` tools with a deepagents-style unified `task(subagent_type, description)` tool, including a per-agent general-purpose subagent switch.

**Architecture:** The engine will build a per-agent subagent registry and expose one `task` tool when the registry is non-empty. SSE and persistence will classify `task` calls by `subagent_type` instead of by per-tool names. The frontend will persist and display `enable_general_purpose_subagent` and continue rendering subagent cards using display names, not the raw `task` tool name.

**Tech Stack:** Python 3.12, LangChain `create_agent`, LangGraph event streams, SQLModel/Alembic, FastAPI, Vue 3, Pinia, Element Plus, pytest, Vite.

---

## Reference Spec

- [2026-07-08-task-subagent-mode-design.md](file:///d:/codes/lc-agent/docs/superpowers/specs/2026-07-08-task-subagent-mode-design.md)

## Global Rules for Execution

- Use `D:\ProgramData\Miniconda3\envs\py312\python.exe` for all Python commands.
- Do not hardcode API keys or secrets.
- Do not create compatibility migrations for old behavior beyond the explicitly listed Alembic schema addition.
- Do not commit unless the user explicitly asks.
- Do not add code comments unless the user asks; keep implementation self-explanatory.
- For LangChain/LangGraph API uncertainty, check the enabled LangChain docs/reference MCP descriptors before coding.

## File Map

### Backend core

- Modify: [models.py](file:///d:/codes/lc-agent/lc_agent/core/models.py)
  - Add `enable_general_purpose_subagent` to `AgentPreset`.
- Modify: [models.py](file:///d:/codes/lc-agent/lc_agent/db/models.py)
  - Add DB field to `AgentPresetDB`.
- Create: `d:\codes\lc-agent\lc_agent\db\migrations\versions\20260708_add_general_purpose_subagent.py`
  - Add/drop `enable_general_purpose_subagent` column.
- Modify: [agents.py](file:///d:/codes/lc-agent/lc_agent/server/routes/agents.py)
  - Add request/response persistence for the new field.
- Modify: [engine.py](file:///d:/codes/lc-agent/lc_agent/core/engine.py)
  - Replace `_make_subagent_tool()` usage with a unified task tool registry.
  - Keep `_depth` as safety protection.
  - Build general-purpose worker with no task tool.
  - Change subagent display metadata from tool-name keyed to `subagent_type` keyed.

### Backend streaming and persistence

- Modify: [stream_utils.py](file:///d:/codes/lc-agent/lc_agent/server/stream_utils.py)
  - Detect subagent boundaries using `tool_name == "task"` and `input.subagent_type`.
  - Map `description` to the existing `query` field for frontend compatibility.
  - Ensure display names do not become `task`.
- Modify: [subagent_tracker.py](file:///d:/codes/lc-agent/lc_agent/server/subagent_tracker.py)
  - Treat payload `name`/`subagent_type` as display source.
- Inspect and modify if needed: [sse.py](file:///d:/codes/lc-agent/lc_agent/server/sse.py)
  - Ensure it passes the new display map into stream utilities and tracker.

### Frontend

- Modify: [agents.ts](file:///d:/codes/lc-agent/frontend/src/stores/agents.ts)
  - Add `enable_general_purpose_subagent` to `AgentPreset`.
- Modify: [AgentEditorDialog.vue](file:///d:/codes/lc-agent/frontend/src/components/dialogs/AgentEditorDialog.vue)
  - Add the general-purpose checkbox in the subagent tab.
  - Persist the new field on create/update.
  - Default new agents to disabled.
- Inspect and modify if needed: [http.ts](file:///d:/codes/lc-agent/frontend/src/api/http.ts)
  - Ensure API typing/payloads do not strip the new field.
- Inspect and modify if needed: [SubAgentCard.vue](file:///d:/codes/lc-agent/frontend/src/components/chat/SubAgentCard.vue)
  - Ensure card title uses display name, not raw `task`.
- Inspect and modify if needed: [chat.ts](file:///d:/codes/lc-agent/frontend/src/stores/chat.ts)
  - Ensure reducer accepts task-mode `subagent_start` / `tool_call` payloads.

### Tests and checks

- Modify: [test_engine_subagents.py](file:///d:/codes/lc-agent/tests/test_engine_subagents.py)
- Modify: [test_stream_utils_subagents.py](file:///d:/codes/lc-agent/tests/test_stream_utils_subagents.py)
- Modify: [test_subagent_run_tracker.py](file:///d:/codes/lc-agent/tests/test_subagent_run_tracker.py)
- Modify: [test_routes_agents.py](file:///d:/codes/lc-agent/tests/test_routes_agents.py)
- Modify or create: `d:\codes\lc-agent\frontend\scripts\check-subagent-reducers-contract.mjs`
- Create if needed: `d:\codes\lc-agent\frontend\scripts\check-agent-editor-general-purpose-contract.mjs`

---

## Task 1: Add AgentPreset and API Field

**Files:**
- Modify: [models.py](file:///d:/codes/lc-agent/lc_agent/core/models.py)
- Modify: [models.py](file:///d:/codes/lc-agent/lc_agent/db/models.py)
- Create: `d:\codes\lc-agent\lc_agent\db\migrations\versions\20260708_add_general_purpose_subagent.py`
- Modify: [agents.py](file:///d:/codes/lc-agent/lc_agent/server/routes/agents.py)
- Test: [test_routes_agents.py](file:///d:/codes/lc-agent/tests/test_routes_agents.py)

- [ ] **Step 1: Add failing route tests for the new field**

Append these tests to [test_routes_agents.py](file:///d:/codes/lc-agent/tests/test_routes_agents.py):

```python
@pytest.mark.asyncio
async def test_create_agent_persists_general_purpose_subagent_flag(app_and_headers):
    app, headers = app_and_headers
    transport = ASGITransport(app=app.fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "name": "Delegating Agent",
            "system_prompt": "Delegate when useful.",
            "default_model": "gpt-4",
            "enable_general_purpose_subagent": True,
        }
        create_resp = await client.post("/api/agents", json=payload, headers=headers)
        assert create_resp.status_code == 201
        created = create_resp.json()
        assert created["enable_general_purpose_subagent"] is True

        list_resp = await client.get("/api/agents", headers=headers)
        assert list_resp.status_code == 200
        listed = next(a for a in list_resp.json() if a["id"] == created["id"])
        assert listed["enable_general_purpose_subagent"] is True


@pytest.mark.asyncio
async def test_update_agent_persists_general_purpose_subagent_flag(app_and_headers):
    app, headers = app_and_headers
    transport = ASGITransport(app=app.fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/api/agents", json={
            "name": "Delegating Agent",
            "system_prompt": "Original",
            "default_model": "gpt-4",
        }, headers=headers)
        agent_id = create_resp.json()["id"]

        update_resp = await client.put(f"/api/agents/{agent_id}", json={
            "enable_general_purpose_subagent": True,
        }, headers=headers)
        assert update_resp.status_code == 200
        assert update_resp.json()["enable_general_purpose_subagent"] is True

        second_update = await client.put(f"/api/agents/{agent_id}", json={
            "enable_general_purpose_subagent": False,
        }, headers=headers)
        assert second_update.status_code == 200
        assert second_update.json()["enable_general_purpose_subagent"] is False
```

- [ ] **Step 2: Run route tests and verify they fail**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_routes_agents.py::test_create_agent_persists_general_purpose_subagent_flag tests/test_routes_agents.py::test_update_agent_persists_general_purpose_subagent_flag -v
```

Expected: failures because the request models / DB model do not yet include `enable_general_purpose_subagent`.

- [ ] **Step 3: Add core model field**

In [models.py](file:///d:/codes/lc-agent/lc_agent/core/models.py), change `AgentPreset` to include:

```python
class AgentPreset(BaseModel):
    """Agent preset configuration (three-value semantics from nb_agent).

    For allowed_* fields:
      None  = all allowed (default)
      []    = all disabled
      ["a"] = only specified items allowed

    source: "builtin" | "code" | "user"
    default_enabled: controls whether tools/MCP/skills default to ON or OFF in the UI
    """

    id: str
    name: str
    system_prompt: str
    default_model: str

    allowed_tool_groups: list[str] | None = None
    allowed_mcp_servers: list[str] | None = None
    allowed_skills: list[str] | None = None

    llm_params: dict | None = None

    source: str = "user"
    default_enabled: bool = True

    subagent_ids: list[str] | None = None
    enable_general_purpose_subagent: bool = False
```

- [ ] **Step 4: Add DB model field**

In [models.py](file:///d:/codes/lc-agent/lc_agent/db/models.py), change `AgentPresetDB` to include:

```python
class AgentPresetDB(SQLModel, table=True):
    __tablename__ = "agent_presets"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    system_prompt: str = ""
    default_model: str = ""
    allowed_tool_groups: list[str] | None = Field(default=None, sa_column=Column(JSON))
    allowed_mcp_servers: list[str] | None = Field(default=None, sa_column=Column(JSON))
    allowed_skills: list[str] | None = Field(default=None, sa_column=Column(JSON))
    subagent_ids: list[str] | None = Field(default=None, sa_column=Column(JSON))
    enable_general_purpose_subagent: bool = False
    llm_params: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
```

- [ ] **Step 5: Add Alembic migration**

Create `d:\codes\lc-agent\lc_agent\db\migrations\versions\20260708_add_general_purpose_subagent.py`:

```python
"""add general purpose subagent flag

Revision ID: 20260708_add_general_purpose_subagent
Revises: 20260707_add_subagent_fields
Create Date: 2026-07-08
"""

from alembic import op
import sqlalchemy as sa


revision = "20260708_add_general_purpose_subagent"
down_revision = "20260707_add_subagent_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_presets",
        sa.Column("enable_general_purpose_subagent", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("agent_presets", "enable_general_purpose_subagent")
```

If the current latest migration revision differs, inspect `lc_agent/db/migrations/versions` and set `down_revision` to the current latest revision.

- [ ] **Step 6: Add API request/response handling**

In [agents.py](file:///d:/codes/lc-agent/lc_agent/server/routes/agents.py):

Add fields to request classes:

```python
class AgentCreateRequest(BaseModel):
    name: str
    system_prompt: str
    default_model: str
    allowed_tool_groups: list[str] | None = None
    allowed_mcp_servers: list[str] | None = None
    allowed_skills: list[str] | None = None
    llm_params: dict | None = None
    subagent_ids: list[str] | None = None
    enable_general_purpose_subagent: bool = False


class AgentUpdateRequest(BaseModel):
    name: str | None = None
    system_prompt: str | None = None
    default_model: str | None = None
    allowed_tool_groups: list[str] | None = None
    allowed_mcp_servers: list[str] | None = None
    allowed_skills: list[str] | None = None
    llm_params: dict | None = None
    subagent_ids: list[str] | None = None
    enable_general_purpose_subagent: bool | None = None
```

Add the field in every returned dict and every `AgentPreset(...)` construction:

```python
"enable_general_purpose_subagent": p.enable_general_purpose_subagent,
```

For code agents, return `False` unless code registration later supports explicitly setting it:

```python
"enable_general_purpose_subagent": False,
```

For DB rows:

```python
"enable_general_purpose_subagent": row.enable_general_purpose_subagent,
```

For create DB:

```python
enable_general_purpose_subagent=body.enable_general_purpose_subagent,
```

For engine preset construction:

```python
enable_general_purpose_subagent=preset_db.enable_general_purpose_subagent,
```

- [ ] **Step 7: Run route tests and verify they pass**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_routes_agents.py -v
```

Expected: all route agent tests pass.

---

## Task 2: Introduce Task Subagent Registry in AgentEngine

**Files:**
- Modify: [engine.py](file:///d:/codes/lc-agent/lc_agent/core/engine.py)
- Test: [test_engine_subagents.py](file:///d:/codes/lc-agent/tests/test_engine_subagents.py)

- [ ] **Step 1: Replace old engine tests with task-mode expectations**

Update [test_engine_subagents.py](file:///d:/codes/lc-agent/tests/test_engine_subagents.py) to cover the new behavior:

```python
import pytest
from unittest.mock import MagicMock

from lc_agent.core.engine import AgentEngine
from lc_agent.core.models import AgentPreset


MINIMAL_CONFIG = {
    "provider": {
        "test": {
            "base_url": "http://localhost:4000/v1",
            "api_key": "test",
            "models": [{"id": "test-model", "context_limit": 8000}],
        }
    },
    "agent": {"default_model": "test-model", "max_subagent_depth": 2},
}


def test_build_subagent_registry_preserves_chinese_subagent_type():
    engine = AgentEngine(MINIMAL_CONFIG)
    engine._presets["child"] = AgentPreset(
        id="child",
        name="funboost教程查询智能体",
        system_prompt="查询 funboost 文档",
        default_model="test-model",
    )
    parent = AgentPreset(
        id="parent",
        name="主智能体",
        system_prompt="你可以委派任务",
        default_model="test-model",
        subagent_ids=["child"],
    )

    registry = engine._build_subagent_registry(parent, depth=0, building_set=frozenset())

    assert list(registry.keys()) == ["funboost教程查询智能体"]
    descriptor = registry["funboost教程查询智能体"]
    assert descriptor.preset_id == "child"
    assert descriptor.display_name == "funboost教程查询智能体"
    assert descriptor.kind == "preset"


def test_build_subagent_registry_disambiguates_duplicate_names():
    engine = AgentEngine(MINIMAL_CONFIG)
    engine._presets["aaaaaaaa-1111"] = AgentPreset(id="aaaaaaaa-1111", name="资料查询", system_prompt="A", default_model="test-model")
    engine._presets["bbbbbbbb-2222"] = AgentPreset(id="bbbbbbbb-2222", name="资料查询", system_prompt="B", default_model="test-model")
    parent = AgentPreset(
        id="parent",
        name="主智能体",
        system_prompt="你可以委派任务",
        default_model="test-model",
        subagent_ids=["aaaaaaaa-1111", "bbbbbbbb-2222"],
    )

    registry = engine._build_subagent_registry(parent, depth=0, building_set=frozenset())

    assert set(registry.keys()) == {"资料查询#aaaaaaaa", "资料查询#bbbbbbbb"}


def test_build_subagent_registry_includes_general_purpose_when_enabled():
    engine = AgentEngine(MINIMAL_CONFIG)
    parent = AgentPreset(
        id="parent",
        name="主智能体",
        system_prompt="你可以委派任务",
        default_model="test-model",
        enable_general_purpose_subagent=True,
    )

    registry = engine._build_subagent_registry(parent, depth=0, building_set=frozenset())

    assert "general-purpose" in registry
    assert registry["general-purpose"].kind == "general-purpose"
    assert registry["general-purpose"].display_name == "general-purpose"


def test_build_subagent_registry_empty_when_no_subagents_enabled():
    engine = AgentEngine(MINIMAL_CONFIG)
    parent = AgentPreset(
        id="parent",
        name="主智能体",
        system_prompt="无委派能力",
        default_model="test-model",
    )

    registry = engine._build_subagent_registry(parent, depth=0, building_set=frozenset())

    assert registry == {}


def test_get_subagent_tool_names_returns_task_after_build(monkeypatch):
    engine = AgentEngine(MINIMAL_CONFIG)
    engine._presets["child"] = AgentPreset(id="child", name="子智能体", system_prompt="子任务", default_model="test-model")
    parent = AgentPreset(
        id="parent",
        name="主智能体",
        system_prompt="你可以委派任务",
        default_model="test-model",
        subagent_ids=["child"],
    )

    monkeypatch.setattr(engine, "_create_llm", lambda *args, **kwargs: MagicMock())

    class FakeAgent:
        pass

    import lc_agent.core.engine as engine_module
    monkeypatch.setattr(engine_module, "create_agent", lambda **kwargs: FakeAgent(), raising=False)

    engine.build_agent(parent, cache_key="parent")

    assert engine.get_subagent_tool_names("parent") == {"task"}
    assert engine.get_subagent_display_name_map("parent") == {"子智能体": "子智能体"}
```

If module-level monkeypatching of `create_agent` does not work because it is imported inside `build_agent`, patch `langchain.agents.create_agent` instead.

- [ ] **Step 2: Run engine subagent tests and verify failures**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine_subagents.py -v
```

Expected: failures because `_build_subagent_registry` and task-mode metadata do not exist.

- [ ] **Step 3: Add descriptor dataclass and imports**

In [engine.py](file:///d:/codes/lc-agent/lc_agent/core/engine.py), add imports:

```python
from dataclasses import dataclass
from typing import Literal
from pydantic import BaseModel, Field
```

Add near the module helpers:

```python
@dataclass(frozen=True)
class SubAgentDescriptor:
    subagent_type: str
    preset_id: str
    display_name: str
    description: str
    kind: Literal["preset", "general-purpose"]


class TaskSubAgentInput(BaseModel):
    subagent_type: str = Field(description="The sub-agent type to run. Use one of the available subagent_type values.")
    description: str = Field(description="The full task description to delegate to the selected sub-agent.")
```

- [ ] **Step 4: Add registry helper methods**

In `AgentEngine`, add:

```python
    @staticmethod
    def _short_preset_id(preset_id: str) -> str:
        return preset_id.replace("-", "")[:8]

    def _build_subagent_registry(
        self,
        preset: AgentPreset,
        depth: int,
        building_set: frozenset[str],
    ) -> dict[str, SubAgentDescriptor]:
        max_depth = self.config.get("agent", {}).get("max_subagent_depth", 2)
        if depth >= max_depth:
            return {}

        candidates: list[tuple[str, AgentPreset]] = []
        for subagent_id in getattr(preset, "subagent_ids", None) or []:
            if subagent_id in building_set:
                logger.warning("Subagent circular reference detected: %s — skipping", subagent_id)
                continue
            if not self._preset_exists(subagent_id):
                logger.warning("Subagent preset not found: %s — skipping", subagent_id)
                continue
            candidates.append((subagent_id, self._resolve_preset(subagent_id)))

        name_counts: dict[str, int] = {}
        for _, subagent_preset in candidates:
            name_counts[subagent_preset.name] = name_counts.get(subagent_preset.name, 0) + 1

        registry: dict[str, SubAgentDescriptor] = {}
        if getattr(preset, "enable_general_purpose_subagent", False):
            registry["general-purpose"] = SubAgentDescriptor(
                subagent_type="general-purpose",
                preset_id=preset.id,
                display_name="general-purpose",
                description="A general-purpose worker with the same capabilities as the current agent, without task delegation.",
                kind="general-purpose",
            )

        for subagent_id, subagent_preset in candidates:
            subagent_type = subagent_preset.name
            if name_counts[subagent_preset.name] > 1:
                subagent_type = f"{subagent_preset.name}#{self._short_preset_id(subagent_id)}"
            registry[subagent_type] = SubAgentDescriptor(
                subagent_type=subagent_type,
                preset_id=subagent_id,
                display_name=subagent_preset.name,
                description=subagent_preset.system_prompt[:200] if subagent_preset.system_prompt else subagent_preset.name,
                kind="preset",
            )
        return registry
```

- [ ] **Step 5: Replace per-subagent tool creation with one task tool**

Add an engine method:

```python
    def _make_task_tool(
        self,
        parent_preset: AgentPreset,
        registry: dict[str, SubAgentDescriptor],
        depth: int,
        building_set: frozenset[str],
    ):
        has_injected = _HAS_INJECTED_TOOL_CALL_ID
        available = ", ".join(registry.keys())
        description = (
            "Delegate a task to a sub-agent. "
            f"Available subagent_type values: {available}. "
            "Use description for the complete delegated task."
        )

        async def _run_task(subagent_type: str, description: str, config: RunnableConfig, tool_call_id: str | None = None) -> str:
            descriptor = registry.get(subagent_type)
            if descriptor is None:
                return f"Unknown subagent_type: {subagent_type}. Available subagent_type values: {available}"

            if descriptor.kind == "general-purpose":
                sub_agent = self._build_general_purpose_subagent(parent_preset, depth=depth)
            else:
                try:
                    sub_agent = self._get_or_build_agent(descriptor.preset_id, _depth=depth)
                except Exception as exc:
                    logger.warning("Could not build subagent %s: %s — skipping", descriptor.preset_id, exc)
                    return f"[Sub-agent error: {exc}]"

            configurable = (config or {}).get("configurable", {})
            parent_tid = configurable.get("thread_id") or ""
            lg_ns = configurable.get("checkpoint_ns", "")
            tc_id = next(
                (seg.split(":", 1)[1] for seg in lg_ns.split("|") if seg.startswith("tools:")),
                tool_call_id or configurable.get("tool_call_id") or "task",
            )
            sub_thread_id = f"{parent_tid}--sa--{tc_id}"
            sub_config = {
                **(config or {}),
                "configurable": {
                    **((config or {}).get("configurable") or {}),
                    "thread_id": sub_thread_id,
                    "sub_session_id": sub_thread_id,
                },
            }

            collector = HttpTraceCollector(provider=None, model=None)
            trace_token = bind_http_trace_collector(collector)
            try:
                result = await sub_agent.ainvoke(
                    {"messages": [{"role": "user", "content": description}]},
                    config=sub_config,
                )
                return _extract_subagent_result(result.get("messages", []))
            except Exception as exc:
                logger.exception("Subagent %s failed: %s", descriptor.subagent_type, exc)
                return f"[Sub-agent error: {exc}]"
            finally:
                reset_http_trace_collector(trace_token)
                register_subagent_collector(sub_thread_id, collector)

        if has_injected:
            @lc_tool("task", description=description, args_schema=TaskSubAgentInput)
            async def task(
                subagent_type: str,
                description: str,
                tool_call_id: Annotated[str, InjectedToolCallId],
                config: RunnableConfig,
            ) -> str:
                return await _run_task(subagent_type, description, config, tool_call_id)
        else:
            @lc_tool("task", description=description, args_schema=TaskSubAgentInput)
            async def task(subagent_type: str, description: str, config: RunnableConfig) -> str:
                return await _run_task(subagent_type, description, config)

        return task
```

If LangChain rejects `args_schema` together with explicit function parameters, use a plain `StructuredTool.from_function` after checking the installed LangChain API.

- [ ] **Step 6: Add general-purpose builder**

Add:

```python
    def _build_general_purpose_subagent(self, parent_preset: AgentPreset, depth: int):
        cloned = parent_preset.model_copy(update={
            "id": f"{parent_preset.id}::general-purpose",
            "name": "general-purpose",
            "subagent_ids": None,
            "enable_general_purpose_subagent": False,
        })
        cache_key = self._get_agent_cache_key(cloned.id, _depth=depth)
        if cache_key in self._agents:
            return self._agents[cache_key]
        return self.build_agent(
            cloned,
            cache_key=cache_key,
            building_set=frozenset({parent_preset.id}),
            _depth=depth,
            disable_task=True,
        )
```

Then update `build_agent` signature:

```python
    def build_agent(
        self,
        preset: AgentPreset | None = None,
        cache_key: str | None = None,
        llm_params: dict | None = None,
        building_set: frozenset[str] | None = None,
        _depth: int = 0,
        disable_task: bool = False,
    ):
```

- [ ] **Step 7: Update build_agent subagent injection block**

Replace the old block that loops over `_make_subagent_tool()` with:

```python
        subagent_display_map: dict[str, str] = {}
        if not disable_task:
            new_building = (building_set or frozenset()) | {preset.id}
            subagent_registry = self._build_subagent_registry(preset, _depth, new_building)
            if subagent_registry:
                task_tool = self._make_task_tool(preset, subagent_registry, _depth + 1, new_building)
                tools.append(task_tool)
                subagent_display_map = {
                    subagent_type: descriptor.display_name
                    for subagent_type, descriptor in subagent_registry.items()
                }
```

Then replace the cache assignment:

```python
        self._agent_subagent_tools[resolved_cache_key] = subagent_display_map
```

- [ ] **Step 8: Update cache display helpers**

Keep public method names for callers, but update docstrings and behavior:

```python
    def get_subagent_tool_names(self, preset_id: str, model_id: str = "", llm_params: dict | None = None, _depth: int = 0) -> set[str]:
        display_map = self.get_subagent_display_name_map(preset_id, model_id=model_id, llm_params=llm_params, _depth=_depth)
        return {"task"} if display_map else set()

    def get_subagent_display_name_map(self, preset_id: str, model_id: str = "", llm_params: dict | None = None, _depth: int = 0) -> dict[str, str]:
        cache_key = self._get_agent_cache_key(preset_id, model_id=model_id, llm_params=llm_params, _depth=_depth)
        if cache_key not in self._agent_subagent_tools:
            return {}
        return self._agent_subagent_tools[cache_key]
```

If existing implementation builds the agent lazily in this helper, preserve that behavior but return `subagent_type -> display_name`.

- [ ] **Step 9: Run engine tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine_subagents.py -v
```

Expected: pass.

---

## Task 3: Convert SSE Utilities to Task-Mode Subagent Detection

**Files:**
- Modify: [stream_utils.py](file:///d:/codes/lc-agent/lc_agent/server/stream_utils.py)
- Test: [test_stream_utils_subagents.py](file:///d:/codes/lc-agent/tests/test_stream_utils_subagents.py)

- [ ] **Step 1: Add task-mode stream tests**

Update [test_stream_utils_subagents.py](file:///d:/codes/lc-agent/tests/test_stream_utils_subagents.py) by replacing old per-tool boundary expectations with task-mode cases:

```python
def test_task_tool_start_emits_subagent_start_with_display_name():
    event = {
        "event": "on_tool_start",
        "name": "task",
        "run_id": "run123",
        "metadata": {"langgraph_checkpoint_ns": "tools:task123"},
        "data": {"input": {"subagent_type": "funboost教程查询智能体", "description": "查询定时任务"}},
    }
    results = convert_stream_event(
        event,
        subagent_tool_names={"task"},
        subagent_display_map={"funboost教程查询智能体": "funboost教程查询智能体"},
    )
    assert results == [
        (
            "tool_call",
            {
                "name": "funboost教程查询智能体",
                "run_id": "task123",
                "args": {"subagent_type": "funboost教程查询智能体", "description": "查询定时任务"},
                "is_subagent": True,
            },
        ),
        (
            "subagent_start",
            {
                "name": "funboost教程查询智能体",
                "subagent_type": "funboost教程查询智能体",
                "tool_call_id": "task123",
                "query": "查询定时任务",
            },
        ),
    ]


def test_task_tool_end_emits_subagent_done():
    event = {
        "event": "on_tool_end",
        "name": "task",
        "run_id": "run123",
        "metadata": {"langgraph_checkpoint_ns": "tools:task123"},
        "data": {"output": "research result"},
    }
    results = convert_stream_event(
        event,
        subagent_tool_names={"task"},
        subagent_display_map={"funboost教程查询智能体": "funboost教程查询智能体"},
    )
    assert results == [
        (
            "subagent_done",
            {
                "tool_call_id": "task123",
                "result_preview": "research result",
                "status": "done",
            },
        )
    ]


def test_task_tool_without_subagent_type_is_regular_tool():
    event = {
        "event": "on_tool_start",
        "name": "task",
        "run_id": "run123",
        "metadata": {"langgraph_checkpoint_ns": "tools:task123"},
        "data": {"input": {"description": "missing type"}},
    }
    results = convert_stream_event(
        event,
        subagent_tool_names={"task"},
        subagent_display_map={"funboost教程查询智能体": "funboost教程查询智能体"},
    )
    assert results == [
        ("tool_call", {"name": "task", "run_id": "run123", "args": {"description": "missing type"}})
    ]
```

Update calls to `convert_stream_event` in existing tests if the function signature changes.

- [ ] **Step 2: Run stream tests and verify failures**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_stream_utils_subagents.py -v
```

Expected: task-mode tests fail because the utility does not yet accept/display `subagent_type`.

- [ ] **Step 3: Add helper for task boundary detection**

In [stream_utils.py](file:///d:/codes/lc-agent/lc_agent/server/stream_utils.py), add:

```python
def _extract_task_subagent_type(tool_name: str, tool_input: Any, subagent_tool_names: set[str] | None) -> str | None:
    if not subagent_tool_names or tool_name not in subagent_tool_names:
        return None
    if not isinstance(tool_input, dict):
        return None
    subagent_type = tool_input.get("subagent_type")
    if not isinstance(subagent_type, str) or not subagent_type.strip():
        return None
    return subagent_type.strip()
```

- [ ] **Step 4: Update convert_stream_event signature**

Change signature:

```python
def convert_stream_event(
    event: dict,
    subagent_tool_names: set[str] | None = None,
    subagent_display_map: dict[str, str] | None = None,
) -> list[tuple[str, dict]]:
```

- [ ] **Step 5: Update on_tool_start handling**

In `on_tool_start`, replace the subagent branch condition with:

```python
        subagent_type = _extract_task_subagent_type(tool_name, tool_input, subagent_tool_names)
        if subagent_type:
            tool_input_dict = tool_input if isinstance(tool_input, dict) else {}
            sa_tc_id = _extract_tools_task_id(checkpoint_ns) or event.get("run_id", "")
            display_name = (subagent_display_map or {}).get(subagent_type, subagent_type)
            display_args = {k: v for k, v in tool_input_dict.items() if k != "tool_call_id"}
            results.append(("tool_call", {
                "name": display_name,
                "run_id": sa_tc_id,
                "args": display_args,
                "is_subagent": True,
            }))
            results.append(("subagent_start", {
                "name": display_name,
                "subagent_type": subagent_type,
                "tool_call_id": sa_tc_id,
                "query": tool_input_dict.get("description", ""),
            }))
```

Keep the existing `elif is_in_subagent` and regular tool branches.

- [ ] **Step 6: Update on_tool_end handling**

For `on_tool_end`, there is no input in some LangGraph events. Since only `task` is a boundary subagent tool, treat `tool_name in subagent_tool_names` as subagent end:

```python
        if subagent_tool_names and tool_name in subagent_tool_names:
            sa_tc_id_end = _extract_tools_task_id(checkpoint_ns) or event.get("run_id", "")
            status = "error" if result_str.startswith("[Sub-agent error:") else "done"
            results.append(("subagent_done", {
                "tool_call_id": sa_tc_id_end,
                "result_preview": result_str[:150],
                "status": status,
            }))
```

This is safe because the engine only puts `task` into `subagent_tool_names` when it is the subagent task tool.

- [ ] **Step 7: Update accumulate_display_state signature and start handling**

Keep signature already containing `subagent_display_map`, but change the subagent branch to extract `subagent_type` from input and use the display map keyed by type:

```python
            subagent_type = _extract_task_subagent_type(tool_name, tool_input, subagent_tool_names)
            if subagent_type:
                display_name = (subagent_display_map or {}).get(subagent_type, subagent_type)
```

Set tool call entry:

```python
            tool_calls.append({
                "name": display_name,
                "runId": sa_tc_id,
                "args": display_args,
                "status": "running",
                "is_subagent": True,
                "sub_session_id": sub_session_id,
                "startTime": int(time.time() * 1000),
            })
```

Ensure the regular `task` tool without `subagent_type` falls through as a normal tool call.

- [ ] **Step 8: Run stream tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_stream_utils_subagents.py -v
```

Expected: pass.

---

## Task 4: Update Subagent Tracker and SSE Call Sites

**Files:**
- Modify: [subagent_tracker.py](file:///d:/codes/lc-agent/lc_agent/server/subagent_tracker.py)
- Modify: [sse.py](file:///d:/codes/lc-agent/lc_agent/server/sse.py)
- Test: [test_subagent_run_tracker.py](file:///d:/codes/lc-agent/tests/test_subagent_run_tracker.py)

- [ ] **Step 1: Add tracker test for task-mode payload**

In [test_subagent_run_tracker.py](file:///d:/codes/lc-agent/tests/test_subagent_run_tracker.py), add a test matching existing fixture style:

```python
def test_subagent_start_uses_task_payload_display_name(tracker):
    event = tracker.handle_event("subagent_start", {
        "name": "funboost教程查询智能体",
        "subagent_type": "funboost教程查询智能体",
        "tool_call_id": "task123",
        "query": "查询定时任务",
    })

    assert event["name"] == "funboost教程查询智能体"
    assert event["tool_call_id"] == "task123"
    assert event["query"] == "查询定时任务"
    assert tracker.runs["task123"].name == "funboost教程查询智能体"
```

Adjust fixture/member names to match the existing test file.

- [ ] **Step 2: Run tracker tests and verify failure if needed**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_subagent_run_tracker.py -v
```

Expected: either pass already or fail where tracker maps `task` incorrectly.

- [ ] **Step 3: Update tracker start handling**

In [subagent_tracker.py](file:///d:/codes/lc-agent/lc_agent/server/subagent_tracker.py), ensure `_handle_start` resolves display name like this:

```python
        subagent_type = payload.get("subagent_type")
        raw_name = payload.get("name") or subagent_type or "sub-agent"
        display_name = self.subagent_display_map.get(subagent_type, raw_name) if subagent_type else raw_name
```

The resulting `_SubAgentRun.name` must be `display_name`.

- [ ] **Step 4: Update SSE stream utility call sites**

In [sse.py](file:///d:/codes/lc-agent/lc_agent/server/sse.py), search for `convert_stream_event(` and pass the display map:

```python
converted = convert_stream_event(
    event,
    subagent_tool_names=subagent_tool_names,
    subagent_display_map=subagent_display_map,
)
```

Search for `accumulate_display_state(` and ensure `subagent_display_map=subagent_display_map` is passed.

If `SubAgentRunTracker` is constructed with the old map, keep the same argument name but ensure the map now means `subagent_type -> display_name`.

- [ ] **Step 5: Run SSE-related tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_subagent_run_tracker.py tests/test_stream_utils_subagents.py tests/test_ws_events.py -v
```

Expected: pass.

---

## Task 5: Add Frontend General-Purpose Checkbox and Types

**Files:**
- Modify: [agents.ts](file:///d:/codes/lc-agent/frontend/src/stores/agents.ts)
- Modify: [AgentEditorDialog.vue](file:///d:/codes/lc-agent/frontend/src/components/dialogs/AgentEditorDialog.vue)
- Inspect/modify: [http.ts](file:///d:/codes/lc-agent/frontend/src/api/http.ts)
- Create if needed: `d:\codes\lc-agent\frontend\scripts\check-agent-editor-general-purpose-contract.mjs`

- [ ] **Step 1: Add contract script for editor field**

Create `d:\codes\lc-agent\frontend\scripts\check-agent-editor-general-purpose-contract.mjs`:

```javascript
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const editor = readFileSync(resolve(root, 'src/components/dialogs/AgentEditorDialog.vue'), 'utf8')
const agentsStore = readFileSync(resolve(root, 'src/stores/agents.ts'), 'utf8')

const checks = [
  ['AgentPreset type exposes enable_general_purpose_subagent', agentsStore.includes('enable_general_purpose_subagent')],
  ['editor form tracks enable_general_purpose_subagent', editor.includes('enable_general_purpose_subagent')],
  ['editor renders general-purpose checkbox', editor.includes('启用通用子 Agent')],
  ['save payload includes enable_general_purpose_subagent', editor.includes('enable_general_purpose_subagent: form.value.enable_general_purpose_subagent')],
]

const failed = checks.filter(([, ok]) => !ok)
if (failed.length) {
  for (const [name] of failed) console.error(`FAIL ${name}`)
  process.exit(1)
}

for (const [name] of checks) console.log(`PASS ${name}`)
```

- [ ] **Step 2: Run script and verify failure**

Run:

```powershell
node frontend/scripts/check-agent-editor-general-purpose-contract.mjs
```

Expected: fails before frontend changes.

- [ ] **Step 3: Add type field**

In [agents.ts](file:///d:/codes/lc-agent/frontend/src/stores/agents.ts), update interface:

```typescript
export interface AgentPreset {
  id: string
  name: string
  system_prompt: string
  default_model: string
  allowed_tool_groups: string[] | null
  allowed_mcp_servers: string[] | null
  allowed_skills: string[] | null
  llm_params: Record<string, any> | null
  subagent_ids: string[] | null
  enable_general_purpose_subagent: boolean
  source: 'builtin' | 'code' | 'user'
  default_enabled: boolean
}
```

- [ ] **Step 4: Add form state field**

In [AgentEditorDialog.vue](file:///d:/codes/lc-agent/frontend/src/components/dialogs/AgentEditorDialog.vue), update form:

```typescript
const form = ref({
  name: '',
  system_prompt: '',
  default_model: '',
  llm_params: null as Record<string, any> | null,
  subagent_ids: [] as string[],
  enable_general_purpose_subagent: false,
})
```

When opening existing agent:

```typescript
form.value.enable_general_purpose_subagent = Boolean(agent.enable_general_purpose_subagent)
```

When creating new agent:

```typescript
form.value = {
  name: '',
  system_prompt: '',
  default_model: toolsStore.currentModel,
  llm_params: null,
  subagent_ids: [],
  enable_general_purpose_subagent: false,
}
```

- [ ] **Step 5: Add UI checkbox in subagent tab**

Inside the subagent tab before the professional subagent list, add:

```vue
<div class="general-purpose-subagent">
  <el-checkbox v-model="form.enable_general_purpose_subagent">
    <span style="font-weight: 600;">启用通用子 Agent</span>
  </el-checkbox>
  <p class="picker-hint" style="font-size:12px; color: var(--el-text-color-secondary); margin: 4px 0 12px 24px;">
    让当前 Agent 可以把复杂任务委派给一个同能力的隔离 worker。该 worker 不会继续调用 task。
  </p>
</div>
```

Then update the existing hint from “选择其他 Agent...” to “选择专业子 Agent...”。

- [ ] **Step 6: Add save payload field**

In `handleSave()`, update `data`:

```typescript
const data = {
  name: form.value.name,
  system_prompt: form.value.system_prompt,
  default_model: form.value.default_model,
  allowed_tool_groups,
  allowed_mcp_servers,
  allowed_skills,
  llm_params: form.value.llm_params || null,
  subagent_ids: form.value.subagent_ids.length > 0 ? form.value.subagent_ids : null,
  enable_general_purpose_subagent: form.value.enable_general_purpose_subagent,
}
```

- [ ] **Step 7: Run frontend contract script**

Run:

```powershell
node frontend/scripts/check-agent-editor-general-purpose-contract.mjs
```

Expected: pass.

---

## Task 6: Ensure Frontend Subagent Cards Handle Task-Mode Events

**Files:**
- Modify if needed: [chat.ts](file:///d:/codes/lc-agent/frontend/src/stores/chat.ts)
- Modify if needed: [SubAgentCard.vue](file:///d:/codes/lc-agent/frontend/src/components/chat/SubAgentCard.vue)
- Modify: `d:\codes\lc-agent\frontend\scripts\check-subagent-reducers-contract.mjs`

- [ ] **Step 1: Inspect existing reducer and card assumptions**

Search in [chat.ts](file:///d:/codes/lc-agent/frontend/src/stores/chat.ts) and [SubAgentCard.vue](file:///d:/codes/lc-agent/frontend/src/components/chat/SubAgentCard.vue) for:

```text
subagent_start
tool_call
is_subagent
task
query
name
```

Determine whether the reducer uses payload `name` directly. If it does, no major reducer change is needed because backend now sends display name.

- [ ] **Step 2: Update reducer contract script**

Ensure `frontend/scripts/check-subagent-reducers-contract.mjs` checks for:

```javascript
const requiredSnippets = [
  'subagent_start',
  'is_subagent',
  'sub_session_id',
  'tool_call_id',
]
```

Add a task-mode fixture in the script if it currently simulates events:

```javascript
const taskModeSubagentStart = {
  type: 'subagent_start',
  name: 'funboost教程查询智能体',
  subagent_type: 'funboost教程查询智能体',
  tool_call_id: 'task123',
  query: '查询定时任务',
}
```

- [ ] **Step 3: Update UI only if it displays raw tool name**

If [SubAgentCard.vue](file:///d:/codes/lc-agent/frontend/src/components/chat/SubAgentCard.vue) displays `toolCall.name`, keep it. Backend now sets display name.

If it derives title from `toolCall.args.name` or raw tool name, change it to:

```typescript
const displayName = computed(() => props.toolCall.name || props.toolCall.args?.subagent_type || '子 Agent')
```

- [ ] **Step 4: Run frontend contract checks**

Run:

```powershell
node frontend/scripts/check-subagent-reducers-contract.mjs
node frontend/scripts/check-agent-editor-general-purpose-contract.mjs
```

Expected: pass.

---

## Task 7: Run Focused Backend Integration Tests

**Files:**
- No code changes expected.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine_subagents.py tests/test_stream_utils_subagents.py tests/test_subagent_run_tracker.py tests/test_routes_agents.py -v
```

Expected: pass.

- [ ] **Step 2: Fix any focused failures**

For each failure:

1. Read the assertion and stack trace.
2. Fix the smallest relevant unit.
3. Re-run the same focused command.
4. Do not broaden scope until focused tests pass.

---

## Task 8: Run Lint, Type/Build, and Full Verification

**Files:**
- No code changes expected unless verification fails.

- [ ] **Step 1: Run Python test suite**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/ -v
```

Expected: pass.

- [ ] **Step 2: Run frontend build**

Run:

```powershell
npm run build
```

Working directory: `d:\codes\lc-agent\frontend`

Expected: Vite build succeeds and updates `lc_agent/web/dist`.

- [ ] **Step 3: Run available frontend contract checks**

Run:

```powershell
node frontend/scripts/check-subagent-reducers-contract.mjs
node frontend/scripts/check-agent-editor-general-purpose-contract.mjs
```

Expected: pass.

- [ ] **Step 4: If verification fails, fix and rerun**

Only claim completion after the failing command passes.

---

## Task 9: Manual Verification in bfzs

**Files:**
- No code changes expected.

- [ ] **Step 1: Rebuild frontend and restart bfzs**

Use the existing restart flow or run:

```powershell
cd D:\codes\lc-agent\frontend
npm run build
cd D:\codes\lc-agent-bfzs
D:\ProgramData\Miniconda3\envs\py312\python.exe -u -m bfzs.main --port 8001
```

If an existing server is running, stop it before starting the new one.

- [ ] **Step 2: Verify Chinese custom subagent**

In the UI:

1. Create or use a Chinese-named child Agent, such as `funboost教程查询智能体`.
2. Create a parent Agent.
3. In the parent Agent's 子Agent tab, leave general-purpose disabled and check the Chinese child Agent.
4. Ask a multi-step question that should trigger delegation.
5. Confirm the tool call is `task` with `subagent_type` equal to the Chinese name.
6. Confirm the card title is the Chinese name, not `task`.
7. Click into the sub-session and refresh the main session to verify history still loads.

- [ ] **Step 3: Verify general-purpose**

In the UI:

1. Edit an Agent and enable `启用通用子 Agent`.
2. Do not select any professional subagent.
3. Ask a complex task suitable for isolated parallel work.
4. Confirm `task(subagent_type="general-purpose", description="...")` can be called.
5. Confirm the general-purpose child run does not itself see or call `task`.

---

## Self-Review

### Spec coverage

- Unified `task(subagent_type, description)` is covered in Tasks 2 and 3.
- General-purpose single checkbox is covered in Tasks 1 and 5.
- General-purpose inherits current Agent capabilities but removes task by cloning preset with `subagent_ids=None` and `enable_general_purpose_subagent=False` in Task 2.
- Custom subagent continued delegation is preserved by calling `_get_or_build_agent()` for preset subagents with incremented depth in Task 2.
- `_depth` remains as max-depth safety in Task 2.
- SSE, tracker, frontend, API, DB, and tests are covered in Tasks 1 through 6.
- Verification is covered in Tasks 7 through 9.

### Placeholder scan

No `TBD`, `TODO`, or undefined placeholder tasks remain. The plan names concrete files and concrete commands.

### Type and naming consistency

- Backend field: `enable_general_purpose_subagent`.
- Frontend field: `enable_general_purpose_subagent`.
- Task input fields: `subagent_type`, `description`.
- Display map semantics: `subagent_type -> display_name`.
- Boundary tool name: `task`.
