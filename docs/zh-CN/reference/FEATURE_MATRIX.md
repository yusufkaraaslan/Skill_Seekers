# Skill Seekers 功能矩阵

所有平台和技能模式的完整功能支持。

## 平台支持

| 平台 | 打包格式 | 上传 | 增强 | 需要 API 密钥 |
|------|----------|------|------|---------------|
| **Claude AI** | ZIP | ✅ Anthropic API | ✅ Sonnet 4 | ANTHROPIC_API_KEY |
| **Google Gemini** | tar.gz | ✅ Files API | ✅ Gemini 2.0 | GOOGLE_API_KEY |
| **OpenAI ChatGPT** | ZIP | ✅ Assistants API | ✅ GPT-4o | OPENAI_API_KEY |
| **MiniMax** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **OpenCode** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **Kimi** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **DeepSeek** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **Qwen** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **OpenRouter** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **Together AI** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **Fireworks AI** | ZIP | ❌ 手动 | ❌ 无 | 无 |
| **IBM Bob** | 目录 | ❌ 手动 | ❌ 无 | 无 |
| **LangChain** | JSON | ❌ 手动 | ❌ 无 | 无 |
| **LlamaIndex** | JSON | ❌ 手动 | ❌ 无 | 无 |
| **Haystack** | JSON | ❌ 手动 | ❌ 无 | 无 |
| **Pinecone** | 向量 | ❌ 手动 | ❌ 无 | PINECONE_API_KEY |
| **Weaviate** | 向量 | ❌ 手动 | ❌ 无 | 无 |
| **Chroma** | 向量 | ❌ 手动 | ❌ 无 | 无 |
| **FAISS** | 索引 | ❌ 手动 | ❌ 无 | 无 |
| **Qdrant** | 向量 | ❌ 手动 | ❌ 无 | 无 |
| **通用 Markdown** | ZIP | ❌ 手动 | ❌ 无 | 无 |

## 技能模式支持

| 模式 | 描述 | 平台 | CLI 命令 | `create` 检测 |
|------|------|------|----------|---------------|
| **文档** | 抓取 HTML 文档 | 全部 21 个 | `scrape` | `https://...` URL |
| **GitHub** | 分析仓库 | 全部 21 个 | `github` | `owner/repo` 或 github.com URL |
| **PDF** | 从 PDF 提取 | 全部 21 个 | `pdf` | `.pdf` 扩展名 |
| **Word** | 从 DOCX 提取 | 全部 21 个 | `word` | `.docx` 扩展名 |
| **EPUB** | 从 EPUB 提取 | 全部 21 个 | `epub` | `.epub` 扩展名 |
| **视频** | 视频转录 | 全部 21 个 | `video` | YouTube/Vimeo URL、视频扩展名 |
| **本地仓库** | 本地代码库分析 | 全部 21 个 | `analyze` | 目录路径 |
| **Jupyter** | 从 notebook 提取 | 全部 21 个 | `jupyter` | `.ipynb` 扩展名 |
| **HTML** | 提取本地 HTML 文件 | 全部 21 个 | `html` | `.html`/`.htm` 扩展名 |
| **OpenAPI** | 提取 API 规范 | 全部 21 个 | `openapi` | `.yaml`/`.yml` 且含 OpenAPI 内容 |
| **AsciiDoc** | 提取 AsciiDoc 文件 | 全部 21 个 | `asciidoc` | `.adoc`/`.asciidoc` 扩展名 |
| **PowerPoint** | 从 PPTX 提取 | 全部 21 个 | `pptx` | `.pptx` 扩展名 |
| **RSS/Atom** | 从订阅源提取 | 全部 21 个 | `rss` | `.rss`/`.atom` 扩展名 |
| **Man 手册页** | 提取 man 手册页 | 全部 21 个 | `manpage` | `.1`-`.8`/`.man` 扩展名 |
| **Confluence** | 从 Confluence 提取 | 全部 21 个 | `confluence` | API 或导出目录 |
| **Notion** | 从 Notion 提取 | 全部 21 个 | `notion` | API 或导出目录 |
| **聊天** | 提取 Slack/Discord | 全部 21 个 | `chat` | 导出目录或 API |
| **统一** | 多源组合 | 全部 21 个 | `unified` | N/A（由配置驱动） |

## CLI 命令支持

