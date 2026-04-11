"""
Browser Renderer — Playwright-based headless browser for JavaScript SPA sites.

When documentation sites use client-side rendering (React, Vue, etc.),
requests.get() returns empty HTML shells. This module uses Playwright
to render JavaScript before extracting content.

Optional dependency: pip install "skill-seekers[browser]"
"""

from __future__ import annotations

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


def _check_playwright_available() -> bool:
    """Check if playwright package is installed."""
    try:
        import playwright  # noqa: F401

        return True
    except ImportError:
        return False


def _auto_install_chromium() -> bool:
    """Auto-install Chromium browser on first use.

    Returns:
        True if install succeeded or already installed, False on failure.
    """
    logger.info("Installing Chromium browser for headless rendering...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            logger.info("Chromium installed successfully.")
            return True
        logger.error("Chromium install failed: %s", result.stderr)
        return False
    except Exception as e:
        logger.error("Failed to install Chromium: %s", e)
        return False


class BrowserRenderer:
    """Render JavaScript pages using Playwright headless Chromium.

    Usage:
        renderer = BrowserRenderer()
        html = renderer.render_page("https://docs.discord.com")
        renderer.close()

    Or as context manager:
        with BrowserRenderer() as renderer:
            html = renderer.render_page(url)
    """

    def __init__(
        self,
        timeout: int = 60000,
        wait_until: str = "domcontentloaded",
        extra_wait: int = 0,
    ):
        """Initialize renderer.

        Args:
            timeout: Page load timeout in milliseconds (default: 60s)
            wait_until: Playwright wait condition — "networkidle", "load", "domcontentloaded"
                        Default changed to "domcontentloaded" for better compatibility
                        with heavy sites (Unity docs, DocFX, etc.) that never reach networkidle.
            extra_wait: Additional milliseconds to wait after page load for lazy-loaded
                        navigation/content (e.g., 5000 for DocFX sidebar). Default: 0.
        """
        if not _check_playwright_available():
            raise ImportError(
                "Playwright is required for --browser mode.\n"
                "Install it with: pip install 'skill-seekers[browser]'\n"
                "Then run: playwright install chromium"
            )

        self._timeout = timeout
        self._wait_until = wait_until
        self._extra_wait = extra_wait
        self._playwright = None
        self._browser = None
        self._context = None

    def _ensure_browser(self) -> None:
        """Launch browser if not already running. Auto-installs chromium if needed."""
        if self._browser is not None:
            return

        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()

        try:
            self._browser = self._playwright.chromium.launch(headless=True)
        except Exception:
            # Browser not installed — try auto-install
            logger.warning("Chromium not found. Attempting auto-install...")
            if _auto_install_chromium():
                self._browser = self._playwright.chromium.launch(headless=True)
            else:
                self._playwright.stop()
                self._playwright = None
                raise RuntimeError(
                    "Could not launch Chromium. Run: playwright install chromium"
                ) from None

        self._context = self._browser.new_context(user_agent="Mozilla/5.0 (Documentation Scraper)")

    def render_page(self, url: str) -> str:
        """Render a page with JavaScript execution and return the HTML.

        Args:
            url: URL to render

        Returns:
            Fully-rendered HTML string after JavaScript execution

        Raises:
            RuntimeError: If browser cannot be launched
            TimeoutError: If page load times out
        """
        self._ensure_browser()

        page = self._context.new_page()
        try:
            page.goto(url, wait_until=self._wait_until, timeout=self._timeout)
            if self._extra_wait > 0:
                page.wait_for_timeout(self._extra_wait)
            html = page.content()
            return html
        finally:
            page.close()

    def close(self) -> None:
        """Shut down browser and Playwright."""
        if self._context:
            self._context.close()
            self._context = None
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
