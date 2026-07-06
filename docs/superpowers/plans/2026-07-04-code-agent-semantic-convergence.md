# Code Agent Semantic Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make code-registered agents semantically self-contained so backend and frontend no longer imply framework-managed prompts, models, tools, MCP servers, or Skills apply to them.

**Architecture:** Backend code-agent metadata will explicitly mark framework-managed capabilities as empty and runtime resolution will always return the registered graph directly. Frontend code-agent views will render an informational, read-only state and suppress configurable framework controls while preserving actual runtime tool-call display in chat messages.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest, Vue 3, Pinia, TypeScript, Vite, existing contract-test scripts.

---

## File Structure

- Modify `lc_agent/app.py`
  - Responsibility: register code agents with explicit self-contained metadata.
- Modify `lc_agent/core/engine.py`
  - Responsibility: resolve code agents directly from registered graphs and prevent rebuild through `build_agent()`.
- Modify `lc_agent/server/routes/agents.py`
  - Responsibility: serialize code-agent capabilities consistently and make activation no-op for code agents.
- Modify `frontend/src/stores/agents.ts`
  - Responsibility: expose an `isCodeAgent` computed helper for UI and send logic.
- Modify `frontend/src/stores/tools.ts`
  - Responsibility: avoid treating `default_model="custom"` as a runtime model choice.
- Modify `frontend/src/components/layout/RightPanel.vue`
  - Responsibility: show code-agent read-only card and hide model/summarization/tool/MCP/Skill controls for code agents.
- Modify `frontend/src/components/dialogs/AgentEditorDialog.vue`
  - Responsibility: make code-agent editor informational only for framework-managed fields.
- Modify `frontend/src/views/ChatView.vue`
  - Responsibility: send empty model override for code agents.
- Modify `frontend/src/App.vue`
  - Responsibility: avoid saving or applying `custom` as a session/runtime model for code agents.
- Modify tests:
  - `tests/test_custom_agents.py`
  - `tests/test_routes_agents.py`
- Create frontend contract script:
  - `frontend/scripts/check-code-agent-contract.mjs`
- Modify `frontend/package.json`
  - Add `test:code-agent` script.

---

### Task 1: Backend Code-Agent Metadata

**Files:**
- Modify: `lc_agent/app.py:167-189`
- Test: `tests/test_custom_agents.py`

- [ ] **Step 1: Write the failing metadata test**

Append this test to `tests/test_custom_agents.py`:

```python
def test_add_agent_marks_code_agent_as_self_contained():
    from lc_agent.app import LcAgentApp

    class DummyGraph:
        async def ainvoke(self, *args, **kwargs):
            return {"messages": []}

        async def astream_events(self, *args, **kwargs):
            if False:
                yield {}

    app = LcAgentApp({"agent": {"default_model": "model-a"}})
    graph = DummyGraph()

    app.add_agent("research", graph, "Research graph")

    preset = app.engine._custom_presets["research"]
    assert app.engine._agents["research"] is graph
    assert preset.source == "code"
    assert preset.default_model == "custom"
    assert preset.system_prompt == "Research graph"
    assert preset.allowed_tool_groups == []
    assert preset.allowed_mcp_servers == []
    assert preset.allowed_skills == []
    assert preset.default_enabled is False
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_custom_agents.py::test_add_agent_marks_code_agent_as_self_contained -v
```

Expected: FAIL because `allowed_tool_groups`, `allowed_mcp_servers`, and `allowed_skills` are currently `None`, and `default_enabled` is currently `True`.

- [ ] **Step 3: Implement metadata convergence**

In `lc_agent/app.py`, replace the `AgentPreset(...)` block inside `add_agent()` with:

```python
        preset = AgentPreset(
            id=name,
            name=name,
            system_prompt=description or f"Custom agent: {name}",
            default_model="custom",
            allowed_tool_groups=[],
            allowed_mcp_servers=[],
            allowed_skills=[],
            source="code",
            default_enabled=False,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_custom_agents.py::test_add_agent_marks_code_agent_as_self_contained -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add lc_agent/app.py tests/test_custom_agents.py
git commit -m "fix: mark code agents as self contained"
```

---

### Task 2: Backend Runtime Resolution

