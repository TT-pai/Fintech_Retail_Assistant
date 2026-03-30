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

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_config
from graph.workflow import InvestmentWorkflow
from tools.stock_data import resolve_stock_input, get_stock_data
from ui.components import (
    render_stock_card,
    render_analysis_card,
    render_risk_card,
    render_source_card
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
    kb = init_knowledge_base(use_mock=True)
    return InvestmentWorkflow(retriever=kb.vector_store)


def main():
    """主函数"""
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
        status_text = st.empty()
        
        # 执行分析
        workflow = get_workflow()
        
        risk_profile_code = risk_map[risk_profile]
        
        # 使用stream模式逐步显示进度
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
        
        try:
            for event in workflow.stream(stock_code, risk_profile_code):
                # 更新进度
                for node_name, node_result in event.items():
                    if node_name in status_messages:
                        current_step += 1
                        progress = current_step / total_steps
                        progress_bar.progress(progress, text=status_messages[node_name])
                        
                        # 短暂延迟以便用户看到进度
                        time.sleep(0.3)
            
            # 获取最终结果
            final_result = workflow.run(stock_code, risk_profile_code)
            
            progress_bar.progress(1.0, text="✅ 分析完成!")
            
            # 显示结果
            display_results(final_result)
            
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


def display_results(result: dict):
    """显示分析结果"""
    st.divider()
    
    # 股票基本信息
    stock_data = result.get("stock_data", {})
    basic_info = stock_data.get("basic_info", {})
    
    if basic_info:
        st.subheader(f"📊 {basic_info.get('name', '未知')} ({basic_info.get('code', '')})")
        render_stock_card(basic_info)
    
    # Tab页签
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 综合报告", "📊 基本面", "📈 技术面", "💰 资金流", "📚 研报观点", "⚠️ 风险评估"
    ])
    
    with tab1:
        # 综合报告
        final_report = result.get("final_report", "")
        if final_report:
            st.markdown(final_report)
        else:
            st.warning("报告生成失败")
    
    with tab2:
        # 基本面分析
        fundamental = result.get("fundamental_analysis", {})
        render_analysis_card("基本面分析", fundamental, "📊")
    
    with tab3:
        # 技术面分析
        technical = result.get("technical_analysis", {})
        render_analysis_card("技术面分析", technical, "📈")
        
        # K线图（如果有数据）
        if stock_data.get("history"):
            try:
                import pandas as pd
                df = pd.DataFrame(stock_data["history"])
                fig = create_candlestick_chart(df, title="K线图")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"图表渲染失败: {e}")
    
    with tab4:
        # 资金流分析
        capital_flow = result.get("capital_flow_analysis", {})
        render_analysis_card("资金流分析", capital_flow, "💰")
    
    with tab5:
        # 研报观点
        report_view = result.get("report_view", {})
        render_analysis_card("研报观点汇总", report_view, "📚")
        
        # 来源卡片
        sources = report_view.get("sources", [])
        if sources:
            render_source_card(sources)
    
    with tab6:
        # 风险评估
        risk_assessment = result.get("risk_assessment", {})
        render_risk_card(risk_assessment)
    
    # 错误信息
    errors = result.get("errors", [])
    if errors:
        st.divider()
        st.warning("⚠️ 分析过程中的警告:")
        for err in errors:
            st.markdown(f"- {err}")


if __name__ == "__main__":
    main()
