# AGENTS.md - Skill Seekers

This file provides essential guidance for AI coding agents working with the Skill Seekers codebase.

---

## Project Overview

**Skill Seekers** is a Python CLI tool that converts documentation websites, GitHub repositories, and PDF files into AI-ready skills for LLM platforms. It supports 4 target platforms:

- **Claude AI** (ZIP + YAML format)
- **Google Gemini** (tar.gz format)
- **OpenAI ChatGPT** (ZIP + Vector Store)
- **Generic Markdown** (universal ZIP export)

**Current Version:** 2.7.4
**Python Version:** 3.10+ required
**License:** MIT
**Website:** https://skillseekersweb.com/

### Core Workflow

1. **Scrape Phase** - Crawl documentation/GitHub/PDF sources
2. **Build Phase** - Organize content into categorized references
3. **Enhancement Phase** - AI-powered quality improvements (optional)
4. **Package Phase** - Create platform-specific packages
5. **Upload Phase** - Auto-upload to target platform (optional)

---

## Project Structure

```
/mnt/1ece809a-2821-4f10-aecb-fcdf34760c0b/Git/Skill_Seekers/
├── src/skill_seekers/              # Main source code (src/ layout)
│   ├── cli/                        # CLI tools and commands
│   │   ├── adaptors/               # Platform adaptors (Strategy pattern)
│   │   │   ├── base.py             # Abstract base class
│   │   │   ├── claude.py           # Claude AI adaptor
│   │   │   ├── gemini.py           # Google Gemini adaptor
│   │   │   ├── openai.py           # OpenAI ChatGPT adaptor
│   │   │   └── markdown.py         # Generic Markdown adaptor
│   │   ├── main.py                 # Unified CLI entry point
│   │   ├── doc_scraper.py          # Documentation scraper
│   │   ├── github_scraper.py       # GitHub repository scraper
│   │   ├── pdf_scraper.py          # PDF extraction
│   │   ├── unified_scraper.py      # Multi-source scraping
│   │   ├── codebase_scraper.py     # Local codebase analysis (C2.x/C3.x)
│   │   ├── enhance_skill_local.py  # AI enhancement (LOCAL mode)
│   │   ├── package_skill.py        # Skill packager
│   │   ├── upload_skill.py         # Upload to platforms
│   │   └── ...                     # 50+ CLI modules
│   └── mcp/                        # MCP server integration
│       ├── server_fastmcp.py       # FastMCP server (main)
│       ├── server.py               # Legacy server
│       └── tools/                  # MCP tool implementations
├── tests/                          # Test suite (76 test files)
├── configs/                        # Preset configuration files
├── docs/                           # Documentation (54 markdown files)
├── .github/workflows/              # CI/CD workflows
├── pyproject.toml                  # Main project configuration
└── requirements.txt                # Pinned dependencies
```

---

## Build and Development Commands

### Setup (REQUIRED before any development)

```bash
# Install in editable mode (REQUIRED for tests due to src/ layout)
pip install -e .

# Install with all platform dependencies
pip install -e ".[all-llms]"

# Install specific platforms only
pip install -e ".[gemini]"    # Google Gemini support
pip install -e ".[openai]"    # OpenAI ChatGPT support
pip install -e ".[mcp]"       # MCP server dependencies
```

**CRITICAL:** The project uses a `src/` layout. Tests WILL FAIL unless you install with `pip install -e .` first.

### Building

```bash
# Build package using uv (recommended)
uv build

# Or using standard build
python -m build

# Publish to PyPI
uv publish
```

### Running Tests

**CRITICAL:** Never skip tests - all tests must pass before commits.

```bash
# All tests (must run pip install -e . first!)
pytest tests/ -v

# Specific test file
pytest tests/test_scraper_features.py -v
pytest tests/test_mcp_fastmcp.py -v

# With coverage
pytest tests/ --cov=src/skill_seekers --cov-report=term --cov-report=html

# Single test
pytest tests/test_scraper_features.py::test_detect_language -v

# E2E tests
pytest tests/test_e2e_three_stream_pipeline.py -v
```

**Test Architecture:**
- 76 test files covering all features
- CI Matrix: Ubuntu + macOS, Python 3.10-3.13
- 1200+ tests passing
- Test markers: `slow`, `integration`, `e2e`, `venv`, `bootstrap`

