import asyncio
import shutil
import sqlite3
import tempfile
import uuid
from pathlib import Path

import aiosqlite
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

DB = Path(r"D:\codes\lc-agent-bfzs\bfzs_data.db")
TMP = Path(r"D:\codes\lc-agent\.tmp")


def item_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def print_file_state(path: Path) -> None:
    print(f"FILE {path} exists={path.exists()} size={path.stat().st_size if path.exists() else None}")


def sqlite3_baseline(path: Path, name: str) -> None:
    print(f"CASE sqlite3-{name}")
    try:
        with sqlite3.connect(str(path), timeout=30) as con:
            print("database_list", con.execute("pragma database_list").fetchall())
            print("quick_check", con.execute("pragma quick_check").fetchall())
            print("journal_mode", con.execute("pragma journal_mode").fetchall())
            con.execute(
                "insert into sessions (id, title, agent_id, model, user_id, message_count, is_pinned, created_at, updated_at) values (?, ?, ?, ?, ?, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (item_id(f"sqlite3-{name}"), f"sqlite3 {name}", "__chat__", "", "debug-script"),
            )
            con.commit()
            print(f"OK sqlite3-{name}")
    except Exception as exc:
        print(f"FAIL sqlite3-{name} {type(exc).__name__}: {exc}")


async def pure_aiosqlite(path: Path, name: str) -> None:
    print(f"CASE pure-aiosqlite-{name}")
    try:
        async with aiosqlite.connect(str(path), timeout=30) as db:
            async with db.execute("pragma database_list") as cur:
                print("database_list", await cur.fetchall())
            async with db.execute("pragma quick_check") as cur:
                print("quick_check", await cur.fetchall())
            async with db.execute("pragma journal_mode") as cur:
                print("journal_mode", await cur.fetchall())
            await db.execute(
                "insert into sessions (id, title, agent_id, model, user_id, message_count, is_pinned, created_at, updated_at) values (?, ?, ?, ?, ?, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (item_id(f"pure-aiosqlite-{name}"), f"pure aiosqlite {name}", "__chat__", "", "debug-script"),
            )
            await db.commit()
            print(f"OK pure-aiosqlite-{name}")
    except Exception as exc:
        code = getattr(exc, "sqlite_errorcode", None)
        err_name = getattr(exc, "sqlite_errorname", None)
        print(f"FAIL pure-aiosqlite-{name} {type(exc).__name__}: {exc} code={code} name={err_name}")


async def sqlalchemy_case(name: str, url: str, **kwargs) -> None:
    print(f"CASE sqlalchemy-{name}")
    engine = create_async_engine(url, echo=False, **kwargs)
    try:
        async with engine.begin() as conn:
            rows = (await conn.execute(text("pragma database_list"))).fetchall()
            print("database_list", rows)
            quick = (await conn.execute(text("pragma quick_check"))).fetchall()
            print("quick_check", quick)
            journal = (await conn.execute(text("pragma journal_mode"))).fetchall()
            print("journal_mode", journal)
            await conn.execute(
                text("insert into sessions (id, title, agent_id, model, user_id, message_count, is_pinned, created_at, updated_at) values (:id, :title, :agent_id, :model, :user_id, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"),
                {"id": item_id(name), "title": name, "agent_id": "__chat__", "model": "", "user_id": "debug-script"},
            )
            print(f"OK sqlalchemy-{name}")
    except Exception as exc:
        code = getattr(exc, "sqlite_errorcode", None)
        err_name = getattr(exc, "sqlite_errorname", None)
        print(f"FAIL sqlalchemy-{name} {type(exc).__name__}: {exc} code={code} name={err_name}")
    finally:
        await engine.dispose()


async def main() -> int:
    print_file_state(DB)
    print_file_state(DB.with_name(DB.name + "-journal"))
    print_file_state(DB.with_name(DB.name + "-wal"))
    print_file_state(DB.with_name(DB.name + "-shm"))
    print("TEMP_DIR", tempfile.gettempdir())
    TMP.mkdir(parents=True, exist_ok=True)
    copied = TMP / "debug_bfzs_data_copy.db"
    if copied.exists():
        copied.unlink()
    shutil.copy2(DB, copied)
    print_file_state(copied)

    sqlite3_baseline(DB, "original")
    sqlite3_baseline(copied, "copy")
    await pure_aiosqlite(DB, "original")
    await pure_aiosqlite(copied, "copy")

    urls = [
        ("original-normal-posix", "sqlite+aiosqlite:///D:/codes/lc-agent-bfzs/bfzs_data.db", {}),
        ("original-nullpool", "sqlite+aiosqlite:///D:/codes/lc-agent-bfzs/bfzs_data.db", {"poolclass": NullPool}),
        ("original-timeout", "sqlite+aiosqlite:///D:/codes/lc-agent-bfzs/bfzs_data.db", {"connect_args": {"timeout": 30}}),
        ("copy-normal-posix", "sqlite+aiosqlite:///D:/codes/lc-agent/.tmp/debug_bfzs_data_copy.db", {}),
        ("copy-nullpool", "sqlite+aiosqlite:///D:/codes/lc-agent/.tmp/debug_bfzs_data_copy.db", {"poolclass": NullPool}),
    ]
    for name, url, kwargs in urls:
        await sqlalchemy_case(name, url, **kwargs)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
