"""
新闻分析师Agent
负责分析宏观新闻和行业动态
"""
from typing import Dict, Any, List
import json

from agents.base import BaseAgent


NEWS_SYSTEM_PROMPT = """你是一位资深的宏观与行业分析师，擅长解读新闻事件对股市的影响。
你的专长是：
- 宏观经济政策分析
- 行业政策解读
- 公司重大事件评估
- 地缘政治影响分析

分析原则：
1. 区分短期噪音和长期趋势
2. 关注政策取向和监管动向
3. 评估事件的实质影响
4. 考虑市场预期与实际差异

请基于新闻信息，分析对目标股票的影响。

**重要**：你的分析需要说明每个新闻事件的影响机制、时间维度、以及对股价的具体影响路径。"""


class NewsAnalyst(BaseAgent):
    """新闻分析师"""
    
    def __init__(self, llm=None):
        super().__init__(
            name="新闻分析师",
            role="分析宏观新闻与行业动态",
            system_prompt=NEWS_SYSTEM_PROMPT,
            llm=llm
        )
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行新闻分析"""
        basic_info = data.get("basic_info", {})
        news_list = data.get("news", [])
        industry = data.get("industry", {})
        
        # 构建详细新闻内容
        news_content = self._format_news(news_list)
        
        analysis_prompt = f"""
请对以下股票进行深入的新闻与宏观分析：

【股票信息】
代码: {basic_info.get('code', 'N/A')}
名称: {basic_info.get('name', 'N/A')}

【行业信息】
{json.dumps(industry, ensure_ascii=False, indent=2)}

【近期新闻】
{news_content}

**请按以下要求进行深入分析：**
1. 识别并解读重大新闻事件，分析其对公司的影响
2. 评估行业政策环境的变化趋势
3. 分析宏观经济因素的影响
4. 识别潜在的催化剂事件
5. 评估各因素的时间维度（短期/中期/长期）

请分析：
1. 重大新闻事件及其影响
2. 行业政策动态
3. 宏观环境变化
4. 潜在催化剂

请按以下结构输出（JSON格式）：
{{
    "summary": "300-400字的新闻面分析摘要，包含主要事件和影响评估",
    "major_events": [
        {{
            "event": "事件描述",
            "impact": "正面/中性/负面",
            "magnitude": "高/中/低",
            "time_horizon": "短期/中期/长期",
            "analysis": "影响机制分析：该事件如何影响公司基本面或市场预期"
        }}
    ],
    "policy_environment": "政策环境评估：当前政策取向及对公司的影响",
    "industry_outlook": "行业前景判断：行业发展趋势及竞争格局变化",
    "catalysts": [
        "潜在催化剂1：具体事件+触发条件+预期影响",
        ...
    ],
    "risks": [
        "新闻面风险1：风险来源+触发条件+潜在损失",
        ...
    ],
    "confidence": 0.0-1.0,
    "recommendation": "新闻面操作建议：基于事件驱动的交易策略"
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
                result = {
                    "summary": response[:500],
                    "major_events": [],
                    "policy_environment": "中性",
                    "industry_outlook": "稳定",
                    "catalysts": [],
                    "risks": [],
                    "confidence": 0.5,
                    "recommendation": "建议综合其他分析"
                }
            
            self.update_state(
                result=result,
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("summary", "")
            )
            
            return result
            
        except Exception as e:
            return {
                "summary": f"新闻分析失败: {str(e)}",
                "major_events": [],
                "policy_environment": "未知",
                "industry_outlook": "未知",
                "catalysts": [],
                "risks": [],
                "confidence": 0.0,
                "recommendation": "建议重新分析"
            }
    
    def _format_news(self, news_list: List[Dict]) -> str:
        """格式化新闻内容"""
        if not news_list:
            return "暂无相关新闻"
        
        formatted = []
        for i, news in enumerate(news_list[:8], 1):
            title = news.get("title", "")
            source = news.get("source", "")
            time = news.get("publish_time", "")
            content = news.get("content", "")[:200]
            
            formatted.append(
                f"【新闻{i}】{title}\n"
                f"来源: {source} | 时间: {time}\n"
                f"内容摘要: {content}...\n"
            )
        
        return "\n".join(formatted)
