from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):
    """Agent 全局状态，贯穿整个状态机"""
    # 输入
    user_query: str
    intent_type: str
    extracted_entities: dict

    # 规划
    plan: list
    planned_tools: list

    # 执行
    tool_records: list
    retrieved_docs: list

    # 评审
    review_result: dict

    # 输出
    final_answer: str
    sources: list

    # 控制
    step_count: int
    error: Optional[str]

    # 拦截
    blocked: bool
    blocked_reason: str

    # 多轮对话记忆
    chat_history: list