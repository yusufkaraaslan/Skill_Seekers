#!/usr/bin/env python3
"""
AsciiDoc Documentation to Skill Converter

Converts AsciiDoc (.adoc, .asciidoc) documentation files into AI-ready skills.
Supports both single files and directories of AsciiDoc documents.

Uses the ``asciidoc`` library when available for accurate HTML rendering,
falling back to a comprehensive regex-based parser that handles headings,
code blocks, tables, admonitions, include directives, and inline formatting.

Usage:
    skill-seekers asciidoc --asciidoc-path doc.adoc --name myskill
    skill-seekers asciidoc --asciidoc-path docs/ --name myskill
    skill-seekers asciidoc --from-json doc_extracted.json
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

# Optional dependency guard — asciidoc library for HTML conversion
try:
    import asciidoc as asciidoc_lib  # noqa: F401

    ASCIIDOC_AVAILABLE = True
except ImportError:
    ASCIIDOC_AVAILABLE = False

logger = logging.getLogger(__name__)

ASCIIDOC_EXTENSIONS = {".adoc", ".asciidoc", ".asc", ".ad"}
ADMONITION_TYPES = ("NOTE", "TIP", "WARNING", "IMPORTANT", "CAUTION")

# Regex patterns for AsciiDoc structure
RE_HEADING = re.compile(r"^(={1,5})\s+(.+)$", re.MULTILINE)
RE_SOURCE_ATTR = re.compile(r"^\[source(?:,\s*(\w[\w+#.-]*))?(?:,.*?)?\]$", re.MULTILINE)
RE_LISTING_DELIM = re.compile(r"^(-{4,})$", re.MULTILINE)
RE_LITERAL_DELIM = re.compile(r"^(\.{4,})$", re.MULTILINE)
RE_TABLE_DELIM = re.compile(r"^\|={3,}$", re.MULTILINE)
RE_TABLE_CELL = re.compile(r"^\|(.+)$", re.MULTILINE)
RE_ADMONITION_PARA = re.compile(
    r"^(NOTE|TIP|WARNING|IMPORTANT|CAUTION):\s+(.+?)(?:\n\n|\Z)",
    re.MULTILINE | re.DOTALL,
)
RE_ADMONITION_BLOCK = re.compile(
    r"^\[(NOTE|TIP|WARNING|IMPORTANT|CAUTION)\]\n={4,}\n(.*?)\n={4,}",
    re.MULTILINE | re.DOTALL,
)
RE_INCLUDE = re.compile(r"^include::(.+?)\[([^\]]*)\]$", re.MULTILINE)
RE_ATTRIBUTE = re.compile(r"^:([a-zA-Z0-9_-]+):\s*(.*)$", re.MULTILINE)
RE_ATTR_REF = re.compile(r"\{([a-zA-Z0-9_-]+)\}")
RE_BOLD = re.compile(r"\*([^\s*](?:.*?[^\s*])?)\*")
RE_ITALIC = re.compile(r"_([^\s_](?:.*?[^\s_])?)_")
RE_MONO = re.compile(r"`([^`]+)`")
RE_LINK = re.compile(r"(https?://\S+)\[([^\]]*)\]")
RE_XREF = re.compile(r"<<([^,>]+)(?:,\s*([^>]+))?>>")


def _check_asciidoc_deps() -> None:
    """Log debug message when asciidoc library is not installed (regex fallback used)."""
    if not ASCIIDOC_AVAILABLE:
        logger.debug(
            "asciidoc library not installed; using regex-based parser.\n"
            'Install with: pip install "skill-seekers[asciidoc]" or: pip install asciidoc'
        )


def infer_description_from_asciidoc(metadata: dict | None = None, name: str = "") -> str:
    """Infer skill description from AsciiDoc document metadata."""
    if metadata:
        if metadata.get("description") and len(str(metadata["description"])) > 20:
            desc = str(metadata["description"]).strip()
            return (
                f"Use when {desc[:147].lower()}..."
                if len(desc) > 150
                else f"Use when {desc.lower()}"
            )
        if metadata.get("title") and len(str(metadata["title"])) > 10:
            return f"Use when working with {str(metadata['title']).lower()}"
    return (
        f"Use when referencing {name} documentation"
        if name
        else "Use when referencing this documentation"
    )


def _score_code_quality(code: str) -> float:
    """Simple quality heuristic for code blocks (0-10 scale)."""
    if not code:
        return 0.0
    score = 5.0
    line_count = len(code.strip().split("\n"))
    if line_count >= 10:
        score += 2.0
    elif line_count >= 5:
        score += 1.0
    if re.search(r"\b(def |class |function |func |fn )", code):
        score += 1.5
    if re.search(r"\b(import |from .+ import|require\(|#include|using )", code):
        score += 0.5
    if re.search(r"^    ", code, re.MULTILINE):
        score += 0.5
    if re.search(r"[=:{}()\[\]]", code):
        score += 0.3
    if len(code) < 30:
        score -= 2.0
    return min(10.0, max(0.0, score))


class AsciiDocToSkillConverter:
    """Convert AsciiDoc documentation to an AI-ready skill.

    Handles single ``.adoc`` files and directories. Content is parsed into
    intermediate JSON, categorised, then rendered into the standard skill
    directory layout (SKILL.md, references/, etc.).
    """

    def __init__(self, config: dict) -> None:
        self.config = config
        self.name: str = config["name"]
        self.asciidoc_path: str = config.get("asciidoc_path", "")
        self.description: str = (
            config.get("description") or f"Use when referencing {self.name} documentation"
        )
        self.skill_dir: str = f"output/{self.name}"
        self.data_file: str = f"output/{self.name}_extracted.json"
        self.categories: dict = config.get("categories", {})
        self.extracted_data: dict | None = None

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    def extract_asciidoc(self) -> bool:
        """Extract content from AsciiDoc file(s).

        Discovers files, resolves attributes/includes, parses sections,
        detects languages, and saves intermediate JSON.

        Returns:
            True on success.

        Raises:
            FileNotFoundError: If path does not exist.
            ValueError: If no AsciiDoc files found.
        """
        _check_asciidoc_deps()
        from skill_seekers.cli.language_detector import LanguageDetector

        print(f"\n🔍 Extracting from AsciiDoc: {self.asciidoc_path}")
        path = Path(self.asciidoc_path)
        if not path.exists():
            raise FileNotFoundError(f"AsciiDoc path not found: {self.asciidoc_path}")

        files = self._discover_files(path)
        if not files:
            raise ValueError(
                f"No AsciiDoc files found at: {self.asciidoc_path}\n"
                f"Expected extensions: {', '.join(sorted(ASCIIDOC_EXTENSIONS))}"
            )
        print(f"   Found {len(files)} AsciiDoc file(s)")

        all_sections: list[dict] = []
        metadata: dict = {}
        section_counter = 0

        for file_path in sorted(files):
            raw_text = file_path.read_text(encoding="utf-8", errors="replace")
            attributes = self._extract_attributes(raw_text)
            resolved_text = self._resolve_attributes(raw_text, attributes)
            resolved_text = self._resolve_includes(resolved_text, file_path.parent)
            if not metadata:
                metadata = self._build_metadata(attributes, file_path)

            for section in self._parse_asciidoc_sections(resolved_text):
                section_counter += 1
                section["section_number"] = section_counter
                section["source_file"] = str(file_path)
                body = section.pop("body", "")
                section["code_samples"] = self._extract_code_blocks(body)
                section["tables"] = self._extract_tables(body)
                section["admonitions"] = self._extract_admonitions(body)
                section["includes"] = self._extract_includes(body)
                section["text"] = self._convert_to_markdown(body)
                all_sections.append(section)

        # Language detection
        detector = LanguageDetector(min_confidence=0.15)
        languages_detected: dict[str, int] = {}
        total_code_blocks = 0
        for section in all_sections:
            for cs in section.get("code_samples", []):
                if cs.get("language"):
                    languages_detected[cs["language"]] = (
                        languages_detected.get(cs["language"], 0) + 1
                    )
                total_code_blocks += 1
        for section in all_sections:
            for cs in section.get("code_samples", []):
                if not cs.get("language") and cs.get("code"):
                    lang, conf = detector.detect_from_code(cs["code"])
                    if lang and conf >= 0.3:
                        cs["language"] = lang
                        languages_detected[lang] = languages_detected.get(lang, 0) + 1

        if not self.config.get("description"):
            self.description = infer_description_from_asciidoc(metadata, self.name)

        result_data = {
            "source_path": self.asciidoc_path,
            "metadata": metadata,
            "total_sections": len(all_sections),
            "total_files": len(files),
            "total_code_blocks": total_code_blocks,
            "total_tables": sum(len(s.get("tables", [])) for s in all_sections),
            "total_admonitions": sum(len(s.get("admonitions", [])) for s in all_sections),
            "languages_detected": languages_detected,
            "pages": all_sections,
        }
        os.makedirs(os.path.dirname(self.data_file) or ".", exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n💾 Saved extracted data to: {self.data_file}")
        self.extracted_data = result_data
        print(
            f"✅ Extracted {len(all_sections)} sections, {total_code_blocks} code blocks, "
            f"{result_data['total_tables']} tables, {result_data['total_admonitions']} admonitions"
        )
        return True

    def _discover_files(self, path: Path) -> list[Path]:
        """Return sorted list of AsciiDoc files from *path* (file or directory)."""
        if path.is_file():
            return [path] if path.suffix.lower() in ASCIIDOC_EXTENSIONS else []
        found: list[Path] = []
        for ext in ASCIIDOC_EXTENSIONS:
            found.extend(path.rglob(f"*{ext}"))
        return sorted(set(found))

    # ------------------------------------------------------------------
    # Attribute / include resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_attributes(text: str) -> dict[str, str]:
        """Extract ``:attr-name: value`` definitions from text."""
        return {m.group(1): m.group(2).strip() for m in RE_ATTRIBUTE.finditer(text)}

    @staticmethod
    def _resolve_attributes(text: str, attributes: dict[str, str]) -> str:
        """Replace ``{attr-name}`` references with their values."""
        return RE_ATTR_REF.sub(lambda m: attributes.get(m.group(1), m.group(0)), text)

    def _resolve_includes(self, text: str, base_dir: Path) -> str:
        """Resolve ``include::`` directives by inlining referenced files."""
        max_depth = 5

        def _resolve_once(src: str, depth: int) -> str:
            if depth >= max_depth:
                return src

            def _replacer(match: re.Match) -> str:
                inc_path = match.group(1).strip()
                inc_file = base_dir / inc_path
                if inc_file.is_file():
                    try:
                        return _resolve_once(
                            inc_file.read_text(encoding="utf-8", errors="replace"), depth + 1
                        )
                    except OSError:
                        logger.debug("Could not read include file: %s", inc_file)
                return f"// include::{inc_path}[] (not resolved)"

            return RE_INCLUDE.sub(_replacer, src)

        return _resolve_once(text, 0)

    @staticmethod
    def _build_metadata(attributes: dict[str, str], file_path: Path) -> dict:
        """Build metadata dict from document attributes."""
        return {
            "title": attributes.get("doctitle", attributes.get("title", file_path.stem)),
            "author": attributes.get("author", ""),
            "email": attributes.get("email", ""),
            "revision": attributes.get("revnumber", attributes.get("version", "")),
            "date": attributes.get("revdate", attributes.get("date", "")),
            "description": attributes.get("description", ""),
            "keywords": attributes.get("keywords", ""),
            "source_file": str(file_path),
        }

    # ------------------------------------------------------------------
    # Section parsing
    # ------------------------------------------------------------------

    def _parse_asciidoc_sections(self, text: str) -> list[dict]:
        """Parse AsciiDoc text into sections split by headings (= through =====)."""
        heading_matches = [
            (m.start(), len(m.group(1)), m.group(2).strip(), m.group(0))
            for m in RE_HEADING.finditer(text)
        ]
        if not heading_matches:
            return [{"heading": "", "heading_level": "h1", "body": text.strip(), "headings": []}]

        sections: list[dict] = []
        preamble = text[: heading_matches[0][0]].strip()
        if preamble:
            sections.append(
                {"heading": "", "heading_level": "h1", "body": preamble, "headings": []}
            )

        for idx, (start, level, heading_text, raw) in enumerate(heading_matches):
            body_start = start + len(raw)
            body_end = heading_matches[idx + 1][0] if idx + 1 < len(heading_matches) else len(text)
            body = text[body_start:body_end].strip()

            sub_headings = [
                {"level": f"h{len(m.group(1))}", "text": m.group(2).strip()}
                for m in RE_HEADING.finditer(body)
                if len(m.group(1)) > level
            ]
            sections.append(
                {
                    "heading": heading_text,
                    "heading_level": f"h{level}",
                    "body": body,
                    "headings": sub_headings,
                }
            )
        return sections

    # ------------------------------------------------------------------
    # Code block extraction
    # ------------------------------------------------------------------

    def _extract_code_blocks(self, text: str) -> list[dict]:
        """Extract source/listing/literal code blocks from AsciiDoc text.

        Handles [source,lang] + ---- blocks, bare ---- blocks, and .... blocks.
        """
        blocks: list[dict] = []
        consumed: list[tuple[int, int]] = []

        # Pattern 1: [source,lang] + ---- block
        for attr_m in RE_SOURCE_ATTR.finditer(text):
            lang = (attr_m.group(1) or "").strip()
            open_m = RE_LISTING_DELIM.search(text, attr_m.end())
            if not open_m:
                continue
            between = text[attr_m.end() : open_m.start()].strip()
            if between and not between.startswith(".") and "\n" in between:
                continue
            delim = open_m.group(1)
            close_m = re.search(
                r"^" + re.escape(delim) + r"$", text[open_m.end() + 1 :], re.MULTILINE
            )
            if not close_m:
                continue
            abs_close = open_m.end() + 1 + close_m.start()
            code = text[open_m.end() : abs_close].strip("\n")
            if code:
                blocks.append(
                    {"code": code, "language": lang, "quality_score": _score_code_quality(code)}
                )
                consumed.append((attr_m.start(), abs_close + len(close_m.group(0))))

        # Pattern 2: bare ---- listing blocks
        for m in RE_LISTING_DELIM.finditer(text):
            if self._in_range(m.start(), consumed):
                continue
            delim = m.group(1)
            close_m = re.search(r"^" + re.escape(delim) + r"$", text[m.end() + 1 :], re.MULTILINE)
            if not close_m:
                continue
            abs_close = m.end() + 1 + close_m.start()
            code = text[m.end() : abs_close].strip("\n")
            if code:
                blocks.append(
                    {"code": code, "language": "", "quality_score": _score_code_quality(code)}
                )
                consumed.append((m.start(), abs_close + len(close_m.group(0))))

        # Pattern 3: .... literal blocks
        for m in RE_LITERAL_DELIM.finditer(text):
            if self._in_range(m.start(), consumed):
                continue
            delim = m.group(1)
            close_m = re.search(r"^" + re.escape(delim) + r"$", text[m.end() + 1 :], re.MULTILINE)
            if not close_m:
                continue
            abs_close = m.end() + 1 + close_m.start()
            code = text[m.end() : abs_close].strip("\n")
            if code:
                blocks.append(
                    {"code": code, "language": "", "quality_score": _score_code_quality(code)}
                )
                consumed.append((m.start(), abs_close + len(close_m.group(0))))

        return blocks

    # ------------------------------------------------------------------
    # Table extraction
    # ------------------------------------------------------------------

    def _extract_tables(self, text: str) -> list[dict]:
        """Parse AsciiDoc tables delimited by ``|===``."""
        tables: list[dict] = []
        delimiters = list(RE_TABLE_DELIM.finditer(text))
        idx = 0
        while idx + 1 < len(delimiters):
            body = text[delimiters[idx].end() : delimiters[idx + 1].start()].strip()
            if body:
                table = self._parse_table_body(body)
                if table:
                    tables.append(table)
            idx += 2
        return tables

    @staticmethod
    def _parse_table_body(table_body: str) -> dict | None:
        """Parse body of an AsciiDoc table into headers and rows."""
        groups = re.split(r"\n\s*\n", table_body.strip())
        if not groups:
            return None

        def _parse_row(row_text: str) -> list[str]:
            return [p.strip() for p in row_text.split("|") if p.strip()]

        # First group → headers
        headers: list[str] = []
        for line in groups[0].strip().splitlines():
            if line.strip().startswith("|"):
                parsed = _parse_row(line)
                if parsed and not headers:
                    headers = parsed
                elif parsed:
                    for i, cell in enumerate(parsed):
                        if i < len(headers):
                            headers[i] = f"{headers[i]} {cell}".strip()
                        else:
                            headers.append(cell)

        # Remaining groups → rows
        rows: list[list[str]] = []
        for group in groups[1:]:
            for line in group.strip().splitlines():
                if line.strip().startswith("|"):
                    parsed = _parse_row(line)
                    if parsed:
                        rows.append(parsed)

        # Single group fallback: first parsed line = header, rest = rows
        if len(groups) == 1 and not rows:
            all_parsed = [
                _parse_row(line)
                for line in groups[0].strip().splitlines()
                if line.strip().startswith("|")
            ]
            all_parsed = [r for r in all_parsed if r]
            if len(all_parsed) > 1:
                headers, rows = all_parsed[0], all_parsed[1:]
            elif all_parsed:
                headers = all_parsed[0]

        return {"headers": headers, "rows": rows} if headers or rows else None

    # ------------------------------------------------------------------
    # Admonition extraction
    # ------------------------------------------------------------------

    def _extract_admonitions(self, text: str) -> list[dict]:
        """Extract NOTE/TIP/WARNING/IMPORTANT/CAUTION admonitions."""
        admonitions: list[dict] = []
        seen: set[str] = set()
        for pattern in (RE_ADMONITION_BLOCK, RE_ADMONITION_PARA):
            for m in pattern.finditer(text):
                adm_type, adm_text = m.group(1), m.group(2).strip()
                if adm_text and adm_text not in seen:
                    admonitions.append({"type": adm_type, "text": adm_text})
                    seen.add(adm_text)
        return admonitions

    # ------------------------------------------------------------------
    # Include directive extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_includes(text: str) -> list[dict]:
        """Detect remaining ``include::`` directives in text."""
        return [
            {"path": m.group(1).strip(), "options": m.group(2).strip()}
            for m in RE_INCLUDE.finditer(text)
        ]

    # ------------------------------------------------------------------
    # AsciiDoc → Markdown conversion
    # ------------------------------------------------------------------

    def _convert_to_markdown(self, text: str) -> str:
        """Convert AsciiDoc inline formatting to Markdown equivalents."""
        result = text
        # Remove processed block delimiters and attribute lines
        for pat in (
            RE_LISTING_DELIM,
            RE_LITERAL_DELIM,
            RE_TABLE_DELIM,
            RE_SOURCE_ATTR,
            RE_ATTRIBUTE,
        ):
            result = pat.sub("", result)
        # Remove admonition block markers and delimiters
        result = re.sub(
            r"^\[(NOTE|TIP|WARNING|IMPORTANT|CAUTION)\]\s*$", "", result, flags=re.MULTILINE
        )
        result = re.sub(r"^={4,}$", "", result, flags=re.MULTILINE)
        # Headings: = Title → # Title
        result = RE_HEADING.sub(lambda m: f"{'#' * len(m.group(1))} {m.group(2).strip()}", result)
        # Inline formatting
        result = RE_BOLD.sub(r"**\1**", result)
        result = RE_ITALIC.sub(r"*\1*", result)
        result = RE_LINK.sub(r"[\2](\1)", result)
        result = RE_XREF.sub(lambda m: f"*{m.group(2) or m.group(1)}*", result)
        # Lists: * item → - item, . item → 1. item
        result = re.sub(
            r"^(\*{1,5})\s+",
            lambda m: "  " * (len(m.group(1)) - 1) + "- ",
            result,
            flags=re.MULTILINE,
        )
        result = re.sub(
            r"^(\.{1,5})\s+",
            lambda m: "  " * (len(m.group(1)) - 1) + "1. ",
            result,
            flags=re.MULTILINE,
        )
        # Block titles: .Title → **Title**
        result = re.sub(r"^\.([A-Z][\w\s]+)$", r"**\1**", result, flags=re.MULTILINE)
        # Include comments
        result = re.sub(
            r"^//\s*include::(.+?)\[\].*$", r"*(included: \1)*", result, flags=re.MULTILINE
        )
        # Remove leftover table cell markers
        result = re.sub(r"^\|\s*", "", result, flags=re.MULTILINE)
        # Collapse blank lines
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()

    # ------------------------------------------------------------------
    # Load / categorize / build
    # ------------------------------------------------------------------

    def load_extracted_data(self, json_path: str) -> bool:
        """Load previously extracted data from JSON file."""
        print(f"\n📂 Loading extracted data from: {json_path}")
        with open(json_path, encoding="utf-8") as f:
            self.extracted_data = json.load(f)
        total = self.extracted_data.get("total_sections", len(self.extracted_data.get("pages", [])))
        print(f"✅ Loaded {total} sections")
        return True

    def categorize_content(self) -> dict:
        """Categorize sections by source file, headings, or keywords."""
        print("\n📋 Categorizing content...")
        categorized: dict[str, dict] = {}
        sections = self.extracted_data.get("pages", [])
        path = Path(self.asciidoc_path) if self.asciidoc_path else None

        if path and path.is_file():
            key = self._sanitize_filename(path.stem)
            categorized[key] = {"title": path.stem, "pages": sections}
            print(f"✅ Created 1 category (single file): {path.stem}: {len(sections)} sections")
            return categorized

        if path and path.is_dir():
            for s in sections:
                src_stem = Path(s.get("source_file", "unknown")).stem
                key = self._sanitize_filename(src_stem)
                categorized.setdefault(key, {"title": src_stem, "pages": []})["pages"].append(s)
            if categorized:
                print(f"✅ Created {len(categorized)} categories (by source file)")
                for cat in categorized.values():
                    print(f"   - {cat['title']}: {len(cat['pages'])} sections")
                return categorized

        if self.categories:
            first_val = next(iter(self.categories.values()), None)
            if isinstance(first_val, list) and first_val and isinstance(first_val[0], dict):
                for k, pages in self.categories.items():
                    categorized[k] = {"title": k.replace("_", " ").title(), "pages": pages}
            else:
                for k in self.categories:
                    categorized[k] = {"title": k.replace("_", " ").title(), "pages": []}
                for s in sections:
                    txt = s.get("text", "").lower()
                    htxt = s.get("heading", "").lower()
                    scores = {
                        k: sum(
                            1
                            for kw in kws
                            if isinstance(kw, str) and (kw.lower() in txt or kw.lower() in htxt)
                        )
                        for k, kws in self.categories.items()
                        if isinstance(kws, list)
                    }
                    scores = {k: v for k, v in scores.items() if v > 0}
                    if scores:
                        categorized[max(scores, key=scores.get)]["pages"].append(s)
                    else:
                        categorized.setdefault("other", {"title": "Other", "pages": []})[
                            "pages"
                        ].append(s)
        else:
            categorized["content"] = {"title": "Content", "pages": sections}

        print(f"✅ Created {len(categorized)} categories")
        for cat in categorized.values():
            print(f"   - {cat['title']}: {len(cat['pages'])} sections")
        return categorized

    def build_skill(self) -> None:
        """Build complete skill directory structure."""
        print(f"\n🏗️  Building skill: {self.name}")
        for subdir in ("references", "scripts", "assets"):
            os.makedirs(f"{self.skill_dir}/{subdir}", exist_ok=True)

        categorized = self.categorize_content()
        print("\n📝 Generating reference files...")
        total_cats = len(categorized)
        for i, (cat_key, cat_data) in enumerate(categorized.items(), 1):
            self._generate_reference_file(cat_key, cat_data, i, total_cats)
        self._generate_index(categorized)
        self._generate_skill_md(categorized)
        print(f"\n✅ Skill built successfully: {self.skill_dir}/")
        print(f"\n📦 Next step: Package with: skill-seekers package {self.skill_dir}/")

    # ------------------------------------------------------------------
    # Private generation methods
    # ------------------------------------------------------------------

    def _ref_filename(self, cat_data: dict, section_num: int, total: int) -> str:
        """Compute reference file path for a category."""
        sections = cat_data["pages"]
        adoc_base = ""
        if self.asciidoc_path:
            p = Path(self.asciidoc_path)
            adoc_base = p.stem if p.is_file() else ""

        if sections:
            nums = [s.get("section_number", i + 1) for i, s in enumerate(sections)]
            if total == 1:
                return f"{self.skill_dir}/references/{adoc_base or 'main'}.md"
            base = adoc_base or "section"
            return f"{self.skill_dir}/references/{base}_s{min(nums)}-s{max(nums)}.md"
        return f"{self.skill_dir}/references/section_{section_num:02d}.md"

    def _generate_reference_file(
        self, _cat_key: str, cat_data: dict, section_num: int, total: int
    ) -> None:
        """Generate a reference Markdown file for one category."""
        filename = self._ref_filename(cat_data, section_num, total)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {cat_data['title']}\n\n")
            for section in cat_data["pages"]:
                sec_num = section.get("section_number", "?")
                heading = section.get("heading", "")
                hl = section.get("heading_level", "h1")
                f.write(f"---\n\n**📄 Source: Section {sec_num}**\n\n")
                if heading:
                    f.write(f"{'#' * (int(hl[1]) + 1)} {heading}\n\n")
                for sub in section.get("headings", []):
                    sl = sub.get("level", "h3")
                    if sub.get("text"):
                        f.write(f"{'#' * (int(sl[1]) + 1)} {sub['text']}\n\n")
                if section.get("text"):
                    f.write(f"{section['text']}\n\n")
                if section.get("code_samples"):
                    f.write("### Code Examples\n\n")
                    for c in section["code_samples"]:
                        f.write(f"```{c.get('language', '')}\n{c['code']}\n```\n\n")
                if section.get("tables"):
                    f.write("### Tables\n\n")
                    for t in section["tables"]:
                        hdrs = t.get("headers", [])
                        if hdrs:
                            f.write("| " + " | ".join(str(h) for h in hdrs) + " |\n")
                            f.write("| " + " | ".join("---" for _ in hdrs) + " |\n")
                        for row in t.get("rows", []):
                            f.write("| " + " | ".join(str(c) for c in row) + " |\n")
                        f.write("\n")
                if section.get("admonitions"):
                    f.write("### Notes & Warnings\n\n")
                    for a in section["admonitions"]:
                        f.write(f"> **{a.get('type', 'NOTE')}:** {a.get('text', '')}\n\n")
                f.write("---\n\n")
        print(f"   Generated: {filename}")

    def _generate_index(self, categorized: dict) -> None:
        """Generate references/index.md."""
        filename = f"{self.skill_dir}/references/index.md"
        adoc_base = ""
        if self.asciidoc_path:
            p = Path(self.asciidoc_path)
            adoc_base = p.stem if p.is_file() else ""
        total = len(categorized)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {self.name.title()} Documentation Reference\n\n## Categories\n\n")
            for i, (_k, cd) in enumerate(categorized.items(), 1):
                pages = cd["pages"]
                cnt = len(pages)
                if pages:
                    nums = [s.get("section_number", j + 1) for j, s in enumerate(pages)]
                    rng = f"Sections {min(nums)}-{max(nums)}"
                    if total == 1:
                        lf = f"{adoc_base or 'main'}.md"
                    else:
                        lf = f"{adoc_base or 'section'}_s{min(nums)}-s{max(nums)}.md"
                else:
                    lf, rng = f"section_{i:02d}.md", "N/A"
                f.write(f"- [{cd['title']}]({lf}) ({cnt} sections, {rng})\n")

            f.write("\n## Statistics\n\n")
            for key, label in [
                ("total_sections", "Total sections"),
                ("total_code_blocks", "Code blocks"),
                ("total_tables", "Tables"),
                ("total_admonitions", "Admonitions"),
                ("total_files", "Source files"),
            ]:
                f.write(f"- {label}: {self.extracted_data.get(key, 0)}\n")
            meta = self.extracted_data.get("metadata", {})
            if meta.get("author"):
                f.write(f"- Author: {meta['author']}\n")
            if meta.get("date"):
                f.write(f"- Date: {meta['date']}\n")
        print(f"   Generated: {filename}")

    def _generate_skill_md(self, categorized: dict) -> None:
        """Generate main SKILL.md file with rich summary content."""
        filename = f"{self.skill_dir}/SKILL.md"
        skill_name = self.name.lower().replace("_", "-").replace(" ", "-")[:64]
        desc = self.description[:1024]
        ed = self.extracted_data  # shorthand

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"---\nname: {skill_name}\ndescription: {desc}\n---\n\n")
            f.write(f"# {self.name.title()} Documentation Skill\n\n{self.description}\n\n")

            # Document metadata
            meta = ed.get("metadata", {})
            if any(v for v in meta.values() if v):
                f.write("## 📋 Document Information\n\n")
                for key, label in [
                    ("title", "Title"),
                    ("author", "Author"),
                    ("revision", "Revision"),
                    ("date", "Date"),
                    ("description", "Description"),
                ]:
                    if meta.get(key):
                        f.write(f"**{label}:** {meta[key]}\n\n")

            f.write("## 💡 When to Use This Skill\n\nUse this skill when you need to:\n")
            f.write(f"- Understand {self.name} concepts and fundamentals\n")
            f.write("- Look up API references and technical specifications\n")
            f.write("- Find code examples and implementation patterns\n")
            f.write("- Review tutorials, guides, and best practices\n")
            f.write("- Explore the complete documentation structure\n\n")

            # Section Overview
            f.write(
                f"## 📖 Section Overview\n\n**Total Sections:** {ed.get('total_sections', 0)}\n\n"
            )
            f.write("**Content Breakdown:**\n\n")
            for cd in categorized.values():
                f.write(f"- **{cd['title']}**: {len(cd['pages'])} sections\n")
            f.write("\n")

            f.write(self._format_key_concepts())
            f.write("## ⚡ Quick Reference\n\n")
            f.write(self._format_patterns_from_content())

            # Code examples (top 15 grouped by language)
            all_code = [c for s in ed.get("pages", []) for c in s.get("code_samples", [])]
            all_code.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
            if all_code[:15]:
                f.write("## 📝 Code Examples\n\n*High-quality examples from documentation*\n\n")
                by_lang: dict[str, list] = {}
                for c in all_code[:15]:
                    by_lang.setdefault(c.get("language", "unknown"), []).append(c)
                for lang in sorted(by_lang):
                    exs = by_lang[lang]
                    f.write(f"### {lang.title()} Examples ({len(exs)})\n\n")
                    for i, c in enumerate(exs[:5], 1):
                        ct = c.get("code", "")
                        f.write(
                            f"**Example {i}** (Quality: {c.get('quality_score', 0):.1f}/10):\n\n"
                        )
                        f.write(f"```{lang}\n{ct[:500]}{'...' if len(ct) > 500 else ''}\n```\n\n")

            # Table summary
            all_tables = [
                (s.get("heading", ""), t) for s in ed.get("pages", []) for t in s.get("tables", [])
            ]
            if all_tables:
                f.write(f"## 📊 Table Summary\n\n*{len(all_tables)} table(s) found*\n\n")
                for sh, t in all_tables[:5]:
                    if sh:
                        f.write(f"**From section: {sh}**\n\n")
                    hdrs = t.get("headers", [])
                    if hdrs:
                        f.write("| " + " | ".join(str(h) for h in hdrs) + " |\n")
                        f.write("| " + " | ".join("---" for _ in hdrs) + " |\n")
                        for row in t.get("rows", [])[:5]:
                            f.write("| " + " | ".join(str(c) for c in row) + " |\n")
                        f.write("\n")

            # Admonition summary
            all_adm = [a for s in ed.get("pages", []) for a in s.get("admonitions", [])]
            if all_adm:
                f.write("## ⚠️ Admonition Summary\n\n")
                by_type: dict[str, list[str]] = {}
                for a in all_adm:
                    by_type.setdefault(a.get("type", "NOTE"), []).append(a.get("text", ""))
                for at in sorted(by_type):
                    items = by_type[at]
                    f.write(f"**{at}** ({len(items)}):\n\n")
                    for txt in items[:5]:
                        f.write(f"> {txt[:120]}{'...' if len(txt) > 120 else ''}\n\n")

            # Statistics
            f.write("## 📊 Documentation Statistics\n\n")
            for key, label in [
                ("total_sections", "Total Sections"),
                ("total_code_blocks", "Code Blocks"),
                ("total_tables", "Tables"),
                ("total_admonitions", "Admonitions"),
                ("total_files", "Source Files"),
            ]:
                f.write(f"- **{label}**: {ed.get(key, 0)}\n")
            langs = ed.get("languages_detected", {})
            if langs:
                f.write(f"- **Programming Languages**: {len(langs)}\n\n**Language Breakdown:**\n\n")
                for lang, count in sorted(langs.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- {lang}: {count} examples\n")
                f.write("\n")

            # Navigation
            f.write("## 🗺️ Navigation\n\n**Reference Files:**\n\n")
            for cd in categorized.values():
                cf = self._sanitize_filename(cd["title"])
                f.write(f"- `references/{cf}.md` - {cd['title']}\n")
            f.write("\nSee `references/index.md` for complete documentation structure.\n\n")
            f.write("---\n\n**Generated by Skill Seeker** | AsciiDoc Scraper\n")

        with open(filename, encoding="utf-8") as f:
            print(f"   Generated: {filename} ({len(f.read().splitlines())} lines)")

    # ------------------------------------------------------------------
    # Content analysis helpers
    # ------------------------------------------------------------------

    def _format_key_concepts(self) -> str:
        """Extract key concepts from headings across all sections."""
        all_h: list[tuple[str, str]] = []
        for s in self.extracted_data.get("pages", []):
            h = s.get("heading", "").strip()
            if h and len(h) > 3:
                all_h.append((s.get("heading_level", "h1"), h))
            for sub in s.get("headings", []):
                t = sub.get("text", "").strip()
                if t and len(t) > 3:
                    all_h.append((sub.get("level", "h3"), t))
        if not all_h:
            return ""
        content = "## 🔑 Key Concepts\n\n*Main topics covered in this documentation*\n\n"
        h1s = [t for lv, t in all_h if lv == "h1"]
        h2s = [t for lv, t in all_h if lv == "h2"]
        if h1s:
            content += "**Major Topics:**\n\n" + "".join(f"- {h}\n" for h in h1s[:10]) + "\n"
        if h2s:
            content += "**Subtopics:**\n\n" + "".join(f"- {h}\n" for h in h2s[:15]) + "\n"
        return content

    def _format_patterns_from_content(self) -> str:
        """Extract common documentation patterns from section headings."""
        keywords = [
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
        patterns: list[dict] = []
        for s in self.extracted_data.get("pages", []):
            ht = s.get("heading", "").lower()
            for kw in keywords:
                if kw in ht:
                    patterns.append(
                        {
                            "type": kw.title(),
                            "heading": s.get("heading", ""),
                            "section": s.get("section_number", 0),
                        }
                    )
                    break
        if not patterns:
            return "*See reference files for detailed content*\n\n"
        by_type: dict[str, list] = {}
        for p in patterns:
            by_type.setdefault(p["type"], []).append(p)
        content = "*Common documentation patterns found:*\n\n"
        for pt in sorted(by_type):
            items = by_type[pt]
            content += f"**{pt}** ({len(items)} sections):\n"
            content += "".join(f"- {it['heading']} (section {it['section']})\n" for it in items[:3])
            content += "\n"
        return content

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Convert name to a safe filename slug."""
        safe = re.sub(r"[^\w\s-]", "", name.lower())
        return re.sub(r"[-\s]+", "_", safe)

    @staticmethod
    def _in_range(pos: int, ranges: list[tuple[int, int]]) -> bool:
        """Check whether pos falls within any consumed range."""
        return any(s <= pos < e for s, e in ranges)


