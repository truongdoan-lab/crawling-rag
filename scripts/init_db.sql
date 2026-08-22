-- Schema quản lý nội dung bài viết (Pipeline 1, bước 3).
-- content_hash + status là 2 điểm bổ sung theo review, giúp:
--   - Phát hiện bài viết bị sửa nội dung dù URL không đổi (content_hash)
--   - Retry đúng bước bị lỗi thay vì crawl lại từ đầu (status)

CREATE TABLE IF NOT EXISTS articles (
    id              BIGSERIAL PRIMARY KEY,
    url             TEXT UNIQUE NOT NULL,
    domain          TEXT NOT NULL,
    title           TEXT,
    published_at    TIMESTAMPTZ,
    content_hash    CHAR(64) NOT NULL DEFAULT '',   -- SHA-256 nội dung đã làm sạch
    status          TEXT NOT NULL DEFAULT 'pending', -- pending|crawled|embedded|failed
    error_message   TEXT,
    crawled_at      TIMESTAMPTZ,
    embedded_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_domain ON articles(domain);
CREATE INDEX IF NOT EXISTS idx_articles_content_hash ON articles(content_hash);
