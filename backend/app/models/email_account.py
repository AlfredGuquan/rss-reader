import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, TimestampMixin


class EmailAccount(Base, UUIDMixin, TimestampMixin):
    """Gmail OAuth connection for newsletter aggregation."""
    __tablename__ = "email_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    email_address: Mapped[str] = mapped_column(String, nullable=False)
    oauth_refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    oauth_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    oauth_token_expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    gmail_label: Mapped[str] = mapped_column(String, default="Newsletters", server_default="Newsletters")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
