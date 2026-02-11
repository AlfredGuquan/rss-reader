from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EmailAccountCreate(BaseModel):
    email_address: str
    app_password: str
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    label: str = "Newsletters"


class EmailAccountResponse(BaseModel):
    id: str
    email_address: str
    imap_host: str
    imap_port: int
    label: str
    is_active: bool
    last_synced_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestConnectionRequest(BaseModel):
    email_address: str
    app_password: str
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
