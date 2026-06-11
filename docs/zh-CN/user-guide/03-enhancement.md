# 增强指南

> **Skill Seekers v3.6.0**
> **AI 驱动的 skill 质量提升**

---

## 什么是增强？

增强使用 AI 来提升生成的 SKILL.md 文件的质量：

```
基础 SKILL.md ──▶ AI 增强器 ──▶ 增强后的 SKILL.md
(100 行)         (60 秒)        (400+ 行)
     ↓                                  ↓
  稀疏的                          全面的
  示例                            包含模式、
                                  导航和深度内容
```

---

## 增强级别

选择应用多少增强：

| 级别 | 效果 | 时间 | 费用 |
|-------|--------------|------|------|
| **0** | 不增强 | 0 秒 | 免费 |
| **1** | 仅 SKILL.md | ~30 秒 | 低 |
| **2** | + 架构/配置 | ~60 秒 | 中等 |
| **3** | 完全增强 | ~2 分钟 | 较高 |

**默认：** Level 2（推荐的平衡点）

---

## 增强模式

### API 模式（如果密钥可用则默认）

通过 `AgentClient` 使用任意受支持的 AI 提供商 API。提供商：Anthropic（Claude）、Moonshot/Kimi、Google Gemini、OpenAI。

**要求：**
```bash
# 设置以下任意一个即可激活 API 模式：
export ANTHROPIC_API_KEY=sk-ant-...   # Claude
export MOONSHOT_API_KEY=...           # Kimi
export GOOGLE_API_KEY=...             # Gemini
export OPENAI_API_KEY=...             # OpenAI
```

如果设置了多个密钥，按优先顺序取第一个：Anthropic → Gemini →
OpenAI → Moonshot/Kimi。可通过 `SKILL_SEEKER_PROVIDER` 强制指定某一个
（参见[环境变量](../reference/ENVIRONMENT_VARIABLES.md)）。

**用法：**
```bash
# 自动检测 API 模式
skill-seekers create <source>

# 显式指定目标平台（API 模式）
skill-seekers enhance output/my-skill/ --target claude
```

**优点：**
- 快速（~60 秒）
- 无需本地设置

**缺点：**
- 每个 skill 费用约 $0.10-0.30
- 需要 API key

---

### LOCAL 模式（无密钥则默认）

通过 `AgentClient` 使用本地 AI 编程代理。支持 Claude Code、Kimi Code、Codex、Copilot、OpenCode 或自定义代理。

**要求：**
- 已安装任意一个受支持的代理（Claude Code、Codex、Copilot、OpenCode、Kimi）

**用法：**
```bash
# 自动检测 LOCAL 模式（无 API key），默认使用 Claude Code
skill-seekers create <source>

# 使用其他本地代理
skill-seekers enhance output/my-skill/ --agent codex
skill-seekers enhance output/my-skill/ --agent copilot
skill-seekers enhance output/my-skill/ --agent kimi
skill-seekers enhance output/my-skill/ --agent opencode

# 自定义代理
skill-seekers enhance output/my-skill/ --agent custom --agent-cmd "my-agent {prompt_file}"
```

**优点：**
- 免费（需有代理订阅）
- 更好的质量（完整上下文）
- 代理无关 —— 适用于任何受支持的编程代理

**缺点：**
- 需要本地编程代理
- 稍慢（~60-120 秒）

---

## 如何增强

### 创建期间

```bash
# 默认增强（level 2）
skill-seekers create <source>

# 不增强（最快）
skill-seekers create <source> --enhance-level 0

# 最大增强
skill-seekers create <source> --enhance-level 3
```

### 创建之后

```bash
# 增强现有 skill
skill-seekers enhance output/my-skill/

# 使用特定 agent
skill-seekers enhance output/my-skill/ --agent claude

# 设置超时
skill-seekers enhance output/my-skill/ --timeout 1200
```

### 后台模式

```bash
# 后台运行
skill-seekers enhance output/my-skill/ --background

# 检查状态
skill-seekers enhance-status output/my-skill/

# 实时查看
skill-seekers enhance-status output/my-skill/ --watch
```

---

## 增强工作流

使用预设工作流应用专门的 AI 分析。

### 内置预设

| 预设 | 阶段 | 重点 |
|--------|--------|-------|
| `default` | 2 | 通用改进 |
| `minimal` | 1 | 轻度润色 |
| `security-focus` | 4 | 安全分析 |
| `architecture-comprehensive` | 7 | 深度架构 |
| `api-documentation` | 3 | API 文档重点 |

### 使用工作流

```bash
# 应用工作流
skill-seekers create <source> --enhance-workflow security-focus

# 链式多个工作流
skill-seekers create <source> \
  --enhance-workflow security-focus \
  --enhance-workflow api-documentation

# 列出可用工作流
skill-seekers workflows list

# 显示工作流内容
skill-seekers workflows show security-focus
```

### 自定义工作流

创建你自己的 YAML 工作流：

```yaml
# my-workflow.yaml
name: my-custom
stages:
  - name: overview
    prompt: "Add comprehensive overview section"
  - name: examples
    prompt: "Add practical code examples"
```

```bash
# 添加工作流
skill-seekers workflows add my-workflow.yaml

# 使用它
skill-seekers create <source> --enhance-workflow my-custom
```

---

## 增强添加的内容

