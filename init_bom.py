import sqlite3
import os

DB_PATH = "data/bom.db"

os.makedirs("data", exist_ok=True)

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE bom_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code TEXT NOT NULL,
    version TEXT NOT NULL,
    change_note TEXT,
    components TEXT,
    created_at TEXT
)
""")

data = [
    ("LBE-2000", "v1.0", "初始版本", "主板×1，均衡模块×4，电源模块×1，通讯模块×1", "2023-01-15"),
    ("LBE-2000", "v2.0", "均衡模块升级为 LBE-M2", "主板×1，均衡模块LBE-M2×4，电源模块×1，通讯模块×1", "2024-03-20"),
    ("LBE-2000", "v2.1", "通讯模块支持 Modbus TCP", "主板×1，均衡模块LBE-M2×4，电源模块×1，通讯模块LBE-C3×1", "2024-09-10"),
    ("直流屏-DC110", "v1.0", "初始版本", "整流模块×3，监控单元×1，电池巡检×1", "2023-05-01"),
    ("直流屏-DC110", "v2.0", "整流模块升级，支持均流", "整流模块LBE-R2×3，监控单元×1，电池巡检×1", "2024-06-15"),
    ("放电设备-FD500", "v1.0", "初始版本", "放电模块×2，控制单元×1，并网逆变×1", "2023-08-20"),
    ("放电设备-FD500", "v1.5", "增加孤岛保护", "放电模块×2，控制单元×1，并网逆变LBE-INV2×1", "2024-11-05"),
]

cursor.executemany(
    "INSERT INTO bom_versions (product_code, version, change_note, components, created_at) VALUES (?, ?, ?, ?, ?)",
    data
)

conn.commit()
conn.close()

print(f"已创建 {DB_PATH}，插入 {len(data)} 条 BOM 记录")