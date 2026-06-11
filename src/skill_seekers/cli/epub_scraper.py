#!/usr/bin/env python3
"""
EPUB Documentation to Skill Converter

Converts EPUB e-books into skills.
Uses ebooklib for EPUB parsing, BeautifulSoup for XHTML content extraction.

Usage:
    skill-seekers epub --epub book.epub --name myskill
    skill-seekers epub --from-json book_extracted.json
"""

import json
import logging
import os

# Optional dependency guard
try:
    import ebooklib
    from ebooklib import epub

    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False

# BeautifulSoup is a core dependency (always available)
from bs4 import BeautifulSoup, Comment

from .document_skill_builder import DocumentSkillBuilder
from skill_seekers.cli.scraper_utils import score_code_quality as _score_code_quality
from skill_seekers.cli.scraper_utils import extract_table_from_html as _extract_table_from_html
from skill_seekers.cli.scraper_utils import parse_leading_int as _parse_leading_int

logger = logging.getLogger(__name__)


def _check_epub_deps():
    """Raise RuntimeError if ebooklib is not installed."""
    if not EPUB_AVAILABLE:
        raise RuntimeError(
            "ebooklib is required for EPUB support.\n"
            'Install with: pip install "skill-seekers[epub]"\n'
            "Or: pip install ebooklib"
        )


