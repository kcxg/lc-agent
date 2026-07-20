# 中断工具调用身份关联 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使用 LangGraph 原生工具 task ID 和 Interrupt.id，使 `ask_user` 恢复后维持同一张工具调用卡片并精确回填结果。

**Architecture:** 后端从 `langgraph_checkpoint_ns` 提取现有的 `tools:{task_uuid}`，将其作为 SSE `tool_call_id` 和持久化 `runId`。前端以该 ID 去重与回填；ask_user 恢复时将 SSE interrupt 数据中的原生 ID 构造成 `Command(resume={id: answer})`，不改动后端的 LangGraph `Command` 调用及回答内容。

**Tech Stack:** Python 3.12、LangGraph、FastAPI SSE、Vue 3、TypeScript、pytest、Vite

## Global Constraints

- 必须复用 LangGraph `Interrupt.id` 与 checkpoint namespace 的工具 task ID；不得生成自定义调用 ID。
- 不修改 `ask_user` 的参数、选项、自由输入、返回文本或选项对照表。
- 不用正则解析用户自由文本；点击选项仍传选项文本，自由输入仍原样传递。
- 不修改数据库 schema、SSE endpoint 路径或 LangGraph 图定义。
- `tool_result` 必须依据精确 `tool_call_id` 回填，不得保留同名运行中工具的模糊匹配。
- 所有 Python 命令使用 `D:\ProgramData\Miniconda3\envs\py312\python.exe`。
- 不新增依赖，不添加代码注释。

---

### Task 1: 后端透传 LangGraph 工具 task ID

**Files:**
- Modify: `lc_agent/server/stream_utils.py:139-236,285-386`
- Modify: `tests/test_ws_events.py:40-70,111-127`

**Interfaces:**
- Consumes: LangGraph 事件 `metadata.langgraph_checkpoint_ns`，格式为 `tools:{task_uuid}` 或包含该片段的多层 namespace。
- Produces: `tool_call` 和 `tool_result` SSE payload 都含 `tool_call_id: str`；持久化工具项 `runId` 使用同一值。

- [ ] **Step 1: 写入普通工具 task ID 透传的失败测试**

在 `tests/test_ws_events.py` 增加以下测试：

```python
def test_convert_stream_event_tool_call_uses_langgraph_task_id():
    event = {
        "event": "on_tool_start",
        "name": "ask_user",
        "run_id": "transient-run-id",
        "metadata": {"langgraph_checkpoint_ns": "tools:stable-task-id"},
        "data": {"input": {"question": "选择颜色"}},
    }

    results = convert_stream_event(event)

    assert results == [(
        "tool_call",
        {
            "name": "ask_user",
            "tool_call_id": "stable-task-id",
            "args": {"question": "选择颜色"},
        },
    )]


def test_convert_stream_event_tool_result_uses_langgraph_task_id():
    event = {
        "event": "on_tool_end",
        "name": "ask_user",
        "run_id": "different-transient-run-id",
        "metadata": {"langgraph_checkpoint_ns": "tools:stable-task-id"},
        "data": {"output": "用户回答: 红色"},
    }

    results = convert_stream_event(event)

    assert results == [(
        "tool_result",
        {
            "name": "ask_user",
            "tool_call_id": "stable-task-id",
            "result": "用户回答: 红色",
        },
    )]
```

在现有 `test_accumulate_display_state_tool` 的事件中增加：

```python
"metadata": {"langgraph_checkpoint_ns": "tools:stable-task-id"},
```

并在断言中增加：

```python
assert tools[0]["runId"] == "stable-task-id"
```

- [ ] **Step 2: 运行测试并确认当前实现失败**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_ws_events.py -v
```

Expected: 新增的断言失败，当前 `tool_call` 使用 `run_id` 且 `tool_result` 不含 `tool_call_id`。

- [ ] **Step 3: 在实时 SSE 转换中使用 task ID**

在 `convert_stream_event()` 的主 Agent 普通工具分支中，提取：

```python
tool_call_id = _extract_tools_task_id(checkpoint_ns) or event.get("run_id", "")
```

将 `on_tool_start` payload 替换为：

```python
results.append(("tool_call", {
    "name": tool_name,
    "tool_call_id": tool_call_id,
    "args": tool_input,
}))
```

将 `on_tool_end` 的主 Agent payload 替换为：

```python
results.append(("tool_result", {
    "name": tool_name,
    "tool_call_id": _extract_tools_task_id(checkpoint_ns) or event.get("run_id", ""),
    "result": result_str,
}))
```

- [ ] **Step 4: 在持久化显示状态中使用相同 task ID 并精确完成**

在 `accumulate_display_state()` 的主 Agent `on_tool_start` 分支中，先计算：

```python
tool_call_id = _extract_tools_task_id(checkpoint_ns) or event.get("run_id", "")
```

新增工具项时使用：

```python
"runId": tool_call_id,
```

并在追加工具项前加入重复 task ID 防护：

```python
if any(tc.get("runId") == tool_call_id for tc in tool_calls):
    return in_thinking
