# llm_params 统一 LLM 参数配置 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 LLM 参数（temperature、reasoning_effort）统一为 `llm_params: dict | None` 字段，支持 preset 持久化和运行时覆盖，并在右侧面板和 agent 编辑器中提供 UI。

**Architecture:** 后端在 `AgentPreset`/`AgentPresetDB` 加 JSON 列 `llm_params`，`engine._create_llm` 从中读取参数；`RunStreamRequest` 用 `llm_params` 替换 `reasoning_effort`，合并策略为运行时覆盖优先。前端 `tools.ts` 维护 `llmParams` dict，右侧面板两个控件（temperature slider + reasoning_effort select）写入该 dict，发消息时带上。

**Tech Stack:** Python 3.12, SQLModel, Pydantic v2, FastAPI, Vue 3, TypeScript, Pinia, Element Plus

**Spec:** `docs/superpowers/specs/2026-07-06-llm-params-design.md`

---

## 文件改动清单

| 文件 | 操作 |
|------|------|
| `lc_agent/core/models.py` | 修改：AgentPreset 加 llm_params |
| `lc_agent/db/models.py` | 修改：AgentPresetDB 加 llm_params JSON 列 |
| `lc_agent/core/engine.py` | 修改：_create_llm、_get_agent_cache_key、build_agent |
| `lc_agent/server/sse.py` | 修改：RunStreamRequest 删 reasoning_effort 加 llm_params |
| `frontend/src/stores/tools.ts` | 修改：删 reasoningEffort，加 llmParams |
| `frontend/src/components/layout/RightPanel.vue` | 修改：temperature slider + reasoning_effort select，统一写 llmParams |
| `frontend/src/components/dialogs/AgentEditorDialog.vue` | 修改：加 temperature 字段 |
| `frontend/src/api/sse-client.ts` | 修改：发消息时传 llm_params |

---

## Task 1: 后端数据模型 — AgentPreset + AgentPresetDB

**Files:**
- Modify: `lc_agent/core/models.py`
- Modify: `lc_agent/db/models.py`

- [ ] **Step 1: 在 AgentPreset 加字段**

  编辑 `lc_agent/core/models.py`，在 `allowed_skills` 字段后加：
  ```python
  llm_params: dict | None = None
  ```

- [ ] **Step 2: 在 AgentPresetDB 加字段**

  编辑 `lc_agent/db/models.py`，在 `allowed_skills` 字段后加：
  ```python
  llm_params: dict | None = Field(default=None, sa_column=Column(JSON))
  ```
  `Column` 和 `JSON` 已在该文件顶部导入，无需额外 import。

- [ ] **Step 3: 验证启动时 Alembic 自动迁移**

  ```powershell
  cd D:\codes\lc-agent-bfzs
  & "D:\ProgramData\Miniconda3\envs\py312\python.exe" -m bfzs.main --port 8001
  ```
  启动日志中不应有 error，`agent_presets` 表会自动加上 `llm_params` 列。
  验证：
  ```powershell
  & "D:\ProgramData\Miniconda3\envs\py312\python.exe" "D:\codes\lc-agent\.agents\skills\query-bfzs-db\scripts\query_session.py" --presets
  ```
  能正常输出即可（字段不报错）。

- [ ] **Step 4: commit**
  ```powershell
  cd D:\codes\lc-agent
  git add lc_agent/core/models.py lc_agent/db/models.py
  git commit -m "feat: add llm_params field to AgentPreset and AgentPresetDB"
  ```

---

## Task 2: 后端 engine — _create_llm 和 cache key

**Files:**
- Modify: `lc_agent/core/engine.py`

- [ ] **Step 1: 更新 _get_agent_cache_key 签名和逻辑**

  当前方法（约 294 行）：
  ```python
  def _get_agent_cache_key(self, preset_id: str, model_id: str = "", reasoning_effort: str | None = None) -> str:
      key = f"{preset_id}::model::{model_id}" if model_id else preset_id
      if reasoning_effort:
          key = f"{key}::reasoning_effort::{reasoning_effort}"
      return key
  ```
  改为：
  ```python
  def _get_agent_cache_key(self, preset_id: str, model_id: str = "", llm_params: dict | None = None) -> str:
      key = f"{preset_id}::model::{model_id}" if model_id else preset_id
      if llm_params:
          import json
          key = f"{key}::llm::{json.dumps(llm_params, sort_keys=True)}"
      return key
  ```

