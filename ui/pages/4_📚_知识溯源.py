"""
知识溯源页面
查看知识图谱和检索来源
"""
import os
import sys
from pathlib import Path

import streamlit as st
from loguru import logger

# 添加项目路径 (pages目录需要向上两级到达项目根目录)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import get_config
from knowledge_base import init_knowledge_base
from rag.knowledge_graph import KnowledgeGraph, build_default_knowledge_graph


st.set_page_config(
    page_title="知识溯源 - 智汇投研Pro",
    page_icon="📚",
    layout="wide"
)


def main():
    """主函数"""
    st.title("📚 知识溯源")
    st.markdown("查看知识图谱和检索来源")
    
    st.divider()
    
    # 初始化知识库
    kb = init_knowledge_base(use_mock=True)
    
    # Tab页签
    tab1, tab2, tab3 = st.tabs(["🔍 知识检索", "🕸️ 知识图谱", "📊 知识库统计"])
    
    with tab1:
        # 知识检索
        st.subheader("🔍 知识检索")
        
        search_query = st.text_input("输入搜索关键词", placeholder="例如：茅台、白酒、新能源")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            doc_type = st.selectbox(
                "文档类型",
                ["全部", "研报", "财报", "新闻", "行业", "法规"]
            )
            top_k = st.slider("返回数量", 1, 20, 5)
        
        if search_query:
            # 执行检索
            filters = None
            if doc_type != "全部":
                type_map = {
                    "研报": "report",
                    "财报": "financial",
                    "新闻": "news",
                    "行业": "industry",
                    "法规": "regulation"
                }
                filters = {"doc_type": type_map.get(doc_type)}
            
            results = kb.search(search_query, top_k=top_k, doc_type=filters.get("doc_type") if filters else None)
            
            st.markdown(f"**找到 {len(results)} 条相关记录**")
            
            for i, result in enumerate(results, 1):
                metadata = result.get("metadata", {})
                score = result.get("score", 0)
                
                with st.expander(f"[{i}] {metadata.get('title', '未知标题')} (相关度: {score:.2f})"):
                    st.markdown(f"""
                    **来源**: {metadata.get('source', '未知')}
                    
                    **日期**: {metadata.get('date', '未知')}
                    
                    **股票**: {metadata.get('stock_name', 'N/A')} ({metadata.get('stock_code', 'N/A')})
                    
                    **类型**: {metadata.get('doc_type', '未知')}
                    
                    ---
                    
                    **内容**:
                    
                    {result.get('content', '无内容')[:500]}...
                    """)
    
    with tab2:
        # 知识图谱
        st.subheader("🕸️ 知识图谱")
        
        # 获取图谱
        kg = kb.knowledge_graph
        
        # 图谱统计
        stats = kg.get_graph_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("节点数", stats["total_nodes"])
        with col2:
            st.metric("关系数", stats["total_edges"])
        with col3:
            st.metric("实体类型", len(stats["entity_types"]))
        
        st.divider()
        
        # 实体搜索
        entity_query = st.text_input("搜索实体", placeholder="例如：茅台、白酒、宁德时代")
        
        if entity_query:
            # 搜索实体
            entities = kg.search_entities(entity_query, limit=10)
            
            if entities:
                st.markdown("**匹配的实体**:")
                
                for entity in entities:
                    with st.expander(f"{entity['name']} ({entity['type']})"):
                        # 查询实体详情
                        entity_info = kg.query_entity(entity['name'])
                        
                        if entity_info:
                            # 显示属性
                            st.markdown("**属性**:")
                            for key, value in entity_info.get("properties", {}).items():
                                st.markdown(f"- {key}: {value}")
                            
                            # 显示关系
                            relations = entity_info.get("relations", [])
                            if relations:
                                st.markdown("**关系**:")
                                for rel in relations[:10]:
                                    if rel["direction"] == "out":
                                        st.markdown(f"- → {rel['relation']} → {rel['target']}")
                                    else:
                                        st.markdown(f"- ← {rel['relation']} ← {rel['source']}")
            else:
                st.info("未找到匹配的实体")
        
        st.divider()
        
        # 图谱可视化（简化版）
        st.markdown("**图谱预览**")
        
        # 显示实体类型统计
        st.json(stats["entity_types"])
        
        # 显示关系类型统计
        st.json(stats["relation_types"])
        
        # 快捷查询
        st.markdown("**快捷查询**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("白酒板块龙头"):
                stocks = kg.get_concept_stocks("白酒")
                st.markdown("**白酒板块龙头**:")
                for stock in stocks[:5]:
                    st.markdown(f"- {stock['name']} ({stock['code']})")
        
        with col2:
            if st.button("茅台竞争对手"):
                competitors = kg.get_competitors("茅台")
                st.markdown("**茅台竞争对手**:")
                for comp in competitors:
                    st.markdown(f"- {comp}")
        
        with col3:
            if st.button("新能源概念股"):
                stocks = kg.get_concept_stocks("新能源")
                st.markdown("**新能源概念股**:")
                for stock in stocks[:5]:
                    st.markdown(f"- {stock['name']} ({stock['code']})")
    
    with tab3:
        # 知识库统计
        st.subheader("📊 知识库统计")
        
        stats = kb.get_stats()
        
        # 向量存储统计
        st.markdown("### 向量存储")
        st.metric("文档总数", stats["vector_store"]["total_documents"])
        
        st.divider()
        
        # 知识图谱统计
        if "knowledge_graph" in stats:
            st.markdown("### 知识图谱")
            
            kg_stats = stats["knowledge_graph"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**实体类型分布**")
                for entity_type, count in kg_stats["entity_types"].items():
                    st.markdown(f"- {entity_type}: {count}")
            
            with col2:
                st.markdown("**关系类型分布**")
                for relation_type, count in kg_stats["relation_types"].items():
                    st.markdown(f"- {relation_type}: {count}")


if __name__ == "__main__":
    main()
