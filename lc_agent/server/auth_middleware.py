from fastapi import Depends, HTTPException, Request
from sqlalchemy import select

from lc_agent.core.auth import AuthService
from lc_agent.db.engine import get_async_session
from lc_agent.db.models_auth import User

PUBLIC_PATHS = {
    "/api/auth/login",
    "/api/health",
    "/api/docs",
    "/api/openapi.json",
}


def _is_public(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    if not path.startswith("/api/"):
        return True
    return False


def _extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return request.query_params.get("token")


async def get_current_user(request: Request) -> User:
    """FastAPI dependency: extract and validate JWT, return User object."""
    auth_service: AuthService | None = getattr(request.app.state, "auth_service", None)
    if auth_service is None:
        raise HTTPException(status_code=500, detail="Auth not configured")

    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="认证失败")

    payload = auth_service.decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="认证失败")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="认证失败")

    db_url = request.app.state.config.get("database", {}).get("url", "sqlite+aiosqlite:///./lc_agent_data.db")
    db = get_async_session(db_url)
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=401, detail="认证失败")
        request.state.current_user = user
        return user
    finally:
        await db.close()


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency: require admin role."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    return user
