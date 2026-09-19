import sqlite3
import os

DB_PATH = "data/tickets.db"

os.makedirs("data", exist_ok=True)

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_no TEXT UNIQUE NOT NULL,
    device_model TEXT NOT NULL,
    fault_phenomenon TEXT NOT NULL,
    root_cause TEXT,
    solution TEXT,
    created_at TEXT
)
""")

data = [
    ("T-2024-001", "LBE-2000", "均衡电流异常",
     "均衡阈值设置错误",
     "修正均衡阈值为 2.35V，观察 30 分钟"),
    ("T-2024-002", "LBE-2000", "通讯中断",
     "RS485 接线松动",
     "重新压接 RS485 端子，检查 A/B 线"),
    ("T-2024-003", "LBE-2000", "通讯中断",
     "终端电阻未接",
     "在末端加装 120Ω 终端电阻"),
    ("T-2024-004", "LBE-2000", "均衡电流偏低",
     "均衡模块硬件故障",
     "更换均衡模块，重启后观察"),
    ("T-2024-005", "直流屏", "绝缘告警",
     "电缆受潮",
     "更换受潮电缆，干燥处理"),
    ("T-2024-006", "直流屏", "绝缘告警",
     "接线端子积尘",
     "清理端子积尘，恢复后复测绝缘电阻"),
    ("T-2024-007", "直流屏", "输出电压偏低",
     "整流模块故障",
     "更换整流模块，检查均流"),
    ("T-2024-008", "放电设备", "放电中途停止",
     "落后电池导致提前终止",
     "更换落后电池，重新放电测试"),
    ("T-2024-009", "放电设备", "放电电流异常",
     "放电参数设置错误",
     "修正放电电流设定值和终止电压"),
    ("T-2024-010", "LBE-2000", "均衡电流异常",
     "Modbus 通讯干扰",
     "检查屏蔽线单端接地，远离动力线"),
]

cursor.executemany(
    "INSERT INTO tickets (ticket_no, device_model, fault_phenomenon, root_cause, solution, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
    data
)

conn.commit()
conn.close()

print(f"已创建 {DB_PATH}，插入 {len(data)} 条工单记录")