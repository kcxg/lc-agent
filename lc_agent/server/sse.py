"""SSE streaming endpoints for chat.

Replaces WebSocket communication with POST → SSE streaming + REST control endpoints.
API design aligns with LangGraph /threads/{id}/runs/stream pattern.
"""

import asyncio
import logging
import time
import traceback
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from lc_agent.core.engine import AgentEngine
from lc_agent.core.http_trace import (
    HttpTraceCollector,
    bind_http_trace_collector,
    init_subagent_collector_registry,
    pop_subagent_traces,
    reset_http_trace_collector,
)
from lc_agent.server import persistence, stream_utils

router = APIRouter(prefix="/api/threads", tags=["chat-sse"])

logger = logging.getLogger(__name__)

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
    llm_params: dict[str, Any] | None = None
    replace_from_message_id: str | None = None
    history: list[dict[str, Any]] | None = None


# --- Endpoints ---


async def _authenticate_sse(request: Request):
    """Authenticate SSE request. Returns User or None. Returns None if auth not configured."""
    auth_service = getattr(request.app.state, "auth_service", None)
    if auth_service is None:
        return None  # Auth not configured, allow all (backward compat)

    from lc_agent.server.auth_middleware import _extract_token
    token = _extract_token(request)
    if not token:
        return None

    payload = auth_service.decode_token(token)
    if payload is None:
        return None

    from lc_agent.db.models_auth import User
    from sqlalchemy import select
    from lc_agent.db.engine import get_async_session
    db_url = request.app.state.config.get("database", {}).get("url", "sqlite+aiosqlite:///./lc_agent_data.db")
    db = get_async_session(db_url)
    try:
        result = await db.execute(select(User).where(User.id == payload["sub"]))
        return result.scalar_one_or_none()
    finally:
        await db.close()


async def _check_sse_auth(request: Request, thread_id: str) -> JSONResponse | None:
    """Return JSONResponse if access denied, None if allowed."""
    user = await _authenticate_sse(request)
    auth_service = getattr(request.app.state, "auth_service", None)
    if auth_service is not None and user is None:
        return JSONResponse(status_code=401, content={"detail": "认证失败"})

    if user is not None:
        from lc_agent.db.engine import get_async_session as _get_session
        from lc_agent.db.models import SessionMeta
        from sqlalchemy import select as sa_select
        db_url = request.app.state.config.get("database", {}).get("url", "sqlite+aiosqlite:///./lc_agent_data.db")
        _db = _get_session(db_url)
        try:
            result = await _db.execute(sa_select(SessionMeta).where(SessionMeta.id == thread_id))
            session_meta = result.scalar_one_or_none()
            if session_meta:
                # Deny if session has owner and it's not this user
                if session_meta.user_id and session_meta.user_id != user.id and user.role != "admin":
                    return JSONResponse(status_code=403, content={"detail": "权限不足"})
                # For sessions with no owner (user_id=""), only admin can access
                if not session_meta.user_id and user.role != "admin":
                    return JSONResponse(status_code=403, content={"detail": "权限不足"})
        finally:
            await _db.close()

    return None


def _get_lock(thread_id: str) -> asyncio.Lock:
    if thread_id not in _run_locks:
        _run_locks[thread_id] = asyncio.Lock()
    return _run_locks[thread_id]


@router.post("/{thread_id}/runs/stream")
async def run_stream(thread_id: str, req: RunStreamRequest, request: Request):
    """Unified entry: send message or resume interrupt, returning SSE stream."""
    auth_error = await _check_sse_auth(request, thread_id)
    if auth_error is not None:
        return auth_error

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
async def cancel_run(thread_id: str, request: Request):
    """Cancel the currently active run for this thread."""
    user = await _authenticate_sse(request)
    auth_service = getattr(request.app.state, "auth_service", None)
    if auth_service is not None and user is None:
        return JSONResponse(status_code=401, content={"detail": "认证失败"})

    _cancel_flags[thread_id] = True
    return {"ok": True, "thread_id": thread_id}


