"""Tests for platform URL detection and RSS feed URL conversion."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.platform_detector import (
    detect_reddit,
    detect_youtube,
    detect_platform,
    PlatformResult,
)


class TestDetectReddit:
    def test_subreddit_basic(self):
        result = detect_reddit("https://www.reddit.com/r/python")
        assert result is not None
        assert result.platform == "reddit"
        assert result.feed_url == "https://www.reddit.com/r/python/.rss"
        assert result.identifier == "python"
        assert result.title_hint == "r/python"
        assert result.site_url == "https://www.reddit.com/r/python"

    def test_subreddit_with_trailing_slash(self):
        result = detect_reddit("https://www.reddit.com/r/python/")
        assert result is not None
        assert result.feed_url == "https://www.reddit.com/r/python/.rss"

    def test_subreddit_with_sort(self):
        result = detect_reddit("https://www.reddit.com/r/python/top")
        assert result is not None
        assert result.feed_url == "https://www.reddit.com/r/python/top/.rss"

    def test_subreddit_with_sort_and_query(self):
        result = detect_reddit("https://www.reddit.com/r/python/top?t=day")
        assert result is not None
        assert result.feed_url == "https://www.reddit.com/r/python/top/.rss?t=day"

    def test_multi_subreddit(self):
        result = detect_reddit("https://www.reddit.com/r/python+rust")
        assert result is not None
        assert result.feed_url == "https://www.reddit.com/r/python+rust/.rss"
        assert result.identifier == "python+rust"

    def test_user_page(self):
        result = detect_reddit("https://www.reddit.com/user/spez")
        assert result is not None
        assert result.platform == "reddit"
        assert result.feed_url == "https://www.reddit.com/user/spez/.rss"
        assert result.identifier == "u/spez"
        assert result.title_hint == "u/spez"

    def test_user_page_with_sort(self):
        result = detect_reddit("https://www.reddit.com/user/spez/top")
        assert result is not None
        assert result.feed_url == "https://www.reddit.com/user/spez/top/.rss"

    def test_old_reddit(self):
        result = detect_reddit("https://old.reddit.com/r/python")
        assert result is not None
        assert result.feed_url == "https://www.reddit.com/r/python/.rss"

    def test_reddit_without_www(self):
        result = detect_reddit("https://reddit.com/r/python")
        assert result is not None
        assert result.feed_url == "https://www.reddit.com/r/python/.rss"

    def test_non_reddit_url(self):
        result = detect_reddit("https://news.ycombinator.com")
        assert result is None

    def test_reddit_homepage(self):
        result = detect_reddit("https://www.reddit.com/")
        assert result is None


class TestDetectYoutube:
    @pytest.mark.asyncio
    async def test_channel_id_short(self):
        result = await detect_youtube("https://www.youtube.com/channel/UCvjgXvBlFQRa4azq")
        assert result is not None
        assert result.platform == "youtube"
        assert result.identifier == "UCvjgXvBlFQRa4azq"

    @pytest.mark.asyncio
    async def test_channel_id_valid(self):
        result = await detect_youtube("https://www.youtube.com/channel/UCxxxYYYzzz123")
        assert result is not None
        assert result.platform == "youtube"
        assert result.feed_url == "https://www.youtube.com/feeds/videos.xml?channel_id=UCxxxYYYzzz123"
        assert result.identifier == "UCxxxYYYzzz123"

    @pytest.mark.asyncio
    async def test_handle_with_mock(self):
        mock_response = MagicMock()
        mock_response.text = '<meta itemprop="channelId" content="UCtest123abc">'
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.platform_detector.httpx.AsyncClient", return_value=mock_client):
            result = await detect_youtube("https://www.youtube.com/@testchannel")

        assert result is not None
        assert result.platform == "youtube"
        assert result.feed_url == "https://www.youtube.com/feeds/videos.xml?channel_id=UCtest123abc"
        assert result.title_hint == "@testchannel"

    @pytest.mark.asyncio
    async def test_handle_fetch_failure(self):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.platform_detector.httpx.AsyncClient", return_value=mock_client):
            result = await detect_youtube("https://www.youtube.com/@testchannel")

        assert result is None

    @pytest.mark.asyncio
    async def test_non_youtube_url(self):
        result = await detect_youtube("https://vimeo.com/channels/staffpicks")
        assert result is None

    @pytest.mark.asyncio
    async def test_youtube_homepage(self):
        result = await detect_youtube("https://www.youtube.com/")
        assert result is None

    @pytest.mark.asyncio
    async def test_custom_url_with_mock(self):
        mock_response = MagicMock()
        mock_response.text = '"browseId":"UCcustom456def"'
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.platform_detector.httpx.AsyncClient", return_value=mock_client):
            result = await detect_youtube("https://www.youtube.com/c/testchannel")

        assert result is not None
        assert result.identifier == "UCcustom456def"


class TestDetectPlatform:
    @pytest.mark.asyncio
    async def test_reddit_url(self):
        result = await detect_platform("https://www.reddit.com/r/python")
        assert result is not None
        assert result.platform == "reddit"

    @pytest.mark.asyncio
    async def test_youtube_channel_url(self):
        result = await detect_platform("https://www.youtube.com/channel/UCtest123abc")
        assert result is not None
        assert result.platform == "youtube"

    @pytest.mark.asyncio
    async def test_regular_url(self):
        result = await detect_platform("https://example.com/feed.xml")
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_string(self):
        result = await detect_platform("")
        assert result is None
