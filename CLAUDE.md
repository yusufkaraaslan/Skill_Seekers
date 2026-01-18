# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Project Overview

**Skill Seekers** is a Python tool that converts documentation websites, GitHub repositories, and PDFs into LLM skills. It supports 4 platforms: Claude AI, Google Gemini, OpenAI ChatGPT, and Generic Markdown.

**Current Version:** v2.7.0
**Python Version:** 3.10+ required
**Status:** Production-ready, published on PyPI
**Website:** https://skillseekersweb.com/ - Browse configs, share, and access documentation

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
├── cli/                              # CLI tools
│   ├── main.py                       # Git-style CLI dispatcher
│   ├── doc_scraper.py                # Main scraper (~790 lines)
│   ├── github_scraper.py             # GitHub repo analysis
│   ├── pdf_scraper.py                # PDF extraction
│   ├── unified_scraper.py            # Multi-source scraping
│   ├── codebase_scraper.py           # Local codebase analysis (C2.x)
│   ├── unified_codebase_analyzer.py  # Three-stream GitHub+local analyzer
│   ├── enhance_skill_local.py        # AI enhancement (LOCAL mode)
│   ├── enhance_status.py             # Enhancement status monitoring
│   ├── package_skill.py              # Skill packager
│   ├── upload_skill.py               # Upload to platforms
│   ├── install_skill.py              # Complete workflow automation
│   ├── install_agent.py              # Install to AI agent directories
│   ├── pattern_recognizer.py         # C3.1 Design pattern detection
│   ├── test_example_extractor.py     # C3.2 Test example extraction
│   ├── how_to_guide_builder.py       # C3.3 How-to guide generation
│   ├── config_extractor.py           # C3.4 Configuration extraction
│   ├── generate_router.py            # C3.5 Router skill generation
│   ├── code_analyzer.py              # Multi-language code analysis
│   ├── api_reference_builder.py      # API documentation builder
│   ├── dependency_analyzer.py        # Dependency graph analysis
│   └── adaptors/                     # Platform adaptor architecture
│       ├── __init__.py
│       ├── base_adaptor.py
│       ├── claude_adaptor.py
│       ├── gemini_adaptor.py
│       ├── openai_adaptor.py
│       └── markdown_adaptor.py
└── mcp/                              # MCP server integration
    ├── server.py                     # FastMCP server (stdio + HTTP)
    └── tools/                        # 18 MCP tool implementations
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
# Test configuration wizard (NEW: v2.7.0)
skill-seekers config --show                          # Show current configuration
skill-seekers config --github                        # GitHub token setup
skill-seekers config --test                          # Test connections

# Test resume functionality (NEW: v2.7.0)
skill-seekers resume --list                          # List resumable jobs
skill-seekers resume --clean                         # Clean up old jobs

# Test GitHub scraping with profiles (NEW: v2.7.0)
skill-seekers github --repo facebook/react --profile personal    # Use specific profile
skill-seekers github --repo owner/repo --non-interactive         # CI/CD mode

# Test scraping (dry run)
skill-seekers scrape --config configs/react.json --dry-run

# Test codebase analysis (C2.x features)
skill-seekers codebase --directory . --output output/codebase/

# Test pattern detection (C3.1)
skill-seekers patterns --file src/skill_seekers/cli/code_analyzer.py

# Test how-to guide generation (C3.3)
skill-seekers how-to-guides output/test_examples.json --output output/guides/

# Test enhancement status monitoring
skill-seekers enhance-status output/react/ --watch

# Test multi-platform packaging
skill-seekers package output/react/ --target gemini --dry-run

# Test MCP server (stdio mode)
python -m skill_seekers.mcp.server_fastmcp

