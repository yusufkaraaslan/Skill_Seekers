# AGENTS.md - Skill Seekers

This file provides essential guidance for AI coding agents working with the Skill Seekers codebase.

---

## Project Overview

**Skill Seekers** is a Python CLI tool that converts documentation websites, GitHub repositories, and PDF files into AI-ready skills for LLM platforms and RAG (Retrieval-Augmented Generation) pipelines. It serves as the universal preprocessing layer for AI systems.

### Key Facts

| Attribute | Value |
|-----------|-------|
| **Current Version** | 2.9.0 |
| **Python Version** | 3.10+ (tested on 3.10, 3.11, 3.12, 3.13) |
| **License** | MIT |
| **Package Name** | `skill-seekers` (PyPI) |
| **Website** | https://skillseekersweb.com/ |
| **Repository** | https://github.com/yusufkaraaslan/Skill_Seekers |

### Supported Target Platforms

| Platform | Format | Use Case |
|----------|--------|----------|
| **Claude AI** | ZIP + YAML | Claude Code skills |
| **Google Gemini** | tar.gz | Gemini skills |
| **OpenAI ChatGPT** | ZIP + Vector Store | Custom GPTs |
| **LangChain** | Documents | QA chains, agents, retrievers |
| **LlamaIndex** | TextNodes | Query engines, chat engines |
| **Haystack** | Documents | Enterprise RAG pipelines |
| **Pinecone** | Ready for upsert | Production vector search |
| **Weaviate** | Vector objects | Vector database |
| **Qdrant** | Points | Vector database |
| **Chroma** | Documents | Local vector database |
| **FAISS** | Index files | Local similarity search |
| **Cursor IDE** | .cursorrules | AI coding assistant rules |
| **Windsurf** | .windsurfrules | AI coding rules |
| **Cline** | .clinerules + MCP | VS Code extension |
| **Continue.dev** | HTTP context | Universal IDE support |
| **Generic Markdown** | ZIP | Universal export |

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
│   ├── cli/                        # CLI tools and commands (70+ modules, ~40k lines)
│   │   ├── adaptors/               # Platform adaptors (Strategy pattern)
│   │   │   ├── base.py             # Abstract base class
│   │   │   ├── claude.py           # Claude AI adaptor
│   │   │   ├── gemini.py           # Google Gemini adaptor
│   │   │   ├── openai.py           # OpenAI ChatGPT adaptor
│   │   │   ├── markdown.py         # Generic Markdown adaptor
│   │   │   ├── chroma.py           # Chroma vector DB adaptor
│   │   │   ├── faiss_helpers.py    # FAISS index adaptor
│   │   │   ├── haystack.py         # Haystack RAG adaptor
│   │   │   ├── langchain.py        # LangChain adaptor
│   │   │   ├── llama_index.py      # LlamaIndex adaptor
│   │   │   ├── qdrant.py           # Qdrant vector DB adaptor
│   │   │   ├── weaviate.py         # Weaviate vector DB adaptor
│   │   │   └── streaming_adaptor.py # Streaming output adaptor
│   │   ├── storage/                # Cloud storage backends
│   │   │   ├── base_storage.py     # Storage interface
│   │   │   ├── s3_storage.py       # AWS S3 support
│   │   │   ├── gcs_storage.py      # Google Cloud Storage
│   │   │   └── azure_storage.py    # Azure Blob Storage
│   │   ├── parsers/                # CLI argument parsers
│   │   ├── main.py                 # Unified CLI entry point
│   │   ├── doc_scraper.py          # Documentation scraper
│   │   ├── github_scraper.py       # GitHub repository scraper
│   │   ├── pdf_scraper.py          # PDF extraction
│   │   ├── unified_scraper.py      # Multi-source scraping
│   │   ├── codebase_scraper.py     # Local codebase analysis
│   │   ├── enhance_skill_local.py  # AI enhancement (local mode)
│   │   ├── package_skill.py        # Skill packager
│   │   ├── upload_skill.py         # Upload to platforms
│   │   ├── cloud_storage_cli.py    # Cloud storage CLI
│   │   ├── benchmark_cli.py        # Benchmarking CLI
│   │   ├── sync_cli.py             # Sync monitoring CLI
│   │   └── ...                     # Additional CLI modules
│   ├── mcp/                        # MCP server integration
│   │   ├── server_fastmcp.py       # FastMCP server (main, ~708 lines)
│   │   ├── server_legacy.py        # Legacy server implementation
│   │   ├── server.py               # Server entry point
│   │   ├── agent_detector.py       # AI agent detection
│   │   ├── git_repo.py             # Git repository operations
│   │   ├── source_manager.py       # Config source management
│   │   └── tools/                  # MCP tool implementations
│   │       ├── config_tools.py     # Configuration tools
│   │       ├── scraping_tools.py   # Scraping tools
│   │       ├── packaging_tools.py  # Packaging tools
│   │       ├── source_tools.py     # Source management tools
│   │       ├── splitting_tools.py  # Config splitting tools
│   │       └── vector_db_tools.py  # Vector database tools
│   ├── sync/                       # Sync monitoring module
│   │   ├── detector.py             # Change detection
│   │   ├── models.py               # Data models
│   │   ├── monitor.py              # Monitoring logic
│   │   └── notifier.py             # Notification system
│   ├── benchmark/                  # Benchmarking framework
│   │   ├── framework.py            # Benchmark framework
│   │   ├── models.py               # Benchmark models
│   │   └── runner.py               # Benchmark runner
│   ├── embedding/                  # Embedding server
│   │   ├── server.py               # FastAPI embedding server
│   │   ├── generator.py            # Embedding generation
│   │   ├── cache.py                # Embedding cache
│   │   └── models.py               # Embedding models
│   ├── _version.py                 # Version information
│   └── __init__.py                 # Package init
├── tests/                          # Test suite (89 test files)
├── configs/                        # Preset configuration files
├── docs/                           # Documentation (80+ markdown files)
│   ├── integrations/               # Platform integration guides
│   ├── guides/                     # User guides
│   ├── reference/                  # API reference
│   ├── features/                   # Feature documentation
│   ├── blog/                       # Blog posts
│   └── roadmap/                    # Roadmap documents
├── examples/                       # Usage examples
│   ├── langchain-rag-pipeline/     # LangChain example
│   ├── llama-index-query-engine/   # LlamaIndex example
│   ├── pinecone-upsert/            # Pinecone example
│   ├── chroma-example/             # Chroma example
│   ├── weaviate-example/           # Weaviate example
│   ├── qdrant-example/             # Qdrant example
│   ├── faiss-example/              # FAISS example
│   ├── haystack-pipeline/          # Haystack example
│   ├── cursor-react-skill/         # Cursor IDE example
│   ├── windsurf-fastapi-context/   # Windsurf example
│   └── continue-dev-universal/     # Continue.dev example
├── .github/workflows/              # CI/CD workflows
├── pyproject.toml                  # Main project configuration
├── requirements.txt                # Pinned dependencies
├── mypy.ini                        # MyPy type checker configuration
├── Dockerfile                      # Main Docker image (multi-stage)
├── Dockerfile.mcp                  # MCP server Docker image
└── docker-compose.yml              # Full stack deployment
```

---

## Build and Development Commands

### Prerequisites

- Python 3.10 or higher
- pip or uv package manager
- Git (for GitHub scraping features)

### Setup (REQUIRED before any development)

```bash
# Install in editable mode (REQUIRED for tests due to src/ layout)
pip install -e .

