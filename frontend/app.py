import streamlit as st
import requests
import json


# 设定后端地址，运行在8501，后端在8000
API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="卖家助手", layout="wide")
st.title("智能卖家助手")

# 侧导航栏
tabs = ["📝 文案生成", "📚 政策问答", "🤖 AI 客服"]
choice = st.sidebar.radio("选择功能", tabs)

# 文案生成
if choice == tabs[0]:
    st.header("📝 电商文案生成器")
    with st.form("copy_form"):
        product = st.text_input("商品名称", "人体工学无线鼠标")
        features = st.text_input("核心卖点（逗号分隔）", "静音按键, Type-C快充, 贴合手部曲线")
        tone = st.selectbox("语气风格", ["专业", "幽默", "热情", "夸张"])
        submitted = st.form_submit_button("✨ 生成文案")

    if submitted:
        with st.spinner("AI 正在创作..."):
            try:
                resp = requests.post(
                    f"{API_BASE}/api/generate_copy",
                    json={"product_name": product, "features": features, "tone": tone}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.success("生成成功！")
                    st.markdown(data["generated_copy"])
                else:
                    st.error(f"请求失败: {resp.text}")
            except Exception as e:
                st.error(f"连接后端失败: {e}")

elif choice == tabs[1]:
    st.header("📚 亚马逊内部政策问答")
    # 使用 session_state 来维护聊天历史
    if "policy_history" not in st.session_state:
        st.session_state.policy_history = []

    # 显示历史消息
    for msg in st.session_state.policy_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 输入框
    if question := st.chat_input("请输入您的政策问题："):
        # 添加用户消息到界面
        st.chat_message("human").markdown(question)
        st.session_state.policy_history.append({"role": "human", "content": question})

        with st.spinner("AI 正在检索知识库..."):
            # 构造请求体，将历史记录转换为 ChatMessage 格式
            chat_history = []
            for msg in st.session_state.policy_history[:-1]:  # 排除最新问题
                if msg["role"] == "human":
                    chat_history.append({"role": "human", "content": msg["content"]})
                else:
                    chat_history.append({"role": "ai", "content": msg["content"]})

            try:
                resp = requests.post(
                    f"{API_BASE}/api/rag/ask",
                    json={"question": question, "chat_history": chat_history}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    answer = data["answer"]
                else:
                    answer = f"❌ 请求失败: {resp.text}"
            except Exception as e:
                answer = f"❌ 连接后端失败: {e}"

        # 显示 AI 回复
        st.chat_message("ai").markdown(answer)
        st.session_state.policy_history.append({"role": "ai", "content": answer})

# ---------- AI 客服（Agent）----------
elif choice == tabs[2]:
    st.header("🤖 AI 多功能客服")
    if "agent_history" not in st.session_state:
        st.session_state.agent_history = []

    for msg in st.session_state.agent_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("您需要什么帮助？（例如：查订单、算汇率）"):
        st.chat_message("human").markdown(user_input)
        st.session_state.agent_history.append({"role": "human", "content": user_input})

        with st.spinner("AI 正在思考并调用工具..."):
            chat_history = []
            for msg in st.session_state.agent_history[:-1]:
                if msg["role"] == "human":
                    chat_history.append({"role": "human", "content": msg["content"]})
                else:
                    chat_history.append({"role": "ai", "content": msg["content"]})

            try:
                resp = requests.post(
                    f"{API_BASE}/api/agent/chat",
                    json={"question": user_input, "chat_history": chat_history}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    answer = data["answer"]
                    # 如果有中间步骤，显示工具调用详情
                    if data.get("intermediate_steps"):
                        with st.expander("🤖 AI 的思考过程"):
                            for step in data["intermediate_steps"]:
                                st.code(
                                    f"调用工具: {step['action']}\n参数: {json.dumps(step['args'], ensure_ascii=False)}")
                else:
                    answer = f"❌ 请求失败: {resp.text}"
            except Exception as e:
                answer = f"❌ 连接后端失败: {e}"

        st.chat_message("ai").markdown(answer)
        st.session_state.agent_history.append({"role": "ai", "content": answer})
