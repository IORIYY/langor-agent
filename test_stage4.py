from agent.graph import build_graph

app = build_graph()

tests = [
    ("LBE-2000 均衡电流异常怎么排查？", "fault"),
    ("通讯中断怎么办？", "fault"),
    ("直流屏绝缘告警怎么处理？", "fault"),
    ("最近哪些故障最常见？", "workorder"),
    ("工单总数是多少？", "workorder"),
    ("LBE-2000 最新 BOM 版本是什么？", "bom"),
    ("直流屏-DC110 有哪些版本变更？", "bom"),
    ("RS485 通讯参数怎么设置？", "knowledge"),
    ("你好", "boundary"),
    ("今天天气怎么样？", "boundary"),
]

passed = 0
failed = []

for i, (q, expected) in enumerate(tests, 1):
    print(f"\n{'='*60}")
    print(f"Q{i} [{expected}]: {q}")
    r = app.invoke({"user_query": q, "step_count": 0})

    intent = r.get("intent_type", "unknown")
    status = r.get("review_result", {}).get("status", "unknown")
    answer = r.get("final_answer", "")
    tools = [t.get("tool") for t in r.get("planned_tools", [])]

    if expected == "fault":
        ok = intent == "fault" and len(answer) > 100
    elif expected == "workorder":
        ok = intent == "workorder" and "workorder_analysis" in tools
    elif expected == "bom":
        ok = intent == "bom" and "bom_version_trace" in tools
    elif expected == "knowledge":
        ok = intent == "knowledge" and len(answer) > 50
    else:
        ok = status == "fail" or "资料不足" in answer or len(answer) == 0

    if ok:
        passed += 1
        print(f"✅ 通过（intent={intent}, tools={tools}, 报告 {len(answer)} 字）")
    else:
        failed.append((i, q, expected, intent, tools, status))
        print(f"❌ 失败（intent={intent}, tools={tools}, status={status}）")

print(f"\n{'='*60}")
print(f"通过：{passed}/{len(tests)}，命中率：{passed/len(tests)*100:.1f}%")

if failed:
    print("\n失败题目：")
    for i, q, exp, intent, tools, status in failed:
        print(f"  Q{i} [{exp}] {q}")
        print(f"    intent={intent}, tools={tools}, status={status}")