# Install with all platform dependencies
pip install -e ".[all-llms]"

# Install with all optional dependencies
pip install -e ".[all]"

# Install specific platforms only
pip install -e ".[gemini]"    # Google Gemini support
pip install -e ".[openai]"    # OpenAI ChatGPT support
pip install -e ".[mcp]"       # MCP server dependencies
pip install -e ".[s3]"        # AWS S3 support
pip install -e ".[gcs]"       # Google Cloud Storage
pip install -e ".[azure]"     # Azure Blob Storage
pip install -e ".[embedding]" # Embedding server support
pip install -e ".[rag-upload]" # Vector DB upload support

# Install dev dependencies (using dependency-groups)
pip install -e ".[dev]"
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

### Docker

```bash
# Build Docker image
docker build -t skill-seekers .

# Run with docker-compose (includes vector databases)
docker-compose up -d

# Run MCP server only
docker-compose up -d mcp-server

# View logs
docker-compose logs -f mcp-server
```

---

## Testing Instructions

### Running Tests

**CRITICAL:** Never skip tests - all tests must pass before commits.

```bash
# All tests (must run pip install -e . first!)
pytest tests/ -v

# Specific test file
pytest tests/test_scraper_features.py -v
pytest tests/test_mcp_fastmcp.py -v
pytest tests/test_cloud_storage.py -v

# With coverage
pytest tests/ --cov=src/skill_seekers --cov-report=term --cov-report=html

# Single test
pytest tests/test_scraper_features.py::test_detect_language -v

# E2E tests
pytest tests/test_e2e_three_stream_pipeline.py -v

# Skip slow tests
pytest tests/ -v -m "not slow"

# Run only integration tests
pytest tests/ -v -m integration

# Run only specific marker
pytest tests/ -v -m "not slow and not integration"
```

