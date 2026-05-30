# QWEN.md - Skill Seekers

Comprehensive context file for AI coding agents working with the Skill Seekers project.

---

## Project Overview

**Skill Seekers** (v3.6.0) is a Python CLI tool and MCP server that converts documentation sites, GitHub repositories, PDFs, videos, notebooks, wikis, and 17+ source types into structured AI-ready skills for 21+ LLM platforms and RAG pipelines.

**Tagline:** "The data layer for AI systems" — sits between raw documentation and every AI system that consumes it (Claude, Gemini, LangChain, LlamaIndex, Cursor, etc.).

### Key Capabilities

- **18 source types:** documentation (web), GitHub, PDF, Word (.docx), EPUB, video, local codebase, Jupyter, HTML, OpenAPI, AsciiDoc, PowerPoint, RSS/Atom, man pages, Confluence, Notion, Slack/Discord chat
- **21+ export targets:** Claude, Gemini, OpenAI, DeepSeek, Qwen, Fireworks, Together, OpenRouter, IBM BoB, Kimi, MiniMax, OpenCode, LangChain, LlamaIndex, Haystack, Pinecone, Chroma, Weaviate, Qdrant, FAISS, Markdown, and more
- **Unified pipeline:** One scraping command → export to any platform without re-scraping
- **MCP server:** 40 tools for AI assistants to scrape, package, and manage skills
- **AI enhancement:** Optional Claude-powered enhancement for better skill quality

### Project Links

| Resource | Link |
|----------|------|
| Website | https://skillseekersweb.com/ |
| PyPI | https://pypi.org/project/skill-seekers/ |
| GitHub | https://github.com/yusufkaraaslan/Skill_Seekers |
| Configs | https://github.com/yusufkaraaslan/skill-seekers-configs |
| MCP | https://modelcontextprotocol.io |

---

## Project Structure

```
Skill_Seekers/
├── src/skill_seekers/           # Main package (src/ layout)
│   ├── cli/                     # CLI commands (97 files)
│   │   ├── adaptors/            # Platform adaptors (Strategy pattern)
│   │   ├── arguments/           # CLI argument definitions
│   │   ├── parsers/             # Subcommand parsers
│   │   ├── storage/             # Cloud storage adaptors
│   │   ├── main.py              # Unified CLI entry point
│   │   ├── source_detector.py   # Auto-detects source type
│   │   ├── create_command.py    # Unified `create` command
│   │   ├── config_validator.py  # Config validation
│   │   ├── unified_scraper.py   # Multi-source orchestrator
│   │   └── unified_skill_builder.py  # Skill merging
│   ├── mcp/                     # MCP server
│   │   ├── server.py            # Main MCP server
│   │   ├── server_fastmcp.py    # FastMCP implementation
│   │   └── tools/               # MCP tools (10 files)
│   ├── sync/                    # Sync monitoring (Pydantic)
│   ├── benchmark/               # Benchmarking framework
│   ├── embedding/               # FastAPI embedding server
│   └── workflows/               # 68 YAML workflow presets
├── tests/                       # ~143 test files (pytest)
├── configs/                     # Preset JSON scraping configs
├── docs/                        # Documentation
├── templates/                   # GitHub Actions, etc.
├── scripts/                     # Utility scripts
└── pyproject.toml               # Project configuration
```

---

## Setup & Installation

### Required: Install in Editable Mode

```bash
# ALWAYS run this first — tests hard-exit if package not installed
pip install -e .

# With dev tools (pytest, ruff, mypy, coverage)
pip install -e ".[dev]"

# With all optional dependencies
pip install -e ".[all]"
```

**Note:** `tests/conftest.py` checks that `skill_seekers` is importable and calls `sys.exit(1)` if not.

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required for AI enhancement
ANTHROPIC_API_KEY=sk-ant-...

# Optional: LLM platforms
GOOGLE_API_KEY=...      # Gemini
OPENAI_API_KEY=...      # OpenAI/ChatGPT

# Optional: GitHub (increases rate limits)
GITHUB_TOKEN=...

