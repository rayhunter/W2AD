"""
Regression tests for the migration-correctness fixes:

1. Extraction failures raise instead of producing an empty "successful" migration.
2. Extraction follows X-WP-TotalPages so large sites are fully fetched.
3. Frontmatter is generated with PyYAML, so titles with quotes/colons stay valid,
   and WordPress HTML entities in titles are unescaped.
4. Unresolvable attachment IDs are never replaced with a guessed image.
"""

import pytest
import requests
import yaml
from unittest.mock import Mock, patch

from extraction_agent import ExtractionAgent, WPPost, WPPage
from transform_agent import TransformAgent, MarkdownPost, MarkdownPage, StaticContentBundle, create_content_files


def _resp(json_data, total_pages=1, status=200):
    r = Mock()
    r.status_code = status
    r.json.return_value = json_data
    r.headers = {"X-WP-TotalPages": str(total_pages)}
    if status >= 400:
        r.raise_for_status.side_effect = requests.HTTPError(f"{status} error")
    else:
        r.raise_for_status.return_value = None
    return r


def _post(i):
    return {
        "id": i,
        "title": {"rendered": f"Post {i}"},
        "content": {"rendered": "<p>hi</p>"},
        "excerpt": {"rendered": ""},
        "date": "2024-01-01T00:00:00",
        "slug": f"post-{i}",
        "status": "publish",
    }


@pytest.fixture
def agent():
    # The constructor pings the API; stub that out.
    with patch("extraction_agent.requests.get", return_value=_resp({})):
        return ExtractionAgent("https://example.com")


class TestExtractionErrors:
    def test_http_error_raises_instead_of_returning_empty(self, agent):
        with patch("extraction_agent.requests.get", return_value=_resp([], status=401)):
            with pytest.raises(RuntimeError) as exc:
                agent.extract_posts()
        assert "401" in str(exc.value)

    def test_network_error_propagates_through_extract_all(self, agent):
        with patch("extraction_agent.requests.get", side_effect=requests.ConnectionError("down")):
            with pytest.raises(RuntimeError) as exc:
                agent.extract_all()
        assert "down" in str(exc.value)

    def test_non_list_response_raises(self, agent):
        with patch("extraction_agent.requests.get", return_value=_resp({"code": "rest_forbidden"})):
            with pytest.raises(RuntimeError):
                agent.extract_posts()


class TestPagination:
    def test_follows_total_pages_header(self, agent):
        pages = [_resp([_post(1), _post(2)], total_pages=3),
                 _resp([_post(3), _post(4)], total_pages=3),
                 _resp([_post(5)], total_pages=3)]
        with patch("extraction_agent.requests.get", side_effect=pages) as mock_get:
            posts = agent.extract_posts(per_page=2)

        assert [p.id for p in posts] == [1, 2, 3, 4, 5]
        assert mock_get.call_count == 3
        assert [c.kwargs["params"]["page"] for c in mock_get.call_args_list] == [1, 2, 3]

    def test_single_page(self, agent):
        with patch("extraction_agent.requests.get", return_value=_resp([_post(1)])) as mock_get:
            posts = agent.extract_posts()
        assert len(posts) == 1
        assert mock_get.call_count == 1

    def test_stops_on_empty_batch_even_if_header_lies(self, agent):
        with patch("extraction_agent.requests.get", return_value=_resp([], total_pages=99)) as mock_get:
            posts = agent.extract_posts()
        assert posts == []
        assert mock_get.call_count == 1


