from agent.tools import memory_search, memory_save

# 保存一条记忆
mid = memory_save(
    device_model="LBE-2000",
    fault_phenomenon="均衡电流异常",
    solution="修正均衡阈值 2.35V，观察30分钟",
    confidence=0.8
)
print(f"保存 ID: {mid}")

# 检索
r = memory_search("均衡电流异常")
print(f"状态: {r['status']}")
print(f"结果数: {len(r['results'])}")
for item in r["results"]:
    print(f"  {item['content']}")