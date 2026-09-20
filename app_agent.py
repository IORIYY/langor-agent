import streamlit as st
from agent.graph import build_graph

st.set_page_config(
    page_title="朗尔设备运维 AI Agent",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 朗尔设备运维 AI Agent")
st.caption("基于 LangGraph 三分离状态机 | 5 个工具 | 多源融合")

with st.sidebar:
    st.header("🤖 Agent 架构")
    st.markdown("""
**三分离状态机**
- **IntentNode**：意图识别
- **PlannerNode**：任务规划
- **ExecutorNode**：工具执行
- **ReviewerNode**：独立评审
- **OutputFormatter**：结构化输出

**5 个工具**
- `rag_search`：知识库混合检索
- `fault_case_match`：历史工单匹配
- `workorder_analysis`：工单统计
- `bom_version_trace`：BOM 查询
- `wecom_chat_fetch`：企业微信经验
- `memory_search`：长期记忆

**多源融合**
SOP + 历史工单 + 企业微信 + 长期记忆
""")

    st.divider()
    if st.button("🔄 清空对话"):
        st.session_state.messages = []
        st.rerun()

# 初始化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "app" not in st.session_state:
    with st.spinner("加载 Agent..."):
        st.session_state.app = build_graph()

# 显示历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("meta"):
            with st.expander("🔍 查看 Agent 执行细节"):
                st.json(msg["meta"])

# 输入
if prompt := st.chat_input("输入问题，如：LBE-2000 均衡电流异常怎么排查？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent 正在处理..."):
            chat_history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1]
            ]
            result = st.session_state.app.invoke({
                "user_query": prompt,
                "step_count": 0,
                "chat_history": chat_history
            })

        # 回答兜底
        answer = (result.get("final_answer") or "").strip()
        if not answer:
            if result.get("blocked"):
                answer = "这个问题我不太方便回答。如果有设备故障或运维问题，可以换个问题问我。"
            elif result.get("intent_type") == "boundary":
                answer = (
                    "我是工业设备运维助手，主要帮你排查设备故障。\n\n"
                    "你可以这样问我：\n"
                    "- LBE-2000 均衡电流异常怎么排查？\n"
                    "- 最近哪些故障最常见？\n"
                    "- LBE-2000 最新 BOM 版本是什么？"
                )
            else:
                answer = "资料不足，无法生成报告。建议人工排查。"

        st.markdown(answer)

        # 元信息
        intent = result.get("intent_type", "-")
        tools = [t.get("tool") for t in result.get("planned_tools", [])]
        sources = result.get("sources", [])
        review = result.get("review_result", {})
        blocked = result.get("blocked", False)

        meta = {
            "意图": intent,
            "工具": tools,
            "来源": sources,
            "评审": review,
            "敏感拦截": blocked,
            "原始final_answer": result.get("final_answer", "")
        }

        with st.expander("🔍 查看 Agent 执行细节"):
            st.json(meta)

        if sources:
            st.caption("📚 来源：" + "、".join(sources))

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "meta": meta
    })