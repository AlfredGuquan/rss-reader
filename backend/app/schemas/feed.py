from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


class FeedCreate(BaseModel):
    url: str
    group_id: Optional[str] = None


class FeedUpdate(BaseModel):
    title: Optional[str] = None
    group_id: Optional[str] = None
    status: Optional[str] = None
    fulltext_config: Optional[dict] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ("active", "paused"):
            raise ValueError("status must be 'active' or 'paused'")
        return v


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
    feed_type: str = "rss"
    fulltext_config: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeedDiscoverResponse(BaseModel):
    feeds: list[dict]
