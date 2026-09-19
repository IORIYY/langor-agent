import sqlite3
import os

DB_PATH = "data/wecom.db"

os.makedirs("data", exist_ok=True)

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE wecom_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    msg_id TEXT UNIQUE NOT NULL,
    chat_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    send_time TEXT NOT NULL,
    content TEXT NOT NULL,
    is_effective INTEGER DEFAULT 0,
    reviewed INTEGER DEFAULT 0
)
""")

data = [
    ("msg001", "售后技术群", "张工", "2024-08-20 10:15",
     "LBE-2000 均衡电流异常，检查了一下是均衡阈值设置错了，改成 2.35V 就正常了", 1, 1),
    ("msg002", "售后技术群", "李工", "2024-08-21 14:30",
     "RS485 通讯中断，一般是接线松动或终端电阻没接，先检查这两处", 1, 1),
    ("msg003", "售后技术群", "王工", "2024-08-22 09:20",
     "直流屏绝缘告警，多数是电缆受潮，干燥处理一下就好", 1, 1),
    ("msg004", "售后技术群", "张工", "2024-08-23 16:45",
     "今天中午吃啥", 0, 0),
    ("msg005", "售后技术群", "刘工", "2024-08-24 11:00",
     "放电设备中途停止，多半是落后电池导致提前终止，换掉落后电池", 1, 1),
    ("msg006", "售后技术群", "李工", "2024-08-25 15:30",
     "Modbus 通讯干扰问题，屏蔽线必须单端接地，而且要远离动力线", 1, 1),
    ("msg007", "售后技术群", "陈工", "2024-08-26 10:00",
     "这个故障我之前遇到过，先检查参数再看硬件", 1, 1),
]

cursor.executemany(
    "INSERT INTO wecom_messages (msg_id, chat_id, sender, send_time, content, is_effective, reviewed) VALUES (?, ?, ?, ?, ?, ?, ?)",
    data
)

conn.commit()
conn.close()

print(f"已创建 {DB_PATH}，插入 {len(data)} 条企业微信消息")