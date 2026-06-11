#!/usr/bin/env python3
"""
Local HTML Documentation to Skill Converter

Converts local HTML files or directories of HTML files into skills.
Uses BeautifulSoup for HTML parsing and content extraction. Supports single
HTML files (.html/.htm) and directories containing multiple HTML files.

Extracts document structure, headings, main content, code blocks, tables,
images, and links. Converts extracted content to clean markdown-like output
suitable for AI skill consumption.

Usage:
    skill-seekers html --html-path page.html --name myskill
    skill-seekers html --html-path ./docs/ --name myskill
    skill-seekers html --from-json page_extracted.json
"""

import json
import logging
import os
import re
from pathlib import Path

# BeautifulSoup is a core dependency (always available)
from bs4 import BeautifulSoup, Comment, Tag

from .document_skill_builder import DocumentSkillBuilder
from skill_seekers.cli.scraper_utils import extract_table_from_html as _extract_table_from_html
from skill_seekers.cli.scraper_utils import parse_leading_int as _parse_leading_int
from skill_seekers.cli.scraper_utils import score_code_quality as _score_code_quality

logger = logging.getLogger(__name__)

# File extensions treated as HTML
HTML_EXTENSIONS = {".html", ".htm", ".xhtml"}


def infer_description_from_html(metadata: dict | None = None, name: str = "") -> str:
    """Infer skill description from HTML metadata.

    Args:
        metadata: HTML document metadata dict (title, description, author, etc.)
        name: Skill name for fallback

    Returns:
        Description string suitable for "Use when..." format
    """
    if metadata:
        if metadata.get("description") and len(metadata["description"]) > 20:
            desc = metadata["description"].strip()
            if len(desc) > 150:
                desc = desc[:147] + "..."
            return f"Use when {desc.lower()}"
        if metadata.get("title") and len(metadata["title"]) > 10:
            return f"Use when working with {metadata['title'].lower()}"
    return (
        f"Use when referencing {name} documentation"
        if name
        else "Use when referencing this documentation"
    )


def _collect_html_files(html_path: str) -> list[Path]:
    """Collect HTML files from a path (file or directory).

    For a single file, returns a list with that file. For a directory,
    recursively finds all .html/.htm/.xhtml files sorted alphabetically.

    Args:
        html_path: Path to an HTML file or directory containing HTML files.

    Returns:
        Sorted list of Path objects pointing to HTML files.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If no HTML files are found.
    """
    path = Path(html_path)

    if not path.exists():
        raise FileNotFoundError(f"HTML path not found: {html_path}")

    if path.is_file():
        if path.suffix.lower() not in HTML_EXTENSIONS:
            raise ValueError(f"Not an HTML file (expected .html/.htm/.xhtml): {html_path}")
        return [path]

    if path.is_dir():
        files = sorted(
            f for f in path.rglob("*") if f.is_file() and f.suffix.lower() in HTML_EXTENSIONS
        )
        if not files:
            raise ValueError(f"No HTML files found in directory: {html_path}")
        return files

    raise ValueError(f"Path is neither a file nor a directory: {html_path}")


