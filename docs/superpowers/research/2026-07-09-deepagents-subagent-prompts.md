# deepagents 子 Agent 提示词与 task 工具深度调研（第二版）

> 调研时间：2026-07-09（第一版）→ 2026-07-10（深度修订）
> 目的：完整记录官方实现，并标注哪些适合迁移到 lc-agent、哪些不宜照搬，指导后续改造。
> 源码：`D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\deepagents\middleware\subagents.py`
>        `D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\deepagents\middleware\_utils.py`

---

## 0. 核心设计哲学（先看这个）

deepagents 的子 Agent 系统建立在两个关键认知上：

**认知 A：LLM 是有"对话惯性"的**
LLM 从训练数据中学到的是"和人类多轮对话"，不会自然地把答案集中到最后一条消息。所以子 Agent 必须被明确告知："你的中间过程没人看，只有最后一条消息有价值"。

**认知 B：主 Agent 会错误地假设上下文共享**
主 Agent 知道对话背景，LLM 在生成 `task` 调用时会无意识地省略背景，误以为子 Agent "懂前文"。必须通过提示词强制主 Agent 意识到子 Agent 是完全无状态的。

这两个认知对应两个不同的提示词注入点，下面详细展开。

---

## 1. 子 Agent（工作者）侧的系统提示词

### 1.1 `DEFAULT_SUBAGENT_PROMPT` 原文

`subagents.py:235-238`：

```python
DEFAULT_SUBAGENT_PROMPT = """In order to complete the objective that the user asks of you, you have access to a number of standard tools.

The calling agent only sees your final assistant message, not your intermediate work, tool results, or status tracking. Ensure your final
response contains the complete answer."""
```

**逐句解析：**

| 句子 | 作用 |
|------|------|
| `In order to complete the objective that the user asks of you` | 用"用户要求你完成的目标"而非"主 Agent 委派"——LLM 视角，不用框架术语 |
| `you have access to a number of standard tools` | 告知有工具，鼓励主动使用 |
| `The calling agent only sees your final assistant message` | 核心句。"calling agent"而非"主 Agent"，更自然；"only... final"明确截断点 |
| `not your intermediate work, tool results, or status tracking` | 列举三种无效内容：中间步骤、工具结果、进度跟踪。防止 LLM 把这些当作"已交付答案" |
| `Ensure your final response contains the complete answer` | 强制约束：完整答案必须在最后一条消息里 |

**设计亮点：**
- 全程第二人称（"you"），没有出现"子 Agent"这个框架概念
- "final assistant message"是 LangChain/LLM 能理解的概念（对应 AIMessage），不是抽象名词
- 两句话，极简，不造成额外认知负担

### 1.2 `DEFAULT_SUBAGENT_PROMPT` 的使用方式

`subagents.py:425-429`：

```python
GENERAL_PURPOSE_SUBAGENT: SubAgent = {
    "name": "general-purpose",
    "description": DEFAULT_GENERAL_PURPOSE_DESCRIPTION,
    "system_prompt": DEFAULT_SUBAGENT_PROMPT,
}
```

这是 deepagents 的 `general-purpose` 子 Agent 默认配置。`system_prompt` 字段直接就是 `DEFAULT_SUBAGENT_PROMPT`，没有追加其他内容。

子 Agent build 时（`_get_subagents` 方法，`subagents.py:728-741`）：

```python
create_agent_kwargs: dict[str, Any] = {
    "system_prompt": spec["system_prompt"],   # 直接用，不做任何追加
    "tools": spec["tools"],
    "middleware": middleware,
    ...
}
runnable = create_agent(model, **create_agent_kwargs)
```

**注意**：deepagents 子 Agent build 时**不会加** `TodoListMiddleware`、skills 中间件等。子 Agent 的 middleware 列表默认为空（或只有 `HumanInTheLoopMiddleware`），主 Agent 拥有的 Todo/技能等全部不传递给子 Agent。