---

## Code Style Guidelines

### Linting and Formatting

```bash
# Run ruff linter
ruff check src/ tests/

# Run ruff formatter check
ruff format --check src/ tests/

# Auto-fix issues
ruff check src/ tests/ --fix
ruff format src/ tests/

# Run mypy type checker
mypy src/skill_seekers --show-error-codes --pretty
```

### Style Rules (from pyproject.toml)

- **Line length:** 100 characters
- **Target Python:** 3.10+
- **Enabled rules:** E, W, F, I, B, C4, UP, ARG, SIM
- **Import sorting:** isort style with `skill_seekers` as first-party

### Code Conventions

1. **Use type hints** where practical (gradual typing approach)
2. **Docstrings:** Use Google-style or standard docstrings
3. **Error handling:** Use specific exceptions, provide helpful messages
4. **Async code:** Use `asyncio`, mark tests with `@pytest.mark.asyncio`
5. **File naming:** Use snake_case for all Python files

---

## Architecture Patterns

### Platform Adaptor Pattern (Strategy Pattern)

All platform-specific logic is encapsulated in adaptors:

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
```

### CLI Architecture (Git-style)

Entry point: `src/skill_seekers/cli/main.py`

The CLI uses subcommands that delegate to existing modules:

```python
# skill-seekers scrape --config react.json
# Transforms to: doc_scraper.main() with modified sys.argv
```

**Available subcommands:**
- `config` - Configuration wizard
- `scrape` - Documentation scraping
- `github` - GitHub repository scraping
- `pdf` - PDF extraction
- `unified` - Multi-source scraping
- `analyze` - Local codebase analysis
- `enhance` - AI enhancement
- `package` - Package skill
- `upload` - Upload to platform
- `install` / `install-agent` - Complete workflow

### MCP Server Architecture

Two implementations:
- `server_fastmcp.py` - Modern, decorator-based (recommended, 708 lines)
- `server.py` - Legacy implementation (2200 lines)

Tools are organized by category:
- Config tools (3)
- Scraping tools (8)
- Packaging tools (4)
- Splitting tools (2)
- Source tools (4)

---

## Testing Instructions

### Test Categories

| Marker | Description |
|--------|-------------|
| `slow` | Tests taking >5 seconds |
| `integration` | Requires external services (APIs) |
| `e2e` | End-to-end tests (resource-intensive) |
| `venv` | Requires virtual environment setup |
| `bootstrap` | Bootstrap skill specific |

### Running Specific Test Categories

```bash
# Skip slow tests
pytest tests/ -v -m "not slow"

# Run only integration tests
pytest tests/ -v -m integration

# Run E2E tests
pytest tests/ -v -m e2e
```

### Test Configuration (pytest.ini in pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short --strict-markers"
asyncio_mode = "auto"
```

---

## Git Workflow

### Branch Structure

```
main (production)
  ↑
  │ (only maintainer merges)
  │
development (integration) ← default branch for PRs
  ↑
  │ (all contributor PRs go here)
  │
feature branches
```

- **`main`** - Production, always stable, protected
- **`development`** - Active development, default for PRs
- **Feature branches** - Your work, created from `development`

### Creating a Feature Branch

```bash
# 1. Checkout development
git checkout development
git pull upstream development

# 2. Create feature branch
git checkout -b my-feature

# 3. Make changes, commit, push
git add .
git commit -m "Add my feature"
git push origin my-feature

# 4. Create PR targeting 'development' branch
```

---

## CI/CD Configuration

### GitHub Actions Workflows

**`.github/workflows/tests.yml`:**
- Runs on: push/PR to `main` and `development`
- Lint job: Ruff + MyPy
- Test matrix: Ubuntu + macOS, Python 3.10-3.12
- Coverage: Uploads to Codecov

**`.github/workflows/release.yml`:**
- Triggered on version tags
- Builds and publishes to PyPI

### Pre-commit Checks (Manual)

```bash
# Before committing, run:
ruff check src/ tests/
ruff format --check src/ tests/
pytest tests/ -v -x  # Stop on first failure
```

---

## Security Considerations

### API Keys and Secrets

1. **Never commit API keys** to the repository
2. **Use environment variables:**
   - `ANTHROPIC_API_KEY` - Claude AI
   - `GOOGLE_API_KEY` - Google Gemini
   - `OPENAI_API_KEY` - OpenAI
   - `GITHUB_TOKEN` - GitHub API