# Test MCP server (HTTP mode)
python -m skill_seekers.mcp.server_fastmcp --transport http --port 8765
```

## 🔧 Key Implementation Details

### CLI Architecture (Git-style)

**Entry point:** `src/skill_seekers/cli/main.py`

The unified CLI modifies `sys.argv` and calls existing `main()` functions to maintain backward compatibility:

```python
# Example: skill-seekers scrape --config react.json
# Transforms to: doc_scraper.main() with modified sys.argv
```

**Subcommands:** scrape, github, pdf, unified, codebase, enhance, enhance-status, package, upload, estimate, install, install-agent, patterns, how-to-guides

**Recent Additions:**
- `codebase` - Local codebase analysis without GitHub API (C2.x + C3.x features)
- `enhance-status` - Monitor background/daemon enhancement processes
- `patterns` - Detect design patterns in code (C3.1)
- `how-to-guides` - Generate educational guides from tests (C3.3)

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

### C3.x Codebase Analysis Features

The project has comprehensive codebase analysis capabilities (C3.1-C3.8):

**C3.1 Design Pattern Detection** (`pattern_recognizer.py`):
- Detects 10 common patterns: Singleton, Factory, Observer, Strategy, Decorator, Builder, Adapter, Command, Template Method, Chain of Responsibility
- Supports 9 languages: Python, JavaScript, TypeScript, C++, C, C#, Go, Rust, Java
- Three detection levels: surface (fast), deep (balanced), full (thorough)
- 87% precision, 80% recall on real-world projects

**C3.2 Test Example Extraction** (`test_example_extractor.py`):
- Extracts real usage examples from test files
- Categories: instantiation, method_call, config, setup, workflow
- AST-based for Python, regex-based for 8 other languages
- Quality filtering with confidence scoring

**C3.3 How-To Guide Generation** (`how_to_guide_builder.py`):
- Transforms test workflows into educational guides
- 5 AI enhancements: step descriptions, troubleshooting, prerequisites, next steps, use cases
- Dual-mode AI: API (fast) or LOCAL (free with Claude Code Max)
- 4 grouping strategies: AI tutorial group, file path, test name, complexity

**C3.4 Configuration Pattern Extraction** (`config_extractor.py`):
- Extracts configuration patterns from codebases
- Identifies config files, env vars, CLI arguments
- AI enhancement for better organization

**C3.5 Architectural Overview** (`generate_router.py`):
- Generates comprehensive ARCHITECTURE.md files
- Router skill generation for large documentation
- Quality improvements: 6.5/10 → 8.5/10 (+31%)
- Integrates GitHub metadata, issues, labels

**C3.6 AI Enhancement** (Claude API integration):
- Enhances C3.1-C3.5 with AI-powered insights
- Pattern explanations and improvement suggestions
- Test example context and best practices
- Guide enhancement with troubleshooting and prerequisites

**C3.7 Architectural Pattern Detection** (`architectural_pattern_detector.py`):
- Detects 8 architectural patterns (MVC, MVVM, MVP, Repository, etc.)
- Framework detection (Django, Flask, Spring, React, Angular, etc.)
- Multi-file analysis with directory structure patterns
- Evidence-based detection with confidence scoring

**C3.8 Standalone Codebase Scraper** (`codebase_scraper.py`):
```bash
# All C3.x features enabled by default, use --skip-* to disable
skill-seekers codebase --directory /path/to/repo

# Disable specific features
skill-seekers codebase --directory . --skip-patterns --skip-how-to-guides

