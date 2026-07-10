import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from lc_agent.core.auth import AuthService
from lc_agent.db.models_auth import User


@pytest_asyncio.fixture
async def client_and_token(tmp_path):
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
        login_resp = await ac.post("/api/auth/login", json={"username": "admin", "password": "adminpass"})
        token = login_resp.json()["token"]
        yield ac, token

    await engine.dispose()
    reset_engine()


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
    assert data["role"] == "user"
    assert "password" in data


@pytest.mark.asyncio
async def test_list_users(client_and_token):
    client, token = client_and_token
    create_resp = await client.post(
        "/api/admin/users",
        json={"username": "listuser"},
        headers={"Authorization": f"Bearer {token}"},
    )
    created_id = create_resp.json()["id"]

    resp = await client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) >= 2
    usernames = {u["username"] for u in users}
    assert "admin" in usernames
    assert "listuser" in usernames
    listuser = next(u for u in users if u["id"] == created_id)
    assert listuser["role"] == "user"
    assert "created_at" in listuser


@pytest.mark.asyncio
async def test_set_user_agents(client_and_token):
    client, token = client_and_token
    create_resp = await client.post(
        "/api/admin/users",
        json={"username": "bob"},
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/admin/users/{user_id}/agents",
        json={"agent_ids": ["chat", "power"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert set(resp.json()["agent_ids"]) == {"chat", "power"}

    resp2 = await client.get(
        f"/api/admin/users/{user_id}/agents",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 200
    assert set(resp2.json()["agent_ids"]) == {"chat", "power"}


@pytest.mark.asyncio
async def test_non_admin_rejected(client_and_token):
    client, token = client_and_token
    create_resp = await client.post(
        "/api/admin/users",
        json={"username": "regular"},
        headers={"Authorization": f"Bearer {token}"},
    )
    password = create_resp.json()["password"]

    login_resp = await client.post("/api/auth/login", json={"username": "regular", "password": password})
    user_token = login_resp.json()["token"]

    resp = await client.get("/api/admin/users", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_user(client_and_token):
    client, token = client_and_token
    create_resp = await client.post(
        "/api/admin/users",
        json={"username": "todelete"},
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = create_resp.json()["id"]

    resp = await client.delete(
        f"/api/admin/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204

    list_resp = await client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    user_ids = {u["id"] for u in list_resp.json()}
    assert user_id not in user_ids


@pytest.mark.asyncio
async def test_cannot_delete_self(client_and_token):
    client, token = client_and_token
    resp = await client.delete(
        "/api/admin/users/admin-id",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
