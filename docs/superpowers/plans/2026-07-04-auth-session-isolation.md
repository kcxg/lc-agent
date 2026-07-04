# 用户认证 & 会话隔离 & 智能体授权 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 lc-agent 添加用户登录、会话隔离和 Admin 管理的智能体授权功能。

**Architecture:** JWT 认证 + SQLite 用户表 + user_id 外键隔离 sessions + M:N 表控制 Agent 访问权限。前端路由守卫 + Admin 管理页面。

**Tech Stack:** FastAPI, python-jose[cryptography], passlib[bcrypt], SQLModel, Vue 3, Element Plus, Pinia

---

## File Structure

### Backend — New Files
| File | Responsibility |
|------|---------------|
| `lc_agent/core/auth.py` | AuthService: JWT 生成/验证, 密码哈希, 用户查询 |
| `lc_agent/server/routes/auth.py` | 认证路由: login, me, change-password |
| `lc_agent/server/routes/admin.py` | Admin 路由: 用户 CRUD, Agent 授权分配 |
| `lc_agent/server/auth_middleware.py` | 认证中间件 + 依赖注入 (get_current_user, require_admin) |
| `lc_agent/db/models_auth.py` | User + UserAgentAccess 数据模型 |
| `lc_agent/db/migrations/versions/20260704_add_users.py` | Alembic 迁移脚本 |
| `tests/test_auth_service.py` | AuthService 单元测试 |
| `tests/test_routes_auth.py` | Auth API 集成测试 |
| `tests/test_routes_admin.py` | Admin API 集成测试 |
| `tests/test_session_isolation.py` | 会话隔离集成测试 |

### Backend — Modified Files
| File | Changes |
|------|---------|
| `lc_agent/config/schema.py` | 新增 AuthConfig |
| `lc_agent/db/models.py` | SessionMeta 加 user_id 字段 |
| `lc_agent/db/repository.py` | SessionRepository 加 user_id 过滤 |
| `lc_agent/server/app.py` | 注册新路由, 添加中间件 |
| `lc_agent/server/sse.py` | SSE 端点加认证 |
| `lc_agent/server/routes/sessions.py` | 注入 current_user, 过滤 |
| `lc_agent/server/routes/agents.py` | 过滤用户可见 Agent |
| `lc_agent/server/routes/permissions.py` | 限制 Admin |
| `lc_agent/app.py` | 启动时初始化 AuthService, 创建首个 Admin |

### Frontend — New Files
| File | Responsibility |
|------|---------------|
| `frontend/src/views/LoginView.vue` | 登录页面 |
| `frontend/src/views/AdminView.vue` | Admin 管理页面 |
| `frontend/src/stores/auth.ts` | 认证状态管理 |
| `frontend/src/api/auth.ts` | 认证 API 客户端 |
| `frontend/src/components/dialogs/ChangePasswordDialog.vue` | 修改密码弹窗 |

### Frontend — Modified Files
| File | Changes |
|------|---------|
| `frontend/src/router/index.ts` | 添加路由 + 守卫 |
| `frontend/src/api/http.ts` | 自动添加 Authorization header |
| `frontend/src/api/sse-client.ts` | SSE URL 拼接 token |
| `frontend/src/App.vue` or layout | Header 显示用户名 + 登出 |

---

## Task 1: 配置 Schema + 依赖

**Files:**
- Modify: `lc_agent/config/schema.py`
- Modify: `requirements.txt` (或 pyproject.toml)

- [ ] **Step 1: 更新配置 Schema**

在 `lc_agent/config/schema.py` 末尾添加 `AuthConfig` 并将其加入 `AppConfig`:

```python
class AuthConfig(BaseModel):
    secret: str = ""
    token_expire_days: int = 7

class AppConfig(BaseModel):
    """Application configuration schema."""
    provider: dict[str, ProviderConfig | dict] = Field(default_factory=dict)
    agent: dict = Field(default_factory=lambda: {
        "system_prompt": "You are a helpful assistant.",
        "default_model": "",
        "streaming": True,
        "recursion_limit": 100,
    })
    mcp: dict = Field(default_factory=dict)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    session: dict = Field(default_factory=lambda: {"db_path": ""})
    ui: dict = Field(default_factory=dict)
    skills: list[str] = Field(default_factory=lambda: ["./skills"])
    mcp_servers: dict[str, McpServerConfig] = Field(default_factory=dict)
    auth: AuthConfig = Field(default_factory=AuthConfig)
```

- [ ] **Step 2: 添加 Python 依赖**

确认 `python-jose[cryptography]` 和 `passlib[bcrypt]` 已在依赖中。运行：

```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

- [ ] **Step 3: Commit**

```bash
git add lc_agent/config/schema.py
git commit -m "feat(auth): add AuthConfig to config schema"
```

---

## Task 2: User 数据模型 + 迁移

**Files:**
- Create: `lc_agent/db/models_auth.py`
- Modify: `lc_agent/db/models.py`
- Create: `lc_agent/db/migrations/versions/20260704_add_users.py`

- [ ] **Step 1: 创建 User 和 UserAgentAccess 模型**

创建 `lc_agent/db/models_auth.py`:

```python
import uuid
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