**Files:**
- Modify: `lc_agent/core/engine.py:299-316`
- Test: `tests/test_custom_agents.py`

- [ ] **Step 1: Write the failing runtime test**

Append this test to `tests/test_custom_agents.py`:

```python
def test_code_agent_resolution_returns_registered_graph_without_rebuild(monkeypatch):
    from lc_agent.app import LcAgentApp

    class DummyGraph:
        async def ainvoke(self, *args, **kwargs):
            return {"messages": []}

        async def astream_events(self, *args, **kwargs):
            if False:
                yield {}

    app = LcAgentApp({"agent": {"default_model": "model-a"}})
    graph = DummyGraph()
    app.add_agent("research", graph, "Research graph")
    app.engine._mcp_generation = 99

    def fail_build_agent(*args, **kwargs):
        raise AssertionError("code agents must not be rebuilt through build_agent")

    monkeypatch.setattr(app.engine, "build_agent", fail_build_agent)

    resolved = app.engine._get_or_build_agent("research", model_id="some-ui-model")

    assert resolved is graph
    assert "research::model::some-ui-model" not in app.engine._agents
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_custom_agents.py::test_code_agent_resolution_returns_registered_graph_without_rebuild -v
```

Expected: FAIL with `AssertionError: code agents must not be rebuilt through build_agent` or a cache-key-related failure.

- [ ] **Step 3: Implement direct code-agent resolution**

In `lc_agent/core/engine.py`, replace `_get_or_build_agent()` with:

```python
    def _get_or_build_agent(self, preset_id: str, model_id: str = ""):
        """Get cached agent or build a new one. Rebuilds preset agents if MCP state changed."""
        preset = self._resolve_preset(preset_id)
        if preset.source == "code" or preset_id in self._custom_presets:
            agent = self._agents.get(preset_id)
            if agent is None:
                raise ValueError(f"Code agent '{preset_id}' is registered without a graph")
            return agent

        if model_id and self._find_model(model_id):
            preset = preset.model_copy(update={"default_model": model_id})
        cache_key = self._get_agent_cache_key(preset_id, model_id if preset.default_model == model_id else "")
        mcp_gen = getattr(self, '_mcp_generation', 0)
        cached = self._agents.get(cache_key)
        cached_gen = self._agent_mcp_gen.get(cache_key, -1)
        if cached is None or cached_gen != mcp_gen:
            agent = self.build_agent(preset, cache_key=cache_key)
            self._agent_mcp_gen[cache_key] = mcp_gen
            return agent
        return cached
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_custom_agents.py::test_code_agent_resolution_returns_registered_graph_without_rebuild tests/test_engine.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add lc_agent/core/engine.py tests/test_custom_agents.py
git commit -m "fix: resolve code agents without rebuilding"
```

---

### Task 3: Backend Agent Routes and Activation No-op

**Files:**
- Modify: `lc_agent/server/routes/agents.py:46-57`
- Modify: `lc_agent/server/routes/agents.py:151-163`
- Modify: `lc_agent/server/routes/agents.py:220-275`
- Test: `tests/test_routes_agents.py`

- [ ] **Step 1: Write the route serialization and activation tests**

Append these tests to `tests/test_routes_agents.py`:

```python
def test_preset_to_dict_normalizes_code_agent_capabilities():
    from lc_agent.core.models import AgentPreset
    from lc_agent.server.routes.agents import _preset_to_dict

    preset = AgentPreset(
        id="research",
        name="research",
        system_prompt="Research graph",
        default_model="custom",
        source="code",
        allowed_tool_groups=None,
        allowed_mcp_servers=None,
        allowed_skills=None,
        default_enabled=True,
    )

    data = _preset_to_dict(preset)

    assert data["source"] == "code"
    assert data["default_model"] == "custom"
    assert data["allowed_tool_groups"] == []
    assert data["allowed_mcp_servers"] == []
    assert data["allowed_skills"] == []
    assert data["default_enabled"] is False


def test_activate_code_agent_is_noop():
    from types import SimpleNamespace
    from lc_agent.core.engine import AgentEngine
    from lc_agent.core.models import AgentPreset
    from lc_agent.server.routes.agents import activate_agent

    engine = AgentEngine({"agent": {"default_model": "model-a"}})
    engine._custom_presets["research"] = AgentPreset(
        id="research",
        name="research",
        system_prompt="Research graph",
        default_model="custom",
        source="code",
        allowed_tool_groups=[],
        allowed_mcp_servers=[],
        allowed_skills=[],
        default_enabled=False,
    )
    engine._agents["research"] = object()
    engine._mcp_generation = 7
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(mcp_manager=None)))

    result = activate_agent("research", request, engine, admin=SimpleNamespace(role="admin"))

    assert result == {
        "agent_id": "research",
        "action": "none",
        "reason": "code agent is controlled by its registered graph",
    }
    assert engine._mcp_generation == 7
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_routes_agents.py::test_preset_to_dict_normalizes_code_agent_capabilities tests/test_routes_agents.py::test_activate_code_agent_is_noop -v
```