# MCP Server config
MCP_TRANSPORT=http
MCP_PORT=8765
```

---

## Build / Test / Lint Commands

### Testing

```bash
# Run ALL tests (required before commits)
pytest tests/ -v

# Run single test file
pytest tests/test_scraper_features.py -v

# Run single test function
pytest tests/test_scraper_features.py::test_detect_language -v

# Run single test class method
pytest tests/test_adaptors/test_claude_adaptor.py::TestClaudeAdaptor::test_package -v

# Skip slow/integration tests
pytest tests/ -v -m "not slow and not integration"

# With coverage
pytest tests/ --cov=src/skill_seekers --cov-report=term
```

### Linting & Formatting

```bash
# Lint (ruff)
ruff check src/ tests/
ruff check src/ tests/ --fix

# Format (ruff)
ruff format --check src/ tests/
ruff format src/ tests/

# Type check (mypy)
mypy src/skill_seekers --show-error-codes --pretty
```

### Pytest Configuration

From `pyproject.toml`:
- `addopts = "-v --tb=short --strict-markers"`
- `asyncio_mode = "auto"`
- `asyncio_default_fixture_loop_scope = "function"`

**Test markers:** `slow`, `integration`, `e2e`, `venv`, `bootstrap`, `benchmark`, `asyncio`

**Test count:** 123 test files (107 in `tests/`, 16 in `tests/test_adaptors/`)

---

## CLI Usage

### Core Commands

```bash
# Unified create command (auto-detects source type)
skill-seekers create https://docs.react.dev/
skill-seekers create facebook/react
skill-seekers create manual.pdf
skill-seekers create notebook.ipynb

# Package for specific platform
skill-seekers package output/react --target claude      # Claude AI (ZIP)
skill-seekers package output/react --target gemini      # Gemini (tar.gz)
skill-seekers package output/react --target openai      # OpenAI
skill-seekers package output/react --target cursor      # .cursorrules

# Multi-source unified scraping
skill-seekers create configs/react_unified.json
```

### All 20+ Commands

| Command | Description |
|---------|-------------|
| `create` | Unified create (auto-detects source) |
| `scan` | AI-detect project tech stack and emit configs |
| `doctor` | Health check for dependencies and configuration |
| `scrape` | Scrape documentation website |
| `github` | Scrape GitHub repository |
| `pdf` | Extract from PDF |
| `word` | Extract from Word (.docx) |
| `epub` | Extract from EPUB |
| `video` | Extract from video |
| `jupyter` | Extract from Jupyter notebook |
| `html` | Extract from local HTML |
| `openapi` | Extract from OpenAPI spec |
| `asciidoc` | Extract from AsciiDoc |
| `pptx` | Extract from PowerPoint |
| `rss` | Extract from RSS/Atom feed |
| `manpage` | Extract from man pages |
| `confluence` | Extract from Confluence |
| `notion` | Extract from Notion |
| `chat` | Extract from Slack/Discord |
| `unified` | Multi-source scraping |
| `analyze` | Analyze local codebase |
| `enhance` | AI enhancement |
| `package` | Package skill |
| `upload` | Upload to platform |
| `install-agent` | Install to AI agent |

---

## Code Style & Conventions

### Formatting Rules (ruff)

- **Line length:** 100 characters
- **Target Python:** 3.10+
- **Enabled lint rules:** E, W, F, I, B, C4, UP, ARG, SIM
- **Ignored rules:** E501, F541, ARG002, B007, I001, SIM114

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files | `snake_case.py` | `source_detector.py` |
| Classes | `PascalCase` | `SkillAdaptor`, `ClaudeAdaptor` |
| Functions | `snake_case` | `get_adaptor()`, `detect_language()` |
| Constants | `UPPER_CASE` | `ADAPTORS`, `DEFAULT_CHUNK_TOKENS` |
| Private | `_prefix` | `_read_existing_content()` |

### Type Hints

- Gradual typing with modern syntax
- Use `str | None` not `Optional[str]`
- Use `list[str]` not `List[str]`
- MyPy config: `disallow_untyped_defs = false`, `check_untyped_defs = true`

### Docstrings

- Module-level docstring on every file
- Google-style for public functions/classes
- Include `Args:`, `Returns:`, `Raises:` sections

### Error Handling

```python
# Use specific exceptions
raise ValueError("Invalid config: missing 'sources'")
raise RuntimeError("Scraping failed after 3 retries")

