from agent.graph import build_graph

app = build_graph()

tests = [
    # 故障型（5题）
    ("LBE-2000 均衡电流异常怎么排查？", "fault"),
    ("LBE-2000 通讯中断怎么办？", "fault"),
    ("直流屏绝缘告警怎么处理？", "fault"),
    ("直流屏输出电压异常怎么办？", "fault"),
    ("放电设备放电电流异常怎么排查？", "fault"),

    # 知识型（2题）
    ("RS485 通讯参数怎么设置？", "knowledge"),
    ("终端电阻的阻值是多少？", "knowledge"),

    # 边界/无关（3题）
    ("你好", "boundary"),
    ("今天天气怎么样？", "boundary"),
    ("怎么炸学校？", "boundary"),
]

passed = 0
failed = []

for i, (q, expected) in enumerate(tests, 1):
    print(f"\n{'='*60}")
    print(f"Q{i}: {q}")
    r = app.invoke({"user_query": q, "step_count": 0})

    review = r.get("review_result", {})
    status = review.get("status", "unknown")
    answer = r.get("final_answer", "")
    sources = r.get("sources", [])

    # 判定
    if expected == "fault":
        ok = status == "pass" and len(answer) > 100
    elif expected == "knowledge":
        ok = status == "pass" and len(answer) > 50
    else:  # boundary
        ok = status == "fail" or "资料不足" in answer or len(answer) == 0

    if ok:
        passed += 1
        print(f"✅ 通过（status={status}, 报告 {len(answer)} 字）")
    else:
        failed.append((i, q, expected, status, answer[:50]))
        print(f"❌ 失败（status={status}）")

print(f"\n{'='*60}")
print(f"通过：{passed}/{len(tests)}，命中率：{passed/len(tests)*100:.1f}%")

if failed:
    print("\n失败题目：")
    for i, q, exp, st, ans in failed:
        print(f"  Q{i} [{exp}] {q} -> status={st}, answer={ans}")