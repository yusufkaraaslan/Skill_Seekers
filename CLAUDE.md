# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Project Overview

**Skill Seekers** is a Python tool that converts documentation websites, GitHub repositories, and PDFs into LLM skills. It supports 4 platforms: Claude AI, Google Gemini, OpenAI ChatGPT, and Generic Markdown.

**Current Version:** v2.5.1
**Python Version:** 3.10+ required
**Status:** Production-ready, published on PyPI

## 🏗️ Architecture

### Core Design Pattern: Platform Adaptors

The codebase uses the **Strategy Pattern** with a factory method to support multiple LLM platforms:

```
src/skill_seekers/cli/adaptors/
├── __init__.py          # Factory: get_adaptor(target)
├── base_adaptor.py      # Abstract base class
├── claude_adaptor.py    # Claude AI (ZIP + YAML)
├── gemini_adaptor.py    # Google Gemini (tar.gz)
├── openai_adaptor.py    # OpenAI ChatGPT (ZIP + Vector Store)
└── markdown_adaptor.py  # Generic Markdown (ZIP)
```

**Key Methods:**
- `package(skill_dir, output_path)` - Platform-specific packaging
- `upload(package_path, api_key)` - Platform-specific upload
- `enhance(skill_dir, mode)` - AI enhancement with platform-specific models

### Data Flow (5 Phases)

1. **Scrape Phase** (`doc_scraper.py:scrape_all()`)
   - BFS traversal from base_url
   - Output: `output/{name}_data/pages/*.json`

2. **Build Phase** (`doc_scraper.py:build_skill()`)
   - Load pages → Categorize → Extract patterns
   - Output: `output/{name}/SKILL.md` + `references/*.md`

3. **Enhancement Phase** (optional, `enhance_skill_local.py`)
   - LLM analyzes references → Rewrites SKILL.md
   - Platform-specific models (Sonnet 4, Gemini 2.0, GPT-4o)

4. **Package Phase** (`package_skill.py` → adaptor)
   - Platform adaptor packages in appropriate format
   - Output: `.zip` or `.tar.gz`

5. **Upload Phase** (optional, `upload_skill.py` → adaptor)
   - Upload via platform API

### File Structure (src/ layout)

```
src/skill_seekers/
├── cli/                        # CLI tools
│   ├── main.py                 # Git-style CLI dispatcher
│   ├── doc_scraper.py          # Main scraper (~790 lines)
│   ├── github_scraper.py       # GitHub repo analysis
│   ├── pdf_scraper.py          # PDF extraction
│   ├── unified_scraper.py      # Multi-source scraping
│   ├── enhance_skill_local.py  # AI enhancement (local)
│   ├── package_skill.py        # Skill packager
│   ├── upload_skill.py         # Upload to platforms
│   ├── install_skill.py        # Complete workflow automation
│   ├── install_agent.py        # Install to AI agent directories
│   └── adaptors/               # Platform adaptor architecture
│       ├── __init__.py
│       ├── base_adaptor.py
│       ├── claude_adaptor.py
│       ├── gemini_adaptor.py
│       ├── openai_adaptor.py
│       └── markdown_adaptor.py
└── mcp/                        # MCP server integration
    ├── server.py               # FastMCP server (stdio + HTTP)
    └── tools/                  # 18 MCP tool implementations
```

## 🛠️ Development Commands

### Setup

```bash
# Install in editable mode (required before tests due to src/ layout)
pip install -e .

# Install with all platform dependencies
pip install -e ".[all-llms]"

# Install specific platforms
pip install -e ".[gemini]"   # Google Gemini
pip install -e ".[openai]"   # OpenAI ChatGPT
```

### Running Tests

**CRITICAL: Never skip tests** - User requires all tests to pass before commits.

```bash
# All tests (must run pip install -e . first!)
pytest tests/ -v

# Specific test file
pytest tests/test_scraper_features.py -v

# Multi-platform tests
pytest tests/test_install_multiplatform.py -v

# With coverage
pytest tests/ --cov=src/skill_seekers --cov-report=term --cov-report=html

# Single test
pytest tests/test_scraper_features.py::test_detect_language -v

# MCP server tests
pytest tests/test_mcp_fastmcp.py -v
```

