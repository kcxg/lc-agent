import sqlite3
import os

db_path = r'D:\codes\lc-agent-bfzs\bfzs_data.db'
recover_path = r'D:\codes\lc-agent-bfzs\bfzs_data_recovered.db'

# Attempt 1: online backup
try:
    src = sqlite3.connect(db_path)
    dst = sqlite3.connect(recover_path)
    src.backup(dst)
    dst.close()
    src.close()
    v = sqlite3.connect(recover_path)
    r = v.execute('PRAGMA integrity_check').fetchone()
    print(f'Backup integrity: {r}')
    v.close()
    print(f'Size: {os.path.getsize(recover_path):,}')
except Exception as e:
    print(f'Backup approach failed: {e}')
    try:
        os.remove(recover_path)
    except:
        pass

# Attempt 2: check which tables are accessible
print('\n--- Table scan ---')
try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f'Tables found: {[t[0] for t in tables]}')
    for t in tables:
        try:
            count = cur.execute(f'SELECT count(*) FROM [{t[0]}]').fetchone()[0]
            print(f'  {t[0]}: {count} rows OK')
        except Exception as te:
            print(f'  {t[0]}: CORRUPTED - {te}')
    conn.close()
except Exception as e2:
    print(f'Table scan also failed: {e2}')
