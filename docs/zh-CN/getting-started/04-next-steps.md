# 下一步

> **Skill Seekers v3.6.0**  
> **创建你的第一个 skill 之后该去哪里**

---

## 你已创建了你的第一个 Skill！🎉

现在呢？这里是你成为 Skill Seekers 高级用户的路线图。

---

## 立即下一步

### 1. 尝试不同来源

你已经做过文档抓取。现在试试：

```bash
# GitHub 仓库
skill-seekers create facebook/react --name react

# 本地项目
skill-seekers create ./my-project --name my-project

# PDF 文档
skill-seekers create manual.pdf --name manual
```

### 2. 打包到多个平台

你的 skill 可以在任何地方工作：

```bash
# 创建一次
skill-seekers create https://docs.djangoproject.com/ --name django

# 打包到所有平台
for platform in claude gemini openai langchain; do
  skill-seekers package output/django/ --target $platform
done
```

### 3. 扫描整个项目（AI 驱动）

用一条命令为真实项目引导生成完整的知识库 —— 参见
[扫描项目](../../getting-started/05-scan-a-project.md)：

```bash
skill-seekers scan ./my-react-app --out ./configs/scanned/
# 为每个检测到的框架生成一份配置 + my-react-app-codebase.json
```

### 4. 探索增强工作流

```bash
# 查看可用工作流
skill-seekers workflows list

# 应用安全聚焦分析
skill-seekers create ./my-project --enhance-workflow security-focus

# 链式多个工作流
skill-seekers create ./my-project \
  --enhance-workflow security-focus \
  --enhance-workflow api-documentation
```

---

## 学习路径

### 初学者（你在这里）

✅ 创建了第一个 skill  
⬜ 尝试不同的来源类型  
⬜ 打包到多个平台  
⬜ 使用预设配置

**资源：**
- [核心概念](../user-guide/01-core-concepts.md)
- [抓取指南](../user-guide/02-scraping.md)
- [打包指南](../user-guide/04-packaging.md)

### 中级

⬜ 自定义配置  
⬜ 多来源抓取  
⬜ 增强工作流  
⬜ 向量数据库导出  
⬜ MCP server 设置

**资源：**
- [配置格式](../reference/CONFIG_FORMAT.md)
- [增强指南](../user-guide/03-enhancement.md)
- [高级：多来源](../advanced/multi-source.md)
- [高级：MCP Server](../advanced/mcp-server.md)

### 高级

⬜ 自定义工作流创建  
⬜ 与 CI/CD 集成  
⬜ API 程序化使用  
⬜ 为项目做贡献

**资源：**
- [高级：自定义工作流](../advanced/custom-workflows.md)
- [MCP 参考](../reference/MCP_REFERENCE.md)
- [API 参考](../advanced/api-reference.md)
- [贡献指南](../../../CONTRIBUTING.md)

---

## 常见用例

### 用例 1：团队文档

**目标：** 为你团队的所有框架创建 skills

```bash
# 创建一个脚本
for framework in django react vue fastapi; do
  echo "Processing $framework..."
  skill-seekers install --config $framework --target claude
done
```

### 用例 2：GitHub 仓库分析

**目标：** 分析你的代码库以获得 AI 辅助

```bash
# 分析你的仓库
skill-seekers create your-org/your-repo --preset comprehensive

# 安装到 Cursor 以获得编码辅助
skill-seekers install-agent output/your-repo/ --agent cursor
```

### 用例 3：RAG Pipeline

**目标：** 将文档输入向量数据库

```bash
# 创建 skill
skill-seekers create https://docs.djangoproject.com/ --name django

# 导出到 ChromaDB
skill-seekers package output/django/ --target chroma

# 或直接导出
export_to_chroma(skill_directory="output/django/")
```

### 用例 4：文档监控

**目标：** 自动保持 skills 最新

```bash
# 检查变化
skill-seekers update output/django/ --check-changes

# 如有变化则更新
skill-seekers update output/django/
```

---

## 按兴趣领域

### 面向 AI Skill 构建者

为 Claude、Gemini 或 ChatGPT 构建 skills？

