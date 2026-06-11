# 抓取指南

> **Skill Seekers v3.6.0**
> **所有抓取选项的完整指南**

---

## 概述

Skill Seekers 可以从 **17 种类型的来源**中提取知识：

| 来源 | 命令 | 适用于 |
|--------|---------|----------|
| **文档** | `create <url>` | 网页文档、教程、API 参考 |
| **GitHub** | `create <repo>` | 源代码、issues、releases |
| **PDF** | `create <file.pdf>` | 手册、论文、报告 |
| **本地** | `create <./path>` | 你的项目、内部代码 |
| **Word** | `create <file.docx>` | 报告、规格说明 |
| **EPUB** | `create <file.epub>` | 电子书、长篇文档 |
| **视频** | `create <url/file>` | 教程、演示 |
| **Jupyter** | `create <file.ipynb>` | 数据科学、实验 |
| **本地 HTML** | `create <file.html>` | 离线文档、保存的页面 |
| **OpenAPI** | `create <spec.yaml>` | API 规范、Swagger 文档 |
| **AsciiDoc** | `create <file.adoc>` | 技术文档 |
| **PowerPoint** | `create <file.pptx>` | 幻灯片、演示文稿 |
| **RSS/Atom** | `create <feed.rss>` | 博客订阅、新闻来源 |
| **Man 手册页** | `create <cmd.1>` | Unix 命令文档 |
| **Confluence** | `confluence` | 团队维基、知识库 |
| **Notion** | `notion` | 工作区文档、数据库 |
| **Slack/Discord** | `chat` | 聊天记录、讨论 |

---

## 文档抓取

### 基本用法

```bash
# 自动检测并抓取
skill-seekers create https://docs.react.dev/

# 使用自定义名称
skill-seekers create https://docs.react.dev/ --name react-docs

# 使用描述
skill-seekers create https://docs.react.dev/ \
  --description "React JavaScript library documentation"
```

### 使用预设配置

```bash
# 列出可用预设
skill-seekers estimate --all

# 使用预设
skill-seekers create --config react
skill-seekers create --config django
skill-seekers create --config fastapi
```

**可用预设：** 查看仓库中的 `configs/` 目录。

### 自定义配置

所有配置必须使用带 `sources` 数组的统一格式（自 v2.11.0 起）：

```bash
# 创建配置文件
cat > configs/my-docs.json << 'EOF'
{
  "name": "my-framework",
  "description": "My framework documentation",
  "sources": [
    {
      "type": "documentation",
      "base_url": "https://docs.example.com/",
      "max_pages": 200,
      "rate_limit": 0.5,
      "selectors": {
        "main_content": "article",
        "title": "h1"
      },
      "url_patterns": {
        "include": ["/docs/", "/api/"],
        "exclude": ["/blog/", "/search"]
      }
    }
  ]
}
EOF

# 使用配置
skill-seekers create --config configs/my-docs.json
```

> **注意：** 在 `selectors` 中省略 `main_content` 可让 Skill Seekers 自动检测
> 最佳内容元素（`main`、`article`、`div[role="main"]` 等）。

查看 [Config Format](../reference/CONFIG_FORMAT.md) 获取所有选项。

### 高级选项

```bash
# 限制页面数（用于测试）
skill-seekers create <url> --max-pages 50

# 调整速率限制
skill-seekers create <url> --rate-limit 1.0

# 并行工作者（更快）
skill-seekers create <url> --workers 5 --async

# 试运行（预览）
skill-seekers create <url> --dry-run

# 恢复中断的任务
skill-seekers create <url> --resume

# 重新开始（忽略缓存）
skill-seekers create <url> --fresh
```

---

## GitHub 仓库抓取

### 基本用法

```bash
# 通过仓库名称
skill-seekers create facebook/react

# 使用显式标志
skill-seekers create  facebook/react

# 使用自定义名称
skill-seekers create  facebook/react --name react-source
```

### 使用 GitHub Token

```bash
# 设置 token 以获得更高的速率限制
export GITHUB_TOKEN=ghp_...

# 使用 token
skill-seekers create  facebook/react
```

**使用 token 的优势：**
- 每小时 5000 次请求，而非 60 次
- 可访问私有仓库
- 更高的 GraphQL 限制

### 提取内容

| 数据 | 默认 | 禁用标志 |
|------|---------|-----------------|
| 源代码 | ✅ | `--scrape-only` |
| README | ✅ | - |
| Issues | ✅ | `--no-issues` |
| Releases | ✅ | `--no-releases` |
| Changelog | ✅ | `--no-changelog` |

### 控制抓取内容

```bash
# 跳过 issues（更快）
skill-seekers create  facebook/react --no-issues

# 限制 issues 数量
skill-seekers create  facebook/react --max-issues 50

# 仅抓取（不构建）
skill-seekers create  facebook/react --scrape-only

# 非交互模式（CI/CD）
skill-seekers create  facebook/react --non-interactive
```

---

## PDF 提取

### 基本用法

