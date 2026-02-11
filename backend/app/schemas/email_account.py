from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class OAuthInitResponse(BaseModel):
    auth_url: str


class OAuthCallbackRequest(BaseModel):
    code: str
    gmail_label: str = "Newsletters"


class EmailAccountResponse(BaseModel):
    id: str
    email_address: str
    gmail_label: str
    is_active: bool
    last_synced_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