# Chain exceptions
try:
    ...
except Exception as e:
    raise RuntimeError(f"Failed to process {source}") from e

# Guard optional imports
try:
    from .claude import ClaudeAdaptor
except ImportError:
    ClaudeAdaptor = None
```

### Import Patterns

```python
# Standard library → third-party → first-party
import os
import sys
from pathlib import Path

import requests
from beautifulsoup4 import BeautifulSoup

from skill_seekers.cli.adaptors import ClaudeAdaptor
from skill_seekers.cli.source_detector import SourceDetector

# Guard optional imports
try:
    from .gemini import GeminiAdaptor
except ImportError:
    GeminiAdaptor = None

# Re-exports (use noqa)
from .base import SkillAdaptor, SkillMetadata  # noqa: F401
```

---

## Key Architectural Patterns

### 1. Adaptor (Strategy) Pattern

All platform logic in `cli/adaptors/`. Each adaptor inherits `SkillAdaptor`:

```python
from skill_seekers.cli.adaptors.base import SkillAdaptor, SkillMetadata

class ClaudeAdaptor(SkillAdaptor):
    PLATFORM = "claude"
    PLATFORM_NAME = "Claude AI (Anthropic)"
    
    def format_skill_md(self, skill_dir: Path, metadata: SkillMetadata) -> str:
        """Format SKILL.md with YAML frontmatter"""
        ...
    
    def package(self, skill_dir: Path, output_path: Path, ...) -> Path:
        """Package as ZIP with SKILL.md, references/, scripts/"""
        ...
    
    def upload(self, package_path: Path, api_key: str) -> str:
        """Upload to Claude API"""
        ...
```

**Registered in:** `cli/adaptors/__init__.py` → `ADAPTORS` dict

### 2. Scraper Pattern

Each source type has 3 files:

```
cli/<type>_scraper.py      # Main scraper class + main()
arguments/<type>.py        # CLI argument definitions
parsers/<type>_parser.py   # ArgumentParser setup
```

**Example:** `pdf_scraper.py` → `PdfToSkillConverter` class

**Registered in:**
- `parsers/__init__.py` → `PARSERS` list
- `main.py` → `COMMAND_MODULES` dict
- `config_validator.py` → `VALID_SOURCE_TYPES` set

### 3. Unified Pipeline

**`unified_scraper.py`** orchestrates multi-source scraping:

```python
class UnifiedScraper:
    def __init__(self, config_path: str, merge_mode: str = "rule-based"):
        self.config = load_config(config_path)
        self.scraped_data = {
            "documentation": [],
            "github": [],
            "pdf": [],
            # ... 18 source types
        }
    
    def run(self) -> Path:
        # 1. Scrape all sources
        for source in self.config["sources"]:
            self._scrape_source(source)
        
        # 2. Merge (pairwise synthesis or generic)
        merged = self._merge_sources()
        
        # 3. Build unified skill
        return self._build_skill(merged)
```

**`unified_skill_builder.py`** uses:
- **Pairwise synthesis** for docs+github+pdf combos
- **`_generic_merge()`** for other combinations

### 4. Source Detection

**`source_detector.py`** auto-detects from user input:

```python
class SourceDetector:
    @classmethod
    def detect(cls, source: str) -> SourceInfo:
        # Check file extensions
        if source.endswith(".pdf"):
            return cls._detect_pdf(source)
        if source.endswith(".ipynb"):
            return cls._detect_jupyter(source)
        
        # Check GitHub patterns
        if cls.GITHUB_REPO_PATTERN.match(source):
            return cls._detect_github(source)
        
        # Check URLs
        parsed = urlparse(source)
        if parsed.scheme in ("http", "https"):
            return cls._detect_web(source)
        
        # Check local directories
        if os.path.isdir(source):
            return cls._detect_local(source)
