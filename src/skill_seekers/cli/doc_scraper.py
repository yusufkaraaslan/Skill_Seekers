#!/usr/bin/env python3
"""
Documentation to AI Skill Converter
Single tool to scrape any documentation and create high-quality AI skills.

Usage:
    skill-seekers scrape --interactive
    skill-seekers scrape --config configs/godot.json
    skill-seekers scrape --url https://react.dev/ --name react
"""

import argparse
import asyncio
import hashlib
import json
import logging
import os
import re
import sys
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import httpx
import requests
from bs4 import BeautifulSoup

from skill_seekers.cli.config_fetcher import (
    get_last_searched_paths,
    list_available_configs,
    resolve_config_path,
)
from skill_seekers.cli.config_validator import ConfigValidator
from skill_seekers.cli.constants import (
    CONTENT_PREVIEW_LENGTH,
    DEFAULT_ASYNC_MODE,
    DEFAULT_CHECKPOINT_INTERVAL,
    DEFAULT_MAX_PAGES,
    DEFAULT_RATE_LIMIT,
    MAX_PAGES_WARNING_THRESHOLD,
    MIN_CATEGORIZATION_SCORE,
)
from skill_seekers.cli.language_detector import LanguageDetector
from skill_seekers.cli.llms_txt_detector import LlmsTxtDetector
from skill_seekers.cli.llms_txt_downloader import LlmsTxtDownloader
from skill_seekers.cli.llms_txt_parser import LlmsTxtParser
from skill_seekers.cli.skill_converter import SkillConverter
from skill_seekers.cli.utils import sanitize_url, setup_logging

# Configure logging
logger = logging.getLogger(__name__)

# Shared fallback selectors for finding main content across all code paths.
# No 'body' — it matches everything and hides real selector failures.
FALLBACK_MAIN_SELECTORS = [
    "main",
    'div[role="main"]',
    "article",
    '[role="main"]',
    ".content",
    ".doc-content",
    "#main-content",
]

# Pre-compiled regex patterns for frequently called methods
_WHITESPACE_RE = re.compile(r"\s+")
_SAFE_TITLE_RE = re.compile(r"[^\w\s-]")
_SAFE_TITLE_SEP_RE = re.compile(r"[-\s]+")


def infer_description_from_docs(
    base_url: str, first_page_content: str | None = None, name: str = ""
) -> str:
    """
    Infer skill description from documentation metadata or first page content.

    Tries multiple strategies:
    1. Extract meta description tag from first page
    2. Extract first meaningful paragraph from content
    3. Fall back to improved template

    Args:
        base_url: Documentation base URL
        first_page_content: HTML content of first page (optional)
        name: Skill name

    Returns:
        Description string suitable for "Use when..." format
    """
    # If we have first page content, try to extract description
    if first_page_content:
        try:
            soup = BeautifulSoup(first_page_content, "html.parser")

            # Strategy 1: Try meta description tag
            meta_desc = soup.find("meta", {"name": "description"})
            if meta_desc and meta_desc.get("content"):
                desc = meta_desc["content"].strip()
                if len(desc) > 20:  # Meaningful length
                    # Clean and format
                    if len(desc) > 150:
                        desc = desc[:147] + "..."
                    return f"Use when {desc.lower()}"

            # Strategy 2: Try OpenGraph description
            og_desc = soup.find("meta", {"property": "og:description"})
            if og_desc and og_desc.get("content"):
                desc = og_desc["content"].strip()
                if len(desc) > 20:
                    if len(desc) > 150:
                        desc = desc[:147] + "..."
                    return f"Use when {desc.lower()}"

            # Strategy 3: Extract first meaningful paragraph from main content
            # Look for common documentation main content areas
            main_content = None
            for selector in [
                "article",
                "main",
                'div[role="main"]',
                "div.content",
                "div.doc-content",
            ]:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            if main_content:
                # Find first paragraph
                for p in main_content.find_all("p", limit=5):
                    text = p.get_text().strip()
                    # Skip empty, very short, or navigation-like paragraphs
                    if len(text) > 30 and not any(
                        skip in text.lower()
                        for skip in ["table of contents", "on this page", "navigation"]
                    ):
                        # Clean and format
                        if len(text) > 150:
                            text = text[:147] + "..."
                        return f"Use when working with {text.lower()}"

        except Exception as e:
            logger.debug(f"Could not infer description from page content: {e}")

    # Improved fallback template
    return (
        f"Use when working with {name}"
        if name
        else f"Use when working with documentation at {urlparse(base_url).netloc}"
    )


