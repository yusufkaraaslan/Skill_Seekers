# MCP 服务器设置指南

> **Skill Seekers v3.6.0**  
> **通过 Model Context Protocol 与 AI 代理集成**

---

## 什么是 MCP？

MCP（Model Context Protocol）让 Claude Code 等 AI 代理通过自然语言控制 Skill Seekers：

```
You: "抓取 React 文档"
Claude: ▶️ scrape_docs({"url": "https://react.dev/"})
        ✅ 完成！已创建 output/react/
```

---

## 安装

```bash
# 安装附带 MCP 支持
pip install skill-seekers[mcp]

# 验证
skill-seekers-mcp --version
```

---

## 传输模式

### stdio 模式（默认）

用于 Claude Code、VS Code + Cline：

```bash
skill-seekers-mcp
```

**适用场景：**
- 在 Claude Code 中运行
- 与基于终端的代理直接集成
- 简单的本地设置

---

### HTTP 模式

用于 Cursor、Windsurf、HTTP 客户端：

```bash
# 启动 HTTP 服务器
skill-seekers-mcp --transport http --port 8765

# 自定义主机
skill-seekers-mcp --transport http --host 0.0.0.0 --port 8765
```

**适用场景：**
- IDE 集成（Cursor、Windsurf）
- 需要远程访问
- 多个客户端

---

## Claude Code 集成

### 自动设置

```bash
# 在 Claude Code 中运行：
/claude add-mcp-server skill-seekers
```

或手动添加到 `~/.claude/mcp.json`：

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

### 使用

连接后，询问 Claude：

```
"列出可用配置"
"抓取 Django 文档"
"将 output/react 打包给 Gemini"
"使用 security-focus 工作流增强 output/my-skill"
```

---

## Cursor IDE 集成

### 设置

1. 启动 MCP 服务器：
```bash
skill-seekers-mcp --transport http --port 8765
```

2. 在 Cursor 设置 → MCP 中：
   - 名称：`skill-seekers`
   - URL：`http://localhost:8765`

### 使用

在 Cursor 聊天中：

```
"从当前项目创建一个技能"
"分析此代码库并生成 cursorrules 文件"
```

---

## Windsurf 集成

### 设置

1. 启动 MCP 服务器：
```bash
skill-seekers-mcp --transport http --port 8765
```

2. 在 Windsurf 设置中：
   - 添加 MCP 服务器端点：`http://localhost:8765`

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

## 常见工作流

### 工作流 1：文档技能

```
User: "Create a skill from React docs"
Claude: ▶️ scrape_docs({"url": "https://react.dev/"})
        ⏳ Scraping...
        ✅ Created output/react/
        
        ▶️ package_skill({"skill_directory": "output/react/", "target": "claude"})
        ✅ Created output/react-claude.zip
        
        Skill ready! Upload to Claude?
```

### 工作流 2：GitHub 分析

```
User: "Analyze the facebook/react repo"
Claude: ▶️ scrape_github({"repo": "facebook/react"})
        ⏳ Analyzing...
        ✅ Created output/react/
        
        ▶️ enhance_skill({"skill_directory": "output/react/", "workflow": "architecture-comprehensive"})
        ✅ Enhanced with architecture analysis
```

### 工作流 3：多平台导出

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

## 配置

### 环境变量

在 `~/.claude/mcp.json` 中设置，或在启动服务器前设置：

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
export OPENAI_API_KEY=sk-...
export GITHUB_TOKEN=ghp_...
```

### 服务器选项

```bash
# 调试模式
skill-seekers-mcp --verbose

# 自定义端口
skill-seekers-mcp --port 8080

# 允许所有来源（CORS）
skill-seekers-mcp --cors
```

---

## 安全

### 仅限本地（stdio）

```bash
# 仅本地 Claude Code 可访问
skill-seekers-mcp
```

### 带认证的 HTTP

```bash
# 使用带认证的反向代理
# nginx、traefik 等
```

### API 密钥保护

```bash
# 不要硬编码密钥
# 使用环境变量
# 或使用密钥管理
```

---

## 故障排除

### "Server not found"

```bash
# 检查是否在运行
curl http://localhost:8765/health

# 重启
skill-seekers-mcp --transport http --port 8765
```

### "Tool not available"

```bash
# 检查版本
skill-seekers-mcp --version

# 更新
pip install --upgrade skill-seekers[mcp]
```

### "Connection refused"

```bash
# 检查端口
lsof -i :8765

# 使用不同端口
skill-seekers-mcp --port 8766
```

---

## 另请参阅

- [MCP 参考文档](../reference/MCP_REFERENCE.md) - 完整工具参考
- [MCP 工具深入](mcp-tools.md) - 高级用法
- [MCP 协议](https://modelcontextprotocol.io/) - 官方 MCP 文档
