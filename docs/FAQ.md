# Frequently Asked Questions (FAQ)

**Version:** 2.7.0
**Last Updated:** 2026-01-18

---

## General Questions

### What is Skill Seekers?

Skill Seekers is a Python tool that converts documentation websites, GitHub repositories, and PDF files into AI skills for Claude AI, Google Gemini, OpenAI ChatGPT, and generic Markdown format.

**Use Cases:**
- Create custom documentation skills for your favorite frameworks
- Analyze GitHub repositories and extract code patterns
- Convert PDF manuals into searchable AI skills
- Combine multiple sources (docs + code + PDFs) into unified skills

### Which platforms are supported?

**Supported Platforms (4):**
1. **Claude AI** - ZIP format with YAML frontmatter
2. **Google Gemini** - tar.gz format for Grounded Generation
3. **OpenAI ChatGPT** - ZIP format for Vector Stores
4. **Generic Markdown** - ZIP format with markdown files

Each platform has a dedicated adaptor for optimal formatting and upload.

### Is it free to use?

**Tool:** Yes, Skill Seekers is 100% free and open-source (MIT license).

**API Costs:**
- **Scraping:** Free (just bandwidth)
- **AI Enhancement (API mode):** ~$0.15-0.30 per skill (Claude API)
- **AI Enhancement (LOCAL mode):** Free! (uses your Claude Code Max plan)
- **Upload:** Free (platform storage limits apply)

**Recommendation:** Use LOCAL mode for free AI enhancement or skip enhancement entirely.

### How long does it take to create a skill?

**Typical Times:**
- Documentation scraping: 5-45 minutes (depends on size)
- GitHub analysis: 1-5 minutes (basic) or 20-60 minutes (C3.x deep analysis)
- PDF extraction: 30 seconds - 5 minutes
- AI enhancement: 30-60 seconds (LOCAL or API mode)
- Total workflow: 10-60 minutes

**Speed Tips:**
- Use `--async` for 2-3x faster scraping
- Use `--skip-scrape` to rebuild without re-scraping
- Skip AI enhancement for faster workflow

---

## Installation & Setup

### How do I install Skill Seekers?

```bash
# Basic installation
pip install skill-seekers

# With all platform support
pip install skill-seekers[all-llms]

# Development installation
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd Skill_Seekers
pip install -e ".[all-llms,dev]"
```

### What Python version do I need?

**Required:** Python 3.10 or higher
**Tested on:** Python 3.10, 3.11, 3.12, 3.13
**OS Support:** Linux, macOS, Windows (WSL recommended)

**Check your version:**
```bash
python --version  # Should be 3.10+
```

### Why do I get "No module named 'skill_seekers'" error?

**Common Causes:**
1. Package not installed
2. Wrong Python environment

**Solutions:**
```bash
# Install package
pip install skill-seekers

# Or for development
pip install -e .

# Verify installation
skill-seekers --version
```

### How do I set up API keys?

```bash
# Claude AI (for enhancement and upload)
export ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini (for upload)
export GOOGLE_API_KEY=AIza...

# OpenAI ChatGPT (for upload)
export OPENAI_API_KEY=sk-...

# GitHub (for higher rate limits)
export GITHUB_TOKEN=ghp_...

# Make permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc
```

---

## Usage Questions

### How do I scrape documentation?

**Using preset config:**
```bash
skill-seekers scrape --config react
```

**Using custom URL:**
```bash
skill-seekers scrape --base-url https://docs.example.com --name my-framework
```

**From custom config file:**
```bash
skill-seekers scrape --config configs/my-framework.json
```

### Can I analyze GitHub repositories?

Yes! Skill Seekers has powerful GitHub analysis:

```bash
# Basic analysis (fast)
skill-seekers github https://github.com/facebook/react

# Deep C3.x analysis (includes patterns, tests, guides)
skill-seekers github https://github.com/vercel/next.js --analysis-depth c3x
```

**C3.x Features:**
- Design pattern detection (10 GoF patterns)
- Test example extraction
- How-to guide generation
- Configuration pattern extraction
- Architectural overview
- API reference generation

### Can I extract content from PDFs?

Yes! PDF extraction with OCR support:

