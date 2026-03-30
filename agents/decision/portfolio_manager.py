"""
决策团队模块
交易员和投资组合经理
"""
from typing import Dict, Any, List
import json

from agents.base import BaseAgent


TRADER_SYSTEM_PROMPT = """你是一位经验丰富的交易员，负责综合各方分析做出交易决策。
你的职责是：
- 整合分析师团队的多元观点
- 评估辩论过程中的关键论据
- 平衡风险与收益
- 给出具体的交易建议

决策原则：
1. 综合判断，不偏信单一观点
2. 关注风险收益比
3. 考虑仓位管理
4. 设置止损止盈

请基于所有分析结果，给出专业的交易建议。"""


PORTFOLIO_MANAGER_SYSTEM_PROMPT = """你是投资组合经理，负责最终的投资决策审批。
你的职责是：
- 审核交易员的建议
- 评估整体风险敞口
- 确保决策符合风控要求
- 考虑投资组合的整体配置

审批原则：
1. 严格风险控制
2. 分散投资原则
3. 流动性管理
4. 合规性检查

请审核交易建议并给出最终决策。"""


class Trader(BaseAgent):
    """交易员"""
    
    def __init__(self, llm=None):
        super().__init__(
            name="交易员",
            role="整合分析结果，提出交易建议",
            system_prompt=TRADER_SYSTEM_PROMPT,
            llm=llm
        )
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """综合分析并给出交易建议"""
        return self.make_decision(data)
    
    def make_decision(
        self,
        analysis_results: Dict[str, Any],
        debate_result: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        做出交易决策
        Args:
            analysis_results: 分析师团队的分析结果
            debate_result: 辩论结果
        """
        debate_summary = ""
        if debate_result:
            debate_summary = f"""
【辩论结果摘要】
看多最终立场: {json.dumps(debate_result.get('bull_final_stance', {}), ensure_ascii=False)}
看空最终立场: {json.dumps(debate_result.get('bear_final_stance', {}), ensure_ascii=False)}
"""
        
        prompt = f"""
请综合以下所有分析，做出交易决策：

【股票基本信息】
{json.dumps(analysis_results.get('basic_info', {}), ensure_ascii=False, indent=2)}

【基本面分析】
{json.dumps(analysis_results.get('fundamental', {}), ensure_ascii=False, indent=2)}

【技术面分析】
{json.dumps(analysis_results.get('technical', {}), ensure_ascii=False, indent=2)}

【情绪面分析】
{json.dumps(analysis_results.get('sentiment', {}), ensure_ascii=False, indent=2)}

【新闻面分析】
{json.dumps(analysis_results.get('news', {}), ensure_ascii=False, indent=2)}

{debate_summary}

请输出交易建议（JSON格式）：
{{
    "decision": "强烈买入/买入/持有/卖出/强烈卖出",
    "confidence": 0.0-1.0,
    "position_suggestion": "建议仓位比例(%)",
    "entry_price_range": {{"low": 价格, "high": 价格}},
    "stop_loss_price": "止损价格",
    "take_profit_price": "止盈价格",
    "holding_period": "建议持有周期",
    "key_reasons": ["理由1", "理由2", ...],
    "main_risks": ["风险1", "风险2", ...],
    "summary": "决策摘要（一句话）"
}}
"""
        
        try:
            response = self.invoke_llm(prompt)
            
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
            except (json.JSONDecodeError, ValueError, KeyError):
                result = {
                    "decision": "持有",
                    "confidence": 0.5,
                    "position_suggestion": "观望",
                    "entry_price_range": {},
                    "stop_loss_price": "N/A",
                    "take_profit_price": "N/A",
                    "holding_period": "待定",
                    "key_reasons": ["分析结果不确定"],
                    "main_risks": ["建议谨慎"],
                    "summary": response[:100]
                }
            
            self.update_state(
                result=result,
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("summary", "")
            )
            
            return result
            
        except Exception as e:
            return {
                "decision": "持有",
                "confidence": 0.0,
                "position_suggestion": "观望",
                "entry_price_range": {},
                "stop_loss_price": "N/A",
                "take_profit_price": "N/A",
                "holding_period": "待定",
                "key_reasons": [f"分析失败: {str(e)}"],
                "main_risks": ["无法完成分析"],
                "summary": "建议观望"
            }


class PortfolioManager(BaseAgent):
    """投资组合经理"""
    
    def __init__(self, llm=None):
        super().__init__(
            name="投资组合经理",
            role="审批交易决策，管理整体风险",
            system_prompt=PORTFOLIO_MANAGER_SYSTEM_PROMPT,
            llm=llm
        )
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """审核决策"""
        return self.review_decision(data)
    
    def review_decision(
        self,
        trader_decision: Dict[str, Any],
        analysis_results: Dict[str, Any] = None,
        risk_profile: str = "moderate"
    ) -> Dict[str, Any]:
        """
        审核交易决策
        Args:
            trader_decision: 交易员的决策
            analysis_results: 分析结果
            risk_profile: 用户风险偏好 conservative/moderate/aggressive
        """
        prompt = f"""
作为投资组合经理，请审核以下交易决策：

【交易员建议】
{json.dumps(trader_decision, ensure_ascii=False, indent=2)}

【用户风险偏好】
{risk_profile}

【风险控制要求】
1. 单一股票仓位不超过总资产的20%
2. 高风险资产比例不超过30%
3. 必须设置止损
4. 考虑流动性风险

请输出审核结果（JSON格式）：
{{
    "approval_status": "批准/有条件批准/拒绝",
    "adjusted_position": "调整后的仓位建议(%)",
    "risk_assessment": "整体风险评估",
    "conditions": ["附加条件1", ...]（如有）,
    "final_decision": "最终决策",
    "final_confidence": 0.0-1.0,
    "key_reminders": ["重要提醒1", ...],
    "summary": "审批摘要"
}}
"""
        
        try:
            response = self.invoke_llm(prompt)
            
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
            except (json.JSONDecodeError, ValueError, KeyError):
                result = {
                    "approval_status": "有条件批准",
                    "adjusted_position": trader_decision.get("position_suggestion", "5%"),
                    "risk_assessment": "中等风险",
                    "conditions": ["建议分批建仓"],
                    "final_decision": trader_decision.get("decision", "持有"),
                    "final_confidence": 0.5,
                    "key_reminders": ["请注意风险控制"],
                    "summary": "审批准入"
                }
            
            self.update_state(
                result=result,
                confidence=result.get("final_confidence", 0.5),
                reasoning=result.get("summary", "")
            )
            
            return result
            
        except Exception as e:
            return {
                "approval_status": "有条件批准",
                "adjusted_position": "5%",
                "risk_assessment": "风险未知",
                "conditions": ["建议进一步研究"],
                "final_decision": "持有",
                "final_confidence": 0.3,
                "key_reminders": ["审核过程出现异常"],
                "summary": f"审核异常: {str(e)}"
            }
    
    def generate_final_report(
        self,
        stock_info: Dict[str, Any],
        analysis_results: Dict[str, Any],
        debate_result: Dict[str, Any],
        trader_decision: Dict[str, Any],
        pm_review: Dict[str, Any]
    ) -> str:
        """生成最终投资报告"""
        
        # 获取辩论观点
        bull_stance = debate_result.get("bull_final_stance", {})
        bear_stance = debate_result.get("bear_final_stance", {})
        
        bull_case = (
            bull_stance.get("bull_case") or 
            bull_stance.get("rebuttal") or 
            bull_stance.get("raw_response") or 
            "分析中..."
        )
        
        bear_case = (
            bear_stance.get("bear_case") or 
            bear_stance.get("rebuttal") or 
            bear_stance.get("raw_response") or 
            "分析中..."
        )
        
        report = f"""
# 📊 {stock_info.get('name', '')} ({stock_info.get('code', '')}) 投资分析报告

## 一、股票概览
- 当前价格: {stock_info.get('price', 'N/A')} 元
- 今日涨跌: {stock_info.get('change_percent', 'N/A')}%
- 成交量: {stock_info.get('volume', 'N/A')}

## 二、多维度分析摘要

### 基本面分析
{analysis_results.get('fundamental', {}).get('summary', '分析中...')}

### 技术面分析
{analysis_results.get('technical', {}).get('summary', '分析中...')}

### 情绪面分析
{analysis_results.get('sentiment', {}).get('summary', '分析中...')}

### 新闻面分析
{analysis_results.get('news', {}).get('summary', '分析中...')}

## 三、红绿辩论精华

### 🔴 看多观点
{bull_case}

### 🟢 看空观点
{bear_case}

## 四、交易建议

### 交易员建议
- 决策: **{trader_decision.get('decision', '持有')}**
- 置信度: {trader_decision.get('confidence', 0) * 100:.0f}%
- 建议仓位: {trader_decision.get('position_suggestion', '观望')}
- 持有周期: {trader_decision.get('holding_period', '待定')}

### 投资组合经理审批
- 审批状态: **{pm_review.get('approval_status', '待审批')}**
- 调整后仓位: {pm_review.get('adjusted_position', '观望')}
- 风险评估: {pm_review.get('risk_assessment', '评估中')}

## 五、风险提示

{chr(10).join(['- ' + r for r in trader_decision.get('main_risks', ['投资有风险，入市需谨慎'])])}

## 六、重要声明

本报告由AI智能投研系统生成，仅供参考研究使用，不构成任何投资建议。
投资决策应基于个人判断，并充分考虑自身风险承受能力。
市场有风险，投资需谨慎。

---
*报告生成时间: 由智汇投研系统自动生成*
"""
        
        return report