# ============================================================================
# CLI entry point
# ============================================================================


def main() -> int:
    """CLI entry point for AsciiDoc scraper."""
    from skill_seekers.cli.arguments.asciidoc import add_asciidoc_arguments

    parser = argparse.ArgumentParser(
        description="Convert AsciiDoc documentation to skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    add_asciidoc_arguments(parser)

    args = parser.parse_args()

    # Set logging level
    if getattr(args, "quiet", False):
        logging.getLogger().setLevel(logging.WARNING)
    elif getattr(args, "verbose", False):
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle --dry-run
    if getattr(args, "dry_run", False):
        source = (
            getattr(args, "asciidoc_path", None) or getattr(args, "from_json", None) or "(none)"
        )
        print(f"\n{'=' * 60}")
        print("DRY RUN: AsciiDoc Extraction")
        print(f"{'=' * 60}")
        print(f"Source:         {source}")
        print(f"Name:           {getattr(args, 'name', None) or '(auto-detect)'}")
        print(f"Enhance level:  {getattr(args, 'enhance_level', 0)}")
        print(f"\n✅ Dry run complete")
        return 0

    # Validate inputs
    if not (getattr(args, "asciidoc_path", None) or getattr(args, "from_json", None)):
        parser.error("Must specify --asciidoc-path or --from-json")

    # Build from JSON workflow
    if getattr(args, "from_json", None):
        name = Path(args.from_json).stem.replace("_extracted", "")
        config = {
            "name": getattr(args, "name", None) or name,
            "description": getattr(args, "description", None)
            or f"Use when referencing {name} documentation",
        }
        try:
            converter = AsciiDocToSkillConverter(config)
            converter.load_extracted_data(args.from_json)
            converter.build_skill()
        except Exception as e:
            print(f"\n❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
        return 0

    # Direct AsciiDoc mode
    if not getattr(args, "name", None):
        p = Path(args.asciidoc_path)
        args.name = p.stem if p.is_file() else p.name

    config = {
        "name": args.name,
        "asciidoc_path": args.asciidoc_path,
        "description": getattr(args, "description", None),
    }

    try:
        converter = AsciiDocToSkillConverter(config)

        # Extract
        if not converter.extract_asciidoc():
            print("\n❌ AsciiDoc extraction failed - see error above", file=sys.stderr)
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

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during AsciiDoc processing: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
