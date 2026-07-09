# DeepAgents-Style Task Subagent Mode Design

## Goal

把 lc-agent 当前“每个子 Agent 暴露成一个 `subagent_xxx` 工具”的模式，重构为更接近 deepagents 的统一 `task(subagent_type, description)` 模式。

核心目标是：

- 避免中文 Agent 名称被 `_sanitize_subagent_tool_name()` 转成无意义 ASCII 工具名。
- 让主 Agent 通过一个稳定工具 `task` 委派任务，由 `subagent_type` 选择具体子 Agent。
- 支持每个 Agent 单独开启一个 general-purpose 子 Agent。
- general-purpose 可以作为“和当前 Agent 能力相同的隔离工作线程”使用，但它自己运行时没有 `task` 能力，避免自我递归。
- custom 子 Agent 是否还能继续委派，完全取决于用户是否在该 custom Agent 页面显式配置了子 Agent。
- 保留现有 `_depth` / `max_subagent_depth` 作为兜底保护，但不再把它作为 general-purpose 防递归的主要机制。

## Background

当前 lc-agent 的子 Agent 实现是 subagents-as-tools：每个被勾选的子 Agent 会生成一个独立工具，例如：

```text
subagent_funboost_ab12cd34(query="...")
subagent_python_ef56abcd(query="...")
```

这个方案有两个明显问题：

1. **中文名称丢失语义**
   当前工具名必须满足 LLM function name 限制，`_sanitize_subagent_tool_name()` 会把中文 Agent 名编码成 ASCII，中文名会被丢弃，最后只剩短 ID 或下划线。这会降低模型理解能力，也让调试体验很差。

2. **工具数量随子 Agent 数量膨胀**
   每个子 Agent 都占一个工具名，主 Agent 看到的是一堆 `subagent_xxx` 函数。deepagents 的设计更偏向一个统一 `task` 工具，通过 `subagent_type` 参数选择子 Agent。

用户已经明确选择方案 2：**更接近 deepagents 原生 task 模式**，而不是最小侵入地保留多个 `subagent_xxx` 工具。

## Non-goals

本次不做以下事情：

- 不直接把整个 lc-agent 改成 deepagents runtime。
- 不要求所有自定义 code agent 自动获得框架注入的 middleware；现有 `app.add_agent(name, graph)` 仍由用户自己控制 graph。
- 不删除 `_depth` 和 `max_subagent_depth`，只降低它们在业务语义里的地位。
- 不做复杂历史兼容迁移。项目处于早期阶段，没有历史包袱；但已有 UI 回放逻辑能自然显示新协议即可。
- 不用文本长度、启发式摘要等方式判断子 Agent 最终答案。

## Product Decisions

### 1. 统一任务工具

主 Agent 不再看到多个 `subagent_xxx` 工具，而是看到一个 `task` 工具。

工具 schema：

```python
class TaskInput(BaseModel):
    subagent_type: str
    description: str
```

LLM 调用形式：

```text
task(subagent_type="funboost教程查询智能体", description="查询 funboost 的定时任务用法，并总结关键代码示例")
```

其中：

- `subagent_type` 是给 LLM 使用的子 Agent 类型标识。
- `description` 是委派给子 Agent 的完整任务描述。
- UI 仍显示用户友好的 Agent 名称，而不是 `task`。

### 2. subagent_type 选择规则

`subagent_type` 默认使用子 Agent 的显示名称 `preset.name`。

如果同一个父 Agent 可用子 Agent 中出现重名，则为重名项生成稳定后缀：

```text
<name>#<short_id>
```

例如：

```text
资料查询#abc12345
资料查询#def67890
```

这只影响当前父 Agent 的 task registry，不要求全局唯一。

设计理由：

- 中文名可以原样作为普通字符串参数，不再受 function name ASCII 限制。
- LLM 更容易根据自然语言名称选择子 Agent。
- 工具名稳定为 `task`，简化事件识别和前端显示。

### 3. general-purpose 单独开关

每个 Web 创建的 Agent 页面增加一个独立复选框：

```text
[ ] 启用通用子 Agent
```

这个开关不等同于把自己加入 `subagent_ids`。

新增字段：

```python
class AgentPreset(BaseModel):
    enable_general_purpose_subagent: bool = False
```

数据库对应字段：

```python
class AgentPresetDB(SQLModel, table=True):
    enable_general_purpose_subagent: bool = False
```

API 请求/响应也带上该字段。

### 4. general-purpose 的能力继承

用户已选择 A：general-purpose 全继承当前主 Agent 能力，但去掉 task。

