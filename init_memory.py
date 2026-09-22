import sqlite3
import os

DB_PATH = "data/memory.db"

os.makedirs("data", exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_model TEXT,
    fault_phenomenon TEXT NOT NULL,
    solution TEXT NOT NULL,
    source_ticket TEXT,
    confidence REAL DEFAULT 0.8,
    verified INTEGER DEFAULT 0,
    access_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    last_accessed_at TEXT
)
""")

conn.commit()
conn.close()

print(f"已创建 {DB_PATH}（含 verified 字段）")