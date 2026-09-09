"""lc-agent 自身作为标准 MCP server 对外提供服务。

见 docs/tasks/lcagent_as_mcp.md。

⚠️ 与 `lc_agent/mcp/` 完全无关：那个是 lc-agent 作为 MCP **客户端**去连第三方服务器，
本包是 lc-agent 作为 MCP **服务端**给别人调用。两者职责相反，不要混用，
也不要复用 `server/routes/mcp.py`（那是 `/api/mcp` 管理接口）。
"""

from lc_agent.lcagent_as_mcp.mounting import mount_lcagent_as_mcp

__all__ = ["mount_lcagent_as_mcp"]