@router.get("/{thread_id}/state")
async def get_thread_state(thread_id: str, request: Request, preset_id: str = "__chat__", model: str = ""):
    """Check thread state — primarily for pending interrupts."""
    auth_error = await _check_sse_auth(request, thread_id)
    if auth_error is not None:
        return auth_error

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
    llm_params = req.llm_params
    lock = _get_lock(thread_id)
    _cancel_flags[thread_id] = False
    user = await _authenticate_sse(request)

    try:
        msg_count = await persistence.get_session_message_count(_db_url, thread_id)
        is_first = msg_count == 0
        if is_first:
            preliminary_title = content[:30].strip()
            await persistence.ensure_session(
                _db_url, thread_id, preliminary_title, preset_id, model_id,
                user_id=user.id if user else "",
            )

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
            # Ensure the agent is built (and subagent tools are cached) before streaming
            try:
                engine._get_or_build_agent(preset_id, model_id, llm_params=llm_params)
            except Exception as _e:
                logger.warning("Failed to pre-build agent for subagent tool name lookup: %s", _e)
            subagent_display_map = engine.get_subagent_display_name_map(
                preset_id, model_id=model_id or "", llm_params=llm_params,
            )
            subagent_tool_names = set(subagent_display_map.keys())
            _sa_writers: dict[str, dict] = {}
            _sa_finalize_tasks: list[asyncio.Task] = []
            _sa_create_tasks: list[asyncio.Task] = []

            # Initialize sub-agent HTTP trace collector registry for this stream
            init_subagent_collector_registry()

            if is_first:
                preliminary_title = content[:30].strip()
                yield stream_utils.format_sse_event("title_update", {
                    "thread_id": thread_id,
                    "title": preliminary_title,
                })

            stream_kwargs: dict[str, Any] = {}
            if model_id:
                stream_kwargs["model_id"] = model_id
            if llm_params:
                stream_kwargs["llm_params"] = llm_params
            if req.replace_from_message_id:
                stream_kwargs["history"] = req.history or []

            model_info = engine._find_model(model_id) if model_id else None
            provider = model_info.provider if model_info else None
            resolved_model = model_info.id if model_info else model_id
            trace_collector = HttpTraceCollector(provider=provider, model=resolved_model)
            trace_token = bind_http_trace_collector(trace_collector)

            try:
                stream = engine.chat_stream(
                    content,
                    thread_id,
                    preset_id,
                    user_id=user.id if user else "anonymous",
                    **stream_kwargs,
                )
                async for event in stream:
                    if _cancel_flags.get(thread_id):
                        yield stream_utils.format_sse_event("cancelled", {})
                        return

                    if await request.is_disconnected():
                        _cancel_flags[thread_id] = True
                        return

                    in_thinking = stream_utils.accumulate_display_state(
                        event, content_parts, tool_calls, in_thinking,
                        subagent_tool_names=subagent_tool_names,
                        thread_id=thread_id,
                        subagent_display_map=subagent_display_map,
                    )

                    for evt_type, evt_data in stream_utils.convert_stream_event(
                        event, subagent_tool_names=subagent_tool_names,
                    ):
                        # Enrich subagent_start with display name and sub_session_id before yielding
                        if evt_type == "subagent_start":
                            tool_name = evt_data.get("name", "")
                            display_name = subagent_display_map.get(tool_name) or tool_name
                            sa_tid_pre = evt_data["tool_call_id"]
                            evt_data = {
                                **evt_data,
                                "name": display_name,
                                "sub_session_id": f"{thread_id}--sa--{sa_tid_pre}",
                            }
                        elif evt_type == "tool_call" and evt_data.get("is_subagent"):
                            # Replace internal tool name with friendly display name
                            raw_name = evt_data.get("name", "")
                            evt_data = {
                                **evt_data,
                                "name": subagent_display_map.get(raw_name) or raw_name,
                            }
                        elif evt_type == "subagent_done":
                            # Pre-yield: pop traces so they can be attached to the event
                            # and front-end live mode can display them immediately.
                            sa_tid_done = evt_data["tool_call_id"]
                            if sa_tid_done in _sa_writers:
                                writer_done = _sa_writers.pop(sa_tid_done)
                                if writer_done["in_thinking"]:
                                    writer_done["content_parts"].append("<!--THINK_END-->")
                                sa_content_done = "".join(writer_done["content_parts"])
                                sub_sid_done = writer_done["sub_session_id"]
                                sa_http_traces = pop_subagent_traces(sub_sid_done) or None
                                if sa_http_traces:
                                    evt_data = {**evt_data, "http_traces": sa_http_traces}
                                _t = asyncio.create_task(persistence.finalize_subsession_message(
                                    _db_url, sub_sid_done, sa_content_done,
                                    tool_calls=writer_done["tool_calls"] or None,
                                    http_traces=sa_http_traces,
                                ))
                                _sa_finalize_tasks.append(_t)
                        yield stream_utils.format_sse_event(evt_type, evt_data)
                        last_event_time = time.time()

                        if evt_type == "subagent_start":
                            sa_tid = evt_data["tool_call_id"]
                            sa_query = evt_data.get("query", "")
                            sa_name = evt_data.get("name", "sub-agent")
                            parent_tid = thread_id
                            sub_sid = f"{parent_tid}--sa--{sa_tid}"
                            _sa_writers[sa_tid] = {
                                "content_parts": [],
                                "tool_calls": [],
                                "query": sa_query,
                                "sub_session_id": sub_sid,
                                "in_thinking": False,
                            }
                            _sa_create_tasks.append(asyncio.create_task(persistence.create_subsession(
                                _db_url, sub_sid, parent_tid, sa_tid,
                                agent_id=sa_name,
                                title=f"{sa_name}: {sa_query[:30]}",
                                user_id=user.id if user else "",
                            )))
                            _sa_create_tasks.append(asyncio.create_task(persistence.save_subsession_delegation_message(
                                _db_url, sub_sid, sa_query,
                            )))
                            for tc in tool_calls:
                                if tc.get("runId") == sa_tid or tc.get("run_id") == sa_tid:
                                    tc["is_subagent"] = True
                                    tc["sub_session_id"] = sub_sid
                                    tc["name"] = sa_name  # use display_name (already enriched)
                                    break

                        elif evt_type == "subagent_thinking":
                            sa_tid = evt_data["tool_call_id"]
                            if sa_tid in _sa_writers:
                                writer = _sa_writers[sa_tid]
                                if not writer["in_thinking"]:
                                    writer["content_parts"].append("<!--THINK_START-->")
                                    writer["in_thinking"] = True
                                writer["content_parts"].append(evt_data.get("content", ""))

                        elif evt_type == "subagent_token":
                            sa_tid = evt_data["tool_call_id"]
                            if sa_tid in _sa_writers:
                                writer = _sa_writers[sa_tid]
                                if writer["in_thinking"]:
                                    writer["content_parts"].append("<!--THINK_END-->")
                                    writer["in_thinking"] = False
                                writer["content_parts"].append(evt_data.get("content", ""))

                        elif evt_type == "subagent_tool_call":
                            sa_tid = evt_data["tool_call_id"]
                            if sa_tid in _sa_writers:
                                writer = _sa_writers[sa_tid]
                                if writer["in_thinking"]:
                                    writer["content_parts"].append("<!--THINK_END-->")
                                    writer["in_thinking"] = False
                                tool_idx = len(writer["tool_calls"])
                                writer["content_parts"].append(f"\n<!--TOOL:{tool_idx}-->\n")
                                writer["tool_calls"].append({
                                    "name": evt_data["name"],
                                    "args": evt_data.get("args"),
                                    "status": "running",
                                    "startTime": int(time.time() * 1000),
                                })

                        elif evt_type == "subagent_tool_result":
                            sa_tid = evt_data["tool_call_id"]
                            if sa_tid in _sa_writers:
                                name = evt_data["name"]
                                for tc in reversed(_sa_writers[sa_tid]["tool_calls"]):
                                    if tc["name"] == name and tc.get("status") == "running":
                                        tc["result"] = evt_data.get("result")
                                        tc["status"] = "done"
                                        tc["duration"] = int(time.time() * 1000) - tc.get("startTime", int(time.time() * 1000))
                                        break

                        elif evt_type == "subagent_done":
                            pass  # Handled in pre-yield block above

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
                agent = engine._get_or_build_agent(preset_id, model_id, llm_params=llm_params)
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
                                reqs = first_value["action_requests"]
                                # Enrich with display_name for sub-agent tools
                                if subagent_display_map:
                                    reqs = [
                                        {**r, "display_name": subagent_display_map.get(r.get("name", ""))}
                                        if r.get("name") in subagent_display_map else r
                                        for r in reqs
                                    ]
                                interrupt_payload["action_requests"] = reqs
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

            # Ensure all sub-agent create/finalize tasks complete before persisting main message
            all_sa_tasks = _sa_create_tasks + _sa_finalize_tasks
            if all_sa_tasks:
                await asyncio.gather(*all_sa_tasks, return_exceptions=True)

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
    llm_params = req.llm_params
    lock = _get_lock(thread_id)
    _cancel_flags[thread_id] = False
    user = await _authenticate_sse(request)

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
            # Ensure the agent is built (and subagent tools are cached) before streaming
            try:
                engine._get_or_build_agent(preset_id, model_id, llm_params=llm_params)
            except Exception as _e:
                logger.warning("Failed to pre-build agent for subagent tool name lookup: %s", _e)
            subagent_display_map = engine.get_subagent_display_name_map(
                preset_id, model_id=model_id or "", llm_params=llm_params,
            )
            subagent_tool_names = set(subagent_display_map.keys())
            from langgraph.types import Command

            agent = engine._get_or_build_agent(preset_id, model_id, llm_params=llm_params)
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
                stream_kwargs: dict[str, Any] = {"config": config, "version": "v2"}
                if engine._should_use_memory_context(preset_id):
                    from lc_agent.core.memory import AgentRuntimeContext, normalize_memory_user_id

                    stream_kwargs["context"] = AgentRuntimeContext(
                        user_id=normalize_memory_user_id(user.id if user else "anonymous"),
                    )
                async for event in agent.astream_events(
                    Command(resume=resume_value),
                    **stream_kwargs,
                ):
                    if _cancel_flags.get(thread_id):
                        yield stream_utils.format_sse_event("cancelled", {})
                        return

                    if await request.is_disconnected():
                        _cancel_flags[thread_id] = True
                        return

                    in_thinking = stream_utils.accumulate_display_state(
                        event, content_parts, tool_calls, in_thinking,
                        subagent_tool_names=subagent_tool_names,
                        thread_id=thread_id,
                        subagent_display_map=subagent_display_map,
                    )

                    for evt_type, evt_data in stream_utils.convert_stream_event(
                        event, subagent_tool_names=subagent_tool_names,
                    ):
                        if evt_type == "subagent_start":
                            tool_name = evt_data.get("name", "")
                            display_name = subagent_display_map.get(tool_name) or tool_name
                            sa_tid_pre = evt_data["tool_call_id"]
                            evt_data = {
                                **evt_data,
                                "name": display_name,
                                "sub_session_id": f"{thread_id}--sa--{sa_tid_pre}",
                            }
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
                                reqs = first_value["action_requests"]
                                if subagent_display_map:
                                    reqs = [
                                        {**r, "display_name": subagent_display_map.get(r.get("name", ""))}
                                        if r.get("name") in subagent_display_map else r
                                        for r in reqs
                                    ]
                                interrupt_payload["action_requests"] = reqs
                            if "review_configs" in first_value:
                                interrupt_payload["review_configs"] = first_value["review_configs"]
                        yield stream_utils.format_sse_event("interrupt", interrupt_payload)
                        interrupt_sent = True
            except Exception as e:
                print(f"[SSE] Failed to check interrupt state after resume: {e}")

            if isinstance(resume_value, dict):
                permanently_allow = resume_value.get("permanently_allow")
                if permanently_allow and hasattr(request.app.state, "permissions"):
                    # Only admin can permanently allow tools
                    if user and user.role == "admin":
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