Expected: FAIL because code-agent serialization and activate no-op are not implemented yet.

- [ ] **Step 3: Normalize code-agent serialization**

In `lc_agent/server/routes/agents.py`, replace `_preset_to_dict()` with:

```python
def _preset_to_dict(p: AgentPreset) -> dict:
    if p.source == "code":
        return {
            "id": p.id,
            "name": p.name,
            "system_prompt": p.system_prompt,
            "default_model": "custom",
            "allowed_tool_groups": [],
            "allowed_mcp_servers": [],
            "allowed_skills": [],
            "source": "code",
            "default_enabled": False,
        }
    return {
        "id": p.id,
        "name": p.name,
        "system_prompt": p.system_prompt,
        "default_model": p.default_model,
        "allowed_tool_groups": p.allowed_tool_groups,
        "allowed_mcp_servers": p.allowed_mcp_servers,
        "allowed_skills": p.allowed_skills,
        "source": p.source,
        "default_enabled": p.default_enabled,
    }
```

- [ ] **Step 4: Make code-agent updates read-only for framework fields**

In `update_agent()`, replace the `if agent_id in engine._custom_presets:` block with:

```python
    if agent_id in engine._custom_presets:
        raise HTTPException(
            status_code=403,
            detail="Code agents are defined by their registered graph and cannot be edited from the UI",
        )
```

- [ ] **Step 5: Make activation no-op for code agents**

In `activate_agent()`, immediately after `preset = engine._resolve_preset(agent_id)`, add:

```python
    if preset.source == "code" or agent_id in engine._custom_presets:
        return {
            "agent_id": agent_id,
            "action": "none",
            "reason": "code agent is controlled by its registered graph",
        }
```

- [ ] **Step 6: Run route tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_routes_agents.py -v
```

Expected: PASS. If an existing test expects code-agent runtime config updates, update that test to expect HTTP 403 with the new detail string because code agents are now read-only for framework-managed fields.

- [ ] **Step 7: Commit**

Run:

```powershell
git add lc_agent/server/routes/agents.py tests/test_routes_agents.py
git commit -m "fix: make code agent route semantics read only"
```

---

### Task 4: Frontend Store Semantics

**Files:**
- Modify: `frontend/src/stores/agents.ts`
- Modify: `frontend/src/stores/tools.ts`
- Create: `frontend/scripts/check-code-agent-contract.mjs`
- Modify: `frontend/package.json`

- [ ] **Step 1: Create the failing contract script**

Create `frontend/scripts/check-code-agent-contract.mjs`:

```javascript
import fs from 'node:fs'
import path from 'node:path'

const root = process.cwd()
function read(rel) {
  return fs.readFileSync(path.join(root, rel), 'utf8')
}
function assertContains(file, needle, message) {
  const content = read(file)
  if (!content.includes(needle)) {
    console.error(`[code-agent-contract] ${message}`)
    console.error(`Missing in ${file}: ${needle}`)
    process.exit(1)
  }
}
function assertNotContains(file, needle, message) {
  const content = read(file)
  if (content.includes(needle)) {
    console.error(`[code-agent-contract] ${message}`)
    console.error(`Unexpected in ${file}: ${needle}`)
    process.exit(1)
  }
}

