from agent.graph import build_graph

app = build_graph()
result = app.invoke({
    "user_query": "LBE-2000 均衡电流异常怎么排查？",
    "step_count": 0
})

print("\n" + "=" * 50)
print("工具记录：")
for t in result.get("tool_records", []):
    print(f"  {t}")

print(f"\n检索到 {len(result.get('retrieved_docs', []))} 个片段")
print(f"总步数：{result.get('step_count')}")