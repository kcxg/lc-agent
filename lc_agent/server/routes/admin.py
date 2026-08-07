from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lc_agent.db.models import ChatUiMessage, SessionMeta
from lc_agent.db.models_auth import User, UserAgentAccess
from lc_agent.server.auth_middleware import get_auth_service, require_admin
from lc_agent.server.dependencies import get_db_session
from lc_agent.utils.loggers import server_logger

router = APIRouter(prefix="/admin", tags=["admin"])


class CreateUserRequest(BaseModel):
    username: str


class SetAgentsRequest(BaseModel):
    agent_ids: list[str]


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
    auth_service = get_auth_service(request)

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

    access = UserAgentAccess(user_id=user.id, agent_id="chat")
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

    # Delete messages for user's sessions
    user_sessions = await db.execute(select(SessionMeta.id).where(SessionMeta.user_id == user_id))
    session_ids = [row[0] for row in user_sessions.all()]
    if session_ids:
        from sqlalchemy import delete as sa_delete
        await db.execute(sa_delete(ChatUiMessage).where(ChatUiMessage.session_id.in_(session_ids)))
        await db.execute(sa_delete(SessionMeta).where(SessionMeta.user_id == user_id))

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
    auth_service = get_auth_service(request)
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


# ---------------------------------------------------------------------------
# 数据清理 / 瘦身（参见 docs/adr/adr-001-data-cleanup.md）
# ---------------------------------------------------------------------------


class CleanupRequest(BaseModel):
    keep_days: int = Field(default=30, ge=1, description="保留最近 N 天的会话")
    skip_pinned: bool = Field(default=True, description="跳过置顶会话")
    skip_active: bool = Field(default=True, description="跳过当前活跃会话")
    active_session_ids: list[str] = Field(
        default_factory=list, description="当前活跃会话 ID 列表（前端传入）"
    )


