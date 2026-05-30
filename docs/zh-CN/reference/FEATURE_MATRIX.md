# Skill Seekers 功能矩阵

所有平台和技能模式的完整功能支持。

## 平台支持

| 平台 | 打包格式 | 上传 | 增强 | 需要 API 密钥 |
|----------|---------------|--------|-------------|------------------|
| **Claude AI** | ZIP | ✅ Anthropic API | ✅ Sonnet 4 | ANTHROPIC_API_KEY |
| **Google Gemini** | tar.gz | ✅ Files API | ✅ Gemini 2.0 | GOOGLE_API_KEY |
| **OpenAI ChatGPT** | ZIP | ✅ Assistants API | ✅ GPT-4o | OPENAI_API_KEY |
| **OpenCode** | 目录 | ❌ 手动 | ❌ 无 | 无 |
| **Kimi** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **DeepSeek** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **Qwen** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **OpenRouter** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **Together AI** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **Fireworks AI** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **MiniMax** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **通用 Markdown** | ZIP | ❌ 手动 | ❌ 无 | 无 |

## 来源类型支持（17 种）

| 来源类型 | CLI 命令 | 平台 | 检测 |
|-------------|------------|-----------|-----------|
| **文档（网页）** | `create <url>` | 全部 12 个 | HTTP/HTTPS URL |
| **GitHub 仓库** | `create owner/repo` | 全部 12 个 | `owner/repo` 或 github.com URL |
| **PDF** | `create file.pdf` | 全部 12 个 | `.pdf` 扩展名 |
| **Word（.docx）** | `create file.docx` | 全部 12 个 | `.docx` 扩展名 |
| **EPUB** | `create file.epub` | 全部 12 个 | `.epub` 扩展名 |
| **视频** | `create <url/file>` | 全部 12 个 | YouTube/Vimeo URL、视频扩展名 |
| **本地代码库** | `scan ./path` | 全部 12 个 | 目录路径 |
| **Jupyter Notebook** | `create file.ipynb` | 全部 12 个 | `.ipynb` 扩展名 |
| **本地 HTML** | `create file.html` | 全部 12 个 | `.html`/`.htm` 扩展名 |
| **OpenAPI/Swagger** | `create spec.yaml` | 全部 12 个 | `.yaml`/`.yml` 且含 OpenAPI 内容 |
| **AsciiDoc** | `create file.adoc` | 全部 12 个 | `.adoc`/`.asciidoc` 扩展名 |
| **PowerPoint** | `create file.pptx` | 全部 12 个 | `.pptx` 扩展名 |
| **RSS/Atom** | `create feed.rss` | 全部 12 个 | `.rss`/`.atom` 扩展名 |
| **Man 手册页** | `create cmd.1` | 全部 12 个 | `.1`–`.8`/`.man` 扩展名 |
| **Confluence** | `create --space-key` | 全部 12 个 | API 或导出目录 |
| **Notion** | `create --database-id` | 全部 12 个 | API 或导出目录 |
| **Slack/Discord** | `create --chat-export-path` | 全部 12 个 | 导出目录或 API |

## 技能模式支持

| 模式 | 描述 | 平台 | 示例配置 |
|------|-------------|-----------|-----------------|
| **文档** | 抓取 HTML 文档 | 全部 12 个 | react.json、django.json（共 14 个） |
| **GitHub** | 分析仓库 | 全部 12 个 | react_github.json、godot_github.json |
| **PDF** | 从 PDF 提取 | 全部 12 个 | example_pdf.json |
| **统一** | 多源（文档+GitHub+PDF+更多） | 全部 12 个 | react_unified.json（共 5 个） |
| **本地仓库** | 无限本地分析 | 全部 12 个 | deck_deck_go_local.json |

## CLI 命令支持

| 命令 | 平台 | 来源类型 | 多平台标志 |
|---------|-----------|-------------|---------------------|
| `create` | 全部 | 自动检测全部 17 种 | 否（输出是通用的） |
| `scan` | 全部 | 本地代码库 | 否（输出是通用的） |
| `doctor` | 全部 | N/A | 否 |
| `enhance` | Claude、Gemini、OpenAI | 全部 | ✅ `--target` |
| `enhance-status` | 全部 | N/A | 否 |
| `package` | 全部 | 全部 | ✅ `--target` |
| `upload` | Claude、Gemini、OpenAI | 全部 | ✅ `--target` |
| `install` | 全部 | 全部 | ✅ `--target` |
| `install-agent` | 全部 | 全部 | 否（代理特定路径） |
| `estimate` | 全部 | 仅文档 | 否（估算是通用的） |
| `extract-test-examples` | 全部 | 代码库 | 否 |
| `resume` | 全部 | 全部 | 否 |
| `quality` | 全部 | 全部 | 否 |
| `config` | 全部 | N/A | 否 |
| `workflows` | 全部 | N/A | 否 |
| `sync-config` | 全部 | N/A | 否 |
| `stream` | 全部 | 大文件 | 否 |
| `update` | 全部 | 文档 | 否 |
| `multilang` | 全部 | 多语言文档 | 否 |

## MCP 工具支持

