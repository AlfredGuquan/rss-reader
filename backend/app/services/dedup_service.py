"""SimHash-based article deduplication service."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from trafilatura.deduplication import Simhash

from app.models.entry import Entry

logger = logging.getLogger(__name__)

TIME_WINDOW_DAYS = 3
HAMMING_THRESHOLD = 10  # max bit differences out of 64 (~0.84 similarity)


def compute_simhash(text: str) -> str:
    """Compute SimHash fingerprint, returns 16-char hex string."""
    h = Simhash(text)
    return format(h.hash, "016x")


def hamming_distance(hex_a: str, hex_b: str) -> int:
    """Compute Hamming distance between two 16-char hex SimHash strings."""
    int_a = int(hex_a, 16)
    int_b = int(hex_b, 16)
    return bin(int_a ^ int_b).count("1")


async def find_duplicate(
    db: AsyncSession,
    entry_id,
    simhash_title: str,
    published_at: datetime,
    feed_id,
) -> str | None:
    """Find a near-duplicate entry within ±TIME_WINDOW_DAYS by title SimHash.

    Returns the id of the canonical (earliest) duplicate, or None.
    Skips entries from the same feed (same-feed duplicates are handled by guid uniqueness).
    """
    window_start = published_at - timedelta(days=TIME_WINDOW_DAYS)
    window_end = published_at + timedelta(days=TIME_WINDOW_DAYS)

    stmt = (
        select(Entry.id, Entry.simhash_title)
        .where(
            and_(
                Entry.id != entry_id,
                Entry.feed_id != feed_id,
                Entry.simhash_title.isnot(None),
                Entry.duplicate_of_id.is_(None),
                Entry.published_at >= window_start,
                Entry.published_at <= window_end,
            )
        )
        .order_by(Entry.published_at.asc())
    )

    result = await db.execute(stmt)
    for row in result.all():
        candidate_id, candidate_hash = row
        if hamming_distance(simhash_title, candidate_hash) <= HAMMING_THRESHOLD:
            logger.debug(
                "Duplicate found: entry %s matches %s (hamming=%d)",
                entry_id,
                candidate_id,
                hamming_distance(simhash_title, candidate_hash),
            )
            return str(candidate_id)

    return None
