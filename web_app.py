import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
from docx import Document
from io import BytesIO

# 1. 页面设置
st.set_page_config(page_title="Cyber Kai 3.0", page_icon="🏀")
st.title("🏀 程凯 | 智能交互版")

# 2. 自动获取密钥
try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except:
    api_key = st.sidebar.text_input("请输入 DeepSeek API Key", type="password")

# 3. 功能函数：文字转语音
def speak_text(text):
    # 生成语音文件
    tts = gTTS(text=text, lang='zh-cn')
    tts.save("response.mp3")
    # 读取并播放
    audio_file = open("response.mp3", "rb")
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
    # 播放完清理文件
    audio_file.close()

# 4. 功能函数：生成 Word 文档
def export_to_word(chat_history):
    doc = Document()
    doc.add_heading('程凯 3.0 聊天记录导出', 0)
    for msg in chat_history:
        role_name = "程凯" if msg["role"] == "assistant" else "我"
        doc.add_paragraph(f"{role_name}: {msg['content']}")
    
    # 将文件存入内存缓冲区
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# 5. 侧边栏：导出功能
if st.session_state.get("messages"):
    st.sidebar.title("🛠️ 导出与管理")
    word_data = export_to_word(st.session_state.messages)
    st.sidebar.download_button(
        label="📥 导出为 Word 文档",
        data=word_data,
        file_name="chat_history.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    if st.sidebar.button("🗑️ 清空当前对话"):
        st.session_state.messages = []
        st.rerun()

# 6. 聊天记录显示
if "messages" not in st.session_state:
    st.session_state["messages"] = []
    st.session_state.messages.append({"role": "assistant", "content": "你好，我是程凯。今天有什么想聊的？"})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 7. 交互逻辑
user_input = st.chat_input("说点什么...")

if user_input:
    if not api_key:
        st.error("🚫 密钥未就位。")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        system_prompt = """
        你现在的身份是【程凯】。你极其聪明、善良且博学，热爱篮球但从不主动显摆。
        你的说话风格抽象幽默，自带一种高级的优雅感。
        当用户心情不好时，你会给出非常有同理心的关怀。
        注意：绝对不要提物理，保持神秘的智者风范。
        """

        with st.chat_message("assistant"):
            with st.spinner("Kai is typing & thinking..."):
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
                    
                    # ✨ 亮点功能：让 AI 说话
                    speak_text(result)
                    
                except Exception as e:
                    st.error(f"连接波动：{e}")