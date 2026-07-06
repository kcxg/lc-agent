import asyncio
import os
import shutil
import sqlite3
import uuid
from pathlib import Path

import aiosqlite

ROOT = Path(r"D:\codes\lc-agent-bfzs")
DB = ROOT / "bfzs_data.db"
TMP = Path(r"D:\codes\lc-agent\.tmp")
SAME_DIR_COPY = ROOT / "debug_bfzs_data_same_dir_copy.db"
TMP_COPY = TMP / "debug_bfzs_data_tmp_copy_2.db"


def item_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def show_path(path: Path) -> None:
    try:
        stat = path.stat()
        print(
            "PATH",
            path,
            "exists=", path.exists(),
            "is_file=", path.is_file(),
            "is_dir=", path.is_dir(),
            "size=", stat.st_size,
            "mode=", oct(stat.st_mode),
        )
    except FileNotFoundError:
        print("PATH", path, "exists=False")


def write_probe(directory: Path) -> None:
    probe = directory / f".__lc_agent_write_probe_{uuid.uuid4().hex}.tmp"
    print("CASE write-probe", directory)
    try:
        probe.write_text("ok", encoding="utf-8")
        print("OK write-probe", probe)
    except Exception as exc:
        print("FAIL write-probe", type(exc).__name__, exc)
    finally:
        try:
            probe.unlink()
        except FileNotFoundError:
            pass
        except Exception as exc:
            print("FAIL unlink-probe", type(exc).__name__, exc)


def copy_probe(src: Path, dst: Path) -> None:
    print("CASE copy-probe", dst)
    try:
        if dst.exists():
            dst.unlink()
        for suffix in ("-journal", "-wal", "-shm"):
            side = dst.with_name(dst.name + suffix)
            if side.exists():
                side.unlink()
        shutil.copy2(src, dst)
        print("OK copy-probe", dst, "size", dst.stat().st_size)
    except Exception as exc:
        print("FAIL copy-probe", type(exc).__name__, exc)


def sqlite3_write(path: Path, name: str) -> None:
    print("CASE sqlite3", name, path)
    try:
        with sqlite3.connect(str(path), timeout=30) as con:
            print("database_list", con.execute("pragma database_list").fetchall())
            print("journal_mode", con.execute("pragma journal_mode").fetchall())
            print("quick_check", con.execute("pragma quick_check").fetchall())
            con.execute(
                "insert into sessions (id, title, agent_id, model, user_id, message_count, is_pinned, created_at, updated_at) values (?, ?, ?, ?, ?, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (item_id(f"sqlite3-{name}"), f"sqlite3 {name}", "__chat__", "", "debug-script"),
            )
            con.commit()
            print("OK sqlite3", name)
    except Exception as exc:
        print("FAIL sqlite3", name, type(exc).__name__, exc)


async def aiosqlite_write(path: Path, name: str) -> None:
    print("CASE aiosqlite", name, path)
    try:
        async with aiosqlite.connect(str(path), timeout=30) as db:
            async with db.execute("pragma database_list") as cur:
                print("database_list", await cur.fetchall())
            async with db.execute("pragma journal_mode") as cur:
                print("journal_mode", await cur.fetchall())
            async with db.execute("pragma quick_check") as cur:
                print("quick_check", await cur.fetchall())
            await db.execute(
                "insert into sessions (id, title, agent_id, model, user_id, message_count, is_pinned, created_at, updated_at) values (?, ?, ?, ?, ?, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (item_id(f"aiosqlite-{name}"), f"aiosqlite {name}", "__chat__", "", "debug-script"),
            )
            await db.commit()
            print("OK aiosqlite", name)
    except Exception as exc:
        print("FAIL aiosqlite", name, type(exc).__name__, exc, getattr(exc, "sqlite_errorcode", None), getattr(exc, "sqlite_errorname", None))


async def main() -> int:
    show_path(ROOT)
    show_path(DB)
    for suffix in ("-journal", "-wal", "-shm"):
        show_path(DB.with_name(DB.name + suffix))
    print("ACCESS root R/W/X", os.access(ROOT, os.R_OK), os.access(ROOT, os.W_OK), os.access(ROOT, os.X_OK))
    print("ACCESS db R/W", os.access(DB, os.R_OK), os.access(DB, os.W_OK))
    write_probe(ROOT)
    write_probe(TMP)
    copy_probe(DB, SAME_DIR_COPY)
    copy_probe(DB, TMP_COPY)
    show_path(SAME_DIR_COPY)
    show_path(TMP_COPY)
    sqlite3_write(DB, "original")
    sqlite3_write(SAME_DIR_COPY, "same-dir-copy")
    sqlite3_write(TMP_COPY, "tmp-copy")
    await aiosqlite_write(DB, "original")
    await aiosqlite_write(SAME_DIR_COPY, "same-dir-copy")
    await aiosqlite_write(TMP_COPY, "tmp-copy")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
