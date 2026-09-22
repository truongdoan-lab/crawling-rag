from common.config import Settings
from preparation_pipeline.embedder import BgeM3Embedder
from preparation_pipeline.vector_store import VectorStore
from chatbot_pipeline.generator import GeminiGenerator
from chatbot_pipeline.reranker import CohereReranker
from chatbot_pipeline.retriever import Retriever
from chatbot_pipeline.semantic_cache import ChatSemanticCache

NO_INFO_ANSWER = "Can not find relevant information in the provided data."


class ChatPipeline:
    def __init__(self, settings: Settings):
        embedder = BgeM3Embedder(settings.embedding_model, settings.embedding_device)
        store = VectorStore(settings.qdrant_url, settings.qdrant_collection)

        self._cache = ChatSemanticCache(
            settings.redis_url,
            embedder,
            distance_threshold=settings.semantic_cache_threshold,
            ttl_seconds=settings.semantic_cache_ttl_seconds,
        )
        self._retriever = Retriever(embedder, store)
        self._reranker = CohereReranker(settings.cohere_api_key, settings.cohere_rerank_model)
        self._generator = GeminiGenerator(settings.gemini_api_key, settings.gemini_model)

    def answer(self, question: str, top_n: int = 3) -> dict:
        cached = self._cache.check(question)
        if cached is not None:
            return {"answer": cached, "from_cache": True, "sources": [], "context_texts": []}

        candidates = self._retriever.retrieve(question, limit=20)
        if not candidates:
            return {"answer": NO_INFO_ANSWER, "from_cache": False, "sources": [], "context_texts": []}

        top_chunks = self._reranker.rerank(question, candidates, top_n=top_n)
        answer = self._generator.generate(question, top_chunks)

        self._cache.store(question, answer)

        sources = [{"title": c.get("title"), "url": c.get("url")} for c in top_chunks]
        
        context_texts = [c["text"] for c in top_chunks]
        return {"answer": answer, "from_cache": False, "sources": sources, "context_texts": context_texts}