def utcnow():
    from lc_agent.db.models import utcnow as _utcnow
    return _utcnow()


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    role: str = "user"  # "admin" or "user"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class UserAgentAccess(SQLModel, table=True):
    __tablename__ = "user_agent_access"

    user_id: str = Field(primary_key=True)
    agent_id: str = Field(primary_key=True)
```

- [ ] **Step 2: 给 SessionMeta 添加 user_id**

在 `lc_agent/db/models.py` 的 `SessionMeta` 类中加入：

```python
class SessionMeta(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str = "新对话"
    agent_id: str = "__chat__"
    model: str = ""
    user_id: str = Field(default="", index=True)  # 关联用户
    message_count: int = 0
    is_pinned: bool = False
    pinned_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
```

- [ ] **Step 3: 创建 Alembic 迁移脚本**

创建 `lc_agent/db/migrations/versions/20260704_add_users.py`:

```python
"""Add users table and user_id to sessions

Revision ID: 20260704_add_users
"""
from alembic import op
import sqlalchemy as sa

revision = "20260704_add_users"
down_revision = "20260704_drop_dangerous_tools"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "user_agent_access",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("agent_id", sa.String(), primary_key=True),
    )

    with op.batch_alter_table("sessions") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.String(), server_default="", nullable=False))
        batch_op.create_index("ix_sessions_user_id", ["user_id"])


def downgrade() -> None:
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.drop_index("ix_sessions_user_id")
        batch_op.drop_column("user_id")
    op.drop_table("user_agent_access")
    op.drop_index("ix_users_username", "users")
    op.drop_table("users")
```

- [ ] **Step 4: 确保模型导入到 migrations env**

检查 `lc_agent/db/migrations/env.py` 中是否 import 了新模型，确保 `from lc_agent.db.models_auth import User, UserAgentAccess` 存在。

- [ ] **Step 5: Commit**

```bash
git add lc_agent/db/models_auth.py lc_agent/db/models.py lc_agent/db/migrations/
git commit -m "feat(auth): add User model, UserAgentAccess, and user_id on sessions"
```

---

## Task 3: AuthService 核心逻辑

**Files:**
- Create: `lc_agent/core/auth.py`
- Test: `tests/test_auth_service.py`

- [ ] **Step 1: 编写 AuthService 测试**

创建 `tests/test_auth_service.py`:

```python
import pytest
from lc_agent.core.auth import AuthService


@pytest.fixture
def auth_service():
    return AuthService(secret="test-secret-key-minimum16chars", token_expire_days=7)


def test_hash_and_verify_password(auth_service):
    hashed = auth_service.hash_password("mypassword")
    assert auth_service.verify_password("mypassword", hashed) is True
    assert auth_service.verify_password("wrongpassword", hashed) is False


def test_create_and_decode_token(auth_service):
    token = auth_service.create_token(user_id="u123", username="alice", role="admin")
    payload = auth_service.decode_token(token)
    assert payload["sub"] == "u123"
    assert payload["username"] == "alice"
    assert payload["role"] == "admin"


def test_expired_token(auth_service):
    svc = AuthService(secret="test-secret-key-minimum16chars", token_expire_days=-1)
    token = svc.create_token(user_id="u1", username="bob", role="user")
    assert svc.decode_token(token) is None


def test_invalid_token(auth_service):
    assert auth_service.decode_token("garbage.token.here") is None


def test_generate_random_password(auth_service):
    pw = auth_service.generate_random_password()
    assert len(pw) >= 12
    pw2 = auth_service.generate_random_password()
    assert pw != pw2
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_auth_service.py -v
```

Expected: FAIL (module not found)

- [ ] **Step 3: 实现 AuthService**

创建 `lc_agent/core/auth.py`:

```python
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext


class AuthService:
    def __init__(self, secret: str, token_expire_days: int = 7):
        if len(secret) < 16:
            raise ValueError("Auth secret must be at least 16 characters")
        self._secret = secret
        self._token_expire_days = token_expire_days
        self._pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self._pwd_ctx.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return self._pwd_ctx.verify(plain, hashed)

    def create_token(self, *, user_id: str, username: str, role: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=self._token_expire_days)
        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": expire,
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def decode_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(token, self._secret, algorithms=["HS256"])
            return payload
        except JWTError:
            return None

    def generate_random_password(self, length: int = 16) -> str:
        return secrets.token_urlsafe(length)[:length]
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_auth_service.py -v
```

Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add lc_agent/core/auth.py tests/test_auth_service.py
git commit -m "feat(auth): implement AuthService with JWT and bcrypt"
```

---

## Task 4: Auth 认证中间件 + 依赖注入

**Files:**
- Create: `lc_agent/server/auth_middleware.py`

- [ ] **Step 1: 实现认证中间件和依赖注入函数**

创建 `lc_agent/server/auth_middleware.py`:

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add lc_agent/server/auth_middleware.py
git commit -m "feat(auth): add auth middleware with get_current_user and require_admin"
```

---

## Task 5: Auth 路由 (login, me, change-password)

**Files:**
- Create: `lc_agent/server/routes/auth.py`
- Test: `tests/test_routes_auth.py`

- [ ] **Step 1: 编写 Auth 路由测试**

创建 `tests/test_routes_auth.py`:

```python
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from lc_agent.core.auth import AuthService
from lc_agent.db.models_auth import User


