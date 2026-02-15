import streamlit as st
from duckduckgo_search import DDGS
from pypdf import PdfReader
import easyocr
from PIL import Image
import numpy as np

st.set_page_config(page_title="黑科技工具箱", page_icon="🛠️")
st.title("🛠️ 程凯的黑科技军火库")

# 导航栏
tab1, tab2, tab3 = st.tabs(["🌐 联网搜索", "📄 考研资料读取", "👁️ 拍照识图"])

# --- Tab 1: 搜索 ---
with tab1:
    st.header("全网信息检索")
    query = st.text_input("输入你想搜的内容（例如：2026 德国物理博士 申请条件）")
    if st.button("开始搜索"):
        with st.spinner("正在扫描全球网络..."):
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=5))
                    for r in results:
                        st.markdown(f"### [{r['title']}]({r['href']})")
                        st.write(r['body'])
                        st.divider()
            except Exception as e:
                st.error(f"搜索失败: {e}")

# --- Tab 2: PDF ---
with tab2:
    st.header("PDF 智能解析")
    uploaded_file = st.file_uploader("上传你的复习资料", type=["pdf"])
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages[:3]: # 只展示前3页预览
            text += page.extract_text()
        st.text_area("文档内容预览", text, height=300)

# --- Tab 3: OCR ---
with tab3:
    st.header("视觉神经连接")
    # 缓存模型
    @st.cache_resource
    def load_model():
        return easyocr.Reader(['ch_sim', 'en'], gpu=False)
    
    reader = load_model()
    
    img_input = st.camera_input("拍摄题目或文字")
    if img_input:
        with st.spinner("视觉中枢解析中..."):
            image = Image.open(img_input)
            img_array = np.array(image)
            results = reader.readtext(img_array)
            text = "\n".join([res[1] for res in results])
            st.success("识别结果：")
            st.code(text)
