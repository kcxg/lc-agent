from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel

from lc_agent.server.auth import (
    clear_auth_cookie,
    get_auth_config,
    is_request_authenticated,
    set_auth_cookie,
    validate_admin_credentials,
)

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.get("/auth/me")
async def auth_state(request: Request):
    settings = get_auth_config(request.app.state.config)
    authenticated = is_request_authenticated(request)
    username = settings.admin_username if authenticated and settings.enabled else ""
    return {"authenticated": authenticated, "username": username}


@router.post("/auth/login")
async def login(body: LoginRequest, request: Request, response: Response):
    settings = get_auth_config(request.app.state.config)
    if not settings.enabled:
        return {"authenticated": True, "username": ""}
    if not validate_admin_credentials(settings, body.username, body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    set_auth_cookie(response, settings)
    return {"authenticated": True, "username": settings.admin_username}


@router.post("/auth/logout")
async def logout(request: Request, response: Response):
    settings = get_auth_config(request.app.state.config)
    clear_auth_cookie(response, settings)
    return {"authenticated": False}
