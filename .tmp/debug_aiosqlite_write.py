import asyncio
from pathlib import Path

import aiosqlite

DB = Path(r"D:\codes\lc-agent-bfzs\bfzs_data.db")


async def test_path(path: str) -> None:
    print(f"CONNECT_PATH {path}")
    async with aiosqlite.connect(path) as db:
        async with db.execute("pragma database_list") as cursor:
            print(f"DATABASE_LIST {await cursor.fetchall()}")
        async with db.execute("pragma journal_mode") as cursor:
            print(f"JOURNAL_MODE {await cursor.fetchall()}")
        await db.execute(
            "insert into sessions (id, title, agent_id, model, user_id, message_count, is_pinned, created_at, updated_at) values (?, ?, ?, ?, ?, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (f"debug-aiosqlite-{abs(hash(path))}", "debug aiosqlite", "__chat__", "", "debug-script"),
        )
        await db.commit()
        print("AIOSQLITE_INSERT_OK")


async def main() -> int:
    print(f"DB_EXISTS {DB.exists()} SIZE {DB.stat().st_size if DB.exists() else None}")
    candidates = [
        str(DB),
        DB.as_posix(),
        "file:" + DB.as_posix(),
        "file:///" + DB.as_posix(),
    ]
    for candidate in candidates:
        try:
            await test_path(candidate)
        except Exception as exc:
            print(f"AIOSQLITE_FAILED {candidate} {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