# Legacy flags (deprecated but still work)
skill-seekers codebase --directory . --build-api-reference --build-dependency-graph
```

- Generates 300+ line standalone SKILL.md files from codebases
- All C3.x features integrated (patterns, tests, guides, config, architecture)
- Complete codebase analysis without documentation scraping

**Key Architecture Decision (BREAKING in v2.5.2):**
- Changed from opt-in (`--build-*`) to opt-out (`--skip-*`) flags
- All analysis features now ON by default for maximum value
- Backward compatibility warnings for deprecated flags

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
# Main unified CLI
skill-seekers = "skill_seekers.cli.main:main"

# Individual tool entry points
skill-seekers-config = "skill_seekers.cli.config_command:main"                # NEW: v2.7.0 Configuration wizard
skill-seekers-resume = "skill_seekers.cli.resume_command:main"                # NEW: v2.7.0 Resume interrupted jobs
skill-seekers-scrape = "skill_seekers.cli.doc_scraper:main"
skill-seekers-github = "skill_seekers.cli.github_scraper:main"
skill-seekers-pdf = "skill_seekers.cli.pdf_scraper:main"
skill-seekers-unified = "skill_seekers.cli.unified_scraper:main"
skill-seekers-codebase = "skill_seekers.cli.codebase_scraper:main"           # NEW: C2.x
skill-seekers-enhance = "skill_seekers.cli.enhance_skill_local:main"
skill-seekers-enhance-status = "skill_seekers.cli.enhance_status:main"       # NEW: Status monitoring
skill-seekers-package = "skill_seekers.cli.package_skill:main"
skill-seekers-upload = "skill_seekers.cli.upload_skill:main"
skill-seekers-estimate = "skill_seekers.cli.estimate_pages:main"
skill-seekers-install = "skill_seekers.cli.install_skill:main"
skill-seekers-install-agent = "skill_seekers.cli.install_agent:main"
skill-seekers-patterns = "skill_seekers.cli.pattern_recognizer:main"         # NEW: C3.1
skill-seekers-how-to-guides = "skill_seekers.cli.how_to_guide_builder:main" # NEW: C3.3
```

### Optional Dependencies

```toml
[project.optional-dependencies]
gemini = ["google-generativeai>=0.8.0"]
openai = ["openai>=1.0.0"]
all-llms = ["google-generativeai>=0.8.0", "openai>=1.0.0"]

[dependency-groups]  # PEP 735 (replaces tool.uv.dev-dependencies)
dev = [
    "pytest>=8.4.2",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=7.0.0",
    "coverage>=7.11.0",
]
```

**Note:** Project uses PEP 735 `dependency-groups` instead of deprecated `tool.uv.dev-dependencies`.

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

### AI Enhancement Modes

AI enhancement transforms basic skills (2-3/10) into production-ready skills (8-9/10). Two modes available:

**API Mode** (default if ANTHROPIC_API_KEY is set):
- Direct Claude API calls (fast, efficient)
- Cost: ~$0.15-$0.30 per skill
- Perfect for CI/CD automation
- Requires: `export ANTHROPIC_API_KEY=sk-ant-...`

**LOCAL Mode** (fallback if no API key):
- Uses Claude Code CLI (your existing Max plan)
- Free! No API charges
- 4 execution modes:
  - Headless (default): Foreground, waits for completion
  - Background (`--background`): Returns immediately
  - Daemon (`--daemon`): Fully detached with nohup
  - Terminal (`--interactive-enhancement`): Opens new terminal (macOS)
- Status monitoring: `skill-seekers enhance-status output/react/ --watch`
- Timeout configuration: `--timeout 300` (seconds)

**Force Mode** (default ON since v2.5.2):
- Skip all confirmations automatically
- Perfect for CI/CD, batch processing
- Use `--no-force` to enable prompts if needed

```bash
# API mode (if ANTHROPIC_API_KEY is set)
skill-seekers enhance output/react/

# LOCAL mode (no API key needed)
skill-seekers enhance output/react/ --mode LOCAL

# Background with status monitoring
skill-seekers enhance output/react/ --background
skill-seekers enhance-status output/react/ --watch

# Force mode OFF (enable prompts)
skill-seekers enhance output/react/ --no-force
```

See `docs/ENHANCEMENT_MODES.md` for detailed documentation.

### Git Workflow

- Main branch: `main`
- Current branch: `development`
- Always create feature branches from `development`
- Feature branch naming: `feature/{task-id}-{description}` or `feature/{category}`

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
python -m skill_seekers.mcp.server_fastmcp

# HTTP mode (Cursor, Windsurf, IntelliJ)
python -m skill_seekers.mcp.server_fastmcp --transport http --port 8765
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

**Codebase Analysis** (`src/skill_seekers/cli/`):
- `codebase_scraper.py` - Main CLI for local codebase analysis
- `code_analyzer.py` - Multi-language AST parsing (9 languages)
- `api_reference_builder.py` - API documentation generation
- `dependency_analyzer.py` - NetworkX-based dependency graphs
- `pattern_recognizer.py` - C3.1 design pattern detection
- `test_example_extractor.py` - C3.2 test example extraction
- `how_to_guide_builder.py` - C3.3 guide generation
- `config_extractor.py` - C3.4 configuration extraction
- `generate_router.py` - C3.5 router skill generation
- `unified_codebase_analyzer.py` - Three-stream GitHub+local analyzer

