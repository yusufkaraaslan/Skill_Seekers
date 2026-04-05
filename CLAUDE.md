# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Skill Seekers** converts documentation from 17 source types into production-ready formats for 24+ AI platforms (LLM platforms, RAG frameworks, vector databases, AI coding assistants). Published on PyPI as `skill-seekers`.

**Version:** 3.4.0 | **Python:** 3.10+ | **Website:** https://skillseekersweb.com/

**Architecture:** See `docs/UML_ARCHITECTURE.md` for UML diagrams and module overview. StarUML project at `docs/UML/skill_seekers.mdj`.

## Essential Commands

```bash
# REQUIRED before running tests or CLI (src/ layout)
pip install -e .

# Run all tests (NEVER skip - all must pass before commits)
pytest tests/ -v

# Fast iteration (skip slow MCP tests ~20min)
pytest tests/ --ignore=tests/test_mcp_fastmcp.py --ignore=tests/test_mcp_server.py --ignore=tests/test_install_skill_e2e.py -q

# Single test
pytest tests/test_scraper_features.py::test_detect_language -vv -s

# Code quality (must pass before push - matches CI)
uvx ruff check src/ tests/
uvx ruff format --check src/ tests/
mypy src/skill_seekers  # continue-on-error in CI

# Auto-fix lint/format issues
uvx ruff check --fix --unsafe-fixes src/ tests/
uvx ruff format src/ tests/

# Build & publish
uv build
uv publish
```

## CI Matrix

Runs on push/PR to `main` or `development`. Lint job (Python 3.12, Ubuntu) + Test job (Ubuntu + macOS, Python 3.10/3.11/3.12, excludes macOS+3.10). Both must pass for merge.

## Git Workflow

- **Main branch:** `main` (requires tests + 1 review)
- **Development branch:** `development` (default PR target, requires tests)
- **Feature branches:** `feature/{task-id}-{description}` from `development`
- PRs always target `development`, never `main` directly

## Architecture

### CLI: Unified create command

Entry point `src/skill_seekers/cli/main.py`. The `create` command is the **only** entry point for skill creation — it auto-detects source type and routes to the appropriate `SkillConverter`.

```
skill-seekers create <source>     # Auto-detect: URL, owner/repo, ./path, file.pdf, etc.
skill-seekers package <dir>       # Package for platform (--target claude/gemini/openai/markdown/minimax/opencode/kimi/deepseek/qwen/openrouter/together/fireworks, --format langchain/llama-index/haystack/chroma/faiss/weaviate/qdrant/pinecone)
```

### SkillConverter Pattern (Template Method + Factory)

All 18 source types implement the `SkillConverter` base class (`skill_converter.py`):

```python
converter = get_converter("web", config)  # Factory lookup
converter.run()  # Template: extract() → build_skill()
```

Registry in `CONVERTER_REGISTRY` maps source type → (module, class). `create_command.py` builds config from `ExecutionContext`, calls `get_converter()`, then runs centralized enhancement.

### Data Flow (5 phases)

1. **Scrape** - Source-specific scraper extracts content to `output/{name}_data/pages/*.json`
2. **Build** - `build_skill()` categorizes pages, extracts patterns, generates `output/{name}/SKILL.md`
3. **Enhance** (optional) - LLM rewrites SKILL.md (`--enhance-level 0-3`, auto-detects API vs LOCAL mode)
4. **Package** - Platform adaptor formats output (`.zip`, `.tar.gz`, JSON, vector index)
5. **Upload** (optional) - Platform API upload

### Platform Adaptor Pattern (Strategy + Factory)

Factory: `get_adaptor(platform, config)` in `adaptors/__init__.py` returns a `SkillAdaptor` instance. Base class `SkillAdaptor` + `SkillMetadata` in `adaptors/base.py`.

