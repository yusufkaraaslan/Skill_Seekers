# Skill Seekers 文档

> **翻译状态**：截至本分支，`docs/zh-CN/` 已完成全部文档树的简体中文翻译。如有疑义，以父目录 `docs/` 中的英文文档为准（英文为权威版本）。

> **Skill Seekers v3.7.0 完整文档**

---

## 欢迎！

这里是 **Skill Seekers** 的官方文档 —— 一款通用工具，可将 **18 种来源类型**（文档站点、GitHub 仓库、PDF、视频、Word 文档、EPUB 电子书、Jupyter 笔记本、本地 HTML、OpenAPI 规范、AsciiDoc、PowerPoint、RSS/Atom 订阅、man 手册页、Confluence、Notion、Slack/Discord 以及本地代码库）转换为面向 21+ 平台的 AI 就绪技能。

---

## 我应该从哪里开始？

### 🚀 我是新手

从我们的**入门指南**开始：

1. [安装](getting-started/01-installation.md) - 安装 Skill Seekers
2. [快速开始](getting-started/02-quick-start.md) - 用 3 条命令创建你的第一个技能
3. [你的第一个技能](getting-started/03-your-first-skill.md) - 完整演练
4. [下一步](getting-started/04-next-steps.md) - 接下来该做什么
5. [扫描项目](../getting-started/05-scan-a-project.md) - 从代码库引导生成配置

### 📖 我想深入学习

探索我们的**用户指南**：

- [核心概念](user-guide/01-core-concepts.md) - Skill Seekers 的工作原理
- [抓取指南](user-guide/02-scraping.md) - 所有抓取选项
- [增强指南](user-guide/03-enhancement.md) - AI 增强详解
- [打包指南](user-guide/04-packaging.md) - 导出到各平台
- [工作流指南](user-guide/05-workflows.md) - 增强工作流
- [故障排除](user-guide/06-troubleshooting.md) - 常见问题

### 📚 我需要查阅参考

查找具体信息：

- [CLI 参考](reference/CLI_REFERENCE.md) - 全部 19 个命令
- [MCP 参考](reference/MCP_REFERENCE.md) - 40 个 MCP 工具
- [配置格式](reference/CONFIG_FORMAT.md) - JSON 规范
- [环境变量](reference/ENVIRONMENT_VARIABLES.md) - 所有环境变量
- [FAQ](../FAQ.md) - 常见问题解答
- [故障排除](../TROUBLESHOOTING.md) - 完整故障排除参考

### 🚀 我准备好进阶了

高级用户功能：

- [MCP 服务器设置](advanced/mcp-server.md) - MCP 集成
- [MCP 工具深入解析](advanced/mcp-server.md) - MCP 高级用法
- [自定义工作流](advanced/custom-workflows.md) - 创建工作流
- [多来源抓取](advanced/multi-source.md) - 组合多个来源

---

## 快速参考

### 3 条命令

```bash
# 1. Install
pip install skill-seekers

# 2. Create skill
skill-seekers create https://docs.django.com/

# 3. Package for Claude
skill-seekers package output/django --target claude
```

### 常用命令

```bash
# Create from any source (auto-detects type)
skill-seekers create https://docs.django.com/
skill-seekers create facebook/react
skill-seekers create manual.pdf
skill-seekers create notebook.ipynb

# Scan a project for tech stack — emits one config per framework
skill-seekers scan ./my-react-app --out ./configs/scanned/

# Enhance skill
skill-seekers enhance output/my-skill/

# Package for platform
skill-seekers package output/my-skill/ --target claude

# Upload
skill-seekers upload output/my-skill-claude.zip

# Install complete workflow
skill-seekers install --config react --target claude

# Doctor / diagnostics
skill-seekers doctor
```

---

## 文档结构

```
docs/
├── README.md                 # This file - start here
├── ARCHITECTURE.md          # How docs are organized
├── UML_ARCHITECTURE.md      # Software architecture (UML diagrams)
├── UNIFICATION_PLAN.md      # Grand Unification refactor plan + phase results
├── BUG_AUDIT.md             # Full-codebase bug audit (historical record)
│
├── getting-started/         # For new users
│   ├── 01-installation.md
│   ├── 02-quick-start.md
│   ├── 03-your-first-skill.md
│   ├── 04-next-steps.md
│   └── 05-scan-a-project.md
│
├── user-guide/              # Common tasks
│   ├── 01-core-concepts.md
│   ├── 02-scraping.md
│   ├── 03-enhancement.md
│   ├── 04-packaging.md
│   ├── 05-workflows.md
│   └── 06-troubleshooting.md
│
├── guides/                  # How-to guides
│   ├── MCP_SETUP.md
│   ├── MIGRATION_GUIDE.md
│   ├── TESTING_GUIDE.md
│   └── UPLOAD_GUIDE.md
│
├── integrations/            # Platform integrations
│   ├── LANGCHAIN.md
│   ├── LLAMA_INDEX.md
│   ├── CURSOR.md
│   └── ...
│
├── features/                # Feature deep-dives
│   ├── BOOTSTRAP_SKILL.md
│   ├── UNIFIED_SCRAPING.md
│   └── ENHANCEMENT.md
│
├── reference/               # Technical reference
│   ├── CLI_REFERENCE.md     # 19 commands
│   ├── MCP_REFERENCE.md     # 40 MCP tools
│   ├── CONFIG_FORMAT.md     # JSON spec
│   └── ENVIRONMENT_VARIABLES.md
│
├── advanced/                # Power user topics
│   ├── mcp-server.md
│   ├── custom-workflows.md
│   └── multi-source.md
│
├── archive/                 # Legacy docs
├── blog/                    # Blog posts
├── case-studies/            # Case studies
├── plans/                   # Feature plans
├── roadmap/                 # Roadmap
├── strategy/                # Strategy docs
└── zh-CN/                   # Chinese translations
```

---

## 按使用场景

### 我想构建 AI 技能

面向 Claude、Gemini、ChatGPT：

1. [快速开始](getting-started/02-quick-start.md)
2. [增强指南](user-guide/03-enhancement.md)
3. [工作流指南](user-guide/05-workflows.md)

### 我想构建 RAG 流水线

面向 LangChain、LlamaIndex、向量数据库：

1. [核心概念](user-guide/01-core-concepts.md)
2. [打包指南](user-guide/04-packaging.md)
3. [MCP 参考](reference/MCP_REFERENCE.md)

### 我想要 AI 编程辅助

面向 Cursor、Windsurf、Cline、Roo、Aider、Bolt、Kilo、Continue、Kimi Code：

1. [你的第一个技能](getting-started/03-your-first-skill.md)
2. [本地代码库分析](user-guide/02-scraping.md#本地代码库分析)
3. `skill-seekers install-agent --agent cursor`

---

## 版本信息

- **当前版本：** 3.7.0
- **最后更新：** 2026-06-11
- **来源类型：** 18
- **Python 要求：** 3.10+

---

## 参与文档贡献

发现问题？想改进文档？

1. 编辑 `docs/` 目录中的文件
2. 遵循现有结构
3. 提交 PR

详见[贡献指南](../../CONTRIBUTING.md)。

---

## 外部链接

- **主仓库：** https://github.com/yusufkaraaslan/Skill_Seekers
- **网站：** https://skillseekersweb.com/
- **PyPI：** https://pypi.org/project/skill-seekers/
- **问题反馈：** https://github.com/yusufkaraaslan/Skill_Seekers/issues

---

## 许可证

MIT 许可证 - 见 [LICENSE](../../LICENSE) 文件。

---

*祝你构建技能愉快！🚀*
