# MCP Server Setup Guide

> **Skill Seekers v3.2.0**  
> **通过 Model Context Protocol 与 AI 代理集成**

---

## What is MCP?

MCP (Model Context Protocol) lets AI agents like Claude Code control Skill Seekers through natural language:

```
You: "Scrape the React documentation"
Claude: ▶️ scrape_docs({"url": "https://react.dev/"})
        ✅ Done! Created output/react/
```

---

## Installation

```bash
# Install with MCP support
pip install skill-seekers[mcp]

# Verify
skill-seekers-mcp --version
```

---

## Transport Modes

### stdio Mode (Default)

For Claude Code, VS Code + Cline:

```bash
skill-seekers-mcp
```

**Use when:**
- Running in Claude Code
- Direct integration with terminal-based agents
- Simple local setup

---

### HTTP Mode

For Cursor, Windsurf, HTTP clients:

```bash
# Start HTTP server
skill-seekers-mcp --transport http --port 8765

# Custom host
skill-seekers-mcp --transport http --host 0.0.0.0 --port 8765
```

**Use when:**
- IDE integration (Cursor, Windsurf)
- Remote access needed
- Multiple clients

---

## Claude Code Integration

### Automatic Setup

```bash
# In Claude Code, run:
/claude add-mcp-server skill-seekers
```

Or manually add to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "skill-seekers": {
      "command": "skill-seekers-mcp",
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "GITHUB_TOKEN": "ghp_..."
      }
    }
  }
}
```

### Usage

Once connected, ask Claude:

```
"List available configs"
"Scrape the Django documentation"
"Package output/react for Gemini"
"Enhance output/my-skill with security-focus workflow"
```

---

## Cursor IDE Integration

### Setup

1. Start MCP server:
```bash
skill-seekers-mcp --transport http --port 8765
```

2. In Cursor Settings → MCP:
   - Name: `skill-seekers`
   - URL: `http://localhost:8765`

### Usage

In Cursor chat:

```
"Create a skill from the current project"
"Analyze this codebase and generate a cursorrules file"
```

---

## Windsurf Integration

### Setup

1. Start MCP server:
```bash
skill-seekers-mcp --transport http --port 8765
```

2. In Windsurf Settings:
   - Add MCP server endpoint: `http://localhost:8765`

---

## 可用工具

27 个工具，按类别组织：

### 核心工具（9 个）
- `list_configs` - 列出预设
- `generate_config` - 从 URL 创建配置
- `validate_config` - 检查配置
- `estimate_pages` - 页面估算
- `scrape_docs` - 抓取文档
- `package_skill` - 打包技能
- `upload_skill` - 上传到平台
- `enhance_skill` - AI 增强
- `install_skill` - 完整工作流

### 扩展工具（10 个）
- `scrape_github` - GitHub 仓库
- `scrape_pdf` - PDF 提取
- `scrape_generic` - 10 种新来源类型的通用抓取器（见下文）
- `scrape_codebase` - 本地代码
- `unified_scrape` - 多源抓取
- `detect_patterns` - 模式检测
- `extract_test_examples` - 测试示例
- `build_how_to_guides` - 操作指南
- `extract_config_patterns` - 配置模式
- `detect_conflicts` - 文档/代码冲突

### 配置源（5 个）
- `add_config_source` - 注册 Git 源
- `list_config_sources` - 列出源
- `remove_config_source` - 删除源
- `fetch_config` - 获取配置
- `submit_config` - 提交配置

### 向量数据库（4 个）
- `export_to_weaviate`
- `export_to_chroma`
- `export_to_faiss`
- `export_to_qdrant`

### scrape_generic 工具

`scrape_generic` 是 v3.2.0 新增的 10 种来源类型的通用入口。它将请求委托给相应的 CLI 抓取器模块。

