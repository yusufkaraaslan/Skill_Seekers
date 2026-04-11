# Frequently Asked Questions (FAQ)

**Version:** 3.2.0
**Last Updated:** 2026-03-15

---

## General Questions

### What is Skill Seekers?

Skill Seekers is a Python tool that converts 17 source types — documentation websites, GitHub repos, PDFs, videos, Word docs, EPUB books, Jupyter notebooks, local HTML files, OpenAPI specs, AsciiDoc, PowerPoint, RSS/Atom feeds, man pages, Confluence wikis, Notion pages, Slack/Discord exports, and local codebases — into AI-ready formats for 30+ platforms: LLM platforms (Claude, Gemini, OpenAI, MiniMax, OpenCode, Kimi, DeepSeek, Qwen, OpenRouter, Together AI, Fireworks AI, Markdown), RAG frameworks (LangChain, LlamaIndex, Haystack), vector databases (ChromaDB, FAISS, Weaviate, Qdrant, Pinecone), and AI coding assistants (Cursor, Windsurf, Cline, Continue.dev, Roo, Aider, Bolt, Kilo, Kimi Code).

**Use Cases:**
- Create custom documentation skills for your favorite frameworks
- Analyze GitHub repositories and extract code patterns
- Convert PDF manuals into searchable AI skills
- Import knowledge from Confluence, Notion, or Slack/Discord
- Extract content from videos (YouTube, Vimeo, local files)
- Convert Jupyter notebooks, EPUB books, or PowerPoint slides into skills
- Parse OpenAPI/Swagger specs into API reference skills
- Combine multiple sources (docs + code + PDFs + more) into unified skills

### Which platforms are supported?

**Supported Platforms (30+):**

*LLM Platforms (12):*
1. **Claude AI** - ZIP format with YAML frontmatter
2. **Google Gemini** - tar.gz format for Grounded Generation
3. **OpenAI ChatGPT** - ZIP format for Vector Stores
4. **MiniMax** - ZIP format
5. **OpenCode** - ZIP format
6. **Kimi** - ZIP format
7. **DeepSeek** - ZIP format
8. **Qwen** - ZIP format
9. **OpenRouter** - ZIP format for multi-model routing
10. **Together AI** - ZIP format for open-source models
11. **Fireworks AI** - ZIP format for fast inference
12. **Generic Markdown** - ZIP format with markdown files

*RAG Frameworks:*
13. **LangChain** - Document objects for QA chains and agents
14. **LlamaIndex** - TextNodes for query engines
15. **Haystack** - Document objects for enterprise RAG

*Vector Databases:*
16. **ChromaDB** - Direct collection upload
17. **FAISS** - Index files for local similarity search
18. **Weaviate** - Vector objects with schema creation
19. **Qdrant** - Points with payload indexing
20. **Pinecone** - Ready-to-upsert format

*AI Coding Assistants (9):*
21. **Cursor** - .cursorrules persistent context
22. **Windsurf** - .windsurfrules AI coding rules
23. **Cline** - .clinerules + MCP integration
24. **Continue.dev** - HTTP context server (all IDEs)
25. **Roo** - .roorules AI coding rules
26. **Aider** - Terminal AI coding assistant
27. **Bolt** - Web IDE AI context
28. **Kilo** - IDE AI context
29. **Kimi Code** - IDE AI context

Each platform has a dedicated adaptor for optimal formatting and upload.

### Is it free to use?

**Tool:** Yes, Skill Seekers is 100% free and open-source (MIT license).

**API Costs:**
- **Scraping:** Free (just bandwidth)
- **AI Enhancement (API mode):** ~$0.15-0.30 per skill (Claude API)
- **AI Enhancement (LOCAL mode):** Free! (uses your Claude Code Max plan)
- **Upload:** Free (platform storage limits apply)

**Recommendation:** Use LOCAL mode for free AI enhancement or skip enhancement entirely.

### How do I set up video extraction?

