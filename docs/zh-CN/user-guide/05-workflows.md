# 工作流指南

> **Skill Seekers v3.6.0**
> **用于专门分析的增强工作流预设**

---

## 什么是工作流？

工作流是**多阶段 AI 增强管道**，对你的 skill 应用专门分析：

```
基础 Skill ──▶ 工作流: Security-Focus ──▶ 安全增强的 Skill
                    Stage 1: Overview
                    Stage 2: Vulnerability Analysis
                    Stage 3: Best Practices
                    Stage 4: Compliance
```

---

## 内置预设

Skill Seekers 包含 5 个内置工作流预设：

| 预设 | 阶段 | 适用于 |
|--------|--------|----------|
| `default` | 2 | 通用改进 |
| `minimal` | 1 | 轻度润色 |
| `security-focus` | 4 | 安全分析 |
| `architecture-comprehensive` | 7 | 深度架构审查 |
| `api-documentation` | 3 | API 文档重点 |

---

## 使用工作流

### 列出可用工作流

```bash
skill-seekers workflows list
```

**输出：**
```
Bundled Workflows:
  - default (built-in)
  - minimal (built-in)
  - security-focus (built-in)
  - architecture-comprehensive (built-in)
  - api-documentation (built-in)

User Workflows:
  - my-custom (user)
```

### 应用工作流

```bash
# 在 skill 创建期间
skill-seekers create <source> --enhance-workflow security-focus

# 多个工作流（链式）
skill-seekers create <source> \
  --enhance-workflow security-focus \
  --enhance-workflow api-documentation
```

### 显示工作流内容

```bash
skill-seekers workflows show security-focus
```

**输出：**
```yaml
name: security-focus
description: Security analysis workflow
stages:
  - name: security-overview
    prompt: Analyze security features and mechanisms...
    
  - name: vulnerability-analysis
    prompt: Identify common vulnerabilities...
    
  - name: best-practices
    prompt: Document security best practices...
    
  - name: compliance
    prompt: Map to security standards...
```

---

## 工作流预设详解

### Default 工作流

**阶段：** 2
**用途：** 通用改进

```yaml
stages:
  - name: structure
    prompt: Improve overall structure and organization
  - name: content
    prompt: Enhance content quality and examples
```

**何时使用：** 你希望进行标准增强，无需特定重点。

---

### Minimal 工作流

**阶段：** 1
**用途：** 轻度润色

```yaml
stages:
  - name: cleanup
    prompt: Basic formatting and cleanup
```

**何时使用：** 你需要快速、最小化的增强。

---

### Security-Focus 工作流

**阶段：** 4
**用途：** 安全分析和建议

```yaml
stages:
  - name: security-overview
    prompt: Identify and document security features...
    
  - name: vulnerability-analysis
    prompt: Analyze potential vulnerabilities...
    
  - name: security-best-practices
    prompt: Document security best practices...
    
  - name: compliance-mapping
    prompt: Map to OWASP, CWE, and other standards...
```

**适用于：**
- 安全库
- 认证系统
- API 框架
- 任何处理敏感数据的代码

**示例：**
```bash
skill-seekers create oauth2-server --enhance-workflow security-focus
```

---

### Architecture-Comprehensive 工作流

**阶段：** 7
**用途：** 深度架构分析

```yaml
stages:
  - name: system-overview
    prompt: Document high-level architecture...
    
  - name: component-analysis
    prompt: Analyze key components...
    
  - name: data-flow
    prompt: Document data flow patterns...
    
  - name: integration-points
    prompt: Identify external integrations...
    
  - name: scalability
    prompt: Document scalability considerations...
    
  - name: deployment
    prompt: Document deployment patterns...
    
  - name: maintenance
    prompt: Document operational concerns...
```

**适用于：**
- 大型框架
- 分布式系统
- 微服务
- 企业平台

**示例：**
```bash
skill-seekers create kubernetes/kubernetes \
  --enhance-workflow architecture-comprehensive
```

---

### API-Documentation 工作流

**阶段：** 3
**用途：** API 重点增强

```yaml
stages:
  - name: endpoint-catalog
    prompt: Catalog all API endpoints...
    
  - name: request-response
    prompt: Document request/response formats...
    
  - name: error-handling
    prompt: Document error codes and handling...
```

**适用于：**
- REST APIs
- GraphQL 服务
- SDKs
- 库文档

**示例：**
```bash
skill-seekers create https://api.example.com/docs \
  --enhance-workflow api-documentation
```

---

## 链式多个工作流

顺序应用多个工作流：

```bash
skill-seekers create <source> \
  --enhance-workflow security-focus \
  --enhance-workflow api-documentation
```

**执行顺序：**
1. 运行 `security-focus` 工作流
2. 在结果上运行 `api-documentation` 工作流
3. 最终的 skill 同时具有安全和 API 重点

**使用场景：** 带安全考虑的 API

---

## 自定义工作流

### 创建自定义工作流

创建一个 YAML 文件：

```yaml
# my-workflow.yaml
name: performance-focus
description: Performance optimization workflow

variables:
  target_latency: "100ms"
  target_throughput: "1000 req/s"

stages:
  - name: performance-overview
    type: builtin
    target: skill_md
    prompt: |
      Analyze performance characteristics of this framework.
      Focus on:
      - Benchmark results
      - Optimization opportunities
      - Scalability limits
    
  - name: optimization-guide
    type: custom
    uses_history: true
    prompt: |
      Based on the previous analysis, create an optimization guide.
      Target latency: {target_latency}
      Target throughput: {target_throughput}
      
      Previous results: {previous_results}
```

