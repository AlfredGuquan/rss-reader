from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse
from app.services import group_service

router = APIRouter(prefix="/api/groups", tags=["groups"])


def _group_to_response(group) -> GroupResponse:
    return GroupResponse(
        id=str(group.id),
        user_id=str(group.user_id),
        name=group.name,
        sort_order=group.sort_order,
        created_at=group.created_at,
    )


@router.post("", response_model=GroupResponse, status_code=201)
async def create_group(data: GroupCreate, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    group = await group_service.create_group(db, user_id, data.name)
    return _group_to_response(group)


@router.get("", response_model=list[GroupResponse])
async def list_groups(db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    groups = await group_service.get_groups(db, user_id)
    return [_group_to_response(g) for g in groups]


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str, data: GroupUpdate, db: AsyncSession = Depends(get_db)
):
    user_id = settings.default_user_id
    group = await group_service.update_group(db, user_id, group_id, data.name)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return _group_to_response(group)


@router.delete("/{group_id}", status_code=204)
async def delete_group(group_id: str, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    deleted = await group_service.delete_group(db, user_id, group_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Group not found")
