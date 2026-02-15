import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="赛博聊天", page_icon="💬")

st.title("💬 与程凯深聊")

# --- 1. 深度思考开关 ---
# 这是一个高级开关，用来切换模型
use_deep_thinking = st.toggle("🧠 开启深度思考模式 (DeepSeek R1)", value=False)

if use_deep_thinking:
    st.caption("🚀 当前模式：深度推理 (R1)。适合：物理推导、考研数学、复杂逻辑。速度较慢，请耐心。")
    current_model = "deepseek-reasoner"  # DeepSeek 的推理模型代码
else:
    st.caption("⚡ 当前模式：快速问答 (V3)。适合：日常聊天、写作、翻译。速度极快。")
    current_model = "deepseek-chat"      # DeepSeek 的通用模型代码

# --- 2. 密钥处理 ---
try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except:
    api_key = st.sidebar.text_input("API Key", type="password")

# --- 3. 聊天逻辑 ---
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = [{"role": "assistant", "content": "我是程凯。请问是来聊物理的，还是聊人生的？"}]

for msg in st.session_state["chat_history"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("输入你的问题...")

if user_input:
    if not api_key:
        st.error("请输入 API Key")
    else:
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

        # 动态调整 Prompt
        if use_deep_thinking:
            system_prompt = "你是一个严谨的物理学家和数学家。请一步步进行链式推理(Chain of Thought)，不要跳过步骤。如果涉及公式，请使用 LaTeX 格式。"
        else:
            system_prompt = "你是一个幽默、博学且抽象的朋友程凯。说话风趣，不用太严肃。"

        with st.chat_message("assistant"):
            # 根据模式显示不同的加载提示
            spinner_text = "🧠 正在进行思维链推导 (R1)..." if use_deep_thinking else "⚡ 正在生成..."
            
            with st.spinner(spinner_text):
                try:
                    response = client.chat.completions.create(
                        model=current_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            *st.session_state["chat_history"]
                        ]
                    )
                    
                    # 尝试获取推理内容（如果是 R1 模型）
                    content = response.choices[0].message.content
                    
                    # 如果 API 返回了 reasoning_content (DeepSeek 特性)，我们可以展示它
                    # 注意：部分封装库可能暂时拿不到 reasoning_content，这里只展示最终结果保证稳定
                    
                    st.write(content)
                    st.session_state["chat_history"].append({"role": "assistant", "content": content})
                    
                except Exception as e:
                    st.error(f"思考过程中路断了: {e}")