```bash
# 直接文件
skill-seekers create manual.pdf --name product-manual

# 使用显式命令
skill-seekers create --pdf manual.pdf --name docs
```

### 扫描版 PDF 的 OCR

```bash
# 启用 OCR
skill-seekers create --pdf scanned.pdf --ocr
```

**要求：**
```bash
pip install skill-seekers[pdf-ocr]
# 还需要: tesseract-ocr（系统包）
```

### 受密码保护的 PDF

```bash
# 在配置文件中
{
  "name": "secure-docs",
  "pdf_path": "protected.pdf",
  "password": "secret123"
}
```

### 页面范围

```bash
# 提取特定页面（通过配置）
{
  "pdf_path": "manual.pdf",
  "page_range": [1, 100]
}
```

---

## 本地代码库分析

### 基本用法

```bash
# 当前目录
skill-seekers create .

# 特定目录
skill-seekers create ./my-project

# 使用显式命令
skill-seekers create ./my-project
```

### 分析预设

```bash
# 快速分析（1-2 分钟）
skill-seekers create ./my-project --preset quick

# 标准分析（5-10 分钟）- 默认
skill-seekers create ./my-project --preset standard

# 全面分析（20-60 分钟）
skill-seekers create ./my-project --preset comprehensive
```

### 分析内容

| 功能 | 快速 | 标准 | 全面 |
|---------|-------|----------|---------------|
| 代码结构 | ✅ | ✅ | ✅ |
| API 提取 | ✅ | ✅ | ✅ |
| 注释 | - | ✅ | ✅ |
| 模式 | - | ✅ | ✅ |
| 测试示例 | - | - | ✅ |
| 操作指南 | - | - | ✅ |
| 配置模式 | - | - | ✅ |

### 语言过滤

```bash
# 特定语言
skill-seekers create ./my-project \
  --languages Python,JavaScript

# 文件模式
skill-seekers create ./my-project \
  --file-patterns "*.py,*.js"
```

### 跳过功能

```bash
# 跳过重型功能
skill-seekers create ./my-project \
  --skip-dependency-graph \
  --skip-patterns \
  --skip-test-examples
```

---

## 视频提取

### 基本用法

```bash
# YouTube 视频
skill-seekers create https://www.youtube.com/watch?v=dQw4w9WgXcQ

# 本地视频文件
skill-seekers create presentation.mp4

# 使用显式命令
skill-seekers create --video-url  https://www.youtube.com/watch?v=...
```

### 视觉分析

```bash
# 安装完整视频支持（包含 Whisper + 场景检测）
pip install skill-seekers[video-full]
skill-seekers create --setup  # 自动检测 GPU 并安装 PyTorch

# 带视觉分析提取
skill-seekers create --video-url <url> --visual
```

**要求：**
```bash
pip install skill-seekers[video]        # 仅转录
pip install skill-seekers[video-full]   # + Whisper、场景检测
```

---

## Word 文档提取

### 基本用法

```bash
# 从 .docx 提取
skill-seekers create report.docx --name project-report

# 使用显式命令
skill-seekers create report.docx
```

**处理内容：** 文本、表格、标题、图片、嵌入式元数据。

---

## EPUB 提取

### 基本用法

```bash
# 从 .epub 提取
skill-seekers create programming-guide.epub --name guide

# 使用显式命令
skill-seekers create programming-guide.epub
```

**处理内容：** 章节、元数据、目录、嵌入式图片。

---

## Jupyter Notebook 提取

### 基本用法

```bash
# 从 .ipynb 提取
skill-seekers create analysis.ipynb --name data-analysis

# 使用显式命令
skill-seekers create analysis.ipynb
```

**要求：**
```bash
pip install skill-seekers[jupyter]
```

**提取内容：** Markdown 单元格、代码单元格、单元格输出、执行顺序。

---

## 本地 HTML 提取

### 基本用法

```bash
# 从 .html 提取
skill-seekers create docs.html --name offline-docs

# 使用显式命令
skill-seekers create docs.html
```

**处理内容：** 完整 HTML 解析、文本提取、链接解析。

---

## OpenAPI/Swagger 提取

### 基本用法

```bash
# 从 OpenAPI 规范提取
skill-seekers create api-spec.yaml --name my-api

# 使用显式命令
skill-seekers create api-spec.yaml
```

**提取内容：** 端点、请求/响应模式、认证信息、示例。

---

## AsciiDoc 提取

### 基本用法

```bash
# 从 .adoc 提取
skill-seekers create guide.adoc --name dev-guide

# 使用显式命令
skill-seekers create guide.adoc
```

**要求：**
```bash
pip install skill-seekers[asciidoc]
```

**处理内容：** 章节、代码块、表格、交叉引用、包含文件。

---

## PowerPoint 提取

### 基本用法

```bash
# 从 .pptx 提取
skill-seekers create slides.pptx --name presentation

# 使用显式命令
skill-seekers create slides.pptx
```

**要求：**
```bash
pip install skill-seekers[pptx]
```

**提取内容：** 幻灯片文本、演讲者备注、图片、表格、幻灯片顺序。

