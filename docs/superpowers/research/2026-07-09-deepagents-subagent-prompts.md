# deepagents 子 Agent 提示词与 task 工具调研

> 调研时间：2026-07-09
> 目的：把官方 deepagents（`deepagents.middleware.subagents`）关于"子 Agent 调用"相关的所有提示词、工具 schema、字段级描述原原本本记录下来，方便后续对齐到 lc-agent 的 task 工具。
> 源码位置：`D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\deepagents\middleware\subagents.py`

---

## 1. 主 Agent 的 system 提示词（关于子 Agent 委派的部分）

deepagents 用 `SubAgentMiddleware.__init__` 把 `TASK_SYSTEM_PROMPT` 和"Available subagent types"列表拼到主 Agent 的 system 提示词**末尾**。代码片段：

```python
# deepagents/middleware/subagents.py:682-685
if system_prompt and subagent_specs:
    agents_desc = "\n".join(f"- {s['name']}: {s['description']}" for s in subagent_specs)
    self.system_prompt = system_prompt + "\n\nAvailable subagent types:\n\n" + agents_desc
```

### 1.1 `TASK_SYSTEM_PROMPT` 原文

`deepagents/middleware/subagents.py:390-420`：

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

### 1.2 实际拼到主 Agent system 末尾的样子

```text
[TASK_SYSTEM_PROMPT 上面这段]

Available subagent types:

- general-purpose: General-purpose agent for researching complex questions, searching for files and content, and executing multi-step tasks. When you are searching for a keyword or file and are not confident that you will find the right match in the first few tries use this agent to perform the search for you. This agent has access to all tools as the main agent.
- research-analyst: use this agent to conduct thorough research on complex topics
- content-reviewer: use this agent after you are done creating significant content or documents
- ...
```

格式规则（`_build_task_tool` 内部用 `subagent_description_str = "\n".join(f"- {s['name']}: {s['description']}" for s in subagents)` 拼）：

```text
- <name>: <description>
- <name>: <description>
...
```

---

## 2. `task` 工具的函数描述（tool description）原文

`deepagents/middleware/subagents.py:280-388` 的 `TASK_TOOL_DESCRIPTION` 模板，下面是**原样**。`{available_agents}` 是占位符，运行时被替换为第 1.2 节里那种 `- name: desc` 列表。

