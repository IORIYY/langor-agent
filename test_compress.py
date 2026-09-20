from agent.tools import memory_save

# 构造一条超长方案（超过 500 字）
long_solution = "排查步骤：" + "第一步检查参数；" * 100  # 约 800 字

print(f"原长度: {len(long_solution)} 字")

mid = memory_save(
    device_model="LBE-2000",
    fault_phenomenon="测试压缩",
    solution=long_solution,
    confidence=0.8
)
print(f"保存 ID: {mid}")

# 查看实际存储长度
import sqlite3
conn = sqlite3.connect("data/memory.db")
cursor = conn.cursor()
cursor.execute("SELECT solution FROM memory WHERE id = ?", (mid,))
sol = cursor.fetchone()[0]
conn.close()

print(f"存后长度: {len(sol)} 字")
print(f"压缩后内容: {sol[:200]}...")