具体规则：

- 继承当前 Agent 的 model、LLM 参数、system prompt。
- 继承当前 Agent 可用的普通工具组、MCP 工具、Skills。
- 继承 TodoList、Summarization 等框架自动 middleware。
- 不注入 `task` 工具。
- 不继承当前 Agent 的 `subagent_ids` 派发能力。

它的定位是：

> 一个与当前 Agent 能力相同的隔离工作线程，用于并行处理复杂子任务、隔离上下文、减少主上下文污染。

### 5. custom 子 Agent 的继续委派规则

用户已选择 A：custom 子 Agent 如果自己配置了子 Agent，则作为子 Agent 运行时也允许继续委派。

规则：

- 每个 Agent 默认没有任何子 Agent。
- 是否拥有子 Agent 必须用户在该 Agent 页面显式勾选。
- custom 子 Agent 运行时会按自己的 `subagent_ids` 和 `enable_general_purpose_subagent` 构建自己的 task registry。
- general-purpose 是例外：它运行时永远不注入 task。

### 6. depth 保留为兜底

保留现有 `_depth` 和 `agent.max_subagent_depth`。

用途改为安全兜底：

- 防止用户手动配置 A -> B -> A 这类循环后无限嵌套。
- 防止模型连续多层委派造成 LangGraph 递归爆炸。
- 超过深度时不注入 task 或跳过更深层子 Agent，并记录 warning。

但 general-purpose 防递归不依赖 depth，而是直接不注入 task。

## Architecture

### Existing architecture

当前核心路径：