class TestFrontmatter:
    def setup_method(self):
        self.agent = TransformAgent()

    @pytest.mark.parametrize("title", [
        "Don't Panic",
        'She said "hello"',
        "Key: value looks like yaml",
        "Ends with colon:",
        "# not a heading",
        "- not a list",
        "Unicode café ☕",
        "",
    ])
    def test_any_title_round_trips_through_yaml(self, title):
        fm = self.agent.create_frontmatter(title=title, date="2024-01-01T00:00:00", slug="x")
        assert fm.startswith("---\n") and fm.endswith("\n---")
        parsed = yaml.safe_load(fm.strip("-\n"))
        assert parsed["title"] == title
        assert parsed["date"] == "2024-01-01T00:00:00"
        assert parsed["slug"] == "x"

    def test_empty_categories_are_lists_not_null(self):
        fm = self.agent.create_frontmatter(title="t", date="d", slug="s", categories=[], tags=[])
        parsed = yaml.safe_load(fm.strip("-\n"))
        assert parsed["categories"] == []
        assert parsed["tags"] == []

    def test_categories_and_tags_serialized(self):
        fm = self.agent.create_frontmatter(title="t", date="d", slug="s",
                                           categories=["Tech", "Web: Dev"], tags=["a"])
        parsed = yaml.safe_load(fm.strip("-\n"))
        assert parsed["categories"] == ["Tech", "Web: Dev"]
        assert parsed["tags"] == ["a"]

    def test_wordpress_entities_in_title_are_unescaped(self):
        wp_post = WPPost(id=1, title="Tom &amp; Jerry&#8217;s <em>Day</em>", content="<p>x</p>",
                         excerpt="", date="2024-01-01", slug="tj", status="publish")
        md = self.agent.transform_post(wp_post)
        assert md.title == "Tom & Jerry’s Day"

        wp_page = WPPage(id=2, title="Q&amp;A", content="", date="2024-01-01", slug="qa", status="publish")
        assert self.agent.transform_page(wp_page).title == "Q&A"

    def test_create_content_files_produces_parseable_files(self):
        bundle = StaticContentBundle(
            posts=[MarkdownPost(title="It's: tricky", content="body", date="2024-01-01", slug="p")],
            pages=[MarkdownPage(title='Say "hi"', content="body", date="2024-01-01", slug="pg")],
        )
        files = create_content_files(bundle)
        for entry in files["posts"] + files["pages"]:
            text = entry["content"]
            assert text.startswith("---\n")
            fm_block = text.split("\n---\n", 1)[0][4:]
            yaml.safe_load(fm_block)  # must not raise
        assert files["posts"][0]["path"] == "src/content/blog/p.md"
        assert files["pages"][0]["path"] == "src/content/pages/pg.md"
        assert yaml.safe_load(files["posts"][0]["content"].split("\n---\n", 1)[0][4:])["title"] == "It's: tricky"


class TestNoImageGuessing:
    def _agent(self):
        with patch("media_agent.storage.Client") as client:
            client.return_value.bucket.return_value.list_blobs.return_value = []
            from media_agent import MediaAgent
            return MediaAgent("/dev/null", "bucket", wp_site_url="https://example.com")

    def test_unresolvable_id_is_dropped_not_guessed(self):
        agent = self._agent()
        not_found = _resp({"code": "rest_post_invalid_id"}, status=404)
        with patch("media_agent.requests.get", return_value=not_found) as mock_get:
            urls = agent.extract_media_urls('<img src="15" alt="x">', context="Rome trip")

        assert urls == []
        # Exactly one lookup (the direct /media/15 call); no keyword or "most recent" fallbacks.
        assert mock_get.call_count == 1
        assert mock_get.call_args.args[0].endswith("/wp-json/wp/v2/media/15")

    def test_resolvable_id_is_used(self):
        agent = self._agent()
        found = _resp({"source_url": "https://example.com/wp-content/uploads/2024/01/a.jpg"})
        with patch("media_agent.requests.get", return_value=found):
            urls = agent.extract_media_urls('<img src="15" alt="x">')
        assert urls == ["https://example.com/wp-content/uploads/2024/01/a.jpg"]

    def test_guessing_helpers_are_gone(self):
        from media_agent import MediaAgent
        assert not hasattr(MediaAgent, "intelligent_attachment_resolution")
        assert not hasattr(MediaAgent, "get_all_available_media")
