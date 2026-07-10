# lc_agent/tools/contrib_tools/ask_user_tool.py
from typing import Annotated

from langgraph.types import interrupt

from lc_agent.tools.registry import tool


@tool(name="ask_user", group="utility", group_description="通用工具")
def ask_user(
    question: Annotated[
        str,
        (
            "向用户展示的问题文本。应清晰简洁，直接表达你需要用户提供的信息或做出的决定。"
            "示例：'您希望报告覆盖哪个时间段？' / '确认要删除这条记录吗？'"
        ),
    ],
    options: Annotated[
        list[str] | None,
        (
            "候选选项列表，将按 A/B/C/D 顺序展示给用户点选。"
            "仅在答案范围有限且可枚举时提供（建议 2~6 项）；若用户需要自由填写则不传。"
            "示例：['本月', '本季度', '自定义时间段']"
        ),
    ] = None,
    allow_multiple: Annotated[
        bool,
        (
            "是否允许用户同时勾选多个选项。True=多选，False=单选（默认）。"
            "仅在 options 不为空时有意义。场景示例：让用户勾选多个偏好标签时传 True。"
        ),
    ] = False,
    allow_free_input: Annotated[
        bool,
        (
            "是否允许用户在选项之外输入自定义文字。True（默认）=点选与自由输入均可；"
            "False=强制仅能从 options 中点选，适合需要受控输入的场景。"
        ),
    ] = True,
) -> str:
    """向用户提问并阻塞等待回答。调用后当前执行将暂停，用户提交答案后自动继续。

    当你需要以下情形时使用此工具：
    - 关键信息缺失，无法从上下文推断，必须由用户补充（自由输入，不传 options）
    - 需要用户从有限方案中做单选或多选（传 options）
    - 需要用户确认一个不可逆操作（如删除、发送）

    禁止在以下情况调用：
    - 你已能从用户先前的消息中推断出答案，不应重复询问
    - 仅用于展示信息或状态（直接在回复中说明即可，无需调用此工具）
    - 在同一轮任务中连续多次调用，应将所有问题合并为一次调用

    返回值：用户回答的原始文本；若传了 options，返回内容还会附带选项 ID 与文本的对照表（格式：A=选项文本）。
    """
    payload: dict = {
        "type": "ask_user",
        "question": question,
        "allow_multiple": allow_multiple,
        "allow_free_input": allow_free_input,
    }
    option_map: dict[str, str] = {}
    if options:
        payload["options"] = [
            {"id": chr(65 + i), "label": opt}
            for i, opt in enumerate(options)
        ]
        option_map = {chr(65 + i): opt for i, opt in enumerate(options)}

    raw_answer: str = interrupt(payload)

    if not option_map:
        return raw_answer

    mapping_lines = "\n".join(f"{k}={v}" for k, v in option_map.items())
    return f"用户回答: {raw_answer}\n选项对照:\n{mapping_lines}"
