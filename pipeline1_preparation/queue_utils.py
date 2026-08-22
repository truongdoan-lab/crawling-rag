"""
Hàm enqueue tầng thấp, dùng chung bởi url_queue.py (API cho script) và
worker.py (job tự enqueue tiếp khi discover thêm URL mới). Tách riêng file
này để 2 module kia không phải import lẫn nhau (tránh circular import).
"""
from urllib.parse import urlparse

from redis import Redis
from rq import Queue

SEEN_URLS_KEY = "crawler:seen_urls"
QUEUE_NAME = "crawl_jobs"


def domain_of(url: str) -> str:
    return urlparse(url).netloc


def enqueue_if_new(redis_conn: Redis, url: str) -> bool:
    """
    Enqueue 1 URL nếu chưa từng thấy (Redis Set dùng làm bộ nhớ dedupe).
    Trả về True nếu vừa enqueue mới, False nếu URL đã tồn tại trong queue/đã
    xử lý trước đó -> bỏ qua, tránh cào trùng và tránh dồn dập request.
    """
    added = redis_conn.sadd(SEEN_URLS_KEY, url)
    if not added:
        return False
    # import trễ (bên trong hàm) để tránh vòng lặp import với worker.py
    from pipeline1_preparation.worker import process_url

    Queue(QUEUE_NAME, connection=redis_conn).enqueue(
        process_url, url, domain_of(url), job_timeout="10m"
    )
    return True