- [ ] **Step 2: 更新 build_agent 方法签名**

  当前（约 100 行）：
  ```python
  def build_agent(
      self,
      preset: AgentPreset | None = None,
      cache_key: str | None = None,
      reasoning_effort: str | None = None,
  ):
  ```
  改为：
  ```python
  def build_agent(
      self,
      preset: AgentPreset | None = None,
      cache_key: str | None = None,
      llm_params: dict | None = None,
  ):
  ```
  在 build_agent 内，找到调用 `_create_llm` 的那一行（约 144 行）：
  ```python
  llm = self._create_llm(model_info, preset.default_model, reasoning_effort=reasoning_effort)
  ```
  改为：
  ```python
  # 合并 preset 的 llm_params 和运行时传入的 llm_params（运行时优先）
  effective_params = {**(preset.llm_params or {}), **(llm_params or {})}
  llm = self._create_llm(model_info, preset.default_model, llm_params=effective_params)
  ```
  同理找到 summarization model 的 `_create_llm` 调用（约 252 行），**不传 llm_params**（summarization 不需要调温度）：
  ```python
  llm = self._create_llm(model_info, summ_model_id)
  ```
  保持不变。

- [ ] **Step 3: 更新 _create_llm 方法**

  当前签名（约 191 行）：
  ```python
  def _create_llm(
      self,
      model_info: ModelInfo | None,
      model_id: str,
      reasoning_effort: str | None = None,
  ):
  ```
  改为：
  ```python
  def _create_llm(
      self,
      model_info: ModelInfo | None,
      model_id: str,
      llm_params: dict | None = None,
  ):
  ```
  在方法体内（改动前三处 `temperature=0.7`），改为统一从 `llm_params` 读取：
  ```python
  params = llm_params or {}
  temperature = params.get("temperature", 0.7)
  reasoning_effort = params.get("reasoning_effort")  # None 时不传
  ```
  然后在每个 `ChatOpenAIReasoning(...)` / `init_chat_model(...)` 的 kwargs 构造里：
  - 将 `temperature=0.7` 改为 `temperature=temperature`
  - `if reasoning_effort:` 块保持原来逻辑，只是现在从 `params` 里读出来的

  **第一个分支（base_url 不为空时，约 204 行）：**
  ```python
  kwargs: dict[str, Any] = dict(
      model=model_info.id,
      base_url=model_info.base_url,
      api_key=model_info.api_key or "not-set",
      temperature=temperature,
      stream_usage=True,
      http_async_client=self._build_tracing_async_client(model_info, model_id),
  )
  if model_info.max_output_tokens > 0:
      kwargs["max_tokens"] = model_info.max_output_tokens
  if reasoning_effort:
      kwargs["reasoning_effort"] = reasoning_effort
  return ChatOpenAIReasoning(**kwargs)
  ```

  **第二个分支（有 model_info，约 221 行）：**
  ```python
  model_str = f"{model_info.provider}:{model_info.id}" if model_info.provider else model_info.id
  kwargs: dict[str, Any] = dict(
      api_key=model_info.api_key or "not-set",
      temperature=temperature,
      stream_usage=True,
  )
  if reasoning_effort:
      kwargs["reasoning_effort"] = reasoning_effort
  return init_chat_model(model_str, **kwargs)
  ```

  **第三个分支（fallback，约 230 行）：**
  ```python
  kwargs: dict[str, Any] = dict(api_key="not-set", temperature=temperature, stream_usage=True)
  if reasoning_effort:
      kwargs["reasoning_effort"] = reasoning_effort
  return init_chat_model(model_id, **kwargs)
  ```