@pytest_asyncio.fixture
async def client(tmp_path):
    from sqlmodel import SQLModel
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from lc_agent.server.app import create_app

    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(db_url)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    auth_service = AuthService(secret="test-secret-key-minimum16chars", token_expire_days=7)

    # Create test user
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        admin = User(
            id="admin-id",
            username="admin",
            password_hash=auth_service.hash_password("adminpass"),
            role="admin",
        )
        session.add(admin)
        await session.commit()

    app = create_app(config={"database": {"url": db_url}})
    app.state.auth_service = auth_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await engine.dispose()


@pytest.mark.asyncio
async def test_login_success(client):
    resp = await client.post("/api/auth/login", json={"username": "admin", "password": "adminpass"})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me(client):
    login = await client.post("/api/auth/login", json={"username": "admin", "password": "adminpass"})
    token = login.json()["token"]
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"


@pytest.mark.asyncio
async def test_change_password(client):
    login = await client.post("/api/auth/login", json={"username": "admin", "password": "adminpass"})
    token = login.json()["token"]
    resp = await client.post(
        "/api/auth/change-password",
        json={"old_password": "adminpass", "new_password": "newpass123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    # Login with new password
    resp2 = await client.post("/api/auth/login", json={"username": "admin", "password": "newpass123"})
    assert resp2.status_code == 200
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_routes_auth.py -v
```

Expected: FAIL (module not found)

- [ ] **Step 3: 实现 Auth 路由**

创建 `lc_agent/server/routes/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lc_agent.core.auth import AuthService
from lc_agent.db.models_auth import User
from lc_agent.server.auth_middleware import get_current_user
from lc_agent.server.dependencies import get_db_session

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


def _get_auth_service(request: Request) -> AuthService:
    svc = getattr(request.app.state, "auth_service", None)
    if svc is None:
        raise HTTPException(status_code=500, detail="Auth not configured")
    return svc


@router.post("/login")
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db_session)):
    auth_service = _get_auth_service(request)
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if user is None or not auth_service.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="认证失败")

    token = auth_service.create_token(user_id=user.id, username=user.username, role=user.role)
    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
    }


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    auth_service = _get_auth_service(request)
    if not auth_service.verify_password(body.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="旧密码错误")

    result = await db.execute(select(User).where(User.id == user.id))
    db_user = result.scalar_one()
    db_user.password_hash = auth_service.hash_password(body.new_password)
    await db.commit()
    return {"message": "密码修改成功"}
```

- [ ] **Step 4: 注册路由到 app**

在 `lc_agent/server/app.py` 中添加:

```python
from lc_agent.server.routes.auth import router as auth_router
# ... in create_app():
app.include_router(auth_router, prefix="/api")
```

- [ ] **Step 5: 运行测试确认通过**

```bash
pytest tests/test_routes_auth.py -v
```

Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add lc_agent/server/routes/auth.py lc_agent/server/app.py tests/test_routes_auth.py
git commit -m "feat(auth): add login/me/change-password API routes"
```

---

## Task 6: Admin 路由 (用户 CRUD + Agent 授权)

**Files:**
- Create: `lc_agent/server/routes/admin.py`
- Test: `tests/test_routes_admin.py`

- [ ] **Step 1: 编写 Admin 路由测试**

创建 `tests/test_routes_admin.py`:

```python
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from lc_agent.core.auth import AuthService
from lc_agent.db.models_auth import User


@pytest_asyncio.fixture
async def client_and_token(tmp_path):
    from sqlmodel import SQLModel
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from lc_agent.server.app import create_app

    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(db_url)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    auth_service = AuthService(secret="test-secret-key-minimum16chars", token_expire_days=7)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        admin = User(
            id="admin-id",
            username="admin",
            password_hash=auth_service.hash_password("adminpass"),
            role="admin",
        )
        session.add(admin)
        await session.commit()

    app = create_app(config={"database": {"url": db_url}})
    app.state.auth_service = auth_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login_resp = await ac.post("/api/auth/login", json={"username": "admin", "password": "adminpass"})
        token = login_resp.json()["token"]
        yield ac, token

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_user(client_and_token):
    client, token = client_and_token
    resp = await client.post(
        "/api/admin/users",
        json={"username": "newuser"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newuser"
    assert "password" in data  # initial random password returned


@pytest.mark.asyncio
async def test_list_users(client_and_token):
    client, token = client_and_token
    resp = await client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_set_user_agents(client_and_token):
    client, token = client_and_token
    # Create user first
    create_resp = await client.post(
        "/api/admin/users",
        json={"username": "bob"},
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = create_resp.json()["id"]

    # Set agents
    resp = await client.put(
        f"/api/admin/users/{user_id}/agents",
        json={"agent_ids": ["__chat__", "__power__"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    # Get agents
    resp2 = await client.get(
        f"/api/admin/users/{user_id}/agents",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert set(resp2.json()["agent_ids"]) == {"__chat__", "__power__"}


@pytest.mark.asyncio
async def test_non_admin_rejected(client_and_token):
    client, token = client_and_token
    # Create regular user
    create_resp = await client.post(
        "/api/admin/users",
        json={"username": "regular"},
        headers={"Authorization": f"Bearer {token}"},
    )
    password = create_resp.json()["password"]

    # Login as regular user
    login_resp = await client.post("/api/auth/login", json={"username": "regular", "password": password})
    user_token = login_resp.json()["token"]

    # Try admin endpoint
    resp = await client.get("/api/admin/users", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_routes_admin.py -v
```

