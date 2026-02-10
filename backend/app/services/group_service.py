"""CRUD operations for feed groups."""

import uuid

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.feed import Feed


async def create_group(session: AsyncSession, user_id: str, name: str) -> Group:
    uid = uuid.UUID(user_id)
    result = await session.execute(
        select(func.coalesce(func.max(Group.sort_order), -1)).where(
            Group.user_id == uid
        )
    )
    max_order = result.scalar()

    group = Group(user_id=uid, name=name, sort_order=max_order + 1)
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return group


async def get_groups(session: AsyncSession, user_id: str) -> list[Group]:
    uid = uuid.UUID(user_id)
    result = await session.execute(
        select(Group).where(Group.user_id == uid).order_by(Group.sort_order)
    )
    return list(result.scalars().all())


async def get_group(
    session: AsyncSession, user_id: str, group_id: str
) -> Group | None:
    uid = uuid.UUID(user_id)
    gid = uuid.UUID(group_id)
    result = await session.execute(
        select(Group).where(and_(Group.id == gid, Group.user_id == uid))
    )
    return result.scalar_one_or_none()


async def update_group(
    session: AsyncSession, user_id: str, group_id: str, name: str
) -> Group | None:
    group = await get_group(session, user_id, group_id)
    if not group:
        return None
    group.name = name
    await session.commit()
    await session.refresh(group)
    return group


async def reorder_groups(
    session: AsyncSession, user_id: str, group_ids: list[str]
) -> list[Group]:
    uid = uuid.UUID(user_id)
    for idx, gid_str in enumerate(group_ids):
        gid = uuid.UUID(gid_str)
        result = await session.execute(
            select(Group).where(and_(Group.id == gid, Group.user_id == uid))
        )
        group = result.scalar_one_or_none()
        if group:
            group.sort_order = idx
    await session.commit()
    return await get_groups(session, user_id)


async def delete_group(
    session: AsyncSession, user_id: str, group_id: str
) -> bool:
    group = await get_group(session, user_id, group_id)
    if not group:
        return False
    uid = uuid.UUID(user_id)
    gid = uuid.UUID(group_id)
    feeds_result = await session.execute(
        select(Feed).where(and_(Feed.group_id == gid, Feed.user_id == uid))
    )
    for feed in feeds_result.scalars().all():
        feed.group_id = None
    await session.delete(group)
    await session.commit()
    return True