**Quick setup:**
```bash
# 1. Install video support
pip install skill-seekers[video-full]

# 2. Auto-detect GPU and install visual deps
skill-seekers video --setup
```

The `--setup` command auto-detects your GPU vendor (NVIDIA CUDA, AMD ROCm, or CPU-only) and installs the correct PyTorch variant along with easyocr and other visual extraction dependencies. This avoids the ~2GB NVIDIA CUDA download that would happen if easyocr were installed via pip on non-NVIDIA systems.

**What it detects:**
- **NVIDIA:** Uses `nvidia-smi` to find CUDA version → installs matching `cu124`/`cu121`/`cu118` PyTorch
- **AMD:** Uses `rocminfo` to find ROCm version → installs matching ROCm PyTorch
- **CPU-only:** Installs lightweight CPU-only PyTorch

### What source types are supported?

Skill Seekers supports **17 source types**:

| # | Source Type | CLI Command | Auto-Detection |
|---|------------|-------------|----------------|
| 1 | Documentation (web) | `scrape` / `create <url>` | HTTP/HTTPS URLs |
| 2 | GitHub repo | `github` / `create owner/repo` | `owner/repo` or github.com URLs |
| 3 | PDF | `pdf` / `create file.pdf` | `.pdf` extension |
| 4 | Word (.docx) | `word` / `create file.docx` | `.docx` extension |
| 5 | EPUB | `epub` / `create file.epub` | `.epub` extension |
| 6 | Video | `video` / `create <url/file>` | YouTube/Vimeo URLs, video extensions |
| 7 | Local codebase | `analyze` / `create ./path` | Directory paths |
| 8 | Jupyter Notebook | `jupyter` / `create file.ipynb` | `.ipynb` extension |
| 9 | Local HTML | `html` / `create file.html` | `.html`/`.htm` extensions |
| 10 | OpenAPI/Swagger | `openapi` / `create spec.yaml` | `.yaml`/`.yml` with OpenAPI content |
| 11 | AsciiDoc | `asciidoc` / `create file.adoc` | `.adoc`/`.asciidoc` extensions |
| 12 | PowerPoint | `pptx` / `create file.pptx` | `.pptx` extension |
| 13 | RSS/Atom | `rss` / `create feed.rss` | `.rss`/`.atom` extensions |
| 14 | Man pages | `manpage` / `create cmd.1` | `.1`-`.8`/`.man` extensions |
| 15 | Confluence | `confluence` | API or export directory |
| 16 | Notion | `notion` | API or export directory |
| 17 | Slack/Discord | `chat` | Export directory or API |

The `create` command auto-detects the source type from your input, so you often don't need to specify a subcommand.

### How long does it take to create a skill?

**Typical Times:**
- Documentation scraping: 5-45 minutes (depends on size)
- GitHub analysis: 1-5 minutes (basic) or 20-60 minutes (C3.x deep analysis)
- PDF extraction: 30 seconds - 5 minutes
- Video extraction: 2-10 minutes (depends on length and visual analysis)
- Word/EPUB/PPTX: 10-60 seconds
- Jupyter notebook: 10-30 seconds
- OpenAPI spec: 5-15 seconds
- Confluence/Notion import: 1-5 minutes (depends on space size)
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

### How do I scrape a Jupyter Notebook?

```bash
# Extract cells, outputs, and markdown from a notebook
skill-seekers jupyter analysis.ipynb --name data-analysis

# Or use auto-detection
skill-seekers create analysis.ipynb
```

Jupyter extraction preserves code cells, markdown cells, and cell outputs. It works with `.ipynb` files from JupyterLab, Google Colab, and other notebook environments.

### How do I import from Confluence or Notion?

**Confluence:**
```bash
# From Confluence Cloud API
export CONFLUENCE_URL=https://yourorg.atlassian.net
export CONFLUENCE_TOKEN=your-api-token
export CONFLUENCE_EMAIL=your-email@example.com
skill-seekers confluence --space MYSPACE --name my-wiki

# From a Confluence HTML/XML export directory
skill-seekers confluence --export-dir ./confluence-export --name my-wiki
```

