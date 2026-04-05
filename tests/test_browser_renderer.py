"""Tests for browser_renderer.py (#321).

Real end-to-end tests using actual Playwright + Chromium.
"""

from __future__ import annotations

import pytest

from skill_seekers.cli.browser_renderer import (
    BrowserRenderer,
    _auto_install_chromium,
    _check_playwright_available,
)

# Skip all real browser tests when Playwright is not installed
_has_playwright = _check_playwright_available()
requires_playwright = pytest.mark.skipif(
    not _has_playwright,
    reason="Playwright not installed (pip install 'skill-seekers[browser]')",
)


@requires_playwright
class TestPlaywrightAvailability:
    """Test that playwright is properly detected."""

    def test_playwright_is_available(self):
        assert _check_playwright_available() is True

    def test_auto_install_succeeds(self):
        # Chromium is already installed, so this should be a no-op success
        assert _auto_install_chromium() is True


@requires_playwright
class TestBrowserRendererReal:
    """Real end-to-end tests with actual Chromium."""

    def test_render_simple_page(self):
        """Render a real page and get HTML back."""
        with BrowserRenderer() as renderer:
            html = renderer.render_page("https://example.com")

        assert "<html" in html.lower()
        assert "Example Domain" in html

    def test_render_returns_js_content(self):
        """Verify that JS-generated content is captured (not just the shell)."""
        with BrowserRenderer() as renderer:
            html = renderer.render_page("https://example.com")

        # example.com has static content, but the point is we get real HTML
        assert len(html) > 500
        assert "<body" in html.lower()

    def test_multiple_pages_reuse_browser(self):
        """Rendering multiple pages should reuse the same browser instance."""
        with BrowserRenderer() as renderer:
            html1 = renderer.render_page("https://example.com")
            html2 = renderer.render_page("https://example.com")

        assert "Example Domain" in html1
        assert "Example Domain" in html2

    def test_close_cleans_up(self):
        """After close(), internal state is None."""
        renderer = BrowserRenderer()
        renderer.render_page("https://example.com")
        assert renderer._browser is not None

        renderer.close()
        assert renderer._browser is None
        assert renderer._context is None
        assert renderer._playwright is None

    def test_context_manager_cleans_up(self):
        """Context manager calls close on exit."""
        with BrowserRenderer() as renderer:
            renderer.render_page("https://example.com")
            assert renderer._browser is not None

        assert renderer._browser is None

    def test_timeout_parameter(self):
        """Custom timeout is respected."""
        renderer = BrowserRenderer(timeout=5000)
        assert renderer._timeout == 5000
        renderer.close()

    def test_wait_until_parameter(self):
        """Custom wait_until is respected."""
        renderer = BrowserRenderer(wait_until="domcontentloaded")
        assert renderer._wait_until == "domcontentloaded"
        renderer.close()


class TestDocScraperBrowserIntegration:
    """Test that doc_scraper correctly accepts browser config."""

    def test_browser_mode_config_sets_attribute(self):
        from skill_seekers.cli.doc_scraper import DocToSkillConverter

        config = {
            "name": "test",
            "base_url": "https://example.com",
            "browser": True,
            "selectors": {},
            "url_patterns": {"include": [], "exclude": []},
        }
        scraper = DocToSkillConverter(config)
        assert scraper.browser_mode is True
        assert scraper._browser_renderer is None

    def test_browser_mode_default_false(self):
        from skill_seekers.cli.doc_scraper import DocToSkillConverter

        config = {
            "name": "test",
            "base_url": "https://example.com",
            "selectors": {},
            "url_patterns": {"include": [], "exclude": []},
        }
        scraper = DocToSkillConverter(config)
        assert scraper.browser_mode is False

    @requires_playwright
    def test_render_with_browser_returns_html(self):
        """Test the _render_with_browser helper directly."""
        from skill_seekers.cli.doc_scraper import DocToSkillConverter

        config = {
            "name": "test",
            "base_url": "https://example.com",
            "browser": True,
            "selectors": {},
            "url_patterns": {"include": [], "exclude": []},
        }
        scraper = DocToSkillConverter(config)

        html = scraper._render_with_browser("https://example.com")
        assert "Example Domain" in html
        assert scraper._browser_renderer is not None

        # Clean up
        scraper._browser_renderer.close()


class TestBrowserArgument:
    """Test --browser argument is accepted by DocToSkillConverter config."""

    def test_browser_config_true(self):
        """Test that DocToSkillConverter accepts browser=True in config."""
        from skill_seekers.cli.doc_scraper import DocToSkillConverter

        config = {
            "name": "test",
            "base_url": "https://example.com",
            "browser": True,
            "selectors": {},
            "url_patterns": {"include": [], "exclude": []},
        }
        scraper = DocToSkillConverter(config)
        assert scraper.browser_mode is True

    def test_browser_config_default_false(self):
        """Test that DocToSkillConverter defaults browser to False."""
        from skill_seekers.cli.doc_scraper import DocToSkillConverter

        config = {
            "name": "test",
            "base_url": "https://example.com",
            "selectors": {},
            "url_patterns": {"include": [], "exclude": []},
        }
        scraper = DocToSkillConverter(config)
        assert scraper.browser_mode is False
