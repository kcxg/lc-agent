import platform
from typing import Any

from langchain_core.messages import SystemMessage
from nb_langchain_agentskills import render_shell_fact, render_shell_guidance, resolve_shell

from lc_agent.middlewares.system_prompt import SystemPromptMiddleware
from lc_agent.tools.system_tools._config import get_shell_preference


def _get_user_os_text() -> str:
    """Build the <user_os> block: server OS + the shell commands actually run in.

    Both halves come from ``nb_langchain_agentskills.resolve_shell`` — the very
    resolver ``run_command`` / ``start_background_process`` execute through — so
    the facts and the syntax guidance handed to the agent cannot drift away from
    what actually runs.
    """
    shell_info = resolve_shell(get_shell_preference())

    os_name = platform.system()
    try:
        os_version = platform.version() if os_name == "Linux" else platform.release()
        os_info = f"{os_name} {os_version} ({render_shell_fact(shell_info)})"
    except Exception:
        os_info = f"{os_name} ({render_shell_fact(shell_info)})"

    return f"<user_os>\n**OS**: {os_info}\n{render_shell_guidance(shell_info)}\n</user_os>"


class UserOsMiddleware(SystemPromptMiddleware):  # type: ignore[misc]
    """Appends the <user_os> block as the final system-message content block."""

    def __init__(self, text: str, middleware_name: str, *, prepend: bool = False):
        super().__init__(text, middleware_name, prepend=prepend)

    def _patched_system(self, existing: Any) -> Any:
        if self._prepend:
            new_block = {"type": "text", "text": _get_user_os_text()}
            new_content = [new_block, *(existing.content_blocks if existing is not None else [])]
        else:
            new_block = {"type": "text", "text": f"\n\n{_get_user_os_text()}"}
            new_content = [*(existing.content_blocks if existing is not None else []), new_block]
        return SystemMessage(content_blocks=new_content)  # type: ignore[call-arg]


user_os_middleware = UserOsMiddleware(text="", middleware_name="UserOsMiddleware", prepend=False)