---

## RSS/Atom 订阅提取

### 基本用法

```bash
# 从 RSS 订阅源提取
skill-seekers create blog.rss --name blog-archive

# Atom 订阅源
skill-seekers create updates.atom --name updates

# 使用显式命令
skill-seekers create blog.rss
```

**要求：**
```bash
pip install skill-seekers[rss]
```

**提取内容：** 文章、标题、日期、作者、分类。

---

## Man 手册页提取

### 基本用法

```bash
# 从 man 手册页提取
skill-seekers create curl.1 --name curl-manual

# 使用显式命令
skill-seekers create curl.1
```

**处理内容：** 各节（NAME、SYNOPSIS、DESCRIPTION、OPTIONS 等）、格式。

---

## Confluence 维基提取

### 基本用法

```bash
# 从 Confluence API
skill-seekers create \
  --conf-base-url https://wiki.example.com \
  --space-key DEV \
  --name team-docs

# 从 Confluence 导出目录
skill-seekers create --conf-export-path ./confluence-export/
```

**要求：**
```bash
pip install skill-seekers[confluence]
```

**提取内容：** 页面、页面树、附件、标签、空间。

---

## Notion 提取

### 基本用法

```bash
# 从 Notion API
export NOTION_API_KEY=secret_...
skill-seekers create --database-id abc123 --name product-wiki

# 从 Notion 导出目录
skill-seekers create --notion-export-path ./notion-export/
```

**要求：**
```bash
pip install skill-seekers[notion]
```

**提取内容：** 页面、数据库、块、属性、关联。

---

## Slack/Discord 聊天提取

### 基本用法

```bash
# 从 Slack 导出
skill-seekers create --chat-export-path  slack-export/ --name team-discussions

# 从 Discord 导出
skill-seekers create --chat-export-path  discord-export/ --name server-archive
```

**要求：**
```bash
pip install skill-seekers[chat]
```

**提取内容：** 消息、线程、频道、表情回应、附件。

---

## 常见抓取模式

### 模式 1：先测试

```bash
# 试运行预览
skill-seekers create <source> --dry-run

# 小规模测试抓取
skill-seekers create <source> --max-pages 10

# 完整抓取
skill-seekers create <source>
```

### 模式 2：迭代开发

```bash
# 不增强抓取（快速）
skill-seekers create <source> --enhance-level 0

# 检查输出
ls output/my-skill/
cat output/my-skill/SKILL.md

# 稍后增强
skill-seekers enhance output/my-skill/
```

### 模式 3：并行处理

```bash
# 快速异步抓取
skill-seekers create <url> --async --workers 5

# 更快（注意速率限制）
skill-seekers create <url> --async --workers 10 --rate-limit 0.2
```

### 模式 4：恢复能力

```bash
# 开始抓取
skill-seekers create <source>
# ...中断...

# 稍后恢复
skill-seekers resume --list
skill-seekers resume <job-id>
```

---

## 抓取故障排除

### "未提取到内容"

**问题：** CSS 选择器错误

**解决方案：**
```bash
# 首先，尝试不指定 main_content 选择器（自动检测）
# 抓取器会依次尝试：main、div[role="main"]、article、.content 等
skill-seekers create <url> --dry-run

# 如果自动检测失败，查找正确的选择器：
curl -s <url> | grep -i 'article\|main\|content'

# 然后在配置的 source 中指定它：
{
  "sources": [{
    "type": "documentation",
    "base_url": "https://...",
    "selectors": {
      "main_content": "div.content"
    }
  }]
}
```

### "超出速率限制"

**问题：** 请求过多

**解决方案：**
```bash
# 减速
skill-seekers create <url> --rate-limit 2.0

# 或对 GitHub 仓库使用 token
export GITHUB_TOKEN=ghp_...
```

### "页面过多"

**问题：** 网站比预期大

**解决方案：**
```bash
# 先估算
skill-seekers estimate configs/my-config.json

# 限制页面数
skill-seekers create <url> --max-pages 100

# 调整 URL 模式
{
  "url_patterns": {
    "exclude": ["/blog/", "/archive/", "/search"]
  }
}
```

### "内存错误"

**问题：** 网站太大，内存不足

**解决方案：**
```bash
# 使用流式模式
skill-seekers create <url> --streaming

# 或更小的分块
skill-seekers create <url> --chunk-tokens 500
```

---

## 性能提示

| 提示 | 命令 | 影响 |
|-----|---------|--------|
| 使用预设 | `--config react` | 更快的设置 |
| 异步模式 | `--async --workers 5` | 快 3-5 倍 |
| 跳过增强 | `--enhance-level 0` | 跳过 60 秒 |
| 使用缓存 | `--skip-scrape` | 即时重建 |
| 恢复 | `--resume` | 继续中断的任务 |

---

## 下一步

- [增强指南](03-enhancement.md) - 提升 skill 质量
- [打包指南](04-packaging.md) - 导出到平台
- [Config Format](../reference/CONFIG_FORMAT.md) - 高级配置
