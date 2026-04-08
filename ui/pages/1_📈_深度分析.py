"""
深度分析页面
多Agent协作分析股票
"""
import os
import sys
from pathlib import Path
import time

import streamlit as st
from loguru import logger

# 添加项目路径 (pages目录需要向上两级到达项目根目录)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import get_config
from graph.workflow import InvestmentWorkflow
from tools.stock_data import resolve_stock_input, get_stock_data
from ui.components import (
    render_stock_card,
    render_analysis_card,
    render_risk_card,
    render_source_card,
    render_debate_card
)
from ui.components.charts import create_candlestick_chart
from knowledge_base import init_knowledge_base


st.set_page_config(
    page_title="深度分析 - 智汇投研Pro",
    page_icon="📈",
    layout="wide"
)


@st.cache_resource
def get_workflow():
    """获取工作流实例"""
    from rag.retriever import RAGRetriever
    kb = init_knowledge_base(use_mock=True)
    retriever = RAGRetriever(vector_store=kb.vector_store)
    return InvestmentWorkflow(retriever=retriever)


def main():
    """主函数"""
    # 侧边栏
    with st.sidebar:
        st.title("📈 深度分析")
        
        st.divider()
        
        # 返回主页
        if st.button("🏠 返回主页", use_container_width=True):
            st.switch_page("app.py")
        
        st.divider()
        
        # 分析历史记录
        st.subheader("📜 分析历史")
        
        # 从session_state获取历史记录
        if "analysis_history" not in st.session_state:
            st.session_state.analysis_history = []
        
        history = st.session_state.analysis_history
        
        if history:
            # 显示最近5条记录
            for i, record in enumerate(history[-5:][::-1]):
                with st.container():
                    st.markdown(f"**{record.get('stock_name', 'N/A')}**")
                    st.caption(f"{record.get('date', 'N/A')} | {record.get('decision', 'N/A')}")
                    if i < len(history[-5:]) - 1:
                        st.divider()
        else:
            st.caption("暂无分析记录")
        
        st.divider()
        
        # 清空历史
        if st.button("🗑️ 清空历史", use_container_width=True):
            st.session_state.analysis_history = []
            st.rerun()
    
    # 主内容区
    st.title("📈 深度分析")
    st.markdown("基于多Agent协作的股票深度分析")
    
    st.divider()
    
    # 搜索区域
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        stock_input = st.text_input(
            "股票代码/名称/拼音首字母",
            placeholder="例如：600519、茅台、MT",
            key="analysis_input"
        )
    
    with col2:
        risk_profile = st.selectbox(
            "风险偏好",
            ["保守型", "稳健型", "激进型"],
            index=1,
            key="risk_profile"
        )
    
    with col3:
        st.write("")
        st.write("")
        analyze_btn = st.button("🔍 开始分析", use_container_width=True, type="primary")
    
    st.divider()
    
    # 分析结果区域
    if analyze_btn and stock_input:
        # 解析股票代码
        try:
            stock_code, stock_name = resolve_stock_input(stock_input)
        except Exception as e:
            st.error(f"无法识别股票: {e}")
            return
        
        # 风险偏好映射
        risk_map = {"保守型": "conservative", "稳健型": "moderate", "激进型": "aggressive"}
        
        # 创建进度显示
        progress_bar = st.progress(0, text="初始化分析引擎...")
        
        # 执行分析
        workflow = get_workflow()
        risk_profile_code = risk_map[risk_profile]
        
        # 状态消息映射
        status_messages = {
            "fetch_data": "📡 获取股票数据...",
            "analyze_fundamental": "📊 基本面分析中...",
            "analyze_technical": "📈 技术面分析中...",
            "analyze_sentiment": "😊 情绪面分析中...",
            "analyze_news": "📰 新闻面分析中...",
            "analyze_capital_flow": "💰 资金流分析中...",
            "retrieve_reports": "📚 检索研报中...",
            "debate": "🗣️ 多空辩论中...",
            "make_decision": "🎯 投资决策中...",
            "assess_risk": "⚠️ 风险评估中...",
            "review_decision": "✅ 审核决策中...",
            "generate_report": "📝 生成报告中..."
        }
        
        total_steps = len(status_messages)
        current_step = 0
        
        # 创建结果容器 - 提前创建，用于逐步填充内容
        st.divider()
        
        # 股票基本信息区域
        stock_info_container = st.container()
        
        # Tab页签 - 提前创建
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
            "📋 综合报告", "📊 基本面", "📈 技术面", "😊 情绪面", "📰 新闻面", "💰 资金流", "📚 研报观点", "🗣️ 多空辩论", "⚠️ 风险评估"
        ])
        
        # 用于存储累积的结果
        accumulated_result = {
            "stock_data": {},
            "fundamental_analysis": {},
            "technical_analysis": {},
            "sentiment_analysis": {},
            "news_analysis": {},
            "capital_flow_analysis": {},
            "report_view": {},
            "debate_result": {},
            "trader_decision": {},
            "risk_assessment": {},
            "pm_review": {},
            "final_report": "",
            "errors": []
        }
        
        try:
            for event in workflow.stream(stock_code, risk_profile_code):
                for node_name, node_result in event.items():
                    if node_name in status_messages:
                        current_step += 1
                        progress = current_step / total_steps
                        progress_bar.progress(progress, text=status_messages[node_name])
                        
                        # 累积结果
                        accumulated_result.update(node_result)
                        
                        # 根据节点类型实时展示结果
                        render_node_result(node_name, node_result, accumulated_result,
                                         stock_info_container, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9)
                        
                        time.sleep(0.1)  # 短暂延迟让用户看到进度
            
            progress_bar.progress(1.0, text="✅ 分析完成!")
            
        except Exception as e:
            st.error(f"分析失败: {e}")
            logger.error(f"分析失败: {e}")
    
    else:
        # 显示说明
        st.info("👈 请输入股票代码或名称，然后点击\"开始分析\"")
        
        st.markdown("""
        ### 分析流程
        
        1. **数据获取** - 获取股票行情、财务、新闻等数据
        2. **多维度分析** - 基本面、技术面、情绪面、资金流分析
        3. **研报检索** - RAG检索相关研报观点
        4. **多空辩论** - 红蓝军对抗辩论
        5. **风险评估** - 多维度风险量化
        6. **投资建议** - 综合决策与报告生成
        """)


