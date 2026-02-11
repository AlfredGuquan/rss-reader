"""Newsletter IMAP aggregation service for Gmail."""

import asyncio
import email
import imaplib
import logging
import uuid
from datetime import datetime, timedelta
from email.header import decode_header
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.models.email_account import EmailAccount
from app.models.entry import Entry
from app.models.feed import Feed
from app.models.group import Group

logger = logging.getLogger(__name__)


def _decode_header_value(value: str) -> str:
    """Decode RFC 2047 encoded header."""
    if not value:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


async def test_connection(
    email_address: str,
    app_password: str,
    imap_host: str = "imap.gmail.com",
    imap_port: int = 993,
) -> tuple[bool, str]:
    """Test IMAP connection. Returns (success, message)."""
    def _connect():
        mail = imaplib.IMAP4_SSL(imap_host, imap_port)
        mail.login(email_address, app_password)
        mail.logout()
        return True

    try:
        await asyncio.to_thread(_connect)
        return True, "Connection successful"
    except Exception as exc:
        return False, str(exc)


async def create_email_account(
    session: AsyncSession,
    user_id: str,
    data: dict,
) -> EmailAccount:
    """Create email account after verifying connection."""
    success, msg = await test_connection(
        data["email_address"],
        data["app_password"],
        data.get("imap_host", "imap.gmail.com"),
        data.get("imap_port", 993),
    )
    if not success:
        raise ValueError(f"Connection failed: {msg}")

    account = EmailAccount(
        user_id=uuid.UUID(user_id),
        email_address=data["email_address"],
        app_password=data["app_password"],
        imap_host=data.get("imap_host", "imap.gmail.com"),
        imap_port=data.get("imap_port", 993),
        label=data.get("label", "Newsletters"),
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


def _extract_html_body(msg: email.message.Message) -> str:
    """Extract HTML body from email message."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/html":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace") if payload else ""
    return ""


def _parse_sender(from_header: str) -> tuple[str, str]:
    """Parse From header into (name, email)."""
    decoded = _decode_header_value(from_header)
    if "<" in decoded and ">" in decoded:
        name = decoded.split("<")[0].strip().strip('"')
        addr = decoded.split("<")[1].split(">")[0].strip()
        return name, addr
    return "", decoded.strip()


async def sync_newsletters(session: AsyncSession, account: EmailAccount) -> int:
    """Sync newsletters from IMAP. Returns count of new entries."""
    uid = account.user_id

    def _fetch_emails():
        mail = imaplib.IMAP4_SSL(account.imap_host, account.imap_port)
        mail.login(account.email_address, account.app_password)

        status, _ = mail.select(f'"{account.label}"')
        if status != "OK":
            mail.select("INBOX")

        since_date = account.last_synced_at or (datetime.utcnow() - timedelta(days=7))
        date_str = since_date.strftime("%d-%b-%Y")
        _, message_numbers = mail.search(None, f'(SINCE "{date_str}")')

        messages = []
        for num in message_numbers[0].split():
            if not num:
                continue
            _, msg_data = mail.fetch(num, "(RFC822)")
            if msg_data[0] is None:
                continue
            raw_email = msg_data[0][1]
            messages.append(raw_email)

        mail.logout()
        return messages

    try:
        raw_messages = await asyncio.to_thread(_fetch_emails)
    except Exception as exc:
        account.last_error = str(exc)
        await session.commit()
        logger.error("Failed to sync newsletters for %s: %s", account.email_address, exc)
        return 0

    group = await _get_or_create_newsletters_group(session, uid)
    new_count = 0

    for raw in raw_messages:
        try:
            msg = email.message_from_bytes(raw)
            message_id = msg.get("Message-ID", "")
            if not message_id:
                continue

            sender_name, sender_email_addr = _parse_sender(msg.get("From", ""))
            subject = _decode_header_value(msg.get("Subject", "No Subject"))

            date_header = msg.get("Date", "")
            try:
                from email.utils import parsedate_to_datetime
                published_at = parsedate_to_datetime(date_header)
                published_at = published_at.replace(tzinfo=None)
            except Exception:
                published_at = datetime.utcnow()

            feed = await _get_or_create_newsletter_feed(
                session, uid, sender_email_addr, sender_name, group.id, account.id
            )

            html_body = _extract_html_body(msg)
            content = None
            if html_body:
                try:
                    import trafilatura
                    content = await asyncio.to_thread(
                        trafilatura.extract, html_body,
                        include_links=True, include_images=True, output_format="html",
                    )
                except Exception:
                    content = html_body

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
