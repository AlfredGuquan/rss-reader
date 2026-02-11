import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, TimestampMixin


class EmailAccount(Base, UUIDMixin, TimestampMixin):
    """Gmail IMAP connection for newsletter aggregation.

    WARNING: app_password stored in plaintext - acceptable for single-user MVP only.
    """
    __tablename__ = "email_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    email_address: Mapped[str] = mapped_column(String, nullable=False)
    app_password: Mapped[str] = mapped_column(String, nullable=False)
    imap_host: Mapped[str] = mapped_column(String, default="imap.gmail.com", server_default="imap.gmail.com")
    imap_port: Mapped[int] = mapped_column(Integer, default=993, server_default="993")
    label: Mapped[str] = mapped_column(String, default="Newsletters", server_default="Newsletters")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
