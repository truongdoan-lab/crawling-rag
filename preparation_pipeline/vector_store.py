from typing import TYPE_CHECKING

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    MatchValue,
    Prefetch,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

if TYPE_CHECKING:
    # Chỉ dùng cho type hint, không import thật lúc chạy -> vector_store.py
    # (mối quan tâm về Qdrant) không bị buộc phải cài FlagEmbedding/torch
    # (mối quan tâm về embedding) chỉ để import module này.
    from pipeline1_preparation.embedder import EmbeddingResult

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"
DENSE_DIM = 1024  # BGE-M3 xuất dense vector 1024 chiều


class VectorStore:
    def __init__(self, url: str, collection: str):
        self._client = QdrantClient(url=url)
        self._collection = collection

    def ensure_collection(self):
        if self._client.collection_exists(self._collection):
            return
        self._client.create_collection(
            collection_name=self._collection,
            vectors_config={DENSE_VECTOR_NAME: VectorParams(size=DENSE_DIM, distance=Distance.COSINE)},
            sparse_vectors_config={SPARSE_VECTOR_NAME: SparseVectorParams()},
        )

    def upsert_chunks(
        self, point_ids: list[str], embeddings: list["EmbeddingResult"], payloads: list[dict]
    ):
        points = [
            PointStruct(
                id=pid,
                vector={
                    DENSE_VECTOR_NAME: emb.dense,
                    SPARSE_VECTOR_NAME: SparseVector(
                        indices=emb.sparse_indices, values=emb.sparse_values
                    ),
                },
                payload=payload,
            )
            for pid, emb, payload in zip(point_ids, embeddings, payloads)
        ]
        self._client.upsert(collection_name=self._collection, points=points)

    def delete_by_url(self, url: str):
        """Xóa toàn bộ chunk cũ của 1 URL trước khi ghi chunk mới - dùng khi
        content_hash đổi (bài viết bị sửa nội dung), tránh để lại vector cũ."""
        self._client.delete(
            collection_name=self._collection,
            points_selector=Filter(must=[FieldCondition(key="url", match=MatchValue(value=url))]),
        )

    def hybrid_search(self, query_embedding: "EmbeddingResult", limit: int = 20) -> list[dict]:
        results = self._client.query_points(
            collection_name=self._collection,
            prefetch=[
                Prefetch(query=query_embedding.dense, using=DENSE_VECTOR_NAME, limit=limit),
                Prefetch(
                    query=SparseVector(
                        indices=query_embedding.sparse_indices, values=query_embedding.sparse_values
                    ),
                    using=SPARSE_VECTOR_NAME,
                    limit=limit,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=limit,
            with_payload=True,
        )
        return [{"id": p.id, "score": p.score, **p.payload} for p in results.points]
