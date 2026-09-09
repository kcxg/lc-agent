"""把 lcagent_as_mcp 挂到 FastAPI 上。

处理 docs/tasks/lcagent_as_mcp.md §3.2 的三个坑：
1. low-level 自建 ASGI 入口，不存在 FastMCP 的 /mcp/mcp 路径重复问题
2. 子 app 的 lifespan 不会自动执行 → 包一层 lifespan_context，手动跑 session manager
3. 本函数必须在 mount_static_files(app) 之前调用，否则被 "/" 静态文件吃掉

stateless_http：不需要 SSE 长连接（不做实时推送，§1 非目标），
每次 POST 独立处理，json_response=True 直接回 JSON。
"""

from contextlib import asynccontextmanager

from starlette.routing import Mount, Route
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from lc_agent.lcagent_as_mcp.config import endpoint_path, is_enabled
from lc_agent.lcagent_as_mcp.server import build_mcp_server
from lc_agent.utils.loggers import server_logger


class _McpAsgiEndpoint:
    """裸 ASGI 端点包装。Route 要求非函数端点（函数会被包成 Request 风格）。"""

    def __init__(self, session_manager: StreamableHTTPSessionManager):
        self.session_manager = session_manager

    async def __call__(self, scope, receive, send):
        # Streamable HTTP 单端点：POST 请求 / GET SSE / DELETE 终止
        await self.session_manager.handle_request(scope, receive, send)


def mount_lcagent_as_mcp(app, engine) -> bool:
    """启用时把 MCP 端点挂到 app 上，返回是否已挂载。

    未在 config.jsonc 里显式配置 lcagent_as_mcp.enabled=true 时什么都不做——
    本期端点不鉴权，默认开启等于把 agent 能力暴露给任何能访问端口的人。
    """
    if not is_enabled():
        return False

    mcp_server = build_mcp_server(engine)
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        json_response=True,
        stateless=True,
    )

    async def asgi_endpoint(scope, receive, send):
        # Streamable HTTP 单端点：POST 请求 / GET SSE / DELETE 终止
        await session_manager.handle_request(scope, receive, send)

    # 坑 2：session manager 必须在 lifespan 里 run()。
    # 包一层现有 lifespan，不侵入 LcAgentApp._lifespan 的内部逻辑。
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan_with_mcp(inner_app):
        async with session_manager.run():
            async with original_lifespan(inner_app):
                yield

    app.router.lifespan_context = lifespan_with_mcp

    # 坑 3：调用方保证在 mount_static_files 之前调用本函数
    path = endpoint_path()
    asgi_endpoint = _McpAsgiEndpoint(session_manager)
    # Starlette 的 Mount("/mcp") 正则是 ^/mcp/(...)$，匹配不到裸路径 /mcp！
    # 客户端（WorkBuddy 等）POST 的正是裸 /mcp，必须补一条精确匹配的 Route
    app.router.routes.append(
        Route(path, endpoint=asgi_endpoint, methods=["GET", "POST", "DELETE"], name="lcagent_as_mcp")
    )
    app.router.routes.append(
        Mount(path, app=asgi_endpoint, name="lcagent_as_mcp_stream")
    )
    server_logger.warning(
        "lcagent_as_mcp 已启用: MCP 端点 %s（本期无鉴权，服务只应监听 127.0.0.1）", path
    )
    return True