### 1.3 lc-agent 的现状对比

lc-agent 的 `build_agent` 递归调用自身来 build 子 Agent，每次调用都会加 `TodoListMiddleware`、memory 中间件、技能中间件等全套中间件。子 Agent 的提示词是 preset 里的 `system_prompt`，没有注入任何"你是被委派的工作者"的说明。

**差距**：
1. ❌ 子 Agent 没有 `DEFAULT_SUBAGENT_PROMPT`，不知道"只有最后一条消息有效"
2. ⚠️ 子 Agent 被加了 `TodoListMiddleware`，LLM 可能把 write_todos 当成"已交付答案"，实际答案零散在工具结果里
3. ⚠️ 子 Agent 的技能注入可能干扰它的专注度

---

## 2. 主 Agent 侧：关于 task 工具的系统提示词

### 2.1 `TASK_SYSTEM_PROMPT` 原文

`subagents.py:390-420`，追加到主 Agent system message 末尾：

```text
## `task` (subagent spawner)

You have access to a `task` tool to launch short-lived subagents that handle isolated tasks. These agents are ephemeral — they live only for the duration of the task and return a single result.

When to use the task tool:

- When a task is complex and multi-step, and can be fully delegated in isolation
- When a task is independent of other tasks and can run in parallel
- When a task requires focused reasoning or heavy token/context usage that would bloat the orchestrator thread
- When sandboxing improves reliability (e.g. code execution, structured searches, data formatting)
- When you only care about the output of the subagent, and not the intermediate steps (ex. performing a lot of research and then returned a synthesized report, performing a series of computations or lookups to achieve a concise, relevant answer.)

Subagent lifecycle:

1. **Spawn** → Provide clear role, instructions, and expected output
2. **Run** → The subagent completes the task autonomously
3. **Return** → The subagent provides a single structured result
4. **Reconcile** → Incorporate or synthesize the result into the main thread

When NOT to use the task tool:

- If you need to see the intermediate reasoning or steps after the subagent has completed (the task tool hides them)
- If the task is trivial (a few tool calls or simple lookup)
- If delegating does not reduce token usage, complexity, or context switching
- If splitting would add latency without benefit

## Important Task Tool Usage Notes to Remember

- Whenever possible, parallelize the work that you do. This is true for both tool_calls, and for tasks. Whenever you have independent steps to complete - make tool_calls, or kick off tasks (subagents) in parallel to accomplish them faster. This saves time for the user, which is incredibly important.
- Remember to use the `task` tool to silo independent tasks within a multi-part objective.
- You should use the `task` tool whenever you have a complex task that will take multiple steps, and is independent from other tasks that the agent needs to complete. These agents are highly competent and efficient.
```

最后，在 `SubAgentMiddleware.__init__`（`subagents.py:683-685`）里，`TASK_SYSTEM_PROMPT` 末尾还追加了可用子 Agent 列表：

```python
agents_desc = "\n".join(f"- {s['name']}: {s['description']}" for s in subagent_specs)
self.system_prompt = system_prompt + "\n\nAvailable subagent types:\n\n" + agents_desc
```

所以最终拼到主 Agent system 里的是：

```text
[TASK_SYSTEM_PROMPT 上面这段]

Available subagent types:

- general-purpose: General-purpose agent for researching...
- code-reviewer: use this agent after you are done creating...
```

### 2.2 注入机制：`wrap_model_call` + `append_to_system_message`

`subagents.py:747-756`：

```python
def wrap_model_call(self, request, handler):
    if self.system_prompt is not None:
        new_system_message = append_to_system_message(request.system_message, self.system_prompt)
        return handler(request.override(system_message=new_system_message))
    return handler(request)
```

`_utils.py:6-23`（`append_to_system_message` 完整实现）：

```python
def append_to_system_message(system_message, text):
    new_content: list[ContentBlock] = list(system_message.content_blocks) if system_message else []
    if new_content:
        text = f"\n\n{text}"
    new_content.append({"type": "text", "text": text})
    return SystemMessage(content_blocks=new_content)  # ← 用 content_blocks 参数，非 content
```