```bash
# Basic PDF extraction
skill-seekers pdf manual.pdf --name product-manual

# With OCR (for scanned PDFs)
skill-seekers pdf scanned.pdf --enable-ocr

# Extract images and tables
skill-seekers pdf document.pdf --extract-images --extract-tables
```

### Can I combine multiple sources?

Yes! Unified multi-source scraping:

**Create unified config** (`configs/unified/my-framework.json`):
```json
{
  "name": "my-framework",
  "sources": {
    "documentation": {
      "type": "docs",
      "base_url": "https://docs.example.com"
    },
    "github": {
      "type": "github",
      "repo_url": "https://github.com/org/repo"
    },
    "pdf": {
      "type": "pdf",
      "pdf_path": "manual.pdf"
    }
  }
}
```

**Run unified scraping:**
```bash
skill-seekers unified --config configs/unified/my-framework.json
```

### How do I upload skills to platforms?

```bash
# Upload to Claude AI
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers upload output/react-claude.zip --target claude

# Upload to Google Gemini
export GOOGLE_API_KEY=AIza...
skill-seekers upload output/react-gemini.tar.gz --target gemini

# Upload to OpenAI ChatGPT
export OPENAI_API_KEY=sk-...
skill-seekers upload output/react-openai.zip --target openai
```

**Or use complete workflow:**
```bash
skill-seekers install react --target claude --upload
```

---

## Platform-Specific Questions

### What's the difference between platforms?

| Feature | Claude AI | Google Gemini | OpenAI ChatGPT | Markdown |
|---------|-----------|---------------|----------------|----------|
| Format | ZIP + YAML | tar.gz | ZIP | ZIP |
| Upload API | Projects API | Corpora API | Vector Stores | N/A |
| Model | Sonnet 4.5 | Gemini 2.0 Flash | GPT-4o | N/A |
| Max Size | 32MB | 10MB | 512MB | N/A |
| Use Case | Claude Code | Grounded Gen | ChatGPT Custom | Export |

**Choose based on:**
- Claude AI: Best for Claude Code integration
- Google Gemini: Best for Grounded Generation in Gemini
- OpenAI ChatGPT: Best for ChatGPT Custom GPTs
- Markdown: Generic export for other tools

### Can I use multiple platforms at once?

Yes! Package and upload to all platforms:

```bash
# Package for all platforms
for platform in claude gemini openai markdown; do
  skill-seekers package output/react/ --target $platform
done

# Upload to all platforms
skill-seekers install react --target claude,gemini,openai --upload
```

### How do I use skills in Claude Code?

1. **Install skill to Claude Code directory:**
```bash
skill-seekers install-agent --skill-dir output/react/ --agent-dir ~/.claude/skills/react
```

2. **Use in Claude Code:**
```
Use the react skill to explain React hooks
```

3. **Or upload to Claude AI:**
```bash
skill-seekers upload output/react-claude.zip --target claude
```

---

## Features & Capabilities

### What is AI enhancement?

AI enhancement transforms basic skills (2-3/10 quality) into production-ready skills (8-9/10 quality) using LLMs.

**Two Modes:**
1. **API Mode:** Direct Claude API calls (fast, costs ~$0.15-0.30)
2. **LOCAL Mode:** Uses Claude Code CLI (free with your Max plan)

**What it improves:**
- Better organization and structure
- Clearer explanations
- More examples and use cases
- Better cross-references
- Improved searchability

**Usage:**
```bash
# API mode (if ANTHROPIC_API_KEY is set)
skill-seekers enhance output/react/

# LOCAL mode (free!)
skill-seekers enhance output/react/ --mode LOCAL

# Background mode
skill-seekers enhance output/react/ --background
skill-seekers enhance-status output/react/ --watch
```

### What are C3.x features?

C3.x features are advanced codebase analysis capabilities:

- **C3.1:** Design pattern detection (Singleton, Factory, Strategy, etc.)
- **C3.2:** Test example extraction (real usage examples from tests)
- **C3.3:** How-to guide generation (educational guides from test workflows)
- **C3.4:** Configuration pattern extraction (env vars, config files)
- **C3.5:** Architectural overview (system architecture analysis)
- **C3.6:** AI enhancement (Claude API integration for insights)
- **C3.7:** Architectural pattern detection (MVC, MVVM, Repository, etc.)
- **C3.8:** Standalone codebase scraping (300+ line SKILL.md from code alone)

