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

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

# BeautifulSoup is a core dependency (always available)
from bs4 import BeautifulSoup, Comment, Tag

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


class HtmlToSkillConverter:
    """Convert local HTML files to a skill.

    Supports single HTML files and directories of HTML files. Parses document
    structure, extracts headings, content, code blocks, tables, images, and
    links, then builds a complete skill directory structure.

    Attributes:
        config: Configuration dict with name, html_path, description.
        name: Skill name.
        html_path: Path to the HTML file or directory.
        description: Skill description text.
        skill_dir: Output directory for the built skill.
        data_file: Path to the intermediate extracted JSON file.
        extracted_data: Parsed extraction results dict.
    """

    def __init__(self, config: dict) -> None:
        """Initialize the HTML to skill converter.

        Args:
            config: Configuration dict containing:
                - name (str): Skill name (required).
                - html_path (str): Path to HTML file or directory (optional).
                - description (str): Skill description (optional).
                - categories (dict): Category definitions for content grouping.
        """
        self.config = config
        self.name: str = config["name"]
        self.html_path: str = config.get("html_path", "")
        self.description: str = (
            config.get("description") or f"Use when referencing {self.name} documentation"
        )

        # Paths
        self.skill_dir = f"output/{self.name}"
        self.data_file = f"output/{self.name}_extracted.json"

        # Categories config
        self.categories: dict = config.get("categories", {})

        # Extracted data
        self.extracted_data: dict | None = None

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
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
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
        headers: list[str] = []
        rows: list[list[str]] = []

        # Try <thead> first for headers
        thead = table_elem.find("thead")
        if thead:
            header_row = thead.find("tr")
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

        # Body rows
        tbody = table_elem.find("tbody") or table_elem
        for row in tbody.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            # Skip the header row we already captured
            if cells and cells != headers:
                rows.append(cells)

        # If no explicit thead, use first row as header
        if not headers and rows:
            headers = rows.pop(0)

        if not headers and not rows:
            return None

        return {"headers": headers, "rows": rows}

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
            "width": int(img_elem.get("width", 0) or 0),
            "height": int(img_elem.get("height", 0) or 0),
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
    # Load / Categorize / Build
    # ------------------------------------------------------------------

    def load_extracted_data(self, json_path: str) -> bool:
        """Load previously extracted data from JSON.

        Args:
            json_path: Path to the intermediate extracted JSON file.

        Returns:
            True on success.
        """
        print(f"\n📂 Loading extracted data from: {json_path}")
        with open(json_path, encoding="utf-8") as f:
            self.extracted_data = json.load(f)
        total = self.extracted_data.get("total_sections", len(self.extracted_data.get("pages", [])))
        print(f"✅ Loaded {total} sections")
        return True

    def categorize_content(self) -> dict:
        """Categorize sections based on headings or keywords.

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

    def build_skill(self) -> None:
        """Build complete skill structure from extracted data.

        Creates the output directory tree, generates reference markdown files,
        an index file, and the main SKILL.md file. Delegates to private
        generator methods for each component.
        """
        print(f"\n🏗️  Building skill: {self.name}")

        # Create directories
        os.makedirs(f"{self.skill_dir}/references", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/scripts", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/assets", exist_ok=True)

        # Categorize content
        categorized = self.categorize_content()

        # Generate reference files
        print("\n📝 Generating reference files...")
        total_sections = len(categorized)
        section_num = 1
        for cat_key, cat_data in categorized.items():
            self._generate_reference_file(cat_key, cat_data, section_num, total_sections)
            section_num += 1

        # Generate index
        self._generate_index(categorized)

        # Generate SKILL.md
        self._generate_skill_md(categorized)

        print(f"\n✅ Skill built successfully: {self.skill_dir}/")
        print(f"\n📦 Next step: Package with: skill-seekers package {self.skill_dir}/")

    # ------------------------------------------------------------------
    # Private generators
    # ------------------------------------------------------------------

    def _generate_reference_file(
        self,
        _cat_key: str,
        cat_data: dict,
        section_num: int,
        total_sections: int,
    ) -> None:
        """Generate a reference markdown file for a content category.

        Creates a markdown file containing all sections in the category,
        with headings, text content, code examples, tables, and images.

        Args:
            _cat_key: Category key (unused but matches epub pattern).
            cat_data: Category dict with 'title' and 'pages' keys.
            section_num: Current section number for filename generation.
            total_sections: Total number of categories for filename logic.
        """
        sections = cat_data["pages"]

        # Determine filename
        html_basename = ""
        if self.html_path:
            path = Path(self.html_path)
            html_basename = path.stem if path.is_file() else self.name

        if sections:
            section_nums = [s.get("section_number", i + 1) for i, s in enumerate(sections)]

            if total_sections == 1:
                filename = (
                    f"{self.skill_dir}/references/{html_basename}.md"
                    if html_basename
                    else f"{self.skill_dir}/references/main.md"
                )
            else:
                sec_range = f"s{min(section_nums)}-s{max(section_nums)}"
                base_name = html_basename if html_basename else "section"
                filename = f"{self.skill_dir}/references/{base_name}_{sec_range}.md"
        else:
            filename = f"{self.skill_dir}/references/section_{section_num:02d}.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {cat_data['title']}\n\n")

            for section in sections:
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
                        headers = table.get("headers", [])
                        rows = table.get("rows", [])
                        if headers:
                            f.write("| " + " | ".join(str(h) for h in headers) + " |\n")
                            f.write("| " + " | ".join("---" for _ in headers) + " |\n")
                        for row in rows:
                            f.write("| " + " | ".join(str(c) for c in row) + " |\n")
                        f.write("\n")

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

        print(f"   Generated: {filename}")

    def _generate_index(self, categorized: dict) -> None:
        """Generate reference index file.

        Creates an index.md in the references directory listing all categories
        with links, section counts, and overall statistics.

        Args:
            categorized: Dict of category_key -> category data.
        """
        filename = f"{self.skill_dir}/references/index.md"

        html_basename = ""
        if self.html_path:
            path = Path(self.html_path)
            html_basename = path.stem if path.is_file() else self.name

        total_categories = len(categorized)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {self.name.title()} Documentation Reference\n\n")
            f.write("## Categories\n\n")

            section_num = 1
            for _cat_key, cat_data in categorized.items():
                sections = cat_data["pages"]
                section_count = len(sections)

                if sections:
                    section_nums = [s.get("section_number", i + 1) for i, s in enumerate(sections)]
                    sec_range_str = f"Sections {min(section_nums)}-{max(section_nums)}"

                    if total_categories == 1:
                        link_filename = f"{html_basename}.md" if html_basename else "main.md"
                    else:
                        sec_range = f"s{min(section_nums)}-s{max(section_nums)}"
                        base_name = html_basename if html_basename else "section"
                        link_filename = f"{base_name}_{sec_range}.md"
                else:
                    link_filename = f"section_{section_num:02d}.md"
                    sec_range_str = "N/A"

                f.write(
                    f"- [{cat_data['title']}]({link_filename}) "
                    f"({section_count} sections, {sec_range_str})\n"
                )
                section_num += 1

            f.write("\n## Statistics\n\n")
            f.write(f"- Total sections: {self.extracted_data.get('total_sections', 0)}\n")
            f.write(f"- Code blocks: {self.extracted_data.get('total_code_blocks', 0)}\n")
            f.write(f"- Images: {self.extracted_data.get('total_images', 0)}\n")
            f.write(f"- HTML files processed: {self.extracted_data.get('total_files', 0)}\n")

            # Metadata
            metadata = self.extracted_data.get("metadata", {})
            if metadata.get("author"):
                f.write(f"- Author: {metadata['author']}\n")

        print(f"   Generated: {filename}")

    def _generate_skill_md(self, categorized: dict) -> None:
        """Generate main SKILL.md file.

        Creates the top-level SKILL.md with YAML frontmatter, document
        information, usage guidance, section overview, key concepts,
        code examples, table summary, statistics, and navigation links.

        Args:
            categorized: Dict of category_key -> category data.
        """
        filename = f"{self.skill_dir}/SKILL.md"

        skill_name = self.name.lower().replace("_", "-").replace(" ", "-")[:64]
        desc = self.description[:1024] if len(self.description) > 1024 else self.description

        with open(filename, "w", encoding="utf-8") as f:
            # YAML frontmatter
            f.write("---\n")
            f.write(f"name: {skill_name}\n")
            f.write(f"description: {desc}\n")
            f.write("---\n\n")

            f.write(f"# {self.name.title()} Documentation Skill\n\n")
            f.write(f"{self.description}\n\n")

            # Document metadata
            metadata = self.extracted_data.get("metadata", {})
            if any(v for v in metadata.values() if v):
                f.write("## 📋 Document Information\n\n")
                if metadata.get("title"):
                    f.write(f"**Title:** {metadata['title']}\n\n")
                if metadata.get("author"):
                    f.write(f"**Author:** {metadata['author']}\n\n")
                if metadata.get("language"):
                    f.write(f"**Language:** {metadata['language']}\n\n")
                if metadata.get("description"):
                    f.write(f"**Description:** {metadata['description']}\n\n")
                if metadata.get("keywords"):
                    f.write(f"**Keywords:** {metadata['keywords']}\n\n")
                total_files = self.extracted_data.get("total_files", 1)
                if total_files > 1:
                    f.write(f"**Source files:** {total_files} HTML files\n\n")

            # When to Use
            f.write("## 💡 When to Use This Skill\n\n")
            f.write("Use this skill when you need to:\n")
            f.write(f"- Understand {self.name} concepts and fundamentals\n")
            f.write("- Look up API references and technical specifications\n")
            f.write("- Find code examples and implementation patterns\n")
            f.write("- Review tutorials, guides, and best practices\n")
            f.write("- Explore the complete documentation structure\n\n")

            # Section Overview
            total_sections = self.extracted_data.get("total_sections", 0)
            f.write("## 📖 Section Overview\n\n")
            f.write(f"**Total Sections:** {total_sections}\n\n")
            f.write("**Content Breakdown:**\n\n")
            for _cat_key, cat_data in categorized.items():
                section_count = len(cat_data["pages"])
                f.write(f"- **{cat_data['title']}**: {section_count} sections\n")
            f.write("\n")

            # Key Concepts from headings
            f.write(self._format_key_concepts())

            # Quick Reference patterns
            f.write("## ⚡ Quick Reference\n\n")
            f.write(self._format_patterns_from_content())

            # Code examples (top 15, grouped by language)
            all_code: list[dict] = []
            for section in self.extracted_data.get("pages", []):
                all_code.extend(section.get("code_samples", []))

            all_code.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
            top_code = all_code[:15]

            if top_code:
                f.write("## 📝 Code Examples\n\n")
                f.write("*High-quality examples extracted from documentation*\n\n")

                by_lang: dict[str, list] = {}
                for code in top_code:
                    lang = code.get("language", "unknown")
                    by_lang.setdefault(lang, []).append(code)

                for lang in sorted(by_lang.keys()):
                    examples = by_lang[lang]
                    f.write(f"### {lang.title()} Examples ({len(examples)})\n\n")
                    for i, code in enumerate(examples[:5], 1):
                        quality = code.get("quality_score", 0)
                        code_text = code.get("code", "")
                        f.write(f"**Example {i}** (Quality: {quality:.1f}/10):\n\n")
                        f.write(f"```{lang}\n")
                        if len(code_text) <= 500:
                            f.write(code_text)
                        else:
                            f.write(code_text[:500] + "\n...")
                        f.write("\n```\n\n")

            # Table Summary (first 5 tables)
            all_tables: list[tuple[str, dict]] = []
            for section in self.extracted_data.get("pages", []):
                for table in section.get("tables", []):
                    all_tables.append((section.get("heading", ""), table))

            if all_tables:
                f.write("## 📊 Table Summary\n\n")
                f.write(f"*{len(all_tables)} table(s) found in document*\n\n")
                for section_heading, table in all_tables[:5]:
                    if section_heading:
                        f.write(f"**From section: {section_heading}**\n\n")
                    headers = table.get("headers", [])
                    rows = table.get("rows", [])
                    if headers:
                        f.write("| " + " | ".join(str(h) for h in headers) + " |\n")
                        f.write("| " + " | ".join("---" for _ in headers) + " |\n")
                        for row in rows[:5]:
                            f.write("| " + " | ".join(str(c) for c in row) + " |\n")
                        f.write("\n")

            # Statistics
            f.write("## 📊 Documentation Statistics\n\n")
            f.write(f"- **Total Sections**: {total_sections}\n")
            f.write(f"- **Code Blocks**: {self.extracted_data.get('total_code_blocks', 0)}\n")
            f.write(f"- **Images/Diagrams**: {self.extracted_data.get('total_images', 0)}\n")
            f.write(f"- **Tables**: {len(all_tables)}\n")
            f.write(f"- **HTML Files**: {self.extracted_data.get('total_files', 0)}\n")

            langs = self.extracted_data.get("languages_detected", {})
            if langs:
                f.write(f"- **Programming Languages**: {len(langs)}\n\n")
                f.write("**Language Breakdown:**\n\n")
                for lang, count in sorted(langs.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- {lang}: {count} examples\n")
                f.write("\n")

            # Navigation
            f.write("## 🗺️ Navigation\n\n")
            f.write("**Reference Files:**\n\n")
            for _cat_key, cat_data in categorized.items():
                cat_file = self._sanitize_filename(cat_data["title"])
                f.write(f"- `references/{cat_file}.md` - {cat_data['title']}\n")
            f.write("\n")
            f.write("See `references/index.md` for complete documentation structure.\n\n")

            # Footer
            f.write("---\n\n")
            f.write("**Generated by Skill Seeker** | HTML Scraper\n")

        with open(filename, encoding="utf-8") as f:
            line_count = len(f.read().split("\n"))
        print(f"   Generated: {filename} ({line_count} lines)")

    # ------------------------------------------------------------------
    # Content analysis helpers
    # ------------------------------------------------------------------

    def _format_key_concepts(self) -> str:
        """Extract key concepts from headings across all sections.

        Collects h1 and h2 headings as major topics, and h3+ headings as
        subtopics. Returns formatted markdown for inclusion in SKILL.md.

        Returns:
            Formatted markdown string with key concepts section.
        """
        all_headings: list[tuple[str, str]] = []
        for section in self.extracted_data.get("pages", []):
            # Main heading
            heading = section.get("heading", "").strip()
            level = section.get("heading_level", "h1")
            if heading and len(heading) > 3:
                all_headings.append((level, heading))
            # Sub-headings
            for sub in section.get("headings", []):
                text = sub.get("text", "").strip()
                sub_level = sub.get("level", "h3")
                if text and len(text) > 3:
                    all_headings.append((sub_level, text))

        if not all_headings:
            return ""

        content = "## 🔑 Key Concepts\n\n"
        content += "*Main topics covered in this documentation*\n\n"

        h1_headings = [text for level, text in all_headings if level == "h1"]
        h2_headings = [text for level, text in all_headings if level == "h2"]

        if h1_headings:
            content += "**Major Topics:**\n\n"
            for heading in h1_headings[:10]:
                content += f"- {heading}\n"
            content += "\n"

        if h2_headings:
            content += "**Subtopics:**\n\n"
            for heading in h2_headings[:15]:
                content += f"- {heading}\n"
            content += "\n"

        return content

    def _format_patterns_from_content(self) -> str:
        """Extract common documentation patterns from section headings.

        Searches for well-known heading keywords like 'getting started',
        'installation', 'api', etc. and groups them by type.

        Returns:
            Formatted markdown string with pattern descriptions.
        """
        patterns: list[dict] = []
        pattern_keywords = [
            "getting started",
            "installation",
            "configuration",
            "usage",
            "api",
            "examples",
            "tutorial",
            "guide",
            "best practices",
            "troubleshooting",
            "faq",
            "reference",
            "changelog",
        ]

        for section in self.extracted_data.get("pages", []):
            heading_text = section.get("heading", "").lower()
            sec_num = section.get("section_number", 0)

            for keyword in pattern_keywords:
                if keyword in heading_text:
                    patterns.append(
                        {
                            "type": keyword.title(),
                            "heading": section.get("heading", ""),
                            "section": sec_num,
                        }
                    )
                    break

        if not patterns:
            return "*See reference files for detailed content*\n\n"

        content = "*Common documentation patterns found:*\n\n"
        by_type: dict[str, list] = {}
        for pattern in patterns:
            ptype = pattern["type"]
            by_type.setdefault(ptype, []).append(pattern)

        for ptype in sorted(by_type.keys()):
            items = by_type[ptype]
            content += f"**{ptype}** ({len(items)} sections):\n"
            for item in items[:3]:
                content += f"- {item['heading']} (section {item['section']})\n"
            content += "\n"

        return content

    def _sanitize_filename(self, name: str) -> str:
        """Convert string to safe filename.

        Removes special characters, converts spaces and hyphens to
        underscores, and lowercases the result.

        Args:
            name: Raw string to sanitize.

        Returns:
            Filesystem-safe filename string.
        """
        safe = re.sub(r"[^\w\s-]", "", name.lower())
        safe = re.sub(r"[-\s]+", "_", safe)
        return safe


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _score_code_quality(code: str) -> float:
    """Simple quality heuristic for code blocks (0-10 scale).

    Scores based on line count, presence of definitions, imports,
    indentation, and operator usage. Short snippets are penalized.

    Args:
        code: Source code string.

    Returns:
        Quality score between 0.0 and 10.0.
    """
    if not code:
        return 0.0

    score = 5.0
    lines = code.strip().split("\n")
    line_count = len(lines)

    # More lines = more substantial
    if line_count >= 10:
        score += 2.0
    elif line_count >= 5:
        score += 1.0

    # Has function/class definitions
    if re.search(r"\b(def |class |function |func |fn )", code):
        score += 1.5

    # Has imports/require
    if re.search(r"\b(import |from .+ import|require\(|#include|using )", code):
        score += 0.5

    # Has indentation (structured code)
    if re.search(r"^    ", code, re.MULTILINE):
        score += 0.5

    # Has assignment, operators, or common code syntax
    if re.search(r"[=:{}()\[\]]", code):
        score += 0.3

    # Very short snippets get penalized
    if len(code) < 30:
        score -= 2.0

    return min(10.0, max(0.0, score))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point for the HTML scraper.

    Parses command-line arguments and runs the extraction/build pipeline.
    Supports two workflows:
    1. Direct HTML extraction: ``--html-path page.html --name myskill``
    2. Build from JSON: ``--from-json page_extracted.json``

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = argparse.ArgumentParser(
        description="Convert local HTML files to skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --html-path page.html --name myskill\n"
            "  %(prog)s --html-path ./docs/ --name myskill\n"
            "  %(prog)s --from-json page_extracted.json\n"
        ),
    )

    # Shared universal args
    from .arguments.common import add_all_standard_arguments

    add_all_standard_arguments(parser)

    # Override enhance-level default to 0 for HTML
    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0
            action.help = (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled (default for HTML), 1=SKILL.md only, "
                "2=+architecture/config, 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, "
                "otherwise LOCAL (Claude Code)"
            )

    # HTML-specific args
    parser.add_argument(
        "--html-path",
        type=str,
        help="Path to HTML file or directory of HTML files",
        metavar="PATH",
    )
    parser.add_argument(
        "--from-json",
        type=str,
        help="Build skill from previously extracted JSON",
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
        source = getattr(args, "html_path", None) or getattr(args, "from_json", None) or "(none)"
        print(f"\n{'=' * 60}")
        print("DRY RUN: HTML Extraction")
        print(f"{'=' * 60}")
        print(f"Source:         {source}")
        print(f"Name:           {getattr(args, 'name', None) or '(auto-detect)'}")
        print(f"Enhance level:  {getattr(args, 'enhance_level', 0)}")
        print(f"\n✅ Dry run complete")
        return 0

    # Validate inputs
    if not (getattr(args, "html_path", None) or getattr(args, "from_json", None)):
        parser.error("Must specify --html-path or --from-json")

    # Build from JSON workflow
    if getattr(args, "from_json", None):
        name = Path(args.from_json).stem.replace("_extracted", "")
        config = {
            "name": getattr(args, "name", None) or name,
            "description": getattr(args, "description", None)
            or f"Use when referencing {name} documentation",
        }
        try:
            converter = HtmlToSkillConverter(config)
            converter.load_extracted_data(args.from_json)
            converter.build_skill()
        except Exception as e:
            print(f"\n❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
        return 0

    # Direct HTML mode
    if not getattr(args, "name", None):
        # Auto-detect name from path
        path = Path(args.html_path)
        args.name = path.stem if path.is_file() else path.name

    config = {
        "name": args.name,
        "html_path": args.html_path,
        # Pass None so extract_html() can infer from HTML metadata
        "description": getattr(args, "description", None),
    }

    try:
        converter = HtmlToSkillConverter(config)

        # Extract
        if not converter.extract_html():
            print(
                "\n❌ HTML extraction failed - see error above",
                file=sys.stderr,
            )
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
                    "   (Workflow provides specialized analysis,"
                    " enhancement provides general improvements)"
                )
            print("")

            skill_dir = converter.skill_dir
            if api_key:
                try:
                    from skill_seekers.cli.enhance_skill import (
                        enhance_skill_md,
                    )

                    enhance_skill_md(skill_dir, api_key)
                    print("✅ API enhancement complete!")
                except ImportError:
                    print("❌ API enhancement not available. Falling back to LOCAL mode...")
                    from skill_seekers.cli.enhance_skill_local import (
                        LocalSkillEnhancer,
                    )

                    enhancer = LocalSkillEnhancer(Path(skill_dir))
                    enhancer.run(headless=True)
                    print("✅ Local enhancement complete!")
            else:
                from skill_seekers.cli.enhance_skill_local import (
                    LocalSkillEnhancer,
                )

                enhancer = LocalSkillEnhancer(Path(skill_dir))
                enhancer.run(headless=True)
                print("✅ Local enhancement complete!")

    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(
            f"\n❌ Unexpected error during HTML processing: {e}",
            file=sys.stderr,
        )
        import traceback

        traceback.print_exc()
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
