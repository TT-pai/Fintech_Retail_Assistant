"""
检索器模块
支持基础检索和混合检索
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
import re


class RAGRetriever:
    """RAG检索器"""
    
    def __init__(
        self,
        vector_store,
        reranker=None,
        top_k: int = 5
    ):
        self.vector_store = vector_store
        self.reranker = reranker
        self.top_k = top_k
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回数量
            filters: 过滤条件，如 {"doc_type": "report", "stock_code": "600519"}
            rerank: 是否重排序
            
        Returns:
            检索结果列表
        """
        k = top_k or self.top_k
        
        # 向量检索
        results = self.vector_store.similarity_search(
            query=query,
            k=k * 2,  # 多取一些用于重排序
            filter=filters
        )
        
        if not results:
            return []
        
        # 重排序
        if rerank and self.reranker:
            results = self.reranker.rerank(query, results, top_k=k)
        else:
            results = results[:k]
        
        return results
    
    def retrieve_with_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        检索并返回上下文字符串
        
        Args:
            query: 查询文本
            top_k: 返回数量
            filters: 过滤条件
            
        Returns:
            (上下文字符串, 检索结果列表)
        """
        results = self.retrieve(query, top_k, filters)
        
        if not results:
            return "", []
        
        # 构建上下文
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result.get("metadata", {}).get("source", "未知来源")
            content = result.get("content", "")
            context_parts.append(f"[{i}] 来源: {source}\n{content}")
        
        context = "\n\n".join(context_parts)
        
        return context, results
    
    def get_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        提取来源信息用于引用
        
        Args:
            results: 检索结果
            
        Returns:
            来源信息列表
        """
        sources = []
        for result in results:
            metadata = result.get("metadata", {})
            source = {
                "doc_id": result.get("doc_id"),
                "source": metadata.get("source", "未知来源"),
                "title": metadata.get("title", ""),
                "date": metadata.get("date", ""),
                "score": result.get("score", 0)
            }
            sources.append(source)
        return sources


class HybridRetriever(RAGRetriever):
    """
    混合检索器
    结合向量检索和关键词检索
    """
    
    def __init__(
        self,
        vector_store,
        reranker=None,
        top_k: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ):
        super().__init__(vector_store, reranker, top_k)
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        
        self._keyword_index: Dict[str, List[str]] = {}
        self._doc_contents: Dict[str, str] = {}
    
    def build_keyword_index(self, documents: List) -> None:
        """构建关键词索引"""
        import jieba
        
        self._keyword_index.clear()
        self._doc_contents.clear()
        
        for doc in documents:
            self._doc_contents[doc.doc_id] = doc.content
            
            words = jieba.lcut(doc.content)
            for word in words:
                if len(word) > 1:
                    if word not in self._keyword_index:
                        self._keyword_index[word] = []
                    self._keyword_index[word].append(doc.doc_id)
        
        logger.info(f"关键词索引构建完成，词汇量: {len(self._keyword_index)}")
    
    def _keyword_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        关键词检索（BM25风格简化版）
        
        Args:
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            检索结果
        """
        import jieba
        from collections import Counter
        
        # 分词
        query_words = jieba.lcut(query)
        
        # 统计文档得分
        doc_scores: Counter = Counter()
        for word in query_words:
            if word in self._keyword_index:
                for doc_id in self._keyword_index[word]:
                    doc_scores[doc_id] += 1
        
        # 排序并返回
        results = []
        for doc_id, score in doc_scores.most_common(top_k):
            if doc_id in self._doc_contents:
                results.append({
                    "doc_id": doc_id,
                    "content": self._doc_contents[doc_id],
                    "score": score / len(query_words),  # 归一化
                    "metadata": {}
                })
        
        return results
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """
        混合检索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            filters: 过滤条件
            rerank: 是否重排序
            
        Returns:
            检索结果列表
        """
        k = top_k or self.top_k
        
        # 1. 向量检索
        vector_results = self.vector_store.similarity_search(
            query=query,
            k=k * 2,
            filter=filters
        )
        
        # 2. 关键词检索
        keyword_results = self._keyword_search(query, k * 2)
        
        # 3. RRF融合
        merged = self._rrf_fusion(vector_results, keyword_results, k * 2)
        
        # 4. 重排序
        if rerank and self.reranker:
            merged = self.reranker.rerank(query, merged, top_k=k)
        else:
            merged = merged[:k]
        
        return merged
    
    def _rrf_fusion(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        top_k: int,
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        RRF (Reciprocal Rank Fusion) 融合算法
        
        Args:
            vector_results: 向量检索结果
            keyword_results: 关键词检索结果
            top_k: 返回数量
            k: RRF常数
            
        Returns:
            融合后的结果
        """
        from collections import defaultdict
        
        # 计算RRF分数
        scores = defaultdict(float)
        doc_map = {}
        
        # 向量检索贡献
        for rank, result in enumerate(vector_results):
            doc_id = result["doc_id"]
            scores[doc_id] += self.vector_weight / (k + rank + 1)
            doc_map[doc_id] = result
        
        # 关键词检索贡献
        for rank, result in enumerate(keyword_results):
            doc_id = result["doc_id"]
            scores[doc_id] += self.keyword_weight / (k + rank + 1)
            if doc_id not in doc_map:
                doc_map[doc_id] = result
        
        # 排序
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # 构建结果
        results = []
        for doc_id, score in sorted_docs:
            result = doc_map[doc_id].copy()
            result["score"] = score
            results.append(result)
        
        return results


