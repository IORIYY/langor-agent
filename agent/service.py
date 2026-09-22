"""
Agent 统一服务入口。

所有调用方（Streamlit / Evals）都通过这里执行，
保证行为一致。
"""
from agent.graph import build_graph
from agent.state import AgentState

_app = None


def get_app():
    global _app
    if _app is None:
        _app = build_graph()
    return _app


def invoke(query: str, chat_history: list = None) -> dict:
    """同步执行，返回最终 state"""
    app = get_app()
    return app.invoke({
        "user_query": query,
        "step_count": 0,
        "retrieval_attempts": 0,
        "chat_history": chat_history or []
    })


def stream(query: str, chat_history: list = None):
    """流式执行，yield 每个节点的状态更新"""
    app = get_app()
    state = {
        "user_query": query,
        "step_count": 0,
        "retrieval_attempts": 0,
        "chat_history": chat_history or []
    }
    for event in app.stream(state):
        yield event