### 安装工作流

```bash
# 添加到用户工作流
skill-seekers workflows add my-workflow.yaml

# 使用自定义名称
skill-seekers workflows add my-workflow.yaml --name perf-guide
```

### 使用自定义工作流

```bash
skill-seekers create <source> --enhance-workflow performance-focus
```

### 更新工作流

```bash
# 编辑文件，然后：
skill-seekers workflows add my-workflow.yaml --name performance-focus
```

### 移除工作流

```bash
skill-seekers workflows remove performance-focus
```

---

## 工作流变量

在运行时向工作流传递变量：

### 在工作流定义中

```yaml
variables:
  target_audience: "beginners"
  focus_area: "security"
```

### 在运行时覆盖

```bash
skill-seekers create <source> \
  --enhance-workflow my-workflow \
  --var target_audience=experts \
  --var focus_area=performance
```

### 在 Prompt 中使用

```yaml
stages:
  - name: customization
    prompt: |
      Tailor content for {target_audience}.
      Focus on {focus_area} aspects.
```

---

## 内联阶段

无需创建工作流文件即可添加一次性增强阶段：

```bash
skill-seekers create <source> \
  --enhance-stage "performance:Analyze performance characteristics"
```

**格式：** `name:prompt`

**多个阶段：**
```bash
skill-seekers create <source> \
  --enhance-stage "perf:Analyze performance" \
  --enhance-stage "security:Check security" \
  --enhance-stage "examples:Add more examples"
```

---

## 工作流试运行

预览工作流将执行的操作，而不实际执行：

```bash
skill-seekers create <source> \
  --enhance-workflow security-focus \
  --workflow-dry-run
```

**输出：**
```
Workflow: security-focus
Stages:
  1. security-overview
     - Will analyze security features
     - Target: skill_md
     
  2. vulnerability-analysis
     - Will identify vulnerabilities
     - Target: skill_md
     
  3. best-practices
     - Will document best practices
     - Target: skill_md
     
  4. compliance
     - Will map to standards
     - Target: skill_md

Execution order: Sequential
Estimated time: ~4 minutes
```

---

## 工作流验证

验证工作流语法：

```bash
# 验证内置工作流
skill-seekers workflows validate security-focus

# 验证文件
skill-seekers workflows validate ./my-workflow.yaml
```

---

## 复制工作流

复制内置工作流以进行自定义：

```bash
# 复制单个工作流
skill-seekers workflows copy security-focus

# 复制多个
skill-seekers workflows copy security-focus api-documentation minimal

# 编辑副本
nano ~/.config/skill-seekers/workflows/security-focus.yaml
```

---

## 最佳实践

### 1. 从 Default 开始

```bash
# 默认值适用于大多数情况
skill-seekers create <source>
```

### 2. 根据需要添加特定工作流

```bash
# 安全重点的项目
skill-seekers create auth-library --enhance-workflow security-focus

# API 项目
skill-seekers create api-framework --enhance-workflow api-documentation
```

### 3. 链式组合以进行全面分析

```bash
# 大型框架：架构 + 安全
skill-seekers create kubernetes/kubernetes \
  --enhance-workflow architecture-comprehensive \
  --enhance-workflow security-focus
```

### 4. 为专门需求创建自定义工作流

```bash
# 为你的领域创建自定义工作流
skill-seekers workflows add ml-workflow.yaml
skill-seekers create ml-framework --enhance-workflow ml-focus
```

### 5. 使用变量以获得灵活性

```bash
# 同一工作流，不同目标
skill-seekers create <source> \
  --enhance-workflow my-workflow \
  --var audience=beginners

skill-seekers create <source> \
  --enhance-workflow my-workflow \
  --var audience=experts
```

---

## 故障排除

### "未找到工作流"

```bash
# 列出可用工作流
skill-seekers workflows list

# 检查拼写
skill-seekers create <source> --enhance-workflow security-focus
```

### "无效的工作流 YAML"

```bash
# 验证
skill-seekers workflows validate ./my-workflow.yaml

# 常见问题：
# - 缺少 'stages' 键
# - 无效的 YAML 语法
# - 未定义的变量引用
```

### "工作流阶段失败"

```bash
# 检查阶段详情
skill-seekers workflows show my-workflow

# 尝试试运行
skill-seekers create <source> \
  --enhance-workflow my-workflow \
  --workflow-dry-run
```

---

## 总结

| 方法 | 何时使用 |
|----------|-------------|
| **Default** | 大多数情况 |
| **Security-Focus** | 安全敏感项目 |
| **Architecture** | 大型框架、系统 |
| **API-Docs** | API 框架、库 |
| **Custom** | 专门领域 |
| **Chaining** | 需要多重视角 |

---

## 下一步

- [Custom Workflows](../advanced/custom-workflows.md) - 高级工作流创建
- [Enhancement Guide](03-enhancement.md) - 增强基础
- [MCP Reference](../reference/MCP_REFERENCE.md) - 通过 MCP 使用工作流
