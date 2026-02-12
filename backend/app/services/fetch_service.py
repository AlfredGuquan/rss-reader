import asyncio
import logging
from datetime import datetime

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.config import settings
from app.models.entry import Entry
from app.models.feed import Feed
from app.services.dedup_service import compute_simhash, find_duplicate

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


async def fetch_feed(session: AsyncSession, feed: Feed) -> int:
    """Fetch new entries for a feed with retry + exponential backoff."""
    headers = {"User-Agent": "RSS Reader/1.0"}

    if getattr(feed, 'source_platform', None) == "reddit":
        headers["User-Agent"] = settings.reddit_user_agent
    if feed.etag:
        headers["If-None-Match"] = feed.etag
    if feed.last_modified_header:
        headers["If-Modified-Since"] = feed.last_modified_header

    response = None
    last_exc = None

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(str(feed.url), headers=headers)

            if response.status_code == 304:
                feed.last_fetched_at = datetime.utcnow()
                await session.commit()
                return 0

            response.raise_for_status()
            last_exc = None
            break
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES - 1:
                delay = 2 ** attempt  # 1s, 2s
                logger.warning(
                    "Retry %d/%d for feed '%s' after %ds: %s",
                    attempt + 1, MAX_RETRIES, feed.title, delay, exc,
                )
                await asyncio.sleep(delay)

    if last_exc is not None:
        feed.last_fetched_at = datetime.utcnow()
        feed.error_count = (feed.error_count or 0) + 1
        feed.last_error = str(last_exc)
        if feed.error_count >= 3:
            feed.status = "error"
        await session.commit()
        logger.error("Error fetching feed '%s' after %d retries: %s", feed.title, MAX_RETRIES, last_exc)
        return 0

    parsed = feedparser.parse(response.text)

    new_count = 0
    for entry in parsed.entries:
        guid = entry.get("id") or entry.get("link") or entry.get("title")
        if not guid:
            continue

        title = entry.get("title", "Untitled")
        url = entry.get("link", "")
        author = entry.get("author")
        summary = entry.get("summary")
        content = (
            entry.get("content", [{}])[0].get("value")
            if entry.get("content")
            else None
        )

        published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if published_parsed:
            published_at = datetime(*published_parsed[:6])
        else:
            published_at = datetime.utcnow()

        simhash_title = compute_simhash(title) if title else None

        stmt = (
            sqlite_insert(Entry)
            .values(
                feed_id=feed.id,
                guid=guid,
                title=title,
                url=url,
                author=author,
                summary=summary,
                content=content,
                content_fetched=False,
                published_at=published_at,
                simhash_title=simhash_title,
            )
            .on_conflict_do_nothing(index_elements=["feed_id", "guid"])
        )
        result = await session.execute(stmt)
        if result.rowcount > 0:
            new_count += 1

            if simhash_title:
                await session.flush()
                entry_row = await session.execute(
                    select(Entry).where(
                        Entry.feed_id == feed.id, Entry.guid == guid
                    )
                )
                new_entry = entry_row.scalar_one()
                dup_id = await find_duplicate(
                    session,
                    new_entry.id,
                    simhash_title,
                    published_at,
                    feed.id,
                )
                if dup_id:
                    new_entry.duplicate_of_id = dup_id

    feed.last_fetched_at = datetime.utcnow()
    feed.etag = response.headers.get("ETag")
    feed.last_modified_header = response.headers.get("Last-Modified")
    feed.error_count = 0
    feed.status = "active"
    feed.last_error = None
    await session.commit()

    logger.info("Fetched %d new entries for feed '%s'", new_count, feed.title)
    return new_count
