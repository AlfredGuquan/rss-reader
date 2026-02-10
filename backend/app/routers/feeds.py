from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.feed import FeedCreate, FeedUpdate, FeedResponse, FeedDiscoverResponse
from app.services import feed_service
from app.services.discovery_service import discover_feeds

router = APIRouter(prefix="/api/feeds", tags=["feeds"])


def _feed_to_response(feed, unread_count: int = 0) -> FeedResponse:
    return FeedResponse(
        id=str(feed.id),
        user_id=str(feed.user_id),
        url=feed.url,
        title=feed.title,
        site_url=feed.site_url,
        description=feed.description,
        favicon_url=feed.favicon_url,
        group_id=str(feed.group_id) if feed.group_id else None,
        fetch_interval_minutes=feed.fetch_interval_minutes,
        last_fetched_at=feed.last_fetched_at,
        status=feed.status,
        error_count=feed.error_count,
        unread_count=unread_count,
        created_at=feed.created_at,
        updated_at=feed.updated_at,
    )


@router.get("/discover", response_model=FeedDiscoverResponse)
async def discover_feed(url: str):
    feeds = await discover_feeds(url)
    return FeedDiscoverResponse(feeds=feeds)


@router.post("/import-opml")
async def import_opml(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    content = await file.read()
    text = content.decode("utf-8")

    from app.services.opml_service import parse_opml
    from app.services.group_service import create_group, get_groups

    opml_feeds = parse_opml(text)

    existing_groups = await get_groups(db, user_id)
    group_map = {g.name: str(g.id) for g in existing_groups}

    added = 0
    skipped = 0
    failed = 0

    for opml_feed in opml_feeds:
        group_id = None
        if opml_feed.group:
            if opml_feed.group not in group_map:
                new_group = await create_group(db, user_id, opml_feed.group)
                group_map[opml_feed.group] = str(new_group.id)
            group_id = group_map[opml_feed.group]

        try:
            await feed_service.create_feed(db, user_id, opml_feed.url, group_id)
            added += 1
        except ValueError:
            skipped += 1
        except Exception:
            failed += 1

    return {"added": added, "skipped": skipped, "failed": failed}


@router.post("", response_model=FeedResponse, status_code=201)
async def create_feed(data: FeedCreate, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    try:
        feed = await feed_service.create_feed(db, user_id, data.url, data.group_id)
    except ValueError as e:
        if "CONFLICT" in str(e):
            raise HTTPException(status_code=409, detail="Feed URL already exists")
        raise
    return _feed_to_response(feed)


@router.get("", response_model=list[FeedResponse])
async def list_feeds(db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    results = await feed_service.get_feeds(db, user_id)
    return [_feed_to_response(r["feed"], r["unread_count"]) for r in results]


@router.get("/{feed_id}", response_model=FeedResponse)
async def get_feed(feed_id: str, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    feed = await feed_service.get_feed(db, user_id, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    return _feed_to_response(feed)


@router.put("/{feed_id}", response_model=FeedResponse)
async def update_feed(feed_id: str, data: FeedUpdate, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    feed = await feed_service.update_feed(db, user_id, feed_id, data.title, data.group_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    return _feed_to_response(feed)


@router.delete("/{feed_id}", status_code=204)
async def delete_feed(feed_id: str, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    deleted = await feed_service.delete_feed(db, user_id, feed_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Feed not found")


@router.post("/{feed_id}/refresh")
async def refresh_feed(feed_id: str, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    feed = await feed_service.get_feed(db, user_id, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    from app.services.fetch_service import fetch_feed

    count = await fetch_feed(db, feed)
    return {"new_entries": count}