| 工具 | 平台 | 技能模式 | 多平台参数 |
|------|-----------|-------------|----------------------|
| **配置工具** |
| `generate_config` | 全部 | 全部 | 否（创建通用 JSON） |
| `list_configs` | 全部 | 全部 | 否 |
| `validate_config` | 全部 | 全部 | 否 |
| `fetch_config` | 全部 | 全部 | 否 |
| **抓取工具** |
| `estimate_pages` | 全部 | 仅文档 | 否 |
| `scrape_docs` | 全部 | 文档 + 统一 | 否（输出是通用的） |
| `scrape_github` | 全部 | 仅 GitHub | 否（输出是通用的） |
| `scrape_pdf` | 全部 | 仅 PDF | 否（输出是通用的） |
| `scrape_generic` | 全部 | 10 种新来源类型 | 否（输出是通用的） |
| **打包工具** |
| `package_skill` | 全部 | 全部 | ✅ `target` 参数 |
| `upload_skill` | Claude、Gemini、OpenAI | 全部 | ✅ `target` 参数 |
| `enhance_skill` | Claude、Gemini、OpenAI | 全部 | ✅ `target` 参数 |
| `install_skill` | 全部 | 全部 | ✅ `target` 参数 |
| **拆分工具** |
| `split_config` | 全部 | 文档 + 统一 | 否 |
| `generate_router` | 全部 | 仅文档 | 否 |

## 按平台的功能对比

### Claude AI（默认）
- **格式：** YAML frontmatter + markdown
- **打包：** ZIP，包含 SKILL.md、references/、scripts/、assets/
- **上传：** POST 到 https://api.anthropic.com/v1/skills
- **增强：** Claude Sonnet 4（本地或 API）
- **独特功能：** MCP 集成、Skills API
- **限制：** 无向量存储、无文件搜索

### Google Gemini
- **格式：** 纯 markdown（无 frontmatter）
- **打包：** tar.gz，包含 system_instructions.md、references/、metadata
- **上传：** Google Files API
- **增强：** Gemini 2.0 Flash
- **独特功能：** Grounding 支持、长上下文（1M token）
- **限制：** 仅 tar.gz 格式

### OpenAI ChatGPT
- **格式：** Assistant instructions（纯文本）
- **打包：** ZIP，包含 assistant_instructions.txt、vector_store_files/、metadata
- **上传：** Assistants API + Vector Store 创建
- **增强：** GPT-4o
- **独特功能：** Vector store、file_search 工具、语义搜索
- **限制：** 需要 Assistants API 结构

### 通用 Markdown
- **格式：** 纯 markdown（通用）
- **打包：** ZIP，包含 README.md、DOCUMENTATION.md、references/
- **上传：** 无（手动分发）
- **增强：** 无
- **独特功能：** 适用于任何 LLM，无 API 依赖
- **限制：** 无上传、无增强

## 工作流覆盖

### 单源工作流
```
Config → Create → Build → [Enhance] → Package --target X → [Upload --target X]
```
**平台：** 全部 12 个
**模式：** 文档、GitHub、PDF

### 统一多源工作流
```
Config → Create All → Detect Conflicts → Merge → Build → [Enhance] → Package --target X → [Upload --target X]
```
**平台：** 全部 12 个
**模式：** 仅统一

### 完整安装工作流
```
install --target X → Fetch → Create → Enhance → Package → Upload
```
**平台：** 全部 12 个
**模式：** 全部（通过配置类型检测）

## API 密钥要求

| 平台 | 环境变量 | 密钥格式 | 用于 |
|----------|---------------------|------------|--------------|
| Claude | `ANTHROPIC_API_KEY` | `sk-ant-*` | 上传、API 增强 |
| Gemini | `GOOGLE_API_KEY` | `AIza*` | 上传、API 增强 |
| OpenAI | `OPENAI_API_KEY` | `sk-*` | 上传、API 增强 |
| Markdown | 无 | N/A | 无需 |

**注意：** 本地增强（Claude Code Max）对任何平台都不需要 API 密钥。

## 安装选项

```bash
# 核心包（仅 Claude）
pip install skill-seekers

# 附带 Gemini 支持
pip install skill-seekers[gemini]

# 附带 OpenAI 支持
pip install skill-seekers[openai]

# 附带所有平台
pip install skill-seekers[all-llms]
```

## 示例

### 为多个平台打包（同一技能）
```bash
# 抓取一次（与平台无关）
skill-seekers create --config configs/react.json

# 为所有平台打包
skill-seekers package output/react/ --target claude
skill-seekers package output/react/ --target gemini
skill-seekers package output/react/ --target openai
skill-seekers package output/react/ --target markdown

# 结果：
# - react.zip (Claude)
# - react-gemini.tar.gz (Gemini)
# - react-openai.zip (OpenAI)
# - react-markdown.zip (通用)
```

### 上传到多个平台
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIzaSy...
export OPENAI_API_KEY=sk-proj-...

skill-seekers upload react.zip --target claude
skill-seekers upload react-gemini.tar.gz --target gemini
skill-seekers upload react-openai.zip --target openai
```

### 为任何平台使用 MCP 工具
```python
# 在 Claude Code 或任何 MCP 客户端中