```text
Launch an ephemeral subagent to handle complex, multi-step independent tasks with isolated context windows.

Available agent types and the tools they have access to:
{available_agents}

When using the Task tool, you must specify a subagent_type parameter to select which agent type to use.

## Usage notes:
1. Launch multiple agents concurrently whenever possible, to maximize performance; to do that, use a single message with multiple tool uses
2. When the agent is done, it will return a single message back to you. The result returned by the agent is not visible to the user. To show the user the result, you should send a text message back to the user with a concise summary of the result.
3. Each agent invocation is stateless. You will not be able to send additional messages to the agent, nor will the agent be able to communicate with you outside of its final report. Therefore, your prompt should contain a highly detailed task description for the agent to perform autonomously and you should specify exactly what information the agent should return back to you in its final and only message to you.
4. The agent's outputs should generally be trusted
5. Clearly tell the agent whether you expect it to create content, perform analysis, or just do research (search, file reads, web fetches, etc.), since it is not aware of the user's intent
6. If the agent description mentions that it should be used proactively, then you should try your best to use it without the user having to ask for it first. Use your judgement.
7. When only the general-purpose agent is provided, you should use it for all tasks. It is great for isolating context and token usage, and completing specific, complex tasks, as it has all the same capabilities as the main agent.

### Example usage of the general-purpose agent:

<example_agent_descriptions>
"general-purpose": use this agent for general purpose tasks, it has access to all tools as the main agent.
</example_agent_descriptions>

<example>
User: "I want to conduct research on the accomplishments of Lebron James, Michael Jordan, and Kobe Bryant, and then compare them."
Assistant: *Uses the task tool in parallel to conduct isolated research on each of the three players*
Assistant: *Synthesizes the results of the three isolated research tasks and responds to the User*
<commentary>
Research is a complex, multi-step task in it of itself.
The research of each individual player is not dependent on the research of the other players.
The assistant uses the task tool to break down the complex objective into three isolated tasks.
Each research task only needs to worry about context and tokens about one player, then returns synthesized information about each player as the Tool Result.
This means each research task can dive deep and spend tokens and context deeply researching each player, but the final result is synthesized information, and saves us tokens in the long run when comparing the players to each other.
</commentary>
</example>

<example>
User: "Analyze a single large code repository for security vulnerabilities and generate a report."
Assistant: *Launches a single `task` subagent for the repository analysis*
Assistant: *Receives report and integrates results into final summary*
<commentary>
Subagent is used to isolate a large, context-heavy task, even though there is only one. This prevents the main thread from being overloaded with details.
If the user then asks followup questions, we have a concise report to reference instead of the entire history of analysis and tool calls, which is good and saves us time and money.
</commentary>
</example>

<example>
User: "Schedule two meetings for me and prepare agendas for each."
Assistant: *Calls the task tool in parallel to launch two `task` subagents (one per meeting) to prepare agendas*
Assistant: *Returns final schedules and agendas*
<commentary>
Tasks are simple individually, but subagents help silo agenda preparation.
Each subagent only needs to worry about the agenda for one meeting.
</commentary>
</example>

<example>
User: "I want to order a pizza from Dominos, order a burger from McDonald's, and order a salad from Subway."
Assistant: *Calls tools directly in parallel to order a pizza from Dominos, a burger from McDonald's, and a salad from Subway*
<commentary>
The assistant did not use the task tool because the objective is super simple and clear and only requires a few trivial tool calls.
It is better to just complete the task directly and NOT use the `task` tool.
</commentary>
</example>

### Example usage with custom agents:

<example_agent_descriptions>
"content-reviewer": use this agent after you are done creating significant content or documents
"greeting-responder": use this agent when to respond to user greetings with a friendly joke
"research-analyst": use this agent to conduct thorough research on complex topics
</example_agent_descriptions>

<example>
user: "Please write a function that checks if a number is prime"
assistant: Sure let me write a function that checks if a number is prime
assistant: First let me use the Write tool to write a function that checks if a number is prime
assistant: I'm going to use the Write tool to write a function that checks if a number is prime
assistant: I'm going to use the Write tool to write a function that checks if a number is prime
<code>
function isPrime(n) {{
  if (n <= 1) return false
  for (let i = 2; i * i <= n; i++) {{
    if (i % n == 0) return false
  }}
  return true
}}
</code>
<commentary>
Since significant content was created and the task was completed, now use the content-reviewer agent to review the work
</commentary>
assistant: Now let me use the content-reviewer agent to review the code
assistant: Uses the Task tool to launch with the content-reviewer agent
</example>

<example>
user: "Can you help me research the environmental impact of different renewable energy sources and create a comprehensive report?"
<commentary>
This is a complex research task that would benefit from using the research-analyst agent to conduct thorough analysis
</commentary>
assistant: I'll help you research the environmental impact of renewable energy sources. Let me use the research-analyst agent to conduct comprehensive research on this topic.
assistant: Uses the Task tool to launch with the research-analyst agent, providing detailed instructions about what research to conduct and what format the report should take
</example>

<example>
user: "Hello"
<commentary>
Since the user is greeting, use the greeting-responder agent to respond with a friendly joke
</commentary>
assistant: "I'm going to use the Task tool to launch with the greeting-responder agent"
</example>
```

### 2.1 运行时实际渲染出来的样子（示例）

假设有 2 个子 Agent，运行时实际拼出的 `description` 字段长这样：

```text
Launch an ephemeral subagent to handle complex, multi-step independent tasks with isolated context windows.

Available agent types and the tools they have access to:
- general-purpose: General-purpose agent for researching complex questions, searching for files and content, and executing multi-step tasks. When you are searching for a keyword or file and are not confident that you will find the right match in the first few tries use this agent to perform the search for you. This agent has access to all tools as the main agent.
- research-analyst: use this agent to conduct thorough research on complex topics

When using the Task tool, you must specify a subagent_type parameter to select which agent type to use.

## Usage notes:
[... 上面那 7 条 Usage notes ...]

### Example usage of the general-purpose agent:
[... 4 个 <example> ...]

### Example usage with custom agents:
[... 3 个 <example> ...]
```

