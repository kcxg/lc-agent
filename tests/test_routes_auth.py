import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from lc_agent.core.auth import AuthService
from lc_agent.db.models_auth import User


@pytest_asyncio.fixture
async def client(tmp_path):
    import lc_agent.db.models_auth  # noqa: F401 — register User table
    from sqlmodel import SQLModel
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from lc_agent.db.engine import reset_engine
    from lc_agent.server.app import create_app

    reset_engine()

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
        yield ac

    await engine.dispose()
    reset_engine()


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

    old_login = await client.post("/api/auth/login", json={"username": "admin", "password": "adminpass"})
    assert old_login.status_code == 401

    new_login = await client.post("/api/auth/login", json={"username": "admin", "password": "newpass123"})
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_unauthenticated(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401
