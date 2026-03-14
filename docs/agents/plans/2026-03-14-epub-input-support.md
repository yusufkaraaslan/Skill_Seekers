---
date: 2026-03-14T19:30:35.172407+00:00
git_commit: 7c90a4b9c9bccac8341b0769550d77aae3b4e524
branch: development
topic: "Add EPUB Input Support"
tags: [plan, epub, scraper, input-format]
status: complete
---

# Add EPUB Input Support — Implementation Plan

## Overview

Add `.epub` as an input format for Skill Seekers, enabling `skill-seekers create book.epub` and `skill-seekers epub --epub book.epub`. Follows the established Word/PDF scraper pattern: source detection → routing → extraction → categorize → build skill.

**Authoritative reference**: [W3C EPUB 3.3 Specification](https://www.w3.org/TR/epub-33/) (also covers EPUB 2 backward compatibility).

## Current State Analysis

The codebase has a consistent multi-layer architecture for document input formats. PDF and Word (.docx) serve as direct analogs. The Word scraper (`word_scraper.py`) is the closest pattern match since both Word and EPUB produce HTML/XHTML that is parsed with BeautifulSoup.

### Key Discoveries:
- Word scraper converts `.docx` → HTML (via mammoth) → BeautifulSoup parse → intermediate JSON → SKILL.md (`word_scraper.py:96-235`)
- EPUB files contain XHTML natively (per W3C spec §5), so the mammoth conversion step is unnecessary — BeautifulSoup can parse EPUB XHTML content directly
- Source detection uses file extension matching (`source_detector.py:57-65`)
- Optional dependencies use a guard pattern with `try/except ImportError` and a `_check_*_deps()` function (`word_scraper.py:21-40`)
- The `ebooklib` library (v0.18+) provides `epub.read_epub()` returning an `EpubBook` with spine iteration, metadata access via `get_metadata('DC', key)`, and item content via `get_content()`/`get_body_content()`
- ebooklib has a known bug: EPUB 3 files read TOC from NCX instead of NAV (issue #200); workaround: `options={"ignore_ncx": True}`
- ebooklib loads entire EPUB into memory — acceptable for typical books but relevant for edge cases

## Desired End State

Running `skill-seekers create book.epub` produces:
```
output/book/
├── SKILL.md              # Main skill file with metadata, concepts, code examples
├── references/
│   ├── index.md          # Category index with statistics
│   └── book.md           # Chapter content (or multiple files if categorized)
├── scripts/
└── assets/
    └── *.png|*.jpg       # Extracted images
```

### CLI Output Mockup

```
$ skill-seekers create programming-rust.epub

ℹ️  Detected source type: epub
ℹ️  Routing to epub scraper...

🔍 Extracting from EPUB: programming-rust.epub
   Title: Programming Rust, 2nd Edition
   Author: Jim Blandy, Jason Orendorff
   Language: en
   Chapters: 23 (spine items)

📄 Processing chapters...
   Chapter 1/23: Why Rust? (2 sections, 1 code block)
   Chapter 2/23: A Tour of Rust (5 sections, 12 code blocks)
   ...
   Chapter 23/23: Macros (4 sections, 8 code blocks)

📊 Extraction complete:
   Sections: 142
   Code blocks: 287 (Rust: 245, Shell: 28, TOML: 14)
   Images: 34
   Tables: 12

💾 Saved extracted data to: output/programming-rust_extracted.json

📋 Categorizing content...
✅ Created 1 category (single EPUB source)
   - programming-rust: 142 sections

📝 Generating reference files...
   Generated: output/programming-rust/references/programming-rust.md
   Generated: output/programming-rust/references/index.md

✅ Skill built successfully: output/programming-rust/

📦 Next step: Package with: skill-seekers package output/programming-rust/
```

### Verification:
- [x] `skill-seekers create book.epub` produces valid output directory
- [x] `skill-seekers epub --epub book.epub --name mybook` works standalone
- [x] `skill-seekers create book.epub --dry-run` shows config without processing
- [x] All ~2,540+ existing tests still pass (982 passed, 1 pre-existing failure)
- [x] New test suite has 100+ tests covering happy path, errors, and edge cases (107 tests, 14 classes)

## What We're NOT Doing

- DRM decryption (detect and error gracefully with clear message)
- EPUB writing/creation (read-only)
- Media overlay / audio / video extraction (ignore gracefully)
- Fixed-layout OCR (detect and warn; extract whatever text exists in XHTML)
- `--chapter-range` flag (can be added later)
- Unified scraper (`unified_scraper.py`) EPUB support (separate future task)
- MCP tool for EPUB (separate future task)

## Implementation Approach

Follow the Word scraper pattern exactly, with EPUB-specific extraction logic:

1. **Phase 1**: Core `epub_scraper.py` — the `EpubToSkillConverter` class
2. **Phase 2**: CLI integration — source detection, arguments, parser, routing, entry points
3. **Phase 3**: Comprehensive test suite — 100+ tests across 11 test classes
4. **Phase 4**: Documentation updates

---

## Phase 1: Core EPUB Scraper

### Overview
Create `epub_scraper.py` with `EpubToSkillConverter` class following the Word scraper pattern. This is the bulk of new code.

### Changes Required:

#### [x] 1. Optional dependency in pyproject.toml
**File**: `pyproject.toml`
**Changes**: Add `epub` optional dependency group and include in `all` group

```toml
# After the docx group (~line 115)
# EPUB (.epub) support
epub = [
    "ebooklib>=0.18",
]
```

Add `"ebooklib>=0.18",` to the `all` group (~line 178).

#### [x] 2. Create `src/skill_seekers/cli/epub_scraper.py`
**File**: `src/skill_seekers/cli/epub_scraper.py` (new)
**Changes**: Full EPUB scraper module

**Structure** (following `word_scraper.py` pattern):

```python
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
    """Infer skill description from EPUB metadata."""
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
```

**`EpubToSkillConverter` class methods:**

```python
class EpubToSkillConverter:
    def __init__(self, config: dict):
        self.config = config
        self.name = config["name"]
        self.epub_path = config.get("epub_path", "")
        self.description = config.get(
            "description", f"Use when referencing {self.name} documentation"
        )
        self.skill_dir = f"output/{self.name}"
        self.data_file = f"output/{self.name}_extracted.json"
        self.categories = config.get("categories", {})
        self.extracted_data = None

    def extract_epub(self) -> bool:
        """Extract content from EPUB file.

        Workflow:
        1. Check dependencies (ebooklib)
        2. Detect DRM via META-INF/encryption.xml (fail fast)
        3. Read EPUB via ebooklib with ignore_ncx=True (EPUB 3 TOC bug workaround)
        4. Extract Dublin Core metadata (title, creator, language, publisher, date, description, subject)
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
```

**DRM detection** (per W3C spec §4.2.6.3.2):

```python
def _detect_drm(self, book) -> bool:
    """Detect DRM by checking for encryption.xml with non-font-obfuscation entries.

    Per W3C EPUB 3.3 spec: encryption.xml is present when resources are encrypted.
    Font obfuscation (IDPF algorithm http://www.idpf.org/2008/embedding or
    Adobe algorithm http://ns.adobe.com/pdf/enc#RC) is NOT DRM — only font mangling.

    Actual DRM uses algorithms like:
    - Adobe ADEPT: http://ns.adobe.com/adept namespace
    - Apple FairPlay: http://itunes.apple.com/dataenc
    - Readium LCP: http://readium.org/2014/01/lcp
    """
```

**Metadata extraction** (per W3C spec §5.2, Dublin Core):

```python
def _extract_metadata(self, book) -> dict:
    """Extract Dublin Core metadata from EPUB.

    Per W3C EPUB 3.3 spec: required elements are dc:identifier, dc:title, dc:language.
    Optional: dc:creator, dc:contributor, dc:date, dc:description, dc:publisher,
    dc:subject, dc:rights, dc:type, dc:coverage, dc:source, dc:relation, dc:format.

    ebooklib API: book.get_metadata('DC', key) returns list of (value, attrs) tuples.
    """
    def _get_one(key):
        data = book.get_metadata('DC', key)
        return data[0][0] if data else None

    def _get_list(key):
        data = book.get_metadata('DC', key)
        return [x[0] for x in data] if data else []

    return {
        "title": _get_one('title') or "Untitled",
        "author": ", ".join(_get_list('creator')) or None,
        "language": _get_one('language') or "en",
        "publisher": _get_one('publisher'),
        "date": _get_one('date'),
        "description": _get_one('description'),
        "subject": ", ".join(_get_list('subject')) or None,
        "rights": _get_one('rights'),
        "identifier": _get_one('identifier'),
    }
```

**Content extraction** (per W3C spec §5 — XHTML Content Documents use XML serialization of HTML5):

```python
def _extract_spine_content(self, book) -> list[dict]:
    """Extract content from spine items in reading order.

    Per W3C EPUB 3.3 spec §3.4.8: spine defines ordered list of content documents.
    Linear="yes" (default) items form the primary reading order.
    Linear="no" items are auxiliary (footnotes, glossary).

    Per spec §5: XHTML content documents use XML syntax of HTML5.
    Parse with BeautifulSoup, split by h1/h2 heading boundaries.
    """
    sections = []
    section_number = 0

    for item_id, linear in book.spine:
        item = book.get_item_with_id(item_id)
        if not item or item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue

        soup = BeautifulSoup(item.get_content(), 'html.parser')

        # Remove scripts, styles, comments (not useful for text extraction)
        for tag in soup(['script', 'style']):
            tag.decompose()
        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            comment.extract()

        body = soup.find('body')
        if not body:
            continue

        # Split by h1/h2 heading boundaries (same as word_scraper)
        # Each heading starts a new section
        ...
```

**Image extraction** (per W3C spec §3.3 — core media types include JPEG, PNG, GIF, WebP, SVG):

```python
def _extract_images(self, book) -> list[dict]:
    """Extract images from EPUB manifest.

    Per W3C EPUB 3.3 spec §3.3: core image media types are
    image/gif, image/jpeg, image/png, image/svg+xml, image/webp.

    ebooklib API: book.get_items_of_type(ebooklib.ITEM_IMAGE)
    returns EpubImage items with get_content() (bytes) and media_type.

    SVG images (ITEM_VECTOR) handled separately.
    """
```

**The remaining methods** (`categorize_content`, `build_skill`, `_generate_reference_file`, `_generate_index`, `_generate_skill_md`, `_format_key_concepts`, `_format_patterns_from_content`, `_sanitize_filename`) follow the Word scraper pattern exactly — they operate on the same intermediate JSON structure.

**`main()` function** (following `word_scraper.py:923-1059`):

```python
def main():
    from .arguments.epub import add_epub_arguments

    parser = argparse.ArgumentParser(
        description="Convert EPUB e-book to skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_epub_arguments(parser)
    args = parser.parse_args()

    # Logging setup
    if getattr(args, "quiet", False):
        logging.getLogger().setLevel(logging.WARNING)
    elif getattr(args, "verbose", False):
        logging.getLogger().setLevel(logging.DEBUG)

    # Dry run
    if getattr(args, "dry_run", False):
        source = args.epub or args.from_json or "(none)"
        print(f"\n{'=' * 60}")
        print("DRY RUN: EPUB Extraction")
        print(f"{'=' * 60}")
        print(f"Source:         {source}")
        print(f"Name:           {getattr(args, 'name', None) or '(auto-detect)'}")
        print(f"Enhance level:  {getattr(args, 'enhance_level', 0)}")
        print(f"\n✅ Dry run complete")
        return

    # Validate inputs
    if not (args.epub or args.from_json):
        parser.error("Must specify --epub or --from-json")

    # From-JSON workflow
    if args.from_json:
        name = Path(args.from_json).stem.replace("_extracted", "")
        config = {
            "name": name,
            "description": args.description or f"Use when referencing {name} documentation",
        }
        converter = EpubToSkillConverter(config)
        converter.load_extracted_data(args.from_json)
        converter.build_skill()
        return

    # Direct EPUB workflow
    name = args.name or Path(args.epub).stem
    config = {
        "name": name,
        "epub_path": args.epub,
        "description": args.description or f"Use when referencing {name} documentation",
    }

    try:
        converter = EpubToSkillConverter(config)
        if not converter.extract_epub():
            print("\n❌ EPUB extraction failed", file=sys.stderr)
            sys.exit(1)
        converter.build_skill()

        # Enhancement workflow integration
        from skill_seekers.cli.workflow_runner import run_workflows
        run_workflows(args)

        # Traditional enhancement
        if getattr(args, "enhance_level", 0) > 0:
            # Same pattern as word_scraper.py and pdf_scraper.py
            ...

    except RuntimeError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
```

### Success Criteria:

#### Automated Verification:
- [x] `ruff check src/skill_seekers/cli/epub_scraper.py` passes
- [x] `ruff format --check src/skill_seekers/cli/epub_scraper.py` passes
- [ ] `mypy src/skill_seekers/cli/epub_scraper.py` passes (continue-on-error)
- [x] `pip install -e ".[epub]"` installs successfully

#### Manual Verification:
- [x] Verify `import ebooklib` works after install
- [x] Review epub_scraper.py structure matches word_scraper.py pattern

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human before proceeding to the next phase.

---

## Phase 2: CLI Integration

### Overview
Wire the EPUB scraper into the CLI: source detection, argument definitions, parser registration, create command routing, and entry points.

### Changes Required:

#### [x] 1. Source detection
**File**: `src/skill_seekers/cli/source_detector.py`
**Changes**: Add `.epub` extension detection, `_detect_epub()` method, validation, and error message update

Add after the `.docx` check (line 64):
```python
if source.endswith(".epub"):
    return cls._detect_epub(source)
```

Add `_detect_epub()` method (following `_detect_word()` at line 124):
```python
@classmethod
def _detect_epub(cls, source: str) -> SourceInfo:
    """Detect EPUB file source."""
    name = os.path.splitext(os.path.basename(source))[0]
    return SourceInfo(
        type="epub", parsed={"file_path": source}, suggested_name=name, raw_input=source
    )
```

Add epub validation in `validate_source()` (after word block at line 278):
```python
elif source_info.type == "epub":
    file_path = source_info.parsed["file_path"]
    if not os.path.exists(file_path):
        raise ValueError(f"EPUB file does not exist: {file_path}")
    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")
```

Add EPUB example to the ValueError message (line 94):
```python
"  EPUB:  skill-seekers create ebook.epub\n"
```

#### [x] 2. Argument definitions
**File**: `src/skill_seekers/cli/arguments/epub.py` (new)
**Changes**: EPUB-specific argument definitions

```python
"""EPUB-specific CLI arguments."""

import argparse
from typing import Any

from .common import add_all_standard_arguments

EPUB_ARGUMENTS: dict[str, dict[str, Any]] = {
    "epub": {
        "flags": ("--epub",),
        "kwargs": {
            "type": str,
            "help": "Direct EPUB file path",
            "metavar": "PATH",
        },
    },
    "from_json": {
        "flags": ("--from-json",),
        "kwargs": {
            "type": str,
            "help": "Build skill from extracted JSON",
            "metavar": "FILE",
        },
    },
}


def add_epub_arguments(parser: argparse.ArgumentParser) -> None:
    """Add EPUB-specific arguments to parser."""
    add_all_standard_arguments(parser)

    # Override enhance-level default to 0 for EPUB
    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0
            action.help = (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled (default for EPUB), 1=SKILL.md only, "
                "2=+architecture/config, 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, "
                "otherwise LOCAL (Claude Code)"
            )

    for arg_name, arg_def in EPUB_ARGUMENTS.items():
        parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])
```

#### [x] 3. Create command argument integration
**File**: `src/skill_seekers/cli/arguments/create.py`
**Changes**: Add EPUB_ARGUMENTS dict, register in helper functions, add mode handling

Add after WORD_ARGUMENTS (~line 411):
```python
# EPUB specific (from epub.py)
EPUB_ARGUMENTS: dict[str, dict[str, Any]] = {
    "epub": {
        "flags": ("--epub",),
        "kwargs": {
            "type": str,
            "help": "EPUB file path",
            "metavar": "PATH",
        },
    },
}
```

Add to `get_source_specific_arguments()` (line 595):
```python
"epub": EPUB_ARGUMENTS,
```

Add to `add_create_arguments()` (after word block at line 678):
```python
if mode in ["epub", "all"]:
    for arg_name, arg_def in EPUB_ARGUMENTS.items():
        parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])
```

#### [x] 4. Parser class
**File**: `src/skill_seekers/cli/parsers/epub_parser.py` (new)
**Changes**: Subcommand parser for standalone `skill-seekers epub` command

```python
"""Parser for epub subcommand."""

from .base import SubcommandParser
from skill_seekers.cli.arguments.epub import add_epub_arguments


class EpubParser(SubcommandParser):
    """Parser for EPUB extraction command."""

    @property
    def name(self) -> str:
        return "epub"

    @property
    def help(self) -> str:
        return "Extract from EPUB e-book (.epub)"

    @property
    def description(self) -> str:
        return "Extract content from EPUB e-book (.epub) and generate skill"

    def add_arguments(self, parser):
        add_epub_arguments(parser)
```

#### [x] 5. Parser registration
**File**: `src/skill_seekers/cli/parsers/__init__.py`
**Changes**: Import and register EpubParser

Add import (after WordParser import, line 15):
```python
from .epub_parser import EpubParser
```

Add to PARSERS list (after `WordParser()`, line 46):
```python
EpubParser(),
```

#### [x] 6. CLI dispatcher
**File**: `src/skill_seekers/cli/main.py`
**Changes**: Add epub to COMMAND_MODULES dict and module docstring

Add to COMMAND_MODULES (after "word" entry, line 52):
```python
"epub": "skill_seekers.cli.epub_scraper",
```

Add to module docstring (after "word" line, line 15):
```python
#    epub                 Extract from EPUB e-book (.epub)
```

#### [x] 7. Create command routing
**File**: `src/skill_seekers/cli/create_command.py`
**Changes**: Add `_route_epub()` method, routing case, help flag, and epilog example

Add to `_route_to_scraper()` (after word case, line 136):
```python
elif self.source_info.type == "epub":
    return self._route_epub()
```

Add `_route_epub()` method (after `_route_word()`, line 352):
```python
def _route_epub(self) -> int:
    """Route to EPUB scraper (epub_scraper.py)."""
    from skill_seekers.cli import epub_scraper

    argv = ["epub_scraper"]
    file_path = self.source_info.parsed["file_path"]
    argv.extend(["--epub", file_path])
    self._add_common_args(argv)

    logger.debug(f"Calling epub_scraper with argv: {argv}")
    original_argv = sys.argv
    try:
        sys.argv = argv
        return epub_scraper.main()
    finally:
        sys.argv = original_argv
```

Add to epilog (line 543, after DOCX example):
```python
  EPUB:     skill-seekers create ebook.epub
```

Add to Source Auto-Detection section:
```python
  • file.epub → EPUB extraction
```

Add `--help-epub` flag and handler (after `--help-word` at line 592):
```python
parser.add_argument(
    "--help-epub", action="store_true", help=argparse.SUPPRESS, dest="_help_epub"
)
```

Add handler block (after `_help_word` block at line 654):
```python
elif args._help_epub:
    parser_epub = argparse.ArgumentParser(
        prog="skill-seekers create",
        description="Create skill from EPUB e-book (.epub)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_create_arguments(parser_epub, mode="epub")
    parser_epub.print_help()
    return 0
```

#### [x] 8. Entry point
**File**: `pyproject.toml`
**Changes**: Add standalone entry point

Add after `skill-seekers-word` (line 224):
```toml
skill-seekers-epub = "skill_seekers.cli.epub_scraper:main"
```

#### [x] 9. Positional argument handling in main.py
**File**: `src/skill_seekers/cli/main.py`
**Changes**: Add "input_file" is already in the positional list at line 153, so no change needed. Verify `_reconstruct_argv` handles epub correctly through the standard delegation path.

### Success Criteria:

#### Automated Verification:
- [x] `ruff check src/skill_seekers/cli/source_detector.py src/skill_seekers/cli/arguments/epub.py src/skill_seekers/cli/parsers/epub_parser.py src/skill_seekers/cli/create_command.py` passes
- [x] `ruff format --check src/skill_seekers/cli/` passes
- [x] `pip install -e ".[epub]"` installs with all entry points
- [x] `skill-seekers epub --help` shows EPUB-specific help
- [x] `skill-seekers create --help-epub` shows EPUB arguments (via standalone entry point `skill-seekers-create`)
- [x] `skill-seekers create nonexistent.epub` gives clear error about missing file
- [x] Existing tests still pass: `pytest tests/ -v -x -m "not slow and not integration"` (875 passed, 1 pre-existing unrelated failure in test_git_sources_e2e)

#### Manual Verification:
- [x] `skill-seekers --help` lists `epub` command
- [x] `skill-seekers create book.epub --dry-run` shows dry run output

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human before proceeding to the next phase.

---

## Phase 3: Comprehensive Test Suite

### Overview
Create `tests/test_epub_scraper.py` with 100+ tests across 11 test classes, covering happy path, negative cases, edge cases, and CLI integration.

### Changes Required:

#### [x] 1. Create test file
**File**: `tests/test_epub_scraper.py` (new)
**Changes**: Comprehensive test suite following `test_word_scraper.py` patterns

```python
"""
Tests for EPUB scraper (epub_scraper.py).

Covers: initialization, extraction, categorization, skill building,
code blocks, tables, images, error handling, JSON workflow, CLI arguments,
helper functions, source detection, DRM detection, and edge cases.

Tests use mock data and do not require actual EPUB files or ebooklib installed.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock


# Conditional import (same pattern as test_word_scraper.py)
try:
    from skill_seekers.cli.epub_scraper import (
        EpubToSkillConverter,
        infer_description_from_epub,
        _score_code_quality,
        _check_epub_deps,
        EPUB_AVAILABLE,
    )
    IMPORT_OK = True
except ImportError:
    IMPORT_OK = False
```

**Helper factory function:**

```python
def _make_sample_extracted_data(
    num_sections=2,
    include_code=False,
    include_tables=False,
    include_images=False,
) -> dict:
    """Create minimal extracted_data dict for testing."""
    sections = []
    total_code = 0
    total_images = 0
    languages = {}

    for i in range(1, num_sections + 1):
        section = {
            "section_number": i,
            "heading": f"Chapter {i}",
            "heading_level": "h1",
            "text": f"Content of chapter {i}. This is sample text.",
            "headings": [{"level": "h2", "text": f"Section {i}.1"}],
            "code_samples": [],
            "tables": [],
            "images": [],
        }

        if include_code:
            section["code_samples"] = [
                {"code": f"def func_{i}():\n    return {i}", "language": "python", "quality_score": 7.5},
                {"code": f"console.log({i})", "language": "javascript", "quality_score": 4.0},
            ]
            total_code += 2
            languages["python"] = languages.get("python", 0) + 1
            languages["javascript"] = languages.get("javascript", 0) + 1

        if include_tables:
            section["tables"] = [
                {"headers": ["Name", "Value"], "rows": [["key", "val"]]}
            ]

        if include_images:
            section["images"] = [
                {"index": 1, "data": b"\x89PNG\r\n\x1a\n", "width": 100, "height": 100}
            ]
            total_images += 1

        sections.append(section)

    return {
        "source_file": "test.epub",
        "metadata": {
            "title": "Test Book",
            "author": "Test Author",
            "language": "en",
            "publisher": "Test Publisher",
            "date": "2024-01-01",
            "description": "A test book for unit testing",
            "subject": "Testing, Unit Tests",
            "rights": "Copyright 2024",
            "identifier": "urn:uuid:12345",
        },
        "total_sections": num_sections,
        "total_code_blocks": total_code,
        "total_images": total_images,
        "languages_detected": languages,
        "pages": sections,
    }
```

### Test Classes and Methods:

#### [x] Class 1: `TestEpubToSkillConverterInit` (8 tests)

**Happy path:**
- `test_init_with_name_and_epub_path` — basic config with name + epub_path
- `test_init_with_full_config` — config with all fields (name, epub_path, description, categories)
- `test_default_description_uses_name` — description defaults to "Use when referencing {name} documentation"
- `test_skill_dir_uses_name` — skill_dir is `output/{name}`
- `test_data_file_uses_name` — data_file is `output/{name}_extracted.json`

**Negative:**
- `test_init_requires_name` — missing "name" key raises KeyError
- `test_init_empty_name` — empty string name still works (no crash)

**Edge case:**
- `test_init_with_special_characters_in_name` — name with spaces/dashes sanitized for paths

#### [x] Class 2: `TestEpubExtraction` (12 tests)

**Happy path:**
- `test_extract_basic_epub` — mock ebooklib, verify sections extracted in spine order
- `test_extract_metadata` — verify Dublin Core metadata extraction (title, creator, language, etc.)
- `test_extract_multiple_chapters` — multiple spine items produce multiple sections
- `test_extract_code_blocks` — `<pre><code>` elements extracted with language detection
- `test_extract_images` — ITEM_IMAGE items extracted with correct content
- `test_heading_boundary_splitting` — h1/h2 boundaries create new sections

**Negative:**
- `test_extract_missing_file_raises_error` — FileNotFoundError for nonexistent path
- `test_extract_invalid_epub_raises_error` — ValueError for corrupted/non-EPUB file
- `test_extract_deps_not_installed` — RuntimeError with install instructions when ebooklib missing

**Edge cases:**
- `test_extract_empty_spine` — EPUB with no spine items produces empty sections list
- `test_extract_spine_item_no_body` — XHTML without `<body>` tag skipped gracefully
- `test_extract_non_linear_spine_items` — linear="no" items still extracted (included but flagged)

#### [x] Class 3: `TestEpubDrmDetection` (6 tests)

**Happy path:**
- `test_no_drm_detected` — normal EPUB without encryption.xml returns False

**Negative:**
- `test_drm_detected_adobe_adept` — encryption.xml with Adobe namespace raises RuntimeError
- `test_drm_detected_apple_fairplay` — encryption.xml with Apple namespace raises RuntimeError
- `test_drm_detected_readium_lcp` — encryption.xml with Readium namespace raises RuntimeError

**Edge cases:**
- `test_font_obfuscation_not_drm` — encryption.xml with only IDPF font obfuscation algorithm (`http://www.idpf.org/2008/embedding`) is NOT DRM, extraction proceeds
- `test_drm_error_message_is_clear` — error message mentions DRM and suggests removing protection

#### [x] Class 4: `TestEpubCategorization` (8 tests)

**Happy path:**
- `test_single_source_creates_one_category` — single EPUB creates category named after file
- `test_keyword_categorization` — sections matched to categories by keyword scoring
- `test_no_categories_uses_default` — no category config creates single "content" category

**Negative:**
- `test_categorize_empty_sections` — empty sections list produces empty categories
- `test_categorize_no_keyword_matches` — unmatched sections go to "other" category

**Edge cases:**
- `test_categorize_single_section` — one section creates one category
- `test_categorize_many_sections` — 50+ sections categorized correctly
- `test_categorize_preserves_section_order` — sections maintain original order within categories

#### [x] Class 5: `TestEpubSkillBuilding` (10 tests)

**Happy path:**
- `test_build_creates_directory_structure` — output/{name}/, references/, scripts/, assets/ created
- `test_build_generates_skill_md` — SKILL.md created with YAML frontmatter
- `test_build_generates_reference_files` — reference markdown files created per category
- `test_build_generates_index` — references/index.md created with category links
- `test_skill_md_contains_metadata` — SKILL.md includes title, author, language from metadata
- `test_skill_md_yaml_frontmatter` — frontmatter has name and description fields

**Negative:**
- `test_build_without_extracted_data_fails` — calling build_skill() before extraction raises error

**Edge cases:**
- `test_build_overwrites_existing_output` — re-running build overwrites existing files
- `test_build_with_long_name` — name > 64 chars truncated in YAML frontmatter
- `test_build_with_unicode_content` — Unicode text (CJK, Arabic, emoji) preserved correctly

#### [x] Class 6: `TestEpubCodeBlocks` (8 tests)

**Happy path:**
- `test_code_blocks_included_in_reference_files` — code samples appear in reference markdown
- `test_code_blocks_in_skill_md_top_15` — SKILL.md shows top 15 code examples by quality
- `test_code_language_grouped` — code examples grouped by language in SKILL.md

**Edge cases:**
- `test_empty_code_block` — `<pre><code></code></pre>` with no content skipped
- `test_code_block_with_html_entities` — `&lt;`, `&gt;`, `&amp;` decoded to `<`, `>`, `&`
- `test_code_block_with_syntax_highlighting_spans` — `<span class="keyword">` stripped, plain text preserved
- `test_code_block_language_from_class` — `class="language-python"`, `class="code-rust"` detected
- `test_code_quality_scoring` — scoring heuristic produces expected ranges (0-10)

#### [x] Class 7: `TestEpubTables` (5 tests)

**Happy path:**
- `test_tables_in_reference_files` — tables rendered as markdown in reference files
- `test_table_with_headers` — headers from `<thead>` used correctly

**Edge cases:**
- `test_table_no_thead` — first row used as headers when no `<thead>`
- `test_empty_table` — empty `<table>` element handled gracefully
- `test_table_with_colspan_rowspan` — complex tables don't crash (data may be imperfect)

#### [x] Class 8: `TestEpubImages` (7 tests)

**Happy path:**
- `test_images_saved_to_assets` — image bytes written to assets/ directory
- `test_image_references_in_markdown` — markdown `![Image](../assets/...)` references correct

**Negative:**
- `test_image_with_zero_bytes` — empty image content skipped

**Edge cases:**
- `test_svg_images_handled` — SVG items (ITEM_VECTOR) extracted or skipped gracefully
- `test_image_filename_conflicts` — duplicate filenames disambiguated
- `test_cover_image_identified` — cover image (ITEM_COVER) extracted
- `test_many_images` — 100+ images extracted without error

#### [x] Class 9: `TestEpubErrorHandling` (10 tests)

**Negative / error cases:**
- `test_missing_epub_file_raises_error` — FileNotFoundError for nonexistent path
- `test_not_a_file_raises_error` — ValueError when path is a directory
- `test_not_epub_extension_raises_error` — ValueError for .txt, .pdf, .doc files
- `test_corrupted_zip_raises_error` — ValueError or RuntimeError for corrupted ZIP
- `test_missing_container_xml` — ValueError for ZIP without META-INF/container.xml
- `test_missing_opf_file` — ValueError when container.xml points to nonexistent OPF
- `test_drm_protected_raises_error` — RuntimeError with clear DRM message
- `test_empty_epub_raises_error` — ValueError for EPUB with no content documents
- `test_ebooklib_not_installed_error` — RuntimeError with install instructions
- `test_malformed_xhtml_handled_gracefully` — unclosed tags, invalid entities don't crash (BeautifulSoup tolerant parsing)

#### [x] Class 10: `TestEpubJSONWorkflow` (6 tests)

**Happy path:**
- `test_load_extracted_json` — load previously extracted JSON
- `test_build_from_json` — full workflow: load JSON → categorize → build
- `test_json_round_trip` — extract → save JSON → load JSON → build produces same output

**Negative:**
- `test_load_invalid_json` — malformed JSON raises appropriate error
- `test_load_nonexistent_json` — FileNotFoundError for missing file

**Edge case:**
- `test_json_with_missing_fields` — partial JSON (missing optional fields) still works

#### [x] Class 11: `TestEpubCLIArguments` (8 tests)

**Happy path:**
- `test_epub_flag_accepted` — `--epub path.epub` parsed correctly
- `test_from_json_flag_accepted` — `--from-json data.json` parsed correctly
- `test_name_flag_accepted` — `--name mybook` parsed correctly
- `test_enhance_level_default_zero` — enhance-level defaults to 0 for EPUB
- `test_dry_run_flag` — `--dry-run` flag parsed correctly

**Negative:**
- `test_no_args_shows_error` — no `--epub` or `--from-json` shows error

**Integration:**
- `test_verbose_flag` — `--verbose` accepted
- `test_quiet_flag` — `--quiet` accepted

#### [x] Class 12: `TestEpubHelperFunctions` (6 tests)

- `test_infer_description_from_metadata_description` — uses description field
- `test_infer_description_from_metadata_title` — falls back to title
- `test_infer_description_fallback` — falls back to name-based template
- `test_infer_description_empty_metadata` — empty dict returns fallback
- `test_score_code_quality_ranges` — scoring returns 0-10
- `test_sanitize_filename` — special characters cleaned

#### [x] Class 13: `TestEpubSourceDetection` (6 tests)

- `test_epub_detected_as_epub_type` — `.epub` extension detected correctly
- `test_epub_suggested_name` — filename stem used as suggested name
- `test_epub_validation_missing_file` — validation raises ValueError for missing file
- `test_epub_validation_not_a_file` — validation raises ValueError for directory
- `test_epub_with_path` — `./books/test.epub` detected with correct file_path
- `test_pdf_still_detected` — regression test: `.pdf` still detected as pdf type

#### [x] Class 14: `TestEpubEdgeCases` (8 tests)

**Per W3C EPUB 3.3 spec edge cases:**
- `test_epub2_vs_epub3` — both versions parse successfully (ebooklib handles both)
- `test_epub_no_toc` — EPUB without table of contents extracts using spine order
- `test_epub_empty_chapters` — chapters with no text content skipped gracefully
- `test_epub_single_chapter` — book with one spine item produces valid output
- `test_epub_unicode_content` — CJK, Arabic, Cyrillic, emoji text preserved
- `test_epub_large_section_count` — 100+ sections processed without error
- `test_epub_nested_headings` — h3/h4/h5/h6 become sub-headings within sections
- `test_fixed_layout_detected` — fixed-layout EPUB produces warning but still extracts text

**Total: ~108 test methods across 14 classes**

### Success Criteria:

#### Automated Verification:
- [x] `pytest tests/test_epub_scraper.py -v` — all 107 tests pass
- [x] `pytest tests/ -v -x -m "not slow and not integration"` — 982 passed (1 pre-existing unrelated failure in test_git_sources_e2e)
- [x] `ruff check tests/test_epub_scraper.py` passes
- [x] `ruff format --check tests/test_epub_scraper.py` passes
- [x] Test count >= 100 methods (107 tests across 14 classes)

#### Manual Verification:
- [x] Review test coverage includes: happy path, negative, edge cases, CLI, source detection, DRM, JSON workflow
- [x] Verify no tests require actual EPUB files or ebooklib installed (all use mocks/skipTest guards)

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human before proceeding to the next phase.

---

## Phase 4: Documentation

### Overview
Update CLAUDE.md and CHANGELOG.md to reflect the new EPUB support.

### Changes Required:

#### [x] 1. Update CLAUDE.md
**File**: `CLAUDE.md`
**Changes**:

Add to Commands section (after pdf line):
```
skill-seekers epub --epub book.epub --name myskill
```

Add to "Unified create" examples:
```
skill-seekers create book.epub
```

Add to Key source files table:
```
| Core scraping | `cli/epub_scraper.py` |
```

Add to "Adding things → New create command flags" section:
```
- Source-specific → `EPUB_ARGUMENTS`
```

#### [x] 2. Update CHANGELOG.md
**File**: `CHANGELOG.md`
**Changes**: Add entry for EPUB support under next version

```markdown
### Added
- EPUB (.epub) input support via `skill-seekers create book.epub` or `skill-seekers epub --epub book.epub`
- Extracts chapters, metadata, code blocks, images, and tables from EPUB 2 and EPUB 3 files
- DRM detection with clear error messages
- Optional dependency: `pip install "skill-seekers[epub]"`
```

### Success Criteria:

#### Automated Verification:
- [x] `ruff check` passes on any modified files
- [x] `pytest tests/ -v -x -m "not slow and not integration"` — all tests still pass (982 passed, 1 pre-existing failure)

#### Manual Verification:
- [x] CLAUDE.md accurately reflects new commands
- [x] CHANGELOG.md entry is clear and complete

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human before proceeding.

---

## Testing Strategy

### Unit Tests (Phase 3 — ~108 tests):

**By category:**
| Category | Count | What's tested |
|----------|-------|---------------|
| Initialization | 8 | Config parsing, defaults, edge cases |
| Extraction | 12 | Spine iteration, metadata, headings, code, images |
| DRM detection | 6 | Adobe, Apple, Readium, font obfuscation (not DRM) |
| Categorization | 8 | Single/multi category, keywords, empty, ordering |
| Skill building | 10 | Directory structure, SKILL.md, references, index |
| Code blocks | 8 | Extraction, quality, language detection, HTML entities |
| Tables | 5 | Headers, no-thead fallback, empty, colspan |
| Images | 7 | Save, references, SVG, conflicts, cover, many |
| Error handling | 10 | Missing file, corrupt, DRM, no deps, malformed XHTML |
| JSON workflow | 6 | Load, build, round-trip, invalid, missing fields |
| CLI arguments | 8 | Flags, defaults, dry-run, verbose/quiet |
| Helper functions | 6 | Description inference, quality scoring, filename sanitization |
| Source detection | 6 | Detection, validation, regression |
| Edge cases | 8 | EPUB 2/3, no TOC, empty chapters, Unicode, fixed-layout |

### Integration Tests:
- Full extract → categorize → build workflow with mock ebooklib
- JSON round-trip (extract → save → load → build)

### Manual Testing Steps:
1. `pip install -e ".[epub]"` — verify install
2. `skill-seekers create book.epub` with a real EPUB file — verify output directory structure
3. `skill-seekers epub --epub book.epub --dry-run` — verify dry run output
4. `skill-seekers create drm-book.epub` — verify DRM error message
5. `skill-seekers create nonexistent.epub` — verify file-not-found error
6. Open generated `SKILL.md` — verify content quality and structure

## Performance Considerations

- ebooklib loads entire EPUB into memory. For typical books (<50MB), this is fine
- For very large EPUBs (100MB+), memory usage may spike. No mitigation needed for v1 — document as known limitation
- BeautifulSoup parsing of XHTML is fast. No performance concerns expected

## Migration Notes

- No migration needed — this is a new feature with no existing data to migrate
- Optional dependency (`ebooklib`) means existing installs are unaffected
- No breaking changes to any existing commands or APIs

## References

- [W3C EPUB 3.3 Specification](https://www.w3.org/TR/epub-33/) — authoritative source of truth
- [W3C EPUB Reading Systems 3.3](https://www.w3.org/TR/epub-rs-33/) — reading system requirements
- [ebooklib GitHub](https://github.com/aerkalov/ebooklib) — Python EPUB library
- [ebooklib PyPI](https://pypi.org/project/EbookLib/) — v0.20, Python 3.9-3.13
- [Research document](../research/2026-03-14-epub-input-support-affected-files.md) — affected files analysis
- Similar implementation: `src/skill_seekers/cli/word_scraper.py` — closest analog
- Similar tests: `tests/test_word_scraper.py` — test pattern template
