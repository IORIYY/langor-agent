from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):
    """Agent 全局状态，贯穿整个状态机"""
    # 输入
    user_query: str                    # 用户原始问题
    intent_type: str                   # 意图：fault/knowledge/boundary
    extracted_entities: dict           # 提取的实体（设备型号等）

    # 规划
    plan: list                         # 子任务列表
    planned_tools: list                # 计划调用的工具

    # 执行
    tool_records: list                 # 工具调用记录
    retrieved_docs: list               # 检索到的文档片段

    # 评审
    review_result: dict                # {status, reason}

    # 输出
    final_answer: str                  # 最终报告
    sources: list                      # 来源

    # 控制
    step_count: int                    # 当前步数
    error: Optional[str]               # 错误信息