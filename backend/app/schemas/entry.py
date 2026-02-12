from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EntryResponse(BaseModel):
    id: str
    feed_id: str
    guid: str
    title: str
    url: str
    author: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    content_fetched: bool
    published_at: datetime
    created_at: datetime
    is_read: bool = False
    is_starred: bool = False
    extra_metadata: Optional[dict] = None
    feed_title: Optional[str] = None
    feed_favicon_url: Optional[str] = None

    class Config:
        from_attributes = True


class MarkAllReadRequest(BaseModel):
    feed_id: str | None = None
    group_id: str | None = None


class EntryListResponse(BaseModel):
    items: list[EntryResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
