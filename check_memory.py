import sqlite3

conn = sqlite3.connect("data/memory.db")
cursor = conn.cursor()
cursor.execute("SELECT id, device_model, fault_phenomenon, confidence, access_count FROM memory")
rows = cursor.fetchall()
conn.close()

print(f"共 {len(rows)} 条记忆：")
for row in rows:
    print(f"  #{row[0]} | {row[1]} | {row[2]} | 置信度 {row[3]} | 访问 {row[4]} 次")