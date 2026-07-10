# SubAgent3 SSE Stabilization Design

## 背景

`subagent2b` 已经把子 agent 前后端流式渲染调通，但当前实现仍处在原型累积阶段：后端 SSE 主流程承担了事件转换、子会话落库、子 agent 状态累计、HTTP trace 聚合、恢复流处理等多种职责；前端 store 也在 SSE 回调里直接维护较复杂的子 agent 状态。

本轮在 `subagent3` 分支进行，目标不是重写实时通信架构，也不是引入 Redis、MQTT、WebSocket 或新的消息中间件，而是在保留现有 SSE 与 UI 行为的前提下，把子 agent 事件语义和状态处理整理到更稳定、更可测试的边界里。

用户明确提醒：旧 pytest 可能不准，因为项目一直在被 AI 修改。因此旧测试只能作为线索，不能作为唯一事实来源。若旧测试与本 spec 确认的事件语义冲突，应先更新测试语义，再改实现。

## 目标

1. 保留现有 SSE 通道和当前已调通的子 agent 前端体验。
2. 明确 LangGraph event 到 lc-agent UIEvent 的子 agent 语义。
3. 降低 `lc_agent/server/sse.py` 中 `_send_stream` 与 `_resume_stream` 的重复和分歧。
4. 把子 agent 运行状态集中到一个后端 tracker 中处理，使发送新消息和 resume 走同一套状态逻辑。
5. 小幅整理前端 SSE 类型和 Pinia store，使 `subagent_*` 事件有明确类型和 reducer 风格处理函数。
6. 以事件转换测试、tracker 测试、前端 reducer 测试为主，避免依赖 Playwright 截图时机验证流式 UI。

## 非目标

1. 不把 SSE 改回 WebSocket。
2. 不引入 MQTT、Redis Pub/Sub、Redis Streams 或 EventBus 中间件。
3. 不重写 `SubAgentCard.vue`、`ChatBubble.vue`、`ChatView.vue` 的 UI 结构。
4. 不做数据库兼容迁移设计；项目仍处于早期阶段，无历史包袱。
5. 不以旧测试为绝对标准；语义冲突时以本 spec 和实际 LangGraph 事件含义为准。
6. 不在本轮处理大规模多进程、多服务或跨机器 agent 事件分发问题。

## 事件语义

### Checkpoint namespace 规则

LangGraph 的 `metadata["langgraph_checkpoint_ns"]` 用于辅助判断事件来源，但不能只凭非空 namespace 就判断为子 agent 内部事件。

采用以下规则：

1. 空 namespace：主 agent 顶层事件。
2. 单段 `tools:{id}`：主 agent ToolNode 正在执行某个工具；这不自动代表已经进入子 agent 内部。
3. 多段 `tools:{id}|...`：处于某个工具调用内部的嵌套图执行；当第一段工具调用对应子 agent tool 时，视为子 agent 内部事件。
4. 主 agent 调用子 agent 的边界事件由 `tool_name in subagent_tool_names` 判断。
5. 普通工具即使有单段 `tools:{id}`，也只应产生普通 `tool_call` / `tool_result` 语义。

这意味着旧测试中如果断言 `_extract_subagent_tool_call_id("tools:abc123") == "abc123"`，该断言应视为过期，应改为单段返回 `None`，多段返回第一段 `tools:` 对应 id。

### UIEvent 协议

`stream_utils.convert_stream_event()` 继续负责把 LangGraph 原始事件转换为 UIEvent。它应输出以下事件：

- 主 agent token：`token`
- 主 agent thinking：`thinking`
- 普通工具开始：`tool_call`
- 普通工具结束：`tool_result`
- 主 agent 调用子 agent tool：`tool_call`，并带 `is_subagent: true`
- 子 agent 开始：`subagent_start`
- 子 agent 内部 token：`subagent_token`
- 子 agent 内部 thinking：`subagent_thinking`
- 子 agent 内部工具开始：`subagent_tool_call`
- 子 agent 内部工具结束：`subagent_tool_result`
- 子 agent tool 结束：`subagent_done`

`subagent_done` 替代子 agent tool 的普通 `tool_result` 展示语义。是否仍需要内部用于落库的原始结果，由后端 tracker 管理，不交给前端猜测。

## 后端设计

### SubAgentRunTracker

新增或抽取一个后端组件，暂定名为 `SubAgentRunTracker`。它接收已经转换后的 UIEvent，而不是直接接收 LangGraph raw event。

它按 `tool_call_id` 维护每次子 agent 运行的状态：

- `tool_call_id`
- `sub_session_id`
- `name`
- `query`
- `tokens`
- `thinking`
- `inner_tool_calls`
- `http_traces`
- `start_time`
- `status`

它处理以下事件：

1. `subagent_start`
   - 创建或确认子会话 id。
   - 初始化运行状态。
   - 准备子会话消息写入上下文。
   - 返回补全后的 SSE payload。
2. `subagent_token`
   - 累计子 agent answer token。
   - 返回原 payload 或补充 token 统计。
3. `subagent_thinking`
   - 累计子 agent thinking 内容。
4. `subagent_tool_call`
   - 记录内部工具调用。
   - 更新内部工具计数。
