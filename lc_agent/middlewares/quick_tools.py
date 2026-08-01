"""QuickToolsMiddleware: bundle tools and an optional system prompt in one shot.

Use when you need to add a set of tools with associated system guidance to an agent
without writing a dedicated middleware class for each use case.
"""
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool


class QuickToolsMiddleware(AgentMiddleware):  # type: ignore[misc]
    """Bundle tools and an optional system prompt into a single middleware.

    Args:
        middleware_name: Middleware identifier (shown in traces and logs).
        tools: List of tools to inject into the agent.
        system_prompt: Optional text block to inject into the system message.
            Pass an empty string (default) to skip system prompt injection.
        prepend: If True, prepend the text block before existing content blocks
            instead of appending after them.

    Example::

        from lc_agent.middlewares import QuickToolsMiddleware
        from langchain_core.tools import tool

        @tool
        def greet(name: str) -> str:
            \"\"\"Say hello to someone.\"\"\"
            return f"Hello, {name}!"

        middleware.append(
            QuickToolsMiddleware(
                middleware_name="GreetMiddleware",
                tools=[greet],
                system_prompt="You have access to a `greet` tool. Use it when greeting users.",
            )
        )
    """

    def __init__(
        self,
        middleware_name: str,
        tools: list[BaseTool],
        system_prompt: str = "",
        *,
        prepend: bool = False,
    ) -> None:
        super().__init__()
        self._middleware_name = middleware_name
        self.tools = list(tools)
        self._system_prompt = system_prompt
        self._prepend = prepend

    @property
    def name(self) -> str:  # type: ignore[override]
        return self._middleware_name

    def _patched_system(self, existing: Any) -> Any:
        if not self._system_prompt:
            return existing
        if self._prepend:
            new_block = {"type": "text", "text": self._system_prompt}
            new_content = [new_block, *(existing.content_blocks if existing is not None else [])]
        else:
            new_block = {"type": "text", "text": f"\n\n{self._system_prompt}"}
            new_content = [*(existing.content_blocks if existing is not None else []), new_block]
        return SystemMessage(content_blocks=new_content)  # type: ignore[call-arg]

    def wrap_model_call(self, request: Any, handler: Any) -> Any:
        if not self._system_prompt:
            return handler(request)
        return handler(request.override(system_message=self._patched_system(request.system_message)))

    async def awrap_model_call(self, request: Any, handler: Any) -> Any:
        if not self._system_prompt:
            return await handler(request)
        return await handler(request.override(system_message=self._patched_system(request.system_message)))
