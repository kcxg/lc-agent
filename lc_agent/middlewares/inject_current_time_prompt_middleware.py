from typing import Any

from langchain_core.messages import SystemMessage

from lc_agent.middlewares.system_prompt import SystemPromptMiddleware


class InjectCurrentTimePromptMiddleware(SystemPromptMiddleware):  # type: ignore[misc]
    """Appends the current datetime as the final system-message content block."""

    def __init__(self, text: str, middleware_name: str, *, prepend: bool = False):
        super().__init__(text, middleware_name, prepend=prepend)

    @staticmethod
    def _get_current_time_text() -> str:
        import datetime

        now = datetime.datetime.now().astimezone()
        offset = now.strftime("%z")
        tz_display = f"UTC{offset[:3]}:{offset[3:]}" if offset else now.strftime("%Z") or "UTC"
        return (
            "<current_datetime>\n"
            f"Current date: {now.strftime('%Y-%m-%d')} ({tz_display}).\n"
            "</current_datetime>"
        )

    def _patched_system(self, existing: Any) -> Any:
        if self._prepend:
            new_block = {"type": "text", "text": self._get_current_time_text()}
            new_content = [new_block, *(existing.content_blocks if existing is not None else [])]
        else:
            new_block = {"type": "text", "text": f"\n\n{self._get_current_time_text()}"}
            new_content = [*(existing.content_blocks if existing is not None else []), new_block]
        return SystemMessage(content_blocks=new_content)  # type: ignore[call-arg]


inject_current_time_prompt_middleware = InjectCurrentTimePromptMiddleware(text="", middleware_name="InjectCurrentTimePromptMiddleware", prepend=False)