- [engine.py](file:///d:/codes/lc-agent/lc_agent/core/engine.py) 构建 Agent。
- `AgentPreset.subagent_ids` 决定可用子 Agent。
- `_make_subagent_tool()` 为每个子 Agent 创建独立工具。
- `stream_utils.convert_stream_event()` 通过 `subagent_tool_names` 判断某个 tool call 是否子 Agent。
- `SubAgentRunTracker` 把子 Agent 事件持久化为子会话。
- 前端 `SubAgentCard.vue` 渲染子 Agent 卡片。

新架构保留子会话、流式事件、卡片展示，但替换子 Agent 工具注册方式。

### New architecture

新增一个内部 task registry：

```python
@dataclass
class SubAgentDescriptor:
    subagent_type: str
    preset_id: str
    display_name: str
    description: str
    kind: Literal["preset", "general-purpose"]
```

构建父 Agent 时：

1. 根据 `preset.subagent_ids` 收集 custom/builtin/code 子 Agent。
2. 如果 `preset.enable_general_purpose_subagent` 为 true，额外加入 `general-purpose`。
3. 为每个 descriptor 分配 `subagent_type`。
4. 如果 registry 非空，向父 Agent 注入一个 `task` 工具。
5. `task` 工具内部按 `subagent_type` 找 descriptor，再构建/调用对应子 Agent。
6. Agent metadata 暴露：
   - `subagent_tool_names = {"task"}` 或更明确的 task tool marker。
   - `subagent_display_map: dict[subagent_type, display_name]`。
   - `subagent_type_map: dict[subagent_type, descriptor]`。

### Task tool behavior

`task` 工具执行流程：

1. 校验 `subagent_type` 是否在当前 registry 中。
2. 如果不存在，返回清晰错误，列出可选 `subagent_type`。
3. 根据 descriptor 构建目标子 Agent：
   - `kind == "preset"`：调用现有 `_get_or_build_agent(preset_id, _depth=depth + 1)`。
   - `kind == "general-purpose"`：构建一个继承当前 preset 能力但 `disable_task=True` 的临时/缓存 Agent。
4. 用 `description` 作为子 Agent 用户输入。
5. 透传 `RunnableConfig`，保留 nested event streaming。
6. 设置子会话 thread id，继续沿用 `parent_thread_id--sa--tool_call_id` 这类稳定格式。
7. 返回 `_extract_subagent_result(msgs)` 的结果。

### General-purpose construction

general-purpose 不应是数据库里的真实 Agent，也不应该出现在 available-subagents 列表中。

推荐实现方式：

```python
def _build_general_purpose_subagent(parent_preset: AgentPreset, depth: int):
    cloned = parent_preset.model_copy(update={
        "id": f"{parent_preset.id}::general-purpose",
        "name": "general-purpose",
        "subagent_ids": None,
        "enable_general_purpose_subagent": False,
    })
    return self._build_agent_from_preset(cloned, _depth=depth, disable_task=True)
```

实际实现时可以按现有 `AgentEngine` 结构拆分私有方法，避免复制整段 build 逻辑。

### Event protocol changes

当前协议按 tool name 判断子 Agent：

```text
tool_name in subagent_tool_names
```

新协议需要按 `task` + `subagent_type` 判断。

#### on_tool_start

当收到：

```json
{
  "name": "task",
  "data": {
    "input": {
      "subagent_type": "funboost教程查询智能体",
      "description": "..."
    }
  }
}
```

且 `subagent_type` 存在于 registry 时，输出：

```json
{
  "type": "subagent_start",
  "name": "funboost教程查询智能体",
  "subagent_type": "funboost教程查询智能体",
  "tool_call_id": "...",
  "query": "..."
}
```

这里 `query` 字段为了兼容前端命名继续保留，但内容来自 `description`。

#### on_tool_end

`task` 结束时输出：

```json
{
  "type": "subagent_done",
  "tool_call_id": "...",
  "result_preview": "...",
  "status": "done"
}
```

普通 `tool_result` 对 task 子 Agent 调用继续抑制，避免父消息里出现重复结果。

#### nested events

子 Agent 内部 token、thinking、tool call 仍依赖 LangGraph nested metadata / checkpoint namespace 识别。

由于所有边界工具名都变成 `task`，需要在 start 时建立：

```python
active_subagent_runs[tool_call_id] = {
    "subagent_type": "...",
    "display_name": "...",
}
```

后续 nested event 通过 checkpoint namespace 中的 tool_call_id 归属到对应运行。

### SubAgentRunTracker changes

`SubAgentRunTracker` 当前 `subagent_display_map` 是 tool_name -> display_name。

新设计改为 subagent_type -> display_name。

`subagent_start` payload 应直接包含：

```json
{
  "name": "funboost教程查询智能体",
  "subagent_type": "funboost教程查询智能体",
  "query": "..."
}
```

Tracker 不应该显示 `task`，而应该显示 `payload.name` 或通过 `subagent_type` 查 display map。

### Frontend changes

#### Agent editor

在 [AgentEditorDialog.vue](file:///d:/codes/lc-agent/frontend/src/components/dialogs/AgentEditorDialog.vue) 的“子Agent” tab 增加 general-purpose 复选框。

建议 UI：

```text
通用子 Agent
[ ] 启用通用子 Agent
    让当前 Agent 可以把复杂任务委派给一个同能力的隔离 worker。该 worker 不会继续调用 task。

专业子 Agent
[ ] funboost教程查询智能体
[ ] python专家
```

保存 payload 增加：

```typescript
enable_general_purpose_subagent: form.value.enable_general_purpose_subagent
```

新建 Agent 默认值：

```typescript
enable_general_purpose_subagent: false
subagent_ids: []
```

#### Stores and API types

[agents.ts](file:///d:/codes/lc-agent/frontend/src/stores/agents.ts) 的 `AgentPreset` 类型需要增加字段：

```typescript
enable_general_purpose_subagent?: boolean
```

创建/更新 Agent 时带上该字段。

#### Chat UI

现有 `SubAgentCard.vue` 可以基本复用。

需要确认 tool call entry 中：

```json
{
  "name": "funboost教程查询智能体",
  "is_subagent": true,
  "args": {
    "subagent_type": "funboost教程查询智能体",
    "description": "..."
  }
}
```

前端不应该显示 `task` 作为卡片标题。

## Data Model

### AgentPreset

修改 [models.py](file:///d:/codes/lc-agent/lc_agent/core/models.py)：

```python
class AgentPreset(BaseModel):
    enable_general_purpose_subagent: bool = False
```

### AgentPresetDB

修改 [models.py](file:///d:/codes/lc-agent/lc_agent/db/models.py)：

```python
class AgentPresetDB(SQLModel, table=True):
    enable_general_purpose_subagent: bool = False
```

项目早期，无需兼容性迁移。仍可按现有 Alembic 自动迁移模式新增 migration。

### API

修改 [agents.py](file:///d:/codes/lc-agent/lc_agent/server/routes/agents.py)：

- `AgentCreateRequest` 增加字段。
- `AgentUpdateRequest` 增加字段。
- `_preset_to_dict()` 返回字段。
- `list_agents()` DB rows 返回字段。
- `create_agent()` 写入 DB 并更新 engine preset。
- `update_agent()` 写入 DB 并 invalidate cache。

## Error Handling

### Unknown subagent_type

如果模型调用不存在的 `subagent_type`：

```text
Unknown subagent_type: xxx. Available subagent_type values: general-purpose, funboost教程查询智能体, python专家
```

这样模型有机会自我修正并重试。

### No subagents configured

如果当前 Agent 没有启用 general-purpose，也没有配置 `subagent_ids`，则不注入 `task` 工具。

模型不会知道可以委派。

### Circular custom subagents

如果用户配置 A -> B -> A：

- `_depth` / `max_subagent_depth` 兜底阻断更深层 task 注入。
- 不因为循环直接让主 Agent 构建失败。
- 记录 warning。

### General-purpose recursion

general-purpose 构建时强制 `disable_task=True`，因此它自己看不到 `task` 工具。

这是主要防递归机制，不依赖模型听话，也不依赖 depth。

## Testing Strategy

### Backend unit tests

新增或修改：

- [test_engine_subagents.py](file:///d:/codes/lc-agent/tests/test_engine_subagents.py)
  - 父 Agent 配置多个子 Agent 时，只注入一个 `task` 工具。
  - `task` schema 包含 `subagent_type` 和 `description`。
  - 中文 Agent 名能作为 `subagent_type` 保留。
  - 重名子 Agent 会生成稳定 disambiguated type。
  - 未启用任何子 Agent 时不注入 `task`。
  - general-purpose 开启后出现在 registry。
  - general-purpose 子 Agent 构建时不含 `task`。

- [test_stream_utils_subagents.py](file:///d:/codes/lc-agent/tests/test_stream_utils_subagents.py)
  - `on_tool_start name=task` + 合法 `subagent_type` 产生 `subagent_start`。
  - `description` 映射到 `query`。
  - task 的 `tool_result` 被抑制，改为 `subagent_done`。
  - 普通工具名 `task` 但无合法 subagent_type 时不被误判。

- [test_subagent_run_tracker.py](file:///d:/codes/lc-agent/tests/test_subagent_run_tracker.py)
  - `subagent_start` 显示 name 不显示 `task`。
  - 子会话 ID 仍按 parent + tool_call_id 生成。

- [test_routes_agents.py](file:///d:/codes/lc-agent/tests/test_routes_agents.py)
  - create/update/list 正确读写 `enable_general_purpose_subagent`。

### Frontend checks

新增或修改现有 contract script：

- `frontend/scripts/check-subagent-reducers-contract.mjs`
  - 确认 task 模式事件能生成 subagent card。
  - 确认 card title 使用 display name，不使用 `task`。

可补一个轻量脚本检查 Agent editor：

- `frontend/scripts/check-agent-editor-general-purpose-contract.mjs`
  - 检查 `enable_general_purpose_subagent` 字段存在。
  - 检查保存 payload 包含该字段。

### Manual verification

1. 创建一个中文名 Agent：`funboost教程查询智能体`。
2. 创建一个主 Agent，勾选该 Agent 作为子 Agent。
3. 询问主 Agent 多知识点问题。
4. 观察模型工具调用应该是：
   ```json
   {"name":"task","args":{"subagent_type":"funboost教程查询智能体","description":"..."}}
   ```
5. 主聊天显示子 Agent 卡片标题为中文名。
6. 点击卡片进入子会话，刷新后仍能加载消息。
7. 创建另一个 Agent，启用 general-purpose。
8. 让主 Agent 并行拆分任务，确认 general-purpose 能被调用。
9. 确认 general-purpose 内部没有继续调用 `task`。

## Migration Notes

本项目当前处于早期开发阶段，无历史包袱。

允许破坏性调整：

- 停止生成 `subagent_xxx` 工具。
- 新 SSE 事件按 task 模式解析。
- 旧会话中已有的 `subagent_xxx` tool call 不要求完美回放。

但为了降低开发风险，建议在实现中短期保留旧 helper 名称或兼容逻辑，等 task 模式稳定后再删除。

## Open Questions

没有阻塞性开放问题。

已确认的用户决策：

- general-purpose 继承策略：全继承主 Agent 能力，但无 task。
- custom 子 Agent 嵌套策略：用户显式配置则允许继续派发。
- UI 配置：单独复选框启用 general-purpose。
- 总体方案：采用更接近 deepagents 的方案 2。

## Self-review

- 没有保留 TBD/TODO 占位内容。
- spec 范围集中在 task 子 Agent 模式，不混入无关功能。
- general-purpose 防递归机制明确：不注入 task。
- custom 子 Agent 继续委派机制明确：由自己的页面配置决定。
- depth 保留但降级为兜底保护。
- 后端、SSE、Tracker、前端、数据库、API、测试范围均覆盖。