**Notion:**
```bash
# From Notion API
export NOTION_TOKEN=secret_...
skill-seekers notion --database DATABASE_ID --name my-notes

# From a Notion HTML/Markdown export directory
skill-seekers notion --export-dir ./notion-export --name my-notes
```

### How do I convert Word, EPUB, or PowerPoint files?

```bash
# Word document
skill-seekers word report.docx --name quarterly-report

# EPUB book
skill-seekers epub handbook.epub --name dev-handbook

# PowerPoint presentation
skill-seekers pptx slides.pptx --name training-deck

# Or use auto-detection for any of them
skill-seekers create report.docx
skill-seekers create handbook.epub
skill-seekers create slides.pptx
```

### How do I parse an OpenAPI/Swagger spec?

```bash
# From a local YAML/JSON file
skill-seekers openapi api-spec.yaml --name my-api

# Auto-detection works too
skill-seekers create api-spec.yaml
```

OpenAPI extraction parses endpoints, schemas, parameters, and examples into a structured API reference skill.

### How do I extract content from RSS feeds or man pages?

```bash
# RSS/Atom feed
skill-seekers rss https://blog.example.com/feed.xml --name blog-feed

# Man page
skill-seekers manpage grep.1 --name grep-manual
```

### How do I import from Slack or Discord?

```bash
# From a Slack export directory
skill-seekers chat --platform slack --export-dir ./slack-export --name team-knowledge

# From a Discord export directory
skill-seekers chat --platform discord --export-dir ./discord-export --name server-archive
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
- MiniMax/Kimi/DeepSeek/Qwen: Best for Chinese LLM ecosystem
- OpenRouter/Together/Fireworks: Best for multi-model routing or open-source model access
- Markdown: Generic export for other tools

### Can I use multiple platforms at once?

Yes! Package and upload to all platforms:

```bash
# Package for all platforms
for platform in claude gemini openai minimax kimi deepseek qwen openrouter together fireworks markdown; do
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

**Two Modes (via AgentClient):**
1. **API Mode:** Multi-provider AI API calls -- Anthropic, Moonshot/Kimi, Gemini, OpenAI (fast, costs ~$0.15-0.30)
2. **LOCAL Mode:** Any supported coding agent -- Claude Code, Kimi, Codex, Copilot, OpenCode, or custom (free with agent subscription)

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

**26 MCP tools:**

*Core Tools (9):*
1. `list_configs` - List preset configurations
2. `generate_config` - Generate config from docs URL
3. `validate_config` - Validate config structure
4. `estimate_pages` - Estimate page count
5. `scrape_docs` - Scrape documentation
6. `package_skill` - Package to .zip (supports `--format` and `--target`)
7. `upload_skill` - Upload to platform (supports `--target`)
8. `enhance_skill` - AI enhancement
9. `install_skill` - Complete workflow

*Extended Tools (10):*
10. `scrape_github` - GitHub analysis
11. `scrape_pdf` - PDF extraction
12. `unified_scrape` - Multi-source scraping
13. `merge_sources` - Merge docs + code
14. `detect_conflicts` - Find discrepancies
15. `split_config` - Split large configs
16. `generate_router` - Generate router skills
17. `add_config_source` - Register git repos
18. `fetch_config` - Fetch configs from git
19. `list_config_sources` - List registered sources
20. `remove_config_source` - Remove config source

*Vector DB Tools (4):*
21. `export_to_chroma` - Export to ChromaDB
22. `export_to_weaviate` - Export to Weaviate
23. `export_to_faiss` - Export to FAISS
24. `export_to_qdrant` - Export to Qdrant

*Cloud Tools (3):*
25. `cloud_upload` - Upload to S3/GCS/Azure
26. `cloud_download` - Download from cloud storage

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

**Version:** 3.2.0
**Last Updated:** 2026-03-15
**Questions? Ask on [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)**
