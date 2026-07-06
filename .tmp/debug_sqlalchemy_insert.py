import asyncio
import uuid
from pathlib import Path

from sqlalchemy import text

from lc_agent.app import LcAgentApp
from lc_agent.config.loader import load_config
from lc_agent.db.engine import get_async_engine, reset_engine
from lc_agent.db.repository import SessionRepository
from lc_agent.db.engine import get_async_session

CONFIG_PATH = Path(r"D:\codes\lc-agent-bfzs\config.jsonc")
URLS = [
    "sqlite+aiosqlite:///D:/codes/lc-agent-bfzs/bfzs_data.db",
    r"sqlite+aiosqlite:///D:\codes\lc-agent-bfzs\bfzs_data.db",
    "sqlite+aiosqlite:////D:/codes/lc-agent-bfzs/bfzs_data.db",
]


async def test_direct_sql(url: str) -> None:
    reset_engine()
    print(f"DIRECT_SQL_URL {url}")
    engine = get_async_engine(url)
    async with engine.begin() as conn:
        rows = (await conn.execute(text("pragma database_list"))).fetchall()
        print(f"DATABASE_LIST {rows}")
        item_id = f"debug-sqlalchemy-direct-{uuid.uuid4()}"
        await conn.execute(
            text("insert into sessions (id, title, agent_id, model, user_id, message_count, is_pinned, created_at, updated_at) values (:id, :title, :agent_id, :model, :user_id, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"),
            {"id": item_id, "title": item_id, "agent_id": "__chat__", "model": "", "user_id": "debug-script"},
        )
        print(f"DIRECT_SQL_INSERT_OK {item_id}")
    await engine.dispose()
    reset_engine()


async def test_repo(url: str) -> None:
    reset_engine()
    print(f"REPO_URL {url}")
    session = get_async_session(url)
    try:
        repo = SessionRepository(session)
        item = await repo.create(title="debug sqlalchemy repo", agent_id="__chat__", model="", user_id="debug-script")
        print(f"REPO_INSERT_OK {item.id}")
    finally:
        await session.close()
        reset_engine()


async def test_app_url() -> None:
    config = load_config(str(CONFIG_PATH))
    app = LcAgentApp(config, host="127.0.0.1", port=8001)
    url = app.fastapi_app.state.config["database"]["url"]
    print(f"APP_RESOLVED_URL {url}")
    await test_direct_sql(url)
    await test_repo(url)


async def main() -> int:
    for url in URLS:
        try:
            await test_direct_sql(url)
            await test_repo(url)
        except Exception as exc:
            code = getattr(exc, "sqlite_errorcode", None)
            name = getattr(exc, "sqlite_errorname", None)
            print(f"URL_FAILED {url} {type(exc).__name__}: {exc} code={code} name={name}")
    await test_app_url()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
