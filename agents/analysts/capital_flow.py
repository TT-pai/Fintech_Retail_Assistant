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
            data: 股票数据，包含basic_info, technical等
            
        Returns:
            资金流分析结果
        """
        basic_info = data.get("basic_info", {})
        technical = data.get("technical", {})
        
        # 构建分析提示
        analysis_prompt = self._build_analysis_prompt(basic_info, technical)
        
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
                result = {
                    "summary": response[:300],
                    "main_force": {"net_inflow": 0, "trend": "未知", "strength": "中"},
                    "northbound": {"net_inflow": 0, "trend": "未知"},
                    "institution": {"holding_change": "未知", "confidence": "低"},
                    "margin_trading": {"trend": "未知"},
                    "conclusion": "数据不足，建议谨慎",
                    "signal": "持有",
                    "confidence": 0.5
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
            return self._error_result(str(e))
    
    def _build_analysis_prompt(
        self,
        basic_info: Dict[str, Any],
        technical: Dict[str, Any]
    ) -> str:
        """构建分析Prompt"""
        
        # 从数据中提取资金相关指标
        volume = basic_info.get("volume", 0)
        turnover = basic_info.get("turnover", 0)
        
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

请分析：
1. 主力资金动向（如果有数据）
2. 北向资金流向（如果有数据）
3. 机构持仓变化（如果有数据）
4. 融资融券情况（如果有数据）
5. 综合资金面判断

注意：
- 如果数据不足，请基于可获取的信息进行合理推断
- 明确标注哪些是推断，哪些是数据支撑
- 给出明确的资金面信号

请按JSON格式输出分析结果。
"""
        return prompt
    
    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """返回错误结果"""
        return {
            "summary": f"资金流分析失败: {error_msg}",
            "main_force": {"net_inflow": 0, "trend": "未知", "strength": "中"},
            "northbound": {"net_inflow": 0, "trend": "未知"},
            "institution": {"holding_change": "未知", "confidence": "低"},
            "margin_trading": {"trend": "未知"},
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