async def _select_cleanup_sessions(
    db: AsyncSession,
    keep_days: int,
    skip_pinned: bool,
    skip_active: bool,
    active_session_ids: list[str],
) -> list[SessionMeta]:
    """查询符合清理条件的会话。

    注意：不排除 `--sa--` 子会话，按各自 updated_at 独立判断（ADR 决策）。
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
    stmt = select(SessionMeta).where(SessionMeta.updated_at < cutoff)
    if skip_pinned:
        stmt = stmt.where(SessionMeta.is_pinned.is_(False))
    if skip_active and active_session_ids:
        stmt = stmt.where(SessionMeta.id.notin_(active_session_ids))
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/cleanup/preview")
async def preview_cleanup(
    body: CleanupRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """预览清理影响范围，不执行删除。"""
    sessions = await _select_cleanup_sessions(
        db, body.keep_days, body.skip_pinned, body.skip_active, body.active_session_ids
    )
    session_ids = [s.id for s in sessions]

    msg_count = 0
    if session_ids:
        msg_result = await db.execute(
            select(func.count())
            .select_from(ChatUiMessage)
            .where(ChatUiMessage.session_id.in_(session_ids))
        )
        msg_count = int(msg_result.scalar_one())

    return {
        "would_delete_sessions": len(session_ids),
        "would_delete_messages": msg_count,
        "would_delete_threads": len(session_ids),
        "affected_session_ids": session_ids,
    }


@router.post("/cleanup")
async def cleanup_data(
    body: CleanupRequest,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """执行数据清理：先删 checkpoints，再在同一事务内删 ChatUiMessage 和 SessionMeta。

    删除顺序依据 ADR §4.1：先删 checkpoints，data 库删除失败时 checkpoints 仍可重建关联。
    ChatUiMessage 和 SessionMeta 同属 data 库，合并为同一事务避免孤儿消息（ADR §11.3）。
    checkpoints 与 data 分属不同 SQLite 文件无法跨库事务，中途失败已删部分不回滚（ADR §8）。
    """
    server_logger.info(
        "cleanup requested by user=%s keep_days=%d skip_pinned=%s skip_active=%s active=%d",
        admin.username,
        body.keep_days,
        body.skip_pinned,
        body.skip_active,
        len(body.active_session_ids),
    )

    sessions = await _select_cleanup_sessions(
        db, body.keep_days, body.skip_pinned, body.skip_active, body.active_session_ids
    )
    session_ids = [s.id for s in sessions]

    # 清理前统计总数，用于计算 kept_sessions（空列表与非空分支共用）
    total_result = await db.execute(select(func.count()).select_from(SessionMeta))
    total_before = int(total_result.scalar_one())

    if not session_ids:
        server_logger.info("cleanup finished: no sessions matched, kept=%d", total_before)
        return {
            "deleted_sessions": 0,
            "deleted_messages": 0,
            "deleted_threads": 0,
            "kept_sessions": total_before,
            "errors": [],
        }

    engine = request.app.state.engine
    errors: list[dict[str, str]] = []
    deleted_threads = 0

    # 1. 删除 checkpoints（按 thread_id 逐个删除，调用 engine.reset_thread）
    for sid in session_ids:
        try:
            await engine.reset_thread(sid)
            deleted_threads += 1
        except Exception as exc:  # noqa: BLE001 - 记录错误继续，避免单个失败阻塞整体清理
            errors.append({"session_id": sid, "phase": "checkpoints", "error": str(exc)})

    # 2-3. 删除 ChatUiMessage 和 SessionMeta（同库，合并为同一事务避免孤儿消息）
    deleted_messages = 0
    deleted_sessions = 0
    try:
        msg_result = await db.execute(
            delete(ChatUiMessage).where(ChatUiMessage.session_id.in_(session_ids))
        )
        deleted_messages = int(msg_result.rowcount or 0)

        sess_result = await db.execute(
            delete(SessionMeta).where(SessionMeta.id.in_(session_ids))
        )
        deleted_sessions = int(sess_result.rowcount or 0)
        await db.commit()
    except Exception as exc:  # noqa: BLE001
        await db.rollback()
        errors.append({"phase": "data-cleanup", "error": str(exc)})
        server_logger.exception("data cleanup failed during delete: %s", exc)

    kept_sessions = max(total_before - deleted_sessions, 0)

    server_logger.info(
        "cleanup finished: deleted sessions=%d messages=%d threads=%d, kept=%d, errors=%d",
        deleted_sessions,
        deleted_messages,
        deleted_threads,
        kept_sessions,
        len(errors),
    )

    return {
        "deleted_sessions": deleted_sessions,
        "deleted_messages": deleted_messages,
        "deleted_threads": deleted_threads,
        "kept_sessions": kept_sessions,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# 数据库压缩 / VACUUM（瘦身后的文件回收，参见 docs/adr/adr-001-data-cleanup.md）
# ---------------------------------------------------------------------------


def _sqlite_path_from_url(url: str) -> str | None:
    """从 SQLAlchemy SQLite URL 中提取文件路径。"""
    prefixes = ("sqlite+aiosqlite:///", "sqlite:///")
    for prefix in prefixes:
        if url.startswith(prefix):
            return url[len(prefix):]
    return None


async def _vacuum_sqlite(path: str) -> tuple[bool, str | None]:
    """对单个 SQLite 文件执行 VACUUM，返回 (success, error_or_none)。"""
    import aiosqlite

    conn = None
    try:
        conn = await aiosqlite.connect(path)
        await conn.execute("VACUUM")
        await conn.commit()
        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    finally:
        if conn is not None:
            try:
                await conn.close()
            except Exception:
                pass


@router.post("/vacuum")
async def vacuum_databases(
    request: Request,
    admin: User = Depends(require_admin),
):
    """对 data 和 checkpoints 两个 SQLite 数据库执行 VACUUM，回收删除后的磁盘空间。

    VACUUM 会重建整个数据库文件，执行期间会短暂锁定数据库。大文件（数 GB）可能耗时较长，
    因此作为独立手动操作暴露，用户确认后再执行。
    """
    db_url = getattr(request.app.state, "db_url", None)
    checkpoint_path = getattr(request.app.state, "checkpoint_path", None)

    if not db_url or not checkpoint_path:
        raise HTTPException(status_code=500, detail="数据库路径未配置")

    data_path = _sqlite_path_from_url(db_url)
    if data_path is None:
        raise HTTPException(status_code=500, detail=f"无法解析 data 数据库 URL: {db_url}")

    server_logger.info("vacuum requested by user=%s", admin.username)

    data_ok, data_error = await _vacuum_sqlite(data_path)
    checkpoint_ok, checkpoint_error = await _vacuum_sqlite(checkpoint_path)

    server_logger.info(
        "vacuum finished: data_ok=%s checkpoint_ok=%s",
        data_ok,
        checkpoint_ok,
    )

    return {
        "data": {"success": data_ok, "path": data_path, "error": data_error},
        "checkpoints": {"success": checkpoint_ok, "path": checkpoint_path, "error": checkpoint_error},
    }
