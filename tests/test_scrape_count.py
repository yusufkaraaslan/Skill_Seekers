"""Tests for accurate scrape page counting (#320) and SPA detection (#321)."""

import logging
import os

import pytest

from skill_seekers.cli.doc_scraper import DocToSkillConverter


@pytest.fixture
def converter(tmp_path):
    """Create a converter with tmp output directory."""
    config = {
        "name": "test-site",
        "base_url": "https://example.com",
        "selectors": {"title": "title", "code_blocks": "pre code"},
        "url_patterns": {"include": [], "exclude": []},
        "rate_limit": 0,
        "max_pages": 100,
    }
    conv = DocToSkillConverter(config)
    # Override paths to use tmp_path
    conv.data_dir = str(tmp_path / "test-site_data")
    conv.skill_dir = str(tmp_path / "test-site")
    os.makedirs(os.path.join(conv.data_dir, "pages"), exist_ok=True)
    return conv


class TestPageCounting:
    """Tests for pages_saved and pages_skipped counters."""

    def test_initial_counters_are_zero(self, converter):
        assert converter.pages_saved == 0
        assert converter.pages_skipped == 0

    def test_save_page_increments_saved_counter(self, converter):
        page = {
            "url": "https://example.com/page1",
            "title": "Test Page",
            "content": "This is a test page with enough content to pass the 50 char minimum threshold for saving.",
        }
        converter.save_page(page)
        assert converter.pages_saved == 1
        assert converter.pages_skipped == 0

    def test_save_page_increments_skipped_for_empty_content(self, converter):
        page = {
            "url": "https://example.com/empty",
            "title": "Empty",
            "content": "",
        }
        converter.save_page(page)
        assert converter.pages_saved == 0
        assert converter.pages_skipped == 1

    def test_save_page_increments_skipped_for_short_content(self, converter):
        page = {
            "url": "https://example.com/short",
            "title": "Short",
            "content": "Too short",
        }
        converter.save_page(page)
        assert converter.pages_saved == 0
        assert converter.pages_skipped == 1

    def test_save_page_increments_skipped_for_missing_content(self, converter):
        page = {
            "url": "https://example.com/none",
            "title": "No Content",
        }
        converter.save_page(page)
        assert converter.pages_saved == 0
        assert converter.pages_skipped == 1

    def test_multiple_saves_track_correctly(self, converter):
        good_page = {
            "url": "https://example.com/good",
            "title": "Good Page",
            "content": "This page has plenty of content to pass the 50 character minimum threshold for saving pages.",
        }
        empty_page = {
            "url": "https://example.com/empty",
            "title": "Empty",
            "content": "",
        }
        converter.save_page(good_page)
        converter.save_page(empty_page)
        converter.save_page(good_page)  # same URL, still counts
        assert converter.pages_saved == 2
        assert converter.pages_skipped == 1


class TestCompletionMessages:
    """Tests for scrape completion log messages."""

    def test_completion_message_shows_saved_and_skipped(self, converter, caplog):
        """The completion message should report saved/skipped breakdown."""
        converter.visited_urls = {"url1", "url2", "url3"}
        converter.pages_saved = 2
        converter.pages_skipped = 1

        with caplog.at_level(logging.INFO):
            converter._log_scrape_completion()

        assert "2 saved" in caplog.text
        assert "1 skipped" in caplog.text

    def test_completion_message_no_skipped(self, converter, caplog):
        """When nothing is skipped, don't mention skipped count."""
        converter.visited_urls = {"url1", "url2"}
        converter.pages_saved = 2
        converter.pages_skipped = 0

        with caplog.at_level(logging.INFO):
            converter._log_scrape_completion()

        assert "2 saved" in caplog.text
        assert "skipped" not in caplog.text.lower()


class TestSPADetection:
    """Tests for SPA site detection warnings (#321)."""

    def test_spa_warning_when_zero_saved(self, converter, caplog):
        """Warn when 0 pages saved out of many visited."""
        converter.visited_urls = {f"url{i}" for i in range(50)}
        converter.pages_saved = 0
        converter.pages_skipped = 50

        with caplog.at_level(logging.WARNING):
            converter._log_scrape_completion()

        assert "JavaScript" in caplog.text

    def test_spa_warning_when_mostly_skipped(self, converter, caplog):
        """Warn when >80% of pages are skipped."""
        converter.visited_urls = {f"url{i}" for i in range(100)}
        converter.pages_saved = 10
        converter.pages_skipped = 90

        with caplog.at_level(logging.WARNING):
            converter._log_scrape_completion()

        assert "JavaScript" in caplog.text

    def test_no_spa_warning_when_mostly_saved(self, converter, caplog):
        """No warning when most pages are saved."""
        converter.visited_urls = {f"url{i}" for i in range(100)}
        converter.pages_saved = 80
        converter.pages_skipped = 20

        with caplog.at_level(logging.WARNING):
            converter._log_scrape_completion()

        assert "JavaScript" not in caplog.text

    def test_no_spa_warning_for_small_scrapes(self, converter, caplog):
        """Don't warn for very small scrapes (< 5 pages)."""
        converter.visited_urls = {"url1", "url2", "url3"}
        converter.pages_saved = 0
        converter.pages_skipped = 3

        with caplog.at_level(logging.WARNING):
            converter._log_scrape_completion()

        # Small scrape - could just be a few bad pages, not SPA
        assert "JavaScript" not in caplog.text


class TestBuildSkillError:
    """Tests for improved build_skill error message."""

    def test_build_skill_error_suggests_cause(self, converter, caplog):
        """build_skill should suggest SPA as cause when 0 pages saved."""
        converter.pages_saved = 0
        converter.pages_skipped = 50

        with caplog.at_level(logging.ERROR):
            result = converter.build_skill()

        assert result is False
        assert "No scraped data found" in caplog.text
        assert "empty content" in caplog.text

    def test_build_skill_error_generic_when_no_skips(self, converter, caplog):
        """build_skill with no data and no skips = generic error (not SPA)."""
        converter.pages_saved = 0
        converter.pages_skipped = 0

        with caplog.at_level(logging.ERROR):
            result = converter.build_skill()

        assert result is False
        assert "No scraped data found" in caplog.text
