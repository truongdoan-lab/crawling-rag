import sys

from common.config import load_settings
from preparation_pipeline.url_queue import UrlQueue


def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    settings = load_settings()
    queue = UrlQueue(settings)

    enqueued = queue.enqueue_many(urls)
    print(f"Enqueued {enqueued}/{len(urls)} URL.")

    if "--watch" in sys.argv:
        queue.schedule_periodic_discovery(urls, settings.crawl_interval_minutes)
        print(f"Scheduled scan at {len(urls)} URLs every {settings.crawl_interval_minutes} minutes.")

if __name__ == "__main__":
    main()
