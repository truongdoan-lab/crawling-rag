"""
Điều phối URL cần crawl bằng Redis Queue (RQ).

Khắc phục 2 điểm đã nêu trong review:
- Dedupe: enqueue_if_new() dùng 1 Redis Set lưu URL đã "seen" để không
  enqueue trùng.
- Scheduling định kỳ: RQ tự thân không có cron built-in -> dùng rq-scheduler
  (Scheduler) để enqueue job discover_and_enqueue theo chu kỳ cố định.
"""
import datetime as dt

from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler

from pipeline1_preparation.queue_utils import QUEUE_NAME, enqueue_if_new


class UrlQueue:
    def __init__(self, settings):
        self._redis = Redis.from_url(settings.redis_url)
        self._queue = Queue(QUEUE_NAME, connection=self._redis)
        self._scheduler = Scheduler(queue=self._queue, connection=self._redis)

    def enqueue_many(self, urls: list[str]) -> int:
        """Enqueue danh sách URL, bỏ qua URL đã enqueue/xử lý trước đó. Trả về số lượng mới."""
        return sum(enqueue_if_new(self._redis, u) for u in urls)

    def schedule_periodic_discovery(self, seed_urls: list[str], interval_minutes: int):
        """
        Lên lịch quét định kỳ: cứ mỗi interval_minutes, mở lại các trang seed
        (trang chủ / trang danh mục) để tìm bài viết mới và enqueue.
        """
        from pipeline1_preparation.worker import discover_and_enqueue

        self._scheduler.schedule(
            scheduled_time=dt.datetime.utcnow(),
            func=discover_and_enqueue,
            args=[seed_urls],
            interval=interval_minutes * 60,
            repeat=None,  # lặp vô hạn
        )
