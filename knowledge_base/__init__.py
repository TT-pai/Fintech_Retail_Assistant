"""
知识库初始化脚本
用于加载知识库数据到向量存储
"""
import os
import json
from typing import List, Dict, Any
from loguru import logger

# 延迟导入，支持精简依赖环境
from rag import (
    EMBEDDING_AVAILABLE, 
    VECTOR_STORE_AVAILABLE,
    KNOWLEDGE_GRAPH_AVAILABLE
)


class KnowledgeBaseManager:
    """知识库管理器"""
    
    def __init__(
        self,
        knowledge_base_path: str = None,
        vector_store=None,
        embedding_engine=None
    ):
        """
        初始化知识库管理器
        
        Args:
            knowledge_base_path: 知识库数据路径
            vector_store: 向量存储
            embedding_engine: 嵌入引擎
        """
        self.knowledge_base_path = knowledge_base_path or os.path.dirname(__file__)
        self.vector_store = vector_store
        self.embedding_engine = embedding_engine
        self.knowledge_graph = None
        self._use_mock = False
    
    def initialize(self, use_mock_embedding: bool = False) -> None:
        """
        初始化知识库
        
        Args:
            use_mock_embedding: 是否使用Mock嵌入引擎
        """
        self._use_mock = use_mock_embedding
        
        # 初始化嵌入引擎
        if not self.embedding_engine:
            if use_mock_embedding or not EMBEDDING_AVAILABLE:
                from rag.embeddings import MockEmbeddingEngine
                self.embedding_engine = MockEmbeddingEngine()
                logger.info("使用 Mock 嵌入引擎")
            else:
                from rag.embeddings import get_embedding_engine
                self.embedding_engine = get_embedding_engine()
        
        # 初始化向量存储
        if not self.vector_store:
            if use_mock_embedding or not VECTOR_STORE_AVAILABLE:
                from rag.vector_store import MockVectorStore
                self.vector_store = MockVectorStore()
                logger.info("使用 Mock 向量存储")
            else:
                from rag.vector_store import VectorStore
                self.vector_store = VectorStore(embedding_engine=self.embedding_engine)
        
        # 加载知识库数据
        self.load_all_knowledge()
        
        # 初始化知识图谱
        self.init_knowledge_graph()
        
        logger.info("知识库初始化完成")
    
    def load_all_knowledge(self) -> int:
        """
        加载所有知识库数据
        
        Returns:
            加载的文档数量
        """
        total_docs = 0
        
        # 加载各类知识库
        knowledge_files = {
            "reports.json": "研报库",
            "financials.json": "财报库",
            "news.json": "新闻库",
            "industry.json": "行业知识库",
            "regulations.json": "监管法规库"
        }
        
        for filename, name in knowledge_files.items():
            docs = self._load_knowledge_file(filename)
            if docs:
                self.vector_store.add_documents(docs)
                total_docs += len(docs)
                logger.info(f"{name}加载完成，文档数: {len(docs)}")
        
        return total_docs
    
    def _load_knowledge_file(self, filename: str) -> List:
        """
        加载单个知识库文件
        
        Args:
            filename: 文件名
            
        Returns:
            文档列表
        """
        from rag.vector_store import Document
        
        filepath = os.path.join(self.knowledge_base_path, filename)
        
        if not os.path.exists(filepath):
            logger.warning(f"知识库文件不存在: {filepath}")
            return []
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            documents = []
            for item in data:
                # 过滤None值，ChromaDB不支持None
                metadata = {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "source": item.get("source"),
                    "date": item.get("date"),
                    "stock_code": item.get("stock_code"),
                    "stock_name": item.get("stock_name"),
                    "doc_type": item.get("doc_type"),
                    "rating": item.get("rating"),
                    "target_price": item.get("target_price"),
                    "sentiment": item.get("sentiment")
                }
                # 移除None值
                metadata = {k: str(v) if v is not None else "" for k, v in metadata.items()}
                
                doc = Document(
                    content=item.get("content", ""),
                    metadata=metadata,
                    doc_id=item.get("id")
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"加载知识库文件失败: {filepath}, {e}")
            return []
    
    def init_knowledge_graph(self) -> None:
        """初始化知识图谱"""
        try:
            from rag.knowledge_graph import KnowledgeGraph, build_default_knowledge_graph
            
            graph_path = os.path.join(
                os.path.dirname(self.knowledge_base_path), 
                "data", 
                "knowledge_graph"
            )
            
            kg = KnowledgeGraph(storage_path=graph_path)
            
            # 如果图谱为空，构建默认图谱
            if kg.graph.number_of_nodes() == 0:
                kg = build_default_knowledge_graph()
            
            self.knowledge_graph = kg
            logger.info(f"知识图谱初始化完成，节点数: {kg.graph.number_of_nodes()}")
        except Exception as e:
            logger.warning(f"知识图谱初始化失败: {e}")
            self.knowledge_graph = None
    
    def search(self, query: str, top_k: int = 5, doc_type: str = None) -> List[Dict[str, Any]]:
        """
        搜索知识库
        
        Args:
            query: 查询文本
            top_k: 返回数量
            doc_type: 文档类型过滤
            
        Returns:
            搜索结果
        """
        filters = None
        if doc_type:
            filters = {"doc_type": doc_type}
        
        return self.vector_store.similarity_search(query, top_k, filters)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        stats = {
            "vector_store": {
                "total_documents": self.vector_store.get_document_count() if self.vector_store else 0
            }
        }
        
        if self.knowledge_graph:
            stats["knowledge_graph"] = self.knowledge_graph.get_graph_stats()
        
        return stats


def init_knowledge_base(use_mock: bool = False) -> KnowledgeBaseManager:
    """
    初始化知识库（便捷函数）
    
    Args:
        use_mock: 是否使用Mock引擎
        
    Returns:
        知识库管理器
    """
    manager = KnowledgeBaseManager()
    manager.initialize(use_mock_embedding=use_mock)
    return manager


if __name__ == "__main__":
    # 初始化知识库
    manager = init_knowledge_base(use_mock=False)
    
    # 打印统计信息
    print("\n知识库统计信息:")
    stats = manager.get_stats()
    print(f"向量存储文档数: {stats['vector_store']['total_documents']}")
    if 'knowledge_graph' in stats:
        print(f"知识图谱节点数: {stats['knowledge_graph']['total_nodes']}")
        print(f"知识图谱边数: {stats['knowledge_graph']['total_edges']}")
    
    # 测试搜索
    print("\n测试搜索:")
    results = manager.search("茅台最新研报观点", top_k=3)
    for i, result in enumerate(results, 1):
        print(f"\n[{i}] {result['metadata'].get('title', 'N/A')}")
        print(f"来源: {result['metadata'].get('source', 'N/A')}")
        print(f"内容: {result['content'][:100]}...")
