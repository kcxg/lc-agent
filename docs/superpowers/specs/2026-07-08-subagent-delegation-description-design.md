# Subagent Delegation Description Design

## Goal

把 lc-agent 当前对子 Agent 的“可委派说明”从不可靠的 `system_prompt[:200]` 截断，升级为一个**单独维护、语义明确、优先挂在主 Agent 与子 Agent 关联关系上的字段**。

目标是让主 Agent 在看到统一 `task(subagent_type, description)` 工具时，不只是知道子 Agent 名字，还能明确知道：

- 什么时候应该调用它
- 它适合处理什么任务
- 它与其它子 Agent 的职责边界是什么

本设计参考 deepagents 的 `SubAgent.description` 思路，但结合 lc-agent 的 Web Agent / Code Agent 双来源架构，进一步将“委派描述”建模为**主从关系属性**，而不是仅仅是子 Agent 本体属性。

## Background

当前 lc-agent 的 task-mode 子 Agent 设计里，主 Agent 通过一个统一 `task` 工具选择子 Agent：

```text
Delegate a task to a sub-agent. Available subagent_type values: feapder爬虫, funboost智能体. Use description for the complete delegated task.
```

这有一个关键问题：

- 主 Agent 只知道可选的 `subagent_type` 名字
- 不知道这些子 Agent 各自擅长什么
- 也不知道何时应触发哪个子 Agent

当前 registry 内部曾使用 `system_prompt[:200]` 作为说明候选，但这个方案不可靠：

1. `system_prompt` 是给子 Agent 自己执行任务时看的内部提示词，不是给主 Agent 选人时看的路由元信息。
2. 截断 200 字会把格式要求、行为约束、输出要求等无关内容暴露给主 Agent，污染工具描述。
3. prompt 前 200 字不一定包含能力边界，甚至可能完全没有“何时调用我”的信息。
4. 对 Code Agent 而言，往往没有自然的 `system_prompt` 可截断，因此无法统一。

deepagents 的设计是显式分离：

- `name`：主 Agent 调用时使用的子 Agent 名称
- `description`：主 Agent 用来判断何时委派
- `system_prompt`：子 Agent 自己执行任务时使用

对于 lc-agent，仅复制 deepagents 的“每个 Agent 本体有一段 description”还不够，因为 lc-agent 存在一个更强的场景：

> 同一个子 Agent，被不同主 Agent 选为子 Agent 时，调用触发条件可能不同。

例如同一个 `funboost智能体`：

- 对 A 主 Agent：`当你需要查询 funboost 知识时候调用它`
- 对 B 主 Agent：`当你需要分析 funboost 分布式消费链路时调用它`
- 对 C 主 Agent：`当你不确定某个任务是否适合 funboost 时，先让它做可行性判断`

这说明“委派描述”更像是：

- **主 Agent -> 子 Agent 的关系属性**
- 而不是子 Agent 本体唯一固定属性

## Product Decisions

### 1. 新增主从关联级 `delegation_description`

主 Agent 选择子 Agent 时，除了记录子 Agent 的 ID，还必须记录一段委派描述：

```python
class SubAgentLink(BaseModel):
    agent_id: str
    delegation_description: str
```

语义：

- `agent_id`：被选中的子 Agent 标识
- `delegation_description`：告诉主 Agent“何时应该调用这个子 Agent”的一句或几句短说明

示例：

- `当你需要查询 funboost 知识时候调用它`
- `当你需要分析 feapder 爬虫项目结构、调度和抓取链路时调用它`
- `当你需要让另一个智能体并行执行通用复杂任务时调用它`

### 2. 主 Agent 勾选子 Agent 时必须填写描述

在 Web UI 中，主 Agent 编辑页不再只是简单勾选 `subagent_ids`，而是配置一个“子 Agent 关联列表”。

每条关联至少包含：

- 选择哪个子 Agent
- 为这条关联填写 `delegation_description`

这是一个强约束：

- 选了子 Agent
- 就必须填写 `delegation_description`
- 不填不能保存

理由：

- 保证主 Agent 获得明确的调用触发规则
- 避免继续依赖子 Agent 自己的 prompt 或名字猜能力
- 与 skill description 的思路一致：面向调用者描述“什么时候该用我”