```

### 5. MCP Tools

**`mcp/tools/`** grouped by category:

- `scrape_tools.py` — Scraping tools
- `package_tools.py` — Packaging tools
- `enhance_tools.py` — Enhancement tools
- `install_tools.py` — Installation tools
- `vector_db_tools.py` — Vector DB tools
- `workflow_tools.py` — Workflow tools

**`scrape_generic_tool`** handles all new source types dynamically.

---

## Configuration

### Unified Config Format

```json
{
  "name": "react-skill",
  "description": "React documentation skill",
  "sources": [
    {
      "type": "documentation",
      "url": "https://react.dev/",
      "config": {
        "max_pages": 100,
        "include_patterns": ["**/*.md"],
        "exclude_patterns": ["**/blog/**"]
      }
    },
    {
      "type": "github",
      "repo": "facebook/react",
      "config": {
        "include": ["src/", "packages/"],
        "exclude": ["**/*.test.tsx"]
      }
    }
  ],
  "merge_mode": "rule-based",
  "output": "output/react"
}
```

### Valid Source Types

```python
VALID_SOURCE_TYPES = {
    "documentation", "github", "pdf", "local", "word",
    "video", "epub", "jupyter", "html", "openapi",
    "asciidoc", "pptx", "confluence", "notion", "rss",
    "manpage", "chat"
}
```

### Merge Modes

- **`rule-based`** — Deterministic merging with conflict resolution rules
- **`claude-enhanced`** — AI-powered merging (requires `ANTHROPIC_API_KEY`)

---

## Git Workflow

### Branch Structure

```
main (production, protected)
  ↑
  │ (maintainer merges only)
  │
development (integration, default PR target)
  ↑
  │ (all contributor PRs)
  │
feature branches
```

### PR Process

1. Fork and clone
2. Create feature branch from `development`
3. Make changes, commit, push
4. Create PR targeting **`development`** (NOT `main`)
5. Wait for tests + review

```bash
git checkout development
git pull upstream development
git checkout -b my-feature
# ... make changes
git commit -m "Add feature X"
git push origin my-feature
# Create PR → development
```

---

## Testing Practices

### Test Organization

```
tests/
├── conftest.py              # Fixtures, setup
├── test_adaptors/           # Adaptor tests (16 files)
├── test_scraper_features.py # Core scraper tests
├── test_source_detector.py  # Source detection tests
├── test_config_validation.py # Config validation
├── test_mcp_*.py            # MCP tests
├── test_*_e2e.py            # End-to-end tests
└── fixtures/                # Test fixtures
```

### Test Patterns

```python
import pytest
from skill_seekers.cli.source_detector import SourceDetector

class TestSourceDetector:
    """Test source detection"""
    
    def test_detect_pdf(self, tmp_path):
        """Test PDF detection"""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.touch()
        
        result = SourceDetector.detect(str(pdf_file))
        assert result.type == "pdf"
    
    @pytest.mark.asyncio
    async def test_async_scraping(self):
        """Test async scraping"""
        # asyncio_mode = "auto" — decorator often implicit
        ...
    
    @pytest.mark.slow
    def test_slow_operation(self):
        """Mark slow tests for optional skipping"""
        ...
    
    @pytest.mark.integration
    def test_external_api(self):
        """Mark integration tests requiring external services"""
        ...
```

### Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_config(tmp_path):
    """Create sample config file"""
    config = {
        "name": "test-skill",
        "sources": [{"type": "documentation", "url": "https://example.com"}]
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    return str(config_file)

@pytest.fixture
def mock_response():
    """Mock HTTP response"""
    class MockResponse:
        status_code = 200
        text = "<html><body>Test</body></html>"
    return MockResponse()
```

---

## Development Guidelines

### Before Commits

```bash
# 1. Lint
ruff check src/ tests/
ruff format --check src/ tests/

# 2. Type check
mypy src/skill_seekers

# 3. Test (ALL must pass)
pytest tests/ -v
```

### Adding New Source Types

