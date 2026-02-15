# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Project Overview

**Skill Seekers** is the **universal documentation preprocessor** for AI systems. It transforms documentation websites, GitHub repositories, and PDFs into production-ready formats for **16+ platforms**: RAG pipelines (LangChain, LlamaIndex, Haystack), vector databases (Pinecone, Chroma, Weaviate, FAISS, Qdrant), AI coding assistants (Cursor, Windsurf, Cline, Continue.dev), and LLM platforms (Claude, Gemini, OpenAI).

**Current Version:** v3.0.0
**Python Version:** 3.10+ required
**Status:** Production-ready, published on PyPI
**Website:** https://skillseekersweb.com/ - Browse configs, share, and access documentation

## 📚 Table of Contents

- [First Time Here?](#-first-time-here) - Start here!
- [Quick Commands](#-quick-command-reference-most-used) - Common workflows
- [Architecture](#️-architecture) - How it works
- [Development](#️-development-commands) - Building & testing
- [Testing](#-testing-guidelines) - Test strategy
- [Debugging](#-debugging-tips) - Troubleshooting
- [Contributing](#-where-to-make-changes) - How to add features

## 👋 First Time Here?

**Complete this 3-minute setup to start contributing:**

```bash
# 1. Install package in editable mode (REQUIRED for development)
pip install -e .

# 2. Verify installation
python -c "import skill_seekers; print(skill_seekers.__version__)"  # Should print: 3.0.0

# 3. Run a quick test
pytest tests/test_scraper_features.py::test_detect_language -v

# 4. You're ready! Pick a task from the roadmap:
# https://github.com/users/yusufkaraaslan/projects/2
```

**Quick Navigation:**
- Building/Testing → [Development Commands](#️-development-commands)
- Architecture → [Core Design Pattern](#️-architecture)
- Common Issues → [Common Pitfalls](#-common-pitfalls--solutions)
- Contributing → See `CONTRIBUTING.md`

## ⚡ Quick Command Reference (Most Used)

**First time setup:**
```bash
pip install -e .  # REQUIRED before running tests or CLI
```

**Running tests (NEVER skip - user requirement):**
```bash
pytest tests/ -v  # All tests
pytest tests/test_scraper_features.py -v  # Single file
pytest tests/ --cov=src/skill_seekers --cov-report=html  # With coverage
```

**Code quality checks (matches CI):**
```bash
ruff check src/ tests/  # Lint
ruff format src/ tests/  # Format
mypy src/skill_seekers  # Type check
```

**Common workflows:**
```bash
# NEW unified create command (auto-detects source type)
skill-seekers create https://docs.react.dev/ -p quick
skill-seekers create facebook/react -p standard
skill-seekers create ./my-project -p comprehensive
skill-seekers create tutorial.pdf

# Legacy commands (still supported)
skill-seekers scrape --config configs/react.json
skill-seekers github --repo facebook/react
skill-seekers analyze --directory . --comprehensive

# Package for LLM platforms
skill-seekers package output/react/ --target claude
skill-seekers package output/react/ --target gemini
```

**RAG Pipeline workflows:**
```bash
# LangChain Documents
skill-seekers package output/react/ --format langchain

# LlamaIndex TextNodes
skill-seekers package output/react/ --format llama-index

# Haystack Documents
skill-seekers package output/react/ --format haystack

# ChromaDB direct upload
skill-seekers package output/react/ --format chroma --upload

# FAISS export
skill-seekers package output/react/ --format faiss

# Weaviate/Qdrant upload (requires API keys)
skill-seekers package output/react/ --format weaviate --upload
skill-seekers package output/react/ --format qdrant --upload
```

**AI Coding Assistant workflows:**
```bash
# Cursor IDE
skill-seekers package output/react/ --target claude
cp output/react-claude/SKILL.md .cursorrules

# Windsurf
cp output/react-claude/SKILL.md .windsurf/rules/react.md

# Cline (VS Code)
cp output/react-claude/SKILL.md .clinerules

# Continue.dev (universal IDE)
python examples/continue-dev-universal/context_server.py
# Configure in ~/.continue/config.json
```

**Cloud Storage:**
```bash
# Upload to S3
skill-seekers cloud upload --provider s3 --bucket my-skills output/react.zip

# Upload to GCS
skill-seekers cloud upload --provider gcs --bucket my-skills output/react.zip

# Upload to Azure
skill-seekers cloud upload --provider azure --container my-skills output/react.zip
```

## 🏗️ Architecture

### Core Design Pattern: Platform Adaptors

The codebase uses the **Strategy Pattern** with a factory method to support **16 platforms** across 4 categories:

```
src/skill_seekers/cli/adaptors/
├── __init__.py          # Factory: get_adaptor(target/format)
├── base.py              # Abstract base class
# LLM Platforms (3)
├── claude.py            # Claude AI (ZIP + YAML)
├── gemini.py            # Google Gemini (tar.gz)
├── openai.py            # OpenAI ChatGPT (ZIP + Vector Store)
# RAG Frameworks (3)
├── langchain.py         # LangChain Documents
├── llama_index.py       # LlamaIndex TextNodes
├── haystack.py          # Haystack Documents
# Vector Databases (5)
├── chroma.py            # ChromaDB
├── faiss_helpers.py     # FAISS
├── qdrant.py            # Qdrant
├── weaviate.py          # Weaviate
# AI Coding Assistants (4 - via Claude format + config files)
# - Cursor, Windsurf, Cline, Continue.dev
# Generic (1)
├── markdown.py          # Generic Markdown (ZIP)
└── streaming_adaptor.py # Streaming data ingest
```

**Key Methods:**
- `package(skill_dir, output_path)` - Platform-specific packaging
- `upload(package_path, api_key)` - Platform-specific upload (where applicable)
- `enhance(skill_dir, mode)` - AI enhancement with platform-specific models
- `export(skill_dir, format)` - Export to RAG/vector DB formats

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

### File Structure (src/ layout) - Key Files Only

```
src/skill_seekers/
├── cli/                              # All CLI commands
│   ├── main.py                       # ⭐ Git-style CLI dispatcher
│   ├── doc_scraper.py                # ⭐ Main scraper (~790 lines)
│   │   ├── scrape_all()              # BFS traversal engine
│   │   ├── smart_categorize()        # Category detection
│   │   └── build_skill()             # SKILL.md generation
│   ├── github_scraper.py             # GitHub repo analysis
│   ├── codebase_scraper.py           # ⭐ Local analysis (C2.x+C3.x)
│   ├── package_skill.py              # Platform packaging
│   ├── unified_scraper.py            # Multi-source scraping
│   ├── unified_codebase_analyzer.py  # Three-stream GitHub+local analyzer
│   ├── enhance_skill_local.py        # AI enhancement (LOCAL mode)
│   ├── enhance_status.py             # Enhancement status monitoring
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
│   ├── signal_flow_analyzer.py       # C3.10 Signal flow analysis (Godot)
│   ├── pdf_scraper.py                # PDF extraction
│   └── adaptors/                     # ⭐ Platform adaptor pattern
│       ├── __init__.py               # Factory: get_adaptor()
│       ├── base_adaptor.py           # Abstract base
│       ├── claude_adaptor.py         # Claude AI
│       ├── gemini_adaptor.py         # Google Gemini
│       ├── openai_adaptor.py         # OpenAI ChatGPT
│       ├── markdown_adaptor.py       # Generic Markdown
│       ├── langchain.py              # LangChain RAG
│       ├── llama_index.py            # LlamaIndex RAG
│       ├── haystack.py               # Haystack RAG
│       ├── chroma.py                 # ChromaDB
│       ├── faiss_helpers.py          # FAISS
│       ├── qdrant.py                 # Qdrant
│       ├── weaviate.py               # Weaviate
│       └── streaming_adaptor.py      # Streaming data ingest
└── mcp/                              # MCP server (26 tools)
    ├── server_fastmcp.py             # FastMCP server
    └── tools/                        # Tool implementations
```

**Most Modified Files (when contributing):**
- Platform adaptors: `src/skill_seekers/cli/adaptors/{platform}.py`
- Tests: `tests/test_{feature}.py`
- Configs: `configs/{framework}.json`

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
- **1,765 tests passing** (current), up from 700+ in v2.x, growing to 1,852+ in v3.1.0
- Must run `pip install -e .` before tests (src/ layout requirement)
- Tests include create command integration tests, CLI refactor E2E tests

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
skill-seekers analyze --directory . --output output/codebase/

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

### New v3.0.0 CLI Commands

```bash
# Setup wizard (interactive configuration)
skill-seekers-setup

# Cloud storage operations
skill-seekers cloud upload --provider s3 --bucket my-bucket output/react.zip
skill-seekers cloud download --provider gcs --bucket my-bucket react.zip
skill-seekers cloud list --provider azure --container my-container

# Embedding server (for RAG pipelines)
skill-seekers embed --port 8080 --model sentence-transformers

# Sync & incremental updates
skill-seekers sync --source https://docs.react.dev/ --target output/react/
skill-seekers update --skill output/react/ --check-changes

# Quality metrics & benchmarking
skill-seekers quality --skill output/react/ --report
skill-seekers benchmark --config configs/react.json --compare-versions

# Multilingual support
skill-seekers multilang --detect output/react/
skill-seekers multilang --translate output/react/ --target zh-CN

# Streaming data ingest
skill-seekers stream --source docs/ --target output/streaming/
```

## 🔧 Key Implementation Details

### CLI Architecture (Git-style)

**Entry point:** `src/skill_seekers/cli/main.py`

The unified CLI modifies `sys.argv` and calls existing `main()` functions to maintain backward compatibility:

```python
# Example: skill-seekers scrape --config react.json
# Transforms to: doc_scraper.main() with modified sys.argv
```

**Subcommands:** create, scrape, github, pdf, unified, codebase, enhance, enhance-status, package, upload, estimate, install, install-agent, patterns, how-to-guides

### NEW: Unified `create` Command

**The recommended way to create skills** - Auto-detects source type and provides progressive help disclosure:

```bash
# Auto-detection examples
skill-seekers create https://docs.react.dev/         # → Web scraping
skill-seekers create facebook/react                  # → GitHub analysis
skill-seekers create ./my-project                    # → Local codebase
skill-seekers create tutorial.pdf                    # → PDF extraction
skill-seekers create configs/react.json              # → Multi-source

# Progressive help system
skill-seekers create --help           # Shows universal args only (13 flags)
skill-seekers create --help-web       # Shows web-specific options
skill-seekers create --help-github    # Shows GitHub-specific options
skill-seekers create --help-local     # Shows local analysis options
skill-seekers create --help-pdf       # Shows PDF extraction options
skill-seekers create --help-advanced  # Shows advanced/rare options
skill-seekers create --help-all       # Shows all 120+ flags

# Universal flags work for ALL sources
skill-seekers create <source> -p quick                    # Preset (-p shortcut)
skill-seekers create <source> --enhance-level 2           # AI enhancement (0-3)
skill-seekers create <source> --chunk-for-rag             # RAG chunking
skill-seekers create <source> --dry-run                   # Preview
```

**Key improvements:**
- **Single command** replaces scrape/github/analyze for most use cases
- **Smart detection** - No need to specify source type
- **Progressive disclosure** - Default help shows 13 flags, detailed help available
- **-p shortcut** - Quick preset selection (`-p quick|standard|comprehensive`)
- **Universal features** - RAG chunking, dry-run, presets work everywhere

**Recent Additions:**
- `create` - **NEW:** Unified command with auto-detection and progressive help
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
# Quick analysis (1-2 min, basic features only)
skill-seekers analyze --directory /path/to/repo --quick

# Comprehensive analysis (20-60 min, all features + AI)
skill-seekers analyze --directory . --comprehensive

# With AI enhancement (auto-detects API or LOCAL)
skill-seekers analyze --directory . --enhance

# Granular AI enhancement control (NEW)
skill-seekers analyze --directory . --enhance-level 1  # SKILL.md only
skill-seekers analyze --directory . --enhance-level 2  # + Architecture + Config + Docs
skill-seekers analyze --directory . --enhance-level 3  # Full enhancement (all features)

# Disable specific features
skill-seekers analyze --directory . --skip-patterns --skip-how-to-guides
```

- Generates 300+ line standalone SKILL.md files from codebases
- All C3.x features integrated (patterns, tests, guides, config, architecture, docs)
- Complete codebase analysis without documentation scraping
- **NEW**: Granular AI enhancement control with `--enhance-level` (0-3)

**C3.9 Project Documentation Extraction** (`codebase_scraper.py`):
- Extracts and categorizes all markdown files from the project
- Auto-detects categories: overview, architecture, guides, workflows, features, etc.
- Integrates documentation into SKILL.md with summaries
- AI enhancement (level 2+) adds topic extraction and cross-references
- Controlled by depth: surface=raw copy, deep=parse+summarize, full=AI-enhanced
- Default ON, use `--skip-docs` to disable

**C3.10 Signal Flow Analysis for Godot Projects** (`signal_flow_analyzer.py`):
- Complete signal flow analysis system for event-driven Godot architectures
- Signal declaration extraction (detects `signal` keyword declarations)
- Connection mapping (tracks `.connect()` calls with targets and methods)
- Emission tracking (finds `.emit()` and `emit_signal()` calls)
- Real-world metrics: 208 signals, 634 connections, 298 emissions in test project
- Signal density metrics (signals per file)
- Event chain detection (signals triggering other signals)
- Signal pattern detection:
  - **EventBus Pattern** (0.90 confidence): Centralized signal hub in autoload
  - **Observer Pattern** (0.85 confidence): Multi-observer signals (3+ listeners)
  - **Event Chains** (0.80 confidence): Cascading signal propagation
- Signal-based how-to guides (C3.10.1):
  - AI-generated step-by-step usage guides (Connect → Emit → Handle)
  - Real code examples from project
  - Common usage locations
  - Parameter documentation
- Outputs: `signal_flow.json`, `signal_flow.mmd` (Mermaid diagram), `signal_reference.md`, `signal_how_to_guides.md`
- Comprehensive Godot 4.x support:
  - GDScript (.gd), Scene files (.tscn), Resources (.tres), Shaders (.gdshader)
  - GDScript test extraction (GUT, gdUnit4, WAT frameworks)
  - 396 test cases extracted in test project
  - Framework detection (Unity, Unreal, Godot)

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

### Test Markers (from pytest.ini_options)

The project uses pytest markers to categorize tests:

```bash
# Run only fast unit tests (default)
pytest tests/ -v

# Include slow tests (>5 seconds)
pytest tests/ -v -m slow

# Run integration tests (requires external services)
pytest tests/ -v -m integration

# Run end-to-end tests (resource-intensive, creates files)
pytest tests/ -v -m e2e

# Run tests requiring virtual environment setup
pytest tests/ -v -m venv

# Run bootstrap feature tests
pytest tests/ -v -m bootstrap

# Skip slow and integration tests (fastest)
pytest tests/ -v -m "not slow and not integration"
```

### Test Execution Strategy

**By default, only fast tests run**. Use markers to control test execution:

```bash
# Default: Only fast tests (skip slow/integration/e2e)
pytest tests/ -v

# Include slow tests (>5 seconds)
pytest tests/ -v -m slow

# Include integration tests (requires external services)
pytest tests/ -v -m integration

# Include resource-intensive e2e tests (creates files)
pytest tests/ -v -m e2e

# Run ONLY fast tests (explicit)
pytest tests/ -v -m "not slow and not integration and not e2e"

# Run everything (CI does this)
pytest tests/ -v -m ""
```

**When to use which:**
- **Local development:** Default (fast tests only) - `pytest tests/ -v`
- **Pre-commit:** Fast tests - `pytest tests/ -v`
- **Before PR:** Include slow + integration - `pytest tests/ -v -m "not e2e"`
- **CI validation:** All tests run automatically

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
- `conftest.py` - Test configuration (checks package installation)

## 🌐 Environment Variables

```bash
# Claude AI / Compatible APIs
# Option 1: Official Anthropic API (default)
export ANTHROPIC_API_KEY=sk-ant-...

# Option 2: GLM-4.7 Claude-compatible API (or any compatible endpoint)
export ANTHROPIC_API_KEY=your-api-key
export ANTHROPIC_BASE_URL=https://glm-4-7-endpoint.com/v1

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

**All AI enhancement features respect these settings**:
- `enhance_skill.py` - API mode SKILL.md enhancement
- `ai_enhancer.py` - C3.1/C3.2 pattern and test example enhancement
- `guide_enhancer.py` - C3.3 guide enhancement
- `config_enhancer.py` - C3.4 configuration enhancement
- `adaptors/claude.py` - Claude platform adaptor enhancement

**Note**: Setting `ANTHROPIC_BASE_URL` allows you to use any Claude-compatible API endpoint, such as GLM-4.7 (智谱 AI).

## 📦 Package Structure (pyproject.toml)

### Entry Points

```toml
[project.scripts]
# Main unified CLI
skill-seekers = "skill_seekers.cli.main:main"

# Individual tool entry points (Core)
skill-seekers-config = "skill_seekers.cli.config_command:main"                # v2.7.0 Configuration wizard
skill-seekers-resume = "skill_seekers.cli.resume_command:main"                # v2.7.0 Resume interrupted jobs
skill-seekers-scrape = "skill_seekers.cli.doc_scraper:main"
skill-seekers-github = "skill_seekers.cli.github_scraper:main"
skill-seekers-pdf = "skill_seekers.cli.pdf_scraper:main"
skill-seekers-unified = "skill_seekers.cli.unified_scraper:main"
skill-seekers-codebase = "skill_seekers.cli.codebase_scraper:main"           # C2.x Local codebase analysis
skill-seekers-enhance = "skill_seekers.cli.enhance_skill_local:main"
skill-seekers-enhance-status = "skill_seekers.cli.enhance_status:main"       # Status monitoring
skill-seekers-package = "skill_seekers.cli.package_skill:main"
skill-seekers-upload = "skill_seekers.cli.upload_skill:main"
skill-seekers-estimate = "skill_seekers.cli.estimate_pages:main"
skill-seekers-install = "skill_seekers.cli.install_skill:main"
skill-seekers-install-agent = "skill_seekers.cli.install_agent:main"
skill-seekers-patterns = "skill_seekers.cli.pattern_recognizer:main"         # C3.1 Pattern detection
skill-seekers-how-to-guides = "skill_seekers.cli.how_to_guide_builder:main" # C3.3 Guide generation

# New v3.0.0 Entry Points
skill-seekers-setup = "skill_seekers.cli.setup_wizard:main"                  # NEW: v3.0.0 Setup wizard
skill-seekers-cloud = "skill_seekers.cli.cloud_storage_cli:main"             # NEW: v3.0.0 Cloud storage
skill-seekers-embed = "skill_seekers.embedding.server:main"                  # NEW: v3.0.0 Embedding server
skill-seekers-sync = "skill_seekers.cli.sync_cli:main"                       # NEW: v3.0.0 Sync & monitoring
skill-seekers-benchmark = "skill_seekers.cli.benchmark_cli:main"             # NEW: v3.0.0 Benchmarking
skill-seekers-stream = "skill_seekers.cli.streaming_ingest:main"             # NEW: v3.0.0 Streaming ingest
skill-seekers-update = "skill_seekers.cli.incremental_updater:main"          # NEW: v3.0.0 Incremental updates
skill-seekers-multilang = "skill_seekers.cli.multilang_support:main"         # NEW: v3.0.0 Multilingual
skill-seekers-quality = "skill_seekers.cli.quality_metrics:main"             # NEW: v3.0.0 Quality metrics
```

### Optional Dependencies

**Project uses PEP 735 `[dependency-groups]` (Python 3.13+)**:
- Replaces deprecated `tool.uv.dev-dependencies`
- Dev dependencies: `[dependency-groups] dev = [...]` in pyproject.toml
- Install with: `pip install -e .` (installs only core deps)
- Install dev deps: See CI workflow or manually install pytest, ruff, mypy

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
- "never skip any test. always make sure all test pass"
- All 1,765+ tests must pass before commits (1,852+ in upcoming v3.1.0)
- Run full test suite: `pytest tests/ -v`
- New tests added for create command and CLI refactor work

### Platform-Specific Dependencies

Platform dependencies are optional (install only what you need):

```bash
# Install specific platform support
pip install -e ".[gemini]"         # Google Gemini
pip install -e ".[openai]"         # OpenAI ChatGPT
pip install -e ".[chroma]"         # ChromaDB
pip install -e ".[weaviate]"       # Weaviate
pip install -e ".[s3]"             # AWS S3
pip install -e ".[gcs]"            # Google Cloud Storage
pip install -e ".[azure]"          # Azure Blob Storage
pip install -e ".[mcp]"            # MCP integration
pip install -e ".[all]"            # Everything (16 platforms + cloud + embedding)

# Or install from PyPI:
pip install skill-seekers[gemini]    # Google Gemini support
pip install skill-seekers[openai]    # OpenAI ChatGPT support
pip install skill-seekers[all-llms]  # All LLM platforms
pip install skill-seekers[chroma]    # ChromaDB support
pip install skill-seekers[weaviate]  # Weaviate support
pip install skill-seekers[s3]        # AWS S3 support
pip install skill-seekers[all]       # All optional dependencies
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

### Enhancement Flag Consolidation (Phase 1)

**IMPORTANT CHANGE:** Three enhancement flags have been unified into a single granular control:

**Old flags (deprecated):**
- `--enhance` - Enable AI enhancement
- `--enhance-local` - Use LOCAL mode (Claude Code)
- `--api-key KEY` - Anthropic API key

**New unified flag:**
- `--enhance-level LEVEL` - Granular AI enhancement control (0-3, default: 2)
  - `0` - Disabled, no AI enhancement
  - `1` - SKILL.md only (core documentation)
  - `2` - + Architecture + Config + Docs (default, balanced)
  - `3` - Full enhancement (all features, comprehensive)

**Auto-detection:** Mode (API vs LOCAL) is auto-detected:
- If `ANTHROPIC_API_KEY` is set → API mode
- Otherwise → LOCAL mode (Claude Code Max)

**Examples:**
```bash
# Auto-detect mode, default enhancement level (2)
skill-seekers create https://docs.react.dev/

# Disable enhancement
skill-seekers create facebook/react --enhance-level 0

# SKILL.md only (fast)
skill-seekers create ./my-project --enhance-level 1

# Full enhancement (comprehensive)
skill-seekers create tutorial.pdf --enhance-level 3

# Force LOCAL mode with specific level
skill-seekers enhance output/react/ --mode LOCAL --enhance-level 2

# Background with status monitoring
skill-seekers enhance output/react/ --background
skill-seekers enhance-status output/react/ --watch
```

**Migration:** Old flags still work with deprecation warnings, will be removed in v4.0.0.

See `docs/ENHANCEMENT_MODES.md` for detailed documentation.

### Git Workflow

**Git Workflow Notes:**
- Main branch: `main`
- Development branch: `development`
- Always create feature branches from `development`
- Branch naming: `feature/{task-id}-{description}` or `feature/{category}`

**To see current status:** `git status`

### CI/CD Pipeline

The project has GitHub Actions workflows in `.github/workflows/`:

**tests.yml** - Runs on every push and PR to `main` or `development`:

1. **Lint Job** (Python 3.12, Ubuntu):
   - `ruff check src/ tests/` - Code linting with GitHub annotations
   - `ruff format --check src/ tests/` - Format validation
   - `mypy src/skill_seekers` - Type checking (continue-on-error)

2. **Test Job** (Matrix):
   - **OS:** Ubuntu + macOS
   - **Python:** 3.10, 3.11, 3.12
   - **Exclusions:** macOS + Python 3.10 (speed optimization)
   - **Steps:**
     - Install dependencies + `pip install -e .`
     - Run CLI tests (scraper, config, integration)
     - Run MCP server tests
     - Generate coverage report → Upload to Codecov

3. **Summary Job** - Single status check for branch protection
   - Ensures both lint and test jobs succeed
   - Provides single "All Checks Complete" status

**release.yml** - Triggers on version tags (e.g., `v2.9.0`):
- Builds package with `uv build`
- Publishes to PyPI with `uv publish`
- Creates GitHub release

**Local Pre-Commit Validation**

Run the same checks as CI before pushing:

```bash
# 1. Code quality (matches lint job)
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/skill_seekers

# 2. Tests (matches test job)
pip install -e .
pytest tests/ -v --cov=src/skill_seekers --cov-report=term

# 3. If all pass, you're good to push!
git push origin feature/my-feature
```

**Branch Protection Rules:**
- **main:** Requires tests + 1 review, only maintainers merge
- **development:** Requires tests to pass, default target for PRs

## 🚨 Common Pitfalls & Solutions

### 1. Import Errors
**Problem:** `ModuleNotFoundError: No module named 'skill_seekers'`

**Solution:** Must install package first due to src/ layout
```bash
pip install -e .
```

**Why:** The src/ layout prevents imports from repo root. Package must be installed.

### 2. Tests Fail with "No module named..."
**Problem:** Package not installed in test environment

**Solution:** CI runs `pip install -e .` before tests - do the same locally
```bash
pip install -e .
pytest tests/ -v
```

### 3. Platform-Specific Dependencies Not Found
**Problem:** `ModuleNotFoundError: No module named 'google.generativeai'`

**Solution:** Install platform-specific dependencies
```bash
pip install -e ".[gemini]"   # For Gemini
pip install -e ".[openai]"   # For OpenAI
pip install -e ".[all-llms]" # For all platforms
```

### 4. Git Branch Confusion
**Problem:** PR targets `main` instead of `development`

**Solution:** Always create PRs targeting `development` branch
```bash
git checkout development
git pull upstream development
git checkout -b feature/my-feature
# ... make changes ...
git push origin feature/my-feature
# Create PR: feature/my-feature → development
```

**Important:** See `CONTRIBUTING.md` for complete branch workflow.

### 5. Tests Pass Locally But Fail in CI
**Problem:** Different Python version or missing dependency

**Solution:** Test with multiple Python versions locally
```bash
# CI tests: Python 3.10, 3.11, 3.12 on Ubuntu + macOS
# Use pyenv or docker to test locally:
pyenv install 3.10.13 3.11.7 3.12.1

pyenv local 3.10.13
pip install -e . && pytest tests/ -v

pyenv local 3.11.7
pip install -e . && pytest tests/ -v

pyenv local 3.12.1
pip install -e . && pytest tests/ -v
```

### 6. Enhancement Not Working
**Problem:** AI enhancement fails or hangs

**Solutions:**
```bash
# Check if API key is set
echo $ANTHROPIC_API_KEY

# Try LOCAL mode instead (uses Claude Code Max, no API key needed)
skill-seekers enhance output/react/ --mode LOCAL

# Monitor enhancement status for background jobs
skill-seekers enhance-status output/react/ --watch
```

### 7. Rate Limit Errors from GitHub
**Problem:** `403 Forbidden` from GitHub API

**Solutions:**
```bash
# Check current rate limit
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit

# Configure multiple GitHub profiles (recommended)
skill-seekers config --github

# Use specific profile
skill-seekers github --repo owner/repo --profile work

# Test all configured tokens
skill-seekers config --test
```

### 8. Confused About Command Options
**Problem:** "Too many flags!" or "Which flags work with which sources?"

**Solution:** Use the progressive disclosure help system in the `create` command:
```bash
# Start with universal options (13 flags)
skill-seekers create --help

# Need web scraping options?
skill-seekers create --help-web

# GitHub-specific flags?
skill-seekers create --help-github

# See ALL options (120+ flags)?
skill-seekers create --help-all

# Quick preset shortcut
skill-seekers create <source> -p quick
skill-seekers create <source> -p standard
skill-seekers create <source> -p comprehensive
```

**Why:** The create command shows only relevant flags by default to reduce cognitive load.

**Legacy commands** (scrape, github, analyze) show all flags in one help screen - use them if you prefer that style.

## 🔌 MCP Integration

### MCP Server (26 Tools)

**Transport modes:**
- stdio: Claude Code, VS Code + Cline
- HTTP: Cursor, Windsurf, IntelliJ IDEA

**Core Tools (9):**
1. `list_configs` - List preset configurations
2. `generate_config` - Generate config from docs URL
3. `validate_config` - Validate config structure
4. `estimate_pages` - Estimate page count
5. `scrape_docs` - Scrape documentation
6. `package_skill` - Package to format (supports `--format` and `--target`)
7. `upload_skill` - Upload to platform (supports `--target`)
8. `enhance_skill` - AI enhancement with platform support
9. `install_skill` - Complete workflow automation

**Extended Tools (10):**
10. `scrape_github` - GitHub repository analysis
11. `scrape_pdf` - PDF extraction
12. `unified_scrape` - Multi-source scraping
13. `merge_sources` - Merge docs + code
14. `detect_conflicts` - Find discrepancies
15. `add_config_source` - Register git repos
16. `fetch_config` - Fetch configs from git
17. `list_config_sources` - List registered sources
18. `remove_config_source` - Remove config source
19. `split_config` - Split large configs

**NEW Vector DB Tools (4):**
20. `export_to_chroma` - Export to ChromaDB
21. `export_to_weaviate` - Export to Weaviate
22. `export_to_faiss` - Export to FAISS
23. `export_to_qdrant` - Export to Qdrant

**NEW Cloud Tools (3):**
24. `cloud_upload` - Upload to S3/GCS/Azure
25. `cloud_download` - Download from cloud storage
26. `cloud_list` - List files in cloud storage

### Starting MCP Server

```bash
# stdio mode (Claude Code, VS Code + Cline)
python -m skill_seekers.mcp.server_fastmcp

# HTTP mode (Cursor, Windsurf, IntelliJ)
python -m skill_seekers.mcp.server_fastmcp --transport http --port 8765
```

## 🤖 RAG Framework & Vector Database Integrations (**NEW - v3.0.0**)

Skill Seekers is now the **universal preprocessor for RAG pipelines**. Export documentation to any RAG framework or vector database with a single command.

### RAG Frameworks

**LangChain Documents:**
```bash
# Export to LangChain Document format
skill-seekers package output/django --format langchain

# Output: output/django-langchain.json
# Format: Array of LangChain Document objects
# - page_content: Full text content
# - metadata: {source, category, type, url}

# Use in LangChain:
from langchain.document_loaders import JSONLoader
loader = JSONLoader("output/django-langchain.json")
documents = loader.load()
```

**LlamaIndex TextNodes:**
```bash
# Export to LlamaIndex TextNode format
skill-seekers package output/django --format llama-index

# Output: output/django-llama-index.json
# Format: Array of LlamaIndex TextNode objects
# - text: Content
# - id_: Unique identifier
# - metadata: {source, category, type}
# - relationships: Document relationships

# Use in LlamaIndex:
from llama_index import StorageContext, load_index_from_storage
from llama_index.schema import TextNode
nodes = [TextNode.from_dict(n) for n in json.load(open("output/django-llama-index.json"))]
```

**Haystack Documents:**
```bash
# Export to Haystack Document format
skill-seekers package output/django --format haystack

# Output: output/django-haystack.json
# Format: Haystack Document objects for pipelines
# Perfect for: Question answering, search, RAG pipelines
```

### Vector Databases

**ChromaDB (Direct Integration):**
```bash
# Export and optionally upload to ChromaDB
skill-seekers package output/django --format chroma

# Output: output/django-chroma/ (ChromaDB collection)
# With direct upload (requires chromadb running):
skill-seekers package output/django --format chroma --upload

# Configuration via environment:
export CHROMA_HOST=localhost
export CHROMA_PORT=8000
```

**FAISS (Facebook AI Similarity Search):**
```bash
# Export to FAISS index format
skill-seekers package output/django --format faiss

# Output:
# - output/django-faiss.index (FAISS index)
# - output/django-faiss-metadata.json (Document metadata)

# Use with FAISS:
import faiss
index = faiss.read_index("output/django-faiss.index")
```

**Weaviate:**
```bash
# Export and upload to Weaviate
skill-seekers package output/django --format weaviate --upload

# Requires environment variables:
export WEAVIATE_URL=http://localhost:8080
export WEAVIATE_API_KEY=your-api-key

# Creates class "DjangoDoc" with schema
```

**Qdrant:**
```bash
# Export and upload to Qdrant
skill-seekers package output/django --format qdrant --upload

# Requires environment variables:
export QDRANT_URL=http://localhost:6333
export QDRANT_API_KEY=your-api-key

# Creates collection "django_docs"
```

**Pinecone (via Markdown):**
```bash
# Pinecone uses the markdown format
skill-seekers package output/django --target markdown

# Then use Pinecone's Python client for upsert
# See: docs/integrations/PINECONE.md
```

### Complete RAG Pipeline Example

```bash
# 1. Scrape documentation
skill-seekers scrape --config configs/django.json

# 2. Export to your RAG stack
skill-seekers package output/django --format langchain  # For LangChain
skill-seekers package output/django --format llama-index  # For LlamaIndex
skill-seekers package output/django --format chroma --upload  # Direct to ChromaDB

# 3. Use in your application
# See examples/:
# - examples/langchain-rag-pipeline/
# - examples/llama-index-query-engine/
# - examples/pinecone-upsert/
```

**Integration Hub:** [docs/integrations/RAG_PIPELINES.md](docs/integrations/RAG_PIPELINES.md)

## 🛠️ AI Coding Assistant Integrations (**NEW - v3.0.0**)

Transform any framework documentation into persistent expert context for 4+ AI coding assistants. Your IDE's AI now "knows" your frameworks without manual prompting.

### Cursor IDE

**Setup:**
```bash
# 1. Generate skill
skill-seekers scrape --config configs/react.json
skill-seekers package output/react/ --target claude

# 2. Install to Cursor
cp output/react-claude/SKILL.md .cursorrules

# 3. Restart Cursor
# AI now has React expertise!
```

**Benefits:**
- ✅ AI suggests React-specific patterns
- ✅ No manual "use React hooks" prompts needed
- ✅ Consistent team patterns
- ✅ Works for ANY framework

**Guide:** [docs/integrations/CURSOR.md](docs/integrations/CURSOR.md)
**Example:** [examples/cursor-react-skill/](examples/cursor-react-skill/)

### Windsurf

**Setup:**
```bash
# 1. Generate skill
skill-seekers scrape --config configs/django.json
skill-seekers package output/django/ --target claude

# 2. Install to Windsurf
mkdir -p .windsurf/rules
cp output/django-claude/SKILL.md .windsurf/rules/django.md

# 3. Restart Windsurf
# AI now knows Django patterns!
```

**Benefits:**
- ✅ Flow-based coding with framework knowledge
- ✅ IDE-native AI assistance
- ✅ Persistent context across sessions

**Guide:** [docs/integrations/WINDSURF.md](docs/integrations/WINDSURF.md)
**Example:** [examples/windsurf-fastapi-context/](examples/windsurf-fastapi-context/)

### Cline (VS Code Extension)

**Setup:**
```bash
# 1. Generate skill
skill-seekers scrape --config configs/fastapi.json
skill-seekers package output/fastapi/ --target claude

# 2. Install to Cline
cp output/fastapi-claude/SKILL.md .clinerules

# 3. Reload VS Code
# Cline now has FastAPI expertise!
```

**Benefits:**
- ✅ Agentic code generation in VS Code
- ✅ Cursor Composer equivalent for VS Code
- ✅ System prompts + MCP integration

**Guide:** [docs/integrations/CLINE.md](docs/integrations/CLINE.md)
**Example:** [examples/cline-django-assistant/](examples/cline-django-assistant/)

### Continue.dev (Universal IDE)

**Setup:**
```bash
# 1. Generate skill
skill-seekers scrape --config configs/react.json
skill-seekers package output/react/ --target claude

# 2. Start context server
cd examples/continue-dev-universal/
python context_server.py --port 8765

# 3. Configure in ~/.continue/config.json
{
  "contextProviders": [
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/context",
        "title": "React Documentation"
      }
    }
  ]
}

# 4. Works in ALL IDEs!
# VS Code, JetBrains, Vim, Emacs...
```

**Benefits:**
- ✅ IDE-agnostic (works in VS Code, IntelliJ, Vim, Emacs)
- ✅ Custom LLM providers supported
- ✅ HTTP-based context serving
- ✅ Team consistency across mixed IDE environments

**Guide:** [docs/integrations/CONTINUE_DEV.md](docs/integrations/CONTINUE_DEV.md)
**Example:** [examples/continue-dev-universal/](examples/continue-dev-universal/)

### Multi-IDE Team Setup

For teams using different IDEs (VS Code, IntelliJ, Vim):

```bash
# Use Continue.dev as universal context provider
skill-seekers scrape --config configs/react.json
python context_server.py --host 0.0.0.0 --port 8765

# ALL team members configure Continue.dev
# Result: Identical AI suggestions across all IDEs!
```

**Integration Hub:** [docs/integrations/INTEGRATIONS.md](docs/integrations/INTEGRATIONS.md)

## ☁️ Cloud Storage Integration (**NEW - v3.0.0**)

Upload skills directly to cloud storage for team sharing and CI/CD pipelines.

### Supported Providers

**AWS S3:**
```bash
# Upload skill
skill-seekers cloud upload --provider s3 --bucket my-skills output/react.zip

# Download skill
skill-seekers cloud download --provider s3 --bucket my-skills react.zip

# List skills
skill-seekers cloud list --provider s3 --bucket my-skills

# Environment variables:
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_REGION=us-east-1
```

**Google Cloud Storage:**
```bash
# Upload skill
skill-seekers cloud upload --provider gcs --bucket my-skills output/react.zip

# Download skill
skill-seekers cloud download --provider gcs --bucket my-skills react.zip

# List skills
skill-seekers cloud list --provider gcs --bucket my-skills

# Environment variables:
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

**Azure Blob Storage:**
```bash
# Upload skill
skill-seekers cloud upload --provider azure --container my-skills output/react.zip

# Download skill
skill-seekers cloud download --provider azure --container my-skills react.zip

# List skills
skill-seekers cloud list --provider azure --container my-skills

# Environment variables:
export AZURE_STORAGE_CONNECTION_STRING=your-connection-string
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Upload skill to S3
  run: |
    skill-seekers scrape --config configs/react.json
    skill-seekers package output/react/
    skill-seekers cloud upload --provider s3 --bucket ci-skills output/react.zip
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

**Guide:** [docs/integrations/CLOUD_STORAGE.md](docs/integrations/CLOUD_STORAGE.md)

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

### Debugging Common Issues

**Import Errors:**
```bash
# Always ensure package is installed first
pip install -e .

# Verify installation
python -c "import skill_seekers; print(skill_seekers.__version__)"
```

**Rate Limit Issues:**
```bash
# Check current GitHub rate limit status
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit

# Configure multiple GitHub profiles
skill-seekers config --github

# Test your tokens
skill-seekers config --test
```

**Enhancement Not Working:**
```bash
# Check if API key is set
echo $ANTHROPIC_API_KEY

# Try LOCAL mode instead (uses Claude Code Max)
skill-seekers enhance output/react/ --mode LOCAL

# Monitor enhancement status
skill-seekers enhance-status output/react/ --watch
```

**Test Failures:**
```bash
# Run specific failing test with verbose output
pytest tests/test_file.py::test_name -vv

# Run with print statements visible
pytest tests/test_file.py -s

# Run with coverage to see what's not tested
pytest tests/test_file.py --cov=src/skill_seekers --cov-report=term-missing

# Run only unit tests (skip slow integration tests)
pytest tests/ -v -m "not slow and not integration"
```

**Config Issues:**
```bash
# Validate config structure
skill-seekers-validate configs/myconfig.json

# Show current configuration
skill-seekers config --show

# Estimate pages before scraping
skill-seekers estimate configs/myconfig.json
```

## 🎯 Where to Make Changes

This section helps you quickly locate the right files when implementing common changes.

### Adding a New CLI Command

**Files to modify:**
1. **Create command file:** `src/skill_seekers/cli/my_command.py`
   ```python
   def main():
       """Entry point for my-command."""
       # Implementation
   ```

2. **Add entry point:** `pyproject.toml`
   ```toml
   [project.scripts]
   skill-seekers-my-command = "skill_seekers.cli.my_command:main"
   ```

3. **Update unified CLI:** `src/skill_seekers/cli/main.py`
   - Add subcommand handler to dispatcher

4. **Add tests:** `tests/test_my_command.py`
   - Test main functionality
   - Test CLI argument parsing
   - Test error cases

5. **Update docs:** `CHANGELOG.md` + `README.md` (if user-facing)

### Adding a New Platform Adaptor

**Files to modify:**
1. **Create adaptor:** `src/skill_seekers/cli/adaptors/my_platform_adaptor.py`
   ```python
   from .base import BaseAdaptor

   class MyPlatformAdaptor(BaseAdaptor):
       def package(self, skill_dir, output_path, **kwargs):
           # Platform-specific packaging
           pass

       def upload(self, package_path, api_key=None, **kwargs):
           # Platform-specific upload (optional for some platforms)
           pass

       def export(self, skill_dir, format, **kwargs):
           # For RAG/vector DB adaptors: export to specific format
           pass
   ```

2. **Register in factory:** `src/skill_seekers/cli/adaptors/__init__.py`
   ```python
   def get_adaptor(target=None, format=None):
       # For LLM platforms (--target flag)
       target_adaptors = {
           'claude': ClaudeAdaptor,
           'gemini': GeminiAdaptor,
           'openai': OpenAIAdaptor,
           'markdown': MarkdownAdaptor,
           'myplatform': MyPlatformAdaptor,  # ADD THIS
       }

       # For RAG/vector DBs (--format flag)
       format_adaptors = {
           'langchain': LangChainAdaptor,
           'llama-index': LlamaIndexAdaptor,
           'chroma': ChromaAdaptor,
           # ... etc
       }
   ```

3. **Add optional dependency:** `pyproject.toml`
   ```toml
   [project.optional-dependencies]
   myplatform = ["myplatform-sdk>=1.0.0"]
   ```

4. **Add tests:** `tests/test_adaptors/test_my_platform_adaptor.py`
   - Test export format
   - Test upload (if applicable)
   - Test with real data

5. **Update documentation:**
   - README.md - Platform comparison table
   - docs/integrations/MY_PLATFORM.md - Integration guide
   - examples/my-platform-example/ - Working example

### Adding a New Config Preset

**Files to modify:**
1. **Create config:** `configs/my_framework.json`
   ```json
   {
     "name": "my_framework",
     "base_url": "https://docs.myframework.com/",
     "selectors": {...},
     "categories": {...}
   }
   ```

2. **Test locally:**
   ```bash
   # Estimate first
   skill-seekers estimate configs/my_framework.json

   # Test scrape (small sample)
   skill-seekers scrape --config configs/my_framework.json --max-pages 50
   ```

3. **Add to README:** Update presets table in `README.md`

4. **Submit to website:** (Optional) Submit to SkillSeekersWeb.com

### Modifying Core Scraping Logic

**Key files by feature:**

| Feature | File | Size | Notes |
|---------|------|------|-------|
| Doc scraping | `src/skill_seekers/cli/doc_scraper.py` | ~90KB | Main scraper, BFS traversal |
| GitHub scraping | `src/skill_seekers/cli/github_scraper.py` | ~56KB | Repo analysis + metadata |
| GitHub API | `src/skill_seekers/cli/github_fetcher.py` | ~17KB | Rate limit handling |
| PDF extraction | `src/skill_seekers/cli/pdf_scraper.py` | Medium | PyMuPDF + OCR |
| Code analysis | `src/skill_seekers/cli/code_analyzer.py` | ~65KB | Multi-language AST parsing |
| Pattern detection | `src/skill_seekers/cli/pattern_recognizer.py` | Medium | C3.1 - 10 GoF patterns |
| Test extraction | `src/skill_seekers/cli/test_example_extractor.py` | Medium | C3.2 - 5 categories |
| Guide generation | `src/skill_seekers/cli/how_to_guide_builder.py` | ~45KB | C3.3 - AI-enhanced guides |
| Config extraction | `src/skill_seekers/cli/config_extractor.py` | ~32KB | C3.4 - 9 formats |
| Router generation | `src/skill_seekers/cli/generate_router.py` | ~43KB | C3.5 - Architecture docs |
| Signal flow | `src/skill_seekers/cli/signal_flow_analyzer.py` | Medium | C3.10 - Godot-specific |

**Always add tests when modifying core logic!**

### Modifying the Unified Create Command

**The create command uses a modular argument system:**

**Files involved:**
1. **Parser:** `src/skill_seekers/cli/parsers/create_parser.py`
   - Defines help text and formatter
   - Registers help mode flags (`--help-web`, `--help-github`, etc.)
   - Uses custom `NoWrapFormatter` for better help display

2. **Arguments:** `src/skill_seekers/cli/arguments/create.py`
   - Three tiers of arguments:
     - `UNIVERSAL_ARGUMENTS` (13 flags) - Work for all sources
     - Source-specific dicts (`WEB_ARGUMENTS`, `GITHUB_ARGUMENTS`, etc.)
     - `ADVANCED_ARGUMENTS` - Rare/advanced options
   - `add_create_arguments(parser, mode)` - Multi-mode argument addition

3. **Source Detection:** `src/skill_seekers/cli/source_detector.py` (if implemented)
   - Auto-detect source type from input
   - Pattern matching (URLs, GitHub repos, file extensions)

4. **Main Logic:** `src/skill_seekers/cli/create_command.py` (if implemented)
   - Route to appropriate scraper based on detected type
   - Argument validation and compatibility checking

**When adding new arguments:**
- Universal args → `UNIVERSAL_ARGUMENTS` in `arguments/create.py`
- Source-specific → Appropriate dict (`WEB_ARGUMENTS`, etc.)
- Always update help text and add tests

**Example: Adding a new universal flag:**
```python
# In arguments/create.py
UNIVERSAL_ARGUMENTS = {
    # ... existing args ...
    "my_flag": {
        "flags": ("--my-flag", "-m"),
        "kwargs": {
            "action": "store_true",
            "help": "Description of my flag",
        },
    },
}
```

### Adding MCP Tools

**Files to modify:**
1. **Add tool function:** `src/skill_seekers/mcp/tools/{category}_tools.py`

2. **Register tool:** `src/skill_seekers/mcp/server.py`
   ```python
   @mcp.tool()
   def my_new_tool(param: str) -> str:
       """Tool description."""
       # Implementation
   ```

3. **Add tests:** `tests/test_mcp_fastmcp.py`

4. **Update count:** README.md (currently 18 tools)

## 📍 Key Files Quick Reference

| Task | File(s) | What to Modify |
|------|---------|----------------|
| Add new CLI command | `src/skill_seekers/cli/my_cmd.py`<br>`pyproject.toml` | Create `main()` function<br>Add entry point |
| Add platform adaptor | `src/skill_seekers/cli/adaptors/my_platform.py`<br>`adaptors/__init__.py` | Inherit `BaseAdaptor`<br>Register in factory |
| Fix scraping logic | `src/skill_seekers/cli/doc_scraper.py` | `scrape_all()`, `extract_content()` |
| Add MCP tool | `src/skill_seekers/mcp/server_fastmcp.py` | Add `@mcp.tool()` function |
| Fix tests | `tests/test_{feature}.py` | Add/modify test functions |
| Add config preset | `configs/{framework}.json` | Create JSON config |
| Update CI | `.github/workflows/tests.yml` | Modify workflow steps |

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
- `signal_flow_analyzer.py` - C3.10 signal flow analysis (Godot projects)
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

**RAG & Vector Database Adaptors** (NEW: v3.0.0 - `src/skill_seekers/cli/adaptors/`):
- `langchain.py` - LangChain Documents export (~250 lines)
  - Exports to LangChain Document format
  - Preserves metadata (source, category, type, url)
  - Smart chunking with overlap
- `llama_index.py` - LlamaIndex TextNodes export (~280 lines)
  - Exports to TextNode format with unique IDs
  - Relationship mapping between documents
  - Metadata preservation
- `haystack.py` - Haystack Documents export (~230 lines)
  - Pipeline-ready document format
  - Supports embeddings and filters
- `chroma.py` - ChromaDB integration (~350 lines)
  - Direct collection creation
  - Batch upsert with embeddings
  - Query interface
- `weaviate.py` - Weaviate vector search (~320 lines)
  - Schema creation with auto-detection
  - Batch import with error handling
- `faiss_helpers.py` - FAISS index generation (~280 lines)
  - Index building with metadata
  - Search utilities
- `qdrant.py` - Qdrant vector database (~300 lines)
  - Collection management
  - Payload indexing
- `streaming_adaptor.py` - Streaming data ingest (~200 lines)
  - Real-time data processing
  - Incremental updates

**Cloud Storage & Infrastructure** (NEW: v3.0.0 - `src/skill_seekers/cli/`):
- `cloud_storage_cli.py` - S3/GCS/Azure upload/download (~450 lines)
  - Multi-provider abstraction
  - Parallel uploads for large files
  - Retry logic with exponential backoff
- `embedding_pipeline.py` - Embedding generation for vectors (~320 lines)
  - Sentence-transformers integration
  - Batch processing
  - Multiple embedding models
- `sync_cli.py` - Continuous sync & monitoring (~380 lines)
  - File watching for changes
  - Automatic re-scraping
  - Smart diff detection
- `incremental_updater.py` - Smart incremental updates (~350 lines)
  - Change detection algorithms
  - Partial skill updates
  - Version tracking
- `streaming_ingest.py` - Real-time data streaming (~290 lines)
  - Stream processing pipelines
  - WebSocket support
- `benchmark_cli.py` - Performance benchmarking (~280 lines)
  - Scraping performance tests
  - Comparison reports
  - CI/CD integration
- `quality_metrics.py` - Quality analysis & reporting (~340 lines)
  - Completeness scoring
  - Link checking
  - Content quality metrics
- `multilang_support.py` - Internationalization support (~260 lines)
  - Language detection
  - Translation integration
  - Multi-locale skills
- `setup_wizard.py` - Interactive setup wizard (~220 lines)
  - Configuration management
  - Profile creation
  - First-time setup

## 🎯 Project-Specific Best Practices

1. **Prefer the unified `create` command** - Use `skill-seekers create <source>` over legacy commands for consistency
2. **Always use platform adaptors** - Never hardcode platform-specific logic
3. **Test all platforms** - Changes must work for all 16 platforms (was 4 in v2.x)
4. **Maintain backward compatibility** - Legacy commands (scrape, github, analyze) must still work
5. **Document API changes** - Update CHANGELOG.md for every release
6. **Keep dependencies optional** - Platform-specific deps are optional (RAG, cloud, etc.)
7. **Use src/ layout** - Proper package structure with `pip install -e .`
8. **Run tests before commits** - Per user instructions, never skip tests (1,765+ tests must pass)
9. **RAG-first mindset** - v3.0.0 is the universal preprocessor for AI systems
10. **Export format clarity** - Use `--format` for RAG/vector DBs, `--target` for LLM platforms
11. **Test with real integrations** - Verify exports work with actual LangChain, ChromaDB, etc.
12. **Progressive disclosure** - When adding flags, categorize as universal/source-specific/advanced

## 🐛 Debugging Tips

### Enable Verbose Logging

```bash
# Set environment variable for debug output
export SKILL_SEEKERS_DEBUG=1
skill-seekers scrape --config configs/react.json
```

### Test Single Function/Module

Run Python modules directly for debugging:
```bash
# Run modules with --help to see options
python -m skill_seekers.cli.doc_scraper --help
python -m skill_seekers.cli.github_scraper --repo facebook/react --dry-run
python -m skill_seekers.cli.package_skill --help

# Test MCP server directly
python -m skill_seekers.mcp.server_fastmcp
```

### Use pytest with Debugging

```bash
# Drop into debugger on failure
pytest tests/test_scraper_features.py --pdb

# Show print statements (normally suppressed)
pytest tests/test_scraper_features.py -s

# Verbose test output (shows full diff, more details)
pytest tests/test_scraper_features.py -vv

# Run only failed tests from last run
pytest tests/ --lf

# Run until first failure (stop immediately)
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l
```

### Debug Specific Test

```bash
# Run single test with full output
pytest tests/test_scraper_features.py::test_detect_language -vv -s

# With debugger
pytest tests/test_scraper_features.py::test_detect_language --pdb
```

### Check Package Installation

```bash
# Verify package is installed
pip list | grep skill-seekers

# Check installation mode (should show editable location)
pip show skill-seekers

# Verify imports work
python -c "import skill_seekers; print(skill_seekers.__version__)"

# Check CLI entry points
which skill-seekers
skill-seekers --version
```

### Common Error Messages & Solutions

**"ModuleNotFoundError: No module named 'skill_seekers'"**
→ **Solution:** `pip install -e .`
→ **Why:** src/ layout requires package installation

**"403 Forbidden" from GitHub API**
→ **Solution:** Rate limit hit, set `GITHUB_TOKEN` or use `skill-seekers config --github`
→ **Check limit:** `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit`

**"SKILL.md enhancement failed"**
→ **Solution:** Check if `ANTHROPIC_API_KEY` is set, or use `--mode LOCAL`
→ **Monitor:** `skill-seekers enhance-status output/react/ --watch`

**"No such file or directory: 'configs/myconfig.json'"**
→ **Solution:** Config path resolution order:
  1. Exact path as provided
  2. `./configs/` (current directory)
  3. `~/.config/skill-seekers/configs/` (user config)
  4. SkillSeekersWeb.com API (presets)

**"pytest: command not found"**
→ **Solution:** Install dev dependencies
```bash
pip install pytest pytest-asyncio pytest-cov coverage
# Or: pip install -e ".[dev]"  (if available)
```

**"ruff: command not found"**
→ **Solution:** Install ruff
```bash
pip install ruff
# Or use uvx: uvx ruff check src/
```

### Debugging Scraping Issues

**No content extracted?**
```python
# Test selectors in Python
from bs4 import BeautifulSoup
import requests

url = "https://docs.example.com/page"
soup = BeautifulSoup(requests.get(url).content, 'html.parser')

# Try different selectors
print(soup.select_one('article'))
print(soup.select_one('main'))
print(soup.select_one('div[role="main"]'))
print(soup.select_one('.documentation-content'))
```

**Categories not working?**
- Check `categories` in config has correct keywords
- Run with `--dry-run` to see categorization without scraping
- Enable debug mode: `export SKILL_SEEKERS_DEBUG=1`

### Profiling Performance

```bash
# Profile scraping performance
python -m cProfile -o profile.stats -m skill_seekers.cli.doc_scraper --config configs/react.json --max-pages 10

# Analyze profile
python -m pstats profile.stats
# In pstats shell:
# > sort cumtime
# > stats 20
```

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

## 🔧 Helper Scripts

The `scripts/` directory contains utility scripts:

```bash
# Bootstrap skill generation - self-hosting skill-seekers as a Claude skill
./scripts/bootstrap_skill.sh

# Start MCP server for HTTP transport
./scripts/start_mcp_server.sh

# Script templates are in scripts/skill_header.md
```

**Bootstrap Skill Workflow:**
1. Analyzes skill-seekers codebase itself (dogfooding)
2. Combines handcrafted header with auto-generated analysis
3. Validates SKILL.md structure
4. Outputs ready-to-use skill for Claude Code

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

**v3.1.0 (In Development) - "Unified CLI & Developer Experience":**
- 🎯 **Unified `create` Command** - Auto-detects source type (web/GitHub/local/PDF/config)
- 📋 **Progressive Disclosure Help** - Default shows 13 universal flags, detailed help available per source
- ⚡ **-p Shortcut** - Quick preset selection (`-p quick|standard|comprehensive`)
- 🔧 **Enhancement Flag Consolidation** - `--enhance-level` (0-3) replaces 3 separate flags
- 🎨 **Smart Source Detection** - No need to specify whether input is URL, repo, or directory
- ✅ **1,765 Tests Passing** - All CLI refactor work verified
- 📚 **Improved Documentation** - CLAUDE.md enhanced with CLI refactor details

**v3.0.0 (February 10, 2026) - "Universal Intelligence Platform":**
- 🚀 **16 Platform Adaptors** - RAG frameworks (LangChain, LlamaIndex, Haystack), vector DBs (Chroma, FAISS, Weaviate, Qdrant), AI coding assistants (Cursor, Windsurf, Cline, Continue.dev), LLM platforms (Claude, Gemini, OpenAI)
- 🛠️ **26 MCP Tools** (up from 18) - Complete automation for any AI system
- ✅ **1,852 Tests Passing** (up from 700+) - Production-grade reliability
- ☁️ **Cloud Storage** - S3, GCS, Azure Blob Storage integration
- 🎯 **AI Coding Assistants** - Persistent context for Cursor, Windsurf, Cline, Continue.dev
- 📊 **Quality Metrics** - Automated completeness scoring and content analysis
- 🌐 **Multilingual Support** - Language detection and translation
- 🔄 **Streaming Ingest** - Real-time data processing pipelines
- 📈 **Benchmarking Tools** - Performance comparison and CI/CD integration
- 🔧 **Setup Wizard** - Interactive first-time configuration
- 📦 **12 Example Projects** - Complete working examples for every integration
- 📚 **18 Integration Guides** - Comprehensive documentation for all platforms

**v2.9.0 (February 3, 2026):**
- **C3.10: Signal Flow Analysis** - Complete signal flow analysis for Godot projects
- Comprehensive Godot 4.x support (GDScript, .tscn, .tres, .gdshader files)
- GDScript test extraction (GUT, gdUnit4, WAT frameworks)
- Signal pattern detection (EventBus, Observer, Event Chains)
- Signal-based how-to guides generation

**v2.8.0 (February 1, 2026):**
- C3.9: Project Documentation Extraction
- Granular AI enhancement control with `--enhance-level` (0-3)

**v2.7.1 (January 18, 2026 - Hotfix):**
- 🚨 **Critical Bug Fix:** Config download 404 errors resolved
- Fixed manual URL construction bug - now uses `download_url` from API response
- All 15 source tools tests + 8 fetch_config tests passing

**v2.7.0 (January 18, 2026):**
- 🔐 **Smart Rate Limit Management** - Multi-token GitHub configuration system
- 🧙 **Interactive Configuration Wizard** - Beautiful terminal UI (`skill-seekers config`)
- 🚦 **Intelligent Rate Limit Handler** - Four strategies (prompt/wait/switch/fail)
- 📥 **Resume Capability** - Continue interrupted jobs with progress tracking
- 🔧 **CI/CD Support** - Non-interactive mode for automation
- 🎯 **Bootstrap Skill** - Self-hosting skill-seekers as Claude Code skill

**v2.6.0 (January 14, 2026):**
- **C3.x Codebase Analysis Suite Complete** (C3.1-C3.8)
- Multi-platform support with platform adaptor architecture (4 platforms)
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
- **C3.9:** Project documentation extraction (markdown categorization, AI enhancement)
- **C3.10:** Signal flow analysis (Godot event-driven architecture, pattern detection)

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
