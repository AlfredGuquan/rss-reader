import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class Entry(Base, UUIDMixin):
    __tablename__ = "entries"
    __table_args__ = (
        UniqueConstraint("feed_id", "guid", name="uq_entry_feed_guid"),
        Index("ix_entries_simhash_title", "simhash_title"),
        Index("ix_entries_duplicate_of_id", "duplicate_of_id"),
    )

    feed_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("feeds.id", ondelete="CASCADE"), nullable=False
    )
    guid: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_fetched: Mapped[bool] = mapped_column(default=False)
    content_fetch_status: Mapped[str] = mapped_column(String, default="pending", server_default="pending")
    content_fetch_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_fetch_retries: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    extraction_method: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    published_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    extra_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    simhash_title: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    simhash_content: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    duplicate_of_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("entries.id", ondelete="SET NULL"), nullable=True
    )

    feed: Mapped["Feed"] = relationship(back_populates="entries")
    user_states: Mapped[list["UserEntryState"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )
    duplicate_of: Mapped[Optional["Entry"]] = relationship(
        remote_side="Entry.id", foreign_keys=[duplicate_of_id]
    )
