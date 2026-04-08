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
        
        # 根据不同分析类型采用不同的展示方式
        if "基本面" in title:
            _render_fundamental_detail(result)
        elif "技术面" in title:
            _render_technical_detail(result)
        elif "情绪面" in title:
            _render_sentiment_detail(result)
        elif "新闻面" in title:
            _render_news_detail(result)
        elif "资金流" in title or "资金面" in title:
            _render_capital_flow_detail(result)
        else:
            # 通用展示方式
            _render_generic_analysis(result)


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


def _render_fundamental_detail(result: Dict[str, Any]) -> None:
    """渲染基本面分析详情"""
    # 质量评分
    if "quality_score" in result:
        score = result["quality_score"]
        color = "#00C853" if score >= 70 else ("#FFB800" if score >= 50 else "#FF5252")
        st.markdown(f"**质量评分**: <span style='color:{color}; font-size:20px;'>{score}/100</span>", unsafe_allow_html=True)
        st.progress(score / 100)
    
    # 关键发现
    if "key_findings" in result and result["key_findings"]:
        st.markdown("### 📊 核心分析")
        for finding in result["key_findings"]:
            st.markdown(f"- {finding}")
    
    # 估值评估
    if "valuation" in result:
        st.markdown("### 💰 估值情况")
        st.info(result["valuation"])
    
    # 优势与风险
    col1, col2 = st.columns(2)
    
    with col1:
        if "strengths" in result and result["strengths"]:
            st.markdown("### ✅ 主要优势")
            for strength in result["strengths"][:3]:
                st.markdown(f"👍 {strength}")
    
    with col2:
        if "red_flags" in result and result["red_flags"]:
            st.markdown("### ⚠️ 风险提示")
            for flag in result["red_flags"][:3]:
                st.markdown(f"🔴 {flag}")
    
    # 建议
    if "recommendation" in result:
        st.markdown("### 💡 投资建议")
        st.success(result["recommendation"])
    
    # 置信度
    if "confidence" in result:
        confidence = result["confidence"]
        st.caption(f"📊 分析置信度: {confidence*100:.0f}%")