| 命令 | 平台 | 技能模式 | 多平台标志 | 可选依赖 |
|------|------|----------|------------|----------|
| `scrape` | 全部 | 仅文档 | 否（输出是通用的） | 无 |
| `github` | 全部 | 仅 GitHub | 否（输出是通用的） | 无 |
| `pdf` | 全部 | 仅 PDF | 否（输出是通用的） | `[pdf]` |
| `word` | 全部 | 仅 Word | 否（输出是通用的） | `[word]` |
| `epub` | 全部 | 仅 EPUB | 否（输出是通用的） | `[epub]` |
| `video` | 全部 | 仅视频 | 否（输出是通用的） | `[video]` |
| `analyze` | 全部 | 仅本地 | 否（输出是通用的） | 无 |
| `jupyter` | 全部 | 仅 Jupyter | 否（输出是通用的） | `[jupyter]` |
| `html` | 全部 | 仅 HTML | 否（输出是通用的） | 无 |
| `openapi` | 全部 | 仅 OpenAPI | 否（输出是通用的） | `[openapi]` |
| `asciidoc` | 全部 | 仅 AsciiDoc | 否（输出是通用的） | `[asciidoc]` |
| `pptx` | 全部 | 仅 PPTX | 否（输出是通用的） | `[pptx]` |
| `rss` | 全部 | 仅 RSS | 否（输出是通用的） | `[rss]` |
| `manpage` | 全部 | 仅 man 手册页 | 否（输出是通用的） | 无 |
| `confluence` | 全部 | 仅 Confluence | 否（输出是通用的） | `[confluence]` |
| `notion` | 全部 | 仅 Notion | 否（输出是通用的） | `[notion]` |
| `chat` | 全部 | 仅聊天 | 否（输出是通用的） | `[chat]` |
| `unified` | 全部 | 仅统一 | 否（输出是通用的） | 因来源而异 |
| `scan` | 全部 | 项目引导 | 否（输出是通用的） | 无（使用现有 `AgentClient`） |
| `enhance` | Claude、Gemini、OpenAI | 全部 | ✅ `--target` | 无 |
| `package` | 全部 | 全部 | ✅ `--target` | 无 |
| `upload` | Claude、Gemini、OpenAI | 全部 | ✅ `--target` | 无 |
| `estimate` | 全部 | 仅文档 | 否（估算是通用的） | 无 |
| `install` | 全部 | 全部 | ✅ `--target` | 无 |
| `install-agent` | 全部 | 全部 | 否（智能体特定路径） | 无 |

## MCP 工具支持

| 工具 | 平台 | 技能模式 | 多平台参数 |
|------|------|----------|------------|
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
| `scrape_generic` | 全部 | 10 种新类型 | 否（输出是通用的） |
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
Config → Scrape → Build → [Enhance] → Package --target X → [Upload --target X]
```
**平台：** 全部 21 个
**模式：** 文档、GitHub、PDF

### 统一多源工作流
```
Config → Scrape All → Detect Conflicts → Merge → Build → [Enhance] → Package --target X → [Upload --target X]
```
**平台：** 全部 21 个
**模式：** 仅统一

### 完整安装工作流
```
install --target X → Fetch → Scrape → Enhance → Package → Upload
```
**平台：** 全部 21 个
**模式：** 全部（通过配置类型检测）

## API 密钥要求

| 平台 | 环境变量 | 密钥格式 | 用于 |
|------|----------|----------|------|
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
python -m skill_seekers.cli.split_config configs/react_unified.json --strategy source

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
- [ ] scrape → package claude → upload claude
- [ ] scrape → package gemini → upload gemini
- [ ] scrape → package openai → upload openai
- [ ] scrape → package markdown
- [ ] github → package（所有平台）
- [ ] pdf → package（所有平台）
- [ ] unified → package（所有平台）
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
- [ ] Word → 所有平台
- [ ] EPUB → 所有平台
- [ ] 视频 → 所有平台
- [ ] 本地仓库 → 所有平台
- [ ] Jupyter → 所有平台
- [ ] HTML → 所有平台
- [ ] OpenAPI → 所有平台
- [ ] AsciiDoc → 所有平台
- [ ] PPTX → 所有平台
- [ ] RSS → 所有平台
- [ ] Man 手册页 → 所有平台
- [ ] Confluence → 所有平台
- [ ] Notion → 所有平台
- [ ] 聊天 → 所有平台
- [ ] 统一 → 所有平台

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
- **MiniMax/Kimi/DeepSeek/Qwen：** 适合中文 LLM 生态系统兼容
- **OpenRouter/Together/Fireworks：** 适合多模型路由或开源模型访问
- **Markdown：** 如果你需要通用兼容性或离线使用

**Q：我可以为不同平台增强技能吗？**
A：可以！增强会添加平台特定的格式：
- Claude：YAML frontmatter + markdown
- Gemini：纯 markdown 加系统指令
- OpenAI：纯文本 assistant instructions

**Q：所有技能模式都适用于所有平台吗？**
A：是的！所有 18 种来源类型都适用于全部 21 个平台（Claude、Gemini、OpenAI、MiniMax、OpenCode、Kimi、DeepSeek、Qwen、OpenRouter、Together AI、Fireworks AI、IBM Bob、LangChain、LlamaIndex、Haystack、Pinecone、Weaviate、Chroma、FAISS、Qdrant 和 Markdown）。

## 另请参阅

- **[README.md](../README.md)** - 完整用户文档
- **[UNIFIED_SCRAPING.md](UNIFIED_SCRAPING.md)** - 多源抓取指南
- **[ENHANCEMENT.md](ENHANCEMENT.md)** - AI 增强指南
- **[UPLOAD_GUIDE.md](UPLOAD_GUIDE.md)** - 上传说明
- **[MCP_SETUP.md](MCP_SETUP.md)** - MCP 服务器设置
