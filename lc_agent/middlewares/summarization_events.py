"""Summarization visibility middleware.

Wraps langchain's SummarizationMiddleware so context compression is visible
to the frontend: emits start/done/failed custom events through LangChain's
custom event system, which the SSE layer forwards to the client.

Events:
- ``summarization_start``: compression triggered (frontend shows animation).
- ``summarization_done``: compression succeeded, with counts.
- ``summarization_failed``: compression skipped or errored, with reason
  (frontend shows a soft notice, conversation continues normally).

The wrapped middleware still performs the actual summarization; this class
only adds observability. All event dispatches are best-effort and never
break the summarization flow.
"""

import logging
from typing import Any

from langchain.agents.middleware.summarization import SummarizationMiddleware
from langgraph.runtime import Runtime

logger = logging.getLogger(__name__)


def _emit(name: str, data: dict) -> None:
    """Best-effort custom event dispatch (sync, mirrors tool event style)."""
    try:
        from langchain_core.callbacks import dispatch_custom_event
        dispatch_custom_event(name, data)
    except Exception:
        pass


async def _aemit(name: str, data: dict) -> None:
    """Best-effort custom event dispatch (async)."""
    try:
        from langchain_core.callbacks import adispatch_custom_event
        await adispatch_custom_event(name, data)
    except Exception:
        pass


class NotifyingSummarizationMiddleware(SummarizationMiddleware):
    """SummarizationMiddleware that notifies the frontend via custom events."""

    def before_model(self, state, runtime: Runtime) -> dict[str, Any] | None:
        messages = state["messages"]
        total_tokens = self.token_counter(messages)
        if not self._should_summarize(messages, total_tokens):
            return None
        cutoff_index = self._determine_cutoff_index(messages)
        if cutoff_index <= 0:
            return None
        messages_to_summarize, _ = self._partition_messages(messages, cutoff_index)
        _emit("summarization_start", {
            "summarized_count": len(messages_to_summarize),
            "total_count": len(messages),
        })
        try:
            result = super().before_model(state, runtime)
        except Exception as e:
            _emit("summarization_failed", {"reason": str(e)[:200]})
            raise
        if result is None:
            _emit("summarization_failed", {"reason": "cutoff unavailable, skipped"})
        else:
            _emit("summarization_done", {
                "summarized_count": len(messages_to_summarize),
                "kept_count": len(messages) - cutoff_index,
            })
        return result

    async def abefore_model(self, state, runtime: Runtime) -> dict[str, Any] | None:
        messages = state["messages"]
        total_tokens = self.token_counter(messages)
        if not self._should_summarize(messages, total_tokens):
            return None
        cutoff_index = self._determine_cutoff_index(messages)
        if cutoff_index <= 0:
            return None
        messages_to_summarize, _ = self._partition_messages(messages, cutoff_index)
        await _aemit("summarization_start", {
            "summarized_count": len(messages_to_summarize),
            "total_count": len(messages),
        })
        try:
            result = await super().abefore_model(state, runtime)
        except Exception as e:
            await _aemit("summarization_failed", {"reason": str(e)[:200]})
            raise
        if result is None:
            await _aemit("summarization_failed", {"reason": "cutoff unavailable, skipped"})
        else:
            await _aemit("summarization_done", {
                "summarized_count": len(messages_to_summarize),
                "kept_count": len(messages) - cutoff_index,
            })
        return result