**AI Enhancement** (`src/skill_seekers/cli/`):
- `enhance_skill_local.py` - LOCAL mode enhancement (4 execution modes)
- `enhance_skill.py` - API mode enhancement
- `enhance_status.py` - Status monitoring for background processes
- `ai_enhancer.py` - Shared AI enhancement logic
- `guide_enhancer.py` - C3.3 guide AI enhancement
- `config_enhancer.py` - C3.4 config AI enhancement

**Platform Adaptors** (`src/skill_seekers/cli/adaptors/`):
- `__init__.py` - Factory function
- `base_adaptor.py` - Abstract base class
- `claude_adaptor.py` - Claude AI implementation
- `gemini_adaptor.py` - Google Gemini implementation
- `openai_adaptor.py` - OpenAI ChatGPT implementation
- `markdown_adaptor.py` - Generic Markdown implementation

**MCP Server** (`src/skill_seekers/mcp/`):
- `server.py` - FastMCP-based server
- `tools/` - 18 MCP tool implementations

**Configuration & Rate Limit Management** (NEW: v2.7.0 - `src/skill_seekers/cli/`):
- `config_manager.py` - Multi-token configuration system (~490 lines)
  - `ConfigManager` class - Singleton pattern for global config access
  - `add_github_profile()` - Add GitHub profile with token and strategy
  - `get_github_token()` - Smart fallback chain (CLI → Env → Config → Prompt)
  - `get_next_profile()` - Profile switching for rate limit handling
  - `save_progress()` / `load_progress()` - Job resumption support
  - `cleanup_old_progress()` - Auto-cleanup of old jobs (7 days default)
- `config_command.py` - Interactive configuration wizard (~400 lines)
  - `main_menu()` - 7-option main menu with navigation
  - `github_token_menu()` - GitHub profile management
  - `add_github_profile()` - Guided token setup with browser integration
  - `api_keys_menu()` - API key configuration for Claude/Gemini/OpenAI
  - `test_connections()` - Connection testing for tokens and API keys
- `rate_limit_handler.py` - Smart rate limit detection and handling (~450 lines)
  - `RateLimitHandler` class - Strategy pattern for rate limit handling
  - `check_upfront()` - Upfront rate limit check before starting
  - `check_response()` - Real-time detection from API responses
  - `handle_rate_limit()` - Execute strategy (prompt/wait/switch/fail)
  - `try_switch_profile()` - Automatic profile switching
  - `wait_for_reset()` - Countdown timer with live progress
  - `show_countdown_timer()` - Live terminal countdown display
- `resume_command.py` - Resume interrupted scraping jobs (~150 lines)
  - `list_resumable_jobs()` - Display all jobs with progress details
  - `resume_job()` - Resume from saved checkpoint
  - `clean_old_jobs()` - Cleanup old progress files

**GitHub Integration** (Modified for v2.7.0 - `src/skill_seekers/cli/`):
- `github_fetcher.py` - Integrated rate limit handler
  - Constructor now accepts `interactive` and `profile_name` parameters
  - `fetch()` - Added upfront rate limit check
  - All API calls check responses for rate limits
  - Raises `RateLimitError` when rate limit cannot be handled
- `github_scraper.py` - Added CLI flags
  - `--non-interactive` flag for CI/CD mode (fail fast)
  - `--profile` flag to select GitHub profile from config
  - Config supports `interactive` and `github_profile` keys

## 🎯 Project-Specific Best Practices

1. **Always use platform adaptors** - Never hardcode platform-specific logic
2. **Test all platforms** - Changes must work for all 4 platforms
3. **Maintain backward compatibility** - Legacy configs must still work
4. **Document API changes** - Update CHANGELOG.md for every release
5. **Keep dependencies optional** - Platform-specific deps are optional
6. **Use src/ layout** - Proper package structure with `pip install -e .`
7. **Run tests before commits** - Per user instructions, never skip tests