**关键细节**：`SystemMessage(content_blocks=new_content)` 而不是 `SystemMessage(content=new_content)`。两者在 langchain_core 里都能工作，但官方用的是 `content_blocks`，语义更明确。

### 2.3 lc-agent 现状对比

lc-agent 目前把 task 工具的子 Agent 列表只放在 **`task` 工具的 description 字段**里，不会往主 Agent system message 里注入 `TASK_SYSTEM_PROMPT`。

**差距**：
- ❌ 主 Agent 在处理用户请求时不会"看到" task 工具的使用时机指引（系统提示词比工具描述更先被 LLM 注意）
- ❌ 没有"When to use / When NOT to use"的明确判断条件
- ❌ 没有 `Subagent lifecycle` 的 4 步骤，主 Agent 不知道要在 `description` 里写完整任务

---

## 3. `task` 工具的 description 和参数 schema

### 3.1 `TASK_TOOL_DESCRIPTION` 原文（含 `{available_agents}` 占位符）

完整原文见 `subagents.py:280-388`，关键结构：

```text
Launch an ephemeral subagent to handle complex, multi-step independent tasks with isolated context windows.

Available agent types and the tools they have access to:
{available_agents}

When using the Task tool, you must specify a subagent_type parameter to select which agent type to use.

## Usage notes:
1. Launch multiple agents concurrently whenever possible...
2. When the agent is done, it will return a single message back to you. The result returned by the agent is not visible to the user...
3. Each agent invocation is stateless. You will not be able to send additional messages to the agent, nor will the agent be able to communicate with you outside of its final report. Therefore, your prompt should contain a highly detailed task description for the agent to perform autonomously and you should specify exactly what information the agent should return back to you in its final and only message to you.
4. The agent's outputs should generally be trusted
5. Clearly tell the agent whether you expect it to create content, perform analysis, or just do research...
6. If the agent description mentions that it should be used proactively...
7. When only the general-purpose agent is provided, you should use it for all tasks...

### Example usage of the general-purpose agent:
<example_agent_descriptions>
"general-purpose": use this agent for general purpose tasks...
</example_agent_descriptions>
<example>
...4 个示例...
</example>

### Example usage with custom agents:
<example_agent_descriptions>
"content-reviewer": ...
"greeting-responder": ...
"research-analyst": ...
</example_agent_descriptions>
<example>
...3 个示例...
</example>
```

**Usage note 3 逐字解析（这是最重要的一条）：**

> `Each agent invocation is **stateless**.`

"stateless"是核心词。它不说"子 Agent 没有上下文"，它说"无状态"——这是 LLM 能精确理解的工程概念。

> `You will not be able to send additional messages to the agent, nor will the agent be able to communicate with you outside of its final report.`

两个方向都说了：你不能追加消息，它不能主动联系你。彻底堵死了主 Agent 的"等子 Agent 汇报"的惰性假设。

> `Therefore, your prompt should contain a highly detailed task description...`

`Therefore` 是关键连词，把"无状态"和"要写详细描述"因果连接起来，LLM 会理解为逻辑推论，而不是命令。

### 3.2 `TaskToolSchema`：参数级 description（Pydantic）

`subagents.py:267-277`：

```python
class TaskToolSchema(BaseModel):
    """Input schema for the `task` tool."""

    description: str = Field(
        description=(
            "A detailed description of the task for the subagent to perform autonomously. "
            "Include all necessary context and specify the expected output format."
        )
    )

    subagent_type: str = Field(
        description=(
            "The type of subagent to use. Must be one of the available agent types listed in the tool description."
        )
    )
```

参数级 description 的价值：LLM 在生成工具调用时，会同时看到**工具级描述**和**参数级描述**。`description` 字段的 Field description 里"Include all necessary context"直接告诉 LLM 填什么，弱模型不会只填一句话敷衍了事。

