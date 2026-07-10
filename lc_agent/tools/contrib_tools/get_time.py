# lc_agent/tools/contrib_tools/get_time.py
from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from lc_agent.tools.registry import tool


@tool(
    name="get_current_time",
    group="utility",
    group_description="通用工具",
    description=(
        "获取指定时区的当前实时日期和时间，返回格式为 'YYYY-MM-DD HH:MM:SS (时区名)'。"
        "当用户提问隐含或显含当前时间的情况下，必须先调用此工具获取准确时间后再回答，不可凭训练知识估算当前时间。"
        "触发场景示例：'现在几点' '今天几号' '今天星期几' '本月/这个月有什么' '今年/今天发生了什么' "
        "'最近/近期/当前的XX情况' '这周/本周计划' 以及任何需要知道当前日期才能正确作答的问题。"
        "禁止在以下情况调用：用户询问的是历史日期或固定时间点（此工具只返回当前实时时间）；"
        "同一轮任务中已获取过时间且时间精度不影响结果时，无需重复调用。"
    ),
)
def get_current_time(
    timezone: Annotated[
        str,
        "IANA 标准时区名称。示例：Asia/Shanghai（北京时间）、America/New_York（纽约）、Europe/London（伦敦）、UTC（协调世界时）。默认 Asia/Shanghai。",
    ] = "Asia/Shanghai",
) -> str:
    try:
        tz = ZoneInfo(timezone)
    except (KeyError, ValueError):
        return f"错误: 无效的时区 '{timezone}'。请使用 IANA 时区格式，如 Asia/Shanghai、UTC。"
    now = datetime.now(tz)
    return f"{now.strftime('%Y-%m-%d %H:%M:%S')} ({timezone})"
