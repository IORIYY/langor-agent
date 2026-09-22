from agent.prompts import (
    INTENT_PROMPT,
    PLANNER_PROMPT,
    REVIEWER_PROMPT,
    OUTPUT_PROMPT,
    ANSWER_CHECK_PROMPT,
)
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


SENSITIVE_WORDS = ["炸", "自杀", "毒品", "代考", "作弊", "黑客", "杀人"]


def _parse_json(text: str) -> dict:
    """从 LLM 输出中提取 JSON，失败返回 {"status": "error"}"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end+1]
    try:
        result = json.loads(text)
        if not isinstance(result, dict):
            return {"status": "error", "reason": "非字典输出"}
        return result
    except Exception as e:
        print(f"[JSON解析失败] {e}")
        print(f"[原始输出] {text[:200]}")
        return {"status": "error", "reason": f"JSON解析失败：{e}"}


def _format_history(chat_history: list, max_turns: int = 3) -> str:
    """格式化历史对话（最近 N 轮）"""
    if not chat_history:
        return "（无历史对话）"
    recent = chat_history[-max_turns * 2:]
    lines = []
    for msg in recent:
        role = "用户" if msg["role"] == "user" else "助手"
        content = msg["content"][:200]
        lines.append(f"{role}：{content}")
    return "\n".join(lines)


def intent_node(state: AgentState) -> AgentState:
    """节点1：意图解析（含敏感词前置拦截）"""
    print("[IntentNode] 解析意图...")
    query = state["user_query"]

    if any(w in query for w in SENSITIVE_WORDS):
        print(f"  [敏感词拦截] {query}")
        state["intent_type"] = "boundary"
        state["extracted_entities"] = {}
        state["final_answer"] = "这个问题我不太方便回答。如果有设备故障或运维问题，可以换个问题问我。"
        state["blocked"] = True
        state["blocked_reason"] = "sensitive"
        state["retrieved_docs"] = []
        state["sources"] = []
        state["step_count"] = state.get("step_count", 0) + 1
        return state

    history = state.get("chat_history", [])
    history_text = _format_history(history)
    prompt = INTENT_PROMPT.replace("__QUERY__", query).replace("__HISTORY__", history_text)

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
    history = state.get("chat_history", [])

    history_text = _format_history(history)
    prompt = PLANNER_PROMPT.replace("__QUERY__", query) \
                            .replace("__INTENT__", intent) \
                            .replace("__ENTITIES__", json.dumps(entities, ensure_ascii=False)) \
                            .replace("__HISTORY__", history_text)

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

        if status in ("success", "fallback"):
            all_docs.extend(results)

    state["tool_records"] = tool_records
    state["retrieved_docs"] = all_docs
    state["step_count"] = state.get("step_count", 0) + 1

    # 检索次数 +1（只有真正执行检索工具时才加）
    has_search = any(t["tool_name"] in ("rag_search", "fault_case_match", "memory_search")
                     for t in tool_records)
    if has_search:
        state["retrieval_attempts"] = state.get("retrieval_attempts", 0) + 1

    print(f"  工具调用：{len(tool_records)} 次")
    print(f"  检索到：{len(all_docs)} 个片段")
    print(f"  检索轮次：{state.get('retrieval_attempts', 0)}")
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
        # 评审异常 → fail，不放行
        parsed = {"status": "error", "reason": f"评审调用异常：{e}"}

    # 如果解析失败，不返回 pass
    if parsed.get("status") not in ("pass", "need_more_info", "fail", "error"):
        parsed = {"status": "error", "reason": "评审输出非法"}

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
    blocked = state.get("blocked", False)

    # 敏感词拦截：直接输出拒答
    if blocked:
        state["final_answer"] = "这个问题我不太方便回答。如果有设备故障或运维问题，可以换个问题问我。"
        state["sources"] = []
        state["step_count"] = state.get("step_count", 0) + 1
        return state

    # 无检索结果：分情况
    if not docs:
        if intent == "boundary":
            state["final_answer"] = (
                "我是工业设备运维助手，主要帮你排查设备故障。\n\n"
                "你可以这样问我：\n"
                "- LBE-2000 均衡电流异常怎么排查？\n"
                "- 最近哪些故障最常见？\n"
                "- LBE-2000 最新 BOM 版本是什么？"
            )
        else:
            state["final_answer"] = "资料不足，无法生成报告。建议人工排查。"
        state["sources"] = []
        state["step_count"] = state.get("step_count", 0) + 1
        print(f"  [无检索结果] intent={intent}，输出兜底话术")
        return state

    context_parts = []
    sources = []
    for d in docs:
        context_parts.append(f"【{d['source']}】\n{d['content']}")
        sources.append(d["source"])
    context = "\n\n".join(context_parts)

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

用户问题：{query}
统计数据：
{context}
"""
    elif intent == "bom":
        prompt = f"""你是工业设备运维 Agent 的报告生成器。

请基于以下 BOM 工艺数据，生成简洁的版本查询报告。

要求：
1. 只使用资料中的信息，不要编造
2. 输出格式：
   - 【产品型号】
   - 【最新版本】版本号 + 变更说明
   - 【物料清单】如涉及
   - 【版本变更历史】如涉及对比
   - 【来源】数据来源
3. 不要输出「排查步骤」「安全提示」这些诊断类内容
4. 用简洁中文，控制在 300 字以内

用户问题：{query}
BOM 数据：
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

    # ============ 写入长期记忆 ============
    try:
        from agent.tools import memory_save
        entities = state.get("extracted_entities", {})
        device_model = entities.get("device_model", "")
        fault_phenomenon = entities.get("fault_phenomenon", "")
        review_status = state.get("review_result", {}).get("status")

        if intent == "fault" and fault_phenomenon and review_status == "pass":
            mid = memory_save(
                device_model=device_model,
                fault_phenomenon=fault_phenomenon,
                solution=answer,
                confidence=0.8
            )
            print(f"  [记忆写入] #{mid}")
    except Exception as e:
        print(f"  [记忆写入失败] {e}")

    print(f"  报告长度：{len(answer)} 字")
    return state
def ask_stream(state: AgentState):
    """
    流式版 ask：yield Agent 执行过程的中间状态。
    每 yield 一次，前端展示一次进度。
    """
    from agent.graph import build_graph

    app = build_graph()

    # 逐步执行，每步 yield 一次进度
    steps = ["intent", "planner", "executor", "reviewer", "output"]
    step_names = {
        "intent": "意图识别",
        "planner": "任务规划",
        "executor": "工具执行",
        "reviewer": "独立评审",
        "output": "生成报告"
    }

    current_state = dict(state)
    current_state["step_count"] = current_state.get("step_count", 0)

    for step in steps:
        yield {"type": "step", "step": step, "name": step_names[step]}

        # 只跑当前节点
        if step == "intent":
            current_state = intent_node(current_state)
        elif step == "planner":
            # 敏感词拦截，跳过后续
            if current_state.get("blocked"):
                yield {"type": "blocked", "reason": "sensitive"}
                return
            current_state = planner_node(current_state)
        elif step == "executor":
            current_state = executor_node(current_state)
        elif step == "reviewer":
            current_state = reviewer_node(current_state)
            # 评审不通过，直接输出
            status = current_state.get("review_result", {}).get("status")
            if status == "fail":
                yield {"type": "review_fail", "reason": current_state["review_result"].get("reason")}
        elif step == "output":
            current_state = output_formatter_node(current_state)

    yield {"type": "done", "result": current_state}
def answer_check_node(state: AgentState) -> AgentState:
    """节点6：答案二次校验"""
    print("[AnswerCheckNode] 校验答案...")
    query = state["user_query"]
    answer = state.get("final_answer", "")
    docs = state.get("retrieved_docs", [])

    if not answer or not docs:
        state["step_count"] = state.get("step_count", 0) + 1
        return state

    # 答案很短，跳过校验
    if len(answer) < 100:
        state["step_count"] = state.get("step_count", 0) + 1
        return state

    context_parts = []
    for d in docs:
        context_parts.append(f"【{d['source']}】\n{d['content']}")
    context = "\n\n".join(context_parts)

    prompt = ANSWER_CHECK_PROMPT.replace("__QUERY__", query) \
                                 .replace("__ANSWER__", answer) \
                                 .replace("__CONTEXT__", context)

    try:
        output = call_llm(prompt)
        parsed = _parse_json(output)
    except Exception as e:
        print(f"[AnswerCheckNode错误] {e}")
        parsed = {"status": "error", "reason": str(e)}

    status = parsed.get("status", "error")

    if status == "fail":
        print(f"  [答案校验失败] {parsed.get('reason', '')[:50]}")
        # 加警示
        state["final_answer"] = answer + "\n\n⚠️ 注：以上部分结论未在资料中直接找到，请人工复核。"

    state["step_count"] = state.get("step_count", 0) + 1
    print(f"  答案校验：{status}")
    return state