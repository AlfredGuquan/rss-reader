"""Full-text content fetching with cascade extraction strategy."""

import asyncio
import json
import logging

import httpx
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.entry import Entry
from app.models.feed import Feed

logger = logging.getLogger(__name__)

_semaphore = asyncio.Semaphore(5)
MAX_CONTENT_RETRIES = 3
MIN_CONTENT_LENGTH = 200


async def download_html(url: str, feed_config: dict | None = None) -> str | None:
    """Download page HTML using httpx."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; RSS-Reader/1.0)"}
    if feed_config:
        if feed_config.get("user_agent"):
            headers["User-Agent"] = feed_config["user_agent"]
        if feed_config.get("headers"):
            headers.update(feed_config["headers"])

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
    except Exception as exc:
        logger.warning("Failed to download %s: %s", url, exc)
        return None


async def extract_with_custom_rules(html: str, config: dict) -> str | None:
    """Layer 0: Extract using CSS selectors from feed config."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")

        css_remove = config.get("css_remove", "")
        if css_remove:
            for selector in css_remove.split(","):
                selector = selector.strip()
                if selector:
                    for el in soup.select(selector):
                        el.decompose()

        css_selector = config.get("css_selector", "")
        if css_selector:
            elements = soup.select(css_selector)
            if elements:
                content = "\n".join(str(el) for el in elements)
                return content if len(content) >= MIN_CONTENT_LENGTH else None

        xpath = config.get("xpath", "")
        if xpath:
            from lxml import etree
            tree = etree.HTML(html)
            elements = tree.xpath(xpath)
            if elements:
                content = "\n".join(
                    etree.tostring(el, encoding="unicode", method="html")
                    for el in elements
                )
                return content if len(content) >= MIN_CONTENT_LENGTH else None

    except Exception as exc:
        logger.warning("Custom rule extraction failed: %s", exc)
    return None


async def extract_with_trafilatura(html: str, mode: str = "default") -> str | None:
    """Layer 1: Extract using trafilatura with enhanced params."""
    try:
        import trafilatura

        kwargs = {
            "include_links": True,
            "include_images": True,
            "output_format": "html",
            "deduplicate": True,
        }
        if mode == "precision":
            kwargs["favor_precision"] = True
        elif mode == "recall":
            kwargs["favor_recall"] = True

        content = await asyncio.to_thread(trafilatura.extract, html, **kwargs)
        if content and len(content) >= MIN_CONTENT_LENGTH:
            return content
    except Exception as exc:
        logger.warning("Trafilatura extraction failed: %s", exc)
    return None


async def extract_with_readability(html: str) -> str | None:
    """Layer 2: Extract using readability-lxml as fallback."""
    try:
        from readability import Document
        doc = await asyncio.to_thread(Document, html)
        content = await asyncio.to_thread(doc.summary)
        if content and len(content) >= MIN_CONTENT_LENGTH:
            return content
    except Exception as exc:
        logger.warning("Readability extraction failed: %s", exc)
    return None


async def cascade_extract(html: str, feed_config: dict | None = None) -> tuple[str | None, str]:
    """Try extraction layers in order, return (content, method_name)."""
    # Layer 0: Custom CSS/XPath rules
    if feed_config and (feed_config.get("css_selector") or feed_config.get("xpath")):
        content = await extract_with_custom_rules(html, feed_config)
        if content:
            return content, "custom_css"

    # Layer 1: Trafilatura
    mode = "default"
    if feed_config:
        mode = feed_config.get("extraction_mode", "default")
    content = await extract_with_trafilatura(html, mode)
    if content:
        return content, "trafilatura"

    # Layer 2: Readability
    content = await extract_with_readability(html)
    if content:
        return content, "readability"

    return None, "none"


async def fetch_content_for_entry(session: AsyncSession, entry: Entry, feed: Feed | None = None) -> bool:
    """Fetch full-text content for a single entry with cascade extraction."""
    if entry.content_fetch_status in ("success", "permanent_failure"):
        return False
    if not entry.url:
        return False

    feed_config = None
    if feed and feed.fulltext_config:
        try:
            feed_config = json.loads(feed.fulltext_config)
        except (json.JSONDecodeError, TypeError):
            pass

    async with _semaphore:
        try:
            html = await download_html(entry.url, feed_config)
            if not html:
                entry.content_fetch_status = "failed"
                entry.content_fetch_error = "Failed to download page"
                entry.content_fetch_retries = (entry.content_fetch_retries or 0) + 1
                if entry.content_fetch_retries >= MAX_CONTENT_RETRIES:
                    entry.content_fetch_status = "permanent_failure"
                entry.content_fetched = True
                await session.commit()
                return False

            content, method = await cascade_extract(html, feed_config)
            if content:
                entry.content = content
                entry.content_fetch_status = "success"
                entry.extraction_method = method
                entry.content_fetch_error = None
            else:
                entry.content_fetch_status = "failed"
                entry.content_fetch_error = "All extraction methods returned empty content"
                entry.content_fetch_retries = (entry.content_fetch_retries or 0) + 1
                if entry.content_fetch_retries >= MAX_CONTENT_RETRIES:
                    entry.content_fetch_status = "permanent_failure"

            entry.content_fetched = True
            await session.commit()
            return content is not None

        except Exception as exc:
            logger.error("Failed to fetch content for %s: %s", entry.url, exc)
            entry.content_fetch_status = "failed"
            entry.content_fetch_error = str(exc)[:500]
            entry.content_fetch_retries = (entry.content_fetch_retries or 0) + 1
            if entry.content_fetch_retries >= MAX_CONTENT_RETRIES:
                entry.content_fetch_status = "permanent_failure"
            entry.content_fetched = True
            await session.commit()
            return False


async def fetch_content_batch(session: AsyncSession, limit: int = 20) -> int:
    """Batch fetch full-text for pending/failed entries, joining Feed for config."""
    result = await session.execute(
        select(Entry)
        .options(joinedload(Entry.feed))
        .where(
            or_(
                Entry.content_fetch_status == "pending",
                Entry.content_fetch_status == "failed",
            ),
            Entry.content_fetch_retries < MAX_CONTENT_RETRIES,
        )
        .order_by(Entry.created_at.desc())
        .limit(limit)
    )
    entries = result.unique().scalars().all()

    count = 0
    for entry in entries:
        if await fetch_content_for_entry(session, entry, entry.feed):
            count += 1

    return count
