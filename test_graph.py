from agent.graph import build_graph

app = build_graph()
result = app.invoke({
    "user_query": "LBE-2000 均衡电流异常怎么排查？",
    "step_count": 0
})

print("\n" + "=" * 50)
print("最终报告：")
print(result.get("final_answer", ""))

print(f"\n来源：{result.get('sources', [])}")
print(f"总步数：{result.get('step_count')}")
print(f"评审结果：{result.get('review_result')}")