- [ ] **Step 3: 实现 Admin 路由**

创建 `lc_agent/server/routes/admin.py`:

```python
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

    # Check duplicate
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

    # Default agent access: __chat__
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

    # Delete agent access
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
    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    # Replace all access records
    await db.execute(delete(UserAgentAccess).where(UserAgentAccess.user_id == user_id))
    for agent_id in body.agent_ids:
        db.add(UserAgentAccess(user_id=user_id, agent_id=agent_id))
    await db.commit()
    return {"agent_ids": body.agent_ids}
```

- [ ] **Step 4: 注册路由**

在 `lc_agent/server/app.py` 添加:

```python
from lc_agent.server.routes.admin import router as admin_router
# in create_app():
app.include_router(admin_router, prefix="/api")
```

- [ ] **Step 5: 运行测试确认通过**

```bash
pytest tests/test_routes_admin.py -v
```

- [ ] **Step 6: Commit**

```bash
git add lc_agent/server/routes/admin.py lc_agent/server/app.py tests/test_routes_admin.py
git commit -m "feat(auth): add admin routes for user management and agent authorization"
```

---

## Task 7: Session 隔离 (Repository + Routes)

**Files:**
- Modify: `lc_agent/db/repository.py`
- Modify: `lc_agent/server/routes/sessions.py`
- Test: `tests/test_session_isolation.py`

- [ ] **Step 1: 编写会话隔离测试**

创建 `tests/test_session_isolation.py`:

```python
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from lc_agent.core.auth import AuthService
from lc_agent.db.models_auth import User


@pytest_asyncio.fixture
async def setup(tmp_path):
    from sqlmodel import SQLModel
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from lc_agent.server.app import create_app

    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(db_url)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    auth_service = AuthService(secret="test-secret-key-minimum16chars", token_expire_days=7)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        alice = User(id="alice-id", username="alice", password_hash=auth_service.hash_password("pass"), role="user")
        bob = User(id="bob-id", username="bob", password_hash=auth_service.hash_password("pass"), role="user")
        session.add_all([alice, bob])
        await session.commit()

    app = create_app(config={"database": {"url": db_url}})
    app.state.auth_service = auth_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        alice_login = await ac.post("/api/auth/login", json={"username": "alice", "password": "pass"})
        bob_login = await ac.post("/api/auth/login", json={"username": "bob", "password": "pass"})
        yield ac, alice_login.json()["token"], bob_login.json()["token"]

    await engine.dispose()


@pytest.mark.asyncio
async def test_session_isolation(setup):
    client, alice_token, bob_token = setup
    alice_h = {"Authorization": f"Bearer {alice_token}"}
    bob_h = {"Authorization": f"Bearer {bob_token}"}

    # Alice creates a session
    resp = await client.post("/api/sessions", json={"title": "Alice's chat"}, headers=alice_h)
    assert resp.status_code == 201

    # Bob creates a session
    resp = await client.post("/api/sessions", json={"title": "Bob's chat"}, headers=bob_h)
    assert resp.status_code == 201

    # Alice only sees her session
    alice_sessions = await client.get("/api/sessions", headers=alice_h)
    assert len(alice_sessions.json()) == 1
    assert alice_sessions.json()[0]["title"] == "Alice's chat"

    # Bob only sees his session
    bob_sessions = await client.get("/api/sessions", headers=bob_h)
    assert len(bob_sessions.json()) == 1
    assert bob_sessions.json()[0]["title"] == "Bob's chat"
```

- [ ] **Step 2: 修改 SessionRepository 支持 user_id 过滤**

在 `lc_agent/db/repository.py` 的 `SessionRepository` 中修改 `list_all` 和 `create`:

```python
class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self, limit: int = 50, user_id: str | None = None) -> list[SessionMeta]:
        stmt = select(SessionMeta)
        if user_id:
            stmt = stmt.where(SessionMeta.user_id == user_id)
        stmt = stmt.order_by(SessionMeta.updated_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> SessionMeta:
        sess = SessionMeta(**kwargs)
        self.session.add(sess)
        await self.session.commit()
        await self.session.refresh(sess)
        return sess

    # ... rest unchanged
```

- [ ] **Step 3: 修改 sessions 路由注入 current_user**

修改 `lc_agent/server/routes/sessions.py`:

