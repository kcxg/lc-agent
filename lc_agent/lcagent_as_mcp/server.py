"""low-level MCP Server：只实现 list_tools / call_tool 两个 handler。

不用 FastMCP 的原因见 docs/tasks/lcagent_as_mcp.md §3.1：
FastMCP 的价值是"从静态函数签名自动生成 inputSchema"，
lc-agent 的工具是数据库驱动的动态集合，没有静态函数可反射，该价值归零。
协议正确性、能力协商、错误处理、JSON-RPC 封装全部由官方 SDK 保证。
"""

from mcp import types
from mcp.server.lowlevel import Server

from lc_agent.lcagent_as_mcp import runner
from lc_agent.lcagent_as_mcp.tool_builder import (
    INVOKE_TOOL_NAME,
    LIST_TOOL_NAME,
    build_agent_directory,
    build_tools,
    list_exposable_presets,
    resolve_agent,
)

SERVER_NAME = "lc-agent"


def _text(message: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=message)]


def build_mcp_server(engine) -> Server:
    """构建 MCP server 实例。"""
    server = Server(SERVER_NAME)

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        # 每次实时查库：服务不重启，客户端重连即拿到最新工具描述（含 agent 快照）
        return await build_tools()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name == LIST_TOOL_NAME:
            # 目录工具：实时查库，新增 agent 立即可见，客户端无需重连
            presets = await list_exposable_presets()
            directory = build_agent_directory(presets)
            return _text(directory or "（当前没有可调用的 agent）")

        if name != INVOKE_TOOL_NAME:
            return _text(f"错误: 未知工具 {name}")

        agent_name = arguments.get("agent_name") if isinstance(arguments, dict) else None
        prompt = arguments.get("prompt") if isinstance(arguments, dict) else None
        if not isinstance(agent_name, str) or not agent_name.strip():
            return _text("错误: agent_name 参数必填且为非空字符串")
        if not isinstance(prompt, str) or not prompt.strip():
            return _text("错误: prompt 参数必填且为非空字符串")

        # 调用时重新查库：期间 agent 可能已被改动
        presets = await list_exposable_presets()
        preset = resolve_agent(presets, agent_name.strip())
        if preset is None:
            # 报错 + 最新目录：一次失败调用顺便完成发现，模型可立即纠错重试
            directory = build_agent_directory(presets)
            return _text(
                f"错误: agent「{agent_name}」不存在或不可调用。\n"
                f"当前可用 agent：\n{directory or '（无）'}"
            )

        output, error = await runner.run_agent_once(engine, preset.id, prompt)
        if error:
            return _text(f"错误: {error}")
        return _text(output or "（agent 无文本输出）")

    return server