assertContains(
  'src/stores/agents.ts',
  'const isCodeAgent = computed(() => currentAgent.value?.source === \'code\')',
  'agents store must expose current code-agent state',
)
assertContains(
  'src/stores/agents.ts',
  'isCodeAgent,',
  'agents store must return isCodeAgent',
)
assertContains(
  'src/stores/tools.ts',
  "if (agentsStore.currentAgent?.source === 'code') {",
  'tools store must special-case code agents when syncing model',
)
assertContains(
  'src/stores/tools.ts',
  "currentModel.value = ''",
  'tools store must clear UI model for code agents',
)
assertNotContains(
  'src/stores/tools.ts',
  'currentModel.value = defaultModel\n      return',
  'tools store must not blindly set default_model=custom as runtime model',
)
console.log('[code-agent-contract] store checks passed')
```

- [ ] **Step 2: Add npm script**

In `frontend/package.json`, add this entry under `scripts`:

```json
"test:code-agent": "node scripts/check-code-agent-contract.mjs"
```

- [ ] **Step 3: Run contract to verify it fails**

Run:

```powershell
cd frontend
npm run test:code-agent
```

Expected: FAIL because `isCodeAgent` and code-agent model clearing are not implemented.

- [ ] **Step 4: Add `isCodeAgent` computed**

In `frontend/src/stores/agents.ts`, after `isChatAgent`, add:

```typescript
  const isCodeAgent = computed(() => currentAgent.value?.source === 'code')
```

In the returned object, add:

```typescript
    isCodeAgent,
```

- [ ] **Step 5: Update model sync for code agents**

In `frontend/src/stores/tools.ts`, replace `syncModelWithAgentDefault()` with:

```typescript
  function syncModelWithAgentDefault() {
    const agentsStore = useAgentsStore()
    if (agentsStore.currentAgent?.source === 'code') {
      currentModel.value = ''
      return
    }
    const defaultModel = agentsStore.currentAgent?.default_model
    if (defaultModel && defaultModel !== 'custom') {
      currentModel.value = defaultModel
      return
    }
    if (models.value.length > 0 && !currentModel.value) {
      currentModel.value = models.value[0].id
    }
  }
```

- [ ] **Step 6: Run contract to verify it passes**

Run:

```powershell
cd frontend
npm run test:code-agent
```

Expected: PASS with `[code-agent-contract] store checks passed`.

- [ ] **Step 7: Commit**

Run:

```powershell
git add frontend/package.json frontend/src/stores/agents.ts frontend/src/stores/tools.ts frontend/scripts/check-code-agent-contract.mjs
git commit -m "fix: add frontend code agent store semantics"
```

---

### Task 5: Frontend Right Panel Code-Agent Card

**Files:**
- Modify: `frontend/src/components/layout/RightPanel.vue`
- Test: `frontend/scripts/check-code-agent-contract.mjs`

- [ ] **Step 1: Extend contract script for right panel**

Append these checks to `frontend/scripts/check-code-agent-contract.mjs` before the final `console.log(...)` line:

```javascript
assertContains(
  'src/components/layout/RightPanel.vue',
  'v-if="!agentsStore.isCodeAgent"',
  'right panel must hide fixed model/summarization controls for code agents',
)
assertContains(
  'src/components/layout/RightPanel.vue',
  'v-if="agentsStore.isCodeAgent"',
  'right panel must render a code-agent explanation branch',
)
assertContains(
  'src/components/layout/RightPanel.vue',
  '代码智能体',
  'right panel must label code-agent informational card',
)
assertContains(
  'src/components/layout/RightPanel.vue',
  '工具、MCP、Skills、提示词和模型由代码中的 graph 决定',
  'right panel must explain code graph ownership',
)
assertContains(
  'src/components/layout/RightPanel.vue',
  'v-if="!agentsStore.isChatAgent && !agentsStore.isCodeAgent"',
  'right panel must hide configurable tools for code agents',
)
```

- [ ] **Step 2: Run contract to verify it fails**

Run:

```powershell
cd frontend
npm run test:code-agent
```

Expected: FAIL on RightPanel checks.

- [ ] **Step 3: Hide fixed framework controls for code agents**

In `frontend/src/components/layout/RightPanel.vue`, wrap the model and summarization sections in a template:

```vue
      <template v-if="!agentsStore.isCodeAgent">
        <div class="panel-section">
          <h4>模型</h4>
          <ModelSelector
            :models="toolsStore.models"
            :current-model="toolsStore.currentModel"
            @change="toolsStore.setModel"
          />
        </div>

        <div class="panel-section window-trim-section">
          <div class="window-trim-control">
            <h4>窗口裁剪模型</h4>
            <el-switch
              :model-value="summEnabled"
              size="small"
              @change="(val: boolean) => { summEnabled = val; updateSummarization({ enabled: val }) }"
            />
          </div>
          <el-select
            v-if="summEnabled"
            v-model="summModel"
            placeholder="默认同主模型"
            size="small"
            filterable
            clearable
            class="window-trim-select"
            @change="updateSummarization({ default_model: $event || '' })"
          >
            <el-option
              v-for="model in toolsStore.models"
              :key="model.id"
              :label="model.id"
              :value="model.id"
            />
          </el-select>
        </div>
      </template>