def render_node_result(node_name: str, node_result: dict, accumulated: dict,
                        stock_info_container, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9):
    """根据节点名称实时渲染结果到对应的 tab"""
    
    # 1. 数据获取完成 - 显示股票基本信息
    if node_name == "fetch_data":
        with stock_info_container:
            stock_data = node_result.get("stock_data", {})
            basic_info = stock_data.get("basic_info", {})
            if basic_info:
                st.subheader(f"📊 {basic_info.get('name', '未知')} ({basic_info.get('code', '')})")
                render_stock_card(basic_info)
    
    # 2. 基本面分析完成
    elif node_name == "analyze_fundamental":
        with tab2:
            st.empty()  # 清空占位
            fundamental = accumulated.get("fundamental_analysis", {})
            render_analysis_card("基本面分析", fundamental, "📊")
    
    # 3. 技术面分析完成
    elif node_name == "analyze_technical":
        with tab3:
            st.empty()
            technical = accumulated.get("technical_analysis", {})
            render_analysis_card("技术面分析", technical, "📈")
            
            # K线图
            stock_data = accumulated.get("stock_data", {})
            if stock_data.get("history"):
                try:
                    import pandas as pd
                    df = pd.DataFrame(stock_data["history"])
                    fig = create_candlestick_chart(df, title="K线图")
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"图表渲染失败: {e}")
    
    # 4. 情绪面分析完成
    elif node_name == "analyze_sentiment":
        with tab4:
            st.empty()
            sentiment = accumulated.get("sentiment_analysis", {})
            render_analysis_card("情绪面分析", sentiment, "😊")
    
    # 5. 新闻面分析完成
    elif node_name == "analyze_news":
        with tab5:
            st.empty()
            news = accumulated.get("news_analysis", {})
            render_analysis_card("新闻面分析", news, "📰")
    
    # 6. 资金流分析完成
    elif node_name == "analyze_capital_flow":
        with tab6:
            st.empty()
            capital_flow = accumulated.get("capital_flow_analysis", {})
            render_analysis_card("资金流分析", capital_flow, "💰")
    
    # 8. 研报检索完成
    elif node_name == "retrieve_reports":
        with tab7:
            st.empty()
            report_view = accumulated.get("report_view", {})
            render_analysis_card("研报观点汇总", report_view, "📚")
            sources = report_view.get("sources", [])
            if sources:
                render_source_card(sources)

    # 9. 辩论完成
    elif node_name == "debate":
        with tab8:
            st.empty()
            debate_result = accumulated.get("debate_result", {})
            render_debate_card(debate_result)

    # 10. 风险评估完成
    elif node_name == "assess_risk":
        with tab9:
            st.empty()
            risk_assessment = accumulated.get("risk_assessment", {})
            render_risk_card(risk_assessment)
    
    # 7. 报告生成完成
    elif node_name == "generate_report":
        with tab1:
            st.empty()
            final_report = accumulated.get("final_report", "")
            if final_report:
                st.markdown(final_report)
            else:
                st.warning("报告生成失败")
        
        # 保存分析历史记录
        try:
            trader_decision = accumulated.get("trader_decision", {})
            basic_info = accumulated.get("stock_data", {}).get("basic_info", {})
            
            record = {
                "stock_code": stock_code,
                "stock_name": stock_name or basic_info.get("name", "N/A"),
                "date": time.strftime("%Y-%m-%d %H:%M"),
                "decision": trader_decision.get("decision", "N/A")
            }
            
            if "analysis_history" not in st.session_state:
                st.session_state.analysis_history = []
            
            st.session_state.analysis_history.append(record)
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")


if __name__ == "__main__":
    main()
