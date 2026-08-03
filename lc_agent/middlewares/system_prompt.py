"""SystemPromptMiddleware: injects a text block as a system message content block.

General-purpose middleware for adding any text to the agent's system prompt
without modifying other content blocks already present.
"""
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import SystemMessage


class SystemPromptMiddleware(AgentMiddleware):  # type: ignore[misc]
    """Injects a text block as a separate system message content block."""

    def __init__(self, text: str, middleware_name: str, *, prepend: bool = False) -> None:
        super().__init__()
        self._text = text
        self._middleware_name = middleware_name
        self._prepend = prepend

    @property
    def name(self) -> str:  # type: ignore[override]
        return self._middleware_name

    def _patched_system(self, existing: Any) -> Any:
        if self._prepend:
            new_block = {"type": "text", "text": self._text}
            new_content = [new_block, *(existing.content_blocks if existing is not None else [])]
        else:
            new_block = {"type": "text", "text": f"\n\n{self._text}"}
            new_content = [*(existing.content_blocks if existing is not None else []), new_block]
        return SystemMessage(content_blocks=new_content)  # type: ignore[call-arg]

    def wrap_model_call(self, request: Any, handler: Any) -> Any:
        return handler(request.override(system_message=self._patched_system(request.system_message)))

    async def awrap_model_call(self, request: Any, handler: Any) -> Any:
        return await handler(request.override(system_message=self._patched_system(request.system_message)))
