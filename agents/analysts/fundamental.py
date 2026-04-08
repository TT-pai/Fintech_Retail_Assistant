"""
基本面分析师Agent
负责评估公司财务状况和内在价值
"""
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
import json

from agents.base import BaseAgent


FUNDAMENTAL_SYSTEM_PROMPT = """你是一位资深的基本面分析师，拥有20年A股投资研究经验。
你的专长是：
- 深度解读财务报表，识别公司真实盈利能力
- 发现财务报表中的潜在红旗警告
- 评估公司的内在价值和安全边际
- 分析行业竞争格局和公司护城河

分析原则：
1. 基于数据和事实，避免主观臆断
2. 关注ROE、现金流、负债率等核心指标
3. 警惕财务造假信号（应收账款激增、存货积压等）
4. 评估公司治理结构和管理层质量

请用专业但易懂的语言进行分析，最后给出明确的投资观点。

**重要**：你的分析必须详细、深入，每个发现都要说明原因和影响。不要只给出结论，要解释"为什么"。"""


class FundamentalAnalyst(BaseAgent):
    """基本面分析师"""
    
    def __init__(self, llm=None):
        super().__init__(
            name="基本面分析师",
            role="评估公司财务状况与内在价值",
            system_prompt=FUNDAMENTAL_SYSTEM_PROMPT,
            llm=llm
        )
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行基本面分析
        Args:
            data: 包含basic_info, financial, industry等字段的数据
        """
        basic_info = data.get("basic_info", {})
        financial = data.get("financial", {})
        industry = data.get("industry", {})
        
        # 构建分析提示
        analysis_prompt = f"""
请对以下股票进行全面深入的基本面分析：

【股票基本信息】
代码: {basic_info.get('code', 'N/A')}
名称: {basic_info.get('name', 'N/A')}
当前价格: {basic_info.get('price', 'N/A')} 元
涨跌幅: {basic_info.get('change_percent', 'N/A')}%

【关键财务指标】
净资产收益率(ROE): {financial.get('roe', 'N/A')}%
总资产净利率(ROA): {financial.get('roa', 'N/A')}%
销售毛利率: {financial.get('gross_margin', 'N/A')}%
销售净利率: {financial.get('net_margin', 'N/A')}%
资产负债率: {financial.get('debt_ratio', 'N/A')}%
流动比率: {financial.get('current_ratio', 'N/A')}
速动比率: {financial.get('quick_ratio', 'N/A')}
每股收益(EPS): {financial.get('eps', 'N/A')} 元
每股净资产(BVPS): {financial.get('bvps', 'N/A')} 元

【行业信息】
{json.dumps(industry, ensure_ascii=False, indent=2)}

**请按以下要求进行深入分析：**
1. 分析每个财务指标的具体含义和当前状态
2. 说明这些指标反映了什么问题或机会
3. 与行业平均水平对比（如能推断）
4. 指出潜在的风险点和机会点
5. 给出明确的投资建议和理由

请按以下结构输出分析结果（JSON格式）：
{{
    "summary": "300-500字的整体评价摘要，包含主要发现和结论",
    "key_findings": [
        "关键发现1：具体内容+原因分析+影响评估",
        "关键发现2：具体内容+原因分析+影响评估",
        ...
    ],
    "valuation": "估值评估：当前估值水平、合理估值区间、估值逻辑",
    "quality_score": 0-100的质量评分,
    "red_flags": ["风险点1：具体描述+潜在影响", ...],
    "strengths": ["优势1：具体描述+竞争优势", ...],
    "confidence": 0.0-1.0的置信度,
    "recommendation": "买入/持有/卖出建议及详细理由"
}}
"""
        
        try:
            response = self.invoke_llm(analysis_prompt)
            
            # 尝试解析JSON
            try:
                # 提取JSON部分
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
                # 如果解析失败，构造基本结果
                result = {
                    "summary": response[:500],
                    "key_findings": ["分析完成，详见摘要"],
                    "valuation": "待评估",
                    "quality_score": 50,
                    "red_flags": [],
                    "strengths": [],
                    "confidence": 0.6,
                    "recommendation": "建议结合其他分析维度综合判断"
                }
            
            # 更新状态
            self.update_state(
                result=result,
                confidence=result.get("confidence", 0.6),
                reasoning=result.get("summary", "")
            )
            
            return result
            
        except Exception as e:
            return {
                "summary": f"分析失败: {str(e)}",
                "key_findings": [],
                "valuation": "无法评估",
                "quality_score": 0,
                "red_flags": ["分析过程出错"],
                "strengths": [],
                "confidence": 0.0,
                "recommendation": "建议重新分析"
            }
