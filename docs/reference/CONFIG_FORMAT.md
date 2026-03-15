# Config Format Reference - Skill Seekers

> **Version:** 3.2.0
> **Last Updated:** 2026-03-15
> **Complete JSON configuration specification for 17 source types**

---

## Table of Contents

- [Overview](#overview)
- [Single-Source Config](#single-source-config)
  - [Documentation Source](#documentation-source)
  - [GitHub Source](#github-source)
  - [PDF Source](#pdf-source)
  - [Local Source](#local-source)
  - [Additional Source Types](#additional-source-types)
- [Unified (Multi-Source) Config](#unified-multi-source-config)
- [Common Fields](#common-fields)
- [Selectors](#selectors)
- [Categories](#categories)
- [URL Patterns](#url-patterns)
- [Examples](#examples)

---

## Overview

Skill Seekers uses JSON configuration files with a unified format. All configs use a `sources` array, even for single-source scraping.

> **Important:** Legacy configs without `sources` were removed in v2.11.0. All configs must use the unified format shown below.

| Use Case | Example |
|----------|---------|
| **Single source** | `"sources": [{ "type": "documentation", ... }]` |
| **Multiple sources** | `"sources": [{ "type": "documentation", ... }, { "type": "github", ... }]` |

---

## Single-Source Config

Even for a single source, wrap it in a `sources` array.

### Documentation Source

For scraping documentation websites.

```json
{
  "name": "react",
  "description": "React - JavaScript library for building UIs",
  "sources": [
    {
      "type": "documentation",
      "base_url": "https://react.dev/",

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
      "max_pages": 300
    }
  ]
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
  "description": "React GitHub repository analysis",
  "sources": [
    {
      "type": "github",
      "repo": "facebook/react",

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
  ]
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
  "description": "Product documentation manual",
  "sources": [
    {
      "type": "pdf",
      "pdf_path": "docs/manual.pdf",

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
  ]
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
  "description": "Local project analysis",
  "sources": [
    {
      "type": "local",
      "directory": "./my-project",

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
  ]
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

### Additional Source Types

The following 10 source types were added in v3.2.0. Each can be used as a standalone config or within a unified `sources` array.

#### Jupyter Notebook Source

```json
{
  "name": "ml-tutorial",
  "sources": [{
    "type": "jupyter",
    "notebook_path": "notebooks/tutorial.ipynb"
  }]
}
```

#### Local HTML Source

```json
{
  "name": "offline-docs",
  "sources": [{
    "type": "html",
    "html_path": "./exported-docs/"
  }]
}
```

#### OpenAPI/Swagger Source

```json
{
  "name": "petstore-api",
  "sources": [{
    "type": "openapi",
    "spec_path": "api/openapi.yaml",
    "spec_url": "https://petstore.swagger.io/v2/swagger.json"
  }]
}
```

#### AsciiDoc Source

```json
{
  "name": "project-guide",
  "sources": [{
    "type": "asciidoc",
    "asciidoc_path": "./docs/guide.adoc"
  }]
}
```

#### PowerPoint Source

```json
{
  "name": "training-slides",
  "sources": [{
    "type": "pptx",
    "pptx_path": "presentations/training.pptx"
  }]
}
```

#### RSS/Atom Feed Source

```json
{
  "name": "engineering-blog",
  "sources": [{
    "type": "rss",
    "feed_url": "https://engineering.example.com/feed.xml",
    "follow_links": true,
    "max_articles": 50
  }]
}
```

#### Man Page Source

```json
{
  "name": "unix-tools",
  "sources": [{
    "type": "manpage",
    "man_names": "ls,grep,find,awk,sed",
    "sections": "1,3"
  }]
}
```

#### Confluence Source

```json
{
  "name": "team-wiki",
  "sources": [{
    "type": "confluence",
    "base_url": "https://wiki.example.com",
    "space_key": "DEV",
    "username": "user@example.com",
    "max_pages": 500
  }]
}
```

#### Notion Source

```json
{
  "name": "product-docs",
  "sources": [{
    "type": "notion",
    "database_id": "abc123def456",
    "max_pages": 500
  }]
}
```

#### Chat (Slack/Discord) Source

```json
{
  "name": "team-knowledge",
  "sources": [{
    "type": "chat",
    "export_path": "./slack-export/",
    "platform": "slack",
    "channel": "engineering",
    "max_messages": 10000
  }]
}
```

#### Additional Source Fields Reference

| Source Type | Required Fields | Optional Fields |
|-------------|-----------------|-----------------|
| `jupyter` | `notebook_path` | — |
| `html` | `html_path` | — |
| `openapi` | `spec_path` or `spec_url` | — |
| `asciidoc` | `asciidoc_path` | — |
| `pptx` | `pptx_path` | — |
| `rss` | `feed_url` or `feed_path` | `follow_links`, `max_articles` |
| `manpage` | `man_names` or `man_path` | `sections` |
| `confluence` | `base_url` + `space_key` or `export_path` | `username`, `token`, `max_pages` |
| `notion` | `database_id` or `page_id` or `export_path` | `token`, `max_pages` |
| `chat` | `export_path` | `platform`, `token`, `channel`, `max_messages` |

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
| `workflows` | array | No | `[]` | Workflow presets to apply |
| `workflow_stages` | array | No | `[]` | Inline enhancement stages |
| `workflow_vars` | object | No | `{}` | Workflow variable overrides |
| `workflow_dry_run` | boolean | No | `false` | Preview workflows without executing |

#### Workflow Configuration (Unified)

Unified configs support defining enhancement workflows at the top level:

```json
{
  "name": "react-complete",
  "description": "React docs + GitHub with security enhancement",
  "merge_mode": "claude-enhanced",
  
  "workflows": ["security-focus", "api-documentation"],
  "workflow_stages": [
    {
      "name": "cleanup",
      "prompt": "Remove boilerplate sections and standardize formatting"
    }
  ],
  "workflow_vars": {
    "focus_area": "performance",
    "detail_level": "comprehensive"
  },
  
  "sources": [
    {"type": "docs", "base_url": "https://react.dev/"},
    {"type": "github", "repo": "facebook/react"}
  ]
}
```

**Workflow Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `workflows` | array | List of workflow preset names to apply |
| `workflow_stages` | array | Inline stages with `name` and `prompt` |
| `workflow_vars` | object | Key-value pairs for workflow variables |
| `workflow_dry_run` | boolean | Preview workflows without executing |

**Note:** CLI flags override config values (CLI takes precedence).

#### Source Types in Unified Config

Each source in the `sources` array can be any of the 17 supported types:

| Type | Required Fields |
|------|-----------------|
| `documentation` / `docs` | `base_url` |
| `github` | `repo` |
| `pdf` | `pdf_path` |
| `word` | `docx_path` |
| `epub` | `epub_path` |
| `video` | `url` or `video_path` |
| `local` | `directory` |
| `jupyter` | `notebook_path` |
| `html` | `html_path` |
| `openapi` | `spec_path` or `spec_url` |
| `asciidoc` | `asciidoc_path` |
| `pptx` | `pptx_path` |
| `rss` | `feed_url` or `feed_path` |
| `manpage` | `man_names` or `man_path` |
| `confluence` | `base_url` + `space_key` or `export_path` |
| `notion` | `database_id` or `page_id` or `export_path` |
| `chat` | `export_path` |

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

If `main_content` is not specified, the scraper tries these selectors in order until one matches:

1. `main`
2. `div[role="main"]`
3. `article`
4. `[role="main"]`
5. `.content`
6. `.doc-content`
7. `#main-content`

> **Tip:** Omit `main_content` from your config to let auto-detection work.
> Only specify it when auto-detection picks the wrong element.

Other defaults:

| Element | Default Selector |
|---------|-----------------|
| `title` | `title` |
| `code_blocks` | `pre code` |

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
  "description": "React - JavaScript library for building UIs",
  "sources": [
    {
      "type": "documentation",
      "base_url": "https://react.dev/",
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
        "include": ["/learn/", "/reference/"],
        "exclude": ["/community/", "/search"]
      },
      "categories": {
        "getting_started": ["learn", "tutorial"],
        "api": ["reference", "api"]
      },
      "rate_limit": 0.5,
      "max_pages": 300
    }
  ]
}
```

### Django GitHub

```json
{
  "name": "django-github",
  "description": "Django web framework source code",
  "sources": [
    {
      "type": "github",
      "repo": "django/django",
      "enable_codebase_analysis": true,
      "code_analysis_depth": "deep",
      "fetch_issues": true,
      "max_issues": 100,
      "fetch_releases": true,
      "file_patterns": ["*.py"],
      "exclude_patterns": ["tests/**", "docs/**"]
    }
  ]
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

### Unified with New Source Types

```json
{
  "name": "project-complete",
  "description": "Full project knowledge from multiple source types",
  "merge_mode": "claude-enhanced",
  "sources": [
    {
      "type": "docs",
      "name": "project-docs",
      "base_url": "https://docs.example.com/",
      "max_pages": 200
    },
    {
      "type": "github",
      "name": "project-code",
      "repo": "example/project"
    },
    {
      "type": "openapi",
      "name": "project-api",
      "spec_path": "api/openapi.yaml"
    },
    {
      "type": "confluence",
      "name": "project-wiki",
      "export_path": "./confluence-export/"
    },
    {
      "type": "jupyter",
      "name": "project-notebooks",
      "notebook_path": "./notebooks/"
    }
  ]
}
```

### Local Project

```json
{
  "name": "my-api",
  "description": "My REST API implementation",
  "sources": [
    {
      "type": "local",
      "directory": "./my-api-project",
      "languages": ["Python"],
      "file_patterns": ["*.py"],
      "exclude_patterns": ["tests/**", "migrations/**"],
      "analysis_depth": "comprehensive",
      "extract_api": true,
      "extract_test_examples": true
    }
  ]
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
