"""
Ghép toàn bộ Pipeline 2 lại: cache -> hybrid search -> rerank -> generate.
"""
from common.config import Settings
from pipeline1_preparation.embedder import BgeM3Embedder
from pipeline1_preparation.vector_store import VectorStore
from pipeline2_chatbot.generator import GeminiGenerator
from pipeline2_chatbot.reranker import CohereReranker
from pipeline2_chatbot.retriever import Retriever
from pipeline2_chatbot.semantic_cache import ChatSemanticCache

NO_INFO_ANSWER = "Tôi không tìm thấy thông tin này trong dữ liệu hiện có."


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

        # Guardrail cho câu hỏi ngoài phạm vi (đã nêu trong review): nếu hybrid
        # search không trả về gì, không đưa câu hỏi cho LLM tự trả lời bừa.
        candidates = self._retriever.retrieve(question, limit=20)
        if not candidates:
            return {"answer": NO_INFO_ANSWER, "from_cache": False, "sources": [], "context_texts": []}

        top_chunks = self._reranker.rerank(question, candidates, top_n=top_n)
        answer = self._generator.generate(question, top_chunks)

        self._cache.store(question, answer)

        sources = [{"title": c.get("title"), "url": c.get("url")} for c in top_chunks]
        # context_texts: nội dung chunk thật đã đưa vào prompt - dùng để đánh giá
        # bằng RAGAS (retrieved_contexts) và để audit/debug câu trả lời khi cần.
        context_texts = [c["text"] for c in top_chunks]
        return {"answer": answer, "from_cache": False, "sources": sources, "context_texts": context_texts}