```python
from lc_agent.server.auth_middleware import get_current_user
from lc_agent.db.models_auth import User

@router.get("/sessions")
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repo = SessionRepository(db)
    sessions = await repo.list_all(user_id=user.id)
    return [serialize_session(s) for s in sessions]


@router.post("/sessions", status_code=201)
async def create_session(
    body: SessionCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repo = SessionRepository(db)
    session = await repo.create(title=body.title, agent_id=body.agent_id, model=body.model, user_id=user.id)
    return {"id": session.id, "title": session.title}


@router.put("/sessions/{session_id}")
async def update_session(
    session_id: str,
    body: SessionUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if sess.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    update_data = body.model_dump(exclude_unset=True)
    result = await repo.update(session_id, **update_data)
    return serialize_session(result)


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if sess.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    await repo.delete(session_id)
    return Response(status_code=204)


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    # Verify ownership
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if sess.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    # ... rest of existing logic
```

- [ ] **Step 4: 运行测试**

```bash
pytest tests/test_session_isolation.py -v
```

- [ ] **Step 5: Commit**

```bash
git add lc_agent/db/repository.py lc_agent/server/routes/sessions.py tests/test_session_isolation.py
git commit -m "feat(auth): add session isolation with user_id filtering"
```

---

## Task 8: Agent 授权过滤 + 路由保护

**Files:**
- Modify: `lc_agent/server/routes/agents.py`
- Modify: `lc_agent/server/routes/permissions.py`

- [ ] **Step 1: 修改 agents 路由过滤用户可见 Agent**

在 `lc_agent/server/routes/agents.py` 的 `list_agents` 中加入授权过滤:

```python
from lc_agent.server.auth_middleware import get_current_user, require_admin
from lc_agent.db.models_auth import User, UserAgentAccess
from sqlalchemy import select as sa_select

@router.get("/agents")
async def list_agents(
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db),
):
    """List agent presets visible to current user."""
    # Admin sees all
    if user.role == "admin":
        allowed_ids = None
    else:
        result = await db.execute(
            sa_select(UserAgentAccess.agent_id).where(UserAgentAccess.user_id == user.id)
        )
        allowed_ids = {row[0] for row in result.all()}

    all_presets = []
    for bp in engine.get_builtin_presets():
        all_presets.append((_preset_to_dict(bp), bp.id))
    for p in engine._custom_presets.values():
        all_presets.append((_preset_to_dict(p), p.id))
    stmt = sa_select(AgentPresetDB)
    rows = await db.execute(stmt)
    for row in rows.scalars().all():
        d = {
            "id": row.id, "name": row.name, "system_prompt": row.system_prompt,
            "default_model": row.default_model, "allowed_tool_groups": row.allowed_tool_groups,
            "allowed_mcp_servers": row.allowed_mcp_servers, "allowed_skills": row.allowed_skills,
            "source": "user", "default_enabled": True,
        }
        all_presets.append((d, row.id))

    if allowed_ids is None:
        return [p[0] for p in all_presets]
    return [p[0] for p in all_presets if p[1] in allowed_ids]
```

- [ ] **Step 2: Agent CRUD 限制 Admin**

给 `create_agent`, `update_agent`, `delete_agent` 添加 `admin: User = Depends(require_admin)`:

```python
@router.post("/agents", status_code=201)
async def create_agent(body: AgentCreateRequest, admin: User = Depends(require_admin), engine: AgentEngine = Depends(get_engine), db=Depends(get_db)):
    ...

@router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, body: AgentUpdateRequest, admin: User = Depends(require_admin), engine: AgentEngine = Depends(get_engine), db=Depends(get_db)):
    ...

@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, admin: User = Depends(require_admin), engine: AgentEngine = Depends(get_engine), db=Depends(get_db)):
    ...
```

- [ ] **Step 3: Permissions 路由限制 Admin**

在 `lc_agent/server/routes/permissions.py` 中对写操作添加 `admin: User = Depends(require_admin)`:

```python
from lc_agent.server.auth_middleware import get_current_user, require_admin
from lc_agent.db.models_auth import User

@router.get("/permissions")
async def get_permissions(user: User = Depends(get_current_user), ...):
    ...

@router.post("/permissions/allow")
async def allow_tool(body: ..., admin: User = Depends(require_admin), ...):
    ...

@router.delete("/permissions/allow/{tool_name}")
async def remove_tool(tool_name: str, admin: User = Depends(require_admin), ...):
    ...

@router.delete("/permissions/allow")
async def clear_all(admin: User = Depends(require_admin), ...):
    ...
```

- [ ] **Step 4: Commit**

```bash
git add lc_agent/server/routes/agents.py lc_agent/server/routes/permissions.py
git commit -m "feat(auth): protect agents and permissions routes with auth"
```

---

## Task 9: SSE 认证

**Files:**
- Modify: `lc_agent/server/sse.py`

- [ ] **Step 1: 在 SSE stream 端点添加 token 验证**

在 `lc_agent/server/sse.py` 的 `run_stream` 函数开头添加认证逻辑:

```python
from lc_agent.server.auth_middleware import _extract_token
from lc_agent.db.models_auth import User
from sqlalchemy import select

async def _authenticate_sse(request: Request) -> User | None:
    """Authenticate SSE request using token from query param or header."""
    auth_service = getattr(request.app.state, "auth_service", None)
    if auth_service is None:
        return None  # Auth not configured, allow all (dev mode)

    token = _extract_token(request)
    if not token:
        return None

    payload = auth_service.decode_token(token)
    if payload is None:
        return None

    from lc_agent.db.engine import get_async_session
    db_url = request.app.state.config.get("database", {}).get("url", "sqlite+aiosqlite:///./lc_agent_data.db")
    db = get_async_session(db_url)
    try:
        result = await db.execute(select(User).where(User.id == payload["sub"]))
        return result.scalar_one_or_none()
    finally:
        await db.close()
```

