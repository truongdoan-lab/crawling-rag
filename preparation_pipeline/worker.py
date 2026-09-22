import uuid
from datetime import datetime, timezone

from common.config import load_settings
from preparation_pipeline.chunking import chunk_markdown
from preparation_pipeline.crawler import crawl_url_sync
from preparation_pipeline.db import ArticleRepository, content_hash
from preparation_pipeline.embedder import BgeM3Embedder
from preparation_pipeline.vector_store import VectorStore

_settings = load_settings()
_repo = ArticleRepository(_settings)
_embedder = BgeM3Embedder(_settings.embedding_model, _settings.embedding_device)
_store = VectorStore(_settings.qdrant_url, _settings.qdrant_collection)
_store.ensure_collection()


def process_url(url: str, domain: str):
    _repo.upsert_pending(url, domain)

    crawled = crawl_url_sync(url)
    if crawled is None:
        _repo.mark_failed(url, "Không cào được nội dung (cả static lẫn Playwright đều thất bại)")
        return

    new_hash = content_hash(crawled.text)

    # Chỉ dựa vào "URL đã tồn tại" là chưa đủ để biết bài "mới" - so hash để
    # phát hiện cả trường hợp bài cũ bị chỉnh sửa nội dung (điểm đã nêu trong review)
    if not _repo.needs_processing(url, new_hash):
        return  # nội dung không đổi kể từ lần embed trước -> bỏ qua, tiết kiệm compute

    _repo.mark_crawled(url, crawled.title, None, new_hash)

    try:
        # Nội dung đã đổi (hoặc là bài mới) -> xóa chunk/vector cũ trước khi ghi mới
        _store.delete_by_url(url)

        chunks = chunk_markdown(crawled.text)
        if not chunks:
            _repo.mark_failed(url, "Không tách được chunk nào từ nội dung")
            return

        embeddings = _embedder.embed([c.text for c in chunks])
        point_ids = [
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{url}#{c.chunk_index}")) for c in chunks
        ]
        payloads = [
            {
                "url": url,
                "domain": domain,
                "title": crawled.title,
                "heading_path": c.heading_path,
                "chunk_index": c.chunk_index,
                "text": c.text,
                "indexed_at": datetime.now(timezone.utc).isoformat(),
            }
            for c in chunks
        ]
        _store.upsert_chunks(point_ids, embeddings, payloads)
        _repo.mark_embedded(url)
    except Exception as exc:  # noqa: BLE001 - job RQ, cần bắt hết để mark_failed thay vì retry vô hạn
        _repo.mark_failed(url, f"Lỗi khi chunk/embed/lưu: {exc}")


def discover_and_enqueue(seed_urls: list[str]) -> int:
    """
    Job chạy định kỳ (qua rq-scheduler): mở lại các trang seed (trang chủ,
    trang danh mục), tìm link bài viết mới, enqueue process_url cho link mới.
    """
    import asyncio

    from redis import Redis

    from crawl4ai import AsyncWebCrawler
    from preparation_pipeline.queue_utils import enqueue_if_new

    redis_conn = Redis.from_url(_settings.redis_url)

    async def _discover() -> set[str]:
        new_links: set[str] = set()
        async with AsyncWebCrawler() as crawler:
            for seed in seed_urls:
                result = await crawler.arun(url=seed)
                if result.success:
                    for link in result.links.get("internal", []):
                        href = link.get("href")
                        if href:
                            new_links.add(href)
        return new_links

    links = asyncio.run(_discover())
    return sum(enqueue_if_new(redis_conn, link) for link in links)
