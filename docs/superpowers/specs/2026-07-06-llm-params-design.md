# llm_params 统一 LLM 参数配置 — 设计文档

**日期：** 2026-07-06  
**状态：** 待实现

---

## 背景与目标

当前 lc-agent 框架中，LLM 参数（如 `temperature`、`reasoning_effort`）分散在多处：
- `temperature` 硬编码为 `0.7`（`engine.py` 中三处）
- `reasoning_effort` 作为独立字段单独传递（`RunStreamRequest.reasoning_effort`、`tools.ts` 中的 `reasoningEffort` ref）

随着以后可能需要支持 `top_p`、`top_k`、`frequency_penalty` 等更多参数，每次都加列/加字段的方案不可扩展。

**目标：** 用一个统一的 `llm_params: dict | None` JSON 字段，在 preset（持久化）和运行时（临时覆盖）两层统一管理所有 LLM 参数。

---

## 功能范围

**本次实现：**
- `temperature`（支持范围 0.0~2.0）
- `reasoning_effort`（从独立字段迁移进 `llm_params`）

**预留扩展，本次不实现：**
- `top_p`、`top_k`、`frequency_penalty` 等（字段已就位，不需要改结构，只需前端表单加项目即可）

---

## 参数优先级

```
请求时临时覆盖 (RunStreamRequest.llm_params)
    ↓ 若为 null
preset 持久化值 (AgentPreset.llm_params)
    ↓ 若字段不存在或为 null
全局代码默认值 (temperature=0.7, reasoning_effort=None)
```

---

## 后端设计

### 1. AgentPreset + AgentPresetDB

**`lc_agent/core/models.py`：**
```python
class AgentPreset(BaseModel):
    ...
    llm_params: dict | None = None  # e.g. {"temperature": 0.7, "reasoning_effort": "high"}
```

**`lc_agent/db/models.py`：**
```python
class AgentPresetDB(SQLModel, table=True):
    ...
    llm_params: dict | None = Field(default=None, sa_column=Column(JSON))
```

Alembic 会在启动时自动迁移，无需手动创建 migration 文件。

### 2. AgentEngine._create_llm

```python
def _create_llm(self, model_info, model_id, llm_params: dict | None = None):
    params = llm_params or {}
    temperature = params.get("temperature", 0.7)
    reasoning_effort = params.get("reasoning_effort")  # None = 不传
    ...
```

### 3. AgentEngine._get_or_build_agent + cache key

```python
# cache key 变更：之前 reasoning_effort 单独加入 key，现在整个 llm_params 加入
def _get_agent_cache_key(self, preset_id, model_id="", llm_params=None):
    key = f"{preset_id}::model::{model_id}" if model_id else preset_id
    if llm_params:
        import json
        key = f"{key}::llm::{json.dumps(llm_params, sort_keys=True)}"
    return key
```

### 4. RunStreamRequest（server/sse.py）

```python
class RunStreamRequest(BaseModel):
    input: str | None = None
    command: dict | None = None
    preset_id: str = "__chat__"
    model: str = ""
    llm_params: dict | None = None          # 新增，替代 reasoning_effort
    # reasoning_effort: str | None = None   # 删除
    replace_from_message_id: str | None = None
    history: list[dict] | None = None
```

运行时 `llm_params` 与 preset 里的 `llm_params` **合并，运行时优先**：

```python
# engine.py 里的合并逻辑
effective_params = {**(preset.llm_params or {}), **(request_llm_params or {})}
```

即：用户在右侧面板只设了 `temperature`，preset 里的 `reasoning_effort` 仍然生效；用户也设了 `reasoning_effort` 则以用户设置为准。

### 5. Agent Preset REST API

`server/routes/agents.py` 中创建/更新 preset 的接口已用 pydantic 接收 `AgentPreset`，加了 `llm_params` 字段后自动透传，**无需额外改动**。

---

## 前端设计

### 1. stores/tools.ts

删除：
```typescript
const reasoningEffort = ref<ReasoningEffort>('default')
function setReasoningEffort(value: ReasoningEffort) { ... }
```

新增：
```typescript
// null 表示不覆盖，使用 preset 里的值
const llmParams = ref<Record<string, any> | null>(null)

function setLlmParam(key: string, value: any) {
    if (llmParams.value === null) llmParams.value = {}
    if (value === null || value === undefined) {
        // 删除该 key，若 dict 为空则整体置 null
        delete llmParams.value[key]
        if (Object.keys(llmParams.value).length === 0) llmParams.value = null
    } else {
        llmParams.value[key] = value
    }
}
```

切换 agent 时重置 `llmParams`（防止上一个 agent 的值带入下一个）。

### 2. components/layout/RightPanel.vue

**删除** `reasoning_effort` 的 `el-select`。

**新增**（放在"模型"区块内，模型选择器下方）：

```
reasoning_effort: [default ▼]     ← 保留 el-select 样式
temperature:      ○──●──── 0.7   ← 新增：el-slider + el-input-number 联动
```

temperature 默认值：`null`（显示 placeholder 提示"不覆盖"），只有用户拖动过才设值。

考虑到右侧面板宽度（350px），slider 宽度约 200px，右侧 input-number 宽度约 60px，布局紧凑。

**"重置"小按钮**（可选）：当 `llmParams` 非空时显示，点击清空所有临时覆盖。

### 3. components/dialogs/AgentEditorDialog.vue

在"模型"字段下方新增：

```
Temperature（可选，留空使用默认 0.7）
[====●=====]  0.7    （range 0~2，step 0.05，marks: {0:"精确", 1:"均衡", 2:"创意"}）
```

`form.llm_params.temperature` — 读写（保存时作为 `llm_params` 的一部分）。

### 4. api/sse-client.ts

发消息时：
```typescript
// 之前
reasoning_effort: toolsStore.reasoningEffort !== 'default' ? toolsStore.reasoningEffort : undefined

// 之后
llm_params: toolsStore.llmParams ?? undefined
```

---

## 兼容性说明

- 旧 preset 的 `llm_params` 为 `null` → fallback 全局默认值，行为不变
- Alembic 自动 ALTER TABLE 加列，已有数据不受影响
- `reasoning_effort` 从 `RunStreamRequest` 删除，前端同步删除，**无旧客户端需兼容**（早期开发阶段）

---

## 不在本次范围内

- 把 `temperature` 配置写进 `config.jsonc`（model 级别）
- 支持 `top_p`、`top_k`、`frequency_penalty` 前端输入（结构已就位，表单扩展留以后）
- 右侧面板 llm_params 跨会话持久化（刷新即重置，同 reasoning_effort 现有行为）
