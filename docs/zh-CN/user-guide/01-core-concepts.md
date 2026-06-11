# 核心概念

> **Skill Seekers v3.6.0**
> **了解 Skill Seekers 的工作原理**

---

## 概述

Skill Seekers 将文档、代码和内容转换为 AI 系统可以有效使用的**结构化知识资产**。它支持 **18 种来源类型**，包括文档站点、GitHub 仓库、PDF、视频、笔记本、维基等等。

```
原始内容 → Skill Seekers → AI 就绪的 Skill
     ↓                              ↓
  (文档、代码、PDF、          (SKILL.md +
   视频、笔记本、              参考文件)
   维基、订阅源等)
```

---

## 什么是 Skill？

**Skill** 是一个结构化的知识包，包含以下内容：

```
output/my-skill/
├── SKILL.md              # 主文件（通常 400+ 行）
├── references/           # 分类内容
│   ├── index.md         # 导航
│   ├── getting_started.md
│   ├── api_reference.md
│   └── ...
├── .skill-seekers/      # 元数据
└── assets/              # 图片、下载文件
```

### SKILL.md 结构

```markdown
# My Framework Skill

## Overview
Brief description of the framework...

## Quick Reference
Common commands and patterns...

## Categories
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Guides](#guides)

## Getting Started
### Installation
```bash
npm install my-framework
```

### First Steps
...

## API Reference
...
```

### 为什么采用这种结构？

| 元素 | 用途 |
|---------|---------|
| **Overview** | 为 AI 提供快速上下文 |
| **Quick Reference** | 快速查看常用模式 |
| **Categories** | 有组织的深度内容 |
| **Code Examples** | 可直接复制粘贴的代码片段 |

---

## 源类型

Skill Seekers 支持 **17 种类型的来源**：

### 1. 文档网站

**类型：** 基于 Web 的文档（ReadTheDocs、Docusaurus、GitBook 等）

**示例：**
- React 文档 (react.dev)
- Django 文档 (docs.djangoproject.com)
- Kubernetes 文档 (kubernetes.io)

**命令：**
```bash
skill-seekers create https://docs.example.com/
```

**适用于：**
- 框架文档
- API 参考
- 教程和指南

---

### 2. GitHub 仓库

**类型：** 经过分析的源代码仓库

**提取内容：**
- 代码结构和 API
- README 和文档
- Issues 和 Discussions
- Releases 和 Changelog

**命令：**
```bash
skill-seekers create owner/repo
skill-seekers create  owner/repo
```

**适用于：**
- 理解代码库
- API 实现细节
- 贡献指南

---

### 3. PDF 文档

**类型：** PDF 手册、论文、文档

**处理能力：**
- 文本提取
- 扫描版 PDF 的 OCR
- 表格提取
- 图片提取

**命令：**
```bash
skill-seekers create manual.pdf
skill-seekers create --pdf manual.pdf
```

**适用于：**
- 产品手册
- 研究论文
- 遗留文档

---

### 4. 本地代码库

**类型：** 你的本地项目和代码

**分析内容：**
- 源代码结构
- 注释和文档字符串
- 测试文件
- 配置模式

**命令：**
```bash
skill-seekers create ./my-project
skill-seekers scan  ./my-project
```

**适用于：**
- 你自己的项目
- 内部工具
- 代码审查准备

---

### 5. Word 文档

**类型：** Microsoft Word（.docx）文件

**命令：**
```bash
skill-seekers create report.docx
```

---

### 6. EPUB 电子书

**类型：** EPUB 电子书文件

**命令：**
```bash
skill-seekers create book.epub
```

---

### 7. 视频

**类型：** YouTube、Vimeo 或本地视频文件（转录 + 视觉分析）

**命令：**
```bash
skill-seekers create https://www.youtube.com/watch?v=...
skill-seekers create --video-url  https://www.youtube.com/watch?v=...
```

---

### 8. Jupyter Notebook

**类型：** 包含代码、markdown 和输出的 `.ipynb` 笔记本文件

