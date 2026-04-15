"""
研报检索Agent
基于RAG检索相关研报，提取关键观点
"""
from typing import Dict, Any, List, Optional
from loguru import logger
import json

from agents.base import BaseAgent
from config.prompts import get_prompt
from rag.retriever import RAGRetriever


REPORT_RETRIEVER_SYSTEM_PROMPT = """你是一位研报分析专家，负责从券商研报中提取关键投资信息。

你的职责：
1. 提取研报核心观点和投资逻辑
2. 汇总机构评级和目标价
3. 识别市场共识和分歧点
4. 评估研报时效性和权威性

输出格式要求：
{
    "summary": "研报观点摘要（200字以内）",
    "core_views": ["核心观点1", "核心观点2", ...],
    "ratings": {
        "buy": 3,
        "hold": 2,
        "sell": 0,
        "avg_target_price": 180.5
    },
    "risks": ["风险点1", "风险点2", ...],
    "opportunities": ["机会点1", "机会点2", ...],
    "sources": [
        {"institution": "中信证券", "date": "2024-04-28", "rating": "买入"},
        ...
    ],
    "confidence": 0.85
}

请基于检索到的研报内容进行分析。"""


class ReportRetrieverAgent(BaseAgent):
    """研报检索Agent"""
    
    def __init__(self, llm=None, retriever: Optional[RAGRetriever] = None):
        super().__init__(
            name="研报检索员",
            role="检索与分析券商研报",
            system_prompt=REPORT_RETRIEVER_SYSTEM_PROMPT,
            llm=llm
        )
        self.retriever = retriever
    
    def set_retriever(self, retriever: RAGRetriever) -> None:
        """设置检索器"""
        self.retriever = retriever
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行研报检索分析
        
        Args:
            data: 包含以下字段:
                - stock_code: 股票代码（可选）
                - stock_name: 股票名称（可选）
                - query: 查询文本（可选）
                - stock_data: 股票数据（可选，从中提取代码和名称）
                
        Returns:
            研报分析结果
        """
        # 提取股票信息
        stock_code = data.get("stock_code")
        stock_name = data.get("stock_name")
        
        # 从stock_data中提取
        stock_data = data.get("stock_data", {})
        if stock_data:
            basic_info = stock_data.get("basic_info", {})
            stock_code = stock_code or basic_info.get("code")
            stock_name = stock_name or basic_info.get("name")
        
        # 构建查询
        query = data.get("query", "")
        if stock_name and not query:
            query = f"{stock_name} 研报观点 评级"
        elif stock_code and not query:
            query = f"{stock_code} 研报观点 评级"
        
        if not query:
            return {
                "summary": "未提供有效的查询条件",
                "core_views": [],
                "ratings": {"buy": 0, "hold": 0, "sell": 0, "avg_target_price": None},
                "risks": [],
                "opportunities": [],
                "sources": [],
                "confidence": 0.0
            }
        
        # 检索研报
        if not self.retriever:
            logger.warning("检索器未初始化，返回空结果")
            return self._empty_result()
        
        try:
            # 过滤条件
            filters = {"doc_type": "report"}
            if stock_code:
                filters["stock_code"] = stock_code
            
            # 检索
            results = self.retriever.retrieve(
                query=query,
                top_k=5,
                filters=filters
            )
            
            if not results:
                logger.info(f"未找到相关研报: {query}")
                return self._empty_result()
            
            # LLM分析
            analysis_result = self._analyze_reports(query, results)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"研报检索失败: {e}")
            return {"error": str(e), **self._empty_result()}
    
    def _analyze_reports(self, query: str, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        使用LLM分析研报内容
        
        Args:
            query: 查询文本
            reports: 检索到的研报列表
            
        Returns:
            分析结果
        """
        # 格式化研报内容
        reports_text = self._format_reports(reports)
        
        prompt = f"""
请分析以下券商研报，提取关键投资信息：

【查询】
{query}

【研报内容】
{reports_text}

请按JSON格式输出分析结果，包含：summary, core_views, ratings, risks, opportunities, sources, confidence。
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
                    "summary": response[:300],
                    "core_views": ["详见研报内容"],
                    "ratings": {"buy": 0, "hold": 0, "sell": 0},
                    "risks": [],
                    "opportunities": [],
                    "sources": [],
                    "confidence": 0.5
                }
            
            # 添加来源信息
            result["sources"] = self._extract_sources(reports)
            result["retrieved_reports"] = len(reports)
            
            return result
            
        except Exception as e:
            logger.error(f"分析研报失败: {e}")
            return {"error": str(e), **self._empty_result()}
    
    def _format_reports(self, reports: List[Dict[str, Any]]) -> str:
        """格式化研报内容"""
        formatted = []
        for i, report in enumerate(reports, 1):
            metadata = report.get("metadata", {})
            content = report.get("content", "")
            score = report.get("score", 0)
            
            formatted.append(
                f"【研报{i}】\n"
                f"标题: {metadata.get('title', 'N/A')}\n"
                f"来源: {metadata.get('source', 'N/A')}\n"
                f"日期: {metadata.get('date', 'N/A')}\n"
                f"评级: {metadata.get('rating', 'N/A')}\n"
                f"目标价: {metadata.get('target_price', 'N/A')}\n"
                f"内容: {content[:500]}...\n"
                f"相关度: {score:.2f}\n"
            )
        
        return "\n".join(formatted)
    
    def _extract_sources(self, reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取来源信息（包含完整研报内容）"""
        sources = []
        for report in reports:
            metadata = report.get("metadata", {})
            sources.append({
                "institution": metadata.get("source", "未知"),
                "source": metadata.get("source", "未知"),  # 兼容两种字段名
                "date": metadata.get("date", "未知"),
                "rating": metadata.get("rating", "未知"),
                "target_price": metadata.get("target_price"),
                "title": metadata.get("title", ""),
                "doc_id": report.get("doc_id"),
                "content": report.get("content", ""),  # 完整研报内容
                "author": metadata.get("author", "")
            })
        return sources
    
    def _empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            "summary": "暂无相关研报数据",
            "core_views": [],
            "ratings": {"buy": 0, "hold": 0, "sell": 0, "avg_target_price": None},
            "risks": [],
            "opportunities": [],
            "sources": [],
            "confidence": 0.0
        }
    
    def search_reports(
        self,
        query: str,
        stock_code: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        直接搜索研报（不经过LLM分析）
        
        Args:
            query: 查询文本
            stock_code: 股票代码
            top_k: 返回数量
            
        Returns:
            研报列表
        """
        if not self.retriever:
            return []
        
        filters = {"doc_type": "report"}
        if stock_code:
            filters["stock_code"] = stock_code
        
        return self.retriever.retrieve(query=query, top_k=top_k, filters=filters)
