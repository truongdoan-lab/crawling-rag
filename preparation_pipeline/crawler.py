import asyncio
from dataclasses import dataclass
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

MIN_CONTENT_LENGTH = 300
USER_AGENT = "Mozilla/5.0 (compatible; CourseProjectBot/1.0; +educational-use)"


@dataclass
class CrawledPage:
    title: str
    text: str 


async def fetch_static(url: str) -> Optional[CrawledPage]:
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        if len(text) < MIN_CONTENT_LENGTH:
            return None
        return CrawledPage(title=title, text=text)
    except Exception:
        return None


async def fetch_with_browser(url: str) -> Optional[CrawledPage]:
    browser_cfg = BrowserConfig(headless=True, verbose=False)
    run_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=run_cfg)
    if not result.success:
        return None
    md = result.markdown
    text = md.raw_markdown if hasattr(md, "raw_markdown") else str(md)
    title = ""
    metadata = getattr(result, "metadata", None)
    if metadata:
        title = metadata.get("title", "") or ""
    return CrawledPage(title=title, text=text)


async def crawl_url(url: str) -> Optional[CrawledPage]:
    page = await fetch_static(url)
    if page:
        return page
    return await fetch_with_browser(url)


def crawl_url_sync(url: str) -> Optional[CrawledPage]:
    return asyncio.run(crawl_url(url))
