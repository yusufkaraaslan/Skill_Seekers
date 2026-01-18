# Quick Reference - Skill Seekers Cheat Sheet

**Version:** 2.7.0 | **Quick Commands** | **One-Page Reference**

---

## Installation

```bash
# Basic installation
pip install skill-seekers

# With all platforms
pip install skill-seekers[all-llms]

# Development mode
pip install -e ".[all-llms,dev]"
```

---

## CLI Commands

### Documentation Scraping

```bash
# Scrape with preset config
skill-seekers scrape --config react

# Scrape custom site
skill-seekers scrape --base-url https://docs.example.com --name my-framework

# Rebuild without re-scraping
skill-seekers scrape --config react --skip-scrape

# Async scraping (2-3x faster)
skill-seekers scrape --config react --async
```

### GitHub Repository Analysis

```bash
# Basic analysis
skill-seekers github https://github.com/facebook/react

# Deep C3.x analysis (patterns, tests, guides)
skill-seekers github https://github.com/vercel/next.js --analysis-depth c3x

# With GitHub token (higher rate limits)
GITHUB_TOKEN=ghp_... skill-seekers github https://github.com/org/repo
```

### PDF Extraction

```bash
# Extract from PDF
skill-seekers pdf manual.pdf --name product-manual

# With OCR (scanned PDFs)
skill-seekers pdf scanned.pdf --enable-ocr

# Large PDF (chunked processing)
skill-seekers pdf large.pdf --chunk-size 50
```

### Multi-Source Scraping

```bash
# Unified scraping (docs + GitHub + PDF)
skill-seekers unified --config configs/unified/react-unified.json

# Merge separate sources
skill-seekers merge-sources \
  --docs output/react-docs \
  --github output/react-github \
  --output output/react-complete
```

### AI Enhancement

```bash
# API mode (fast, costs ~$0.15-0.30)
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers enhance output/react/

# LOCAL mode (free, uses Claude Code Max)
skill-seekers enhance output/react/ --mode LOCAL

# Background enhancement
skill-seekers enhance output/react/ --background

# Monitor background enhancement
skill-seekers enhance-status output/react/ --watch
```

### Packaging & Upload

```bash
# Package for Claude AI
skill-seekers package output/react/ --target claude

# Package for all platforms
for platform in claude gemini openai markdown; do
  skill-seekers package output/react/ --target $platform
done

# Upload to Claude AI
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers upload output/react-claude.zip --target claude

# Upload to Google Gemini
export GOOGLE_API_KEY=AIza...
skill-seekers upload output/react-gemini.tar.gz --target gemini
```

### Complete Workflow

```bash
# One command: fetch → scrape → enhance → package → upload
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers install react --target claude --enhance --upload

# Multi-platform install
skill-seekers install react --target claude,gemini,openai --enhance --upload

# Without enhancement or upload
skill-seekers install vue --target markdown
```

---

## Common Workflows

### Workflow 1: Quick Skill from Docs

```bash
# 1. Scrape documentation
skill-seekers scrape --config react

# 2. Package for Claude
skill-seekers package output/react/ --target claude

# 3. Upload to Claude
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers upload output/react-claude.zip --target claude
```

### Workflow 2: GitHub Repo to Skill

```bash
# 1. Analyze repository with C3.x features
skill-seekers github https://github.com/facebook/react --analysis-depth c3x

# 2. Package for multiple platforms
skill-seekers package output/react/ --target claude,gemini,openai
```

### Workflow 3: Complete Multi-Source Skill

```bash
# 1. Create unified config (configs/unified/my-framework.json)
{
  "name": "my-framework",
  "sources": {
    "documentation": {"type": "docs", "base_url": "https://docs..."},
    "github": {"type": "github", "repo_url": "https://github..."},
    "pdf": {"type": "pdf", "pdf_path": "manual.pdf"}
  }
}

# 2. Run unified scraping
skill-seekers unified --config configs/unified/my-framework.json

# 3. Enhance with AI
skill-seekers enhance output/my-framework/

# 4. Package and upload
skill-seekers package output/my-framework/ --target claude
skill-seekers upload output/my-framework-claude.zip --target claude
```

---

## MCP Server

### Starting MCP Server

```bash
# stdio mode (Claude Code, VS Code + Cline)
skill-seekers-mcp

# HTTP mode (Cursor, Windsurf, IntelliJ)
skill-seekers-mcp --transport http --port 8765
```

### MCP Tools (18 total)

**Core Tools:**
1. `list_configs` - List preset configurations
2. `generate_config` - Generate config from docs URL
3. `validate_config` - Validate config structure
4. `estimate_pages` - Estimate page count
5. `scrape_docs` - Scrape documentation
6. `package_skill` - Package to .zip
7. `upload_skill` - Upload to platform
8. `enhance_skill` - AI enhancement
9. `install_skill` - Complete workflow