**命令：**
```bash
skill-seekers create analysis.ipynb
skill-seekers create analysis.ipynb
```

---

### 9. 本地 HTML 文件

**类型：** 磁盘上的 HTML/HTM 文件

**命令：**
```bash
skill-seekers create page.html
skill-seekers create page.html
```

---

### 10. OpenAPI/Swagger 规范

**类型：** OpenAPI YAML/JSON 规范

**命令：**
```bash
skill-seekers create api-spec.yaml
skill-seekers create api-spec.yaml
```

---

### 11. AsciiDoc

**类型：** AsciiDoc（.adoc、.asciidoc）文件

**命令：**
```bash
skill-seekers create guide.adoc
skill-seekers create guide.adoc
```

---

### 12. PowerPoint 演示文稿

**类型：** Microsoft PowerPoint（.pptx）文件

**命令：**
```bash
skill-seekers create slides.pptx
skill-seekers create slides.pptx
```

---

### 13. RSS/Atom 订阅

**类型：** RSS 或 Atom 订阅源文件

**命令：**
```bash
skill-seekers create feed.rss
skill-seekers create feed.rss
```

---

### 14. Man 手册页

**类型：** Unix 手册页（.1 至 .8、.man）

**命令：**
```bash
skill-seekers create grep.1
skill-seekers create grep.1
```

---

### 15. Confluence 维基

**类型：** Atlassian Confluence 空间（通过 API 或导出）

**命令：**
```bash
skill-seekers create --conf-base-url https://wiki.example.com --space-key DEV
```

---

### 16. Notion 工作区

**类型：** Notion 页面和数据库（通过 API 或导出）

**命令：**
```bash
skill-seekers create --database-id  abc123
```

---

### 17. Slack/Discord 聊天

**类型：** 聊天平台导出或 API 访问

**命令：**
```bash
skill-seekers create --chat-export-path  slack-export/
```

---

## 工作流程

### 阶段 1：摄取（Ingest）

```
┌─────────────┐     ┌──────────────┐
│   来源      │────▶│   抓取器     │
│ (URL/仓库/  │     │ (提取        │
│  PDF/本地)  │     │  内容)       │
└─────────────┘     └──────────────┘
```

- 自动检测源类型
- 爬取和下载内容
- 遵守速率限制
- 提取文本、代码、元数据

---

### 阶段 2：结构化（Structure）

```
┌──────────────┐     ┌──────────────┐
│   原始数据   │────▶│   构建器     │
│ (页面/文件/  │     │ (按类别      │
│  提交)       │     │  组织)       │
└──────────────┘     └──────────────┘
```

- 按主题分类内容
- 提取代码示例
- 构建导航结构
- 创建参考文件

---

### 阶段 3：增强（Enhance）（可选）

```
┌──────────────┐     ┌──────────────┐
│   SKILL.md   │────▶│  增强器      │
│  (基础版)    │     │ (AI 改进     │
│              │     │  质量)       │
└──────────────┘     └──────────────┘
```

- AI 审查和改进内容
- 添加示例和模式
- 修复格式
- 增强导航

**模式：**
- **API：** 使用 Claude API（快速，费用约 $0.10-0.30）
- **LOCAL：** 使用 Claude Code（免费，需要 Claude Code Max）

---

### 阶段 4：打包（Package）

```
┌──────────────┐     ┌──────────────┐
│   Skill 目录 │────▶│   打包器     │
│ (结构化      │     │ (创建        │
│  内容)       │     │  平台格式)   │
└──────────────┘     └──────────────┘
```

- 格式化为目标平台格式
- 创建归档文件（ZIP、tar.gz）
- 优化大小
- 验证结构

---

### 阶段 5：上传（Upload）（可选）

```
┌──────────────┐     ┌──────────────┐
│   包         │────▶│   平台       │
│ (.zip/.tar)  │     │ (Claude/     │
│              │     │  Gemini 等)  │
└──────────────┘     └──────────────┘
```

- 上传到目标平台
- 配置设置
- 返回 skill ID/URL

---

## 增强级别