class HtmlToSkillConverter(DocumentSkillBuilder):
    """Convert local HTML files to a skill.

    Supports single HTML files and directories of HTML files. Parses document
    structure, extracts headings, content, code blocks, tables, images, and
    links. The build side (categorize/reference/index/SKILL.md) comes from
    DocumentSkillBuilder; this class owns HTML extraction plus the html-only
    build behaviors (multi-file grouping, source-file annotations, links).

    Attributes:
        config: Configuration dict with name, html_path, description.
        name: Skill name.
        html_path: Path to the HTML file or directory.
        description: Skill description text.
        skill_dir: Output directory for the built skill.
        data_file: Path to the intermediate extracted JSON file.
        extracted_data: Parsed extraction results dict.
    """

    SOURCE_TYPE = "html"
    SOURCE_PATH_ATTR = "html_path"
    SOURCE_LABEL = "HTML"
    FOOTER_LABEL = "HTML Scraper"
    # html recognizes two extra pattern keywords on top of the shared list.
    PATTERN_KEYWORDS = DocumentSkillBuilder.PATTERN_KEYWORDS + ("reference", "changelog")
    SKILL_MD_METADATA_FIELDS = (
        ("title", "Title"),
        ("author", "Author"),
        ("language", "Language"),
        ("description", "Description"),
        ("keywords", "Keywords"),
    )

    def __init__(self, config: dict) -> None:
        """Initialize the HTML to skill converter.

        Args:
            config: Configuration dict containing:
                - name (str): Skill name (required).
                - html_path (str): Path to HTML file or directory (optional).
                - description (str): Skill description (optional).
                - categories (dict): Category definitions for content grouping.
        """
        super().__init__(config)
        self.config = config
        self.name: str = config["name"]
        self.html_path: str = config.get("html_path", "")
        self.description: str = (
            config.get("description") or f"Use when referencing {self.name} documentation"
        )

        # Paths
        # skill_dir is resolved once in SkillConverter.__init__
        self.data_file = self.data_file_for()

        # Categories config
        self.categories: dict = config.get("categories", {})

        # Extracted data
        self.extracted_data: dict | None = None

    def extract(self):
        """SkillConverter interface — delegates to extract_html()."""
        return self.extract_html()

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    def extract_html(self) -> bool:
        """Extract content from local HTML file(s).

        Workflow:
        1. Collect HTML files from path (single file or directory)
        2. For each file: parse with BeautifulSoup (html.parser)
        3. Extract document metadata (title, meta tags)
        4. Extract main content using common selectors (article, main, etc.)
        5. Split content by h1/h2 heading boundaries into sections
        6. Extract code blocks from <pre>/<code> elements
        7. Extract tables and convert to markdown-ready dicts
        8. Extract images and links
        9. Detect code languages via LanguageDetector
        10. Save intermediate JSON to {name}_extracted.json

        Returns:
            True on success.

        Raises:
            FileNotFoundError: If the HTML path does not exist.
            ValueError: If no valid HTML files are found.
        """
        from skill_seekers.cli.language_detector import LanguageDetector

        print(f"\n🔍 Extracting from HTML: {self.html_path}")

        html_files = _collect_html_files(self.html_path)
        print(f"   Found {len(html_files)} HTML file(s)")

        # Aggregate metadata from the first file
        aggregate_metadata: dict = {}
        all_sections: list[dict] = []
        total_images = 0
        section_number = 0

        for file_path in html_files:
            try:
                raw_html = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.warning("Could not read %s: %s", file_path, e)
                continue

            soup = BeautifulSoup(raw_html, "html.parser")

            # Extract metadata from first file (or merge)
            file_meta = self._extract_metadata(soup, file_path)
            if not aggregate_metadata:
                aggregate_metadata = file_meta
            elif file_meta.get("title"):
                # Keep track of all titles for multi-file mode
                existing = aggregate_metadata.get("all_titles", [])
                if aggregate_metadata.get("title"):
                    existing.append(aggregate_metadata["title"])
                existing.append(file_meta["title"])
                aggregate_metadata["all_titles"] = existing

            print(f"   Processing: {file_path.name}")

            # Clean the soup
            self._clean_soup(soup)

            # Find main content area
            main_content = self._find_main_content(soup)

            # Split into sections by heading boundaries
            file_sections, img_count = self._extract_sections(
                main_content, section_number, file_path
            )
            section_number += len(file_sections)
            total_images += img_count
            all_sections.extend(file_sections)

        # If no sections were created, warn
        if not all_sections:
            logger.warning("No sections extracted from HTML files")

        # Update description from metadata if not set explicitly
        if not self.config.get("description"):
            self.description = infer_description_from_html(aggregate_metadata, self.name)

        print(f"   Title: {aggregate_metadata.get('title', 'Unknown')}")
        print(f"   Author: {aggregate_metadata.get('author', 'Unknown')}")

        # Detect languages for code samples
        detector = LanguageDetector(min_confidence=0.15)
        languages_detected: dict[str, int] = {}
        total_code_blocks = 0

        for section in all_sections:
            for code_sample in section.get("code_samples", []):
                lang = code_sample.get("language", "")
                if lang:
                    languages_detected[lang] = languages_detected.get(lang, 0) + 1
                total_code_blocks += 1

        # Detect languages for samples without language
        for section in all_sections:
            for code_sample in section.get("code_samples", []):
                if not code_sample.get("language"):
                    code = code_sample.get("code", "")
                    if code:
                        lang, confidence = detector.detect_from_code(code)
                        if lang and confidence >= 0.3:
                            code_sample["language"] = lang
                            languages_detected[lang] = languages_detected.get(lang, 0) + 1

        result_data = {
            "source_file": self.html_path,
            "metadata": aggregate_metadata,
            "total_sections": len(all_sections),
            "total_code_blocks": total_code_blocks,
            "total_images": total_images,
            "total_files": len(html_files),
            "languages_detected": languages_detected,
            "pages": all_sections,
        }

        # Save extracted data
        os.makedirs(os.path.dirname(self.data_file) or ".", exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n💾 Saved extracted data to: {self.data_file}")
        self.extracted_data = result_data
        print(
            f"✅ Extracted {len(all_sections)} sections, "
            f"{total_code_blocks} code blocks, "
            f"{total_images} images from {len(html_files)} file(s)"
        )
        return True

    # ------------------------------------------------------------------
    # Metadata extraction
    # ------------------------------------------------------------------

    def _extract_metadata(self, soup: BeautifulSoup, file_path: Path) -> dict:
        """Extract metadata from HTML document head.

        Checks <title>, <meta name="..."> tags for standard metadata fields
        (description, author, keywords, generator, language).

        Args:
            soup: Parsed BeautifulSoup document.
            file_path: Path to the source file (used as fallback title).

        Returns:
            Metadata dict with title, author, description, language, etc.
        """
        metadata: dict[str, str | None] = {
            "title": None,
            "author": None,
            "description": None,
            "language": None,
            "keywords": None,
            "generator": None,
            "source_file": str(file_path),
        }

        # <title> tag
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)

        # <meta> tags
        meta_map = {
            "description": "description",
            "author": "author",
            "keywords": "keywords",
            "generator": "generator",
        }
        for meta_name, key in meta_map.items():
            meta_tag = soup.find("meta", attrs={"name": meta_name})
            if meta_tag and meta_tag.get("content"):
                metadata[key] = meta_tag["content"].strip()

        # OpenGraph fallbacks
        if not metadata["title"]:
            og_title = soup.find("meta", attrs={"property": "og:title"})
            if og_title and og_title.get("content"):
                metadata["title"] = og_title["content"].strip()

        if not metadata["description"]:
            og_desc = soup.find("meta", attrs={"property": "og:description"})
            if og_desc and og_desc.get("content"):
                metadata["description"] = og_desc["content"].strip()

        # Language from <html lang="...">
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            metadata["language"] = html_tag["lang"]

        # Fallback title from filename
        if not metadata["title"]:
            metadata["title"] = file_path.stem.replace("_", " ").replace("-", " ").title()

        return metadata

    # ------------------------------------------------------------------
    # Soup cleaning
    # ------------------------------------------------------------------

    def _clean_soup(self, soup: BeautifulSoup) -> None:
        """Remove non-content elements from the parsed HTML.

        Strips scripts, styles, navigation, footers, ads, comments, and other
        boilerplate elements that should not be part of the extracted content.

        Args:
            soup: BeautifulSoup object to clean in-place.
        """
        # Remove script and style elements
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # Remove HTML comments
        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            comment.extract()

        # Remove common boilerplate elements by tag
        boilerplate_tags = ["nav", "footer", "header"]
        for tag_name in boilerplate_tags:
            for tag in soup.find_all(tag_name):
                # Keep header if it contains h1 (likely document title)
                if tag_name == "header" and tag.find(["h1", "h2"]):
                    continue
                tag.decompose()

        # Remove common boilerplate by class/id patterns
        boilerplate_patterns = [
            "sidebar",
            "menu",
            "navbar",
            "breadcrumb",
            "pagination",
            "cookie",
            "banner",
            "advertisement",
            "ad-",
            "social-share",
            "share-buttons",
            "comment-section",
            "comments",
        ]
        for pattern in boilerplate_patterns:
            for elem in soup.find_all(
                attrs={"class": lambda c, p=pattern: c and p in " ".join(c).lower()}
            ):
                elem.decompose()
            for elem in soup.find_all(attrs={"id": lambda i, p=pattern: i and p in i.lower()}):
                elem.decompose()

    # ------------------------------------------------------------------
    # Main content detection
    # ------------------------------------------------------------------

    def _find_main_content(self, soup: BeautifulSoup) -> Tag | BeautifulSoup:
        """Find the main content area of an HTML document.

        Tries common content selectors in priority order:
        1. <main> tag
        2. <article> tag
        3. Elements with role="main"
        4. Common content class/id selectors (.content, #content, etc.)
        5. Falls back to <body> or the entire soup

        Args:
            soup: Cleaned BeautifulSoup document.

        Returns:
            BeautifulSoup Tag representing the main content area.
        """
        # Priority 1: semantic HTML5 tags
        main_tag = soup.find("main")
        if main_tag and len(main_tag.get_text(strip=True)) > 50:
            return main_tag

        article_tag = soup.find("article")
        if article_tag and len(article_tag.get_text(strip=True)) > 50:
            return article_tag

        # Priority 2: ARIA role
        role_main = soup.find(attrs={"role": "main"})
        if role_main and len(role_main.get_text(strip=True)) > 50:
            return role_main

        # Priority 3: common CSS class/id selectors
        content_selectors = [
            {"class_": "content"},
            {"class_": "main-content"},
            {"class_": "page-content"},
            {"class_": "post-content"},
            {"class_": "entry-content"},
            {"class_": "article-content"},
            {"class_": "documentation"},
            {"class_": "doc-content"},
            {"id": "content"},
            {"id": "main-content"},
            {"id": "main"},
            {"id": "article"},
            {"id": "documentation"},
        ]

        for selector in content_selectors:
            # find_all returns tags matching any class in a multi-class element
            elem = soup.find("div", **selector) or soup.find("section", **selector)
            if elem and len(elem.get_text(strip=True)) > 50:
                return elem

        # Priority 4: largest <div> by text length (heuristic)
        divs = soup.find_all("div")
        if divs:
            largest = max(divs, key=lambda d: len(d.get_text(strip=True)))
            text_len = len(largest.get_text(strip=True))
            if text_len > 200:
                return largest

        # Fallback: body or entire soup
        body = soup.find("body")
        return body if body else soup

    # ------------------------------------------------------------------
    # Section extraction
    # ------------------------------------------------------------------

    def _extract_sections(
        self,
        content: Tag | BeautifulSoup,
        start_section_number: int,
        source_file: Path,
    ) -> tuple[list[dict], int]:
        """Extract sections from HTML content by splitting on heading boundaries.

        Iterates through top-level children of the content element. When an
        h1 or h2 heading is encountered, the previous accumulated elements
        are flushed into a section dict. Code blocks, tables, images, and
        links are extracted from each section.

        Args:
            content: BeautifulSoup Tag containing the main content.
            start_section_number: Starting section number for numbering.
            source_file: Path to the source HTML file.

        Returns:
            Tuple of (sections list, image count).
        """
        sections: list[dict] = []
        section_number = start_section_number
        image_count = 0

        current_heading: str | None = None
        current_heading_level: str | None = None
        current_elements: list = []

        for elem in content.children:
            if not hasattr(elem, "name") or elem.name is None:
                # NavigableString — skip whitespace, keep text
                continue

            if elem.name in ("h1", "h2"):
                # Flush previous section
                if current_heading is not None or current_elements:
                    section_number += 1
                    section, img_count = self._build_section(
                        section_number,
                        current_heading,
                        current_heading_level,
                        current_elements,
                        source_file,
                    )
                    sections.append(section)
                    image_count += img_count
                current_heading = elem.get_text(strip=True)
                current_heading_level = elem.name
                current_elements = []
            else:
                current_elements.append(elem)

        # Flush last section
        if current_heading is not None or current_elements:
            section_number += 1
            section, img_count = self._build_section(
                section_number,
                current_heading,
                current_heading_level,
                current_elements,
                source_file,
            )
            sections.append(section)
            image_count += img_count

        return sections, image_count

    def _build_section(
        self,
        section_number: int,
        heading: str | None,
        heading_level: str | None,
        elements: list,
        source_file: Path,
    ) -> tuple[dict, int]:
        """Build a section dict from a list of BeautifulSoup elements.

        Processes each element to extract text paragraphs, code samples,
        tables, sub-headings, images, and links. Handles nested structures
        by recursively searching within container elements.

        Args:
            section_number: 1-based section index.
            heading: Heading text (or None for preamble content).
            heading_level: Heading level string ('h1', 'h2', etc.).
            elements: List of BeautifulSoup Tag objects in this section.
            source_file: Path to the source HTML file for resolving links.

        Returns:
            Tuple of (section dict, image count found in this section).
        """
        text_parts: list[str] = []
        code_samples: list[dict] = []
        tables: list[dict] = []
        sub_headings: list[dict] = []
        images: list[dict] = []
        links: list[dict] = []

        for elem in elements:
            if not hasattr(elem, "name") or elem.name is None:
                continue

            tag = elem.name

            # Sub-headings (h3, h4, h5, h6) within the section
            if tag in ("h3", "h4", "h5", "h6"):
                sub_text = elem.get_text(strip=True)
                if sub_text:
                    sub_headings.append({"level": tag, "text": sub_text})
                continue

            # Code blocks — <pre> or standalone <code>
            if tag == "pre" or (tag == "code" and elem.find_parent("pre") is None):
                extracted = self._extract_code_blocks(elem)
                if extracted:
                    code_samples.extend(extracted)
                continue

            # Tables
            if tag == "table":
                table_data = self._extract_tables(elem)
                if table_data:
                    tables.append(table_data)
                continue

            # Images (top-level)
            if tag == "img":
                img_info = self._extract_image_info(elem, source_file)
                if img_info:
                    img_info["index"] = len(images)
                    images.append(img_info)
                continue

            # For container elements, recursively look for nested content
            nested_codes = elem.find_all("pre")
            for pre in nested_codes:
                extracted = self._extract_code_blocks(pre)
                if extracted:
                    code_samples.extend(extracted)
                pre.decompose()  # Remove so we don't double-count text

            nested_tables = elem.find_all("table")
            for tbl in nested_tables:
                table_data = self._extract_tables(tbl)
                if table_data:
                    tables.append(table_data)
                tbl.decompose()

            nested_images = elem.find_all("img")
            for img in nested_images:
                img_info = self._extract_image_info(img, source_file)
                if img_info:
                    img_info["index"] = len(images)
                    images.append(img_info)

            # Extract links from this element
            for a_tag in elem.find_all("a", href=True):
                link_info = self._extract_link_info(a_tag, source_file)
                if link_info:
                    links.append(link_info)

            # Regular text/paragraph content
            text = self._html_to_text(elem)
            if text and text.strip():
                text_parts.append(text.strip())

        image_count = len(images)

        section_dict = {
            "section_number": section_number,
            "heading": heading or "",
            "heading_level": heading_level or "h1",
            "text": "\n\n".join(text_parts),
            "headings": sub_headings,
            "code_samples": code_samples,
            "tables": tables,
            "images": images,
            "links": links,
            "source_file": str(source_file.name),
        }
        return section_dict, image_count

    # ------------------------------------------------------------------
    # Code block extraction
    # ------------------------------------------------------------------

    def _extract_code_blocks(self, elem: Tag) -> list[dict]:
        """Extract code blocks from <pre> and <code> elements.

        Handles multiple patterns:
        - <pre><code class="language-python">...</code></pre>
        - <pre class="code">...</pre>
        - Standalone <code>...</code> (only if substantial)

        Language detection is attempted from CSS classes first, falling
        back to content-based heuristics via _detect_language().

        Args:
            elem: A BeautifulSoup Tag (<pre> or <code>).

        Returns:
            List of code sample dicts with 'code', 'language', 'quality_score'.
        """
        results: list[dict] = []

        if elem.name == "pre":
            # Look for <code> child within <pre>
            code_elem = elem.find("code")
            if code_elem:
                code_text = code_elem.get_text()
                lang = self._detect_language_from_classes(code_elem)
                if not lang:
                    lang = self._detect_language_from_classes(elem)
            else:
                code_text = elem.get_text()
                lang = self._detect_language_from_classes(elem)

            code_text = code_text.strip()
            if code_text:
                quality = _score_code_quality(code_text)
                results.append(
                    {
                        "code": code_text,
                        "language": lang,
                        "quality_score": quality,
                    }
                )

        elif elem.name == "code":
            # Standalone <code> — only include if substantial
            code_text = elem.get_text().strip()
            if code_text and len(code_text) > 30:
                lang = self._detect_language_from_classes(elem)
                quality = _score_code_quality(code_text)
                results.append(
                    {
                        "code": code_text,
                        "language": lang,
                        "quality_score": quality,
                    }
                )

        return results

    def _detect_language_from_classes(self, elem: Tag) -> str:
        """Detect programming language from CSS classes on an element.

        Common conventions: ``language-python``, ``lang-js``, ``code-ruby``,
        ``highlight-go``, bare language names as class values.

        Args:
            elem: BeautifulSoup Tag with potential language class.

        Returns:
            Detected language string, or empty string if not found.
        """
        classes = elem.get("class", [])
        if not classes:
            return ""

        # Known class prefixes for language hints
        prefixes = ("language-", "lang-", "code-", "highlight-", "brush:")
        for cls in classes:
            cls_lower = cls.lower()
            for prefix in prefixes:
                if cls_lower.startswith(prefix):
                    return cls_lower[len(prefix) :]

        # Check for bare language names
        known_langs = {
            "python",
            "javascript",
            "typescript",
            "java",
            "ruby",
            "go",
            "rust",
            "cpp",
            "c",
            "csharp",
            "php",
            "swift",
            "kotlin",
            "scala",
            "html",
            "css",
            "sql",
            "bash",
            "shell",
            "json",
            "yaml",
            "xml",
            "markdown",
            "r",
            "perl",
            "lua",
            "dart",
            "haskell",
            "elixir",
            "clojure",
            "jsx",
            "tsx",
        }
        for cls in classes:
            if cls.lower() in known_langs:
                return cls.lower()

        return ""

    def _detect_language(self, code: str) -> str:
        """Detect programming language from code content using heuristics.

        Performs lightweight pattern matching against common language features.
        For more robust detection, the full LanguageDetector is used during
        the extract_html() pipeline.

        Args:
            code: Source code string.

        Returns:
            Best-guess language string, or empty string if unknown.
        """
        if not code or len(code) < 10:
            return ""

        # Quick heuristic patterns (ordered by specificity)
        patterns: list[tuple[str, str]] = [
            (r"\bdef\s+\w+\s*\(.*\)\s*(->\s*\w+)?\s*:", "python"),
            (r"\bimport\s+\w+\s*\n|from\s+\w+\s+import\b", "python"),
            (r"\bclass\s+\w+.*:\s*$", "python"),
            (r"\bfunction\s+\w+\s*\(", "javascript"),
            (r"\bconst\s+\w+\s*=\s*(async\s+)?\(", "javascript"),
            (r"\bexport\s+(default\s+)?", "javascript"),
            (r"\binterface\s+\w+\s*\{", "typescript"),
            (r":\s*(string|number|boolean|void)\b", "typescript"),
            (r"\bpackage\s+\w+;", "java"),
            (r"\bpublic\s+class\s+\w+", "java"),
            (r"\bfn\s+\w+\s*\(", "rust"),
            (r"\blet\s+mut\s+", "rust"),
            (r"\bfunc\s+\w+\s*\(", "go"),
            (r"\bpackage\s+main\b", "go"),
            (r"<\?php\b", "php"),
            (r"\$\w+\s*=\s*", "php"),
            (r"#include\s*<\w+", "c"),
            (r"\bint\s+main\s*\(", "c"),
            (r"\bstd::", "cpp"),
            (r"\busing\s+namespace\s+", "cpp"),
            (r"\brequire\s*\(", "javascript"),
            (r"^\s*<\w+[\s>]", "html"),
            (r"SELECT\s+.*\s+FROM\s+", "sql"),
            (r"#!/bin/(ba)?sh", "bash"),
            (r"\b(if|for|while)\s*\[", "bash"),
        ]

        for pattern, lang in patterns:
            if re.search(pattern, code, re.MULTILINE | re.IGNORECASE):
                return lang

        return ""

    # ------------------------------------------------------------------
    # Table extraction
    # ------------------------------------------------------------------

    def _extract_tables(self, table_elem: Tag) -> dict | None:
        """Extract an HTML table and convert to a markdown-ready dict.

        Handles <thead>/<tbody> structure as well as header-less tables.
        If no explicit <thead> is present, the first row is used as headers.

        Args:
            table_elem: BeautifulSoup <table> Tag.

        Returns:
            Dict with 'headers' (list[str]) and 'rows' (list[list[str]]),
            or None if the table has no meaningful content.
        """
        return _extract_table_from_html(table_elem)

    # ------------------------------------------------------------------
    # Image and link extraction
    # ------------------------------------------------------------------

    def _extract_image_info(self, img_elem: Tag, source_file: Path) -> dict | None:
        """Extract image information from an <img> tag.

        Captures src, alt text, title, and dimensions. Resolves relative
        src paths against the source file location.

        Args:
            img_elem: BeautifulSoup <img> Tag.
            source_file: Path to the containing HTML file.

        Returns:
            Image info dict or None if the img has no src.
        """
        src = img_elem.get("src", "")
        if not src:
            return None

        # Resolve relative paths
        resolved_src = self._resolve_relative_path(src, source_file)

        return {
            "src": resolved_src,
            "alt": img_elem.get("alt", ""),
            "title": img_elem.get("title", ""),
            "width": _parse_leading_int(img_elem.get("width")),
            "height": _parse_leading_int(img_elem.get("height")),
            "data": b"",  # Placeholder; actual image data loaded separately
        }

    def _extract_link_info(self, a_elem: Tag, source_file: Path) -> dict | None:
        """Extract link information from an <a> tag.

        Captures href, link text, and title. Resolves relative hrefs.
        Skips empty anchors and JavaScript links.

        Args:
            a_elem: BeautifulSoup <a> Tag with href attribute.
            source_file: Path to the containing HTML file.

        Returns:
            Link info dict or None if the link is empty or a JS link.
        """
        href = a_elem.get("href", "")
        if not href or href.startswith("javascript:") or href.startswith("#"):
            return None

        text = a_elem.get_text(strip=True)
        if not text:
            return None

        resolved_href = self._resolve_relative_path(href, source_file)

        return {
            "href": resolved_href,
            "text": text,
            "title": a_elem.get("title", ""),
        }

    def _resolve_relative_path(self, path: str, source_file: Path) -> str:
        """Resolve a relative path against the source file's directory.

        Absolute URLs (http/https) and data URIs are returned as-is.
        Relative paths are resolved against the source file's parent
        directory and returned as POSIX-style strings.

        Args:
            path: The URL or relative path to resolve.
            source_file: The HTML file containing this reference.

        Returns:
            Resolved path or URL string.
        """
        # Absolute URLs and data URIs — return as-is
        if path.startswith(("http://", "https://", "data:", "//", "mailto:")):
            return path

        # Resolve relative to source file directory
        try:
            base_dir = source_file.parent
            resolved = (base_dir / path).resolve()
            return str(resolved)
        except Exception:
            return path

    # ------------------------------------------------------------------
    # HTML-to-text conversion
    # ------------------------------------------------------------------

    def _html_to_text(self, elem: Tag) -> str:
        """Convert an HTML element to clean markdown-like text.

        Processes the element's content recursively, converting:
        - <p> to paragraphs with double newlines
        - <br> to newlines
        - <strong>/<b> to **bold**
        - <em>/<i> to *italic*
        - <a> to [text](href) markdown links
        - <ul>/<ol> to markdown list items
        - <blockquote> to > prefixed lines
        - <code> (inline) to `backticks`
        - Heading tags to markdown headings

        Args:
            elem: BeautifulSoup Tag to convert.

        Returns:
            Cleaned text string with markdown formatting.
        """
        if elem.name is None:
            return str(elem).strip()

        parts: list[str] = []

        for child in elem.children:
            if not hasattr(child, "name"):
                # NavigableString (raw text)
                text = str(child)
                if text.strip():
                    parts.append(text)
                continue

            if child.name is None:
                continue

            tag = child.name

            if tag == "br":
                parts.append("\n")
            elif tag in ("p", "div"):
                inner = self._html_to_text(child)
                if inner.strip():
                    parts.append(f"\n\n{inner.strip()}\n\n")
            elif tag in ("strong", "b"):
                inner = child.get_text(strip=True)
                if inner:
                    parts.append(f"**{inner}**")
            elif tag in ("em", "i"):
                inner = child.get_text(strip=True)
                if inner:
                    parts.append(f"*{inner}*")
            elif tag == "a" and child.get("href"):
                link_text = child.get_text(strip=True)
                href = child.get("href", "")
                if link_text and href and not href.startswith("javascript:"):
                    parts.append(f"[{link_text}]({href})")
                elif link_text:
                    parts.append(link_text)
            elif tag in ("ul", "ol"):
                items = child.find_all("li", recursive=False)
                for idx, li in enumerate(items):
                    li_text = li.get_text(strip=True)
                    if li_text:
                        prefix = f"{idx + 1}." if tag == "ol" else "-"
                        parts.append(f"\n{prefix} {li_text}")
                parts.append("\n")
            elif tag == "blockquote":
                bq_text = child.get_text(strip=True)
                if bq_text:
                    lines = bq_text.split("\n")
                    quoted = "\n".join(f"> {line}" for line in lines)
                    parts.append(f"\n\n{quoted}\n\n")
            elif tag == "code":
                # Inline code (not inside <pre>)
                if child.find_parent("pre") is None:
                    code_text = child.get_text()
                    if code_text.strip():
                        parts.append(f"`{code_text.strip()}`")
            elif tag in ("h3", "h4", "h5", "h6"):
                level = int(tag[1])
                inner = child.get_text(strip=True)
                if inner:
                    parts.append(f"\n\n{'#' * level} {inner}\n\n")
            elif tag == "dl":
                # Definition lists
                for dt in child.find_all("dt"):
                    term = dt.get_text(strip=True)
                    dd = dt.find_next_sibling("dd")
                    definition = dd.get_text(strip=True) if dd else ""
                    parts.append(f"\n**{term}**: {definition}")
                parts.append("\n")
            elif tag == "hr":
                parts.append("\n\n---\n\n")
            else:
                # Generic element — extract text
                inner = self._html_to_text(child)
                if inner.strip():
                    parts.append(inner)

        result = "".join(parts)
        # Collapse excessive whitespace
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result

    # ------------------------------------------------------------------
    # Build-side overrides (base machinery in DocumentSkillBuilder)
    # ------------------------------------------------------------------

    @property
    def source_stem(self) -> str:
        """Reference-filename base: file stem for a single HTML file,
        the skill name for a directory source ('' when no path)."""
        if not self.html_path:
            return ""
        path = Path(self.html_path)
        return path.stem if path.is_file() else self.name

    def categorize_content(self) -> dict:
        """Categorize sections based on headings or keywords.

        Overrides the base categorizer: html's single-source fast path is
        gated on the path being an actual FILE (not just a truthy path), and
        a directory source groups sections per source HTML file — neither is
        expressible via the base hooks.

        For single-source HTML (single file), groups all sections under one
        category named after the source. For directories, creates categories
        per file. Keyword-based categorization is used when ``self.categories``
        is configured.

        Returns:
            Dict mapping category keys to dicts with 'title' and 'pages'.
        """
        print("\n📋 Categorizing content...")

        categorized: dict[str, dict] = {}
        sections = self.extracted_data.get("pages", [])

        # For a single HTML file, use single category
        total_files = self.extracted_data.get("total_files", 1)
        if total_files == 1 and self.html_path:
            path = Path(self.html_path)
            if path.is_file():
                basename = path.stem
                category_key = self._sanitize_filename(basename)
                categorized[category_key] = {
                    "title": basename,
                    "pages": sections,
                }
                print("✅ Created 1 category (single HTML file)")
                print(f"   - {basename}: {len(sections)} sections")
                return categorized

        # For directory with multiple files, group by source file
        if total_files > 1:
            for section in sections:
                source = section.get("source_file", "unknown")
                source_stem = Path(source).stem
                cat_key = self._sanitize_filename(source_stem)
                if cat_key not in categorized:
                    categorized[cat_key] = {
                        "title": source_stem,
                        "pages": [],
                    }
                categorized[cat_key]["pages"].append(section)

            print(f"✅ Created {len(categorized)} categories (multi-file)")
            for _key, cat_data in categorized.items():
                print(f"   - {cat_data['title']}: {len(cat_data['pages'])} sections")
            return categorized

        # Keyword-based categorization
        if self.categories:
            first_value = next(iter(self.categories.values()), None)
            if isinstance(first_value, list) and first_value and isinstance(first_value[0], dict):
                # Already categorized format
                for cat_key, pages in self.categories.items():
                    categorized[cat_key] = {
                        "title": cat_key.replace("_", " ").title(),
                        "pages": pages,
                    }
            else:
                # Keyword-based categorization
                for cat_key in self.categories:
                    categorized[cat_key] = {
                        "title": cat_key.replace("_", " ").title(),
                        "pages": [],
                    }

                for section in sections:
                    text = section.get("text", "").lower()
                    heading_text = section.get("heading", "").lower()

                    scores: dict[str, int] = {}
                    for cat_key, keywords in self.categories.items():
                        if isinstance(keywords, list):
                            score = sum(
                                1
                                for kw in keywords
                                if isinstance(kw, str)
                                and (kw.lower() in text or kw.lower() in heading_text)
                            )
                        else:
                            score = 0
                        if score > 0:
                            scores[cat_key] = score

                    if scores:
                        best_cat = max(scores, key=scores.get)
                        categorized[best_cat]["pages"].append(section)
                    else:
                        if "other" not in categorized:
                            categorized["other"] = {
                                "title": "Other",
                                "pages": [],
                            }
                        categorized["other"]["pages"].append(section)
        else:
            # No categorization — single category
            categorized["content"] = {"title": "Content", "pages": sections}

        print(f"✅ Created {len(categorized)} categories")
        for _cat_key, cat_data in categorized.items():
            print(f"   - {cat_data['title']}: {len(cat_data['pages'])} sections")

        return categorized

    def _write_reference_section(self, f, section: dict) -> None:
        """Write one section's body into a reference file.

        Overrides the base to annotate the source HTML file next to the
        section number, render images as markdown links (src/alt/title —
        bytes are never embedded), and append the html-only Links block.
        """
        sec_num = section.get("section_number", "?")
        heading = section.get("heading", "")
        heading_level = section.get("heading_level", "h1")
        source = section.get("source_file", "")

        f.write(f"---\n\n**📄 Source: Section {sec_num}**")
        if source:
            f.write(f" *({source})*")
        f.write("\n\n")

        # Add heading
        if heading:
            md_level = "#" * (int(heading_level[1]) + 1) if heading_level else "##"
            f.write(f"{md_level} {heading}\n\n")

        # Add sub-headings (h3+) found within the section
        for sub_heading in section.get("headings", []):
            sub_level = sub_heading.get("level", "h3")
            sub_text = sub_heading.get("text", "")
            if sub_text:
                sub_md = "#" * (int(sub_level[1]) + 1) if sub_level else "###"
                f.write(f"{sub_md} {sub_text}\n\n")

        # Add text content
        if section.get("text"):
            f.write(f"{section['text']}\n\n")

        # Add code samples
        code_list = section.get("code_samples", [])
        if code_list:
            f.write("### Code Examples\n\n")
            for code in code_list:
                lang = code.get("language", "")
                f.write(f"```{lang}\n{code['code']}\n```\n\n")

        # Add tables as markdown
        table_list = section.get("tables", [])
        if table_list:
            f.write("### Tables\n\n")
            for table in table_list:
                self._write_markdown_table(f, table)

        # Add images
        images = section.get("images", [])
        if images:
            f.write("### Images\n\n")
            for img in images:
                alt = img.get("alt", "")
                src = img.get("src", "")
                title = img.get("title", "")
                if alt or src:
                    display = alt or title or f"Image {img.get('index', 0)}"
                    f.write(f"![{display}]({src})\n\n")

        # Add notable links
        link_list = section.get("links", [])
        if link_list:
            f.write("### Links\n\n")
            for link in link_list[:20]:  # Cap at 20 links per section
                f.write(f"- [{link['text']}]({link['href']})\n")
            f.write("\n")

        f.write("---\n\n")

    def _write_index_statistics(self, f) -> None:
        """Statistics block of index.md, with the html-only file count line."""
        f.write(f"- Total sections: {self.extracted_data.get('total_sections', 0)}\n")
        f.write(f"- Code blocks: {self.extracted_data.get('total_code_blocks', 0)}\n")
        f.write(f"- Images: {self.extracted_data.get('total_images', 0)}\n")
        f.write(f"- HTML files processed: {self.extracted_data.get('total_files', 0)}\n")

        # Metadata
        metadata = self.extracted_data.get("metadata", {})
        if metadata.get("author"):
            f.write(f"- Author: {metadata['author']}\n")

    # _generate_skill_md and _format_patterns_from_content are inherited
    # from DocumentSkillBuilder: SKILL_MD_METADATA_FIELDS / PATTERN_KEYWORDS
    # plus the two hooks below reproduce the html output exactly.

    def _write_skill_md_metadata(self, f, metadata) -> None:
        """Document Information body: shared fields plus the html-only
        multi-file "Source files" line."""
        super()._write_skill_md_metadata(f, metadata)
        total_files = self.extracted_data.get("total_files", 1)
        if total_files > 1:
            f.write(f"**Source files:** {total_files} HTML files\n\n")

    def _write_skill_md_extra_stats(self, f) -> None:
        """Add the html-only file count to the SKILL.md statistics block."""
        f.write(f"- **HTML Files**: {self.extracted_data.get('total_files', 0)}\n")


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------
