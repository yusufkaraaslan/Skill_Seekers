---
date: 2026-03-14T12:54:24.700367+00:00
git_commit: 7c90a4b9c9bccac8341b0769550d77aae3b4e524
branch: development
topic: "What files would be affected to add .epub support for input"
tags: [research, codebase, epub, input-format, scraper]
status: complete
---

# Research: What files would be affected to add .epub support for input

## Research Question

What files would be affected to add .epub support for input.

## Summary

Adding `.epub` input support follows an established pattern already used for PDF and Word (.docx) formats. The codebase has a consistent multi-layer architecture for document input formats: source detection, argument definitions, parser registration, create command routing, standalone scraper module, and tests. Based on analysis of the existing PDF and Word implementations, **16 existing files would need modification** and **4 new files would need to be created**.

## Detailed Findings

### New Files to Create (4 files)

| File | Purpose |
|------|---------|
| `src/skill_seekers/cli/epub_scraper.py` | Core EPUB extraction and skill building logic (analog: `word_scraper.py` at ~750 lines) |
| `src/skill_seekers/cli/arguments/epub.py` | EPUB-specific argument definitions (analog: `arguments/word.py`) |
| `src/skill_seekers/cli/parsers/epub_parser.py` | Subcommand parser class (analog: `parsers/word_parser.py`) |
| `tests/test_epub_scraper.py` | Test suite (analog: `test_word_scraper.py` at ~750 lines, 130+ tests) |

### Existing Files to Modify (16 files)

#### 1. Source Detection Layer

**`src/skill_seekers/cli/source_detector.py`** (3 locations)

- **`SourceDetector.detect()`** (line ~60): Add `.epub` extension check, following the `.docx` pattern at line 63-64:
  ```python
  if source.endswith(".epub"):
      return cls._detect_epub(source)
  ```

- **New method `_detect_epub()`**: Add detection method (following `_detect_word()` at lines 124-129):
  ```python
  @classmethod
  def _detect_epub(cls, source: str) -> SourceInfo:
      name = os.path.splitext(os.path.basename(source))[0]
      return SourceInfo(
          type="epub", parsed={"file_path": source}, suggested_name=name, raw_input=source
      )
  ```

- **`validate_source()`** (line ~250): Add epub validation block (following the word block at lines 273-278)

- **Error message** (line ~94): Add EPUB example to the `ValueError` help text

#### 2. CLI Dispatcher

**`src/skill_seekers/cli/main.py`** (2 locations)

- **`COMMAND_MODULES` dict** (line ~46): Add epub entry:
  ```python
  "epub": "skill_seekers.cli.epub_scraper",
  ```

- **Module docstring** (line ~1): Add `epub` to the commands list

#### 3. Create Command Routing

**`src/skill_seekers/cli/create_command.py`** (3 locations)

- **`_route_to_scraper()`** (line ~121): Add `elif self.source_info.type == "epub":` routing case

- **New `_route_epub()` method**: Following the `_route_word()` pattern at lines 331-352:
  ```python
  def _route_epub(self) -> int:
      from skill_seekers.cli import epub_scraper
      argv = ["epub_scraper"]
      file_path = self.source_info.parsed["file_path"]
      argv.extend(["--epub", file_path])
      self._add_common_args(argv)
      # epub-specific args here
      ...
  ```

- **`main()` epilog** (line ~537): Add EPUB example and source auto-detection entry

- **Progressive help** (line ~590): Add `--help-epub` flag and handler block

#### 4. Argument Definitions

**`src/skill_seekers/cli/arguments/create.py`** (4 locations)

- **New `EPUB_ARGUMENTS` dict** (~line 401): Define epub-specific arguments (e.g., `--epub` file path flag), following the `WORD_ARGUMENTS` pattern at lines 402-411

- **`get_source_specific_arguments()`** (line 595): Add `"epub": EPUB_ARGUMENTS` to the `source_args` dict

- **`add_create_arguments()`** (line 676): Add epub mode block:
  ```python
  if mode in ["epub", "all"]:
      for arg_name, arg_def in EPUB_ARGUMENTS.items():
          parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])
  ```

#### 5. Parser Registration

**`src/skill_seekers/cli/parsers/__init__.py`** (2 locations)

- **Import** (line ~15): Add `from .epub_parser import EpubParser`

- **`PARSERS` list** (line ~46): Add `EpubParser()` entry (near `WordParser()` and `PDFParser()`)

#### 6. Package Configuration

**`pyproject.toml`** (3 locations)

- **`[project.optional-dependencies]`** (line ~111): Add `epub` optional dependency group:
  ```toml
  epub = [
      "ebooklib>=0.18",
  ]
  ```

- **`all` optional dependency group** (line ~178): Add epub dependency to the combined `all` group

- **`[project.scripts]`** (line ~224): Add standalone entry point:
  ```toml
  skill-seekers-epub = "skill_seekers.cli.epub_scraper:main"
  ```

#### 7. Argument Commons

**`src/skill_seekers/cli/arguments/common.py`**