在 `run_stream` 路由函数内验证:

```python
@router.post("/{thread_id}/runs/stream")
async def run_stream(thread_id: str, body: RunStreamRequest, request: Request):
    user = await _authenticate_sse(request)
    if user is None and getattr(request.app.state, "auth_service", None) is not None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"detail": "认证失败"})

    # Verify session ownership
    if user:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.models import SessionMeta
        db_url = request.app.state.config.get("database", {}).get("url", "sqlite+aiosqlite:///./lc_agent_data.db")
        db = get_async_session(db_url)
        try:
            result = await db.execute(select(SessionMeta).where(SessionMeta.id == thread_id))
            session_meta = result.scalar_one_or_none()
            if session_meta and session_meta.user_id and session_meta.user_id != user.id and user.role != "admin":
                return JSONResponse(status_code=403, content={"detail": "权限不足"})
        finally:
            await db.close()

    # ... existing logic continues
```

- [ ] **Step 2: Commit**

```bash
git add lc_agent/server/sse.py
git commit -m "feat(auth): add JWT authentication to SSE streaming endpoint"
```

---

## Task 10: App 启动初始化 (AuthService + 首个 Admin)

**Files:**
- Modify: `lc_agent/app.py`

- [ ] **Step 1: 在 app 启动时初始化 AuthService 并创建首个 Admin**

在 `lc_agent/app.py` 的启动逻辑中添加:

```python
from lc_agent.core.auth import AuthService
from lc_agent.db.models_auth import User, UserAgentAccess

async def _init_auth(self):
    """Initialize auth service and ensure at least one admin exists."""
    auth_config = self.config.get("auth", {})
    secret = auth_config.get("secret", "")
    if not secret:
        print("[Auth] WARNING: auth.secret not configured, authentication DISABLED")
        return

    token_expire_days = auth_config.get("token_expire_days", 7)
    self._auth_service = AuthService(secret=secret, token_expire_days=token_expire_days)

    # Ensure first admin exists
    from sqlalchemy import select
    from lc_agent.db.engine import get_async_session
    db_url = self.config.get("database", {}).get("url", "sqlite+aiosqlite:///./lc_agent_data.db")
    db = get_async_session(db_url)
    try:
        result = await db.execute(select(User).where(User.role == "admin"))
        admin = result.scalar_one_or_none()
        if admin is None:
            password = self._auth_service.generate_random_password()
            admin = User(
                username="admin",
                password_hash=self._auth_service.hash_password(password),
                role="admin",
            )
            db.add(admin)

            # Assign existing sessions to this admin
            from lc_agent.db.models import SessionMeta
            await db.execute(
                SessionMeta.__table__.update().where(SessionMeta.user_id == "").values(user_id=admin.id)
            )

            await db.commit()
            print(f"[Auth] Created initial admin user: admin / {password}")
            print(f"[Auth] ⚠️  请立即保存此密码，后续不再显示！")
        else:
            print(f"[Auth] Admin user exists: {admin.username}")
    finally:
        await db.close()
```

在 lifespan 或 startup 中调用 `_init_auth()`，并将 `auth_service` 挂载到 `app.state.auth_service`。

- [ ] **Step 2: Commit**

```bash
git add lc_agent/app.py
git commit -m "feat(auth): init AuthService on startup and create first admin"
```

---

## Task 11: 前端 — Auth Store + HTTP 客户端

**Files:**
- Create: `frontend/src/stores/auth.ts`
- Create: `frontend/src/api/auth.ts`
- Modify: `frontend/src/api/http.ts`
- Modify: `frontend/src/api/sse-client.ts`

- [ ] **Step 1: 创建 auth API 客户端**

创建 `frontend/src/api/auth.ts`:

```typescript
const BASE_URL = '/api/auth'

export interface LoginResponse {
  token: string
  user: { id: string; username: string; role: string }
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const resp = await fetch(`${BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!resp.ok) throw new Error('认证失败')
  return resp.json()
}

export async function getMe(token: string): Promise<{ id: string; username: string; role: string }> {
  const resp = await fetch(`${BASE_URL}/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!resp.ok) throw new Error('Token 无效')
  return resp.json()
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  const token = localStorage.getItem('token') || ''
  const resp = await fetch(`${BASE_URL}/change-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  })
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}))
    throw new Error(data.detail || '修改失败')
  }
}
```

- [ ] **Step 2: 创建 auth store**

创建 `frontend/src/stores/auth.ts`:

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, getMe } from '@/api/auth'
import type { LoginResponse } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<{ id: string; username: string; role: string } | null>(null)
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(username: string, password: string) {
    const resp: LoginResponse = await apiLogin(username, password)
    token.value = resp.token
    user.value = resp.user
    localStorage.setItem('token', resp.token)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  async function checkAuth(): Promise<boolean> {
    if (!token.value) return false
    try {
      user.value = await getMe(token.value)
      return true
    } catch {
      logout()
      return false
    }
  }

  return { token, user, isAuthenticated, isAdmin, login, logout, checkAuth }
})
```

