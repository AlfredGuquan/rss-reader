import asyncio
import logging
from datetime import datetime

from sqlalchemy import select

from app.database import async_session
from app.models.feed import Feed
from app.services.fetch_service import fetch_feed

logger = logging.getLogger(__name__)


async def fetch_all_feeds():
    """Fetch all active feeds that are due for refresh."""
    async with async_session() as session:
        result = await session.execute(
            select(Feed).where(Feed.status == "active")
        )
        feeds = result.scalars().all()

    semaphore = asyncio.Semaphore(5)

    async def fetch_one(feed: Feed):
        async with semaphore:
            async with async_session() as session:
                merged_feed = await session.merge(feed)
                now = datetime.utcnow()
                if (
                    merged_feed.last_fetched_at
                    and (now - merged_feed.last_fetched_at).total_seconds()
                    < merged_feed.fetch_interval_minutes * 60
                ):
                    return
                try:
                    count = await fetch_feed(session, merged_feed)
                    if count > 0:
                        logger.info(
                            "Feed '%s': %d new entries",
                            merged_feed.title,
                            count,
                        )
                except Exception as exc:
                    logger.error(
                        "Failed to fetch feed '%s': %s",
                        merged_feed.title,
                        exc,
                    )

    tasks = [asyncio.create_task(fetch_one(feed)) for feed in feeds]
    if tasks:
        await asyncio.gather(*tasks)
        logger.info("Scheduled fetch complete: %d feeds processed", len(tasks))


async def fetch_content_batch():
    """Batch fetch full-text content for entries that need it."""
    async with async_session() as session:
        from app.services.content_service import fetch_content_batch as _fetch_batch

        count = await _fetch_batch(session)
        if count > 0:
            logger.info("Content fetch batch: %d entries processed", count)
