"""
向量嵌入引擎
支持多种中文Embedding模型
"""
from typing import List, Optional
from loguru import logger
import os


class EmbeddingEngine:
    """向量嵌入引擎"""
    
    def __init__(
        self,
        model_name: str = "shibing624/text2vec-base-chinese",
        device: str = "cpu",
        cache_dir: Optional[str] = None
    ):
        """
        初始化嵌入引擎
        
        Args:
            model_name: 模型名称，支持:
                - shibing624/text2vec-base-chinese (默认，轻量级)
                - BAAI/bge-small-zh-v1.5 (更高质量)
                - BAAI/bge-base-zh-v1.5 (平衡)
            device: 运行设备 cpu/cuda
            cache_dir: 模型缓存目录
        """
        self.model_name = model_name
        self.device = device
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), "..", "data", "models")
        self._model = None
        self._dimension = None
        
    @property
    def model(self):
        """懒加载模型"""
        if self._model is None:
            self._load_model()
        return self._model
    
    def _load_model(self):
        """加载模型"""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"加载Embedding模型: {self.model_name}")
            self._model = SentenceTransformer(
                self.model_name,
                cache_folder=self.cache_dir,
                device=self.device
            )
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"模型加载成功，向量维度: {self._dimension}")
            
        except Exception as e:
            logger.error(f"加载Embedding模型失败: {e}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        对文档列表进行向量化
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        if not texts:
            return []
        
        try:
            embeddings = self.model.encode(
                texts,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True  # L2归一化，便于余弦相似度计算
            )
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"文档向量化失败: {e}")
            raise
    
    def embed_query(self, query: str) -> List[float]:
        """
        对查询进行向量化
        
        Args:
            query: 查询文本
            
        Returns:
            查询向量
        """
        try:
            embedding = self.model.encode(
                query,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"查询向量化失败: {e}")
            raise
    
    @property
    def dimension(self) -> int:
        """获取向量维度"""
        if self._dimension is None:
            self._load_model()
        return self._dimension
    
    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        由于向量已归一化，直接点积即为余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            相似度分数 [0, 1]
        """
        import numpy as np
        return float(np.dot(vec1, vec2))


class MockEmbeddingEngine:
    """
    Mock嵌入引擎，用于测试或无GPU环境
    使用简单的哈希方法生成伪向量
    """
    
    def __init__(self, dimension: int = 384):
        self._dimension = dimension
        logger.warning("使用MockEmbeddingEngine，仅用于测试环境")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(text) for text in texts]
    
    def embed_query(self, query: str) -> List[float]:
        import hashlib
        import numpy as np
        
        # 使用MD5哈希生成确定性向量
        hash_bytes = hashlib.md5(query.encode()).digest()
        np.random.seed(int.from_bytes(hash_bytes[:4], 'big'))
        vec = np.random.randn(self._dimension)
        vec = vec / np.linalg.norm(vec)  # 归一化
        return vec.tolist()
    
    @property
    def dimension(self) -> int:
        return self._dimension


def get_embedding_engine(use_mock: bool = False, **kwargs) -> EmbeddingEngine:
    """
    获取嵌入引擎实例
    
    Args:
        use_mock: 是否使用Mock引擎
        **kwargs: 传递给EmbeddingEngine的参数
        
    Returns:
        嵌入引擎实例
    """
    if use_mock:
        return MockEmbeddingEngine()
    return EmbeddingEngine(**kwargs)
