"""
资金流分析Agent
分析主力资金、北向资金、机构持仓等
"""
from typing import Dict, Any, List, Optional
from loguru import logger
import json

from agents.base import BaseAgent
from config.prompts import get_prompt


CAPITAL_FLOW_SYSTEM_PROMPT = """你是一位资金流向分析专家，专注于追踪主力资金动向。

你的职责：
1. 分析主力资金进出情况
2. 追踪北向资金/南向资金流向
3. 解读机构持仓变化
4. 分析龙虎榜数据
5. 解读融资融券数据

分析原则：
1. 跟随聪明资金，但不盲目跟风
2. 关注资金持续性和一致性
3. 区分主动买入和被动配置
4. 结合筹码分布判断压力位

资金流向判断标准：
- 主力净流入 > 0：资金流入，偏多
- 主力净流入 < 0：资金流出，偏空
- 北向资金连续流入：外资看好
- 北向资金连续流出：外资谨慎

输出格式要求：
{
    "summary": "资金面分析摘要",
    "main_force": {
        "net_inflow": 100000000,
        "trend": "流入/流出/平衡",
        "strength": "强/中/弱"
    },
    "northbound": {
        "net_inflow": 50000000,
        "consecutive_days": 3,
        "trend": "流入/流出"
    },
    "institution": {
        "holding_change": "增持/减持/不变",
        "confidence": "高/中/低"
    },
    "margin_trading": {
        "financing_balance": 1000000000,
        "trend": "上升/下降"
    },
    "conclusion": "整体判断",
    "signal": "买入/持有/卖出",
    "confidence": 0.0-1.0
}"""


class CapitalFlowAnalyst(BaseAgent):
    """资金流分析师"""
    
    def __init__(self, llm=None):
        super().__init__(
            name="资金流分析师",
            role="追踪主力资金与机构动向",
            system_prompt=CAPITAL_FLOW_SYSTEM_PROMPT,
            llm=llm
        )
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行资金流分析
        
        Args:
            data: 股票数据，包含basic_info, technical, capital_flow等
            
        Returns:
            资金流分析结果
        """
        basic_info = data.get("basic_info", {})
        technical = data.get("technical", {})
        capital_flow_data = data.get("capital_flow", {})  # 获取资金流数据
        
        # 构建分析提示
        analysis_prompt = self._build_analysis_prompt(basic_info, technical, capital_flow_data)
        
        try:
            response = self.invoke_llm(analysis_prompt)
            
            # 解析结果
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
                # 如果解析失败，使用原始资金流数据
                result = {
                    "summary": response[:300] if response else capital_flow_data.get("conclusion", "资金流分析"),
                    "main_force": capital_flow_data.get("main_force", {"net_inflow": 0, "trend": "未知", "strength": "中"}),
                    "northbound": capital_flow_data.get("northbound", {"net_inflow": 0, "trend": "未知"}),
                    "institution": capital_flow_data.get("institution", {"holding_change": "未知", "confidence": "低"}),
                    "margin_trading": capital_flow_data.get("margin_trading", {"trend": "未知"}),
                    "conclusion": capital_flow_data.get("conclusion", "数据不足，建议谨慎"),
                    "signal": capital_flow_data.get("signal", "持有"),
                    "confidence": capital_flow_data.get("confidence", 0.5)
                }
            
            # 更新状态
            self.update_state(
                result=result,
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("summary", "")
            )
            
            return result
            
        except Exception as e:
            logger.error(f"资金流分析失败: {e}")
            return self._error_result(str(e), capital_flow_data)
    
    def _build_analysis_prompt(
        self,
        basic_info: Dict[str, Any],
        technical: Dict[str, Any],
        capital_flow_data: Dict[str, Any]
    ) -> str:
        """构建分析Prompt"""
        
        # 从数据中提取资金相关指标
        volume = basic_info.get("volume", 0)
        turnover = basic_info.get("turnover", 0)
        
        # 格式化资金流数据
        capital_flow_summary = self._format_capital_flow_data(capital_flow_data)
        
        prompt = f"""
请对以下股票进行资金面分析：