- [ ] **Step 3: 修改 HTTP 客户端自动添加 token**

修改 `frontend/src/api/http.ts`:

```typescript
const BASE_URL = '/api'

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = localStorage.getItem('token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: getAuthHeaders(),
    ...options,
  })
  if (response.status === 401) {
    localStorage.removeItem('token')
    window.location.hash = '#/login'
    throw new Error('认证已过期，请重新登录')
  }
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

// ... rest of api object unchanged
```

- [ ] **Step 4: SSE 客户端拼接 token**

在 `frontend/src/api/sse-client.ts` 中，URL 拼接 token:

```typescript
// 在构建 SSE URL 的地方:
const token = localStorage.getItem('token') || ''
const url = `/api/threads/${threadId}/runs/stream?token=${encodeURIComponent(token)}`
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/stores/auth.ts frontend/src/api/auth.ts frontend/src/api/http.ts frontend/src/api/sse-client.ts
git commit -m "feat(auth): add frontend auth store and token injection"
```

---

## Task 12: 前端 — Login 页面 + 路由守卫

**Files:**
- Create: `frontend/src/views/LoginView.vue`
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: 创建登录页面**

创建 `frontend/src/views/LoginView.vue`:

```vue
<template>
  <div class="login-container">
    <el-card class="login-card" shadow="always">
      <template #header>
        <h2 class="login-title">登录</h2>
      </template>
      <el-form @submit.prevent="handleLogin" :model="form" label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" autofocus />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleLogin" style="width: 100%">
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

async function handleLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    router.push('/')
  } catch (e: any) {
    ElMessage.error(e.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: var(--el-bg-color-page);
}
.login-card {
  width: 380px;
}
.login-title {
  text-align: center;
  margin: 0;
  font-size: 20px;
}
</style>
```

- [ ] **Step 2: 配置路由和守卫**

修改 `frontend/src/router/index.ts`:

```typescript
import { createRouter, createWebHashHistory } from 'vue-router'
import ChatView from '@/views/ChatView.vue'
import LoginView from '@/views/LoginView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true },
    },
    {
      path: '/',
      name: 'home',
      component: ChatView,
    },
    {
      path: '/c/:sessionId',
      name: 'chat',
      component: ChatView,
      props: true,
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/test-segments',
      name: 'test-segments',
      component: () => import('@/views/TestSegments.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  // Public routes don't need auth
  if (to.meta.public) return true

  // Check auth state
  if (!authStore.isAuthenticated) {
    const valid = await authStore.checkAuth()
    if (!valid) return { name: 'login' }
  }

  // Admin routes
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return { name: 'home' }
  }

  return true
})

export default router
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/LoginView.vue frontend/src/router/index.ts
git commit -m "feat(auth): add login page and router guard"
```

---

## Task 13: 前端 — Admin 管理页面

**Files:**
- Create: `frontend/src/views/AdminView.vue`

- [ ] **Step 1: 创建 Admin 管理页面**

创建 `frontend/src/views/AdminView.vue` 包含:
- 用户列表表格（username, role, created_at, 操作列）
- 创建用户按钮 → 弹窗输入 username → 显示生成的密码
- 删除用户按钮（带确认）
- 重置密码按钮（显示新密码）
- Agent 授权按钮 → 弹窗选择 Agent（多选穿梭框或 checkbox）

使用 Element Plus 组件: `el-table`, `el-dialog`, `el-button`, `el-input`, `el-transfer` 或 `el-checkbox-group`。

