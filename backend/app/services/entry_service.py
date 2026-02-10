import uuid
from datetime import datetime, timezone

from sqlalchemy import select, and_, or_, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entry import Entry
from app.models.feed import Feed
from app.models.user_entry_state import UserEntryState


async def get_entry(db: AsyncSession, user_id: str, entry_id: str) -> dict | None:
    """Get single entry with user state and feed info."""
    uid = uuid.UUID(user_id)
    eid = uuid.UUID(entry_id)

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
        .where(Entry.id == eid)
    )
    result = await db.execute(stmt)
    row = result.one_or_none()
    if row is None:
        return None

    entry = row[0]
    return {
        "entry": entry,
        "is_read": row[1] if row[1] is not None else False,
        "is_starred": row[2] if row[2] is not None else False,
        "feed_title": row[3],
        "feed_favicon_url": row[4],
    }


async def _get_or_create_state(
    db: AsyncSession, user_id: uuid.UUID, entry_id: uuid.UUID
) -> UserEntryState:
    """Fetch existing UserEntryState or create a new one."""
    stmt = select(UserEntryState).where(
        and_(
            UserEntryState.user_id == user_id,
            UserEntryState.entry_id == entry_id,
        )
    )
    result = await db.execute(stmt)
    state = result.scalar_one_or_none()
    if state is not None:
        return state

    state = UserEntryState(user_id=user_id, entry_id=entry_id)
    db.add(state)
    await db.flush()
    return state


async def mark_read(db: AsyncSession, user_id: str, entry_id: str) -> bool:
    """Mark entry as read. Lazy-create UserEntryState if needed."""
    uid = uuid.UUID(user_id)
    eid = uuid.UUID(entry_id)

    entry_exists = await db.execute(select(Entry.id).where(Entry.id == eid))
    if entry_exists.scalar_one_or_none() is None:
        return False

    state = await _get_or_create_state(db, uid, eid)
    state.is_read = True
    state.read_at = datetime.now(timezone.utc)
    await db.commit()
    return True


async def mark_unread(db: AsyncSession, user_id: str, entry_id: str) -> bool:
    """Mark entry as unread. Lazy-create UserEntryState if needed."""
    uid = uuid.UUID(user_id)
    eid = uuid.UUID(entry_id)

    entry_exists = await db.execute(select(Entry.id).where(Entry.id == eid))
    if entry_exists.scalar_one_or_none() is None:
        return False

    state = await _get_or_create_state(db, uid, eid)
    state.is_read = False
    state.read_at = None
    await db.commit()
    return True


async def toggle_star(db: AsyncSession, user_id: str, entry_id: str, starred: bool) -> bool:
    """Set star status. Lazy-create UserEntryState if needed."""
    uid = uuid.UUID(user_id)
    eid = uuid.UUID(entry_id)

    entry_exists = await db.execute(select(Entry.id).where(Entry.id == eid))
    if entry_exists.scalar_one_or_none() is None:
        return False

    state = await _get_or_create_state(db, uid, eid)
    state.is_starred = starred
    state.starred_at = datetime.now(timezone.utc) if starred else None
    await db.commit()
    return True


async def mark_all_read(
    db: AsyncSession,
    user_id: str,
    feed_id: str | None = None,
    group_id: str | None = None,
) -> int:
    """Mark all entries as read, optionally scoped to feed_id or group_id.

    For entries that already have a UserEntryState, update is_read=True.
    For entries without one, create a new state with is_read=True.
    Returns count of entries affected.
    """
    uid = uuid.UUID(user_id)
    now = datetime.now(timezone.utc)

    # Build base filter for entries in scope
    entry_filter = select(Entry.id).join(Feed, Entry.feed_id == Feed.id)
    if feed_id:
        entry_filter = entry_filter.where(Entry.feed_id == uuid.UUID(feed_id))
    if group_id:
        entry_filter = entry_filter.where(Feed.group_id == uuid.UUID(group_id))

    # Find unread entries that already have a state row
    existing_unread_stmt = (
        select(UserEntryState.id)
        .where(
            and_(
                UserEntryState.user_id == uid,
                UserEntryState.entry_id.in_(entry_filter),
                UserEntryState.is_read.is_(False),
            )
        )
    )
    existing_result = await db.execute(existing_unread_stmt)
    existing_ids = [row[0] for row in existing_result.all()]

    updated_count = 0
    if existing_ids:
        await db.execute(
            update(UserEntryState)
            .where(UserEntryState.id.in_(existing_ids))
            .values(is_read=True, read_at=now)
        )
        updated_count = len(existing_ids)

    # Find entries without any state row for this user
    missing_stmt = (
        entry_filter
        .outerjoin(
            UserEntryState,
            and_(
                UserEntryState.entry_id == Entry.id,
                UserEntryState.user_id == uid,
            ),
        )
        .where(UserEntryState.id.is_(None))
    )
    missing_result = await db.execute(missing_stmt)
    missing_entry_ids = [row[0] for row in missing_result.all()]

    for entry_id_val in missing_entry_ids:
        db.add(
            UserEntryState(
                user_id=uid,
                entry_id=entry_id_val,
                is_read=True,
                read_at=now,
            )
        )

    await db.commit()
    return updated_count + len(missing_entry_ids)