**Test Architecture:**
- 46 test files covering all features
- CI Matrix: Ubuntu + macOS, Python 3.10-3.13
- 700+ tests passing
- Must run `pip install -e .` before tests (src/ layout requirement)

### Building & Publishing

```bash
# Build package (using uv - recommended)
uv build

# Or using build
python -m build

# Publish to PyPI
uv publish

# Or using twine
python -m twine upload dist/*
```

### Testing CLI Commands

```bash
# Test scraping (dry run)
skill-seekers scrape --config configs/react.json --dry-run

# Test multi-platform packaging
skill-seekers package output/react/ --target gemini --dry-run

# Test MCP server (stdio mode)
python -m skill_seekers.mcp.server

# Test MCP server (HTTP mode)
python -m skill_seekers.mcp.server --transport http --port 8765
```

## 🔧 Key Implementation Details

### CLI Architecture (Git-style)

**Entry point:** `src/skill_seekers/cli/main.py`

The unified CLI modifies `sys.argv` and calls existing `main()` functions to maintain backward compatibility:

```python
# Example: skill-seekers scrape --config react.json
# Transforms to: doc_scraper.main() with modified sys.argv
```

**Subcommands:** scrape, github, pdf, unified, enhance, package, upload, estimate, install

### Platform Adaptor Usage

```python
from skill_seekers.cli.adaptors import get_adaptor

# Get platform-specific adaptor
adaptor = get_adaptor('gemini')  # or 'claude', 'openai', 'markdown'

# Package skill
adaptor.package(skill_dir='output/react/', output_path='output/')

# Upload to platform
adaptor.upload(
    package_path='output/react-gemini.tar.gz',
    api_key=os.getenv('GOOGLE_API_KEY')
)

# AI enhancement
adaptor.enhance(skill_dir='output/react/', mode='api')
```

### Smart Categorization Algorithm

Located in `doc_scraper.py:smart_categorize()`:
- Scores pages against category keywords
- 3 points for URL match, 2 for title, 1 for content
- Threshold of 2+ for categorization
- Auto-infers categories from URL segments if none provided
- Falls back to "other" category

### Language Detection

Located in `doc_scraper.py:detect_language()`:
1. CSS class attributes (`language-*`, `lang-*`)
2. Heuristics (keywords like `def`, `const`, `func`)

### Configuration File Structure

Configs (`configs/*.json`) define scraping behavior:

```json
{
  "name": "framework-name",
  "description": "When to use this skill",
  "base_url": "https://docs.example.com/",
  "selectors": {
    "main_content": "article",  // CSS selector
    "title": "h1",
    "code_blocks": "pre code"
  },
  "url_patterns": {
    "include": ["/docs"],
    "exclude": ["/blog"]
  },
  "categories": {
    "getting_started": ["intro", "quickstart"],
    "api": ["api", "reference"]
  },
  "rate_limit": 0.5,
  "max_pages": 500
}
```

## 🧪 Testing Guidelines

### Test Coverage Requirements

- Core features: 100% coverage required
- Platform adaptors: Each platform has dedicated tests
- MCP tools: All 18 tools must be tested
- Integration tests: End-to-end workflows

### Key Test Files

- `test_scraper_features.py` - Core scraping functionality
- `test_mcp_server.py` - MCP integration (18 tools)
- `test_mcp_fastmcp.py` - FastMCP framework
- `test_unified.py` - Multi-source scraping
- `test_github_scraper.py` - GitHub analysis
- `test_pdf_scraper.py` - PDF extraction
- `test_install_multiplatform.py` - Multi-platform packaging
- `test_integration.py` - End-to-end workflows
- `test_install_skill.py` - One-command install
- `test_install_agent.py` - AI agent installation

## 🌐 Environment Variables

```bash
# Claude AI (default platform)
export ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini (optional)
export GOOGLE_API_KEY=AIza...

# OpenAI ChatGPT (optional)
export OPENAI_API_KEY=sk-...

# GitHub (for higher rate limits)
export GITHUB_TOKEN=ghp_...

# Private config repositories (optional)
export GITLAB_TOKEN=glpat-...
export GITEA_TOKEN=...
export BITBUCKET_TOKEN=...
```

## 📦 Package Structure (pyproject.toml)

### Entry Points

