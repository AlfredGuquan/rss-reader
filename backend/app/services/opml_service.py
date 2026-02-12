"""OPML file parser and generator for feed subscriptions."""

import uuid
import xml.etree.ElementTree as ET
import xml.dom.minidom
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feed import Feed


@dataclass
class OpmlFeed:
    title: str
    url: str
    group: str | None
    site_url: str | None = None
    description: str | None = None


def parse_opml(content: str) -> list[OpmlFeed]:
    """Parse OPML XML string and return list of feeds with optional group names.

    Supports multi-level nesting (3+ levels flatten to "Parent / Child" group names).
    Handles BOM-prefixed content gracefully.
    """
    content = content.lstrip("\ufeff")
    feeds: list[OpmlFeed] = []
    root = ET.fromstring(content)
    body = root.find("body")
    if body is None:
        return feeds

    def _walk(element: ET.Element, group_parts: list[str]) -> None:
        for outline in element:
            xml_url = outline.get("xmlUrl")
            if xml_url:
                group_name = " / ".join(group_parts) if group_parts else None
                feeds.append(
                    OpmlFeed(
                        title=outline.get("title") or outline.get("text") or xml_url,
                        url=xml_url,
                        group=group_name,
                        site_url=outline.get("htmlUrl"),
                        description=outline.get("description"),
                    )
                )
            else:
                name = outline.get("title") or outline.get("text") or "Unnamed"
                _walk(outline, group_parts + [name])

    _walk(body, [])
    return feeds


def generate_opml(feeds_with_groups: list[dict]) -> str:
    """Generate OPML 2.0 XML from feeds.

    Each dict should have keys 'feed' (Feed model instance) and 'group_name' (str | None).
    """
    opml = ET.Element("opml", version="2.0")
    head = ET.SubElement(opml, "head")
    ET.SubElement(head, "title").text = "RSS Reader Subscriptions"
    ET.SubElement(head, "dateCreated").text = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S %z"
    )
    body = ET.SubElement(opml, "body")

    grouped: dict[str, list] = {}
    ungrouped: list = []
    for item in feeds_with_groups:
        gname = item["group_name"]
        if gname:
            grouped.setdefault(gname, []).append(item["feed"])
        else:
            ungrouped.append(item["feed"])

    for feed in ungrouped:
        _add_feed_outline(body, feed)

    for group_name, group_feeds in grouped.items():
        group_el = ET.SubElement(body, "outline", text=group_name, title=group_name)
        for feed in group_feeds:
            _add_feed_outline(group_el, feed)

    raw_xml = ET.tostring(opml, encoding="unicode", xml_declaration=True)
    return xml.dom.minidom.parseString(raw_xml).toprettyxml(indent="  ")


def _add_feed_outline(parent: ET.Element, feed: Feed) -> None:
    attrs = {
        "type": "rss",
        "text": feed.title,
        "title": feed.title,
        "xmlUrl": feed.url,
    }
    if feed.site_url:
        attrs["htmlUrl"] = feed.site_url
    if feed.description:
        attrs["description"] = feed.description
    ET.SubElement(parent, "outline", **attrs)


async def create_feed_from_opml(
    session: AsyncSession, user_id: str, opml_feed: OpmlFeed, group_id: str | None
) -> Feed | None:
    """Create a Feed record directly from OPML metadata, skipping HTTP fetch.

    Returns None if a feed with the same URL already exists for this user.
    """
    uid = uuid.UUID(user_id)

    existing = await session.execute(
        select(Feed).where(and_(Feed.user_id == uid, Feed.url == opml_feed.url))
    )
    if existing.scalar_one_or_none():
        return None

    domain = ""
    for candidate_url in [opml_feed.site_url, opml_feed.url]:
        if candidate_url:
            parsed = urlparse(candidate_url)
            if parsed.netloc:
                domain = parsed.netloc
                break

    favicon_url = (
        f"https://www.google.com/s2/favicons?domain={domain}&sz=32" if domain else None
    )

    feed = Feed(
        user_id=uid,
        url=opml_feed.url,
        title=opml_feed.title,
        site_url=opml_feed.site_url,
        description=opml_feed.description,
        favicon_url=favicon_url,
        group_id=uuid.UUID(group_id) if group_id else None,
        status="active",
        feed_type="rss",
    )
    session.add(feed)
    return feed
