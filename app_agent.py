import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import streamlit as st
from agent.service import invoke
from agent.tool_registry import list_tools

st.set_page_config(
    page_title="朗尔设备运维 AI Agent",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 朗尔设备运维 AI Agent")
st.caption("基于 LangGraph 三分离状态机 | 6 个工具 | 多源融合")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("工具数", len(list_tools()))
with col2:
    st.metric("意图类型", 5)
with col3:
    st.metric("Evals 通过率", "95%")
with col4:
    st.metric("检索层", "4 层")

with st.sidebar:
    st.header("🤖 Agent 架构")

    st.markdown("**三分离状态机**")
    st.code(
        "用户问题\n"
        "   ↓\n"
        "IntentNode（意图识别）\n"
        "   ↓\n"
        "PlannerNode（任务规划）\n"
        "   ↓\n"
        "ExecutorNode（工具执行）\n"
        "   ↓\n"
        "ReviewerNode（独立评审）\n"
        "   ├─ pass → OutputFormatter\n"
        "   ├─ need_more → PlannerNode\n"
        "   └─ fail → 结束",
        language="text"
    )

    st.markdown("**6 个工具**")
    st.markdown(
        "- `rag_search`：知识库混合检索\n"
        "- `fault_case_match`：历史工单\n"
        "- `workorder_analysis`：工单统计\n"
        "- `bom_version_trace`：BOM 查询\n"
        "- `wecom_chat_fetch`：企业微信\n"
        "- `memory_search`：长期记忆"
    )

    st.divider()
    if st.button("🔄 清空对话"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.info(
        "👋 我是朗尔设备运维助手，可以帮你：\n\n"
        "- **故障诊断**：LBE-2000 均衡电流异常怎么排查？\n"
        "- **工单统计**：最近哪些故障最常见？\n"
        "- **BOM 查询**：LBE-2000 最新 BOM 版本是什么？\n"
        "- **知识问答**：RS485 通讯参数怎么设置？"
    )

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("meta"):
            with st.expander("🔍 查看 Agent 执行细节"):
                st.json(msg["meta"])

if prompt := st.chat_input("输入问题，如：LBE-2000 均衡电流异常怎么排查？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        chat_history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[:-1]
        ]

        with st.status("🤖 Agent 正在处理...", expanded=True) as status:
            st.write("▶ 调用统一服务入口...")
            final_result = invoke(prompt, chat_history=chat_history)
            status.update(label="✅ 完成", state="complete", expanded=False)

        answer = (final_result.get("final_answer") or "").strip()
        if not answer:
            if final_result.get("blocked"):
                answer = "这个问题我不太方便回答。"
            elif final_result.get("intent_type") == "boundary":
                answer = "我是工业设备运维助手，主要帮你排查设备故障。"
            else:
                answer = "资料不足，无法生成报告。"

        st.markdown(answer)

        intent = final_result.get("intent_type", "-")
        tools = [t.get("tool") for t in final_result.get("planned_tools", [])]
        sources = final_result.get("sources", [])
        review = final_result.get("review_result", {})
        blocked = final_result.get("blocked", False)

        meta = {
            "意图": intent,
            "工具": tools,
            "来源": sources,
            "评审": review,
            "敏感拦截": blocked
        }

        if sources:
            with st.expander("📚 来源详情"):
                for s in sources:
                    st.write(f"- {s}")

        with st.expander("🔍 完整执行细节"):
            st.json(meta)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "meta": meta
        })