```

Keep Markdown theme and TodoList outside this template because they are UI-level features, not framework-managed agent capabilities.

- [ ] **Step 4: Add the read-only code-agent card**

Inside `<div class="right-panel-scroll">`, before the normal tool/MCP/Skills template, add:

```vue
      <div v-if="agentsStore.isCodeAgent" class="panel-section code-agent-hint">
        <div class="hint-box code-agent-box">
          <span class="hint-icon">⚙️</span>
          <span class="hint-text">代码智能体</span>
          <span class="hint-sub">此智能体由代码注册，工具、MCP、Skills、提示词和模型由代码中的 graph 决定。当前面板的框架级配置不适用于它。</span>
        </div>
      </div>
```

- [ ] **Step 5: Hide configurable lists for code agents**

Change this template condition:

```vue
      <template v-if="!agentsStore.isChatAgent">
```

to:

```vue
      <template v-if="!agentsStore.isChatAgent && !agentsStore.isCodeAgent">
```

- [ ] **Step 6: Add minimal styles**

In the `<style scoped>` section, add:

```css
.code-agent-hint .hint-sub {
  line-height: 1.45;
}

.code-agent-box {
  border: 1px solid var(--el-color-primary-light-7);
  background: color-mix(in srgb, var(--el-color-primary) 7%, var(--el-fill-color-light));
}
```

- [ ] **Step 7: Run contract and build**

Run:

```powershell
cd frontend
npm run test:code-agent
npm run build
```

Expected: contract PASS and build PASS.

- [ ] **Step 8: Commit**

Run:

```powershell
git add frontend/src/components/layout/RightPanel.vue frontend/scripts/check-code-agent-contract.mjs
git commit -m "fix: show code agent read only right panel"
```

---

### Task 6: Frontend Agent Editor Read-only Code Agents

**Files:**
- Modify: `frontend/src/components/dialogs/AgentEditorDialog.vue`
- Test: `frontend/scripts/check-code-agent-contract.mjs`

- [ ] **Step 1: Extend contract script for editor**

Append these checks to `frontend/scripts/check-code-agent-contract.mjs` before the final `console.log(...)` line:

```javascript
assertContains(
  'src/components/dialogs/AgentEditorDialog.vue',
  '此智能体由代码注册（CompiledGraph），工具、MCP、Skills、提示词和模型由代码中的 graph 决定。',
  'editor must explain that code-agent framework fields are graph-owned',
)
assertContains(
  'src/components/dialogs/AgentEditorDialog.vue',
  '<el-form v-if="!isCodeAgent"',
  'editor must hide normal editable form for code agents',
)
assertContains(
  'src/components/dialogs/AgentEditorDialog.vue',
  'v-if="!isCodeAgent"',
  'editor save button must be hidden for code agents',
)
assertNotContains(
  'src/components/dialogs/AgentEditorDialog.vue',
  '仅可修改运行时配置（工具/MCP/Skills）',
  'editor must not claim code-agent runtime framework config is editable',
)
```

- [ ] **Step 2: Run contract to verify it fails**

Run:

```powershell
cd frontend
npm run test:code-agent
```

Expected: FAIL on editor checks.

- [ ] **Step 3: Replace code-agent alert text**

In `AgentEditorDialog.vue`, replace the code-agent alert body with:

```vue
      此智能体由代码注册（CompiledGraph），工具、MCP、Skills、提示词和模型由代码中的 graph 决定。此处仅展示说明，不能修改框架级配置。
