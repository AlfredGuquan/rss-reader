import re
from urllib.parse import urljoin

import httpx


async def discover_feeds(url: str) -> list[dict]:
    """Parse an HTML page to find RSS/Atom feed links."""
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "RSS Reader/1.0"})
            html = response.text
    except httpx.HTTPError:
        return []

    feeds = []
    link_pattern = re.compile(
        r'<link[^>]+type=["\']application/(rss|atom)\+xml["\'][^>]*/?>',
        re.IGNORECASE,
    )

    for match in link_pattern.finditer(html):
        tag = match.group(0)

        href_match = re.search(r'href=["\']([^"\']+)["\']', tag)
        if not href_match:
            continue
        href = href_match.group(1)
        feed_url = urljoin(url, href)

        title_match = re.search(r'title=["\']([^"\']+)["\']', tag)
        title = title_match.group(1) if title_match else feed_url

        feeds.append({"url": feed_url, "title": title})

    # Also try the reverse attribute order (type after href)
    link_pattern_alt = re.compile(
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/(rss|atom)\+xml["\'][^>]*/?>',
        re.IGNORECASE,
    )
    seen_urls = {f["url"] for f in feeds}
    for match in link_pattern_alt.finditer(html):
        href = match.group(1)
        feed_url = urljoin(url, href)
        if feed_url in seen_urls:
            continue
        seen_urls.add(feed_url)

        tag = match.group(0)
        title_match = re.search(r'title=["\']([^"\']+)["\']', tag)
        title = title_match.group(1) if title_match else feed_url

        feeds.append({"url": feed_url, "title": title})

    return feeds