**Enable C3.x:**
```bash
# All C3.x features enabled by default
skill-seekers codebase --directory /path/to/repo

# Skip specific features
skill-seekers codebase --directory . --skip-patterns --skip-how-to-guides
```

### What are router skills?

Router skills help Claude navigate large documentation (>500 pages) by providing a table of contents and keyword index.

**When to use:**
- Documentation with 500+ pages
- Complex multi-section docs
- Large API references

**Generate router:**
```bash
skill-seekers generate-router output/large-docs/
```

### What preset configurations are available?

**24 preset configs:**
- Web: react, vue, angular, svelte, nextjs
- Python: django, flask, fastapi, sqlalchemy, pytest
- Game Dev: godot, pygame, unity
- DevOps: docker, kubernetes, terraform, ansible
- Unified: react-unified, vue-unified, nextjs-unified, etc.

**List all:**
```bash
skill-seekers list-configs
```

---

## Troubleshooting

### Scraping is very slow, how can I speed it up?

**Solutions:**
1. **Use async mode** (2-3x faster):
```bash
skill-seekers scrape --config react --async
```

2. **Increase rate limit** (faster requests):
```json
{
  "rate_limit": 0.1  // Faster (but may hit rate limits)
}
```

3. **Limit pages**:
```json
{
  "max_pages": 100  // Stop after 100 pages
}
```

### Why are some pages missing?

**Common Causes:**
1. **URL patterns exclude them**
2. **Max pages limit reached**
3. **BFS didn't reach them**

**Solutions:**
```bash
# Check URL patterns in config
{
  "url_patterns": {
    "include": ["/docs/"],  // Make sure your pages match
    "exclude": []           // Remove overly broad exclusions
  }
}

# Increase max pages
{
  "max_pages": 1000  // Default is 500
}

# Use verbose mode to see what's being scraped
skill-seekers scrape --config react --verbose
```

### How do I fix "NetworkError: Connection failed"?

**Solutions:**
1. **Check internet connection**
2. **Verify URL is accessible**:
```bash
curl -I https://docs.example.com
```

3. **Increase timeout**:
```json
{
  "timeout": 30  // 30 seconds
}
```

4. **Check rate limiting**:
```json
{
  "rate_limit": 1.0  // Slower requests
}
```

### Tests are failing, what should I do?

**Quick fixes:**
```bash
# Ensure package is installed
pip install -e ".[all-llms,dev]"

# Clear caches
rm -rf .pytest_cache/ **/__pycache__/

# Run specific failing test
pytest tests/test_file.py::test_name -vv

# Check for missing dependencies
pip install -e ".[all-llms,dev]"
```

