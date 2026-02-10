from datetime import datetime

from pydantic import BaseModel


class GroupCreate(BaseModel):
    name: str


class GroupUpdate(BaseModel):
    name: str


class GroupReorder(BaseModel):
    group_ids: list[str]


class GroupResponse(BaseModel):
    id: str
    user_id: str
    name: str
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True
