"""服务用户：非真人发起的调用（当前即 MCP 调用）统一归属到它。

见 docs/tasks/lcagent_as_mcp.md §3.5——角色恒为 user，绝不能是 admin。
原因：MCP 端点不鉴权，服务用户一旦是 admin，任何能访问端口的人就等于拿到了管理员权限。
"""

import secrets

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lc_agent.config import get_config, get_config_value
from lc_agent.db.models_auth import User
from lc_agent.utils.loggers import server_logger

DEFAULT_SERVICE_USERNAME = "lcagent_as_mcp_user"


def service_username() -> str:
    return str(get_config_value(get_config(), "auth.service_username", DEFAULT_SERVICE_USERNAME))


async def ensure_service_user(db: AsyncSession) -> User:
    """确保服务用户存在并返回；不存在则自动创建。

    密码是随机串且从不返回，因此该账号实际不可登录。
    """
    username = service_username()
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    password_hash = bcrypt.hashpw(
        secrets.token_urlsafe(32).encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    user = User(username=username, password_hash=password_hash, role="user")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    server_logger.info("已自动创建服务用户 %s（role=user，不可登录）", username)
    return user