```

在主 Agent `on_tool_end` 分支中，将按 `run_id` 再按名称回退的查找替换为：

```python
tool_call_id = _extract_tools_task_id(checkpoint_ns) or event.get("run_id", "")
tool_call = next(
    (tc for tc in tool_calls if tc.get("runId") == tool_call_id),
    None,
)
```

保持已有的状态、结果、时长与结果长度更新逻辑，且 `tool_call` 为 `None` 时不更新任何条目。

- [ ] **Step 5: 运行后端回归测试并确认通过**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_ws_events.py tests/test_stream_utils_subagents.py -v
```

Expected: 所有测试通过；主 Agent 工具事件使用 task ID，子 Agent 现有行为不变。

### Task 2: 前端按精确 tool_call_id 合并与回填

**Files:**
- Modify: `frontend/src/stores/chat.ts:677-736`
- Modify: `frontend/src/api/sse-client.ts:8-47`

**Interfaces:**
- Consumes: `SseMessage.tool_call_id?: string`。
- Produces: `ToolCall.runId` 保存 task ID；相同 ID 的第二次 `tool_call` 不增加工具记录或 marker；`tool_result` 仅完成 ID 匹配的工具记录。

- [ ] **Step 1: 扩展 SSE 类型以记录缺失 ID 的诊断信息**

`SseMessage` 已声明 `tool_call_id?: string`，保持该字段；不新增 `run_id` 的新使用处。

- [ ] **Step 2: 修改 tool_call 的去重与记录字段**

在 `chat.ts` 的 `client.on('tool_call')` 处理器中，将：

```ts
const existingByRunId = last.toolCalls.find(t => t.runId === msg.run_id)
```

替换为：

```ts
const toolCallId = msg.tool_call_id
if (!toolCallId) {
  console.warn('[Chat] Ignored tool_call without tool_call_id', msg)
  return
}
const existingByToolCallId = last.toolCalls.find(t => t.runId === toolCallId)
```

将去重判断改为：

```ts
if (existingByToolCallId) return
```

创建 `ToolCall` 时使用：

```ts
runId: toolCallId,
```

- [ ] **Step 3: 修改 tool_result 的精确回填**

将 `client.on('tool_result')` 中的名称匹配：

```ts
const tc = last.toolCalls.find(t => t.name === msg.name && t.status === 'running')
```

替换为：

```ts
const toolCallId = msg.tool_call_id
if (!toolCallId) {
  console.warn('[Chat] Ignored tool_result without tool_call_id', msg)
  return
}
const tc = last.toolCalls.find(t => t.runId === toolCallId)
```

保持后续 `result`、`status`、`duration` 与 `resultLength` 赋值不变。

- [ ] **Step 4: 进行 TypeScript 类型检查和生产构建**

Run:

```powershell
npm run build
```

Expected: `vue-tsc --noEmit` 与 `vite build` 以退出码 0 完成。

### Task 3: 使用 Interrupt.id 精确恢复 ask_user

**Files:**
- Modify: `frontend/src/components/chat/InterruptDialog.vue:85-183`
- Modify: `frontend/src/views/ChatView.vue:882-884`
- Modify: `frontend/src/stores/chat.ts:1024-1040`
- Modify: `frontend/src/api/sse-client.ts:116-134`

**Interfaces:**
- Consumes: `InterruptInfo.data[0]` 中的 `{ value: AskUserPayload, id: string }`。
- Produces: `sendInterruptResume({ [interruptId]: answer }, presetId, model, llmParams)`，并由后端原样用于 `Command(resume=...)`。

- [ ] **Step 1: 让 InterruptDialog 从原始 interrupt 数据取得 ID**

在 `InterruptDialog.vue` 新增类型：

```ts
interface AskUserInterrupt {
  id?: string
  value: AskUserPayload
}
```

