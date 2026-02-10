import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User


async def seed_default_user(session: AsyncSession) -> None:
    default_id = uuid.UUID(settings.default_user_id)
    result = await session.execute(select(User).where(User.id == default_id))
    existing = result.scalar_one_or_none()
    if existing is None:
        user = User(id=default_id, username=settings.default_username)
        session.add(user)
        await session.commit()
