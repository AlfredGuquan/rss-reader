from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.email_account import (
    EmailAccountResponse,
    OAuthCallbackRequest,
    OAuthInitResponse,
)
from app.services import email_service

router = APIRouter(prefix="/api/email-accounts", tags=["email-accounts"])


@router.post("/oauth/init", response_model=OAuthInitResponse)
async def oauth_init():
    auth_url = email_service.get_auth_url()
    return OAuthInitResponse(auth_url=auth_url)


@router.post("/oauth/callback", response_model=EmailAccountResponse)
async def oauth_callback(data: OAuthCallbackRequest, db: AsyncSession = Depends(get_db)):
    user_id = settings.default_user_id
    try:
        account = await email_service.handle_oauth_callback(
            db, user_id, data.code, data.gmail_label
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return EmailAccountResponse(
        id=str(account.id),
        email_address=account.email_address,
        gmail_label=account.gmail_label,
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
            gmail_label=a.gmail_label,
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


@router.post("/{account_id}/refetch")
async def refetch_email(account_id: str, db: AsyncSession = Depends(get_db)):
    """Re-fetch HTML for entries that were stored as plain text."""
    user_id = settings.default_user_id
    accounts = await email_service.get_email_accounts(db, user_id)
    account = next((a for a in accounts if str(a.id) == account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")
    count = await email_service.refetch_plain_text_entries(db, account)
    return {"updated_entries": count}
