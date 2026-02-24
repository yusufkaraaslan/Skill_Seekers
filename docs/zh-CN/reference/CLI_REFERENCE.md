# CLI Reference - Skill Seekers

> **Version:** 3.1.0  
> **Last Updated:** 2026-02-16  
> **Complete reference for all 20 CLI commands**

---

## Table of Contents

- [Overview](#overview)
  - [Installation](#installation)
  - [Global Flags](#global-flags)
  - [Environment Variables](#environment-variables)
- [Command Reference](#command-reference)
  - [analyze](#analyze) - Analyze local codebase
  - [config](#config) - Configuration wizard
  - [create](#create) - Create skill (auto-detects source)
  - [enhance](#enhance) - AI enhancement (local mode)
  - [enhance-status](#enhance-status) - Monitor enhancement
  - [estimate](#estimate) - Estimate page counts
  - [github](#github) - Scrape GitHub repository
  - [install](#install) - One-command complete workflow
  - [install-agent](#install-agent) - Install to AI agent
  - [multilang](#multilang) - Multi-language docs
  - [package](#package) - Package skill for platform
  - [pdf](#pdf) - Extract from PDF
  - [quality](#quality) - Quality scoring
  - [resume](#resume) - Resume interrupted jobs
  - [scrape](#scrape) - Scrape documentation
  - [stream](#stream) - Stream large files
  - [unified](#unified) - Multi-source scraping
  - [update](#update) - Incremental updates
  - [upload](#upload) - Upload to platform
  - [workflows](#workflows) - Manage workflow presets
- [Common Workflows](#common-workflows)
- [Exit Codes](#exit-codes)
- [Troubleshooting](#troubleshooting)

---

## Overview

Skill Seekers provides a unified CLI for converting documentation, GitHub repositories, PDFs, and local codebases into AI-ready skills.

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

These flags work with most commands:

| Flag | Description |
|------|-------------|
| `-h, --help` | Show help message and exit |
| `--version` | Show version number and exit |
| `-v, --verbose` | Enable verbose (DEBUG) output |
| `-q, --quiet` | Minimize output (WARNING only) |
| `--dry-run` | Preview without executing |

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
skill-seekers analyze --directory DIR [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `--directory DIR` | Yes | Directory to analyze |
| `--output DIR` | No | Output directory (default: output/codebase/) |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--preset` | standard | Analysis preset: quick, standard, comprehensive |
| | `--preset-list` | | Show available presets and exit |
| | `--languages` | auto | Comma-separated languages (Python,JavaScript,C++) |
| | `--file-patterns` | | Comma-separated file patterns |
| | `--enhance-level` | 2 | AI enhancement: 0=off, 1=SKILL.md, 2=+config, 3=full |
| | `--skip-api-reference` | | Skip API docs generation |
| | `--skip-dependency-graph` | | Skip dependency graph |
| | `--skip-patterns` | | Skip pattern detection |
| | `--skip-test-examples` | | Skip test example extraction |
| | `--skip-how-to-guides` | | Skip how-to guide generation |
| | `--skip-config-patterns` | | Skip config pattern extraction |
| | `--skip-docs` | | Skip project docs (README) |
| | `--no-comments` | | Skip comment extraction |
| `-v` | `--verbose` | | Enable verbose logging |

**Examples:**

```bash
# Basic analysis with defaults
skill-seekers analyze --directory ./my-project

# Quick analysis (1-2 min)
skill-seekers analyze --directory ./my-project --preset quick

# Comprehensive analysis with all features
skill-seekers analyze --directory ./my-project --preset comprehensive

# Specific languages only
skill-seekers analyze --directory ./my-project --languages Python,JavaScript

# Skip heavy features for faster analysis
skill-seekers analyze --directory ./my-project --skip-dependency-graph --skip-patterns
```

**Exit Codes:**
- `0` - Success
- `1` - Analysis failed

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
| | `--max-discovery` | 1000 | Max pages to discover |

**Examples:**

```bash
# Estimate with config file
skill-seekers estimate configs/react.json

# Quick estimate (100 pages)
skill-seekers estimate configs/react.json --max-discovery 100

# List all available presets
skill-seekers estimate --all
```

---

### github

Scrape GitHub repository and generate skill.

**Purpose:** Extract code, issues, releases, and metadata from GitHub repos.

**Syntax:**
```bash
skill-seekers github [options]
```

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--repo` | | Repository (owner/repo format) |
| `-c` | `--config` | | Config JSON file |
| | `--token` | | GitHub personal access token |
| `-n` | `--name` | auto | Skill name |
| `-d` | `--description` | auto | Description |
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

**Examples:**

```bash
# Basic repo analysis
skill-seekers github --repo facebook/react

# With GitHub token (higher rate limits)
skill-seekers github --repo facebook/react --token $GITHUB_TOKEN

# Skip issues for faster scraping
skill-seekers github --repo facebook/react --no-issues

# Scrape only, build later
skill-seekers github --repo facebook/react --scrape-only
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
| `--agent AGENT` | Yes | Target agent: cursor, windsurf, cline, continue |

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

### multilang

Multi-language documentation support.

**Purpose:** Scrape and merge documentation in multiple languages.

**Syntax:**
```bash
skill-seekers multilang --config CONFIG [options]
```

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| `-c` | `--config` | Config JSON file |
| | `--primary` | Primary language |
| | `--languages` | Comma-separated languages |
| | `--merge-strategy` | How to merge: parallel, hierarchical |

**Examples:**

```bash
# Multi-language scrape
skill-seekers multilang --config configs/react-i18n.json

# Specific languages
skill-seekers multilang --config configs/docs.json --languages en,zh,es
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
| | `--no-preserve-code` | | Allow code block splitting |

**Supported Platforms:**

| Platform | Format | Flag |
|----------|--------|------|
| Claude AI | ZIP + YAML | `--target claude` |
| Google Gemini | tar.gz | `--target gemini` |
| OpenAI | ZIP + Vector | `--target openai` |
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
skill-seekers pdf [options]
```

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| `-c` | `--config` | PDF config JSON file |
| | `--pdf` | Direct PDF file path |
| `-n` | `--name` | Skill name |
| `-d` | `--description` | Description |
| | `--from-json` | Build from extracted JSON |
| | `--enhance-workflow` | Apply workflow preset |
| | `--enhance-stage` | Add inline stage |
| | `--var` | Override workflow variable |
| | `--workflow-dry-run` | Preview workflow |
| | `--enhance-level` | 0 | AI enhancement (default: 0 for PDF) |

**Examples:**

```bash
# Direct PDF path
skill-seekers pdf --pdf manual.pdf --name product-manual

# With config file
skill-seekers pdf --config configs/manual.json

# Enable enhancement
skill-seekers pdf --pdf manual.pdf --enhance-level 2
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
| | `--threshold` | Quality threshold (0-10) |

**Examples:**

```bash
# Basic quality check
skill-seekers quality output/react/

# Detailed report
skill-seekers quality output/react/ --report

# Fail if below threshold
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

### scrape

Scrape documentation website and generate skill.

**Purpose:** The main command for converting web documentation into skills.

**Syntax:**
```bash
skill-seekers scrape [url] [options]
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
skill-seekers scrape --config configs/react.json

# Quick mode
skill-seekers scrape --name react --url https://react.dev/

# Interactive mode
skill-seekers scrape --interactive

# Dry run
skill-seekers scrape --config configs/react.json --dry-run

# Fast async scraping
skill-seekers scrape --config configs/react.json --async --workers 5

# Skip scrape, rebuild from cache
skill-seekers scrape --config configs/react.json --skip-scrape

# Resume interrupted scrape
skill-seekers scrape --config configs/react.json --resume
```

---

### stream

Stream large files chunk-by-chunk.

**Purpose:** Memory-efficient processing for very large documentation sites.

**Syntax:**
```bash
skill-seekers stream --config CONFIG [options]
```

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| `-c` | `--config` | Config JSON file |
| | `--streaming-chunk-chars` | Maximum characters per chunk (default: 4000) |
| | `--output` | Output directory |

**Examples:**

```bash
# Stream large documentation
skill-seekers stream --config configs/large-docs.json

# Custom chunk size
skill-seekers stream --config configs/large-docs.json --streaming-chunk-chars 1000
```

---

### unified

Multi-source scraping combining docs + GitHub + PDF.

**Purpose:** Create a single skill from multiple sources with conflict detection.

**Syntax:**
```bash
skill-seekers unified --config FILE [options]
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
| | `--dry-run` | | Dry run mode |

**Examples:**

```bash
# Unified scraping
skill-seekers unified --config configs/react-unified.json

# Fresh start
skill-seekers unified --config configs/react-unified.json --fresh

# Rule-based merging
skill-seekers unified --config configs/react-unified.json --merge-mode rule-based
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
skill-seekers update --config CONFIG [options]
```

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| `-c` | `--config` | Config JSON file |
| | `--since` | Update since date |
| | `--check-only` | Check for updates only |

**Examples:**

```bash
# Check for updates
skill-seekers update --config configs/react.json --check-only

# Update since specific date
skill-seekers update --config configs/react.json --since 2026-01-01

# Full update
skill-seekers update --config configs/react.json
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
skill-seekers scrape --config configs/react.json

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
skill-seekers github --repo facebook/react

# 2. Package
skill-seekers package output/react/ --target claude

# 3. Upload
skill-seekers upload output/react-claude.zip
```

### Workflow 3: Local Codebase → Skill

```bash
# 1. Analyze codebase
skill-seekers analyze --directory ./my-project

# 2. Package
skill-seekers package output/codebase/ --target claude

# 3. Install to Cursor
skill-seekers install-agent output/codebase/ --agent cursor
```

### Workflow 4: PDF → Skill

```bash
# 1. Extract PDF
skill-seekers pdf --pdf manual.pdf --name product-docs

# 2. Package
skill-seekers package output/product-docs/ --target claude
```

### Workflow 5: Multi-Source → Skill

```bash
# 1. Create unified config (configs/my-project.json)
# 2. Run unified scraping
skill-seekers unified --config configs/my-project.json

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

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Warning (e.g., estimation hit limit) |
| `130` | Interrupted by user (Ctrl+C) |

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
skill-seekers scrape --config react.json --rate-limit 1.0
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
