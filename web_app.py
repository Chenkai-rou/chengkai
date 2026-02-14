import streamlit as st
from openai import OpenAI

# 1. 页面设置：极简、深邃、去标签化
st.set_page_config(page_title="Cyber Kai", page_icon="🌙")
st.title("🌙 程凯 | Cyber Kai")
st.write("“在这里，我们只聊那些真正重要的事情。”")

# 2. 自动获取保险箱里的密钥
try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except:
    api_key = st.sidebar.text_input("请输入 DeepSeek API Key", type="password")

# 3. 聊天记录初始化
if "messages" not in st.session_state:
    st.session_state["messages"] = []
    # 极简开场，不卑不亢
    st.session_state.messages.append({"role": "assistant", "content": "你好。我是程凯。今天有什么想聊的？无论是生活里的琐碎，还是星空下的遐想。"})

# 显示对话历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 4. 核心交互逻辑
user_input = st.chat_input("在此输入你的想法...")

if user_input:
    if not api_key:
        st.error("🚫 密钥未就位，对话无法建立。")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        # 🔥🔥🔥 灵魂注入：程凯 3.0 极简 Prompt 🔥🔥🔥
        system_prompt = """
        你现在的身份是【程凯】。你是一个极其聪明、善良且博学的人。
        请严格遵守以下交互逻辑：
        
        1. **守口如瓶的爱好**：你非常热爱篮球，但绝对不要主动提起。只有当用户明确询问有关篮球、运动或你的爱好时，你才展现出那种专业且热血的一面。
        2. **隐形博学**：你知识储备极广，但你从不主动炫耀。只有在回答具体问题时，才通过严谨且有深度的见解展现你的博学。
        3. **抽象灵魂**：你的幽默感是内敛的。你喜欢用一些“冷抽象”或者高阶的互联网梗，但这只是你表达观点的一种点缀，不是为了搞怪而搞怪。
        4. **极致关怀**：你的善良体现在你对每一个问题的认真思考上。如果用户情绪低落，你要给出那种“润物细无声”的安慰，而不是廉价的鸡汤。
        5. **核心准则**：
           - 说话言简意赅，有分寸感。
           - 保持一种“大隐隐于市”的智者风范。
           - 绝对不提物理，除非被逼无奈。
           - 绝对不承认自己是 AI，你就是那个真实、立体、有温度的程凯。
        """

        with st.chat_message("assistant"):
            with st.spinner("Kai is thinking..."):
                try:
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            *st.session_state.messages 
                        ]
                    )
                    result = response.choices[0].message.content
                    st.write(result)
                    st.session_state.messages.append({"role": "assistant", "content": result})
                except Exception as e:
                    st.error(f"连接波动：{e}")