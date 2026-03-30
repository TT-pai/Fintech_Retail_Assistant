"""
红蓝军辩论模块
看多研究员 vs 看空研究员的结构化辩论
"""
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import json

from agents.base import BaseAgent


BULL_SYSTEM_PROMPT = """你是一位坚定的看多研究员（牛派分析师）。
你的职责是：
- 从所有分析中挖掘看多理由
- 挑战看空观点，找出其逻辑漏洞
- 强调潜在的机会和上涨空间
- 提供积极但理性的投资论据

辩论原则：
1. 基于数据和事实，不是盲目乐观
2. 承认风险存在，但强调机会更大
3. 用逻辑和证据支持你的观点
4. 尊重对手但坚持己见

请针对给定的分析结果，提出强有力的看多论点。"""


BEAR_SYSTEM_PROMPT = """你是一位谨慎的看空研究员（熊派分析师）。
你的职责是：
- 从所有分析中发现风险和隐忧
- 挑战看多观点，找出其过度乐观之处
- 强调潜在的风险和下跌空间
- 提供谨慎但理性的预警

辩论原则：
1. 基于数据和事实，不是盲目悲观
2. 承认机会存在，但强调风险更大
3. 用逻辑和证据支持你的观点
4. 尊重对手但坚持己见

请针对给定的分析结果，提出强有力的看空论点。"""