- No changes strictly required, but `add_all_standard_arguments()` is called by the new `arguments/epub.py` (no modification needed — it's used as-is)

#### 8. Documentation / Configuration

**`CLAUDE.md`** (2 locations)

- **Commands section**: Add `epub` to the list of subcommands
- **Key source files table**: Add `epub_scraper.py` entry

**`CONTRIBUTING.md`** — Potentially update with epub format mention

**`CHANGELOG.md`** — New feature entry

### Files NOT Affected

These files do **not** need changes:

- **`unified_scraper.py`** — Multi-source configs could add epub support later but it's not required for basic input support
- **Platform adaptors** (`adaptors/*.py`) — Adaptors work on the output side (packaging), not input
- **Enhancement system** (`enhance_skill.py`, `enhance_skill_local.py`) — Works generically on SKILL.md
- **MCP server** (`mcp/server_fastmcp.py`) — Operates on completed skills
- **`pdf_extractor_poc.py`** — PDF-specific extraction; epub needs its own extractor

## Code References

### Pattern to Follow (Word .docx implementation)

- `src/skill_seekers/cli/word_scraper.py:1-750` — Full scraper with `WordToSkillConverter` class
- `src/skill_seekers/cli/arguments/word.py:1-75` — Argument definitions with `add_word_arguments()`
- `src/skill_seekers/cli/parsers/word_parser.py:1-33` — Parser class extending `SubcommandParser`
- `tests/test_word_scraper.py:1-750` — Comprehensive test suite with 130+ tests

### Key Integration Points

- `src/skill_seekers/cli/source_detector.py:57-65` — File extension detection order
- `src/skill_seekers/cli/source_detector.py:124-129` — `_detect_word()` method (template for `_detect_epub()`)
- `src/skill_seekers/cli/create_command.py:121-143` — `_route_to_scraper()` dispatch
- `src/skill_seekers/cli/create_command.py:331-352` — `_route_word()` (template for `_route_epub()`)
- `src/skill_seekers/cli/arguments/create.py:401-411` — `WORD_ARGUMENTS` dict (template)
- `src/skill_seekers/cli/arguments/create.py:595-604` — `get_source_specific_arguments()` mapping
- `src/skill_seekers/cli/arguments/create.py:676-678` — `add_create_arguments()` mode handling
- `src/skill_seekers/cli/parsers/__init__.py:35-59` — `PARSERS` registry list
- `src/skill_seekers/cli/main.py:46-70` — `COMMAND_MODULES` dict
- `pyproject.toml:111-115` — Optional dependency group pattern (docx)
- `pyproject.toml:213-246` — Script entry points

### Data Flow Architecture

The epub scraper would follow the same three-step pipeline as Word/PDF:

1. **Extract** — Parse `.epub` file → sections with text, headings, code, images → save to `output/{name}_extracted.json`
2. **Categorize** — Group sections by chapters/keywords
3. **Build** — Generate `SKILL.md`, `references/*.md`, `references/index.md`, `assets/`

The intermediate JSON format uses the same structure as Word/PDF:
```python
{
    "source_file": str,
    "metadata": {"title", "author", "created", ...},
    "total_sections": int,
    "total_code_blocks": int,
    "total_images": int,
    "languages_detected": {str: int},
    "pages": [  # sections
        {
            "section_number": int,
            "heading": str,
            "text": str,
            "code_samples": [...],
            "images": [...],
            "headings": [...]
        }
    ]
}
```

## Architecture Documentation

### Document Input Format Pattern

Each input format follows a consistent architecture:

```
[source_detector.py] → detect type by extension
        ↓
[create_command.py] → route to scraper
        ↓
[{format}_scraper.py] → extract → categorize → build skill
        ↓
[output/{name}/] → SKILL.md + references/ + assets/
```

Supporting files per format:
- `arguments/{format}.py` — CLI argument definitions
- `parsers/{format}_parser.py` — Subcommand parser class
- `tests/test_{format}_scraper.py` — Test suite

### Dependency Guard Pattern

The Word scraper uses an optional dependency guard that epub should replicate:

```python
try:
    import ebooklib
    from ebooklib import epub
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False

def _check_epub_deps():
    if not EPUB_AVAILABLE:
        raise RuntimeError(
            "ebooklib is required for EPUB support.\n"
            'Install with: pip install "skill-seekers[epub]"\n'
            "Or: pip install ebooklib"
        )
```

## Summary Table

| Category | Files | Action |
|----------|-------|--------|
| New files | 4 | Create from scratch |
| Source detection | 1 | Add epub detection + validation |
| CLI dispatcher | 1 | Add command module mapping |
| Create command | 1 | Add routing + help + examples |
| Arguments | 1 | Add EPUB_ARGUMENTS + register in helpers |
| Parser registry | 1 | Import + register EpubParser |
| Package config | 1 | Add deps + entry point |
| Documentation | 2+ | Update CLAUDE.md, CHANGELOG |
| **Total** | **12+ modified, 4 new** | |

## Open Questions

- Should epub support reuse any of the existing HTML parsing from `word_scraper.py` (which uses mammoth to convert to HTML then parses with BeautifulSoup)? EPUB internally contains XHTML files, so BeautifulSoup parsing would be directly applicable.
- Should the epub scraper support DRM-protected files, or only DRM-free epub files?
- Should epub-specific arguments include options like `--chapter-range` (similar to PDF's `--pages`)?
