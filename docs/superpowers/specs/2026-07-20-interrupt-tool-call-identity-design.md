# 中断工具调用身份关联设计

**日期**: 2026-07-20
**状态**: 已确认，待实现规划

## 背景与目标

`ask_user` 调用 `interrupt()` 暂停后，用户提交回答会通过 `Command(resume=...)` 恢复图执行。LangGraph 的恢复语义会从中断所在节点的开头重新执行，因此工具流会再次产生 `on_tool_start`。当前框架把每次事件的 `run_id` 当作工具调用身份，恢复后的新 `run_id` 使前端创建第二张同名卡片；随后 `tool_result` 不带身份，只能按同名运行中卡片猜测回填目标。

目标：

1. 复用 LangGraph 原生身份关联中断工具的完整生命周期，不创建自定义 ID。
2. 同一个 `ask_user` 在暂停、恢复、完成后始终显示为一张工具调用卡片。
3. 工具结果按精确身份回填，移除依赖“同名且运行中”的模糊匹配。
4. 保持用户自然语言回答与 `ask_user` 工具返回语义不变。

## LangGraph 原生协议

### Interrupt.id

LangGraph 的 `Interrupt.id` 是待恢复中断的原生身份。`Command.resume` 支持传入 `{interrupt_id: resume_value}` 映射，因此前端应保存 interrupt 事件中的 `id`，恢复时用该映射精确指定回答属于哪个中断。

### 工具 task ID

LangGraph 工具节点的 checkpoint namespace 包含工具 task ID。现有 `_extract_tools_task_id(checkpoint_ns)` 已用于子 Agent 工具开始和结束的关联。主 Agent 普通工具也使用相同提取结果作为 SSE `tool_call_id`；仅当 namespace 不可用时才回退事件 `run_id`。

`run_id` 是单次 LangChain 事件执行的 tracing ID，不是跨中断恢复的工具调用身份，不能作为首选 UI 关联键。

## 设计方案

### 1. SSE 工具事件统一携带 tool_call_id

`tool_call` 事件字段：

```json
{
  "type": "tool_call",
  "name": "ask_user",
  "tool_call_id": "<LangGraph 工具 task ID>",
  "args": {"question": "..."}
}
```

`tool_result` 事件使用相同字段：

```json
{
  "type": "tool_result",
  "name": "ask_user",
  "tool_call_id": "<同一 LangGraph 工具 task ID>",
  "result": "用户回答: A..."
}
```

后端在 `convert_stream_event()` 和 `accumulate_display_state()` 中均从同一 checkpoint namespace 提取 task ID，保证实时事件与持久化的 `runId` 一致。

### 2. 前端按 tool_call_id 合并工具卡片

前端 `ToolCall.runId` 继续存放 SSE `tool_call_id`，避免扩大前端数据模型。

- 收到 `tool_call` 时，若当前 assistant 消息已有相同 `runId`，不新增工具记录、不新增 `<!--TOOL:n-->` marker。
- 收到 `tool_result` 时，只按 `msg.tool_call_id` 精确定位对应卡片并完成状态、结果、时长和长度。
- 无 ID 的异常旧事件仅记录警告且不使用同名回退匹配，避免将结果填入错误的并发工具卡片。

### 3. 精确恢复 ask_user

`interrupt` SSE 数据已包含原生 `Interrupt.id`。前端 `InterruptDialog` 及恢复调用链将当前 ask_user 中断 ID 与用户回答共同传到 `sendInterruptResume()`，发送：

```json
{
  "command": {
    "resume": {
      "<Interrupt.id>": "用户原始回答"
    }
  }
}
```

后端不转换该映射，直接传给 `Command(resume=resume_value)`。用户点击候选项仍提交选项文本；自由输入仍原样提交，不做正则解析。

## 数据流

```text
on_tool_start
  -> checkpoint namespace 的 task ID
  -> SSE tool_call.tool_call_id
  -> ToolCall.runId + 一个 TOOL marker

interrupt
  -> Interrupt.id
  -> 前端保存当前中断 ID
  -> Command(resume={Interrupt.id: 用户原始回答})

恢复后的 on_tool_start
  -> 同一 task ID
  -> 前端命中现有 ToolCall，不新增 marker

on_tool_end
  -> 同一 task ID
  -> SSE tool_result.tool_call_id
  -> 前端精确完成原 ToolCall
```

## 改动范围

- `lc_agent/server/stream_utils.py`：主 Agent 普通工具的 ID 提取、SSE `tool_result` 字段和持久化关联。
- `frontend/src/api/sse-client.ts`：透传恢复映射，不将 resume 值降级为字符串。
- `frontend/src/stores/chat.ts`：按 `tool_call_id` 去重及精确结果回填。
- `frontend/src/components/chat/InterruptDialog.vue`、`frontend/src/views/ChatView.vue`：保存并传递 ask_user 的原生 interrupt ID。
- 相关 TypeScript 事件类型：补充 `tool_call_id` 字段。

不修改：

- `ask_user` 工具的参数、问题、选项、自由输入、返回文本和选项对照表。
- 数据库 schema、SSE endpoint 路径、LangGraph 图定义。

## 验收场景

1. `ask_user` 首次暂停时仅显示一张运行中工具卡片。
2. 用户选择或自由输入并恢复后，仍为同一张工具卡片；不新增第二个工具 marker 或工具计数。
3. 同一张卡片接收结果后变为完成，显示工具返回内容与时长。
4. 多个并发 interrupt 时，回答通过各自 `Interrupt.id` 精确恢复，不串答。
5. 两个同名普通工具并发执行时，各自结果只更新对应 `tool_call_id` 的卡片。
6. 自由文本如“我选 A 和 B”原样传给模型，前端不进行解析。