### 3. 子 Agent 本体可选保留默认描述，但优先级低于关联描述

为了兼容 Code Agent 和某些默认场景，允许子 Agent 本体存在一个**可选默认委派描述**。

例如：

- Web Agent 本体可选字段：`default_delegation_description`
- Code Agent 注册时可选参数：`delegation_description`

但运行时优先级必须是：

1. 主 Agent 与子 Agent 关联上的 `delegation_description`
2. 子 Agent 本体默认描述
3. 弱提示（例如 `未提供委派描述，请仅在你明确知道其用途时调用`）

明确禁止：

- 不再把 `system_prompt[:200]` 作为长期默认兜底

### 4. 统一 `task` 工具描述生成格式

主 Agent 看到的 `task` 工具描述，必须从“只有名字”升级成“名字 + 触发说明”。

当前弱形式：

```text
Available subagent_type values: feapder爬虫, funboost智能体
```

目标形式：

```text
Delegate a task to a sub-agent.

Available subagent_type values:
- feapder爬虫: 当你需要分析 feapder 爬虫框架、调度、抓取链路和反爬问题时调用它
- funboost智能体: 当你需要查询 funboost 知识时候调用它

Use description for the complete delegated task.
```

这样主 Agent 才是在按“能力和触发场景”路由，而不是按名字盲猜。

### 5. 设计必须同时兼容 Web Agent、Code Agent、general-purpose

#### Web Agent

Web Agent 作为子 Agent 被主 Agent 选择时，关联项中必须填写 `delegation_description`。

#### Code Agent

Code Agent 本身不一定有数据库里的 preset 字段，但必须能提供一个稳定 ID，并可选提供默认描述。

例如：

```python
app.add_agent(
    name="funboost智能体",
    graph=graph,
    description="Funboost 专家",
    delegation_description="当你需要查询 funboost 知识或分析 Funboost 任务编排时调用它",
)
```

如果主 Agent 关联里填写了描述，则覆盖 Code Agent 的默认描述。

#### general-purpose

general-purpose 是框架自动生成的特殊子 Agent，也必须有明确可展示的描述。

建议默认值：

```text
当你需要一个与当前智能体能力相近、但在隔离上下文中并行处理复杂任务的工作线程时调用它。
```

若未来允许用户对 general-purpose 的调用场景进行自定义，也应优先保存在主从关联上。

## Data Model

### 现状

当前主 Agent 配置的是：

```python
subagent_ids: list[str] | None
```

这只能表达“选了哪些子 Agent”，无法表达“为什么选它、何时该调它”。

### 目标模型

新增：

```python
class SubAgentLink(BaseModel):
    agent_id: str
    delegation_description: str
```

主 Agent 上改为：

```python
subagents: list[SubAgentLink] | None
```

其中：

- `agent_id` 替代旧 `subagent_ids` 里的元素
- `delegation_description` 是关联级必填字段

### 兼容策略

项目处于早期阶段，没有历史包袱，因此允许破坏性升级，但运行时仍应温和处理未配置数据。

推荐策略：

- 新模型只保留 `subagents`
- 旧 `subagent_ids` 在迁移中转换为 `subagents=[{"agent_id": ..., "delegation_description": ""}]`
- 运行时若发现空描述，则按“未配置”处理，并在 UI/API 校验层阻止继续保存空值

不需要为历史版本编写复杂兼容性迁移逻辑。

## API Design

### AgentPreset API

当前：

```json
{
  "subagent_ids": ["agent-a", "agent-b"]
}
```

目标：

```json
{
  "subagents": [
    {
      "agent_id": "agent-a",
      "delegation_description": "当你需要查询 funboost 知识时候调用它"
    },
    {
      "agent_id": "agent-b",
      "delegation_description": "当你需要分析 feapder 爬虫链路和调度时调用它"
    }
  ]
}
```

### 校验规则

服务端保存时：

- `agent_id` 必须存在
- `delegation_description` 不能为空字符串
- 建议做 `strip()` 后非空校验
- 推荐长度上限（如 `500` 字），防止用户把完整 prompt 塞进去

### Code Agent 注册接口

对 `app.add_agent(...)` 增加可选参数：