class BullResearcher(BaseAgent):
    """看多研究员"""
    
    def __init__(self, llm=None):
        super().__init__(
            name="看多研究员",
            role="挖掘看多理由，挑战看空观点",
            system_prompt=BULL_SYSTEM_PROMPT,
            llm=llm
        )
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成看多论点"""
        return self._generate_arguments(data)
    
    def _generate_arguments(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成看多论点"""
        prompt = f"""
基于以下分析结果，请提出你的看多论点：

【基本面分析】
{json.dumps(analysis_data.get('fundamental', {}), ensure_ascii=False, indent=2)}

【技术面分析】
{json.dumps(analysis_data.get('technical', {}), ensure_ascii=False, indent=2)}

【情绪面分析】
{json.dumps(analysis_data.get('sentiment', {}), ensure_ascii=False, indent=2)}

【新闻面分析】
{json.dumps(analysis_data.get('news', {}), ensure_ascii=False, indent=2)}

请输出JSON格式：
{{
    "bull_case": "核心看多逻辑",
    "key_arguments": ["论点1", "论点2", ...],
    "risk_acknowledgment": "我承认的风险点",
    "upside_potential": "上涨空间评估",
    "confidence_level": 0.0-1.0,
    "rebuttal_points": ["针对看空观点的反驳"]
}}
"""
        response = self.invoke_llm(prompt)
        return self._parse_response(response)
    
    def rebut(self, bear_arguments: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """反驳看空观点"""
        prompt = f"""
看空研究员提出以下论点：
{json.dumps(bear_arguments, ensure_ascii=False, indent=2)}

请针对这些看空论点进行反驳，并重申你的看多立场。

输出JSON格式：
{{
    "rebuttal": "反驳陈述",
    "counter_points": ["反驳点1", "反驳点2", ...],
    "remaining_concern": "仍需关注的问题",
    "confidence_after_debate": 0.0-1.0
}}
"""
        response = self.invoke_llm(prompt)
        return self._parse_response(response)
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析响应"""
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "{" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                json_str = response[start:end]
            else:
                return {"raw_response": response}
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError, KeyError):
            return {"raw_response": response}


class BearResearcher(BaseAgent):
    """看空研究员"""
    
    def __init__(self, llm=None):
        super().__init__(
            name="看空研究员",
            role="发现风险隐忧，挑战看多观点",
            system_prompt=BEAR_SYSTEM_PROMPT,
            llm=llm
        )
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成看空论点"""
        return self._generate_arguments(data)
    
    def _generate_arguments(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成看空论点"""
        prompt = f"""
基于以下分析结果，请提出你的看空论点：

【基本面分析】
{json.dumps(analysis_data.get('fundamental', {}), ensure_ascii=False, indent=2)}

【技术面分析】
{json.dumps(analysis_data.get('technical', {}), ensure_ascii=False, indent=2)}

【情绪面分析】
{json.dumps(analysis_data.get('sentiment', {}), ensure_ascii=False, indent=2)}

【新闻面分析】
{json.dumps(analysis_data.get('news', {}), ensure_ascii=False, indent=2)}

请输出JSON格式：
{{
    "bear_case": "核心看空逻辑",
    "key_arguments": ["论点1", "论点2", ...],
    "opportunity_acknowledgment": "我承认的机会点",
    "downside_risk": "下跌风险评估",
    "confidence_level": 0.0-1.0,
    "rebuttal_points": ["针对看多观点的反驳"]
}}
"""
        response = self.invoke_llm(prompt)
        return self._parse_response(response)
    
    def rebut(self, bull_arguments: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """反驳看多观点"""
        prompt = f"""
看多研究员提出以下论点：
{json.dumps(bull_arguments, ensure_ascii=False, indent=2)}

请针对这些看多论点进行反驳，并重申你的看空立场。

输出JSON格式：
{{
    "rebuttal": "反驳陈述",
    "counter_points": ["反驳点1", "反驳点2", ...],
    "remaining_hope": "仍可能的上行空间",
    "confidence_after_debate": 0.0-1.0
}}
"""
        response = self.invoke_llm(prompt)
        return self._parse_response(response)
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析响应"""
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "{" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                json_str = response[start:end]
            else:
                return {"raw_response": response}
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError, KeyError):
            return {"raw_response": response}


class DebateRoom:
    """辩论室 - 管理多轮辩论流程"""
    
    def __init__(self, llm=None, max_rounds: int = 2):
        self.bull = BullResearcher(llm=llm)
        self.bear = BearResearcher(llm=llm)
        self.max_rounds = max_rounds
        self.debate_history: List[Dict[str, Any]] = []
    
    def conduct_debate(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行多轮辩论
        Returns:
            辩论结果，包含双方观点和辩论历史
        """
        self.debate_history = []
        
        # 第一轮：双方提出初始论点
        bull_args = self.bull.analyze(analysis_results)
        bear_args = self.bear.analyze(analysis_results)
        
        self.debate_history.append({
            "round": 1,
            "type": "opening",
            "bull_arguments": bull_args,
            "bear_arguments": bear_args
        })
        
        # 后续轮次：互相反驳
        for round_num in range(2, self.max_rounds + 1):
            bull_rebuttal = self.bull.rebut(bear_args, analysis_results)
            bear_rebuttal = self.bear.rebut(bull_args, analysis_results)
            
            self.debate_history.append({
                "round": round_num,
                "type": "rebuttal",
                "bull_rebuttal": bull_rebuttal,
                "bear_rebuttal": bear_rebuttal
            })
            
            # 更新论点供下一轮使用
            bull_args = bull_rebuttal
            bear_args = bear_rebuttal
        
        return {
            "debate_history": self.debate_history,
            "bull_final_stance": bull_args,
            "bear_final_stance": bear_args,
            "total_rounds": self.max_rounds
        }
    
    def get_debate_summary(self) -> str:
        """获取辩论摘要"""
        summary_parts = []
        
        for record in self.debate_history:
            round_num = record["round"]
            summary_parts.append(f"\n=== 第{round_num}轮辩论 ===\n")
            
            if record["type"] == "opening":
                summary_parts.append(f"【看多观点】{record['bull_arguments'].get('bull_case', 'N/A')}")
                summary_parts.append(f"【看空观点】{record['bear_arguments'].get('bear_case', 'N/A')}")
            else:
                summary_parts.append(f"【看多反驳】{record['bull_rebuttal'].get('rebuttal', 'N/A')}")
                summary_parts.append(f"【看空反驳】{record['bear_rebuttal'].get('rebuttal', 'N/A')}")
        
        return "\n".join(summary_parts)
