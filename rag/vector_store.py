"""
向量存储模块
基于ChromaDB实现向量存储与检索
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import json
from loguru import logger


class Document:
    """文档对象"""
    
    def __init__(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ):
        self.content = content
        self.metadata = metadata or {}
        self.doc_id = doc_id or self._generate_id()
        
    def _generate_id(self) -> str:
        """生成文档ID"""
        import hashlib
        content_hash = hashlib.md5(self.content.encode()).hexdigest()[:12]
        return f"doc_{content_hash}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        return cls(
            content=data["content"],
            metadata=data.get("metadata", {}),
            doc_id=data.get("doc_id")
        )


class VectorStore:
    """向量存储"""
    
    def __init__(
        self,
        collection_name: str = "fintech_knowledge",
        persist_directory: Optional[str] = None,
        embedding_engine = None
    ):
        """
        初始化向量存储
        
        Args:
            collection_name: 集合名称
            persist_directory: 持久化目录
            embedding_engine: 嵌入引擎
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or os.path.join(
            os.path.dirname(__file__), "..", "data", "chroma"
        )
        self.embedding_engine = embedding_engine
        self._client = None
        self._collection = None
        
        # 延迟初始化嵌入引擎
        if self.embedding_engine is None:
            from rag.embeddings import get_embedding_engine
            self.embedding_engine = get_embedding_engine(use_mock=True)
        
    @property
    def client(self):
        """懒加载Chroma客户端"""
        if self._client is None:
            self._init_client()
        return self._client
    
    @property
    def collection(self):
        """懒加载集合"""
        if self._collection is None:
            self._init_client()
        return self._collection
    
    def _init_client(self):
        """初始化Chroma客户端"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # 确保目录存在
            os.makedirs(self.persist_directory, exist_ok=True)
            
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # 获取或创建集合
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"向量存储初始化成功: {self.collection_name}, 文档数: {self._collection.count()}")
            
        except ImportError:
            raise ImportError(
                "chromadb 未安装。请安装: pip install chromadb\n"
                "或使用 MockVectorStore 替代"
            )
        except Exception as e:
            logger.error(f"向量存储初始化失败: {e}")
            raise
    
    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100
    ) -> int:
        """
        批量添加文档
        
        Args:
            documents: 文档列表
            batch_size: 批量大小
            
        Returns:
            添加的文档数量
        """
        if not documents:
            return 0
        
        total_added = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # 生成向量
            contents = [doc.content for doc in batch]
            embeddings = self.embedding_engine.embed_documents(contents)
            
            # 添加到集合
            self.collection.add(
                ids=[doc.doc_id for doc in batch],
                documents=contents,
                embeddings=embeddings,
                metadatas=[doc.metadata for doc in batch]
            )
            
            total_added += len(batch)
            logger.info(f"已添加 {total_added}/{len(documents)} 个文档")
        
        return total_added
    
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        添加文本列表
        
        Args:
            texts: 文本列表
            metadatas: 元数据列表
            
        Returns:
            文档ID列表
        """
        documents = [
            Document(
                content=text,
                metadata=metadatas[i] if metadatas else {}
            )
            for i, text in enumerate(texts)
        ]
        self.add_documents(documents)
        return [doc.doc_id for doc in documents]
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        相似度搜索
        
        Args:
            query: 查询文本
            k: 返回数量
            filter: 元数据过滤条件
            
        Returns:
            搜索结果列表
        """
        # 向量化查询
        query_embedding = self.embedding_engine.embed_query(query)
        
        # 搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter
        )
        
        # 格式化结果
        documents = []
        for i in range(len(results["ids"][0])):
            doc = {
                "doc_id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "score": 1 - results["distances"][0][i] if results["distances"] else 1.0
            }
            documents.append(doc)
        
        return documents
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """
        相似度搜索（带分数）
        
        Returns:
            (Document, score) 元组列表
        """
        results = self.similarity_search(query, k, filter)
        return [(Document.from_dict(r), r["score"]) for r in results]
    
    def delete_documents(self, doc_ids: List[str]) -> None:
        """删除文档"""
        self.collection.delete(ids=doc_ids)
        logger.info(f"已删除 {len(doc_ids)} 个文档")
    
    def delete_by_filter(self, filter: Dict[str, Any]) -> None:
        """按条件删除文档"""
        # 先查询符合条件的文档
        results = self.collection.get(where=filter)
        if results["ids"]:
            self.delete_documents(results["ids"])
    
    def get_document_count(self) -> int:
        """获取文档数量"""
        return self.collection.count()
    
    def clear(self) -> None:
        """清空集合"""
        # 删除并重建集合
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"集合 {self.collection_name} 已清空")


class MockVectorStore:
    """
    Mock向量存储，用于测试
    使用内存字典存储
    """
    
    def __init__(self):
        self._documents: Dict[str, Document] = {}
        self._embeddings: Dict[str, List[float]] = {}
        logger.warning("使用MockVectorStore，仅用于测试环境")
    
    def add_documents(self, documents: List[Document]) -> int:
        for doc in documents:
            self._documents[doc.doc_id] = doc
        return len(documents)
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict]] = None) -> List[str]:
        doc_ids = []
        for i, text in enumerate(texts):
            doc = Document(content=text, metadata=metadatas[i] if metadatas else {})
            self._documents[doc.doc_id] = doc
            doc_ids.append(doc.doc_id)
        return doc_ids
    
    def similarity_search(self, query: str, k: int = 5, filter: Optional[Dict] = None) -> List[Dict]:
        # 应用过滤条件
        filtered_docs = []
        for doc_id, doc in self._documents.items():
            # 检查是否满足过滤条件
            if filter:
                match = True
                for key, value in filter.items():
                    if doc.metadata.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            filtered_docs.append((doc_id, doc))
        
        # 返回前k个
        results = []
        for doc_id, doc in filtered_docs[:k]:
            results.append({
                "doc_id": doc_id,
                "content": doc.content,
                "metadata": doc.metadata,
                "score": 0.8
            })
        return results
    
    def get_document_count(self) -> int:
        return len(self._documents)
    
    def clear(self) -> None:
        self._documents.clear()
