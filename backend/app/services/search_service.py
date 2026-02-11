import uuid
import re
import math

from sqlalchemy import text, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entry import Entry
from app.models.feed import Feed
from app.models.user_entry_state import UserEntryState
from app.schemas.entry import EntryResponse, EntryListResponse


def _sanitize_fts_query(query: str) -> str:
    """Escape FTS5 special characters and wrap each word in quotes."""
    words = query.strip().split()
    sanitized = []
    for word in words:
        cleaned = re.sub(r'["\*\(\)\-\+\^]', '', word)
        if cleaned:
            sanitized.append(f'"{cleaned}"')
    return ' '.join(sanitized)


async def search_entries(
    db: AsyncSession,
    user_id: str,
    query: str,
    page: int = 1,
    per_page: int = 50,
) -> EntryListResponse:
    uid = uuid.UUID(user_id)
    sanitized = _sanitize_fts_query(query)
    if not sanitized:
        return EntryListResponse(items=[], total=0, page=page, per_page=per_page, total_pages=0)

    count_sql = text("""
        SELECT COUNT(*) FROM entries_fts
        JOIN entries ON entries_fts.entry_id = entries.id
        JOIN feeds ON entries.feed_id = feeds.id
        WHERE entries_fts MATCH :query
        AND feeds.user_id = :user_id
    """)
    count_result = await db.execute(count_sql, {"query": sanitized, "user_id": uid.hex})
    total = count_result.scalar() or 0
    total_pages = max(1, math.ceil(total / per_page))

    offset = (page - 1) * per_page
    search_sql = text("""
        SELECT entries_fts.entry_id, rank
        FROM entries_fts
        JOIN entries ON entries_fts.entry_id = entries.id
        JOIN feeds ON entries.feed_id = feeds.id
        WHERE entries_fts MATCH :query
        AND feeds.user_id = :user_id
        ORDER BY rank
        LIMIT :limit OFFSET :offset
    """)
    search_result = await db.execute(
        search_sql,
        {"query": sanitized, "user_id": uid.hex, "limit": per_page, "offset": offset},
    )
    raw_entry_ids = [row[0] for row in search_result.all()]

    if not raw_entry_ids:
        return EntryListResponse(items=[], total=total, page=page, per_page=per_page, total_pages=total_pages)

    # Convert hex strings from raw SQL to UUID objects for ORM query
    entry_ids = [uuid.UUID(eid) if isinstance(eid, str) else eid for eid in raw_entry_ids]

    stmt = (
        select(
            Entry,
            UserEntryState.is_read,
            UserEntryState.is_starred,
            Feed.title.label("feed_title"),
            Feed.favicon_url.label("feed_favicon_url"),
        )
        .join(Feed, Entry.feed_id == Feed.id)
        .outerjoin(
            UserEntryState,
            and_(
                UserEntryState.entry_id == Entry.id,
                UserEntryState.user_id == uid,
            ),
        )
        .where(Entry.id.in_(entry_ids))
    )
    result = await db.execute(stmt)

    entry_map = {}
    for row in result.all():
        entry = row[0]
        entry_map[str(entry.id)] = EntryResponse(
            id=str(entry.id),
            feed_id=str(entry.feed_id),
            guid=entry.guid,
            title=entry.title,
            url=entry.url,
            author=entry.author,
            summary=entry.summary,
            content=entry.content,
            content_fetched=entry.content_fetched,
            published_at=entry.published_at,
            created_at=entry.created_at,
            is_read=row[1] if row[1] is not None else False,
            is_starred=row[2] if row[2] is not None else False,
            feed_title=row[3],
            feed_favicon_url=row[4],
        )

    items = [entry_map[str(eid)] for eid in entry_ids if str(eid) in entry_map]

    return EntryListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )
