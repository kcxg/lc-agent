from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from lc_agent.core.auth import AuthService
from lc_agent.db.models_auth import User, UserAgentAccess
from lc_agent.server.auth_middleware import require_admin
from lc_agent.server.dependencies import get_db_session

router = APIRouter(prefix="/admin", tags=["admin"])


class CreateUserRequest(BaseModel):
    username: str


class SetAgentsRequest(BaseModel):
    agent_ids: list[str]


def _get_auth_service(request: Request) -> AuthService:
    svc = getattr(request.app.state, "auth_service", None)
    if svc is None:
        raise HTTPException(status_code=500, detail="Auth not configured")
    return svc


@router.get("/users")
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(User).order_by(User.created_at))
    users = result.scalars().all()
    return [
        {"id": u.id, "username": u.username, "role": u.role, "created_at": u.created_at.isoformat()}
        for u in users
    ]


@router.post("/users", status_code=201)
async def create_user(
    body: CreateUserRequest,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    auth_service = _get_auth_service(request)

    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="用户名已存在")

    password = auth_service.generate_random_password()
    user = User(
        username=body.username,
        password_hash=auth_service.hash_password(password),
        role="user",
    )
    db.add(user)

    access = UserAgentAccess(user_id=user.id, agent_id="__chat__")
    db.add(access)

    await db.commit()
    await db.refresh(user)

    return {"id": user.id, "username": user.username, "role": user.role, "password": password}


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    await db.execute(delete(UserAgentAccess).where(UserAgentAccess.user_id == user_id))
    await db.delete(user)
    await db.commit()


@router.put("/users/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    auth_service = _get_auth_service(request)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    password = auth_service.generate_random_password()
    user.password_hash = auth_service.hash_password(password)
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"password": password}


@router.get("/users/{user_id}/agents")
async def get_user_agents(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(UserAgentAccess.agent_id).where(UserAgentAccess.user_id == user_id))
    agent_ids = [row[0] for row in result.all()]
    return {"agent_ids": agent_ids}


@router.put("/users/{user_id}/agents")
async def set_user_agents(
    user_id: str,
    body: SetAgentsRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    await db.execute(delete(UserAgentAccess).where(UserAgentAccess.user_id == user_id))
    for agent_id in body.agent_ids:
        db.add(UserAgentAccess(user_id=user_id, agent_id=agent_id))
    await db.commit()
    return {"agent_ids": body.agent_ids}