- [ ] **Step 4: 更新 _get_or_build_agent 方法**

  当前签名（约 323 行）：
  ```python
  def _get_or_build_agent(
      self,
      preset_id: str,
      model_id: str = "",
      reasoning_effort: str | None = None,
  ):
  ```
  改为：
  ```python
  def _get_or_build_agent(
      self,
      preset_id: str,
      model_id: str = "",
      llm_params: dict | None = None,
  ):
  ```
  方法内的 cache_key 计算（约 339 行）：
  ```python
  cache_key = self._get_agent_cache_key(
      preset_id,
      model_id if preset.default_model == model_id else "",
      reasoning_effort=reasoning_effort,  # 改为：
      llm_params=llm_params,
  )
  ```
  调用 `build_agent` 时（约 348 行）：
  ```python
  agent = self.build_agent(preset, cache_key=cache_key, reasoning_effort=reasoning_effort)
  # 改为：
  agent = self.build_agent(preset, cache_key=cache_key, llm_params=llm_params)
  ```

- [ ] **Step 5: 更新 chat_stream 方法签名**

  当前（约 367 行）：
  ```python
  async def chat_stream(
      self,
      message: str,
      thread_id: str,
      preset_id: str = "__chat__",
      model_id: str = "",
      history: list[dict[str, str]] | None = None,
      reasoning_effort: str | None = None,
  ) -> AsyncIterator[dict]:
      agent = self._get_or_build_agent(preset_id, model_id, reasoning_effort=reasoning_effort)
  ```
  改为：
  ```python
  async def chat_stream(
      self,
      message: str,
      thread_id: str,
      preset_id: str = "__chat__",
      model_id: str = "",
      history: list[dict[str, str]] | None = None,
      llm_params: dict | None = None,
  ) -> AsyncIterator[dict]:
      agent = self._get_or_build_agent(preset_id, model_id, llm_params=llm_params)
  ```

- [ ] **Step 6: 验证无 Python 语法错误**
  ```powershell
  & "D:\ProgramData\Miniconda3\envs\py312\python.exe" -c "from lc_agent.core.engine import AgentEngine; print('OK')"
  ```
  期望输出：`OK`

- [ ] **Step 7: commit**
  ```powershell
  cd D:\codes\lc-agent
  git add lc_agent/core/engine.py
  git commit -m "feat: unify LLM params via llm_params dict in engine"
  ```

---

## Task 3: 后端 SSE — RunStreamRequest 更新

**Files:**
- Modify: `lc_agent/server/sse.py`

- [ ] **Step 1: 更新 RunStreamRequest**

  找到（约 49 行）：
  ```python
  class RunStreamRequest(BaseModel):
      input: str | None = None
      command: dict[str, Any] | None = None
      preset_id: str = "__chat__"
      model: str = ""
      reasoning_effort: str | None = None
      replace_from_message_id: str | None = None
      history: list[dict[str, Any]] | None = None
  ```
  改为：
  ```python
  class RunStreamRequest(BaseModel):
      input: str | None = None
      command: dict[str, Any] | None = None
      preset_id: str = "__chat__"
      model: str = ""
      llm_params: dict[str, Any] | None = None
      replace_from_message_id: str | None = None
      history: list[dict[str, Any]] | None = None
  ```

- [ ] **Step 2: 更新 _send_stream 方法内对 reasoning_effort 的引用**

  在 `_send_stream` 函数内（约 207 行）：
  ```python
  reasoning_effort = req.reasoning_effort  # 删除此行
  ```
  改为：
  ```python
  llm_params = req.llm_params
  ```

  找到 `stream_kwargs` 构建（约 262 行）：
  ```python
  if reasoning_effort:
      stream_kwargs["reasoning_effort"] = reasoning_effort
  ```
  改为：
  ```python
  if llm_params:
      stream_kwargs["llm_params"] = llm_params
  ```

  找到 interrupt 后检查 state 那行（约 312 行）：
  ```python
  agent = engine._get_or_build_agent(preset_id, model_id, reasoning_effort=reasoning_effort)
  ```
  改为：
  ```python
  agent = engine._get_or_build_agent(preset_id, model_id, llm_params=llm_params)
  ```

- [ ] **Step 3: 更新 _resume_stream 方法**

  在 `_resume_stream` 函数内（约 399 行）：
  ```python
  reasoning_effort = req.reasoning_effort  # 删除
  ```
  改为：
  ```python
  llm_params = req.llm_params
  ```

  找到 `engine._get_or_build_agent` 的调用（约 419 行）：
  ```python
  agent = engine._get_or_build_agent(preset_id, model_id, reasoning_effort=reasoning_effort)
  ```
  改为：
  ```python
  agent = engine._get_or_build_agent(preset_id, model_id, llm_params=llm_params)
  ```

  注意：`get_thread_state` 接口（约 172 行）不涉及 llm_params，保持不变。