**支持的来源类型：** `jupyter`（Jupyter 笔记本）、`html`（本地 HTML）、`openapi`（OpenAPI/Swagger 规范）、`asciidoc`（AsciiDoc 文档）、`pptx`（PowerPoint 演示文稿）、`rss`（RSS/Atom 订阅源）、`manpage`（Man 手册页）、`confluence`（Confluence 维基）、`notion`（Notion 页面）、`chat`（Slack/Discord 聊天记录）

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `source_type` | string | 是 | 10 种支持的来源类型之一 |
| `name` | string | 是 | 输出的技能名称 |
| `path` | string | 否 | 文件或目录路径（用于基于文件的来源） |
| `url` | string | 否 | URL（用于 confluence、notion、rss 等基于 URL 的来源） |

**使用示例：**

```
"抓取 Jupyter 笔记本 analysis.ipynb"
→ scrape_generic(source_type="jupyter", name="analysis", path="analysis.ipynb")

"提取 API 规范内容"
→ scrape_generic(source_type="openapi", name="my-api", path="api-spec.yaml")

"处理 PowerPoint 演示文稿"
→ scrape_generic(source_type="pptx", name="slides", path="presentation.pptx")

"抓取 Confluence 维基"
→ scrape_generic(source_type="confluence", name="wiki", url="https://wiki.example.com")
```

详见 [MCP 参考文档](../reference/MCP_REFERENCE.md)。

---

## Common Workflows

### Workflow 1: Documentation Skill

```
User: "Create a skill from React docs"
Claude: ▶️ scrape_docs({"url": "https://react.dev/"})
        ⏳ Scraping...
        ✅ Created output/react/
        
        ▶️ package_skill({"skill_directory": "output/react/", "target": "claude"})
        ✅ Created output/react-claude.zip
        
        Skill ready! Upload to Claude?
```

### Workflow 2: GitHub Analysis

```
User: "Analyze the facebook/react repo"
Claude: ▶️ scrape_github({"repo": "facebook/react"})
        ⏳ Analyzing...
        ✅ Created output/react/
        
        ▶️ enhance_skill({"skill_directory": "output/react/", "workflow": "architecture-comprehensive"})
        ✅ Enhanced with architecture analysis
```

### Workflow 3: Multi-Platform Export

```
User: "Create Django skill for all platforms"
Claude: ▶️ scrape_docs({"config": "django"})
        ✅ Created output/django/
        
        ▶️ package_skill({"skill_directory": "output/django/", "target": "claude"})
        ▶️ package_skill({"skill_directory": "output/django/", "target": "gemini"})
        ▶️ package_skill({"skill_directory": "output/django/", "target": "openai"})
        ✅ Created packages for all platforms
```

---

## Configuration

### Environment Variables

Set in `~/.claude/mcp.json` or before starting server:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
export OPENAI_API_KEY=sk-...
export GITHUB_TOKEN=ghp_...
```

### Server Options

```bash
# Debug mode
skill-seekers-mcp --verbose

# Custom port
skill-seekers-mcp --port 8080

# Allow all origins (CORS)
skill-seekers-mcp --cors
```

---

## Security

### Local Only (stdio)

```bash
# Only accessible by local Claude Code
skill-seekers-mcp
```

### HTTP with Auth

```bash
# Use reverse proxy with auth
# nginx, traefik, etc.
```

### API Key Protection

```bash
# Don't hardcode keys
# Use environment variables
# Or secret management
```

---

## Troubleshooting

### "Server not found"

```bash
# Check if running
curl http://localhost:8765/health

# Restart
skill-seekers-mcp --transport http --port 8765
```

### "Tool not available"

```bash
# Check version
skill-seekers-mcp --version

# Update
pip install --upgrade skill-seekers[mcp]
```

### "Connection refused"

```bash
# Check port
lsof -i :8765

# Use different port
skill-seekers-mcp --port 8766
```

---

## See Also

- [MCP 参考文档](../reference/MCP_REFERENCE.md) - 完整工具参考
- [MCP 工具深入](mcp-tools.md) - 高级用法
- [MCP 协议](https://modelcontextprotocol.io/) - 官方 MCP 文档
