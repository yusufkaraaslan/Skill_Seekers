# 自定义工作流指南

> **Skill Seekers v3.6.0**  
> **创建自定义 AI 增强工作流**

---

## 什么是自定义工作流？

工作流是 YAML 定义的多阶段 AI 增强流水线：

```yaml
my-workflow.yaml
├── name
├── description
├── variables (optional)
└── stages (1-10)
    ├── name
    ├── type (builtin/custom)
    ├── target (skill_md/references/)
    ├── prompt
    └── uses_history (optional)
```

---

## 基本工作流结构

```yaml
name: my-custom
description: Custom enhancement workflow

stages:
  - name: stage-one
    type: builtin
    target: skill_md
    prompt: |
      Improve the SKILL.md by adding...
      
  - name: stage-two
    type: custom
    target: references
    prompt: |
      Enhance the references by...
```

---

## 工作流字段

### 顶层

| 字段 | 必需 | 描述 |
|-------|----------|-------------|
| `name` | 是 | 工作流标识符 |
| `description` | 否 | 人类可读的描述 |
| `variables` | 否 | 可配置变量 |
| `stages` | 是 | 阶段定义数组 |

### 阶段字段

| 字段 | 必需 | 描述 |
|-------|----------|-------------|
| `name` | 是 | 阶段标识符 |
| `type` | 是 | `builtin` 或 `custom` |
| `target` | 是 | `skill_md` 或 `references` |
| `prompt` | 是 | AI 提示文本 |
| `uses_history` | 否 | 访问前一阶段结果 |

---

## 创建你的第一个工作流

### 示例：性能分析

```yaml
# performance.yaml
name: performance-focus
description: Analyze and document performance characteristics

variables:
  target_latency: "100ms"
  target_throughput: "1000 req/s"

stages:
  - name: performance-overview
    type: builtin
    target: skill_md
    prompt: |
      Add a "Performance" section to SKILL.md covering:
      - Benchmark results
      - Performance characteristics
      - Resource requirements
      
  - name: optimization-guide
    type: custom
    target: references
    uses_history: true
    prompt: |
      Create an optimization guide with:
      - Target latency: {target_latency}
      - Target throughput: {target_throughput}
      - Common bottlenecks
      - Optimization techniques
```

### 安装与使用

```bash
# 添加工作流
skill-seekers workflows add performance.yaml

# 使用它
skill-seekers create <source> --enhance-workflow performance-focus

# 使用自定义变量
skill-seekers create <source> \
  --enhance-workflow performance-focus \
  --var target_latency=50ms \
  --var target_throughput=5000req/s
```

---

## 阶段类型

### builtin

使用内置增强逻辑：

```yaml
stages:
  - name: structure-improvement
    type: builtin
    target: skill_md
    prompt: "Improve document structure"
```

### custom

完全自定义提示控制：

```yaml
stages:
  - name: custom-analysis
    type: custom
    target: skill_md
    prompt: |
      Your detailed custom prompt here...
      Can use {variables} and {history}
```

---

## 目标

### skill_md

增强主 SKILL.md 文件：

```yaml
stages:
  - name: improve-skill
    target: skill_md
    prompt: "Add comprehensive overview section"
```

### references

增强参考文件：

```yaml
stages:
  - name: improve-refs
    target: references
    prompt: "Add cross-references between files"
```

---

## 变量

### 定义变量

```yaml
variables:
  audience: "beginners"
  focus_area: "security"
  include_examples: true
```

### 使用变量

```yaml
stages:
  - name: customize
    prompt: |
      Tailor content for {audience}.
      Focus on {focus_area}.
      Include examples: {include_examples}
```

### 运行时覆盖

```bash
skill-seekers create <source> \
  --enhance-workflow my-workflow \
  --var audience=experts \
  --var focus_area=performance
```

---

## 历史传递

访问前一阶段的结果：

```yaml
stages:
  - name: analyze
    type: custom
    target: skill_md
    prompt: "Analyze security features"
    
  - name: document
    type: custom
    target: skill_md
    uses_history: true
    prompt: |
      Based on previous analysis:
      {previous_results}
      
      Create documentation...
```

---

## 高级示例：安全审查

```yaml
name: comprehensive-security
description: Multi-stage security analysis

variables:
  compliance_framework: "OWASP Top 10"
  risk_level: "high"

stages:
  - name: asset-inventory
    type: builtin
    target: skill_md
    prompt: |
      Document all security-sensitive components:
      - Authentication mechanisms
      - Authorization checks
      - Data validation
      - Encryption usage
      
  - name: threat-analysis
    type: custom
    target: skill_md
    uses_history: true
    prompt: |
      Based on assets: {all_history}
      
      Analyze threats for {compliance_framework}:
      - Threat vectors
      - Attack scenarios
      - Risk ratings ({risk_level} focus)
      
  - name: mitigation-guide
    type: custom
    target: references
    uses_history: true
    prompt: |
      Create mitigation guide:
      - Countermeasures
      - Best practices
      - Code examples
      - Testing strategies
```

---

## 验证

### 安装前验证

```bash
skill-seekers workflows validate ./my-workflow.yaml
```

### 常见错误

| 错误 | 原因 | 修复 |
|-------|-------|-----|
| `Missing 'stages'` | 无 stages 数组 | 添加 stages: |
| `Invalid type` | 不是 builtin/custom | 检查 type 字段 |
| `Undefined variable` | 已使用但未定义 | 添加到 variables: |

---

## 最佳实践

### 1. 从简单开始

```yaml
# 从 1-2 个阶段开始
name: simple
description: Simple workflow
stages:
  - name: improve
    type: builtin
    target: skill_md
    prompt: "Improve SKILL.md"
```

### 2. 使用清晰的阶段名称

```yaml
# 良好
stages:
  - name: security-overview
  - name: vulnerability-analysis
  
# 不佳
stages:
  - name: stage1
  - name: step2
```

### 3. 记录变量

```yaml
variables:
  # Target audience level: beginner, intermediate, expert
  audience: "intermediate"
  
  # Security focus area: owasp, pci, hipaa
  compliance: "owasp"
```

### 4. 增量测试

```bash
# 使用干运行测试
skill-seekers create <source> \
  --enhance-workflow my-workflow \
  --workflow-dry-run

# 然后实际运行
skill-seekers create <source> \
  --enhance-workflow my-workflow
```

### 5. 链式调用以进行复杂分析

```bash
# 使用多个工作流
skill-seekers create <source> \
  --enhance-workflow security-focus \
  --enhance-workflow performance-focus
```

---

## 共享工作流

### 导出工作流

```bash
# 获取工作流内容
skill-seekers workflows show my-workflow > my-workflow.yaml
```

### 与团队共享

```bash
# 添加到版本控制
git add my-workflow.yaml
git commit -m "Add custom security workflow"

# 团队成员安装
skill-seekers workflows add my-workflow.yaml
```

### 发布

提交到 Skill Seekers 社区：
- GitHub Discussions
- Skill Seekers 网站
- 文档贡献

---

## 另请参阅

- [工作流指南](../user-guide/05-workflows.md) - 使用工作流
- [MCP 参考](../reference/MCP_REFERENCE.md) - 通过 MCP 使用工作流
- [增强指南](../user-guide/03-enhancement.md) - 增强基础
