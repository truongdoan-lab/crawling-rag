"""
Hybrid search: dùng chung BgeM3Embedder + VectorStore của Pipeline 1.
Qdrant tự fusion dense + sparse bằng RRF ngay trong Query API - đây chính
là chỗ hưởng lợi từ việc dùng BGE-M3 cho cả dense lẫn sparse (đã nêu trong
review): không cần train/duy trì thêm một hệ BM25 riêng cho chatbot.
"""
from pipeline1_preparation.embedder import BgeM3Embedder
from pipeline1_preparation.vector_store import VectorStore


class Retriever:
    def __init__(self, embedder: BgeM3Embedder, store: VectorStore):
        self._embedder = embedder
        self._store = store

    def retrieve(self, query: str, limit: int = 20) -> list[dict]:
        query_embedding = self._embedder.embed_one(query)
        return self._store.hybrid_search(query_embedding, limit=limit)