**学习：**
- 提升质量的增强工作流
- 多来源组合以获得全面的 skills
- 上传前的质量评分

**命令：**
```bash
skill-seekers quality output/my-skill/ --report
skill-seekers create ./my-project --enhance-workflow architecture-comprehensive
```

### 面向 RAG 工程师

构建检索增强生成系统？

**学习：**
- 向量数据库导出（Chroma、Weaviate、Qdrant、FAISS）
- 分块策略
- Embedding 集成

**命令：**
```bash
skill-seekers package output/my-skill/ --target chroma
skill-seekers package output/my-skill/ --target weaviate
skill-seekers package output/my-skill/ --target langchain
```

### 面向 AI 编码助手用户

使用 Cursor、Windsurf 或 Cline？

**学习：**
- 本地代码库分析
- Agent 安装
- 模式检测

**命令：**
```bash
skill-seekers create ./my-project --preset comprehensive
skill-seekers install-agent output/my-project/ --agent cursor
```

### 面向 DevOps/SRE

自动化文档工作流？

**学习：**
- CI/CD 集成
- MCP server 设置
- 配置来源

**命令：**
```bash
# 启动 MCP server
python -m skill_seekers.mcp.server_fastmcp --transport http --port 8765
```

---

## 推荐阅读顺序

### 快速参考（每篇 5 分钟）

1. [CLI 参考](../reference/CLI_REFERENCE.md) - 所有命令
2. [配置格式](../reference/CONFIG_FORMAT.md) - JSON 规范
3. [环境变量](../reference/ENVIRONMENT_VARIABLES.md) - 设置

### 用户指南（每篇 10-15 分钟）

1. [核心概念](../user-guide/01-core-concepts.md) - 工作原理
2. [抓取指南](../user-guide/02-scraping.md) - 来源选项
3. [增强指南](../user-guide/03-enhancement.md) - AI 选项
4. [工作流指南](../user-guide/05-workflows.md) - 预设工作流
5. [故障排除](../user-guide/06-troubleshooting.md) - 常见问题

### 高级主题（每篇 20+ 分钟）

1. [多来源抓取](../advanced/multi-source.md)
2. [MCP Server 设置](../advanced/mcp-server.md)
3. [自定义工作流](../advanced/custom-workflows.md)
4. [API 参考](../advanced/api-reference.md)

---

## 加入社区

### 获取帮助

- **GitHub Issues:** https://github.com/yusufkaraaslan/Skill_Seekers/issues
- **Discussions:** 分享用例并获得建议
- **Discord:** [README 中的链接]

### 贡献

- **Bug 报告：** 帮助改进项目
- **功能请求：** 建议新功能
- **文档：** 改进这些文档
- **代码：** 提交 PR

请参阅 [贡献指南](../../../CONTRIBUTING.md)

### 保持更新

- **Watch** GitHub 仓库
- **Star** 这个项目
- **Follow** Twitter：@_yUSyUS_

---

## 快速命令参考

```bash
# 核心工作流
skill-seekers create <source>              # 创建 skill
skill-seekers package <dir> --target <p>   # 打包
skill-seekers upload <file> --target <p>   # 上传

# 分析
skill-seekers scan  <dir>    # 本地代码库
skill-seekers create  <owner/repo>   # GitHub 仓库
skill-seekers create --pdf <file>             # PDF

# 工具
skill-seekers estimate <config>            # 页面估算
skill-seekers quality <dir>                # 质量检查
skill-seekers resume                       # 恢复任务
skill-seekers workflows list               # 列出工作流

# MCP server
skill-seekers-mcp                          # 启动 MCP server
```

---

## 记住

- **从简单开始** - 使用 `create` 加默认参数
- **先试运行** - 使用 `--dry-run` 预览
- **迭代** - 增强、打包、测试、重复
- **分享** - 打包到多个平台
- **自动化** - 使用 `install` 实现一键工作流

---

## 你已经准备好了！

去构建一些令人惊叹的东西吧。文档就是你的牡蛎。🦪

```bash
# 你的下一个 skill 在等你
skill-seekers create <your-source-here>
```
