"""Internal Agent execution service shared by chat and automation."""

import time
from dataclasses import dataclass
from typing import Any

from lc_agent.core.engine import AgentEngine
from lc_agent.core.http_trace import (
    HttpTraceCollector,
    bind_http_trace_collector,
    init_subagent_collector_registry,
    reset_http_trace_collector,
)
from lc_agent.server import persistence, stream_utils
from lc_agent.server.subagent_tracker import SubAgentRunTracker


@dataclass
class AgentRunResult:
    error: str | None = None
    interrupted: bool = False


class AgentRunService:
    """Consume one Agent stream and persist its complete UI execution record."""

    def __init__(self, engine: AgentEngine, db_url: str):
        self.engine = engine
        self.db_url = db_url

    async def run(
        self,
        *,
        session_id: str,
        prompt: str,
        preset_id: str,
        user_id: str,
        model_id: str = "",
        llm_params: dict[str, Any] | None = None,
    ) -> AgentRunResult:
        if not self.engine._preset_exists(preset_id):
            return AgentRunResult(error=f"Agent 不存在: {preset_id}")

        content = [{"type": "text", "text": prompt}]
        tool_calls: list[dict[str, Any]] = []
        usage_rounds: list[dict[str, Any]] = []
        content_parts: list[str] = []
        active_subagent_tool_call_ids: set[str] = set()
        in_thinking = False
        stream_start_time = time.time()
        round_start_time = stream_start_time

        try:
            await persistence.save_ui_message(
                self.db_url,
                session_id,
                "user",
                content,
            )
            self.engine._get_or_build_agent(preset_id, model_id, llm_params=llm_params)
            display_map = self.engine.get_subagent_display_name_map(
                preset_id, model_id=model_id, llm_params=llm_params,
            )
            tool_names = self.engine.get_subagent_tool_names(
                preset_id, model_id=model_id, llm_params=llm_params,
            )
            tracker = SubAgentRunTracker(
                db_url=self.db_url,
                parent_thread_id=session_id,
                user_id=user_id,
                subagent_display_map=display_map,
                tool_calls=tool_calls,
            )
            init_subagent_collector_registry()
            trace_collector = HttpTraceCollector(provider=None, model=model_id or None)
            trace_token = bind_http_trace_collector(trace_collector)
            from lc_agent.tools.system_tools._file_change_tracker import bind_session_for_file_tracking

            file_token = bind_session_for_file_tracking(session_id)
            try:
                async for event in self.engine.chat_stream(
                    content,
                    session_id,
                    preset_id,
                    model_id=model_id,
                    llm_params=llm_params,
                    user_id=user_id,
                ):
                    in_thinking = stream_utils.accumulate_display_state(
                        event,
                        content_parts,
                        tool_calls,
                        in_thinking,
                        subagent_tool_names=tool_names,
                        thread_id=session_id,
                        subagent_display_map=display_map,
                        active_subagent_tool_call_ids=active_subagent_tool_call_ids,
                    )
                    for event_type, payload in stream_utils.convert_stream_event(
                        event,
                        subagent_tool_names=tool_names,
                        subagent_display_map=display_map,
                        active_subagent_tool_call_ids=active_subagent_tool_call_ids,
                    ):
                        if event_type == "subagent_start":
                            tool_call_id = payload.get("tool_call_id")
                            if isinstance(tool_call_id, str):
                                active_subagent_tool_call_ids.add(tool_call_id)
                        elif event_type == "subagent_done":
                            tool_call_id = payload.get("tool_call_id")
                            if isinstance(tool_call_id, str):
                                active_subagent_tool_call_ids.discard(tool_call_id)
                        elif event_type == "file_change":
                            await persistence.save_file_change(
                                self.db_url,
                                payload.get("session_id", session_id),
                                payload.get("file_path", ""),
                                payload.get("change_type", ""),
                                old_string=payload.get("old_string"),
                                new_string=payload.get("new_string"),
                                tool_call_id=payload.get("tool_call_id"),
                                move_destination=payload.get("move_destination"),
                            )
                        elif event_type == "file_change_git_snapshot":
                            await persistence.save_git_base_hash(
                                self.db_url,
                                payload.get("session_id", session_id),
                                payload.get("git_base_hash", ""),
                            )
                        tracker.handle_event(event_type, payload)

                    before = len(usage_rounds)
                    stream_utils.accumulate_usage(event, usage_rounds)
                    if len(usage_rounds) > before:
                        usage_rounds[-1]["duration_ms"] = int((time.time() - round_start_time) * 1000)
                        round_start_time = time.time()
            finally:
                if in_thinking:
                    content_parts.append("<!--THINK_END-->")
                from lc_agent.tools.system_tools._file_change_tracker import reset_session_for_file_tracking

                reset_session_for_file_tracking(file_token)
                reset_http_trace_collector(trace_token)

            await tracker.drain()
            traces = trace_collector.snapshot()
            if content_parts or tool_calls or usage_rounds or traces:
                await persistence.save_ui_message(
                    self.db_url,
                    session_id,
                    "assistant",
                    [{"type": "text", "text": "".join(content_parts)}],
                    tool_calls=tool_calls or None,
                    usage={
                        "rounds": usage_rounds,
                        "tool_call_count": len(tool_calls),
                        "total_duration_ms": int((time.time() - stream_start_time) * 1000),
                    },
                    http_traces=traces or None,
                )
            await persistence.increment_session_message_count(self.db_url, session_id)
            try:
                agent = self.engine._get_or_build_agent(preset_id, model_id, llm_params=llm_params)
                config = {"configurable": {"thread_id": session_id}, "recursion_limit": self.engine.recursion_limit}
                state = await agent.aget_state(config)
                if any(task.interrupts for task in (state.tasks or ())):
                    return AgentRunResult(
                        error="任务需要人工审批，自动化执行无法继续",
                        interrupted=True,
                    )
            except Exception:
                # Graphs compiled without a checkpointer cannot expose interrupt state.
                # The completed stream remains a successful run in that case.
                pass
            return AgentRunResult()
        except Exception as exc:
            return AgentRunResult(error=str(exc))
