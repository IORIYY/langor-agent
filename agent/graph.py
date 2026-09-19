from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import (
    intent_node,
    planner_node,
    executor_node,
    reviewer_node,
    output_formatter_node,
)


def build_graph():
    """构建 LangGraph 状态机"""
    graph = StateGraph(AgentState)

    graph.add_node("intent", intent_node)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("output", output_formatter_node)

    graph.set_entry_point("intent")

    graph.add_edge("intent", "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "reviewer")

    def route_after_review(state: AgentState) -> str:
        status = state.get("review_result", {}).get("status", "fail")
        step_count = state.get("step_count", 0)

        if step_count >= 8:
            print("[Graph] 超过 8 轮，强制结束")
            return "end"

        if status == "pass":
            return "output"
        elif status == "need_more_info":
            return "planner"
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

    graph.add_edge("output", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    print("LangGraph 状态机构建成功")
    print("节点列表：intent → planner → executor → reviewer → output")