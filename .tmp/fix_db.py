import sqlite3
import os

db_path = r'D:\codes\lc-agent-bfzs\bfzs_data.db'
new_path = r'D:\codes\lc-agent-bfzs\bfzs_data_new.db'
backup_path = r'D:\codes\lc-agent-bfzs\bfzs_data_corrupt_backup.db'

# Clean up previous attempt
for p in [new_path, backup_path]:
    if os.path.exists(p):
        os.remove(p)

old = sqlite3.connect(db_path)
old_cur = old.cursor()

tables = old_cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'").fetchall()
indexes = old_cur.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchall()

new = sqlite3.connect(new_path)
new_cur = new.cursor()

for name, sql in tables:
    new_cur.execute(sql)

for (idx_sql,) in indexes:
    try:
        new_cur.execute(idx_sql)
    except:
        pass

for name, _ in tables:
    cols_info = old_cur.execute(f'PRAGMA table_info([{name}])').fetchall()
    col_names = ', '.join(c[1] for c in cols_info)
    placeholders = ', '.join('?' for _ in cols_info)

    copied = 0
    skipped = 0
    try:
        cursor = old.execute(f'SELECT {col_names} FROM [{name}]')
        while True:
            try:
                row = cursor.fetchone()
                if row is None:
                    break
                try:
                    new_cur.execute(f'INSERT INTO [{name}] ({col_names}) VALUES ({placeholders})', row)
                    copied += 1
                except Exception as ie:
                    skipped += 1
            except sqlite3.DatabaseError:
                skipped += 1
                break
    except sqlite3.DatabaseError as e:
        print(f'  {name}: cannot open cursor - {e}')
        continue

    print(f'  {name}: {copied} copied, {skipped} skipped')

new.commit()

r = new_cur.execute('PRAGMA integrity_check').fetchone()
print(f'\nNew DB integrity: {r}')
print(f'New DB size: {os.path.getsize(new_path):,} bytes')

new.close()
old.close()

os.rename(db_path, backup_path)
os.rename(new_path, db_path)

for ext in ['-wal', '-shm']:
    orig = db_path + ext
    if os.path.exists(orig):
        os.remove(orig)
        print(f'Removed {orig}')

print(f'\nDone! Corrupt backup: {backup_path}')
print(f'Clean DB: {db_path}')
