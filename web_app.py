import streamlit as st
from openai import OpenAI
from gtts import gTTS
from docx import Document
from io import BytesIO
import easyocr
from PIL import Image
import numpy as np
from duckduckgo_search import DDGS
from pypdf import PdfReader
from streamlit_mic_recorder import speech_to_text

# --- 1. 页面设置：回归极简 ---
st.set_page_config(
    page_title="程凯的全能助手", 
    page_icon="🤖", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.title("🤖 程凯的全能助手")
st.write("联网搜索 | 文档分析 | 语音交互 | 视觉识别")
st.divider() # 加一条优雅的分隔线

# --- 2. 初始化模型 (缓存) ---
@st.cache_resource
def load_ocr_model():
    return easyocr.Reader(['ch_sim', 'en'], gpu=False)

with st.spinner("正在启动视觉引擎..."):
    ocr_reader = load_ocr_model()

# --- 3. 获取 API Key ---
try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except:
    api_key = st.sidebar.text_input("请输入 DeepSeek API Key", type="password")

# --- 4. 核心功能函数 ---

def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if results:
                return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return "未搜索到相关信息。"
    except Exception as e:
        return f"搜索暂不可用: {e}"

def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages[:5]: # 只读前5页
        text += page.extract_text()
    return text

def speak_text(text):
    try:
        short_text = text[:100] # 只读前100字
        tts = gTTS(text=short_text, lang='zh-cn')
        tts.save("response.mp3")
        audio_file = open("response.mp3", "rb")
        audio_bytes = audio_file.read()
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
    except:
        pass

# --- 5. 侧边栏：清爽的功能区 ---
st.sidebar.header("🛠️ 功能面板")

# [插件 1] 联网开关
enable_search = st.sidebar.toggle("🌐 开启联网搜索")

# [插件 2] 知识库
st.sidebar.write("---")
uploaded_file = st.sidebar.file_uploader("📄 上传文档 (PDF)", type=["pdf"])
knowledge_base = ""
if uploaded_file:
    knowledge_base = read_pdf(uploaded_file)
    st.sidebar.success(f"已读取: {uploaded_file.name}")

# [插件 3] 拍照识图
st.sidebar.write("---")
with st.sidebar.expander("📷 拍照/识图"): # 用折叠卡片收纳，更整洁
    img_input = st.camera_input("点击拍照")
    ocr_text = ""
    if img_input:
        image = Image.open(img_input)
        img_array = np.array(image)
        results = ocr_reader.readtext(img_array)
        ocr_text = "\n".join([res[1] for res in results])
        st.info(f"识别内容：{ocr_text[:50]}...")

# [插件 4] 语音对讲
st.sidebar.write("---")
st.sidebar.write("🎤 语音输入")
audio_text = speech_to_text(language='zh', start_prompt="点击说话", stop_prompt="点击发送", just_once=True)

# --- 6. 聊天逻辑 ---
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "你好，程凯。系统已就绪，随时待命。"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 处理输入
final_user_input = None
if audio_text:
    final_user_input = audio_text
elif ocr_text:
    final_user_input = f"【图片内容】：\n{ocr_text}"
else:
    text_input = st.chat_input("输入你的问题...")
    if text_input:
        final_user_input = text_input

# --- 7. 生成回复 ---
if final_user_input:
    if not api_key:
        st.error("请先配置密钥")
    else:
        st.session_state.messages.append({"role": "user", "content": final_user_input})
        with st.chat_message("user"):
            st.write(final_user_input)

        # 构建 Prompt
        context_info = ""
        if enable_search:
            with st.status("🔍 正在检索网络...", expanded=False) as status:
                search_result = search_web(final_user_input)
                context_info += f"\n\n【搜索结果】：\n{search_result}\n"
                status.update(label="搜索完成", state="complete")
        
        if knowledge_base:
            context_info += f"\n\n【文档内容】：\n{knowledge_base[:2000]}...\n"

        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        system_prompt = f"""
        你是一个全能助手。请基于以下信息回答用户：
        {context_info}
        如果你有文档或搜索结果，请优先参考。保持回答简洁、专业。
        """

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": system_prompt}, *st.session_state.messages]
                    )
                    result = response.choices[0].message.content
                    st.write(result)
                    st.session_state.messages.append({"role": "assistant", "content": result})
                    speak_text(result)
                except Exception as e:
                    st.error(f"Error: {e}")