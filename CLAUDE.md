# CLAUDE.md

## Workflow Rules

- Every change made must be committed.
- Every new relevant learning requires an according update of CLAUDE.md.

## Project

**Skill Seekers** — universal documentation preprocessor for AI systems. Transforms docs sites, GitHub repos, PDFs, EPUBs into formats for 16+ platforms (RAG, vector DBs, AI coding assistants, LLMs).

- **Version:** 3.2.0 | **Python:** 3.10+ | **PyPI:** published
- **Website:** https://skillseekersweb.com/

## Setup

```bash
pip install -e .                    # REQUIRED — src/ layout needs installation
pytest tests/ -v                    # verify
```

## Commands

```bash
# Preferred: unified create (auto-detects source type)
skill-seekers create <url|owner/repo|./path|file.pdf|book.epub> -p quick|standard|comprehensive
skill-seekers create <source> --enhance-level 0-3 --dry-run --chunk-for-rag

# Legacy (still work)
skill-seekers scrape --config configs/react.json
skill-seekers github --repo facebook/react
skill-seekers analyze --directory . --comprehensive

# Standalone EPUB
skill-seekers epub --epub book.epub --name myskill

# Package
skill-seekers package output/react/ --target claude|gemini|openai|markdown
skill-seekers package output/react/ --format langchain|llama-index|haystack|chroma|faiss|weaviate|qdrant

# Other
skill-seekers enhance output/react/ --mode LOCAL|API
skill-seekers cloud upload --provider s3|gcs|azure --bucket my-bucket output/react.zip
skill-seekers config --show|--github|--test
```

Progressive help: `--help`, `--help-web`, `--help-github`, `--help-local`, `--help-pdf`, `--help-epub`, `--help-all`

## Development

### Tests — never skip, all must pass before commits

```bash
pytest tests/ -v                                          # all (default: fast only)
pytest tests/test_scraper_features.py::test_name -v       # single test
pytest tests/ --cov=src/skill_seekers --cov-report=term   # with coverage
pytest tests/ -v -m slow                                  # include slow
pytest tests/ -v -m "not slow and not integration"        # fast only (explicit)
```

~2,540 tests across 46 files. CI matrix: Ubuntu + macOS, Python 3.10–3.12.

### Code quality (matches CI)

```bash
ruff check src/ tests/              # lint
ruff format src/ tests/             # format
mypy src/skill_seekers              # type check (continue-on-error in CI)
```

Auto-fix before pushing:
```bash
uvx ruff check --fix --unsafe-fixes src/ tests/
uvx ruff format src/ tests/
```

### Build & publish

```bash
uv build && uv publish
```

## Architecture

### Data flow

1. **Scrape** (`doc_scraper.py:scrape_all()`) — BFS traversal → `output/{name}_data/pages/*.json`
2. **Build** (`doc_scraper.py:build_skill()`) — categorize + extract → `SKILL.md` + `references/*.md`
3. **Enhance** (optional) — LLM rewrites SKILL.md (API or LOCAL mode)
4. **Package** (`package_skill.py` → adaptor) — platform-specific format
5. **Upload** (optional) — platform API

### Platform adaptors (Strategy pattern)

Factory: `get_adaptor(target/format)` in `src/skill_seekers/cli/adaptors/__init__.py`

- LLM: claude, gemini, openai (use `--target`)
- RAG: langchain, llama-index, haystack (use `--format`)
- Vector DBs: chroma, faiss, weaviate, qdrant (use `--format`)
- AI assistants: Cursor, Windsurf, Cline, Continue.dev (via claude format + copy)
- Generic: markdown

Base class: `base_adaptor.py` — methods: `package()`, `upload()`, `enhance()`, `export()`

### CLI architecture

Entry point: `src/skill_seekers/cli/main.py` — git-style dispatcher, modifies `sys.argv` and calls sub-module `main()` functions.

Subcommands: create, scrape, github, pdf, epub, unified, codebase, enhance, enhance-status, package, upload, estimate, install, install-agent, patterns, how-to-guides, config, resume, cloud, embed, sync, update, quality, benchmark, multilang, stream, video, workflows

### Key source files

| Area | Files |
|------|-------|
| Core scraping | `cli/doc_scraper.py`, `cli/github_scraper.py`, `cli/pdf_scraper.py`, `cli/epub_scraper.py`, `cli/codebase_scraper.py` |
| Code analysis | `cli/code_analyzer.py`, `cli/pattern_recognizer.py`, `cli/test_example_extractor.py` |
| Guides & docs | `cli/how_to_guide_builder.py`, `cli/config_extractor.py`, `cli/generate_router.py` |
| AI enhancement | `cli/enhance_skill_local.py`, `cli/enhance_skill.py`, `cli/ai_enhancer.py` |
| Adaptors | `cli/adaptors/{platform}_adaptor.py`, `cli/adaptors/__init__.py` |
| MCP server | `mcp/server_fastmcp.py`, `mcp/tools/` (26 tools) |
| Create command | `cli/parsers/create_parser.py`, `cli/arguments/create.py`, `cli/source_detector.py` |
| Config/rate limit | `cli/config_manager.py`, `cli/rate_limit_handler.py`, `cli/config_command.py` |
| Godot signals | `cli/signal_flow_analyzer.py` (C3.10) |

