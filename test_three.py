from agent.graph import build_graph

app = build_graph()
for q in [
    "LBE-2000 均衡电流异常怎么排查？",
    "通讯中断怎么办？",
    "今天天气怎么样？",
]:
    print(f"\n{'='*60}")
    print(f"问题：{q}")
    r = app.invoke({"user_query": q, "step_count": 0})
    print(f"\n报告：\n{r.get('final_answer', '')}")
    print(f"来源：{r.get('sources', [])}")
    print(f"评审：{r.get('review_result')}")