# CLI 参考 - Skill Seekers

> **版本：** 3.6.0
> **最后更新：** 2026-03-15
> **所有 30 个 CLI 命令的完整参考**

---

## 目录

- [概述](#overview)
  - [安装](#installation)
  - [全局标志](#global-flags)
  - [环境变量](#environment-variables)
- [命令参考](#command-reference)
  - [analyze](#analyze) - 分析本地代码库
  - [asciidoc](#asciidoc) - 从 AsciiDoc 文件提取
  - [chat](#chat) - 从 Slack/Discord 提取
  - [config](#config) - 配置向导
  - [confluence](#confluence) - 从 Confluence 提取
  - [create](#create) - 创建技能（自动检测来源）
  - [enhance](#enhance) - AI 增强（本地模式）
  - [enhance-status](#enhance-status) - 监控增强
  - [estimate](#estimate) - 估算页面数
  - [github](#github) - 抓取 GitHub 仓库
  - [本地 HTML 文件（通过 `create`）](#local-html-files-via-create) - 从本地 HTML 文件提取
  - [install](#install) - 单命令完整工作流
  - [install-agent](#install-agent) - 安装到 AI 代理
  - [jupyter](#jupyter) - 从 Jupyter 笔记本提取
  - [manpage](#manpage) - 从 man 手册页提取
  - [multilang](#multilang) - 多语言文档
  - [notion](#notion) - 从 Notion 提取
  - [openapi](#openapi) - 从 OpenAPI/Swagger 规范提取
  - [package](#package) - 为平台打包技能
  - [pdf](#pdf) - 从 PDF 提取
  - [pptx](#pptx) - 从 PowerPoint 文件提取
  - [quality](#quality) - 质量评分
  - [resume](#resume) - 恢复中断的任务
  - [rss](#rss) - 从 RSS/Atom 订阅源提取
  - [scan](#scan) - AI 检测项目技术栈并按框架生成配置
  - [scrape](#scrape) - 抓取文档
  - [stream](#stream) - 流式处理大文件
  - [unified](#unified) - 多源抓取
  - [update](#update) - 增量更新
  - [upload](#upload) - 上传到平台
  - [video](#video) - 视频提取与设置
  - [workflows](#workflows) - 管理工作流预设
- [常见工作流](#common-workflows)
- [退出码](#exit-codes)
- [故障排除](#troubleshooting)

---

## 概述

Skill Seekers 提供一个统一的 CLI，可将文档、GitHub 仓库、PDF、视频、笔记本、维基等 18 种来源类型（17 + config）转换为 AI 就绪的技能，面向 21+ 个 LLM 平台和 RAG 流水线。

### 安装

```bash
# 基础安装
pip install skill-seekers

# 附带所有平台支持
pip install skill-seekers[all-llms]

# 开发环境设置
pip install -e ".[all-llms,dev]"
```

验证安装：
```bash
skill-seekers --version
```

### 全局标志

这些标志适用于**所有来源类型子命令和 `create`**：

| 标志 | 描述 |
|------|-------------|
| `-h, --help` | 显示帮助信息并退出 |
| `--version` | 显示版本号并退出 |
| `-n, --name` | 技能名称 |
| `-d, --description` | 技能描述 |
| `-o, --output` | 输出目录 |
| `--enhance-level` | AI 增强级别（0-3） |
| `--api-key` | Anthropic API 密钥 |
| `-v, --verbose` | 启用详细（DEBUG）输出 |
| `-q, --quiet` | 最小化输出（仅 WARNING） |
| `--dry-run` | 预览而不执行 |
| `--enhance-workflow` | 应用增强工作流预设 |

### 环境变量

完整参考请参阅 [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md)。

**常用变量：**

| 变量 | 用途 |
|----------|---------|
| `ANTHROPIC_API_KEY` | Claude AI API 访问 |
| `GOOGLE_API_KEY` | Google Gemini API 访问 |
| `OPENAI_API_KEY` | OpenAI API 访问 |
| `GITHUB_TOKEN` | GitHub API（更高的速率限制） |

---

## 命令参考

命令按字母顺序排列。

---

### analyze

分析本地代码库并提取代码知识。

**用途：** 深度代码分析，包括模式检测、API 提取和文档生成。

**语法：**
```bash
skill-seekers create DIR [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `DIR`（位置参数，或 `--directory DIR`） | 是 | 要分析的目录 |
| `--output DIR` | 否 | 输出目录（默认：output/codebase/） |

**标志：**

| 短 | 长 | 默认值 | 描述 |
|-------|------|---------|-------------|
| `-n` | `--name` | auto | 技能名称（默认为目录名） |
| `-d` | `--description` | auto | 技能描述 |
| | `--preset` | standard | 分析预设：quick、standard、comprehensive |
| | `--preset-list` | | 显示可用预设并退出 |
| | `--languages` | auto | 逗号分隔的语言（Python,JavaScript,C++） |
| | `--file-patterns` | | 逗号分隔的文件模式 |
| | `--enhance-level` | 0 | AI 增强：0=关闭（默认），1=SKILL.md，2=+config，3=完整 |
| | `--api-key` | | Anthropic API 密钥（或 ANTHROPIC_API_KEY 环境变量） |
| | `--enhance-workflow` | | 应用工作流预设（可多次使用） |
| | `--enhance-stage` | | 添加内联增强阶段（name:prompt） |
| | `--var` | | 覆盖工作流变量（key=value） |
| | `--workflow-dry-run` | | 预览工作流而不执行 |
| | `--dry-run` | | 预览分析而不创建输出 |
| `-v` | `--verbose` | | 启用详细（DEBUG）日志 |
| `-q` | `--quiet` | | 最小化输出（仅 WARNING） |
| | `--skip-api-reference` | | 跳过 API 文档生成 |
| | `--skip-dependency-graph` | | 跳过依赖图 |
| | `--skip-patterns` | | 跳过模式检测 |
| | `--skip-test-examples` | | 跳过测试示例提取 |
| | `--skip-how-to-guides` | | 跳过操作指南生成 |
| | `--skip-config-patterns` | | 跳过配置模式提取 |
| | `--skip-docs` | | 跳过项目文档（README） |
| | `--no-comments` | | 跳过注释提取 |

**示例：**

```bash
# 使用默认值进行基础分析
skill-seekers create ./my-project

# 快速分析（1-2 分钟）
skill-seekers create ./my-project --preset quick

# 全面分析，包含所有功能
skill-seekers create ./my-project --preset comprehensive

# 仅特定语言
skill-seekers create ./my-project --languages Python,JavaScript

# 跳过重型功能以加快分析
skill-seekers create ./my-project --skip-dependency-graph --skip-patterns
```

**退出码：**
- `0` - 成功
- `1` - 分析失败

---

### asciidoc

从 AsciiDoc 文件提取内容并生成技能。

**用途：** 将 `.adoc` / `.asciidoc` 文档转换为 AI 就绪的技能。

**语法：**
```bash
skill-seekers create <asciidoc-file> [options]
```

**关键标志：**

| 标志 | 描述 |
|------|-------------|
| `--asciidoc-path PATH` | AsciiDoc 文件或目录的路径 |
| `-n, --name` | 技能名称 |
| `--from-json FILE` | 从提取的 JSON 构建 |
| `--enhance-level` | AI 增强（默认：0） |
| `--dry-run` | 预览而不执行 |

**示例：**

```bash
# 单个文件
skill-seekers create guide.adoc --name my-guide

# AsciiDoc 文件目录
skill-seekers create ./docs/ --name project-docs
```

---

### chat

从 Slack 或 Discord 聊天记录导出提取知识。

**用途：** 将聊天历史转换为可搜索的 AI 就绪技能。

**语法：**
```bash
skill-seekers create [options]
```

**关键标志：**

| 标志 | 描述 |
|------|-------------|
| `--chat-export-path PATH` | Slack/Discord 导出目录的路径 |
| `--platform {slack,discord}` | 聊天平台（默认：slack） |
| `-n, --name` | 技能名称 |
| `--dry-run` | 预览而不执行 |

**示例：**

```bash
# 从 Slack 导出
skill-seekers create --chat-export-path ./slack-export/ --name team-knowledge

# 从 Discord 导出
skill-seekers create --chat-export-path ./discord-export/ --platform discord --name discord-docs
```

---

### config

API 密钥和设置的交互式配置向导。

**用途：** 设置 GitHub token、API 密钥和首选项。

**语法：**
```bash
skill-seekers config [options]
```

**标志：**

| 短 | 长 | 描述 |
|-------|------|-------------|
| | `--github` | 直接进入 GitHub token 设置 |
| | `--api-keys` | 直接进入 API 密钥设置 |
| | `--show` | 显示当前配置 |
| | `--test` | 测试连接 |

**示例：**

```bash
# 完整配置向导
skill-seekers config

# 快速 GitHub 设置
skill-seekers config --github

# 查看当前配置
skill-seekers config --show

# 测试所有连接
skill-seekers config --test
```

---

### confluence

从 Confluence 维基提取内容。

**用途：** 通过 API 或 HTML 导出将 Confluence 空间转换为 AI 就绪的技能。

**语法：**
```bash
skill-seekers create [options]
```

**关键标志：**

| 标志 | 描述 |
|------|-------------|
| `--conf-base-url URL` | Confluence 实例的基础 URL |
| `--space-key KEY` | Confluence 空间键 |
| `--conf-export-path PATH` | Confluence HTML/XML 导出目录的路径 |
| `--max-pages N` | 最大提取页数 |
| `-n, --name` | 技能名称 |
| `--dry-run` | 预览而不执行 |

身份验证来自 `CONFLUENCE_USERNAME` / `CONFLUENCE_TOKEN`
环境变量。

**示例：**

```bash
# 通过 API
export CONFLUENCE_USERNAME=user@example.com
export CONFLUENCE_TOKEN=...
skill-seekers create --conf-base-url https://wiki.example.com --space-key DEV --name dev-wiki

# 从导出
skill-seekers create --conf-export-path ./confluence-export/ --name team-docs
```

---

### create

从任意来源创建技能。自动检测来源类型。

**用途：** 通用入口——自动处理 URL、GitHub 仓库、本地目录、PDF 和配置文件。

**语法：**
```bash
skill-seekers create [source] [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `source` | 否 | 来源 URL、仓库、路径或配置文件 |

**来源类型（自动检测）：**
| 来源模式 | 类型 | 示例 |
|----------------|------|---------|
| `https://...` | 文档 | `https://docs.react.dev/` |
| `owner/repo` | GitHub | `facebook/react` |
| `./path` | 本地代码库 | `./my-project` |
| `*.pdf` | PDF | `manual.pdf` |
| `*.docx` | Word | `report.docx` |
| `*.epub` | EPUB | `book.epub` |
| `*.ipynb` | Jupyter Notebook | `analysis.ipynb` |
| `*.html`/`*.htm` | 本地 HTML | `docs.html` |
| `*.yaml`/`*.yml` | OpenAPI/Swagger | `openapi.yaml` |
| `*.adoc`/`*.asciidoc` | AsciiDoc | `guide.adoc` |
| `*.pptx` | PowerPoint | `slides.pptx` |
| `*.rss`/`*.atom` | RSS/Atom 订阅源 | `feed.rss` |
| `*.1`-`*.8`/`*.man` | Man 手册页 | `grep.1` |
| `*.json` | 配置文件 | `config.json` |

**标志：**

| 短 | 长 | 默认值 | 描述 |
|-------|------|---------|-------------|
| `-n` | `--name` | auto | 技能名称 |
| `-d` | `--description` | auto | 技能描述 |
| `-o` | `--output` | auto | 输出目录 |
| `-p` | `--preset` | | 分析预设：quick、standard、comprehensive |
| `-c` | `--config` | | 从 JSON 文件加载设置 |
| | `--enhance-level` | 2 | AI 增强级别（0-3） |
| | `--api-key` | | Anthropic API 密钥 |
| | `--enhance-workflow` | | 应用工作流预设（可多次使用） |
| | `--enhance-stage` | | 添加内联增强阶段 |
| | `--var` | | 覆盖工作流变量（key=value） |
| | `--workflow-dry-run` | | 预览工作流而不执行 |
| | `--dry-run` | | 预览而不创建 |
| | `--chunk-for-rag` | | 启用 RAG 分块 |
| | `--chunk-tokens` | 512 | 分块大小（token） |
| | `--chunk-overlap-tokens` | 50 | 分块重叠（token） |
| | `--help-web` | | 显示网页抓取选项 |
| | `--help-github` | | 显示 GitHub 选项 |
| | `--help-local` | | 显示本地分析选项 |
| | `--help-pdf` | | 显示 PDF 选项 |
| | `--help-all` | | 显示所有 120+ 选项 |

**示例：**

```bash
# 文档网站
skill-seekers create https://docs.django.com/

# GitHub 仓库
skill-seekers create facebook/react

# 本地代码库
skill-seekers create ./my-project

# PDF 文件
skill-seekers create manual.pdf --name product-docs

# 使用预设
skill-seekers create https://docs.react.dev/ --preset quick

# 使用增强工作流
skill-seekers create ./my-project --enhance-workflow security-focus

# 多工作流链式调用
skill-seekers create ./my-project \
  --enhance-workflow security-focus \
  --enhance-workflow api-documentation
```

---

### enhance

使用本地编码代理（Claude Code）增强 SKILL.md。

**用途：** 无需 API 成本的 AI 驱动质量提升。需要安装 Claude Code。

**语法：**
```bash
skill-seekers enhance SKILL_DIRECTORY [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `SKILL_DIRECTORY` | 是 | 技能目录路径 |

**标志：**

| 短 | 长 | 默认值 | 描述 |
|-------|------|---------|-------------|
| | `--agent` | claude | 要使用的本地编码代理 |
| | `--agent-cmd` | | 覆盖代理命令模板 |
| | `--background` | | 后台运行 |
| | `--daemon` | | 以守护进程运行 |
| | `--no-force` | | 启用确认 |
| | `--timeout` | 600 | 超时时间（秒） |

**示例：**

```bash
# 基础增强
skill-seekers enhance output/react/

# 后台模式
skill-seekers enhance output/react/ --background

# 自定义超时
skill-seekers enhance output/react/ --timeout 1200

# 监控后台增强
skill-seekers enhance-status output/react/ --watch
```

**要求：** 必须安装并认证 Claude Code。

---

### enhance-status

监控后台增强进程。

**用途：** 检查后台/守护进程模式下增强的运行状态。

**语法：**
```bash
skill-seekers enhance-status SKILL_DIRECTORY [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `SKILL_DIRECTORY` | 是 | 技能目录路径 |

**标志：**

| 短 | 长 | 默认值 | 描述 |
|-------|------|---------|-------------|
| `-w` | `--watch` | | 实时监视 |
| | `--json` | | JSON 输出 |
| | `--interval` | 5 | 监视间隔（秒） |

**示例：**

```bash
# 一次性检查状态
skill-seekers enhance-status output/react/

# 持续监视
skill-seekers enhance-status output/react/ --watch

# 用于脚本的 JSON 输出
skill-seekers enhance-status output/react/ --json
```

---

### estimate

抓取前估算页面数。

**用途：** 预览将抓取多少页面，无需实际下载。

**语法：**
```bash
skill-seekers estimate [config] [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `config` | 否 | 配置 JSON 文件路径 |

**标志：**

| 短 | 长 | 默认值 | 描述 |
|-------|------|---------|-------------|
| | `--all` | | 列出所有可用配置 |
| `-m` | `--max-discovery` | 1000 | 最大发现页面数（`-1` 表示无限制） |
| `-u` | `--unlimited` | | 取消发现限制（等同于 `--max-discovery -1`） |
| `-t` | `--timeout` | 30 | HTTP 请求超时（秒） |

**示例：**

```bash
# 使用配置文件估算
skill-seekers estimate configs/react.json

# 快速估算（100 页）
skill-seekers estimate configs/react.json --max-discovery 100

# 发现全部页面，给较慢的站点更多时间
skill-seekers estimate configs/react.json --unlimited --timeout 60

# 列出所有可用预设
skill-seekers estimate --all
```

---

### github

抓取 GitHub 仓库并生成技能。

**用途：** 从 GitHub 仓库提取代码、issues、releases 和元数据。

**语法：**
```bash
skill-seekers create [options]
```

**标志：**

| 短 | 长 | 默认值 | 描述 |
|-------|------|---------|-------------|
| | `--repo` | | 仓库（owner/repo 格式） |
| `-c` | `--config` | | 配置 JSON 文件 |
| | `--token` | | GitHub 个人访问令牌 |
| `-n` | `--name` | auto | 技能名称 |
| `-d` | `--description` | auto | 描述 |
| `-o` | `--output` | auto | 输出目录 |
| | `--no-issues` | | 跳过 GitHub issues |
| | `--no-changelog` | | 跳过 CHANGELOG |
| | `--no-releases` | | 跳过 releases |
| | `--max-issues` | 100 | 最大获取 issues 数 |
| | `--scrape-only` | | 仅抓取，不构建 |
| | `--enhance-level` | 2 | AI 增强（0-3） |
| | `--api-key` | | Anthropic API 密钥 |
| | `--enhance-workflow` | | 应用工作流预设 |
| | `--non-interactive` | | CI/CD 模式（快速失败） |
| | `--profile` | | 配置中的 GitHub 个人资料 |
| | `--dry-run` | | 预览而不执行 |
| `-v` | `--verbose` | | 启用详细（DEBUG）日志 |
| `-q` | `--quiet` | | 最小化输出（仅 WARNING） |

**示例：**

```bash
# 基础仓库分析
skill-seekers create  facebook/react

# 使用 GitHub token（更高速率限制）
skill-seekers create  facebook/react --token $GITHUB_TOKEN

# 跳过 issues 以加快抓取
skill-seekers create  facebook/react --no-issues

# 干运行预览
skill-seekers create  facebook/react --dry-run

# 仅抓取，稍后构建
skill-seekers create  facebook/react --scrape-only
```

---

### 本地 HTML 文件（通过 `create`）

从本地 HTML 文件或 HTML 文件目录提取内容。使用统一的
`create` 命令——独立的 `html` 子命令已在 v3.x 中移除。

**用途：** 将本地 HTML 文档转换为 AI 就绪的技能（适用于离线
镜像、导出的文档、wget 快照等）。

**自动检测规则：**

| 输入 | 检测为 |
|-------|-------------|
| `page.html` / `page.htm` / `page.xhtml` | `html`（单个文件） |
| 以 `.html`/`.htm`/`.xhtml` 文件为主的目录 | `html`（目录） |
| 混合目录（以代码为主） | `local`（代码库抓取器） |
| `https://.../page.html` | `web`（先抓取） |

**显式覆盖：** `--html-path PATH` 强制使用 html 抓取器模式，并优先于
自动检测。当目录中混合了代码和 HTML 文件、而你只想要 HTML 时
非常有用。

**示例：**

```bash
# 单个 HTML 文件（按扩展名自动检测）
skill-seekers create docs/index.html --name my-docs

# 整个 HTML 文件目录（自动检测）
skill-seekers create ./mirror_output/site/ --name site-mirror

# 在混合/以代码为主的目录上强制 HTML 模式
skill-seekers create ./repo/ --html-path ./repo/docs/build/html/ --name myrepo-docs

# --html-path 单独使用，无需位置参数来源
skill-seekers create --html-path ./html-export/ --name exported-docs
```

---

### install

单命令完整工作流：获取 → 抓取 → 增强 → 打包 → 上传。

**用途：** 常见工作流的端到端自动化。

**语法：**
```bash
skill-seekers install --config CONFIG [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `--config CONFIG` | 是 | 配置名称或路径 |

**标志：**

| 短 | 长 | 默认值 | 描述 |
|-------|------|---------|-------------|
| | `--destination` | output/ | 输出目录 |
| | `--no-upload` | | 跳过上传到 Claude |
| | `--unlimited` | | 移除页面限制 |
| | `--dry-run` | | 预览而不执行 |

**示例：**

```bash
# 使用预设的完整工作流
skill-seekers install --config react

# 跳过上传
skill-seekers install --config react --no-upload

# 自定义配置
skill-seekers install --config configs/my-project.json

# 干运行预览
skill-seekers install --config react --dry-run
```

**注意：** install 命令强制启用 AI 增强。

---

### install-agent

将技能安装到 AI 代理目录（Cursor、Windsurf、Cline）。

**用途：** 直接安装到 IDE AI 助手上下文目录。

**语法：**
```bash
skill-seekers install-agent SKILL_DIRECTORY --agent AGENT [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `SKILL_DIRECTORY` | 是 | 技能目录路径 |
| `--agent AGENT` | 是 | 目标代理：cursor、windsurf、cline、continue、roo、aider、bolt、kilo、kimi-code |

**标志：**

| 短 | 长 | 描述 |
|-------|------|-------------|
| | `--force` | 覆盖现有文件 |

**示例：**

```bash
# 安装到 Cursor
skill-seekers install-agent output/react/ --agent cursor

# 安装到 Windsurf
skill-seekers install-agent output/react/ --agent windsurf

# 强制覆盖
skill-seekers install-agent output/react/ --agent cursor --force
```

---

### jupyter

从 Jupyter Notebook 文件提取内容并生成技能。

**用途：** 将 `.ipynb` 笔记本转换为包含代码、markdown 和输出的 AI 就绪技能。

**语法：**
```bash
skill-seekers create <notebook.ipynb> [options]
```

**关键标志：**

| 标志 | 描述 |
|------|-------------|
| `--notebook PATH` | .ipynb 文件或目录的路径 |
| `-n, --name` | 技能名称 |
| `--from-json FILE` | 从提取的 JSON 构建 |
| `--enhance-level` | AI 增强（默认：0） |
| `--dry-run` | 预览而不执行 |

**示例：**

```bash
# 单个笔记本
skill-seekers create analysis.ipynb --name data-analysis

# 笔记本目录
skill-seekers create ./notebooks/ --name ml-tutorials
```

---

### manpage

从 Unix/Linux man 手册页提取内容并生成技能。

**用途：** 将 man 手册页转换为 AI 就绪的参考技能。

**语法：**
```bash
skill-seekers create <manpage.1> [options]
```

**关键标志：**

| 标志 | 描述 |
|------|-------------|
| `--man-names NAMES` | 逗号分隔的 man 手册页名称（例如 `ls,grep,find`） |
| `--man-path PATH` | 包含 man 手册页文件的目录路径 |
| `-n, --name` | 技能名称 |
| `--dry-run` | 预览而不执行 |

**示例：**

```bash
# 按名称（系统 man 手册页）
skill-seekers create --man-names ls,grep,find,awk --name unix-essentials

# 从目录
skill-seekers create --man-path /usr/share/man/man1/ --name section1-cmds
```

---

### multilang

多语言文档支持。

**用途：** 检测、报告并导出已抓取技能目录中包含的语言。

**语法：**
```bash
skill-seekers multilang SKILL_DIRECTORY [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `SKILL_DIRECTORY` | 是 | 技能目录路径 |

**标志：**

| 短 | 长 | 描述 |
|-------|------|-------------|
| | `--detect` | 自动检测语言 |
| | `--report` | 生成翻译报告 |
| | `--export` | 按语言导出到指定目录 |
| | `--languages` | 将 `--detect`/`--export` 限制为这些语言（空格分隔，例如 `en es fr`） |

**示例：**

```bash
# 检测技能中的语言
skill-seekers multilang output/react/ --detect

# 翻译覆盖率报告
skill-seekers multilang output/react/ --report

# 按语言导出目录树，仅英语和西班牙语
skill-seekers multilang output/react/ --export output/by-lang/ --languages en es
```

---

### notion

从 Notion 工作区提取内容。

**用途：** 通过 API 或导出将 Notion 页面和数据库转换为 AI 就绪的技能。

**语法：**
```bash
skill-seekers create [options]
```

**关键标志：**

| 标志 | 描述 |
|------|-------------|
| `--database-id ID` | 要提取的 Notion 数据库 ID |
| `--page-id ID` | 要提取的 Notion 页面 ID |
| `--notion-export-path PATH` | Notion 导出目录的路径 |
| `-n, --name` | 技能名称 |
| `--dry-run` | 预览而不执行 |

Notion 集成 token 来自 `NOTION_TOKEN` 环境变量。

**示例：**

```bash
# 通过 API
export NOTION_TOKEN=secret_...
skill-seekers create --database-id abc123 --name team-docs

# 从导出
skill-seekers create --notion-export-path ./notion-export/ --name project-wiki
```

---

### openapi

从 OpenAPI/Swagger 规范提取内容并生成技能。

**用途：** 将 API 规范转换为带端点文档的 AI 就绪参考技能。

**语法：**
```bash
skill-seekers create <openapi.yaml> [options]
```

**关键标志：**

| 标志 | 描述 |
|------|-------------|
| `--spec PATH` | OpenAPI/Swagger 规范文件的路径 |
| `--spec-url URL` | OpenAPI/Swagger 规范的 URL |
| `-n, --name` | 技能名称 |
| `--from-json FILE` | 从提取的 JSON 构建 |
| `--enhance-level` | AI 增强（默认：0） |
| `--dry-run` | 预览而不执行 |

**示例：**

```bash
# 从本地文件
skill-seekers create api/openapi.yaml --name my-api

# 从 URL
skill-seekers create --spec-url https://petstore.swagger.io/v2/swagger.json --name petstore
```

---

### package

将技能目录打包为平台特定格式。

**用途：** 为 Claude、Gemini、OpenAI 和 RAG 平台创建可上传的包。

**语法：**
```bash
skill-seekers package SKILL_DIRECTORY [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `SKILL_DIRECTORY` | 是 | 技能目录路径 |

**标志：**

| 短 | 长 | 默认值 | 描述 |
|-------|------|---------|-------------|
| | `--target` | claude | 目标平台 |
| | `--no-open` | | 不打开输出文件夹 |
| | `--skip-quality-check` | | 跳过质量检查 |
| | `--upload` | | 打包后自动上传 |
| | `--streaming` | | 大文档流式模式 |
| | `--streaming-chunk-chars` | 4000 | 每块最大字符数（流式） |
| | `--streaming-overlap-chars` | 200 | 块之间重叠（字符） |
| | `--batch-size` | 100 | 每批块数 |
| | `--chunk-for-rag` | | 启用 RAG 分块 |
| | `--chunk-tokens` | 512 | 每块最大 token 数 |
| | `--chunk-overlap-tokens` | 50 | 块之间重叠（token） |
| | `--no-preserve-code-blocks` | | 允许代码块分割 |

**支持的平台：**

| 平台 | 格式 | 标志 |
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

**示例：**

```bash
# 为 Claude 打包（默认）
skill-seekers package output/react/

# 为 Gemini 打包
skill-seekers package output/react/ --target gemini

# 为多个平台打包
for platform in claude gemini openai; do
  skill-seekers package output/react/ --target $platform
done

# 打包并上传
skill-seekers package output/react/ --target claude --upload

# 大文档流式模式
skill-seekers package output/large-docs/ --streaming
```

---

### pdf

从 PDF 提取内容并生成技能。

**用途：** 将 PDF 手册、文档和论文转换为技能。

**语法：**
```bash
skill-seekers create --pdf [options]
```

**标志：**

| 短 | 长 | 默认值 | 描述 |
|-------|------|---------|-------------|
| `-c` | `--config` | | PDF 配置 JSON 文件 |
| | `--pdf` | | 直接 PDF 文件路径 |
| `-n` | `--name` | auto | 技能名称 |
| `-d` | `--description` | auto | 描述 |
| `-o` | `--output` | auto | 输出目录 |
| | `--from-json` | | 从提取的 JSON 构建 |
| | `--enhance-level` | 0 | AI 增强（PDF 默认：0） |
| | `--api-key` | | Anthropic API 密钥 |
| | `--enhance-workflow` | | 应用工作流预设 |
| | `--enhance-stage` | | 添加内联阶段 |
| | `--var` | | 覆盖工作流变量 |
| | `--workflow-dry-run` | | 预览工作流 |
| | `--dry-run` | | 预览而不执行 |
| `-v` | `--verbose` | | 启用详细（DEBUG）日志 |
| `-q` | `--quiet` | | 最小化输出（仅 WARNING） |

**示例：**

```bash
# 直接 PDF 路径
skill-seekers create --pdf manual.pdf --name product-manual

# 使用配置文件（PDF 路径由配置中的 source 提供）
skill-seekers create --config configs/manual.json

# 启用增强
skill-seekers create --pdf manual.pdf --enhance-level 2

# 干运行预览
skill-seekers create --pdf manual.pdf --name test --dry-run
```

---

### pptx

从 PowerPoint 文件提取内容并生成技能。

**用途：** 将 `.pptx` 演示文稿转换为 AI 就绪的技能。

**语法：**
```bash
skill-seekers create <slides.pptx> [options]
```

**关键标志：**

| 标志 | 描述 |
|------|-------------|
| `--pptx PATH` | PowerPoint 文件（.pptx）的路径 |
| `-n, --name` | 技能名称 |
| `--from-json FILE` | 从提取的 JSON 构建 |
| `--enhance-level` | AI 增强（默认：0） |
| `--dry-run` | 预览而不执行 |

**示例：**

```bash
# 从演示文稿提取
skill-seekers create training-slides.pptx --name training-material

# 带增强
skill-seekers create architecture.pptx --name arch-overview --enhance-level 2
```

---

### quality

分析并评分技能文档质量。

**用途：** 打包/上传前的质量保证。

**语法：**
```bash
skill-seekers quality SKILL_DIRECTORY [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `SKILL_DIRECTORY` | 是 | 技能目录路径 |

**标志：**

| 短 | 长 | 描述 |
|-------|------|-------------|
| | `--report` | 生成详细报告 |
| | `--output` | JSON 报告的输出路径 |
| | `--threshold` | 质量门禁阈值（0-10）。设置后，技能得分低于阈值时以非零退出码退出；未设置时该命令仅报告（退出码 0） |

**示例：**

```bash
# 基础质量检查（仅报告，始终以 0 退出）
skill-seekers quality output/react/

# 详细报告
skill-seekers quality output/react/ --report

# 将报告保存为 JSON
skill-seekers quality output/react/ --output quality.json

# 质量门禁：低于阈值则失败（非零退出码）
skill-seekers quality output/react/ --threshold 7.0
```

---

### resume

从检查点恢复中断的抓取任务。

**用途：** 从抓取失败或中断处继续。

**语法：**
```bash
skill-seekers resume [JOB_ID] [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `JOB_ID` | 否 | 要恢复的任务 ID |

**标志：**

| 短 | 长 | 描述 |
|-------|------|-------------|
| | `--list` | 列出所有可恢复的任务 |
| | `--clean` | 清理旧的进度文件 |

**示例：**

```bash
# 列出可恢复的任务
skill-seekers resume --list

# 恢复特定任务
skill-seekers resume job-abc123

# 清理旧检查点
skill-seekers resume --clean
```

---

### rss

从 RSS/Atom 订阅源提取内容并生成技能。

**用途：** 将博客订阅源和新闻来源转换为 AI 就绪的技能。

**语法：**
```bash
skill-seekers create <feed.rss> [options]
```

**关键标志：**

| 标志 | 描述 |
|------|-------------|
| `--feed-url URL` | RSS/Atom 订阅源的 URL |
| `--feed-path PATH` | 本地 RSS/Atom 订阅源文件的路径 |
| `-n, --name` | 技能名称 |
| `--dry-run` | 预览而不执行 |

**示例：**

```bash
# 从 URL
skill-seekers create https://blog.example.com/feed.xml --name blog-knowledge

# 从本地文件
skill-seekers create --feed-path ./feed.rss --name feed-summaries
```

---

### scan

AI 检测项目的技术栈，并为每个检测到的框架生成一个配置，外加一个针对项目自身代码的 `<project>-codebase.json`。

**用途：** 用一条命令为现有项目引导出完整的 Skill Seekers 知识库。AI 代理会检查约 50 种清单类型（package.json、pyproject.toml、Pipfile、environment.yml、Cargo.toml、go.mod、Gemfile、build.gradle、pom.xml、composer.json、mix.exs、flake.nix、deno.json、deps.edn、dune-project、BUILD.bazel、project.godot……）、README、Dockerfile/CI、每个被采样源文件的前 2 KB，以及 git 远程 URL——然后将按框架划分的配置文件输出到指定的输出目录。每个生成的配置都会被打上 `metadata.detected_version` 标记，因此重新扫描可以报告**新增**、**版本提升**和**移除**的依赖（最后一种会被移动到 `.archived/`，绝不删除）。

**用法：**

```bash
skill-seekers scan <directory> [OPTIONS]
```

**参数：**
- `directory`（必需）- 要扫描的项目根目录（例如 `.`、`./my-react-app`）

**选项：**

| 标志 | 默认值 | 用途 |
|---|---|---|
| `--out <dir>` | `./configs/scanned/` | 生成配置的输出目录 |
| `--no-fetch` | 关闭 | 解析过程中跳过 skillseekersweb.com API 回退（离线模式） |
| `--no-generate` | 关闭 | 对未映射的检测跳过 AI 生成 |
| `--no-publish-prompt` | 关闭 | 抑制交互式的"提交到社区注册表？"提示（CI 友好） |
| `--agent <name>` | `claude`（或 `$SKILL_SEEKER_AGENT`） | 未设置 API 密钥时的 LOCAL 代理名称：`claude`、`codex`、`copilot`、`opencode`、`kimi`、`custom` |
| `--min-confidence <0-1>` | `0.4` | 丢弃置信度低于此值的 AI 检测 |
| `--max-ai-generations <N>` | `10` | 限制对未映射检测的 AI 配置生成数量。达到上限后，剩余未映射项会在报告中列为 `unresolved`，但不再触发 AI 调用。传 `0` 可完全禁用 AI 生成（等同于 `--no-generate`）。 |
| `--dry-run` | 关闭 | 预览扫描将会生成什么。不写入文件，不进行 AI 生成。解析链会被执行（成本低，为预览提供信息）。 |
| `--probe-urls` | 关闭 | AI 生成后，对每个 `base_url` / GitHub 仓库 URL 进行 HEAD 探测（5 秒超时）。遇到 4xx/5xx 时：带反馈重新询问 AI 一次。如果仍然无效：在配置上打 `metadata._url_unverified` 标记。每个生成的配置增加 5-10 秒。 |
| `--verbose`、`-v` | 关闭 | 显示每个检测及其证据 + INFO 级日志 |

**解析链**（针对每个检测）：
1. **输出目录缓存** —— 复用上次扫描留下的 `<out_dir>/<slug>.json`（只重新打 `metadata.detected_version` 标记，保留任何手动编辑）
2. **本地仓库 / 用户目录** —— 先 `./configs/<name>.json`，再 `~/.config/skill-seekers/configs/<name>.json`（每个候选都会对照规范名称列表尝试，该列表包含 CJK / 欧洲语言后缀剥离，例如 "Godot 引擎" → `godot`）
3. **社区 API** —— `https://api.skillseekersweb.com/api/configs/<name>`（除非 `--no-fetch`）
4. **AI 生成** —— 最后手段（除非 `--no-generate` 或已达 `--max-ai-generations` 上限）；会对照统一配置模式和注册表名称正则进行验证；可选地进行 URL 探测（`--probe-urls`）

**示例：**

```bash
# 引导一个 React 项目
skill-seekers scan ./my-react-app --out ./configs/scanned/
#   → react.json, vite.json, tailwind.json, my-react-app-codebase.json
#
# 然后构建任意一个生成的配置：
skill-seekers create ./configs/scanned/react.json

# 离线模式——只使用本地预设，不调用 AI 也不调用 API
skill-seekers scan ./my-project --out ./configs/ --no-fetch --no-generate

# 在 monorepo 上干运行——在投入之前预览成本
skill-seekers scan ./my-monorepo --dry-run --verbose
#   🔍 DRY RUN — no files written, no AI generation invoked.

# 在有大量未映射依赖的项目上限制 AI 生成成本
skill-seekers scan ./my-project --max-ai-generations 3

# 验证 AI 生成的 URL（更慢但能捕获幻觉）
skill-seekers scan ./my-project --probe-urls

# CI 友好——无交互式提交提示
skill-seekers scan . --out ./configs/ --no-publish-prompt

# 严格过滤低置信度检测
skill-seekers scan ./my-project --min-confidence 0.7

# 重新扫描会报告与上次扫描的差异并归档过期配置
skill-seekers scan ./my-react-app --out ./configs/scanned/
#   Diff vs previous scan:
#     + added       prisma
#     ↻ updated     react   18.2.0 → 18.3.1
#     - removed     moment
#   📦 Archived 1 stale config(s) → 2026-05-25T14-30-00Z/
```

**输出：**
- 每个已解析/已生成的检测对应一个 JSON 配置（小写 slug 文件名，例如 `react.json`）
- 始终生成一个 `<project>-codebase.json`（指向项目根目录的 `type: local` 来源）
- `out_dir/.archived/<UTC-timestamp>/` —— 来自先前扫描、不再匹配任何检测的过期配置（每次运行时移入此处；用户需要 `rm -rf` 来清理）
- stdout 上的 doctor 风格报告，显示检测结果、已解析/已生成/未解析/已归档计数，以及与上次扫描的差异

**退出码：**
- `0` —— 至少生成了一个框架配置或代码库配置
- `1` —— 目录无效或什么都没有生成（既无检测也无代码库配置——极其罕见）
- `130` —— 被中断（Ctrl+C）

**所需环境变量（可选）：**
- `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GOOGLE_API_KEY` / `MOONSHOT_API_KEY` —— API 模式检测至少需要其中一个。一个都没有时，回退到 LOCAL 代理模式。
- `GITHUB_TOKEN` —— *仅*在向社区注册表提交 AI 生成的配置时需要。扫描本身无需它即可运行（只是跳过发布提示并给出一行提示信息）。

**发布流程（原生异步，自愿参与）：**
- 扫描完成后，对每个新近 AI 生成的配置提示："Submit '<name>' to the community config registry?"
- **幂等性：** 提交前会查询 GitHub Search API，检查是否已存在标题包含该配置名称的打开 issue。如果找到，打印现有 URL 并跳过——不会重复提交。
- **重试：** 瞬时失败（速率限制、5xx）最多重试 3 次，退避间隔为 0s / 5s / 15s。
- **单次尝试超时：** 30 秒。
- 在 [skill-seekers-configs](https://github.com/yusufkaraaslan/skill-seekers-configs) 打开一个 GitHub issue——不进行直接 git 推送。

**说明：**
- `name` 不匹配 `^[a-zA-Z0-9_-]+$` 的 AI 生成配置会被拒绝并重试——注册表提交流程要求满足该正则。
- 最多读取约 64 KB 的项目信号（清单、README、Dockerfile/CI、每个被采样源文件的前 2 KB）。按类型的预算可防止一个 50 KB 的 `package.json` 挤占 README + 源文件样本。
- 源文件采样意味着实际代码会出现在提示词中。如需完全本地的流程，请使用 `skill-seekers create ./path --enhance-level 0`。

---

### scrape

抓取文档网站并生成技能。

**用途：** 将网页文档转换为技能的主要命令。

**语法：**
```bash
skill-seekers create [url] [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `url` | 否 | 基础文档 URL |

**标志：**

| 短 | 长 | 默认值 | 描述 |
|-------|------|---------|-------------|
| `-c` | `--config` | | 配置 JSON 文件 |
| `-n` | `--name` | | 技能名称 |
| `-d` | `--description` | | 描述 |
| | `--enhance-level` | 2 | AI 增强（0-3） |
| | `--api-key` | | Anthropic API 密钥 |
| | `--enhance-workflow` | | 应用工作流预设 |
| | `--enhance-stage` | | 添加内联阶段 |
| | `--var` | | 覆盖工作流变量 |
| | `--workflow-dry-run` | | 预览工作流 |
| `-i` | `--interactive` | | 交互模式 |
| | `--url` | | 基础 URL（位置参数的替代） |
| | `--max-pages` | | 最大抓取页数 |
| | `--skip-scrape` | | 使用现有数据 |
| | `--dry-run` | | 预览而不抓取 |
| | `--resume` | | 从检查点恢复 |
| | `--fresh` | | 清除检查点 |
| `-r` | `--rate-limit` | 0.5 | 速率限制（秒） |
| `-w` | `--workers` | 1 | 并行工作者（最大 10） |
| | `--async` | | 启用异步模式 |
| | `--no-rate-limit` | | 禁用速率限制 |
| | `--interactive-enhancement` | | 交互式增强 |
| `-v` | `--verbose` | | 详细输出 |
| `-q` | `--quiet` | | 静默输出 |

**示例：**

```bash
# 使用预设配置
skill-seekers create --config configs/react.json

# 快速模式
skill-seekers create --name react --url https://react.dev/

# 交互模式
skill-seekers create --interactive

# 干运行
skill-seekers create --config configs/react.json --dry-run

# 快速异步抓取
skill-seekers create --config configs/react.json --async --workers 5

# 跳过抓取，从缓存重建
skill-seekers create --config configs/react.json --skip-scrape

# 恢复中断的抓取
skill-seekers create --config configs/react.json --resume
```

---

### stream

逐块流式处理大文件。

**用途：** 针对非常大的文档站点的内存高效处理。

**语法：**
```bash
skill-seekers stream INPUT_FILE [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `INPUT_FILE` | 是 | 要流式处理的大文件 |

**标志：**

| 短 | 长 | 描述 |
|-------|------|-------------|
| | `--streaming-chunk-chars` | 每块最大字符数（默认：4000） |
| | `--streaming-overlap-chars` | 块重叠字符数（默认：200） |
| | `--batch-size` | 处理批次大小（默认：100） |
| | `--checkpoint` | 检查点文件路径 |
| | `--output` | 将收集的分块写为 JSON（可以是 `.json` 文件路径，或一个将写入 `chunks.json` 的目录） |

**示例：**

```bash
# 流式处理一个大文档文件
skill-seekers stream big-docs.md

# 自定义块大小和重叠
skill-seekers stream big-docs.md --streaming-chunk-chars 1000 --streaming-overlap-chars 100

# 保存收集的分块
skill-seekers stream big-docs.md --output chunks.json
```

---

### unified

多源抓取，合并文档 + GitHub + PDF。

**用途：** 通过冲突检测从多个来源创建单个技能。

**语法：**
```bash
skill-seekers create --config FILE [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `--config FILE` | 是 | 统一配置 JSON 文件 |

**标志：**

| 短 | 长 | 默认值 | 描述 |
|-------|------|---------|-------------|
| | `--merge-mode` | claude-enhanced | 合并模式：rule-based、claude-enhanced |
| | `--fresh` | | 清除现有数据 |
| | `--dry-run` | | 干运行模式（预览来源，不写入） |
| `-o` | `--output` | output/ | 输出目录（统一配置同样生效；结尾斜杠安全） |
| | `--enhance-level` | | 覆盖增强级别（0-3） |
| | `--api-key` | | Anthropic API 密钥（或 ANTHROPIC_API_KEY 环境变量） |
| | `--enhance-workflow` | | 应用工作流预设（可多次使用） |
| | `--enhance-stage` | | 添加内联增强阶段（name:prompt） |
| | `--var` | | 覆盖工作流变量（key=value） |
| | `--workflow-dry-run` | | 预览工作流而不执行 |
| | `--skip-codebase-analysis` | | 对 GitHub 来源跳过 C3.x 代码库分析 |

**示例：**

```bash
# 统一抓取
skill-seekers create --config configs/react-unified.json

# 全新开始
skill-seekers create --config configs/react-unified.json --fresh

# 基于规则的合并
skill-seekers create --config configs/react-unified.json --merge-mode rule-based
```

**配置格式：**
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

无需完全重新抓取即可更新文档。

**用途：** 针对已变更文档的增量更新。

**语法：**
```bash
skill-seekers update SKILL_DIRECTORY [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `SKILL_DIRECTORY` | 是 | 要更新的技能目录 |

**标志：**

| 短 | 长 | 描述 |
|-------|------|-------------|
| | `--check-changes` | 仅检查变化 |
| | `--force` | 强制更新所有文件（当前可接受但尚未实现） |
| | `--generate-package` | 在指定路径生成更新包 |
| | `--apply-update` | 应用指定路径的更新包 |

**示例：**

```bash
# 检查变化
skill-seekers update output/react/ --check-changes

# 生成更新包
skill-seekers update output/react/ --generate-package update-pkg.json

# 应用更新包
skill-seekers update output/react/ --apply-update update-pkg.json
```

---

### upload

将技能包上传到 LLM 平台或向量数据库。

**用途：** 将打包的技能部署到目标平台。

**语法：**
```bash
skill-seekers upload PACKAGE_FILE [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `PACKAGE_FILE` | 是 | 包文件路径（.zip、.tar.gz） |

**标志：**

| 短 | 长 | 默认值 | 描述 |
|-------|------|---------|-------------|
| | `--target` | claude | 目标平台 |
| | `--api-key` | | 平台 API 密钥 |
| | `--chroma-url` | | ChromaDB URL |
| | `--persist-directory` | ./chroma_db | ChromaDB 本地目录 |
| | `--embedding-function` | | Embedding 函数 |
| | `--openai-api-key` | | 用于 embeddings 的 OpenAI 密钥 |
| | `--weaviate-url` | | Weaviate URL |
| | `--use-cloud` | | 使用 Weaviate Cloud |
| | `--cluster-url` | | Weaviate Cloud 集群 URL |

**示例：**

```bash
# 上传到 Claude
skill-seekers upload output/react-claude.zip

# 上传到 Gemini
skill-seekers upload output/react-gemini.tar.gz --target gemini

# 上传到 ChromaDB
skill-seekers upload output/react-chroma.zip --target chroma

# 上传到 Weaviate Cloud
skill-seekers upload output/react-weaviate.zip --target weaviate \
  --use-cloud --cluster-url https://xxx.weaviate.network
```

---

### video

从视频教程（YouTube、Vimeo 或本地文件）提取技能。

### 用法

```bash
# 设置（首次——自动检测 GPU，安装 PyTorch + 视觉依赖）
skill-seekers create --setup

# 从 YouTube 提取
skill-seekers create --video-url  https://www.youtube.com/watch?v=VIDEO_ID --name my-skill

# 带视觉帧提取（需要先执行 --setup）
skill-seekers create --video-url  VIDEO_URL --name my-skill --visual

# 本地视频文件
skill-seekers create --video-url  /path/to/video.mp4 --name my-skill
```

### 关键标志

| 标志 | 描述 |
|------|-------------|
| `--setup` | 自动检测 GPU 并安装视觉提取依赖 |
| `--url URL` | 视频 URL（YouTube、Vimeo）或本地文件路径 |
| `--name NAME` | 输出的技能名称 |
| `--visual` | 启用视觉帧提取（对关键帧做 OCR） |
| `--vision-api` | 对低置信度帧使用 Claude Vision API 作为 OCR 回退 |

### 说明

- `--setup` 会检测 NVIDIA（CUDA）、AMD（ROCm）或纯 CPU，并安装正确的 PyTorch 变体
- 需要 `pip install skill-seekers[video]`（字幕）或 `skill-seekers[video-full]`（+ whisper + 场景检测）
- EasyOCR 不包含在 pip extras 中——它由 `--setup` 配合正确的 GPU 后端安装

---

### workflows

管理增强工作流预设。

**用途：** 列出、查看、复制、添加、移除和验证 YAML 工作流预设。

**语法：**
```bash
skill-seekers workflows ACTION [options]
```

**操作：**

| 操作 | 描述 |
|--------|-------------|
| `list` | 列出所有工作流（内置 + 用户） |
| `show` | 打印工作流的 YAML 内容 |
| `copy` | 将内置工作流复制到用户目录 |
| `add` | 安装自定义 YAML 工作流 |
| `remove` | 删除用户工作流 |
| `validate` | 验证工作流文件 |

**标志：**

| 短 | 长 | 描述 |
|-------|------|-------------|
| | `--name` | add 操作的自定义名称 |

**示例：**

```bash
# 列出所有工作流
skill-seekers workflows list

# 查看工作流内容
skill-seekers workflows show security-focus

# 复制以供编辑
skill-seekers workflows copy security-focus

# 添加自定义工作流
skill-seekers workflows add ./my-workflow.yaml

# 带自定义名称添加
skill-seekers workflows add ./workflow.yaml --name my-custom

# 移除用户工作流
skill-seekers workflows remove my-workflow

# 验证工作流
skill-seekers workflows validate security-focus
skill-seekers workflows validate ./my-workflow.yaml
```

**内置预设：**
- `default` - 标准增强
- `minimal` - 轻量增强
- `security-focus` - 安全分析（4 阶段）
- `architecture-comprehensive` - 深度架构审查（7 阶段）
- `api-documentation` - API 文档聚焦（3 阶段）

---

## 常见工作流

### 工作流 1：文档 → 技能

```bash
# 1. 估算页数（可选）
skill-seekers estimate configs/react.json

# 2. 抓取文档
skill-seekers create --config configs/react.json

# 3. 增强 SKILL.md（可选，推荐）
skill-seekers enhance output/react/

# 4. 为 Claude 打包
skill-seekers package output/react/ --target claude

# 5. 上传
skill-seekers upload output/react-claude.zip
```

### 工作流 2：GitHub → 技能

```bash
# 1. 分析仓库
skill-seekers create  facebook/react

# 2. 打包
skill-seekers package output/react/ --target claude

# 3. 上传
skill-seekers upload output/react-claude.zip
```

### 工作流 3：本地代码库 → 技能

```bash
# 1. 分析代码库
skill-seekers create ./my-project

# 2. 打包
skill-seekers package output/codebase/ --target claude

# 3. 安装到 Cursor
skill-seekers install-agent output/codebase/ --agent cursor
```

### 工作流 4：PDF → 技能

```bash
# 1. 提取 PDF
skill-seekers create --pdf manual.pdf --name product-docs

# 2. 打包
skill-seekers package output/product-docs/ --target claude
```

### 工作流 5：多源 → 技能

```bash
# 1. 创建统一配置（configs/my-project.json）
# 2. 运行统一抓取
skill-seekers create --config configs/my-project.json

# 3. 打包
skill-seekers package output/my-project/ --target claude
```

### 工作流 6：单命令完成

```bash
# 一个命令完成所有
skill-seekers install --config react --destination ./output

# 或使用 create
skill-seekers create https://docs.react.dev/ --preset standard
```

---

## 退出码

在 `cli/exit_codes.py` 中标准化：

| 码 | 含义 |
|------|---------|
| `0` | 成功（`EXIT_SUCCESS`） |
| `1` | 一般/运行时错误（`EXIT_ERROR`） |
| `2` | 参数错误 / 验证失败（`EXIT_VALIDATION`，与 argparse 一致） |
| `130` | 用户中断（Ctrl+C，`EXIT_INTERRUPT`） |

---

## 故障排除

### 命令未找到
```bash
# 确保包已安装
pip install skill-seekers

# 检查 PATH
which skill-seekers
```

### ImportError
```bash
# 以可编辑模式安装（开发）
pip install -e .
```

### 速率限制
```bash
# 增加速率限制
skill-seekers create --config react.json --rate-limit 1.0
```

### 内存不足
```bash
# 使用流式模式
skill-seekers package output/large/ --streaming
```

---

## 另请参阅

- [配置格式](CONFIG_FORMAT.md) - JSON 配置规范
- [环境变量](ENVIRONMENT_VARIABLES.md) - 完整环境变量参考
- [MCP 参考](MCP_REFERENCE.md) - MCP 工具文档

---

*获取更多帮助：`skill-seekers --help` 或 `skill-seekers <command> --help`*