## 📖 Additional Documentation

**Official Website:**
- [SkillSeekersWeb.com](https://skillseekersweb.com/) - Browse 24+ preset configs, share configs, complete documentation

**For Users:**
- [README.md](README.md) - Complete user documentation
- [BULLETPROOF_QUICKSTART.md](BULLETPROOF_QUICKSTART.md) - Beginner guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

**For Developers:**
- [CHANGELOG.md](CHANGELOG.md) - Release history
- [ROADMAP.md](ROADMAP.md) - 136 tasks across 10 categories
- [docs/UNIFIED_SCRAPING.md](docs/UNIFIED_SCRAPING.md) - Multi-source scraping
- [docs/MCP_SETUP.md](docs/MCP_SETUP.md) - MCP server setup
- [docs/ENHANCEMENT_MODES.md](docs/ENHANCEMENT_MODES.md) - AI enhancement modes
- [docs/PATTERN_DETECTION.md](docs/PATTERN_DETECTION.md) - C3.1 pattern detection
- [docs/THREE_STREAM_STATUS_REPORT.md](docs/THREE_STREAM_STATUS_REPORT.md) - Three-stream architecture
- [docs/MULTI_LLM_SUPPORT.md](docs/MULTI_LLM_SUPPORT.md) - Multi-platform support

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

### Three-Stream GitHub Architecture

The `unified_codebase_analyzer.py` splits GitHub repositories into three independent streams:

**Stream 1: Code Analysis** (C3.x features)
- Deep AST parsing (9 languages)
- Design pattern detection (C3.1)
- Test example extraction (C3.2)
- How-to guide generation (C3.3)
- Configuration extraction (C3.4)
- Architectural overview (C3.5)
- API reference + dependency graphs

**Stream 2: Documentation**
- README, CONTRIBUTING, LICENSE
- docs/ directory markdown files
- Wiki pages (if available)
- CHANGELOG and version history

**Stream 3: Community Insights**
- GitHub metadata (stars, forks, watchers)
- Issue analysis (top problems and solutions)
- PR trends and contributor stats
- Release history
- Label-based topic detection

**Key Benefits:**
- Unified interface for GitHub URLs and local paths
- Analysis depth control: 'basic' (1-2 min) or 'c3x' (20-60 min)
- Enhanced router generation with GitHub context
- Smart keyword extraction weighted by GitHub labels (2x weight)
- 81 E2E tests passing (0.44 seconds)

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

**v2.6.0 (Latest - January 14, 2026):**
- **C3.x Codebase Analysis Suite Complete** (C3.1-C3.8)
- Multi-platform support with platform adaptor architecture
- 18 MCP tools fully functional
- 700+ tests passing
- Unified multi-source scraping maturity

**C3.x Series (Complete - Code Analysis Features):**
- **C3.1:** Design pattern detection (10 GoF patterns, 9 languages, 87% precision)
- **C3.2:** Test example extraction (5 categories, AST-based for Python)
- **C3.3:** How-to guide generation with AI enhancement (5 improvements)
- **C3.4:** Configuration pattern extraction (env vars, config files, CLI args)
- **C3.5:** Architectural overview & router skill generation
- **C3.6:** AI enhancement for patterns and test examples (Claude API integration)
- **C3.7:** Architectural pattern detection (8 patterns, framework-aware)
- **C3.8:** Standalone codebase scraper (300+ line SKILL.md from code alone)

**v2.5.2:**
- UX Improvement: Analysis features now default ON with --skip-* flags (BREAKING)
- Router quality improvements: 6.5/10 → 8.5/10 (+31%)
- All 107 codebase analysis tests passing

**v2.5.0:**
- Multi-platform support (Claude, Gemini, OpenAI, Markdown)
- Platform adaptor architecture
- 18 MCP tools (up from 9)
- Complete feature parity across platforms

**v2.1.0:**
- Unified multi-source scraping (docs + GitHub + PDF)
- Conflict detection between sources
- 427 tests passing

**v1.0.0:**
- Production release with MCP integration
- Documentation scraping with smart categorization
- 12 preset configurations