### Level 1：SKILL.md 改进

- 更好的结构和组织
- 改进的描述
- 修复格式
- 添加导航

### Level 2：架构与配置（默认）

Level 1 的所有内容，加上：

- 架构概述
- 配置示例
- 模式文档
- 最佳实践

### Level 3：完全增强

Level 2 的所有内容，加上：

- 深度代码示例
- 常见陷阱
- 性能提示
- 集成指南

---

## 增强工作流详情

### Security-Focus 工作流

4 个阶段：
1. **安全概述** - 识别安全功能
2. **漏洞分析** - 常见问题
3. **最佳实践** - 安全编码模式
4. **合规性** - 安全标准

### Architecture-Comprehensive 工作流

7 个阶段：
1. **系统概述** - 高层架构
2. **组件分析** - 关键组件
3. **数据流** - 数据如何流动
4. **集成点** - 外部连接
5. **可扩展性** - 性能考虑
6. **部署** - 基础设施
7. **维护** - 运维问题

### API-Documentation 工作流

3 个阶段：
1. **端点目录** - 所有 API 端点
2. **请求/响应** - 详细示例
3. **错误处理** - 常见错误

---

## 监控增强

### 检查状态

```bash
# 当前状态
skill-seekers enhance-status output/my-skill/

# JSON 输出（用于脚本）
skill-seekers enhance-status output/my-skill/ --json

# 查看模式
skill-seekers enhance-status output/my-skill/ --watch --interval 10
```

### 进程状态值

| 状态 | 含义 |
|--------|---------|
| `running` | 增强进行中 |
| `completed` | 成功完成 |
| `failed` | 发生错误 |
| `pending` | 等待开始 |

---

## 何时跳过增强

在以下情况跳过增强：

- **测试：** 开发期间快速迭代
- **批量处理：** 处理多个 skill，稍后增强最佳 skill
- **自定义处理：** 你有自己的增强管道
- **时间紧迫：** 需要立即获取结果

```bash
# 创建期间跳过
skill-seekers create <source> --enhance-level 0

# 稍后增强最佳 skill
skill-seekers enhance output/best-skill/
```

---

## 增强最佳实践

### 1. 大多数情况下使用 Level 2

```bash
# 默认值通常很合适
skill-seekers create <source>
```

### 2. 应用领域特定的工作流

```bash
# 安全审查
skill-seekers create <source> --enhance-workflow security-focus

# API 重点
skill-seekers create <source> --enhance-workflow api-documentation
```

### 3. 链式组合以进行全面分析

```bash
# 多个视角
skill-seekers create <source> \
  --enhance-workflow security-focus \
  --enhance-workflow architecture-comprehensive
```

### 4. 使用 LOCAL 模式以获得质量

```bash
# 使用 Claude Code 获得更好结果
export ANTHROPIC_API_KEY=""  # 取消设置以强制使用 LOCAL
skill-seekers enhance output/my-skill/
```

### 5. 迭代增强

```bash
# 创建时不增强
skill-seekers create <source> --enhance-level 0

# 审查并增强
skill-seekers enhance output/my-skill/
# 再次审查...
skill-seekers enhance output/my-skill/  # 再次运行以进一步润色
```

---

## 故障排除

### "增强失败：无 API key"

**解决方案：**
```bash
# 设置 API key
export ANTHROPIC_API_KEY=sk-ant-...

# 或使用 LOCAL 模式（无 API key 时自动选择；指定一个已安装的代理）
skill-seekers enhance output/my-skill/ --agent claude
```

### "增强超时"

**解决方案：**
```bash
# 增加超时
skill-seekers enhance output/my-skill/ --timeout 1200

# 或使用后台模式
skill-seekers enhance output/my-skill/ --background
```

### "未找到 Claude Code"（LOCAL 模式）

**解决方案：**
```bash
# 安装 Claude Code
# 参见: https://claude.ai/code

# 或切换到 API 模式（设置密钥后自动使用）
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers enhance output/my-skill/
```

### "未找到工作流"

**解决方案：**
```bash
# 列出可用工作流
skill-seekers workflows list

# 检查拼写
skill-seekers create <source> --enhance-workflow security-focus
```

---

## 费用估算

### API 模式费用

| Skill 大小 | Level 1 | Level 2 | Level 3 |
|------------|---------|---------|---------|
| 小型 (< 50 页) | $0.02 | $0.05 | $0.10 |
| 中型 (50-200 页) | $0.05 | $0.10 | $0.20 |
| 大型 (200-500 页) | $0.10 | $0.20 | $0.40 |

*费用为近似值，取决于实际内容。*

### LOCAL 模式费用

使用 Claude Code Max 订阅免费（约 $20/月）。

---

## 总结

| 方法 | 何时使用 |
|----------|-------------|
| **Level 0** | 测试、批量处理 |
| **Level 2 (默认)** | 大多数使用场景 |
| **Level 3** | 需要最高质量 |
| **API 模式** | 速度优先，无 Claude Code |
| **LOCAL 模式** | 质量优先，Max 套餐免费 |
| **工作流** | 领域特定需求 |

---

## 下一步

- [工作流指南](05-workflows.md) - 自定义工作流创建
- [打包指南](04-packaging.md) - 导出增强后的 skill
- [MCP Reference](../reference/MCP_REFERENCE.md) - 通过 MCP 增强
