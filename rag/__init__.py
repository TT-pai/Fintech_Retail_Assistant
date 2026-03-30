"""
RAG模块 - 检索增强生成
包含向量嵌入、向量存储、检索器、重排序器、知识图谱
"""

# 条件导入，支持精简依赖环境
try:
    from rag.embeddings import EmbeddingEngine, MockEmbeddingEngine, get_embedding_engine
    EMBEDDING_AVAILABLE = True
except ImportError:
    EmbeddingEngine = None
    MockEmbeddingEngine = None
    def get_embedding_engine(use_mock=False, **kwargs):
        raise ImportError("Embedding engine not available. Install sentence-transformers.")
    EMBEDDING_AVAILABLE = False

try:
    from rag.vector_store import VectorStore, Document, MockVectorStore
    VECTOR_STORE_AVAILABLE = True
except ImportError:
    VectorStore = None
    Document = None
    MockVectorStore = None
    VECTOR_STORE_AVAILABLE = False

try:
    from rag.retriever import RAGRetriever, HybridRetriever
    RETRIEVER_AVAILABLE = True
except ImportError:
    RAGRetriever = None
    HybridRetriever = None
    RETRIEVER_AVAILABLE = False

try:
    from rag.reranker import ReRanker
    RERANKER_AVAILABLE = True
except ImportError:
    ReRanker = None
    RERANKER_AVAILABLE = False

try:
    from rag.knowledge_graph import KnowledgeGraph
    KNOWLEDGE_GRAPH_AVAILABLE = True
except ImportError:
    KnowledgeGraph = None
    KNOWLEDGE_GRAPH_AVAILABLE = False

__all__ = [
    "EmbeddingEngine",
    "MockEmbeddingEngine",
    "get_embedding_engine",
    "VectorStore",
    "Document",
    "MockVectorStore",
    "RAGRetriever",
    "HybridRetriever",
    "ReRanker",
    "KnowledgeGraph",
    "EMBEDDING_AVAILABLE",
    "VECTOR_STORE_AVAILABLE",
    "RETRIEVER_AVAILABLE",
    "RERANKER_AVAILABLE",
    "KNOWLEDGE_GRAPH_AVAILABLE",
]
