"""Tests for SimHash-based article deduplication."""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.models.user import User
from app.models.feed import Feed
from app.models.entry import Entry
from app.models.group import Group
from app.services.dedup_service import compute_simhash, hamming_distance, find_duplicate


@pytest.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def on_connect(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def sample_feeds(db_session: AsyncSession):
    user = User(id=uuid.uuid4(), username="testuser")
    db_session.add(user)
    await db_session.flush()

    group = Group(id=uuid.uuid4(), name="Tech", sort_order=0, user_id=user.id)
    db_session.add(group)
    await db_session.flush()

    feed_a = Feed(
        id=uuid.uuid4(),
        title="Feed A",
        url="https://feed-a.example.com/rss",
        group_id=group.id,
        user_id=user.id,
        status="active",
    )
    feed_b = Feed(
        id=uuid.uuid4(),
        title="Feed B",
        url="https://feed-b.example.com/rss",
        group_id=group.id,
        user_id=user.id,
        status="active",
    )
    db_session.add_all([feed_a, feed_b])
    await db_session.flush()
    return feed_a, feed_b


class TestComputeSimhash:
    def test_returns_16_char_hex(self):
        result = compute_simhash("Hello World")
        assert len(result) == 16
        int(result, 16)  # should not raise

    def test_deterministic(self):
        assert compute_simhash("test input") == compute_simhash("test input")

    def test_different_inputs_differ(self):
        h1 = compute_simhash("Breaking news: earthquake hits California")
        h2 = compute_simhash("Python 3.13 released with new features")
        assert h1 != h2


class TestHammingDistance:
    def test_identical(self):
        h = compute_simhash("test")
        assert hamming_distance(h, h) == 0

    def test_similar_titles_low_distance(self):
        h1 = compute_simhash("Breaking News: Major earthquake hits California coast")
        h2 = compute_simhash("Breaking News: Major earthquake strikes California coast")
        assert hamming_distance(h1, h2) <= 10

    def test_different_titles_high_distance(self):
        h1 = compute_simhash("Breaking News: Major earthquake hits California coast")
        h2 = compute_simhash("Python 3.13 released with new features and improvements")
        assert hamming_distance(h1, h2) > 10

    def test_max_distance_is_64(self):
        assert hamming_distance("0000000000000000", "ffffffffffffffff") == 64


class TestFindDuplicate:
    @pytest.mark.asyncio
    async def test_finds_duplicate_across_feeds(self, db_session, sample_feeds):
        feed_a, feed_b = sample_feeds
        now = datetime.utcnow()
        title = "Breaking News: Major earthquake hits California coast"
        simhash = compute_simhash(title)

        entry_a = Entry(
            id=uuid.uuid4(),
            feed_id=feed_a.id,
            guid="entry-a-1",
            title=title,
            url="https://feed-a.example.com/1",
            published_at=now,
            simhash_title=simhash,
        )
        db_session.add(entry_a)
        await db_session.flush()

        similar_title = "Breaking News: Major earthquake strikes California coast"
        similar_hash = compute_simhash(similar_title)
        entry_b_id = uuid.uuid4()

        result = await find_duplicate(
            db_session, entry_b_id, similar_hash, now + timedelta(hours=1), feed_b.id
        )
        assert result == str(entry_a.id)

    @pytest.mark.asyncio
    async def test_no_duplicate_for_different_titles(self, db_session, sample_feeds):
        feed_a, feed_b = sample_feeds
        now = datetime.utcnow()

        entry_a = Entry(
            id=uuid.uuid4(),
            feed_id=feed_a.id,
            guid="entry-a-1",
            title="Breaking News: Major earthquake hits California",
            url="https://feed-a.example.com/1",
            published_at=now,
            simhash_title=compute_simhash("Breaking News: Major earthquake hits California"),
        )
        db_session.add(entry_a)
        await db_session.flush()

        different_hash = compute_simhash("Python 3.13 released with new features and improvements")
        result = await find_duplicate(
            db_session, uuid.uuid4(), different_hash, now, feed_b.id
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_respects_time_window(self, db_session, sample_feeds):
        feed_a, feed_b = sample_feeds
        now = datetime.utcnow()
        title = "Breaking News: Major earthquake hits California coast"
        simhash = compute_simhash(title)

        entry_a = Entry(
            id=uuid.uuid4(),
            feed_id=feed_a.id,
            guid="entry-a-1",
            title=title,
            url="https://feed-a.example.com/1",
            published_at=now - timedelta(days=5),
            simhash_title=simhash,
        )
        db_session.add(entry_a)
        await db_session.flush()

        similar_hash = compute_simhash("Breaking News: Major earthquake strikes California coast")
        result = await find_duplicate(
            db_session, uuid.uuid4(), similar_hash, now, feed_b.id
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_skips_same_feed(self, db_session, sample_feeds):
        feed_a, _ = sample_feeds
        now = datetime.utcnow()
        title = "Breaking News: Major earthquake hits California coast"
        simhash = compute_simhash(title)

        entry_a = Entry(
            id=uuid.uuid4(),
            feed_id=feed_a.id,
            guid="entry-a-1",
            title=title,
            url="https://feed-a.example.com/1",
            published_at=now,
            simhash_title=simhash,
        )
        db_session.add(entry_a)
        await db_session.flush()

        result = await find_duplicate(
            db_session, uuid.uuid4(), simhash, now, feed_a.id
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_skips_entries_already_marked_duplicate(self, db_session, sample_feeds):
        feed_a, feed_b = sample_feeds
        now = datetime.utcnow()
        title = "Breaking News: Major earthquake hits California coast"
        simhash = compute_simhash(title)

        canonical = Entry(
            id=uuid.uuid4(),
            feed_id=feed_a.id,
            guid="canonical",
            title=title,
            url="https://feed-a.example.com/1",
            published_at=now,
            simhash_title=simhash,
        )
        db_session.add(canonical)
        await db_session.flush()

        already_dup = Entry(
            id=uuid.uuid4(),
            feed_id=feed_b.id,
            guid="already-dup",
            title=title,
            url="https://feed-b.example.com/1",
            published_at=now,
            simhash_title=simhash,
            duplicate_of_id=canonical.id,
        )
        db_session.add(already_dup)
        await db_session.flush()

        # A third feed's entry should match canonical, not already_dup
        result = await find_duplicate(
            db_session, uuid.uuid4(), simhash, now, feed_a.id
        )
        # feed_a is the same feed as canonical, so it should find nothing
        # Let's test with a third feed scenario — we reuse feed_b but different id
        third_entry_id = uuid.uuid4()
        # The canonical is in feed_a, already_dup is in feed_b (marked as dup)
        # Querying from a "third" perspective with feed_id != feed_a and != feed_b
        # But we only have 2 feeds. Let's just verify already_dup is skipped:
        # Query from feed_a perspective — canonical is in feed_a so skipped, already_dup is marked so skipped
        result = await find_duplicate(
            db_session, third_entry_id, simhash, now, feed_a.id
        )
        assert result is None  # already_dup is skipped because it has duplicate_of_id set
