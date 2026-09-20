from agent.graph import build_graph

app = build_graph()

# 模拟多轮对话
chat_history = []

questions = [
    "LBE-2000 均衡电流异常怎么排查？",
    "那怎么修？",
    "流程呢？",
]

for q in questions:
    print(f"\n{'='*60}")
    print(f"用户：{q}")

    result = app.invoke({
        "user_query": q,
        "step_count": 0,
        "chat_history": chat_history
    })

    answer = result.get("final_answer", "")
    intent = result.get("intent_type", "unknown")
    tools = [t.get("tool") for t in result.get("planned_tools", [])]

    print(f"助手：{answer[:150]}...")
    print(f"[意图] {intent}")
    print(f"[工具] {tools}")

    chat_history.append({"role": "user", "content": q})
    chat_history.append({"role": "assistant", "content": answer})