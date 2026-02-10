"""OPML file parser for importing feed subscriptions."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass
class OpmlFeed:
    title: str
    url: str
    group: str | None


def parse_opml(content: str) -> list[OpmlFeed]:
    """Parse OPML XML string and return list of feeds with optional group names."""
    feeds: list[OpmlFeed] = []
    root = ET.fromstring(content)
    body = root.find("body")
    if body is None:
        return feeds

    for outline in body:
        xml_url = outline.get("xmlUrl")
        if xml_url:
            feeds.append(
                OpmlFeed(
                    title=outline.get("title") or outline.get("text") or xml_url,
                    url=xml_url,
                    group=None,
                )
            )
        else:
            group_name = outline.get("title") or outline.get("text") or "Unnamed"
            for child in outline:
                child_url = child.get("xmlUrl")
                if child_url:
                    feeds.append(
                        OpmlFeed(
                            title=child.get("title")
                            or child.get("text")
                            or child_url,
                            url=child_url,
                            group=group_name,
                        )
                    )
    return feeds
