import json
import os
import shutil
from datetime import datetime


RESULTS_FILE = "data/eval_results.json"
HISTORY_DIR = "data/eval_history"
LATEST_FILE = f"{HISTORY_DIR}/latest.json"
PREV_FILE = f"{HISTORY_DIR}/previous.json"

# 退化阈值：通过率下降超过 5% 告警
REGRESSION_THRESHOLD = 0.05


def load_json(path: str) -> dict:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def compare_results(prev: dict, curr: dict) -> dict:
    """对比两次评估结果"""
    if prev is None:
        return {
            "is_regression": False,
            "reason": "首次运行，无对比基线",
            "prev_pass_rate": None,
            "curr_pass_rate": curr["summary"]["pass_rate"],
            "delta": None
        }

    prev_rate = prev["summary"]["pass_rate"]
    curr_rate = curr["summary"]["pass_rate"]
    delta = curr_rate - prev_rate

    is_regression = delta < -REGRESSION_THRESHOLD

    return {
        "is_regression": is_regression,
        "reason": f"通过率从 {prev_rate*100:.1f}% 变为 {curr_rate*100:.1f}%（Δ{delta*100:+.1f}%）",
        "prev_pass_rate": prev_rate,
        "curr_pass_rate": curr_rate,
        "delta": delta
    }


def generate_report(prev: dict, curr: dict, comparison: dict) -> str:
    """生成 Markdown 报告"""
    s = curr["summary"]
    lines = [
        "# Agent Evals 评估报告",
        f"\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n## 总体指标\n",
        "| 指标 | 数值 |",
        "|---|---|",
        f"| 通过率 | {s['pass_rate']*100:.1f}% |",
        f"| 意图识别 | {s['intent_rate']*100:.1f}% |",
        f"| 工具调用 | {s['tools_rate']*100:.1f}% |",
        f"| 要点命中 | {s['points_rate']*100:.1f}% |",
        f"| 总题数 | {s['total']} |",
        f"| 通过题数 | {s['passed']} |",
    ]

    if comparison["prev_pass_rate"] is not None:
        lines.extend([
            "\n## 与上次对比\n",
            f"- 上次通过率：{comparison['prev_pass_rate']*100:.1f}%",
            f"- 本次通过率：{comparison['curr_pass_rate']*100:.1f}%",
            f"- 变化：{comparison['delta']*100:+.1f}%",
        ])
        if comparison["is_regression"]:
            lines.append(f"\n⚠️ **退化告警**：{comparison['reason']}")
        else:
            lines.append(f"\n✅ 无退化：{comparison['reason']}")

    # 失败题目
    failed = [d for d in curr["details"] if not d["overall"]]
    if failed:
        lines.append("\n## 失败题目\n")
        lines.append("| ID | 问题 | 实际意图 | 缺要点 |")
        lines.append("|---|---|---|---|")
        for d in failed:
            missed = "、".join(d["missed_points"]) or "-"
            lines.append(f"| {d['id']} | {d['query']} | {d['actual_intent']} | {missed} |")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("Agent Evals 回归测试")
    print("=" * 60)

    # 读取当前结果
    curr = load_json(RESULTS_FILE)
    if curr is None:
        print(f"错误：找不到 {RESULTS_FILE}，请先运行 python eval_runner.py")
        return

    # 读取历史
    prev = load_json(PREV_FILE)

    # 对比
    comparison = compare_results(prev, curr)
    print(f"\n{comparison['reason']}")
    if comparison["is_regression"]:
        print(f"⚠️  检测到退化，请检查！")
    else:
        print(f"✅ 无退化")

    # 保存历史
    os.makedirs(HISTORY_DIR, exist_ok=True)
    if os.path.exists(LATEST_FILE):
        shutil.copy(LATEST_FILE, PREV_FILE)
    shutil.copy(RESULTS_FILE, LATEST_FILE)

    # 生成报告
    report = generate_report(prev, curr, comparison)
    report_path = "data/eval_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n报告已保存：{report_path}")

    # 打印报告内容
    print("\n" + "=" * 60)
    print(report)


if __name__ == "__main__":
    main()