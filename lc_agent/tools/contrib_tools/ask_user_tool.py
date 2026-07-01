# lc_agent/tools/contrib_tools/ask_user_tool.py
from typing import Annotated

from langgraph.types import interrupt

from lc_agent.tools.registry import tool


@tool(name="ask_user", group="utility", group_description="通用工具")
def ask_user(
    question: Annotated[str, "要问用户的问题"],
    options: Annotated[list[str] | None, "预设选项列表，展示为 A/B/C/D 供用户点选"] = None,
    allow_multiple: Annotated[bool, "是否允许用户同时选择多个选项"] = False,
    allow_free_input: Annotated[bool, "是否允许用户输入自定义文字"] = True,
) -> str:
    """向用户提问并等待回复。支持自由文本、单选列表、多选列表、或列表+自由输入混合模式。"""
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
