import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from lc_agent.core.auth import AuthService
from lc_agent.db.models_auth import User


@pytest_asyncio.fixture
async def setup(tmp_path):
    import lc_agent.db.models  # noqa: F401 — register SessionMeta table
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
    reset_engine()


@pytest.mark.asyncio
async def test_session_isolation(setup):
    client, alice_token, bob_token = setup
    alice_h = {"Authorization": f"Bearer {alice_token}"}
    bob_h = {"Authorization": f"Bearer {bob_token}"}

    # Alice creates session
    resp = await client.post("/api/sessions", json={"title": "Alice's chat"}, headers=alice_h)
    assert resp.status_code == 201

    # Bob creates session
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
