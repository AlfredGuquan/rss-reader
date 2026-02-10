from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FeedCreate(BaseModel):
    url: str
    group_id: Optional[str] = None


class FeedUpdate(BaseModel):
    title: Optional[str] = None
    group_id: Optional[str] = None


class FeedResponse(BaseModel):
    id: str
    user_id: str
    url: str
    title: str
    site_url: Optional[str] = None
    description: Optional[str] = None
    favicon_url: Optional[str] = None
    group_id: Optional[str] = None
    fetch_interval_minutes: int
    last_fetched_at: Optional[datetime] = None
    status: str
    error_count: int
    unread_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeedDiscoverResponse(BaseModel):
    feeds: list[dict]