### 3.3 注册方式（`infer_schema=False` 的重要性）

`subagents.py:590-597`：

```python
return StructuredTool.from_function(
    name="task",
    func=task,
    coroutine=atask,
    description=description,
    infer_schema=False,       # ← 关键
    args_schema=TaskToolSchema,
)
```

`infer_schema=False` + 显式 `args_schema=TaskToolSchema` 的组合确保：
- LLM 看到的参数 description 来自 Pydantic Field，而不是从函数签名推断
- `runtime: ToolRuntime` 参数不会出现在 LLM 的 schema 里

---

## 4. 状态隔离机制：哪些状态传给子 Agent

### 4.1 `_EXCLUDED_STATE_KEYS`

`subagents.py:240-263`：

```python
_EXCLUDED_STATE_KEYS = {
    "messages",          # 对话历史，子 Agent 只看自己的 HumanMessage(description)
    "todos",             # 父 Agent 的 todo 列表
    "structured_response",
    "skills_metadata",   # 父 Agent 的技能状态
    "skills_load_errors",
    "memory_contents",   # 父 Agent 的记忆
}
```

子 Agent 启动时的状态构成（`subagents.py:534-539`）：

```python
subagent_state = {k: v for k, v in runtime.state.items() if k not in _EXCLUDED_STATE_KEYS}
subagent_state["messages"] = [HumanMessage(content=description)]
```

即：
- 父 Agent 状态里除以上 6 个 key 之外的字段**会透传**给子 Agent（如自定义 state schema 字段）
- 对话历史全部抹去，替换为 `[HumanMessage(description)]`

### 4.2 lc-agent 对比

lc-agent 目前在 `_make_task_tool` 里用 `HumanMessage(description)` 作为子 Agent 的输入（行为与 deepagents 一致），但没有按照 `_EXCLUDED_STATE_KEYS` 过滤父 Agent 状态。

---

## 5. 子 Agent 的返回协议

### 5.1 提取最终答案的逻辑

`subagents.py:514-525`（核心片段）：

```python
content = ""
for msg in reversed(result["messages"]):
    if isinstance(msg, AIMessage):
        text = msg.text.rstrip() if msg.text else ""
        if text:
            content = text
            break
```

**特殊处理**：倒序找最后一条**非空** AIMessage。这是因为 Anthropic Claude 偶尔会在最后一个工具调用成功后追加一条空的 `end_turn` AIMessage，如果取最后一条会得到空字符串。deepagents 用倒序 + 非空判断绕过了这个 quirk。

### 5.2 有结构化输出时的处理

```python
structured = result.get("structured_response")
if structured is not None:
    if hasattr(structured, "model_dump_json"):
        content = structured.model_dump_json()
    elif dataclasses.is_dataclass(structured):
        content = json.dumps(dataclasses.asdict(structured))
    else:
        content = json.dumps(structured)
```

如果 SubAgent 设置了 `response_format`，结果是 JSON 序列化的结构体，替代最后一条消息文本。

### 5.3 返回给主 Agent 的内容

```python
return Command(
    update={
        **state_update,  # 过滤掉 _EXCLUDED_STATE_KEYS 后的子 Agent 状态
        "messages": [ToolMessage(content, tool_call_id=runtime.tool_call_id)],
    }
)
```

主 Agent 看到的就是一条 ToolMessage，内容是子 Agent 的最终答案（或结构体 JSON）。

---

## 6. lc-agent 改造的对与不对：逐条分析

### 6.1 哪些可以直接参考

