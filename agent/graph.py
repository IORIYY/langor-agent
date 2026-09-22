from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import (
    intent_node,
    planner_node,
    executor_node,
    reviewer_node,
    output_formatter_node,
    answer_check_node,
)


def build_graph():
    """构建 LangGraph 状态机"""
    graph = StateGraph(AgentState)

    graph.add_node("intent", intent_node)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("output", output_formatter_node)
    graph.add_node("answer_check", answer_check_node)

    graph.set_entry_point("intent")

    def route_after_intent(state: AgentState) -> str:
        if state.get("blocked"):
            print("[Graph] 敏感词拦截，跳过后续节点")
            return "end"
        if state.get("intent_type") == "boundary":
            print("[Graph] boundary 意图，跳过规划和执行")
            return "output"
        return "planner"

    graph.add_conditional_edges(
        "intent",
        route_after_intent,
        {
            "planner": "planner",
            "output": "output",
            "end": END,
        }
    )

    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "reviewer")

    def route_after_review(state: AgentState) -> str:
        status = state.get("review_result", {}).get("status", "fail")
        attempts = state.get("retrieval_attempts", 0)
        step_count = state.get("step_count", 0)

        if step_count >= 10:
            print("[Graph] 超过 10 步，强制结束")
            return "output"

        if status == "pass":
            return "output"
        elif status == "need_more_info":
            if attempts < 2:
                print(f"[Graph] 补检索（第 {attempts + 1} 次）")
                return "planner"
            print("[Graph] 补检索超限，直接输出")
            return "output"
        else:
            return "end"

    graph.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "output": "output",
            "planner": "planner",
            "end": END,
        }
    )

    graph.add_edge("output", "answer_check")
    graph.add_edge("answer_check", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    print("LangGraph 状态机构建成功")
    print("节点：intent → planner → executor → reviewer → output → answer_check")