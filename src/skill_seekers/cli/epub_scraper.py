#!/usr/bin/env python3
"""
EPUB Documentation to Skill Converter

Converts EPUB e-books into skills.
Uses ebooklib for EPUB parsing, BeautifulSoup for XHTML content extraction.

Usage:
    skill-seekers epub --epub book.epub --name myskill
    skill-seekers epub --from-json book_extracted.json
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

# Optional dependency guard
try:
    import ebooklib
    from ebooklib import epub

    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False

# BeautifulSoup is a core dependency (always available)
from bs4 import BeautifulSoup, Comment

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


class EpubToSkillConverter:
    """Convert EPUB e-book to Claude skill."""

    def __init__(self, config):
        self.config = config
        self.name = config["name"]
        self.epub_path = config.get("epub_path", "")
        self.description = (
            config.get("description") or f"Use when referencing {self.name} documentation"
        )

        # Paths
        self.skill_dir = f"output/{self.name}"
        self.data_file = f"output/{self.name}_extracted.json"

        # Categories config
        self.categories = config.get("categories", {})

        # Extracted data
        self.extracted_data = None

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
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
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
        try:
            for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                image_count += 1
        except Exception:
            logger.debug("Could not enumerate images in EPUB")

        # Also count SVG items
        try:
            for item in book.get_items():
                if hasattr(item, "media_type") and item.media_type == "image/svg+xml":
                    image_count += 1
        except Exception:
            pass

        return image_count

    def load_extracted_data(self, json_path):
        """Load previously extracted data from JSON."""
        print(f"\n📂 Loading extracted data from: {json_path}")
        with open(json_path, encoding="utf-8") as f:
            self.extracted_data = json.load(f)
        total = self.extracted_data.get("total_sections", len(self.extracted_data.get("pages", [])))
        print(f"✅ Loaded {total} sections")
        return True

    def categorize_content(self):
        """Categorize sections based on headings or keywords."""
        print("\n📋 Categorizing content...")

        categorized = {}
        sections = self.extracted_data.get("pages", [])

        # For single EPUB source, use single category with all sections
        if self.epub_path:
            epub_basename = Path(self.epub_path).stem
            category_key = self._sanitize_filename(epub_basename)
            categorized[category_key] = {
                "title": epub_basename,
                "pages": sections,
            }
            print("✅ Created 1 category (single EPUB source)")
            print(f"   - {epub_basename}: {len(sections)} sections")
            return categorized

        # Keyword-based categorization (multi-source scenario)
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

                    scores = {}
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
                            categorized["other"] = {"title": "Other", "pages": []}
                        categorized["other"]["pages"].append(section)
        else:
            # No categorization - single category
            categorized["content"] = {"title": "Content", "pages": sections}

        print(f"✅ Created {len(categorized)} categories")
        for _cat_key, cat_data in categorized.items():
            print(f"   - {cat_data['title']}: {len(cat_data['pages'])} sections")

        return categorized

    def build_skill(self):
        """Build complete skill structure."""
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

    def _generate_reference_file(self, _cat_key, cat_data, section_num, total_sections):
        """Generate a reference markdown file for a category."""
        sections = cat_data["pages"]

        # Use epub basename for filename
        epub_basename = ""
        if self.epub_path:
            epub_basename = Path(self.epub_path).stem

        if sections:
            section_nums = [s.get("section_number", i + 1) for i, s in enumerate(sections)]

            if total_sections == 1:
                filename = (
                    f"{self.skill_dir}/references/{epub_basename}.md"
                    if epub_basename
                    else f"{self.skill_dir}/references/main.md"
                )
            else:
                sec_range = f"s{min(section_nums)}-s{max(section_nums)}"
                base_name = epub_basename if epub_basename else "section"
                filename = f"{self.skill_dir}/references/{base_name}_{sec_range}.md"
        else:
            filename = f"{self.skill_dir}/references/section_{section_num:02d}.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {cat_data['title']}\n\n")

            for section in sections:
                sec_num = section.get("section_number", "?")
                heading = section.get("heading", "")
                heading_level = section.get("heading_level", "h1")

                f.write(f"---\n\n**📄 Source: Section {sec_num}**\n\n")

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
                tables = section.get("tables", [])
                if tables:
                    f.write("### Tables\n\n")
                    for table in tables:
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
                    assets_dir = os.path.join(self.skill_dir, "assets")
                    os.makedirs(assets_dir, exist_ok=True)

                    f.write("### Images\n\n")
                    for img in images:
                        img_index = img.get("index", 0)
                        img_data = img.get("data", b"")
                        img_filename = f"section_{sec_num}_img_{img_index}.png"
                        img_path = os.path.join(assets_dir, img_filename)

                        if isinstance(img_data, (bytes, bytearray)):
                            with open(img_path, "wb") as img_file:
                                img_file.write(img_data)
                            f.write(f"![Image {img_index}](../assets/{img_filename})\n\n")

                f.write("---\n\n")

        print(f"   Generated: {filename}")

    def _generate_index(self, categorized):
        """Generate reference index."""
        filename = f"{self.skill_dir}/references/index.md"

        epub_basename = ""
        if self.epub_path:
            epub_basename = Path(self.epub_path).stem

        total_sections = len(categorized)

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

                    if total_sections == 1:
                        link_filename = f"{epub_basename}.md" if epub_basename else "main.md"
                    else:
                        sec_range = f"s{min(section_nums)}-s{max(section_nums)}"
                        base_name = epub_basename if epub_basename else "section"
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

            # Metadata
            metadata = self.extracted_data.get("metadata", {})
            if metadata.get("author"):
                f.write(f"- Author: {metadata['author']}\n")
            if metadata.get("date"):
                f.write(f"- Date: {metadata['date']}\n")

        print(f"   Generated: {filename}")

    def _generate_skill_md(self, categorized):
        """Generate main SKILL.md file."""
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
                if metadata.get("publisher"):
                    f.write(f"**Publisher:** {metadata['publisher']}\n\n")
                if metadata.get("date"):
                    f.write(f"**Date:** {metadata['date']}\n\n")

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
            all_code = []
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
            all_tables = []
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
            f.write("**Generated by Skill Seeker** | EPUB Scraper\n")

        with open(filename, encoding="utf-8") as f:
            line_count = len(f.read().split("\n"))
        print(f"   Generated: {filename} ({line_count} lines)")

    def _format_key_concepts(self) -> str:
        """Extract key concepts from headings across all sections."""
        all_headings = []
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
        """Extract common patterns from text content."""
        patterns = []
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

    def _sanitize_filename(self, name):
        """Convert string to safe filename."""
        safe = re.sub(r"[^\w\s-]", "", name.lower())
        safe = re.sub(r"[-\s]+", "_", safe)
        return safe


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
                        "width": int(elem.get("width", 0) or 0),
                        "height": int(elem.get("height", 0) or 0),
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


def _extract_table_from_html(table_elem) -> dict | None:
    """Extract headers and rows from a BeautifulSoup <table> element."""
    headers = []
    rows = []

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


def _score_code_quality(code: str) -> float:
    """Simple quality heuristic for code blocks (0-10 scale)."""
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

    # Has indentation (common in Python, JS, etc.)
    if re.search(r"^    ", code, re.MULTILINE):
        score += 0.5

    # Has assignment, operators, or common code syntax
    if re.search(r"[=:{}()\[\]]", code):
        score += 0.3

    # Very short snippets get penalized
    if len(code) < 30:
        score -= 2.0

    return min(10.0, max(0.0, score))


def main():
    from .arguments.epub import add_epub_arguments

    parser = argparse.ArgumentParser(
        description="Convert EPUB e-book to skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    add_epub_arguments(parser)

    args = parser.parse_args()

    # Set logging level
    if getattr(args, "quiet", False):
        logging.getLogger().setLevel(logging.WARNING)
    elif getattr(args, "verbose", False):
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle --dry-run
    if getattr(args, "dry_run", False):
        source = getattr(args, "epub", None) or getattr(args, "from_json", None) or "(none)"
        print(f"\n{'=' * 60}")
        print("DRY RUN: EPUB Extraction")
        print(f"{'=' * 60}")
        print(f"Source:         {source}")
        print(f"Name:           {getattr(args, 'name', None) or '(auto-detect)'}")
        print(f"Enhance level:  {getattr(args, 'enhance_level', 0)}")
        print(f"\n✅ Dry run complete")
        return 0

    # Validate inputs
    if not (getattr(args, "epub", None) or getattr(args, "from_json", None)):
        parser.error("Must specify --epub or --from-json")

    # Build from JSON workflow
    if getattr(args, "from_json", None):
        name = Path(args.from_json).stem.replace("_extracted", "")
        config = {
            "name": getattr(args, "name", None) or name,
            "description": getattr(args, "description", None)
            or f"Use when referencing {name} documentation",
        }
        try:
            converter = EpubToSkillConverter(config)
            converter.load_extracted_data(args.from_json)
            converter.build_skill()
        except Exception as e:
            print(f"\n❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
        return 0

    # Direct EPUB mode
    if not getattr(args, "name", None):
        # Auto-detect name from filename
        args.name = Path(args.epub).stem

    config = {
        "name": args.name,
        "epub_path": args.epub,
        # Pass None so extract_epub() can infer from EPUB metadata
        "description": getattr(args, "description", None),
    }

    try:
        converter = EpubToSkillConverter(config)

        # Extract
        if not converter.extract_epub():
            print("\n❌ EPUB extraction failed - see error above", file=sys.stderr)
            sys.exit(1)

        # Build skill
        converter.build_skill()

        # Enhancement Workflow Integration
        from skill_seekers.cli.workflow_runner import run_workflows

        workflow_executed, workflow_names = run_workflows(args)
        workflow_name = ", ".join(workflow_names) if workflow_names else None

        # Traditional enhancement (complements workflow system)
        if getattr(args, "enhance_level", 0) > 0:
            import os

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
        print(f"\n❌ Unexpected error during EPUB processing: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