**Extended Tools:**
10. `scrape_github` - GitHub analysis
11. `scrape_pdf` - PDF extraction
12. `unified_scrape` - Multi-source scraping
13. `merge_sources` - Merge docs + code
14. `detect_conflicts` - Find discrepancies
15. `split_config` - Split large configs
16. `generate_router` - Generate router skills
17. `add_config_source` - Register git repos
18. `fetch_config` - Fetch configs from git

---

## Environment Variables

```bash
# Claude AI (default platform)
export ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini
export GOOGLE_API_KEY=AIza...

# OpenAI ChatGPT
export OPENAI_API_KEY=sk-...

# GitHub (higher rate limits)
export GITHUB_TOKEN=ghp_...
```

---

## Testing

```bash
# Run all tests (1200+)
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/skill_seekers --cov-report=html

# Fast tests only (skip slow tests)
pytest tests/ -m "not slow"

# Specific test category
pytest tests/test_mcp*.py -v             # MCP tests
pytest tests/test_*_integration.py -v    # Integration tests
pytest tests/test_*_e2e.py -v            # E2E tests
```

---

## Code Quality

```bash
# Linting with Ruff
ruff check .                 # Check for issues
ruff check --fix .           # Auto-fix issues
ruff format .                # Format code

# Run before commit
ruff check . && ruff format --check . && pytest tests/ -v
```

---

## Preset Configurations (24)

**Web Frameworks:**
- `react`, `vue`, `angular`, `svelte`, `nextjs`

**Python:**
- `django`, `flask`, `fastapi`, `sqlalchemy`, `pytest`

**Game Development:**
- `godot`, `pygame`, `unity`

**Tools & Libraries:**
- `docker`, `kubernetes`, `terraform`, `ansible`

**Unified (Docs + GitHub):**
- `react-unified`, `vue-unified`, `nextjs-unified`, etc.

**List all configs:**
```bash
skill-seekers list-configs
```

---

## Tips & Tricks

### Speed Up Scraping

```bash
# Use async mode (2-3x faster)
skill-seekers scrape --config react --async

# Rebuild without re-scraping
skill-seekers scrape --config react --skip-scrape
```

### Save API Costs

```bash
# Use LOCAL mode for free AI enhancement
skill-seekers enhance output/react/ --mode LOCAL

# Or skip enhancement entirely
skill-seekers install react --target claude --no-enhance
```

### Large Documentation

```bash
# Generate router skill (>500 pages)
skill-seekers generate-router output/large-docs/

# Split configuration
skill-seekers split-config configs/large.json --output configs/split/
```

### Debugging

```bash
# Verbose output
skill-seekers scrape --config react --verbose

# Dry run (no actual scraping)
skill-seekers scrape --config react --dry-run

# Show config without scraping
skill-seekers validate-config configs/react.json
```

### Batch Processing

```bash
# Process multiple configs
for config in react vue angular svelte; do
  skill-seekers install $config --target claude
done

# Parallel processing
skill-seekers install react --target claude &
skill-seekers install vue --target claude &
wait
```

---

## File Locations

**Configurations:**
- Preset configs: `skill-seekers-configs/official/*.json`
- Custom configs: `configs/*.json`

**Output:**
- Scraped data: `output/{name}_data/`
- Built skills: `output/{name}/`
- Packages: `output/{name}-{platform}.{zip|tar.gz}`

**MCP:**
- Server: `src/skill_seekers/mcp/server_fastmcp.py`
- Tools: `src/skill_seekers/mcp/tools/*.py`

**Tests:**
- All tests: `tests/test_*.py`
- Fixtures: `tests/fixtures/`

---

## Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `NetworkError` | Connection failed | Check URL, internet connection |
| `InvalidConfigError` | Bad config | Validate with `validate-config` |
| `RateLimitError` | Too many requests | Increase `rate_limit` in config |
| `ScrapingError` | Scraping failed | Check selectors, URL patterns |
| `APIError` | Platform API failed | Check API key, quota |

---

## Getting Help

```bash
# Command help
skill-seekers --help
skill-seekers scrape --help
skill-seekers install --help

# Version info
skill-seekers --version

# Check configuration
skill-seekers validate-config configs/my-config.json
```

**Documentation:**
- [Full README](../README.md)
- [Usage Guide](guides/USAGE.md)
- [API Reference](reference/API_REFERENCE.md)
- [Troubleshooting](../TROUBLESHOOTING.md)

**Links:**
- GitHub: https://github.com/yusufkaraaslan/Skill_Seekers
- PyPI: https://pypi.org/project/skill-seekers/
- Issues: https://github.com/yusufkaraaslan/Skill_Seekers/issues

---

**Version:** 2.7.0 | **Test Count:** 1200+ | **Platforms:** Claude, Gemini, OpenAI, Markdown
