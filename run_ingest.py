"""
CLI: enqueue danh sách URL ban đầu để Pipeline 1 xử lý.

Dùng:
    python run_ingest.py seed_urls.txt          # enqueue 1 lần
    python run_ingest.py seed_urls.txt --watch   # + lên lịch quét lại định kỳ

seed_urls.txt: mỗi dòng 1 URL.
Sau khi enqueue, chạy worker riêng ở terminal khác: rq worker crawl_jobs
(và rqscheduler nếu dùng --watch, xem README).
"""
import sys

from common.config import load_settings
from pipeline1_preparation.url_queue import UrlQueue


def main():
    if len(sys.argv) < 2:
        print("Dùng: python run_ingest.py <file_url> [--watch]")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    settings = load_settings()
    queue = UrlQueue(settings)

    enqueued = queue.enqueue_many(urls)
    print(f"Đã enqueue {enqueued}/{len(urls)} URL (số còn lại đã tồn tại từ trước).")

    if "--watch" in sys.argv:
        queue.schedule_periodic_discovery(urls, settings.crawl_interval_minutes)
        print(f"Đã lên lịch quét lại {len(urls)} trang seed mỗi {settings.crawl_interval_minutes} phút.")
        print("Nhớ chạy thêm: rqscheduler")

    print("Chạy worker để xử lý job: rq worker crawl_jobs")


if __name__ == "__main__":
    main()