```toml
[project.scripts]
skill-seekers = "skill_seekers.cli.main:main"
skill-seekers-scrape = "skill_seekers.cli.doc_scraper:main"
skill-seekers-github = "skill_seekers.cli.github_scraper:main"
skill-seekers-pdf = "skill_seekers.cli.pdf_scraper:main"
skill-seekers-unified = "skill_seekers.cli.unified_scraper:main"
skill-seekers-enhance = "skill_seekers.cli.enhance_skill_local:main"
skill-seekers-package = "skill_seekers.cli.package_skill:main"
skill-seekers-upload = "skill_seekers.cli.upload_skill:main"
skill-seekers-estimate = "skill_seekers.cli.estimate_pages:main"
skill-seekers-install = "skill_seekers.cli.install_skill:main"
skill-seekers-install-agent = "skill_seekers.cli.install_agent:main"
```

### Optional Dependencies

```toml
[project.optional-dependencies]
gemini = ["google-generativeai>=0.8.0"]
openai = ["openai>=1.0.0"]
all-llms = ["google-generativeai>=0.8.0", "openai>=1.0.0"]
dev = ["pytest>=8.4.2", "pytest-asyncio>=0.24.0", "pytest-cov>=7.0.0"]
```

## 🚨 Critical Development Notes

### Must Run Before Tests

```bash
# REQUIRED: Install package before running tests
pip install -e .

# Why: src/ layout requires package installation
# Without this, imports will fail
```

### Never Skip Tests

Per user instructions in `~/.claude/CLAUDE.md`:
- "never skipp any test. always make sure all test pass"
- All 700+ tests must pass before commits
- Run full test suite: `pytest tests/ -v`

### Platform-Specific Dependencies

Platform dependencies are optional:
```bash
# Install only what you need
pip install skill-seekers[gemini]  # Gemini support
pip install skill-seekers[openai]  # OpenAI support
pip install skill-seekers[all-llms]  # All platforms
```

### Git Workflow

- Main branch: `main`
- Current branch: `development`
- Always create feature branches from `development`
- Clean status currently (no uncommitted changes)

## 🔌 MCP Integration

### MCP Server (18 Tools)

**Transport modes:**
- stdio: Claude Code, VS Code + Cline
- HTTP: Cursor, Windsurf, IntelliJ IDEA

**Core Tools (9):**
1. `list_configs` - List preset configurations
2. `generate_config` - Generate config from docs URL
3. `validate_config` - Validate config structure
4. `estimate_pages` - Estimate page count
5. `scrape_docs` - Scrape documentation
6. `package_skill` - Package to .zip (supports `--target`)
7. `upload_skill` - Upload to platform (supports `--target`)
8. `enhance_skill` - AI enhancement with platform support
9. `install_skill` - Complete workflow automation

**Extended Tools (9):**
10. `scrape_github` - GitHub repository analysis
11. `scrape_pdf` - PDF extraction
12. `unified_scrape` - Multi-source scraping
13. `merge_sources` - Merge docs + code
14. `detect_conflicts` - Find discrepancies
15. `split_config` - Split large configs
16. `generate_router` - Generate router skills
17. `add_config_source` - Register git repos
18. `fetch_config` - Fetch configs from git

### Starting MCP Server

```bash
# stdio mode (Claude Code, VS Code + Cline)
python -m skill_seekers.mcp.server

# HTTP mode (Cursor, Windsurf, IntelliJ)
python -m skill_seekers.mcp.server --transport http --port 8765
```

## 📋 Common Workflows

### Adding a New Platform

1. Create adaptor in `src/skill_seekers/cli/adaptors/{platform}_adaptor.py`
2. Inherit from `BaseAdaptor`
3. Implement `package()`, `upload()`, `enhance()` methods
4. Add to factory in `adaptors/__init__.py`
5. Add optional dependency to `pyproject.toml`
6. Add tests in `tests/test_install_multiplatform.py`

### Adding a New Feature

1. Implement in appropriate CLI module
2. Add entry point to `pyproject.toml` if needed
3. Add tests in `tests/test_{feature}.py`
4. Run full test suite: `pytest tests/ -v`
5. Update CHANGELOG.md
6. Commit only when all tests pass

### Debugging Test Failures

