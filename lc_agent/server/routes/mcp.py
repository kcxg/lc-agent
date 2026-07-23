from fastapi import APIRouter, Depends, HTTPException, Request

from lc_agent.db.models_auth import User
from lc_agent.server.auth_middleware import get_current_user

router = APIRouter(tags=["mcp"])


def _serialize_server(server):
    return {
        "name": server.name,
        "type": server.type,
        "command": server.command,
        "url": server.url,
        "enabled": server.enabled,
        "status": server.status,
        "tools": server.tools,
        "tool_schemas": server.tool_schemas,
        "error": server.error,
    }


@router.get("/mcp")
def list_mcp_servers(
    request: Request,
    user: User = Depends(get_current_user),
):
    """List MCP servers with their status."""
    manager = getattr(request.app.state, "mcp_manager", None)
    if manager is None:
        return []
    return [_serialize_server(server) for server in manager.servers]


@router.post("/mcp/refresh")
async def refresh_all_mcp_servers(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Reconnect every enabled MCP server and reload its tool schemas."""
    manager = getattr(request.app.state, "mcp_manager", None)
    if manager is None:
        raise HTTPException(status_code=404, detail="MCP manager not found")
    return [_serialize_server(server) for server in await manager.refresh_all()]


@router.post("/mcp/{name}/refresh")
async def refresh_mcp_server(
    name: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Reconnect one enabled MCP server and reload its tool schemas."""
    manager = getattr(request.app.state, "mcp_manager", None)
    if manager is None:
        raise HTTPException(status_code=404, detail="MCP manager not found")
    server = manager.get_server(name)
    if server is None:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")
    if not server.enabled:
        raise HTTPException(status_code=409, detail=f"MCP server '{name}' is disabled")
    return _serialize_server(await manager.refresh_server(name))


@router.post("/mcp/{name}/toggle")
def toggle_mcp_server(
    name: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Toggle a MCP server's enabled state at runtime."""
    manager = getattr(request.app.state, "mcp_manager", None)
    if manager is None:
        raise HTTPException(status_code=404, detail="MCP manager not found")
    server = manager.get_server(name)
    if server is None:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")
    server.enabled = not server.enabled
    if not server.enabled:
        server.status = "disabled"
    else:
        has_session = name in manager._sessions
        if has_session:
            server.status = "connected"
        else:
            server.status = "disconnected"
    engine = getattr(request.app.state, "engine", None)
    if engine:
        engine._mcp_generation += 1
    return {"name": name, "enabled": server.enabled, "status": server.status}
