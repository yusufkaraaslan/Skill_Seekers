#!/usr/bin/env python3
"""
RSS/Atom Feed to Skill Converter

Converts RSS 2.0, RSS 1.0 (RDF), and Atom feeds into AI-ready skills.
Uses feedparser for feed parsing, optionally follows article links to scrape
full content using requests + BeautifulSoup.

Supports both remote feed URLs and local feed XML files. Extracts article
metadata (title, author, published date, categories), feed-level metadata
(title, description, link, language), and optionally the full article text
from linked pages.

Usage:
    skill-seekers rss --feed-url https://example.com/feed.xml --name myblog
    skill-seekers rss --feed-path ./feed.xml --name myblog
    skill-seekers rss --feed-url https://example.com/rss --no-follow-links --name myblog
    skill-seekers rss --from-json myblog_extracted.json
    python3 -m skill_seekers.cli.rss_scraper --feed-url https://example.com/atom.xml --name myblog
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Optional dependency guard — feedparser is not in core deps
try:
    import feedparser  # noqa: F401

    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

# BeautifulSoup is a core dependency (always available)
from bs4 import BeautifulSoup, Comment, Tag

logger = logging.getLogger(__name__)

# Feed type constants
FEED_TYPE_RSS_20 = "RSS 2.0"
FEED_TYPE_RSS_10 = "RSS 1.0 (RDF)"
FEED_TYPE_ATOM = "Atom"
FEED_TYPE_UNKNOWN = "Unknown"

# Default request headers for scraping article pages
_DEFAULT_HEADERS = {
    "User-Agent": "SkillSeekers/RSS-Scraper (https://github.com/skill-seekers)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Tags to strip from scraped article HTML
_STRIP_TAGS = {"script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"}

# Maximum length for a single article's scraped text (characters)
_MAX_ARTICLE_TEXT_LENGTH = 50_000

# Delay between HTTP requests when following links (seconds)
_REQUEST_DELAY = 1.0


def _check_feedparser_deps() -> None:
    """Raise RuntimeError if feedparser is not installed."""
    if not FEEDPARSER_AVAILABLE:
        raise RuntimeError(
            "feedparser is required for RSS/Atom feed support.\n"
            'Install with: pip install "skill-seekers[rss]"\n'
            "Or: pip install feedparser"
        )


def infer_description_from_feed(
    feed_meta: dict[str, Any] | None = None,
    name: str = "",
) -> str:
    """Infer skill description from feed-level metadata.

    Tries to build a meaningful "Use when..." description from the feed
    title and subtitle/description fields.

    Args:
        feed_meta: Feed metadata dict with title, description, link, etc.
        name: Skill name for fallback.

    Returns:
        Description string suitable for "Use when..." format.
    """
    if feed_meta:
        desc = feed_meta.get("description", "")
        if desc and len(desc) > 20:
            if len(desc) > 150:
                desc = desc[:147] + "..."
            return f"Use when referencing {desc.lower()}"
        title = feed_meta.get("title", "")
        if title and len(title) > 5:
            return f"Use when referencing articles from {title}"
    return (
        f"Use when referencing {name} feed content"
        if name
        else "Use when referencing this feed content"
    )


class RssToSkillConverter:
    """Convert RSS/Atom feeds to AI-ready skills.

    Parses RSS 2.0, RSS 1.0 (RDF), and Atom feeds using feedparser.
    Optionally follows article links to scrape full page content via
    requests + BeautifulSoup.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the converter with configuration.

        Args:
            config: Dictionary with name (required), feed_url, feed_path,
                follow_links (default True), max_articles (default 50),
                and description (optional).
        """
        self.config = config
        self.name: str = config["name"]
        self.feed_url: str = config.get("feed_url", "")
        self.feed_path: str = config.get("feed_path", "")
        self.follow_links: bool = config.get("follow_links", True)
        self.max_articles: int = config.get("max_articles", 50)
        self.description: str = config.get(
            "description", f"Use when referencing {self.name} feed content"
        )

        # Output paths
        self.skill_dir: str = f"output/{self.name}"
        self.data_file: str = f"output/{self.name}_extracted.json"

        # Internal state
        self.extracted_data: dict[str, Any] | None = None

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def extract_feed(self) -> bool:
        """Parse the RSS/Atom feed and extract article data.

        Parses feed, extracts metadata and articles, optionally follows links
        to scrape full content, saves intermediate JSON.

        Returns:
            True on success.
        """
        _check_feedparser_deps()

        source = self.feed_url or self.feed_path
        print(f"\n🔍 Extracting RSS/Atom feed: {source}")

        # Parse the feed
        parsed = self._parse_feed()

        # Detect feed type
        feed_type = self._detect_feed_type(parsed)
        print(f"   Feed type: {feed_type}")

        # Extract feed-level metadata
        feed_meta = self._extract_feed_metadata(parsed)
        print(f"   Title: {feed_meta.get('title', 'Unknown')}")
        print(f"   Link: {feed_meta.get('link', 'N/A')}")
        print(f"   Language: {feed_meta.get('language', 'N/A')}")

        # Update description from feed metadata if not explicitly set
        if "description" not in self.config:
            self.description = infer_description_from_feed(feed_meta, self.name)

        # Extract articles
        articles = self._extract_articles(parsed)
        print(f"   Articles found: {len(articles)}")

        # Optionally scrape full article content
        if self.follow_links:
            print(f"\n🌐 Following article links (max {len(articles)})...")
            scraped_count = 0
            for i, article in enumerate(articles):
                link = article.get("link", "")
                if not link:
                    continue
                print(f"   [{i + 1}/{len(articles)}] {link[:80]}...")
                content = self._scrape_article_content(link)
                if content:
                    article["full_text"] = content
                    scraped_count += 1
                # Be polite — delay between requests
                if i < len(articles) - 1:
                    time.sleep(_REQUEST_DELAY)
            print(f"   Scraped full content for {scraped_count}/{len(articles)} articles")
        else:
            print("   Skipping link following (--no-follow-links)")

        # Categorize articles by feed categories/tags
        all_categories = self._collect_all_categories(articles)

        # Build result data
        result_data: dict[str, Any] = {
            "source": source,
            "feed_type": feed_type,
            "feed_metadata": feed_meta,
            "total_articles": len(articles),
            "followed_links": self.follow_links,
            "all_categories": sorted(all_categories),
            "articles": articles,
        }

        # Persist extracted data
        os.makedirs(os.path.dirname(self.data_file) or ".", exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n💾 Saved extracted data to: {self.data_file}")
        self.extracted_data = result_data
        print(
            f"✅ Extracted {len(articles)} articles ({len(all_categories)} unique categories/tags)"
        )
        return True

    def load_extracted_data(self, json_path: str) -> bool:
        """Load previously extracted data from a JSON file."""
        print(f"\n📂 Loading extracted data from: {json_path}")
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Extracted data file not found: {json_path}")

        with open(json_path, encoding="utf-8") as f:
            self.extracted_data = json.load(f)

        total = self.extracted_data.get(
            "total_articles", len(self.extracted_data.get("articles", []))
        )
        print(f"✅ Loaded {total} articles")
        return True

    def categorize_content(self) -> dict[str, dict[str, Any]]:
        """Categorize articles by their feed categories/tags."""
        print("\n📋 Categorizing content by feed tags...")

        if not self.extracted_data:
            raise RuntimeError("No extracted data available. Call extract_feed() first.")

        articles = self.extracted_data.get("articles", [])
        categorized: dict[str, dict[str, Any]] = {}

        for article in articles:
            cats = article.get("categories", [])
            if not cats:
                cats = ["uncategorized"]

            for cat in cats:
                cat_key = self._sanitize_filename(cat)
                if cat_key not in categorized:
                    categorized[cat_key] = {
                        "title": cat,
                        "articles": [],
                    }
                # Avoid duplicates if an article has overlapping normalized keys
                article_id = article.get("id", article.get("link", ""))
                existing_ids = {
                    a.get("id", a.get("link", "")) for a in categorized[cat_key]["articles"]
                }
                if article_id not in existing_ids:
                    categorized[cat_key]["articles"].append(article)

        # If no categories at all, put everything in one group
        if not categorized:
            categorized["all_articles"] = {
                "title": "All Articles",
                "articles": articles,
            }

        print(f"✅ Created {len(categorized)} categories")
        for cat_key, cat_data in categorized.items():
            print(f"   - {cat_data['title']}: {len(cat_data['articles'])} articles")

        return categorized

    def build_skill(self) -> None:
        """Build complete skill structure from extracted data."""
        print(f"\n🏗️  Building skill: {self.name}")

        if not self.extracted_data:
            raise RuntimeError("No extracted data available. Call extract_feed() first.")

        # Create directories
        os.makedirs(f"{self.skill_dir}/references", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/scripts", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/assets", exist_ok=True)

        # Categorize content
        categorized = self.categorize_content()

        # Generate reference files
        print("\n📝 Generating reference files...")
        for cat_key, cat_data in categorized.items():
            self._generate_reference_file(cat_key, cat_data)

        # Generate index
        self._generate_index(categorized)

        # Generate SKILL.md
        self._generate_skill_md(categorized)

        print(f"\n✅ Skill built successfully: {self.skill_dir}/")
        print(f"\n📦 Next step: Package with: skill-seekers package {self.skill_dir}/")

    # ──────────────────────────────────────────────────────────────────────
    # Feed parsing internals
    # ──────────────────────────────────────────────────────────────────────

    def _parse_feed(self) -> "feedparser.FeedParserDict":
        """Parse feed from URL or local file using feedparser."""
        import feedparser as fp

        if self.feed_path:
            if not os.path.exists(self.feed_path):
                raise FileNotFoundError(f"Feed file not found: {self.feed_path}")
            logger.info("Parsing feed from local file: %s", self.feed_path)
            parsed = fp.parse(self.feed_path)
        elif self.feed_url:
            logger.info("Fetching feed from URL: %s", self.feed_url)
            parsed = fp.parse(
                self.feed_url,
                agent="SkillSeekers/RSS-Scraper",
            )
        else:
            raise RuntimeError(
                "No feed source provided. Use feed_url (remote URL) or feed_path (local file)."
            )

        # Check for parsing errors
        if parsed.bozo and not parsed.entries:
            exc = parsed.get("bozo_exception", "Unknown parse error")
            raise RuntimeError(f"Failed to parse feed: {exc}")

        return parsed

    def _detect_feed_type(self, parsed: "feedparser.FeedParserDict") -> str:
        """Detect RSS 2.0, RSS 1.0, or Atom from feedparser's version field."""
        version = getattr(parsed, "version", "") or ""
        version_lower = version.lower()

        if "atom" in version_lower:
            return FEED_TYPE_ATOM
        if "rss20" in version_lower or version_lower == "rss20":
            return FEED_TYPE_RSS_20
        if "rss10" in version_lower or "rdf" in version_lower:
            return FEED_TYPE_RSS_10
        if version_lower.startswith("rss"):
            return FEED_TYPE_RSS_20

        # Fallback heuristic: check feed dict for version clues
        feed = parsed.get("feed", {})
        if feed.get("xmlns", "").startswith("http://www.w3.org/2005/Atom"):
            return FEED_TYPE_ATOM
        if feed.get("rss_version"):
            return FEED_TYPE_RSS_20

        return FEED_TYPE_UNKNOWN

    def _extract_feed_metadata(self, parsed: "feedparser.FeedParserDict") -> dict[str, Any]:
        """Extract feed-level metadata (title, description, link, language, etc.)."""
        feed = parsed.get("feed", {})

        # feedparser normalizes subtitle (Atom) and description (RSS)
        description = feed.get("subtitle", "") or feed.get("description", "")

        # Published / updated dates
        published = feed.get("published", "") or feed.get("updated", "")

        # Feed image (RSS <image>, Atom <icon>/<logo>)
        image_url = ""
        image_data = feed.get("image", {})
        if isinstance(image_data, dict):
            image_url = image_data.get("href", "") or image_data.get("url", "")
        elif isinstance(image_data, str):
            image_url = image_data

        return {
            "title": feed.get("title", "Untitled Feed"),
            "description": description,
            "link": feed.get("link", ""),
            "language": feed.get("language", ""),
            "author": feed.get("author", ""),
            "published": published,
            "generator": feed.get("generator", ""),
            "image_url": image_url,
            "rights": feed.get("rights", ""),
        }

    def _extract_articles(self, parsed: "feedparser.FeedParserDict") -> list[dict[str, Any]]:
        """Extract article entries (title, link, summary, date, author, categories)."""
        articles: list[dict[str, Any]] = []

        for entry in parsed.entries[: self.max_articles]:
            # Unique identifier (Atom id, RSS guid, or link hash)
            entry_id = entry.get("id", "") or entry.get("link", "")
            if not entry_id:
                entry_id = hashlib.sha256(entry.get("title", "").encode("utf-8")).hexdigest()[:16]

            # Published date normalization
            published = entry.get("published", "") or entry.get("updated", "")
            published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
            published_iso = ""
            if published_parsed:
                try:
                    dt = datetime(*published_parsed[:6])
                    published_iso = dt.isoformat()
                except (TypeError, ValueError):
                    published_iso = published

            # Categories / tags
            categories: list[str] = []
            for tag_data in entry.get("tags", []):
                term = tag_data.get("term", "")
                if term:
                    categories.append(term)

            # Summary — feedparser may provide HTML; clean it
            summary_raw = entry.get("summary", "") or entry.get("description", "")
            summary_text = self._html_to_text(summary_raw) if summary_raw else ""

            # Content — some feeds include full content inline
            content_text = ""
            content_list = entry.get("content", [])
            if content_list and isinstance(content_list, list):
                for content_block in content_list:
                    value = content_block.get("value", "")
                    if value:
                        content_text += self._html_to_text(value) + "\n\n"
                content_text = content_text.strip()

            # Author(s)
            author = entry.get("author", "")
            if not author:
                authors_detail = entry.get("authors", [])
                if authors_detail:
                    author = ", ".join(a.get("name", "") for a in authors_detail if a.get("name"))

            article: dict[str, Any] = {
                "id": entry_id,
                "title": entry.get("title", "Untitled"),
                "link": entry.get("link", ""),
                "summary": summary_text,
                "content": content_text,
                "published": published,
                "published_iso": published_iso,
                "author": author,
                "categories": categories,
            }

            articles.append(article)

        return articles

    def _scrape_article_content(self, url: str) -> str:
        """Follow article URL, extract full page content using requests + BeautifulSoup."""
        try:
            import requests
        except ImportError:
            logger.warning(
                "requests library not available — cannot follow article links. "
                "Install with: pip install requests"
            )
            return ""

        try:
            response = requests.get(
                url,
                headers=_DEFAULT_HEADERS,
                timeout=15,
                allow_redirects=True,
            )
            response.raise_for_status()
        except Exception as e:
            logger.debug("Failed to fetch %s: %s", url, e)
            return ""

        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type.lower() and "xml" not in content_type.lower():
            logger.debug("Skipping non-HTML content at %s (type: %s)", url, content_type)
            return ""

        return self._extract_article_text(response.text)

    def _extract_article_text(self, html: str) -> str:
        """Clean article HTML to text/markdown. Finds <article>/<main>, strips nav/ads."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted elements
        for tag_name in _STRIP_TAGS:
            for element in soup.find_all(tag_name):
                element.decompose()
        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            comment.extract()

        # Try to find the main article container
        main_content = (
            soup.find("article")
            or soup.find("main")
            or soup.find(attrs={"role": "main"})
            or soup.find(attrs={"id": re.compile(r"(content|article|post|entry)", re.I)})
            or soup.find(attrs={"class": re.compile(r"(content|article|post|entry)", re.I)})
        )

        if not main_content:
            main_content = soup.find("body") or soup

        # Convert to text with basic structure preservation
        text_parts: list[str] = []
        for element in main_content.descendants:
            if isinstance(element, Tag):
                if element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                    level = int(element.name[1])
                    heading_text = element.get_text(strip=True)
                    if heading_text:
                        text_parts.append(f"\n{'#' * level} {heading_text}\n")
                elif element.name == "p":
                    para_text = element.get_text(separator=" ", strip=True)
                    if para_text:
                        text_parts.append(f"\n{para_text}\n")
                elif element.name in ("pre", "code"):
                    code_text = element.get_text()
                    if code_text and code_text.strip():
                        # Detect language from class if available
                        classes = element.get("class", [])
                        lang = ""
                        for cls in classes:
                            if isinstance(cls, str) and (
                                cls.startswith("language-") or cls.startswith("lang-")
                            ):
                                lang = cls.split("-", 1)[1]
                                break
                        text_parts.append(f"\n```{lang}\n{code_text.strip()}\n```\n")
                elif element.name == "li":
                    li_text = element.get_text(separator=" ", strip=True)
                    if li_text:
                        text_parts.append(f"- {li_text}")
                elif element.name == "blockquote":
                    bq_text = element.get_text(separator=" ", strip=True)
                    if bq_text:
                        text_parts.append(f"\n> {bq_text}\n")

        text = "\n".join(text_parts).strip()

        # Collapse excessive whitespace
        text = re.sub(r"\n{4,}", "\n\n\n", text)

        # Truncate if too long
        if len(text) > _MAX_ARTICLE_TEXT_LENGTH:
            text = text[:_MAX_ARTICLE_TEXT_LENGTH] + "\n\n[Content truncated]"

        return text

    # ──────────────────────────────────────────────────────────────────────
    # Categorization helpers
    # ──────────────────────────────────────────────────────────────────────

    def _collect_all_categories(self, articles: list[dict[str, Any]]) -> set[str]:
        """Collect all unique category/tag strings across articles."""
        categories: set[str] = set()
        for article in articles:
            for cat in article.get("categories", []):
                if cat:
                    categories.add(cat)
        return categories

    def _html_to_text(self, html_fragment: str) -> str:
        """Convert an HTML fragment to plain text, stripping all tags."""
        if not html_fragment:
            return ""
        soup = BeautifulSoup(html_fragment, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # ──────────────────────────────────────────────────────────────────────
    # Skill generation — reference files
    # ──────────────────────────────────────────────────────────────────────

    def _generate_reference_file(self, cat_key: str, cat_data: dict[str, Any]) -> None:
        """Generate a reference markdown file for a category of articles."""
        safe_name = self._sanitize_filename(cat_data["title"])
        filepath = f"{self.skill_dir}/references/{safe_name}.md"

        articles = cat_data["articles"]

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {cat_data['title']}\n\n")
            f.write(f"**Articles:** {len(articles)}\n\n")
            f.write("---\n\n")

            for article in articles:
                f.write(f"## {article.get('title', 'Untitled')}\n\n")

                # Metadata block
                if article.get("author"):
                    f.write(f"**Author:** {article['author']}\n\n")
                if article.get("published"):
                    f.write(f"**Published:** {article['published']}\n\n")
                if article.get("link"):
                    f.write(f"**Link:** {article['link']}\n\n")
                if article.get("categories"):
                    tags = ", ".join(article["categories"])
                    f.write(f"**Tags:** {tags}\n\n")

                # Summary
                summary = article.get("summary", "")
                if summary:
                    f.write("### Summary\n\n")
                    f.write(f"{summary}\n\n")

                # Inline content from feed (if present)
                inline_content = article.get("content", "")
                if inline_content and inline_content != summary:
                    f.write("### Content\n\n")
                    f.write(f"{inline_content}\n\n")

                # Full scraped text
                full_text = article.get("full_text", "")
                if full_text:
                    f.write("### Full Article\n\n")
                    f.write(f"{full_text}\n\n")

                f.write("---\n\n")

        print(f"   Generated: {filepath}")

    def _generate_index(self, categorized: dict[str, dict[str, Any]]) -> None:
        """Generate the reference index file with category links and statistics."""
        filepath = f"{self.skill_dir}/references/index.md"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {self.name.title()} Feed Reference Index\n\n")

            feed_meta = self.extracted_data.get("feed_metadata", {})
            if feed_meta.get("title"):
                f.write(f"**Feed:** {feed_meta['title']}\n\n")
            if feed_meta.get("link"):
                f.write(f"**Source:** {feed_meta['link']}\n\n")

            f.write("## Categories\n\n")

            total_articles = 0
            for cat_key, cat_data in sorted(categorized.items()):
                safe_name = self._sanitize_filename(cat_data["title"])
                count = len(cat_data["articles"])
                total_articles += count
                f.write(f"- [{cat_data['title']}]({safe_name}.md) ({count} articles)\n")

            f.write(f"\n**Total articles:** {total_articles}\n\n")

            # Statistics
            f.write("## Statistics\n\n")
            f.write(f"- Total articles: {self.extracted_data.get('total_articles', 0)}\n")
            f.write(f"- Feed type: {self.extracted_data.get('feed_type', FEED_TYPE_UNKNOWN)}\n")
            f.write(
                f"- Links followed: "
                f"{'Yes' if self.extracted_data.get('followed_links') else 'No'}\n"
            )

            all_cats = self.extracted_data.get("all_categories", [])
            if all_cats:
                f.write(f"- Unique tags: {len(all_cats)}\n")

            # Author summary
            author_counts = self._count_authors()
            if author_counts:
                f.write(f"\n## Authors ({len(author_counts)})\n\n")
                for author, count in sorted(
                    author_counts.items(), key=lambda x: x[1], reverse=True
                )[:20]:
                    f.write(f"- {author}: {count} articles\n")

        print(f"   Generated: {filepath}")

    def _generate_skill_md(self, categorized: dict[str, dict[str, Any]]) -> None:
        """Generate the main SKILL.md file with feed overview and navigation."""
        filepath = f"{self.skill_dir}/SKILL.md"

        feed_meta = self.extracted_data.get("feed_metadata", {})
        feed_title = feed_meta.get("title", self.name.title())
        feed_type = self.extracted_data.get("feed_type", FEED_TYPE_UNKNOWN)

        # Skill name for frontmatter (lowercase, hyphens, max 64 chars)
        skill_name = self.name.lower().replace("_", "-").replace(" ", "-")[:64]

        # Truncate description
        desc = self.description[:1024] if len(self.description) > 1024 else self.description

        with open(filepath, "w", encoding="utf-8") as f:
            # YAML frontmatter
            f.write("---\n")
            f.write(f"name: {skill_name}\n")
            f.write(f"description: {desc}\n")
            f.write("---\n\n")

            # Header
            f.write(f"# {feed_title} Feed Skill\n\n")
            f.write(f"{self.description}\n\n")

            # Feed Information
            f.write("## 📡 Feed Information\n\n")
            f.write(f"**Feed Title:** {feed_title}\n\n")
            f.write(f"**Feed Type:** {feed_type}\n\n")
            if feed_meta.get("link"):
                f.write(f"**Website:** {feed_meta['link']}\n\n")
            if feed_meta.get("language"):
                f.write(f"**Language:** {feed_meta['language']}\n\n")
            if feed_meta.get("description"):
                feed_desc = feed_meta["description"]
                if len(feed_desc) > 300:
                    feed_desc = feed_desc[:297] + "..."
                f.write(f"**Description:** {feed_desc}\n\n")
            if feed_meta.get("generator"):
                f.write(f"**Generator:** {feed_meta['generator']}\n\n")
            if feed_meta.get("rights"):
                f.write(f"**Rights:** {feed_meta['rights']}\n\n")

            # When to Use
            f.write("## 💡 When to Use This Skill\n\n")
            f.write("Use this skill when you need to:\n")
            f.write(f"- Reference articles and content from {feed_title}\n")
            f.write("- Look up specific topics covered in the feed\n")
            f.write("- Find author perspectives and expert analysis\n")
            f.write("- Review recent posts and updates on the subject\n")
            f.write("- Explore categorized content by tags or topics\n\n")

            # Article Overview
            total_articles = self.extracted_data.get("total_articles", 0)
            f.write("## 📖 Article Overview\n\n")
            f.write(f"**Total Articles:** {total_articles}\n\n")

            # Category breakdown
            f.write("**Content by Category:**\n\n")
            for cat_key, cat_data in sorted(categorized.items()):
                count = len(cat_data["articles"])
                f.write(f"- **{cat_data['title']}**: {count} articles\n")
            f.write("\n")

            # Recent articles (top 10 by date or order)
            articles = self.extracted_data.get("articles", [])
            recent = articles[:10]
            if recent:
                f.write("## 📰 Recent Articles\n\n")
                for article in recent:
                    title = article.get("title", "Untitled")
                    published = article.get("published", "")
                    author = article.get("author", "")
                    link = article.get("link", "")

                    f.write(f"### {title}\n\n")
                    meta_parts: list[str] = []
                    if published:
                        meta_parts.append(f"**Published:** {published}")
                    if author:
                        meta_parts.append(f"**Author:** {author}")
                    if meta_parts:
                        f.write(" | ".join(meta_parts) + "\n\n")

                    summary = article.get("summary", "")
                    if summary:
                        # Show first 200 chars of summary
                        short = summary[:200] + "..." if len(summary) > 200 else summary
                        f.write(f"{short}\n\n")

                    if link:
                        f.write(f"[Read more]({link})\n\n")

            # Authors
            author_counts = self._count_authors()
            if author_counts:
                f.write(f"## ✍️ Authors ({len(author_counts)})\n\n")
                for author, count in sorted(
                    author_counts.items(), key=lambda x: x[1], reverse=True
                )[:15]:
                    f.write(f"- **{author}**: {count} articles\n")
                f.write("\n")

            # All categories/tags
            all_cats = self.extracted_data.get("all_categories", [])
            if all_cats:
                f.write(f"## 🏷️ Tags ({len(all_cats)})\n\n")
                f.write(", ".join(f"`{cat}`" for cat in all_cats[:50]))
                if len(all_cats) > 50:
                    f.write(f" ... and {len(all_cats) - 50} more")
                f.write("\n\n")

            # Statistics
            f.write("## 📊 Feed Statistics\n\n")
            f.write(f"- **Total Articles**: {total_articles}\n")
            f.write(f"- **Feed Type**: {feed_type}\n")
            f.write(f"- **Categories/Tags**: {len(all_cats)}\n")
            f.write(f"- **Authors**: {len(author_counts)}\n")
            followed = self.extracted_data.get("followed_links", False)
            f.write(f"- **Full Content Scraped**: {'Yes' if followed else 'No'}\n\n")

            # Date range
            date_range = self._get_date_range()
            if date_range:
                f.write(f"- **Date Range**: {date_range[0]} to {date_range[1]}\n\n")

            # Navigation
            f.write("## 🗺️ Navigation\n\n")
            f.write("**Reference Files:**\n\n")
            for cat_key, cat_data in sorted(categorized.items()):
                safe_name = self._sanitize_filename(cat_data["title"])
                f.write(
                    f"- `references/{safe_name}.md` - {cat_data['title']}"
                    f" ({len(cat_data['articles'])} articles)\n"
                )
            f.write("\n")
            f.write("See `references/index.md` for complete feed structure.\n\n")

            # Footer
            f.write("---\n\n")
            f.write("**Generated by Skill Seeker** | RSS/Atom Feed Scraper\n")

        with open(filepath, encoding="utf-8") as f:
            line_count = len(f.read().split("\n"))
        print(f"   Generated: {filepath} ({line_count} lines)")

    # ──────────────────────────────────────────────────────────────────────
    # Utility helpers
    # ──────────────────────────────────────────────────────────────────────

    def _count_authors(self) -> dict[str, int]:
        """Count articles per author."""
        if not self.extracted_data:
            return {}
        counts: dict[str, int] = {}
        for article in self.extracted_data.get("articles", []):
            author = article.get("author", "").strip()
            if author:
                counts[author] = counts.get(author, 0) + 1
        return counts

    def _get_date_range(self) -> tuple[str, str] | None:
        """Get the date range (earliest, latest) of articles, or None."""
        if not self.extracted_data:
            return None
        dates: list[str] = []
        for article in self.extracted_data.get("articles", []):
            iso = article.get("published_iso", "")
            if iso:
                dates.append(iso)
        if not dates:
            return None
        dates.sort()
        return (dates[0][:10], dates[-1][:10])

    def _sanitize_filename(self, name: str) -> str:
        """Convert a string to a safe filename."""
        safe = re.sub(r"[^\w\s-]", "", name.lower())
        safe = re.sub(r"[-\s]+", "_", safe)
        return safe or "unnamed"


# ──────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────


def main() -> int:
    """CLI entry point for the RSS/Atom feed scraper."""
    from .arguments.common import add_all_standard_arguments

    parser = argparse.ArgumentParser(
        description="Convert RSS/Atom feed to AI-ready skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --feed-url https://example.com/feed.xml --name myblog\n"
            "  %(prog)s --feed-path ./feed.xml --name myblog\n"
            "  %(prog)s --feed-url https://example.com/rss --no-follow-links --name myblog\n"
            "  %(prog)s --from-json myblog_extracted.json\n"
        ),
    )

    # Standard arguments (name, description, output, enhance-level, etc.)
    add_all_standard_arguments(parser)

    # Override enhance-level default to 0 for RSS
    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0
            action.help = (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled (default for RSS), 1=SKILL.md only, "
                "2=+architecture/config, 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, "
                "otherwise LOCAL (Claude Code)"
            )

    # RSS-specific arguments
    parser.add_argument(
        "--feed-url",
        type=str,
        help="URL of the RSS/Atom feed to scrape",
        metavar="URL",
    )
    parser.add_argument(
        "--feed-path",
        type=str,
        help="Local file path to an RSS/Atom XML file",
        metavar="PATH",
    )
    parser.add_argument(
        "--follow-links",
        action="store_true",
        default=True,
        dest="follow_links",
        help="Follow article links to scrape full content (default: enabled)",
    )
    parser.add_argument(
        "--no-follow-links",
        action="store_false",
        dest="follow_links",
        help="Do not follow article links — use feed content only",
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        default=50,
        metavar="N",
        help="Maximum number of articles to process (default: 50)",
    )
    parser.add_argument(
        "--from-json",
        type=str,
        help="Build skill from previously extracted JSON file",
        metavar="FILE",
    )

    args = parser.parse_args()

    # Set logging level
    if getattr(args, "quiet", False):
        logging.getLogger().setLevel(logging.WARNING)
    elif getattr(args, "verbose", False):
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle --dry-run
    if getattr(args, "dry_run", False):
        source = (
            getattr(args, "feed_url", None)
            or getattr(args, "feed_path", None)
            or getattr(args, "from_json", None)
            or "(none)"
        )
        print(f"\n{'=' * 60}")
        print("DRY RUN: RSS/Atom Feed Extraction")
        print(f"{'=' * 60}")
        print(f"Source:          {source}")
        print(f"Name:            {getattr(args, 'name', None) or '(auto-detect)'}")
        print(f"Follow links:    {getattr(args, 'follow_links', True)}")
        print(f"Max articles:    {getattr(args, 'max_articles', 50)}")
        print(f"Enhance level:   {getattr(args, 'enhance_level', 0)}")
        print(f"\n✅ Dry run complete")
        return 0

    # Validate inputs
    has_source = (
        getattr(args, "feed_url", None)
        or getattr(args, "feed_path", None)
        or getattr(args, "from_json", None)
    )
    if not has_source:
        parser.error("Must specify --feed-url, --feed-path, or --from-json")

    # Build from JSON workflow
    if getattr(args, "from_json", None):
        name = Path(args.from_json).stem.replace("_extracted", "")
        config: dict[str, Any] = {
            "name": getattr(args, "name", None) or name,
            "description": getattr(args, "description", None)
            or f"Use when referencing {name} feed content",
        }
        try:
            converter = RssToSkillConverter(config)
            converter.load_extracted_data(args.from_json)
            converter.build_skill()
        except Exception as e:
            print(f"\n❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
        return 0

    # Feed extraction workflow
    if not getattr(args, "name", None):
        # Auto-detect name from URL or file path
        if getattr(args, "feed_url", None):
            from urllib.parse import urlparse

            parsed_url = urlparse(args.feed_url)
            args.name = parsed_url.hostname.replace(".", "-") if parsed_url.hostname else "feed"
        elif getattr(args, "feed_path", None):
            args.name = Path(args.feed_path).stem

    config = {
        "name": args.name,
        "feed_url": getattr(args, "feed_url", "") or "",
        "feed_path": getattr(args, "feed_path", "") or "",
        "follow_links": getattr(args, "follow_links", True),
        "max_articles": getattr(args, "max_articles", 50),
        "description": getattr(args, "description", None),
    }

    try:
        converter = RssToSkillConverter(config)

        # Extract feed
        if not converter.extract_feed():
            print("\n❌ Feed extraction failed — see error above", file=sys.stderr)
            sys.exit(1)

        # Build skill
        converter.build_skill()

        # Enhancement Workflow Integration
        from skill_seekers.cli.workflow_runner import run_workflows

        workflow_executed, workflow_names = run_workflows(args)
        workflow_name = ", ".join(workflow_names) if workflow_names else None

        # Traditional enhancement (complements workflow system)
        if getattr(args, "enhance_level", 0) > 0:
            api_key = getattr(args, "api_key", None) or os.environ.get("ANTHROPIC_API_KEY")
            mode = "API" if api_key else "LOCAL"

            print("\n" + "=" * 80)
            print(f"🤖 Traditional AI Enhancement ({mode} mode, level {args.enhance_level})")
            print("=" * 80)
            if workflow_executed:
                print(f"   Running after workflow: {workflow_name}")
                print(
                    "   (Workflow provides specialized analysis, "
                    "enhancement provides general improvements)"
                )
            print("")

            skill_dir = converter.skill_dir
            if api_key:
                try:
                    from skill_seekers.cli.enhance_skill import enhance_skill_md

                    enhance_skill_md(skill_dir, api_key)
                    print("✅ API enhancement complete!")
                except ImportError:
                    print("❌ API enhancement not available. Falling back to LOCAL mode...")
                    from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

                    enhancer = LocalSkillEnhancer(Path(skill_dir))
                    enhancer.run(headless=True)
                    print("✅ Local enhancement complete!")
            else:
                from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

                enhancer = LocalSkillEnhancer(Path(skill_dir))
                enhancer.run(headless=True)
                print("✅ Local enhancement complete!")

    except RuntimeError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during feed processing: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
