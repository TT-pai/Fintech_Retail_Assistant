"""
技术分析师Agent
负责分析K线形态和技术指标
"""
from typing import Dict, Any
import json

from agents.base import BaseAgent


TECHNICAL_SYSTEM_PROMPT = """你是一位资深技术分析师，精通各类技术指标和K线形态分析。
你的专长是：
- 趋势判断：MA均线系统、趋势线分析
- 动量指标：MACD、RSI、KDJ等
- 形态识别：头肩顶/底、双顶/底、三角形整理等
- 支撑压力位判断

分析原则：
1. 技术分析是概率游戏，没有100%准确
2. 多指标共振增加可靠性
3. 关注量价配合关系
4. 识别可能的假突破信号

请结合具体数据给出专业的技术面分析，明确指出当前趋势和关键位置。

**重要**：你的分析必须详细说明每个指标的状态、产生原因和交易启示。"""


class TechnicalAnalyst(BaseAgent):
    """技术分析师"""
    
    def __init__(self, llm=None):
        super().__init__(
            name="技术分析师",
            role="分析K线形态与技术指标",
            system_prompt=TECHNICAL_SYSTEM_PROMPT,
            llm=llm
        )
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行技术分析"""
        basic_info = data.get("basic_info", {})
        technical = data.get("technical", {})
        
        macd = technical.get("macd", {})
        bb = technical.get("bollinger_bands", {})
        
        analysis_prompt = f"""
请对以下股票进行深入的技术面分析：

【股票信息】
代码: {basic_info.get('code', 'N/A')}
名称: {basic_info.get('name', 'N/A')}
当前价格: {basic_info.get('price', 'N/A')} 元

【均线系统】
MA5: {technical.get('ma5', 'N/A')} 元
MA10: {technical.get('ma10', 'N/A')} 元
MA20: {technical.get('ma20', 'N/A')} 元
MA60: {technical.get('ma60', 'N/A')} 元
当前趋势: {technical.get('trend', 'N/A')}

【动量指标】
RSI(14): {technical.get('rsi', 'N/A')}
MACD:
  - DIF: {macd.get('dif', 'N/A')}
  - DEA: {macd.get('dea', 'N/A')}
  - 柱状图: {macd.get('histogram', 'N/A')}

【布林带】
上轨: {bb.get('upper', 'N/A')} 元
中轨: {bb.get('middle', 'N/A')} 元
下轨: {bb.get('lower', 'N/A')} 元
价格位置: {bb.get('position', 'N/A')} (0=下轨, 1=上轨)

**请按以下要求进行深入分析：**
1. 分析均线排列形态，说明当前趋势强度和方向
2. 解读MACD的金叉/死叉状态及柱状图变化的意义
3. 分析RSI所处的区域及其交易启示
4. 说明布林带位置反映的市场状态
5. 综合判断给出具体的支撑压力位和操作建议

请按以下结构输出分析结果（JSON格式）：
{{
    "summary": "300-400字的技术面整体判断，包含趋势分析和关键结论",
    "trend_analysis": "趋势分析详情：均线状态、趋势强度、持续时间预测",
    "key_levels": {{
        "support": ["支撑位1：具体价位+形成原因", "支撑位2"],
        "resistance": ["压力位1：具体价位+形成原因", "压力位2"]
    }},
    "signals": {{
        "bullish": ["看多信号1：具体指标+信号含义+可靠性评估", ...],
        "bearish": ["看空信号1：具体指标+信号含义+可靠性评估", ...]
    }},
    "rsi_status": "RSI状态判断（超买/超卖/正常）及交易启示",
    "macd_status": "MACD状态判断及趋势预测",
    "confidence": 0.0-1.0,
    "recommendation": "技术面操作建议：具体入场点、止损位、目标位"
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
                    "trend_analysis": "详见摘要",
                    "key_levels": {"support": [], "resistance": []},
                    "signals": {"bullish": [], "bearish": []},
                    "rsi_status": "未知",
                    "macd_status": "未知",
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
                "summary": f"技术分析失败: {str(e)}",
                "trend_analysis": "分析异常",
                "key_levels": {"support": [], "resistance": []},
                "signals": {"bullish": [], "bearish": []},
                "rsi_status": "未知",
                "macd_status": "未知",
                "confidence": 0.0,
                "recommendation": "建议重新分析"
            }
