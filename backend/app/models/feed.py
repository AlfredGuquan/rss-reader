import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Feed(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "feeds"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    site_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("groups.id"), nullable=True
    )
    fetch_interval_minutes: Mapped[int] = mapped_column(default=30)
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String, default="active")
    etag: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_modified_header: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    feed_type: Mapped[str] = mapped_column(String, default="rss", server_default="rss")
    email_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("email_accounts.id"), nullable=True)
    fulltext_config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_platform: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_identifier: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    filter_rules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="feeds")
    group: Mapped[Optional["Group"]] = relationship(back_populates="feeds")
    entries: Mapped[list["Entry"]] = relationship(
        back_populates="feed", cascade="all, delete-orphan"
    )
