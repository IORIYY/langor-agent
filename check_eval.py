import json

r = json.load(open("data/eval_results.json", encoding="utf-8"))

print("=== 失败题目详情 ===\n")
for d in r["details"]:
    if not d["overall"]:
        print(f"{d['id']}: {d['query']}")
        print(f"  意图：{d['actual_intent']} | 工具：{d['actual_tools']}")
        print(f"  缺要点：{d['missed_points']}")
        print()