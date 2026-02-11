"""Regression tests for Gmail HTML extraction priority."""

import base64

from app.services.email_service import _extract_html_from_payload


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode()


class TestExtractHtmlFromPayload:
    """Core regression: multipart/alternative should prefer text/html over text/plain."""

    def test_multipart_alternative_prefers_html(self):
        payload = {
            "mimeType": "multipart/alternative",
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": _b64("Plain text version")},
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": _b64("<h1>HTML version</h1>")},
                },
            ],
        }
        result = _extract_html_from_payload(payload)
        assert result == "<h1>HTML version</h1>"

    def test_single_text_html(self):
        payload = {
            "mimeType": "text/html",
            "body": {"data": _b64("<p>Hello</p>")},
        }
        result = _extract_html_from_payload(payload)
        assert result == "<p>Hello</p>"

    def test_single_text_plain_returns_pre_wrapped(self):
        payload = {
            "mimeType": "text/plain",
            "body": {"data": _b64("Just plain text")},
        }
        result = _extract_html_from_payload(payload)
        assert result == "<pre>Just plain text</pre>"

    def test_multipart_related_with_nested_alternative(self):
        payload = {
            "mimeType": "multipart/related",
            "parts": [
                {
                    "mimeType": "multipart/alternative",
                    "parts": [
                        {
                            "mimeType": "text/plain",
                            "body": {"data": _b64("Plain fallback")},
                        },
                        {
                            "mimeType": "text/html",
                            "body": {"data": _b64("<div>Rich HTML</div>")},
                        },
                    ],
                },
                {
                    "mimeType": "image/png",
                    "body": {"attachmentId": "abc123"},
                    "headers": [{"name": "Content-ID", "value": "<img001>"}],
                },
            ],
        }
        result = _extract_html_from_payload(payload)
        assert result == "<div>Rich HTML</div>"

    def test_empty_payload(self):
        result = _extract_html_from_payload({})
        assert result == ""

    def test_multipart_with_only_plain(self):
        payload = {
            "mimeType": "multipart/alternative",
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": _b64("Only plain here")},
                },
            ],
        }
        result = _extract_html_from_payload(payload)
        assert result == "<pre>Only plain here</pre>"

    def test_deeply_nested_html(self):
        payload = {
            "mimeType": "multipart/mixed",
            "parts": [
                {
                    "mimeType": "multipart/related",
                    "parts": [
                        {
                            "mimeType": "multipart/alternative",
                            "parts": [
                                {
                                    "mimeType": "text/plain",
                                    "body": {"data": _b64("Deep plain")},
                                },
                                {
                                    "mimeType": "text/html",
                                    "body": {"data": _b64("<b>Deep HTML</b>")},
                                },
                            ],
                        },
                    ],
                },
            ],
        }
        result = _extract_html_from_payload(payload)
        assert result == "<b>Deep HTML</b>"
