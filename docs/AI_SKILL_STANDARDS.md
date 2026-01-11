# AI Skill Standards & Best Practices (2026)

**Version:** 1.0
**Last Updated:** 2026-01-11
**Scope:** Cross-platform AI skills for Claude, Gemini, OpenAI, and generic LLMs

## Table of Contents

1. [Introduction](#introduction)
2. [Universal Standards](#universal-standards)
3. [Platform-Specific Guidelines](#platform-specific-guidelines)
4. [Knowledge Base Design Patterns](#knowledge-base-design-patterns)
5. [Quality Grading Rubric](#quality-grading-rubric)
6. [Common Pitfalls](#common-pitfalls)
7. [Future-Proofing](#future-proofing)

---

## Introduction

This document establishes the definitive standards for AI skill creation based on 2026 industry best practices, official platform documentation, and emerging patterns in agentic AI systems.

### What is an AI Skill?

An **AI skill** is a focused knowledge package that enhances an AI agent's capabilities in a specific domain. Skills include:
- **Instructions**: How to use the knowledge
- **Context**: When the skill applies
- **Resources**: Reference documentation, examples, patterns
- **Metadata**: Discovery, versioning, platform compatibility

### Design Philosophy

Modern AI skills follow three core principles:

1. **Progressive Disclosure**: Load information only when needed (metadata → instructions → resources)
2. **Context Economy**: Every token competes with conversation history
3. **Cross-Platform Portability**: Design for the open Agent Skills standard

---

## Universal Standards

These standards apply to **all platforms** (Claude, Gemini, OpenAI, generic).

### 1. Naming Conventions

**Format**: Gerund form (verb + -ing)

**Why**: Clearly describes the activity or capability the skill provides.

**Examples**:
- ✅ "Building React Applications"
- ✅ "Working with Django REST Framework"
- ✅ "Analyzing Godot 4.x Projects"
- ❌ "React Documentation" (passive, unclear)
- ❌ "Django Guide" (vague)

**Implementation**:
```yaml
name: building-react-applications  # kebab-case, gerund form
description: Building modern React applications with hooks, routing, and state management
```

### 2. Description Field (Critical for Discovery)

**Format**: Third person, actionable, includes BOTH "what" and "when"

**Why**: Injected into system prompts; inconsistent POV causes discovery problems.

**Structure**:
```
[What it does]. Use when [specific triggers/scenarios].
```

**Examples**:
- ✅ "Building modern React applications with TypeScript, hooks, and routing. Use when implementing React components, managing state, or configuring build tools."
- ✅ "Analyzing Godot 4.x game projects with GDScript patterns. Use when debugging game logic, optimizing performance, or implementing new features in Godot."
- ❌ "I will help you with React" (first person, vague)
- ❌ "Documentation for Django" (no when clause)

### 3. Token Budget (Progressive Disclosure)

**Token Allocation**:
- **Metadata loading**: ~100 tokens (YAML frontmatter + description)
- **Full instructions**: <5,000 tokens (main SKILL.md without references)
- **Bundled resources**: Load on-demand only

**Why**: Token efficiency is critical—unused context wastes capacity.

**Best Practice**:
```markdown
## Quick Reference
*30-second overview with most common patterns*

[Core content - 3,000-4,500 tokens]

## Extended Reference
*See references/api.md for complete API documentation*
```

### 4. Conciseness & Relevance

**Principles**:
- Every sentence must provide **unique value**
- Remove redundancy, filler, and "nice to have" information
- Prioritize **actionable** over **explanatory** content
- Use progressive disclosure: Quick Reference → Deep Dive → References

**Example Transformation**:

**Before** (130 tokens):
```
React is a popular JavaScript library for building user interfaces.
It was created by Facebook and is now maintained by Meta and the
open-source community. React uses a component-based architecture
where you build encapsulated components that manage their own state.
```

**After** (35 tokens):
```
Component-based UI library. Build reusable components with local
state, compose them into complex UIs, and efficiently update the
DOM via virtual DOM reconciliation.
```

### 5. Structure & Organization

**Required Sections** (in order):

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

**Optional Sections**:
- Installation
- Configuration
- Testing Patterns
- Migration Guides
- Performance Tips

### 6. Code Examples Quality

**Standards**:
- **Tested**: From official docs, test suites, or production code
- **Complete**: Copy-paste ready, not fragments
- **Annotated**: Brief explanation of what/why, not how (code shows how)
- **Progressive**: Basic → Intermediate → Advanced
- **Diverse**: Cover common use cases (80% of user needs)

**Format**:
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

### 7. Cross-Platform Compatibility

**File Structure** (Open Agent Skills Standard):
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

**YAML Frontmatter** (required for all platforms):
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

## Platform-Specific Guidelines

### Claude AI (Agent Skills)

**Official Standard**: [Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

**Key Differences**:
- **Discovery**: Description injected into system prompt—must be third person
- **Token limit**: ~5k tokens for main SKILL.md (hard limit for fast loading)
- **Loading behavior**: Claude loads skill when description matches user intent
- **Resource access**: References loaded on-demand via file reads

**Best Practices**:
- Use emojis for section headers (improves scannability): 💡 ⚡ 📝 🔧 🏗️ ⚠️ 📚
- Include "trigger phrases" in description: "when implementing...", "when debugging...", "when configuring..."
- Keep Quick Reference ultra-concise (user sees this first)
- Link to references explicitly: "See `references/api.md` for complete API"

**Example Description**:
```yaml
description: >
  Building modern React applications with TypeScript, hooks, and routing.
  Use when implementing React components, managing application state,
  configuring build tools, or debugging React applications.
```

### Google Gemini (Actions)

**Official Standard**: [Grounding Best Practices](https://ai.google.dev/gemini-api/docs/google-search)

**Key Differences**:
- **Grounding**: Skills can leverage Google Search for real-time information
- **Temperature**: Keep at 1.0 (default) for optimal grounding results
- **Format**: Supports tar.gz packages (not ZIP)
- **Limitations**: No Maps grounding in Gemini 3 (use Gemini 2.5 if needed)

**Grounding Enhancements**:
```markdown
## When to Use This Skill

Use this skill when:
- Implementing React components (skill provides patterns)
- Checking latest React version (grounding provides current info)
- Debugging common errors (skill + grounding = comprehensive solution)
```

**Note**: Grounding costs $14 per 1,000 queries (as of Jan 5, 2026).

### OpenAI (GPT Actions)

**Official Standard**: [Key Guidelines for Custom GPTs](https://help.openai.com/en/articles/9358033-key-guidelines-for-writing-instructions-for-custom-gpts)

**Key Differences**:
- **Multi-step instructions**: Break into simple, atomic steps
- **Trigger/Instruction pairs**: Use delimiters to separate scenarios
- **Thoroughness prompts**: Include "take your time", "take a deep breath", "check your work"
- **Not compatible**: GPT-5.1 reasoning models don't support custom actions yet

**Format**:
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

### Generic Markdown (Platform-Agnostic)

**Use Case**: Documentation sites, internal wikis, non-LLM tools

**Format**: Standard markdown with minimal metadata

**Best Practice**: Focus on human readability over token economy

---

## Knowledge Base Design Patterns

Modern AI skills leverage advanced RAG (Retrieval-Augmented Generation) patterns for optimal knowledge delivery.

### 1. Agentic RAG (Recommended for 2026+)

**Pattern**: Multi-query, context-aware retrieval with agent orchestration

**Architecture**:
```
User Query → Agent Plans Retrieval → Multi-Source Fetch →
Context Synthesis → Response Generation → Self-Verification
```

**Benefits**:
- **Adaptive**: Agent adjusts retrieval based on conversation context
- **Accurate**: Multi-query approach reduces hallucination
- **Efficient**: Only retrieves what's needed for current query

**Implementation in Skills**:
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

**Why**: Agent can navigate structure to find exactly what's needed.

**Sources**:
- [Traditional RAG vs. Agentic RAG - NVIDIA](https://developer.nvidia.com/blog/traditional-rag-vs-agentic-rag-why-ai-agents-need-dynamic-knowledge-to-get-smarter/)
- [What is Agentic RAG? - IBM](https://www.ibm.com/think/topics/agentic-rag)

### 2. GraphRAG (Advanced Use Cases)

**Pattern**: Knowledge graph structures for complex reasoning

**Use Case**: Large codebases, interconnected concepts, architectural analysis

**Structure**:
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

**Benefits**: Multi-hop reasoning, relationship exploration, complex queries

**Sources**:
- [Emerging Patterns in Building GenAI Products - Martin Fowler](https://martinfowler.com/articles/gen-ai-patterns/)

### 3. Multi-Agent Systems (Enterprise Scale)

**Pattern**: Specialized agents for different knowledge domains

**Architecture**:
```
Skill Repository
├── research-agent-skill/      # Explores information space
├── verification-agent-skill/  # Checks factual claims
├── synthesis-agent-skill/     # Combines findings
└── governance-agent-skill/    # Ensures compliance
```

**Use Case**: Enterprise workflows, compliance requirements, multi-domain expertise

**Sources**:
- [4 Agentic AI Design Patterns - AIMultiple](https://research.aimultiple.com/agentic-ai-design-patterns/)

### 4. Reflection Pattern (Quality Assurance)

**Pattern**: Self-evaluation and refinement before finalizing responses

**Implementation**:
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

**Benefits**: Higher quality outputs, fewer errors, better adherence to standards

**Sources**:
- [4 Agentic AI Design Patterns - AIMultiple](https://research.aimultiple.com/agentic-ai-design-patterns/)

### 5. Vector Database Integration

**Pattern**: Semantic search over embeddings for concept-based retrieval

**Use Case**: Large documentation sets, conceptual queries, similarity search

**Structure**:
- Store reference documents as embeddings
- User query → embedding → similarity search → top-k retrieval
- Agent synthesizes retrieved chunks

**Tools**:
- Pinecone, Weaviate, Chroma, Qdrant
- Model Context Protocol (MCP) for standardized access

**Sources**:
- [Anatomy of an AI agent knowledge base - InfoWorld](https://www.infoworld.com/article/4091400/anatomy-of-an-ai-agent-knowledge-base.html)

---

## Quality Grading Rubric

Use this rubric to assess AI skill quality on a **10-point scale**.

### Categories & Weights

| Category | Weight | Description |
|----------|--------|-------------|
| **Discovery & Metadata** | 10% | How easily agents find and load the skill |
| **Conciseness & Token Economy** | 15% | Efficient use of context window |
| **Structural Organization** | 15% | Logical flow, progressive disclosure |
| **Code Example Quality** | 20% | Tested, complete, diverse examples |
| **Accuracy & Correctness** | 20% | Factually correct, up-to-date information |
| **Actionability** | 10% | User can immediately apply knowledge |
| **Cross-Platform Compatibility** | 10% | Works across Claude, Gemini, OpenAI |

### Detailed Scoring

#### 1. Discovery & Metadata (10%)

**10/10 - Excellent**:
- ✅ Name in gerund form, clear and specific
- ✅ Description: third person, what + when, <1024 chars
- ✅ Trigger phrases that match user intent
- ✅ Appropriate tags for discovery
- ✅ Version and platform metadata present

**7/10 - Good**:
- ✅ Name clear but not gerund form
- ✅ Description has what + when but verbose
- ⚠️ Some trigger phrases missing
- ✅ Tags present

**4/10 - Poor**:
- ⚠️ Name vague or passive
- ⚠️ Description missing "when" clause
- ⚠️ No trigger phrases
- ❌ Missing tags

**1/10 - Failing**:
- ❌ No metadata or incomprehensible name
- ❌ Description is first person or generic

#### 2. Conciseness & Token Economy (15%)

**10/10 - Excellent**:
- ✅ Main SKILL.md <5,000 tokens
- ✅ No redundancy or filler content
- ✅ Every sentence provides unique value
- ✅ Progressive disclosure (references on-demand)
- ✅ Quick Reference <500 tokens

**7/10 - Good**:
- ✅ Main SKILL.md <7,000 tokens
- ⚠️ Minor redundancy (5-10% waste)
- ✅ Most content valuable
- ⚠️ Some references inline instead of separate

**4/10 - Poor**:
- ⚠️ Main SKILL.md 7,000-10,000 tokens
- ⚠️ Significant redundancy (20%+ waste)
- ⚠️ Verbose explanations, filler words
- ⚠️ Poor reference organization

**1/10 - Failing**:
- ❌ Main SKILL.md >10,000 tokens
- ❌ Massive redundancy, encyclopedic content
- ❌ No progressive disclosure

#### 3. Structural Organization (15%)

**10/10 - Excellent**:
- ✅ Clear hierarchy: Quick Ref → Core → Extended → References
- ✅ Logical flow (discovery → usage → deep dive)
- ✅ Emojis for scannability
- ✅ Proper use of headings (##, ###)
- ✅ Table of contents for long documents

**7/10 - Good**:
- ✅ Most sections present
- ⚠️ Flow could be improved
- ✅ Headings used correctly
- ⚠️ No emojis or TOC

**4/10 - Poor**:
- ⚠️ Missing key sections
- ⚠️ Illogical flow (advanced before basic)
- ⚠️ Inconsistent heading levels
- ❌ Wall of text, no structure

**1/10 - Failing**:
- ❌ No structure, single massive block
- ❌ Missing required sections

#### 4. Code Example Quality (20%)

**10/10 - Excellent**:
- ✅ 5-10 examples covering 80% of use cases
- ✅ All examples tested/validated
- ✅ Complete (copy-paste ready)
- ✅ Progressive complexity (basic → advanced)
- ✅ Annotated with brief explanations
- ✅ Correct language detection
- ✅ Real-world patterns (not toy examples)

**7/10 - Good**:
- ✅ 3-5 examples
- ✅ Most tested
- ⚠️ Some incomplete (require modification)
- ✅ Some progression
- ⚠️ Light annotations

**4/10 - Poor**:
- ⚠️ 1-2 examples only
- ⚠️ Untested or broken examples
- ⚠️ Fragments, not complete
- ⚠️ All same complexity level
- ❌ No annotations

**1/10 - Failing**:
- ❌ No examples or all broken
- ❌ Incorrect language tags
- ❌ Toy examples only

#### 5. Accuracy & Correctness (20%)

**10/10 - Excellent**:
- ✅ All information factually correct
- ✅ Current best practices (2026)
- ✅ No deprecated patterns
- ✅ Correct API signatures
- ✅ Accurate version information
- ✅ No hallucinated features

**7/10 - Good**:
- ✅ Mostly accurate
- ⚠️ 1-2 minor errors or outdated details
- ✅ Core patterns correct
- ⚠️ Some version ambiguity

**4/10 - Poor**:
- ⚠️ Multiple factual errors
- ⚠️ Deprecated patterns presented as current
- ⚠️ API signatures incorrect
- ⚠️ Mixing versions

**1/10 - Failing**:
- ❌ Fundamentally incorrect information
- ❌ Hallucinated APIs or features
- ❌ Dangerous or insecure patterns

#### 6. Actionability (10%)

**10/10 - Excellent**:
- ✅ User can immediately apply knowledge
- ✅ Step-by-step instructions for complex tasks
- ✅ Common workflows documented
- ✅ Troubleshooting guidance
- ✅ Links to deeper resources when needed

**7/10 - Good**:
- ✅ Most tasks actionable
- ⚠️ Some workflows missing steps
- ✅ Basic troubleshooting present
- ⚠️ Some dead-end references

**4/10 - Poor**:
- ⚠️ Theoretical knowledge, unclear application
- ⚠️ Missing critical steps
- ❌ No troubleshooting
- ⚠️ Broken links

**1/10 - Failing**:
- ❌ Pure reference, no guidance
- ❌ Cannot use information without external help

#### 7. Cross-Platform Compatibility (10%)

**10/10 - Excellent**:
- ✅ Follows Open Agent Skills standard
- ✅ Works on Claude, Gemini, OpenAI, Markdown
- ✅ No platform-specific dependencies
- ✅ Proper file structure
- ✅ Valid YAML frontmatter

**7/10 - Good**:
- ✅ Works on 2-3 platforms
- ⚠️ Minor platform-specific tweaks needed
- ✅ Standard structure

**4/10 - Poor**:
- ⚠️ Only works on 1 platform
- ⚠️ Non-standard structure
- ⚠️ Invalid YAML

**1/10 - Failing**:
- ❌ Platform-locked, proprietary format
- ❌ Cannot be ported

### Overall Grade Calculation

```
Total Score = (Discovery × 0.10) +
              (Conciseness × 0.15) +
              (Structure × 0.15) +
              (Examples × 0.20) +
              (Accuracy × 0.20) +
              (Actionability × 0.10) +
              (Compatibility × 0.10)
```

**Grade Mapping**:
- **9.0-10.0**: A+ (Exceptional, reference quality)
- **8.0-8.9**: A (Excellent, production-ready)
- **7.0-7.9**: B (Good, minor improvements needed)
- **6.0-6.9**: C (Acceptable, significant improvements needed)
- **5.0-5.9**: D (Poor, major rework required)
- **0.0-4.9**: F (Failing, not usable)

---

## Common Pitfalls

### 1. Encyclopedic Content

**Problem**: Including everything about a topic instead of focusing on actionable knowledge.

**Example**:
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

**Fix**: Focus on **what the user needs to do**, not history or background.

### 2. First-Person Descriptions

**Problem**: Using "I" or "you" in metadata (breaks Claude discovery).

**Example**:
```yaml
❌ BAD:
description: I will help you build React applications with best practices

✅ GOOD:
description: Building modern React applications with TypeScript, hooks,
  and routing. Use when implementing components or managing state.
```

**Fix**: Always use third person in description field.

### 3. Token Waste

**Problem**: Redundant explanations, verbose phrasing, or filler content.

**Example**:
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

**Fix**: Use bullet points, remove filler, focus on distinctions.

### 4. Untested Examples

**Problem**: Code examples that don't compile or run.

**Example**:
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

**Fix**: Test all code examples, ensure they compile/run.

### 5. Missing "When to Use"

**Problem**: Description explains what but not when.

**Example**:
```yaml
❌ BAD:
description: Documentation for React hooks and component patterns

✅ GOOD:
description: Building React applications with hooks and components.
  Use when implementing UI components, managing state, or optimizing
  React performance.
```

**Fix**: Always include "Use when..." or "Use for..." clause.

### 6. Flat Reference Structure

**Problem**: All references in one file or directory, no organization.

**Example**:
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

**Fix**: Organize by category, enable agent navigation.

### 7. Outdated Information

**Problem**: Including deprecated APIs or old best practices.

**Example**:
```markdown
❌ BAD (deprecated in React 18):
Use componentDidMount() and componentWillUnmount() for side effects.

✅ GOOD (current as of 2026):
Use useEffect() hook for side effects in function components.
```

**Fix**: Regularly update skills, include version info.

---

## Future-Proofing

### Emerging Standards (2026-2030)

1. **Model Context Protocol (MCP)**: Standardizes how agents access tools and data
   - Skills will integrate with MCP servers
   - Expect MCP endpoints in skill metadata

2. **Multi-Modal Skills**: Beyond text (images, audio, video)
   - Include diagram references, video tutorials
   - Prepare for vision-capable agents

3. **Skill Composition**: Skills that reference other skills
   - Modular architecture (React skill imports TypeScript skill)
   - Dependency management for skills

4. **Real-Time Grounding**: Skills + live data sources
   - Gemini-style grounding becomes universal
   - Skills provide context, grounding provides current data

5. **Federated Skill Repositories**: Decentralized skill discovery
   - GitHub-style skill hosting
   - Version control, pull requests for skills

### Recommendations

- **Version your skills**: Use semantic versioning (1.0.0, 1.1.0, 2.0.0)
- **Tag platform compatibility**: Specify which platforms/versions tested
- **Document dependencies**: If skill references external APIs or tools
- **Provide migration guides**: When updating major versions
- **Maintain changelog**: Track what changed and why

---

## References

### Official Documentation

- [Claude Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [OpenAI Custom GPT Guidelines](https://help.openai.com/en/articles/9358033-key-guidelines-for-writing-instructions-for-custom-gpts)
- [Google Gemini Grounding Best Practices](https://ai.google.dev/gemini-api/docs/google-search)

### Industry Standards

- [Agent Skills: Anthropic's Next Bid to Define AI Standards - The New Stack](https://thenewstack.io/agent-skills-anthropics-next-bid-to-define-ai-standards/)
- [Claude Skills and CLAUDE.md: a practical 2026 guide for teams](https://www.gend.co/blog/claude-skills-claude-md-guide)

### Design Patterns

- [Emerging Patterns in Building GenAI Products - Martin Fowler](https://martinfowler.com/articles/gen-ai-patterns/)
- [4 Agentic AI Design Patterns - AIMultiple](https://research.aimultiple.com/agentic-ai-design-patterns/)
- [Traditional RAG vs. Agentic RAG - NVIDIA](https://developer.nvidia.com/blog/traditional-rag-vs-agentic-rag-why-ai-agents-need-dynamic-knowledge-to-get-smarter/)
- [What is Agentic RAG? - IBM](https://www.ibm.com/think/topics/agentic-rag)

### Knowledge Base Architecture

- [Anatomy of an AI agent knowledge base - InfoWorld](https://www.infoworld.com/article/4091400/anatomy-of-an-ai-agent-knowledge-base.html)
- [The Next Frontier of RAG: Enterprise Knowledge Systems 2026-2030 - NStarX](https://nstarxinc.com/blog/the-next-frontier-of-rag-how-enterprise-knowledge-systems-will-evolve-2026-2030/)
- [RAG Architecture Patterns For Developers](https://customgpt.ai/rag-architecture-patterns/)

### Community Resources

- [awesome-claude-skills - GitHub](https://github.com/travisvn/awesome-claude-skills)
- [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)

---

**Document Maintenance**:
- Review quarterly for platform updates
- Update examples with new framework versions
- Track emerging patterns in AI agent space
- Incorporate community feedback

**Version History**:
- 1.0 (2026-01-11): Initial release based on 2026 standards
