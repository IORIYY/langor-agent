import json
from agent.state import AgentState
from agent.llm import call_llm
from agent.prompts import (
    INTENT_PROMPT,
    PLANNER_PROMPT,
    REVIEWER_PROMPT,
    OUTPUT_PROMPT,
)
from agent.tool_registry import execute_tool
import agent.tools  # 触发 @register_tool 装饰器


def _parse_json(text: str) -> dict:
    """从 LLM 输出中提取 JSON"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end+1]
    try:
        return json.loads(text)
    except Exception as e:
        print(f"[JSON解析失败] {e}")
        print(f"[原始输出] {text[:200]}")
        return {}


def intent_node(state: AgentState) -> AgentState:
    """节点1：意图解析"""
    print("[IntentNode] 解析意图...")
    query = state["user_query"]

    prompt = INTENT_PROMPT.replace("__QUERY__", query)
    try:
        output = call_llm(prompt)
        parsed = _parse_json(output)
    except Exception as e:
        print(f"[IntentNode错误] {e}")
        parsed = {}

    state["intent_type"] = parsed.get("intent_type", "fault")
    state["extracted_entities"] = parsed.get("entities", {})
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"  意图：{state['intent_type']}")
    print(f"  实体：{state['extracted_entities']}")
    return state


def planner_node(state: AgentState) -> AgentState:
    """节点2：任务规划"""
    print("[PlannerNode] 规划任务...")
    query = state["user_query"]
    intent = state.get("intent_type", "fault")
    entities = state.get("extracted_entities", {})

    prompt = PLANNER_PROMPT.replace("__QUERY__", query) \
                            .replace("__INTENT__", intent) \
                            .replace("__ENTITIES__", json.dumps(entities, ensure_ascii=False))
    try:
        output = call_llm(prompt)
        parsed = _parse_json(output)
    except Exception as e:
        print(f"[PlannerNode错误] {e}")
        parsed = {}

    state["plan"] = parsed.get("plan", [])
    state["planned_tools"] = parsed.get("planned_tools", [])
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"  计划：{state['plan']}")
    print(f"  工具：{[t.get('tool') for t in state['planned_tools']]}")
    return state


def executor_node(state: AgentState) -> AgentState:
    """节点3：执行工具"""
    print("[ExecutorNode] 执行工具...")
    planned_tools = state.get("planned_tools", [])

    tool_records = []
    all_docs = []

    for tool_call in planned_tools:
        tool_name = tool_call.get("tool")
        params = tool_call.get("params", {})

        print(f"  调用 {tool_name}({params})...")
        result = execute_tool(tool_name, params)

        status = result.get("status", "unknown")
        results = result.get("results", [])

        tool_records.append({
            "tool_name": tool_name,
            "input_params": params,
            "status": status,
            "duration_ms": result.get("duration_ms", 0),
            "result_count": len(results),
            "error": result.get("error")
        })

        if status == "success":
            all_docs.extend(results)

    state["tool_records"] = tool_records
    state["retrieved_docs"] = all_docs
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"  工具调用：{len(tool_records)} 次")
    print(f"  检索到：{len(all_docs)} 个片段")
    return state


def reviewer_node(state: AgentState) -> AgentState:
    """节点4：独立评审"""
    print("[ReviewerNode] 评审结果...")
    query = state["user_query"]
    docs = state.get("retrieved_docs", [])

    if not docs:
        state["review_result"] = {"status": "fail", "reason": "无检索结果"}
        state["step_count"] = state.get("step_count", 0) + 1
        print("  评审：fail（无检索结果）")
        return state

    context_parts = []
    for d in docs:
        context_parts.append(f"【{d['source']}】\n{d['content']}")
    context = "\n\n".join(context_parts)

    prompt = REVIEWER_PROMPT.replace("__QUERY__", query).replace("__CONTEXT__", context)

    try:
        output = call_llm(prompt)
        parsed = _parse_json(output)
    except Exception as e:
        print(f"[ReviewerNode错误] {e}")
        parsed = {"status": "pass", "reason": "解析失败，默认通过"}

    state["review_result"] = parsed
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"  评审：{parsed.get('status')} - {parsed.get('reason', '')[:50]}")
    return state


def output_formatter_node(state: AgentState) -> AgentState:
    """节点5：格式化输出"""
    print("[OutputFormatterNode] 格式化输出...")
    query = state["user_query"]
    intent = state.get("intent_type", "fault")
    docs = state.get("retrieved_docs", [])

    if not docs:
        state["final_answer"] = "资料不足，无法生成报告。建议人工排查。"
        state["sources"] = []
        state["step_count"] = state.get("step_count", 0) + 1
        return state

    context_parts = []
    sources = []
    for d in docs:
        context_parts.append(f"【{d['source']}】\n{d['content']}")
        sources.append(d["source"])
    context = "\n\n".join(context_parts)

    # 根据意图选不同 Prompt
    if intent == "workorder":
        prompt = f"""你是工业设备运维 Agent 的报告生成器。

请基于以下工单统计数据，生成简洁的统计报告。

要求：
1. 只使用资料中的信息，不要编造
2. 输出格式：
   - 【统计结果】列出 TOP 故障 / 设备
   - 【简要分析】1-2 句话
   - 【来源】数据来源
3. 不要输出「排查步骤」「所需配件」「安全提示」这些诊断类内容
4. 用简洁中文，控制在 300 字以内
5. 直接输出报告，不要复述指令

用户问题：{query}
统计数据：
{context}
"""
    else:
        prompt = OUTPUT_PROMPT.replace("__QUERY__", query).replace("__CONTEXT__", context)

    try:
        answer = call_llm(prompt)
    except Exception as e:
        answer = f"生成报告失败：{e}"

    state["final_answer"] = answer
    state["sources"] = list(set(sources))
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"  报告长度：{len(answer)} 字")
    return state