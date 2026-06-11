# 你的第一个 Skill — 完整演练

> **Skill Seekers v3.6.0**  
> **创建你的第一个 skill 的分步指南**

---

## 我们要构建什么

一个来自 **Django 文档** 的 skill，可与 Claude AI 一起使用。

**所需时间：** ~15-20 分钟  
**结果：** 一份包含约 400 行结构化文档的综合 Django skill

---

## 前置条件

```bash
# 确保 skill-seekers 已安装
skill-seekers --version

# 应输出：skill-seekers 3.6.0
```

---

## 第 1 步：选择你的来源

在本演练中，我们将使用 Django 文档。你也可以使用以下任意一种：

```bash
# 选项 A：Django 文档（我们将使用的）
https://docs.djangoproject.com/

# 选项 B：React 文档
https://react.dev/

# 选项 C：你自己的项目
./my-project

# 选项 D：GitHub 仓库
facebook/react
```

---

## 第 2 步：使用试运行预览

在抓取之前，让我们预览将要发生的事情：

```bash
skill-seekers create https://docs.djangoproject.com/ --dry-run
```

**预期输出：**
```
🔍 Dry Run Preview
==================
Source: https://docs.djangoproject.com/
Type: Documentation website
Estimated pages: ~400
Estimated time: 15-20 minutes

Will create:
  - output/django/
  - output/django/SKILL.md
  - output/django/references/

Configuration:
  Rate limit: 0.5s
  Max pages: 500
  Enhancement: Level 2

✅ Preview complete. Run without --dry-run to execute.
```

这向你展示了将要发生的事情，而不会实际进行抓取。

---

## 第 3 步：创建 Skill

现在让我们实际创建它：

```bash
skill-seekers create https://docs.djangoproject.com/ --name django
```

**发生了什么：**
1. **检测** — 识别为文档网站
2. **爬取** — 从基础 URL 发现页面
3. **抓取** — 下载并提取内容（~5-10 分钟）
4. **处理** — 按类别组织
5. **增强** — AI 提升 SKILL.md 质量（~60 秒）

**进度输出：**
```
🚀 Creating skill: django
📍 Source: https://docs.djangoproject.com/
📋 Type: Documentation

⏳ Phase 1/5: Detecting source type...
✅ Detected: Documentation website

⏳ Phase 2/5: Discovering pages...
✅ Discovered: 387 pages

⏳ Phase 3/5: Scraping content...
Progress: [████████████████████░░░░░] 320/387 pages (83%)
Rate: 1.8 pages/sec | ETA: 37 seconds

⏳ Phase 4/5: Processing and categorizing...
✅ Categories: getting_started, models, views, templates, forms, admin, security

⏳ Phase 5/5: AI enhancement (Level 2)...
✅ SKILL.md enhanced: 423 lines

🎉 Skill created successfully!
   Location: output/django/
   SKILL.md: 423 lines
   References: 7 categories, 42 files

⏱️  Total time: 12 minutes 34 seconds
```

---

## 第 4 步：探索输出

让我们看看创建了什么：

```bash
ls -la output/django/
```

**输出：**
```
output/django/
├── .skill-seekers/           # 元数据
│   └── manifest.json
├── SKILL.md                  # 主 skill 文件 ⭐
├── references/               # 整理的文档
│   ├── index.md
│   ├── getting_started.md
│   ├── models.md
│   ├── views.md
│   ├── templates.md
│   ├── forms.md
│   ├── admin.md
│   └── security.md
└── assets/                   # 图片（如果有）
```

### 查看 SKILL.md

```bash
head -50 output/django/SKILL.md
```

**你将看到：**
```markdown
# Django Skill

## Overview
Django is a high-level Python web framework that encourages rapid development 
and clean, pragmatic design...

## Quick Reference

### Create a Project
```bash
django-admin startproject mysite
```

### Create an App
```bash
python manage.py startapp myapp
```

## Categories
- [Getting Started](#getting-started)
- [Models](#models)
- [Views](#views)
- [Templates](#templates)
- [Forms](#forms)
- [Admin](#admin)
- [Security](#security)

...
```

### 检查参考文献

```bash
ls output/django/references/
cat output/django/references/models.md | head -30
```

---

## 第 5 步：打包到 Claude

现在为 Claude AI 打包：

