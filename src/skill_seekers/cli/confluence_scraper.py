#!/usr/bin/env python3
"""
Confluence Documentation to Skill Converter

Converts Confluence spaces into AI-ready skills by extracting page content,
hierarchy, code blocks, tables, and attachments. Supports two extraction modes:

1. **API mode**: Connects to a Confluence instance via the Atlassian REST API
   (requires ``atlassian-python-api``). Fetches pages from a specified space,
   preserving the parent-child hierarchy. Requires ``--base-url``, ``--space-key``,
   and authentication via ``--username`` / ``--token`` (or env vars).

2. **Export mode**: Parses a Confluence HTML/XML export directory previously
   downloaded from the Confluence admin UI. Requires ``--export-path`` pointing
   to the extracted export directory containing ``entities.xml`` or HTML files.

Usage:
    # API mode
    skill-seekers confluence --base-url https://wiki.example.com \\
        --space-key PROJ --username user@example.com --token $CONFLUENCE_TOKEN \\
        --name my-project-wiki

    # Export mode
    skill-seekers confluence --export-path ./confluence-export/ --name my-wiki

    # Build from previously extracted JSON
    skill-seekers confluence --from-json my-wiki_extracted.json

    # Standalone execution
    python3 -m skill_seekers.cli.confluence_scraper --base-url https://wiki.example.com \\
        --space-key DEV --name dev-wiki --max-pages 200
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from skill_seekers.cli.skill_converter import SkillConverter

# Optional dependency guard for atlassian-python-api
try:
    from atlassian import Confluence

    ATLASSIAN_AVAILABLE = True
except ImportError:
    ATLASSIAN_AVAILABLE = False

# BeautifulSoup is a core dependency (always available)
from bs4 import BeautifulSoup, Comment, Tag

logger = logging.getLogger(__name__)

# Confluence-specific HTML macro class patterns to strip during cleaning
_CONFLUENCE_MACRO_CLASSES = {
    "confluence-information-macro",
    "confluence-information-macro-body",
    "confluence-information-macro-icon",
    "expand-container",
    "expand-content",
    "expand-control",
    "plugin-tabmeta",
    "plugin_pagetree",
    "page-metadata",
    "aui-message",
}

# Confluence macro element tag names (structured-macro in storage format)
_STORAGE_MACRO_TAGS = {
    "ac:structured-macro",
    "ac:rich-text-body",
    "ac:parameter",
    "ac:plain-text-body",
    "ac:image",
    "ac:link",
    "ac:emoticon",
    "ac:task-list",
    "ac:task",
    "ac:task-body",
    "ac:task-status",
    "ri:attachment",
    "ri:page",
    "ri:space",
    "ri:url",
    "ri:user",
}

# Known Confluence code macro language mappings
_CODE_MACRO_LANGS = {
    "py": "python",
    "python": "python",
    "python3": "python",
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "java": "java",
    "bash": "bash",
    "sh": "bash",
    "shell": "bash",
    "sql": "sql",
    "xml": "xml",
    "html": "html",
    "css": "css",
    "json": "json",
    "yaml": "yaml",
    "yml": "yaml",
    "ruby": "ruby",
    "go": "go",
    "golang": "go",
    "rust": "rust",
    "c": "c",
    "cpp": "cpp",
    "csharp": "csharp",
    "cs": "csharp",
    "kotlin": "kotlin",
    "swift": "swift",
    "scala": "scala",
    "groovy": "groovy",
    "perl": "perl",
    "php": "php",
    "r": "r",
    "powershell": "powershell",
    "dockerfile": "dockerfile",
    "terraform": "hcl",
    "hcl": "hcl",
    "markdown": "markdown",
    "text": "",
    "none": "",
}


def _check_atlassian_deps() -> None:
    """Raise RuntimeError if atlassian-python-api is not installed."""
    if not ATLASSIAN_AVAILABLE:
        raise RuntimeError(
            "atlassian-python-api is required for Confluence API mode.\n"
            "Install with: pip install atlassian-python-api\n"
            'Or: pip install "skill-seekers[confluence]"'
        )


def infer_description_from_confluence(
    space_info: dict | None = None,
    name: str = "",
) -> str:
    """Infer skill description from Confluence space metadata.

    Args:
        space_info: Confluence space metadata dict (name, description, key).
        name: Skill name for fallback.

    Returns:
        Description string suitable for "Use when..." format.
    """
    if space_info:
        desc_text = space_info.get("description", "")
        if isinstance(desc_text, dict):
            # Confluence API returns description as {"plain": {"value": "..."}}
            desc_text = desc_text.get("plain", {}).get("value", "") or desc_text.get(
                "view", {}
            ).get("value", "")
        if desc_text and len(desc_text) > 20:
            clean = re.sub(r"<[^>]+>", "", desc_text).strip()
            if len(clean) > 150:
                clean = clean[:147] + "..."
            return f"Use when {clean.lower()}"
        space_name = space_info.get("name", "")
        if space_name and len(space_name) > 5:
            return f"Use when working with {space_name.lower()} documentation"
    return (
        f"Use when referencing {name} documentation"
        if name
        else "Use when referencing this Confluence documentation"
    )


class ConfluenceToSkillConverter(SkillConverter):
    """Convert Confluence space documentation to an AI-ready skill.

    Supports two extraction modes:

    - **API mode**: Uses the Atlassian Confluence REST API to fetch pages from
      a space, including page hierarchy, labels, and storage-format content.
      Requires ``base_url``, ``space_key``, and authentication credentials.

    - **Export mode**: Parses a Confluence HTML/XML export directory that has
      been downloaded and extracted from the Confluence admin interface.
      Requires ``export_path`` pointing to the extracted directory.

    After extraction, the converter categorises pages by their parent-child
    hierarchy, generates reference markdown files, an index, and the main
    SKILL.md manifest.

    Attributes:
        config: Configuration dictionary.
        name: Skill name used for output directory and filenames.
        base_url: Confluence instance base URL (API mode).
        space_key: Confluence space key (API mode).
        export_path: Path to exported Confluence directory (export mode).
        username: Confluence username / email for API authentication.
        token: Confluence API token or password.
        description: Skill description for SKILL.md frontmatter.
        max_pages: Maximum number of pages to fetch in API mode.
        skill_dir: Output directory for the generated skill.
        data_file: Path to the intermediate extracted JSON file.
        extracted_data: Structured extraction results dict.
    """

    SOURCE_TYPE = "confluence"

    def __init__(self, config: dict) -> None:
        """Initialize the Confluence to skill converter.

        Args:
            config: Configuration dictionary containing:
                - name (str): Skill name (required).
                - base_url (str): Confluence instance URL (API mode).
                - space_key (str): Confluence space key (API mode).
                - export_path (str): Path to export directory (export mode).
                - username (str): API username / email (optional, falls back to env).
                - token (str): API token (optional, falls back to env).
                - description (str): Skill description (optional).
                - max_pages (int): Maximum pages to fetch, default 500.
        """
        super().__init__(config)
        self.config = config
        self.name: str = config["name"]
        self.base_url: str = config.get("base_url", "")
        self.space_key: str = config.get("space_key", "")
        self.export_path: str = config.get("export_path", "")
        self.username: str = config.get("username", "")
        self.token: str = config.get("token", "")
        self.description: str = (
            config.get("description") or f"Use when referencing {self.name} documentation"
        )
        self.max_pages: int = int(config.get("max_pages", 500))

        # Output paths
        self.skill_dir = f"output/{self.name}"
        self.data_file = f"output/{self.name}_extracted.json"

        # Extracted data storage
        self.extracted_data: dict[str, Any] | None = None

    def extract(self):
        """Extract content from Confluence (SkillConverter interface)."""
        self.extract_confluence()

    # ──────────────────────────────────────────────────────────────────────
    # Extraction dispatcher
    # ──────────────────────────────────────────────────────────────────────

    def extract_confluence(self) -> bool:
        """Extract content from Confluence, dispatching to API or export mode.

        Determines the extraction mode based on the provided configuration:
        - If ``base_url`` and ``space_key`` are set, uses API mode.
        - If ``export_path`` is set, uses export mode.
        - Raises ValueError if neither mode is configured.

        After extraction, saves intermediate JSON to ``{name}_extracted.json``
        and updates the description from space metadata if not explicitly set.

        Returns:
            True on successful extraction.

        Raises:
            ValueError: If neither API nor export configuration is provided.
            RuntimeError: If API dependencies are missing or connection fails.
        """
        if self.base_url and self.space_key:
            print(f"\n  Extracting from Confluence API: {self.base_url}")
            print(f"  Space: {self.space_key}")
            raw_pages = self._extract_via_api()
        elif self.export_path:
            print(f"\n  Extracting from Confluence export: {self.export_path}")
            raw_pages = self._extract_from_export()
        else:
            raise ValueError(
                "No Confluence source configured. Provide either:\n"
                "  - --base-url and --space-key (API mode), or\n"
                "  - --export-path (export mode)"
            )

        if not raw_pages:
            logger.warning("No pages extracted from Confluence")

        # Build page hierarchy tree
        page_tree = self._extract_page_tree(raw_pages)

        # Parse each page's HTML content to structured sections
        sections: list[dict[str, Any]] = []
        total_code_blocks = 0
        total_images = 0
        section_number = 0

        for page in raw_pages:
            page_id = page.get("id", "")
            page_title = page.get("title", "Untitled")
            body_html = page.get("body", "")
            labels = page.get("labels", [])
            parent_id = page.get("parent_id", "")

            if not body_html:
                logger.debug("Skipping page with no body: %s", page_title)
                continue

            # Parse the Confluence HTML content
            parsed = self._parse_confluence_html(body_html, page_title)

            section_number += 1
            section_data: dict[str, Any] = {
                "section_number": section_number,
                "page_id": page_id,
                "heading": page_title,
                "heading_level": "h1",
                "parent_id": parent_id,
                "labels": labels,
                "text": parsed.get("text", ""),
                "headings": parsed.get("headings", []),
                "code_samples": parsed.get("code_samples", []),
                "tables": parsed.get("tables", []),
                "images": parsed.get("images", []),
                "links": parsed.get("links", []),
                "macros": parsed.get("macros", []),
            }
            sections.append(section_data)
            total_code_blocks += len(parsed.get("code_samples", []))
            total_images += len(parsed.get("images", []))

        # Collect space metadata
        space_info = raw_pages[0].get("space_info", {}) if raw_pages else {}

        # Update description from space metadata if not explicitly set
        if not self.config.get("description"):
            self.description = infer_description_from_confluence(space_info, self.name)

        # Detect programming languages in code samples
        languages_detected: dict[str, int] = {}
        for section in sections:
            for code_sample in section.get("code_samples", []):
                lang = code_sample.get("language", "")
                if lang:
                    languages_detected[lang] = languages_detected.get(lang, 0) + 1

        result_data: dict[str, Any] = {
            "source": self.base_url or self.export_path,
            "space_key": self.space_key,
            "space_info": space_info,
            "page_tree": page_tree,
            "total_sections": len(sections),
            "total_pages": len(raw_pages),
            "total_code_blocks": total_code_blocks,
            "total_images": total_images,
            "languages_detected": languages_detected,
            "pages": sections,
        }

        # Save extracted data
        os.makedirs(os.path.dirname(self.data_file) or ".", exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n  Saved extracted data to: {self.data_file}")
        self.extracted_data = result_data
        print(
            f"  Extracted {len(sections)} pages, "
            f"{total_code_blocks} code blocks, "
            f"{total_images} images"
        )
        return True

    # ──────────────────────────────────────────────────────────────────────
    # API extraction
    # ──────────────────────────────────────────────────────────────────────

    def _extract_via_api(self) -> list[dict[str, Any]]:
        """Fetch pages from a Confluence space using the REST API.

        Connects to the Confluence instance using ``atlassian-python-api``,
        retrieves all pages in the configured space (up to ``max_pages``),
        and returns them as a list of normalised page dicts.

        Authentication is resolved in priority order:
        1. Constructor arguments (username/token)
        2. Environment variables (CONFLUENCE_USERNAME / CONFLUENCE_TOKEN)

        Returns:
            List of page dicts with keys: id, title, body, parent_id, labels,
            url, space_info, version, created, modified.

        Raises:
            RuntimeError: If atlassian-python-api is not installed or
                          the connection / fetch fails.
        """
        _check_atlassian_deps()

        # Resolve authentication credentials
        username = (
            self.username
            or os.environ.get("CONFLUENCE_USERNAME", "")
            or os.environ.get("ATLASSIAN_USERNAME", "")
        )
        token = (
            self.token
            or os.environ.get("CONFLUENCE_TOKEN", "")
            or os.environ.get("ATLASSIAN_TOKEN", "")
        )

        if not username or not token:
            raise RuntimeError(
                "Confluence API authentication required.\n"
                "Provide --username and --token, or set CONFLUENCE_USERNAME "
                "and CONFLUENCE_TOKEN environment variables."
            )

        # Connect to Confluence
        try:
            confluence = Confluence(
                url=self.base_url,
                username=username,
                password=token,
                cloud=self._is_cloud_instance(),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Confluence at {self.base_url}: {e}") from e

        # Fetch space information
        space_info: dict[str, Any] = {}
        try:
            space_data = confluence.get_space(self.space_key, expand="description.plain,homepage")
            space_info = {
                "key": space_data.get("key", self.space_key),
                "name": space_data.get("name", self.space_key),
                "description": space_data.get("description", {}),
                "type": space_data.get("type", "global"),
                "homepage_id": (
                    space_data.get("homepage", {}).get("id", "")
                    if space_data.get("homepage")
                    else ""
                ),
            }
            print(f"  Space: {space_info.get('name', self.space_key)}")
        except Exception as e:
            logger.warning("Could not fetch space info: %s", e)
            space_info = {"key": self.space_key, "name": self.space_key}

        # Fetch all pages in the space, paginated
        pages: list[dict[str, Any]] = []
        start = 0
        limit = 50  # Confluence API page size
        expand_fields = "body.storage,version,ancestors,metadata.labels"

        print(f"  Fetching pages (max {self.max_pages})...")

        while len(pages) < self.max_pages:
            try:
                batch = confluence.get_all_pages_from_space(
                    self.space_key,
                    start=start,
                    limit=min(limit, self.max_pages - len(pages)),
                    expand=expand_fields,
                    content_type="page",
                )
            except Exception as e:
                logger.error("Failed to fetch pages at offset %d: %s", start, e)
                break

            if not batch:
                break

            for page_data in batch:
                page_id = str(page_data.get("id", ""))
                title = page_data.get("title", "Untitled")

                # Extract body (storage format HTML)
                body = page_data.get("body", {}).get("storage", {}).get("value", "")

                # Extract parent ID from ancestors
                ancestors = page_data.get("ancestors", [])
                parent_id = str(ancestors[-1]["id"]) if ancestors else ""

                # Extract labels
                labels_data = page_data.get("metadata", {}).get("labels", {}).get("results", [])
                labels = [lbl.get("name", "") for lbl in labels_data if lbl.get("name")]

                # Version and dates
                version_info = page_data.get("version", {})
                version_number = version_info.get("number", 1)
                created = version_info.get("when", "") if version_number == 1 else ""
                modified = version_info.get("when", "")

                # Build page URL
                page_url = f"{self.base_url}/wiki/spaces/{self.space_key}/pages/{page_id}"
                links = page_data.get("_links", {})
                if links.get("webui"):
                    page_url = f"{self.base_url}/wiki{links['webui']}"

                page_dict: dict[str, Any] = {
                    "id": page_id,
                    "title": title,
                    "body": body,
                    "parent_id": parent_id,
                    "labels": labels,
                    "url": page_url,
                    "space_info": space_info,
                    "version": version_number,
                    "created": created,
                    "modified": modified,
                }
                pages.append(page_dict)

            print(f"    Fetched {len(pages)} pages...")
            start += len(batch)

            # If we got fewer results than the limit, we've reached the end
            if len(batch) < limit:
                break

        print(f"  Total pages fetched: {len(pages)}")
        return pages

    def _is_cloud_instance(self) -> bool:
        """Detect whether the base URL points to an Atlassian Cloud instance.

        Cloud instances use ``*.atlassian.net`` domain names.

        Returns:
            True if the URL looks like an Atlassian Cloud instance.
        """
        return "atlassian.net" in self.base_url.lower()

    # ──────────────────────────────────────────────────────────────────────
    # Export extraction
    # ──────────────────────────────────────────────────────────────────────

    def _extract_from_export(self) -> list[dict[str, Any]]:
        """Parse a Confluence HTML/XML export directory into page dicts.

        Confluence exports can contain either:
        - An ``entities.xml`` file (full XML export from admin)
        - A directory of HTML files (HTML export)

        This method auto-detects the export format and delegates accordingly.
        HTML files are parsed with BeautifulSoup to extract content and metadata.

        Returns:
            List of normalised page dicts (same structure as API mode).

        Raises:
            FileNotFoundError: If the export path does not exist.
            ValueError: If no parseable content is found in the export.
        """
        export_dir = Path(self.export_path)
        if not export_dir.exists():
            raise FileNotFoundError(f"Confluence export path not found: {self.export_path}")
        if not export_dir.is_dir():
            raise ValueError(f"Export path is not a directory: {self.export_path}")

        pages: list[dict[str, Any]] = []
        space_info: dict[str, Any] = {"key": self.space_key or "EXPORT", "name": self.name}

        # Check for entities.xml (full XML export)
        entities_xml = export_dir / "entities.xml"
        if entities_xml.exists():
            pages = self._parse_entities_xml(entities_xml, space_info)
            if pages:
                print(f"  Parsed entities.xml: {len(pages)} pages")
                return pages

        # Fall back to HTML file export
        html_files = sorted(
            f for f in export_dir.rglob("*.html") if f.is_file() and f.name != "index.html"
        )

        if not html_files:
            # Also try .htm files
            html_files = sorted(
                f for f in export_dir.rglob("*.htm") if f.is_file() and f.name != "index.htm"
            )

        if not html_files:
            raise ValueError(
                f"No HTML files found in export directory: {self.export_path}\n"
                "Expected either entities.xml or HTML files from Confluence export."
            )

        print(f"  Found {len(html_files)} HTML files in export")

        # Parse index.html for page hierarchy if available
        index_file = export_dir / "index.html"
        hierarchy_map: dict[str, str] = {}  # filename -> parent filename
        if index_file.exists():
            hierarchy_map = self._parse_export_index(index_file)

        for idx, html_file in enumerate(html_files):
            if idx >= self.max_pages:
                logger.info("Reached max_pages limit (%d)", self.max_pages)
                break

            try:
                raw_html = html_file.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.warning("Could not read %s: %s", html_file, e)
                continue

            soup = BeautifulSoup(raw_html, "html.parser")

            # Extract title
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else html_file.stem

            # Find main content area (Confluence exports use specific div IDs)
            main_content = (
                soup.find("div", id="main-content")
                or soup.find("div", class_="wiki-content")
                or soup.find("div", id="content")
                or soup.find("body")
            )

            body_html = str(main_content) if main_content else ""
            file_key = html_file.stem
            parent_key = hierarchy_map.get(file_key, "")

            page_dict: dict[str, Any] = {
                "id": file_key,
                "title": title,
                "body": body_html,
                "parent_id": parent_key,
                "labels": [],
                "url": str(html_file),
                "space_info": space_info,
                "version": 1,
                "created": "",
                "modified": "",
            }
            pages.append(page_dict)

        print(f"  Parsed {len(pages)} pages from HTML export")
        return pages

    def _parse_entities_xml(
        self,
        xml_path: Path,
        space_info: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Parse Confluence entities.xml export file.

        The entities.xml file contains all page data including body content
        in Confluence storage format. This method extracts page objects and
        their parent-child relationships.

        Args:
            xml_path: Path to the entities.xml file.
            space_info: Space metadata dict to attach to each page.

        Returns:
            List of normalised page dicts.
        """
        pages: list[dict[str, Any]] = []

        try:
            # Use iterparse for memory efficiency on large exports
            import xml.etree.ElementTree as ET

            tree = ET.parse(xml_path)  # noqa: S314
            root = tree.getroot()
        except Exception as e:
            logger.warning("Failed to parse entities.xml: %s", e)
            return []

        # Find all page objects in the XML
        for obj_elem in root.iter("object"):
            obj_class = obj_elem.get("class", "")
            if obj_class != "Page":
                continue

            page_data: dict[str, str] = {}
            for prop_elem in obj_elem:
                prop_name = prop_elem.get("name", "")
                if prop_name == "title":
                    page_data["title"] = prop_elem.text or ""
                elif prop_name == "id":
                    page_data["id"] = prop_elem.text or ""
                elif prop_name == "bodyContents":
                    # Body content is nested inside a collection
                    for body_obj in prop_elem.iter("object"):
                        for body_prop in body_obj:
                            if body_prop.get("name") == "body":
                                page_data["body"] = body_prop.text or ""
                elif prop_name == "parent":
                    # Parent reference
                    parent_ref = prop_elem.find("id")
                    if parent_ref is not None and parent_ref.text:
                        page_data["parent_id"] = parent_ref.text

            if page_data.get("title") and page_data.get("id"):
                page_dict: dict[str, Any] = {
                    "id": page_data.get("id", ""),
                    "title": page_data.get("title", ""),
                    "body": page_data.get("body", ""),
                    "parent_id": page_data.get("parent_id", ""),
                    "labels": [],
                    "url": "",
                    "space_info": space_info,
                    "version": 1,
                    "created": "",
                    "modified": "",
                }
                pages.append(page_dict)

        return pages

    def _parse_export_index(self, index_path: Path) -> dict[str, str]:
        """Parse the index.html from a Confluence HTML export for hierarchy.

        The export index page contains a nested list structure representing
        the page tree. This method parses it to build a child-to-parent mapping.

        Args:
            index_path: Path to the index.html file.

        Returns:
            Dict mapping page filename stem to parent filename stem.
        """
        hierarchy: dict[str, str] = {}

        try:
            raw_html = index_path.read_text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(raw_html, "html.parser")

            # Confluence export index uses nested <ul><li><a href="..."> structure
            def _walk_list(ul_elem: Tag, parent_key: str = "") -> None:
                for li in ul_elem.find_all("li", recursive=False):
                    link = li.find("a", href=True)
                    if not link:
                        continue
                    href = link.get("href", "")
                    # Extract filename stem from href
                    page_key = Path(href).stem if href else ""
                    if page_key and parent_key:
                        hierarchy[page_key] = parent_key

                    # Recurse into nested lists
                    nested_ul = li.find("ul", recursive=False)
                    if nested_ul:
                        _walk_list(nested_ul, page_key)

            top_ul = soup.find("ul")
            if top_ul:
                _walk_list(top_ul)

        except Exception as e:
            logger.warning("Failed to parse export index: %s", e)

        return hierarchy

    # ──────────────────────────────────────────────────────────────────────
    # HTML / content parsing
    # ──────────────────────────────────────────────────────────────────────

    def _parse_confluence_html(
        self,
        html_content: str,
        page_title: str = "",
    ) -> dict[str, Any]:
        """Parse Confluence storage format HTML into structured content.

        Confluence uses a custom XHTML-based storage format with proprietary
        macro elements (``ac:structured-macro``, ``ac:rich-text-body``, etc.).
        This method:

        1. Extracts code macros and panel macros before cleaning.
        2. Cleans Confluence-specific markup (macros, boilerplate divs).
        3. Extracts sub-headings, text content, code blocks, tables, images,
           and links from the cleaned HTML.

        Args:
            html_content: Raw HTML string in Confluence storage format.
            page_title: Page title for context in logging.

        Returns:
            Dict with keys: text, headings, code_samples, tables, images,
            links, macros.
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # Step 1: Extract macros before cleaning (they contain valuable content)
        macros = self._extract_macros(soup)

        # Step 2: Clean Confluence-specific HTML
        cleaned_soup = self._clean_confluence_html(soup)

        # Step 3: Extract structured content from cleaned HTML
        text_parts: list[str] = []
        headings: list[dict[str, str]] = []
        code_samples: list[dict[str, Any]] = []
        tables: list[dict[str, Any]] = []
        images: list[dict[str, str]] = []
        links: list[dict[str, str]] = []

        # Add code samples from extracted macros
        for macro in macros:
            if macro.get("type") == "code":
                code_samples.append(
                    {
                        "code": macro.get("content", ""),
                        "language": macro.get("language", ""),
                        "title": macro.get("title", ""),
                        "quality_score": _score_code_quality(macro.get("content", "")),
                    }
                )

        # Extract headings (h1-h6)
        for heading_tag in cleaned_soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            heading_text = heading_tag.get_text(strip=True)
            if heading_text:
                headings.append(
                    {
                        "level": heading_tag.name,
                        "text": heading_text,
                    }
                )

        # Extract code blocks from <pre>/<code> elements (non-macro code)
        for pre_tag in cleaned_soup.find_all("pre"):
            code_elem = pre_tag.find("code")
            if code_elem:
                code_text = code_elem.get_text()
                lang = self._detect_language_from_classes(code_elem)
            else:
                code_text = pre_tag.get_text()
                lang = self._detect_language_from_classes(pre_tag)

            code_text = code_text.strip()
            if code_text and len(code_text) > 10:
                # Avoid duplicates from macro extraction
                is_duplicate = any(cs.get("code", "").strip() == code_text for cs in code_samples)
                if not is_duplicate:
                    code_samples.append(
                        {
                            "code": code_text,
                            "language": lang,
                            "title": "",
                            "quality_score": _score_code_quality(code_text),
                        }
                    )
            pre_tag.decompose()

        # Extract tables
        for table_tag in cleaned_soup.find_all("table"):
            table_data = self._extract_table(table_tag)
            if table_data:
                tables.append(table_data)
            table_tag.decompose()

        # Extract images
        for img_tag in cleaned_soup.find_all("img"):
            src = img_tag.get("src", "")
            alt = img_tag.get("alt", "")
            if src:
                images.append({"src": src, "alt": alt})

        # Extract links
        for a_tag in cleaned_soup.find_all("a", href=True):
            href = a_tag.get("href", "")
            link_text = a_tag.get_text(strip=True)
            if href and link_text and not href.startswith("javascript:"):
                links.append({"href": href, "text": link_text})

        # Extract remaining text content
        body_text = self._html_to_text(cleaned_soup)
        if body_text and body_text.strip():
            text_parts.append(body_text.strip())

        return {
            "text": "\n\n".join(text_parts),
            "headings": headings,
            "code_samples": code_samples,
            "tables": tables,
            "images": images,
            "links": links,
            "macros": [m for m in macros if m.get("type") != "code"],
        }

    def _extract_macros(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract Confluence macros from storage format HTML.

        Identifies and parses structured macros including:
        - **code**: Code blocks with language specification.
        - **panel** / **info** / **note** / **warning** / **tip**: Callout panels.
        - **expand**: Expandable content sections.
        - **toc**: Table of contents macro.
        - **jira**: JIRA issue references.
        - **excerpt**: Page excerpts.

        Extracts the macro content and metadata, then removes the macro
        elements from the soup to avoid double-processing.

        Args:
            soup: BeautifulSoup object containing Confluence storage format HTML.

        Returns:
            List of macro dicts with type, content, language (for code), title.
        """
        macros: list[dict[str, Any]] = []

        # Find all ac:structured-macro elements
        for macro_elem in soup.find_all("ac:structured-macro"):
            macro_name = macro_elem.get("ac:name", "") or macro_elem.get("data-macro-name", "")
            if not macro_name:
                continue

            # Extract parameters
            params: dict[str, str] = {}
            for param in macro_elem.find_all("ac:parameter"):
                param_name = param.get("ac:name", "") or param.get("name", "")
                param_value = param.get_text(strip=True)
                if param_name:
                    params[param_name] = param_value

            # Extract body content
            body_elem = macro_elem.find("ac:rich-text-body") or macro_elem.find(
                "ac:plain-text-body"
            )
            body_content = ""
            if body_elem:
                if macro_elem.find("ac:plain-text-body"):
                    body_content = body_elem.get_text()
                else:
                    body_content = body_elem.get_text(strip=True)

            macro_dict: dict[str, Any] = {
                "type": macro_name,
                "params": params,
                "content": body_content,
            }

            # Special handling for code macros
            if macro_name == "code":
                lang_raw = params.get("language", "").lower().strip()
                macro_dict["language"] = _CODE_MACRO_LANGS.get(lang_raw, lang_raw)
                macro_dict["title"] = params.get("title", "")
                macro_dict["type"] = "code"

            # Panel-type macros
            elif macro_name in ("panel", "info", "note", "warning", "tip", "excerpt"):
                macro_dict["title"] = params.get("title", "")

            macros.append(macro_dict)

            # Remove the macro element to avoid double-processing
            macro_elem.decompose()

        # Also handle legacy Confluence code blocks with class="code-macro"
        for code_div in soup.find_all("div", class_="code"):
            pre_elem = code_div.find("pre")
            if pre_elem:
                code_text = pre_elem.get_text()
                if code_text and code_text.strip():
                    macros.append(
                        {
                            "type": "code",
                            "params": {},
                            "content": code_text.strip(),
                            "language": "",
                            "title": "",
                        }
                    )
            code_div.decompose()

        return macros

    def _clean_confluence_html(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Strip Confluence-specific markup from parsed HTML.

        Removes:
        - Script and style elements.
        - HTML comments.
        - Confluence-specific macro wrapper divs (by class name).
        - Remaining ``ac:*`` and ``ri:*`` namespace elements.
        - Empty ``<div>`` and ``<span>`` containers.
        - Confluence status/date live-search elements.

        Args:
            soup: BeautifulSoup object to clean (modified in-place and returned).

        Returns:
            The cleaned BeautifulSoup object.
        """
        # Remove script, style, noscript
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # Remove HTML comments
        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            comment.extract()

        # Remove Confluence-specific boilerplate divs by class
        for css_class in _CONFLUENCE_MACRO_CLASSES:
            for elem in soup.find_all(class_=css_class):
                elem.decompose()

        # Remove remaining ac:* and ri:* namespace elements that weren't
        # captured by macro extraction (e.g. empty placeholders)
        for tag_name in list(_STORAGE_MACRO_TAGS):
            for elem in soup.find_all(tag_name):
                # Preserve text content by replacing element with its text
                text_content = elem.get_text(strip=True)
                if text_content:
                    elem.replace_with(text_content)
                else:
                    elem.decompose()

        # Remove Confluence status macros and date elements
        for elem in soup.find_all("time"):
            elem.decompose()
        for elem in soup.find_all("ac:emoticon"):
            elem.decompose()

        # Remove empty wrapper divs and spans (cleanup after macro removal)
        for tag_name in ("div", "span"):
            for elem in soup.find_all(tag_name):
                if not elem.get_text(strip=True) and not elem.find(["img", "table", "pre"]):
                    elem.decompose()

        return soup

    def _extract_page_tree(
        self,
        pages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build a hierarchical page tree from a flat list of pages.

        Constructs a tree structure based on parent_id relationships. Pages
        without a parent are placed at the root level. The tree is useful
        for categorisation and navigation.

        Args:
            pages: Flat list of page dicts with id and parent_id fields.

        Returns:
            List of tree node dicts, each with keys: id, title, children,
            depth, labels.
        """
        # Build lookup maps
        by_id: dict[str, dict[str, Any]] = {}
        for page in pages:
            page_id = page.get("id", "")
            if page_id:
                by_id[page_id] = {
                    "id": page_id,
                    "title": page.get("title", ""),
                    "children": [],
                    "depth": 0,
                    "labels": page.get("labels", []),
                }

        # Build parent-child relationships
        roots: list[dict[str, Any]] = []
        for page in pages:
            page_id = page.get("id", "")
            parent_id = page.get("parent_id", "")
            node = by_id.get(page_id)
            if not node:
                continue

            if parent_id and parent_id in by_id:
                parent_node = by_id[parent_id]
                parent_node["children"].append(node)
                node["depth"] = parent_node["depth"] + 1
            else:
                roots.append(node)

        # Sort children alphabetically at each level
        def _sort_children(node: dict[str, Any]) -> None:
            node["children"].sort(key=lambda n: n.get("title", "").lower())
            for child in node["children"]:
                _sort_children(child)

        for root in roots:
            _sort_children(root)

        roots.sort(key=lambda n: n.get("title", "").lower())
        return roots

    def _extract_table(self, table_elem: Tag) -> dict[str, Any] | None:
        """Extract an HTML table to a markdown-ready dict.

        Handles ``<thead>``/``<tbody>`` structure as well as header-less tables.
        Confluence tables often use ``<th>`` in the first row.

        Args:
            table_elem: BeautifulSoup ``<table>`` Tag.

        Returns:
            Dict with 'headers' and 'rows' lists, or None if empty.
        """
        headers: list[str] = []
        rows: list[list[str]] = []

        # Try <thead> for headers
        thead = table_elem.find("thead")
        if thead:
            header_row = thead.find("tr")
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

        # Body rows
        tbody = table_elem.find("tbody") or table_elem
        all_rows = tbody.find_all("tr")

        for row in all_rows:
            cells = row.find_all(["td", "th"])
            cell_texts = [c.get_text(strip=True) for c in cells]

            # If no thead and first row has <th> elements, use as headers
            if not headers and row.find("th") and not rows:
                headers = cell_texts
                continue

            if cell_texts and cell_texts != headers:
                rows.append(cell_texts)

        # If still no headers, promote first row
        if not headers and rows:
            headers = rows.pop(0)

        if not headers and not rows:
            return None

        return {"headers": headers, "rows": rows}

    def _detect_language_from_classes(self, elem: Tag) -> str:
        """Detect programming language from CSS classes on an element.

        Checks for common class conventions: ``language-python``,
        ``brush: java``, ``code-python``, or bare language names.

        Args:
            elem: BeautifulSoup Tag with potential language class hints.

        Returns:
            Normalised language string, or empty string if undetected.
        """
        classes = elem.get("class", [])
        if not classes:
            return ""

        prefixes = ("language-", "lang-", "code-", "highlight-", "brush:")
        for cls in classes:
            cls_lower = cls.lower().strip()
            for prefix in prefixes:
                if cls_lower.startswith(prefix):
                    lang_raw = cls_lower[len(prefix) :].strip()
                    return _CODE_MACRO_LANGS.get(lang_raw, lang_raw)

        # Check for bare language names
        known = set(_CODE_MACRO_LANGS.keys())
        for cls in classes:
            if cls.lower() in known:
                return _CODE_MACRO_LANGS.get(cls.lower(), cls.lower())

        return ""

    def _html_to_text(self, elem: Tag | BeautifulSoup) -> str:
        """Convert an HTML element to clean markdown-like text.

        Handles paragraphs, bold/italic, links, lists, blockquotes,
        inline code, headings, definition lists, and horizontal rules.

        Args:
            elem: BeautifulSoup Tag or soup to convert.

        Returns:
            Cleaned text string with basic markdown formatting.
        """
        if not hasattr(elem, "children"):
            return str(elem).strip()

        parts: list[str] = []

        for child in elem.children:
            if not hasattr(child, "name"):
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
                if child.find_parent("pre") is None:
                    code_text = child.get_text()
                    if code_text.strip():
                        parts.append(f"`{code_text.strip()}`")
            elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                level = int(tag[1])
                inner = child.get_text(strip=True)
                if inner:
                    parts.append(f"\n\n{'#' * level} {inner}\n\n")
            elif tag == "dl":
                for dt in child.find_all("dt"):
                    term = dt.get_text(strip=True)
                    dd = dt.find_next_sibling("dd")
                    definition = dd.get_text(strip=True) if dd else ""
                    parts.append(f"\n**{term}**: {definition}")
                parts.append("\n")
            elif tag == "hr":
                parts.append("\n\n---\n\n")
            else:
                inner = self._html_to_text(child)
                if inner.strip():
                    parts.append(inner)

        result = "".join(parts)
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result

    # ──────────────────────────────────────────────────────────────────────
    # Load extracted data
    # ──────────────────────────────────────────────────────────────────────

    def load_extracted_data(self, json_path: str) -> bool:
        """Load previously extracted data from a JSON file.

        Args:
            json_path: Path to the intermediate extracted JSON file.

        Returns:
            True on success.

        Raises:
            FileNotFoundError: If the JSON file does not exist.
        """
        print(f"\n  Loading extracted data from: {json_path}")
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Extracted data file not found: {json_path}")

        with open(json_path, encoding="utf-8") as f:
            self.extracted_data = json.load(f)

        total = self.extracted_data.get("total_sections", 0)
        print(f"  Loaded {total} pages")
        return True

    # ──────────────────────────────────────────────────────────────────────
    # Categorisation
    # ──────────────────────────────────────────────────────────────────────

    def categorize_content(self) -> dict[str, dict[str, Any]]:
        """Categorise pages by space / parent-page hierarchy.

        Groups pages based on their parent page relationships. Root pages
        (those without a parent) form top-level categories. Pages with
        parents are grouped under their parent's category. Deep nesting
        is flattened to two levels.

        If no hierarchy information is available, falls back to grouping
        by labels or placing all pages in a single "content" category.

        Returns:
            Dict mapping category key to dict with 'title' and 'pages' lists.
        """
        print("\n  Categorising content...")

        categorised: dict[str, dict[str, Any]] = {}
        sections = self.extracted_data.get("pages", [])
        page_tree = self.extracted_data.get("page_tree", [])

        if not sections:
            categorised["content"] = {"title": "Content", "pages": []}
            return categorised

        # Build a lookup from page_id to section
        sections_by_id: dict[str, dict[str, Any]] = {}
        for section in sections:
            page_id = section.get("page_id", "")
            if page_id:
                sections_by_id[page_id] = section

        # Strategy 1: Use page hierarchy if available
        if page_tree:
            for root_node in page_tree:
                root_id = root_node.get("id", "")
                root_title = root_node.get("title", "Untitled")
                cat_key = self._sanitize_filename(root_title)

                # Collect the root page and all its descendants
                descendant_ids = self._collect_descendant_ids(root_node)
                all_ids = [root_id] + descendant_ids

                cat_pages = [sections_by_id[pid] for pid in all_ids if pid in sections_by_id]

                if cat_pages:
                    categorised[cat_key] = {
                        "title": root_title,
                        "pages": cat_pages,
                    }

        # Strategy 2: Group by parent_id when no tree is available
        if not categorised:
            parent_groups: dict[str, list[dict[str, Any]]] = {}
            for section in sections:
                parent_id = section.get("parent_id", "")
                group_key = parent_id or "root"
                if group_key not in parent_groups:
                    parent_groups[group_key] = []
                parent_groups[group_key].append(section)

            for group_key, group_pages in parent_groups.items():
                if group_key == "root":
                    cat_title = "Root Pages"
                else:
                    # Try to find the parent page title
                    parent_section = sections_by_id.get(group_key)
                    cat_title = (
                        parent_section.get("heading", "Section")
                        if parent_section
                        else f"Section {group_key}"
                    )

                cat_key = self._sanitize_filename(cat_title)
                categorised[cat_key] = {
                    "title": cat_title,
                    "pages": group_pages,
                }

        # Strategy 3: Single category fallback
        if not categorised:
            categorised["content"] = {
                "title": "Content",
                "pages": sections,
            }

        print(f"  Created {len(categorised)} categories")
        for cat_key, cat_data in categorised.items():
            print(f"    - {cat_data['title']}: {len(cat_data['pages'])} pages")

        return categorised

    def _collect_descendant_ids(self, node: dict[str, Any]) -> list[str]:
        """Recursively collect all descendant page IDs from a tree node.

        Args:
            node: Tree node dict with 'children' list.

        Returns:
            Flat list of all descendant page IDs.
        """
        ids: list[str] = []
        for child in node.get("children", []):
            child_id = child.get("id", "")
            if child_id:
                ids.append(child_id)
            ids.extend(self._collect_descendant_ids(child))
        return ids

    # ──────────────────────────────────────────────────────────────────────
    # Skill building
    # ──────────────────────────────────────────────────────────────────────

    def build_skill(self) -> None:
        """Build the complete skill structure from extracted data.

        Creates output directories, categorises content, and generates:
        - Reference markdown files for each category.
        - A reference index file.
        - The main SKILL.md manifest.

        The output directory structure follows the standard skill layout::

            output/{name}/
                SKILL.md
                references/
                    index.md
                    {category}.md
                scripts/
                assets/
        """
        print(f"\n  Building skill: {self.name}")

        # Create directories
        os.makedirs(f"{self.skill_dir}/references", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/scripts", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/assets", exist_ok=True)

        # Categorise content
        categorised = self.categorize_content()

        # Generate reference files
        print("\n  Generating reference files...")
        section_num = 1
        total_categories = len(categorised)
        for cat_key, cat_data in categorised.items():
            self._generate_reference_file(cat_key, cat_data, section_num, total_categories)
            section_num += 1

        # Generate index
        self._generate_index(categorised)

        # Generate SKILL.md
        self._generate_skill_md(categorised)

        print(f"\n  Skill built successfully: {self.skill_dir}/")
        print(f"\n  Next step: Package with: skill-seekers package {self.skill_dir}/")

    # ──────────────────────────────────────────────────────────────────────
    # Private generators
    # ──────────────────────────────────────────────────────────────────────

    def _generate_reference_file(
        self,
        cat_key: str,
        cat_data: dict[str, Any],
        section_num: int,
        total_categories: int,
    ) -> None:
        """Generate a reference markdown file for a content category.

        Creates a markdown file containing all pages in the category, with
        headings, text content, code examples, tables, images, and links.

        Args:
            cat_key: Category key (sanitised filename stem).
            cat_data: Category dict with 'title' and 'pages' keys.
            section_num: Current section number for filename generation.
            total_categories: Total number of categories for filename logic.
        """
        sections = cat_data["pages"]
        safe_key = self._sanitize_filename(cat_data["title"])
        filename = f"{self.skill_dir}/references/{safe_key}.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {cat_data['title']}\n\n")

            for section in sections:
                sec_num = section.get("section_number", "?")
                heading = section.get("heading", "")
                labels = section.get("labels", [])

                f.write(f"---\n\n**Page {sec_num}: {heading}**\n\n")

                # Labels
                if labels:
                    label_str = ", ".join(f"`{lbl}`" for lbl in labels)
                    f.write(f"**Labels:** {label_str}\n\n")

                # Sub-headings
                for sub in section.get("headings", []):
                    sub_level = sub.get("level", "h3")
                    sub_text = sub.get("text", "")
                    if sub_text:
                        md_depth = int(sub_level[1]) + 1 if sub_level else 4
                        md_depth = min(md_depth, 6)
                        f.write(f"{'#' * md_depth} {sub_text}\n\n")

                # Text content
                if section.get("text"):
                    f.write(f"{section['text']}\n\n")

                # Code samples
                code_list = section.get("code_samples", [])
                if code_list:
                    f.write("### Code Examples\n\n")
                    for code in code_list:
                        lang = code.get("language", "")
                        title = code.get("title", "")
                        if title:
                            f.write(f"**{title}**\n\n")
                        f.write(f"```{lang}\n{code['code']}\n```\n\n")

                # Tables
                table_list = section.get("tables", [])
                if table_list:
                    for table in table_list:
                        headers = table.get("headers", [])
                        rows = table.get("rows", [])
                        if headers:
                            f.write("| " + " | ".join(str(h) for h in headers) + " |\n")
                            f.write("| " + " | ".join("---" for _ in headers) + " |\n")
                        for row in rows:
                            f.write("| " + " | ".join(str(c) for c in row) + " |\n")
                        f.write("\n")

                # Images
                image_list = section.get("images", [])
                if image_list:
                    for img in image_list:
                        alt = img.get("alt", "Image")
                        src = img.get("src", "")
                        if src:
                            f.write(f"![{alt}]({src})\n\n")

                # Links
                link_list = section.get("links", [])
                if link_list:
                    f.write("### Related Links\n\n")
                    for link in link_list[:20]:
                        f.write(f"- [{link['text']}]({link['href']})\n")
                    f.write("\n")

                # Non-code macros (panels, notes, warnings, etc.)
                macro_list = section.get("macros", [])
                if macro_list:
                    for macro in macro_list:
                        macro_type = macro.get("type", "")
                        macro_content = macro.get("content", "")
                        macro_title = macro.get("title", "")

                        if macro_type in ("info", "note", "tip"):
                            prefix = {"info": "INFO", "note": "NOTE", "tip": "TIP"}.get(
                                macro_type, "NOTE"
                            )
                            header = f"> **{prefix}**"
                            if macro_title:
                                header += f": {macro_title}"
                            f.write(f"{header}\n")
                            for line in macro_content.split("\n"):
                                f.write(f"> {line}\n")
                            f.write("\n")
                        elif macro_type == "warning":
                            header = "> **WARNING**"
                            if macro_title:
                                header += f": {macro_title}"
                            f.write(f"{header}\n")
                            for line in macro_content.split("\n"):
                                f.write(f"> {line}\n")
                            f.write("\n")
                        elif macro_type == "panel":
                            if macro_title:
                                f.write(f"**{macro_title}**\n\n")
                            if macro_content:
                                f.write(f"{macro_content}\n\n")
                        elif macro_type == "expand":
                            expand_title = macro_title or "Details"
                            f.write(f"<details>\n<summary>{expand_title}</summary>\n\n")
                            f.write(f"{macro_content}\n\n")
                            f.write("</details>\n\n")
                        elif macro_content:
                            f.write(f"{macro_content}\n\n")

                f.write("---\n\n")

        print(f"    Generated: {filename}")

    def _generate_index(self, categorised: dict[str, dict[str, Any]]) -> None:
        """Generate the reference index file.

        Creates an ``index.md`` listing all categories with links, page counts,
        and overall statistics about the extracted content.

        Args:
            categorised: Dict of category_key -> category data.
        """
        filename = f"{self.skill_dir}/references/index.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {self.name.title()} Confluence Reference\n\n")

            space_info = self.extracted_data.get("space_info", {})
            if space_info.get("name"):
                f.write(f"**Space:** {space_info['name']}")
                if space_info.get("key"):
                    f.write(f" ({space_info['key']})")
                f.write("\n\n")

            f.write("## Categories\n\n")

            for cat_key, cat_data in categorised.items():
                safe_name = self._sanitize_filename(cat_data["title"])
                page_count = len(cat_data["pages"])
                f.write(f"- [{cat_data['title']}]({safe_name}.md) ({page_count} pages)\n")

            f.write("\n## Statistics\n\n")
            f.write(f"- Total pages: {self.extracted_data.get('total_sections', 0)}\n")
            f.write(f"- Code blocks: {self.extracted_data.get('total_code_blocks', 0)}\n")
            f.write(f"- Images: {self.extracted_data.get('total_images', 0)}\n")

            langs = self.extracted_data.get("languages_detected", {})
            if langs:
                f.write(f"- Programming languages: {len(langs)}\n\n")
                f.write("**Language Breakdown:**\n\n")
                for lang, count in sorted(langs.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- {lang}: {count} examples\n")

            # Page tree structure
            page_tree = self.extracted_data.get("page_tree", [])
            if page_tree:
                f.write("\n## Page Tree\n\n")
                f.write("```\n")
                self._write_tree_structure(f, page_tree, indent=0)
                f.write("```\n")

        print(f"    Generated: {filename}")

    def _write_tree_structure(
        self,
        f: Any,
        nodes: list[dict[str, Any]],
        indent: int = 0,
    ) -> None:
        """Write a page tree structure to a file in ASCII tree format.

        Args:
            f: File handle to write to.
            nodes: List of tree node dicts with 'title' and 'children'.
            indent: Current indentation level.
        """
        for node in nodes:
            prefix = "  " * indent
            title = node.get("title", "Untitled")
            f.write(f"{prefix}- {title}\n")
            children = node.get("children", [])
            if children:
                self._write_tree_structure(f, children, indent + 1)

    def _generate_skill_md(self, categorised: dict[str, dict[str, Any]]) -> None:
        """Generate the main SKILL.md file.

        Creates a comprehensive skill manifest with:
        - YAML frontmatter (name, description).
        - Space information and metadata.
        - Usage guidance ("When to Use This Skill").
        - Content overview with category listing.
        - Key topics extracted from page headings.
        - Code examples (top quality samples).
        - Documentation statistics.
        - Navigation links to reference files.

        Args:
            categorised: Dict of category_key -> category data.
        """
        filename = f"{self.skill_dir}/SKILL.md"
        space_info = self.extracted_data.get("space_info", {})

        # Skill name for frontmatter (lowercase, hyphens, max 64 chars)
        skill_name = self.name.lower().replace("_", "-").replace(" ", "-")[:64]
        desc = self.description[:1024] if len(self.description) > 1024 else self.description

        with open(filename, "w", encoding="utf-8") as f:
            # YAML frontmatter
            f.write("---\n")
            f.write(f"name: {skill_name}\n")
            f.write(f"description: {desc}\n")
            f.write("---\n\n")

            # Header
            space_name = space_info.get("name", self.name.title())
            f.write(f"# {space_name} Documentation Skill\n\n")
            f.write(f"{self.description}\n\n")

            # Space metadata
            if space_info.get("key"):
                f.write("## Space Information\n\n")
                f.write(f"**Space:** {space_info.get('name', 'N/A')}\n")
                f.write(f"**Key:** {space_info.get('key', 'N/A')}\n")
                source = self.extracted_data.get("source", "")
                if source:
                    f.write(f"**Source:** {source}\n")
                f.write(f"**Pages:** {self.extracted_data.get('total_pages', 0)}\n\n")

            # When to Use
            f.write("## When to Use This Skill\n\n")
            f.write("Use this skill when you need to:\n")
            f.write(f"- Understand {space_name} concepts and architecture\n")
            f.write("- Look up API references and technical specifications\n")
            f.write("- Find code examples and implementation patterns\n")
            f.write("- Review processes, guidelines, and best practices\n")
            f.write("- Navigate the documentation structure and find related pages\n\n")

            # Content overview
            total_pages = self.extracted_data.get("total_sections", 0)
            f.write("## Content Overview\n\n")
            f.write(f"**Total Pages:** {total_pages}\n\n")
            f.write("**Categories:**\n\n")
            for cat_key, cat_data in categorised.items():
                page_count = len(cat_data["pages"])
                f.write(f"- **{cat_data['title']}**: {page_count} pages\n")
            f.write("\n")

            # Key topics from headings
            f.write(self._format_key_topics())

            # Code examples (top quality)
            all_code: list[dict[str, Any]] = []
            for section in self.extracted_data.get("pages", []):
                for code in section.get("code_samples", []):
                    code_copy = dict(code)
                    code_copy["source_page"] = section.get("heading", "")
                    all_code.append(code_copy)

            all_code.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
            top_code = all_code[:10]

            if top_code:
                f.write("## Code Examples\n\n")
                f.write("*Top code examples from the documentation*\n\n")

                by_lang: dict[str, list[dict[str, Any]]] = {}
                for code in top_code:
                    lang = code.get("language", "") or "unknown"
                    by_lang.setdefault(lang, []).append(code)

                for lang in sorted(by_lang.keys()):
                    examples = by_lang[lang]
                    lang_display = lang.title() if lang != "unknown" else "Other"
                    f.write(f"### {lang_display} ({len(examples)} examples)\n\n")
                    for i, code in enumerate(examples[:3], 1):
                        quality = code.get("quality_score", 0)
                        source = code.get("source_page", "")
                        title = code.get("title", "")
                        code_text = code.get("code", "")

                        header_parts = [f"**Example {i}**"]
                        if title:
                            header_parts.append(f"({title})")
                        if source:
                            header_parts.append(f"from *{source}*")
                        header_parts.append(f"[Quality: {quality:.1f}/10]")
                        f.write(" ".join(header_parts) + ":\n\n")

                        f.write(f"```{lang}\n")
                        if len(code_text) <= 500:
                            f.write(code_text)
                        else:
                            f.write(code_text[:500] + "\n...")
                        f.write("\n```\n\n")

            # Statistics
            f.write("## Documentation Statistics\n\n")
            f.write(f"- **Total Pages**: {total_pages}\n")
            f.write(f"- **Code Blocks**: {self.extracted_data.get('total_code_blocks', 0)}\n")
            f.write(f"- **Images**: {self.extracted_data.get('total_images', 0)}\n")
            f.write(f"- **Categories**: {len(categorised)}\n")

            langs = self.extracted_data.get("languages_detected", {})
            if langs:
                f.write(f"- **Programming Languages**: {len(langs)}\n\n")
                f.write("**Language Breakdown:**\n\n")
                for lang, count in sorted(langs.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- {lang}: {count} examples\n")
                f.write("\n")
            else:
                f.write("\n")

            # Navigation
            f.write("## Navigation\n\n")
            f.write("**Reference Files:**\n\n")
            for cat_key, cat_data in categorised.items():
                safe_name = self._sanitize_filename(cat_data["title"])
                f.write(f"- `references/{safe_name}.md` - {cat_data['title']}\n")
            f.write("\n")
            f.write("See `references/index.md` for complete documentation structure.\n\n")

            # Footer
            f.write("---\n\n")
            f.write("**Generated by Skill Seekers** | Confluence Documentation Scraper\n")

        with open(filename, encoding="utf-8") as f:
            line_count = len(f.read().split("\n"))
        print(f"    Generated: {filename} ({line_count} lines)")

    def _format_key_topics(self) -> str:
        """Extract key topics from page headings across all sections.

        Collects page titles and sub-headings to identify the main topics
        covered in the documentation.

        Returns:
            Formatted markdown string with key topics section.
        """
        page_titles: list[str] = []
        sub_headings: list[str] = []

        for section in self.extracted_data.get("pages", []):
            heading = section.get("heading", "").strip()
            if heading and len(heading) > 3:
                page_titles.append(heading)

            for sub in section.get("headings", []):
                text = sub.get("text", "").strip()
                level = sub.get("level", "h3")
                if text and len(text) > 3 and level in ("h2", "h3"):
                    sub_headings.append(text)

        if not page_titles and not sub_headings:
            return ""

        content = "## Key Topics\n\n"
        content += "*Main topics covered in this documentation*\n\n"

        if page_titles:
            content += "**Pages:**\n\n"
            for title in page_titles[:15]:
                content += f"- {title}\n"
            if len(page_titles) > 15:
                content += f"- *...and {len(page_titles) - 15} more*\n"
            content += "\n"

        if sub_headings:
            # Deduplicate and show top subtopics
            unique_subs = list(dict.fromkeys(sub_headings))
            content += "**Subtopics:**\n\n"
            for heading in unique_subs[:20]:
                content += f"- {heading}\n"
            if len(unique_subs) > 20:
                content += f"- *...and {len(unique_subs) - 20} more*\n"
            content += "\n"

        return content

    # ──────────────────────────────────────────────────────────────────────
    # Utility helpers
    # ──────────────────────────────────────────────────────────────────────

    def _sanitize_filename(self, name: str) -> str:
        """Convert a string to a safe filename.

        Removes special characters, converts spaces and hyphens to underscores,
        and lowercases the result.

        Args:
            name: Raw string to sanitise.

        Returns:
            Filesystem-safe filename string.
        """
        safe = re.sub(r"[^\w\s-]", "", name.lower())
        safe = re.sub(r"[-\s]+", "_", safe)
        return safe[:100]  # Limit filename length


# ──────────────────────────────────────────────────────────────────────────────
# Module-level helpers
# ──────────────────────────────────────────────────────────────────────────────


def _score_code_quality(code: str) -> float:
    """Simple quality heuristic for code blocks (0-10 scale).

    Scores based on line count, presence of definitions, imports,
    indentation, and operator usage. Short snippets are penalised.

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

    # Very short snippets get penalised
    if len(code) < 30:
        score -= 2.0

    return min(10.0, max(0.0, score))
