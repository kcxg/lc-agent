# SSE Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 lc-agent 通信从 WebSocket 迁移到 SSE + REST，删除 WebSocket 代码。

**Architecture:** 从 websocket.py 拆分为 stream_utils.py + persistence.py + sse.py 三个模块；前端用 fetch + ReadableStream 替代 WebSocket。

**Tech Stack:** FastAPI StreamingResponse, asyncio generators, Vue 3 fetch API

---

## Task 1: 提取 stream_utils.py

**Files:**
- Create: `lc_agent/server/stream_utils.py`
- Reference: `lc_agent/server/websocket.py:655-837`

- [ ] **Step 1: 创建 stream_utils.py，提取事件格式化和 usage 累积**

从 `websocket.py` 提取以下方法为独立函数（去掉 self 参数，去掉 websocket 依赖）：
- `_accumulate_assistant_display_state()` → 保持签名，接收 event + 可变状态
- `_accumulate_usage()` → 保持签名
- `format_sse_event(event_type, data)` → 新函数，格式化为 `event: xxx\ndata: {...}\n\n`
- `convert_stream_event(event)` → 新函数，从 astream_events v2 event 生成 SSE 事件列表

关键：`convert_stream_event` 相当于现有的 `_send_event`，但返回 `list[tuple[str, dict]]` 而不是直接发 WebSocket。

```python
def convert_stream_event(event: dict) -> list[tuple[str, dict]]:
    """Convert astream_events v2 event to SSE event tuples (type, payload)."""
    results = []
    kind = event.get("event", "")
    
    if kind == "on_chat_model_stream":
        chunk = event.get("data", {}).get("chunk")
        if chunk:
            additional = getattr(chunk, "additional_kwargs", None) or {}
            reasoning = additional.get("reasoning_content") or additional.get("reasoning")
            if reasoning:
                results.append(("thinking", {"content": reasoning}))
            if hasattr(chunk, "content") and chunk.content:
                content = chunk.content
                if isinstance(content, list):
                    content = "".join(
                        p.get("text", "") if isinstance(p, dict) else str(p) for p in content
                    )
                results.append(("token", {"content": content}))
    elif kind == "on_tool_start":
        # ... 同现有 _send_event 逻辑
    elif kind == "on_tool_end":
        # ... 同现有 _send_event 逻辑
    
    return results
```

- [ ] **Step 2: 验证提取正确**

运行 `pytest tests/` 确保无 import 错误。

- [ ] **Step 3: Commit**

```bash
git add lc_agent/server/stream_utils.py
git commit -m "refactor: extract stream_utils from websocket handler"
```

---

## Task 2: 提取 persistence.py

**Files:**
- Create: `lc_agent/server/persistence.py`
- Reference: `lc_agent/server/websocket.py:288-653`

- [ ] **Step 1: 创建 persistence.py，提取 DB 操作**

提取以下方法为独立 async 函数：
- `save_ui_message(db_url, thread_id, role, content, *, tool_calls, usage, http_traces)`
- `update_message_after_resume(db_url, thread_id, content, *, all_tool_calls, usage_rounds, http_traces, resume_duration_ms)`
- `ensure_session(db_url, thread_id, title, preset_id, model_id)`
- `increment_session_message_count(db_url, thread_id)`
- `generate_title(engine, thread_id, content, preset_id, model_id)` → 返回 title string
- `truncate_from_message(db_url, thread_id, message_id)`
- `load_resume_context(db_url, thread_id)` → 返回 (tool_calls, trace_count)

所有函数接收 `db_url` 参数而非 self。

- [ ] **Step 2: Commit**

```bash
git add lc_agent/server/persistence.py
git commit -m "refactor: extract persistence from websocket handler"
```

---

## Task 3: 实现 sse.py

**Files:**
- Create: `lc_agent/server/sse.py`
- Modify: `lc_agent/server/app.py`

- [ ] **Step 1: 创建 SSE 路由 — stream 端点**

```python
router = APIRouter(prefix="/api/threads", tags=["chat-sse"])

@router.post("/{thread_id}/runs/stream")
async def run_stream(thread_id: str, req: RunStreamRequest, request: Request):
    """统一入口：发消息或恢复中断，都返回 SSE 流。"""
    if req.command:
        return await _resume_stream(thread_id, req, request)
    return await _send_stream(thread_id, req, request)
```

`_send_stream` 逻辑：
1. 获取 engine + agent
2. 创建 `async def event_stream()` generator
3. 内部调用 `engine.chat_stream()` 循环
4. 用 `stream_utils.convert_stream_event()` 转换每个事件
5. 用 `stream_utils.format_sse_event()` 格式化
6. 流结束后检查 interrupt (aget_state)
7. 调用 persistence 保存消息
8. yield done 事件
9. 返回 `StreamingResponse(event_stream(), media_type="text/event-stream")`

