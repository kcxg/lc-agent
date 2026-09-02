"""进程级配置单例：set_config_path 注册路径，get_config 惰性加载并缓存。

典型用法（应用入口，如 bfzs/main.py）::

    from lc_agent import LcAgentApp, set_config_path

    set_config_path("config.jsonc")   # 注册一次
    app = LcAgentApp()               # 不再传 config
    app.run()

框架内部任何地方可无参获取配置::

    from lc_agent.config import get_config, get_app_name, get_database_url
"""

import os
from pathlib import Path

from lc_agent.config.utils import (
    DEFAULT_APP_NAME,
    DEFAULT_DATABASE_URL,
    ENV_CONFIG_PATH,
    get_config_value,
)

_config: dict | None = None


def set_config_path(path: str) -> None:
    """注册配置文件路径（写入环境变量，进程内全局生效）。

    已加载的配置缓存会失效，下次 get_config() 按新路径重新加载。
    """
    file_path = Path(path).expanduser()
    if not file_path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")
    global _config
    _config = None
    os.environ[ENV_CONFIG_PATH] = str(file_path.resolve())


def set_config(config: dict) -> None:
    """直接注入配置对象（显式传入 dict 时同步写全局，全局持有同一引用）。"""
    global _config
    _config = config


def reset_config() -> None:
    """清空全局配置缓存（测试用）。"""
    global _config
    _config = None


def get_config() -> dict:
    """返回全局配置 dict（惰性加载：未注册时按搜索链加载并缓存）。

    返回的是同一份引用：运行时对它的修改立即对所有人可见。
    搜索链为显式路径 > LC_AGENT_CONFIG_PATH > ./config.jsonc > ~/.lc_agent/config.jsonc，
    全部未命中时 load_config 会 raise RuntimeError。
    """
    global _config
    if _config is None:
        from lc_agent.config.loader import load_config

        _config = load_config()
    return _config


def get_app_name() -> str:
    """无参读取 ui.app_name。"""
    return get_config_value(get_config(), "ui.app_name", DEFAULT_APP_NAME)


def get_database_url() -> str:
    """无参读取 database.url。"""
    return get_config_value(get_config(), "database.url", DEFAULT_DATABASE_URL)
