# lc_agent/tools/builtin_tools/__init__.py
# Tools registered with group="__builtin__" are always injected into every agent,
# regardless of allowed_tool_groups.
import lc_agent.tools.builtin_tools.get_system_info  # noqa: F401