```

- [ ] **Step 4: Hide normal edit form for code agents**

Change:

```vue
    <el-form :model="form" label-width="100px" label-position="top">
```

to:

```vue
    <el-form v-if="!isCodeAgent" :model="form" label-width="100px" label-position="top">
```

After the form, add:

```vue
    <div v-else class="code-agent-readonly">
      <div class="readonly-row">
        <span class="readonly-label">名称</span>
        <span class="readonly-value">{{ form.name }}</span>
      </div>
      <div class="readonly-row">
        <span class="readonly-label">说明</span>
        <span class="readonly-value">{{ form.system_prompt }}</span>
      </div>
      <div class="readonly-row">
        <span class="readonly-label">运行模型</span>
        <span class="readonly-value">由代码 graph 决定</span>
      </div>
      <div class="readonly-row">
        <span class="readonly-label">工具能力</span>
        <span class="readonly-value">由代码 graph 决定</span>
      </div>
    </div>
```

- [ ] **Step 5: Hide save button for code agents**

Change the primary save button opening tag from:

```vue
      <el-button type="primary" :loading="saving" @click="handleSave">
```

to:

```vue
      <el-button v-if="!isCodeAgent" type="primary" :loading="saving" @click="handleSave">
```

- [ ] **Step 6: Add editor read-only styles**

In the `<style scoped>` section, add:

```css
.code-agent-readonly {
  padding: 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-light);
}

.readonly-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.readonly-row:last-child {
  border-bottom: none;
}

.readonly-label {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 600;
}

.readonly-value {
  color: var(--el-text-color-primary);
  font-size: 13px;
  text-align: right;
}
```

- [ ] **Step 7: Run contract and build**

Run:

```powershell
cd frontend
npm run test:code-agent
npm run build
```

Expected: contract PASS and build PASS.

- [ ] **Step 8: Commit**

Run:

```powershell
git add frontend/src/components/dialogs/AgentEditorDialog.vue frontend/scripts/check-code-agent-contract.mjs
git commit -m "fix: make code agent editor informational"
```

---

### Task 7: Frontend Message and Session Model Handling

**Files:**
- Modify: `frontend/src/views/ChatView.vue:419-430`
- Modify: `frontend/src/App.vue:111-122`
- Modify: `frontend/src/App.vue:166-176`
- Modify: `frontend/src/App.vue:182-228`
- Test: `frontend/scripts/check-code-agent-contract.mjs`

- [ ] **Step 1: Extend contract script for send/session model handling**

Append these checks to `frontend/scripts/check-code-agent-contract.mjs` before the final `console.log(...)` line:

```javascript
assertContains(
  'src/views/ChatView.vue',
  "const modelOverride = agentsStore.isCodeAgent ? '' : toolsStore.currentModel",
  'chat send must clear model override for code agents',
)
assertContains(
  'src/views/ChatView.vue',
  'chatStore.sendMessage(content, agentsStore.currentAgentId, modelOverride, {',
  'chat send must use code-agent-aware model override',
)
assertContains(
  'src/App.vue',
  "function getSessionModelForAgent(agentId: string): string {",
  'app must centralize code-agent-aware session model selection',
)
assertContains(
  'src/App.vue',
  "if (agent?.source === 'code') return ''",
  'app session model helper must return empty model for code agents',
)
assertContains(
  'src/App.vue',
  'const sessionModel = getSessionModelForAgent(agentId)',
  'new chats must use code-agent-aware session model',
)
```

- [ ] **Step 2: Run contract to verify it fails**

Run:

```powershell
cd frontend
npm run test:code-agent
```

Expected: FAIL on ChatView/App checks.

- [ ] **Step 3: Clear model override in ChatView**

In `frontend/src/views/ChatView.vue`, replace `handleSend()` with:

```typescript
function handleSend(content: string) {
  const editMessageId = editingMessageId.value
  const history = editMessageId ? getReplayHistory(editMessageId) : undefined
  const modelOverride = agentsStore.isCodeAgent ? '' : toolsStore.currentModel
  if (editingMessageId.value) {
    chatStore.truncateAfterMessage(editingMessageId.value)
    cancelEdit()
  }
  chatStore.sendMessage(content, agentsStore.currentAgentId, modelOverride, {
    replaceFromMessageId: editMessageId || undefined,
    history,
  })
}
```

- [ ] **Step 4: Add session model helper in App.vue**

In `frontend/src/App.vue`, after `initApp()` or before `restoreSession()`, add:

```typescript
function getSessionModelForAgent(agentId: string): string {
  const agent = agentsStore.agents.find(a => a.id === agentId)
  if (agent?.source === 'code') return ''
  return agent?.default_model || toolsStore.currentModel || ''
}

