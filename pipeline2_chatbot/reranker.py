"""
Rerank bằng Cohere Rerank API - lọc lại top candidates từ hybrid search,
chỉ giữ 1-3 kết quả liên quan nhất để đưa vào prompt.

Cập nhật đã nêu trong review: dùng bản rerank-v3.5 (hoặc rerank-v4 khi cần
chất lượng cao nhất) thay vì mặc định nghĩ tới bản v3.0 cũ. Nếu muốn tự host
toàn bộ (giống hướng BGE-M3), có thể thay client này bằng bge-reranker-v2-m3
mà vẫn giữ nguyên interface .rerank(query, candidates, top_n).
"""
import cohere


class CohereReranker:
    def __init__(self, api_key: str, model: str = "rerank-v3.5"):
        self._client = cohere.ClientV2(api_key=api_key)
        self._model = model

    def rerank(self, query: str, candidates: list[dict], top_n: int = 3) -> list[dict]:
        if not candidates:
            return []
        docs = [c["text"] for c in candidates]
        response = self._client.rerank(
            model=self._model, query=query, documents=docs, top_n=min(top_n, len(docs))
        )
        return [
            {**candidates[r.index], "rerank_score": r.relevance_score} for r in response.results
        ]
