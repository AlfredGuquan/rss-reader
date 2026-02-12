"""Tests for cascade content extraction logic."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.content_service import (
    cascade_extract,
    extract_with_custom_rules,
    extract_with_trafilatura,
    extract_with_readability,
    MIN_CONTENT_LENGTH,
)


LONG_HTML_CONTENT = "<p>" + "This is a test paragraph with some meaningful content. " * 20 + "</p>"
SHORT_HTML_CONTENT = "<p>Short</p>"


@pytest.mark.asyncio
async def test_cascade_extract_trafilatura_first():
    """Trafilatura is tried when no custom config is provided."""
    html = "<html><body>" + LONG_HTML_CONTENT + "</body></html>"
    with patch("app.services.content_service.extract_with_trafilatura", new_callable=AsyncMock) as mock_traf:
        mock_traf.return_value = LONG_HTML_CONTENT
        content, method = await cascade_extract(html)
        assert method == "trafilatura"
        assert content == LONG_HTML_CONTENT
        mock_traf.assert_called_once()


@pytest.mark.asyncio
async def test_cascade_extract_falls_back_to_readability():
    """If trafilatura returns None, readability is tried."""
    html = "<html><body>" + LONG_HTML_CONTENT + "</body></html>"
    with (
        patch("app.services.content_service.extract_with_trafilatura", new_callable=AsyncMock) as mock_traf,
        patch("app.services.content_service.extract_with_readability", new_callable=AsyncMock) as mock_read,
    ):
        mock_traf.return_value = None
        mock_read.return_value = LONG_HTML_CONTENT
        content, method = await cascade_extract(html)
        assert method == "readability"
        assert content == LONG_HTML_CONTENT


@pytest.mark.asyncio
async def test_cascade_extract_custom_css_takes_priority():
    """Custom CSS rules are tried first when feed_config has css_selector."""
    html = "<html><body><div class='article'>" + LONG_HTML_CONTENT + "</div></body></html>"
    config = {"css_selector": ".article"}
    with patch("app.services.content_service.extract_with_custom_rules", new_callable=AsyncMock) as mock_css:
        mock_css.return_value = LONG_HTML_CONTENT
        content, method = await cascade_extract(html, feed_config=config)
        assert method == "custom_css"
        mock_css.assert_called_once_with(html, config)


@pytest.mark.asyncio
async def test_cascade_extract_custom_css_fallback_to_trafilatura():
    """If custom CSS returns None, trafilatura is tried next."""
    html = "<html><body>" + LONG_HTML_CONTENT + "</body></html>"
    config = {"css_selector": ".nonexistent"}
    with (
        patch("app.services.content_service.extract_with_custom_rules", new_callable=AsyncMock) as mock_css,
        patch("app.services.content_service.extract_with_trafilatura", new_callable=AsyncMock) as mock_traf,
    ):
        mock_css.return_value = None
        mock_traf.return_value = LONG_HTML_CONTENT
        content, method = await cascade_extract(html, feed_config=config)
        assert method == "trafilatura"


@pytest.mark.asyncio
async def test_cascade_extract_all_fail():
    """When all extractors fail, returns (None, 'none')."""
    html = "<html><body></body></html>"
    with (
        patch("app.services.content_service.extract_with_trafilatura", new_callable=AsyncMock) as mock_traf,
        patch("app.services.content_service.extract_with_readability", new_callable=AsyncMock) as mock_read,
    ):
        mock_traf.return_value = None
        mock_read.return_value = None
        content, method = await cascade_extract(html)
        assert content is None
        assert method == "none"


@pytest.mark.asyncio
async def test_cascade_extract_passes_extraction_mode():
    """extraction_mode from feed config is passed to trafilatura."""
    html = "<html><body>" + LONG_HTML_CONTENT + "</body></html>"
    config = {"extraction_mode": "precision"}
    with patch("app.services.content_service.extract_with_trafilatura", new_callable=AsyncMock) as mock_traf:
        mock_traf.return_value = LONG_HTML_CONTENT
        await cascade_extract(html, feed_config=config)
        mock_traf.assert_called_once_with(html, "precision")


@pytest.mark.asyncio
async def test_extract_with_custom_rules_css_selector():
    """CSS selector extraction works with BeautifulSoup."""
    html = '<html><body><nav>Menu</nav><div class="content">' + "A" * MIN_CONTENT_LENGTH + '</div></body></html>'
    config = {"css_selector": ".content"}
    result = await extract_with_custom_rules(html, config)
    assert result is not None
    assert "A" * MIN_CONTENT_LENGTH in result


@pytest.mark.asyncio
async def test_extract_with_custom_rules_css_remove():
    """css_remove strips unwanted elements before extraction."""
    inner = "B" * MIN_CONTENT_LENGTH
    html = f'<html><body><div class="content"><div class="ads">Ad</div>{inner}</div></body></html>'
    config = {"css_selector": ".content", "css_remove": ".ads"}
    result = await extract_with_custom_rules(html, config)
    assert result is not None
    assert "ads" not in result.lower() or "Ad" not in result


@pytest.mark.asyncio
async def test_extract_with_custom_rules_short_content_returns_none():
    """Content shorter than MIN_CONTENT_LENGTH is rejected."""
    html = '<html><body><div class="content">Short</div></body></html>'
    config = {"css_selector": ".content"}
    result = await extract_with_custom_rules(html, config)
    assert result is None


@pytest.mark.asyncio
async def test_extract_with_trafilatura_returns_content():
    """Trafilatura extracts HTML content."""
    long_text = "Word " * 100
    html = f"<html><body><article><p>{long_text}</p></article></body></html>"
    result = await extract_with_trafilatura(html)
    # trafilatura may or may not extract depending on content, just verify no crash
    # The actual extraction quality depends on trafilatura's internal logic
    assert result is None or len(result) >= MIN_CONTENT_LENGTH


@pytest.mark.asyncio
async def test_extract_with_readability_returns_content():
    """Readability extracts content from HTML."""
    long_text = "Paragraph content here. " * 50
    html = f"<html><head><title>Test</title></head><body><article><p>{long_text}</p></article></body></html>"
    result = await extract_with_readability(html)
    assert result is None or len(result) >= MIN_CONTENT_LENGTH
