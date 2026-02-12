import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.config import settings
from app.database import get_db
from app.models.entry import Entry
from app.models.feed import Feed
from app.models.user_entry_state import UserEntryState
from app.schemas.entry import EntryResponse, EntryListResponse, MarkAllReadRequest, DuplicateSource
from app.services import entry_service

router = APIRouter(prefix="/api/entries", tags=["entries"])


@router.get("", response_model=EntryListResponse)
async def list_entries(
    feed_id: str | None = None,
    group_id: str | None = None,
    status: str = Query(default="all", pattern="^(all|unread|starred)$"),
    deduplicate: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(settings.default_user_id)

    base_query = (
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
                UserEntryState.user_id == user_id,
            ),
        )
    )

    if feed_id:
        base_query = base_query.where(Entry.feed_id == uuid.UUID(feed_id))
    if group_id:
        base_query = base_query.where(Feed.group_id == uuid.UUID(group_id))

    if status == "unread":
        base_query = base_query.where(
            or_(
                UserEntryState.id.is_(None),
                UserEntryState.is_read.is_(False),
            )
        )
    elif status == "starred":
        base_query = base_query.where(UserEntryState.is_starred.is_(True))

    if deduplicate:
        base_query = base_query.where(Entry.duplicate_of_id.is_(None))

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    total_pages = max(1, math.ceil(total / per_page))

    offset = (page - 1) * per_page
    items_query = base_query.order_by(Entry.published_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(items_query)

    entry_ids = []
    rows_data = []
    for row in result.all():
        entry = row[0]
        rows_data.append(row)
        entry_ids.append(entry.id)

    dup_counts: dict[str, int] = {}
    dup_sources_map: dict[str, list[DuplicateSource]] = {}
    if deduplicate and entry_ids:
        DupEntry = aliased(Entry)
        DupFeed = aliased(Feed)
        dup_query = (
            select(
                DupEntry.duplicate_of_id,
                DupFeed.title,
                DupFeed.favicon_url,
                DupEntry.published_at,
            )
            .join(DupFeed, DupEntry.feed_id == DupFeed.id)
            .where(DupEntry.duplicate_of_id.in_(entry_ids))
        )
        dup_result = await db.execute(dup_query)
        for dup_of_id, dup_feed_title, dup_feed_favicon, dup_pub_at in dup_result.all():
            key = str(dup_of_id)
            dup_counts[key] = dup_counts.get(key, 0) + 1
            if key not in dup_sources_map:
                dup_sources_map[key] = []
            dup_sources_map[key].append(
                DuplicateSource(
                    feed_title=dup_feed_title,
                    feed_favicon_url=dup_feed_favicon,
                    published_at=dup_pub_at,
                )
            )

    items = []
    for row in rows_data:
        entry = row[0]
        is_read = row[1] if row[1] is not None else False
        is_starred = row[2] if row[2] is not None else False
        feed_title = row[3]
        feed_favicon_url = row[4]

        entry_id_str = str(entry.id)
        items.append(
            EntryResponse(
                id=entry_id_str,
                feed_id=str(entry.feed_id),
                guid=entry.guid,
                title=entry.title,
                url=entry.url,
                author=entry.author,
                summary=entry.summary,
                content=entry.content,
                content_fetched=entry.content_fetched,
                content_fetch_status=getattr(entry, 'content_fetch_status', 'pending'),
                extraction_method=getattr(entry, 'extraction_method', None),
                published_at=entry.published_at,
                created_at=entry.created_at,
                is_read=is_read,
                is_starred=is_starred,
                feed_title=feed_title,
                feed_favicon_url=feed_favicon_url,
                duplicate_of_id=str(entry.duplicate_of_id) if entry.duplicate_of_id else None,
                duplicate_count=dup_counts.get(entry_id_str, 0),
                duplicate_sources=dup_sources_map.get(entry_id_str),
            )
        )

    return EntryListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.post("/mark-all-read")
async def mark_all_read(data: MarkAllReadRequest, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    count = await entry_service.mark_all_read(
        db, user_id, feed_id=data.feed_id, group_id=data.group_id
    )
    return {"count": count}


@router.get("/search", response_model=EntryListResponse)
async def search_entries(
    q: str = Query(min_length=1, max_length=200),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    user_id = settings.default_user_id
    from app.services.search_service import search_entries as _search
    return await _search(db, user_id, q, page, per_page)


@router.get("/{entry_id}", response_model=EntryResponse)
async def get_entry(entry_id: str, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    result = await entry_service.get_entry(db, user_id, entry_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    entry = result["entry"]
    return EntryResponse(
        id=str(entry.id),
        feed_id=str(entry.feed_id),
        guid=entry.guid,
        title=entry.title,
        url=entry.url,
        author=entry.author,
        summary=entry.summary,
        content=entry.content,
        content_fetched=entry.content_fetched,
        content_fetch_status=getattr(entry, 'content_fetch_status', 'pending'),
        extraction_method=getattr(entry, 'extraction_method', None),
        published_at=entry.published_at,
        created_at=entry.created_at,
        is_read=result["is_read"],
        is_starred=result["is_starred"],
        feed_title=result["feed_title"],
        feed_favicon_url=result["feed_favicon_url"],
        duplicate_of_id=str(entry.duplicate_of_id) if entry.duplicate_of_id else None,
    )


@router.put("/{entry_id}/read")
async def mark_entry_read(entry_id: str, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    success = await entry_service.mark_read(db, user_id, entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"success": True}


@router.put("/{entry_id}/unread")
async def mark_entry_unread(entry_id: str, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    success = await entry_service.mark_unread(db, user_id, entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"success": True}


@router.put("/{entry_id}/star")
async def star_entry(entry_id: str, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    success = await entry_service.toggle_star(db, user_id, entry_id, starred=True)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"success": True}


@router.put("/{entry_id}/unstar")
async def unstar_entry(entry_id: str, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    success = await entry_service.toggle_star(db, user_id, entry_id, starred=False)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"success": True}


@router.post("/{entry_id}/fetch-content")
async def fetch_entry_content(entry_id: str, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    result = await entry_service.get_entry(db, user_id, entry_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    entry = result["entry"]
    # Reset status for refetch
    entry.content_fetch_status = "pending"
    entry.content_fetch_retries = 0
    entry.content_fetch_error = None
    await db.commit()

    # Load feed for fulltext config
    feed = await db.get(Feed, entry.feed_id)

    from app.services.content_service import fetch_content_for_entry
    success = await fetch_content_for_entry(db, entry, feed)

    await db.refresh(entry)
    return {
        "success": success,
        "content_fetched": entry.content_fetched,
        "has_content": entry.content is not None,
        "extraction_method": entry.extraction_method,
    }
