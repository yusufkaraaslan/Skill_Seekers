"""
DocumentSkillBuilder — shared build-side machinery for document-type scrapers.

Phase 2 of docs/UNIFICATION_PLAN.md. The document scrapers (EPUB, Word, PPTX,
HTML, PDF, man, RSS, chat, Jupyter) all build the same artifact shape —
``SKILL.md`` + ``references/*.md`` + ``references/index.md`` — and before this
class each carried its own near-identical copy of the categorize / reference /
index / SKILL.md generation code (~90% identical between EPUB and Word, with
the rest diverging only in labels, metadata fields, and per-section bodies).

Subclass contract (attributes the scraper's ``__init__``/``extract`` provide):
- ``self.name``, ``self.description``, ``self.skill_dir`` (from SkillConverter)
- ``self.categories``: dict from config (may be empty)
- ``self.extracted_data``: the loaded ``*_extracted.json`` dict with a
  ``"pages"`` list of section dicts (``section_number``, ``heading``,
  ``heading_level``, ``headings``, ``text``, ``code_samples``, ``tables``,
  ``images``) plus totals/metadata keys.

Per-scraper variation points are class attributes and small hook methods —
override those, not the generators.
"""

import json
import os
import re
from pathlib import Path

from skill_seekers.cli.scraper_utils import reference_filename
from skill_seekers.cli.skill_converter import SkillConverter