class DocToSkillConverter(SkillConverter):
    SOURCE_TYPE = "web"

    def __init__(self, config: dict[str, Any], dry_run: bool = False, resume: bool = False) -> None:
        super().__init__(config)
        self.config = config
        self.name = config["name"]
        self.base_url = config["base_url"]
        self.dry_run = dry_run
        self.resume = resume

        # Paths
        self.data_dir = f"output/{self.name}_data"
        self.skill_dir = f"output/{self.name}"
        self.checkpoint_file = f"{self.data_dir}/checkpoint.json"

        # Checkpoint config
        checkpoint_config = config.get("checkpoint", {})
        self.checkpoint_enabled = checkpoint_config.get("enabled", False)
        self.checkpoint_interval = checkpoint_config.get("interval", DEFAULT_CHECKPOINT_INTERVAL)

        # llms.txt detection state
        skip_llms_txt_value = config.get("skip_llms_txt", False)
        if not isinstance(skip_llms_txt_value, bool):
            logger.warning(
                "Invalid value for 'skip_llms_txt': %r (expected bool). Defaulting to False.",
                skip_llms_txt_value,
            )
            self.skip_llms_txt = False
        else:
            self.skip_llms_txt = skip_llms_txt_value
        self.llms_txt_detected = False
        self.llms_txt_variant = None
        self.llms_txt_variants: list[str] = []  # Track all downloaded variants

        # Browser rendering mode (for JavaScript SPA sites)
        self.browser_mode = config.get("browser", False)
        self._browser_renderer = None
        self._browser_wait_until = config.get("browser_wait_until", "domcontentloaded")
        self._browser_extra_wait = config.get("browser_extra_wait", 0)  # ms

        # Parallel scraping config
        self.workers = config.get("workers", 1)
        self.async_mode = config.get("async_mode", DEFAULT_ASYNC_MODE)

        # State
        self.visited_urls: set[str] = set()
        # Support multiple starting URLs
        start_urls = config.get("start_urls", [self.base_url])
        self.pending_urls = deque(start_urls)
        self._enqueued_urls: set[str] = set(
            start_urls
        )  # Track all ever-enqueued URLs for O(1) dedup
        self.pages: list[dict[str, Any]] = []
        self.pages_scraped = 0
        self.pages_saved = 0
        self.pages_skipped = 0

        # Language detection
        self.language_detector = LanguageDetector(min_confidence=0.15)

        # Pre-cache URL patterns for faster is_valid_url checks
        url_patterns = config.get("url_patterns", {})
        self._include_patterns: list[str] = url_patterns.get("include", [])
        self._exclude_patterns: list[str] = url_patterns.get("exclude", [])

        # Thread-safe lock for parallel scraping
        if self.workers > 1:
            import threading

            self.lock = threading.Lock()

        # Create directories (unless dry-run)
        if not dry_run:
            os.makedirs(f"{self.data_dir}/pages", exist_ok=True)
            os.makedirs(f"{self.skill_dir}/references", exist_ok=True)
            os.makedirs(f"{self.skill_dir}/scripts", exist_ok=True)
            os.makedirs(f"{self.skill_dir}/assets", exist_ok=True)

        # Load checkpoint if resuming
        if resume and not dry_run:
            self.load_checkpoint()

    def _enqueue_url(self, url: str) -> None:
        """Add a URL to the pending queue if not already visited or enqueued (O(1)).

        Applies :func:`sanitize_url` to percent-encode square brackets before
        enqueueing, preventing ``Invalid IPv6 URL`` errors on fetch (see #284).
        """
        url = sanitize_url(url)
        if url not in self.visited_urls and url not in self._enqueued_urls:
            self._enqueued_urls.add(url)
            self.pending_urls.append(url)

    def is_valid_url(self, url: str) -> bool:
        """Check if URL should be scraped based on patterns.

        Args:
            url (str): URL to validate

        Returns:
            bool: True if URL matches include patterns and doesn't match exclude patterns
        """
        # Use directory part of base_url for prefix check so sibling pages match.
        # e.g., base_url "https://example.com/docs/index.html" → prefix "https://example.com/docs/"
        base_dir = self.base_url if self.base_url.endswith("/") else self.base_url + "/"
        if not url.startswith(base_dir):
            return False

        if self._include_patterns and not any(pattern in url for pattern in self._include_patterns):
            return False

        return not any(pattern in url for pattern in self._exclude_patterns)

    @staticmethod
    def _has_md_extension(url: str) -> bool:
        """Check if URL path ends with .md extension.

        Uses URL path parsing instead of substring matching to avoid
        false positives on URLs like /embed/page or /cmd-line.
        """
        return urlparse(url).path.endswith(".md")

    def save_checkpoint(self) -> None:
        """Save progress checkpoint"""
        if not self.checkpoint_enabled or self.dry_run:
            return

        checkpoint_data = {
            "config": self.config,
            "visited_urls": list(self.visited_urls),
            "pending_urls": list(self.pending_urls),
            "pages_scraped": self.pages_scraped,
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "checkpoint_interval": self.checkpoint_interval,
        }

        try:
            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2)
            logger.info("  💾 Checkpoint saved (%d pages)", self.pages_scraped)
        except Exception as e:
            logger.warning("  ⚠️  Failed to save checkpoint: %s", e)

    def load_checkpoint(self) -> None:
        """Load progress from checkpoint"""
        if not os.path.exists(self.checkpoint_file):
            logger.info("ℹ️  No checkpoint found, starting fresh")
            return

        try:
            with open(self.checkpoint_file, encoding="utf-8") as f:
                checkpoint_data = json.load(f)

            self.visited_urls = set(checkpoint_data["visited_urls"])
            pending = checkpoint_data["pending_urls"]
            self.pending_urls = deque(pending)
            self._enqueued_urls = set(pending)
            self.pages_scraped = checkpoint_data["pages_scraped"]

            logger.info("✅ Resumed from checkpoint")
            logger.info("   Pages already scraped: %d", self.pages_scraped)
            logger.info("   URLs visited: %d", len(self.visited_urls))
            logger.info("   URLs pending: %d", len(self.pending_urls))
            logger.info("   Last updated: %s", checkpoint_data["last_updated"])
            logger.info("")

        except Exception as e:
            logger.warning("⚠️  Failed to load checkpoint: %s", e)
            logger.info("   Starting fresh")

    def clear_checkpoint(self) -> None:
        """Remove checkpoint file"""
        if os.path.exists(self.checkpoint_file):
            try:
                os.remove(self.checkpoint_file)
                logger.info("✅ Checkpoint cleared")
            except Exception as e:
                logger.warning("⚠️  Failed to clear checkpoint: %s", e)

    def _find_main_content(self, soup: Any) -> tuple[Any, str | None]:
        """Find the main content element using config selector with fallbacks.

        Tries the config-specified selector first, then falls back through
        FALLBACK_MAIN_SELECTORS. Does NOT fall back to <body> since that
        matches everything and hides real selector failures.

        Args:
            soup: BeautifulSoup parsed page

        Returns:
            Tuple of (element, selector_used) or (None, None) if nothing matched
        """
        selectors = self.config.get("selectors", {})
        main_selector = selectors.get("main_content")

        if main_selector:
            main = soup.select_one(main_selector)
            if main:
                return main, main_selector
            # Config selector didn't match — fall through to fallbacks

        for selector in FALLBACK_MAIN_SELECTORS:
            main = soup.select_one(selector)
            if main:
                return main, selector

        return None, None

    def extract_content(self, soup: Any, url: str) -> dict[str, Any]:
        """Extract content with improved code and pattern detection"""
        page = {
            "url": url,
            "title": "",
            "content": "",
            "headings": [],
            "code_samples": [],
            "patterns": [],  # NEW: Extract common patterns
            "links": [],
        }

        selectors = self.config.get("selectors", {})

        # Extract title
        title_elem = soup.select_one(selectors.get("title", "title"))
        if title_elem:
            page["title"] = self.clean_text(title_elem.get_text())

        # Extract links from entire page (always, even if main content not found).
        # This allows discovery of navigation links outside the main content area.
        seen_links: set[str] = set()
        for link in soup.find_all("a", href=True):
            href = urljoin(url, link["href"])
            # Strip anchor fragments to avoid treating #anchors as separate pages
            href = href.split("#")[0]
            if href not in seen_links and self.is_valid_url(href):
                seen_links.add(href)
                page["links"].append(href)

        # Find main content using shared fallback logic
        main, _selector_used = self._find_main_content(soup)

        if not main:
            logger.warning("⚠ No content: %s", url)
            return page

        # Extract headings with better structure
        for h in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            text = self.clean_text(h.get_text())
            if text:
                page["headings"].append({"level": h.name, "text": text, "id": h.get("id", "")})

        # Extract code with language detection
        code_selector = selectors.get("code_blocks", "pre code")
        for code_elem in main.select(code_selector):
            code = code_elem.get_text()
            if len(code.strip()) > 10:
                # Try to detect language
                lang = self.detect_language(code_elem, code)
                page["code_samples"].append({"code": code.strip(), "language": lang})

        # Extract patterns (NEW: common code patterns)
        page["patterns"] = self.extract_patterns(main, page["code_samples"])

        # Extract paragraphs
        paragraphs = []
        for p in main.find_all("p"):
            text = self.clean_text(p.get_text())
            if text and len(text) > 20:  # Skip very short paragraphs
                paragraphs.append(text)

        page["content"] = "\n\n".join(paragraphs)

        return page

    def _extract_markdown_content(self, content: str, url: str) -> dict[str, Any]:
        """Extract structured content from a Markdown file.

        Uses the enhanced unified MarkdownParser for comprehensive extraction:
        - Title from first h1 heading or frontmatter
        - Headings (h1-h6) with IDs
        - Code blocks with language detection and quality scoring
        - Tables (GitHub-flavored)
        - Internal .md links for BFS crawling
        - Content paragraphs (>20 chars)
        - Admonitions/callouts
        - Images

        Auto-detects HTML content and falls back to _extract_html_as_markdown.

        Args:
            content: Raw markdown content string (or HTML if server returned HTML)
            url: Source URL for resolving relative links

        Returns:
            Dict with keys:
                - url: str - Source URL
                - title: str - Extracted from first # heading
                - content: str - Paragraphs joined with double newlines
                - headings: List[Dict] - {'level': 'h2', 'text': str, 'id': str}
                - code_samples: List[Dict] - {'code': str, 'language': str}
                - links: List[str] - Absolute URLs to other .md files
                - patterns: List - Empty (reserved for future use)

        Note:
            Only .md links are extracted to avoid client-side rendered HTML pages.
            Anchor fragments (#section) are stripped from links.
        """
        # Detect if content is actually HTML (some .md URLs return HTML)
        if content.strip().startswith("<!DOCTYPE") or content.strip().startswith("<html"):
            return self._extract_html_as_markdown(content, url)

        # Try enhanced unified parser first
        try:
            from skill_seekers.cli.parsers.extractors import MarkdownParser

            parser = MarkdownParser()
            result = parser.parse_string(content, url)

            if result.success and result.document:
                doc = result.document

                # Extract links from the document
                links = []
                for link in doc.external_links:
                    href = link.target
                    if href.startswith("http"):
                        full_url = href
                    elif not href.startswith("#"):
                        full_url = urljoin(url, href)
                    else:
                        continue
                    full_url = full_url.split("#")[0]
                    if (
                        self._has_md_extension(full_url)
                        and self.is_valid_url(full_url)
                        and full_url not in links
                    ):
                        links.append(full_url)

                return {
                    "url": url,
                    "title": doc.title or "",
                    "content": "\n\n".join(
                        p for p in doc._extract_content_text().split("\n\n") if len(p.strip()) >= 20
                    ),
                    "headings": [
                        {"level": f"h{h.level}", "text": h.text, "id": h.id or ""}
                        for h in doc.headings
                        if h.level > 1
                    ],
                    "code_samples": [
                        {"code": cb.code, "language": cb.language or "unknown"}
                        for cb in doc.code_blocks
                    ],
                    "patterns": [],
                    "links": links,
                    "_enhanced": True,
                    "_tables": len(doc.tables),
                    "_images": len(doc.images),
                }
        except Exception as e:
            logger.debug(f"Enhanced markdown parser failed: {e}, using legacy parser")

        # Legacy extraction (fallback)
        page = {
            "url": url,
            "title": "",
            "content": "",
            "headings": [],
            "code_samples": [],
            "patterns": [],
            "links": [],
            "_enhanced": False,
        }

        lines = content.split("\n")

        # Extract title from first h1
        for line in lines:
            if line.startswith("# "):
                page["title"] = line[2:].strip()
                break

        # Extract headings (h2-h6)
        for line in lines:
            match = re.match(r"^(#{2,6})\s+(.+)$", line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                page["headings"].append(
                    {
                        "level": f"h{level}",
                        "text": text,
                        "id": text.lower().replace(" ", "-"),
                    }
                )

        # Extract code blocks with language
        code_blocks = re.findall(r"```(\w+)?\n(.*?)```", content, re.DOTALL)
        for lang, code in code_blocks:
            if len(code.strip()) > 10:
                page["code_samples"].append({"code": code.strip(), "language": lang or "unknown"})

        # Extract content (paragraphs)
        content_no_code = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        paragraphs = []
        for para in content_no_code.split("\n\n"):
            text = para.strip()
            # Skip headings and short text
            if text and len(text) > 20 and not text.startswith("#"):
                paragraphs.append(text)
        page["content"] = "\n\n".join(paragraphs)

        # Extract links from markdown (only .md files to avoid client-side rendered HTML pages)
        md_links = re.findall(r"\[([^\]]*)\]\(([^)]+)\)", content)
        for _, href in md_links:
            if href.startswith("http"):
                full_url = href
            elif not href.startswith("#"):
                full_url = urljoin(url, href)
            else:
                continue
            # Strip anchor fragments
            full_url = full_url.split("#")[0]
            # Only include .md URLs to avoid client-side rendered HTML pages
            if (
                self._has_md_extension(full_url)
                and self.is_valid_url(full_url)
                and full_url not in page["links"]
            ):
                page["links"].append(full_url)

        return page

    def _extract_html_as_markdown(self, html_content: str, url: str) -> dict[str, Any]:
        """Extract content from HTML and convert to markdown-like structure.

        Fallback method when .md URL returns HTML content instead of markdown.
        Uses BeautifulSoup to extract structured data from HTML elements.

        Extraction strategy:
        1. Title from <title> tag
        2. Main content from <main>, <article>, [role="main"], or <body>
        3. Headings (h1-h6) with text and id attributes
        4. Code blocks from <pre><code> or <pre> tags
        5. Text content from paragraphs

        Args:
            html_content: Raw HTML content string
            url: Source URL (for reference in result dict)

        Returns:
            Dict with keys:
                - url: str - Source URL
                - title: str - From <title> tag, cleaned
                - content: str - Text content from main area
                - headings: List[Dict] - {'level': 'h2', 'text': str, 'id': str}
                - code_samples: List[Dict] - {'code': str, 'language': str}
                - links: List - Empty (HTML links not extracted to avoid client-side routes)
                - patterns: List - Empty (reserved for future use)

        Note:
            Prefers <main> or <article> tags for content area.
            Falls back to <body> if no semantic content container found.
            Language detection uses detect_language() method.
        """
        page = {
            "url": url,
            "title": "",
            "content": "",
            "headings": [],
            "code_samples": [],
            "patterns": [],
            "links": [],
        }

        soup = BeautifulSoup(html_content, "html.parser")

        # Try to extract title
        title_elem = soup.select_one("title")
        if title_elem:
            page["title"] = self.clean_text(title_elem.get_text())

        # Try to find main content area
        main = soup.select_one('main, article, [role="main"], .content')
        if not main:
            main = soup.body if soup.body else soup

        if main:
            # Extract headings
            for h in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                text = self.clean_text(h.get_text())
                if text:
                    page["headings"].append({"level": h.name, "text": text, "id": h.get("id", "")})

            # Extract code blocks
            for code_elem in main.select("pre code, pre"):
                code = code_elem.get_text()
                if len(code.strip()) > 10:
                    lang = self.detect_language(code_elem, code)
                    page["code_samples"].append({"code": code.strip(), "language": lang})

            # Extract paragraphs
            paragraphs = []
            for p in main.find_all("p"):
                text = self.clean_text(p.get_text())
                if text and len(text) > 20:
                    paragraphs.append(text)
            page["content"] = "\n\n".join(paragraphs)

        return page

    def detect_language(self, elem, code):
        """Detect programming language from code block

        UPDATED: Now uses confidence-based detection with 20+ languages
        """
        lang, confidence = self.language_detector.detect_from_html(elem, code)

        # Log low-confidence detections for debugging
        if confidence < 0.5:
            logger.debug(f"Low confidence language detection: {lang} ({confidence:.2f})")

        return lang  # Return string for backward compatibility

    def extract_patterns(
        self, main: Any, _code_samples: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Extract common coding patterns (NEW FEATURE)"""
        patterns = []

        # Look for "Example:" or "Pattern:" sections
        for elem in main.find_all(["p", "div"]):
            text = elem.get_text().lower()
            if any(word in text for word in ["example:", "pattern:", "usage:", "typical use"]):
                # Get the code that follows
                next_code = elem.find_next(["pre", "code"])
                if next_code:
                    patterns.append(
                        {
                            "description": self.clean_text(elem.get_text()),
                            "code": next_code.get_text().strip(),
                        }
                    )

        return patterns[:5]  # Limit to 5 most relevant patterns

    def clean_text(self, text: str) -> str:
        """Clean text content"""
        return _WHITESPACE_RE.sub(" ", text).strip()

    def save_page(self, page: dict[str, Any]) -> None:
        """Save page data (skip pages with empty content)"""
        # Skip pages with empty or very short content
        if not page.get("content") or len(page.get("content", "")) < 50:
            self.pages_skipped += 1
            logger.debug("Skipping page with empty/short content: %s", page.get("url", "unknown"))
            return

        self.pages_saved += 1

        url_hash = hashlib.md5(page["url"].encode()).hexdigest()[:10]
        safe_title = _SAFE_TITLE_RE.sub("", page["title"])[:50]
        safe_title = _SAFE_TITLE_SEP_RE.sub("_", safe_title)

        filename = f"{safe_title}_{url_hash}.json"
        filepath = os.path.join(self.data_dir, "pages", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(page, f, indent=2, ensure_ascii=False)

    def _render_with_browser(self, url: str) -> str:
        """Render a page using headless browser (Playwright).

        Lazily initializes the BrowserRenderer on first call.

        Args:
            url: URL to render

        Returns:
            Fully-rendered HTML string
        """
        if self._browser_renderer is None:
            from skill_seekers.cli.browser_renderer import BrowserRenderer

            self._browser_renderer = BrowserRenderer(
                wait_until=self._browser_wait_until,
                extra_wait=self._browser_extra_wait,
            )
            logger.info(
                f"Launched headless browser for JavaScript rendering "
                f"(wait_until={self._browser_wait_until})"
            )
        return self._browser_renderer.render_page(url)

    def scrape_page(self, url: str) -> None:
        """Scrape a single page with thread-safe operations.

        Args:
            url (str): URL to scrape

        Returns:
            dict or None: Page data dict on success, None on failure

        Note:
            Uses threading locks when workers > 1 for thread safety
            Supports both HTML pages and Markdown (.md) files
        """
        try:
            # Sanitise brackets before fetching (safety net for start_urls; see #284)
            url = sanitize_url(url)

            # Scraping part (no lock needed - independent)
            if self.browser_mode and not self._has_md_extension(url):
                # Use Playwright headless browser for JavaScript rendering
                html = self._render_with_browser(url)
                soup = BeautifulSoup(html, "html.parser")
                page = self.extract_content(soup, url)
            else:
                headers = {"User-Agent": "Mozilla/5.0 (Documentation Scraper)"}
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()

                # Check if this is a Markdown file
                if self._has_md_extension(url):
                    page = self._extract_markdown_content(response.text, url)
                else:
                    soup = BeautifulSoup(response.content, "html.parser")
                    page = self.extract_content(soup, url)

            # Thread-safe operations (lock required for workers > 1)
            if self.workers > 1:
                with self.lock:
                    logger.info("  %s", url)
                    self.save_page(page)
                    self.pages.append(page)
                    for link in page["links"]:
                        self._enqueue_url(link)
            else:
                logger.info("  %s", url)
                self.save_page(page)
                self.pages.append(page)
                for link in page["links"]:
                    self._enqueue_url(link)

            # Rate limiting
            rate_limit = self.config.get("rate_limit", DEFAULT_RATE_LIMIT)
            if rate_limit > 0:
                time.sleep(rate_limit)

        except Exception as e:
            if self.workers > 1:
                with self.lock:
                    logger.error("  ✗ Error scraping %s: %s: %s", url, type(e).__name__, e)
            else:
                logger.error("  ✗ Error scraping page: %s: %s", type(e).__name__, e)
                logger.error("     URL: %s", url)

    async def scrape_page_async(
        self, url: str, semaphore: asyncio.Semaphore, client: httpx.AsyncClient
    ) -> None:
        """Scrape a single page asynchronously.

        Args:
            url: URL to scrape
            semaphore: Asyncio semaphore for concurrency control
            client: Shared httpx AsyncClient for connection pooling

        Note:
            Uses asyncio.Lock for async-safe operations instead of threading.Lock
            Supports both HTML pages and Markdown (.md) files
        """
        async with semaphore:  # Limit concurrent requests
            try:
                # Sanitise brackets before fetching (safety net; see #284)
                url = sanitize_url(url)

                if self.browser_mode and not self._has_md_extension(url):
                    # Use Playwright in executor (sync API in async context)
                    loop = asyncio.get_event_loop()
                    html = await loop.run_in_executor(None, self._render_with_browser, url)
                    soup = BeautifulSoup(html, "html.parser")
                    page = self.extract_content(soup, url)
                else:
                    # Async HTTP request
                    headers = {"User-Agent": "Mozilla/5.0 (Documentation Scraper)"}
                    response = await client.get(url, headers=headers, timeout=30.0)
                    response.raise_for_status()

                    # Check if this is a Markdown file
                    if self._has_md_extension(url):
                        page = self._extract_markdown_content(response.text, url)
                    else:
                        # BeautifulSoup parsing (still synchronous, but fast)
                        soup = BeautifulSoup(response.content, "html.parser")
                        page = self.extract_content(soup, url)

                # Async-safe operations (no lock needed - single event loop)
                logger.info("  %s", url)
                self.save_page(page)
                self.pages.append(page)

                # Add new URLs
                for link in page["links"]:
                    self._enqueue_url(link)

                # Rate limiting
                rate_limit = self.config.get("rate_limit", DEFAULT_RATE_LIMIT)
                if rate_limit > 0:
                    await asyncio.sleep(rate_limit)

            except Exception as e:
                logger.error("  ✗ Error scraping %s: %s: %s", url, type(e).__name__, e)

    def _convert_to_md_urls(self, urls: list[str]) -> list[str]:
        """
        Clean URLs from llms.txt: strip anchor fragments, deduplicate base URLs.

        Previously this method blindly appended /index.html.md to non-.md URLs,
        which caused 404 errors on sites that don't serve raw markdown files
        (e.g. Discord docs, see issue #277). Now it preserves original URLs as-is
        and lets the scraper handle both HTML and markdown content.

        Args:
            urls: List of URLs to process

        Returns:
            List of cleaned, deduplicated URLs (no anchors)
        """
        from urllib.parse import urlparse, urlunparse

        seen_base_urls = set()
        cleaned_urls = []

        for url in urls:
            # Parse URL to extract and remove fragment (anchor)
            parsed = urlparse(url)
            base_url = urlunparse(parsed._replace(fragment=""))  # Remove #anchor

            # Normalize trailing slashes for dedup (but keep original form)
            dedup_key = base_url.rstrip("/")

            # Skip if we've already processed this base URL
            if dedup_key in seen_base_urls:
                continue
            seen_base_urls.add(dedup_key)

            cleaned_urls.append(base_url)

        logger.info(
            "  ✓ Cleaned %d URLs to %d unique URLs (anchors stripped, will validate during crawl)",
            len(urls),
            len(cleaned_urls),
        )
        return cleaned_urls

    def _try_llms_txt(self) -> bool:
        """
        Try to use llms.txt instead of HTML scraping.
        Downloads ALL available variants and stores with .md extension.

        Returns:
            True if llms.txt was found and processed successfully
        """
        logger.info("\n🔍 Checking for llms.txt at %s...", self.base_url)

        # Check for explicit config URL first
        explicit_url = self.config.get("llms_txt_url")
        if explicit_url:
            logger.info("\n📌 Using explicit llms_txt_url from config: %s", explicit_url)

            # Download explicit file first
            downloader = LlmsTxtDownloader(explicit_url)
            content = downloader.download()

            if content:
                # Save explicit file with proper .md extension
                filename = downloader.get_proper_filename()
                filepath = os.path.join(self.skill_dir, "references", filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info("  💾 Saved %s (%d chars)", filename, len(content))

                # Also try to detect and download ALL other variants
                detector = LlmsTxtDetector(self.base_url)
                variants = detector.detect_all()

                if variants:
                    logger.info(
                        "\n🔍 Found %d total variant(s), downloading remaining...",
                        len(variants),
                    )
                    for variant_info in variants:
                        url = variant_info["url"]
                        variant = variant_info["variant"]

                        # Skip the explicit one we already downloaded
                        if url == explicit_url:
                            continue

                        logger.info("  📥 Downloading %s...", variant)
                        extra_downloader = LlmsTxtDownloader(url)
                        extra_content = extra_downloader.download()

                        if extra_content:
                            extra_filename = extra_downloader.get_proper_filename()
                            extra_filepath = os.path.join(
                                self.skill_dir, "references", extra_filename
                            )
                            with open(extra_filepath, "w", encoding="utf-8") as f:
                                f.write(extra_content)
                            logger.info(
                                "     ✓ %s (%d chars)",
                                extra_filename,
                                len(extra_content),
                            )

                # Parse explicit file for skill building
                parser = LlmsTxtParser(content, self.base_url)

                # Extract URLs from llms.txt and add to pending_urls for BFS crawling
                extracted_urls = parser.extract_urls()
                if extracted_urls:
                    # Clean URLs: strip anchors, deduplicate
                    cleaned_urls = self._convert_to_md_urls(extracted_urls)
                    logger.info(
                        "\n🔗 Found %d URLs in llms.txt (%d unique), starting BFS crawl...",
                        len(extracted_urls),
                        len(cleaned_urls),
                    )

                    # Filter URLs based on url_patterns config
                    for url in cleaned_urls:
                        if self.is_valid_url(url):
                            self._enqueue_url(url)

                    logger.info(
                        "  📋 %d URLs added to crawl queue after filtering",
                        len(self.pending_urls),
                    )

                    # Return False to trigger HTML scraping with the populated pending_urls
                    self.llms_txt_detected = True
                    self.llms_txt_variant = "explicit"
                    return False  # Continue with BFS crawling

                # Fallback: if no URLs found, use section-based parsing
                pages = parser.parse()

                if pages:
                    for page in pages:
                        self.save_page(page)
                        self.pages.append(page)

                    self.llms_txt_detected = True
                    self.llms_txt_variant = "explicit"
                    return True

        # Auto-detection: Find ALL variants
        detector = LlmsTxtDetector(self.base_url)
        variants = detector.detect_all()

        if not variants:
            logger.info("ℹ️  No llms.txt found, using HTML scraping")
            return False

        logger.info("✅ Found %d llms.txt variant(s)", len(variants))

        # Download ALL variants
        downloaded = {}
        for variant_info in variants:
            url = variant_info["url"]
            variant = variant_info["variant"]

            logger.info("  📥 Downloading %s...", variant)
            downloader = LlmsTxtDownloader(url)
            content = downloader.download()

            if content:
                filename = downloader.get_proper_filename()
                downloaded[variant] = {
                    "content": content,
                    "filename": filename,
                    "size": len(content),
                }
                logger.info("     ✓ %s (%d chars)", filename, len(content))

        if not downloaded:
            logger.warning("⚠️  Failed to download any variants, falling back to HTML scraping")
            return False

        # Save ALL variants to references/
        os.makedirs(os.path.join(self.skill_dir, "references"), exist_ok=True)

        for _variant, data in downloaded.items():
            filepath = os.path.join(self.skill_dir, "references", data["filename"])
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(data["content"])
            logger.info("  💾 Saved %s", data["filename"])

        # Parse LARGEST variant for skill building
        largest = max(downloaded.items(), key=lambda x: x[1]["size"])
        logger.info("\n📄 Parsing %s for skill building...", largest[1]["filename"])

        parser = LlmsTxtParser(largest[1]["content"], self.base_url)

        # Extract URLs from llms.txt and add to pending_urls for BFS crawling
        extracted_urls = parser.extract_urls()
        if extracted_urls:
            # Clean URLs: strip anchors, deduplicate
            cleaned_urls = self._convert_to_md_urls(extracted_urls)
            logger.info(
                "\n🔗 Found %d URLs in llms.txt (%d unique), starting BFS crawl...",
                len(extracted_urls),
                len(cleaned_urls),
            )

            # Filter URLs based on url_patterns config
            for url in cleaned_urls:
                if self.is_valid_url(url):
                    self._enqueue_url(url)

            logger.info(
                "  📋 %d URLs added to crawl queue after filtering",
                len(self.pending_urls),
            )

            # Return False to trigger HTML scraping with the populated pending_urls
            self.llms_txt_detected = True
            self.llms_txt_variants = list(downloaded.keys())
            return False  # Continue with BFS crawling

        # Fallback: if no URLs found, use section-based parsing
        pages = parser.parse()

        if not pages:
            logger.warning("⚠️  Failed to parse llms.txt, falling back to HTML scraping")
            return False

        logger.info("  ✓ Parsed %d sections", len(pages))

        # Save pages for skill building
        for page in pages:
            self.save_page(page)
            self.pages.append(page)

        self.llms_txt_detected = True
        self.llms_txt_variants = list(downloaded.keys())

        return True

    def _try_sitemap(self) -> list[str]:
        """Layer 1: Try to discover pages via sitemap.xml.

        Checks common sitemap locations at the domain root.
        Parses XML for <loc> tags, filters by is_valid_url().

        Returns:
            List of discovered valid URLs (empty if no sitemap found).
        """
        try:
            import defusedxml.ElementTree as ET
        except ImportError:
            import xml.etree.ElementTree as ET

        from urllib.parse import urlparse

        parsed = urlparse(self.base_url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        sitemap_urls_to_try = [
            f"{domain}/sitemap.xml",
            f"{domain}/sitemap_index.xml",
        ]

        discovered = []

        for sitemap_url in sitemap_urls_to_try:
            try:
                response = requests.get(
                    sitemap_url, timeout=10, headers={"User-Agent": "SkillSeekers/3.4"}
                )
                if response.status_code != 200:
                    continue

                if "xml" not in response.headers.get("content-type", ""):
                    continue

                root = ET.fromstring(response.text)
                ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

                # Handle sitemap index (nested sitemaps)
                for sitemap in root.findall(".//sm:sitemap/sm:loc", ns):
                    try:
                        sub_resp = requests.get(
                            sitemap.text.strip(),
                            timeout=10,
                            headers={"User-Agent": "SkillSeekers/3.4"},
                        )
                        if sub_resp.status_code == 200:
                            sub_root = ET.fromstring(sub_resp.text)
                            for loc in sub_root.findall(".//sm:url/sm:loc", ns):
                                url = loc.text.strip().split("#")[0]
                                if self.is_valid_url(url):
                                    discovered.append(url)
                    except Exception:
                        continue

                # Handle direct sitemap
                for loc in root.findall(".//sm:url/sm:loc", ns):
                    url = loc.text.strip().split("#")[0]
                    if self.is_valid_url(url):
                        discovered.append(url)

                if discovered:
                    logger.info(f"📋 Found sitemap at {sitemap_url} ({len(discovered)} valid URLs)")
                    return list(set(discovered))

            except Exception as e:
                logger.debug(f"Sitemap check failed for {sitemap_url}: {e}")
                continue

        return []

    def _discover_spa_nav(self) -> list[str]:
        """Layer 3: Render index page with networkidle to discover SPA navigation.

        Used when browser mode is on and sitemap/llms.txt didn't find pages.
        Renders the first page with networkidle (slower but discovers full nav),
        then normal crawl uses domcontentloaded (fast).

        Returns:
            List of discovered valid URLs from the rendered navigation.
        """
        if not self.browser_mode:
            return []

        logger.info("🌐 Rendering index page with networkidle to discover SPA navigation...")

        try:
            from skill_seekers.cli.browser_renderer import BrowserRenderer

            # Use a separate renderer with networkidle for discovery only
            discovery_renderer = BrowserRenderer(
                timeout=60000,
                wait_until="networkidle",
                extra_wait=3000,  # 3s extra for lazy-loaded nav
            )
            html = discovery_renderer.render_page(self.base_url)
            discovery_renderer.close()

            # Parse rendered DOM for all links
            soup = BeautifulSoup(html, "html.parser")
            discovered = []
            seen = set()

            for link in soup.find_all("a", href=True):
                href = urljoin(self.base_url, link["href"]).split("#")[0]
                if href not in seen and self.is_valid_url(href):
                    seen.add(href)
                    discovered.append(href)

            if discovered:
                logger.info(f"🌐 Discovered {len(discovered)} pages from rendered SPA navigation")

            return discovered

        except Exception as e:
            logger.warning(f"⚠️  SPA navigation discovery failed: {e}")
            return []

    def scrape_all(self) -> None:
        """Scrape all pages (supports llms.txt and HTML scraping)

        Routes to async version if async_mode is enabled in config.
        """
        # Route to async version if enabled
        if self.async_mode:
            asyncio.run(self.scrape_all_async())
            return

        # === Three-Layer Discovery Engine ===
        # Discovers pages before the BFS crawl loop starts.
        # Layer 1: sitemap.xml — instant, no rendering needed
        # Layer 2: llms.txt — existing mechanism
        # Layer 3: SPA nav — renders index with networkidle to find JS-rendered links

        if not self.dry_run:
            # Layer 1: Try sitemap.xml
            sitemap_urls = self._try_sitemap()
            if sitemap_urls:
                for url in sitemap_urls:
                    self._enqueue_url(url)

            # Layer 2: Try llms.txt (unless explicitly disabled)
            if not sitemap_urls and not self.skip_llms_txt:
                llms_result = self._try_llms_txt()
                if llms_result:
                    logger.info(
                        "\n✅ Used llms.txt (%s) - skipping HTML scraping",
                        self.llms_txt_variant,
                    )
                    self.save_summary()
                    return

            # Layer 3: SPA nav discovery (browser mode only, when other layers found few pages)
            if self.browser_mode and len(self.pending_urls) <= 1:
                spa_urls = self._discover_spa_nav()
                for url in spa_urls:
                    self._enqueue_url(url)

        # HTML scraping (sync/thread-based logic)
        logger.info("\n" + "=" * 60)
        if self.dry_run:
            logger.info("DRY RUN: %s", self.name)
        else:
            logger.info("SCRAPING: %s", self.name)
        logger.info("=" * 60)
        logger.info("Base URL: %s", self.base_url)

        if self.dry_run:
            logger.info("Mode: Preview only (no actual scraping)\n")
        else:
            logger.info("Output: %s", self.data_dir)
            if self.workers > 1:
                logger.info("Workers: %d parallel threads", self.workers)
            logger.info("")

        max_pages = self.config.get("max_pages", DEFAULT_MAX_PAGES)

        # Handle unlimited mode
        if max_pages is None or max_pages == -1:
            logger.warning("⚠️  UNLIMITED MODE: No page limit (will scrape all pages)\n")
            unlimited = True
        else:
            unlimited = False

        # Dry run: preview first 20 URLs
        preview_limit = 20 if self.dry_run else max_pages

        # Single-threaded mode (original sequential logic)
        if self.workers <= 1:
            while self.pending_urls and (unlimited or len(self.visited_urls) < preview_limit):
                url = self.pending_urls.popleft()

                if url in self.visited_urls:
                    continue

                self.visited_urls.add(url)

                if self.dry_run:
                    # Just show what would be scraped
                    url = sanitize_url(url)  # encode brackets before fetch (see #284)
                    logger.info("  [Preview] %s", url)
                    try:
                        headers = {"User-Agent": "Mozilla/5.0 (Documentation Scraper - Dry Run)"}
                        response = requests.get(url, headers=headers, timeout=10)
                        soup = BeautifulSoup(response.content, "html.parser")

                        # Discover links from full page (not just main content)
                        # to match real scrape path behaviour in extract_content()
                        for link in soup.find_all("a", href=True):
                            href = urljoin(url, link["href"])
                            href = href.split("#")[0]
                            if self.is_valid_url(href):
                                self._enqueue_url(href)
                    except Exception as e:
                        # Failed to extract links in fast mode, continue anyway
                        logger.warning("⚠️  Warning: Could not extract links from %s: %s", url, e)
                else:
                    self.scrape_page(url)
                    self.pages_scraped += 1

                    if (
                        self.checkpoint_enabled
                        and self.pages_scraped % self.checkpoint_interval == 0
                    ):
                        self.save_checkpoint()

                if len(self.visited_urls) % 10 == 0:
                    logger.info("  [%d pages]", len(self.visited_urls))

        # Multi-threaded mode (parallel scraping)
        else:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            logger.info("🚀 Starting parallel scraping with %d workers\n", self.workers)

            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = []

                while self.pending_urls and (unlimited or len(self.visited_urls) < preview_limit):
                    # Get next batch of URLs (thread-safe)
                    batch = []
                    batch_size = min(self.workers * 2, len(self.pending_urls))

                    with self.lock:
                        for _ in range(batch_size):
                            if not self.pending_urls:
                                break
                            url = self.pending_urls.popleft()

                            if url not in self.visited_urls:
                                self.visited_urls.add(url)
                                batch.append(url)

                    # Submit batch to executor
                    for url in batch:
                        if unlimited or len(self.visited_urls) <= preview_limit:
                            future = executor.submit(self.scrape_page, url)
                            futures.append(future)

                    # Wait for some to complete before submitting more
                    for future in as_completed(futures[:batch_size]):
                        # Check for exceptions
                        try:
                            future.result()  # Raises exception if scrape_page failed
                        except Exception as e:
                            with self.lock:
                                logger.warning("  ⚠️  Worker exception: %s", e)

                        with self.lock:
                            self.pages_scraped += 1

                            if (
                                self.checkpoint_enabled
                                and self.pages_scraped % self.checkpoint_interval == 0
                            ):
                                self.save_checkpoint()

                            if self.pages_scraped % 10 == 0:
                                logger.info("  [%d pages scraped]", self.pages_scraped)

                    # Remove completed futures
                    futures = [f for f in futures if not f.done()]

                # Wait for remaining futures
                for future in as_completed(futures):
                    # Check for exceptions
                    try:
                        future.result()
                    except Exception as e:
                        with self.lock:
                            logger.warning("  ⚠️  Worker exception: %s", e)

                    with self.lock:
                        self.pages_scraped += 1

        if self.dry_run:
            logger.info("\n✅ Dry run complete: would scrape ~%d pages", len(self.visited_urls))
            if len(self.visited_urls) >= preview_limit:
                logger.info(
                    "   (showing first %d, actual scraping may find more)",
                    preview_limit,
                )
            logger.info("\n💡 To actually scrape, run without --dry-run")
        else:
            self._log_scrape_completion()
            self.save_summary()

    async def scrape_all_async(self) -> None:
        """Scrape all pages asynchronously (async/await version).

        This method provides significantly better performance for parallel scraping
        compared to thread-based scraping, with lower memory overhead and better
        CPU utilization.

        Performance: ~2-3x faster than sync mode with same worker count.
        """
        # Try llms.txt first (unless dry-run or explicitly disabled)
        if not self.dry_run and not self.skip_llms_txt:
            llms_result = self._try_llms_txt()
            if llms_result:
                logger.info(
                    "\n✅ Used llms.txt (%s) - skipping HTML scraping",
                    self.llms_txt_variant,
                )
                self.save_summary()
                return

        # HTML scraping (async version)
        logger.info("\n" + "=" * 60)
        if self.dry_run:
            logger.info("DRY RUN (ASYNC): %s", self.name)
        else:
            logger.info("SCRAPING (ASYNC): %s", self.name)
        logger.info("=" * 60)
        logger.info("Base URL: %s", self.base_url)

        if self.dry_run:
            logger.info("Mode: Preview only (no actual scraping)\n")
        else:
            logger.info("Output: %s", self.data_dir)
            logger.info("Workers: %d concurrent tasks (async)", self.workers)
            logger.info("")

        max_pages = self.config.get("max_pages", DEFAULT_MAX_PAGES)

        # Handle unlimited mode
        if max_pages is None or max_pages == -1:
            logger.warning("⚠️  UNLIMITED MODE: No page limit (will scrape all pages)\n")
            unlimited = True
            preview_limit = float("inf")
        else:
            unlimited = False
            preview_limit = 20 if self.dry_run else max_pages

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.workers)

        # Create shared HTTP client with connection pooling
        async with httpx.AsyncClient(
            timeout=30.0, limits=httpx.Limits(max_connections=self.workers * 2)
        ) as client:
            tasks = []

            while self.pending_urls and (unlimited or len(self.visited_urls) < preview_limit):
                # Get next batch of URLs
                batch = []
                batch_size = min(self.workers * 2, len(self.pending_urls))

                for _ in range(batch_size):
                    if not self.pending_urls:
                        break
                    url = self.pending_urls.popleft()

                    if url not in self.visited_urls:
                        self.visited_urls.add(url)
                        batch.append(url)

                # Create async tasks for batch
                for url in batch:
                    if unlimited or len(self.visited_urls) <= preview_limit:
                        if self.dry_run:
                            url = sanitize_url(url)  # encode brackets (see #284)
                            logger.info("  [Preview] %s", url)
                            # Discover links from full page (async dry-run)
                            try:
                                response = await client.get(
                                    url,
                                    headers={
                                        "User-Agent": "Mozilla/5.0 (Documentation Scraper - Dry Run)"
                                    },
                                    timeout=10,
                                )
                                soup = BeautifulSoup(response.content, "html.parser")
                                for link in soup.find_all("a", href=True):
                                    href = urljoin(url, link["href"])
                                    href = href.split("#")[0]
                                    if self.is_valid_url(href):
                                        self._enqueue_url(href)
                            except Exception as e:
                                logger.warning(
                                    "⚠️  Warning: Could not extract links from %s: %s", url, e
                                )
                        else:
                            task = asyncio.create_task(
                                self.scrape_page_async(url, semaphore, client)
                            )
                            tasks.append(task)

                # Wait for batch to complete before continuing
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in results:
                        if isinstance(result, Exception):
                            logger.error(
                                "  ✗ Async task failed: %s: %s", type(result).__name__, result
                            )
                    tasks = []
                    self.pages_scraped = len(self.visited_urls)

                    # Progress indicator
                    if self.pages_scraped % 10 == 0 and not self.dry_run:
                        logger.info("  [%d pages scraped]", self.pages_scraped)

                    # Checkpoint saving
                    if (
                        not self.dry_run
                        and self.checkpoint_enabled
                        and self.pages_scraped % self.checkpoint_interval == 0
                    ):
                        self.save_checkpoint()

            # Wait for any remaining tasks
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        logger.error("  ✗ Async task failed: %s: %s", type(result).__name__, result)

        if self.dry_run:
            logger.info("\n✅ Dry run complete: would scrape ~%d pages", len(self.visited_urls))
            if len(self.visited_urls) >= preview_limit:
                logger.info(
                    "   (showing first %d, actual scraping may find more)",
                    int(preview_limit),
                )
            logger.info("\n💡 To actually scrape, run without --dry-run")
        else:
            self._log_scrape_completion()
            self.save_summary()

        # Clean up browser renderer if used
        if self._browser_renderer is not None:
            self._browser_renderer.close()
            self._browser_renderer = None

    def _log_scrape_completion(self) -> None:
        """Log scrape completion with accurate saved/skipped counts."""
        visited = len(self.visited_urls)
        if self.pages_skipped > 0:
            logger.info(
                "\n✅ Scraped %d pages (%d saved, %d skipped - empty content)",
                visited,
                self.pages_saved,
                self.pages_skipped,
            )
        else:
            logger.info(
                "\n✅ Scraped %d pages (%d saved)",
                visited,
                self.pages_saved,
            )

        # SPA detection: warn when most pages had empty content
        if visited >= 5 and self.pages_saved == 0:
            logger.warning(
                "⚠️  All %d pages had empty content. This site likely requires "
                "JavaScript rendering (SPA/React/Vue).\n"
                "   Try: skill-seekers create <url> --browser\n"
                "   Install: pip install 'skill-seekers[browser]'",
                visited,
            )
        elif visited >= 10 and self.pages_skipped > 0:
            skip_ratio = self.pages_skipped / visited
            if skip_ratio > 0.8:
                logger.warning(
                    "⚠️  %d%% of pages had empty content. This site may use "
                    "JavaScript rendering for some pages.\n"
                    "   Try: skill-seekers create <url> --browser",
                    int(skip_ratio * 100),
                )

    def save_summary(self) -> None:
        """Save scraping summary"""
        summary = {
            "name": self.name,
            "total_pages": len(self.pages),
            "base_url": self.base_url,
            "llms_txt_detected": self.llms_txt_detected,
            "llms_txt_variant": self.llms_txt_variant,
            "pages": [{"title": p["title"], "url": p["url"]} for p in self.pages],
        }

        try:
            with open(f"{self.data_dir}/summary.json", "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.error("  ✗ Failed to save summary: %s", e)

    def load_scraped_data(self) -> list[dict[str, Any]]:
        """Load previously scraped data"""
        pages = []
        pages_dir = Path(self.data_dir) / "pages"

        if not pages_dir.exists():
            return []

        for json_file in pages_dir.glob("*.json"):
            try:
                with open(json_file, encoding="utf-8") as f:
                    pages.append(json.load(f))
            except Exception as e:
                logger.error(
                    "⚠️  Error loading scraped data file %s: %s: %s",
                    json_file,
                    type(e).__name__,
                    e,
                )
                logger.error(
                    "   Suggestion: File may be corrupted, consider re-scraping with --fresh"
                )

        return pages

    def smart_categorize(self, pages: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Improved categorization with better pattern matching"""
        category_defs = self.config.get("categories", {})

        # Default smart categories if none provided
        if not category_defs:
            category_defs = self.infer_categories(pages)

        categories: dict[str, list[dict[str, Any]]] = {cat: [] for cat in category_defs}
        categories["other"] = []

        # Pre-lowercase keywords once instead of per-page per-keyword
        lowered_defs = {
            cat: [kw.lower() for kw in keywords] for cat, keywords in category_defs.items()
        }

        for page in pages:
            url = page["url"].lower()
            title = page["title"].lower()
            content = page.get("content", "").lower()[
                :CONTENT_PREVIEW_LENGTH
            ]  # Check first N chars for categorization

            categorized = False

            # Match against pre-lowercased keywords
            for cat, keywords in lowered_defs.items():
                score = 0
                for keyword in keywords:
                    if keyword in url:
                        score += 3
                    if keyword in title:
                        score += 2
                    if keyword in content:
                        score += 1

                if score >= MIN_CATEGORIZATION_SCORE:  # Threshold for categorization
                    categories[cat].append(page)
                    categorized = True
                    break

            if not categorized:
                categories["other"].append(page)

        # Remove empty categories
        categories = {k: v for k, v in categories.items() if v}

        return categories

    def infer_categories(self, pages: list[dict[str, Any]]) -> dict[str, list[str]]:
        """Infer categories from URL patterns (IMPROVED)"""
        url_segments: defaultdict[str, int] = defaultdict(int)

        for page in pages:
            path = urlparse(page["url"]).path
            segments = [
                s for s in path.split("/") if s and s not in ["en", "stable", "latest", "docs"]
            ]

            for seg in segments:
                url_segments[seg] += 1

        # Top segments become categories
        top_segments = sorted(url_segments.items(), key=lambda x: x[1], reverse=True)[:8]

        categories = {}
        for seg, count in top_segments:
            if count >= 3:  # At least 3 pages
                categories[seg] = [seg]

        # Add common defaults (use pre-built URL list to avoid repeated comprehensions)
        all_urls = [p["url"] for p in pages]
        if "tutorials" not in categories and any("tutorial" in url for url in all_urls):
            categories["tutorials"] = ["tutorial", "guide", "getting-started"]

        if "api" not in categories and any("api" in url or "reference" in url for url in all_urls):
            categories["api"] = ["api", "reference", "class"]

        return categories

    def generate_quick_reference(self, pages: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Generate quick reference from common patterns (NEW FEATURE)"""
        quick_ref = []

        # Collect all patterns
        all_patterns = []
        for page in pages:
            all_patterns.extend(page.get("patterns", []))

        # Get most common code patterns
        seen_codes = set()
        for pattern in all_patterns:
            code = pattern["code"]
            if code not in seen_codes and len(code) < 300:
                quick_ref.append(pattern)
                seen_codes.add(code)
                if len(quick_ref) >= 15:
                    break

        return quick_ref

    def create_reference_file(self, category: str, pages: list[dict[str, Any]]) -> None:
        """Create enhanced reference file"""
        if not pages:
            return

        lines = []
        lines.append(f"# {self.name.title()} - {category.replace('_', ' ').title()}\n")
        lines.append(f"**Pages:** {len(pages)}\n")
        lines.append("---\n")

        for page in pages:
            lines.append(f"## {page['title']}\n")
            lines.append(f"**URL:** {page['url']}\n")

            # Table of contents from headings
            if page.get("headings"):
                lines.append("**Contents:**")
                for h in page["headings"][:10]:
                    level = int(h["level"][1]) if len(h["level"]) > 1 else 1
                    indent = "  " * max(0, level - 2)
                    lines.append(f"{indent}- {h['text']}")
                lines.append("")

            # Content (NO TRUNCATION)
            if page.get("content"):
                lines.append(page["content"])
                lines.append("")

            # Code examples with language (NO TRUNCATION)
            if page.get("code_samples"):
                lines.append("**Examples:**\n")
                for i, sample in enumerate(page["code_samples"][:4], 1):
                    lang = sample.get("language", "unknown")
                    code = sample.get("code", sample if isinstance(sample, str) else "")
                    lines.append(f"Example {i} ({lang}):")
                    lines.append(f"```{lang}")
                    lines.append(code)  # Full code, no truncation
                    lines.append("```\n")

            lines.append("---\n")

        filepath = os.path.join(self.skill_dir, "references", f"{category}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info("  ✓ %s.md (%d pages)", category, len(pages))

    def create_enhanced_skill_md(
        self,
        categories: dict[str, list[dict[str, Any]]],
        quick_ref: list[dict[str, str]],
    ) -> None:
        """Create SKILL.md with actual examples (IMPROVED)"""
        # Try to infer description if not in config
        if "description" not in self.config:
            # Get first page HTML content to infer description
            first_page_html = None
            for pages in categories.values():
                if pages:
                    first_page_html = pages[0].get("raw_html", "")
                    break
            description = infer_description_from_docs(self.base_url, first_page_html, self.name)
        else:
            description = self.config["description"]

        # Extract actual code examples from docs
        example_codes = []
        for pages in categories.values():
            for page in pages[:3]:  # First 3 pages per category
                for sample in page.get("code_samples", [])[:2]:  # First 2 samples per page
                    code = sample.get("code", sample if isinstance(sample, str) else "")
                    lang = sample.get("language", "unknown")
                    if len(code) < 200 and lang != "unknown":
                        example_codes.append((lang, code))
                    if len(example_codes) >= 10:
                        break
                if len(example_codes) >= 10:
                    break
            if len(example_codes) >= 10:
                break

        doc_version = self.config.get("doc_version", "")
        content = f"""---
name: {self.name}
description: {description}
doc_version: {doc_version}
---

# {self.name.title()} Skill

{description.capitalize()}, generated from official documentation.

## When to Use This Skill

This skill should be triggered when:
- Working with {self.name}
- Asking about {self.name} features or APIs
- Implementing {self.name} solutions
- Debugging {self.name} code
- Learning {self.name} best practices

## Quick Reference

### Common Patterns

"""

        # Add actual quick reference patterns
        if quick_ref:
            for i, pattern in enumerate(quick_ref[:8], 1):
                desc = pattern.get("description", "Example pattern")
                # Format description: extract first sentence, truncate if too long
                first_sentence = desc.split(".")[0] if "." in desc else desc
                if len(first_sentence) > 150:
                    first_sentence = first_sentence[:147] + "..."

                content += f"**Pattern {i}:** {first_sentence}\n\n"
                content += "```\n"
                content += pattern.get("code", "")[:300]
                content += "\n```\n\n"
        else:
            content += "*Quick reference patterns will be added as you use the skill.*\n\n"

        # Add example codes from docs
        if example_codes:
            content += "### Example Code Patterns\n\n"
            for i, (lang, code) in enumerate(example_codes[:5], 1):
                content += f"**Example {i}** ({lang}):\n```{lang}\n{code}\n```\n\n"

        content += """## Reference Files

This skill includes comprehensive documentation in `references/`:

"""

        for cat in sorted(categories.keys()):
            content += f"- **{cat}.md** - {cat.replace('_', ' ').title()} documentation\n"

        content += """
Use `view` to read specific reference files when detailed information is needed.

## Working with This Skill

### For Beginners
Start with the getting_started or tutorials reference files for foundational concepts.

### For Specific Features
Use the appropriate category reference file (api, guides, etc.) for detailed information.

### For Code Examples
The quick reference section above contains common patterns extracted from the official docs.

## Resources

### references/
Organized documentation extracted from official sources. These files contain:
- Detailed explanations
- Code examples with language annotations
- Links to original documentation
- Table of contents for quick navigation

### scripts/
Add helper scripts here for common automation tasks.

### assets/
Add templates, boilerplate, or example projects here.

## Notes

- This skill was automatically generated from official documentation
- Reference files preserve the structure and examples from source docs
- Code examples include language detection for better syntax highlighting
- Quick reference patterns are extracted from common usage examples in the docs

## Updating

To refresh this skill with updated documentation:
1. Re-run the scraper with the same configuration
2. The skill will be rebuilt with the latest information
"""

        filepath = os.path.join(self.skill_dir, "SKILL.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info("  ✓ SKILL.md (enhanced with %d examples)", len(example_codes))

    def create_index(self, categories: dict[str, list[dict[str, Any]]]) -> None:
        """Create navigation index"""
        lines = []
        lines.append(f"# {self.name.title()} Documentation Index\n")
        lines.append("## Categories\n")

        for cat, pages in sorted(categories.items()):
            lines.append(f"### {cat.replace('_', ' ').title()}")
            lines.append(f"**File:** `{cat}.md`")
            lines.append(f"**Pages:** {len(pages)}\n")

        filepath = os.path.join(self.skill_dir, "references", "index.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info("  ✓ index.md")

    def extract(self):
        """SkillConverter interface — delegates to scrape_all()."""
        self.scrape_all()

    def build_skill(self) -> bool:
        """Build the skill from scraped data.

        Loads scraped JSON files, categorizes pages, extracts patterns,
        and generates SKILL.md and reference files.

        Returns:
            bool: True if build succeeded, False otherwise
        """
        logger.info("\n" + "=" * 60)
        logger.info("BUILDING SKILL: %s", self.name)
        logger.info("=" * 60 + "\n")

        # Load data
        logger.info("Loading scraped data...")
        pages = self.load_scraped_data()

        if not pages:
            logger.error("✗ No scraped data found!")
            if self.pages_skipped > 0:
                logger.error(
                    "   %d pages were visited but had empty content. "
                    "The site may require JavaScript rendering (SPA).",
                    self.pages_skipped,
                )
            return False

        logger.info("  ✓ Loaded %d pages\n", len(pages))

        # Categorize
        logger.info("Categorizing pages...")
        categories = self.smart_categorize(pages)
        logger.info("  ✓ Created %d categories\n", len(categories))

        # Generate quick reference
        logger.info("Generating quick reference...")
        quick_ref = self.generate_quick_reference(pages)
        logger.info("  ✓ Extracted %d patterns\n", len(quick_ref))

        # Create reference files
        logger.info("Creating reference files...")
        for cat, cat_pages in categories.items():
            self.create_reference_file(cat, cat_pages)

        # Create index
        self.create_index(categories)
        logger.info("")

        # Create enhanced SKILL.md
        logger.info("Creating SKILL.md...")
        self.create_enhanced_skill_md(categories, quick_ref)

        logger.info("\n✅ Skill built: %s/", self.skill_dir)
        return True


def validate_config(config: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Validate configuration structure and values.

    Args:
        config (dict): Configuration dictionary to validate

    Returns:
        tuple: (errors, warnings) where each is a list of strings

    Example:
        >>> errors, warnings = validate_config({'name': 'test', 'base_url': 'https://example.com'})
        >>> if errors:
        ...     print("Invalid config:", errors)
    """
    errors = []
    warnings = []

    # Required fields
    required_fields = ["name", "base_url"]
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: '{field}'")

    # Validate name (alphanumeric, hyphens, underscores only)
    if "name" in config and not re.match(r"^[a-zA-Z0-9_-]+$", config["name"]):
        errors.append(
            f"Invalid name: '{config['name']}' (use only letters, numbers, hyphens, underscores)"
        )

    # Validate base_url
    if "base_url" in config and not config["base_url"].startswith(("http://", "https://")):
        errors.append(
            f"Invalid base_url: '{config['base_url']}' (must start with http:// or https://)"
        )

    # Validate selectors structure
    if "selectors" in config:
        if not isinstance(config["selectors"], dict):
            errors.append("'selectors' must be a dictionary")
        else:
            recommended_selectors = ["main_content", "title", "code_blocks"]
            for selector in recommended_selectors:
                if selector not in config["selectors"]:
                    warnings.append(f"Missing recommended selector: '{selector}'")
    else:
        warnings.append("Missing 'selectors' section (recommended)")

    # Validate url_patterns
    if "url_patterns" in config:
        if not isinstance(config["url_patterns"], dict):
            errors.append("'url_patterns' must be a dictionary")
        else:
            for key in ["include", "exclude"]:
                if key in config["url_patterns"] and not isinstance(
                    config["url_patterns"][key], list
                ):
                    errors.append(f"'url_patterns.{key}' must be a list")

    # Validate categories
    if "categories" in config:
        if not isinstance(config["categories"], dict):
            errors.append("'categories' must be a dictionary")
        else:
            for cat_name, keywords in config["categories"].items():
                if not isinstance(keywords, list):
                    errors.append(f"'categories.{cat_name}' must be a list of keywords")

    # Validate rate_limit
    if "rate_limit" in config:
        try:
            rate = float(config["rate_limit"])
            if rate < 0:
                errors.append(f"'rate_limit' must be non-negative (got {rate})")
            elif rate > 10:
                warnings.append(
                    f"'rate_limit' is very high ({rate}s) - this may slow down scraping significantly"
                )
        except (ValueError, TypeError):
            errors.append(f"'rate_limit' must be a number (got {config['rate_limit']})")

    # Validate max_pages
    if "max_pages" in config:
        max_p_value = config["max_pages"]

        # Allow None for unlimited
        if max_p_value is None:
            warnings.append(
                "'max_pages' is None (unlimited) - this will scrape ALL pages. Use with caution!"
            )
        else:
            try:
                max_p = int(max_p_value)
                # Allow -1 for unlimited
                if max_p == -1:
                    warnings.append(
                        "'max_pages' is -1 (unlimited) - this will scrape ALL pages. Use with caution!"
                    )
                elif max_p < 1:
                    errors.append(
                        f"'max_pages' must be at least 1 or -1 for unlimited (got {max_p})"
                    )
                elif max_p > MAX_PAGES_WARNING_THRESHOLD:
                    warnings.append(
                        f"'max_pages' is very high ({max_p}) - scraping may take a very long time"
                    )
            except (ValueError, TypeError):
                errors.append(
                    f"'max_pages' must be an integer, -1, or null (got {config['max_pages']})"
                )

    # Validate start_urls if present
    if "start_urls" in config:
        if not isinstance(config["start_urls"], list):
            errors.append("'start_urls' must be a list")
        else:
            for url in config["start_urls"]:
                if not url.startswith(("http://", "https://")):
                    errors.append(
                        f"Invalid start_url: '{url}' (must start with http:// or https://)"
                    )

    return errors, warnings


def load_config(config_path: str) -> dict[str, Any]:
    """Load and validate configuration from JSON file.

    Automatically fetches configs from SkillSeekersWeb.com API if not found locally.

    Args:
        config_path (str): Path to JSON configuration file

    Returns:
        dict: Validated configuration dictionary

    Raises:
        SystemExit: If config is invalid or file not found

    Example:
        >>> config = load_config('configs/react.json')
        >>> print(config['name'])
        'react'
    """
    # Try to resolve config path (with auto-fetch from API)
    resolved_path = resolve_config_path(config_path, auto_fetch=True)

    if resolved_path is None:
        # Config not found locally and fetch failed
        available = list_available_configs()
        searched_paths = get_last_searched_paths()

        logger.error("❌ Error: Config file not found: %s", config_path)
        logger.error("")
        logger.error("   Searched in these locations:")
        for i, path in enumerate(searched_paths, 1):
            logger.error("     %d. %s", i, path)
        logger.error("     %d. SkillSeekersWeb.com API", len(searched_paths) + 1)
        logger.error("")

        # Show where user should place custom configs
        user_config_dir = Path.home() / ".config" / "skill-seekers" / "configs"
        logger.error("   💡 To use a custom config, place it in one of these locations:")
        logger.error("      • Current directory: ./configs/%s", Path(config_path).name)
        logger.error("      • User config directory: %s", user_config_dir / Path(config_path).name)
        logger.error("      • Absolute path: /full/path/to/%s", Path(config_path).name)
        logger.error("")

        if available:
            logger.error("   📋 Or use a preset config from API (%d total):", len(available))
            for cfg in available[:10]:  # Show first 10
                logger.error("      • %s", cfg)
            if len(available) > 10:
                logger.error("      ... and %d more", len(available) - 10)
            logger.error("")
            logger.error("   💡 Use any preset: skill-seekers scrape --config <name>.json")
            logger.error("   🌐 Browse all: https://skillseekersweb.com/")
        else:
            logger.error("   ⚠️  Could not connect to API to list available configs")
            logger.error("   🌐 Visit: https://skillseekersweb.com/ for available configs")
        sys.exit(1)

    # Load the resolved config file
    try:
        with open(resolved_path, encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("❌ Error: Invalid JSON in config file: %s", resolved_path)
        logger.error("   Details: %s", e)
        logger.error("   Suggestion: Check syntax at line %d, column %d", e.lineno, e.colno)
        sys.exit(1)

    # Validate config using ConfigValidator (supports both unified and legacy formats)
    try:
        validator = ConfigValidator(config)
        validator.validate()

        # Log config type
        if validator.is_unified:
            logger.debug("✓ Unified config format detected")
    except ValueError as e:
        logger.error("❌ Configuration validation errors in %s:", config_path)
        logger.error("   %s", str(e))
        logger.error(
            "\n   Suggestion: Fix the above errors or check https://skillseekersweb.com/ for examples"
        )
        sys.exit(1)

    return config


def scrape_documentation(
    config: dict[str, Any],
    ctx: Any | None = None,
    verbose: bool = False,
    quiet: bool = False,
) -> int:
    """Scrape documentation using config and optional context.

    This is the main entry point for programmatic use. CLI main() is a thin
    wrapper around this function.

    Args:
        config: Configuration dictionary with required fields (name, base_url, etc.)
        ctx: Optional ExecutionContext for shared configuration
        verbose: Enable verbose logging
        quiet: Minimize logging output

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    from skill_seekers.cli.execution_context import ExecutionContext

    # Setup logging
    setup_logging(verbose=verbose, quiet=quiet)

    # Initialize context if not provided
    if ctx is None:
        ctx = ExecutionContext.initialize(args=argparse.Namespace(**config))

    # Build converter and execute
    try:
        converter = _run_scraping(config)
        if converter is None:
            return 1

        # Handle enhancement if enabled
        if ctx.enhancement.enabled and ctx.enhancement.level > 0:
            _run_enhancement(config, ctx, converter)

        return 0
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return 1


def _run_scraping(config: dict[str, Any]) -> Optional["DocToSkillConverter"]:
    """Run the scraping process."""
    # Create converter
    converter = DocToSkillConverter(config)

    # Check for resume
    if config.get("resume") and converter.checkpoint_exists():
        logger.info("📂 Resuming from checkpoint...")
        converter.load_checkpoint()
    else:
        # Clear checkpoint if fresh start
        if config.get("fresh"):
            converter.clear_checkpoint()

    # Scrape
    if not config.get("skip_scrape"):
        logger.info("\n🔍 Starting scrape...")
        try:
            asyncio.run(converter.scrape())
        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Interrupted by user")
            converter.save_checkpoint()
            logger.info("💾 Checkpoint saved. Resume with --resume")
            return None

    # Build skill
    logger.info("\n📦 Building skill...")
    converter.build_skill()

    return converter


def _run_enhancement(
    config: dict[str, Any],
    ctx: Any,
    _converter: Any,
) -> None:
    """Run enhancement using context settings."""
    from pathlib import Path

    skill_dir = f"output/{config['name']}"

    logger.info("\n" + "=" * 60)
    logger.info(f"🤖 Enhancing SKILL.md (level {ctx.enhancement.level})")
    logger.info("=" * 60)

    # Use AgentClient from context
    try:
        agent_client = ctx.get_agent_client()

        # Run enhancement based on mode
        if agent_client.mode == "api" and agent_client.client:
            # API mode enhancement
            from skill_seekers.cli.enhance_skill import enhance_skill_md

            # Use AgentClient's API key detection (respects priority: CLI > config > env)
            api_key = ctx.enhancement.api_key or agent_client.api_key
            if api_key:
                enhance_skill_md(skill_dir, api_key)
                logger.info("✅ API enhancement complete!")
            else:
                logger.warning("⚠️  No API key available for enhancement")
        else:
            # Local mode enhancement
            from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

            enhancer = LocalSkillEnhancer(
                Path(skill_dir),
                agent=ctx.enhancement.agent,
                agent_cmd=ctx.enhancement.agent_cmd,
            )
            success = enhancer.run(headless=True, timeout=ctx.enhancement.timeout)
            if success:
                agent_name = ctx.enhancement.agent or "claude"
                logger.info(f"✅ Local enhancement complete! (via {agent_name})")
            else:
                logger.warning("⚠️  Local enhancement did not complete")
    except Exception as e:
        logger.warning(f"⚠️  Enhancement failed: {e}")
