import asyncio
from pathlib import Path

from sqlalchemy import text

from lc_agent.app import LcAgentApp
from lc_agent.config.loader import load_config
from lc_agent.db.engine import get_async_engine, get_async_session, reset_engine
from lc_agent.db.models import SessionMeta
from lc_agent.db.repository import SessionRepository

CONFIG_PATH = Path(r"D:\codes\lc-agent-bfzs\config.jsonc")


async def inspect_url(url: str) -> None:
    reset_engine()
    engine = get_async_engine(url)
    print(f"ENGINE_URL {engine.url}")
    async with engine.connect() as conn:
        print(f"DATABASE_LIST {(await conn.execute(text('pragma database_list'))).fetchall()}")
        print(f"JOURNAL_MODE {(await conn.execute(text('pragma journal_mode'))).fetchall()}")
        print(f"TABLES {(await conn.execute(text("select name from sqlite_master where type='table' order by name"))).fetchall()}")
    await engine.dispose()
    reset_engine()


async def insert_direct_sql(url: str) -> None:
    reset_engine()
    engine = get_async_engine(url)
    async with engine.begin() as conn:
        await conn.execute(
            text("insert into sessions (id, title, agent_id, model, user_id, message_count, is_pinned, created_at, updated_at) values (:id, :title, :agent_id, :model, :user_id, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"),
            {"id": "debug-direct-sql", "title": "debug direct sql", "agent_id": "__chat__", "model": "", "user_id": "debug-script"},
        )
        print("DIRECT_SQL_INSERT_OK")
    await engine.dispose()
    reset_engine()


async def insert_orm_session(url: str) -> None:
    reset_engine()
    session = get_async_session(url)
    try:
        item = SessionMeta(title="debug orm add", agent_id="__chat__", model="", user_id="debug-script")
        session.add(item)
        await session.commit()
        await session.refresh(item)
        print(f"ORM_INSERT_OK {item.id}")
    finally:
        await session.close()
        reset_engine()


async def insert_repo(url: str) -> None:
    reset_engine()
    session = get_async_session(url)
    try:
        repo = SessionRepository(session)
        item = await repo.create(title="debug repo", agent_id="__chat__", model="", user_id="debug-script")
        print(f"REPO_INSERT_OK {item.id}")
    finally:
        await session.close()
        reset_engine()


async def main() -> int:
    config = load_config(str(CONFIG_PATH))
    app = LcAgentApp(config, host="127.0.0.1", port=8001)
    url = app.fastapi_app.state.config["database"]["url"]
    print(f"RESOLVED_URL {url}")
    await inspect_url(url)
    await insert_direct_sql(url)
    await insert_orm_session(url)
    await insert_repo(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
