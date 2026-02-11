"""Gmail OAuth newsletter aggregation service."""

import base64
import json
import logging
import re
import uuid
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.config import settings
from app.models.email_account import EmailAccount
from app.models.entry import Entry
from app.models.feed import Feed
from app.models.group import Group

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_oauth_flow() -> Flow:
    """Create OAuth flow from credentials file."""
    flow = Flow.from_client_secrets_file(
        settings.google_oauth_credentials_path,
        scopes=SCOPES,
        redirect_uri=settings.google_oauth_redirect_uri,
    )
    return flow


def get_auth_url() -> str:
    """Generate Google OAuth authorization URL."""
    flow = get_oauth_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
    )
    return auth_url


async def handle_oauth_callback(
    session: AsyncSession,
    user_id: str,
    code: str,
    gmail_label: str = "Newsletters",
) -> EmailAccount:
    """Exchange auth code for tokens, create or update EmailAccount."""
    import asyncio

    def _exchange_code():
        flow = get_oauth_flow()
        flow.fetch_token(code=code)
        return flow.credentials

    credentials = await asyncio.to_thread(_exchange_code)

    def _get_email(creds):
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        return profile["emailAddress"]

    email_address = await asyncio.to_thread(_get_email, credentials)

    uid = uuid.UUID(user_id)
    result = await session.execute(
        select(EmailAccount).where(
            and_(EmailAccount.user_id == uid, EmailAccount.email_address == email_address)
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.oauth_refresh_token = credentials.refresh_token or existing.oauth_refresh_token
        existing.oauth_access_token = credentials.token
        existing.oauth_token_expires_at = credentials.expiry
        existing.gmail_label = gmail_label
        existing.is_active = True
        existing.last_error = None
        await session.commit()
        await session.refresh(existing)
        return existing

    account = EmailAccount(
        user_id=uid,
        email_address=email_address,
        oauth_refresh_token=credentials.refresh_token,
        oauth_access_token=credentials.token,
        oauth_token_expires_at=credentials.expiry,
        gmail_label=gmail_label,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account


async def get_email_accounts(session: AsyncSession, user_id: str) -> list[EmailAccount]:
    uid = uuid.UUID(user_id)
    result = await session.execute(
        select(EmailAccount).where(EmailAccount.user_id == uid)
    )
    return list(result.scalars().all())


async def delete_email_account(session: AsyncSession, user_id: str, account_id: str) -> bool:
    uid = uuid.UUID(user_id)
    aid = uuid.UUID(account_id)
    result = await session.execute(
        select(EmailAccount).where(
            and_(EmailAccount.id == aid, EmailAccount.user_id == uid)
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        return False
    await session.delete(account)
    await session.commit()
    return True


async def _get_or_create_newsletters_group(session: AsyncSession, user_id: uuid.UUID) -> Group:
    """Find or create the 'Newsletters' group."""
    result = await session.execute(
        select(Group).where(and_(Group.user_id == user_id, Group.name == "Newsletters"))
    )
    group = result.scalar_one_or_none()
    if group:
        return group

    group = Group(user_id=user_id, name="Newsletters")
    session.add(group)
    await session.flush()
    return group


async def _get_or_create_newsletter_feed(
    session: AsyncSession,
    user_id: uuid.UUID,
    sender_email: str,
    sender_name: str,
    group_id: uuid.UUID,
    account_id: uuid.UUID,
) -> Feed:
    """Find or create a feed for a newsletter sender."""
    result = await session.execute(
        select(Feed).where(
            and_(
                Feed.user_id == user_id,
                Feed.url == sender_email,
                Feed.feed_type == "newsletter",
            )
        )
    )
    feed = result.scalar_one_or_none()
    if feed:
        return feed

    feed = Feed(
        user_id=user_id,
        url=sender_email,
        title=sender_name or sender_email,
        feed_type="newsletter",
        group_id=group_id,
        email_account_id=account_id,
    )
    session.add(feed)
    await session.flush()
    return feed


def _get_gmail_credentials(account: EmailAccount) -> Credentials:
    """Build Credentials object from stored tokens, auto-refresh if expired."""
    with open(settings.google_oauth_credentials_path) as f:
        client_config = json.load(f)["installed"]

    creds = Credentials(
        token=account.oauth_access_token,
        refresh_token=account.oauth_refresh_token,
        token_uri=client_config["token_uri"],
        client_id=client_config["client_id"],
        client_secret=client_config["client_secret"],
        scopes=SCOPES,
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return creds


def _extract_with_preference(payload: dict) -> tuple[str, bool]:
    """Recursively extract body from Gmail payload, returning (content, is_html).

    Collects all candidates from MIME parts and prefers HTML over plain text,
    fixing the bug where text/plain in multipart/alternative was returned early.
    """
    mime_type = payload.get("mimeType", "")

    if mime_type == "text/html":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace"), True

    parts = payload.get("parts", [])
    if parts:
        html_candidates: list[str] = []
        plain_candidates: list[str] = []
        for part in parts:
            result, is_html = _extract_with_preference(part)
            if result:
                (html_candidates if is_html else plain_candidates).append(result)
        if html_candidates:
            return html_candidates[0], True
        if plain_candidates:
            return plain_candidates[0], False

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            return f"<pre>{text}</pre>", False

    return "", False


def _extract_html_from_payload(payload: dict) -> str:
    """Recursively extract HTML body from Gmail API message payload."""
    content, _ = _extract_with_preference(payload)
    return content


def _extract_cid_images(payload: dict, service, user_id: str, message_id: str) -> dict[str, str]:
    """Extract CID-referenced inline images from message parts."""
    cid_map = {}
    parts = payload.get("parts", [])

    for part in parts:
        headers = {h["name"].lower(): h["value"] for h in part.get("headers", [])}
        content_id = headers.get("content-id", "")
        mime_type = part.get("mimeType", "")

        if content_id and mime_type.startswith("image/"):
            cid = content_id.strip("<>")
            attachment_id = part.get("body", {}).get("attachmentId")

            if attachment_id:
                attachment = service.users().messages().attachments().get(
                    userId=user_id, messageId=message_id, id=attachment_id
                ).execute()
                data = attachment.get("data", "")
                if data:
                    cid_map[cid] = f"data:{mime_type};base64,{data}"

        nested = _extract_cid_images(part, service, user_id, message_id)
        cid_map.update(nested)

    return cid_map


def _replace_cid_references(html: str, cid_map: dict[str, str]) -> str:
    """Replace cid:xxx references in HTML with data URIs."""
    for cid, data_uri in cid_map.items():
        html = html.replace(f"cid:{cid}", data_uri)
    return html


def _sanitize_email_html(html: str) -> str:
    """Remove dangerous elements from email HTML while preserving layout."""
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'\s+on\w+\s*=\s*"[^"]*"', "", html, flags=re.IGNORECASE)
    html = re.sub(r"\s+on\w+\s*=\s*'[^']*'", "", html, flags=re.IGNORECASE)
    html = re.sub(
        r'<img[^>]*(?:width\s*=\s*["\']?1["\']?\s+height\s*=\s*["\']?1["\']?|height\s*=\s*["\']?1["\']?\s+width\s*=\s*["\']?1["\']?)[^>]*/?>',
        "", html, flags=re.IGNORECASE
    )
    return html


def _parse_sender_from_header(from_header: str) -> tuple[str, str]:
    """Parse From header into (name, email)."""
    if "<" in from_header and ">" in from_header:
        name = from_header.split("<")[0].strip().strip('"')
        addr = from_header.split("<")[1].split(">")[0].strip()
        return name, addr
    return "", from_header.strip()


async def sync_newsletters(session: AsyncSession, account: EmailAccount) -> int:
    """Sync newsletters from Gmail API. Returns count of new entries."""
    import asyncio

    uid = account.user_id

    def _fetch_from_gmail():
        creds = _get_gmail_credentials(account)
        service = build("gmail", "v1", credentials=creds)

        updated_tokens = None
        if creds.token != account.oauth_access_token:
            updated_tokens = {
                "access_token": creds.token,
                "expires_at": creds.expiry,
            }

        # Resolve label name to label ID (required for nested labels like "Cora/Newsletter")
        label_id = None
        labels_response = service.users().labels().list(userId="me").execute()
        for lbl in labels_response.get("labels", []):
            if lbl["name"] == account.gmail_label:
                label_id = lbl["id"]
                break

        since_date = account.last_synced_at or (datetime.utcnow() - timedelta(days=7))
        date_str = since_date.strftime("%Y/%m/%d")
        date_query = f"after:{date_str}"

        messages_data = []
        list_kwargs = {"userId": "me", "q": date_query, "maxResults": 50}
        if label_id:
            list_kwargs["labelIds"] = [label_id]
        result = service.users().messages().list(**list_kwargs).execute()
        message_refs = result.get("messages", [])

        for msg_ref in message_refs:
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"], format="full"
            ).execute()

            payload = msg.get("payload", {})
            headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}

            html_body = _extract_html_from_payload(payload)

            cid_map = _extract_cid_images(payload, service, "me", msg_ref["id"])
            if cid_map and html_body:
                html_body = _replace_cid_references(html_body, cid_map)

            if html_body:
                html_body = _sanitize_email_html(html_body)

            messages_data.append({
                "message_id": headers.get("message-id", msg_ref["id"]),
                "from": headers.get("from", ""),
                "subject": headers.get("subject", "No Subject"),
                "date": headers.get("date", ""),
                "html_body": html_body,
            })

        return messages_data, updated_tokens

    try:
        messages_data, updated_tokens = await asyncio.to_thread(_fetch_from_gmail)

        if updated_tokens:
            account.oauth_access_token = updated_tokens["access_token"]
            account.oauth_token_expires_at = updated_tokens["expires_at"]
    except Exception as exc:
        account.last_error = str(exc)
        await session.commit()
        logger.error("Failed to sync newsletters for %s: %s", account.email_address, exc)
        return 0

    group = await _get_or_create_newsletters_group(session, uid)
    new_count = 0

    for msg_data in messages_data:
        try:
            message_id = msg_data["message_id"]
            if not message_id:
                continue

            sender_name, sender_email_addr = _parse_sender_from_header(msg_data["from"])
            subject = msg_data["subject"]

            date_str = msg_data["date"]
            try:
                published_at = parsedate_to_datetime(date_str)
                published_at = published_at.replace(tzinfo=None)
            except Exception:
                published_at = datetime.utcnow()

            feed = await _get_or_create_newsletter_feed(
                session, uid, sender_email_addr, sender_name, group.id, account.id
            )

            content = msg_data["html_body"]

            stmt = (
                sqlite_insert(Entry)
                .values(
                    feed_id=feed.id,
                    guid=message_id,
                    title=subject,
                    url="",
                    author=sender_name or sender_email_addr,
                    summary=subject,
                    content=content,
                    content_fetched=True,
                    published_at=published_at,
                )
                .on_conflict_do_nothing(index_elements=["feed_id", "guid"])
            )
            result = await session.execute(stmt)
            if result.rowcount > 0:
                new_count += 1
        except Exception as exc:
            logger.warning("Failed to process email: %s", exc)
            continue

    account.last_synced_at = datetime.utcnow()
    account.last_error = None
    await session.commit()

    logger.info("Synced %d new newsletters for %s", new_count, account.email_address)
    return new_count


async def refetch_plain_text_entries(session: AsyncSession, account: EmailAccount) -> int:
    """Re-fetch HTML for entries stored as plain text <pre> blocks."""
    import asyncio

    result = await session.execute(
        select(Entry)
        .join(Feed, Entry.feed_id == Feed.id)
        .where(
            and_(
                Feed.email_account_id == account.id,
                Feed.feed_type == "newsletter",
                Entry.content.like("<pre>%"),
            )
        )
    )
    entries = list(result.scalars().all())
    if not entries:
        return 0

    def _refetch_from_gmail(message_ids: list[str]) -> dict[str, str]:
        creds = _get_gmail_credentials(account)
        service = build("gmail", "v1", credentials=creds)
        results = {}
        for msg_id in message_ids:
            try:
                search = service.users().messages().list(
                    userId="me", q=f"rfc822msgid:{msg_id}", maxResults=1
                ).execute()
                refs = search.get("messages", [])
                if not refs:
                    continue
                msg = service.users().messages().get(
                    userId="me", id=refs[0]["id"], format="full"
                ).execute()
                payload = msg.get("payload", {})
                html_body = _extract_html_from_payload(payload)
                if html_body and not html_body.startswith("<pre>"):
                    cid_map = _extract_cid_images(payload, service, "me", refs[0]["id"])
                    if cid_map:
                        html_body = _replace_cid_references(html_body, cid_map)
                    html_body = _sanitize_email_html(html_body)
                    results[msg_id] = html_body
            except Exception as exc:
                logger.warning("Failed to refetch message %s: %s", msg_id, exc)
        return results

    message_ids = [e.guid for e in entries]
    updated_html = await asyncio.to_thread(_refetch_from_gmail, message_ids)

    updated_count = 0
    for entry in entries:
        if entry.guid in updated_html:
            entry.content = updated_html[entry.guid]
            updated_count += 1

    await session.commit()
    logger.info("Refetched %d/%d plain-text entries for %s", updated_count, len(entries), account.email_address)
    return updated_count


async def sync_all_newsletters_task():
    """Scheduled task to sync all active email accounts."""
    from app.database import async_session

    async with async_session() as session:
        result = await session.execute(
            select(EmailAccount).where(EmailAccount.is_active == True)  # noqa: E712
        )
        accounts = result.scalars().all()

    for account in accounts:
        async with async_session() as session:
            merged = await session.merge(account)
            try:
                await sync_newsletters(session, merged)
            except Exception as exc:
                logger.error("Failed to sync account %s: %s", merged.email_address, exc)
