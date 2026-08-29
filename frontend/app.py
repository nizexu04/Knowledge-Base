# frontend/app.py
import streamlit as st
import requests
import json
import base64
from pathlib import Path

# ----- 页面配置 -----
st.set_page_config(
    page_title="Personal Note Knowledge Base",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ----- 自定义 CSS -----
st.markdown("""
<style>
    /* 1. 全局字体 */
    html, body, .stApp, div, p, h1, h2, h3, span {
        font-family: "Segoe UI", "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif !important;
    }

    /* 2. 隐藏默认顶栏和页脚 */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 3. 主内容区紧凑 */
    .main > div {
        padding-top: 0rem !important;
    }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
    }

    /* 4. 标题样式 */
    .custom-title {
        text-align: center;
        margin-bottom: 1.2rem;
        padding: 0.2rem 0 0.4rem 0;
    }
    .custom-title h1 {
        font-family: "Georgia", "Palatino Linotype", "Book Antiqua", serif !important;
        font-size: 2.6rem !important;
        font-weight: 600 !important;
        font-style: italic;
        color: #1f2937 !important;
        margin: 0 !important;
        padding: 0 !important;
        letter-spacing: 0.02em;
        display: inline-block;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.08);
    }
    .custom-title .subtitle {
        font-size: 1.4rem !important;
        font-weight: 400 !important;
        color: #6b7280 !important;
        margin-left: 0.3rem;
        letter-spacing: 0.04em;
    }

    /* 5. 输入框 */
    .stChatInput > div {
        max-width: 100% !important;
    }

    /* 6. 加载动画 */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .loading-spinner {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2.5px solid #d1d5db;
        border-top-color: #6366f1;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        vertical-align: middle;
        margin-right: 0.4rem;
    }

    /* 7. Sidebar 浮层覆盖，贴满左边 */
    [data-testid="stSidebar"] {
        position: fixed !important;
        left: 0 !important;
        top: 0 !important;
        height: 100vh !important;
        z-index: 999;
        border-right: 1px solid #e5e7eb !important;
        overflow: hidden !important;
        background: #f8f9fb !important;
    }
    [data-testid="stSidebar"]::-webkit-scrollbar {
        display: none !important;
    }
    [data-testid="stSidebar"][aria-expanded="false"] {
        transform: translateX(-100%) !important;
    }
    /* 让 sidebar 内部内容撑满 */
    [data-testid="stSidebar"] > div {
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        background: #f8f9fb !important;
    }
    /* 内容区域可滚动，标题固定 */
    [data-testid="stSidebarContent"] {
        flex: 1 !important;
        overflow-y: auto !important;
    }
    [data-testid="stSidebarContent"]::-webkit-scrollbar {
        display: none !important;
    }
    [data-testid="stSidebarContent"] > div:first-child {
        position: sticky !important;
        top: 0 !important;
        z-index: 10 !important;
        background: #f8f9fb !important;
    }
    /* 统一 sidebar 头部背景 */
    [data-testid="stSidebarHeader"] {
        background: #f8f9fb !important;
    }

    /* 右侧拖拽条：缩短 + 默认隐藏，hover 时显示 */
    [data-testid="stSidebar"] ~ div[data-testid="stSidebarBorder"],
    [data-testid="stSidebar"] + div[data-testid="stBorderDragHandle"],
    [data-testid="stSidebar"] ~ div:first-of-type {
        width: 4px !important;
        min-width: 4px !important;
        max-width: 4px !important;
        opacity: 0 !important;
        transition: opacity 0.2s !important;
    }
    [data-testid="stSidebar"] ~ div[data-testid="stSidebarBorder"]:hover,
    [data-testid="stSidebar"] + div[data-testid="stBorderDragHandle"]:hover,
    [data-testid="stSidebar"] ~ div:first-of-type:hover {
        opacity: 1 !important;
    }

    /* 8. Sidebar 标题样式 */
    [data-testid="stSidebar"] .sidebar-title {
        font-family: "Georgia", "Palatino Linotype", "Book Antiqua", serif !important;
        font-size: 1.6rem !important;
        font-weight: 600 !important;
        font-style: italic;
        color: #1f2937 !important;
        letter-spacing: 0.02em;
        margin-bottom: 0.2rem;
        padding-top: 0.5rem;
    }

    /* 9. Sidebar 内部分割线 */
    [data-testid="stSidebar"] hr {
        margin: 0.4rem 0 !important;
    }

    /* 8. Sidebar 历史记录样式 */
    [data-testid="stSidebar"] .history-btn {
        display: block;
        width: 100%;
        text-align: left;
        padding: 0.45rem 0.6rem;
        margin: 0.15rem 0;
        border-radius: 0.4rem;
        font-size: 0.85rem;
        color: #374151;
        background: transparent;
        border: none;
        cursor: pointer;
        transition: background 0.15s;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    [data-testid="stSidebar"] .history-btn:hover {
        background: #f3f4f6;
    }
    [data-testid="stSidebar"] .history-btn-active {
        background: #eef2ff;
        color: #4338ca;
        font-weight: 600;
    }

    /* 11. 右侧装饰图片 */
    .right-deco-img {
        position: fixed;
        right: 20px;
        bottom: 80px;
        z-index: 50;
        pointer-events: none;
        text-align: center;
        will-change: transform;
        transform: translateZ(0);
    }
    .right-deco-img-idle {
        position: fixed;
        right: 60px;
        bottom: 80px;
        z-index: 50;
        pointer-events: none;
        text-align: center;
        will-change: transform;
        transform: translateZ(0);
    }
    .right-deco-img img, .right-deco-img-idle img {
        height: 24vh;
        width: auto;
        object-fit: contain;
    }
    .right-deco-status {
        font-size: 1rem;
        color: #4b5563;
        margin-bottom: 8px;
        min-height: 1.5em;
        white-space: nowrap;
        font-weight: 500;
    }
    
    /* 12. 右上角统计信息 */
    .right-stats {
        position: fixed;
        right: 20px;
        top: 80px;
        z-index: 50;
        text-align: right;
        font-size: 0.85rem;
        color: #6b7280;
        will-change: transform;
        transform: translateZ(0);
    }
    .right-stats .stat-item {
        margin-bottom: 0.3rem;
    }
    .right-stats .stat-value {
        font-weight: 600;
        color: #1f2937;
    }
    
    /* 13. Chroma 分数图表 */
    .score-chart {
        position: fixed;
        right: 20px;
        top: 160px;
        z-index: 50;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        min-width: 180px;
        will-change: transform;
        transform: translateZ(0);
    }
    .score-chart .chart-title {
        font-size: 0.8rem;
        color: #6b7280;
        margin-bottom: 6px;
        font-weight: 500;
    }
    .score-chart .bar-item {
        display: flex;
        align-items: center;
        margin-bottom: 4px;
        font-size: 0.75rem;
    }
    .score-chart .bar-label {
        width: 25px;
        color: #374151;
        font-weight: 500;
    }
    .score-chart .bar-bg {
        flex: 1;
        height: 12px;
        background: #e5e7eb;
        border-radius: 6px;
        overflow: hidden;
        margin: 0 6px;
    }
    .score-chart .bar-fill {
        height: 100%;
        border-radius: 6px;
        background: linear-gradient(90deg, #6366f1, #818cf8);
    }
    .score-chart .bar-value {
        width: 35px;
        text-align: right;
        color: #6b7280;
    }
    .score-chart .best-hint {
        font-size: 0.7rem;
        color: #9ca3af;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ----- 自定义标题 -----
st.markdown("""
<div class="custom-title">
    <h1>
        Personal Note Knowledge Base
        <span class="subtitle">Q&A System · Powered by RAG</span>
    </h1>
</div>
""", unsafe_allow_html=True)

# ----- 右侧装饰图片 -----
import subprocess, tempfile

@st.cache_data
def load_heic_as_png(heic_path):
    """将 HEIC 文件转换为 PNG 并返回 base64 编码（带缓存）"""
    heic_path = Path(heic_path)
    if not heic_path.exists():
        return None
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    # 先用 sips 转 PNG（自动处理 HEIC 方向元数据）
    subprocess.run(["sips", "-s", "format", "png", str(heic_path), "--out", tmp_path],
                    capture_output=True)
    img_bytes = Path(tmp_path).read_bytes()
    Path(tmp_path).unlink()
    return base64.b64encode(img_bytes).decode()

def render_score_chart(scores):
    """生成 Chroma 分数图表 HTML（分数越低条越长）"""
    if not scores:
        return ""
    bars_html = ""
    for s in scores:
        # 分数越低越好，用 1-score 表示匹配度
        fill = max(0, 1 - s["score"])
        bars_html += (
            f'<div class="bar-item">'
            f'<span class="bar-label">{s["label"]}</span>'
            f'<div class="bar-bg"><div class="bar-fill" style="width: {fill * 100:.1f}%"></div></div>'
            f'<span class="bar-value">{s["score"]:.4f}</span>'
            f'</div>'
        )
    return (
        f'<div class="score-chart">'
        f'<div class="chart-title">Chroma Similarity Scores</div>'
        f'{bars_html}'
        f'<div class="best-hint">← lower = better match</div>'
        f'</div>'
    )

image_dir = Path(__file__).parent.parent / "image"
img_idle = load_heic_as_png(str(image_dir / "HEIF图像.heic"))
img_loading = load_heic_as_png(str(image_dir / "HEIF图像 2.HEIC"))
img_generating = load_heic_as_png(str(image_dir / "HEIF图像 3.HEIC"))

if "deco_status" not in st.session_state:
    st.session_state.deco_status = "idle"

status_map = {
    "idle": ("What can I do for you?", img_idle),
    "loading": ("Loading embedding model (BAAI/bge-m3)...", img_loading),
    "generating": ("Generating answer...", img_generating),
}
status_text, current_img = status_map[st.session_state.deco_status]

deco_placeholder = st.empty()
if current_img:
    deco_class = "right-deco-img-idle" if st.session_state.deco_status == "idle" else "right-deco-img"
    deco_placeholder.markdown(
        f'<div class="{deco_class}">'
        f'<div class="right-deco-status">{status_text}</div>'
        f'<img src="data:image/png;base64,{current_img}" alt="deco">'
        f'</div>',
        unsafe_allow_html=True,
    )

# ----- 后端 API 地址 -----
API_URL = "http://localhost:8000/api/v1/chat/stream"
STATS_URL = "http://localhost:8000/api/v1/stats"

# ----- 初始化 -----
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_view" not in st.session_state:
    st.session_state.current_view = -1
if "stats" not in st.session_state:
    st.session_state.stats = None
if "scores" not in st.session_state:
    st.session_state.scores = []

# ----- 获取统计数据（仅首次加载时请求） -----
if st.session_state.stats is None:
    try:
        stats_resp = requests.get(STATS_URL, timeout=5)
        if stats_resp.status_code == 200:
            st.session_state.stats = stats_resp.json()
    except:
        pass

# ----- 显示统计信息 -----
stats_placeholder = st.empty()
if st.session_state.stats:
    stats = st.session_state.stats
    stats_placeholder.markdown(
        f'<div class="right-stats">'
        f'<div class="stat-item">Notes: <span class="stat-value">{stats.get("note_count", 0)}</span></div>'
        f'<div class="stat-item">Vectors: <span class="stat-value">{stats.get("vector_count", 0)}</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ----- 显示 Chroma 分数图表 -----
scores_placeholder = st.empty()
if st.session_state.scores:
    scores_placeholder.markdown(
        render_score_chart(st.session_state.scores),
        unsafe_allow_html=True,
    )

# ----- 构建 Q&A 对列表 -----
# messages 格式: [user0, assistant0, user1, assistant1, ...]
# qa_pairs: [(user_msg, assistant_msg), ...]
qa_pairs = []
i = 0
while i < len(st.session_state.messages):
    if st.session_state.messages[i]["role"] == "user":
        user_msg = st.session_state.messages[i]
        assistant_msg = st.session_state.messages[i + 1] if i + 1 < len(st.session_state.messages) else None
        qa_pairs.append((user_msg, assistant_msg))
    i += 1

# ----- Sidebar：历史问题列表 -----
with st.sidebar:
    st.markdown(
        '<div class="sidebar-title">💬 Chat History</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    if not qa_pairs:
        st.caption("No questions yet.")
    else:
        for idx, (user_msg, _) in enumerate(reversed(qa_pairs)):
            real_idx = len(qa_pairs) - 1 - idx
            is_active = real_idx == st.session_state.current_view
            cls = "history-btn history-btn-active" if is_active else "history-btn"
            if st.button(
                user_msg["content"],
                key=f"hist_{real_idx}",
                use_container_width=True,
            ):
                st.session_state.current_view = real_idx
                st.session_state.deco_status = "idle"
                st.session_state.scores = []
                scores_placeholder.empty()
                st.rerun()

# ----- 主区域：显示当前选中的问答 -----
if st.session_state.current_view >= 0 and st.session_state.current_view < len(qa_pairs):
    user_msg, assistant_msg = qa_pairs[st.session_state.current_view]
    with st.chat_message("user"):
        st.markdown(user_msg["content"])
    if assistant_msg:
        with st.chat_message("assistant"):
            st.markdown(assistant_msg["content"])
            if "sources" in assistant_msg:
                # 显示历史分数图表
                if assistant_msg["sources"]:
                    hist_scores = [
                        {"label": f"[{i+1}]", "score": s.get("score", 0)}
                        for i, s in enumerate(assistant_msg["sources"])
                    ]
                    st.session_state.scores = hist_scores
                    scores_placeholder.markdown(
                        render_score_chart(hist_scores),
                        unsafe_allow_html=True,
                    )
                with st.expander("📎 View Citation Sources"):
                    for src in assistant_msg["sources"]:
                        st.write(f"**File**: {src['file_name']}")
                        st.write(f"**Original Text**: {src['content'][:200]}...")
                        st.divider()

# ----- 输入框 -----
if prompt := st.chat_input("💬 Ask me anything about your notes..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.deco_status = "loading"
    new_pair_idx = len(qa_pairs)
    st.session_state.current_view = new_pair_idx
    st.rerun()

# ----- 流式生成（在 rerun 后执行） -----
if (
    st.session_state.current_view == len(qa_pairs) - 1
    and st.session_state.messages
    and st.session_state.messages[-1]["role"] == "user"
    and (len(qa_pairs) == 0 or qa_pairs[-1][1] is None)
):
    user_msg = qa_pairs[-1][0]
    prompt = user_msg["content"]

    with st.chat_message("assistant"):
        placeholder = st.empty()
        spinner_placeholder = st.empty()
        full_response = ""
        sources = []

        try:
            spinner_placeholder.markdown(
                '<span class="loading-spinner"></span>🔍 Retrieving and thinking...',
                unsafe_allow_html=True,
            )
            response = requests.post(
                API_URL,
                json={"question": prompt, "top_k": 3},
                stream=True,
            )

            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode("utf-8")
                        if line_str.startswith("data: "):
                            data_str = line_str[6:]
                            try:
                                data = json.loads(data_str)
                                msg_type = data.get("type")

                                if msg_type == "sources":
                                    sources = data.get("data", [])
                                    # 提取分数用于图表显示
                                    st.session_state.scores = [
                                        {"label": f"[{i+1}]", "score": s.get("score", 0)}
                                        for i, s in enumerate(sources)
                                    ]
                                    # 更新分数图表
                                    if st.session_state.scores:
                                        scores_placeholder.markdown(
                                            render_score_chart(st.session_state.scores),
                                            unsafe_allow_html=True,
                                        )
                                elif msg_type == "content":
                                    if not full_response:
                                        spinner_placeholder.empty()
                                        # 切换到生成状态图片
                                        if img_generating:
                                            deco_placeholder.markdown(
                                                f'<div class="right-deco-img">'
                                                f'<div class="right-deco-status">Generating answer...</div>'
                                                f'<img src="data:image/png;base64,{img_generating}" alt="deco">'
                                                f'</div>',
                                                unsafe_allow_html=True,
                                            )
                                    chunk = data.get("data", "")
                                    full_response += chunk
                                    placeholder.markdown(full_response + "▌")
                                elif msg_type == "end":
                                    spinner_placeholder.empty()
                                    placeholder.markdown(full_response)
                                    # 切回 idle 图片
                                    if img_idle:
                                        deco_placeholder.markdown(
                                            f'<div class="right-deco-img-idle">'
                                            f'<div class="right-deco-status">What can I do for you?</div>'
                                            f'<img src="data:image/png;base64,{img_idle}" alt="deco">'
                                            f'</div>',
                                            unsafe_allow_html=True,
                                        )
                                    # 渲染最终分数图表
                                    if st.session_state.scores:
                                        scores_placeholder.markdown(
                                            render_score_chart(st.session_state.scores),
                                            unsafe_allow_html=True,
                                        )
                            except json.JSONDecodeError:
                                pass
            else:
                spinner_placeholder.empty()
                st.session_state.deco_status = "idle"
                st.session_state.scores = []
                scores_placeholder.empty()
                st.error(f"❌ Backend service error: {response.status_code}")

        except requests.exceptions.ConnectionError:
            spinner_placeholder.empty()
            st.session_state.deco_status = "idle"
            st.session_state.scores = []
            scores_placeholder.empty()
            st.error("❌ Cannot connect to backend service. Please ensure FastAPI is running on port 8000")
        except Exception as e:
            spinner_placeholder.empty()
            st.session_state.deco_status = "idle"
            st.session_state.scores = []
            scores_placeholder.empty()
            st.error(f"❌ 流式接收出错: {str(e)}")

        if full_response:
            if sources:
                with st.expander("📎 View Citation Sources"):
                    for src in sources:
                        st.write(f"**File**: {src['file_name']}")
                        st.write(f"**Original Snippet**: {src['content'][:150]}...")
                        st.divider()

            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "sources": sources,
            })
            st.session_state.deco_status = "idle"
