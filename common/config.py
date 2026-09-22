import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Postgres
    postgres_dsn: str

    # Redis
    redis_url: str

    # Qdrant
    qdrant_url: str
    qdrant_collection: str

    # Embedding: BGE-M3
    embedding_model: str
    embedding_device: str

    # Cohere Rerank
    cohere_api_key: str
    cohere_rerank_model: str

    # Gemini
    gemini_api_key: str
    gemini_model: str

    # Crawl and Cache
    crawl_interval_minutes: int
    semantic_cache_threshold: float
    semantic_cache_ttl_seconds: int


def load_settings() -> Settings:
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB", "") # Fill
    pg_user = os.getenv("POSTGRES_USER", "") # Fill
    pg_password = os.getenv("POSTGRES_PASSWORD", "") # Fill
    postgres_dsn = (
        f"host={pg_host} port={pg_port} dbname={pg_db} "
        f"user={pg_user} password={pg_password}"
    )

    return Settings(
        postgres_dsn=postgres_dsn,
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        qdrant_collection=os.getenv("QDRANT_COLLECTION", "articles"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3"),
        embedding_device=os.getenv("EMBEDDING_DEVICE", "cpu"),
        cohere_api_key=os.getenv("COHERE_API_KEY", ""),
        cohere_rerank_model=os.getenv("COHERE_RERANK_MODEL", "rerank-v3.5"),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        crawl_interval_minutes=int(os.getenv("CRAWL_INTERVAL_MINUTES", "60")),
        semantic_cache_threshold=float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.1")),
        semantic_cache_ttl_seconds=int(os.getenv("SEMANTIC_CACHE_TTL_SECONDS", "86400")),
    )
