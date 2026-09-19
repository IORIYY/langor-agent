import streamlit as st
from agent import ask_stream

st.set_page_config(page_title="朗尔设备运维助手", page_icon="🔧")
st.title("🔧 朗尔设备运维助手")
st.caption("可提问：蓄电池均衡器、直流屏、放电设备等故障排查")

# 初始化历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 输入
if prompt := st.chat_input("输入故障描述，比如：LBE-2000 均衡电流异常怎么排查？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        answer = st.write_stream(ask_stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": answer})