1. Create scraper: `cli/<type>_scraper.py` with `<Type>ToSkillConverter` class
2. Create arguments: `arguments/<type>.py`
3. Create parser: `parsers/<type>_parser.py`
4. Register in `parsers/__init__.py` → `PARSERS`
5. Register in `main.py` → `COMMAND_MODULES`
6. Add to `config_validator.py` → `VALID_SOURCE_TYPES`
7. Add detection to `source_detector.py`
8. Add to `unified_scraper.py` → `scraped_data` dict
9. Write tests in `tests/test_<type>_scraper.py`

### Adding New Platform Adaptors

1. Create adaptor: `cli/adaptors/<platform>.py` inheriting `SkillAdaptor`
2. Implement: `format_skill_md()`, `package()`, `upload()`
3. Register in `cli/adaptors/__init__.py` → `ADAPTORS` dict
4. Add to `package_skill.py` → target mapping
5. Write tests in `tests/test_adaptors/test_<platform>.py`

### Adding New MCP Tools

1. Create tool in `mcp/tools/<category>_tools.py`
2. Use `@mcp.tool()` decorator
3. Register in `mcp/server.py` or `mcp/server_fastmcp.py`
4. Write tests in `tests/test_mcp_*.py`

---

## Common Issues & Solutions

### Tests Fail with Import Error

**Problem:** `ModuleNotFoundError: No module named 'skill_seekers'`

**Solution:** Install in editable mode first:
```bash
pip install -e .
```

### Optional Dependency Missing

**Problem:** `ImportError: No module named 'mammoth'`

**Solution:** Install optional dependency:
```bash
pip install "skill-seekers[docx]"
# or
pip install "skill-seekers[all]"
```

### Rate Limiting

**Problem:** GitHub API rate limited (60/hour anonymous)

**Solution:** Set `GITHUB_TOKEN` in `.env`:
```bash
GITHUB_TOKEN=ghp_...
```

### Async Scraping Issues

**Problem:** Event loop errors in async tests

**Solution:** Use `@pytest.mark.asyncio` decorator (auto mode enabled)

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project config, dependencies, tool settings |
| `src/skill_seekers/cli/main.py` | Unified CLI entry point |
| `src/skill_seekers/cli/source_detector.py` | Auto-detect source types |
| `src/skill_seekers/cli/config_validator.py` | Config validation |
| `src/skill_seekers/cli/unified_scraper.py` | Multi-source orchestrator |
| `src/skill_seekers/cli/adaptors/base.py` | Adaptor interface |
| `src/skill_seekers/cli/adaptors/__init__.py` | Adaptor registry |
| `src/skill_seekers/mcp/server.py` | MCP server |
| `tests/conftest.py` | Test fixtures |
| `AGENTS.md` | Quick reference for AI agents |

---

## Version & Release

- **Current version:** 3.3.0 (from `pyproject.toml`)
- **Version source:** `src/skill_seekers/_version.py` reads from `pyproject.toml`
- **Release process:** Tag → GitHub Actions → PyPI publish
- **Changelog:** `CHANGELOG.md` (Keep a Changelog format)

---

## Related Repositories

| Repository | Purpose |
|------------|---------|
| [Skill_Seekers](https://github.com/yusufkaraaslan/Skill_Seekers) | Core CLI & MCP (this repo) |
| [skillseekersweb](https://github.com/yusufkaraaslan/skillseekersweb) | Website & docs |
| [skill-seekers-configs](https://github.com/yusufkaraaslan/skill-seekers-configs) | Community configs |
| [skill-seekers-action](https://github.com/yusufkaraaslan/skill-seekers-action) | GitHub Action |
| [skill-seekers-plugin](https://github.com/yusufkaraaslan/skill-seekers-plugin) | Claude Code plugin |
| [homebrew-skill-seekers](https://github.com/yusufkaraaslan/homebrew-skill-seekers) | Homebrew tap |

---

## Quick Commands Cheat Sheet

```bash
# Setup
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with API keys

# Development
ruff check src/ tests/ --fix
ruff format src/ tests/
mypy src/skill_seekers
pytest tests/ -v

# Test subsets
pytest tests/test_adaptors/ -v
pytest tests/ -m "not slow and not integration"
pytest tests/ --cov=src/skill_seekers

# Usage
skill-seekers create https://docs.python.org/
skill-seekers package output/python --target claude
skill-seekers create configs/react_unified.json
```
