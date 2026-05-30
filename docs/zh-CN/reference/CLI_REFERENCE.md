# CLI 参考 - Skill Seekers

> **版本：** 3.6.0
> **最后更新：** 2026-03-21
> **所有 30+ CLI 命令的完整参考**

---

## 目录

- [概述](#overview)
  - [安装](#installation)
  - [全局标志](#global-flags)
  - [环境变量](#environment-variables)
- [命令参考](#command-reference)
  - [config](#config) - 配置向导
  - [create](#create) - 创建技能（自动检测来源）
  - [enhance](#enhance) - AI 增强（本地模式）
  - [enhance-status](#enhance-status) - 监控增强
  - [estimate](#estimate) - 估算页面数
  - [install](#install) - 单命令完整工作流
  - [install-agent](#install-agent) - 安装到 AI 代理
  - [multilang](#multilang) - 多语言文档
  - [package](#package) - 为平台打包技能
  - [quality](#quality) - 质量评分
  - [resume](#resume) - 恢复中断的任务
  - [stream](#stream) - 流式处理大文件
  - [update](#update) - 增量更新
  - [upload](#upload) - 上传到平台
  - [workflows](#workflows) - 管理工作流预设
- [常见工作流](#common-workflows)
- [退出码](#exit-codes)
- [故障排除](#troubleshooting)

---

## 概述

Skill Seekers 提供一个统一的 CLI，可将 17 种来源类型——文档、GitHub 仓库、PDF、视频、笔记本、维基等——转换为 AI 就绪的技能。

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

这些标志适用于大多数命令：

| 标志 | 描述 |
|------|-------------|
| `-h, --help` | 显示帮助信息并退出 |
| `--version` | 显示版本号并退出 |
| `-v, --verbose` | 启用详细（DEBUG）输出 |
| `-q, --quiet` | 最小化输出（仅 WARNING） |
| `--dry-run` | 预览而不执行 |

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
skill-seekers scan  DIR [options]
```

**参数：**

| 名称 | 必需 | 描述 |
|------|----------|-------------|
| `--directory DIR` | 是 | 要分析的目录 |
| `--output DIR` | 否 | 输出目录（默认：output/codebase/） |

**标志：**

| 短 | 长 | 默认值 | 描述 |
|-------|------|---------|-------------|
| | `--preset` | standard | 分析预设：quick、standard、comprehensive |
| | `--preset-list` | | 显示可用预设并退出 |
| | `--languages` | auto | 逗号分隔的语言（Python,JavaScript,C++） |
| | `--file-patterns` | | 逗号分隔的文件模式 |
| | `--enhance-level` | 2 | AI 增强：0=关闭，1=SKILL.md，2=+config，3=完整 |
| | `--skip-api-reference` | | 跳过 API 文档生成 |
| | `--skip-dependency-graph` | | 跳过依赖图 |
| | `--skip-patterns` | | 跳过模式检测 |
| | `--skip-test-examples` | | 跳过测试示例提取 |
| | `--skip-how-to-guides` | | 跳过操作指南生成 |
| | `--skip-config-patterns` | | 跳过配置模式提取 |
| | `--skip-docs` | | 跳过项目文档（README） |
| | `--no-comments` | | 跳过注释提取 |
| `-v` | `--verbose` | | 启用详细日志 |

**示例：**

```bash
# 使用默认值进行基础分析
skill-seekers scan  ./my-project

# 快速分析（1-2 分钟）
skill-seekers scan  ./my-project --preset quick

# 全面分析，包含所有功能
skill-seekers scan  ./my-project --preset comprehensive

# 仅特定语言
skill-seekers scan  ./my-project --languages Python,JavaScript

# 跳过重型功能以加快分析
skill-seekers scan  ./my-project --skip-dependency-graph --skip-patterns
```

**退出码：**
- `0` - 成功
- `1` - 分析失败

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
| `*.docx` | Word 文档 | `report.docx` |
| `*.epub` | EPUB | `book.epub` |
| `*.ipynb` | Jupyter Notebook | `analysis.ipynb` |
| `*.html` / `*.htm` | 本地 HTML | `page.html` |
| `*.yaml` / `*.yml` (OpenAPI) | OpenAPI/Swagger | `api-spec.yaml` |
| `*.adoc` / `*.asciidoc` | AsciiDoc | `guide.adoc` |
| `*.pptx` | PowerPoint | `slides.pptx` |
| `*.rss` / `*.atom` | RSS/Atom 订阅源 | `feed.rss` |
| `*.1`–`*.8` / `*.man` | Man 手册页 | `curl.1` |
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
| | `--max-discovery` | 1000 | 最大发现页面数 |

**示例：**

```bash
# 使用配置文件估算
skill-seekers estimate configs/react.json

# 快速估算（100 页）
skill-seekers estimate configs/react.json --max-discovery 100

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

**示例：**

```bash
# 基础仓库分析
skill-seekers create  facebook/react

# 使用 GitHub token（更高速率限制）
skill-seekers create  facebook/react --token $GITHUB_TOKEN

# 跳过 issues 以加快抓取
skill-seekers create  facebook/react --no-issues

# 仅抓取，稍后构建
skill-seekers create  facebook/react --scrape-only
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

将技能安装到 AI 代理目录（Cursor、Windsurf、Cline、Roo、Aider、Bolt、Kilo、Continue、Kimi Code）。

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

### multilang

多语言文档支持。

**用途：** 抓取并合并多语言文档。

**语法：**
```bash
skill-seekers multilang --config CONFIG [options]
```

**标志：**

| 短 | 长 | 描述 |
|-------|------|-------------|
| `-c` | `--config` | 配置 JSON 文件 |
| | `--primary` | 主要语言 |
| | `--languages` | 逗号分隔的语言 |
| | `--merge-strategy` | 合并方式：parallel、hierarchical |

**示例：**

```bash
# 多语言抓取
skill-seekers multilang --config configs/react-i18n.json

# 特定语言
skill-seekers multilang --config configs/docs.json --languages en,zh,es
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
| OpenCode | 目录 | `--target opencode` |
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

| 短 | 长 | 描述 |
|-------|------|-------------|
| `-c` | `--config` | PDF 配置 JSON 文件 |
| | `--pdf` | 直接 PDF 文件路径 |
| `-n` | `--name` | 技能名称 |
| `-d` | `--description` | 描述 |
| | `--from-json` | 从提取的 JSON 构建 |
| | `--enhance-workflow` | 应用工作流预设 |
| | `--enhance-stage` | 添加内联阶段 |
| | `--var` | 覆盖工作流变量 |
| | `--workflow-dry-run` | 预览工作流 |
| | `--enhance-level` | 0 | AI 增强（PDF 默认：0） |

**示例：**

```bash
# 直接 PDF 路径
skill-seekers create --pdf manual.pdf --name product-manual

# 使用配置文件
skill-seekers create --pdf --config configs/manual.json

# 启用增强
skill-seekers create --pdf manual.pdf --enhance-level 2
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
| | `--threshold` | 质量阈值（0-10） |

**示例：**

```bash
# 基础质量检查
skill-seekers quality output/react/

# 详细报告
skill-seekers quality output/react/ --report

# 低于阈值则失败
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
skill-seekers stream --config CONFIG [options]
```

**标志：**

| 短 | 长 | 描述 |
|-------|------|-------------|
| `-c` | `--config` | 配置 JSON 文件 |
| | `--streaming-chunk-chars` | 每块最大字符数（默认：4000） |
| | `--output` | 输出目录 |

**示例：**

```bash
# 流式处理大文档
skill-seekers stream --config configs/large-docs.json

# 自定义块大小
skill-seekers stream --config configs/large-docs.json --streaming-chunk-chars 1000
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
| | `--dry-run` | | 干运行模式 |

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
skill-seekers update --config CONFIG [options]
```

**标志：**

| 短 | 长 | 描述 |
|-------|------|-------------|
| `-c` | `--config` | 配置 JSON 文件 |
| | `--since` | 更新起始日期 |
| | `--check-only` | 仅检查更新 |

**示例：**

```bash
# 检查更新
skill-seekers update --config configs/react.json --check-only

# 更新自特定日期
skill-seekers update --config configs/react.json --since 2026-01-01

# 完整更新
skill-seekers update --config configs/react.json
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

从 YouTube、Vimeo 或本地视频文件提取内容。

**语法：**
```bash
skill-seekers create --video-url [options]
```

**标志：**

| 短 | 长 | 默认值 | 描述 |
|-------|------|---------|-------------|
| | `--url` | | YouTube/Vimeo URL |
| | `--video-file` | | 本地视频文件路径 |
| | `--playlist` | | YouTube 播放列表 URL |
| `-n` | `--name` | auto | 技能名称 |
| | `--visual` | | 启用视觉帧分析 |
| | `--enhance-level` | 2 | AI 增强（0-3） |
| | `--start-time` | | 开始时间（秒或 MM:SS 或 HH:MM:SS） |
| | `--end-time` | | 结束时间 |
| | `--setup` | | 自动检测 GPU 并安装视觉依赖 |

**示例：**

```bash
# YouTube 视频
skill-seekers create --video-url  https://www.youtube.com/watch?v=... --name tutorial

# 带视觉分析的本地视频
skill-seekers create --video-file recording.mp4 --name recording --visual

# 设置 GPU 感知依赖
skill-seekers create --setup
```

---

### word

> **已移除：** `word` 独立命令在 v3.6.0 中已移除。使用 `skill-seekers create <file.docx>` 代替。

---

### epub

> **已移除：** `epub` 独立命令在 v3.6.0 中已移除。使用 `skill-seekers create <file.epub>` 代替。

---

### jupyter

> **已移除：** `jupyter` 独立命令在 v3.6.0 中已移除。使用 `skill-seekers create <file.ipynb>` 代替。

---

### html

> **已移除：** `html` 独立命令在 v3.6.0 中已移除。使用 `skill-seekers create <file.html>` 代替。

---

### openapi

> **已移除：** `openapi` 独立命令在 v3.6.0 中已移除。使用 `skill-seekers create <spec.yaml>` 代替。

---

### asciidoc

> **已移除：** `asciidoc` 独立命令在 v3.6.0 中已移除。使用 `skill-seekers create <file.adoc>` 代替。

---

### pptx

> **已移除：** `pptx` 独立命令在 v3.6.0 中已移除。使用 `skill-seekers create <file.pptx>` 代替。

---

### rss

> **已移除：** `rss` 独立命令在 v3.6.0 中已移除。使用 `skill-seekers create <feed.rss>` 代替。

---

### manpage

> **已移除：** `manpage` 独立命令在 v3.6.0 中已移除。使用 `skill-seekers create <file.1>` 代替。

---

### confluence

从 Confluence 维基提取内容。

**语法：**
```bash
skill-seekers create [options]
```

**标志：**

| 短 | 长 | 描述 |
|-------|------|-------------|
| | `--space-key` | Confluence 空间密钥 |
| | `--base-url` | Confluence 基础 URL |
| | `--export-path` | Confluence 导出目录路径 |
| `-n` | `--name` | 技能名称 |

**示例：**

```bash
# 从 Confluence API
skill-seekers create --space-key -key DEV --base-url https://wiki.example.com --name team-wiki

# 从 Confluence 导出
skill-seekers create --export-path ./confluence-export/ --name wiki
```

---

### notion

从 Notion 页面和数据库提取内容。

**语法：**
```bash
skill-seekers create [options]
```

**标志：**

| 短 | 长 | 描述 |
|-------|------|-------------|
| | `--database-id` | Notion 数据库 ID |
| | `--page-id` | Notion 页面 ID |
| | `--export-path` | Notion 导出目录路径 |
| `-n` | `--name` | 技能名称 |

**示例：**

```bash
# 从 Notion API
skill-seekers create --database-id -id abc123 --name my-notes

# 从 Notion 导出
skill-seekers create --export-path ./notion-export/ --name notes
```

---

### chat

从 Slack/Discord 聊天记录导出提取内容。

**语法：**
```bash
skill-seekers create --chat-export-path -path DIR [options]
```

**示例：**

```bash
skill-seekers create --chat-export-path -path ./slack-export/ --name team-chat
skill-seekers create --chat-export-path -path ./discord-export/ --name server-archive
```

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
skill-seekers scan  ./my-project

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

| 码 | 含义 |
|------|---------|
| `0` | 成功 |
| `1` | 一般错误 |
| `2` | 警告（例如，估算达到上限） |
| `130` | 用户中断（Ctrl+C） |

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
