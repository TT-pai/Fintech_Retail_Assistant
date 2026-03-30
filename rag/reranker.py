"""
重排序模块
支持时效性加权、相关性调整
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger


class ReRanker:
    """重排序器"""
    
    def __init__(
        self,
        freshness_weight: float = 0.3,
        relevance_weight: float = 0.7,
        recency_days: int = 30
    ):
        """
        初始化重排序器
        
        Args:
            freshness_weight: 时效性权重
            relevance_weight: 相关性权重
            recency_days: 时效衰减天数
        """
        self.freshness_weight = freshness_weight
        self.relevance_weight = relevance_weight
        self.recency_days = recency_days
    
    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        重排序检索结果
        
        Args:
            query: 查询文本
            results: 原始结果
            top_k: 返回数量
            
        Returns:
            重排序后的结果
        """
        if not results:
            return []
        
        # 计算综合分数
        scored_results = []
        for result in results:
            # 原始相关性分数
            relevance_score = result.get("score", 0.5)
            
            # 时效性分数
            freshness_score = self._calculate_freshness(result)
            
            # 综合分数
            final_score = (
                relevance_score * self.relevance_weight +
                freshness_score * self.freshness_weight
            )
            
            result_copy = result.copy()
            result_copy["final_score"] = final_score
            result_copy["freshness_score"] = freshness_score
            result_copy["relevance_score"] = relevance_score
            scored_results.append(result_copy)
        
        # 按综合分数排序
        scored_results.sort(key=lambda x: x["final_score"], reverse=True)
        
        return scored_results[:top_k]
    
    def _calculate_freshness(self, result: Dict[str, Any]) -> float:
        """
        计算时效性分数
        
        Args:
            result: 检索结果
            
        Returns:
            时效性分数 [0, 1]
        """
        metadata = result.get("metadata", {})
        date_str = metadata.get("date") or metadata.get("publish_time")
        
        if not date_str:
            return 0.5  # 无日期信息，给中等分数
        
        try:
            # 解析日期
            doc_date = self._parse_date(date_str)
            if not doc_date:
                return 0.5
            
            # 计算天数差
            days_old = (datetime.now() - doc_date).days
            
            # 指数衰减
            freshness = 1.0 / (1 + days_old / self.recency_days)
            
            return max(0.1, min(1.0, freshness))
            
        except Exception as e:
            logger.debug(f"解析日期失败: {date_str}, {e}")
            return 0.5
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        解析日期字符串
        
        Args:
            date_str: 日期字符串
            
        Returns:
            datetime对象
        """
        if not date_str:
            return None
        
        # 尝试多种格式
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str[:len(datetime.now().strftime(fmt))], fmt)
            except ValueError:
                continue
        
        return None


class CrossEncoderReRanker:
    """
    基于Cross-Encoder的重排序器
    使用预训练模型进行精确重排序
    """
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        device: str = "cpu"
    ):
        """
        初始化Cross-Encoder重排序器
        
        Args:
            model_name: 模型名称
            device: 运行设备
        """
        self.model_name = model_name
        self.device = device
        self._model = None
        logger.info(f"初始化Cross-Encoder重排序器: {model_name}")
    
    @property
    def model(self):
        """懒加载模型"""
        if self._model is None:
            self._load_model()
        return self._model
    
    def _load_model(self):
        """加载模型"""
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.model_name, device=self.device)
            logger.info("Cross-Encoder模型加载成功")
        except Exception as e:
            logger.error(f"加载Cross-Encoder模型失败: {e}")
            raise
    
    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        使用Cross-Encoder重排序
        
        Args:
            query: 查询文本
            results: 原始结果
            top_k: 返回数量
            
        Returns:
            重排序后的结果
        """
        if not results:
            return []
        
        try:
            # 构建查询-文档对
            pairs = [(query, result.get("content", "")) for result in results]
            
            # 计算分数
            scores = self.model.predict(pairs)
            
            # 排序
            scored_results = []
            for i, result in enumerate(results):
                result_copy = result.copy()
                result_copy["rerank_score"] = float(scores[i])
                scored_results.append(result_copy)
            
            scored_results.sort(key=lambda x: x["rerank_score"], reverse=True)
            
            return scored_results[:top_k]
            
        except Exception as e:
            logger.error(f"Cross-Encoder重排序失败: {e}")
            return results[:top_k]


class DiversityReRanker:
    """
    多样性重排序器
    确保结果具有多样性，避免过于相似的文档
    """
    
    def __init__(
        self,
        diversity_threshold: float = 0.8,
        embedding_engine = None
    ):
        """
        初始化多样性重排序器
        
        Args:
            diversity_threshold: 多样性阈值
            embedding_engine: 嵌入引擎
        """
        self.diversity_threshold = diversity_threshold
        self.embedding_engine = embedding_engine
    
    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        多样性重排序
        
        Args:
            query: 查询文本
            results: 原始结果
            top_k: 返回数量
            
        Returns:
            重排序后的结果
        """
        if not results or len(results) <= top_k:
            return results
        
        if not self.embedding_engine:
            return results[:top_k]
        
        try:
            # 计算文档向量
            contents = [r.get("content", "") for r in results]
            embeddings = self.embedding_engine.embed_documents(contents)
            
            # MMR风格选择
            selected_indices = []
            selected_embeddings = []
            
            # 第一个选最高分
            selected_indices.append(0)
            selected_embeddings.append(embeddings[0])
            
            # 逐步选择
            while len(selected_indices) < top_k and len(selected_indices) < len(results):
                best_idx = -1
                best_score = -1
                
                for i in range(len(results)):
                    if i in selected_indices:
                        continue
                    
                    # 计算与已选文档的最大相似度
                    max_sim = max(
                        self.embedding_engine.similarity(embeddings[i], se)
                        for se in selected_embeddings
                    )
                    
                    # 多样性分数 = 相关性分数 * (1 - 最大相似度)
                    relevance = results[i].get("score", 0.5)
                    diversity_score = relevance * (1 - max_sim)
                    
                    if diversity_score > best_score:
                        best_score = diversity_score
                        best_idx = i
                
                if best_idx >= 0:
                    selected_indices.append(best_idx)
                    selected_embeddings.append(embeddings[best_idx])
            
            return [results[i] for i in selected_indices]
            
        except Exception as e:
            logger.error(f"多样性重排序失败: {e}")
            return results[:top_k]