# 为 Gemini 打包
package_skill(skill_dir="output/react", target="gemini")

# 上传到 OpenAI
upload_skill(skill_zip="output/react-openai.zip", target="openai")

# 使用 Gemini 增强
enhance_skill(skill_dir="output/react", target="gemini", mode="api")
```

### 使用不同平台的完整工作流
```bash
# 为 Claude 安装 React 技能（默认）
skill-seekers install --config react

# 为 Gemini 安装 Django 技能
skill-seekers install --config django --target gemini

# 为 OpenAI 安装 FastAPI 技能
skill-seekers install --config fastapi --target openai

# 将 Vue 技能安装为通用 markdown
skill-seekers install --config vue --target markdown
```

### 按来源拆分统一配置
```bash
# 将多源配置拆分为单独的配置
skill-seekers split --config configs/react_unified.json --strategy source

# 创建：
# - react-documentation.json（仅文档）
# - react-github.json（仅 GitHub）

# 然后分别抓取每个
skill-seekers create --config react-documentation.json
skill-seekers create --config react-github.json

# 或并行抓取以加快速度
skill-seekers create --config react-documentation.json &
skill-seekers create --config react-github.json &
wait
```

## 验证清单

发布前，验证所有组合：

### CLI 命令 × 平台
- [ ] create → package claude → upload claude
- [ ] create → package gemini → upload gemini
- [ ] create → package openai → upload openai
- [ ] create → package markdown
- [ ] create (GitHub) → package（所有平台）
- [ ] create (PDF) → package（所有平台）
- [ ] create (unified) → package（所有平台）
- [ ] enhance claude
- [ ] enhance gemini
- [ ] enhance openai

### MCP 工具 × 平台
- [ ] package_skill target=claude
- [ ] package_skill target=gemini
- [ ] package_skill target=openai
- [ ] package_skill target=markdown
- [ ] upload_skill target=claude
- [ ] upload_skill target=gemini
- [ ] upload_skill target=openai
- [ ] enhance_skill target=claude
- [ ] enhance_skill target=gemini
- [ ] enhance_skill target=openai
- [ ] install_skill target=claude
- [ ] install_skill target=gemini
- [ ] install_skill target=openai

### 技能模式 × 平台
- [ ] 文档 → Claude
- [ ] 文档 → Gemini
- [ ] 文档 → OpenAI
- [ ] 文档 → Markdown
- [ ] GitHub → 所有平台
- [ ] PDF → 所有平台
- [ ] 统一 → 所有平台
- [ ] 本地仓库 → 所有平台

## 平台特定说明

### Claude AI
- **最适合：** 通用技能、MCP 集成
- **何时使用：** 默认选择，最佳 MCP 支持
- **文件大小限制：** 每个技能包 25 MB

### Google Gemini
- **最适合：** 大上下文技能、grounding 支持
- **何时使用：** 需要长上下文（1M token）、grounding 功能
- **文件大小限制：** 每次上传 100 MB

### OpenAI ChatGPT
- **最适合：** 向量搜索、语义检索
- **何时使用：** 需要在文档间进行语义搜索
- **文件大小限制：** 每个向量存储 512 MB

### 通用 Markdown
- **最适合：** 通用兼容性、无 API 依赖
- **何时使用：** 使用非 Claude/Gemini/OpenAI 的 LLM、离线使用
- **分发：** 手动 - 直接共享 ZIP 文件

## 常见问题

**Q：我可以打包一次并上传到多个平台吗？**
A：不可以。每个平台需要平台特定的打包格式。你必须：
1. 抓取一次（通用）
2. 为每个平台单独打包（`--target` 标志）
3. 上传每个平台特定的包

**Q：我需要为每个平台单独抓取吗？**
A：不需要！抓取是与平台无关的。抓取一次，然后为多个平台打包。

**Q：我应该选择哪个平台？**
A：
- **Claude：** 最佳默认选择，出色的 MCP 集成
- **Gemini：** 如果你需要长上下文（1M token）或 grounding
- **OpenAI：** 如果你需要向量搜索和语义检索
- **Markdown：** 如果你需要通用兼容性或离线使用

**Q：我可以为不同平台增强技能吗？**
A：可以！增强会添加平台特定的格式：
- Claude：YAML frontmatter + markdown
- Gemini：纯 markdown 加系统指令
- OpenAI：纯文本 assistant instructions

**Q：所有技能模式都适用于所有平台吗？**
A：是的！所有 17 种来源类型和所有 5 种技能模式（文档、GitHub、PDF、统一、本地仓库）都适用于全部 12 个平台。

## 另请参阅

- **[README.md](../README.md)** - 完整用户文档
- **[UNIFIED_SCRAPING.md](UNIFIED_SCRAPING.md)** - 多源抓取指南
- **[ENHANCEMENT.md](ENHANCEMENT.md)** - AI 增强指南
- **[UPLOAD_GUIDE.md](UPLOAD_GUIDE.md)** - 上传说明
- **[MCP_SETUP.md](MCP_SETUP.md)** - MCP 服务器设置
