import datetime as dt

from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler

from preparation_pipeline.queue_utils import QUEUE_NAME, enqueue_if_new


class UrlQueue:
    def __init__(self, settings):
        self._redis = Redis.from_url(settings.redis_url)
        self._queue = Queue(QUEUE_NAME, connection=self._redis)
        self._scheduler = Scheduler(queue=self._queue, connection=self._redis)

    def enqueue_many(self, urls: list[str]) -> int:
        return sum(enqueue_if_new(self._redis, u) for u in urls)

    def schedule_periodic_discovery(self, seed_urls: list[str], interval_minutes: int):
        from preparation_pipeline.worker import discover_and_enqueue

        self._scheduler.schedule(
            scheduled_time=dt.datetime.now(dt.timezone.utc),
            func=discover_and_enqueue,
            args=[seed_urls],
            interval=interval_minutes * 60,
            repeat=None,
            timeout=600
        )
