import asyncio
import sqlite3
import time
import uuid
from pathlib import Path

import aiosqlite

DB = Path(r"D:\codes\lc-agent-bfzs\bfzs_data.db")
ROOT = DB.parent


def label(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def insert_sqlite3(name: str) -> None:
    con = sqlite3.connect(str(DB), timeout=10)
    try:
        print(f"SQLITE3_DATABASE_LIST {con.execute('pragma database_list').fetchall()}")
        print(f"SQLITE3_JOURNAL_MODE {con.execute('pragma journal_mode').fetchall()}")
        con.execute(
            "insert into sessions (id, title, agent_id, model, user_id, message_count, is_pinned, created_at, updated_at) values (?, ?, ?, ?, ?, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (name, name, "__chat__", "", "debug-script"),
        )
        con.commit()
        print(f"SQLITE3_INSERT_OK {name}")
    finally:
        con.close()


async def insert_aiosqlite(name: str, pragmas: list[str]) -> None:
    async with aiosqlite.connect(str(DB), timeout=10) as db:
        async with db.execute("pragma database_list") as cur:
            print(f"AIOSQLITE_DATABASE_LIST {await cur.fetchall()}")
        for pragma in pragmas:
            async with db.execute(pragma) as cur:
                print(f"AIOSQLITE_PRAGMA {pragma} {await cur.fetchall()}")
        await db.execute(
            "insert into sessions (id, title, agent_id, model, user_id, message_count, is_pinned, created_at, updated_at) values (?, ?, ?, ?, ?, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (name, name, "__chat__", "", "debug-script"),
        )
        await db.commit()
        print(f"AIOSQLITE_INSERT_OK {name}")


async def run_case(name: str, func) -> None:
    print(f"CASE_BEGIN {name}")
    try:
        await func()
    except Exception as exc:
        code = getattr(exc, "sqlite_errorcode", None)
        err_name = getattr(exc, "sqlite_errorname", None)
        print(f"CASE_FAILED {name} {type(exc).__name__}: {exc} code={code} name={err_name}")
    print(f"CASE_END {name}")


async def main() -> int:
    print(f"DB {DB}")
    print(f"DB_EXISTS {DB.exists()} SIZE {DB.stat().st_size if DB.exists() else None}")
    print(f"ROOT_EXISTS {ROOT.exists()}")
    probe = ROOT / f"__write_probe_{uuid.uuid4().hex}.tmp"
    try:
        probe.write_text("ok", encoding="utf-8")
        print("DIR_WRITE_OK")
    finally:
        if probe.exists():
            probe.unlink()
    for side in ["bfzs_data.db-journal", "bfzs_data.db-wal", "bfzs_data.db-shm"]:
        path = ROOT / side
        print(f"SIDE_FILE {side} EXISTS {path.exists()} SIZE {path.stat().st_size if path.exists() else None}")

    await run_case("sqlite3-default", lambda: asyncio.to_thread(insert_sqlite3, label("debug-sqlite3")))
    await run_case("aiosqlite-default", lambda: insert_aiosqlite(label("debug-aiosqlite-default"), []))
    await run_case("aiosqlite-temp-memory", lambda: insert_aiosqlite(label("debug-aiosqlite-temp-memory"), ["pragma temp_store=memory"]))
    await run_case("aiosqlite-journal-memory", lambda: insert_aiosqlite(label("debug-aiosqlite-journal-memory"), ["pragma journal_mode=memory"]))
    await run_case("aiosqlite-journal-wal", lambda: insert_aiosqlite(label("debug-aiosqlite-journal-wal"), ["pragma journal_mode=wal"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