### Test Architecture

- **89 test files** covering all features
- **1200+ tests** passing
- CI Matrix: Ubuntu + macOS, Python 3.10-3.12
- Test markers defined in `pyproject.toml`:

| Marker | Description |
|--------|-------------|
| `slow` | Tests taking >5 seconds |
| `integration` | Requires external services (APIs) |
| `e2e` | End-to-end tests (resource-intensive) |
| `venv` | Requires virtual environment setup |
| `bootstrap` | Bootstrap skill specific |
| `benchmark` | Performance benchmark tests |

### Test Configuration

From `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short --strict-markers"
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

The `conftest.py` file checks that the package is installed before running tests.

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
- **Ignored rules:** E501, F541, ARG002, B007, I001, SIM114
- **Import sorting:** isort style with `skill_seekers` as first-party

### MyPy Configuration (from mypy.ini)

```ini
[mypy]
python_version = 3.10
warn_return_any = False
warn_unused_configs = True
disallow_untyped_defs = False
check_untyped_defs = True
ignore_missing_imports = True
no_implicit_optional = True
show_error_codes = True

# Gradual typing - be lenient for now
disallow_incomplete_defs = False
disallow_untyped_calls = False
```

### Code Conventions

1. **Use type hints** where practical (gradual typing approach)
2. **Docstrings:** Use Google-style or standard docstrings
3. **Error handling:** Use specific exceptions, provide helpful messages
4. **Async code:** Use `asyncio`, mark tests with `@pytest.mark.asyncio`
5. **File naming:** Use snake_case for all Python files
6. **Class naming:** Use PascalCase for classes
7. **Function naming:** Use snake_case for functions and methods
8. **Constants:** Use UPPER_CASE for module-level constants

---

## Architecture Patterns

### Platform Adaptor Pattern (Strategy Pattern)

All platform-specific logic is encapsulated in adaptors:

```python
from skill_seekers.cli.adaptors import get_adaptor

# Get platform-specific adaptor
adaptor = get_adaptor('gemini')  # or 'claude', 'openai', 'langchain', etc.

# Package skill
adaptor.package(skill_dir='output/react/', output_path='output/')

# Upload to platform
adaptor.upload(
    package_path='output/react-gemini.tar.gz',
    api_key=os.getenv('GOOGLE_API_KEY')
)
```

Each adaptor inherits from `SkillAdaptor` base class and implements:
- `format_skill_md()` - Format SKILL.md content
- `package()` - Create platform-specific package
- `upload()` - Upload to platform API
- `validate_api_key()` - Validate API key format
- `supports_enhancement()` - Whether AI enhancement is supported

### CLI Architecture (Git-style)

Entry point: `src/skill_seekers/cli/main.py`

The CLI uses subcommands that delegate to existing modules:

```bash
# skill-seekers scrape --config react.json
# Transforms to: doc_scraper.main() with modified sys.argv
```

**Available subcommands:**
- `config` - Configuration wizard
- `scrape` - Documentation scraping
- `github` - GitHub repository scraping
- `pdf` - PDF extraction
- `unified` - Multi-source scraping
- `analyze` / `codebase` - Local codebase analysis
- `enhance` - AI enhancement
- `package` - Package skill for target platform
- `upload` - Upload to platform
- `cloud` - Cloud storage operations
- `sync` - Sync monitoring
- `benchmark` - Performance benchmarking
- `embed` - Embedding server
- `install` / `install-agent` - Complete workflow
- `stream` - Streaming ingestion
- `update` - Incremental updates
- `multilang` - Multi-language support
- `quality` - Quality metrics

### MCP Server Architecture

Two implementations:
- `server_fastmcp.py` - Modern, decorator-based (recommended, ~708 lines)
- `server_legacy.py` - Legacy implementation

Tools are organized by category:
- Config tools (3 tools): generate_config, list_configs, validate_config
- Scraping tools (8 tools): estimate_pages, scrape_docs, scrape_github, scrape_pdf, scrape_codebase, detect_patterns, extract_test_examples, build_how_to_guides
- Packaging tools (4 tools): package_skill, upload_skill, enhance_skill, install_skill
- Source tools (5 tools): fetch_config, submit_config, add_config_source, list_config_sources, remove_config_source
- Splitting tools (2 tools): split_config, generate_router
- Vector Database tools (4 tools): export_to_weaviate, export_to_chroma, export_to_faiss, export_to_qdrant

**Running MCP Server:**
```bash
# Stdio transport (default)
python -m skill_seekers.mcp.server_fastmcp

