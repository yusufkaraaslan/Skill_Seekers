# 快速入门指南

> **Skill Seekers v3.6.0**  
> **用 3 条命令创建你的第一个 skill**

---

## 3 条命令

```bash
# 1. 安装 Skill Seekers
pip install skill-seekers

# 2. 从任意来源创建 skill
skill-seekers create https://docs.django.com/

# 3. 打包为你的 AI 平台
skill-seekers package output/django --target claude
```

**完成了！** 你现在拥有 `output/django-claude.zip`，可以直接上传。

---

## 你可以从什么来源创建

`create` 命令自动检测你的来源：

| 来源类型 | 示例命令 |
|-------------|-----------------|
| **文档网站** | `skill-seekers create https://docs.react.dev/` |
| **GitHub 仓库** | `skill-seekers create facebook/react` |
| **本地代码** | `skill-seekers create ./my-project` |
| **PDF 文件** | `skill-seekers create manual.pdf` |
| **Word 文档** | `skill-seekers create report.docx` |
| **EPUB 电子书** | `skill-seekers create book.epub` |
| **视频** | `skill-seekers create https://youtube.com/watch?v=...` |
| **Jupyter Notebook** | `skill-seekers create analysis.ipynb` |
| **本地 HTML（文件）** | `skill-seekers create page.html` |
| **本地 HTML（目录）** | `skill-seekers create ./mirror_output/site/` |
| **OpenAPI 规范** | `skill-seekers create api-spec.yaml` |
| **AsciiDoc** | `skill-seekers create guide.adoc` |
| **PowerPoint** | `skill-seekers create slides.pptx` |
| **RSS/Atom 订阅** | `skill-seekers create feed.rss` |
| **Man Page** | `skill-seekers create grep.1` |
| **Confluence** | `skill-seekers create --space-key  DEV` |
| **Notion** | `skill-seekers create --database-id  abc123` |
| **Slack/Discord** | `skill-seekers create --chat-export-path  slack-export/` |
| **配置文件** | `skill-seekers create configs/custom.json` |

对于一个你还不清楚需要为哪些框架创建技能的现有项目，可使用 `skill-seekers scan <dir>` —— 它会通过 AI 检测技术栈，并为每个框架生成一份配置。参见[扫描项目](../../getting-started/05-scan-a-project.md)。

---

## 按来源分类的示例

### 文档网站

```bash
# React 文档
skill-seekers create https://react.dev/
skill-seekers package output/react --target claude

# Django 文档  
skill-seekers create https://docs.djangoproject.com/
skill-seekers package output/django --target claude
```

### GitHub 仓库

```bash
# React 源代码
skill-seekers create facebook/react
skill-seekers package output/react --target claude

# 你自己的仓库
skill-seekers create yourusername/yourrepo
skill-seekers package output/yourrepo --target claude
```

### 本地项目

```bash
# 你的代码库
skill-seekers create ./my-project
skill-seekers package output/my-project --target claude

# 特定目录
cd ~/projects/my-api
skill-seekers create .
skill-seekers package output/my-api --target claude
```

### PDF 文档

```bash
# 技术手册
skill-seekers create manual.pdf --name product-docs
skill-seekers package output/product-docs --target claude

# 研究论文
skill-seekers create paper.pdf --name research
skill-seekers package output/research --target claude
```

### 视频

```bash
# YouTube 视频转录
skill-seekers create https://www.youtube.com/watch?v=dQw4w9WgXcQ --name tutorial
skill-seekers package output/tutorial --target claude
```

### Jupyter Notebook

```bash
# 数据科学 notebook
skill-seekers create analysis.ipynb --name ml-analysis
skill-seekers package output/ml-analysis --target claude
```

### PowerPoint / Word / EPUB

```bash
# PowerPoint 幻灯片
skill-seekers create presentation.pptx --name quarterly-review

# Word 文档
skill-seekers create spec.docx --name api-spec

# EPUB 电子书
skill-seekers create rust-book.epub --name rust-guide
```

### Confluence / Notion / Slack

```bash
# Confluence wiki 空间
skill-seekers create --space-key  DEV --name team-docs

# Notion 工作区
skill-seekers create --database-id  abc123 --name product-wiki

# Slack/Discord 导出
skill-seekers create --chat-export-path  slack-export/ --name team-chat
```

---

## 常用选项

### 指定名称

```bash
skill-seekers create https://docs.example.com/ --name my-docs
```

### 添加描述

