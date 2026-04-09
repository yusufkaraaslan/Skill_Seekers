# AGENTS.md - Skill Seekers

Comprehensive reference for AI coding agents. Skill Seekers is a Python CLI tool (v3.4.0) that converts documentation sites, GitHub repos, PDFs, videos, notebooks, wikis, and more into AI-ready skills for 21+ LLM platforms and RAG pipelines.

## Project Overview

**Skill Seekers** is a universal preprocessing layer that transforms raw documentation and code into structured knowledge assets. It supports 17+ source types and exports to 21+ AI platforms including Claude, Gemini, OpenAI, LangChain, LlamaIndex, and various vector databases.

### Key Capabilities
- **Source Types (17):** Documentation websites, GitHub repos, PDFs, Word docs, EPUBs, videos, local codebases, Jupyter notebooks, HTML, OpenAPI specs, AsciiDoc, PowerPoint, Confluence, Notion, RSS feeds, man pages, chat exports
- **Export Targets (21):** Claude, Gemini, OpenAI, MiniMax, OpenCode, Kimi, DeepSeek, Qwen, OpenRouter, Together AI, Fireworks AI, Markdown, LangChain, LlamaIndex, Haystack, Weaviate, ChromaDB, FAISS, Qdrant, Pinecone
- **MCP Server:** FastMCP-based Model Context Protocol server for AI assistant integration

## Setup

```bash
# REQUIRED before running tests (src/ layout — tests hard-exit if package not installed)
pip install -e .

# With dev tools (pytest, ruff, mypy, coverage)
pip install -e ".[dev]"

# With specific LLM platform support
pip install -e ".[gemini]"      # Google Gemini
pip install -e ".[openai]"      # OpenAI ChatGPT
pip install -e ".[all-llms]"    # All LLM platforms

# With all optional dependencies (except video-full)
pip install -e ".[all]"

# Full video processing (heavy dependencies)
pip install -e ".[video-full]"
```

Note: `tests/conftest.py` checks that `skill_seekers` is importable and calls `sys.exit(1)` if not. Always install in editable mode first.

### Environment Variables

Create a `.env` file or export these variables:
```bash
ANTHROPIC_API_KEY      # For Claude AI enhancement
GOOGLE_API_KEY         # For Gemini support
OPENAI_API_KEY         # For OpenAI support
GITHUB_TOKEN           # For GitHub repo scraping (higher rate limits)
```

## Build / Test / Lint Commands

```bash
# Run ALL tests (never skip tests — all must pass before commits)
pytest tests/ -v

# Run a single test file
pytest tests/test_scraper_features.py -v

# Run a single test function
pytest tests/test_scraper_features.py::test_detect_language -v

# Run a single test class method
pytest tests/test_adaptors/test_claude_adaptor.py::TestClaudeAdaptor::test_package -v

# Skip slow/integration tests
pytest tests/ -v -m "not slow and not integration"

# With coverage
pytest tests/ --cov=src/skill_seekers --cov-report=term

# Lint (ruff)
ruff check src/ tests/
ruff check src/ tests/ --fix

# Format (ruff)
ruff format --check src/ tests/
ruff format src/ tests/

# Type check (mypy)
mypy src/skill_seekers --show-error-codes --pretty
```

**Pytest config** (from pyproject.toml): `addopts = "-v --tb=short --strict-markers"`, `asyncio_mode = "auto"`, `asyncio_default_fixture_loop_scope = "function"`.

**Test markers:** `slow`, `integration`, `e2e`, `venv`, `bootstrap`, `benchmark`, `asyncio`.

**Async tests:** use `@pytest.mark.asyncio`; asyncio_mode is `auto` so the decorator is often implicit.

**Test count:** 160 test files (138 in `tests/`, 22 in `tests/test_adaptors/`).

## Code Style

### Formatting Rules (ruff — from pyproject.toml)
- **Line length:** 100 characters
- **Target Python:** 3.10+
- **Enabled lint rules:** E, W, F, I, B, C4, UP, ARG, SIM
- **Ignored rules:** E501 (line length handled by formatter), F541 (f-string style), ARG002 (unused method args for interface compliance), B007 (intentional unused loop vars), I001 (formatter handles imports), SIM114 (readability preference)

### Imports
- Sort with isort (via ruff); `skill_seekers` is first-party
- Standard library → third-party → first-party, separated by blank lines
- Use `from __future__ import annotations` only if needed for forward refs
- Guard optional imports with try/except ImportError (see `adaptors/__init__.py` pattern):
  ```python
  try:
      from .claude import ClaudeAdaptor
      from .minimax import MiniMaxAdaptor
  except ImportError:
      ClaudeAdaptor = None
      MiniMaxAdaptor = None
  ```

