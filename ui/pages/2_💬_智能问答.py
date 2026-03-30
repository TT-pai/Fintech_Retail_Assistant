"""
智能问答页面
基于RAG的智能问答
"""
import os
import sys
from pathlib import Path

import streamlit as st
from loguru import logger

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_config
from config.prompts import get_rag_qa_prompt
from knowledge_base import init_knowledge_base
from rag.retriever import RAGRetriever
from memory import ConversationManager
from ui.components.chat import (
    render_chat_message,
    render_chat_input,
    render_chat_history,
    render_quick_questions
)
from langchain_openai import ChatOpenAI


st.set_page_config(
    page_title="智能问答 - 智汇投研Pro",
    page_icon="💬",
    layout="wide"
)


@st.cache_resource
def init_rag_system():
    """初始化RAG系统"""
    kb = init_knowledge_base(use_mock=True)
    retriever = RAGRetriever(vector_store=kb.vector_store)
    return kb, retriever


def get_llm():
    """获取LLM实例"""
    config = get_config()
    return ChatOpenAI(
        model=config.llm.deep_think_model,
        api_key=config.llm.openai_api_key or "sk-dummy",
        base_url=config.llm.openai_base_url,
        temperature=0.7
    )


def main():
    """主函数"""
    st.title("💬 智能问答")
    st.markdown("基于RAG知识增强的智能问答助手")
    
    st.divider()
    
    # 初始化系统
    kb, retriever = init_rag_system()
    conversation_manager = ConversationManager()
    
    # 初始化会话状态
    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = "default"
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # 侧边栏
    with st.sidebar:
        st.subheader("📚 知识库统计")
        stats = kb.get_stats()
        st.metric("文档总数", stats["vector_store"]["total_documents"])
        
        if "knowledge_graph" in stats:
            st.metric("图谱节点", stats["knowledge_graph"]["total_nodes"])
            st.metric("图谱关系", stats["knowledge_graph"]["total_edges"])
        
        st.divider()
        
        if st.button("🗑️ 清空对话", use_container_width=True):
            st.session_state.chat_messages = []
            conversation_manager.clear_session(st.session_state.chat_session_id)
            st.rerun()
    
    # 快速问题
    quick_questions = [
        "茅台最新研报观点",
        "宁德时代财务分析",
        "白酒行业投资机会",
        "新能源板块走势"
    ]
    
    # 显示聊天历史
    render_chat_history(st.session_state.chat_messages)
    
    # 快速问题按钮
    st.markdown("**💡 快速提问**")
    cols = st.columns(len(quick_questions))
    for i, (col, question) in enumerate(zip(cols, quick_questions)):
        with col:
            if st.button(question, key=f"quick_{i}", use_container_width=True):
                handle_question(question, retriever, kb)
    
    st.divider()
    
    # 聊天输入
    user_input = render_chat_input("输入您的问题...", key="chat_input")
    
    if user_input:
        handle_question(user_input, retriever, kb)


def handle_question(question: str, retriever: RAGRetriever, kb):
    """处理用户问题"""
    # 添加用户消息
    st.session_state.chat_messages.append({
        "role": "user",
        "content": question
    })
    
    # 显示用户消息
    render_chat_message("user", question)
    
    # 检索相关知识
    with st.spinner("🔍 正在检索知识库..."):
        context, results = retriever.retrieve_with_context(question, top_k=5)
    
    # 生成回答
    with st.spinner("🤖 正在生成回答..."):
        try:
            llm = get_llm()
            prompt = get_rag_qa_prompt(context, question)
            
            response = llm.invoke(prompt)
            answer = response.content
            
        except Exception as e:
            logger.error(f"生成回答失败: {e}")
            # 降级：直接显示检索结果
            if results:
                answer = "抱歉，AI服务暂时不可用。以下是从知识库检索到的相关信息：\n\n"
                for i, r in enumerate(results[:3], 1):
                    answer += f"**[{i}]** {r.get('content', '')[:200]}...\n\n"
            else:
                answer = f"抱歉，无法获取回答。错误信息: {str(e)}"
    
    # 提取来源
    sources = []
    for r in results:
        metadata = r.get("metadata", {})
        sources.append({
            "source": metadata.get("source", "未知"),
            "title": metadata.get("title", ""),
            "date": metadata.get("date", ""),
            "score": r.get("score", 0)
        })
    
    # 添加助手消息
    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })
    
    # 显示助手消息
    render_chat_message("assistant", answer, sources)
    
    # 刷新页面
    st.rerun()


if __name__ == "__main__":
    main()
