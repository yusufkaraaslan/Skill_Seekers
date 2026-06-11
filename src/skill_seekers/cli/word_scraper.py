#!/usr/bin/env python3
"""
Word Document (.docx) to AI Skill Converter (Task B2)

Converts Word documents into AI skills.
Uses mammoth for HTML conversion and python-docx for metadata/tables.

Usage:
    python3 word_scraper.py --docx document.docx --name myskill
    python3 word_scraper.py --from-json document_extracted.json
"""

import json
import logging
import os
import re
from pathlib import Path

# Optional dependency guard
try:
    import mammoth
    import docx as python_docx

    WORD_AVAILABLE = True
except ImportError:
    WORD_AVAILABLE = False

from .document_skill_builder import DocumentSkillBuilder
from skill_seekers.cli.scraper_utils import score_code_quality as _score_code_quality
from skill_seekers.cli.scraper_utils import extract_table_from_html as _extract_table_from_html
from skill_seekers.cli.scraper_utils import parse_leading_int as _parse_leading_int

logger = logging.getLogger(__name__)


def _check_word_deps():
    """Raise RuntimeError if mammoth/python-docx are not installed."""
    if not WORD_AVAILABLE:
        raise RuntimeError(
            "mammoth and python-docx are required for Word document support.\n"
            'Install with: pip install "skill-seekers[docx]"\n'
            "Or: pip install mammoth python-docx"
        )


def infer_description_from_word(metadata: dict = None, name: str = "") -> str:
    """Infer skill description from Word document metadata or name.

    Args:
        metadata: Document metadata dict with title, subject, etc.
        name: Skill name for fallback

    Returns:
        Description string suitable for "Use when..." format
    """
    if metadata:
        # Try subject field first
        if metadata.get("subject"):
            desc = str(metadata["subject"]).strip()
            if len(desc) > 20:
                if len(desc) > 150:
                    desc = desc[:147] + "..."
                return f"Use when {desc.lower()}"

        # Try title if meaningful
        if metadata.get("title"):
            title = str(metadata["title"]).strip()
            if len(title) > 10 and not title.lower().endswith(".docx"):
                return f"Use when working with {title.lower()}"

    return (
        f"Use when referencing {name} documentation"
        if name
        else "Use when referencing this documentation"
    )


