"""查库 → 固定 2 个 MCP 工具（目录 + 调用）。

暴露过滤、目录数据、工具描述与 inputSchema 全部在这里，
设计见 docs/tasks/lcagent_as_mcp_two_tools.md。

固定 2 个工具（`list_lca_agents` / `invoke_lca_agent`）：
工具数不随 agent 数增长，新增 agent 不需要 MCP 客户端重连，
外部 agent 通过目录工具即可发现。

每次 `tools/list` 请求都重新执行：不做缓存，
`invoke_lca_agent` 的描述里嵌入当次查询的 agent 快照，
列表非最新时以目录工具为准。
"""

from html import escape

from mcp import types
from sqlalchemy import select

from lc_agent.db.engine import get_business_async_session
from lc_agent.db.models import AgentPresetDB

# 固定两个工具名
LIST_TOOL_NAME = "list_lca_agents"
INVOKE_TOOL_NAME = "invoke_lca_agent"


async def list_exposable_presets() -> list[AgentPresetDB]:
    """当前允许通过 MCP 调用的 agent（实时查库，无缓存）。

    唯一过滤：`can_be_mcp == True`（与内部 task 委派的
    `can_be_subagent` 独立，委派描述共用
    `default_delegation_description`）。
    不再检查工具组是否含 file_write / command：
    勾选即代表用户显式授权对外暴露其全部能力。
    """
    db = get_business_async_session()
    try:
        result = await db.execute(select(AgentPresetDB))
        presets = list(result.scalars().all())
    finally:
        await db.close()

    return [p for p in presets if getattr(p, "can_be_mcp", False)]

def delegation_description(preset: AgentPresetDB) -> str:
    """单个 agent 的委派描述，空时兜底。"""
    description = (preset.default_delegation_description or "").strip()
    if description:
        return description
    display = preset.display_name or preset.name
    return f"调用 lc-agent 的「{display}」agent 处理任务"


def build_agent_directory(presets: list[AgentPresetDB]) -> str:
    """agent 目录 XML，供目录工具返回、工具描述与错误信息复用。"""
    if not presets:
        return "<agents />"
    items = "\n".join(
        "  <agent>\n"
        f"    <agent_name>{escape(preset.name)}</agent_name>\n"
        f"    <delegation_description>{escape(delegation_description(preset))}</delegation_description>\n"
        "  </agent>"
        for preset in presets
    )
    return f"<agents>\n{items}\n</agents>"


def resolve_agent(
    presets: list[AgentPresetDB], agent_name: str
) -> AgentPresetDB | None:
    """按 agent 名精确匹配目标。"""
    for preset in presets:
        if preset.name == agent_name:
            return preset
    return None


def _invoke_description(agent_directory: str) -> str:
    """生成 invoke_lca_agent 面向调用方的工具描述。

    只有 agent 列表保留 XML 标签做清晰分割，
    外层用纯文本 + 空行分段，避免标签过多。
    """
    return (
        "委派指定的 agent 完成任务并返回结果。当需要把子任务交给下方列表中的某个专用 agent 时调用。\n"
        "\n"
        "可用 agent 列表（快照，可能非最新；找不到目标时先调用 list_lca_agents 获取最新列表）：\n"
        f"{agent_directory}\n"
        "\n"
        "prompt 写作要求：\n"
        "- 目标 agent 看不到你的对话上下文，任务必须自包含。\n"
        "- 写清背景、目标和期望结果。\n"
        "- 将必要的文件路径、数据和术语直接写入 prompt。\n"
        "- 说明期望输出的内容与格式。"
    )


async def build_tools() -> list[types.Tool]:
    """生成固定的 2 个 MCP 工具（实时查库，invoke 描述嵌当次快照）。"""
    presets = await list_exposable_presets()
    snapshot = build_agent_directory(presets)
    return [
        types.Tool(
            name=LIST_TOOL_NAME,
            description=(
                "实时列出当前可通过 invoke_lca_agent 调用的全部 agent 的名字和委派描述。"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name=INVOKE_TOOL_NAME,
            description=_invoke_description(snapshot),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "要调用的 agent 名字。",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "发给该 agent 的自包含任务描述",
                    },
                },
                "required": ["agent_name", "prompt"],
            },
        ),
    ]
