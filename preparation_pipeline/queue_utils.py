from urllib.parse import urlparse

from redis import Redis
from rq import Queue

SEEN_URLS_KEY = "crawler:seen_urls"
QUEUE_NAME = "crawl_jobs"


def domain_of(url: str) -> str:
    return urlparse(url).netloc


def enqueue_if_new(redis_conn: Redis, url: str) -> bool:
    added = redis_conn.sadd(SEEN_URLS_KEY, url)
    if not added:
        return False
    
    from preparation_pipeline.worker import process_url

    Queue(QUEUE_NAME, connection=redis_conn).enqueue(
        process_url, url, domain_of(url), job_timeout="10m"
    )
    return True
