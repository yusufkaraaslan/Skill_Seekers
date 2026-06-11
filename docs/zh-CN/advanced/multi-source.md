# 多源抓取指南

> **Skill Seekers v3.6.0**  
> **将 18 种来源类型合并为一个统一技能**

---

## 什么是多源抓取？

将多个来源合并为单个综合技能。Skill Seekers 支持 **18 种来源类型**，可自由混合搭配：

```
┌──────────────┐
│ Documentation│──┐
│ (Web docs)   │  │
├──────────────┤  │
│ GitHub Repo  │  │
│ (Source code) │  │
├──────────────┤  │     ┌──────────────────┐
│ PDF / Word / │  │     │  Unified Skill   │
│ EPUB / PPTX  │──┼────▶│  (Single source  │
├──────────────┤  │     │   of truth)      │
│ Video /      │  │     └──────────────────┘
│ Jupyter / HTML│  │
├──────────────┤  │
│ OpenAPI /    │  │
│ AsciiDoc /   │  │
│ RSS / Man    │  │
├──────────────┤  │
│ Confluence / │──┘
│ Notion / Chat│
└──────────────┘
```

---

## 何时使用多源

### 使用场景

| 场景 | 来源 | 优势 |
|----------|---------|---------|
| 框架 + 示例 | 文档 + GitHub 仓库 | 理论 + 实践 |
| 产品 + API | 文档 + OpenAPI 规范 | 用法 + 参考 |
| 旧版 + 当前 | PDF + 网页文档 | 完整历史 |
| 内部 + 外部 | 本地代码 + 公共文档 | 完整上下文 |
| 数据科学项目 | Jupyter + GitHub + 文档 | 代码 + 笔记本 + 文档 |
| 企业维基 | Confluence + GitHub + 视频 | 维基 + 代码 + 教程 |
| API 优先产品 | OpenAPI + 文档 + Jupyter | 规范 + 文档 + 示例 |
| CLI 工具 | Man 手册页 + GitHub + AsciiDoc | 参考 + 代码 + 文档 |
| 团队知识 | Notion + Slack/Discord + 文档 | 笔记 + 讨论 + 文档 |
| 书籍 + 代码 | EPUB + GitHub + PDF | 理论 + 实现 |
| 演示文稿 + 代码 | PowerPoint + GitHub + 文档 | 幻灯片 + 代码 + 参考 |
| 内容订阅 | RSS/Atom + 文档 + GitHub | 更新 + 文档 + 代码 |

### 优势

- **单一事实来源** - 一个技能包含所有上下文
- **冲突检测** - 发现文档/代码差异
- **交叉引用** - 来源之间建立链接
- **全面性** - 知识无缺口

---

## 创建统一配置

### 基本结构

```json
{
  "name": "my-framework-complete",
  "description": "Complete documentation and code",
  "merge_mode": "claude-enhanced",
  
  "sources": [
    {
      "type": "docs",
      "name": "documentation",
      "base_url": "https://docs.example.com/"
    },
    {
      "type": "github",
      "name": "source-code",
      "repo": "owner/repo"
    }
  ]
}
```

---

## 来源类型（支持 17 种）

### 1. 文档（网页）

```json
{
  "type": "docs",
  "name": "official-docs",
  "base_url": "https://docs.framework.com/",
  "max_pages": 500,
  "categories": {
    "getting_started": ["intro", "quickstart"],
    "api": ["reference", "api"]
  }
}
```

### 2. GitHub 仓库

```json
{
  "type": "github",
  "name": "source-code",
  "repo": "facebook/react",
  "fetch_issues": true,
  "max_issues": 100,
  "enable_codebase_analysis": true
}
```

### 3. PDF 文档

```json
{
  "type": "pdf",
  "name": "legacy-manual",
  "pdf_path": "docs/legacy-manual.pdf",
  "enable_ocr": false
}
```

### 4. 本地代码库

```json
{
  "type": "local",
  "name": "internal-tools",
  "directory": "./internal-lib",
  "languages": ["Python", "JavaScript"]
}
```

### 5. Word 文档（.docx）

```json
{
  "type": "word",
  "name": "product-spec",
  "path": "docs/specification.docx"
}
```

### 6. 视频（YouTube/Vimeo/本地）

```json
{
  "type": "video",
  "name": "tutorial-video",
  "url": "https://www.youtube.com/watch?v=example",
  "language": "en"
}
```

### 7. EPUB

```json
{
  "type": "epub",
  "name": "programming-book",
  "path": "books/python-guide.epub"
}
```

### 8. Jupyter Notebook

```json
{
  "type": "jupyter",
  "name": "analysis-notebooks",
  "path": "notebooks/data-analysis.ipynb"
}
```

### 9. 本地 HTML

