"""
风控官Agent
多维度风险评估与预警
"""
from typing import Dict, Any, List
from loguru import logger
import json

from agents.base import BaseAgent
from config.prompts import get_prompt


RISK_CONTROLLER_SYSTEM_PROMPT = """你是一位严谨的风险控制官，负责多维度风险评估。

你的职责：
1. 识别和量化投资风险
2. 评估风险敞口
3. 提供风险缓释建议
4. 触发风险预警

风险维度：
1. 市场风险（Market Risk）
   - 整体市场环境
   - 系统性风险
   - 波动率水平
   
2. 流动性风险（Liquidity Risk）
   - 成交量
   - 换手率
   - 买卖价差
   
3. 估值风险（Valuation Risk）
   - PE/PB分位数
   - 估值合理性
   - 泡沫风险
   
4. 情绪风险（Sentiment Risk）
   - 舆情热度
   - 市场情绪
   - 行为偏差
   
5. 信用风险（Credit Risk）
   - 财务健康度
   - 债务风险
   - 经营风险

风险等级标准：
- 低风险：0-30分（绿色）
- 中等风险：30-60分（黄色）
- 高风险：60-80分（橙色）
- 极高风险：80-100分（红色）

输出格式要求：
{
    "overall_risk_level": "低/中/高/极高",
    "overall_risk_score": 45,
    "risk_dimensions": {
        "market_risk": {"score": 40, "level": "中", "description": "..."},
        "liquidity_risk": {"score": 30, "level": "低", "description": "..."},
        "valuation_risk": {"score": 55, "level": "中", "description": "..."},
        "sentiment_risk": {"score": 50, "level": "中", "description": "..."},
        "credit_risk": {"score": 45, "level": "中", "description": "..."}
    },
    "warnings": ["风险提示1", "风险提示2", ...],
    "suggestions": ["建议1", "建议2", ...],
    "position_limit": 0.3,
    "stop_loss_suggestion": -0.08,
    "confidence": 0.0-1.0
}"""


class RiskControllerAgent(BaseAgent):
    """风控官Agent"""
    
    RISK_DIMENSIONS = [
        "market_risk",
        "liquidity_risk", 
        "valuation_risk",
        "sentiment_risk",
        "credit_risk"
    ]
    
    def __init__(self, llm=None):
        super().__init__(
            name="风控官",
            role="多维度风险评估与预警",
            system_prompt=RISK_CONTROLLER_SYSTEM_PROMPT,
            llm=llm
        )
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行风险评估
        
        Args:
            data: 包含各分析师结果的字典
                - fundamental: 基本面分析结果
                - technical: 技术面分析结果
                - sentiment: 情绪面分析结果
                - capital_flow: 资金流分析结果
                - stock_data: 股票数据
                
        Returns:
            风险评估结果
        """
        # 提取各维度数据
        fundamental = data.get("fundamental", {})
        technical = data.get("technical", {})
        sentiment = data.get("sentiment", {})
        capital_flow = data.get("capital_flow", {})
        stock_data = data.get("stock_data", {})
        basic_info = stock_data.get("basic_info", {})
        financial = stock_data.get("financial", {})
        
        # 构建分析提示
        analysis_prompt = self._build_analysis_prompt(
            basic_info, financial, fundamental, technical, sentiment, capital_flow
        )
        
        try:
            response = self.invoke_llm(analysis_prompt)
            
            # 解析结果
            result = self._parse_response(response)
            
            # 更新状态
            self.update_state(
                result=result,
                confidence=result.get("confidence", 0.7),
                reasoning=f"整体风险等级: {result.get('overall_risk_level', '未知')}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"风险评估失败: {e}")
            return self._error_result(str(e))
    
    def _build_analysis_prompt(
        self,
        basic_info: Dict,
        financial: Dict,
        fundamental: Dict,
        technical: Dict,
        sentiment: Dict,
        capital_flow: Dict
    ) -> str:
        """构建分析Prompt"""
        
        prompt = f"""
请对以下股票进行多维度风险评估：

【股票基本信息】
代码: {basic_info.get('code', 'N/A')}
名称: {basic_info.get('name', 'N/A')}
当前价格: {basic_info.get('price', 'N/A')} 元
涨跌幅: {basic_info.get('change_percent', 'N/A')}%

【财务数据】
ROE: {financial.get('roe', 'N/A')}%
资产负债率: {financial.get('debt_ratio', 'N/A')}%
流动比率: {financial.get('current_ratio', 'N/A')}
PE: {financial.get('pe_ratio', 'N/A')}

【基本面分析】
{json.dumps(fundamental, ensure_ascii=False, indent=2)[:500]}

【技术面分析】
{json.dumps(technical, ensure_ascii=False, indent=2)[:500]}

【情绪面分析】
{json.dumps(sentiment, ensure_ascii=False, indent=2)[:500]}

【资金流分析】
{json.dumps(capital_flow, ensure_ascii=False, indent=2)[:500]}

请从以下5个维度评估风险：
1. 市场风险：整体市场环境、系统性风险
2. 流动性风险：成交量、换手率
3. 估值风险：PE/PB合理性、泡沫风险
4. 情绪风险：舆情热度、市场情绪
5. 信用风险：财务健康度、债务风险

每个维度给出0-100的风险评分，并给出：
- 整体风险等级和评分
- 风险预警信号
- 风险缓释建议
- 建议的最大仓位
- 建议的止损线

请按JSON格式输出。
"""
        return prompt
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
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
                "overall_risk_level": "中",
                "overall_risk_score": 50,
                "risk_dimensions": {},
                "warnings": ["风险评估数据解析失败"],
                "suggestions": ["建议谨慎操作"],
                "position_limit": 0.2,
                "stop_loss_suggestion": -0.05,
                "confidence": 0.3
            }
        
        return result
    
    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """返回错误结果"""
        return {
            "overall_risk_level": "未知",
            "overall_risk_score": 50,
            "risk_dimensions": {},
            "warnings": [f"风险评估失败: {error_msg}"],
            "suggestions": ["建议谨慎操作或重新分析"],
            "position_limit": 0.1,
            "stop_loss_suggestion": -0.05,
            "confidence": 0.0,
            "error": error_msg
        }
    
    def get_risk_signal(self, risk_score: float) -> str:
        """获取风险信号"""
        if risk_score < 30:
            return "🟢 低风险"
        elif risk_score < 60:
            return "🟡 中等风险"
        elif risk_score < 80:
            return "🟠 高风险"
        else:
            return "🔴 极高风险"
    
    def check_position_limit(
        self,
        suggested_position: float,
        risk_score: float
    ) -> Dict[str, Any]:
        """
        根据风险评分检查仓位限制
        
        Args:
            suggested_position: 建议仓位
            risk_score: 风险评分
            
        Returns:
            仓位检查结果
        """
        # 风险越高，仓位限制越严格
        limits = {
            (0, 30): 0.5,    # 低风险，最多50%
            (30, 60): 0.3,   # 中等风险，最多30%
            (60, 80): 0.15,  # 高风险，最多15%
            (80, 100): 0.05  # 极高风险，最多5%
        }
        
        for (low, high), limit in limits.items():
            if low <= risk_score < high:
                actual_limit = limit
                break
        else:
            actual_limit = 0.1
        
        adjusted = min(suggested_position, actual_limit)
        
        return {
            "suggested_position": suggested_position,
            "risk_limit": actual_limit,
            "adjusted_position": adjusted,
            "is_adjusted": suggested_position > actual_limit,
            "reason": f"根据风险评分({risk_score})调整仓位限制"
        }