```python
def add_agent(
    name: str,
    graph,
    description: str | None = None,
    delegation_description: str | None = None,
): ...
```

语义：

- `description`：现有 Agent 列表/展示层可继续使用
- `delegation_description`：作为该 Code Agent 的默认可委派说明

若不想新增第二个参数，也可以把现有 `description` 明确重定义为默认可委派说明，但这会混淆“展示描述”和“委派触发描述”，因此不推荐。

## Runtime Architecture

### 统一 Descriptor

运行时 registry 中统一收敛成：

```python
@dataclass
class SubAgentDescriptor:
    subagent_type: str
    agent_id: str
    display_name: str
    delegation_description: str
    kind: Literal["preset", "code", "general-purpose"]
```

这里 `delegation_description` 是面向主 Agent 的公开字段。

### 构建优先级

构建 registry 时：

1. 优先读取主 Agent 与子 Agent 关联上的 `delegation_description`
2. 若缺失，再使用子 Agent 本体默认描述（Web Agent / Code Agent / GP 默认）
3. 若仍缺失，则填弱提示，不再截断 prompt

### task 描述生成

`_make_task_tool()` 中根据 registry 生成结构化 description。

建议格式：

```text
Delegate a task to a sub-agent.

Available subagent_type values:
- {subagent_type}: {delegation_description}
- ...

Use description for the complete delegated task.
```

## Frontend Design

### 编辑器交互

当前多选子 Agent 的 UI 要升级为“子 Agent 关联配置列表”。

每行包含：

- 子 Agent 选择器
- 委派描述输入框
- 删除按钮
- 可选来源标签（网页 / 代码 / 通用）

示例：

```text
[funboost智能体]  当你需要查询 funboost 知识时候调用它
[feapder爬虫]     当你需要分析 feapder 爬虫链路和调度时调用它
```

### 表单规则

- 新增一条关联时必须先选子 Agent
- 选中后必须填写描述
- 未填描述不能保存
- 允许编辑已有描述
- 不允许同一个主 Agent 重复引用同一个子 Agent 多次，除非未来明确支持“同一子 Agent 不同触发规则的多条路由”

当前建议先禁止重复，避免复杂度膨胀。

## Error Handling

### 1. 空描述

- 前端保存前阻止
- 服务端再做一次兜底校验
- 返回明确错误：
  - `subagent delegation_description is required`

### 2. 关联指向不存在的 Agent

- 服务端保存时校验 `agent_id`
- 运行时 registry 构建时若目标不存在，跳过并写 warning

### 3. Code Agent 缺默认描述

- 允许存在
- 但如果某个主 Agent 引用它时没有提供关联描述，则 task 描述中使用弱提示
- 不再读取 `system_prompt[:200]`

## Testing

需要新增/修改测试：

### 后端模型/API

- `AgentPreset` 支持 `subagents`
- 保存时 `delegation_description` 必填
- 读写 API 返回 `subagents` 结构

### Runtime

- `_build_subagent_registry()` 优先使用关联级描述
- 缺关联描述时使用 Code Agent 默认描述
- `task` tool description 包含“名字 + 触发说明”
- 明确断言不再使用 `system_prompt[:200]`

### 前端

- 编辑器保存时，如果某条子 Agent 关联没填描述，则保存失败
- 现有 contract test 扩展：验证 payload 由 `subagent_ids` 升级成 `subagents`
- 验证重新打开编辑器时能正确回显描述

## Rollout Plan

建议实现顺序：

1. 数据模型/DB/API 增加 `subagents`
2. 前端 Agent 编辑器改为关联配置式 UI
3. 运行时 registry 改读取关联描述
4. `task` 工具描述改结构化输出
5. Code Agent 注册接口增加默认描述字段
6. 删除/废弃 `system_prompt[:200]` 兜底逻辑

## Final Decision

最终采用：

- **委派描述优先作为主 Agent 与子 Agent 之间的关联属性存储**
- **主 Agent 在勾选子 Agent 时必须填写这段描述**
- **Code Agent 可提供默认描述作为 fallback，但优先级低于关联描述**
- **不再把 `system_prompt` 截断当作委派说明**

这是最符合用户心智、最接近 deepagents 思路、也最兼容 lc-agent 当前双来源架构的设计。
