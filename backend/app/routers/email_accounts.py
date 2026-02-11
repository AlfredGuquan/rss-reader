from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.email_account import (
    EmailAccountCreate,
    EmailAccountResponse,
    TestConnectionRequest,
)
from app.services import email_service

router = APIRouter(prefix="/api/email-accounts", tags=["email-accounts"])


@router.post("", response_model=EmailAccountResponse, status_code=201)
async def connect_email(data: EmailAccountCreate, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    try:
        account = await email_service.create_email_account(
            db, user_id, data.model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return EmailAccountResponse(
        id=str(account.id),
        email_address=account.email_address,
        imap_host=account.imap_host,
        imap_port=account.imap_port,
        label=account.label,
        is_active=account.is_active,
        last_synced_at=account.last_synced_at,
        last_error=account.last_error,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


@router.get("", response_model=list[EmailAccountResponse])
async def list_email_accounts(db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    accounts = await email_service.get_email_accounts(db, user_id)
    return [
        EmailAccountResponse(
            id=str(a.id),
            email_address=a.email_address,
            imap_host=a.imap_host,
            imap_port=a.imap_port,
            label=a.label,
            is_active=a.is_active,
            last_synced_at=a.last_synced_at,
            last_error=a.last_error,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in accounts
    ]


@router.delete("/{account_id}", status_code=204)
async def disconnect_email(account_id: str, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    deleted = await email_service.delete_email_account(db, user_id, account_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Email account not found")


@router.post("/{account_id}/sync")
async def sync_email(account_id: str, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    accounts = await email_service.get_email_accounts(db, user_id)
    account = next((a for a in accounts if str(a.id) == account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")
    count = await email_service.sync_newsletters(db, account)
    return {"new_entries": count}


@router.post("/test")
async def test_connection(data: TestConnectionRequest):
    success, message = await email_service.test_connection(
        data.email_address, data.app_password, data.imap_host, data.imap_port
    )
    return {"success": success, "message": message}