- [ ] **Step 4: 验证无错误**
  ```powershell
  & "D:\ProgramData\Miniconda3\envs\py312\python.exe" -c "from lc_agent.server.sse import RunStreamRequest; r = RunStreamRequest(llm_params={'temperature': 0.5}); print(r.llm_params)"
  ```
  期望输出：`{'temperature': 0.5}`

- [ ] **Step 5: commit**
  ```powershell
  cd D:\codes\lc-agent
  git add lc_agent/server/sse.py
  git commit -m "feat: replace reasoning_effort with llm_params in RunStreamRequest"
  ```

---

## Task 4: 前端 store — tools.ts

**Files:**
- Modify: `frontend/src/stores/tools.ts`

- [ ] **Step 1: 删除 reasoningEffort，加 llmParams**

  删除：
  ```typescript
  export type ReasoningEffort = 'default' | 'none' | 'minimal' | 'low' | 'medium' | 'high' | 'xhigh'
  ```

  在 `useToolsStore` 函数内，删除：
  ```typescript
  const reasoningEffort = ref<ReasoningEffort>('default')
  ```
  加入：
  ```typescript
  const llmParams = ref<Record<string, any> | null>(null)
  ```

  删除 `setReasoningEffort` 函数，加入：
  ```typescript
  function setLlmParam(key: string, value: any) {
    if (value === null || value === undefined || value === '') {
      if (llmParams.value) {
        delete llmParams.value[key]
        if (Object.keys(llmParams.value).length === 0) llmParams.value = null
      }
    } else {
      if (!llmParams.value) llmParams.value = {}
      llmParams.value[key] = value
    }
  }

  function resetLlmParams() {
    llmParams.value = null
  }
  ```

- [ ] **Step 2: 切换 agent 时重置 llmParams**

  在 `watch(() => agentsStore.currentAgentId, ...)` 里，调用 `resetLlmParams()`：
  ```typescript
  watch(() => agentsStore.currentAgentId, () => {
    _clearOverrides()
    syncModelWithAgentDefault()
    resetLlmParams()
  })
  ```

- [ ] **Step 3: 更新 return 对象**

  删除 `reasoningEffort`、`setReasoningEffort`，加入 `llmParams`、`setLlmParam`、`resetLlmParams`：
  ```typescript
  return {
    groups, models, mcpServers, skills, currentModel, llmParams, mcpRefreshing,
    filteredGroups, filteredMcp, filteredSkills,
    init, refreshMcpServers, toggleGroup, toggleMcp, toggleSkill,
    setModel, setLlmParam, resetLlmParams, syncModelWithAgentDefault,
  }
  ```

- [ ] **Step 4: commit（此 task 与 Task 5 前端同步提交）**
  先不 commit，等 Task 5 完成后一起提交。

---

## Task 5: 前端右侧面板 — RightPanel.vue

**Files:**
- Modify: `frontend/src/components/layout/RightPanel.vue`

- [ ] **Step 1: 替换 reasoning_effort 控件，加入 temperature slider**

  找到模板中 `reasoning-effort-control` div（约 12 行）：
  ```html
  <div class="reasoning-effort-control">
    <span class="reasoning-effort-label">reasoning_effort</span>
    <el-select
      :model-value="toolsStore.reasoningEffort"
      size="small"
      class="reasoning-effort-select"
      @update:model-value="toolsStore.setReasoningEffort"
    >
      <el-option
        v-for="effort in ['default', 'none', 'minimal', 'low', 'medium', 'high', 'xhigh']"
        :key="effort"
        :label="effort"
        :value="effort"
      />
    </el-select>
  </div>
  ```
  改为：
  ```html
  <div class="llm-params-controls">
    <div class="param-row">
      <span class="param-label">reasoning_effort</span>
      <el-select
        :model-value="toolsStore.llmParams?.reasoning_effort ?? 'default'"
        size="small"
        class="reasoning-effort-select"
        @update:model-value="(v: string) => toolsStore.setLlmParam('reasoning_effort', v === 'default' ? null : v)"
      >
        <el-option
          v-for="effort in ['default', 'none', 'minimal', 'low', 'medium', 'high', 'xhigh']"
          :key="effort"
          :label="effort"
          :value="effort"
        />
      </el-select>
    </div>
    <div class="param-row param-row-slider">
      <span class="param-label">temperature</span>
      <div class="temperature-control">
        <el-slider
          :model-value="toolsStore.llmParams?.temperature ?? 0.7"
          :min="0"
          :max="2"
          :step="0.1"
          size="small"
          class="temperature-slider"
          @update:model-value="(v: number) => toolsStore.setLlmParam('temperature', v)"
        />
        <el-input-number
          :model-value="toolsStore.llmParams?.temperature ?? 0.7"
          :min="0"
          :max="2"
          :step="0.1"
          :precision="1"
          size="small"
          controls-position="right"
          class="temperature-input"
          @update:model-value="(v: number | undefined) => toolsStore.setLlmParam('temperature', v ?? null)"
        />
      </div>
    </div>
  </div>
  ```

