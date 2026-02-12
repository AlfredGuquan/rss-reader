from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
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
        feed_type=getattr(feed, 'feed_type', 'rss'),
        source_platform=getattr(feed, 'source_platform', None),
        source_identifier=getattr(feed, 'source_identifier', None),
        created_at=feed.created_at,
        updated_at=feed.updated_at,
    )


@router.get("/discover", response_model=FeedDiscoverResponse)
async def discover_feed(url: str):
    feeds = await discover_feeds(url)
    return FeedDiscoverResponse(feeds=feeds)


@router.get("/export-opml")
async def export_opml(db: AsyncSession = Depends(get_db)):
    """Export all feeds as OPML 2.0 XML."""
    from app.services.opml_service import generate_opml
    from app.services.group_service import get_groups

    user_id = settings.default_user_id
    feed_results = await feed_service.get_feeds(db, user_id)
    groups = await get_groups(db, user_id)
    group_name_map = {str(g.id): g.name for g in groups}

    feeds_with_groups = []
    for r in feed_results:
        feed = r["feed"]
        group_name = group_name_map.get(str(feed.group_id)) if feed.group_id else None
        feeds_with_groups.append({"feed": feed, "group_name": group_name})

    xml_content = generate_opml(feeds_with_groups)
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=subscriptions.opml"},
    )


@router.post("/preview-opml")
async def preview_opml(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Parse an OPML file and return a preview of feeds to import."""
    from app.services.opml_service import parse_opml
    from sqlalchemy import select
    from app.models.feed import Feed as FeedModel
    import uuid

    user_id = settings.default_user_id
    uid = uuid.UUID(user_id)

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("utf-8", errors="replace")

    opml_feeds = parse_opml(text)

    existing_result = await db.execute(
        select(FeedModel.url).where(FeedModel.user_id == uid)
    )
    existing_urls = {row[0] for row in existing_result.all()}

    from app.services.group_service import get_groups
    existing_groups = await get_groups(db, user_id)
    existing_group_names = {g.name for g in existing_groups}

    feeds_preview = []
    group_feed_counts: dict[str, dict] = {}
    new_count = 0
    duplicate_count = 0

    for opml_feed in opml_feeds:
        is_dup = opml_feed.url in existing_urls
        status = "duplicate" if is_dup else "new"
        if is_dup:
            duplicate_count += 1
        else:
            new_count += 1

        feeds_preview.append({
            "title": opml_feed.title,
            "url": opml_feed.url,
            "site_url": opml_feed.site_url,
            "group": opml_feed.group,
            "status": status,
        })

        if opml_feed.group:
            if opml_feed.group not in group_feed_counts:
                group_feed_counts[opml_feed.group] = {
                    "name": opml_feed.group,
                    "feed_count": 0,
                    "is_new": opml_feed.group not in existing_group_names,
                }
            group_feed_counts[opml_feed.group]["feed_count"] += 1

    return {
        "groups": list(group_feed_counts.values()),
        "feeds": feeds_preview,
        "summary": {
            "total": len(opml_feeds),
            "new": new_count,
            "duplicate": duplicate_count,
        },
    }


@router.post("/import-opml")
async def import_opml(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Import feeds from an OPML file using batch creation (no HTTP fetching)."""
    from app.services.opml_service import parse_opml, create_feed_from_opml
    from app.services.group_service import create_group, get_groups

    user_id = settings.default_user_id
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("utf-8", errors="replace")

    opml_feeds = parse_opml(text)

    existing_groups = await get_groups(db, user_id)
    group_map = {g.name: str(g.id) for g in existing_groups}

    added = 0
    skipped = 0

    for opml_feed in opml_feeds:
        group_id = None
        if opml_feed.group:
            if opml_feed.group not in group_map:
                new_group = await create_group(db, user_id, opml_feed.group)
                group_map[opml_feed.group] = str(new_group.id)
            group_id = group_map[opml_feed.group]

        feed = await create_feed_from_opml(db, user_id, opml_feed, group_id)
        if feed is None:
            skipped += 1
        else:
            added += 1

    await db.commit()
    return {"added": added, "skipped": skipped, "failed": 0}


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
    feed = await feed_service.update_feed(db, user_id, feed_id, data.title, data.group_id, data.status)
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