【股票基本信息】
代码: {basic_info.get('code', 'N/A')}
名称: {basic_info.get('name', 'N/A')}
当前价格: {basic_info.get('price', 'N/A')} 元
成交量: {volume}
成交额: {turnover}

【技术指标】
{json.dumps(technical, ensure_ascii=False, indent=2)}

【资金流向数据】
{capital_flow_summary}

请分析：
1. 主力资金动向及其影响
2. 北向资金流向及连续性
3. 机构持仓变化的意义
4. 融资融券情况分析
5. 综合资金面判断

注意：
- 基于提供的资金数据进行深入分析
- 说明资金流向对股价的影响机制
- 给出明确的资金面信号

请按JSON格式输出分析结果：
{{
    "summary": "资金面分析摘要",
    "main_force": {{
        "net_inflow": 净流入金额,
        "trend": "流入/流出/平衡",
        "strength": "强/中/弱",
        "analysis": "主力资金动向分析"
    }},
    "northbound": {{
        "net_inflow": 净流入金额,
        "trend": "流入/流出",
        "consecutive_days": 连续天数,
        "analysis": "北向资金分析"
    }},
    "institution": {{
        "holding_change": "增持/减持/不变",
        "confidence": "高/中/低",
        "analysis": "机构持仓分析"
    }},
    "margin_trading": {{
        "financing_balance": 融资余额,
        "trend": "上升/下降",
        "analysis": "融资融券分析"
    }},
    "conclusion": "整体判断",
    "signal": "买入/持有/卖出",
    "confidence": 0.0-1.0
}}
"""
        return prompt
    
    def _format_capital_flow_data(self, capital_flow_data: Dict[str, Any]) -> str:
        """格式化资金流数据"""
        if not capital_flow_data:
            return "暂无资金流数据"
        
        main_force = capital_flow_data.get("main_force", {})
        northbound = capital_flow_data.get("northbound", {})
        institution = capital_flow_data.get("institution", {})
        margin = capital_flow_data.get("margin_trading", {})
        
        return f"""
【主力资金】
净流入: {main_force.get('net_inflow', 0):.2f} 元
趋势: {main_force.get('trend', '未知')}
强度: {main_force.get('strength', '中')}

【北向资金】
净流入: {northbound.get('net_inflow', 0):.2f} 元
趋势: {northbound.get('trend', '未知')}
连续天数: {northbound.get('consecutive_days', 0)} 天

【机构持仓】
变化: {institution.get('holding_change', '未知')}
置信度: {institution.get('confidence', '低')}
持仓比例: {institution.get('holdings_ratio', 0):.2f}%

【融资融券】
融资余额: {margin.get('financing_balance', 0):.2f} 元
趋势: {margin.get('trend', '未知')}

【综合判断】
{capital_flow_data.get('conclusion', '无')}
信号: {capital_flow_data.get('signal', '持有')}
"""
    
    def _error_result(self, error_msg: str, capital_flow_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """返回错误结果"""
        capital_flow_data = capital_flow_data or {}
        return {
            "summary": f"资金流分析失败: {error_msg}",
            "main_force": capital_flow_data.get("main_force", {"net_inflow": 0, "trend": "未知", "strength": "中"}),
            "northbound": capital_flow_data.get("northbound", {"net_inflow": 0, "trend": "未知"}),
            "institution": capital_flow_data.get("institution", {"holding_change": "未知", "confidence": "低"}),
            "margin_trading": capital_flow_data.get("margin_trading", {"trend": "未知"}),
            "conclusion": "分析失败",
            "signal": "持有",
            "confidence": 0.0,
            "error": error_msg
        }
    
    def get_capital_flow_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取资金流向数据（实际应用中接入数据源）
        
        Args:
            stock_code: 股票代码
            
        Returns:
            资金流向数据
        """
        # 这里可以接入实际的资金流向API
        # 如东方财富、同花顺等数据源
        return {
            "stock_code": stock_code,
            "main_force": {
                "net_inflow": 0,
                "buy_amount": 0,
                "sell_amount": 0
            },
            "northbound": {
                "net_inflow": 0,
                "holdings": 0
            },
            "institution": {
                "holdings_ratio": 0,
                "change_ratio": 0
            },
            "margin": {
                "financing_balance": 0,
                "securities_balance": 0
            }
        }
