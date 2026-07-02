# lc_agent/tools/contrib_tools/get_time.py
from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from lc_agent.tools.registry import tool


@tool(name="get_current_time", group="utility", group_description="通用工具")
def get_current_time(
    timezone: Annotated[str, "IANA 时区名称，如 Asia/Shanghai、America/New_York、Europe/London、UTC"] = "Asia/Shanghai",
) -> str:
    """获取指定时区的当前日期和时间。"""
    try:
        tz = ZoneInfo(timezone)
    except (KeyError, ValueError):
        return f"错误: 无效的时区 '{timezone}'。请使用 IANA 时区格式，如 Asia/Shanghai、UTC。"
    now = datetime.now(tz)
    return f"{now.strftime('%Y-%m-%d %H:%M:%S')} ({timezone})"