新增计算属性：

```ts
const askUserInterrupt = computed<AskUserInterrupt | null>(() => {
  const item = props.interrupt?.data?.[0]
  if (item?.value && typeof item.value === 'object' && item.value.type === 'ask_user') {
    return item as AskUserInterrupt
  }
  return null
})
```

让 `askPayload` 返回 `askUserInterrupt.value?.value ?? null`。

- [ ] **Step 2: 将回答与原生 interrupt ID 一起发出**

在 `submitAskUser()` 中，将：

```ts
emit('resume', answer)
```

替换为：

```ts
const interruptId = askUserInterrupt.value?.id
if (!interruptId) {
  console.warn('[InterruptDialog] Missing LangGraph interrupt id')
  return
}
emit('resume', { [interruptId]: answer })
```

保持 `answer` 的构建过程不变，继续使用用户点击的选项文本或原样自由输入。

- [ ] **Step 3: 保持页面、store 和 SSE 客户端对恢复映射的透传**

`handleInterruptResume`、`resumeInterrupt` 和 `sendInterruptResume` 的参数已是 `any`，无需转换或序列化 answer；确认下列调用均原样传递对象：

```ts
chatStore.resumeInterrupt(value, agentsStore.currentAgentId, toolsStore.currentModel, toolsStore.llmParams)
state.client.sendInterruptResume(resumeValue, presetId, model, llmParams)
command: { resume: resumeValue }
```

不得把对象包装为 `{ answer: ... }` 或提取为字符串。

- [ ] **Step 4: 执行完整构建与目标后端测试**

Run:

```powershell
npm run build
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_ws_events.py tests/test_stream_utils_subagents.py -v
```

Expected: 两条命令均以退出码 0 完成。

### Task 4: 浏览器端到端验收

**Files:**
- Modify: none

**Interfaces:**
- Consumes: 已构建的 `lc_agent/web/dist` 和运行中的 bfzs 服务。
- Produces: 对真实 `ask_user` 中断恢复与普通工具结果关联的验证证据。

- [ ] **Step 1: 重建前端并重启后端服务**

本任务同时修改了前端和后端，运行：

```powershell
powershell -ExecutionPolicy Bypass -File "D:\codes\lc-agent\.agents\skills\restart-bfzs\scripts\restart.ps1"
```

Expected: 输出 `Uvicorn running on http://127.0.0.1:8001`，服务可访问。

- [ ] **Step 2: 验证 ask_user 只有一张工具卡片**

在新会话发送：

```text
请使用 ask_user 询问我喜欢什么颜色，提供红色、蓝色、绿色三个选项，允许多选和自由输入。
```

检查：首次暂停只有一张 `ask_user` 卡片，状态为执行中；选择任意选项或输入自然语言并提交后，该卡片变为完成，工具计数不增加第二次，也没有第二个 `<!--TOOL:n-->` 对应卡片。

- [ ] **Step 3: 验证自由输入和同名工具的精确关联**

在 ask_user 自由输入框输入：

```text
我选 A 和 B，但蓝色优先
```

检查：Agent 能收到原样回答并继续；工具卡显示一次调用和对应结果。再触发两个同名普通工具调用，确认每个结果只回填到自己的卡片。

- [ ] **Step 4: 检查浏览器控制台与工作区差异**

Run:

```powershell
git diff --check
git diff -- lc_agent/server/stream_utils.py frontend/src/stores/chat.ts frontend/src/components/chat/InterruptDialog.vue frontend/src/views/ChatView.vue frontend/src/api/sse-client.ts
git status --short
```

Expected: `git diff --check` 无输出；无缺失 `tool_call_id` 的前端警告；不触碰用户已有的 `pub_pypi_lc_agent.py` 修改。

- [ ] **Step 5: 提交完成的功能改动**

仅在用户明确要求提交时执行：

```powershell
git add lc_agent/server/stream_utils.py frontend/src/stores/chat.ts frontend/src/components/chat/InterruptDialog.vue frontend/src/views/ChatView.vue frontend/src/api/sse-client.ts tests/test_ws_events.py docs/superpowers/specs/2026-07-20-interrupt-tool-call-identity-design.md docs/superpowers/plans/2026-07-20-interrupt-tool-call-identity.md
git commit -m "fix: preserve tool identity across interrupts"
```

Expected: 创建仅包含中断工具身份关联改动与对应文档的提交。
