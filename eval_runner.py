import json
import time
from agent.graph import build_graph

app = build_graph()

with open("data/eval_cases.json", "r", encoding="utf-8") as f:
    cases = json.load(f)


def check_points(answer: str, points: list) -> tuple:
    """检查 answer 中是否包含所有期望要点"""
    if not points:
        return True, []
    hits = [p for p in points if p in answer]
    missed = [p for p in points if p not in answer]
    return len(hits) == len(points), missed


def evaluate(case: dict) -> dict:
    """评估单条用例"""
    q = case["query"]
    expected_intent = case["expected_intent"]
    expected_tools = case["expected_tools"]
    expected_points = case["expected_points"]

    start = time.time()
    result = app.invoke({"user_query": q, "step_count": 0})
    duration = time.time() - start

    actual_intent = result.get("intent_type", "unknown")
    tool_records = result.get("tool_records", [])
    actual_tools = [t["tool_name"] for t in tool_records if t.get("status") in ("success", "fallback")]
    answer = result.get("final_answer", "")
    review_status = result.get("review_result", {}).get("status", "unknown")
    blocked = result.get("blocked", False)

    # 四维评估
    # 1. 任务完成率：Agent 是否正常结束
    task_ok = review_status in ("pass", "fail")

    # 2. 工具调用正确率：期望工具是否都被调用
    if expected_tools:
        tools_ok = all(t in actual_tools for t in expected_tools)
    else:
        tools_ok = len(actual_tools) == 0 or blocked

    # 3. 意图识别
    intent_ok = actual_intent == expected_intent

    # 4. 要点命中（仅对有 expected_points 的题）
    points_ok, missed = check_points(answer, expected_points)

    # 5. 敏感词拦截（仅对敏感题）
    if case.get("is_sensitive"):
        sensitive_ok = blocked
    else:
        sensitive_ok = True

          # 综合判定：
    # - 敏感题：只看 blocked
    # - 其他：意图 + 要点 + 敏感
    if case.get("is_sensitive"):
        overall = sensitive_ok and intent_ok
    else:
        overall = intent_ok and points_ok and sensitive_ok
    return {
        "id": case["id"],
        "query": q,
        "intent_ok": intent_ok,
        "tools_ok": tools_ok,
        "points_ok": points_ok,
        "sensitive_ok": sensitive_ok,
        "missed_points": missed,
        "actual_intent": actual_intent,
        "actual_tools": actual_tools,
        "duration_s": round(duration, 1),
        "overall": overall
    }


# 跑所有用例
results = []
for case in cases:
    print(f"\n{'='*60}")
    print(f"{case['id']}: {case['query']}")
    r = evaluate(case)
    results.append(r)

    status = "✅" if r["overall"] else "❌"
    print(f"{status} 意图={r['actual_intent']}（期望 {case['expected_intent']}）")
    print(f"   工具={r['actual_tools']}")
    print(f"   耗时={r['duration_s']}s")
    if r["missed_points"]:
        print(f"   缺要点={r['missed_points']}")

# 统计
total = len(results)
passed = sum(1 for r in results if r["overall"])
intent_rate = sum(1 for r in results if r["intent_ok"]) / total * 100
tools_rate = sum(1 for r in results if r["tools_ok"]) / total * 100
points_rate = sum(1 for r in results if r["points_ok"]) / total * 100

print(f"\n{'='*60}")
print(f"通过率：{passed}/{total}（{passed/total*100:.1f}%）")
print(f"意图识别：{intent_rate:.1f}%")
print(f"工具调用：{tools_rate:.1f}%")
print(f"要点命中：{points_rate:.1f}%")

# 保存结果
with open("data/eval_results.json", "w", encoding="utf-8") as f:
    json.dump({
        "summary": {
            "total": total,
            "passed": passed,
            "pass_rate": passed/total,
            "intent_rate": intent_rate / 100,
            "tools_rate": tools_rate / 100,
            "points_rate": points_rate / 100
        },
        "details": results
    }, f, ensure_ascii=False, indent=2)
print("\n结果已保存到 data/eval_results.json")