`_resume_stream` 逻辑类似，但用 `Command(resume=value)` 调用 agent。

- [ ] **Step 2: 实现 cancel 端点**

```python
@router.post("/{thread_id}/runs/cancel")
async def cancel_run(thread_id: str):
    _cancel_flags[thread_id] = True
    return {"ok": True}
```

- [ ] **Step 3: 实现 state 端点**

```python
@router.get("/{thread_id}/state")
async def get_thread_state(thread_id: str, ...):
    # 检查是否有 pending interrupt
```

- [ ] **Step 4: 实现 heartbeat 机制**

在 event_stream generator 中，当工具执行时间超过 15 秒时插入 SSE comment。

- [ ] **Step 5: 实现客户端断开检测**

```python
async def event_stream():
    ...
    # 检测客户端是否断开
    if await request.is_disconnected():
        _cancel_flags[thread_id] = True
        return
```

- [ ] **Step 6: 注册路由到 app.py**

在 `create_app()` 中添加 `app.include_router(sse_router)`。

- [ ] **Step 7: Commit**

```bash
git add lc_agent/server/sse.py lc_agent/server/app.py
git commit -m "feat: implement SSE streaming endpoints"
```

---

## Task 4: 前端 SSE 客户端

**Files:**
- Create: `frontend/src/api/sse-client.ts`

- [ ] **Step 1: 创建 SSE client 类**

核心方法：
- `sendMessage(threadId, content, presetId, model)` → POST + 消费流
- `resumeInterrupt(threadId, resumeValue, presetId, model)` → POST + 消费流
- `cancel(threadId)` → POST /cancel
- `on(event, handler)` / `off(event, handler)` — 事件订阅

内部 `_consumeStream(response)` 使用 `response.body.getReader()` + TextDecoder 解析 SSE。

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/sse-client.ts
git commit -m "feat: add SSE client for frontend"
```

---

## Task 5: 前端 Store 切换

**Files:**
- Modify: `frontend/src/stores/chat.ts`
- Modify: `frontend/src/components/chat/ChatInput.vue`
- Modify: `frontend/src/components/chat/InterruptDialog.vue`

- [ ] **Step 1: 修改 chat.ts store**

替换 WebSocket 调用为 SSE client 调用：
- `sendMessage()` → `sseClient.sendMessage()`
- interrupt response → `sseClient.resumeInterrupt()`
- cancel → `sseClient.cancel()`
- 事件处理保持现有 handler 逻辑（token → appendContent, tool_call → addToolCall, etc.）

- [ ] **Step 2: 修改 ChatInput.vue**

如果发送逻辑在组件中有直接 WS 引用，替换为 store action 调用。

- [ ] **Step 3: 修改 InterruptDialog.vue**

审批/拒绝按钮改为调用 store 的 resume action。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/stores/chat.ts frontend/src/components/chat/ChatInput.vue frontend/src/components/chat/InterruptDialog.vue
git commit -m "feat: wire frontend to SSE endpoints"
```

---

## Task 6: 删除 WebSocket 代码

**Files:**
- Delete: `lc_agent/server/websocket.py`
- Delete: `frontend/src/api/websocket.ts`
- Modify: `lc_agent/server/app.py` (删除 WS 路由注册)
- Modify: `lc_agent/app.py` (删除 WS handler 初始化)

- [ ] **Step 1: 删除后端 WebSocket 文件和注册**

删除 `websocket.py`，从 `app.py` 中移除 WebSocket 路由注册代码。

- [ ] **Step 2: 删除前端 WebSocket 文件**

删除 `websocket.ts`，确保无处引用它。

- [ ] **Step 3: 全局搜索清理残留引用**

`rg "websocket|WebSocket|ws\." --type py --type ts` 确保无遗漏。

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: remove WebSocket code, SSE migration complete"
```

---

## Task 7: 集成测试

- [ ] **Step 1: 写 SSE 端点集成测试**

使用 httpx AsyncClient + ASGI transport 测试：
- `/runs/stream` 正常响应 SSE 格式
- `/runs/cancel` 返回 200
- `/state` 返回正确格式

- [ ] **Step 2: 手动端到端验证**

启动 bfzs 项目，验证：
1. 正常对话流
2. 工具调用 + 审批
3. 取消
4. 错误处理

- [ ] **Step 3: Commit 测试**

```bash
git add tests/
git commit -m "test: add SSE endpoint integration tests"
```