| 官方实现 | 适配 lc-agent 时的建议 |
|----------|----------------------|
| `DEFAULT_SUBAGENT_PROMPT` 注入子 Agent | ✅ 直接参考，但改写成中文或中英混合，更适合国产模型 |
| `TASK_SYSTEM_PROMPT` 注入主 Agent system | ✅ 直接参考，需翻译并精简，lc-agent 用的是弱模型 |
| `TaskToolSchema` Pydantic 参数级 description | ✅ lc-agent 已有类似实现，但可以强化"Include all necessary context"的措辞 |
| `append_to_system_message` 用 content block 而非字符串拼接 | ✅ lc-agent 已通过 `_SystemBlockMiddleware` 实现，机制一致 |
| 不向子 Agent 注入 TodoListMiddleware | ✅ 强烈建议：子 Agent 写 todo 毫无意义，还会干扰"最终答案"提取 |

### 6.2 哪些不宜照搬

| 官方实现 | 不宜照搬的原因 |
|----------|--------------|
| 全英文提示词 | lc-agent 主打国产中文模型，弱模型对中文指令理解更好 |
| `general-purpose` 这个英文命名 | lc-agent 的子 Agent 已有中文 `display_name`，保持现有约定 |
| 7 条 Usage notes 全部照搬 | 条目过多，弱模型注意力有限，建议保留前 3 条核心条目 |
| `<example_agent_descriptions>` 标签格式 | 对 Claude 有强提示效果，对国产弱模型效果未知，需验证后再决定 |
| 子 Agent 必须显式指定 `model` 和 `tools` | lc-agent 的子 Agent 继承 preset 配置，不需要显式指定 |

### 6.3 lc-agent 专属要考虑的问题

**问题 1：子 Agent 不应该有 `TodoListMiddleware`**
deepagents 的子 Agent 默认**不加** TodoListMiddleware。lc-agent 目前递归调用 `build_agent`，子 Agent 会完整继承所有中间件。Todo 对子 Agent 无意义，而且 `write_todos` 工具调用会出现在子 Agent 的消息历史里，当 lc-agent 提取"最后一条非工具调用消息"时可能出错。

**问题 2：子 Agent system_prompt 的构成**
deepagents 直接用 spec 里的 `system_prompt`（比如 `DEFAULT_SUBAGENT_PROMPT`），不会再拼 skills、memory 等提示词。lc-agent 目前会把 preset 的 system_prompt 追加 memory 提示词、skills 提示词等。对子 Agent 而言，memory 和 skills 的说明可能是不必要的干扰（子 Agent 通常没有 memory，也可能不需要 skills）。

**问题 3：`display_name` vs 英文 ASCII name**
deepagents 要求子 Agent `name` 是 ASCII（用于 LLM 填参数），但展示给用户时可以用其他名字。lc-agent 目前把中文 `display_name` 作为子 Agent 类型标识，弱模型在填 `subagent_type` 参数时可能拼错或用错。建议参考 deepagents，内部用英文 slug，对用户展示中文 display_name。

---

## 7. 改造建议（按 ROI 从高到低）

| 优先级 | 改造项 | 影响 | 难度 |
|--------|--------|------|------|
| P0 | 子 Agent 注入"你是被委派的工作者"提示词（参考 `DEFAULT_SUBAGENT_PROMPT` 改写） | 解决子 Agent 散答问题，ROI 极高 | 低 |
| P0 | 子 Agent **不加** `TodoListMiddleware`（build 时区分是否是子 Agent） | 避免 Todo 干扰答案提取，防止行为异常 | 低 |
| P1 | 主 Agent system 注入 task 工具使用指南（参考 `TASK_SYSTEM_PROMPT` 精简） | 弱模型更主动委派，`description` 写得更完整 | 中 |
| P1 | task 工具 description 强调"stateless"语义 + 要求 description 写完整背景 | 解决委派描述不完整的问题 | 低 |
| P2 | `TaskToolSchema` 参数级 description 强化 | 弱模型参数填写更准确 | 低 |
| P2 | `subagent_type` 统一用英文 slug，`display_name` 仅用于界面显示 | 弱模型填参数不出错 | 中 |
| P3 | 子 Agent system_prompt 不追加 memory/skills 提示词（除非 spec 显式要求） | 减少子 Agent 干扰，专注任务 | 中 |
