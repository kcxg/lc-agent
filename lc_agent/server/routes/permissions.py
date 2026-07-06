from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from lc_agent.core.permissions import PermissionsService
from lc_agent.db.models_auth import User
from lc_agent.server.auth_middleware import get_current_user, require_admin

router = APIRouter(tags=["permissions"])


def _get_permissions(request: Request) -> PermissionsService:
    return request.app.state.permissions


class AllowToolRequest(BaseModel):
    tool_name: str


class SetAllowlistRequest(BaseModel):
    tool_allowlist: list[str]


@router.get("/permissions")
def get_permissions(
    request: Request,
    user: User = Depends(get_current_user),
):
    svc = _get_permissions(request)
    return {"version": 1, "tool_allowlist": svc.get_allowlist()}


@router.post("/permissions/allow")
def allow_tool(
    body: AllowToolRequest,
    request: Request,
    admin: User = Depends(require_admin),
):
    svc = _get_permissions(request)
    svc.allow_tool(body.tool_name)
    return {"ok": True, "tool_allowlist": svc.get_allowlist()}


@router.post("/permissions/remove")
def remove_tool(
    body: AllowToolRequest,
    request: Request,
    admin: User = Depends(require_admin),
):
    svc = _get_permissions(request)
    svc.remove_tool(body.tool_name)
    return {"ok": True, "tool_allowlist": svc.get_allowlist()}


@router.put("/permissions")
def set_permissions(
    body: SetAllowlistRequest,
    request: Request,
    admin: User = Depends(require_admin),
):
    svc = _get_permissions(request)
    svc.set_allowlist(body.tool_allowlist)
    return {"ok": True, "tool_allowlist": svc.get_allowlist()}