- [ ] **Step 2: 更新 CSS**

  在 `<style scoped>` 里删除 `.reasoning-effort-control`、`.reasoning-effort-label`、`.reasoning-effort-select` 样式，加入：
  ```css
  .llm-params-controls {
    margin-top: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .param-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .param-row-slider {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .param-label {
    font-size: 11px;
    color: var(--el-text-color-secondary);
    white-space: nowrap;
    flex-shrink: 0;
  }

  .reasoning-effort-select {
    width: 100%;
  }

  .temperature-control {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
  }

  .temperature-slider {
    flex: 1;
  }

  .temperature-input {
    width: 68px;
    flex-shrink: 0;
  }
  ```

- [ ] **Step 3: 删除 script 中的 reasoningEffort 引用**

  在 `<script setup>` 里，删除对 `reasoningEffort` 的所有引用（如有）。
  `toolsStore.setReasoningEffort` 已改为 `toolsStore.setLlmParam`，检查无残留引用。

- [ ] **Step 4: 一起 commit（Task 4 + 5）**
  ```powershell
  cd D:\codes\lc-agent
  git add frontend/src/stores/tools.ts frontend/src/components/layout/RightPanel.vue
  git commit -m "feat: replace reasoningEffort with llmParams in frontend store and RightPanel"
  ```

---

## Task 6: 前端 AgentEditorDialog.vue — 加 temperature 字段

**Files:**
- Modify: `frontend/src/components/dialogs/AgentEditorDialog.vue`

- [ ] **Step 1: 找到 form 数据结构，加 llm_params 字段**

  在 `<script setup>` 里找到 `form` reactive 对象的定义，找到并在末尾加：
  ```typescript
  llm_params: null as Record<string, any> | null,
  ```

- [ ] **Step 2: 在 preset 加载时从 llm_params 读出 temperature**

  找到 preset 数据赋值给 form 的位置（open dialog 时），在现有字段赋值后加：
  ```typescript
  form.llm_params = preset.llm_params ?? null
  ```

- [ ] **Step 3: 在模板"模型"字段下方加 temperature 输入**

  在 `el-form-item label="模型"` 的 `</el-form-item>` 闭合标签后，插入：
  ```html
  <el-form-item label="Temperature（可选，留空使用默认 0.7）">
    <div class="temperature-preset-control">
      <el-slider
        :model-value="form.llm_params?.temperature ?? 0.7"
        :min="0"
        :max="2"
        :step="0.05"
        :marks="{ 0: '精确', 1: '均衡', 2: '创意' }"
        :disabled="isCodeAgent"
        class="temp-slider"
        @update:model-value="(v: number) => {
          if (!form.llm_params) form.llm_params = {}
          form.llm_params.temperature = v
        }"
      />
      <el-input-number
        :model-value="form.llm_params?.temperature ?? 0.7"
        :min="0"
        :max="2"
        :step="0.05"
        :precision="2"
        size="small"
        controls-position="right"
        :disabled="isCodeAgent"
        style="width: 80px"
        @update:model-value="(v: number | undefined) => {
          if (v === undefined) return
          if (!form.llm_params) form.llm_params = {}
          form.llm_params.temperature = v
        }"
      />
    </div>
  </el-form-item>
  ```

