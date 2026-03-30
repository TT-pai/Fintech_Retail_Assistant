"""
卡片组件
用于展示股票信息、分析结果、风险评估等
"""
from typing import Dict, Any, List, Optional
import streamlit as st


def render_stock_card(basic_info: Dict[str, Any]) -> None:
    """
    渲染股票信息卡片
    
    Args:
        basic_info: 股票基本信息
    """
    with st.container():
        # 标题行
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"### {basic_info.get('name', '未知')} ({basic_info.get('code', 'N/A')})")
        
        with col2:
            price = basic_info.get('price', 0)
            change = basic_info.get('change_percent', 0)
            color = "#00C853" if change >= 0 else "#FF5252"
            st.markdown(f"<span style='font-size:24px; color:{color}'>{price:.2f}</span>", unsafe_allow_html=True)
        
        with col3:
            change_color = "#00C853" if change >= 0 else "#FF5252"
            arrow = "↑" if change >= 0 else "↓"
            st.markdown(f"<span style='color:{change_color}'>{arrow} {abs(change):.2f}%</span>", unsafe_allow_html=True)
        
        st.divider()
        
        # 详细信息
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("今开", f"{basic_info.get('open', 'N/A')}")
        with col2:
            st.metric("最高", f"{basic_info.get('high', 'N/A')}")
        with col3:
            st.metric("最低", f"{basic_info.get('low', 'N/A')}")
        with col4:
            st.metric("成交量", f"{_format_volume(basic_info.get('volume', 0))}")


def render_analysis_card(
    title: str,
    result: Dict[str, Any],
    icon: str = "📊"
) -> None:
    """
    渲染分析结果卡片
    
    Args:
        title: 卡片标题
        result: 分析结果
        icon: 图标
    """
    with st.expander(f"{icon} {title}", expanded=True):
        if "error" in result:
            st.error(f"分析失败: {result['error']}")
            return
        
        # 摘要
        if "summary" in result:
            st.markdown(f"**摘要**: {result['summary']}")
        
        # 关键发现
        if "key_findings" in result and result["key_findings"]:
            st.markdown("**关键发现**:")
            for finding in result["key_findings"][:5]:
                st.markdown(f"- {finding}")
        
        # 建议
        if "recommendation" in result:
            st.info(f"💡 **建议**: {result['recommendation']}")
        
        # 置信度
        if "confidence" in result:
            confidence = result["confidence"]
            confidence_pct = confidence * 100
            st.progress(confidence)
            st.caption(f"置信度: {confidence_pct:.0f}%")


def render_risk_card(risk_assessment: Dict[str, Any]) -> None:
    """
    渲染风险评估卡片
    
    Args:
        risk_assessment: 风险评估结果
    """
    overall_level = risk_assessment.get("overall_risk_level", "未知")
    overall_score = risk_assessment.get("overall_risk_score", 50)
    
    # 风险等级颜色
    level_colors = {
        "低": "#00C853",
        "中": "#FFB800",
        "高": "#FF9800",
        "极高": "#FF5252"
    }
    color = level_colors.get(overall_level, "#808080")
    
    with st.container():
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f"""
            <div style='text-align: center; padding: 20px; background: {color}20; border-radius: 10px;'>
                <div style='font-size: 36px; color: {color};'>{overall_level}风险</div>
                <div style='font-size: 48px; font-weight: bold; color: {color};'>{overall_score}</div>
                <div style='font-size: 14px; color: #888;'>/100</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # 各维度风险
            dimensions = risk_assessment.get("risk_dimensions", {})
            for dim_name, dim_data in dimensions.items():
                dim_name_cn = {
                    "market_risk": "市场风险",
                    "liquidity_risk": "流动性风险",
                    "valuation_risk": "估值风险",
                    "sentiment_risk": "情绪风险",
                    "credit_risk": "信用风险"
                }.get(dim_name, dim_name)
                
                score = dim_data.get("score", 0)
                st.markdown(f"**{dim_name_cn}**: {score}/100")
                st.progress(score / 100)
    
    # 风险提示
    warnings = risk_assessment.get("warnings", [])
    if warnings:
        st.warning("⚠️ **风险提示**:")
        for warning in warnings[:3]:
            st.markdown(f"- {warning}")
    
    # 建议
    suggestions = risk_assessment.get("suggestions", [])
    if suggestions:
        st.info("📋 **风险缓释建议**:")
        for suggestion in suggestions[:3]:
            st.markdown(f"- {suggestion}")


def render_source_card(sources: List[Dict[str, Any]]) -> None:
    """
    渲染来源信息卡片
    
    Args:
        sources: 来源信息列表
    """
    with st.expander("📚 知识来源", expanded=False):
        for i, source in enumerate(sources, 1):
            st.markdown(f"""
            **[{i}] {source.get('institution', '未知来源')}**
            - 日期: {source.get('date', '未知')}
            - 评级: {source.get('rating', '未知')}
            - 标题: {source.get('title', '')[:50]}...
            """)
            st.divider()


def render_watchlist_card(stocks: List[Dict[str, Any]]) -> None:
    """
    渲染自选股卡片
    
    Args:
        stocks: 自选股列表
    """
    with st.container():
        st.markdown("### 📌 自选股")
        
        if not stocks:
            st.info("暂无自选股，快去添加吧！")
            return
        
        for stock in stocks[:5]:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**{stock.get('name', '未知')}** ({stock.get('code', '')})")
            
            with col2:
                price = stock.get('price', 0)
                st.markdown(f"{price:.2f}")
            
            with col3:
                change = stock.get('change_percent', 0)
                color = "#00C853" if change >= 0 else "#FF5252"
                st.markdown(f"<span style='color:{color}'>{change:+.2f}%</span>", unsafe_allow_html=True)
            
            st.divider()


def _format_volume(volume: float) -> str:
    """格式化成交量"""
    if not volume:
        return "N/A"
    
    if volume >= 1e8:
        return f"{volume/1e8:.2f}亿"
    elif volume >= 1e4:
        return f"{volume/1e4:.2f}万"
    else:
        return f"{volume:.0f}"
