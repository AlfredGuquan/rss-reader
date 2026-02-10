import logging
from datetime import datetime

import feedparser
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.models.entry import Entry
from app.models.feed import Feed

logger = logging.getLogger(__name__)


async def fetch_feed(session: AsyncSession, feed: Feed) -> int:
    """Fetch new entries for a feed. Returns number of new entries."""
    headers = {"User-Agent": "RSS Reader/1.0"}
    if feed.etag:
        headers["If-None-Match"] = feed.etag
    if feed.last_modified_header:
        headers["If-Modified-Since"] = feed.last_modified_header

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(str(feed.url), headers=headers)

        if response.status_code == 304:
            feed.last_fetched_at = datetime.utcnow()
            await session.commit()
            return 0

        response.raise_for_status()
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

            published_parsed = entry.get("published_parsed") or entry.get(
                "updated_parsed"
            )
            if published_parsed:
                published_at = datetime(*published_parsed[:6])
            else:
                published_at = datetime.utcnow()

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
                )
                .on_conflict_do_nothing(index_elements=["feed_id", "guid"])
            )
            result = await session.execute(stmt)
            if result.rowcount > 0:
                new_count += 1

        feed.last_fetched_at = datetime.utcnow()
        feed.etag = response.headers.get("ETag")
        feed.last_modified_header = response.headers.get("Last-Modified")
        feed.error_count = 0
        feed.status = "active"
        feed.last_error = None
        await session.commit()

        logger.info("Fetched %d new entries for feed '%s'", new_count, feed.title)
        return new_count

    except Exception as exc:
        feed.last_fetched_at = datetime.utcnow()
        feed.error_count = (feed.error_count or 0) + 1
        feed.last_error = str(exc)
        if feed.error_count >= 3:
            feed.status = "error"
        await session.commit()
        logger.error("Error fetching feed '%s': %s", feed.title, exc)
        return 0
