"""Tests for OPML parsing and generation."""

from app.services.opml_service import parse_opml, generate_opml, OpmlFeed


class TestParseOpml:
    def test_flat_feeds(self):
        content = """<?xml version="1.0" encoding="UTF-8"?>
        <opml version="2.0">
          <head><title>Test</title></head>
          <body>
            <outline type="rss" text="Feed A" title="Feed A" xmlUrl="https://a.com/feed.xml" htmlUrl="https://a.com" description="Desc A"/>
            <outline type="rss" text="Feed B" xmlUrl="https://b.com/rss"/>
          </body>
        </opml>"""
        feeds = parse_opml(content)
        assert len(feeds) == 2
        assert feeds[0].title == "Feed A"
        assert feeds[0].url == "https://a.com/feed.xml"
        assert feeds[0].site_url == "https://a.com"
        assert feeds[0].description == "Desc A"
        assert feeds[0].group is None
        assert feeds[1].title == "Feed B"
        assert feeds[1].site_url is None

    def test_grouped_feeds(self):
        content = """<?xml version="1.0" encoding="UTF-8"?>
        <opml version="2.0">
          <head><title>Test</title></head>
          <body>
            <outline text="Tech">
              <outline type="rss" text="TechCrunch" xmlUrl="https://tc.com/feed"/>
            </outline>
            <outline text="News">
              <outline type="rss" text="BBC" xmlUrl="https://bbc.com/feed"/>
            </outline>
          </body>
        </opml>"""
        feeds = parse_opml(content)
        assert len(feeds) == 2
        assert feeds[0].group == "Tech"
        assert feeds[1].group == "News"

    def test_nested_three_levels(self):
        content = """<?xml version="1.0" encoding="UTF-8"?>
        <opml version="2.0">
          <head><title>Test</title></head>
          <body>
            <outline text="Tech">
              <outline text="Programming">
                <outline type="rss" text="Hacker News" xmlUrl="https://hn.com/feed"/>
              </outline>
            </outline>
          </body>
        </opml>"""
        feeds = parse_opml(content)
        assert len(feeds) == 1
        assert feeds[0].group == "Tech / Programming"

    def test_bom_handling(self):
        content = "\ufeff" + """<?xml version="1.0" encoding="UTF-8"?>
        <opml version="2.0">
          <head><title>Test</title></head>
          <body>
            <outline type="rss" text="Feed" xmlUrl="https://example.com/feed"/>
          </body>
        </opml>"""
        feeds = parse_opml(content)
        assert len(feeds) == 1

    def test_empty_body(self):
        content = """<?xml version="1.0"?>
        <opml version="2.0">
          <head><title>Empty</title></head>
          <body/>
        </opml>"""
        feeds = parse_opml(content)
        assert feeds == []

    def test_no_body(self):
        content = """<?xml version="1.0"?>
        <opml version="2.0"><head/></opml>"""
        feeds = parse_opml(content)
        assert feeds == []

    def test_mixed_grouped_and_ungrouped(self):
        content = """<?xml version="1.0" encoding="UTF-8"?>
        <opml version="2.0">
          <body>
            <outline type="rss" text="Solo" xmlUrl="https://solo.com/feed"/>
            <outline text="Group1">
              <outline type="rss" text="G1F1" xmlUrl="https://g1f1.com/feed"/>
            </outline>
          </body>
        </opml>"""
        feeds = parse_opml(content)
        assert len(feeds) == 2
        assert feeds[0].group is None
        assert feeds[1].group == "Group1"

    def test_title_fallback_to_text(self):
        content = """<?xml version="1.0"?>
        <opml version="2.0">
          <body>
            <outline text="TextOnly" xmlUrl="https://x.com/feed"/>
          </body>
        </opml>"""
        feeds = parse_opml(content)
        assert feeds[0].title == "TextOnly"

    def test_title_fallback_to_url(self):
        content = """<?xml version="1.0"?>
        <opml version="2.0">
          <body>
            <outline xmlUrl="https://x.com/feed"/>
          </body>
        </opml>"""
        feeds = parse_opml(content)
        assert feeds[0].title == "https://x.com/feed"


class TestGenerateOpml:
    def _make_feed(self, title, url, site_url=None, description=None):
        """Create a mock feed object with required attributes."""
        class MockFeed:
            pass
        f = MockFeed()
        f.title = title
        f.url = url
        f.site_url = site_url
        f.description = description
        return f

    def test_generates_valid_xml(self):
        feed = self._make_feed("Test Feed", "https://test.com/feed", "https://test.com", "A test feed")
        result = generate_opml([{"feed": feed, "group_name": None}])
        assert '<?xml version="1.0" ?>' in result
        assert '<opml version="2.0">' in result
        assert "RSS Reader Subscriptions" in result
        assert 'xmlUrl="https://test.com/feed"' in result
        assert 'htmlUrl="https://test.com"' in result

    def test_grouped_feeds(self):
        f1 = self._make_feed("Feed1", "https://f1.com/feed")
        f2 = self._make_feed("Feed2", "https://f2.com/feed")
        result = generate_opml([
            {"feed": f1, "group_name": "Tech"},
            {"feed": f2, "group_name": "Tech"},
        ])
        assert 'text="Tech"' in result
        assert 'xmlUrl="https://f1.com/feed"' in result
        assert 'xmlUrl="https://f2.com/feed"' in result

    def test_ungrouped_at_top_level(self):
        feed = self._make_feed("Solo", "https://solo.com/feed")
        result = generate_opml([{"feed": feed, "group_name": None}])
        assert 'text="Solo"' in result
        assert 'xmlUrl="https://solo.com/feed"' in result

    def test_roundtrip(self):
        f1 = self._make_feed("Ungrouped", "https://ug.com/feed", "https://ug.com")
        f2 = self._make_feed("Grouped", "https://gr.com/feed", "https://gr.com", "desc")
        xml = generate_opml([
            {"feed": f1, "group_name": None},
            {"feed": f2, "group_name": "MyGroup"},
        ])
        feeds = parse_opml(xml)
        assert len(feeds) == 2
        assert feeds[0].title == "Ungrouped"
        assert feeds[0].group is None
        assert feeds[1].title == "Grouped"
        assert feeds[1].group == "MyGroup"
        assert feeds[1].description == "desc"