class DocumentSkillBuilder(SkillConverter):
    """Template for building a skill from extracted document sections."""

    # ── Variation points ──────────────────────────────────────────────────
    # Attribute on self holding the source file path (used for the category
    # stem and the single-source fast path), e.g. "epub_path", "docx_path".
    SOURCE_PATH_ATTR: str = ""
    # Human label for the source kind in progress output, e.g. "EPUB", "Word".
    SOURCE_LABEL: str = "document"
    # Footer credit line suffix in SKILL.md, e.g. "EPUB Scraper".
    FOOTER_LABEL: str = "Document Scraper"
    # Unit noun in progress output and section counts.
    UNIT_LABEL: str = "sections"
    # Document noun: index.md title ("{Name} {Noun.title()} Reference") and
    # the Quick Reference blurb ("Common {noun} patterns found").
    DOC_NOUN: str = "documentation"
    # Key in the extracted JSON holding the total count reported by
    # load_extracted_data (man/pdf use "total_pages").
    LOAD_TOTAL_KEY: str = "total_sections"
    # Key holding each page's number and the range prefix in reference
    # filenames (pdf uses "page_number"/"p").
    NUMBER_KEY: str = "section_number"
    NUMBER_PREFIX: str = "s"
    # Label before the number range in index.md category lines
    # ("Sections 1-5"; pdf uses "Pages").
    RANGE_LABEL: str = "Sections"
    # Heading keywords recognized by _format_patterns_from_content.
    PATTERN_KEYWORDS: tuple[str, ...] = (
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
    )
    # (metadata key, display label) pairs for SKILL.md "Document Information".
    SKILL_MD_METADATA_FIELDS: tuple[tuple[str, str], ...] = (
        ("title", "Title"),
        ("author", "Author"),
    )
    # (metadata key, display label) pairs appended to index.md statistics.
    INDEX_METADATA_FIELDS: tuple[tuple[str, str], ...] = (("author", "Author"),)

    # ── Shared helpers ────────────────────────────────────────────────────

    @property
    def source_path(self) -> str:
        """The scraper's source file path ('' when not set)."""
        return getattr(self, self.SOURCE_PATH_ATTR, "") if self.SOURCE_PATH_ATTR else ""

    @property
    def source_stem(self) -> str:
        """Stem of the source file, used as the reference-filename base."""
        return Path(self.source_path).stem if self.source_path else ""

    def load_extracted_data(self, json_path):
        """Load previously extracted data from JSON."""
        print(f"\n📂 Loading extracted data from: {json_path}")
        with open(json_path, encoding="utf-8") as f:
            self.extracted_data = json.load(f)
        total = self.extracted_data.get(
            self.LOAD_TOTAL_KEY, len(self.extracted_data.get("pages", []))
        )
        print(f"✅ Loaded {total} {self.UNIT_LABEL}")
        return True

    def _sanitize_filename(self, name):
        """Convert string to safe filename."""
        safe = re.sub(r"[^\w\s-]", "", name.lower())
        safe = re.sub(r"[-\s]+", "_", safe)
        return safe

    def category_stem(self, cat_key):
        """Stem used as the base of a category's reference filename.

        Base: the source-file stem (all single-source document scrapers).
        chat overrides this to name files by category key instead.
        """
        del cat_key  # unused in the base; hook parameter for subclasses
        return self.source_stem

    def _reference_filename(self, cat_data, section_num, total_sections, cat_key=""):
        """Basename of a category's reference file — single source of truth shared
        by the writer, index.md, and the SKILL.md nav so links can't drift (DOC-07).

        ``cat_key`` is trailing-and-defaulted for backward compatibility with
        existing callers; only ``category_stem`` overrides consume it.
        """
        return reference_filename(
            cat_data.get("pages") or [],
            section_num,
            total_sections,
            self.category_stem(cat_key),
            number_key=self.NUMBER_KEY,
            prefix=self.NUMBER_PREFIX,
        )

    # ── Categorization ────────────────────────────────────────────────────

    def categorize_content(self):
        """Categorize sections based on headings or keywords."""
        print("\n📋 Categorizing content...")

        categorized = {}
        sections = self.extracted_data.get("pages", [])

        # For a single source file, use one category with all sections
        if self.source_path:
            basename = self.source_stem
            category_key = self._sanitize_filename(basename)
            categorized[category_key] = {
                "title": basename,
                "pages": sections,
            }
            print(f"✅ Created 1 category (single {self.SOURCE_LABEL} source)")
            print(f"   - {basename}: {len(sections)} {self.UNIT_LABEL}")
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
            print(f"   - {cat_data['title']}: {len(cat_data['pages'])} {self.UNIT_LABEL}")

        return categorized

    # ── Build orchestration ───────────────────────────────────────────────

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

    # ── Reference files ───────────────────────────────────────────────────

    def _generate_reference_file(self, _cat_key, cat_data, section_num, total_sections):
        """Generate a reference markdown file for a category."""
        filename = (
            f"{self.skill_dir}/references/"
            f"{self._reference_filename(cat_data, section_num, total_sections, _cat_key)}"
        )
        sections = cat_data.get("pages") or []

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {cat_data['title']}\n\n")
            for section in sections:
                self._write_reference_section(f, section)

        print(f"   Generated: {filename}")

    def _write_reference_section(self, f, section):
        """Write one section's body into a reference file. Override for
        source types whose sections aren't heading+text+code+tables shaped."""
        sec_num = section.get(self.NUMBER_KEY, "?")
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
                self._write_markdown_table(f, table)

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

                # Require NON-EMPTY bytes — b"" passed the isinstance
                # check and produced a 0-byte PNG plus a broken ![] link.
                if isinstance(img_data, (bytes, bytearray)) and len(img_data) > 0:
                    with open(img_path, "wb") as img_file:
                        img_file.write(img_data)
                    f.write(f"![Image {img_index}](../assets/{img_filename})\n\n")

        f.write("---\n\n")

    @staticmethod
    def _write_markdown_table(f, table, max_rows: int | None = None):
        """Render one extracted table dict as a markdown table."""
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        if headers:
            f.write("| " + " | ".join(str(h) for h in headers) + " |\n")
            f.write("| " + " | ".join("---" for _ in headers) + " |\n")
        for row in rows if max_rows is None else rows[:max_rows]:
            f.write("| " + " | ".join(str(c) for c in row) + " |\n")
        f.write("\n")

    # ── index.md ──────────────────────────────────────────────────────────

    def _generate_index(self, categorized):
        """Generate reference index."""
        filename = f"{self.skill_dir}/references/index.md"

        total_sections = len(categorized)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {self.name.title()} {self.DOC_NOUN.title()} Reference\n\n")
            f.write("## Categories\n\n")

            section_num = 1
            for _cat_key, cat_data in categorized.items():
                sections = cat_data["pages"]
                section_count = len(sections)

                link_filename = self._reference_filename(
                    cat_data, section_num, total_sections, _cat_key
                )
                if sections:
                    section_nums = [s.get(self.NUMBER_KEY, i + 1) for i, s in enumerate(sections)]
                    sec_range_str = f"{self.RANGE_LABEL} {min(section_nums)}-{max(section_nums)}"
                else:
                    sec_range_str = "N/A"

                f.write(
                    f"- [{cat_data['title']}]({link_filename}) "
                    f"({section_count} {self.UNIT_LABEL}, {sec_range_str})\n"
                )
                section_num += 1

            f.write("\n## Statistics\n\n")
            self._write_index_statistics(f)

        print(f"   Generated: {filename}")

    def _write_index_statistics(self, f):
        """Statistics block of index.md. Override to add source-type lines."""
        f.write(f"- Total sections: {self.extracted_data.get('total_sections', 0)}\n")
        f.write(f"- Code blocks: {self.extracted_data.get('total_code_blocks', 0)}\n")
        f.write(f"- Images: {self.extracted_data.get('total_images', 0)}\n")

        metadata = self.extracted_data.get("metadata", {})
        for key, label in self.INDEX_METADATA_FIELDS:
            if metadata.get(key):
                f.write(f"- {label}: {metadata[key]}\n")

    # ── SKILL.md ──────────────────────────────────────────────────────────

    @staticmethod
    def _frontmatter_value(value: str) -> str:
        """Quote a YAML frontmatter scalar only when it needs it.

        json.dumps yields a valid double-quoted YAML scalar. Quoting is
        conditional so safe values keep their historical unquoted form
        (golden outputs depend on the exact bytes) while a hostile value
        like "godot: engine" can't corrupt the frontmatter.
        """
        if value != value.strip() or any(c in value for c in ":#\"'\n"):
            return json.dumps(value)
        return value

    def _generate_skill_md(self, categorized):
        """Generate main SKILL.md file."""
        filename = f"{self.skill_dir}/SKILL.md"

        skill_name = self.name.lower().replace("_", "-").replace(" ", "-")[:64]
        desc = self.description[:1024] if len(self.description) > 1024 else self.description

        with open(filename, "w", encoding="utf-8") as f:
            # YAML frontmatter
            f.write("---\n")
            f.write(f"name: {self._frontmatter_value(skill_name)}\n")
            f.write(f"description: {self._frontmatter_value(desc)}\n")
            f.write("---\n\n")

            f.write(f"# {self.name.title()} Documentation Skill\n\n")
            f.write(f"{self.description}\n\n")

            # Document metadata
            metadata = self.extracted_data.get("metadata", {})
            if any(v for v in metadata.values() if v):
                f.write("## 📋 Document Information\n\n")
                self._write_skill_md_metadata(f, metadata)

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
                f.write(f"- **{cat_data['title']}**: {section_count} {self.UNIT_LABEL}\n")
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
                    if table.get("headers", []):
                        self._write_markdown_table(f, table, max_rows=5)

            # Statistics
            f.write("## 📊 Documentation Statistics\n\n")
            f.write(f"- **Total Sections**: {total_sections}\n")
            f.write(f"- **Code Blocks**: {self.extracted_data.get('total_code_blocks', 0)}\n")
            f.write(f"- **Images/Diagrams**: {self.extracted_data.get('total_images', 0)}\n")
            f.write(f"- **Tables**: {len(all_tables)}\n")
            self._write_skill_md_extra_stats(f)

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
            total_sections = len(categorized)
            for section_num, (_cat_key, cat_data) in enumerate(categorized.items(), 1):
                cat_file = self._reference_filename(cat_data, section_num, total_sections, _cat_key)
                f.write(f"- `references/{cat_file}` - {cat_data['title']}\n")
            f.write("\n")
            f.write("See `references/index.md` for complete documentation structure.\n\n")

            # Footer
            f.write("---\n\n")
            f.write(f"**Generated by Skill Seeker** | {self.FOOTER_LABEL}\n")

        with open(filename, encoding="utf-8") as f:
            line_count = len(f.read().split("\n"))
        print(f"   Generated: {filename} ({line_count} lines)")

    def _write_skill_md_metadata(self, f, metadata):
        """Body of the SKILL.md "Document Information" block (header and
        any-metadata gate stay in the base). Override to append extra lines."""
        for key, label in self.SKILL_MD_METADATA_FIELDS:
            if metadata.get(key):
                f.write(f"**{label}:** {metadata[key]}\n\n")

    def _write_skill_md_extra_stats(self, f):
        """Extra bullet lines inside SKILL.md "Documentation Statistics",
        written after the Tables count (html adds its file count here)."""

    # ── SKILL.md content helpers ──────────────────────────────────────────

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
        """Extract common patterns from text content (keywords come from
        the PATTERN_KEYWORDS class attribute)."""
        patterns = []

        for section in self.extracted_data.get("pages", []):
            heading_text = section.get("heading", "").lower()
            sec_num = section.get(self.NUMBER_KEY, 0)

            for keyword in self.PATTERN_KEYWORDS:
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

        content = f"*Common {self.DOC_NOUN} patterns found:*\n\n"
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