---

## 3. `task` 工具的每个函数入参和描述

deepagents 用 Pydantic `BaseModel` 显式定义入参 schema（这是 lc-agent 当前缺的）。源码 `deepagents/middleware/subagents.py:267-277`：

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

### 3.1 入参一览

| 参数 | 类型 | 是否必填 | 字段级 description 原文 |
|------|------|---------|------------------------|
| `description` | `str` | 是 | `A detailed description of the task for the subagent to perform autonomously. Include all necessary context and specify the expected output format.` |
| `subagent_type` | `str` | 是 | `The type of subagent to use. Must be one of the available agent types listed in the tool description.` |

### 3.2 实际渲染的 JSON Schema（LLM 看到的样子）

```json
{
  "type": "function",
  "function": {
    "name": "task",
    "description": "Launch an ephemeral subagent ...（第 2 节那一坨）",
    "parameters": {
      "type": "object",
      "properties": {
        "description": {
          "type": "string",
          "description": "A detailed description of the task for the subagent to perform autonomously. Include all necessary context and specify the expected output format."
        },
        "subagent_type": {
          "type": "string",
          "description": "The type of subagent to use. Must be one of the available agent types listed in the tool description."
        }
      },
      "required": ["description", "subagent_type"]
    }
  }
}
```

### 3.3 函数签名（同步 / 异步两个版本）

`deepagents/middleware/subagents.py:542-588`：

```python
def task(
    description: str,
    subagent_type: str,
    runtime: ToolRuntime,
) -> str | Command:
    ...

async def atask(
    description: str,
    subagent_type: str,
    runtime: ToolRuntime,
) -> str | Command:
    ...
```

通过 `StructuredTool.from_function(name="task", func=task, coroutine=atask, description=description, infer_schema=False, args_schema=TaskToolSchema)` 注册（`subagents.py:590-597`）。**注意 `infer_schema=False` + `args_schema=TaskToolSchema` 是关键**，显式 schema 优先于从函数签名推断。

### 3.4 内部错误返回文案（也属于"工具语义"的一部分）

当 `subagent_type` 不在白名单里时（`subagents.py:547-549, 571-573`）：

```text
We cannot invoke subagent {subagent_type} because it does not exist, the only allowed types are `name1`, `name2`, ...
```

这个文案会作为 `ToolMessage` 反馈给主 Agent，让 LLM 自我纠正。

---

## 4. 委派子 Agent 时，子 Agent 自动添加的系统提示词

deepagents 的子 Agent **不是裸跑**。在 `_get_subagents()` 里（`subagents.py:691-745`），每个 `SubAgent` 在 build 自己的 graph 时传入的 `system_prompt` 来自 `spec["system_prompt"]`，而**默认 `system_prompt` 是 `DEFAULT_SUBAGENT_PROMPT`**（`subagents.py:425-429`）：

```python
DEFAULT_SUBAGENT_PROMPT = """In order to complete the objective that the user asks of you, you have access to a number of standard tools.

The calling agent only sees your final assistant message, not your intermediate work, tool results, or status tracking. Ensure your final
response contains the complete answer."""
```

### 4.1 子 Agent 看到的 system 提示词构成

```text
[用户写在 SubAgent 里的 system_prompt]


[如果用户没写，就用上面 DEFAULT_SUBAGENT_PROMPT]
```

注意：**子 Agent 看到的只有 `spec["system_prompt"]` 这一个 system message**。deepagents 不会像主 Agent 那样再拼"Availble Skills / subagent 列表"等附加段，因为子 Agent 的任务由主 Agent 通过 `description` 完整告知，没必要再注入任务上下文。

### 4.2 子 Agent 拿到的 user 消息

`deepagents/middleware/subagents.py:534-540` 的 `_validate_and_prepare_state`：

