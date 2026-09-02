# lc_agent/__init__.py
"""lc_agent — LangChain Agent framework with built-in Web UI."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("lc-agent-app")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

from lc_agent.app import LcAgentApp
from lc_agent.config import (
    get_app_name,
    get_config,
    get_database_url,
    load_config,
    set_config_path,
)
from lc_agent.core.traced_llm import (
    create_traced_chat_openai,
    create_traced_openai_http_client,
)
from lc_agent.tools.registry import ToolRegistry, tool

__all__ = [
    "LcAgentApp",
    "load_config",
    "set_config_path",
    "get_config",
    "get_app_name",
    "get_database_url",
    "create_traced_chat_openai",
    "create_traced_openai_http_client",
    "ToolRegistry",
    "tool",
    "__version__",
]