控制应用多少 AI 增强：

| 级别 | 效果 | 使用场景 |
|-------|--------------|----------|
| **0** | 不增强 | 快速抓取，手动审查 |
| **1** | 仅 SKILL.md | 基础改进 |
| **2** | + 架构/配置 | **推荐** - 良好平衡 |
| **3** | 完全增强 | 最高质量，耗时更长 |

**默认：** Level 2

```bash
# 跳过增强（最快）
skill-seekers create <source> --enhance-level 0

# 完全增强（最佳质量）
skill-seekers create <source> --enhance-level 3
```

---

## 目标平台

将 skill 打包为不同 AI 系统的格式：

| 平台 | 格式 | 用途 |
|----------|--------|-----|
| **Claude AI** | ZIP + YAML | Claude Code, Claude API |
| **Gemini** | tar.gz | Google Gemini |
| **OpenAI** | ZIP + Vector | ChatGPT, Assistants API |
| **LangChain** | Documents | RAG 管道 |
| **LlamaIndex** | TextNodes | 查询引擎 |
| **ChromaDB** | Collection | 向量搜索 |
| **Weaviate** | Objects | 向量数据库 |
| **Cursor** | .cursorrules | IDE AI 助手 |
| **Windsurf** | .windsurfrules | IDE AI 助手 |

---

## 配置

### 简单模式（自动检测）

```bash
# 只需提供来源
skill-seekers create https://docs.react.dev/
```

### 预设配置

```bash
# 使用预定义配置
skill-seekers create --config react
```

**可用预设：** `react`, `vue`, `django`, `fastapi`, `godot` 等。

### 自定义配置

```bash
# 创建自定义配置
cat > configs/my-docs.json << 'EOF'
{
  "name": "my-docs",
  "base_url": "https://docs.example.com/",
  "max_pages": 200
}
EOF

skill-seekers create --config configs/my-docs.json
```

查看 [Config Format](../reference/CONFIG_FORMAT.md) 获取完整规范。

---

## 多来源 Skill

将多个来源合并为一个 skill：

```bash
# 创建统一配置
cat > configs/my-project.json << 'EOF'
{
  "name": "my-project",
  "sources": [
    {"type": "docs", "base_url": "https://docs.example.com/"},
    {"type": "github", "repo": "owner/repo"},
    {"type": "pdf", "pdf_path": "manual.pdf"}
  ]
}
EOF

# 运行统一抓取
skill-seekers create --config configs/my-project.json
```

**优势：**
- 单一 skill，完整上下文
- 自动冲突检测
- 交叉引用内容

---

## 缓存与恢复

### 缓存工作原理

```
首次抓取:    下载所有页面 → 保存到 output/{name}_data/
第二次抓取:  复用缓存数据 → 快速重建
```

### 跳过抓取

```bash
# 使用缓存数据，仅重建
skill-seekers create --config react --skip-scrape
```

### 恢复中断的任务

```bash
# 列出可恢复的任务
skill-seekers resume --list

# 恢复特定任务
skill-seekers resume job-abc123
```

---

## 速率限制

尊重服务器：

```bash
# 默认：请求间隔 0.5 秒
skill-seekers create <source>

# 更快（用于你自己的服务器）
skill-seekers create <source> --rate-limit 0.1

# 更慢（用于有限速的网站）
skill-seekers create <source> --rate-limit 2.0
```

**为什么重要：**
- 防止被封禁
- 尊重服务器资源
- 良好的网络公民意识

---

## 关键要点

1. **Skill 是结构化知识** - 不仅仅是原始文本
2. **自动检测有效** - 通常不需要自定义配置
3. **增强提高质量** - Level 2 是最佳平衡点
4. **一次打包，处处使用** - 同一个 skill，多种平台
5. **缓存节省时间** - 无需重新抓取即可重建

---

## 下一步

- [抓取指南](02-scraping.md) - 深入探讨来源选项
- [增强指南](03-enhancement.md) - AI 增强详解
- [Config Format](../reference/CONFIG_FORMAT.md) - 自定义配置