```python
def _validate_and_prepare_state(subagent_type: str, description: str, runtime: ToolRuntime) -> tuple[Runnable, dict]:
    subagent = subagent_graphs[subagent_type]
    subagent_state = {k: v for k, v in runtime.state.items() if k not in _EXCLUDED_STATE_KEYS}
    subagent_state["messages"] = [HumanMessage(content=description)]
    return subagent, subagent_state
```

也就是说，子 Agent 启动时只看到一条 HumanMessage：

```text
HumanMessage(content=<主 Agent 传给 task 工具的 description 参数>)
```

主 Agent 的对话历史、todo、memory 都**不传过去**（被 `_EXCLUDED_STATE_KEYS` 过滤掉）。子 Agent 是一个**完全隔离**的 context window。

### 4.3 子 Agent 的"return 协议"

子 Agent 完成后，deepagents 用 `_return_command_with_state_update`（`subagents.py:494-532`）把结果回传给主 Agent：

1. 如果子 Agent 设了 `response_format`，把 `structured_response` JSON 序列化作为 `ToolMessage` content
2. 否则**回溯 messages 找最后一条非空 AIMessage**（绕过 Anthropic 偶尔追加的 `end_turn` 空消息）作为 `ToolMessage` content
3. 用 `Command(update={"messages": [ToolMessage(content, tool_call_id=...)], ...})` 回写主 Agent 状态

返回给主 Agent 的内容大致是：

```text
ToolMessage(
    content="<子 Agent 最后一条 AI 消息文本>",
    tool_call_id=<主 Agent 调 task 时拿到的 tool_call_id>
)
```

主 Agent 看到的就是"task 工具返回了子 Agent 的最终答案"。

### 4.4 默认 `general-purpose` 子 Agent 的 description

`deepagents/middleware/subagents.py:423`：

```python
DEFAULT_GENERAL_PURPOSE_DESCRIPTION = "General-purpose agent for researching complex questions, searching for files and content, and executing multi-step tasks. When you are searching for a keyword or file and are not confident that you will find the right match in the first few tries use this agent to perform the search for you. This agent has access to all tools as the main agent."
```

注意这段 description 是**写给主 Agent 看的**（让主 Agent 知道"什么时候该调 general-purpose"），不是给子 Agent 看的 system_prompt。

---

## 5. 对照 lc-agent 现状的差距（待办）

| 维度 | deepagents | lc-agent 现状 | 差距 |
|------|-----------|--------------|------|
| 主 Agent system 是否列子 Agent | ✅ system 末尾 + 工具 description 双列 | ❌ 只在 `task` 工具 description 里列 | 主 Agent 不知道有子 Agent |
| 主 Agent system 是否有"何时用 / 何时不用" task 工具 | ✅ `TASK_SYSTEM_PROMPT` | ❌ 没有 | 国产弱模型不主动调 |
| task 工具 description 长度 + example | ✅ 100+ 行 + 4-5 个 `<example>` | 短，无 example | 弱模型读不懂 |
| task 工具**参数级** description | ✅ `TaskToolSchema` Pydantic | ❌ 无字段级 description | 弱模型猜参数 |
| task 工具 description 是否用 `<example_agent_descriptions>` | ✅ | ❌ | 缺 Claude 强信号 |
| 子 Agent 有没有"我被委派的"提示词 | ✅ `DEFAULT_SUBAGENT_PROMPT` | ❌ 裸跑 | 子 Agent 啰嗦 |
| 子 Agent 名字规范 | 英文 ASCII | 中文 `display_name` | 中文名弱模型可能乱填 |

---

## 6. 后续改造建议（按 ROI 排序）

1. **加 `TaskToolSchema` 字段级 description**（10 行，巨大收益）
2. **把 `TASK_SYSTEM_PROMPT` 拼到主 Agent system 末尾**（5 行）
3. **子 Agent 默认加 `TASK_DELEGATION_PROMPT`**（5 行）
4. **task 工具 description 加 1-2 个 `<example>` 块**（30 行）
5. **参数 description 加中英双语**（可选，国产模型友好）
