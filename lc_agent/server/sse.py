"""SSE streaming endpoints for chat.

Replaces WebSocket communication with POST → SSE streaming + REST control endpoints.
API design aligns with LangGraph /threads/{id}/runs/stream pattern.
"""

import asyncio
import time
import traceback
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from lc_agent.core.engine import AgentEngine
from lc_agent.core.http_trace import (
    HttpTraceCollector,
    bind_http_trace_collector,
    reset_http_trace_collector,
)
from lc_agent.server import persistence, stream_utils

router = APIRouter(prefix="/api/threads", tags=["chat-sse"])

_cancel_flags: dict[str, bool] = {}
_run_locks: dict[str, asyncio.Lock] = {}

_engine: AgentEngine | None = None
_db_url: str = "sqlite+aiosqlite:///./lc_agent_data.db"


def configure(engine: AgentEngine, db_url: str) -> None:
    """Initialize the SSE module with engine and DB URL. Called once at app startup."""
    global _engine, _db_url
    _engine = engine
    _db_url = db_url


def _get_engine() -> AgentEngine:
    if _engine is None:
        raise RuntimeError("SSE module not configured. Call sse.configure() first.")
    return _engine


# --- Request Models ---


class RunStreamRequest(BaseModel):
    input: str | None = None
    command: dict[str, Any] | None = None
    preset_id: str = "__chat__"
    model: str = ""
    replace_from_message_id: str | None = None
    history: list[dict[str, Any]] | None = None


# --- Endpoints ---


def _get_lock(thread_id: str) -> asyncio.Lock:
    if thread_id not in _run_locks:
        _run_locks[thread_id] = asyncio.Lock()
    return _run_locks[thread_id]


