import sqlite3
conn = sqlite3.connect(r"D:\codes\lc-agent-bfzs\bfzs_data.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [r[0] for r in cursor.fetchall()])
cursor.execute("PRAGMA table_info(session_meta)")
print("session_meta columns:", [r[1] for r in cursor.fetchall()])
try:
    cursor.execute("PRAGMA table_info(file_changes)")
    print("file_changes columns:", [r[1] for r in cursor.fetchall()])
except:
    print("file_changes table does not exist")
try:
    cursor.execute("SELECT id, git_base_hash FROM session_meta WHERE git_base_hash IS NOT NULL LIMIT 5")
    print("Sessions with git_base_hash:", cursor.fetchall())
except Exception as e:
    print("git_base_hash query error:", e)
try:
    cursor.execute("SELECT COUNT(*) FROM file_changes")
    print("file_changes count:", cursor.fetchone()[0])
except Exception as e:
    print("file_changes count error:", e)
conn.close()
