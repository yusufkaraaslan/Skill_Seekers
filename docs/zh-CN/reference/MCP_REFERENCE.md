# MCP 参考 - Skill Seekers

> **版本：** 3.6.0  
> **最后更新：** 2026-04-09  
> **40 个 MCP 工具的完整参考**

---

## 目录

- [概述](#overview)
  - [什么是 MCP？](#what-is-mcp)
  - [传输模式](#transport-modes)
  - [启动服务器](#starting-the-server)
- [工具类别](#tool-categories)
  - [核心工具（9 个）](#core-tools)
  - [扩展工具（10 个）](#extended-tools)
  - [配置源工具（5 个）](#config-source-tools)
  - [配置拆分工具（2 个）](#config-splitting-tools)
  - [配置发布工具（1 个）](#config-publishing-tools)
  - [Marketplace 工具（4 个）](#marketplace-tools)
  - [向量数据库工具（4 个）](#vector-database-tools)
  - [工作流工具（5 个）](#workflow-tools)
- [工具参考](#tool-reference)
- [常见模式](#common-patterns)
- [错误处理](#error-handling)

---

## 概述

### 什么是 MCP？

MCP（Model Context Protocol）允许 Claude Code 等 AI 代理通过标准化接口与 Skill Seekers 交互。无需运行 CLI 命令，你可以使用自然语言：

```
"抓取 React 文档并创建一个技能"
"将 output/react 技能打包给 Claude"
"列出可用的工作流预设"
```

### 传输模式

MCP 服务器支持两种传输模式：

| 模式 | 使用场景 | 命令 |
|------|----------|---------|
| **stdio** | Claude Code、VS Code + Cline | `skill-seekers-mcp` |
| **HTTP** | Cursor、Windsurf、HTTP 客户端 | `skill-seekers-mcp --transport http --port 8765` |

### 启动服务器

```bash
# stdio 模式（默认）
skill-seekers-mcp

# HTTP 模式
skill-seekers-mcp --transport http --port 8765

# 自定义主机
skill-seekers-mcp --transport http --host 0.0.0.0 --port 8765
```

### 执行模型

工具**在进程内**运行 — 抓取工具通过 `get_converter()`，分析/打包工具
（`estimate_pages`、`detect_patterns`、`extract_test_examples`、
`extract_config_patterns`、`build_how_to_guides`、`split_config`、
`generate_router`、`package_skill`、`upload_skill`）通过与 CLI 相同的
解析器和 `main()` 函数运行（无子进程）。有两个例外仍按设计使用子进程：
使用 LOCAL 代理的 `enhance_skill` 和 `install_skill` 的增强步骤
（长时间运行的真实代理，已防止递归启动）。

共享的领域逻辑（marketplace 发布、配置发布、来源注册表、git 仓库处理、
分类检测）位于 `skill_seekers.services` 包中；旧的 `skill_seekers.mcp.*`
导入路径作为向后兼容 shim 保留。

---

## 工具类别

### 核心工具（9 个）

基本技能创建工作流的必备工具：

| 工具 | 用途 |
|------|---------|
| `list_configs` | 列出预设配置 |
| `generate_config` | 从文档 URL 生成配置 |
| `validate_config` | 验证配置结构 |
| `estimate_pages` | 估算页数 |
| `scrape_docs` | 抓取文档 |
| `package_skill` | 打包为 .zip |
| `upload_skill` | 上传到平台 |
| `enhance_skill` | AI 增强 |
| `install_skill` | 完整工作流 |

### 扩展工具（10 个）

高级抓取和分析工具：

| 工具 | 用途 |
|------|---------|
| `scrape_github` | GitHub 仓库分析 |
| `scrape_pdf` | PDF 提取 |
| `scrape_video` | 视频转录提取 |
| `scrape_codebase` | 本地代码库分析 |
| `scrape_generic` | 10 种新来源类型的通用抓取器 |
| `sync_config` | 从远程来源同步配置 |
| `detect_patterns` | 模式检测 |
| `extract_test_examples` | 从测试中提取使用示例 |
| `build_how_to_guides` | 生成操作指南 |
| `extract_config_patterns` | 提取配置模式 |

### 配置源工具（5 个）

管理配置来源：

| 工具 | 用途 |
|------|---------|
| `add_config_source` | 将 Git 仓库注册为配置源 |
| `list_config_sources` | 列出已注册的源 |
| `remove_config_source` | 移除配置源 |
| `fetch_config` | 从 Git 获取配置 |
| `submit_config` | 向源提交配置 |

### 配置拆分工具（2 个）

处理大型文档：

| 工具 | 用途 |
|------|---------|
| `split_config` | 拆分大型配置 |
| `generate_router` | 生成路由器技能 |

### 配置发布工具（1 个）

将配置推送到已注册的源仓库：

| 工具 | 用途 |
|------|---------|
| `push_config` | 将已验证的配置推送到已注册的配置源仓库 |

### Marketplace 工具（4 个）

管理插件 marketplace 仓库：

| 工具 | 用途 |
|------|---------|
| `add_marketplace` | 注册一个 marketplace 仓库 |
| `list_marketplaces` | 列出已注册的 marketplace |
| `remove_marketplace` | 移除一个 marketplace |
| `publish_to_marketplace` | 将技能发布到 marketplace 仓库 |

### 向量数据库工具（4 个）

导出到向量数据库：

| 工具 | 用途 |
|------|---------|
| `export_to_weaviate` | 导出到 Weaviate |
| `export_to_chroma` | 导出到 ChromaDB |
| `export_to_faiss` | 导出到 FAISS |
| `export_to_qdrant` | 导出到 Qdrant |

### 工作流工具（5 个）

管理增强工作流：

| 工具 | 用途 |
|------|---------|
| `list_workflows` | 列出所有工作流 |
| `get_workflow` | 获取工作流 YAML |
| `create_workflow` | 创建新工作流 |
| `update_workflow` | 更新工作流 |
| `delete_workflow` | 删除工作流 |

---

## 工具参考

---

### 核心工具

#### list_configs

列出所有可用的预设配置。

**参数：** 无

**返回：** 配置对象数组

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

**示例：**
```python
# 自然语言
"List available configurations"
"What configs are available?"
"Show me the preset configs"
```

---

#### generate_config

从文档 URL 生成配置文件。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `url` | string | 是 | 文档 URL |
| `name` | string | 否 | 配置名称（自动检测） |
| `description` | string | 否 | 描述（自动检测） |

**返回：** 配置 JSON 对象

**示例：**
```python
# 自然语言
"Generate a config for https://docs.django.com/"
"Create a Django config"
"Make a config from the React docs URL"
```

---

#### validate_config

验证配置文件结构。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `config` | object/string | 是 | 配置对象或文件路径 |

**返回：** 验证结果

```json
{
  "valid": true,
  "errors": [],
  "warnings": []
}
```

**示例：**
```python
# 自然语言
"Validate this config: {config_json}"
"Check if my config is valid"
"Validate configs/react.json"
```

---

#### estimate_pages

估算文档抓取的总页数。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `config` | object/string | 是 | 配置对象或文件路径 |
| `max_discovery` | number | 否 | 最大发现页数（默认：1000） |

**返回：** 估算结果

```json
{
  "estimated_pages": 230,
  "discovery_rate": 1.28,
  "estimated_time_minutes": 3.8
}
```

**示例：**
```python
# 自然语言
"Estimate pages for the React config"
"How many pages will Django docs have?"
"Estimate with max 500 pages"
```

---

#### scrape_docs

抓取文档网站并生成技能。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `config` | object/string | 是 | 配置对象或文件路径 |
| `enhance_level` | number | 否 | 0-3（默认：2） |
| `max_pages` | number | 否 | 覆盖最大页数 |
| `dry_run` | boolean | 否 | 仅预览（统一多源配置同样支持） |

**返回：** 抓取结果

```json
{
  "skill_directory": "output/react/",
  "pages_scraped": 180,
  "references_generated": 12,
  "status": "success"
}
```

**示例：**
```python
# 自然语言
"Scrape the React documentation"
"Scrape Django with enhancement level 3"
"Do a dry run of the Vue docs scrape"
```

---

#### package_skill

将技能目录打包为可上传格式。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `skill_directory` | string | 是 | 技能目录路径 |
| `target` | string | 否 | 平台（默认：claude） |
| `streaming` | boolean | 否 | 使用流式模式 |

**返回：** 包信息

```json
{
  "package_path": "output/react-claude.zip",
  "platform": "claude",
  "size_bytes": 245760
}
```

**示例：**
```python
# 自然语言
"Package the React skill for Claude"
"Create a Gemini package for output/django/"
"Package with streaming mode"
```

---

#### upload_skill

将技能包上传到 LLM 平台。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `package_path` | string | 是 | 包文件路径 |
| `target` | string | 否 | 平台（默认：claude） |
| `api_key` | string | 否 | 平台 API 密钥 |

**返回：** 上传结果

```json
{
  "success": true,
  "platform": "claude",
  "skill_id": "skill_abc123"
}
```

**示例：**
```python
# 自然语言
"Upload the React package to Claude"
"Upload output/django-gemini.tar.gz to Gemini"
```

---

#### enhance_skill

AI 驱动的 SKILL.md 增强。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `skill_directory` | string | 是 | 技能目录路径 |
| `mode` | string | 否 | API 或 LOCAL（默认：auto） |
| `workflow` | string | 否 | 工作流预设名称 |

**返回：** 增强结果

```json
{
  "success": true,
  "mode": "LOCAL",
  "skill_md_lines": 450
}
```

**示例：**
```python
# 自然语言
"Enhance the React skill"
"Enhance with security-focus workflow"
"Run enhancement in API mode"
```

---

#### install_skill

完整工作流：抓取 → 增强 → 打包 → 上传。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `config` | object/string | 是 | 配置对象或文件路径 |
| `target` | string | 否 | 平台（默认：claude） |
| `enhance` | boolean | 否 | 启用增强（默认：true） |
| `upload` | boolean | 否 | 自动上传（默认：true） |

**返回：** 安装结果

```json
{
  "success": true,
  "skill_directory": "output/react/",
  "package_path": "output/react-claude.zip",
  "uploaded": true
}
```

**示例：**
```python
# 自然语言
"Install the React skill"
"Install Django for Gemini with no upload"
"Complete install of the Vue config"
```

---

### 扩展工具

#### scrape_github

抓取 GitHub 仓库。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `repo` | string | 是 | owner/repo 格式 |
| `token` | string | 否 | GitHub token |
| `name` | string | 否 | 技能名称 |
| `include_issues` | boolean | 否 | 包含 issues（默认：true） |
| `include_releases` | boolean | 否 | 包含 releases（默认：true） |

**示例：**
```python
# 自然语言
"Scrape the facebook/react repository"
"Analyze the Django GitHub repo"
"Scrape vercel/next.js with issues"
```

---

#### scrape_pdf

从 PDF 文件提取内容。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `pdf_path` | string | 是 | PDF 文件路径 |
| `name` | string | 否 | 技能名称 |
| `enable_ocr` | boolean | 否 | 为扫描版 PDF 启用 OCR |

**示例：**
```python
# 自然语言
"Scrape the manual.pdf file"
"Extract content from API-docs.pdf"
"Process scanned.pdf with OCR"
```

---

#### scrape_codebase

分析本地代码库。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `directory` | string | 是 | 目录路径 |
| `preset` | string | 否 | quick/standard/comprehensive |
| `languages` | array | 否 | 语言筛选 |

**示例：**
```python
# 自然语言
"Analyze the ./my-project directory"
"Scrape this codebase with comprehensive preset"
"Analyze only Python and JavaScript files"
```

---

#### unified_scrape

多源抓取（文档 + GitHub + PDF）。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `config` | object/string | 是 | 统一配置 |
| `merge_mode` | string | 否 | rule-based 或 claude-enhanced |

**示例：**
```python
# 自然语言
"Run unified scraping with my-config.json"
"Combine docs and GitHub for React"
"Multi-source scrape with claude-enhanced merge"
```

---

#### detect_patterns

检测仓库中的代码模式。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `directory` | string | 是 | 目录路径 |
| `pattern_types` | array | 否 | 要检测的类型 |

**返回：** 检测到的模式

**示例：**
```python
# 自然语言
"Detect patterns in this codebase"
"Find architectural patterns"
"Show me the code patterns"
```

---

#### extract_test_examples

从测试文件提取使用示例。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `directory` | string | 是 | 测试目录路径 |
| `language` | string | 否 | 主要语言 |

**返回：** 测试示例

**示例：**
```python
# 自然语言
"Extract test examples from tests/"
"Get Python test examples"
"Find usage examples in the test suite"
```

---

#### build_how_to_guides

从代码库生成操作指南。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `directory` | string | 是 | 目录路径 |
| `topics` | array | 否 | 特定主题 |

**返回：** 生成的指南

**示例：**
```python
# 自然语言
"Build how-to guides for this project"
"Generate guides about authentication"
"Create how-to documentation"
```

---

#### extract_config_patterns

提取配置模式。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `directory` | string | 是 | 目录路径 |

**返回：** 配置模式

**示例：**
```python
# 自然语言
"Extract config patterns from this project"
"Find configuration examples"
"Show me how this project is configured"
```

---

#### detect_conflicts

查找文档和代码之间的差异。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `docs_source` | string | 是 | 文档配置或目录 |
| `code_source` | string | 是 | 代码目录或仓库 |

**返回：** 冲突报告

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

**示例：**
```python
# 自然语言
"Detect conflicts between docs and code"
"Find discrepancies in React"
"Compare documentation to implementation"
```

---

#### scrape_generic

从 10 种新来源类型中的任意一种抓取内容。

**目的：** 一个通用入口点，将请求委派给对应的 CLI 抓取器模块，支持：jupyter、html、openapi、asciidoc、pptx、confluence、notion、rss、manpage、chat。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `source_type` | string | 是 | 其中之一：`jupyter`、`html`、`openapi`、`asciidoc`、`pptx`、`confluence`、`notion`、`rss`、`manpage`、`chat` |
| `name` | string | 是 | 输出的技能名称 |
| `path` | string | 否 | 文件或目录路径（用于基于文件的来源） |
| `url` | string | 否 | URL（用于基于 URL 的来源，如 confluence、notion、rss） |

**注意：** 必须根据来源类型提供 `path` 或 `url` 之一。

**来源类型 → 输入映射：**

| 来源类型 | 典型输入 | 使用的 CLI 标志 |
|-------------|--------------|---------------|
| `jupyter` | `path` | `--notebook` |
| `html` | `path` | `--html-path` |
| `openapi` | `path` | `--spec` |
| `asciidoc` | `path` | `--asciidoc-path` |
| `pptx` | `path` | `--pptx` |
| `manpage` | `path` | `--man-path` |
| `confluence` | `path` 或 `url` | `--export-path` / `--base-url` |
| `notion` | `path` 或 `url` | `--export-path` / `--database-id` |
| `rss` | `path` 或 `url` | `--feed-path` / `--feed-url` |
| `chat` | `path` | `--export-path` |

**返回：** 包含文件路径和统计信息的抓取结果

```json
{
  "skill_directory": "output/my-api/",
  "source_type": "openapi",
  "status": "success"
}
```

**示例：**
```python
# 自然语言
"Scrape the OpenAPI spec at api/openapi.yaml"
"Extract content from my Jupyter notebook analysis.ipynb"
"Process the Confluence export in ./wiki-export/"
"Convert the PowerPoint slides.pptx into a skill"

# 显式工具调用
scrape_generic(source_type="openapi", name="my-api", path="api/openapi.yaml")
scrape_generic(source_type="jupyter", name="ml-tutorial", path="notebooks/tutorial.ipynb")
scrape_generic(source_type="rss", name="blog", url="https://blog.example.com/feed.xml")
scrape_generic(source_type="confluence", name="wiki", path="./confluence-export/")
```

---

### 配置源工具

#### add_config_source

将 Git 仓库注册为配置源。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `name` | string | 是 | 源名称 |
| `url` | string | 是 | Git 仓库 URL |
| `branch` | string | 否 | Git 分支（默认：main） |

**示例：**
```python
# 自然语言
"Add my-configs repo as a source"
"Register https://github.com/org/configs as configs"
```

---

#### list_config_sources

列出所有已注册的配置源。

**参数：** 无

**返回：** 源列表

**示例：**
```python
# 自然语言
"List my config sources"
"Show registered sources"
```

---

#### remove_config_source

移除配置源。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `name` | string | 是 | 源名称 |

**示例：**
```python
# 自然语言
"Remove the configs source"
"Delete my old config source"
```

---

#### fetch_config

从 Git 源获取配置。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `source` | string | 是 | 源名称 |
| `config_name` | string | 否 | 要获取的特定配置 |

**示例：**
```python
# 自然语言
"Fetch configs from my source"
"Get the react config from configs source"
```

---

#### submit_config

向源提交配置。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `source` | string | 是 | 源名称 |
| `config_path` | string | 是 | 配置文件路径 |

**示例：**
```python
# 自然语言
"Submit my-config.json to configs source"
"Add this config to my source"
```

---

### 配置拆分工具

#### split_config

将大型配置拆分为更小的块。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `config` | string | 是 | 配置文件路径 |
| `max_pages_per_chunk` | number | 否 | 每块页数（默认：100） |
| `output_dir` | string | 否 | 输出目录 |

**示例：**
```python
# 自然语言
"Split the large config into chunks"
"Break up this 500-page config"
"Split with 50 pages per chunk"
```

---

#### generate_router

为大型文档生成路由器技能。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `config` | string | 是 | 配置文件路径 |
| `output_dir` | string | 否 | 输出目录 |

**示例：**
```python
# 自然语言
"Generate a router for this large config"
"Create a router skill for Django docs"
```

---

### 向量数据库工具

#### export_to_weaviate

将技能导出到 Weaviate 向量数据库。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `skill_directory` | string | 是 | 技能路径 |
| `weaviate_url` | string | 否 | Weaviate URL |
| `class_name` | string | 否 | 类/集合名称 |

**示例：**
```python
# 自然语言
"Export React skill to Weaviate"
"Send to Weaviate at localhost:8080"
```

---

#### export_to_chroma

将技能导出到 ChromaDB。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `skill_directory` | string | 是 | 技能路径 |
| `collection_name` | string | 否 | 集合名称 |
| `persist_directory` | string | 否 | 存储目录 |

**示例：**
```python
# 自然语言
"Export to ChromaDB"
"Send Django skill to Chroma"
```

---

#### export_to_faiss

将技能导出到 FAISS 索引。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `skill_directory` | string | 是 | 技能路径 |
| `output_path` | string | 否 | 索引文件路径 |

**示例：**
```python
# 自然语言
"Export to FAISS index"
"Create FAISS index for this skill"
```

---

#### export_to_qdrant

将技能导出到 Qdrant。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `skill_directory` | string | 是 | 技能路径 |
| `collection_name` | string | 否 | 集合名称 |
| `qdrant_url` | string | 否 | Qdrant URL |

**示例：**
```python
# 自然语言
"Export to Qdrant"
"Send skill to Qdrant vector DB"
```

---

### 工作流工具

#### list_workflows

列出所有可用的工作流预设。

**参数：** 无

**返回：**
```json
{
  "workflows": [
    {"name": "security-focus", "source": "bundled"},
    {"name": "my-custom", "source": "user"}
  ]
}
```

**示例：**
```python
# 自然语言
"List available workflows"
"What workflow presets do I have?"
```

---

#### get_workflow

获取工作流的完整 YAML 内容。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `name` | string | 是 | 工作流名称 |

**返回：** 工作流 YAML

**示例：**
```python
# 自然语言
"Show me the security-focus workflow"
"Get the YAML for the default workflow"
```

---

#### create_workflow

创建新工作流。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `name` | string | 是 | 工作流名称 |
| `yaml_content` | string | 是 | 工作流 YAML |

**示例：**
```python
# 自然语言
"Create a workflow called my-workflow"
"Save this YAML as a new workflow"
```

---

#### update_workflow

更新现有工作流。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `name` | string | 是 | 工作流名称 |
| `yaml_content` | string | 是 | 新的 YAML 内容 |

**示例：**
```python
# 自然语言
"Update my-custom workflow"
"Modify the security-focus workflow"
```

---

#### delete_workflow

删除用户工作流。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| `name` | string | 是 | 工作流名称 |

**示例：**
```python
# 自然语言
"Delete my-old-workflow"
"Remove the test workflow"
```

---

## 常见模式

### 模式 1：快速文档技能

```python
# 自然语言序列：
"List available configs"
"Scrape the react config"
"Package output/react for Claude"
```

工具：`list_configs` → `scrape_docs` → `package_skill`

---

### 模式 2：GitHub 仓库分析

```python
# 自然语言序列：
"Scrape the facebook/react GitHub repo"
"Enhance the output/react skill"
"Package it for Gemini"
```

工具：`scrape_github` → `enhance_skill` → `package_skill`

---

### 模式 3：完整单命令

```python
# 自然语言：
"Install the Django skill for Claude"
```

工具：`install_skill`

---

### 模式 4：带工作流的多源

```python
# 自然语言序列：
"List available workflows"
"Run unified scrape with my-unified.json"
"Apply security-focus and api-documentation workflows"
"Package for Claude"
```

工具：`list_workflows` → `unified_scrape` → `enhance_skill` → `package_skill`

---

### 模式 5：新来源类型抓取

```python
# 自然语言序列：
"Scrape the OpenAPI spec at api/openapi.yaml"
"Package the output for Claude"
```

工具：`scrape_generic` → `package_skill`

---

### 模式 6：向量数据库导出

```python
# 自然语言序列：
"Scrape the Django documentation"
"Export to ChromaDB"
```

工具：`scrape_docs` → `export_to_chroma`

---

## 错误处理

### 常见错误

| 错误 | 原因 | 解决方案 |
|-------|-------|----------|
| `ConfigNotFoundError` | 配置不存在 | 检查配置名称或路径 |
| `InvalidConfigError` | 配置格式错误 | 使用 `validate_config` |
| `ScrapingError` | 网络或选择器问题 | 检查 URL 和选择器 |
| `RateLimitError` | 请求过多 | 等待或使用 token |
| `EnhancementError` | AI 增强失败 | 检查 API 密钥或 Claude Code |

### 错误响应格式

```json
{
  "error": true,
  "error_type": "ConfigNotFoundError",
  "message": "Config 'react' not found",
  "suggestion": "Run list_configs to see available configs"
}
```

---

## 另请参阅

- [CLI 参考](CLI_REFERENCE.md) - 命令行界面
- [配置格式](CONFIG_FORMAT.md) - JSON 配置
- [MCP 设置指南](../advanced/mcp-server.md) - 服务器配置

---

*获取工具帮助：向 AI 代理询问特定工具*
