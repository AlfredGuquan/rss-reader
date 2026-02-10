import uuid
from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)

    feeds: Mapped[list["Feed"]] = relationship(back_populates="user")
    groups: Mapped[list["Group"]] = relationship(back_populates="user")
    entry_states: Mapped[list["UserEntryState"]] = relationship(back_populates="user")