```json
{
  "type": "html",
  "name": "exported-docs",
  "path": "exports/documentation.html"
}
```

### 10. OpenAPI/Swagger

```json
{
  "type": "openapi",
  "name": "api-spec",
  "path": "specs/openapi.yaml"
}
```

### 11. AsciiDoc

```json
{
  "type": "asciidoc",
  "name": "technical-docs",
  "path": "docs/manual.adoc"
}
```

### 12. PowerPoint（.pptx）

```json
{
  "type": "pptx",
  "name": "architecture-deck",
  "path": "presentations/architecture.pptx"
}
```

### 13. RSS/Atom 订阅

```json
{
  "type": "rss",
  "name": "release-feed",
  "url": "https://blog.example.com/releases.xml"
}
```

### 14. Man 手册页

```json
{
  "type": "manpage",
  "name": "cli-reference",
  "path": "man/mytool.1"
}
```

### 15. Confluence

```json
{
  "type": "confluence",
  "name": "team-wiki",
  "base_url": "https://company.atlassian.net/wiki",
  "space_key": "ENGINEERING"
}
```

### 16. Notion

```json
{
  "type": "notion",
  "name": "project-docs",
  "workspace": "my-workspace",
  "root_page_id": "abc123def456"
}
```

### 17. Slack/Discord（聊天）

```json
{
  "type": "chat",
  "name": "team-discussions",
  "path": "exports/slack-export/"
}
```

---

## 完整示例

### React 完整技能

```json
{
  "name": "react-complete",
  "description": "React - docs, source, and guides",
  "merge_mode": "claude-enhanced",
  
  "sources": [
    {
      "type": "docs",
      "name": "react-docs",
      "base_url": "https://react.dev/",
      "max_pages": 300,
      "categories": {
        "getting_started": ["learn", "tutorial"],
        "api": ["reference", "hooks"],
        "advanced": ["concurrent", "suspense"]
      }
    },
    {
      "type": "github",
      "name": "react-source",
      "repo": "facebook/react",
      "fetch_issues": true,
      "max_issues": 50,
      "enable_codebase_analysis": true,
      "code_analysis_depth": "deep"
    },
    {
      "type": "pdf",
      "name": "react-patterns",
      "pdf_path": "downloads/react-patterns.pdf"
    }
  ],
  
  "conflict_detection": {
    "enabled": true,
    "rules": [
      {
        "field": "api_signature",
        "action": "flag_mismatch"
      },
      {
        "field": "version",
        "action": "warn_outdated"
      }
    ]
  },
  
  "output_structure": {
    "group_by_source": false,
    "cross_reference": true
  }
}
```

---

## 运行统一抓取

### 基础命令

```bash
skill-seekers create --config react-complete.json
```

### 带选项

```bash
# 全新开始（忽略缓存）
skill-seekers create --config react-complete.json --fresh

# 干运行
skill-seekers create --config react-complete.json --dry-run

# 基于规则的合并
skill-seekers create --config react-complete.json --merge-mode rule-based
```

---

## 合并模式

### claude-enhanced（默认）

使用 AI 智能合并来源：

- 检测内容之间的关系
- 智能解决冲突
- 创建交叉引用
- 最佳质量，较慢

```bash
skill-seekers create --config my-config.json --merge-mode claude-enhanced
```

### rule-based

使用定义的规则进行合并：

- 更快
- 确定性
- 较不复杂

```bash
skill-seekers create --config my-config.json --merge-mode rule-based
```

### 通用合并系统

当组合超出标准 docs+github+pdf 三元组的来源类型时，**通用合并系统**（`unified_skill_builder.py` 中的 `_generic_merge()`）会自动处理任意组合。它对已知组合（docs+github、docs+pdf、github+pdf）使用成对合成，对所有其他来源类型组合则回退到通用合并策略。

### AI 驱动的多来源合并

对于复杂的多来源项目，可使用 `complex-merge.yaml` 工作流预设进行 AI 驱动的合并：

```bash
skill-seekers create --config my-config.json \
  --enhance-workflow complex-merge
```

该工作流使用 Claude 智能协调来自不同来源类型的内容，解决冲突，并在原本难以确定性合并的来源之间建立连贯的交叉引用。

---

## 冲突检测

### 自动检测

发现来源之间的差异：

```json
{
  "conflict_detection": {
    "enabled": true,
    "rules": [
      {
        "field": "api_signature",
        "action": "flag_mismatch"
      },
      {
        "field": "version",
        "action": "warn_outdated"
      },
      {
        "field": "deprecation",
        "action": "highlight"
      }
    ]
  }
}
```

### 冲突报告

抓取后，检查冲突：

