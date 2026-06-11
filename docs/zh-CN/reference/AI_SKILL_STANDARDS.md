# AI 技能标准与最佳实践（2026）

**版本：** 1.0
**最后更新：** 2026-01-11
**适用范围：** 面向 Claude、Gemini、OpenAI 及通用 LLM 的跨平台 AI 技能

## 目录

1. [引言](#引言)
2. [通用标准](#通用标准)
3. [平台特定指南](#平台特定指南)
4. [知识库设计模式](#知识库设计模式)
5. [质量评分标准](#质量评分标准)
6. [常见误区](#常见误区)
7. [面向未来](#面向未来)

---

## 引言

本文档基于 2026 年行业最佳实践、官方平台文档以及智能体 AI 系统中的新兴模式，确立了 AI 技能创建的权威标准。

### 什么是 AI 技能？

**AI 技能**是一个聚焦的知识包，可增强 AI 智能体在特定领域的能力。技能包括：
- **指令**：如何使用这些知识
- **上下文**：技能何时适用
- **资源**：参考文档、示例、模式
- **元数据**：发现、版本控制、平台兼容性

### 设计理念

现代 AI 技能遵循三个核心原则：

1. **渐进式披露**：仅在需要时加载信息（元数据 → 指令 → 资源）
2. **上下文经济**：每个 token 都在与对话历史竞争
3. **跨平台可移植性**：面向开放的 Agent Skills 标准进行设计

---

## 通用标准

这些标准适用于**所有平台**（Claude、Gemini、OpenAI、通用）。

### 1. 命名约定

**格式**：动名词形式（动词 + -ing）

**原因**：清晰描述技能提供的活动或能力。

**示例**：
- ✅ "Building React Applications"
- ✅ "Working with Django REST Framework"
- ✅ "Analyzing Godot 4.x Projects"
- ❌ "React Documentation"（被动，不清晰）
- ❌ "Django Guide"（模糊）

**实现**：
```yaml
name: building-react-applications  # kebab-case, gerund form
description: Building modern React applications with hooks, routing, and state management
```

### 2. Description 字段（对发现至关重要）

**格式**：第三人称、可执行、同时包含"做什么"和"何时用"

**原因**：会被注入系统提示；人称不一致会导致发现问题。

**结构**：
```
[What it does]. Use when [specific triggers/scenarios].
```

**示例**：
- ✅ "Building modern React applications with TypeScript, hooks, and routing. Use when implementing React components, managing state, or configuring build tools."
- ✅ "Analyzing Godot 4.x game projects with GDScript patterns. Use when debugging game logic, optimizing performance, or implementing new features in Godot."
- ❌ "I will help you with React"（第一人称，模糊）
- ❌ "Documentation for Django"（缺少 when 子句）

### 3. Token 预算（渐进式披露）

**Token 分配**：
- **元数据加载**：约 100 个 token（YAML frontmatter + description）
- **完整指令**：<5,000 个 token（不含参考文件的主 SKILL.md）
- **捆绑资源**：仅按需加载

**原因**：token 效率至关重要——未使用的上下文会浪费容量。

**最佳实践**：
```markdown
## Quick Reference
*30-second overview with most common patterns*

[Core content - 3,000-4,500 tokens]

## Extended Reference
*See references/api.md for complete API documentation*
```

### 4. 简洁性与相关性

**原则**：
- 每个句子必须提供**独特价值**
- 删除冗余、填充和"锦上添花"的信息
- 优先**可执行**而非**解释性**内容
- 使用渐进式披露：快速参考 → 深入探讨 → 参考文件

**转换示例**：

**改写前**（130 个 token）：
```
React is a popular JavaScript library for building user interfaces.
It was created by Facebook and is now maintained by Meta and the
open-source community. React uses a component-based architecture
where you build encapsulated components that manage their own state.
```

**改写后**（35 个 token）：
```
Component-based UI library. Build reusable components with local
state, compose them into complex UIs, and efficiently update the
DOM via virtual DOM reconciliation.
```

### 5. 结构与组织

**必需的章节**（按顺序）：

```markdown
---
name: skill-name
description: [What + When in third person]
---

# Skill Title

[1-2 sentence elevator pitch]

## 💡 When to Use This Skill

[3-5 specific scenarios with trigger phrases]

## ⚡ Quick Reference

[30-second overview, most common patterns]

## 📝 Code Examples

[Real-world, tested, copy-paste ready]

## 🔧 API Reference

[Core APIs, signatures, parameters - link to full reference]

## 🏗️ Architecture

[Key patterns, design decisions, trade-offs]

## ⚠️ Common Issues

[Known problems, workarounds, gotchas]

## 📚 References

[Links to deeper documentation]
```

**可选章节**：
- 安装
- 配置
- 测试模式
- 迁移指南
- 性能提示

### 6. 代码示例质量

**标准**：
- **经过测试**：来自官方文档、测试套件或生产代码
- **完整**：可直接复制粘贴，而非片段
- **带注解**：简要说明做什么/为什么，而非怎么做（代码本身展示怎么做）
- **渐进式**：基础 → 中级 → 高级
- **多样化**：覆盖常见用例（80% 的用户需求）

**格式**：
```markdown
### Example: User Authentication

```typescript
// Complete working example
import { useState } from 'react';
import { signIn } from './auth';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await signIn(email, password);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input value={email} onChange={e => setEmail(e.target.value)} />
      <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <button type="submit">Sign In</button>
    </form>
  );
}
```

**Why this works**: Demonstrates state management, event handling, async operations, and TypeScript types in a real-world pattern.
```

### 7. 跨平台兼容性

**文件结构**（开放 Agent Skills 标准）：
```
skill-name/
├── SKILL.md                # Main instructions (<5k tokens)
├── skill.yaml              # Metadata (optional, redundant with frontmatter)
├── references/             # On-demand resources
│   ├── api.md
│   ├── patterns.md
│   ├── examples/
│   │   ├── basic.md
│   │   └── advanced.md
│   └── index.md
└── resources/              # Optional: scripts, configs, templates
    ├── .clinerules
    └── templates/
```

**YAML Frontmatter**（所有平台均必需）：
```yaml
---
name: skill-name              # kebab-case, max 64 chars
description: >                # What + When, max 1024 chars
  Building modern React applications with TypeScript.
  Use when implementing React components or managing state.
version: 1.0.0                # Semantic versioning
platforms:                    # Tested platforms
  - claude
  - gemini
  - openai
  - markdown
tags:                         # Discovery keywords
  - react
  - typescript
  - frontend
  - web
---
```

---

## 平台特定指南

### Claude AI（Agent Skills）

**官方标准**：[Agent Skills 最佳实践](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

**关键差异**：
- **发现机制**：description 被注入系统提示——必须使用第三人称
- **Token 限制**：主 SKILL.md 约 5k 个 token（快速加载的硬性限制）
- **加载行为**：当 description 匹配用户意图时 Claude 才加载技能
- **资源访问**：参考文件通过文件读取按需加载

**最佳实践**：
- 在章节标题中使用 emoji（提升可扫描性）：💡 ⚡ 📝 🔧 🏗️ ⚠️ 📚
- 在 description 中包含"触发短语"："when implementing..."、"when debugging..."、"when configuring..."
- 保持快速参考极度简洁（用户最先看到这部分）
- 显式链接到参考文件："See `references/api.md` for complete API"

**示例 description**：
```yaml
description: >
  Building modern React applications with TypeScript, hooks, and routing.
  Use when implementing React components, managing application state,
  configuring build tools, or debugging React applications.
```

### Google Gemini（Actions）

**官方标准**：[Grounding 最佳实践](https://ai.google.dev/gemini-api/docs/google-search)

**关键差异**：
- **Grounding**：技能可借助 Google 搜索获取实时信息
- **Temperature**：保持 1.0（默认值）以获得最佳 grounding 效果
- **格式**：支持 tar.gz 包（不是 ZIP）
- **限制**：Gemini 3 中没有 Maps grounding（如需要请使用 Gemini 2.5）

**Grounding 增强**：
```markdown
## When to Use This Skill

Use this skill when:
- Implementing React components (skill provides patterns)
- Checking latest React version (grounding provides current info)
- Debugging common errors (skill + grounding = comprehensive solution)
```

**注意**：Grounding 费用为每 1,000 次查询 $14（截至 2026 年 1 月 5 日）。

### OpenAI（GPT Actions）

**官方标准**：[Custom GPT 关键指南](https://help.openai.com/en/articles/9358033-key-guidelines-for-writing-instructions-for-custom-gpts)

**关键差异**：
- **多步指令**：拆分为简单的原子步骤
- **触发/指令对**：使用分隔符区分不同场景
- **细致性提示**：包含 "take your time"、"take a deep breath"、"check your work"
- **不兼容**：GPT-5.1 推理模型尚不支持自定义 action

**格式**：
```markdown
## Instructions

### When user asks about React state management

1. First, identify the state management need (local vs global)
2. Then, recommend appropriate solution:
   - Local state → useState or useReducer
   - Global state → Context API or Redux
3. Provide code example matching their use case
4. Finally, explain trade-offs and alternatives

Take your time to understand the user's specific requirements before recommending a solution.

---

### When user asks about React performance

[Similar structured approach]
```

### 通用 Markdown（平台无关）

**用例**：文档站点、内部 wiki、非 LLM 工具

**格式**：带最少元数据的标准 markdown

**最佳实践**：注重人类可读性而非 token 经济

---

## 知识库设计模式

现代 AI 技能利用先进的 RAG（检索增强生成）模式来实现最优的知识交付。

### 1. 智能体 RAG（2026+ 推荐）

**模式**：由智能体编排的多查询、上下文感知检索

**架构**：
```
User Query → Agent Plans Retrieval → Multi-Source Fetch →
Context Synthesis → Response Generation → Self-Verification
```

**优势**：
- **自适应**：智能体根据对话上下文调整检索
- **准确**：多查询方式减少幻觉
- **高效**：仅检索当前查询所需内容

**在技能中的实现**：
```markdown
references/
├── index.md              # Navigation hub
├── api/                  # API references (structured)
│   ├── components.md
│   ├── hooks.md
│   └── utilities.md
├── patterns/             # Design patterns (by use case)
│   ├── state-management.md
│   └── performance.md
└── examples/             # Code examples (by complexity)
    ├── basic/
    ├── intermediate/
    └── advanced/
```

**原因**：智能体可以浏览这种结构，精确找到所需内容。

**来源**：
- [Traditional RAG vs. Agentic RAG - NVIDIA](https://developer.nvidia.com/blog/traditional-rag-vs-agentic-rag-why-ai-agents-need-dynamic-knowledge-to-get-smarter/)
- [What is Agentic RAG? - IBM](https://www.ibm.com/think/topics/agentic-rag)

### 2. GraphRAG（高级用例）

**模式**：用于复杂推理的知识图谱结构

**用例**：大型代码库、相互关联的概念、架构分析

**结构**：
```markdown
references/
├── entities/              # Nodes in knowledge graph
│   ├── Component.md
│   ├── Hook.md
│   └── Context.md
├── relationships/         # Edges in knowledge graph
│   ├── Component-uses-Hook.md
│   └── Context-provides-State.md
└── graph.json            # Machine-readable graph
```

**优势**：多跳推理、关系探索、复杂查询

**来源**：
- [Emerging Patterns in Building GenAI Products - Martin Fowler](https://martinfowler.com/articles/gen-ai-patterns/)

### 3. 多智能体系统（企业级规模）

**模式**：针对不同知识领域的专门智能体

**架构**：
```
Skill Repository
├── research-agent-skill/      # Explores information space
├── verification-agent-skill/  # Checks factual claims
├── synthesis-agent-skill/     # Combines findings
└── governance-agent-skill/    # Ensures compliance
```

**用例**：企业工作流、合规要求、多领域专业知识

**来源**：
- [4 Agentic AI Design Patterns - AIMultiple](https://research.aimultiple.com/agentic-ai-design-patterns/)

### 4. 反思模式（质量保障）

**模式**：在最终确定响应前进行自我评估和完善

**实现**：
```markdown
## Usage Instructions

When providing code examples:
1. Generate initial example
2. Evaluate against these criteria:
   - Completeness (can user copy-paste and run?)
   - Best practices (follows framework conventions?)
   - Security (no vulnerabilities?)
   - Performance (efficient patterns?)
3. Refine example based on evaluation
4. Present final version with explanations
```

**优势**：更高质量的输出、更少的错误、更好地遵循标准

**来源**：
- [4 Agentic AI Design Patterns - AIMultiple](https://research.aimultiple.com/agentic-ai-design-patterns/)

### 5. 向量数据库集成

**模式**：基于嵌入的语义搜索，实现按概念检索

**用例**：大型文档集、概念性查询、相似度搜索

**结构**：
- 将参考文档存储为嵌入向量
- 用户查询 → 嵌入 → 相似度搜索 → top-k 检索
- 智能体综合检索到的分块

**工具**：
- Pinecone、Weaviate、Chroma、Qdrant
- Model Context Protocol（MCP）用于标准化访问

**来源**：
- [Anatomy of an AI agent knowledge base - InfoWorld](https://www.infoworld.com/article/4091400/anatomy-of-an-ai-agent-knowledge-base.html)

---

## 质量评分标准

使用此评分标准在 **10 分制**上评估 AI 技能质量。

### 类别与权重

| 类别 | 权重 | 描述 |
|------|------|------|
| **发现与元数据** | 10% | 智能体找到并加载技能的难易程度 |
| **简洁性与 Token 经济** | 15% | 上下文窗口的高效利用 |
| **结构组织** | 15% | 逻辑流程、渐进式披露 |
| **代码示例质量** | 20% | 经过测试、完整、多样的示例 |
| **准确性与正确性** | 20% | 信息事实正确、与时俱进 |
| **可执行性** | 10% | 用户可立即应用知识 |
| **跨平台兼容性** | 10% | 在 Claude、Gemini、OpenAI 上均可用 |

### 详细评分

#### 1. 发现与元数据（10%）

**10/10 - 优秀**：
- ✅ 名称为动名词形式，清晰具体
- ✅ Description：第三人称、what + when、<1024 字符
- ✅ 匹配用户意图的触发短语
- ✅ 适当的发现标签
- ✅ 包含版本和平台元数据

**7/10 - 良好**：
- ✅ 名称清晰但非动名词形式
- ✅ Description 包含 what + when 但冗长
- ⚠️ 缺少一些触发短语
- ✅ 有标签

**4/10 - 差**：
- ⚠️ 名称模糊或被动
- ⚠️ Description 缺少 "when" 子句
- ⚠️ 没有触发短语
- ❌ 缺少标签

**1/10 - 不合格**：
- ❌ 没有元数据或名称无法理解
- ❌ Description 为第一人称或泛泛而谈

#### 2. 简洁性与 Token 经济（15%）

**10/10 - 优秀**：
- ✅ 主 SKILL.md <5,000 个 token
- ✅ 无冗余或填充内容
- ✅ 每个句子都提供独特价值
- ✅ 渐进式披露（参考文件按需加载）
- ✅ 快速参考 <500 个 token

**7/10 - 良好**：
- ✅ 主 SKILL.md <7,000 个 token
- ⚠️ 轻微冗余（5-10% 浪费）
- ✅ 大部分内容有价值
- ⚠️ 一些参考内容内联而非独立文件

**4/10 - 差**：
- ⚠️ 主 SKILL.md 7,000-10,000 个 token
- ⚠️ 明显冗余（20%+ 浪费）
- ⚠️ 解释冗长、有填充词
- ⚠️ 参考文件组织混乱

**1/10 - 不合格**：
- ❌ 主 SKILL.md >10,000 个 token
- ❌ 大量冗余、百科全书式内容
- ❌ 没有渐进式披露

#### 3. 结构组织（15%）

**10/10 - 优秀**：
- ✅ 清晰的层次：快速参考 → 核心 → 扩展 → 参考文件
- ✅ 逻辑流程（发现 → 使用 → 深入）
- ✅ 使用 emoji 提升可扫描性
- ✅ 正确使用标题（##、###）
- ✅ 长文档有目录

**7/10 - 良好**：
- ✅ 大部分章节齐全
- ⚠️ 流程可以改进
- ✅ 标题使用正确
- ⚠️ 没有 emoji 或目录

**4/10 - 差**：
- ⚠️ 缺少关键章节
- ⚠️ 流程不合逻辑（高级在基础之前）
- ⚠️ 标题层级不一致
- ❌ 文字堆砌，没有结构

**1/10 - 不合格**：
- ❌ 没有结构，单个巨大文本块
- ❌ 缺少必需章节

#### 4. 代码示例质量（20%）

**10/10 - 优秀**：
- ✅ 5-10 个示例，覆盖 80% 的用例
- ✅ 所有示例经过测试/验证
- ✅ 完整（可直接复制粘贴）
- ✅ 复杂度渐进（基础 → 高级）
- ✅ 带简要说明的注解
- ✅ 语言检测正确
- ✅ 真实世界模式（非玩具示例）

**7/10 - 良好**：
- ✅ 3-5 个示例
- ✅ 大部分经过测试
- ⚠️ 部分不完整（需要修改）
- ✅ 有一定的渐进性
- ⚠️ 注解较少

**4/10 - 差**：
- ⚠️ 仅 1-2 个示例
- ⚠️ 未测试或损坏的示例
- ⚠️ 片段而非完整代码
- ⚠️ 所有示例复杂度相同
- ❌ 没有注解

**1/10 - 不合格**：
- ❌ 没有示例或全部损坏
- ❌ 语言标签错误
- ❌ 仅有玩具示例

#### 5. 准确性与正确性（20%）

**10/10 - 优秀**：
- ✅ 所有信息事实正确
- ✅ 当前最佳实践（2026）
- ✅ 没有已废弃的模式
- ✅ API 签名正确
- ✅ 版本信息准确
- ✅ 没有幻觉出来的功能

**7/10 - 良好**：
- ✅ 基本准确
- ⚠️ 1-2 个小错误或过时细节
- ✅ 核心模式正确
- ⚠️ 一些版本含糊不清

**4/10 - 差**：
- ⚠️ 多处事实错误
- ⚠️ 将废弃模式当作当前模式呈现
- ⚠️ API 签名不正确
- ⚠️ 混用版本

**1/10 - 不合格**：
- ❌ 信息根本性错误
- ❌ 幻觉出来的 API 或功能
- ❌ 危险或不安全的模式

#### 6. 可执行性（10%）

**10/10 - 优秀**：
- ✅ 用户可立即应用知识
- ✅ 复杂任务有分步指令
- ✅ 记录了常见工作流
- ✅ 有故障排除指导
- ✅ 需要时链接到更深入的资源

**7/10 - 良好**：
- ✅ 大多数任务可执行
- ⚠️ 部分工作流缺少步骤
- ✅ 有基本的故障排除
- ⚠️ 一些死链引用

**4/10 - 差**：
- ⚠️ 理论知识，应用方式不明
- ⚠️ 缺少关键步骤
- ❌ 没有故障排除
- ⚠️ 链接损坏

**1/10 - 不合格**：
- ❌ 纯参考资料，没有指导
- ❌ 没有外部帮助无法使用这些信息

#### 7. 跨平台兼容性（10%）

**10/10 - 优秀**：
- ✅ 遵循开放 Agent Skills 标准
- ✅ 在 Claude、Gemini、OpenAI、Markdown 上均可用
- ✅ 没有平台特定依赖
- ✅ 文件结构正确
- ✅ YAML frontmatter 有效

**7/10 - 良好**：
- ✅ 在 2-3 个平台上可用
- ⚠️ 需要少量平台特定调整
- ✅ 标准结构

**4/10 - 差**：
- ⚠️ 仅在 1 个平台上可用
- ⚠️ 非标准结构
- ⚠️ YAML 无效

**1/10 - 不合格**：
- ❌ 平台锁定，专有格式
- ❌ 无法移植

### 总分计算

```
Total Score = (Discovery × 0.10) +
              (Conciseness × 0.15) +
              (Structure × 0.15) +
              (Examples × 0.20) +
              (Accuracy × 0.20) +
              (Actionability × 0.10) +
              (Compatibility × 0.10)
```

**等级映射**：
- **9.0-10.0**：A+（卓越，参考级质量）
- **8.0-8.9**：A（优秀，生产就绪）
- **7.0-7.9**：B（良好，需少量改进）
- **6.0-6.9**：C（可接受，需大量改进）
- **5.0-5.9**：D（差，需要重大返工）
- **0.0-4.9**：F（不合格，不可用）

---

## 常见误区

### 1. 百科全书式内容

**问题**：囊括某主题的一切，而非聚焦可执行的知识。

**示例**：
```markdown
❌ BAD:
React was created by Jordan Walke, a software engineer at Facebook,
in 2011. It was first deployed on Facebook's newsfeed in 2011 and
later on Instagram in 2012. It was open-sourced at JSConf US in May
2013. Over the years, React has evolved significantly...

✅ GOOD:
React is a component-based UI library. Build reusable components,
manage state with hooks, and efficiently update the DOM.
```

**修复**：聚焦于**用户需要做什么**，而非历史或背景。

### 2. 第一人称的 Description

**问题**：在元数据中使用 "I" 或 "you"（破坏 Claude 的发现机制）。

**示例**：
```yaml
❌ BAD:
description: I will help you build React applications with best practices

✅ GOOD:
description: Building modern React applications with TypeScript, hooks,
  and routing. Use when implementing components or managing state.
```

**修复**：description 字段始终使用第三人称。

### 3. Token 浪费

**问题**：冗余的解释、啰嗦的措辞或填充内容。

**示例**：
```markdown
❌ BAD (85 tokens):
When you are working on a project and you need to manage state in your
React application, you have several different options available to you.
One option is to use the useState hook, which is great for managing
local component state. Another option is to use useReducer, which is
better for more complex state logic.

✅ GOOD (28 tokens):
State management options:
- Local state → useState (simple values)
- Complex logic → useReducer (state machines)
- Global state → Context API or Redux
```

**修复**：使用要点列表，删除填充内容，聚焦差异。

### 4. 未测试的示例

**问题**：无法编译或运行的代码示例。

**示例**：
```typescript
❌ BAD:
function Example() {
  const [data, setData] = useState();  // No type, no initial value
  useEffect(() => {
    fetchData();  // Function doesn't exist
  });  // Missing dependency array
  return <div>{data}</div>;  // TypeScript error
}

✅ GOOD:
interface User {
  id: number;
  name: string;
}

function Example() {
  const [data, setData] = useState<User | null>(null);

  useEffect(() => {
    fetch('/api/user')
      .then(r => r.json())
      .then(setData);
  }, []);  // Empty deps = run once

  return <div>{data?.name ?? 'Loading...'}</div>;
}
```

**修复**：测试所有代码示例，确保它们能编译/运行。

### 5. 缺少"何时使用"

**问题**：description 只说明了"是什么"，没有说明"何时用"。

**示例**：
```yaml
❌ BAD:
description: Documentation for React hooks and component patterns

✅ GOOD:
description: Building React applications with hooks and components.
  Use when implementing UI components, managing state, or optimizing
  React performance.
```

**修复**：始终包含 "Use when..." 或 "Use for..." 子句。

### 6. 扁平的参考文件结构

**问题**：所有参考内容堆在一个文件或目录中，没有组织。

**示例**：
```
❌ BAD:
references/
├── everything.md  (20,000+ tokens)

✅ GOOD:
references/
├── index.md
├── api/
│   ├── components.md
│   └── hooks.md
├── patterns/
│   ├── state-management.md
│   └── performance.md
└── examples/
    ├── basic/
    └── advanced/
```

**修复**：按类别组织，便于智能体导航。

### 7. 过时的信息

**问题**：包含已废弃的 API 或旧的最佳实践。

**示例**：
```markdown
❌ BAD (deprecated in React 18):
Use componentDidMount() and componentWillUnmount() for side effects.

✅ GOOD (current as of 2026):
Use useEffect() hook for side effects in function components.
```

**修复**：定期更新技能，包含版本信息。

---

## 面向未来

### 新兴标准（2026-2030）

1. **Model Context Protocol（MCP）**：标准化智能体访问工具和数据的方式
   - 技能将与 MCP 服务器集成
   - 预计技能元数据中会出现 MCP 端点

2. **多模态技能**：超越文本（图像、音频、视频）
   - 包含图表引用、视频教程
   - 为具备视觉能力的智能体做准备

3. **技能组合**：引用其他技能的技能
   - 模块化架构（React 技能导入 TypeScript 技能）
   - 技能的依赖管理

4. **实时 Grounding**：技能 + 实时数据源
   - Gemini 式 grounding 将变得普遍
   - 技能提供上下文，grounding 提供最新数据

5. **联邦式技能仓库**：去中心化的技能发现
   - GitHub 式的技能托管
   - 技能的版本控制、pull request

### 建议

- **为技能设置版本**：使用语义化版本（1.0.0、1.1.0、2.0.0）
- **标注平台兼容性**：指明已测试的平台/版本
- **记录依赖**：技能引用外部 API 或工具时
- **提供迁移指南**：在更新主版本时
- **维护变更日志**：跟踪变更内容及原因

---

## 参考文献

### 官方文档

- [Claude Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [OpenAI Custom GPT Guidelines](https://help.openai.com/en/articles/9358033-key-guidelines-for-writing-instructions-for-custom-gpts)
- [Google Gemini Grounding Best Practices](https://ai.google.dev/gemini-api/docs/google-search)

### 行业标准

- [Agent Skills: Anthropic's Next Bid to Define AI Standards - The New Stack](https://thenewstack.io/agent-skills-anthropics-next-bid-to-define-ai-standards/)
- [Claude Skills and CLAUDE.md: a practical 2026 guide for teams](https://www.gend.co/blog/claude-skills-claude-md-guide)

### 设计模式

- [Emerging Patterns in Building GenAI Products - Martin Fowler](https://martinfowler.com/articles/gen-ai-patterns/)
- [4 Agentic AI Design Patterns - AIMultiple](https://research.aimultiple.com/agentic-ai-design-patterns/)
- [Traditional RAG vs. Agentic RAG - NVIDIA](https://developer.nvidia.com/blog/traditional-rag-vs-agentic-rag-why-ai-agents-need-dynamic-knowledge-to-get-smarter/)
- [What is Agentic RAG? - IBM](https://www.ibm.com/think/topics/agentic-rag)

### 知识库架构

- [Anatomy of an AI agent knowledge base - InfoWorld](https://www.infoworld.com/article/4091400/anatomy-of-an-ai-agent-knowledge-base.html)
- [The Next Frontier of RAG: Enterprise Knowledge Systems 2026-2030 - NStarX](https://nstarxinc.com/blog/the-next-frontier-of-rag-how-enterprise-knowledge-systems-will-evolve-2026-2030/)
- [RAG Architecture Patterns For Developers](https://customgpt.ai/rag-architecture-patterns/)

### 社区资源

- [awesome-claude-skills - GitHub](https://github.com/travisvn/awesome-claude-skills)
- [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)

---

**文档维护**：
- 每季度审查平台更新
- 用新框架版本更新示例
- 跟踪 AI 智能体领域的新兴模式
- 吸纳社区反馈

**版本历史**：
- 1.0（2026-01-11）：基于 2026 标准的首次发布
