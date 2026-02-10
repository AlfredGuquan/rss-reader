import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class UserEntryState(Base, UUIDMixin):
    __tablename__ = "user_entry_states"
    __table_args__ = (
        UniqueConstraint("user_id", "entry_id", name="uq_user_entry_state"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    entry_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("entries.id", ondelete="CASCADE"), nullable=False
    )
    is_read: Mapped[bool] = mapped_column(default=False)
    is_starred: Mapped[bool] = mapped_column(default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    starred_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="entry_states")
    entry: Mapped["Entry"] = relationship(back_populates="user_states")
