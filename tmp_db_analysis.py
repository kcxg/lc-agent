# 临时脚本：分析 lc-agent-bfzs 两个 SQLite 数据库的空间占用
import sqlite3
from pathlib import Path

DATA_DB = Path(r"D:\codes\lc-agent-bfzs\bfzs_data.db")
CHECK_DB = Path(r"D:\codes\lc-agent-bfzs\bfzs_checkpoints.db")


def analyze_db(path: Path, label: str):
    print(f"\n{'='*60}")
    print(f"数据库: {label} ({path})")
    print(f"文件大小: {path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"{'='*60}")

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. 表列表
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row["name"] for row in cur.fetchall()]
    print("\n表列表:", tables)

    # 2. 每表行数和估算大小（通过 dbstat）
    print("\n--- 表行数与占用空间 ---")
    for table in tables:
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            row_count = cur.fetchone()[0]
        except Exception as e:
            row_count = f"error: {e}"

        try:
            cur.execute(
                "SELECT SUM(pgsize) as bytes FROM dbstat WHERE name=?", (table,)
            )
            bytes_raw = cur.fetchone()[0] or 0
            size_mb = bytes_raw / 1024 / 1024
        except Exception as e:
            size_mb = f"error: {e}"

        print(f"  {table:30s} 行数: {row_count:>10}  占用: {size_mb if isinstance(size_mb, str) else f'{size_mb:.2f} MB':>12}")

    # 3. data 库大字段分析
    if label == "data":
        print("\n--- chat_ui_messages 大字段统计 ---")
        try:
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(LENGTH(content)) as total_content_bytes,
                    AVG(LENGTH(content)) as avg_content_bytes,
                    MAX(LENGTH(content)) as max_content_bytes,
                    SUM(LENGTH(tool_calls)) as total_tool_calls_bytes,
                    SUM(LENGTH(http_traces)) as total_http_traces_bytes
                FROM chat_ui_messages
            """)
            row = cur.fetchone()
            print(f"  总消息数: {row['total']}")
            print(f"  content 总大小: {row['total_content_bytes'] / 1024 / 1024:.2f} MB")
            print(f"  content 平均大小: {row['avg_content_bytes'] / 1024:.2f} KB")
            print(f"  content 最大单条: {row['max_content_bytes'] / 1024:.2f} KB")
            print(f"  tool_calls 总大小: {row['total_tool_calls_bytes'] / 1024 / 1024:.2f} MB")
            print(f"  http_traces 总大小: {row['total_http_traces_bytes'] / 1024 / 1024:.2f} MB")

            print("\n--- 按 role 分组的消息数 ---")
            cur.execute("SELECT role, COUNT(*) as cnt FROM chat_ui_messages GROUP BY role")
            for row in cur.fetchall():
                print(f"  {row['role']}: {row['cnt']}")

            print("\n--- 消息数 TOP 10 的会话 ---")
            cur.execute("""
                SELECT session_id, COUNT(*) as cnt, SUM(LENGTH(content)) as bytes
                FROM chat_ui_messages
                GROUP BY session_id
                ORDER BY bytes DESC
                LIMIT 10
            """)
            for row in cur.fetchall():
                print(f"  {row['session_id']}: {row['cnt']} 条, {row['bytes']/1024/1024:.2f} MB")
        except Exception as e:
            print(f"  分析失败: {e}")

    # 4. checkpoints 库大字段分析
    if label == "checkpoints":
        print("\n--- checkpoints 表统计 ---")
        try:
            cur.execute("SELECT COUNT(*) FROM checkpoints")
            print(f"  checkpoints 行数: {cur.fetchone()[0]}")

            cur.execute("SELECT COUNT(*) FROM writes")
            print(f"  writes 行数: {cur.fetchone()[0]}")

            # SQLite 中 checkpoints 表结构：thread_id, checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(LENGTH(checkpoint)) as total_checkpoint_bytes,
                    AVG(LENGTH(checkpoint)) as avg_checkpoint_bytes,
                    MAX(LENGTH(checkpoint)) as max_checkpoint_bytes,
                    SUM(LENGTH(metadata)) as total_metadata_bytes
                FROM checkpoints
            """)
            row = cur.fetchone()
            print(f"  checkpoint 字段总大小: {row['total_checkpoint_bytes'] / 1024 / 1024:.2f} MB")
            print(f"  checkpoint 字段平均: {row['avg_checkpoint_bytes'] / 1024:.2f} KB")
            print(f"  checkpoint 字段最大: {row['max_checkpoint_bytes'] / 1024:.2f} KB")
            print(f"  metadata 字段总大小: {row['total_metadata_bytes'] / 1024 / 1024:.2f} MB")

            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(LENGTH(value)) as total_value_bytes,
                    AVG(LENGTH(value)) as avg_value_bytes,
                    MAX(LENGTH(value)) as max_value_bytes
                FROM writes
            """)
            row = cur.fetchone()
            print(f"  writes.value 总大小: {row['total_value_bytes'] / 1024 / 1024:.2f} MB")
            print(f"  writes.value 平均: {row['avg_value_bytes'] / 1024:.2f} KB")
            print(f"  writes.value 最大: {row['max_value_bytes'] / 1024:.2f} KB")

            print("\n--- checkpoints 按 thread_id TOP 10（按总大小） ---")
            cur.execute("""
                SELECT thread_id, COUNT(*) as cnt, SUM(LENGTH(checkpoint)) as bytes
                FROM checkpoints
                GROUP BY thread_id
                ORDER BY bytes DESC
                LIMIT 10
            """)
            for row in cur.fetchall():
                print(f"  {row['thread_id']}: {row['cnt']} 个 checkpoint, {row['bytes']/1024/1024:.2f} MB")
        except Exception as e:
            print(f"  分析失败: {e}")

    conn.close()


if __name__ == "__main__":
    analyze_db(DATA_DB, "data")
    analyze_db(CHECK_DB, "checkpoints")