- [ ] **Step 4: 提交时把 llm_params 加到 payload**

  找到保存 preset 的地方（调用 `api.createPreset` 或 `api.updatePreset` 的位置），在 payload 里加：
  ```typescript
  llm_params: form.llm_params || null,
  ```

- [ ] **Step 5: 加 CSS**
  ```css
  .temperature-preset-control {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
  }

  .temp-slider {
    flex: 1;
  }
  ```

- [ ] **Step 6: commit**
  ```powershell
  cd D:\codes\lc-agent
  git add frontend/src/components/dialogs/AgentEditorDialog.vue
  git commit -m "feat: add temperature field to agent preset editor dialog"
  ```

---

## Task 7: 前端 SSE 客户端 — sse-client.ts

**Files:**
- Modify: `frontend/src/api/sse-client.ts`

- [ ] **Step 1: 找到发送消息的请求体构建位置**

  找到构建 body 的对象，找到 `reasoning_effort` 字段，替换为 `llm_params`：
  ```typescript
  // 删除：
  reasoning_effort: toolsStore.reasoningEffort !== 'default' ? toolsStore.reasoningEffort : undefined,
  
  // 改为：
  llm_params: toolsStore.llmParams ?? undefined,
  ```

- [ ] **Step 2: 验证 TypeScript 无类型错误**

  在 frontend 目录运行：
  ```powershell
  cd D:\codes\lc-agent\frontend
  npx tsc --noEmit
  ```
  期望：无 error 输出（或只有与本次改动无关的旧 warning）。

- [ ] **Step 3: commit**
  ```powershell
  cd D:\codes\lc-agent
  git add frontend/src/api/sse-client.ts
  git commit -m "feat: send llm_params instead of reasoning_effort in SSE client"
  ```

---

## Task 8: 集成验证

**Files:** 无新文件，验证现有功能

- [ ] **Step 1: 构建前端**
  ```powershell
  cd D:\codes\lc-agent\frontend
  npm run build
  ```
  期望：Build 成功无 error。

- [ ] **Step 2: 重启 bfzs 验证启动**

  使用 restart-bfzs skill，或手动：
  ```powershell
  cd D:\codes\lc-agent-bfzs
  & "D:\ProgramData\Miniconda3\envs\py312\python.exe" -m bfzs.main --port 8001
  ```
  启动日志中确认：
  - 无 import error
  - `[Auth] Admin user exists: admin`
  - `Uvicorn running on http://127.0.0.1:8001`

- [ ] **Step 3: 浏览器验证**

  打开 `http://127.0.0.1:8001`，登录后：
  1. 右侧面板显示 `temperature` 滑块，默认 0.7，可以拖动
  2. `reasoning_effort` select 仍然显示
  3. 拖动 temperature 后发消息，服务器日志不报错
  4. 打开某个 agent 的编辑器，有 temperature 输入框

- [ ] **Step 4: 验证 preset 保存 llm_params**

  在编辑器里修改某个 preset 的 temperature 为 1.0，保存，再用 query 脚本确认：
  ```powershell
  & "D:\ProgramData\Miniconda3\envs\py312\python.exe" "D:\codes\lc-agent\.agents\skills\query-bfzs-db\scripts\query_session.py" --presets
  ```
  该 preset 的 `llm_params` 字段应显示 `{"temperature": 1.0}`。

---

## Self-Review

**Spec coverage check:**

| Spec 要求 | 对应 Task |
|-----------|-----------|
| AgentPreset + DB 加 llm_params | Task 1 |
| _create_llm 从 llm_params 读参数 | Task 2 |
| 合并逻辑（运行时优先） | Task 2 Step 2 |
| RunStreamRequest 改用 llm_params | Task 3 |
| tools.ts 删 reasoningEffort 加 llmParams | Task 4 |
| RightPanel.vue 两个控件统一写 llmParams | Task 5 |
| AgentEditorDialog.vue 加 temperature | Task 6 |
| sse-client.ts 发 llm_params | Task 7 |

全部覆盖 ✓

**Placeholder scan:** 无 TBD/TODO ✓

**Type consistency:** `llm_params: dict | None`（Python）/ `Record<string, any> | null`（TS）全链路一致 ✓