All source under `src/skill_seekers/`.

### C3.x codebase analysis features

- **C3.1** Pattern detection — 10 GoF patterns, 9 languages (`pattern_recognizer.py`)
- **C3.2** Test example extraction — AST-based for Python, regex for others (`test_example_extractor.py`)
- **C3.3** How-to guide generation — from test workflows, AI-enhanced (`how_to_guide_builder.py`)
- **C3.4** Config extraction — env vars, config files, CLI args (`config_extractor.py`)
- **C3.5** Architectural overview — ARCHITECTURE.md, router skills (`generate_router.py`)
- **C3.6** AI enhancement — Claude API integration for C3.1–C3.5
- **C3.7** Architectural pattern detection — MVC, MVVM, etc. (`architectural_pattern_detector.py`)
- **C3.8** Standalone codebase scraper — full SKILL.md from code alone (`codebase_scraper.py`)
- **C3.9** Project doc extraction — markdown categorization (`codebase_scraper.py`)
- **C3.10** Signal flow analysis — Godot event-driven architecture (`signal_flow_analyzer.py`)

All features ON by default; use `--skip-*` flags to disable.

## Environment variables

```bash
ANTHROPIC_API_KEY=sk-ant-...          # Claude AI (required for API enhancement)
ANTHROPIC_BASE_URL=...                # optional, for compatible endpoints
GOOGLE_API_KEY=AIza...                # Gemini (optional)
OPENAI_API_KEY=sk-...                 # OpenAI (optional)
GITHUB_TOKEN=ghp_...                  # higher rate limits
```

Enhancement auto-detects mode: API key set → API mode, otherwise → LOCAL (Claude Code Max).

`--enhance-level`: 0=disabled, 1=SKILL.md only, 2=+architecture+config+docs (default), 3=full

## Git workflow

- Main: `main`, development: `development`
- Feature branches from `development`: `feature/{task-id}-{description}`
- PRs target `development`

## CI/CD

`.github/workflows/tests.yml` — on push/PR to main or development:
1. **Lint** — ruff check, ruff format --check, mypy
2. **Test** — matrix (Ubuntu + macOS, Python 3.10–3.12), coverage → Codecov
3. **Summary** — single status check for branch protection

`.github/workflows/release.yml` — on version tags: `uv build` → `uv publish` → GitHub release

## Adding things

### New platform adaptor
1. Create `src/skill_seekers/cli/adaptors/{platform}_adaptor.py` inheriting `BaseAdaptor`
2. Register in `adaptors/__init__.py` factory
3. Add optional dep to `pyproject.toml`
4. Add tests in `tests/`

### New CLI command
1. Create `src/skill_seekers/cli/my_command.py` with `main()`
2. Add entry point in `pyproject.toml` `[project.scripts]`
3. Add to dispatcher in `cli/main.py`
4. Add tests

### New create command flags
- Universal → `UNIVERSAL_ARGUMENTS` in `cli/arguments/create.py`
- Source-specific → `WEB_ARGUMENTS`, `GITHUB_ARGUMENTS`, `EPUB_ARGUMENTS`, etc.

### New MCP tool
- Add `@mcp.tool()` in `mcp/server_fastmcp.py`
- Add tests in `tests/test_mcp_fastmcp.py`

## Common pitfalls

- **`ModuleNotFoundError: skill_seekers`** → run `pip install -e .` (src/ layout requirement)
- **GitHub 403** → rate limit; set `GITHUB_TOKEN` or use `skill-seekers config --github`
- **Enhancement fails** → check `ANTHROPIC_API_KEY` or use `--mode LOCAL`
- **CI fails locally passes** → use `uvx ruff` (not local ruff), check dep versions match between `requirements.txt` and `pyproject.toml`
- **pytest not found** → `pip install pytest pytest-asyncio pytest-cov`

## Config file structure

```json
{
  "name": "framework-name",
  "base_url": "https://docs.example.com/",
  "selectors": { "main_content": "article", "title": "h1", "code_blocks": "pre code" },
  "url_patterns": { "include": ["/docs"], "exclude": ["/blog"] },
  "categories": { "getting_started": ["intro", "quickstart"] },
  "rate_limit": 0.5,
  "max_pages": 500
}
```

## Key algorithms

- **Smart categorization** (`doc_scraper.py:smart_categorize()`) — scores pages against category keywords (3pt URL, 2pt title, 1pt content), threshold 2+, falls back to "other"
- **Language detection** (`doc_scraper.py:detect_language()`) — CSS class attrs first, then keyword heuristics
- **Selector fallback** — `FALLBACK_MAIN_SELECTORS` constant + `_find_main_content()` helper; `body` deliberately excluded

## Docs

- [CONTRIBUTING.md](CONTRIBUTING.md) — branch workflow, PR process
- [CHANGELOG.md](CHANGELOG.md) — release history
- [docs/ENHANCEMENT_MODES.md](docs/ENHANCEMENT_MODES.md) — API vs LOCAL enhancement
- [docs/MCP_SETUP.md](docs/MCP_SETUP.md) — MCP server setup
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — common issues