function applySessionModel(model: string) {
  if (model) {
    toolsStore.setModel(model)
  }
}
```

- [ ] **Step 5: Use helper for route-created local sessions**

Replace each pattern like:

```typescript
const defaultModel = agentsStore.agents.find(a => a.id === agentQuery)?.default_model || ''
sessionsStore.ensureLocalSession(routeSessionId, agentQuery, defaultModel)
```

with:

```typescript
const sessionModel = getSessionModelForAgent(agentQuery)
sessionsStore.ensureLocalSession(routeSessionId, agentQuery, sessionModel)
```

Then replace `if (defaultModel) { toolsStore.setModel(defaultModel) }` with:

```typescript
applySessionModel(sessionModel)
```

Apply the same pattern in the second route-created local session block in `restoreSession()`.

- [ ] **Step 6: Use helper for new chat and agent changes**

In `handleNewChat()`, replace:

```typescript
const session = sessionsStore.createLocalSession(agentsStore.currentAgentId, toolsStore.currentModel)
```

with:

```typescript
const sessionModel = getSessionModelForAgent(agentsStore.currentAgentId)
const session = sessionsStore.createLocalSession(agentsStore.currentAgentId, sessionModel)
```

In `handleAgentChange()`, replace:

```typescript
const defaultModel = agentsStore.currentAgent?.default_model
if (defaultModel) {
  toolsStore.setModel(defaultModel)
}
const session = sessionsStore.createLocalSession(agentId, toolsStore.currentModel)
```

with:

```typescript
const sessionModel = getSessionModelForAgent(agentId)
applySessionModel(sessionModel)
const session = sessionsStore.createLocalSession(agentId, sessionModel)
```

- [ ] **Step 7: Run contract and build**

Run:

```powershell
cd frontend
npm run test:code-agent
npm run build
```

Expected: contract PASS and build PASS.

- [ ] **Step 8: Commit**

Run:

```powershell
git add frontend/src/views/ChatView.vue frontend/src/App.vue frontend/scripts/check-code-agent-contract.mjs
git commit -m "fix: clear code agent model overrides"
```

---

### Task 8: Final Verification

**Files:**
- Verify only; no planned source changes unless tests expose regressions.

- [ ] **Step 1: Run backend focused tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_custom_agents.py tests/test_routes_agents.py tests/test_engine.py -v
```

Expected: PASS.

- [ ] **Step 2: Run full backend test suite**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/ -v
```

Expected: PASS. If unrelated pre-existing tests fail, capture exact failures and fix only failures caused by code-agent semantic changes.

- [ ] **Step 3: Run frontend contract and build**

Run:

```powershell
cd frontend
npm run test:code-agent
npm run build
```

Expected: PASS.

- [ ] **Step 4: Inspect git status**

Run:

```powershell
git status --short
```

Expected: clean working tree after all task commits.

- [ ] **Step 5: Commit any verification fixes**

If verification required fixes, run:

```powershell
git add <changed-files>
git commit -m "fix: stabilize code agent semantic convergence"
```

Expected: final branch contains only the design, plan, implementation, and verification-related commits for this feature.

---

## Self-Review

- Spec coverage: Backend metadata, runtime resolution, route serialization, activation no-op, frontend right panel, editor behavior, message model override, and runtime tool-call preservation are covered.
- Placeholder scan: No placeholder markers remain in this plan.
- Type consistency: Uses existing `AgentPreset.source`, `allowed_tool_groups`, `allowed_mcp_servers`, `allowed_skills`, `default_enabled`, `agentsStore.isCodeAgent`, and current project paths consistently.
- Scope check: This is one cohesive feature touching backend semantics and frontend representation. It does not require splitting into multiple plans.

