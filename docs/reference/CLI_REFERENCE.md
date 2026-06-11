# CLI Reference - Skill Seekers

> **Version:** 3.6.0
> **Last Updated:** 2026-03-15
> **Complete reference for all 30 CLI commands**

---

## Table of Contents

- [Overview](#overview)
  - [Installation](#installation)
  - [Global Flags](#global-flags)
  - [Environment Variables](#environment-variables)
- [Command Reference](#command-reference)
  - [analyze](#analyze) - Analyze local codebase
  - [asciidoc](#asciidoc) - Extract from AsciiDoc files
  - [chat](#chat) - Extract from Slack/Discord
  - [config](#config) - Configuration wizard
  - [confluence](#confluence) - Extract from Confluence
  - [create](#create) - Create skill (auto-detects source)
  - [enhance](#enhance) - AI enhancement (local mode)
  - [enhance-status](#enhance-status) - Monitor enhancement
  - [estimate](#estimate) - Estimate page counts
  - [github](#github) - Scrape GitHub repository
  - [Local HTML files (via `create`)](#local-html-files-via-create) - Extract from local HTML files
  - [install](#install) - One-command complete workflow
  - [install-agent](#install-agent) - Install to AI agent
  - [jupyter](#jupyter) - Extract from Jupyter notebooks
  - [manpage](#manpage) - Extract from man pages
  - [multilang](#multilang) - Multi-language docs
  - [notion](#notion) - Extract from Notion
  - [openapi](#openapi) - Extract from OpenAPI/Swagger specs
  - [package](#package) - Package skill for platform
  - [pdf](#pdf) - Extract from PDF
  - [pptx](#pptx) - Extract from PowerPoint files
  - [quality](#quality) - Quality scoring
  - [resume](#resume) - Resume interrupted jobs
  - [rss](#rss) - Extract from RSS/Atom feeds
  - [scan](#scan) - AI-detect a project's tech stack and emit per-framework configs
  - [scrape](#scrape) - Scrape documentation
  - [stream](#stream) - Stream large files
  - [unified](#unified) - Multi-source scraping
  - [update](#update) - Incremental updates
  - [upload](#upload) - Upload to platform
  - [video](#video) - Video extraction & setup
  - [workflows](#workflows) - Manage workflow presets
- [Common Workflows](#common-workflows)
- [Exit Codes](#exit-codes)
- [Troubleshooting](#troubleshooting)

---

## Overview

Skill Seekers provides a unified CLI for converting documentation, GitHub repositories, PDFs, videos, notebooks, wikis, and 18 source types (17 + config) into AI-ready skills for 21+ LLM platforms and RAG pipelines.

### Installation

```bash
# Basic installation
pip install skill-seekers

# With all platform support
pip install skill-seekers[all-llms]

# Development setup
pip install -e ".[all-llms,dev]"
```

Verify installation:
```bash
skill-seekers --version
```

### Global Flags

These flags work with **all source-type subcommands and `create`**:

| Flag | Description |
|------|-------------|
| `-h, --help` | Show help message and exit |
| `--version` | Show version number and exit |
| `-n, --name` | Skill name |
| `-d, --description` | Skill description |
| `-o, --output` | Output directory |
| `--enhance-level` | AI enhancement level (0-3) |
| `--api-key` | Anthropic API key |
| `-v, --verbose` | Enable verbose (DEBUG) output |
| `-q, --quiet` | Minimize output (WARNING only) |
| `--dry-run` | Preview without executing |
| `--enhance-workflow` | Apply enhancement workflow preset |

### Environment Variables

See [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) for complete reference.

**Common variables:**

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Claude AI API access |
| `GOOGLE_API_KEY` | Google Gemini API access |
| `OPENAI_API_KEY` | OpenAI API access |
| `GITHUB_TOKEN` | GitHub API (higher rate limits) |

---

## Command Reference

Commands are organized alphabetically.

---

### analyze

Analyze local codebase and extract code knowledge.

**Purpose:** Deep code analysis with pattern detection, API extraction, and documentation generation.

**Syntax:**
```bash
skill-seekers create DIR [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `DIR` (positional, or `--directory DIR`) | Yes | Directory to analyze |
| `--output DIR` | No | Output directory (default: output/codebase/) |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| `-n` | `--name` | auto | Skill name (defaults to directory name) |
| `-d` | `--description` | auto | Skill description |
| | `--preset` | standard | Analysis preset: quick, standard, comprehensive |
| | `--preset-list` | | Show available presets and exit |
| | `--languages` | auto | Comma-separated languages (Python,JavaScript,C++) |
| | `--file-patterns` | | Comma-separated file patterns |
| | `--enhance-level` | 0 | AI enhancement: 0=off (default), 1=SKILL.md, 2=+config, 3=full |
| | `--api-key` | | Anthropic API key (or ANTHROPIC_API_KEY env) |
| | `--enhance-workflow` | | Apply workflow preset (can use multiple) |
| | `--enhance-stage` | | Add inline enhancement stage (name:prompt) |
| | `--var` | | Override workflow variable (key=value) |
| | `--workflow-dry-run` | | Preview workflow without executing |
| | `--dry-run` | | Preview analysis without creating output |
| `-v` | `--verbose` | | Enable verbose (DEBUG) logging |
| `-q` | `--quiet` | | Minimize output (WARNING only) |
| | `--skip-api-reference` | | Skip API docs generation |
| | `--skip-dependency-graph` | | Skip dependency graph |
| | `--skip-patterns` | | Skip pattern detection |
| | `--skip-test-examples` | | Skip test example extraction |
| | `--skip-how-to-guides` | | Skip how-to guide generation |
| | `--skip-config-patterns` | | Skip config pattern extraction |
| | `--skip-docs` | | Skip project docs (README) |
| | `--no-comments` | | Skip comment extraction |

**Examples:**

```bash
# Basic analysis with defaults
skill-seekers create ./my-project

# Quick analysis (1-2 min)
skill-seekers create ./my-project --preset quick

# Comprehensive analysis with all features
skill-seekers create ./my-project --preset comprehensive

# Specific languages only
skill-seekers create ./my-project --languages Python,JavaScript

# Skip heavy features for faster analysis
skill-seekers create ./my-project --skip-dependency-graph --skip-patterns
```

**Exit Codes:**
- `0` - Success
- `1` - Analysis failed

---

### asciidoc

Extract content from AsciiDoc files and generate skill.

**Purpose:** Convert `.adoc` / `.asciidoc` documentation into AI-ready skills.

**Syntax:**
```bash
skill-seekers create <asciidoc-file> [options]
```

**Key Flags:**

| Flag | Description |
|------|-------------|
| `--asciidoc-path PATH` | Path to AsciiDoc file or directory |
| `-n, --name` | Skill name |
| `--from-json FILE` | Build from extracted JSON |
| `--enhance-level` | AI enhancement (default: 0) |
| `--dry-run` | Preview without executing |

**Examples:**

```bash
# Single file
skill-seekers create guide.adoc --name my-guide

# Directory of AsciiDoc files
skill-seekers create ./docs/ --name project-docs
```

---

### chat

Extract knowledge from Slack or Discord chat exports.

**Purpose:** Convert chat history into searchable AI-ready skills.

**Syntax:**
```bash
skill-seekers create [options]
```

**Key Flags:**

| Flag | Description |
|------|-------------|
| `--chat-export-path PATH` | Path to Slack/Discord export directory |
| `--platform {slack,discord}` | Chat platform (default: slack) |
| `-n, --name` | Skill name |
| `--dry-run` | Preview without executing |

**Examples:**

```bash
# From Slack export
skill-seekers create --chat-export-path ./slack-export/ --name team-knowledge

# From Discord export
skill-seekers create --chat-export-path ./discord-export/ --platform discord --name discord-docs
```

---

### config

Interactive configuration wizard for API keys and settings.

**Purpose:** Setup GitHub tokens, API keys, and preferences.

**Syntax:**
```bash
skill-seekers config [options]
```

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--github` | Go directly to GitHub token setup |
| | `--api-keys` | Go directly to API keys setup |
| | `--show` | Show current configuration |
| | `--test` | Test connections |

**Examples:**

```bash
# Full configuration wizard
skill-seekers config

# Quick GitHub setup
skill-seekers config --github

# View current config
skill-seekers config --show

# Test all connections
skill-seekers config --test
```

---

### confluence

Extract content from Confluence wikis.

**Purpose:** Convert Confluence spaces into AI-ready skills via API or HTML export.

**Syntax:**
```bash
skill-seekers create [options]
```

**Key Flags:**

| Flag | Description |
|------|-------------|
| `--conf-base-url URL` | Confluence instance base URL |
| `--space-key KEY` | Confluence space key |
| `--conf-export-path PATH` | Path to Confluence HTML/XML export directory |
| `--max-pages N` | Max pages to extract |
| `-n, --name` | Skill name |
| `--dry-run` | Preview without executing |

Authentication comes from the `CONFLUENCE_USERNAME` / `CONFLUENCE_TOKEN`
environment variables.

**Examples:**

```bash
# Via API
export CONFLUENCE_USERNAME=user@example.com
export CONFLUENCE_TOKEN=...
skill-seekers create --conf-base-url https://wiki.example.com --space-key DEV --name dev-wiki

# From export
skill-seekers create --conf-export-path ./confluence-export/ --name team-docs
```

---

### create

Create skill from any source. Auto-detects source type.

**Purpose:** Universal entry point - handles URLs, GitHub repos, local directories, PDFs, and config files automatically.

**Syntax:**
```bash
skill-seekers create [source] [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `source` | No | Source URL, repo, path, or config file |

**Source Types (Auto-Detected):**
| Source Pattern | Type | Example |
|----------------|------|---------|
| `https://...` | Documentation | `https://docs.react.dev/` |
| `owner/repo` | GitHub | `facebook/react` |
| `./path` | Local codebase | `./my-project` |
| `*.pdf` | PDF | `manual.pdf` |
| `*.docx` | Word | `report.docx` |
| `*.epub` | EPUB | `book.epub` |
| `*.ipynb` | Jupyter Notebook | `analysis.ipynb` |
| `*.html`/`*.htm` | Local HTML | `docs.html` |
| `*.yaml`/`*.yml` | OpenAPI/Swagger | `openapi.yaml` |
| `*.adoc`/`*.asciidoc` | AsciiDoc | `guide.adoc` |
| `*.pptx` | PowerPoint | `slides.pptx` |
| `*.rss`/`*.atom` | RSS/Atom feed | `feed.rss` |
| `*.1`-`*.8`/`*.man` | Man page | `grep.1` |
| `*.json` | Config file | `config.json` |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| `-n` | `--name` | auto | Skill name |
| `-d` | `--description` | auto | Skill description |
| `-o` | `--output` | auto | Output directory |
| `-p` | `--preset` | | Analysis preset: quick, standard, comprehensive |
| `-c` | `--config` | | Load settings from JSON file |
| | `--enhance-level` | 2 | AI enhancement level (0-3) |
| | `--api-key` | | Anthropic API key |
| | `--enhance-workflow` | | Apply workflow preset (can use multiple) |
| | `--enhance-stage` | | Add inline enhancement stage |
| | `--var` | | Override workflow variable (key=value) |
| | `--workflow-dry-run` | | Preview workflow without executing |
| | `--dry-run` | | Preview without creating |
| | `--chunk-for-rag` | | Enable RAG chunking |
| | `--chunk-tokens` | 512 | Chunk size in tokens |
| | `--chunk-overlap-tokens` | 50 | Chunk overlap in tokens |
| | `--help-web` | | Show web scraping options |
| | `--help-github` | | Show GitHub options |
| | `--help-local` | | Show local analysis options |
| | `--help-pdf` | | Show PDF options |
| | `--help-all` | | Show all 120+ options |

**Examples:**

```bash
# Documentation website
skill-seekers create https://docs.django.com/

# GitHub repository
skill-seekers create facebook/react

# Local codebase
skill-seekers create ./my-project

# PDF file
skill-seekers create manual.pdf --name product-docs

# With preset
skill-seekers create https://docs.react.dev/ --preset quick

# With enhancement workflow
skill-seekers create ./my-project --enhance-workflow security-focus

# Multi-workflow chaining
skill-seekers create ./my-project \
  --enhance-workflow security-focus \
  --enhance-workflow api-documentation
```

---

### enhance

Enhance SKILL.md using local coding agent (Claude Code).

**Purpose:** AI-powered quality improvement without API costs. Requires Claude Code installed.

**Syntax:**
```bash
skill-seekers enhance SKILL_DIRECTORY [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `SKILL_DIRECTORY` | Yes | Path to skill directory |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--agent` | claude | Local coding agent to use |
| | `--agent-cmd` | | Override agent command template |
| | `--background` | | Run in background |
| | `--daemon` | | Run as daemon |
| | `--no-force` | | Enable confirmations |
| | `--timeout` | 600 | Timeout in seconds |

**Examples:**

```bash
# Basic enhancement
skill-seekers enhance output/react/

# Background mode
skill-seekers enhance output/react/ --background

# With custom timeout
skill-seekers enhance output/react/ --timeout 1200

# Monitor background enhancement
skill-seekers enhance-status output/react/ --watch
```

**Requirements:** Claude Code must be installed and authenticated.

---

### enhance-status

Monitor background enhancement processes.

**Purpose:** Check status of enhancement running in background/daemon mode.

**Syntax:**
```bash
skill-seekers enhance-status SKILL_DIRECTORY [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `SKILL_DIRECTORY` | Yes | Path to skill directory |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| `-w` | `--watch` | | Watch in real-time |
| | `--json` | | JSON output |
| | `--interval` | 5 | Watch interval in seconds |

**Examples:**

```bash
# Check status once
skill-seekers enhance-status output/react/

# Watch continuously
skill-seekers enhance-status output/react/ --watch

# JSON output for scripting
skill-seekers enhance-status output/react/ --json
```

---

### estimate

Estimate page count before scraping.

**Purpose:** Preview how many pages will be scraped without downloading.

**Syntax:**
```bash
skill-seekers estimate [config] [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `config` | No | Config JSON file path |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--all` | | List all available configs |
| `-m` | `--max-discovery` | 1000 | Max pages to discover (`-1` for unlimited) |
| `-u` | `--unlimited` | | Remove discovery limit (same as `--max-discovery -1`) |
| `-t` | `--timeout` | 30 | HTTP request timeout in seconds |

**Examples:**

```bash
# Estimate with config file
skill-seekers estimate configs/react.json

# Quick estimate (100 pages)
skill-seekers estimate configs/react.json --max-discovery 100

# Discover everything, slower sites get more time
skill-seekers estimate configs/react.json --unlimited --timeout 60

# List all available presets
skill-seekers estimate --all
```

---

### github

Scrape GitHub repository and generate skill.

**Purpose:** Extract code, issues, releases, and metadata from GitHub repos.

**Syntax:**
```bash
skill-seekers create [options]
```

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--repo` | | Repository (owner/repo format) |
| `-c` | `--config` | | Config JSON file |
| | `--token` | | GitHub personal access token |
| `-n` | `--name` | auto | Skill name |
| `-d` | `--description` | auto | Description |
| `-o` | `--output` | auto | Output directory |
| | `--no-issues` | | Skip GitHub issues |
| | `--no-changelog` | | Skip CHANGELOG |
| | `--no-releases` | | Skip releases |
| | `--max-issues` | 100 | Max issues to fetch |
| | `--scrape-only` | | Only scrape, don't build |
| | `--enhance-level` | 2 | AI enhancement (0-3) |
| | `--api-key` | | Anthropic API key |
| | `--enhance-workflow` | | Apply workflow preset |
| | `--non-interactive` | | CI/CD mode (fail fast) |
| | `--profile` | | GitHub profile from config |
| | `--dry-run` | | Preview without executing |
| `-v` | `--verbose` | | Enable verbose (DEBUG) logging |
| `-q` | `--quiet` | | Minimize output (WARNING only) |

**Examples:**

```bash
# Basic repo analysis
skill-seekers create  facebook/react

# With GitHub token (higher rate limits)
skill-seekers create  facebook/react --token $GITHUB_TOKEN

# Skip issues for faster scraping
skill-seekers create  facebook/react --no-issues

# Dry run to preview
skill-seekers create  facebook/react --dry-run

# Scrape only, build later
skill-seekers create  facebook/react --scrape-only
```

---

### Local HTML files (via `create`)

Extract content from local HTML files or directories of HTML files. Use the
unified `create` command — the standalone `html` subcommand was removed in
v3.x.

**Purpose:** Convert local HTML documentation into AI-ready skills (for offline
mirrors, exported docs, wget snapshots, etc.).

**Auto-detection rules:**

| Input | Detected as |
|-------|-------------|
| `page.html` / `page.htm` / `page.xhtml` | `html` (single file) |
| Directory dominated by `.html`/`.htm`/`.xhtml` files | `html` (directory) |
| Mixed directory (mostly code) | `local` (codebase scraper) |
| `https://.../page.html` | `web` (fetched first) |

**Explicit override:** `--html-path PATH` forces html-scraper mode and beats
auto-detection. Useful when a directory contains a mix of code and HTML
files and you only want the HTML.

**Examples:**

```bash
# Single HTML file (auto-detected by extension)
skill-seekers create docs/index.html --name my-docs

# Whole directory of HTML files (auto-detected)
skill-seekers create ./mirror_output/site/ --name site-mirror

# Force HTML mode on a mixed/code-heavy directory
skill-seekers create ./repo/ --html-path ./repo/docs/build/html/ --name myrepo-docs

# --html-path alone works without a positional source
skill-seekers create --html-path ./html-export/ --name exported-docs
```

---

### install

One-command complete workflow: fetch → scrape → enhance → package → upload.

**Purpose:** End-to-end automation for common workflows.

**Syntax:**
```bash
skill-seekers install --config CONFIG [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `--config CONFIG` | Yes | Config name or path |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--destination` | output/ | Output directory |
| | `--no-upload` | | Skip upload to Claude |
| | `--unlimited` | | Remove page limits |
| | `--dry-run` | | Preview without executing |

**Examples:**

```bash
# Complete workflow with preset
skill-seekers install --config react

# Skip upload
skill-seekers install --config react --no-upload

# Custom config
skill-seekers install --config configs/my-project.json

# Dry run to preview
skill-seekers install --config react --dry-run
```

**Note:** AI enhancement is mandatory for install command.

---

### install-agent

Install skill to AI agent directories (Cursor, Windsurf, Cline).

**Purpose:** Direct installation to IDE AI assistant context directories.

**Syntax:**
```bash
skill-seekers install-agent SKILL_DIRECTORY --agent AGENT [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `SKILL_DIRECTORY` | Yes | Path to skill directory |
| `--agent AGENT` | Yes | Target agent: cursor, windsurf, cline, continue, roo, aider, bolt, kilo, kimi-code |

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--force` | Overwrite existing |

**Examples:**

```bash
# Install to Cursor
skill-seekers install-agent output/react/ --agent cursor

# Install to Windsurf
skill-seekers install-agent output/react/ --agent windsurf

# Force overwrite
skill-seekers install-agent output/react/ --agent cursor --force
```

---

### jupyter

Extract content from Jupyter Notebook files and generate skill.

**Purpose:** Convert `.ipynb` notebooks into AI-ready skills with code, markdown, and outputs.

**Syntax:**
```bash
skill-seekers create <notebook.ipynb> [options]
```

**Key Flags:**

| Flag | Description |
|------|-------------|
| `--notebook PATH` | Path to .ipynb file or directory |
| `-n, --name` | Skill name |
| `--from-json FILE` | Build from extracted JSON |
| `--enhance-level` | AI enhancement (default: 0) |
| `--dry-run` | Preview without executing |

**Examples:**

```bash
# Single notebook
skill-seekers create analysis.ipynb --name data-analysis

# Directory of notebooks
skill-seekers create ./notebooks/ --name ml-tutorials
```

---

### manpage

Extract content from Unix/Linux man pages and generate skill.

**Purpose:** Convert man pages into AI-ready reference skills.

**Syntax:**
```bash
skill-seekers create <manpage.1> [options]
```

**Key Flags:**

| Flag | Description |
|------|-------------|
| `--man-names NAMES` | Comma-separated man page names (e.g., `ls,grep,find`) |
| `--man-path PATH` | Path to directory containing man page files |
| `-n, --name` | Skill name |
| `--dry-run` | Preview without executing |

**Examples:**

```bash
# By name (system man pages)
skill-seekers create --man-names ls,grep,find,awk --name unix-essentials

# From directory
skill-seekers create --man-path /usr/share/man/man1/ --name section1-cmds
```

---

### multilang

Multi-language documentation support.

**Purpose:** Detect, report on, and export the languages present in a scraped skill directory.

**Syntax:**
```bash
skill-seekers multilang SKILL_DIRECTORY [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `SKILL_DIRECTORY` | Yes | Skill directory path |

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--detect` | Auto-detect languages |
| | `--report` | Generate translation report |
| | `--export` | Export by language to specified directory |
| | `--languages` | Restrict `--detect`/`--export` to these languages (space-separated, e.g. `en es fr`) |

**Examples:**

```bash
# Detect languages in a skill
skill-seekers multilang output/react/ --detect

# Translation coverage report
skill-seekers multilang output/react/ --report

# Export per-language trees, English and Spanish only
skill-seekers multilang output/react/ --export output/by-lang/ --languages en es
```

---

### notion

Extract content from Notion workspaces.

**Purpose:** Convert Notion pages and databases into AI-ready skills via API or export.

**Syntax:**
```bash
skill-seekers create [options]
```

**Key Flags:**

| Flag | Description |
|------|-------------|
| `--database-id ID` | Notion database ID to extract from |
| `--page-id ID` | Notion page ID to extract from |
| `--notion-export-path PATH` | Path to Notion export directory |
| `-n, --name` | Skill name |
| `--dry-run` | Preview without executing |

The Notion integration token comes from the `NOTION_TOKEN` environment variable.

**Examples:**

```bash
# Via API
export NOTION_TOKEN=secret_...
skill-seekers create --database-id abc123 --name team-docs

# From export
skill-seekers create --notion-export-path ./notion-export/ --name project-wiki
```

---

### openapi

Extract content from OpenAPI/Swagger specifications and generate skill.

**Purpose:** Convert API specs into AI-ready reference skills with endpoint documentation.

**Syntax:**
```bash
skill-seekers create <openapi.yaml> [options]
```

**Key Flags:**

| Flag | Description |
|------|-------------|
| `--spec PATH` | Path to OpenAPI/Swagger spec file |
| `--spec-url URL` | URL to OpenAPI/Swagger spec |
| `-n, --name` | Skill name |
| `--from-json FILE` | Build from extracted JSON |
| `--enhance-level` | AI enhancement (default: 0) |
| `--dry-run` | Preview without executing |

**Examples:**

```bash
# From local file
skill-seekers create api/openapi.yaml --name my-api

# From URL
skill-seekers create --spec-url https://petstore.swagger.io/v2/swagger.json --name petstore
```

---

### package

Package skill directory into platform-specific format.

**Purpose:** Create uploadable packages for Claude, Gemini, OpenAI, and RAG platforms.

**Syntax:**
```bash
skill-seekers package SKILL_DIRECTORY [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `SKILL_DIRECTORY` | Yes | Path to skill directory |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--target` | claude | Target platform |
| | `--no-open` | | Don't open output folder |
| | `--skip-quality-check` | | Skip quality checks |
| | `--upload` | | Auto-upload after packaging |
| | `--streaming` | | Streaming mode for large docs |
| | `--streaming-chunk-chars` | 4000 | Max chars per chunk (streaming) |
| | `--streaming-overlap-chars` | 200 | Overlap between chunks (chars) |
| | `--batch-size` | 100 | Chunks per batch |
| | `--chunk-for-rag` | | Enable RAG chunking |
| | `--chunk-tokens` | 512 | Max tokens per chunk |
| | `--chunk-overlap-tokens` | 50 | Overlap between chunks (tokens) |
| | `--no-preserve-code-blocks` | | Allow code block splitting |

**Supported Platforms:**

| Platform | Format | Flag |
|----------|--------|------|
| Claude AI | ZIP + YAML | `--target claude` |
| Google Gemini | tar.gz | `--target gemini` |
| OpenAI | ZIP + Vector | `--target openai` |
| MiniMax | ZIP | `--target minimax` |
| OpenCode | ZIP | `--target opencode` |
| Kimi | ZIP | `--target kimi` |
| DeepSeek | ZIP | `--target deepseek` |
| Qwen | ZIP | `--target qwen` |
| OpenRouter | ZIP | `--target openrouter` |
| Together AI | ZIP | `--target together` |
| Fireworks AI | ZIP | `--target fireworks` |
| LangChain | Documents | `--target langchain` |
| LlamaIndex | TextNodes | `--target llama-index` |
| Haystack | Documents | `--target haystack` |
| ChromaDB | Collection | `--target chroma` |
| Weaviate | Objects | `--target weaviate` |
| Qdrant | Points | `--target qdrant` |
| FAISS | Index | `--target faiss` |
| Pinecone | Markdown | `--target pinecone` |
| Markdown | ZIP | `--target markdown` |

**Examples:**

```bash
# Package for Claude (default)
skill-seekers package output/react/

# Package for Gemini
skill-seekers package output/react/ --target gemini

# Package for multiple platforms
for platform in claude gemini openai; do
  skill-seekers package output/react/ --target $platform
done

# Package with upload
skill-seekers package output/react/ --target claude --upload

# Streaming mode for large docs
skill-seekers package output/large-docs/ --streaming
```

---

### pdf

Extract content from PDF and generate skill.

**Purpose:** Convert PDF manuals, documentation, and papers into skills.

**Syntax:**
```bash
skill-seekers create --pdf [options]
```

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| `-c` | `--config` | | PDF config JSON file |
| | `--pdf` | | Direct PDF file path |
| `-n` | `--name` | auto | Skill name |
| `-d` | `--description` | auto | Description |
| `-o` | `--output` | auto | Output directory |
| | `--from-json` | | Build from extracted JSON |
| | `--enhance-level` | 0 | AI enhancement (default: 0 for PDF) |
| | `--api-key` | | Anthropic API key |
| | `--enhance-workflow` | | Apply workflow preset |
| | `--enhance-stage` | | Add inline stage |
| | `--var` | | Override workflow variable |
| | `--workflow-dry-run` | | Preview workflow |
| | `--dry-run` | | Preview without executing |
| `-v` | `--verbose` | | Enable verbose (DEBUG) logging |
| `-q` | `--quiet` | | Minimize output (WARNING only) |

**Examples:**

```bash
# Direct PDF path
skill-seekers create --pdf manual.pdf --name product-manual

# With config file (the config's source carries the PDF path)
skill-seekers create --config configs/manual.json

# Enable enhancement
skill-seekers create --pdf manual.pdf --enhance-level 2

# Dry run to preview
skill-seekers create --pdf manual.pdf --name test --dry-run
```

---

### pptx

Extract content from PowerPoint files and generate skill.

**Purpose:** Convert `.pptx` presentations into AI-ready skills.

**Syntax:**
```bash
skill-seekers create <slides.pptx> [options]
```

**Key Flags:**

| Flag | Description |
|------|-------------|
| `--pptx PATH` | Path to PowerPoint file (.pptx) |
| `-n, --name` | Skill name |
| `--from-json FILE` | Build from extracted JSON |
| `--enhance-level` | AI enhancement (default: 0) |
| `--dry-run` | Preview without executing |

**Examples:**

```bash
# Extract from presentation
skill-seekers create training-slides.pptx --name training-material

# With enhancement
skill-seekers create architecture.pptx --name arch-overview --enhance-level 2
```

---

### quality

Analyze and score skill documentation quality.

**Purpose:** Quality assurance before packaging/uploading.

**Syntax:**
```bash
skill-seekers quality SKILL_DIRECTORY [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `SKILL_DIRECTORY` | Yes | Path to skill directory |

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--report` | Generate detailed report |
| | `--output` | Output path for JSON report |
| | `--threshold` | Quality gate threshold (0-10). When set, exit non-zero if the skill scores below it; without it the command only reports (exit 0) |

**Examples:**

```bash
# Basic quality check (report only, always exits 0)
skill-seekers quality output/react/

# Detailed report
skill-seekers quality output/react/ --report

# Save report as JSON
skill-seekers quality output/react/ --output quality.json

# Quality gate: fail (non-zero exit) if below threshold
skill-seekers quality output/react/ --threshold 7.0
```

---

### resume

Resume interrupted scraping job from checkpoint.

**Purpose:** Continue from where a scrape failed or was interrupted.

**Syntax:**
```bash
skill-seekers resume [JOB_ID] [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `JOB_ID` | No | Job ID to resume |

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--list` | List all resumable jobs |
| | `--clean` | Clean up old progress files |

**Examples:**

```bash
# List resumable jobs
skill-seekers resume --list

# Resume specific job
skill-seekers resume job-abc123

# Clean old checkpoints
skill-seekers resume --clean
```

---

### rss

Extract content from RSS/Atom feeds and generate skill.

**Purpose:** Convert blog feeds and news sources into AI-ready skills.

**Syntax:**
```bash
skill-seekers create <feed.rss> [options]
```

**Key Flags:**

| Flag | Description |
|------|-------------|
| `--feed-url URL` | URL of the RSS/Atom feed |
| `--feed-path PATH` | Path to local RSS/Atom feed file |
| `-n, --name` | Skill name |
| `--dry-run` | Preview without executing |

**Examples:**

```bash
# From URL
skill-seekers create https://blog.example.com/feed.xml --name blog-knowledge

# From local file
skill-seekers create --feed-path ./feed.rss --name feed-summaries
```

---

### scan

AI-detect a project's tech stack and emit one config per detected framework, plus a `<project>-codebase.json` for the project's own code.

**Purpose:** Bootstrap a complete Skill Seekers knowledge base for an existing project in one command. An AI agent inspects ~50 manifest types (package.json, pyproject.toml, Pipfile, environment.yml, Cargo.toml, go.mod, Gemfile, build.gradle, pom.xml, composer.json, mix.exs, flake.nix, deno.json, deps.edn, dune-project, BUILD.bazel, project.godot, …), README, Dockerfile/CI, the first 2 KB of each sampled source file, and the git remote URL — then emits per-framework config files into a chosen output directory. Each emitted config is stamped with `metadata.detected_version` so re-scans report **added**, **version-bumped**, and **removed** dependencies (the last MOVED to `.archived/`, never deleted).

**Usage:**

```bash
skill-seekers scan <directory> [OPTIONS]
```

**Arguments:**
- `directory` (required) - Project root to scan (e.g., `.`, `./my-react-app`)

**Options:**

| Flag | Default | Purpose |
|---|---|---|
| `--out <dir>` | `./configs/scanned/` | Output directory for emitted configs |
| `--no-fetch` | off | Skip the skillseekersweb.com API fallback during resolution (offline mode) |
| `--no-generate` | off | Skip AI generation for unmapped detections |
| `--no-publish-prompt` | off | Suppress the interactive "Submit to community registry?" prompt (CI-friendly) |
| `--agent <name>` | `claude` (or `$SKILL_SEEKER_AGENT`) | LOCAL agent name when no API key is set: `claude`, `codex`, `copilot`, `opencode`, `kimi`, `custom` |
| `--min-confidence <0-1>` | `0.4` | Drop AI detections below this confidence |
| `--max-ai-generations <N>` | `10` | Cap AI config generation for unmapped detections. Once hit, remaining unmapped are listed as `unresolved` in the report but no further AI calls fire. Pass `0` to disable AI generation entirely (same as `--no-generate`). |
| `--dry-run` | off | Preview what scan WOULD emit. No files written, no AI generation. Resolution chain IS exercised (cheap, informs the preview). |
| `--probe-urls` | off | After AI generation, HEAD-probe each `base_url` / GitHub repo URL (5s timeout). On 4xx/5xx: re-ask AI once with feedback. If still bad: stamp config with `metadata._url_unverified`. Adds 5-10s per generated config. |
| `--verbose`, `-v` | off | Show each detection with its evidence + INFO-level logging |

**Resolution chain** for each detection:
1. **Out-dir cache** — `<out_dir>/<slug>.json` from a prior scan is reused (just re-stamps `metadata.detected_version`, preserving any manual edits)
2. **Local repo / user dir** — `./configs/<name>.json` then `~/.config/skill-seekers/configs/<name>.json` (each candidate is tried against the canonical-name list which includes CJK / EU suffix strips, e.g. "Godot 引擎" → `godot`)
3. **Community API** — `https://api.skillseekersweb.com/api/configs/<name>` (unless `--no-fetch`)
4. **AI generation** — last resort (unless `--no-generate` or `--max-ai-generations` cap reached); validated against the unified config schema and registry name regex; optionally URL-probed (`--probe-urls`)

**Examples:**

```bash
# Bootstrap a React project
skill-seekers scan ./my-react-app --out ./configs/scanned/
#   → react.json, vite.json, tailwind.json, my-react-app-codebase.json
#
# Then build any of the emitted configs:
skill-seekers create ./configs/scanned/react.json

# Offline mode — only use local presets, never call AI or the API
skill-seekers scan ./my-project --out ./configs/ --no-fetch --no-generate

# Dry-run on a monorepo — preview cost before committing
skill-seekers scan ./my-monorepo --dry-run --verbose
#   🔍 DRY RUN — no files written, no AI generation invoked.

# Cap AI generation cost on a project with many unmapped deps
skill-seekers scan ./my-project --max-ai-generations 3

# Validate AI URLs (slower but catches hallucinations)
skill-seekers scan ./my-project --probe-urls

# CI-friendly — no interactive submission prompt
skill-seekers scan . --out ./configs/ --no-publish-prompt

# Tightly filter low-confidence detections
skill-seekers scan ./my-project --min-confidence 0.7

# Re-scan reports diff vs prior scan AND archives stale configs
skill-seekers scan ./my-react-app --out ./configs/scanned/
#   Diff vs previous scan:
#     + added       prisma
#     ↻ updated     react   18.2.0 → 18.3.1
#     - removed     moment
#   📦 Archived 1 stale config(s) → 2026-05-25T14-30-00Z/
```

**Output:**
- One JSON config per resolved/generated detection (lowercased slug filename, e.g. `react.json`)
- One `<project>-codebase.json` always emitted (a `type: local` source pointed at the project root)
- `out_dir/.archived/<UTC-timestamp>/` — stale configs from previous scans that no longer match a detection (moved here on each run; user must `rm -rf` to clean up)
- A doctor-style report on stdout showing detections, resolved/generated/unresolved/archived counts, and the diff vs prior scan

**Exit codes:**
- `0` — at least one framework config OR the codebase config was emitted
- `1` — directory invalid or nothing emitted (no detections AND no codebase config — extremely rare)
- `130` — interrupted (Ctrl+C)

**Required environment variables (optional):**
- `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GOOGLE_API_KEY` / `MOONSHOT_API_KEY` — at least one needed for API-mode detection. Without any, falls back to LOCAL agent mode.
- `GITHUB_TOKEN` — required *only* to submit AI-generated configs to the community registry. The scan itself runs without it (it just skips the publish prompt with a one-line hint).

**Publish flow (native async, opt-in):**
- After scan completes, for each freshly AI-generated config, prompts: "Submit '<name>' to the community config registry?"
- **Idempotency:** before submitting, queries the GitHub Search API for an existing open issue with the config name in the title. If found, prints the existing URL and skips — no duplicate submissions.
- **Retry:** transient failures (rate limit, 5xx) retry up to 3 times with 0s / 5s / 15s backoff.
- **Per-attempt timeout:** 30s.
- Opens a GitHub issue at [skill-seekers-configs](https://github.com/yusufkaraaslan/skill-seekers-configs) — no direct git push.

**Notes:**
- AI-generated configs whose `name` doesn't match `^[a-zA-Z0-9_-]+$` are rejected and retried — the registry submission flow requires the regex.
- Reads up to ~64 KB of project signals (manifests, README, Dockerfile/CI, first 2 KB of each sampled source file). Per-kind budgets prevent a 50 KB `package.json` from crowding out README + source samples.
- Source-file sampling means actual code is in the prompt. For a fully-local flow use `skill-seekers create ./path --enhance-level 0`.

---

### scrape

Scrape documentation website and generate skill.

**Purpose:** The main command for converting web documentation into skills.

**Syntax:**
```bash
skill-seekers create [url] [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `url` | No | Base documentation URL |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| `-c` | `--config` | | Config JSON file |
| `-n` | `--name` | | Skill name |
| `-d` | `--description` | | Description |
| | `--enhance-level` | 2 | AI enhancement (0-3) |
| | `--api-key` | | Anthropic API key |
| | `--enhance-workflow` | | Apply workflow preset |
| | `--enhance-stage` | | Add inline stage |
| | `--var` | | Override workflow variable |
| | `--workflow-dry-run` | | Preview workflow |
| `-i` | `--interactive` | | Interactive mode |
| | `--url` | | Base URL (alternative to positional) |
| | `--max-pages` | | Max pages to scrape |
| | `--skip-scrape` | | Use existing data |
| | `--dry-run` | | Preview without scraping |
| | `--resume` | | Resume from checkpoint |
| | `--fresh` | | Clear checkpoint |
| `-r` | `--rate-limit` | 0.5 | Rate limit in seconds |
| `-w` | `--workers` | 1 | Parallel workers (max 10) |
| | `--async` | | Enable async mode |
| | `--no-rate-limit` | | Disable rate limiting |
| | `--interactive-enhancement` | | Interactive enhancement |
| `-v` | `--verbose` | | Verbose output |
| `-q` | `--quiet` | | Quiet output |

**Examples:**

```bash
# With preset config
skill-seekers create --config configs/react.json

# Quick mode
skill-seekers create --name react --url https://react.dev/

# Interactive mode
skill-seekers create --interactive

# Dry run
skill-seekers create --config configs/react.json --dry-run

# Fast async scraping
skill-seekers create --config configs/react.json --async --workers 5

# Skip scrape, rebuild from cache
skill-seekers create --config configs/react.json --skip-scrape

# Resume interrupted scrape
skill-seekers create --config configs/react.json --resume
```

---

### stream

Stream large files chunk-by-chunk.

**Purpose:** Memory-efficient processing for very large documentation sites.

**Syntax:**
```bash
skill-seekers stream INPUT_FILE [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `INPUT_FILE` | Yes | Large file to stream |

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--streaming-chunk-chars` | Maximum characters per chunk (default: 4000) |
| | `--streaming-overlap-chars` | Chunk overlap in characters (default: 200) |
| | `--batch-size` | Batch size for processing (default: 100) |
| | `--checkpoint` | Checkpoint file path |
| | `--output` | Write the collected chunks as JSON (a `.json` file path, or a directory that will receive `chunks.json`) |

**Examples:**

```bash
# Stream a large documentation file
skill-seekers stream big-docs.md

# Custom chunk size and overlap
skill-seekers stream big-docs.md --streaming-chunk-chars 1000 --streaming-overlap-chars 100

# Save the collected chunks
skill-seekers stream big-docs.md --output chunks.json
```

---

### unified

Multi-source scraping combining docs + GitHub + PDF.

**Purpose:** Create a single skill from multiple sources with conflict detection.

**Syntax:**
```bash
skill-seekers create --config FILE [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `--config FILE` | Yes | Unified config JSON file |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--merge-mode` | claude-enhanced | Merge mode: rule-based, claude-enhanced |
| | `--fresh` | | Clear existing data |
| | `--dry-run` | | Dry run mode (previews sources without writing) |
| `-o` | `--output` | output/ | Output directory (honored for unified configs; trailing slashes are safe) |
| | `--enhance-level` | | Override enhancement level (0-3) |
| | `--api-key` | | Anthropic API key (or ANTHROPIC_API_KEY env) |
| | `--enhance-workflow` | | Apply workflow preset (can use multiple) |
| | `--enhance-stage` | | Add inline enhancement stage (name:prompt) |
| | `--var` | | Override workflow variable (key=value) |
| | `--workflow-dry-run` | | Preview workflow without executing |
| | `--skip-codebase-analysis` | | Skip C3.x codebase analysis for GitHub sources |

**Examples:**

```bash
# Unified scraping
skill-seekers create --config configs/react-unified.json

# Fresh start
skill-seekers create --config configs/react-unified.json --fresh

# Rule-based merging
skill-seekers create --config configs/react-unified.json --merge-mode rule-based
```

**Config Format:**
```json
{
  "name": "react-complete",
  "sources": [
    {"type": "docs", "base_url": "https://react.dev/"},
    {"type": "github", "repo": "facebook/react"}
  ]
}
```

---

### update

Update docs without full rescrape.

**Purpose:** Incremental updates for changed documentation.

**Syntax:**
```bash
skill-seekers update SKILL_DIRECTORY [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `SKILL_DIRECTORY` | Yes | Skill directory to update |

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--check-changes` | Check for changes only |
| | `--force` | Force update all files (currently accepted but not yet implemented) |
| | `--generate-package` | Generate update package at specified path |
| | `--apply-update` | Apply update package from specified path |

**Examples:**

```bash
# Check for changes
skill-seekers update output/react/ --check-changes

# Generate an update package
skill-seekers update output/react/ --generate-package update-pkg.json

# Apply an update package
skill-seekers update output/react/ --apply-update update-pkg.json
```

---

### upload

Upload skill package to LLM platform or vector database.

**Purpose:** Deploy packaged skills to target platforms.

**Syntax:**
```bash
skill-seekers upload PACKAGE_FILE [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `PACKAGE_FILE` | Yes | Path to package file (.zip, .tar.gz) |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--target` | claude | Target platform |
| | `--api-key` | | Platform API key |
| | `--chroma-url` | | ChromaDB URL |
| | `--persist-directory` | ./chroma_db | ChromaDB local directory |
| | `--embedding-function` | | Embedding function |
| | `--openai-api-key` | | OpenAI key for embeddings |
| | `--weaviate-url` | | Weaviate URL |
| | `--use-cloud` | | Use Weaviate Cloud |
| | `--cluster-url` | | Weaviate Cloud cluster URL |

**Examples:**

```bash
# Upload to Claude
skill-seekers upload output/react-claude.zip

# Upload to Gemini
skill-seekers upload output/react-gemini.tar.gz --target gemini

# Upload to ChromaDB
skill-seekers upload output/react-chroma.zip --target chroma

# Upload to Weaviate Cloud
skill-seekers upload output/react-weaviate.zip --target weaviate \
  --use-cloud --cluster-url https://xxx.weaviate.network
```

---

### video

Extract skills from video tutorials (YouTube, Vimeo, or local files).

### Usage

```bash
# Setup (first time — auto-detects GPU, installs PyTorch + visual deps)
skill-seekers create --setup

# Extract from YouTube
skill-seekers create --video-url  https://www.youtube.com/watch?v=VIDEO_ID --name my-skill

# With visual frame extraction (requires --setup first)
skill-seekers create --video-url  VIDEO_URL --name my-skill --visual

# Local video file
skill-seekers create --video-url  /path/to/video.mp4 --name my-skill
```

### Key Flags

| Flag | Description |
|------|-------------|
| `--setup` | Auto-detect GPU and install visual extraction dependencies |
| `--url URL` | Video URL (YouTube, Vimeo) or local file path |
| `--name NAME` | Skill name for output |
| `--visual` | Enable visual frame extraction (OCR on keyframes) |
| `--vision-api` | Use Claude Vision API as OCR fallback for low-confidence frames |

### Notes

- `--setup` detects NVIDIA (CUDA), AMD (ROCm), or CPU-only and installs the correct PyTorch variant
- Requires `pip install skill-seekers[video]` (transcripts) or `skill-seekers[video-full]` (+ whisper + scene detection)
- EasyOCR is NOT included in pip extras — it is installed by `--setup` with the correct GPU backend

---

### workflows

Manage enhancement workflow presets.

**Purpose:** List, inspect, copy, add, remove, and validate YAML workflow presets.

**Syntax:**
```bash
skill-seekers workflows ACTION [options]
```

**Actions:**

| Action | Description |
|--------|-------------|
| `list` | List all workflows (bundled + user) |
| `show` | Print YAML content of workflow |
| `copy` | Copy bundled workflow to user dir |
| `add` | Install custom YAML workflow |
| `remove` | Delete user workflow |
| `validate` | Validate workflow file |

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--name` | Custom name for add action |

**Examples:**

```bash
# List all workflows
skill-seekers workflows list

# Show workflow content
skill-seekers workflows show security-focus

# Copy for editing
skill-seekers workflows copy security-focus

# Add custom workflow
skill-seekers workflows add ./my-workflow.yaml

# Add with custom name
skill-seekers workflows add ./workflow.yaml --name my-custom

# Remove user workflow
skill-seekers workflows remove my-workflow

# Validate workflow
skill-seekers workflows validate security-focus
skill-seekers workflows validate ./my-workflow.yaml
```

**Built-in Presets:**
- `default` - Standard enhancement
- `minimal` - Light enhancement
- `security-focus` - Security analysis (4 stages)
- `architecture-comprehensive` - Deep architecture review (7 stages)
- `api-documentation` - API docs focus (3 stages)

---

## Common Workflows

### Workflow 1: Documentation → Skill

```bash
# 1. Estimate pages (optional)
skill-seekers estimate configs/react.json

# 2. Scrape documentation
skill-seekers create --config configs/react.json

# 3. Enhance SKILL.md (optional, recommended)
skill-seekers enhance output/react/

# 4. Package for Claude
skill-seekers package output/react/ --target claude

# 5. Upload
skill-seekers upload output/react-claude.zip
```

### Workflow 2: GitHub → Skill

```bash
# 1. Analyze repository
skill-seekers create  facebook/react

# 2. Package
skill-seekers package output/react/ --target claude

# 3. Upload
skill-seekers upload output/react-claude.zip
```

### Workflow 3: Local Codebase → Skill

```bash
# 1. Analyze codebase
skill-seekers create ./my-project

# 2. Package
skill-seekers package output/codebase/ --target claude

# 3. Install to Cursor
skill-seekers install-agent output/codebase/ --agent cursor
```

### Workflow 4: PDF → Skill

```bash
# 1. Extract PDF
skill-seekers create --pdf manual.pdf --name product-docs

# 2. Package
skill-seekers package output/product-docs/ --target claude
```

### Workflow 5: Multi-Source → Skill

```bash
# 1. Create unified config (configs/my-project.json)
# 2. Run unified scraping
skill-seekers create --config configs/my-project.json

# 3. Package
skill-seekers package output/my-project/ --target claude
```

### Workflow 6: One-Command Complete

```bash
# Everything in one command
skill-seekers install --config react --destination ./output

# Or with create
skill-seekers create https://docs.react.dev/ --preset standard
```

---

## Exit Codes

Standardized in `cli/exit_codes.py`:

| Code | Meaning |
|------|---------|
| `0` | Success (`EXIT_SUCCESS`) |
| `1` | General/runtime error (`EXIT_ERROR`) |
| `2` | Bad arguments / failed validation (`EXIT_VALIDATION`, matches argparse) |
| `130` | Interrupted by user (Ctrl+C, `EXIT_INTERRUPT`) |

---

## Troubleshooting

### Command not found
```bash
# Ensure package is installed
pip install skill-seekers

# Check PATH
which skill-seekers
```

### ImportError
```bash
# Install in editable mode (development)
pip install -e .
```

### Rate limiting
```bash
# Increase rate limit
skill-seekers create --config react.json --rate-limit 1.0
```

### Out of memory
```bash
# Use streaming mode
skill-seekers package output/large/ --streaming
```

---

## See Also

- [Config Format](CONFIG_FORMAT.md) - JSON configuration specification
- [Environment Variables](ENVIRONMENT_VARIABLES.md) - Complete env var reference
- [MCP Reference](MCP_REFERENCE.md) - MCP tools documentation

---

*For additional help: `skill-seekers --help` or `skill-seekers <command> --help`*