```
src/skill_seekers/cli/adaptors/
├── __init__.py              # Factory: get_adaptor(platform, config), ADAPTORS registry
├── base.py                  # Abstract base: SkillAdaptor, SkillMetadata
├── openai_compatible.py     # Shared base for OpenAI-compatible platforms
├── claude.py                # --target claude
├── gemini.py                # --target gemini
├── openai.py                # --target openai
├── markdown.py              # --target markdown
├── minimax.py               # --target minimax
├── opencode.py              # --target opencode
├── kimi.py                  # --target kimi
├── deepseek.py              # --target deepseek
├── qwen.py                  # --target qwen
├── openrouter.py            # --target openrouter
├── together.py              # --target together
├── fireworks.py             # --target fireworks
├── langchain.py             # --format langchain
├── llama_index.py           # --format llama-index
├── haystack.py              # --format haystack
├── chroma.py                # --format chroma
├── faiss_helpers.py         # --format faiss
├── qdrant.py                # --format qdrant
├── weaviate.py              # --format weaviate
├── pinecone_adaptor.py      # --format pinecone
└── streaming_adaptor.py     # --format streaming
```

`--target` = LLM platforms, `--format` = RAG/vector DBs. All adaptors are imported with `try/except ImportError` so missing optional deps don't break the registry.

### 18 Source Type Converters

Each in `src/skill_seekers/cli/{type}_scraper.py` as a `SkillConverter` subclass (no `main()`). The `create_command.py` uses `source_detector.py` to auto-detect, then calls `get_converter()`. Converters: web (doc_scraper), github, pdf, word, epub, video, local (codebase_scraper), jupyter, html, openapi, asciidoc, pptx, rss, manpage, confluence, notion, chat, config (unified_scraper).

### CLI Argument System

```
src/skill_seekers/cli/
├── parsers/              # Subcommand parser registration
│   └── create_parser.py  # Progressive help disclosure (--help-web, --help-github, etc.)
├── arguments/            # Argument definitions
│   ├── common.py         # add_all_standard_arguments() - shared across all scrapers
│   └── create.py         # UNIVERSAL_ARGUMENTS, WEB_ARGUMENTS, GITHUB_ARGUMENTS, etc.
└── source_detector.py    # Auto-detect source type from input string
```

### C3.x Codebase Analysis Pipeline

Local codebase analysis features, all opt-out (`--skip-*` flags):
- C3.1 `pattern_recognizer.py` - Design pattern detection (10 GoF patterns, 9 languages)
- C3.2 `test_example_extractor.py` - Usage examples from tests
- C3.3 `how_to_guide_builder.py` - AI-enhanced educational guides
- C3.4 `config_extractor.py` - Configuration pattern extraction
- C3.5 `generate_router.py` - Architecture overview generation
- C3.10 `signal_flow_analyzer.py` - Godot signal flow analysis

### MCP Server

`src/skill_seekers/mcp/server_fastmcp.py` - 40 tools via FastMCP. Transport: stdio (Claude Code) or HTTP (Cursor/Windsurf). Optional dependency: `pip install -e ".[mcp]"`

Supporting modules:
- `marketplace_publisher.py` - Publish skills to plugin marketplace repositories
- `marketplace_manager.py` - Manage marketplace registry
- `config_publisher.py` - Push configs to registered config source repositories

### Enhancement Modes (via AgentClient)

Enhancement now uses the `AgentClient` abstraction (`src/skill_seekers/cli/agent_client.py`) instead of direct Claude API calls:

- **API mode** (if API key set): Supports Anthropic, Moonshot/Kimi, Google Gemini, OpenAI
- **LOCAL mode** (fallback): Supports Claude Code, Kimi Code, Codex, Copilot, OpenCode, custom agents
- Control: `--enhance-level 0` (off) / `1` (SKILL.md only) / `2` (default, balanced) / `3` (full)
- Agent selection: `--agent claude|codex|copilot|opencode|kimi|custom`

## Key Implementation Details

### Smart Categorization (`doc_scraper.py:smart_categorize()`)

Scores pages against category keywords: 3 points for URL match, 2 for title, 1 for content. Threshold of 2+ required. Falls back to "other".

