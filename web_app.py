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

# --- 1. 页面与动态氛围背景 (CSS) ---
st.set_page_config(page_title="Cyber Kai 5.0", page_icon="🌌", layout="wide")

# 注入动态赛博朋克背景 CSS
st.markdown("""
    <style>
    /* 全局背景动画 */
    @keyframes gradient {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    .stApp {
        background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        color: #e0e0e0;
    }
    /* 输入框霓虹特效 */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid #00d2ff;
        box-shadow: 0 0 5px #00d2ff;
    }
    /* 侧边栏半透明 */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 12, 41, 0.9);
        border-right: 1px solid #302b63;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌌 赛博程凯：全知全能版")
st.caption("“联网、识图、听觉、知识库……我的进化没有终点。”")

# --- 2. 初始化缓存 (避免重复加载模型) ---
@st.cache_resource
def load_ocr_model():
    return easyocr.Reader(['ch_sim', 'en'], gpu=False)

ocr_reader = load_ocr_model()

# --- 3. 获取 API Key ---
try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except:
    api_key = st.sidebar.text_input("请输入 DeepSeek API Key", type="password")

# --- 4. 核心功能函数 ---

# 功能 A: 联网搜索
def search_web(query):
    try:
        results = DDGS().text(query, max_results=3)
        if results:
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return "未搜索到相关信息。"
    except Exception as e:
        return f"搜索功能暂时离线: {e}"

# 功能 B: 读取 PDF 文件
def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    # 为了防止 token 爆炸，只读前 5 页
    for page in reader.pages[:5]:
        text += page.extract_text()
    return text

# 功能 C: 语音播报
def speak_text(text):
    try:
        # 只读前100个字，避免太吵
        short_text = text[:100]
        tts = gTTS(text=short_text, lang='zh-cn')
        tts.save("response.mp3")
        audio_file = open("response.mp3", "rb")
        audio_bytes = audio_file.read()
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
    except:
        pass

# --- 5. 侧边栏：多功能控制台 ---
st.sidebar.header("🛠️ 赛博义体插件")

# [插件 1] 联网开关
enable_search = st.sidebar.toggle("🌐 开启联网搜索模式")

# [插件 2] 知识库上传
uploaded_file = st.sidebar.file_uploader("📂 上传考研/物理资料 (PDF)", type=["pdf"])
knowledge_base = ""
if uploaded_file:
    with st.spinner("正在读取神经记忆..."):
        knowledge_base = read_pdf(uploaded_file)
        st.sidebar.success(f"已加载资料：{uploaded_file.name}")

# [插件 3] 拍照识图 (保留之前的)
st.sidebar.write("---")
img_input = st.sidebar.camera_input("👁️ 视觉传感器")
ocr_text = ""
if img_input:
    image = Image.open(img_input)
    img_array = np.array(image)
    results = ocr_reader.readtext(img_array)
    ocr_text = "\n".join([res[1] for res in results])
    st.sidebar.info(f"识别结果：{ocr_text[:50]}...")

# [插件 4] 语音对讲
st.sidebar.write("---")
st.sidebar.write("🎤 按下说话 (自动发送)")
audio_text = speech_to_text(language='zh', start_prompt="🟢 点我录音", stop_prompt="🔴 停止并发送", just_once=True)

# --- 6. 聊天逻辑处理 ---
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "系统已重启。我是程凯 5.0。我在听，也在看。"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 决定用户的输入内容 (语音优先，其次是识图，最后是打字)
final_user_input = None

if audio_text:
    final_user_input = audio_text
elif ocr_text:
    final_user_input = f"【系统提示：用户上传了一张图片，文字内容如下】\n{ocr_text}"
else:
    text_input = st.chat_input("输入指令...")
    if text_input:
        final_user_input = text_input

# --- 7. AI 处理与生成 ---
if final_user_input:
    if not api_key:
        st.error("请先配置密钥！")
    else:
        # 显示用户消息
        st.session_state.messages.append({"role": "user", "content": final_user_input})
        with st.chat_message("user"):
            st.write(final_user_input)

        # 构建超级 Prompt
        context_info = ""
        
        # 1. 如果开启联网，先去搜
        if enable_search:
            with st.status("🌐 正在检索全球网络...", expanded=True) as status:
                search_result = search_web(final_user_input)
                context_info += f"\n\n【联网搜索结果】：\n{search_result}\n"
                status.update(label="搜索完成", state="complete", expanded=False)
        
        # 2. 如果有文件，挂载知识库
        if knowledge_base:
            context_info += f"\n\n【本地知识库内容】：\n{knowledge_base[:3000]}...\n"

        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        system_prompt = f"""
        你现在的身份是【程凯 5.0】。
        
        【能力面板】
        1. 你拥有【联网能力】，如果提供了搜索结果，请基于结果回答。
        2. 你拥有【知识库】，如果提供了本地资料，请优先参考。
        3. 你依然保持【抽象、博学、篮球迷】的人设，但更加全知全能。
        
        【当前外部信息】
        {context_info}
        
        请结合上述信息回答用户。如果是语音输入，回答要简练。
        """

        with st.chat_message("assistant"):
            with st.spinner("正在调用算力..."):
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
                    
                    # 自动朗读回答
                    speak_text(result)
                    
                except Exception as e:
                    st.error(f"系统过载：{e}")