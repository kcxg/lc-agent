"""lcagent_as_mcp 的配置读取。"""

from lc_agent.config import get_config, get_config_value

DEFAULT_PATH = "/mcp"


def is_enabled() -> bool:
    """默认关闭。

    该端点本期不鉴权，一旦默认开启就等于把 agent 能力暴露给任何能访问端口的人，
    所以必须由用户在 config.jsonc 里显式打开。
    """
    return bool(get_config_value(get_config(), "lcagent_as_mcp.enabled", False))


def endpoint_path() -> str:
    return str(get_config_value(get_config(), "lcagent_as_mcp.path", DEFAULT_PATH))