@router.post("/{thread_id}/runs/stream")
async def run_stream(thread_id: str, req: RunStreamRequest, request: Request):
    """Unified entry: send message or resume interrupt, returning SSE stream."""
    lock = _get_lock(thread_id)
    if lock.locked():
        _cancel_flags[thread_id] = True
        try:
            await asyncio.wait_for(lock.acquire(), timeout=10)
            lock.release()
        except asyncio.TimeoutError:
            async def timeout_stream():
                yield stream_utils.format_sse_event("error", {
                    "title": "请求超时",
                    "detail": "等待前一个请求完成超时，请稍后重试。",
                    "suggestions": ["稍后再次发送消息"],
                    "error_code": "LOCK_TIMEOUT",
                    "tech_detail": "Timed out waiting for previous run to complete",
                    "message": "Timed out waiting for previous run to complete",
                })

            return StreamingResponse(
                timeout_stream(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
            )

    if req.command is not None:
        return await _resume_stream(thread_id, req, request)
    return await _send_stream(thread_id, req, request)


@router.post("/{thread_id}/runs/cancel")
async def cancel_run(thread_id: str):
    """Cancel the currently active run for this thread."""
    _cancel_flags[thread_id] = True
    return {"ok": True, "thread_id": thread_id}


@router.get("/{thread_id}/state")
async def get_thread_state(thread_id: str, preset_id: str = "__chat__", model: str = ""):
    """Check thread state — primarily for pending interrupts."""
    engine = _get_engine()
    agent = engine._get_or_build_agent(preset_id, model)
    if agent is None:
        return {"has_interrupts": False, "error": "agent_not_found"}

    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": engine.recursion_limit}
    try:
        graph_state = await agent.aget_state(config)
        interrupts = []
        if graph_state.tasks:
            for task in graph_state.tasks:
                for intr in (task.interrupts or ()):
                    interrupts.append({
                        "value": intr.value,
                        "id": getattr(intr, "id", None),
                    })
        return {"has_interrupts": bool(interrupts), "interrupts": interrupts}
    except Exception as e:
        return {"has_interrupts": False, "error": str(e)}


# --- Internal Stream Implementations ---


async def _send_stream(thread_id: str, req: RunStreamRequest, request: Request):
    """Handle new message: save to DB, stream agent response as SSE."""
    engine = _get_engine()
    content = req.input or ""
    preset_id = req.preset_id
    model_id = req.model
    lock = _get_lock(thread_id)
    _cancel_flags[thread_id] = False

    try:
        msg_count = await persistence.get_session_message_count(_db_url, thread_id)
        is_first = msg_count == 0
        if is_first:
            preliminary_title = content[:30].strip()
            await persistence.ensure_session(_db_url, thread_id, preliminary_title, preset_id, model_id)

        if req.replace_from_message_id:
            await persistence.truncate_from_message(_db_url, thread_id, req.replace_from_message_id)
            await engine.reset_thread(thread_id)

        await persistence.save_ui_message(_db_url, thread_id, "user", content)
    except Exception as e:
        traceback.print_exc()

        async def error_stream():
            error_info = stream_utils.categorize_error(e)
            error_info["tech_detail"] = str(e)
            error_info["message"] = str(e)
            yield stream_utils.format_sse_event("error", error_info)

        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    async def event_stream():
        nonlocal is_first
        await lock.acquire()
        try:
            usage_rounds: list[dict] = []
            round_start_time = time.time()
            stream_start_time = time.time()
            content_parts: list[str] = []
            tool_calls: list[dict[str, Any]] = []
            in_thinking = False
            last_event_time = time.time()

            if is_first:
                preliminary_title = content[:30].strip()
                yield stream_utils.format_sse_event("title_update", {
                    "thread_id": thread_id,
                    "title": preliminary_title,
                })

            stream_kwargs: dict[str, Any] = {}
            if model_id:
                stream_kwargs["model_id"] = model_id
            if req.replace_from_message_id:
                stream_kwargs["history"] = req.history or []

            model_info = engine._find_model(model_id) if model_id else None
            provider = model_info.provider if model_info else None
            resolved_model = model_info.id if model_info else model_id
            trace_collector = HttpTraceCollector(provider=provider, model=resolved_model)
            trace_token = bind_http_trace_collector(trace_collector)

            try:
                stream = engine.chat_stream(content, thread_id, preset_id, **stream_kwargs)
                async for event in stream:
                    if _cancel_flags.get(thread_id):
                        yield stream_utils.format_sse_event("cancelled", {})
                        return

                    if await request.is_disconnected():
                        _cancel_flags[thread_id] = True
                        return

                    in_thinking = stream_utils.accumulate_display_state(
                        event, content_parts, tool_calls, in_thinking,
                    )

                    for evt_type, evt_data in stream_utils.convert_stream_event(event):
                        yield stream_utils.format_sse_event(evt_type, evt_data)
                        last_event_time = time.time()

                    prev_len = len(usage_rounds)
                    stream_utils.accumulate_usage(event, usage_rounds)
                    if len(usage_rounds) > prev_len:
                        usage_rounds[-1]["duration_ms"] = int((time.time() - round_start_time) * 1000)
                        round_start_time = time.time()
                        yield stream_utils.format_sse_event("llm_usage", usage_rounds[-1])

                    if time.time() - last_event_time > 15:
                        yield stream_utils.SSE_HEARTBEAT
                        last_event_time = time.time()
            finally:
                if in_thinking:
                    content_parts.append("<!--THINK_END-->")
                reset_http_trace_collector(trace_token)

            interrupt_sent = False
            try:
                agent = engine._get_or_build_agent(preset_id, model_id)
                state_config = {"configurable": {"thread_id": thread_id}, "recursion_limit": engine.recursion_limit}
                graph_state = await agent.aget_state(state_config)
                if graph_state.tasks:
                    all_interrupts = []
                    for task in graph_state.tasks:
                        for intr in (task.interrupts or ()):
                            all_interrupts.append({
                                "value": intr.value,
                                "id": getattr(intr, "id", None),
                            })
                    if all_interrupts:
                        interrupt_payload: dict[str, Any] = {
                            "message": "Tool requires approval",
                            "data": all_interrupts,
                        }
                        first_value = all_interrupts[0].get("value")
                        if isinstance(first_value, dict):
                            if "action_requests" in first_value:
                                interrupt_payload["action_requests"] = first_value["action_requests"]
                            if "review_configs" in first_value:
                                interrupt_payload["review_configs"] = first_value["review_configs"]
                        yield stream_utils.format_sse_event("interrupt", interrupt_payload)
                        interrupt_sent = True
            except Exception as e:
                print(f"[SSE] Failed to check interrupt state: {e}")

            http_traces = trace_collector.snapshot()
            if http_traces:
                for i in range(len(http_traces)):
                    marker = f"\n<!--HTTP:{i}-->\n"
                    content_parts.append(marker)
                    yield stream_utils.format_sse_event("content", {"content": marker})

            done_payload: dict[str, Any] = {}
            if usage_rounds:
                done_payload["usage"] = usage_rounds
            if http_traces:
                done_payload["http_traces"] = http_traces

            if content_parts or tool_calls or usage_rounds or http_traces:
                await persistence.save_ui_message(
                    _db_url, thread_id, "assistant",
                    "".join(content_parts),
                    tool_calls=tool_calls or None,
                    usage={
                        "rounds": usage_rounds,
                        "tool_call_count": len(tool_calls),
                        "total_duration_ms": int((time.time() - stream_start_time) * 1000),
                    },
                    http_traces=http_traces or None,
                )

            yield stream_utils.format_sse_event("done", done_payload)

            asyncio.create_task(persistence.increment_session_message_count(_db_url, thread_id))

            if is_first:
                asyncio.create_task(_generate_and_yield_title(thread_id, content, preset_id, model_id))

        except Exception as e:
            traceback.print_exc()
            error_info = stream_utils.categorize_error(e)
            error_info["tech_detail"] = str(e)
            error_info["message"] = str(e)
            yield stream_utils.format_sse_event("error", error_info)
        finally:
            lock.release()
            _cancel_flags.pop(thread_id, None)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _resume_stream(thread_id: str, req: RunStreamRequest, request: Request):
    """Handle interrupt resume: stream continued agent response as SSE."""
    engine = _get_engine()
    preset_id = req.preset_id
    model_id = req.model
    lock = _get_lock(thread_id)
    _cancel_flags[thread_id] = False

    resume_value = req.command.get("resume", {}) if req.command else {}

    async def event_stream():
        await lock.acquire()
        try:
            usage_rounds: list[dict] = []
            round_start_time = time.time()
            stream_start_time = time.time()
            content_parts: list[str] = []
            in_thinking = False
            last_event_time = time.time()

            existing_tool_calls, existing_trace_count = await persistence.load_resume_context(_db_url, thread_id)
            tool_calls: list[dict[str, Any]] = list(existing_tool_calls)
            from langgraph.types import Command

            agent = engine._get_or_build_agent(preset_id, model_id)
            if agent is None:
                yield stream_utils.format_sse_event("error", {
                    "title": "缺少 AI 代理配置",
                    "detail": "没有找到用于恢复对话的 AI 代理配置，可能是配置已变更。",
                    "suggestions": ["刷新页面后重试", "重新选择 AI 助手并开始新对话"],
                    "error_code": "AGENT_NOT_FOUND",
                    "tech_detail": "No agent found for resume",
                })
                return

            config = {"configurable": {"thread_id": thread_id}, "recursion_limit": engine.recursion_limit}

            model_info = engine._find_model(model_id) if model_id else None
            provider = model_info.provider if model_info else None
            resolved_model = model_info.id if model_info else model_id
            trace_collector = HttpTraceCollector(
                provider=provider, model=resolved_model, seq_offset=existing_trace_count,
            )
            trace_token = bind_http_trace_collector(trace_collector)

            try:
                async for event in agent.astream_events(
                    Command(resume=resume_value),
                    config=config,
                    version="v2",
                ):
                    if _cancel_flags.get(thread_id):
                        yield stream_utils.format_sse_event("cancelled", {})
                        return

                    if await request.is_disconnected():
                        _cancel_flags[thread_id] = True
                        return

                    in_thinking = stream_utils.accumulate_display_state(
                        event, content_parts, tool_calls, in_thinking,
                    )

                    for evt_type, evt_data in stream_utils.convert_stream_event(event):
                        yield stream_utils.format_sse_event(evt_type, evt_data)
                        last_event_time = time.time()

                    prev_len = len(usage_rounds)
                    stream_utils.accumulate_usage(event, usage_rounds)
                    if len(usage_rounds) > prev_len:
                        usage_rounds[-1]["duration_ms"] = int((time.time() - round_start_time) * 1000)
                        round_start_time = time.time()
                        yield stream_utils.format_sse_event("llm_usage", usage_rounds[-1])

                    if time.time() - last_event_time > 15:
                        yield stream_utils.SSE_HEARTBEAT
                        last_event_time = time.time()
            finally:
                if in_thinking:
                    content_parts.append("<!--THINK_END-->")
                reset_http_trace_collector(trace_token)

            interrupt_sent = False
            try:
                graph_state = await agent.aget_state(config)
                if graph_state.tasks:
                    all_interrupts = []
                    for task in graph_state.tasks:
                        for intr in (task.interrupts or ()):
                            all_interrupts.append({
                                "value": intr.value,
                                "id": getattr(intr, "id", None),
                            })
                    if all_interrupts:
                        interrupt_payload: dict[str, Any] = {
                            "message": "Tool requires approval",
                            "data": all_interrupts,
                        }
                        first_value = all_interrupts[0].get("value")
                        if isinstance(first_value, dict):
                            if "action_requests" in first_value:
                                interrupt_payload["action_requests"] = first_value["action_requests"]
                            if "review_configs" in first_value:
                                interrupt_payload["review_configs"] = first_value["review_configs"]
                        yield stream_utils.format_sse_event("interrupt", interrupt_payload)
                        interrupt_sent = True
            except Exception as e:
                print(f"[SSE] Failed to check interrupt state after resume: {e}")

            if isinstance(resume_value, dict):
                permanently_allow = resume_value.get("permanently_allow")
                if permanently_allow and hasattr(request.app.state, "permissions"):
                    request.app.state.permissions.allow_tool(permanently_allow)

            http_traces = trace_collector.snapshot()
            done_payload: dict[str, Any] = {"is_resume": True}
            if usage_rounds:
                done_payload["usage"] = usage_rounds
            if http_traces:
                done_payload["http_traces"] = http_traces

            new_content = "".join(content_parts)
            if new_content or tool_calls or usage_rounds or http_traces:
                await persistence.append_to_last_assistant_message(
                    _db_url, thread_id, new_content,
                    all_tool_calls=tool_calls or None,
                    usage_rounds=usage_rounds or None,
                    http_traces=http_traces or None,
                    resume_duration_ms=int((time.time() - stream_start_time) * 1000),
                )

            yield stream_utils.format_sse_event("done", done_payload)

        except Exception as e:
            traceback.print_exc()
            error_info = stream_utils.categorize_error(e)
            error_info["tech_detail"] = str(e)
            error_info["message"] = str(e)
            yield stream_utils.format_sse_event("error", error_info)
        finally:
            lock.release()
            _cancel_flags.pop(thread_id, None)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _generate_and_yield_title(
    thread_id: str,
    first_message: str,
    preset_id: str,
    model_id: str,
) -> None:
    """Background task: generate title and save to DB.

    Note: since the SSE stream is already closed by the time this runs,
    the title update will be delivered on the next state query or page refresh.
    """
    engine = _get_engine()
    title = await persistence.generate_title(engine, thread_id, first_message, preset_id, model_id)
    if title:
        await persistence.save_title(_db_url, thread_id, title)
