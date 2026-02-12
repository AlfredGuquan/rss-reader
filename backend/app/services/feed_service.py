import uuid
from urllib.parse import urlparse

import feedparser
import httpx
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.feed import Feed
from app.models.entry import Entry
from app.models.user_entry_state import UserEntryState
from app.services.discovery_service import discover_feeds
from app.services.platform_detector import detect_platform


async def parse_feed_url(url: str) -> dict | None:
    """Fetch and parse an RSS/Atom feed URL, returning metadata or None."""
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "RSS Reader/1.0"})
            feed = feedparser.parse(response.text)
    except httpx.HTTPError:
        return None

    if not feed.feed.get("title"):
        return None

    site_url = feed.feed.get("link", "")
    domain = urlparse(site_url).netloc if site_url else urlparse(url).netloc

    return {
        "title": feed.feed.get("title", url),
        "description": feed.feed.get("description"),
        "site_url": site_url,
        "favicon_url": f"https://www.google.com/s2/favicons?domain={domain}&sz=32" if domain else None,
    }


async def create_feed(
    session: AsyncSession,
    user_id: str,
    url: str,
    group_id: str | None = None,
) -> Feed:
    uid = uuid.UUID(user_id)

    # Platform detection — may transform URL to RSS feed URL
    platform_result = await detect_platform(url)
    actual_url = platform_result.feed_url if platform_result else url

    existing = await session.execute(
        select(Feed).where(and_(Feed.user_id == uid, Feed.url == actual_url))
    )
    if existing.scalar_one_or_none():
        raise ValueError("CONFLICT")

    meta = await parse_feed_url(actual_url)

    if meta is None and not platform_result:
        discovered = await discover_feeds(url)
        if discovered:
            meta = await parse_feed_url(discovered[0]["url"])
            if meta:
                actual_url = discovered[0]["url"]

    title = meta["title"] if meta else (platform_result.title_hint if platform_result else url)
    description = meta.get("description") if meta else None
    site_url = meta.get("site_url") if meta else (platform_result.site_url if platform_result else None)
    favicon_url = meta.get("favicon_url") if meta else None

    if platform_result and not favicon_url:
        domain = urlparse(platform_result.site_url or url).netloc
        favicon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=32" if domain else None

    feed = Feed(
        user_id=uid,
        url=actual_url,
        title=title,
        description=description,
        site_url=site_url,
        favicon_url=favicon_url,
        group_id=uuid.UUID(group_id) if group_id else None,
        source_platform=platform_result.platform if platform_result else None,
        source_identifier=platform_result.identifier if platform_result else None,
    )

    if platform_result and platform_result.platform == "reddit":
        feed.fetch_interval_minutes = 60

    session.add(feed)
    await session.commit()
    await session.refresh(feed)
    return feed


async def get_feeds(session: AsyncSession, user_id: str) -> list[dict]:
    uid = uuid.UUID(user_id)

    # Subquery: count unread entries per feed
    # An entry is unread if there is no user_entry_state row OR is_read is False
    unread_subq = (
        select(
            Entry.feed_id,
            func.count(Entry.id).label("unread_count"),
        )
        .outerjoin(
            UserEntryState,
            and_(
                UserEntryState.entry_id == Entry.id,
                UserEntryState.user_id == uid,
            ),
        )
        .where(
            or_(
                UserEntryState.id.is_(None),
                UserEntryState.is_read.is_(False),
            )
        )
        .group_by(Entry.feed_id)
        .subquery()
    )

    stmt = (
        select(Feed, func.coalesce(unread_subq.c.unread_count, 0).label("unread_count"))
        .outerjoin(unread_subq, Feed.id == unread_subq.c.feed_id)
        .where(Feed.user_id == uid)
        .order_by(Feed.created_at)
    )
    result = await session.execute(stmt)

    feeds = []
    for row in result.all():
        feed = row[0]
        unread_count = row[1]
        feeds.append({"feed": feed, "unread_count": unread_count})
    return feeds


async def get_feed(session: AsyncSession, user_id: str, feed_id: str) -> Feed | None:
    uid = uuid.UUID(user_id)
    fid = uuid.UUID(feed_id)
    result = await session.execute(
        select(Feed).where(and_(Feed.id == fid, Feed.user_id == uid))
    )
    return result.scalar_one_or_none()


async def update_feed(
    session: AsyncSession,
    user_id: str,
    feed_id: str,
    title: str | None = None,
    group_id: str | None = None,
    status: str | None = None,
) -> Feed | None:
    feed = await get_feed(session, user_id, feed_id)
    if not feed:
        return None

    if title is not None:
        feed.title = title
    if group_id is not None:
        feed.group_id = uuid.UUID(group_id) if group_id else None
    if status is not None:
        feed.status = status
        if status == "active":
            feed.error_count = 0
            feed.last_error = None

    await session.commit()
    await session.refresh(feed)
    return feed


async def delete_feed(session: AsyncSession, user_id: str, feed_id: str) -> bool:
    feed = await get_feed(session, user_id, feed_id)
    if not feed:
        return False
    await session.delete(feed)
    await session.commit()
    return True
