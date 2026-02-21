# MCP Reference - Skill Seekers

> **Version:** 3.1.0  
> **Last Updated:** 2026-02-16  
> **Complete reference for 26 MCP tools**

---

## Table of Contents

- [Overview](#overview)
  - [What is MCP?](#what-is-mcp)
  - [Transport Modes](#transport-modes)
  - [Starting the Server](#starting-the-server)
- [Tool Categories](#tool-categories)
  - [Core Tools (9)](#core-tools)
  - [Extended Tools (9)](#extended-tools)
  - [Config Source Tools (5)](#config-source-tools)
  - [Config Splitting Tools (2)](#config-splitting-tools)
  - [Vector Database Tools (4)](#vector-database-tools)
  - [Workflow Tools (5)](#workflow-tools)
- [Tool Reference](#tool-reference)
- [Common Patterns](#common-patterns)
- [Error Handling](#error-handling)

---

## Overview

### What is MCP?

MCP (Model Context Protocol) allows AI agents like Claude Code to interact with Skill Seekers through a standardized interface. Instead of running CLI commands, you can use natural language:

```
"Scrape the React documentation and create a skill"
"Package the output/react skill for Claude"
"List available workflow presets"
```

### Transport Modes

The MCP server supports two transport modes:

| Mode | Use Case | Command |
|------|----------|---------|
| **stdio** | Claude Code, VS Code + Cline | `skill-seekers-mcp` |
| **HTTP** | Cursor, Windsurf, HTTP clients | `skill-seekers-mcp --transport http --port 8765` |

### Starting the Server

```bash
# stdio mode (default)
skill-seekers-mcp

# HTTP mode
skill-seekers-mcp --transport http --port 8765

# With custom host
skill-seekers-mcp --transport http --host 0.0.0.0 --port 8765
```

---

## Tool Categories

### Core Tools (9)

Essential tools for basic skill creation workflow:

| Tool | Purpose |
|------|---------|
| `list_configs` | List preset configurations |
| `generate_config` | Generate config from docs URL |
| `validate_config` | Validate config structure |
| `estimate_pages` | Estimate page count |
| `scrape_docs` | Scrape documentation |
| `package_skill` | Package to .zip |
| `upload_skill` | Upload to platform |
| `enhance_skill` | AI enhancement |
| `install_skill` | Complete workflow |

### Extended Tools (9)

Advanced scraping and analysis tools:

| Tool | Purpose |
|------|---------|
| `scrape_github` | GitHub repository analysis |
| `scrape_pdf` | PDF extraction |
| `scrape_codebase` | Local codebase analysis |
| `unified_scrape` | Multi-source scraping |
| `detect_patterns` | Pattern detection |
| `extract_test_examples` | Extract usage examples from tests |
| `build_how_to_guides` | Generate how-to guides |
| `extract_config_patterns` | Extract configuration patterns |
| `detect_conflicts` | Find doc/code discrepancies |

### Config Source Tools (5)

Manage configuration sources:

| Tool | Purpose |
|------|---------|
| `add_config_source` | Register git repo as config source |
| `list_config_sources` | List registered sources |
| `remove_config_source` | Remove config source |
| `fetch_config` | Fetch configs from git |
| `submit_config` | Submit config to source |

### Config Splitting Tools (2)

Handle large documentation:

| Tool | Purpose |
|------|---------|
| `split_config` | Split large config |
| `generate_router` | Generate router skill |

### Vector Database Tools (4)

Export to vector databases:

| Tool | Purpose |
|------|---------|
| `export_to_weaviate` | Export to Weaviate |
| `export_to_chroma` | Export to ChromaDB |
| `export_to_faiss` | Export to FAISS |
| `export_to_qdrant` | Export to Qdrant |

### Workflow Tools (5)

Manage enhancement workflows:

| Tool | Purpose |
|------|---------|
| `list_workflows` | List all workflows |
| `get_workflow` | Get workflow YAML |
| `create_workflow` | Create new workflow |
| `update_workflow` | Update workflow |
| `delete_workflow` | Delete workflow |

---

## Tool Reference

---

### Core Tools

#### list_configs

List all available preset configurations.

**Parameters:** None

**Returns:** Array of config objects

```json
{
  "configs": [
    {
      "name": "react",
      "description": "React documentation",
      "source": "bundled"
    }
  ]
}
```

**Example:**
```python
# Natural language
"List available configurations"
"What configs are available?"
"Show me the preset configs"
```

---

#### generate_config

Generate a configuration file from a documentation URL.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `url` | string | Yes | Documentation URL |
| `name` | string | No | Config name (auto-detected) |
| `description` | string | No | Description (auto-detected) |

**Returns:** Config JSON object

**Example:**
```python
# Natural language
"Generate a config for https://docs.django.com/"
"Create a Django config"
"Make a config from the React docs URL"
```

---

#### validate_config

Validate a configuration file structure.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `config` | object/string | Yes | Config object or file path |

**Returns:** Validation result

```json
{
  "valid": true,
  "errors": [],
  "warnings": []
}
```

**Example:**
```python
# Natural language
"Validate this config: {config_json}"
"Check if my config is valid"
"Validate configs/react.json"
```

---

#### estimate_pages

Estimate total pages for documentation scraping.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `config` | object/string | Yes | Config object or file path |
| `max_discovery` | number | No | Max pages to discover (default: 1000) |

**Returns:** Estimation results

```json
{
  "estimated_pages": 230,
  "discovery_rate": 1.28,
  "estimated_time_minutes": 3.8
}
```

**Example:**
```python
# Natural language
"Estimate pages for the React config"
"How many pages will Django docs have?"
"Estimate with max 500 pages"
```

---

#### scrape_docs

Scrape documentation website and generate skill.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `config` | object/string | Yes | Config object or file path |
| `enhance_level` | number | No | 0-3 (default: 2) |
| `max_pages` | number | No | Override max pages |
| `dry_run` | boolean | No | Preview only |

**Returns:** Scraping results

```json
{
  "skill_directory": "output/react/",
  "pages_scraped": 180,
  "references_generated": 12,
  "status": "success"
}
```

**Example:**
```python
# Natural language
"Scrape the React documentation"
"Scrape Django with enhancement level 3"
"Do a dry run of the Vue docs scrape"
```

---

#### package_skill

Package skill directory into uploadable format.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `skill_directory` | string | Yes | Path to skill directory |
| `target` | string | No | Platform (default: claude) |
| `streaming` | boolean | No | Use streaming mode |

**Returns:** Package info

```json
{
  "package_path": "output/react-claude.zip",
  "platform": "claude",
  "size_bytes": 245760
}
```

**Example:**
```python
# Natural language
"Package the React skill for Claude"
"Create a Gemini package for output/django/"
"Package with streaming mode"
```

---

#### upload_skill

Upload skill package to LLM platform.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `package_path` | string | Yes | Path to package file |
| `target` | string | No | Platform (default: claude) |
| `api_key` | string | No | Platform API key |

**Returns:** Upload result

```json
{
  "success": true,
  "platform": "claude",
  "skill_id": "skill_abc123"
}
```

**Example:**
```python
# Natural language
"Upload the React package to Claude"
"Upload output/django-gemini.tar.gz to Gemini"
```

---

#### enhance_skill

AI-powered enhancement of SKILL.md.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `skill_directory` | string | Yes | Path to skill directory |
| `mode` | string | No | API or LOCAL (default: auto) |
| `workflow` | string | No | Workflow preset name |

**Returns:** Enhancement result

```json
{
  "success": true,
  "mode": "LOCAL",
  "skill_md_lines": 450
}
```

**Example:**
```python
# Natural language
"Enhance the React skill"
"Enhance with security-focus workflow"
"Run enhancement in API mode"
```

---

#### install_skill

Complete workflow: scrape → enhance → package → upload.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `config` | object/string | Yes | Config object or file path |
| `target` | string | No | Platform (default: claude) |
| `enhance` | boolean | No | Enable enhancement (default: true) |
| `upload` | boolean | No | Auto-upload (default: true) |

**Returns:** Installation result

```json
{
  "success": true,
  "skill_directory": "output/react/",
  "package_path": "output/react-claude.zip",
  "uploaded": true
}
```

**Example:**
```python
# Natural language
"Install the React skill"
"Install Django for Gemini with no upload"
"Complete install of the Vue config"
```

---

### Extended Tools

#### scrape_github

Scrape GitHub repository.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `repo` | string | Yes | Owner/repo format |
| `token` | string | No | GitHub token |
| `name` | string | No | Skill name |
| `include_issues` | boolean | No | Include issues (default: true) |
| `include_releases` | boolean | No | Include releases (default: true) |

**Example:**
```python
# Natural language
"Scrape the facebook/react repository"
"Analyze the Django GitHub repo"
"Scrape vercel/next.js with issues"
```

---

#### scrape_pdf

Extract content from PDF file.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `pdf_path` | string | Yes | Path to PDF file |
| `name` | string | No | Skill name |
| `enable_ocr` | boolean | No | Enable OCR for scanned PDFs |

**Example:**
```python
# Natural language
"Scrape the manual.pdf file"
"Extract content from API-docs.pdf"
"Process scanned.pdf with OCR"
```

---

#### scrape_codebase

Analyze local codebase.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | Yes | Path to directory |
| `preset` | string | No | quick/standard/comprehensive |
| `languages` | array | No | Language filters |

**Example:**
```python
# Natural language
"Analyze the ./my-project directory"
"Scrape this codebase with comprehensive preset"
"Analyze only Python and JavaScript files"
```

---

#### unified_scrape

Multi-source scraping (docs + GitHub + PDF).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `config` | object/string | Yes | Unified config |
| `merge_mode` | string | No | rule-based or claude-enhanced |

**Example:**
```python
# Natural language
"Run unified scraping with my-config.json"
"Combine docs and GitHub for React"
"Multi-source scrape with claude-enhanced merge"
```

---

#### detect_patterns

Detect code patterns in repository.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | Yes | Path to directory |
| `pattern_types` | array | No | Types to detect |

**Returns:** Detected patterns

**Example:**
```python
# Natural language
"Detect patterns in this codebase"
"Find architectural patterns"
"Show me the code patterns"
```

---

#### extract_test_examples

Extract usage examples from test files.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | Yes | Path to test directory |
| `language` | string | No | Primary language |

**Returns:** Test examples

**Example:**
```python
# Natural language
"Extract test examples from tests/"
"Get Python test examples"
"Find usage examples in the test suite"
```

---

#### build_how_to_guides

Generate how-to guides from codebase.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | Yes | Path to directory |
| `topics` | array | No | Specific topics |

**Returns:** Generated guides

**Example:**
```python
# Natural language
"Build how-to guides for this project"
"Generate guides about authentication"
"Create how-to documentation"
```

---

#### extract_config_patterns

Extract configuration patterns.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | Yes | Path to directory |

**Returns:** Config patterns

**Example:**
```python
# Natural language
"Extract config patterns from this project"
"Find configuration examples"
"Show me how this project is configured"
```

---

#### detect_conflicts

Find discrepancies between documentation and code.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `docs_source` | string | Yes | Docs config or directory |
| `code_source` | string | Yes | Code directory or repo |

**Returns:** Conflict report

```json
{
  "conflicts": [
    {
      "type": "api_mismatch",
      "doc_signature": "foo(a, b)",
      "code_signature": "foo(a, b, c=default)"
    }
  ]
}
```

**Example:**
```python
# Natural language
"Detect conflicts between docs and code"
"Find discrepancies in React"
"Compare documentation to implementation"
```

---

### Config Source Tools

#### add_config_source

Register a git repository as a config source.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Source name |
| `url` | string | Yes | Git repository URL |
| `branch` | string | No | Git branch (default: main) |

**Example:**
```python
# Natural language
"Add my-configs repo as a source"
"Register https://github.com/org/configs as configs"
```

---

#### list_config_sources

List all registered config sources.

**Parameters:** None

**Returns:** List of sources

**Example:**
```python
# Natural language
"List my config sources"
"Show registered sources"
```

---

#### remove_config_source

Remove a config source.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Source name |

**Example:**
```python
# Natural language
"Remove the configs source"
"Delete my old config source"
```

---

#### fetch_config

Fetch configs from a git source.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `source` | string | Yes | Source name |
| `config_name` | string | No | Specific config to fetch |

**Example:**
```python
# Natural language
"Fetch configs from my source"
"Get the react config from configs source"
```

---

#### submit_config

Submit a config to a source.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `source` | string | Yes | Source name |
| `config_path` | string | Yes | Path to config file |

**Example:**
```python
# Natural language
"Submit my-config.json to configs source"
"Add this config to my source"
```

---

### Config Splitting Tools

#### split_config

Split large configuration into smaller chunks.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `config` | string | Yes | Config file path |
| `max_pages_per_chunk` | number | No | Pages per chunk (default: 100) |
| `output_dir` | string | No | Output directory |

**Example:**
```python
# Natural language
"Split the large config into chunks"
"Break up this 500-page config"
"Split with 50 pages per chunk"
```

---

#### generate_router

Generate a router skill for large documentation.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `config` | string | Yes | Config file path |
| `output_dir` | string | No | Output directory |

**Example:**
```python
# Natural language
"Generate a router for this large config"
"Create a router skill for Django docs"
```

---

### Vector Database Tools

#### export_to_weaviate

Export skill to Weaviate vector database.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `skill_directory` | string | Yes | Path to skill |
| `weaviate_url` | string | No | Weaviate URL |
| `class_name` | string | No | Class/collection name |

**Example:**
```python
# Natural language
"Export React skill to Weaviate"
"Send to Weaviate at localhost:8080"
```

---

#### export_to_chroma

Export skill to ChromaDB.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `skill_directory` | string | Yes | Path to skill |
| `collection_name` | string | No | Collection name |
| `persist_directory` | string | No | Storage directory |

**Example:**
```python
# Natural language
"Export to ChromaDB"
"Send Django skill to Chroma"
```

---

#### export_to_faiss

Export skill to FAISS index.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `skill_directory` | string | Yes | Path to skill |
| `output_path` | string | No | Index file path |

**Example:**
```python
# Natural language
"Export to FAISS index"
"Create FAISS index for this skill"
```

---

#### export_to_qdrant

Export skill to Qdrant.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `skill_directory` | string | Yes | Path to skill |
| `collection_name` | string | No | Collection name |
| `qdrant_url` | string | No | Qdrant URL |

**Example:**
```python
# Natural language
"Export to Qdrant"
"Send skill to Qdrant vector DB"
```

---

### Workflow Tools

#### list_workflows

List all available workflow presets.

**Parameters:** None

**Returns:**
```json
{
  "workflows": [
    {"name": "security-focus", "source": "bundled"},
    {"name": "my-custom", "source": "user"}
  ]
}
```

**Example:**
```python
# Natural language
"List available workflows"
"What workflow presets do I have?"
```

---

#### get_workflow

Get full YAML content of a workflow.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Workflow name |

**Returns:** Workflow YAML

**Example:**
```python
# Natural language
"Show me the security-focus workflow"
"Get the YAML for the default workflow"
```

---

#### create_workflow

Create a new workflow.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Workflow name |
| `yaml_content` | string | Yes | Workflow YAML |

**Example:**
```python
# Natural language
"Create a workflow called my-workflow"
"Save this YAML as a new workflow"
```

---

#### update_workflow

Update an existing workflow.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Workflow name |
| `yaml_content` | string | Yes | New YAML content |

**Example:**
```python
# Natural language
"Update my-custom workflow"
"Modify the security-focus workflow"
```

---

#### delete_workflow

Delete a user workflow.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Workflow name |

**Example:**
```python
# Natural language
"Delete my-old-workflow"
"Remove the test workflow"
```

---

## Common Patterns

### Pattern 1: Quick Documentation Skill

```python
# Natural language sequence:
"List available configs"
"Scrape the react config"
"Package output/react for Claude"
```

Tools: `list_configs` → `scrape_docs` → `package_skill`

---

### Pattern 2: GitHub Repository Analysis

```python
# Natural language sequence:
"Scrape the facebook/react GitHub repo"
"Enhance the output/react skill"
"Package it for Gemini"
```

Tools: `scrape_github` → `enhance_skill` → `package_skill`

---

### Pattern 3: Complete One-Command

```python
# Natural language:
"Install the Django skill for Claude"
```

Tool: `install_skill`

---

### Pattern 4: Multi-Source with Workflows

```python
# Natural language sequence:
"List available workflows"
"Run unified scrape with my-unified.json"
"Apply security-focus and api-documentation workflows"
"Package for Claude"
```

Tools: `list_workflows` → `unified_scrape` → `enhance_skill` → `package_skill`

---

### Pattern 5: Vector Database Export

```python
# Natural language sequence:
"Scrape the Django documentation"
"Export to ChromaDB"
```

Tools: `scrape_docs` → `export_to_chroma`

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ConfigNotFoundError` | Config doesn't exist | Check config name or path |
| `InvalidConfigError` | Config malformed | Use `validate_config` |
| `ScrapingError` | Network or selector issue | Check URL and selectors |
| `RateLimitError` | Too many requests | Wait or use token |
| `EnhancementError` | AI enhancement failed | Check API key or Claude Code |

### Error Response Format

```json
{
  "error": true,
  "error_type": "ConfigNotFoundError",
  "message": "Config 'react' not found",
  "suggestion": "Run list_configs to see available configs"
}
```

---

## See Also

- [CLI Reference](CLI_REFERENCE.md) - Command-line interface
- [Config Format](CONFIG_FORMAT.md) - JSON configuration
- [MCP Setup Guide](../advanced/mcp-server.md) - Server configuration

---

*For tool help: Ask the AI agent about specific tools*
