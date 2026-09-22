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
