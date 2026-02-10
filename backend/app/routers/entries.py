import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.entry import Entry
from app.models.feed import Feed
from app.models.user_entry_state import UserEntryState
from app.schemas.entry import EntryResponse, EntryListResponse, MarkAllReadRequest
from app.services import entry_service

router = APIRouter(prefix="/api/entries", tags=["entries"])


@router.get("", response_model=EntryListResponse)
async def list_entries(
    feed_id: str | None = None,
    group_id: str | None = None,
    status: str = Query(default="all", pattern="^(all|unread|starred)$"),
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

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    total_pages = max(1, math.ceil(total / per_page))

    offset = (page - 1) * per_page
    items_query = base_query.order_by(Entry.published_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(items_query)

    items = []
    for row in result.all():
        entry = row[0]
        is_read = row[1] if row[1] is not None else False
        is_starred = row[2] if row[2] is not None else False
        feed_title = row[3]
        feed_favicon_url = row[4]

        items.append(
            EntryResponse(
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
                is_read=is_read,
                is_starred=is_starred,
                feed_title=feed_title,
                feed_favicon_url=feed_favicon_url,
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
        published_at=entry.published_at,
        created_at=entry.created_at,
        is_read=result["is_read"],
        is_starred=result["is_starred"],
        feed_title=result["feed_title"],
        feed_favicon_url=result["feed_favicon_url"],
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
