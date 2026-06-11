# 配置格式参考 - Skill Seekers

> **版本：** 3.6.0
> **最后更新：** 2026-03-15
> **18 种来源类型的完整 JSON 配置规范**

---

## 目录

- [概述](#概述)
- [单源配置](#单源配置)
  - [文档来源](#文档来源)
  - [GitHub 来源](#github-来源)
  - [PDF 来源](#pdf-来源)
  - [本地来源](#本地来源)
  - [其他来源类型](#其他来源类型)
- [统一（多源）配置](#统一多源配置)
- [公共字段](#公共字段)
- [选择器](#选择器)
- [类别](#类别)
- [URL 模式](#url-模式)
- [示例](#示例)

---

## 概述

Skill Seekers 使用统一格式的 JSON 配置文件。所有配置都使用 `sources` 数组，即使只抓取单一来源也是如此。

> **重要：** 不含 `sources` 的旧版配置已在 v2.11.0 中移除。所有配置必须使用下面展示的统一格式。

| 使用场景 | 示例 |
|----------|------|
| **单一来源** | `"sources": [{ "type": "documentation", ... }]` |
| **多个来源** | `"sources": [{ "type": "documentation", ... }, { "type": "github", ... }]` |

---

## 单源配置

即使只有单一来源，也要将其包裹在 `sources` 数组中。

### 文档来源

用于抓取文档网站。

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

#### 文档字段

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 是 | - | 技能名称（字母数字、破折号、下划线） |
| `base_url` | string | 是 | - | 基础文档 URL |
| `description` | string | 否 | "" | 用于 SKILL.md 的技能描述 |
| `start_urls` | array | 否 | `[base_url]` | 开始爬取的 URL |
| `selectors` | object | 否 | 见下文 | 用于内容提取的 CSS 选择器 |
| `url_patterns` | object | 否 | `{}` | 包含/排除 URL 模式 |
| `categories` | object | 否 | `{}` | 内容分类规则 |
| `rate_limit` | number | 否 | 0.5 | 请求间隔（秒） |
| `max_pages` | number | 否 | 500 | 最大抓取页数 |
| `merge_mode` | string | 否 | "claude-enhanced" | 合并策略 |
| `extract_api` | boolean | 否 | false | 提取 API 参考 |
| `llms_txt_url` | string | 否 | auto | llms.txt 文件路径 |

---

### GitHub 来源

用于分析 GitHub 仓库。

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

#### GitHub 字段

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 是 | - | 技能名称 |
| `type` | string | 是 | - | 必须为 `"github"` |
| `repo` | string | 是 | - | `owner/repo` 格式的仓库 |
| `description` | string | 否 | "" | 技能描述 |
| `enable_codebase_analysis` | boolean | 否 | true | 分析源代码 |
| `code_analysis_depth` | string | 否 | "standard" | `surface`、`standard`、`deep` |
| `fetch_issues` | boolean | 否 | true | 获取 GitHub issues |
| `max_issues` | number | 否 | 100 | 最大获取 issues 数 |
| `issue_labels` | array | 否 | [] | 按标签筛选 |
| `fetch_releases` | boolean | 否 | true | 获取 releases |
| `max_releases` | number | 否 | 20 | 最大 releases 数 |
| `fetch_changelog` | boolean | 否 | true | 提取 CHANGELOG |
| `analyze_commit_history` | boolean | 否 | false | 分析 commits |
| `file_patterns` | array | 否 | [] | 包含文件模式 |
| `exclude_patterns` | array | 否 | [] | 排除文件模式 |

---

### PDF 来源

用于从 PDF 文件提取内容。

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

#### PDF 字段

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 是 | - | 技能名称 |
| `type` | string | 是 | - | 必须为 `"pdf"` |
| `pdf_path` | string | 是 | - | PDF 文件路径 |
| `description` | string | 否 | "" | 技能描述 |
| `enable_ocr` | boolean | 否 | false | 扫描版 PDF 的 OCR |
| `password` | string | 否 | "" | 加密 PDF 的密码 |
| `extract_images` | boolean | 否 | false | 提取嵌入的图像 |
| `image_output_dir` | string | 否 | auto | 图像存放目录 |
| `extract_tables` | boolean | 否 | false | 提取表格 |
| `table_format` | string | 否 | "markdown" | `markdown`、`json`、`csv` |
| `page_range` | array | 否 | all | `[start, end]` 页码范围 |
| `split_by_chapters` | boolean | 否 | false | 按检测到的章节拆分 |
| `chunk_size` | number | 否 | 1000 | 每块字符数 |
| `chunk_overlap` | number | 否 | 100 | 块之间重叠 |

---

### 本地来源

用于分析本地代码库。

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

#### 本地字段

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 是 | - | 技能名称 |
| `type` | string | 是 | - | 必须为 `"local"` |
| `directory` | string | 是 | - | 目录路径 |
| `description` | string | 否 | "" | 技能描述 |
| `languages` | array | 否 | auto | 要分析的语言 |
| `file_patterns` | array | 否 | all | 包含模式 |
| `exclude_patterns` | array | 否 | common | 排除模式 |
| `analysis_depth` | string | 否 | "standard" | `quick`、`standard`、`comprehensive` |
| `extract_api` | boolean | 否 | true | 提取 API 文档 |
| `extract_patterns` | boolean | 否 | true | 检测模式 |
| `extract_test_examples` | boolean | 否 | true | 提取测试示例 |
| `extract_how_to_guides` | boolean | 否 | true | 生成指南 |
| `extract_config_patterns` | boolean | 否 | true | 提取配置模式 |
| `include_comments` | boolean | 否 | true | 包含代码注释 |
| `include_docstrings` | boolean | 否 | true | 包含 docstrings |
| `include_readme` | boolean | 否 | true | 包含 README |

---

### 其他来源类型

以下 10 种来源类型在 v3.2.0 中添加。每种都可以作为独立配置使用，也可以放在统一的 `sources` 数组中。

#### Jupyter Notebook 来源

```json
{
  "name": "ml-tutorial",
  "sources": [{
    "type": "jupyter",
    "notebook_path": "notebooks/tutorial.ipynb"
  }]
}
```

#### 本地 HTML 来源

```json
{
  "name": "offline-docs",
  "sources": [{
    "type": "html",
    "html_path": "./exported-docs/"
  }]
}
```

#### OpenAPI/Swagger 来源

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

#### AsciiDoc 来源

```json
{
  "name": "project-guide",
  "sources": [{
    "type": "asciidoc",
    "asciidoc_path": "./docs/guide.adoc"
  }]
}
```

#### PowerPoint 来源

```json
{
  "name": "training-slides",
  "sources": [{
    "type": "pptx",
    "pptx_path": "presentations/training.pptx"
  }]
}
```

#### RSS/Atom 订阅源来源

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

#### Man Page 来源

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

#### Confluence 来源

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

#### Notion 来源

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

#### 聊天（Slack/Discord）来源

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

#### 其他来源字段参考

| 来源类型 | 必填字段 | 可选字段 |
|----------|----------|----------|
| `jupyter` | `notebook_path` | — |
| `html` | `html_path` | — |
| `openapi` | `spec_path` 或 `spec_url` | — |
| `asciidoc` | `asciidoc_path` | — |
| `pptx` | `pptx_path` | — |
| `rss` | `feed_url` 或 `feed_path` | `follow_links`、`max_articles` |
| `manpage` | `man_names` 或 `man_path` | `sections` |
| `confluence` | `base_url` + `space_key` 或 `export_path` | `username`、`token`、`max_pages` |
| `notion` | `database_id` 或 `page_id` 或 `export_path` | `token`、`max_pages` |
| `chat` | `export_path` | `platform`、`token`、`channel`、`max_messages` |

---

## 统一（多源）配置

将多个来源合并为一个技能，并带有冲突检测。

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

#### 统一字段

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 是 | - | 合并后的技能名称 |
| `description` | string | 否 | "" | 技能描述 |
| `merge_mode` | string | 否 | "claude-enhanced" | `rule-based`、`claude-enhanced` |
| `sources` | array | 是 | - | 来源配置列表 |
| `conflict_detection` | object | 否 | `{}` | 冲突检测设置 |
| `output_structure` | object | 否 | `{}` | 输出组织 |
| `workflows` | array | 否 | `[]` | 要应用的工作流预设 |
| `workflow_stages` | array | 否 | `[]` | 内联增强阶段 |
| `workflow_vars` | object | 否 | `{}` | 工作流变量覆盖 |
| `workflow_dry_run` | boolean | 否 | `false` | 预览工作流而不执行 |

#### 工作流配置（统一）

统一配置支持在顶层定义增强工作流：

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

**工作流字段：**

| 字段 | 类型 | 描述 |
|------|------|------|
| `workflows` | array | 要应用的工作流预设名称列表 |
| `workflow_stages` | array | 包含 `name` 和 `prompt` 的内联阶段 |
| `workflow_vars` | object | 工作流变量的键值对 |
| `workflow_dry_run` | boolean | 预览工作流而不执行 |

**注意：** CLI 标志会覆盖配置中的值（CLI 优先）。

#### 统一配置中的来源类型

`sources` 数组中的每个来源可以是支持的 17 种类型中的任意一种：

| 类型 | 必填字段 |
|------|----------|
| `documentation` / `docs` | `base_url` |
| `github` | `repo` |
| `pdf` | `pdf_path` |
| `word` | `docx_path` |
| `epub` | `epub_path` |
| `video` | `url` 或 `video_path` |
| `local` | `directory` |
| `jupyter` | `notebook_path` |
| `html` | `html_path` |
| `openapi` | `spec_path` 或 `spec_url` |
| `asciidoc` | `asciidoc_path` |
| `pptx` | `pptx_path` |
| `rss` | `feed_url` 或 `feed_path` |
| `manpage` | `man_names` 或 `man_path` |
| `confluence` | `base_url` + `space_key` 或 `export_path` |
| `notion` | `database_id` 或 `page_id` 或 `export_path` |
| `chat` | `export_path` |

---

## 公共字段

所有配置类型中可用的字段：

| 字段 | 类型 | 描述 |
|------|------|------|
| `name` | string | 技能标识符。必须匹配 `^[a-zA-Z0-9_-]+$`（字母、数字、破折号、下划线）。提交到社区注册表时必填。 |
| `description` | string | 人类可读的描述 |
| `metadata.detected_version` | string \| null | **可选，由 `skill-seekers scan` 写入。** 从项目清单文件中检测到的框架版本（例如从 `package.json` 检测到 React 的 `"18.3.1"`）。位于 `metadata` 之下，与 `metadata.version` 并列（后者是配置 schema 版本——两者含义不同）。重新扫描时用于报告版本升级。旧的顶层位置在读取时仍然兼容，但新写入会放在 metadata 下。 |
| `metadata._url_unverified` | list[str] \| 不存在 | **可选，由 `skill-seekers scan --probe-urls` 写入。** 此配置中在生成后 HEAD 探测时返回 4xx/5xx 且无法通过重新提示 AI 修复的 URL 列表。仅当 AI 编造了不可达的 `base_url` 或 GitHub 仓库时才会出现。请视为 TODO：替换损坏的 URL 并删除该字段。下划线前缀表示这是扫描工具的元数据，不属于规范 schema。 |
| `rate_limit` | number | 请求间隔（秒） |
| `output_dir` | string | 自定义输出目录 |
| `skip_scrape` | boolean | 使用现有数据 |
| `enhance_level` | number | 0=关闭，1=SKILL.md，2=+config，3=完整 |

---

## 选择器

从 HTML 提取内容的 CSS 选择器：

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

### 默认选择器

如果未指定 `main_content`，抓取器会按以下顺序逐个尝试这些选择器，直到有一个匹配：

1. `main`
2. `div[role="main"]`
3. `article`
4. `[role="main"]`
5. `.content`
6. `.doc-content`
7. `#main-content`

> **提示：** 在配置中省略 `main_content` 可启用自动检测。
> 仅当自动检测选中了错误的元素时才需要显式指定。

其他默认值：

| 元素 | 默认选择器 |
|------|-----------|
| `title` | `title` |
| `code_blocks` | `pre code` |

---

## 类别

将 URL 模式映射到内容类别：

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

类别在生成的 SKILL.md 中显示为章节。

---

## URL 模式

控制包含或排除哪些 URL：

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

### 模式规则

- 模式与 URL 路径匹配
- 使用 `*` 作为通配符：`/api/v*/`
- 使用 `**` 作为递归通配符：`/docs/**/*.html`
- 排除优先于包含

---

## 示例

### React 文档

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

### 统一多源

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

### 使用新来源类型的统一配置

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

### 本地项目

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

## 验证

抓取前验证你的配置：

```bash
# 使用 CLI
skill-seekers create --config my-config.json --dry-run

# 使用 MCP 工具
validate_config({"config": "my-config.json"})
```

---

## 另请参阅

- [CLI 参考](CLI_REFERENCE.md) - 命令参考
- [环境变量](ENVIRONMENT_VARIABLES.md) - 配置环境

---

*更多示例，请参阅仓库中的 `configs/` 目录*