# HTTP transport
python -m skill_seekers.mcp.server_fastmcp --http --port 8765
```

### Cloud Storage Architecture

Abstract base class pattern for cloud providers:
- `base_storage.py` - Defines `CloudStorage` interface
- `s3_storage.py` - AWS S3 implementation
- `gcs_storage.py` - Google Cloud Storage implementation
- `azure_storage.py` - Azure Blob Storage implementation

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

All workflows are in `.github/workflows/`:

**`tests.yml`:**
- Runs on: push/PR to `main` and `development`
- Lint job: Ruff + MyPy
- Test matrix: Ubuntu + macOS, Python 3.10-3.12
- Coverage: Uploads to Codecov

**`release.yml`:**
- Triggered on version tags (`v*`)
- Builds and publishes to PyPI using `uv`
- Creates GitHub release with changelog

**`docker-publish.yml`:**
- Builds and publishes Docker images

**`vector-db-export.yml`:**
- Tests vector database exports

**`scheduled-updates.yml`:**
- Scheduled sync monitoring

**`quality-metrics.yml`:**
- Quality metrics tracking

**`test-vector-dbs.yml`:**
- Vector database integration tests

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
   - `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` - AWS S3
   - `GOOGLE_APPLICATION_CREDENTIALS` - GCS
   - `AZURE_STORAGE_CONNECTION_STRING` - Azure
3. **Configuration storage:**
   - Stored at `~/.config/skill-seekers/config.json`
   - Permissions: 600 (owner read/write only)

### Rate Limit Handling

- GitHub API has rate limits (5000 requests/hour for authenticated)
- The tool has built-in rate limit handling with retry logic
- Use `--non-interactive` flag for CI/CD environments

### Custom API Endpoints

Support for Claude-compatible APIs:

```bash
export ANTHROPIC_API_KEY=your-custom-api-key
export ANTHROPIC_BASE_URL=https://custom-endpoint.com/v1
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
3. Implement required methods: `package()`, `upload()`, `format_skill_md()`
4. Register in `src/skill_seekers/cli/adaptors/__init__.py`
5. Add optional dependencies in `pyproject.toml`
6. Add tests in `tests/test_adaptors/`

### Adding an MCP Tool

1. Implement tool logic in `src/skill_seekers/mcp/tools/category_tools.py`
2. Register in `src/skill_seekers/mcp/server_fastmcp.py`
3. Add test in `tests/test_mcp_fastmcp.py`

### Adding Cloud Storage Provider

1. Create module in `src/skill_seekers/cli/storage/my_storage.py`
2. Inherit from `CloudStorage` base class
3. Implement required methods: `upload()`, `download()`, `list()`, `delete()`
4. Register in `src/skill_seekers/cli/storage/__init__.py`
5. Add optional dependencies in `pyproject.toml`

---

## Documentation

### Project Documentation

