import json
from agent.state import AgentState
from agent.llm import call_llm
from agent.prompts import INTENT_PROMPT, PLANNER_PROMPT
from agent.tools import execute_tool


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

        tool_records.append({
            "tool_name": tool_name,
            "input_params": params,
            "status": result["status"],
            "duration_ms": result["duration_ms"],
            "result_count": len(result.get("results", [])),
            "error": result.get("error")
        })

        if result["status"] == "success":
            all_docs.extend(result.get("results", []))

    state["tool_records"] = tool_records
    state["retrieved_docs"] = all_docs
    state["step_count"] = state.get("step_count", 0) + 1

    print(f"  工具调用：{len(tool_records)} 次")
    print(f"  检索到：{len(all_docs)} 个片段")
    return state


def reviewer_node(state: AgentState) -> AgentState:
    """节点4：独立评审（骨架，Day4实现）"""
    print("[ReviewerNode] 评审结果...")
    state["review_result"] = {"status": "pass", "reason": "骨架"}
    state["step_count"] = state.get("step_count", 0) + 1
    return state


def output_formatter_node(state: AgentState) -> AgentState:
    """节点5：格式化输出（骨架，Day4实现）"""
    print("[OutputFormatterNode] 格式化输出...")
    state["final_answer"] = "骨架输出"
    state["sources"] = []
    state["step_count"] = state.get("step_count", 0) + 1
    return state