5. `subagent_tool_result`
   - 更新内部工具调用结果。
6. `subagent_done`
   - 标记完成或错误。
   - 生成 result preview。
   - flush 子会话消息。
   - 返回包含最终统计、duration、HTTP traces 的 payload。

tracker 的职责边界是子 agent 运行状态和子会话副作用。它不负责 LangGraph raw event 解析，不负责 SSE 字符串格式化，也不负责前端 UI 展示。

### `_send_stream` 与 `_resume_stream`

`_send_stream` 和 `_resume_stream` 应共用同一套 UIEvent 后处理路径：

1. 调用 engine 产生 raw stream event。
2. 使用 `convert_stream_event()` 转成 UIEvent。
3. 把每个 UIEvent 交给 `SubAgentRunTracker` enrich / persist。
4. 使用 `format_sse_event()` 输出给前端。
5. 在结束、错误或取消时，让 tracker 有机会 finalize 未完成的子 agent 状态。

这样可以避免新消息场景和 resume 场景下子 agent 子会话落库、done 状态、result preview、HTTP traces 处理不一致。

### 错误与取消

如果主流中断、取消或异常发生时仍有运行中的子 agent，tracker 应把这些子 agent 标记为 error 或 cancelled，并尽量 flush 已经收到的 token/thinking/tool 信息。前端应能收到最终状态，避免卡在永久 running。

## 前端设计

### SSE 类型

扩展 `frontend/src/api/sse-client.ts` 中的消息类型，使 `subagent_*` 事件有明确字段，而不是主要依赖 `(msg as any)`。

应覆盖的字段包括：

- `tool_call_id`
- `sub_session_id`
- `name`
- `query`
- `content`
- `status`
- `result_preview`
- `duration`
- `http_traces`
- `tool_count`
- `token_count`

类型整理只服务于本轮子 agent 事件稳定，不扩大到全量协议重写。

### Store reducer helpers

在 `frontend/src/stores/chat.ts` 中抽出 reducer 风格 helper，保持现有 UI 行为不变：

- `applySubAgentStart`
- `applySubAgentToken`
- `applySubAgentThinking`
- `applySubAgentToolCall`
- `applySubAgentToolResult`
- `applySubAgentDone`

这些 helper 接收当前 assistant message 和事件 payload，返回或原地更新子 agent 状态。SSE 回调只负责取最后一条 assistant message、调用 helper、必要时触发 Vue re-render。

本轮不重写 `SubAgentCard.vue`，除非类型字段调整需要极小适配。

## 测试策略

### 后端测试

优先新增或修正以下测试：

1. `stream_utils` 事件语义测试
   - 空 namespace 是主 agent。
   - 单段 `tools:{id}` 不自动是子 agent 内部。
   - 多段 `tools:{id}|...` 可识别子 agent 内部事件。
   - `tool_name in subagent_tool_names` 产生子 agent 边界事件。
2. `SubAgentRunTracker` 单元测试
   - start → token → done。
   - start → thinking → tool_call → tool_result → done。
   - error / cancel finalize。
   - `_send_stream` 和 `_resume_stream` 使用同一 tracker 路径时输出一致的关键 payload。
3. 保留有价值的旧测试，但更新与本 spec 冲突的断言。

### 前端测试

优先测试 reducer helpers，而不是截图：

1. `applySubAgentStart` 能创建 entry 并同步 tool call 标记。
2. `applySubAgentToken` 能累计 tokens/tokenCount。
3. `applySubAgentThinking` 能累计 thinking/thinkCount。
4. `applySubAgentToolCall` / `applySubAgentToolResult` 能维护内部工具列表。
5. `applySubAgentDone` 能将状态置为 done/error，并保留完整 tokens、preview、duration、HTTP traces。

如果现有前端测试基础不足，本轮至少保证 `npm run build` 或项目已有 typecheck/build 命令通过。

## 验证命令

后端使用项目指定 Python 解释器：

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_stream_utils_subagents.py tests/test_engine_subagents.py -q
```

根据实现新增 tracker 测试后，应追加对应测试文件。若修改涉及更广范围，再运行：

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/ -q
```

前端在 `frontend` 目录运行项目已有构建或检查命令，优先使用 `package.json` 中已有脚本，例如：

```powershell
npm run build
```

## 风险控制

1. 所有代码改动只在 `subagent3` 分支进行，保护 `subagent2b`。
2. 先更新/补充测试，再改实现。
3. 每次只做小步整理，不做大规模协议或 UI 重写。
4. 旧 pytest 失败不直接等于当前代码错；先判断它是否符合本 spec 的语义。
5. 对已经调通的 UI 行为保持兼容，重点整理边界和状态归属。

## Spec 自审

- Placeholder scan：无 TBD/TODO 占位。
- Internal consistency：事件语义、后端 tracker、前端 reducer、测试策略均以保留 SSE 和稳定子 agent 状态为中心。
- Scope check：范围限定在 `subagent3` 的 SSE 子 agent 稳定整理，不包含通信架构迁移。
- Ambiguity check：明确了单段 `tools:{id}` 不是子 agent 内部事件，旧测试冲突时更新测试。