def infer_description_from_epub(metadata: dict | None = None, name: str = "") -> str:
    """Infer skill description from EPUB metadata.

    Args:
        metadata: EPUB Dublin Core metadata dict
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


class EpubToSkillConverter(DocumentSkillBuilder):
    """Convert EPUB e-book to AI skill.

    Build side (categorize/reference/index/SKILL.md) comes from
    DocumentSkillBuilder; this class owns EPUB extraction only.
    """

    SOURCE_TYPE = "epub"
    SOURCE_PATH_ATTR = "epub_path"
    SOURCE_LABEL = "EPUB"
    FOOTER_LABEL = "EPUB Scraper"
    SKILL_MD_METADATA_FIELDS = (
        ("title", "Title"),
        ("author", "Author"),
        ("language", "Language"),
        ("publisher", "Publisher"),
        ("date", "Date"),
    )
    INDEX_METADATA_FIELDS = (("author", "Author"), ("date", "Date"))

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.name = config["name"]
        self.epub_path = config.get("epub_path", "")
        self.description = (
            config.get("description") or f"Use when referencing {self.name} documentation"
        )

        # Paths
        # skill_dir is resolved once in SkillConverter.__init__
        self.data_file = self.data_file_for()

        # Categories config
        self.categories = config.get("categories", {})

        # Extracted data
        self.extracted_data = None

    def extract(self):
        """SkillConverter interface — delegates to extract_epub()."""
        return self.extract_epub()

    def extract_epub(self):
        """Extract content from EPUB file.

        Workflow:
        1. Check dependencies (ebooklib)
        2. Detect DRM via encryption.xml (fail fast)
        3. Read EPUB via ebooklib with ignore_ncx=True (EPUB 3 TOC bug workaround)
        4. Extract Dublin Core metadata
        5. Iterate spine items in reading order
        6. For each ITEM_DOCUMENT: parse XHTML with BeautifulSoup
        7. Split by h1/h2 heading boundaries into sections
        8. Extract code blocks from <pre>/<code> elements
        9. Extract images from EpubImage items
        10. Detect code languages via LanguageDetector
        11. Save intermediate JSON to {name}_extracted.json

        Returns True on success.
        Raises RuntimeError for DRM-protected files.
        Raises FileNotFoundError for missing files.
        Raises ValueError for invalid EPUB files.
        """
        _check_epub_deps()

        from skill_seekers.cli.language_detector import LanguageDetector

        print(f"\n🔍 Extracting from EPUB: {self.epub_path}")

        if not os.path.exists(self.epub_path):
            raise FileNotFoundError(f"EPUB file not found: {self.epub_path}")

        if not os.path.isfile(self.epub_path):
            raise ValueError(f"Path is not a file: {self.epub_path}")

        if not self.epub_path.lower().endswith(".epub"):
            raise ValueError(f"Not an EPUB file (expected .epub): {self.epub_path}")

        # Read EPUB with ignore_ncx=True to work around EPUB 3 TOC bug
        try:
            book = epub.read_epub(self.epub_path, options={"ignore_ncx": True})
        except Exception as e:
            raise ValueError(f"Failed to read EPUB file: {e}") from e

        # DRM detection (fail fast)
        if self._detect_drm(book):
            raise RuntimeError(
                f"EPUB file appears to be DRM-protected: {self.epub_path}\n"
                "Skill Seekers cannot process DRM-protected files.\n"
                "Please use a DRM-free version of the e-book."
            )

        # Extract Dublin Core metadata
        metadata = self._extract_metadata(book)

        print(f"   Title: {metadata.get('title', 'Unknown')}")
        print(f"   Author: {metadata.get('author', 'Unknown')}")
        print(f"   Language: {metadata.get('language', 'Unknown')}")

        # Update description from metadata if not set explicitly
        if not self.config.get("description"):
            self.description = infer_description_from_epub(metadata, self.name)

        # Extract content from spine items
        sections = self._extract_spine_content(book)

        spine_count = sum(1 for _, _ in book.spine)
        print(f"   Chapters: {spine_count} (spine items)")

        # If no sections were created, create one default section
        if not sections:
            logger.warning("No sections extracted from EPUB")

        # Extract images
        images_extracted = self._extract_images(book)

        # Detect languages for code samples
        detector = LanguageDetector(min_confidence=0.15)
        languages_detected: dict[str, int] = {}
        total_code_blocks = 0

        for section in sections:
            for code_sample in section.get("code_samples", []):
                lang = code_sample.get("language", "")
                if lang:
                    languages_detected[lang] = languages_detected.get(lang, 0) + 1
                total_code_blocks += 1

        # Detect languages for samples without language
        for section in sections:
            for code_sample in section.get("code_samples", []):
                if not code_sample.get("language"):
                    code = code_sample.get("code", "")
                    if code:
                        lang, confidence = detector.detect_from_code(code)
                        if lang and confidence >= 0.3:
                            code_sample["language"] = lang
                            languages_detected[lang] = languages_detected.get(lang, 0) + 1

        result_data = {
            "source_file": self.epub_path,
            "metadata": metadata,
            "total_sections": len(sections),
            "total_code_blocks": total_code_blocks,
            "total_images": images_extracted,
            "languages_detected": languages_detected,
            "pages": sections,  # "pages" key for pipeline compatibility
        }

        # Save extracted data
        os.makedirs(os.path.dirname(self.data_file) or ".", exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n💾 Saved extracted data to: {self.data_file}")
        self.extracted_data = result_data
        print(
            f"✅ Extracted {len(sections)} sections, "
            f"{total_code_blocks} code blocks, "
            f"{images_extracted} images"
        )
        return True

    def _detect_drm(self, book) -> bool:
        """Detect DRM by checking for encryption.xml with non-font-obfuscation entries.

        Per W3C EPUB 3.3 spec: encryption.xml is present when resources are encrypted.
        Font obfuscation (IDPF algorithm http://www.idpf.org/2008/embedding or
        Adobe algorithm http://ns.adobe.com/pdf/enc#RC) is NOT DRM.

        Actual DRM uses algorithms like:
        - Adobe ADEPT: http://ns.adobe.com/adept namespace
        - Apple FairPlay: http://itunes.apple.com/dataenc
        - Readium LCP: http://readium.org/2014/01/lcp
        """
        # Font obfuscation URIs — these are NOT DRM
        font_obfuscation_uris = {
            "http://www.idpf.org/2008/embedding",
            "http://ns.adobe.com/pdf/enc#RC",
        }

        # Known DRM namespace patterns
        drm_patterns = [
            "http://ns.adobe.com/adept",
            "http://itunes.apple.com/dataenc",
            "http://readium.org/2014/01/lcp",
        ]

        try:
            # Look for META-INF/encryption.xml in the EPUB items
            for item in book.get_items():
                if hasattr(item, "file_name") and item.file_name == "META-INF/encryption.xml":
                    content = item.get_content()
                    if isinstance(content, bytes):
                        content = content.decode("utf-8", errors="ignore")

                    # Check for DRM namespace patterns
                    for pattern in drm_patterns:
                        if pattern in content:
                            return True

                    # Check if there are encryption entries that are NOT font obfuscation
                    soup = BeautifulSoup(content, "html.parser")
                    enc_methods = soup.find_all("encryptionmethod") or soup.find_all(
                        "EncryptionMethod"
                    )
                    for method in enc_methods:
                        algorithm = method.get("Algorithm", method.get("algorithm", ""))
                        if algorithm and algorithm not in font_obfuscation_uris:
                            return True
        except Exception:
            # If we can't check for DRM, proceed anyway
            logger.debug("Could not check for DRM, proceeding with extraction")

        return False

    def _extract_metadata(self, book) -> dict:
        """Extract Dublin Core metadata from EPUB.

        Per W3C EPUB 3.3 spec: required elements are dc:identifier, dc:title, dc:language.
        Optional: dc:creator, dc:contributor, dc:date, dc:description, dc:publisher,
        dc:subject, dc:rights, dc:type, dc:coverage, dc:source, dc:relation, dc:format.

        ebooklib API: book.get_metadata('DC', key) returns list of (value, attrs) tuples.
        """

        def _get_one(key):
            data = book.get_metadata("DC", key)
            return data[0][0] if data else None

        def _get_list(key):
            data = book.get_metadata("DC", key)
            return [x[0] for x in data] if data else []

        return {
            "title": _get_one("title") or "Untitled",
            "author": ", ".join(_get_list("creator")) or None,
            "language": _get_one("language") or "en",
            "publisher": _get_one("publisher"),
            "date": _get_one("date"),
            "description": _get_one("description"),
            "subject": ", ".join(_get_list("subject")) or None,
            "rights": _get_one("rights"),
            "identifier": _get_one("identifier"),
        }

    def _extract_spine_content(self, book) -> list[dict]:
        """Extract content from spine items in reading order.

        Per W3C EPUB 3.3 spec: spine defines ordered list of content documents.
        Linear="yes" (default) items form the primary reading order.
        Linear="no" items are auxiliary (footnotes, glossary).

        Parse with BeautifulSoup, split by h1/h2 heading boundaries.
        """
        sections = []
        section_number = 0

        for item_id, linear in book.spine:
            item = book.get_item_with_id(item_id)
            if not item or item.get_type() != ebooklib.ITEM_DOCUMENT:
                continue

            try:
                content = item.get_content()
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="ignore")
            except Exception:
                logger.debug(f"Could not read spine item {item_id}, skipping")
                continue

            soup = BeautifulSoup(content, "html.parser")

            # Remove scripts, styles, comments
            for tag in soup(["script", "style"]):
                tag.decompose()
            for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
                comment.extract()

            body = soup.find("body")
            if not body:
                # Some EPUBs have content directly without a body tag
                body = soup

            # Split by h1/h2 heading boundaries
            current_heading = None
            current_heading_level = None
            current_elements = []

            for elem in body.children:
                if not hasattr(elem, "name") or elem.name is None:
                    continue

                if elem.name in ("h1", "h2"):
                    # Flush previous section
                    if current_heading is not None or current_elements:
                        section_number += 1
                        section = _build_section(
                            section_number,
                            current_heading,
                            current_heading_level,
                            current_elements,
                        )
                        sections.append(section)
                    current_heading = elem.get_text(strip=True)
                    current_heading_level = elem.name
                    current_elements = []
                else:
                    current_elements.append(elem)

            # Flush last section
            if current_heading is not None or current_elements:
                section_number += 1
                section = _build_section(
                    section_number,
                    current_heading,
                    current_heading_level,
                    current_elements,
                )
                sections.append(section)

        return sections

    def _extract_images(self, book) -> int:
        """Extract images from EPUB manifest.

        Per W3C EPUB 3.3 spec: core image media types are
        image/gif, image/jpeg, image/png, image/svg+xml, image/webp.

        Returns count of images found (images are stored in extracted_data sections).
        """
        image_count = 0
        seen_ids: set[int] = set()  # Track items already counted to avoid duplicates
        try:
            for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                image_count += 1
                seen_ids.add(id(item))
        except Exception:
            logger.debug("Could not enumerate images in EPUB")

        # Also count SVG items not already included in ITEM_IMAGE
        try:
            for item in book.get_items():
                if (
                    id(item) not in seen_ids
                    and hasattr(item, "media_type")
                    and item.media_type == "image/svg+xml"
                ):
                    image_count += 1
        except Exception:
            logger.debug("Could not enumerate SVG images in EPUB")

        return image_count


# ---------------------------------------------------------------------------
# XHTML-to-sections helper (module-level for clarity)
# ---------------------------------------------------------------------------


def _build_section(
    section_number: int,
    heading: str | None,
    heading_level: str | None,
    elements: list,
) -> dict:
    """Build a section dict from a list of BeautifulSoup elements.

    Args:
        section_number: 1-based section index
        heading: Heading text (or None for preamble)
        heading_level: 'h1', 'h2', etc.
        elements: List of BeautifulSoup Tag objects belonging to this section

    Returns:
        Section dict compatible with the intermediate JSON format
    """
    text_parts = []
    code_samples = []
    tables = []
    sub_headings = []
    images = []

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

        # Code blocks
        if tag == "pre" or (tag == "code" and elem.find_parent("pre") is None):
            code_elem = elem.find("code") if tag == "pre" else elem
            code_text = code_elem.get_text() if code_elem else elem.get_text()

            code_text = code_text.strip()
            if code_text:
                # Try to detect language from class attribute
                classes = (code_elem or elem).get("class", [])
                lang = ""
                for cls in classes:
                    if cls.startswith("language-") or cls.startswith("lang-"):
                        lang = cls.split("-", 1)[1]
                        break
                    # Also check for "code-{lang}" pattern
                    if cls.startswith("code-"):
                        lang = cls.split("-", 1)[1]
                        break

                quality_score = _score_code_quality(code_text)
                code_samples.append(
                    {"code": code_text, "language": lang, "quality_score": quality_score}
                )
            continue

        # Tables
        if tag == "table":
            table_data = _extract_table_from_html(elem)
            if table_data:
                tables.append(table_data)
            continue

        # Images
        if tag == "img":
            src = elem.get("src", "")
            if src:
                images.append(
                    {
                        "index": len(images),
                        "data": b"",  # EPUB images handled separately via manifest
                        "width": _parse_leading_int(elem.get("width")),
                        "height": _parse_leading_int(elem.get("height")),
                    }
                )
            continue

        # Regular text/paragraph content
        text = elem.get_text(separator=" ", strip=True)
        if text:
            text_parts.append(text)

    return {
        "section_number": section_number,
        "heading": heading or "",
        "heading_level": heading_level or "h1",
        "text": "\n\n".join(text_parts),
        "headings": sub_headings,
        "code_samples": code_samples,
        "tables": tables,
        "images": images,
    }