```bash
skill-seekers package output/django/ --target claude
```

**输出：**
```
📦 Packaging skill: django
🎯 Target: Claude AI

✅ Validated: SKILL.md (423 lines)
✅ Packaged: output/django-claude.zip
📊 Size: 245 KB

Next steps:
  1. Upload to Claude: skill-seekers upload output/django-claude.zip
  2. Or manually: Use "Create Skill" in Claude Code
```

---

## 第 6 步：上传到 Claude

### 选项 A：自动上传

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers upload output/django-claude.zip --target claude
```

### 选项 B：手动上传

1. 打开 [Claude Code](https://claude.ai/code) 或 Claude Desktop
2. 进入 "Skills" 或 "Projects"
3. 点击 "Create Skill" 或 "Upload"
4. 选择 `output/django-claude.zip`

---

## 第 7 步：使用你的 Skill

上传后，你可以向 Claude 提问：

```
"How do I create a Django model with foreign keys?"
"Show me how to use class-based views"
"What's the best way to handle forms in Django?"
"Explain Django's ORM query optimization"
```

Claude 将使用你的 skill 提供准确、有上下文的回答。

---

## 替代方案：跳过增强以加快速度

如果你想要更快的结果（无需 AI 增强）：

```bash
# 创建但不增强
skill-seekers create https://docs.djangoproject.com/ --name django --enhance-level 0

# 打包
skill-seekers package output/django/ --target claude

# 如有需要，稍后增强
skill-seekers enhance output/django/
```

---

## 替代方案：使用预设配置

不使用自动检测，而是使用预设：

```bash
# 查看可用预设
skill-seekers estimate --all

# 使用 Django 预设
skill-seekers create --config django
skill-seekers package output/django/ --target claude
```

---

## 你学到了什么

✅ **Create** - `skill-seekers create <source>` 自动检测并抓取  
✅ **Dry Run** - `--dry-run` 预览而不执行  
✅ **Enhancement** - AI 自动提升 SKILL.md 质量  
✅ **Package** - `skill-seekers package <dir> --target <platform>`  
✅ **Upload** - 直接上传或手动导入  

---

## 常见变体

### GitHub 仓库

```bash
skill-seekers create facebook/react --name react
skill-seekers package output/react/ --target claude
```

### 本地项目

```bash
cd ~/projects/my-api
skill-seekers create . --name my-api
skill-seekers package output/my-api/ --target claude
```

### PDF 文档

```bash
skill-seekers create manual.pdf --name docs
skill-seekers package output/docs/ --target claude
```

### 多平台

```bash
# 创建一次
skill-seekers create https://docs.djangoproject.com/ --name django

# 打包到多个平台
skill-seekers package output/django/ --target claude
skill-seekers package output/django/ --target gemini
skill-seekers package output/django/ --target openai

# 上传到每个平台
skill-seekers upload output/django-claude.zip --target claude
skill-seekers upload output/django-gemini.tar.gz --target gemini
```

---

## 故障排除

### 抓取中断

```bash
# 从检查点恢复
skill-seekers resume --list
skill-seekers resume <job-id>
```

### 页面过多

```bash
# 限制页面数
skill-seekers create https://docs.djangoproject.com/ --max-pages 100
```

### 提取了错误的内容

```bash
# 使用带有选择器的自定义配置
cat > configs/django.json << 'EOF'
{
  "name": "django",
  "base_url": "https://docs.djangoproject.com/",
  "selectors": {
    "main_content": "#docs-content"
  }
}
EOF

skill-seekers create --config configs/django.json
```

---

## 下一步

- [下一步](04-next-steps.md) - 从这里去哪里
- [核心概念](../user-guide/01-core-concepts.md) - 了解系统
- [抓取指南](../user-guide/02-scraping.md) - 高级抓取选项
- [增强指南](../user-guide/03-enhancement.md) - AI 增强深入探讨

---

## 总结

| 步骤 | 命令 | 时间 |
|------|---------|------|
| 1 | `skill-seekers create https://docs.djangoproject.com/` | ~15 分钟 |
| 2 | `skill-seekers package output/django/ --target claude` | ~5 秒 |
| 3 | `skill-seekers upload output/django-claude.zip` | ~10 秒 |

**总计：** ~15 分钟获得一个可用于生产环境的 AI skill！🎉