- **README.md** - Main project documentation
- **README.zh-CN.md** - Chinese translation
- **CLAUDE.md** - Detailed implementation guidance
- **QUICKSTART.md** - Quick start guide
- **CONTRIBUTING.md** - Contribution guidelines
- **TROUBLESHOOTING.md** - Common issues and solutions
- **AGENTS.md** - This file, for AI coding agents
- **docs/** - Comprehensive documentation (80+ files)
  - `docs/integrations/` - Integration guides for each platform
  - `docs/guides/` - User guides
  - `docs/reference/` - API reference
  - `docs/features/` - Feature documentation
  - `docs/blog/` - Blog posts and articles
  - `docs/roadmap/` - Roadmap documents

### Configuration Documentation

Preset configs are in `configs/` directory:
- `godot.json` - Godot Engine
- `blender.json` / `blender-unified.json` - Blender Engine
- `claude-code.json` - Claude Code
- `httpx_comprehensive.json` - HTTPX library
- `medusa-mercurjs.json` - Medusa/MercurJS
- `astrovalley_unified.json` - Astrovalley
- `configs/integrations/` - Integration-specific configs

---

## Key Dependencies

### Core Dependencies (Required)

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | >=2.32.5 | HTTP requests |
| `beautifulsoup4` | >=4.14.2 | HTML parsing |
| `PyGithub` | >=2.5.0 | GitHub API |
| `GitPython` | >=3.1.40 | Git operations |
| `httpx` | >=0.28.1 | Async HTTP |
| `anthropic` | >=0.76.0 | Claude AI API |
| `PyMuPDF` | >=1.24.14 | PDF processing |
| `Pillow` | >=11.0.0 | Image processing |
| `pytesseract` | >=0.3.13 | OCR |
| `pydantic` | >=2.12.3 | Data validation |
| `pydantic-settings` | >=2.11.0 | Settings management |
| `click` | >=8.3.0 | CLI framework |
| `Pygments` | >=2.19.2 | Syntax highlighting |
| `pathspec` | >=0.12.1 | Path matching |
| `networkx` | >=3.0 | Graph operations |
| `schedule` | >=1.2.0 | Scheduled tasks |
| `python-dotenv` | >=1.1.1 | Environment variables |
| `jsonschema` | >=4.25.1 | JSON validation |

### Optional Dependencies

| Feature | Package | Install Command |
|---------|---------|-----------------|
| MCP Server | `mcp>=1.25,<2` | `pip install -e ".[mcp]"` |
| Google Gemini | `google-generativeai>=0.8.0` | `pip install -e ".[gemini]"` |
| OpenAI | `openai>=1.0.0` | `pip install -e ".[openai]"` |
| AWS S3 | `boto3>=1.34.0` | `pip install -e ".[s3]"` |
| Google Cloud Storage | `google-cloud-storage>=2.10.0` | `pip install -e ".[gcs]"` |
| Azure Blob Storage | `azure-storage-blob>=12.19.0` | `pip install -e ".[azure]"` |
| Chroma DB | `chromadb>=0.4.0` | `pip install -e ".[chroma]"` |
| Weaviate | `weaviate-client>=3.25.0` | `pip install -e ".[weaviate]"` |
| Embedding Server | `fastapi>=0.109.0`, `uvicorn>=0.27.0`, `sentence-transformers>=2.3.0` | `pip install -e ".[embedding]"` |

### Dev Dependencies (in dependency-groups)

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=8.4.2 | Testing framework |
| `pytest-asyncio` | >=0.24.0 | Async test support |
| `pytest-cov` | >=7.0.0 | Coverage |
| `coverage` | >=7.11.0 | Coverage reporting |
| `ruff` | >=0.14.13 | Linting/formatting |
| `mypy` | >=1.19.1 | Type checking |

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

**Docker build failures**
- Ensure you have BuildKit enabled: `DOCKER_BUILDKIT=1`
- Check that all submodules are initialized: `git submodule update --init`

**Rate limit errors from GitHub**
- Set `GITHUB_TOKEN` environment variable for authenticated requests
- Improves rate limit from 60 to 5000 requests/hour

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

## Environment Variables Reference

| Variable | Purpose | Required For |
|----------|---------|--------------|
| `ANTHROPIC_API_KEY` | Claude AI API access | Claude enhancement/upload |
| `GOOGLE_API_KEY` | Google Gemini API access | Gemini enhancement/upload |
| `OPENAI_API_KEY` | OpenAI API access | OpenAI enhancement/upload |
| `GITHUB_TOKEN` | GitHub API authentication | GitHub scraping (recommended) |
| `AWS_ACCESS_KEY_ID` | AWS S3 authentication | S3 cloud storage |
| `AWS_SECRET_ACCESS_KEY` | AWS S3 authentication | S3 cloud storage |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCS authentication path | GCS cloud storage |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Blob authentication | Azure cloud storage |
| `ANTHROPIC_BASE_URL` | Custom Claude endpoint | Custom API endpoints |
| `SKILL_SEEKERS_HOME` | Data directory path | Docker/runtime |
| `SKILL_SEEKERS_OUTPUT` | Output directory path | Docker/runtime |

---

*This document is maintained for AI coding agents. For human contributors, see README.md and CONTRIBUTING.md.*

*Last updated: 2026-02-08*