def _render_technical_detail(result: Dict[str, Any]) -> None:
    """渲染技术面分析详情"""
    # 趋势分析
    if "trend_analysis" in result:
        st.markdown("### 📈 趋势判断")
        st.info(result["trend_analysis"])
    
    # 关键位置
    if "key_levels" in result:
        levels = result["key_levels"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if "support" in levels and levels["support"]:
                st.markdown("### 🟢 支撑位")
                for level in levels["support"]:
                    st.markdown(f"📍 {level}")
        
        with col2:
            if "resistance" in levels and levels["resistance"]:
                st.markdown("### 🔴 压力位")
                for level in levels["resistance"]:
                    st.markdown(f"📍 {level}")
    
    # 信号分析
    if "signals" in result:
        signals = result["signals"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if "bullish" in signals and signals["bullish"]:
                st.markdown("### ✅ 看多信号")
                for signal in signals["bullish"]:
                    st.markdown(f"📈 {signal}")
        
        with col2:
            if "bearish" in signals and signals["bearish"]:
                st.markdown("### ❌ 看空信号")
                for signal in signals["bearish"]:
                    st.markdown(f"📉 {signal}")
    
    # 指标状态
    col1, col2 = st.columns(2)
    
    with col1:
        if "rsi_status" in result:
            st.markdown("### 📊 RSI状态")
            st.markdown(f"• {result['rsi_status']}")
    
    with col2:
        if "macd_status" in result:
            st.markdown("### 📊 MACD状态")
            st.markdown(f"• {result['macd_status']}")
    
    # 操作建议
    if "recommendation" in result:
        st.markdown("### 💡 操作建议")
        st.success(result["recommendation"])
    
    # 置信度
    if "confidence" in result:
        confidence = result["confidence"]
        st.caption(f"📊 分析置信度: {confidence*100:.0f}%")


def _render_sentiment_detail(result: Dict[str, Any]) -> None:
    """渲染情绪面分析详情"""
    # 情绪评分
    if "sentiment_score" in result:
        score = result["sentiment_score"]
        if "overall_sentiment" in result:
            sentiment = result["overall_sentiment"]
            
            # 情绪颜色
            sentiment_colors = {
                "极度贪婪": "#00C853",
                "贪婪": "#7CFC00",
                "中性": "#FFB800",
                "恐慌": "#FF9800",
                "极度恐慌": "#FF5252"
            }
            color = sentiment_colors.get(sentiment, "#808080")
            
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; background: {color}20; border-radius: 10px; margin-bottom: 10px;'>
                <div style='font-size: 24px; font-weight: bold; color: {color};'>{sentiment}</div>
                <div style='font-size: 36px; font-weight: bold; color: {color};'>{score:.1f}</div>
                <div style='font-size: 12px; color: #888;'>情绪分数 (-100 ~ 100)</div>
            </div>
            """, unsafe_allow_html=True)
    
    # 新闻情绪
    if "news_sentiment" in result:
        news_sentiment = result["news_sentiment"]
        emoji = {"正面": "😊", "中性": "😐", "负面": "😟"}.get(news_sentiment, "😐")
        st.markdown(f"**新闻情绪**: {emoji} {news_sentiment}")
    
    # 驱动因素
    if "key_drivers" in result and result["key_drivers"]:
        st.markdown("### 🔍 情绪驱动因素")
        for driver in result["key_drivers"]:
            st.markdown(f"• {driver}")
    
    # 逆向信号
    if "contrarian_signal" in result:
        signal = result["contrarian_signal"]
        if "是" in signal:
            st.warning(f"⚠️ **逆向信号**: {signal}")
    
    # 短期影响
    if "short_term_impact" in result:
        st.markdown("### 📅 短期影响预测")
        st.info(result["short_term_impact"])
    
    # 建议
    if "recommendation" in result:
        st.markdown("### 💡 情绪面建议")
        st.success(result["recommendation"])
    
    # 置信度
    if "confidence" in result:
        confidence = result["confidence"]
        st.caption(f"📊 分析置信度: {confidence*100:.0f}%")


def _render_news_detail(result: Dict[str, Any]) -> None:
    """渲染新闻面分析详情"""
    # 重大事件
    if "major_events" in result and result["major_events"]:
        st.markdown("### 📰 重大事件影响")
        for event in result["major_events"]:
            impact = event.get("impact", "中性")
            impact_color = {"正面": "#00C853", "中性": "#FFB800", "负面": "#FF5252"}.get(impact, "#808080")
            impact_emoji = {"正面": "✅", "中性": "➖", "负面": "❌"}.get(impact, "➖")
            
            with st.container():
                st.markdown(f"**{event.get('event', '事件')}**")
                st.markdown(f"{impact_emoji} 影响: <span style='color:{impact_color};'>{impact}</span> | 强度: {event.get('magnitude', '中')} | 时间维度: {event.get('time_horizon', '未知')}", unsafe_allow_html=True)
                st.markdown(f"📝 {event.get('analysis', '暂无分析')}")
                st.divider()
    
    # 政策环境
    if "policy_environment" in result:
        st.markdown("### 🏛️ 政策环境")
        st.info(result["policy_environment"])
    
    # 行业前景
    if "industry_outlook" in result:
        st.markdown("### 🏭 行业前景")
        st.info(result["industry_outlook"])
    
    # 潜在催化剂
    if "catalysts" in result and result["catalysts"]:
        st.markdown("### 🚀 潜在催化剂")
        for catalyst in result["catalysts"]:
            st.markdown(f"⭐ {catalyst}")
    
    # 风险点
    if "risks" in result and result["risks"]:
        st.markdown("### ⚠️ 风险提示")
        for risk in result["risks"]:
            st.markdown(f"🔴 {risk}")
    
    # 建议
    if "recommendation" in result:
        st.markdown("### 💡 新闻面建议")
        st.success(result["recommendation"])
    
    # 置信度
    if "confidence" in result:
        confidence = result["confidence"]
        st.caption(f"📊 分析置信度: {confidence*100:.0f}%")


def _render_capital_flow_detail(result: Dict[str, Any]) -> None:
    """渲染资金流分析详情"""
    # 主力资金
    if "main_force" in result:
        main = result["main_force"]
        net_inflow = main.get("net_inflow", 0)
        trend = main.get("trend", "未知")
        strength = main.get("strength", "中")
        
        trend_color = "#00C853" if trend == "流入" else "#FF5252"
        trend_emoji = "📈" if trend == "流入" else "📉"
        
        st.markdown("### 💰 主力资金")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("净流入", f"{net_inflow/1e6:.2f}万" if abs(net_inflow) < 1e8 else f"{net_inflow/1e8:.2f}亿")
        with col2:
            st.markdown(f"**趋势**: {trend_emoji} <span style='color:{trend_color};'>{trend}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"**强度**: {strength}")
        
        if "analysis" in main:
            st.info(main["analysis"])
    
    # 北向资金
    if "northbound" in result:
        north = result["northbound"]
        net_inflow = north.get("net_inflow", 0)
        trend = north.get("trend", "未知")
        consecutive = north.get("consecutive_days", 0)
        
        trend_color = "#00C853" if trend == "流入" else "#FF5252"
        trend_emoji = "📈" if trend == "流入" else "📉"
        
        st.markdown("### 🌏 北向资金")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("净流入", f"{net_inflow/1e6:.2f}万" if abs(net_inflow) < 1e8 else f"{net_inflow/1e8:.2f}亿")
        with col2:
            st.markdown(f"**趋势**: {trend_emoji} <span style='color:{trend_color};'>{trend}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"**连续天数**: {consecutive}天")
        
        if "analysis" in north:
            st.info(north["analysis"])
    
    # 机构持仓
    if "institution" in result:
        inst = result["institution"]
        change = inst.get("holding_change", "未知")
        confidence = inst.get("confidence", "低")
        ratio = inst.get("holdings_ratio", 0)
        
        change_color = {"增持": "#00C853", "不变": "#FFB800", "减持": "#FF5252"}.get(change, "#808080")
        change_emoji = {"增持": "📈", "不变": "➖", "减持": "📉"}.get(change, "➖")
        
        st.markdown("### 🏛️ 机构持仓")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**变化**: {change_emoji} <span style='color:{change_color};'>{change}</span>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"**持仓比例**: {ratio:.2f}%")
        with col3:
            st.markdown(f"**置信度**: {confidence}")
        
        if "analysis" in inst:
            st.info(inst["analysis"])
    
    # 融资融券
    if "margin_trading" in result:
        margin = result["margin_trading"]
        balance = margin.get("financing_balance", 0)
        trend = margin.get("trend", "未知")
        
        trend_color = "#00C853" if trend == "上升" else "#FF5252"
        trend_emoji = "📈" if trend == "上升" else "📉"
        
        st.markdown("### 🏦 融资融券")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("融资余额", f"{balance/1e8:.2f}亿" if balance > 1e8 else f"{balance/1e6:.2f}万")
        with col2:
            st.markdown(f"**趋势**: {trend_emoji} <span style='color:{trend_color};'>{trend}</span>", unsafe_allow_html=True)
        
        if "analysis" in margin:
            st.info(margin["analysis"])
    
    # 综合判断
    if "conclusion" in result:
        st.markdown("### 📊 综合判断")
        signal = result.get("signal", "持有")
        signal_color = {"买入": "#00C853", "持有": "#FFB800", "卖出": "#FF5252"}.get(signal, "#808080")
        signal_emoji = {"买入": "✅", "持有": "➖", "卖出": "❌"}.get(signal, "➖")
        
        st.markdown(f"**资金面信号**: {signal_emoji} <span style='color:{signal_color}; font-size:18px;'>{signal}</span>", unsafe_allow_html=True)
        st.info(result["conclusion"])
    
    # 置信度
    if "confidence" in result:
        confidence = result["confidence"]
        st.caption(f"📊 分析置信度: {confidence*100:.0f}%")


def _render_generic_analysis(result: Dict[str, Any]) -> None:
    """渲染通用分析结果"""
    # 摘要
    if "summary" in result:
        st.markdown("### 📋 分析摘要")
        st.info(result["summary"])
    
    # 关键发现
    if "key_findings" in result and result["key_findings"]:
        st.markdown("### 🔍 关键发现")
        for finding in result["key_findings"]:
            st.markdown(f"• {finding}")
    
    # 建议
    if "recommendation" in result:
        st.markdown("### 💡 建议")
        st.success(result["recommendation"])

    # 置信度
    if "confidence" in result:
        confidence = result["confidence"]
        st.caption(f"📊 分析置信度: {confidence*100:.0f}%")


def render_debate_card(debate_result: Dict[str, Any]) -> None:
    """
    渲染红蓝军辩论卡片

    Args:
        debate_result: 辩论结果，包含辩论历史和最终立场
    """
    if "error" in debate_result:
        st.error(f"辩论失败: {debate_result['error']}")
        return

    # 辩论历史
    debate_history = debate_result.get("debate_history", [])

    if not debate_history:
        st.info("暂无辩论记录")
        return

    st.markdown("### 🗣️ 多空辩论室")
    st.markdown("看多研究员 vs 看空研究员的结构化辩论")

    st.divider()

    # 展示每一轮辩论
    for record in debate_history:
        round_num = record.get("round", 1)
        debate_type = record.get("type", "opening")

        st.markdown(f"#### 第 {round_num} 轮 - {'开场陈述' if debate_type == 'opening' else '互相反驳'}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div style='background: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 4px solid #00C853;'>
                <h5 style='color: #00C853; margin: 0;'>🐂 看多观点</h5>
            </div>
            """, unsafe_allow_html=True)

            if debate_type == "opening":
                bull_args = record.get("bull_arguments", {})
                _render_bull_arguments(bull_args)
            else:
                bull_rebuttal = record.get("bull_rebuttal", {})
                _render_bull_rebuttal(bull_rebuttal)

        with col2:
            st.markdown("""
            <div style='background: #FFEBEE; padding: 15px; border-radius: 10px; border-left: 4px solid #FF5252;'>
                <h5 style='color: #FF5252; margin: 0;'>🐻 看空观点</h5>
            </div>
            """, unsafe_allow_html=True)

            if debate_type == "opening":
                bear_args = record.get("bear_arguments", {})
                _render_bear_arguments(bear_args)
            else:
                bear_rebuttal = record.get("bear_rebuttal", {})
                _render_bear_rebuttal(bear_rebuttal)

        st.divider()

    # 最终立场对比
    st.markdown("### 📊 最终立场对比")

    bull_final = debate_result.get("bull_final_stance", {})
    bear_final = debate_result.get("bear_final_stance", {})

    col1, col2 = st.columns(2)

    with col1:
        bull_conf = bull_final.get("confidence_after_debate", bull_final.get("confidence_level", 0))
        st.metric("看多置信度", f"{bull_conf*100:.0f}%")

    with col2:
        bear_conf = bear_final.get("confidence_after_debate", bear_final.get("confidence_level", 0))
        st.metric("看空置信度", f"{bear_conf*100:.0f}%")

    # 辩论轮数
    total_rounds = debate_result.get("total_rounds", 0)
    st.caption(f"共进行 {total_rounds} 轮辩论")


def _render_bull_arguments(args: Dict[str, Any]) -> None:
    """渲染看多论点"""
    bull_case = args.get("bull_case", "")
    if bull_case:
        st.markdown(f"**核心逻辑**: {bull_case}")

    key_args = args.get("key_arguments", [])
    if key_args:
        st.markdown("**主要论点**:")
        for arg in key_args[:3]:
            st.markdown(f"✅ {arg}")

    upside = args.get("upside_potential", "")
    if upside:
        st.info(f"📈 上涨空间: {upside}")

    risk_ack = args.get("risk_acknowledgment", "")
    if risk_ack:
        st.warning(f"⚠️ 承认的风险: {risk_ack}")

    conf = args.get("confidence_level", 0)
    st.caption(f"置信度: {conf*100:.0f}%")


def _render_bear_arguments(args: Dict[str, Any]) -> None:
    """渲染看空论点"""
    bear_case = args.get("bear_case", "")
    if bear_case:
        st.markdown(f"**核心逻辑**: {bear_case}")

    key_args = args.get("key_arguments", [])
    if key_args:
        st.markdown("**主要论点**:")
        for arg in key_args[:3]:
            st.markdown(f"❌ {arg}")

    downside = args.get("downside_risk", "")
    if downside:
        st.error(f"📉 下跌风险: {downside}")

    opp_ack = args.get("opportunity_acknowledgment", "")
    if opp_ack:
        st.info(f"💡 承认的机会: {opp_ack}")

    conf = args.get("confidence_level", 0)
    st.caption(f"置信度: {conf*100:.0f}%")


def _render_bull_rebuttal(rebuttal: Dict[str, Any]) -> None:
    """渲染看多反驳"""
    rebuttal_text = rebuttal.get("rebuttal", "")
    if rebuttal_text:
        st.markdown(f"**反驳陈述**: {rebuttal_text}")

    counter_points = rebuttal.get("counter_points", [])
    if counter_points:
        st.markdown("**反驳要点**:")
        for point in counter_points[:3]:
            st.markdown(f"🛡️ {point}")

    concern = rebuttal.get("remaining_concern", "")
    if concern:
        st.warning(f"⚠️ 仍需关注: {concern}")

    conf = rebuttal.get("confidence_after_debate", 0)
    st.caption(f"辩论后置信度: {conf*100:.0f}%")


def _render_bear_rebuttal(rebuttal: Dict[str, Any]) -> None:
    """渲染看空反驳"""
    rebuttal_text = rebuttal.get("rebuttal", "")
    if rebuttal_text:
        st.markdown(f"**反驳陈述**: {rebuttal_text}")

    counter_points = rebuttal.get("counter_points", [])
    if counter_points:
        st.markdown("**反驳要点**:")
        for point in counter_points[:3]:
            st.markdown(f"🛡️ {point}")

    hope = rebuttal.get("remaining_hope", "")
    if hope:
        st.info(f"💡 可能的上行: {hope}")

    conf = rebuttal.get("confidence_after_debate", 0)
    st.caption(f"辩论后置信度: {conf*100:.0f}%")
