import hashlib
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

import psycopg2

from common.config import Settings


def content_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


class ArticleRepository:
    def __init__(self, settings: Settings):
        self._dsn = settings.postgres_dsn

    @contextmanager
    def _conn(self):
        conn = psycopg2.connect(self._dsn)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def upsert_pending(self, url: str, domain: str) -> int:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO articles (url, domain, content_hash, status)
                VALUES (%s, %s, '', 'pending')
                ON CONFLICT (url) DO NOTHING
                RETURNING id
                """,
                (url, domain),
            )
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute("SELECT id FROM articles WHERE url = %s", (url,))
            return cur.fetchone()[0]

    def needs_processing(self, url: str, new_hash: str) -> bool:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT content_hash, status FROM articles WHERE url = %s", (url,)
            )
            row = cur.fetchone()
            if row is None:
                return True
            old_hash, status = row
            if status != "embedded":
                return True
            return old_hash != new_hash

    def mark_crawled(
        self, url: str, title: str, published_at: Optional[datetime], new_hash: str
    ):
        now = datetime.now(timezone.utc)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE articles
                SET title = %s, published_at = %s, content_hash = %s,
                    status = 'crawled', crawled_at = %s, updated_at = %s,
                    error_message = NULL
                WHERE url = %s
                """,
                (title, published_at, new_hash, now, now, url),
            )

    def mark_embedded(self, url: str):
        now = datetime.now(timezone.utc)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE articles
                SET status = 'embedded', embedded_at = %s, updated_at = %s
                WHERE url = %s
                """,
                (now, now, url),
            )

    def mark_failed(self, url: str, error_message: str):
        now = datetime.now(timezone.utc)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE articles
                SET status = 'failed', error_message = %s, updated_at = %s
                WHERE url = %s
                """,
                (error_message[:2000], now, url),
            )
