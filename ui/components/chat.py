"""
聊天组件
用于智能问答界面
"""
from typing import Dict, Any, List, Optional, Generator
import streamlit as st
from datetime import datetime


def render_chat_message(
    role: str,
    content: str,
    sources: List[Dict[str, Any]] = None,
    avatar: str = None
) -> None:
    """
    渲染聊天消息
    
    Args:
        role: 角色 (user/assistant)
        content: 消息内容
        sources: 来源信息
        avatar: 头像
    """
    if role == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(content)
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(content)
            
            # 显示来源
            if sources:
                with st.expander("📚 查看来源"):
                    for i, source in enumerate(sources, 1):
                        st.markdown(f"""
                        **[{i}] {source.get('source', '未知来源')}**
                        - 标题: {source.get('title', '')}
                        - 日期: {source.get('date', '')}
                        - 相关度: {source.get('score', 0):.2f}
                        """)


def render_chat_input(
    placeholder: str = "输入您的问题...",
    key: str = "chat_input"
) -> Optional[str]:
    """
    渲染聊天输入框
    
    Args:
        placeholder: 占位符文本
        key: 组件key
        
    Returns:
        用户输入的文本
    """
    return st.chat_input(placeholder, key=key)


def render_sources_panel(sources: List[Dict[str, Any]], title: str = "参考来源") -> None:
    """
    渲染来源面板
    
    Args:
        sources: 来源列表
        title: 面板标题
    """
    if not sources:
        return
    
    st.markdown(f"### 📚 {title}")
    
    for i, source in enumerate(sources, 1):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{source.get('title', '未知标题')}**")
                st.caption(f"来源: {source.get('source', '未知')} | 日期: {source.get('date', '未知')}")
            
            with col2:
                score = source.get('score', 0)
                st.metric("相关度", f"{score:.2f}")
            
            st.divider()


def render_thinking_indicator(message: str = "正在思考中...") -> None:
    """
    渲染思考指示器
    
    Args:
        message: 提示消息
    """
    with st.spinner(message):
        st.empty()


def stream_response(generator: Generator[str, None, None], placeholder) -> str:
    """
    流式显示响应
    
    Args:
        generator: 响应生成器
        placeholder: Streamlit占位符
        
    Returns:
        完整响应文本
    """
    full_response = ""
    
    for chunk in generator:
        full_response += chunk
        placeholder.markdown(full_response + "▌")
    
    placeholder.markdown(full_response)
    return full_response


def render_chat_history(messages: List[Dict[str, Any]]) -> None:
    """
    渲染聊天历史
    
    Args:
        messages: 消息列表
    """
    for message in messages:
        render_chat_message(
            role=message.get("role", "user"),
            content=message.get("content", ""),
            sources=message.get("sources")
        )


def render_quick_questions(questions: List[str], on_click_callback) -> None:
    """
    渲染快捷问题按钮
    
    Args:
        questions: 问题列表
        on_click_callback: 点击回调
    """
    st.markdown("**💡 快速提问**")
    
    cols = st.columns(len(questions))
    for i, (col, question) in enumerate(zip(cols, questions)):
        with col:
            if st.button(question, key=f"quick_q_{i}"):
                on_click_callback(question)


def render_agent_status(agent_name: str, status: str, description: str = "") -> None:
    """
    渲染Agent状态指示器
    
    Args:
        agent_name: Agent名称
        status: 状态 (pending/running/completed/error)
        description: 描述
    """
    status_icons = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅",
        "error": "❌"
    }
    
    status_colors = {
        "pending": "#888",
        "running": "#0A84FF",
        "completed": "#00C853",
        "error": "#FF5252"
    }
    
    icon = status_icons.get(status, "⏳")
    color = status_colors.get(status, "#888")
    
    st.markdown(f"""
    <div style='padding: 10px; border-left: 3px solid {color}; background: {color}10; margin-bottom: 5px;'>
        <span style='font-size: 18px;'>{icon}</span>
        <span style='font-weight: bold;'>{agent_name}</span>
        <span style='color: #888; font-size: 12px;'>{description}</span>
    </div>
    """, unsafe_allow_html=True)


def render_progress_bar(current: int, total: int, label: str = "分析进度") -> None:
    """
    渲染进度条
    
    Args:
        current: 当前进度
        total: 总数
        label: 标签
    """
    progress = current / total if total > 0 else 0
    st.progress(progress, text=f"{label}: {current}/{total}")
