import asyncio
import sqlite3
import threading
from pathlib import Path

import aiosqlite

DB = Path(r"D:\codes\lc-agent-bfzs\bfzs_data.db")


def insert_sqlite3(label: str) -> None:
    con = sqlite3.connect(str(DB))
    try:
        con.execute(
            "insert into sessions (id, title, agent_id, model, user_id, message_count, is_pinned, created_at, updated_at) values (?, ?, ?, ?, ?, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (label, label, "__chat__", "", "debug-script"),
        )
        con.commit()
        print(f"SQLITE3_INSERT_OK {label}")
    finally:
        con.close()


def insert_sqlite3_thread() -> None:
    error = None

    def target() -> None:
        nonlocal error
        try:
            insert_sqlite3("debug-sqlite3-thread")
        except Exception as exc:
            error = exc

    thread = threading.Thread(target=target)
    thread.start()
    thread.join()
    if error:
        print(f"SQLITE3_THREAD_FAILED {type(error).__name__}: {error}")
        raise error


async def insert_aiosqlite(label: str, pragmas: list[str]) -> None:
    print(f"AIOSQLITE_CASE {label}")
    async with aiosqlite.connect(str(DB)) as db:
        for pragma in pragmas:
            print(f"PRAGMA {pragma}")
            async with db.execute(pragma) as cursor:
                rows = await cursor.fetchall()
                print(f"PRAGMA_RESULT {rows}")
        try:
            await db.execute(
                "insert into sessions (id, title, agent_id, model, user_id, message_count, is_pinned, created_at, updated_at) values (?, ?, ?, ?, ?, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (label, label, "__chat__", "", "debug-script"),
            )
            await db.commit()
            print(f"AIOSQLITE_INSERT_OK {label}")
        except Exception as exc:
            code = getattr(exc, "sqlite_errorcode", None)
            name = getattr(exc, "sqlite_errorname", None)
            print(f"AIOSQLITE_INSERT_FAILED {label} {type(exc).__name__}: {exc} code={code} name={name}")


async def main() -> int:
    print(f"DB {DB} EXISTS {DB.exists()} SIZE {DB.stat().st_size if DB.exists() else None}")
    insert_sqlite3("debug-sqlite3-main")
    insert_sqlite3_thread()
    await insert_aiosqlite("debug-aiosqlite-default", [])
    await insert_aiosqlite("debug-aiosqlite-temp-memory", ["pragma temp_store=memory"])
    await insert_aiosqlite("debug-aiosqlite-journal-memory", ["pragma journal_mode=memory"])
    await insert_aiosqlite("debug-aiosqlite-journal-wal", ["pragma journal_mode=wal"])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