class WordToSkillConverter(DocumentSkillBuilder):
    """Convert Word document (.docx) to AI skill.

    Build side (categorize/reference/index/SKILL.md) comes from
    DocumentSkillBuilder; this class owns DOCX extraction only.
    """

    SOURCE_TYPE = "word"
    SOURCE_PATH_ATTR = "docx_path"
    SOURCE_LABEL = "Word"
    FOOTER_LABEL = "Word Document Scraper"
    SKILL_MD_METADATA_FIELDS = (
        ("title", "Title"),
        ("author", "Author"),
        ("created", "Created"),
        ("modified", "Modified"),
    )
    INDEX_METADATA_FIELDS = (("author", "Author"), ("created", "Created"))

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.name = config["name"]
        self.docx_path = config.get("docx_path", "")
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
        """SkillConverter interface — delegates to extract_docx()."""
        return self.extract_docx()

    def extract_docx(self):
        """Extract content from Word document using mammoth + python-docx.

        - mammoth converts body content to HTML (leverages Word paragraph styles)
        - python-docx provides metadata and fine-grained table access
        - BeautifulSoup parses the HTML and splits by h1/h2 heading boundaries
        - LanguageDetector identifies code language in <code> blocks
        """
        _check_word_deps()

        from bs4 import BeautifulSoup
        from skill_seekers.cli.language_detector import LanguageDetector

        print(f"\n🔍 Extracting from Word document: {self.docx_path}")

        if not os.path.exists(self.docx_path):
            raise FileNotFoundError(f"Word document not found: {self.docx_path}")

        if not self.docx_path.lower().endswith(".docx"):
            raise ValueError(f"Not a Word document (expected .docx): {self.docx_path}")

        # --- Extract metadata via python-docx ---
        doc = python_docx.Document(self.docx_path)
        core_props = doc.core_properties
        metadata = {
            "title": core_props.title or "",
            "author": core_props.author or "",
            "created": str(core_props.created) if core_props.created else "",
            "modified": str(core_props.modified) if core_props.modified else "",
            "subject": core_props.subject or "",
        }

        # Update description from metadata if not set explicitly
        if not self.config.get("description"):
            self.description = infer_description_from_word(metadata, self.name)

        # --- Convert body to HTML with mammoth ---
        with open(self.docx_path, "rb") as f:
            result = mammoth.convert_to_html(f)

        html_content = result.value

        # --- Parse HTML with BeautifulSoup ---
        soup = BeautifulSoup(html_content, "html.parser")

        # --- Split by h1/h2 heading boundaries into sections ---
        sections = []
        current_heading = None
        current_heading_level = None
        current_elements = []
        section_number = 0

        def _flush_section():
            nonlocal section_number
            if current_heading is not None or current_elements:
                section_number += 1
                section = _build_section(
                    section_number,
                    current_heading,
                    current_heading_level,
                    current_elements,
                    doc,
                )
                sections.append(section)

        for elem in soup.children:
            if not hasattr(elem, "name") or elem.name is None:
                continue

            if elem.name in ("h1", "h2"):
                # Flush previous section
                _flush_section()
                current_heading = elem.get_text(strip=True)
                current_heading_level = elem.name
                current_elements = []
            else:
                current_elements.append(elem)

        # Flush last section
        _flush_section()

        # If no sections were created (no headings), create one default section
        if not sections:
            section_number = 1
            all_elements = [e for e in soup.children if hasattr(e, "name") and e.name]
            section = _build_section(
                1,
                Path(self.docx_path).stem,
                "h1",
                all_elements,
                doc,
            )
            sections = [section]

        # --- Collect language statistics ---
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
            "source_file": self.docx_path,
            "metadata": metadata,
            "total_sections": len(sections),
            "total_code_blocks": total_code_blocks,
            "total_images": sum(len(s.get("images", [])) for s in sections),
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
            f"{result_data['total_images']} images"
        )
        return True


# ---------------------------------------------------------------------------
# HTML-to-sections helper (module-level for clarity)
# ---------------------------------------------------------------------------


def _build_section(
    section_number: int,
    heading: str | None,
    heading_level: str | None,
    elements: list,
    doc,  # noqa: ARG001
) -> dict:
    """Build a section dict from a list of BeautifulSoup elements.

    Args:
        section_number: 1-based section index
        heading: Heading text (or None for preamble)
        heading_level: 'h1', 'h2', etc.
        elements: List of BeautifulSoup Tag objects belonging to this section
        doc: python-docx Document (used for table cross-reference, not currently used)

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
            # mammoth embeds images as data URIs; extract if present
            src = elem.get("src", "")
            if src.startswith("data:"):
                import base64

                try:
                    header, b64data = src.split(",", 1)
                    img_bytes = base64.b64decode(b64data)
                    images.append(
                        {
                            "index": len(images),
                            "data": img_bytes,
                            "width": _parse_leading_int(elem.get("width")),
                            "height": _parse_leading_int(elem.get("height")),
                        }
                    )
                except Exception:
                    pass
            continue

        # Detect code in <p> elements that contain <br> tags (multi-line content)
        # Mammoth renders monospace/Courier paragraphs as <p> with <br> — not <pre>
        if tag == "p" and elem.find("br"):
            raw_text = elem.get_text(separator="\n").strip()
            # Exclude bullet-point / prose lists (•, *, -)
            if raw_text and not re.search(r"^[•\-\*]\s", raw_text, re.MULTILINE):
                quality_score = _score_code_quality(raw_text)
                if quality_score >= 5.5:
                    code_samples.append(
                        {"code": raw_text, "language": "", "quality_score": quality_score}
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
