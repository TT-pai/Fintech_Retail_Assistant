"""
智汇投研Pro - Streamlit主应用
AI智能投研平台
"""
import os
import sys
from pathlib import Path

import streamlit as st
from loguru import logger
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_config
from graph.workflow import InvestmentWorkflow
from knowledge_base import init_knowledge_base
from memory import ConversationManager, UserProfileManager


# 页面配置
st.set_page_config(
    page_title="智汇投研Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    /* 深色主题 */
    .stApp {
        background-color: #0D1117;
        color: #F0F6FC;
    }
    
    /* 卡片样式 */
    .card {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid rgba(48, 54, 61, 0.5);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 10px;
    }
    
    /* 标题样式 */
    h1, h2, h3 {
        color: #F0F6FC !important;
    }
    
    /* 按钮样式 */
    .stButton>button {
        background-color: #0A84FF;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
    }
    
    .stButton>button:hover {
        background-color: #0070E0;
    }
    
    /* 输入框样式 */
    .stTextInput>div>div>input {
        background-color: #161B22;
        border: 1px solid #30363D;
        color: #F0F6FC;
    }
    
    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
    }
    
    /* 指标样式 */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    
    /* 进度条样式 */
    .stProgress > div > div > div {
        background-color: #0A84FF;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_system():
    """初始化系统（缓存）"""
    # 加载环境变量
    load_dotenv()
    
    # 获取配置
    config = get_config()
    
    # 初始化知识库
    knowledge_base = init_knowledge_base(use_mock=True)
    
    # 初始化对话管理器
    conversation_manager = ConversationManager()
    
    # 初始化用户画像管理器
    user_profile_manager = UserProfileManager()
    
    return config, knowledge_base, conversation_manager, user_profile_manager


def main():
    """主函数"""
    # 初始化系统
    config, knowledge_base, conversation_manager, user_profile_manager = init_system()
    
    # 侧边栏
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/stock.png", width=80)
        st.title("智汇投研Pro")
        st.caption(f"版本: {config.app_version}")
        
        st.divider()
        
        # 用户设置
        st.subheader("⚙️ 设置")
        
        risk_profile = st.select_slider(
            "风险偏好",
            options=["保守型", "稳健型", "激进型"],
            value="稳健型"
        )
        
        st.divider()
        
        # 快速入口
        st.subheader("🚀 快速入口")
        
        if st.button("📊 深度分析", use_container_width=True):
            st.switch_page("pages/1_📈_深度分析.py")
        
        if st.button("💬 智能问答", use_container_width=True):
            st.switch_page("pages/2_💬_智能问答.py")
        
        if st.button("📚 知识溯源", use_container_width=True):
            st.switch_page("pages/4_📚_知识溯源.py")
        
        st.divider()
        
        # 系统信息
        st.caption(f"LLM: {config.llm.provider}")
        st.caption(f"知识库: {knowledge_base.get_stats()['vector_store']['total_documents']} 文档")
    
    # 主内容区
    st.title("📈 智汇投研Pro")
    st.markdown("**基于RAG+Agent的AI智能投研平台**")
    
    st.divider()
    
    # 快速搜索
    col1, col2 = st.columns([3, 1])
    
    with col1:
        stock_input = st.text_input(
            "输入股票代码或名称",
            placeholder="例如：600519、茅台、平安银行",
            key="main_search"
        )
    
    with col2:
        st.write("")
        st.write("")
        analyze_btn = st.button("🔍 开始分析", use_container_width=True)
    
    # 功能介绍卡片
    st.markdown("### 🌟 核心功能")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class='card'>
            <h4>📊 深度分析</h4>
            <p>多Agent协作分析<br>基本面+技术面+资金流</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='card'>
            <h4>💬 智能问答</h4>
            <p>RAG知识增强<br>研报/财报/新闻检索</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='card'>
            <h4>🎯 风险评估</h4>
            <p>多维度风险量化<br>智能仓位建议</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class='card'>
            <h4>📚 知识溯源</h4>
            <p>知识图谱可视化<br>来源可追溯</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # 今日市场热点（示例）
    st.markdown("### 🔥 今日热点")
    
    hot_stocks = [
        {"name": "贵州茅台", "code": "600519", "change": 2.35},
        {"name": "宁德时代", "code": "300750", "change": -1.28},
        {"name": "比亚迪", "code": "002594", "change": 3.56},
        {"name": "五粮液", "code": "000858", "change": 1.12},
    ]
    
    cols = st.columns(len(hot_stocks))
    for i, (col, stock) in enumerate(zip(cols, hot_stocks)):
        with col:
            color = "#00C853" if stock["change"] >= 0 else "#FF5252"
            st.markdown(f"""
            <div class='card' style='text-align: center;'>
                <div style='font-weight: bold;'>{stock['name']}</div>
                <div style='font-size: 12px; color: #888;'>{stock['code']}</div>
                <div style='font-size: 20px; color: {color};'>{stock['change']:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # 最新研报
    st.markdown("### 📰 最新研报")
    
    reports = knowledge_base.search("研报", top_k=3, doc_type="report")
    
    for report in reports:
        metadata = report.get("metadata", {})
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{metadata.get('title', '未知标题')}**")
                st.caption(f"来源: {metadata.get('source', '未知')} | 日期: {metadata.get('date', '未知')}")
            with col2:
                rating = metadata.get("rating", "未知")
                rating_color = "#00C853" if rating == "买入" else "#FFB800"
                st.markdown(f"<span style='color: {rating_color}; font-weight: bold;'>{rating}</span>", unsafe_allow_html=True)
            st.divider()
    
    # 底部信息
    st.markdown("""
    ---
    <div style='text-align: center; color: #888;'>
        <p>智汇投研Pro - 基于RAG+Agent的AI智能投研平台</p>
        <p style='font-size: 12px;'>⚠️ 本平台仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
