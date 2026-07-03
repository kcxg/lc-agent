# SSE Migration Design Spec

## Goal

将 lc-agent 前后端通信从 WebSocket 迁移到 SSE + REST，删除 WebSocket 代码，对齐 LangGraph runs 命名规范。

## Decisions Made

| 决策 | 选择 |
|------|------|
| 迁移目标 | 对齐 LangChain SSE 主流方式 |
| WebSocket 代码 | 完全删除 |
| Thread 管理 | 保持现有 sessions API |
| 事件格式 | 保持现有类型（token, thinking, tool_call, tool_result, interrupt, done, error, llm_usage, cancelled） |
| SSE 对齐层次 | 简单 SSE 流（非完整 Agent Server Protocol v2） |
| 前端消费方式 | fetch() + ReadableStream reader |
| API 命名 | 对齐 LangGraph `/threads/{id}/runs/stream` 模式 |

---

## API Design

### Endpoints

| 端点 | 方法 | 请求体 | 响应 | 用途 |
|------|------|--------|------|------|
| `/api/threads/{thread_id}/runs/stream` | POST | `{input: string, preset_id?, model?}` | SSE stream | 发消息+流式回复 |
| `/api/threads/{thread_id}/runs/stream` | POST | `{command: {resume: value}, preset_id?, model?}` | SSE stream | 中断恢复+流式 |
| `/api/threads/{thread_id}/runs/cancel` | POST | `{}` | JSON `{ok: true}` | 取消当前 run |
| `/api/threads/{thread_id}/state` | GET | - | JSON `{has_interrupts, ...}` | 获取线程状态 |

### SSE Event Format

每个事件格式：
```
event: <type>
data: {"type": "<type>", ...payload}

```

事件类型（保持与现有 WebSocket 消息一致）：

| 事件 | 数据 | 含义 |
|------|------|------|
| `token` | `{content: string}` | 流式文本 token |
| `thinking` | `{content: string}` | 推理/思考内容 |
| `tool_call` | `{name, run_id, args}` | 工具开始调用 |
| `tool_result` | `{name, result}` | 工具执行结果 |
| `llm_usage` | `{input_tokens, output_tokens, ...}` | 单轮 token 用量 |
| `interrupt` | `{message, data: [{value, id}]}` | 需要用户审批 |
| `done` | `{usage: [...], http_traces: [...]}` | 流结束 |
| `cancelled` | `{}` | 用户取消 |
| `error` | `{title, detail, suggestions, error_code}` | 错误 |
| `heartbeat` | (SSE comment `: heartbeat`) | 保活信号 |

### Request Body Discrimination

同一端点 `/runs/stream` 通过 body 区分操作：

```json
// 发送新消息
{"input": "你好", "preset_id": "__chat__", "model": ""}

// 恢复中断
{"command": {"resume": {"approved": true}}, "preset_id": "__chat__", "model": ""}

// 恢复中断（自定义 resume value，如 ask_user 回复）
{"command": {"resume": {"answer": "用户输入的回答"}}, "preset_id": "__chat__", "model": ""}
```

---

## Architecture

### Backend Module Split

从 `websocket.py`（~840 行）拆分为 3 个模块：

```
lc_agent/server/
├── sse.py              # SSE 端点：stream, cancel, state
│                       # 职责：HTTP 处理、流生命周期、cancel flag
│
├── stream_utils.py     # 流事件处理（从 websocket.py 提取）
│                       # 职责：_send_event → _format_sse_event
│                       #       _accumulate_usage
│                       #       _accumulate_assistant_display_state
│
├── persistence.py      # DB 持久化（从 websocket.py 提取）
│                       # 职责：save_ui_message, update_after_resume
│                       #       ensure_session, generate_title
│
├── websocket.py        # [删除]
└── app.py              # 添加 SSE router 注册
```

### Frontend Module Change

```
frontend/src/api/
├── sse-client.ts       # [新建] SSE 客户端
│                       # 职责：fetch + reader, 事件分发, cancel
├── websocket.ts        # [删除]
└── http.ts             # [保留] 其他 REST API
```

### Data Flow

```
ChatInput.vue
    ↓ sendMessage()
chat.ts store
    ↓ fetch POST /api/threads/{id}/runs/stream
FastAPI sse.py endpoint
    ↓ StreamingResponse(event_stream(), media_type="text/event-stream")
event_stream() generator
    ↓ engine.chat_stream() → astream_events v2
    ↓ stream_utils.format_sse_event(event) → yield SSE frame
    ↓ persistence.save_ui_message() (async, after stream)
    ↓ check interrupts via aget_state()
    ↓ yield done/interrupt event
    ↓ [END]
ReadableStream reader (前端)
    ↓ 解析 SSE frames
chat.ts store
    ↓ 根据 event.type 更新 reactive state
Vue 组件渲染
```

---

## Error Handling

| 场景 | 处理 |
|------|------|
| Agent 不存在 | yield error event, return |
| LLM API 错误 | `_categorize_error()` → yield error event |
| 客户端断开 | FastAPI `ClientDisconnect` → set cancel flag |
| Cancel 请求 | set flag → yield cancelled event → return |
| 工具执行超时（>30s） | 穿插 heartbeat comment |
| 并发 run 同一 thread | cancel 前一个 run |
| Stream 异常结束 | 前端检测到 reader done，调 `/state` 检查 |

---

## Testing Strategy

| 层级 | 内容 | 工具 |
|------|------|------|
| 单元 | stream_utils 事件解析 | pytest |
| 集成 | SSE 端点 + mock stream | httpx AsyncClient |
| E2E | 前端→后端完整流程 | 手动 + DevTools |

---

## Migration Steps (High Level)

1. 创建 `stream_utils.py` — 提取事件处理逻辑
2. 创建 `persistence.py` — 提取 DB 操作
3. 创建 `sse.py` — 实现 SSE 端点
4. 注册路由到 `app.py`
5. 创建前端 `sse-client.ts`
6. 修改 `chat.ts` store 和相关组件
7. 删除 `websocket.py` 和 `websocket.ts`
8. 删除 `app.py` 中的 WebSocket 路由注册
9. 测试全部流程

---

## Out of Scope

- Agent Server Protocol v2 完整实现（seq、channel filter、reconnect replay）
- `@langchain/vue` 官方 SDK 集成（未来可选）
- 多 run 并发管理（当前一个 thread 同时只有一个 run）
- SSE 断线自动重连（前端检测异常后手动恢复即可）
