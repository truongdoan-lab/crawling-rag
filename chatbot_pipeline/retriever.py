from preparation_pipeline.embedder import BgeM3Embedder
from preparation_pipeline.vector_store import VectorStore


class Retriever:
    def __init__(self, embedder: BgeM3Embedder, store: VectorStore):
        self._embedder = embedder
        self._store = store

    def retrieve(self, query: str, limit: int = 20) -> list[dict]:
        query_embedding = self._embedder.embed_one(query)
        return self._store.hybrid_search(query_embedding, limit=limit)