```bash
# 冲突在输出中报告
ls output/react-complete/conflicts.json

# 或使用 MCP 工具
detect_conflicts({
  "docs_source": "output/react-docs",
  "code_source": "output/react-source"
})
```

---

## 输出结构

### 合并输出

```
output/react-complete/
├── SKILL.md                    # 合并后的技能
├── references/
│   ├── index.md               # 主索引
│   ├── getting_started.md     # 来自文档
│   ├── api_reference.md       # 来自文档
│   ├── source_overview.md     # 来自 GitHub
│   ├── code_examples.md       # 来自 GitHub
│   └── patterns.md            # 来自 PDF
├── .skill-seekers/
│   ├── manifest.json          # 元数据
│   ├── sources.json           # 来源列表
│   └── conflicts.json         # 检测到的冲突
└── cross-references.json      # 来源之间的链接
```

---

## 最佳实践

### 1. 清晰命名来源

```json
{
  "sources": [
    {"type": "docs", "name": "official-docs"},
    {"type": "github", "name": "source-code"},
    {"type": "pdf", "name": "legacy-reference"}
  ]
}
```

### 2. 限制来源范围

```json
{
  "type": "github",
  "name": "core-source",
  "repo": "owner/repo",
  "file_patterns": ["src/**/*.py"],  // 仅核心文件
  "exclude_patterns": ["tests/**", "docs/**"]
}
```

### 3. 启用冲突检测

```json
{
  "conflict_detection": {
    "enabled": true
  }
}
```

### 4. 使用适当的合并模式

- **claude-enhanced** - 最佳质量，用于重要技能
- **rule-based** - 更快，用于测试或大型数据集

### 5. 增量测试

```bash
# 首先用一个来源测试
skill-seekers create <source1>

# 然后添加来源
skill-seekers create --config my-config.json --dry-run
```

---

## 故障排除

### "Source not found"

```bash
# 检查所有来源是否存在
curl -I https://docs.example.com/
ls downloads/manual.pdf
```

### "Merge conflicts"

```bash
# 检查冲突报告
cat output/my-skill/conflicts.json

# 调整 merge_mode
skill-seekers create --config my-config.json --merge-mode rule-based
```

### "Out of memory"

```bash
# 分别处理来源
# 然后手动合并
```

---

## 示例

### 框架 + 示例

```json
{
  "name": "django-complete",
  "sources": [
    {"type": "docs", "base_url": "https://docs.djangoproject.com/"},
    {"type": "github", "repo": "django/django", "fetch_issues": false}
  ]
}
```

### 文档 + OpenAPI 规范

```json
{
  "name": "stripe-complete",
  "sources": [
    {"type": "docs", "base_url": "https://stripe.com/docs"},
    {"type": "openapi", "path": "specs/stripe-openapi.yaml"}
  ]
}
```

### 代码 + Jupyter 笔记本

```json
{
  "name": "ml-project",
  "sources": [
    {"type": "github", "repo": "org/ml-pipeline"},
    {"type": "jupyter", "path": "notebooks/training.ipynb"},
    {"type": "jupyter", "path": "notebooks/evaluation.ipynb"}
  ]
}
```

### Confluence + GitHub

```json
{
  "name": "internal-platform",
  "sources": [
    {"type": "confluence", "base_url": "https://company.atlassian.net/wiki", "space_key": "PLATFORM"},
    {"type": "github", "repo": "company/platform-core"},
    {"type": "openapi", "path": "specs/platform-api.yaml"}
  ]
}
```

### 旧版 + 当前

```json
{
  "name": "product-docs",
  "sources": [
    {"type": "docs", "base_url": "https://docs.example.com/v2/"},
    {"type": "pdf", "pdf_path": "v1-legacy-manual.pdf"}
  ]
}
```

### CLI 工具（Man 手册页 + GitHub + AsciiDoc）

```json
{
  "name": "mytool-complete",
  "sources": [
    {"type": "manpage", "path": "man/mytool.1"},
    {"type": "github", "repo": "org/mytool"},
    {"type": "asciidoc", "path": "docs/user-guide.adoc"}
  ]
}
```

### 团队知识（Notion + 聊天 + 视频）

```json
{
  "name": "onboarding-knowledge",
  "sources": [
    {"type": "notion", "workspace": "engineering", "root_page_id": "abc123"},
    {"type": "chat", "path": "exports/slack-engineering/"},
    {"type": "video", "url": "https://www.youtube.com/playlist?list=PLonboarding"}
  ]
}
```

---

## 另请参阅

- [配置格式](../reference/CONFIG_FORMAT.md) - 完整 JSON 规范
- [抓取指南](../user-guide/02-scraping.md) - 单个来源选项
- [MCP 参考](../reference/MCP_REFERENCE.md) - `scrape_docs` 工具（处理统一多源配置）
