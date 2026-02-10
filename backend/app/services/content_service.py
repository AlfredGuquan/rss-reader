"""Full-text content fetching for RSS entries using trafilatura."""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entry import Entry

logger = logging.getLogger(__name__)

_semaphore = asyncio.Semaphore(5)


async def fetch_content_for_entry(session: AsyncSession, entry: Entry) -> bool:
    """Fetch full-text content for a single entry. Returns True if content was updated."""
    if entry.content_fetched or not entry.url:
        return False

    async with _semaphore:
        try:
            import trafilatura

            downloaded = await asyncio.to_thread(trafilatura.fetch_url, entry.url)
            if downloaded:
                content = await asyncio.to_thread(
                    trafilatura.extract,
                    downloaded,
                    include_links=True,
                    include_images=True,
                    output_format="html",
                )
                if content:
                    entry.content = content
            entry.content_fetched = True
            await session.commit()
            return True
        except Exception as exc:
            logger.error("Failed to fetch content for %s: %s", entry.url, exc)
            entry.content_fetched = True
            await session.commit()
            return False


async def fetch_content_batch(session: AsyncSession, limit: int = 20) -> int:
    """Fetch full-text content for entries that haven't been fetched yet.

    Processes entries sequentially to avoid SQLite concurrency issues.
    """
    result = await session.execute(
        select(Entry)
        .where(Entry.content_fetched == False)  # noqa: E712
        .order_by(Entry.created_at.desc())
        .limit(limit)
    )
    entries = result.scalars().all()

    count = 0
    for entry in entries:
        if await fetch_content_for_entry(session, entry):
            count += 1

    return count
