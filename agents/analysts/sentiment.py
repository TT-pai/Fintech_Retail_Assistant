"""
情绪分析师Agent
负责分析市场情绪和舆情
"""
from typing import Dict, Any, List
import json

from agents.base import BaseAgent


SENTIMENT_SYSTEM_PROMPT = """你是一位资深的市场情绪分析师，擅长解读市场情绪和投资者心理。
你的专长是：
- 社交媒体情绪分析（雪球、东方财富股吧等）
- 资金流向分析
- 市场热度判断
- 散户与机构行为分析

分析原则：
1. 情绪是短期市场波动的重要驱动力
2. 极端情绪往往是反转信号
3. 关注聪明钱的动向
4. 区分噪音和信号

请基于提供的新闻和数据，分析当前市场情绪状态。

**重要**：你的分析需要说明情绪形成的原因、对股价的影响机制、以及可能的演变方向。"""


class SentimentAnalyst(BaseAgent):
    """情绪分析师"""
    
    def __init__(self, llm=None):
        super().__init__(
            name="情绪分析师",
            role="分析市场情绪与舆情",
            system_prompt=SENTIMENT_SYSTEM_PROMPT,
            llm=llm
        )
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行情绪分析"""
        basic_info = data.get("basic_info", {})
        news_list = data.get("news", [])
        sentiment_data = data.get("sentiment", {})  # 获取情绪数据
        
        # 构建新闻摘要
        news_summary = self._summarize_news(news_list)
        
        # 构建情绪数据摘要
        sentiment_summary = self._format_sentiment_data(sentiment_data)
        
        analysis_prompt = f"""
请对以下股票进行深入的市场情绪分析：

【股票信息】
代码: {basic_info.get('code', 'N/A')}
名称: {basic_info.get('name', 'N/A')}
当前价格: {basic_info.get('price', 'N/A')} 元
涨跌幅: {basic_info.get('change_percent', 'N/A')}%
成交量: {basic_info.get('volume', 'N/A')}

【近期新闻摘要】（前5条）
{news_summary}

【市场情绪数据】
{sentiment_summary}

【市场表现】
今日涨跌: {basic_info.get('change_percent', 0):.2f}%
成交活跃度: {"活跃" if basic_info.get('volume', 0) > 10000000 else "一般"}

**请按以下要求进行深入分析：**
1. 综合情绪数据分析当前市场情绪状态
2. 解读新闻事件对投资者情绪的影响机制
3. 分析情绪分数和涨跌幅反映的市场情绪
4. 判断当前情绪所处的阶段（恐慌/贪婪周期）
5. 评估情绪反转的可能性和触发条件
6. 说明情绪因素对短期股价的可能影响

请按以下结构输出（JSON格式）：
{{
    "summary": "300-400字的情绪分析摘要，包含情绪状态和主要驱动因素",
    "overall_sentiment": "极度恐慌/恐慌/中性/贪婪/极度贪婪",
    "sentiment_score": -100到100的情绪分数,
    "news_sentiment": "正面/中性/负面",
    "key_drivers": [
        "情绪驱动因素1：具体事件+影响机制+持续性判断",
        ...
    ],
    "contrarian_signal": "是否出现逆向信号（是/否），原因分析",
    "short_term_impact": "短期（1-5日）情绪对股价的影响预测",
    "confidence": 0.0-1.0,
    "recommendation": "情绪面操作建议：基于情绪判断的交易策略"
}}
"""
        
        try:
            response = self.invoke_llm(analysis_prompt)
            
            # 解析JSON
            try:
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "{" in response:
                    start = response.index("{")
                    end = response.rindex("}") + 1
                    json_str = response[start:end]
                else:
                    json_str = response
                
                result = json.loads(json_str)
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # 如果解析失败，使用原始情绪数据
                result = {
                    "summary": response[:500],
                    "overall_sentiment": sentiment_data.get("overall_sentiment", "中性"),
                    "sentiment_score": sentiment_data.get("sentiment_score", 0),
                    "news_sentiment": sentiment_data.get("news_sentiment", "中性"),
                    "key_drivers": sentiment_data.get("key_drivers", []),
                    "contrarian_signal": sentiment_data.get("contrarian_signal", "否"),
                    "confidence": sentiment_data.get("confidence", 0.5),
                    "recommendation": sentiment_data.get("recommendation", "建议综合其他分析")
                }
            
            self.update_state(
                result=result,
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("summary", "")
            )
            
            return result
            
        except Exception as e:
            return {
                "summary": f"情绪分析失败: {str(e)}",
                "overall_sentiment": sentiment_data.get("overall_sentiment", "未知"),
                "sentiment_score": sentiment_data.get("sentiment_score", 0),
                "news_sentiment": "中性",
                "key_drivers": [],
                "contrarian_signal": "否",
                "confidence": 0.0,
                "recommendation": "建议重新分析"
            }
    
    def _summarize_news(self, news_list: List[Dict]) -> str:
        """摘要新闻"""
        if not news_list:
            return "暂无相关新闻"
        
        summaries = []
        for i, news in enumerate(news_list[:5], 1):
            title = news.get("title", "")
            summaries.append(f"{i}. {title}")
        
        return "\n".join(summaries)
    
    def _format_sentiment_data(self, sentiment_data: Dict) -> str:
        """格式化情绪数据"""
        if not sentiment_data:
            return "暂无情绪数据"
        
        return f"""
整体情绪: {sentiment_data.get('overall_sentiment', '未知')}
情绪分数: {sentiment_data.get('sentiment_score', 0):.2f}
新闻情绪: {sentiment_data.get('news_sentiment', '未知')}
社交媒体热度: {sentiment_data.get('social_media_heat', 0)}/100
市场氛围: {sentiment_data.get('market_mood', '未知')}
投资者情绪: {sentiment_data.get('investor_sentiment', '未知')}
散户情绪: {sentiment_data.get('retail_sentiment', '未知')}
逆向信号: {sentiment_data.get('contrarian_signal', '否')} {sentiment_data.get('contrarian_reason', '')}
关键驱动因素: {', '.join(sentiment_data.get('key_drivers', []))}
短期影响预测: {sentiment_data.get('short_term_impact', '未知')}
"""