```bash
# Run specific failing test with verbose output
pytest tests/test_file.py::test_name -vv

# Run with print statements visible
pytest tests/test_file.py -s

# Run with coverage to see what's not tested
pytest tests/test_file.py --cov=src/skill_seekers --cov-report=term-missing
```

## 📚 Key Code Locations

**Documentation Scraper** (`src/skill_seekers/cli/doc_scraper.py`):
- `is_valid_url()` - URL validation
- `extract_content()` - Content extraction
- `detect_language()` - Code language detection
- `extract_patterns()` - Pattern extraction
- `smart_categorize()` - Smart categorization
- `infer_categories()` - Category inference
- `generate_quick_reference()` - Quick reference generation
- `create_enhanced_skill_md()` - SKILL.md generation
- `scrape_all()` - Main scraping loop
- `main()` - Entry point

**Platform Adaptors** (`src/skill_seekers/cli/adaptors/`):
- `__init__.py` - Factory function
- `base_adaptor.py` - Abstract base class
- `claude_adaptor.py` - Claude AI implementation
- `gemini_adaptor.py` - Google Gemini implementation
- `openai_adaptor.py` - OpenAI ChatGPT implementation
- `markdown_adaptor.py` - Generic Markdown implementation

**MCP Server** (`src/skill_seekers/mcp/`):
- `server.py` - FastMCP-based server
- `tools/` - MCP tool implementations

## 🎯 Project-Specific Best Practices

1. **Always use platform adaptors** - Never hardcode platform-specific logic
2. **Test all platforms** - Changes must work for all 4 platforms
3. **Maintain backward compatibility** - Legacy configs must still work
4. **Document API changes** - Update CHANGELOG.md for every release
5. **Keep dependencies optional** - Platform-specific deps are optional
6. **Use src/ layout** - Proper package structure with `pip install -e .`
7. **Run tests before commits** - Per user instructions, never skip tests

## 📖 Additional Documentation

**For Users:**
- [README.md](README.md) - Complete user documentation
- [BULLETPROOF_QUICKSTART.md](BULLETPROOF_QUICKSTART.md) - Beginner guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

**For Developers:**
- [CHANGELOG.md](CHANGELOG.md) - Release history
- [FLEXIBLE_ROADMAP.md](FLEXIBLE_ROADMAP.md) - 134 tasks across 22 feature groups
- [docs/UNIFIED_SCRAPING.md](docs/UNIFIED_SCRAPING.md) - Multi-source scraping
- [docs/MCP_SETUP.md](docs/MCP_SETUP.md) - MCP server setup

## 🎓 Understanding the Codebase

### Why src/ Layout?

Modern Python best practice (PEP 517/518):
- Prevents accidental imports from repo root
- Forces proper package installation
- Better isolation between package and tests
- Required: `pip install -e .` before running tests

### Why Platform Adaptors?

Strategy pattern benefits:
- Single codebase supports 4 platforms
- Platform-specific optimizations (format, APIs, models)
- Easy to add new platforms (implement BaseAdaptor)
- Clean separation of concerns
- Testable in isolation

### Why Git-style CLI?

User experience benefits:
- Familiar to developers (like `git`)
- Single entry point: `skill-seekers`
- Backward compatible: individual tools still work
- Cleaner than multiple separate commands
- Easier to document and teach

## 🔍 Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Scraping (sync) | 15-45 min | First time, thread-based |
| Scraping (async) | 5-15 min | 2-3x faster with `--async` |
| Building | 1-3 min | Fast rebuild from cache |
| Re-building | <1 min | With `--skip-scrape` |
| Enhancement (LOCAL) | 30-60 sec | Uses Claude Code Max |
| Enhancement (API) | 20-40 sec | Requires API key |
| Packaging | 5-10 sec | Final .zip creation |

## 🎉 Recent Achievements

**v2.5.1 (Latest):**
- Fixed critical PyPI packaging bug (missing adaptors module)
- 100% of multi-platform features working

**v2.5.0:**
- Multi-platform support (4 LLM platforms)
- Platform adaptor architecture
- 18 MCP tools (up from 9)
- Complete feature parity across platforms
- 700+ tests passing

**v2.0.0:**
- Unified multi-source scraping
- Conflict detection between docs and code
- 5 unified configs (React, Django, FastAPI, Godot)
- 22 unified tests passing
