"""URL platform detection and RSS feed URL conversion."""

import re
import logging
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


@dataclass
class PlatformResult:
    platform: str | None  # "reddit", "youtube", or None
    feed_url: str  # The RSS feed URL to subscribe to
    identifier: str | None  # subreddit name, channel_id, etc.
    title_hint: str | None  # Suggested title
    site_url: str | None  # Original website URL


def detect_reddit(url: str) -> PlatformResult | None:
    """Detect Reddit URLs and convert to RSS feed URL.

    Supports:
    - /r/subreddit -> /r/subreddit/.rss
    - /r/sub1+sub2 -> /r/sub1+sub2/.rss
    - /user/username -> /user/username/.rss
    - /r/subreddit/top -> /r/subreddit/top/.rss
    """
    parsed = urlparse(url)
    if parsed.netloc not in ("www.reddit.com", "reddit.com", "old.reddit.com"):
        return None

    path = parsed.path.rstrip("/")

    subreddit_match = re.match(r"^(/r/[\w+]+)(/\w+)?$", path)
    if subreddit_match:
        base = subreddit_match.group(1)
        sort = subreddit_match.group(2) or ""
        feed_url = f"https://www.reddit.com{base}{sort}/.rss"

        identifier = base.lstrip("/r/")

        query = f"?{parsed.query}" if parsed.query else ""
        feed_url += query

        return PlatformResult(
            platform="reddit",
            feed_url=feed_url,
            identifier=identifier,
            title_hint=f"r/{identifier}",
            site_url=f"https://www.reddit.com{base}",
        )

    user_match = re.match(r"^/user/([\w-]+)(/\w+)?$", path)
    if user_match:
        username = user_match.group(1)
        sort = user_match.group(2) or ""
        return PlatformResult(
            platform="reddit",
            feed_url=f"https://www.reddit.com/user/{username}{sort}/.rss",
            identifier=f"u/{username}",
            title_hint=f"u/{username}",
            site_url=f"https://www.reddit.com/user/{username}",
        )

    return None


async def detect_youtube(url: str) -> PlatformResult | None:
    """Detect YouTube URLs and convert to RSS feed URL.

    Supports:
    - /@handle -> extract channel_id from page meta tag
    - /channel/UCxxxx -> direct channel_id extraction
    """
    parsed = urlparse(url)
    if parsed.netloc not in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        return None

    path = parsed.path.rstrip("/")

    # /channel/UCxxxx
    channel_match = re.match(r"^/channel/(UC[\w-]+)$", path)
    if channel_match:
        channel_id = channel_match.group(1)
        return PlatformResult(
            platform="youtube",
            feed_url=f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
            identifier=channel_id,
            title_hint=None,
            site_url=url,
        )

    # /@handle
    handle_match = re.match(r"^/@([\w.-]+)$", path)
    if handle_match:
        handle = handle_match.group(1)
        channel_id = await _fetch_youtube_channel_id(url)
        if channel_id:
            return PlatformResult(
                platform="youtube",
                feed_url=f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
                identifier=channel_id,
                title_hint=f"@{handle}",
                site_url=url,
            )
        return None

    # /c/customname
    custom_match = re.match(r"^/c/([\w.-]+)$", path)
    if custom_match:
        channel_id = await _fetch_youtube_channel_id(url)
        if channel_id:
            return PlatformResult(
                platform="youtube",
                feed_url=f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
                identifier=channel_id,
                title_hint=None,
                site_url=url,
            )
        return None

    return None


async def _fetch_youtube_channel_id(url: str) -> str | None:
    """Fetch a YouTube page and extract channel_id from meta tags or page source."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; RSS-Reader/1.0)",
            })
            response.raise_for_status()
            text = response.text

        meta_match = re.search(r'<meta\s+itemprop="channelId"\s+content="(UC[\w-]+)"', text)
        if meta_match:
            return meta_match.group(1)

        browse_match = re.search(r'"browseId"\s*:\s*"(UC[\w-]+)"', text)
        if browse_match:
            return browse_match.group(1)

        external_match = re.search(r'"externalId"\s*:\s*"(UC[\w-]+)"', text)
        if external_match:
            return external_match.group(1)

    except Exception as exc:
        logger.warning("Failed to fetch YouTube channel_id from %s: %s", url, exc)

    return None


async def detect_platform(url: str) -> PlatformResult | None:
    """Main entry point: detect platform from URL and return feed info."""
    result = detect_reddit(url)
    if result:
        return result

    result = await detect_youtube(url)
    if result:
        return result

    return None
