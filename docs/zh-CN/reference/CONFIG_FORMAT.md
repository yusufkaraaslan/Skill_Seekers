# Config Format Reference - Skill Seekers

> **Version:** 3.1.0  
> **Last Updated:** 2026-02-16  
> **Complete JSON configuration specification**

---

## Table of Contents

- [Overview](#overview)
- [Single-Source Config](#single-source-config)
  - [Documentation Source](#documentation-source)
  - [GitHub Source](#github-source)
  - [PDF Source](#pdf-source)
  - [Local Source](#local-source)
- [Unified (Multi-Source) Config](#unified-multi-source-config)
- [Common Fields](#common-fields)
- [Selectors](#selectors)
- [Categories](#categories)
- [URL Patterns](#url-patterns)
- [Examples](#examples)

---

## Overview

Skill Seekers uses JSON configuration files to define scraping targets. There are two types:

| Type | Use Case | File |
|------|----------|------|
| **Single-Source** | One source (docs, GitHub, PDF, or local) | `*.json` |
| **Unified** | Multiple sources combined | `*-unified.json` |

---

## Single-Source Config

### Documentation Source

For scraping documentation websites.

```json
{
  "name": "react",
  "base_url": "https://react.dev/",
  "description": "React - JavaScript library for building UIs",
  
  "start_urls": [
    "https://react.dev/learn",
    "https://react.dev/reference/react"
  ],
  
  "selectors": {
    "main_content": "article",
    "title": "h1",
    "code_blocks": "pre code"
  },
  
  "url_patterns": {
    "include": ["/learn/", "/reference/"],
    "exclude": ["/blog/", "/community/"]
  },
  
  "categories": {
    "getting_started": ["learn", "tutorial", "intro"],
    "api": ["reference", "api", "hooks"]
  },
  
  "rate_limit": 0.5,
  "max_pages": 300,
  "merge_mode": "claude-enhanced"
}
```

#### Documentation Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Skill name (alphanumeric, dashes, underscores) |
| `base_url` | string | Yes | - | Base documentation URL |
| `description` | string | No | "" | Skill description for SKILL.md |
| `start_urls` | array | No | `[base_url]` | URLs to start crawling from |
| `selectors` | object | No | see below | CSS selectors for content extraction |
| `url_patterns` | object | No | `{}` | Include/exclude URL patterns |
| `categories` | object | No | `{}` | Content categorization rules |
| `rate_limit` | number | No | 0.5 | Seconds between requests |
| `max_pages` | number | No | 500 | Maximum pages to scrape |
| `merge_mode` | string | No | "claude-enhanced" | Merge strategy |
| `extract_api` | boolean | No | false | Extract API references |
| `llms_txt_url` | string | No | auto | Path to llms.txt file |

---

### GitHub Source

For analyzing GitHub repositories.

```json
{
  "name": "react-github",
  "type": "github",
  "repo": "facebook/react",
  "description": "React GitHub repository analysis",
  
  "enable_codebase_analysis": true,
  "code_analysis_depth": "deep",
  
  "fetch_issues": true,
  "max_issues": 100,
  "issue_labels": ["bug", "enhancement"],
  
  "fetch_releases": true,
  "max_releases": 20,
  
  "fetch_changelog": true,
  "analyze_commit_history": true,
  
  "file_patterns": ["*.js", "*.ts", "*.tsx"],
  "exclude_patterns": ["*.test.js", "node_modules/**"],
  
  "rate_limit": 1.0
}
```

#### GitHub Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Skill name |
| `type` | string | Yes | - | Must be `"github"` |
| `repo` | string | Yes | - | Repository in `owner/repo` format |
| `description` | string | No | "" | Skill description |
| `enable_codebase_analysis` | boolean | No | true | Analyze source code |
| `code_analysis_depth` | string | No | "standard" | `surface`, `standard`, `deep` |
| `fetch_issues` | boolean | No | true | Fetch GitHub issues |
| `max_issues` | number | No | 100 | Maximum issues to fetch |
| `issue_labels` | array | No | [] | Filter by labels |
| `fetch_releases` | boolean | No | true | Fetch releases |
| `max_releases` | number | No | 20 | Maximum releases |
| `fetch_changelog` | boolean | No | true | Extract CHANGELOG |
| `analyze_commit_history` | boolean | No | false | Analyze commits |
| `file_patterns` | array | No | [] | Include file patterns |
| `exclude_patterns` | array | No | [] | Exclude file patterns |

---

### PDF Source

For extracting content from PDF files.

```json
{
  "name": "product-manual",
  "type": "pdf",
  "pdf_path": "docs/manual.pdf",
  "description": "Product documentation manual",
  
  "enable_ocr": false,
  "password": "",
  
  "extract_images": true,
  "image_output_dir": "output/images/",
  
  "extract_tables": true,
  "table_format": "markdown",
  
  "page_range": [1, 100],
  "split_by_chapters": true,
  
  "chunk_size": 1000,
  "chunk_overlap": 100
}
```

#### PDF Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Skill name |
| `type` | string | Yes | - | Must be `"pdf"` |
| `pdf_path` | string | Yes | - | Path to PDF file |
| `description` | string | No | "" | Skill description |
| `enable_ocr` | boolean | No | false | OCR for scanned PDFs |
| `password` | string | No | "" | PDF password if encrypted |
| `extract_images` | boolean | No | false | Extract embedded images |
| `image_output_dir` | string | No | auto | Directory for images |
| `extract_tables` | boolean | No | false | Extract tables |
| `table_format` | string | No | "markdown" | `markdown`, `json`, `csv` |
| `page_range` | array | No | all | `[start, end]` page range |
| `split_by_chapters` | boolean | No | false | Split by detected chapters |
| `chunk_size` | number | No | 1000 | Characters per chunk |
| `chunk_overlap` | number | No | 100 | Overlap between chunks |

---

### Local Source

For analyzing local codebases.

```json
{
  "name": "my-project",
  "type": "local",
  "directory": "./my-project",
  "description": "Local project analysis",
  
  "languages": ["Python", "JavaScript"],
  "file_patterns": ["*.py", "*.js"],
  "exclude_patterns": ["*.pyc", "node_modules/**", ".git/**"],
  
  "analysis_depth": "comprehensive",
  
  "extract_api": true,
  "extract_patterns": true,
  "extract_test_examples": true,
  "extract_how_to_guides": true,
  "extract_config_patterns": true,
  
  "include_comments": true,
  "include_docstrings": true,
  "include_readme": true
}
```

#### Local Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Skill name |
| `type` | string | Yes | - | Must be `"local"` |
| `directory` | string | Yes | - | Path to directory |
| `description` | string | No | "" | Skill description |
| `languages` | array | No | auto | Languages to analyze |
| `file_patterns` | array | No | all | Include patterns |
| `exclude_patterns` | array | No | common | Exclude patterns |
| `analysis_depth` | string | No | "standard" | `quick`, `standard`, `comprehensive` |
| `extract_api` | boolean | No | true | Extract API documentation |
| `extract_patterns` | boolean | No | true | Detect patterns |
| `extract_test_examples` | boolean | No | true | Extract test examples |
| `extract_how_to_guides` | boolean | No | true | Generate guides |
| `extract_config_patterns` | boolean | No | true | Extract config patterns |
| `include_comments` | boolean | No | true | Include code comments |
| `include_docstrings` | boolean | No | true | Include docstrings |
| `include_readme` | boolean | No | true | Include README |

---

## Unified (Multi-Source) Config

Combine multiple sources into one skill with conflict detection.

```json
{
  "name": "react-complete",
  "description": "React docs + GitHub + examples",
  "merge_mode": "claude-enhanced",
  
  "sources": [
    {
      "type": "docs",
      "name": "react-docs",
      "base_url": "https://react.dev/",
      "max_pages": 200,
      "categories": {
        "getting_started": ["learn"],
        "api": ["reference"]
      }
    },
    {
      "type": "github",
      "name": "react-github",
      "repo": "facebook/react",
      "fetch_issues": true,
      "max_issues": 50
    },
    {
      "type": "pdf",
      "name": "react-cheatsheet",
      "pdf_path": "docs/react-cheatsheet.pdf"
    },
    {
      "type": "local",
      "name": "react-examples",
      "directory": "./react-examples"
    }
  ],
  
  "conflict_detection": {
    "enabled": true,
    "rules": [
      {
        "field": "api_signature",
        "action": "flag_mismatch"
      }
    ]
  },
  
  "output_structure": {
    "group_by_source": false,
    "cross_reference": true
  }
}
```

#### Unified Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Combined skill name |
| `description` | string | No | "" | Skill description |
| `merge_mode` | string | No | "claude-enhanced" | `rule-based`, `claude-enhanced` |
| `sources` | array | Yes | - | List of source configs |
| `conflict_detection` | object | No | `{}` | Conflict detection settings |
| `output_structure` | object | No | `{}` | Output organization |

#### Source Types in Unified Config

Each source in the `sources` array can be:

| Type | Required Fields |
|------|-----------------|
| `docs` | `base_url` |
| `github` | `repo` |
| `pdf` | `pdf_path` |
| `local` | `directory` |

---

## Common Fields

Fields available in all config types:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Skill identifier (letters, numbers, dashes, underscores) |
| `description` | string | Human-readable description |
| `rate_limit` | number | Delay between requests in seconds |
| `output_dir` | string | Custom output directory |
| `skip_scrape` | boolean | Use existing data |
| `enhance_level` | number | 0=off, 1=SKILL.md, 2=+config, 3=full |

---

## Selectors

CSS selectors for content extraction from HTML:

```json
{
  "selectors": {
    "main_content": "article",
    "title": "h1",
    "code_blocks": "pre code",
    "navigation": "nav.sidebar",
    "breadcrumbs": "nav[aria-label='breadcrumb']",
    "next_page": "a[rel='next']",
    "prev_page": "a[rel='prev']"
  }
}
```

### Default Selectors

If not specified, these defaults are used:

| Element | Default Selector |
|---------|-----------------|
| `main_content` | `article, main, .content, #content, [role='main']` |
| `title` | `h1, .page-title, title` |
| `code_blocks` | `pre code, code[class*="language-"]` |
| `navigation` | `nav, .sidebar, .toc` |

---

## Categories

Map URL patterns to content categories:

```json
{
  "categories": {
    "getting_started": [
      "intro", "tutorial", "quickstart", 
      "installation", "getting-started"
    ],
    "core_concepts": [
      "concept", "fundamental", "architecture",
      "principle", "overview"
    ],
    "api_reference": [
      "reference", "api", "method", "function",
      "class", "interface", "type"
    ],
    "guides": [
      "guide", "how-to", "example", "recipe",
      "pattern", "best-practice"
    ],
    "advanced": [
      "advanced", "expert", "performance",
      "optimization", "internals"
    ]
  }
}
```

Categories appear as sections in the generated SKILL.md.

---

## URL Patterns

Control which URLs are included or excluded:

```json
{
  "url_patterns": {
    "include": [
      "/docs/",
      "/guide/",
      "/api/",
      "/reference/"
    ],
    "exclude": [
      "/blog/",
      "/news/",
      "/community/",
      "/search",
      "?print=1",
      "/_static/",
      "/_images/"
    ]
  }
}
```

### Pattern Rules

- Patterns are matched against the URL path
- Use `*` for wildcards: `/api/v*/`
- Use `**` for recursive: `/docs/**/*.html`
- Exclude takes precedence over include

---

## Examples

### React Documentation

```json
{
  "name": "react",
  "base_url": "https://react.dev/",
  "description": "React - JavaScript library for building UIs",
  "start_urls": [
    "https://react.dev/learn",
    "https://react.dev/reference/react",
    "https://react.dev/reference/react-dom"
  ],
  "selectors": {
    "main_content": "article",
    "title": "h1",
    "code_blocks": "pre code"
  },
  "url_patterns": {
    "include": ["/learn/", "/reference/", "/blog/"],
    "exclude": ["/community/", "/search"]
  },
  "categories": {
    "getting_started": ["learn", "tutorial"],
    "api": ["reference", "api"],
    "blog": ["blog"]
  },
  "rate_limit": 0.5,
  "max_pages": 300
}
```

### Django GitHub

```json
{
  "name": "django-github",
  "type": "github",
  "repo": "django/django",
  "description": "Django web framework source code",
  "enable_codebase_analysis": true,
  "code_analysis_depth": "deep",
  "fetch_issues": true,
  "max_issues": 100,
  "fetch_releases": true,
  "file_patterns": ["*.py"],
  "exclude_patterns": ["tests/**", "docs/**"]
}
```

### Unified Multi-Source

```json
{
  "name": "godot-complete",
  "description": "Godot Engine - docs, source, and manual",
  "merge_mode": "claude-enhanced",
  "sources": [
    {
      "type": "docs",
      "name": "godot-docs",
      "base_url": "https://docs.godotengine.org/en/stable/",
      "max_pages": 500
    },
    {
      "type": "github",
      "name": "godot-source",
      "repo": "godotengine/godot",
      "fetch_issues": false
    },
    {
      "type": "pdf",
      "name": "godot-manual",
      "pdf_path": "docs/godot-manual.pdf"
    }
  ]
}
```

### Local Project

```json
{
  "name": "my-api",
  "type": "local",
  "directory": "./my-api-project",
  "description": "My REST API implementation",
  "languages": ["Python"],
  "file_patterns": ["*.py"],
  "exclude_patterns": ["tests/**", "migrations/**"],
  "analysis_depth": "comprehensive",
  "extract_api": true,
  "extract_test_examples": true
}
```

---

## Validation

Validate your config before scraping:

```bash
# Using CLI
skill-seekers scrape --config my-config.json --dry-run

# Using MCP tool
validate_config({"config": "my-config.json"})
```

---

## See Also

- [CLI Reference](CLI_REFERENCE.md) - Command reference
- [Environment Variables](ENVIRONMENT_VARIABLES.md) - Configuration environment

---

*For more examples, see `configs/` directory in the repository*
