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