### Content Extraction (`doc_scraper.py`)

`FALLBACK_MAIN_SELECTORS` constant + `_find_main_content()` helper handle CSS selector fallback. Links are extracted from the full page before early return (not just main content). `body` is deliberately excluded from fallbacks.

### Three-Stream GitHub Architecture (`unified_codebase_analyzer.py`)

Stream 1: Code Analysis (AST, patterns, tests, guides). Stream 2: Documentation (README, docs/, wiki). Stream 3: Community (issues, PRs, metadata). Depth control: `basic` (1-2 min) or `c3x` (20-60 min).

## Testing

### Test markers (pytest.ini)

```bash
pytest tests/ -v                                    # Default: fast tests only
pytest tests/ -v -m slow                            # Include slow tests (>5s)
pytest tests/ -v -m integration                     # External services required
pytest tests/ -v -m e2e                             # Resource-intensive
pytest tests/ -v -m "not slow and not integration"  # Fastest subset
```

### Known legitimate skips (~11)

- 2: chromadb incompatible with Python 3.14 (pydantic v1)
- 2: weaviate-client not installed
- 2: Qdrant not running (requires docker)
- 2: langchain/llama_index not installed
- 3: GITHUB_TOKEN not set

### sys.modules gotcha

`test_swift_detection.py` deletes `skill_seekers.cli` modules from `sys.modules`. It must save and restore both `sys.modules` entries AND parent package attributes (`setattr`). See the test file for the pattern.

## Dependencies

Core deps include `langchain`, `llama-index`, `anthropic`, `httpx`, `PyMuPDF`, `pydantic`. Platform-specific deps are optional:

```bash
pip install -e ".[mcp]"       # MCP server
pip install -e ".[gemini]"    # Google Gemini
pip install -e ".[openai]"    # OpenAI
pip install -e ".[docx]"      # Word documents
pip install -e ".[epub]"      # EPUB books
pip install -e ".[video]"     # Video (lightweight)
pip install -e ".[video-full]"# Video (Whisper + visual)
pip install -e ".[jupyter]"   # Jupyter notebooks
pip install -e ".[pptx]"      # PowerPoint
pip install -e ".[rss]"       # RSS/Atom feeds
pip install -e ".[confluence]"# Confluence wiki
pip install -e ".[notion]"    # Notion pages
pip install -e ".[chroma]"    # ChromaDB
pip install -e ".[all]"       # Everything (except video-full)
```

Dev dependencies use PEP 735 `[dependency-groups]` in pyproject.toml.

## Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...          # Claude AI (or compatible endpoint)
ANTHROPIC_BASE_URL=https://...        # Optional: Claude-compatible API endpoint
GOOGLE_API_KEY=AIza...                # Google Gemini (optional)
OPENAI_API_KEY=sk-...                 # OpenAI (optional)
GITHUB_TOKEN=ghp_...                  # Higher GitHub rate limits
```

## Adding New Features

### New platform adaptor
1. Create `src/skill_seekers/cli/adaptors/{platform}.py` inheriting `SkillAdaptor` from `base.py`
2. Register in `adaptors/__init__.py` (add try/except import + add to `ADAPTORS` dict)
3. Add optional dep to `pyproject.toml`
4. Add tests in `tests/`

### New source type converter
1. Create `src/skill_seekers/cli/{type}_scraper.py` with a class inheriting `SkillConverter`
2. Implement `extract()` and `build_skill()` methods, set `SOURCE_TYPE`
3. Register in `CONVERTER_REGISTRY` in `skill_converter.py`
4. Add source type config building in `create_command.py:_build_config()`
5. Add auto-detection in `source_detector.py`
6. Add optional dep if needed
7. Add tests

### New CLI argument
- Universal: `UNIVERSAL_ARGUMENTS` in `arguments/create.py`
- Source-specific: appropriate dict (`WEB_ARGUMENTS`, `GITHUB_ARGUMENTS`, etc.)
- Shared across scrapers: `add_all_standard_arguments()` in `arguments/common.py`
