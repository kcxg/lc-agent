import sqlite3
from pathlib import Path

DB = Path(r"D:\codes\lc-agent-bfzs\bfzs_data.db")
ROOT = DB.parent


def main() -> int:
    print(f"DB {DB}")
    print(f"DB_EXISTS {DB.exists()} SIZE {DB.stat().st_size if DB.exists() else None}")
    print(f"ROOT_EXISTS {ROOT.exists()}")

    probe = ROOT / "__write_probe.tmp"
    try:
        probe.write_text("ok", encoding="utf-8")
        print("DIR_WRITE_OK")
    finally:
        if probe.exists():
            probe.unlink()

    journal = ROOT / "bfzs_data.db-journal"
    wal = ROOT / "bfzs_data.db-wal"
    shm = ROOT / "bfzs_data.db-shm"
    for path in [journal, wal, shm]:
        print(f"SIDE_FILE {path.name} EXISTS {path.exists()} SIZE {path.stat().st_size if path.exists() else None}")

    con = sqlite3.connect(str(DB))
    try:
        print(f"DATABASE_LIST {con.execute('pragma database_list').fetchall()}")
        print(f"JOURNAL_MODE {con.execute('pragma journal_mode').fetchall()}")
        print(f"LOCKING_MODE {con.execute('pragma locking_mode').fetchall()}")
        print(f"FOREIGN_KEYS {con.execute('pragma foreign_keys').fetchall()}")
        print(f"TABLE_INFO_SESSIONS {con.execute('pragma table_info(sessions)').fetchall()}")
        print("SESSIONS_DDL_BEGIN")
        for row in con.execute("select type, name, sql from sqlite_master where tbl_name='sessions' or sql like '%sessions%' order by type, name").fetchall():
            print(row)
        print("SESSIONS_DDL_END")
        con.execute("insert into sessions (id, title, agent_id, model, user_id, message_count, is_pinned, created_at, updated_at) values (?, ?, ?, ?, ?, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)", ("debug-sqlite3-direct", "debug sqlite3 direct", "__chat__", "", "debug-script"))
        con.commit()
        print("SQLITE3_INSERT_OK")
    finally:
        con.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