class GraphRAGRetriever(RAGRetriever):
    """
    GraphRAG检索器
    结合知识图谱和向量检索
    """
    
    def __init__(
        self,
        vector_store,
        knowledge_graph,
        reranker=None,
        top_k: int = 5
    ):
        super().__init__(vector_store, reranker, top_k)
        self.knowledge_graph = knowledge_graph
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """
        GraphRAG检索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            filters: 过滤条件
            rerank: 是否重排序
            
        Returns:
            检索结果列表
        """
        k = top_k or self.top_k
        
        # 1. 实体识别（简化版，使用关键词匹配）
        entities = self._extract_entities(query)
        
        # 2. 知识图谱查询
        graph_context = []
        if entities and self.knowledge_graph:
            graph_context = self.knowledge_graph.query_entities(entities)
        
        # 3. 向量检索
        vector_results = self.vector_store.similarity_search(
            query=query,
            k=k * 2,
            filter=filters
        )
        
        # 4. 融合结果
        merged = self._merge_results(graph_context, vector_results, k * 2)
        
        # 5. 重排序
        if rerank and self.reranker:
            merged = self.reranker.rerank(query, merged, top_k=k)
        else:
            merged = merged[:k]
        
        return merged
    
    def _extract_entities(self, query: str) -> List[str]:
        """
        从查询中提取实体（简化版）
        
        Args:
            query: 查询文本
            
        Returns:
            实体列表
        """
        # 这里可以接入NER模型，简化起见使用正则
        import re
        
        entities = []
        
        # 股票代码匹配
        stock_codes = re.findall(r'\b(0\d{5}|6\d{5}|3\d{5})\b', query)
        entities.extend(stock_codes)
        
        # 常见公司名（茅台、五粮液等）
        common_companies = [
            "茅台", "五粮液", "宁德时代", "比亚迪", "腾讯", "阿里",
            "平安", "招商", "美的", "格力", "恒瑞", "药明"
        ]
        for company in common_companies:
            if company in query:
                entities.append(company)
        
        return entities
    
    def _merge_results(
        self,
        graph_context: List[Dict],
        vector_results: List[Dict],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """融合图谱和向量结果"""
        # 简单合并，去重
        seen_ids = set()
        merged = []
        
        for result in graph_context:
            doc_id = result.get("doc_id", f"graph_{len(merged)}")
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                merged.append(result)
        
        for result in vector_results:
            doc_id = result.get("doc_id")
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                merged.append(result)
        
        return merged[:top_k]