```bash
skill-seekers create facebook/react --description "React source code analysis"
```

### 试运行（预览）

```bash
skill-seekers create https://docs.react.dev/ --dry-run
```

### 跳过增强（更快）

```bash
skill-seekers create https://docs.react.dev/ --enhance-level 0
```

### 使用预设

```bash
# 快速分析（1-2 分钟）
skill-seekers create ./my-project --preset quick

# 全面分析（20-60 分钟）
skill-seekers create ./my-project --preset comprehensive
```

---

## 打包到不同平台

### Claude AI（默认）

```bash
skill-seekers package output/my-skill/
# 生成：output/my-skill-claude.zip
```

### Google Gemini

```bash
skill-seekers package output/my-skill/ --target gemini
# 生成：output/my-skill-gemini.tar.gz
```

### OpenAI ChatGPT

```bash
skill-seekers package output/my-skill/ --target openai
# 生成：output/my-skill-openai.zip
```

### LangChain

```bash
skill-seekers package output/my-skill/ --target langchain
# 生成：output/my-skill-langchain/ 目录
```

### 多平台

```bash
for platform in claude gemini openai; do
  skill-seekers package output/my-skill/ --target $platform
done
```

---

## 上传到平台

### 上传到 Claude

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers upload output/my-skill-claude.zip --target claude
```

### 上传到 Gemini

```bash
export GOOGLE_API_KEY=AIza...
skill-seekers upload output/my-skill-gemini.tar.gz --target gemini
```

### 打包后自动上传

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers package output/my-skill/ --target claude --upload
```

---

## 完整的一键工作流

使用 `install` 一步到位：

```bash
# 完整流程：抓取 → 增强 → 打包 → 上传
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers install --config react --target claude

# 跳过上传
skill-seekers install --config react --target claude --no-upload
```

---

## 输出结构

运行 `create` 后，你将获得：

```
output/
├── django/                    # Skill 目录
│   ├── SKILL.md              # 主 skill 文件
│   ├── references/           # 整理的文档
│   │   ├── index.md
│   │   ├── getting_started.md
│   │   └── api_reference.md
│   └── .skill-seekers/       # 元数据
│
└── django-claude.zip         # 打包后的 skill（打包后生成）
```

---

## 时间估算

| 来源类型 | 大小 | 时间 |
|-------------|------|------|
| 小型文档（< 50 页） | ~10 MB | 2-5 分钟 |
| 中型文档（50-200 页） | ~50 MB | 10-20 分钟 |
| 大型文档（200-500 页） | ~200 MB | 30-60 分钟 |
| GitHub 仓库（< 1000 个文件） | varies | 5-15 分钟 |
| 本地项目 | varies | 2-10 分钟 |
| PDF（< 100 页） | ~5 MB | 1-3 分钟 |

*时间包含抓取 + 增强（level 2）。使用 `--enhance-level 0` 可跳过增强。*

---

## 快速提示

### 先用试运行测试

```bash
skill-seekers create https://docs.example.com/ --dry-run
```

### 使用预设获得更快结果

```bash
# 测试用快速模式
skill-seekers create https://docs.react.dev/ --preset quick
```

### 跳过增强以加快速度

```bash
skill-seekers create https://docs.react.dev/ --enhance-level 0
skill-seekers enhance output/react/  # 稍后增强
```

### 检查可用配置

```bash
skill-seekers estimate --all
```

### 恢复中断的任务

```bash
skill-seekers resume --list
skill-seekers resume <job-id>
```

---

## 下一步

- [你的第一个 Skill](03-your-first-skill.md) - 完整演练
- [核心概念](../user-guide/01-core-concepts.md) - 了解工作原理
- [抓取指南](../user-guide/02-scraping.md) - 所有抓取选项

---

## 故障排除

### "command not found"

```bash
# 添加到 PATH
export PATH="$HOME/.local/bin:$PATH"
```

### "No module named 'skill_seekers'"

```bash
# 重新安装
pip install --force-reinstall skill-seekers
```

### 抓取太慢

```bash
# 使用异步模式
skill-seekers create https://docs.react.dev/ --async --workers 5
```

### 内存不足

```bash
# 使用流式模式
skill-seekers package output/large-skill/ --streaming
```

---

## 参见

- [安装指南](01-installation.md) - 详细安装说明
- [CLI 参考](../reference/CLI_REFERENCE.md) - 所有命令
- [配置格式](../reference/CONFIG_FORMAT.md) - 自定义配置