3. **Configuration storage:**
   - Stored at `~/.config/skill-seekers/config.json`
   - Permissions: 600 (owner read/write only)

### Rate Limit Handling

- GitHub API has rate limits (5000 requests/hour for authenticated)
- The tool has built-in rate limit handling with retry logic
- Use `--non-interactive` flag for CI/CD environments

### Custom API Endpoints

Support for Claude-compatible APIs (e.g., GLM-4.7):

```bash
export ANTHROPIC_API_KEY=your-glm-47-api-key
export ANTHROPIC_BASE_URL=https://glm-4-7-endpoint.com/v1
```

---

## Common Development Tasks

### Adding a New CLI Command

1. Create module in `src/skill_seekers/cli/my_command.py`
2. Implement `main()` function with argument parsing
3. Add entry point in `pyproject.toml`:
   ```toml
   [project.scripts]
   skill-seekers-my-command = "skill_seekers.cli.my_command:main"
   ```
4. Add subcommand handler in `src/skill_seekers/cli/main.py`
5. Add tests in `tests/test_my_command.py`

### Adding a New Platform Adaptor

1. Create `src/skill_seekers/cli/adaptors/my_platform.py`
2. Inherit from `SkillAdaptor` base class
3. Implement required methods: `package()`, `upload()`, `enhance()`
4. Register in `src/skill_seekers/cli/adaptors/__init__.py`
5. Add optional dependencies in `pyproject.toml`
6. Add tests in `tests/test_adaptors/`

### Adding an MCP Tool

1. Implement tool logic in `src/skill_seekers/mcp/tools/category_tools.py`
2. Register in `src/skill_seekers/mcp/server_fastmcp.py`
3. Add test in `tests/test_mcp_fastmcp.py`

---

## Documentation

### Project Documentation

- **README.md** - Main project documentation
- **README.zh-CN.md** - Chinese translation
- **CLAUDE.md** - Detailed implementation guidance
- **QUICKSTART.md** - Quick start guide
- **CONTRIBUTING.md** - Contribution guidelines
- **docs/** - Comprehensive documentation (54 files)

### Configuration Documentation

Preset configs are in `configs/` directory:
- `godot.json` - Godot Engine
- `react.json` - React
- `vue.json` - Vue.js
- `fastapi.json` - FastAPI
- `*_unified.json` - Multi-source configs

---

## Troubleshooting

### Common Issues

**ImportError: No module named 'skill_seekers'**
- Solution: Run `pip install -e .`

**Tests failing with "package not installed"**
- Solution: Ensure you ran `pip install -e .` in the correct virtual environment

**MCP server import errors**
- Solution: Install with `pip install -e ".[mcp]"`

**Type checking failures**
- MyPy is configured to be lenient (gradual typing)
- Focus on critical paths, not full coverage

### Getting Help

- Check **TROUBLESHOOTING.md** for detailed solutions
- Review **docs/FAQ.md** for common questions
- Visit https://skillseekersweb.com/ for documentation
- Open an issue on GitHub with:
  - Clear title and description
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details (OS, Python version)
  - Error messages and stack traces

---

## Key Dependencies

### Core Dependencies
- `requests>=2.32.5` - HTTP requests
- `beautifulsoup4>=4.14.2` - HTML parsing
- `PyGithub>=2.5.0` - GitHub API
- `GitPython>=3.1.40` - Git operations
- `httpx>=0.28.1` - Async HTTP
- `anthropic>=0.76.0` - Claude AI API
- `PyMuPDF>=1.24.14` - PDF processing
- `pydantic>=2.12.3` - Data validation
- `click>=8.3.0` - CLI framework

### Optional Dependencies
- `mcp>=1.25` - MCP server
- `google-generativeai>=0.8.0` - Gemini support
- `openai>=1.0.0` - OpenAI support

### Dev Dependencies
- `pytest>=8.4.2` - Testing framework
- `pytest-asyncio>=0.24.0` - Async test support
- `pytest-cov>=7.0.0` - Coverage
- `ruff>=0.14.13` - Linting/formatting
- `mypy>=1.19.1` - Type checking

---

*This document is maintained for AI coding agents. For human contributors, see README.md and CONTRIBUTING.md.*