**If still failing:**
1. Check [Troubleshooting Guide](../TROUBLESHOOTING.md)
2. Report issue on [GitHub](https://github.com/yusufkaraaslan/Skill_Seekers/issues)

---

## MCP Server Questions

### How do I start the MCP server?

```bash
# stdio mode (Claude Code, VS Code + Cline)
skill-seekers-mcp

# HTTP mode (Cursor, Windsurf, IntelliJ)
skill-seekers-mcp --transport http --port 8765
```

### What MCP tools are available?

**18 MCP tools:**
1. `list_configs` - List preset configurations
2. `generate_config` - Generate config from docs URL
3. `validate_config` - Validate config structure
4. `estimate_pages` - Estimate page count
5. `scrape_docs` - Scrape documentation
6. `package_skill` - Package to .zip
7. `upload_skill` - Upload to platform
8. `enhance_skill` - AI enhancement
9. `install_skill` - Complete workflow
10. `scrape_github` - GitHub analysis
11. `scrape_pdf` - PDF extraction
12. `unified_scrape` - Multi-source scraping
13. `merge_sources` - Merge docs + code
14. `detect_conflicts` - Find discrepancies
15. `split_config` - Split large configs
16. `generate_router` - Generate router skills
17. `add_config_source` - Register git repos
18. `fetch_config` - Fetch configs from git

### How do I configure MCP for Claude Code?

**Add to `claude_desktop_config.json`:**
```json
{
  "mcpServers": {
    "skill-seekers": {
      "command": "skill-seekers-mcp"
    }
  }
}
```

**Restart Claude Code**, then use:
```
Use skill-seekers MCP tools to scrape React documentation
```

---

## Advanced Questions

### Can I use Skill Seekers programmatically?

Yes! Full API for Python integration:

```python
from skill_seekers.cli.doc_scraper import scrape_all, build_skill
from skill_seekers.cli.adaptors import get_adaptor

# Scrape documentation
pages = scrape_all(
    base_url='https://docs.example.com',
    selectors={'main_content': 'article'},
    config={'name': 'example'}
)

# Build skill
skill_path = build_skill(
    config_name='example',
    output_dir='output/example'
)

# Package for platform
adaptor = get_adaptor('claude')
package_path = adaptor.package(skill_path, 'output/')
```

**See:** [API Reference](reference/API_REFERENCE.md)

### How do I create custom configurations?

**Create config file** (`configs/my-framework.json`):
```json
{
  "name": "my-framework",
  "description": "My custom framework documentation",
  "base_url": "https://docs.example.com/",
  "selectors": {
    "main_content": "article",  // CSS selector
    "title": "h1",
    "code_blocks": "pre code"
  },
  "url_patterns": {
    "include": ["/docs/", "/api/"],
    "exclude": ["/blog/", "/changelog/"]
  },
  "categories": {
    "getting_started": ["intro", "quickstart"],
    "api": ["api", "reference"]
  },
  "rate_limit": 0.5,
  "max_pages": 500
}
```

**Use config:**
```bash
skill-seekers scrape --config configs/my-framework.json
```

### Can I contribute preset configs?

Yes! We welcome config contributions:

1. **Create config** in `configs/` directory
2. **Test it** thoroughly:
```bash
skill-seekers scrape --config configs/your-framework.json
```
3. **Submit PR** on [GitHub](https://github.com/yusufkaraaslan/Skill_Seekers)

**Guidelines:**
- Name: `{framework-name}.json`
- Include all required fields
- Add to appropriate category
- Test with real documentation

### How do I debug scraping issues?

```bash
# Verbose output
skill-seekers scrape --config react --verbose

# Dry run (no actual scraping)
skill-seekers scrape --config react --dry-run

# Single page test
skill-seekers scrape --base-url https://docs.example.com/intro --max-pages 1

# Check selectors
skill-seekers validate-config configs/react.json
```

---

## Getting More Help

### Where can I find documentation?

**Main Documentation:**
- [README](../README.md) - Project overview
- [Usage Guide](guides/USAGE.md) - Detailed usage
- [API Reference](reference/API_REFERENCE.md) - Programmatic usage
- [Troubleshooting](../TROUBLESHOOTING.md) - Common issues

**Guides:**
- [MCP Setup](guides/MCP_SETUP.md)
- [Testing Guide](guides/TESTING_GUIDE.md)
- [Migration Guide](guides/MIGRATION_GUIDE.md)
- [Quick Reference](QUICK_REFERENCE.md)

### How do I report bugs?

1. **Check existing issues:** https://github.com/yusufkaraaslan/Skill_Seekers/issues
2. **Create new issue** with:
   - Skill Seekers version (`skill-seekers --version`)
   - Python version (`python --version`)
   - Operating system
   - Config file (if relevant)
   - Error message and stack trace
   - Steps to reproduce

### How do I request features?

1. **Check roadmap:** [ROADMAP.md](../ROADMAP.md)
2. **Create feature request:** https://github.com/yusufkaraaslan/Skill_Seekers/issues
3. **Join discussions:** https://github.com/yusufkaraaslan/Skill_Seekers/discussions

### Is there a community?

Yes!
- **GitHub Discussions:** https://github.com/yusufkaraaslan/Skill_Seekers/discussions
- **Issue Tracker:** https://github.com/yusufkaraaslan/Skill_Seekers/issues
- **Project Board:** https://github.com/users/yusufkaraaslan/projects/2

---

**Version:** 2.7.0
**Last Updated:** 2026-01-18
**Questions? Ask on [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)**