### Naming Conventions
- **Files:** `snake_case.py` (e.g., `source_detector.py`, `config_validator.py`)
- **Classes:** `PascalCase` (e.g., `SkillAdaptor`, `ClaudeAdaptor`, `SourceDetector`)
- **Functions/methods:** `snake_case` (e.g., `get_adaptor()`, `detect_language()`)
- **Constants:** `UPPER_CASE` (e.g., `ADAPTORS`, `DEFAULT_CHUNK_TOKENS`, `VALID_SOURCE_TYPES`)
- **Private:** prefix with `_` (e.g., `_read_existing_content()`, `_validate_unified()`)

### Type Hints
- Gradual typing — add hints where practical, not enforced everywhere
- Use modern syntax: `str | None` not `Optional[str]`, `list[str]` not `List[str]`
- MyPy config: `disallow_untyped_defs = false`, `check_untyped_defs = true`, `ignore_missing_imports = true`
- Tests are excluded from strict type checking (`disallow_untyped_defs = false`, `check_untyped_defs = false` for `tests.*`)

### Docstrings
- Module-level docstring on every file (triple-quoted, describes purpose)
- Google-style docstrings for public functions/classes
- Include `Args:`, `Returns:`, `Raises:` sections where useful

### Error Handling
- Use specific exceptions, never bare `except:`
- Provide helpful error messages with context
- Use `raise ValueError(...)` for invalid arguments, `raise RuntimeError(...)` for state errors
- Guard optional dependency imports with try/except and give clear install instructions on failure
- Chain exceptions with `raise ... from e` when wrapping

### Suppressing Lint Warnings
- Use inline `# noqa: XXXX` comments (e.g., `# noqa: F401` for re-exports, `# noqa: ARG001` for required but unused params)

## Project Layout

```
src/skill_seekers/           # Main package (src/ layout)
  cli/                       # CLI commands and entry points (100+ files)
    adaptors/                # Platform adaptors (Strategy pattern, inherit SkillAdaptor)
    arguments/               # CLI argument definitions (one per source type)
    parsers/                 # Subcommand parsers (one per source type)
    storage/                 # Cloud storage (inherit BaseStorageAdaptor)
    main.py                  # Unified CLI entry point (COMMAND_MODULES dict)
    source_detector.py       # Auto-detects source type from user input
    create_command.py        # Unified `create` command routing
    config_validator.py      # VALID_SOURCE_TYPES set + per-type validation
    unified_scraper.py       # Multi-source orchestrator (scraped_data + dispatch)
    unified_skill_builder.py # Pairwise synthesis + generic merge
  mcp/                       # MCP server (FastMCP + legacy)
    tools/                   # MCP tool implementations by category (10 files)
    server_fastmcp.py        # FastMCP server implementation
    server_legacy.py         # Legacy MCP server
  sync/                      # Sync monitoring (Pydantic models)
  benchmark/                 # Benchmarking framework
  embedding/                 # FastAPI embedding server
  workflows/                 # 67 YAML workflow presets
  _version.py                # Reads version from pyproject.toml
tests/                       # 160 test files (pytest)
  test_adaptors/             # 22 adaptor-specific test files
  conftest.py                # Test configuration with package check
configs/                     # Preset JSON scraping configs
docs/                        # Documentation (guides, integrations, architecture)
```

## Key Patterns

**Adaptor (Strategy) pattern** — all platform logic in `cli/adaptors/`. Inherit `SkillAdaptor`, implement `format_skill_md()`, `package()`, `upload()`. Register in `adaptors/__init__.py` ADAPTORS dict.

**Scraper pattern** — each source type has: `cli/<type>_scraper.py` (with `<Type>ToSkillConverter` class + `main()`), `arguments/<type>.py`, `parsers/<type>_parser.py`. Register in `parsers/__init__.py` PARSERS list, `main.py` COMMAND_MODULES dict, `config_validator.py` VALID_SOURCE_TYPES set.

**Unified pipeline** — `unified_scraper.py` dispatches to per-type `_scrape_<type>()` methods. `unified_skill_builder.py` uses pairwise synthesis for docs+github+pdf combos and `_generic_merge()` for all other combinations.

**MCP tools** — grouped in `mcp/tools/` by category. `scrape_generic_tool` handles all new source types.

**CLI subcommands** — git-style in `cli/main.py`. Each delegates to a module's `main()` function.