```vue
<template>
  <div class="admin-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>用户管理</h3>
          <el-button type="primary" @click="showCreateDialog = true">创建用户</el-button>
        </div>
      </template>

      <el-table :data="users" stripe>
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="role" label="角色" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button size="small" @click="openAgentDialog(row)">授权</el-button>
            <el-button size="small" @click="resetPassword(row)">重置密码</el-button>
            <el-button size="small" type="danger" @click="deleteUser(row)" :disabled="row.role === 'admin'">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create User Dialog -->
    <el-dialog v-model="showCreateDialog" title="创建用户" width="400">
      <el-form label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="newUsername" placeholder="请输入用户名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createUser">创建</el-button>
      </template>
    </el-dialog>

    <!-- Agent Authorization Dialog -->
    <el-dialog v-model="showAgentDialog" title="智能体授权" width="500">
      <el-checkbox-group v-model="selectedAgents">
        <el-checkbox v-for="agent in allAgents" :key="agent.id" :label="agent.id">
          {{ agent.name }} ({{ agent.id }})
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="showAgentDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAgentAccess">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchApi } from '@/api/http'
import { ElMessage, ElMessageBox } from 'element-plus'

const users = ref<any[]>([])
const allAgents = ref<any[]>([])
const showCreateDialog = ref(false)
const showAgentDialog = ref(false)
const newUsername = ref('')
const selectedAgents = ref<string[]>([])
const currentUserId = ref('')

async function loadUsers() {
  users.value = await fetchApi<any[]>('/admin/users')
}

async function loadAgents() {
  allAgents.value = await fetchApi<any[]>('/agents')
}

async function createUser() {
  if (!newUsername.value) return
  try {
    const data = await fetchApi<any>('/admin/users', {
      method: 'POST',
      body: JSON.stringify({ username: newUsername.value }),
    })
    ElMessageBox.alert(
      `用户 ${data.username} 创建成功\n初始密码: ${data.password}\n\n请立即复制保存！`,
      '创建成功',
      { confirmButtonText: '已复制', type: 'success' }
    )
    showCreateDialog.value = false
    newUsername.value = ''
    await loadUsers()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function deleteUser(row: any) {
  await ElMessageBox.confirm(`确定删除用户 ${row.username}？`, '确认')
  await fetchApi<void>(`/admin/users/${row.id}`, { method: 'DELETE' })
  ElMessage.success('已删除')
  await loadUsers()
}

async function resetPassword(row: any) {
  await ElMessageBox.confirm(`确定重置 ${row.username} 的密码？`, '确认')
  const data = await fetchApi<{ password: string }>(`/admin/users/${row.id}/reset-password`, { method: 'PUT' })
  ElMessageBox.alert(`新密码: ${data.password}\n\n请立即复制保存！`, '密码已重置', { type: 'success' })
}

async function openAgentDialog(row: any) {
  currentUserId.value = row.id
  const data = await fetchApi<{ agent_ids: string[] }>(`/admin/users/${row.id}/agents`)
  selectedAgents.value = data.agent_ids
  showAgentDialog.value = true
}

async function saveAgentAccess() {
  await fetchApi<any>(`/admin/users/${currentUserId.value}/agents`, {
    method: 'PUT',
    body: JSON.stringify({ agent_ids: selectedAgents.value }),
  })
  ElMessage.success('授权已更新')
  showAgentDialog.value = false
}

onMounted(() => {
  loadUsers()
  loadAgents()
})
</script>

<style scoped>
.admin-container { padding: 20px; max-width: 900px; margin: 0 auto; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-header h3 { margin: 0; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/AdminView.vue
git commit -m "feat(auth): add admin management page"
```

---

## Task 14: 前端 — Header 用户信息 + 修改密码 + 登出

**Files:**
- Create: `frontend/src/components/dialogs/ChangePasswordDialog.vue`
- Modify: `frontend/src/App.vue` or layout component

- [ ] **Step 1: 创建修改密码弹窗**

创建 `frontend/src/components/dialogs/ChangePasswordDialog.vue`:

```vue
<template>
  <el-dialog v-model="visible" title="修改密码" width="400">
    <el-form label-position="top" :model="form">
      <el-form-item label="旧密码">
        <el-input v-model="form.oldPassword" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="form.newPassword" type="password" show-password />
      </el-form-item>
      <el-form-item label="确认新密码">
        <el-input v-model="form.confirmPassword" type="password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="submit">确认修改</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { changePassword } from '@/api/auth'
import { ElMessage } from 'element-plus'

const visible = defineModel<boolean>({ required: true })
const loading = ref(false)
const form = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })

async function submit() {
  if (form.newPassword !== form.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  if (form.newPassword.length < 6) {
    ElMessage.warning('新密码至少6位')
    return
  }
  loading.value = true
  try {
    await changePassword(form.oldPassword, form.newPassword)
    ElMessage.success('密码修改成功')
    visible.value = false
    form.oldPassword = ''
    form.newPassword = ''
    form.confirmPassword = ''
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>
```

- [ ] **Step 2: 在布局中添加用户菜单**

在适当的布局组件（如 Header 或 Sidebar 顶部）添加:

```vue
<!-- 用户区域 -->
<div class="user-menu" v-if="authStore.isAuthenticated">
  <el-dropdown>
    <span class="user-trigger">
      {{ authStore.user?.username }}
      <el-icon><ArrowDown /></el-icon>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item @click="showChangePassword = true">修改密码</el-dropdown-item>
        <el-dropdown-item v-if="authStore.isAdmin" @click="$router.push('/admin')">管理后台</el-dropdown-item>
        <el-dropdown-item divided @click="handleLogout">登出</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</div>

<ChangePasswordDialog v-model="showChangePassword" />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/dialogs/ChangePasswordDialog.vue frontend/src/...
git commit -m "feat(auth): add user menu with logout and change password"
```

---

## Task 15: 集成测试 + 收尾

**Files:**
- Run all tests
- Verify end-to-end flow

- [ ] **Step 1: 运行全部后端测试**

```bash
pytest tests/ -v
```

Expected: ALL PASS

- [ ] **Step 2: 构建前端**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: 手动验证流程**

1. 启动服务 → 控制台打印初始 admin 密码
2. 访问前端 → 自动跳转登录页
3. 用 admin 登录 → 进入主页
4. 创建新用户 → 新用户只能看到 __chat__ Agent
5. 新用户创建会话 → admin 看不到该会话（除非切换到 admin 查看全部模式）

- [ ] **Step 4: 最终 Commit**

```bash
git add -A
git commit -m "feat(auth): complete auth/session-isolation/agent-authorization implementation"
```
