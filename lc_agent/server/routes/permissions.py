from fastapi import APIRouter, Request
from pydantic import BaseModel

from lc_agent.core.permissions import PermissionsService

router = APIRouter(tags=["permissions"])


def _get_permissions(request: Request) -> PermissionsService:
    return request.app.state.permissions


class AllowToolRequest(BaseModel):
    tool_name: str


class SetAllowlistRequest(BaseModel):
    tool_allowlist: list[str]


@router.get("/permissions")
def get_permissions(request: Request):
    svc = _get_permissions(request)
    return {"version": 1, "tool_allowlist": svc.get_allowlist()}


@router.post("/permissions/allow")
def allow_tool(body: AllowToolRequest, request: Request):
    svc = _get_permissions(request)
    svc.allow_tool(body.tool_name)
    return {"ok": True, "tool_allowlist": svc.get_allowlist()}


@router.post("/permissions/remove")
def remove_tool(body: AllowToolRequest, request: Request):
    svc = _get_permissions(request)
    svc.remove_tool(body.tool_name)
    return {"ok": True, "tool_allowlist": svc.get_allowlist()}


@router.put("/permissions")
def set_permissions(body: SetAllowlistRequest, request: Request):
    svc = _get_permissions(request)
    svc.set_allowlist(body.tool_allowlist)
    return {"ok": True, "tool_allowlist": svc.get_allowlist()}