**Supported source types (17):** documentation (web), github, pdf, local, word, video, epub, jupyter, html, openapi, asciidoc, pptx, confluence, notion, rss, manpage, chat. Each detected automatically by `source_detector.py`.

**Supported platforms (21):** claude, gemini, openai, minimax, opencode, kimi, deepseek, qwen, openrouter, together, fireworks, markdown, langchain, llama-index, haystack, weaviate, chroma, faiss, qdrant, pinecone.

## CLI Commands

```bash
# Core commands
skill-seekers create <source>              # Create skill from any source (auto-detects type)
skill-seekers enhance <directory>          # AI-powered enhancement
skill-seekers package <directory>          # Package skill for target platform
skill-seekers upload <file>                # Upload skill to target platform
skill-seekers install <source>             # One-command workflow (scrape + enhance + package + upload)

# Utilities
skill-seekers estimate <source>            # Estimate page count before scraping
skill-seekers doctor                       # Health check for dependencies
skill-seekers config                       # Configure API keys and settings
skill-seekers workflows                    # List and apply workflow presets
skill-seekers resume <job_id>              # Resume interrupted scraping

# Advanced
skill-seekers stream <source>              # Streaming ingestion
skill-seekers update <directory>           # Incremental update
skill-seekers multilang <directory>        # Multi-language support
```

## Testing Instructions

### Test Structure
- Unit tests: `tests/test_*.py` — test individual modules
- Adaptor tests: `tests/test_adaptors/test_*_adaptor.py` — test platform adaptors
- E2E tests: `tests/test_*_e2e.py` — end-to-end integration tests

### Running Tests
```bash
# Fast test run (skip slow/integration tests)
pytest tests/ -v -m "not slow and not integration"

# Full test suite
pytest tests/ -v

# With coverage report
pytest tests/ --cov=src/skill_seekers --cov-report=term-missing

# Specific test categories
pytest tests/ -v -m "slow"           # Only slow tests
pytest tests/ -v -m "integration"    # Only integration tests
pytest tests/ -v -m "e2e"            # Only E2E tests
```

### Test Fixtures
Test fixtures are located in `tests/fixtures/` and include sample configs, HTML files, and mock data.

## Git Workflow

- **`main`** — production, protected
- **`development`** — default PR target, active dev
- Feature branches created from `development`

## Pre-commit Checklist

```bash
ruff check src/ tests/
ruff format --check src/ tests/
pytest tests/ -v -x   # stop on first failure
```

Never commit API keys. Use env vars: `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `GITHUB_TOKEN`.

## CI/CD

GitHub Actions (7 workflows in `.github/workflows/`):
- **tests.yml** — ruff + mypy lint job, then pytest matrix (Ubuntu + macOS, Python 3.10-3.12) with Codecov upload
- **release.yml** — tag-triggered: tests → version verification → PyPI publish via `uv build`
- **test-vector-dbs.yml** — tests vector DB adaptors (weaviate, chroma, faiss, qdrant)
- **docker-publish.yml** — multi-platform Docker builds (amd64, arm64) for CLI + MCP images
- **quality-metrics.yml** — quality analysis with configurable threshold
- **scheduled-updates.yml** — weekly skill updates for popular frameworks
- **vector-db-export.yml** — weekly vector DB exports

## Deployment

### Docker
Multi-stage Dockerfile with Python 3.12 slim base:
```bash
# Build image
docker build -t skill-seekers .

# Run CLI
docker run -v $(pwd)/output:/output skill-seekers create https://docs.example.com

# Run MCP server
docker run -p 8765:8765 skill-seekers skill-seekers-mcp
```

### MCP Server
The MCP server provides Model Context Protocol integration:
```bash
# Start FastMCP server
skill-seekers-mcp

# Or use the Python module
python -m skill_seekers.mcp.server_fastmcp
```

## Security Considerations

- **API Keys:** Never commit API keys to version control. Use environment variables or `.env` files (already in `.gitignore`)
- **Docker:** Runs as non-root user (`skillseeker`, UID 1000)
- **Dependencies:** Regular security updates via `pip audit` or `safety check`
- **Sandboxing:** Video processing uses optional dependencies that can be heavy; install `[video-full]` only when needed

## Additional Resources

- **Website:** https://skillseekersweb.com/
- **Documentation:** https://skillseekersweb.com/
- **PyPI:** https://pypi.org/project/skill-seekers/
- **Repository:** https://github.com/yusufkaraaslan/Skill_Seekers
- **Config Browser:** https://skillseekersweb.com/
- **Project Board:** https://github.com/users/yusufkaraaslan/projects/2
