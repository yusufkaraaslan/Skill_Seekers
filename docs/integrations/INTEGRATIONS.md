# AI System Integrations with Skill Seekers

**Universal Preprocessor:** Transform documentation into structured knowledge for any AI system

---

## 🤔 Which Integration Should I Use?

| Your Goal | Recommended Tool | Format | Setup Time | Guide |
|-----------|-----------------|--------|------------|-------|
| Build RAG with Python | LangChain | `--target langchain` | 5 min | [Guide](LANGCHAIN.md) |
| Query engine from docs | LlamaIndex | `--target llama-index` | 5 min | [Guide](LLAMA_INDEX.md) |
| Vector database only | Pinecone/Weaviate | `--target [db]` | 3 min | [Guide](PINECONE.md) |
| AI coding (VS Code fork) | Cursor | `--target claude` | 5 min | [Guide](CURSOR.md) |
| AI coding (Windsurf) | Windsurf | `--target markdown` | 5 min | [Guide](WINDSURF.md) |
| AI coding (VS Code ext) | Cline (MCP) | `--target claude` | 10 min | [Guide](CLINE.md) |
| AI coding (any IDE) | Continue.dev | `--target markdown` | 5 min | [Guide](CONTINUE_DEV.md) |
| Claude AI chat | Claude | `--target claude` | 3 min | [Guide](CLAUDE.md) |
| Chunked for RAG | Any + chunking | `--chunk-for-rag` | + 2 min | [RAG Guide](RAG_PIPELINES.md) |

---

## 📚 RAG & Vector Databases

### Production-Ready RAG Frameworks

Transform documentation into RAG-ready formats for AI-powered search and retrieval:

| Framework | Users | Format | Best For | Guide |
|-----------|-------|--------|----------|-------|
| **[LangChain](LANGCHAIN.md)** | 500K+ | Document | Python RAG, most popular | [Setup →](LANGCHAIN.md) |
| **[LlamaIndex](LLAMA_INDEX.md)** | 200K+ | TextNode | Q&A focus, query engine | [Setup →](LLAMA_INDEX.md) |
| **[Haystack](HAYSTACK.md)** | 50K+ | Document | Enterprise, multi-language | [Setup →](HAYSTACK.md) |

**Quick Example:**
```bash
# Generate LangChain documents
skill-seekers scrape --config configs/react.json
skill-seekers package output/react --target langchain

# Use in RAG pipeline
python examples/langchain-rag-pipeline/quickstart.py
```

### Vector Database Integrations

Direct upload to vector databases without RAG frameworks:

| Database | Type | Best For | Guide |
|----------|------|----------|-------|
| **[Pinecone](PINECONE.md)** | Cloud | Production, serverless | [Setup →](PINECONE.md) |
| **[Weaviate](WEAVIATE.md)** | Self-hosted/Cloud | Enterprise, GraphQL | [Setup →](WEAVIATE.md) |
| **[Chroma](CHROMA.md)** | Local | Development, embeddings included | [Setup →](CHROMA.md) |
| **[FAISS](FAISS.md)** | Local | High performance, Facebook | [Setup →](FAISS.md) |
| **[Qdrant](QDRANT.md)** | Self-hosted/Cloud | Rust engine, filtering | [Setup →](QDRANT.md) |

**Quick Example:**
```bash
# Generate Pinecone format
skill-seekers scrape --config configs/fastapi.json
skill-seekers package output/fastapi --target pinecone

# Upsert to Pinecone
python examples/pinecone-upsert/quickstart.py
```

---

## 💻 AI Coding Assistants

### IDE-Native AI Tools

Give AI coding assistants expert knowledge of your frameworks:

| Tool | Type | IDEs | Format | Setup | Guide |
|------|------|------|--------|-------|-------|
| **[Cursor](CURSOR.md)** | IDE (VS Code fork) | Cursor IDE | `.cursorrules` | 5 min | [Setup →](CURSOR.md) |
| **[Windsurf](WINDSURF.md)** | IDE (Codeium) | Windsurf IDE | `.windsurfrules` | 5 min | [Setup →](WINDSURF.md) |
| **[Cline](CLINE.md)** | VS Code Extension | VS Code | `.clinerules` + MCP | 10 min | [Setup →](CLINE.md) |
| **[Continue.dev](CONTINUE_DEV.md)** | Plugin | VS Code, JetBrains, Vim | HTTP context | 5 min | [Setup →](CONTINUE_DEV.md) |

**Quick Example:**
```bash
# For any AI coding assistant (Cursor, Windsurf, Cline, Continue.dev)
skill-seekers scrape --config configs/django.json
skill-seekers package output/django --target markdown  # or --target claude

# Copy to your project
cp output/django-markdown/SKILL.md my-project/.cursorrules  # or appropriate config
```

**Comparison:**

| Feature | Cursor | Windsurf | Cline | Continue.dev |
|---------|--------|----------|-------|--------------|
| **IDE Type** | Fork (VS Code) | Native IDE | Extension | Plugin (multi-IDE) |
| **Config File** | `.cursorrules` | `.windsurfrules` | `.clinerules` | HTTP context provider |
| **Multi-IDE** | ❌ (Cursor only) | ❌ (Windsurf only) | ❌ (VS Code only) | ✅ (All IDEs) |
| **MCP Support** | ✅ | ✅ | ✅ | ✅ |
| **Character Limit** | No limit | 12K chars (6K per file) | No limit | No limit |
| **Setup Complexity** | Easy ⭐ | Easy ⭐ | Medium ⭐⭐ | Easy ⭐ |
| **Team Sharing** | Git-tracked file | Git-tracked files | Git-tracked file | HTTP server |

---

## 🎯 AI Chat Platforms

Upload documentation as custom skills to AI chat platforms:

| Platform | Provider | Format | Best For | Guide |
|----------|----------|--------|----------|-------|
| **[Claude](CLAUDE.md)** | Anthropic | ZIP + YAML | Claude.ai Projects | [Setup →](CLAUDE.md) |
| **[Gemini](GEMINI_INTEGRATION.md)** | Google | tar.gz | Gemini AI | [Setup →](GEMINI_INTEGRATION.md) |
| **[ChatGPT](OPENAI_INTEGRATION.md)** | OpenAI | ZIP + Vector Store | GPT Actions | [Setup →](OPENAI_INTEGRATION.md) |

**Quick Example:**
```bash
# Generate Claude skill
skill-seekers scrape --config configs/vue.json
skill-seekers package output/vue --target claude

# Upload to Claude
skill-seekers upload output/vue-claude.zip --target claude
```

---

## 🧠 Choosing the Right Integration

### By Use Case

| Your Goal | Best Integration | Why? | Setup Time |
|-----------|-----------------|------|------------|
| **Build Python RAG pipeline** | LangChain | Most popular, 500K+ users, extensive docs | 5 min |
| **Query engine from docs** | LlamaIndex | Optimized for Q&A, built-in persistence | 5 min |
| **Enterprise RAG system** | Haystack | Production-ready, multi-language support | 10 min |
| **Vector DB only (no framework)** | Pinecone/Weaviate/Chroma | Direct upload, no framework overhead | 3 min |
| **AI coding (VS Code fork)** | Cursor | Best integration, native `.cursorrules` | 5 min |
| **AI coding (flow-based)** | Windsurf | Unique flow paradigm, Codeium AI | 5 min |
| **AI coding (VS Code ext)** | Cline | Claude in VS Code, MCP integration | 10 min |
| **AI coding (any IDE)** | Continue.dev | Works everywhere, open-source | 5 min |
| **Chat with documentation** | Claude/Gemini/ChatGPT | Direct upload as custom skill | 3 min |

### By Technical Requirements

| Requirement | Compatible Integrations |
|-------------|-------------------------|
| **Python required** | LangChain, LlamaIndex, Haystack, all vector DBs |
| **No dependencies** | Cursor, Windsurf, Cline, Continue.dev (markdown export) |
| **Cloud-hosted** | Pinecone, Claude, Gemini, ChatGPT |
| **Self-hosted** | Chroma, FAISS, Qdrant, Continue.dev |
| **Multi-language** | Haystack, Continue.dev |
| **VS Code specific** | Cursor, Cline, Continue.dev |
| **IDE agnostic** | LangChain, LlamaIndex, Continue.dev |
| **Real-time updates** | Continue.dev (HTTP server), MCP servers |

### By Team Size

| Team Size | Recommended Stack | Why? |
|-----------|------------------|------|
| **Solo developer** | Cursor + Claude + Chroma (local) | Simple setup, no infrastructure |
| **Small team (2-5)** | Continue.dev + LangChain + Pinecone | IDE-agnostic, cloud vector DB |
| **Medium team (5-20)** | Windsurf/Cursor + LlamaIndex + Weaviate | Good balance of features |
| **Enterprise (20+)** | Continue.dev + Haystack + Qdrant/Weaviate | Production-ready, scalable |

### By Development Environment

| Environment | Recommended Tools | Setup |
|-------------|------------------|-------|
| **VS Code Only** | Cursor (fork) or Cline (extension) | `.cursorrules` or `.clinerules` |
| **JetBrains Only** | Continue.dev | HTTP context provider |
| **Mixed IDEs** | Continue.dev | Same config, all IDEs |
| **Vim/Neovim** | Continue.dev | Plugin + HTTP server |
| **Multiple Frameworks** | Continue.dev + RAG pipeline | HTTP server + vector search |

---

## 🚀 Quick Decision Tree

```
Do you need RAG/search?
├─ Yes → Use RAG framework (LangChain/LlamaIndex/Haystack)
│   ├─ Beginner? → LangChain (most docs)
│   ├─ Q&A focus? → LlamaIndex (optimized for queries)
│   └─ Enterprise? → Haystack (production-ready)
│
└─ No → Use AI coding tool or chat platform
    ├─ Need AI coding assistant?
    │   ├─ Use VS Code?
    │   │   ├─ Want native fork? → Cursor
    │   │   └─ Want extension? → Cline
    │   ├─ Use other IDE? → Continue.dev
    │   ├─ Use Windsurf? → Windsurf
    │   └─ Team uses mixed IDEs? → Continue.dev
    │
    └─ Just chat with docs? → Claude/Gemini/ChatGPT
```

---

## 🎨 Common Patterns

### Pattern 1: RAG + AI Coding

**Best for:** Deep documentation search + context-aware coding

```bash
# 1. Generate RAG pipeline (LangChain)
skill-seekers scrape --config configs/django.json
skill-seekers package output/django --target langchain --chunk-for-rag

# 2. Generate AI coding context (Cursor)
skill-seekers package output/django --target claude

# 3. Use both:
# - Cursor: Quick context for common patterns
# - RAG: Deep search for complex questions

# Copy to project
cp output/django-claude/SKILL.md my-project/.cursorrules

# Query RAG when needed
python rag_search.py "How to implement custom Django middleware?"
```

### Pattern 2: Multi-IDE Team Consistency

**Best for:** Teams using different IDEs

```bash
# 1. Generate documentation
skill-seekers scrape --config configs/react.json

# 2. Set up Continue.dev HTTP server (team server)
python context_server.py --host 0.0.0.0 --port 8765

# 3. Team members configure Continue.dev:
# ~/.continue/config.json (same for all IDEs)
{
  "contextProviders": [{
    "name": "http",
    "params": {
      "url": "http://team-server:8765/docs/react",
      "title": "react-docs"
    }
  }]
}

# Result: VS Code, IntelliJ, PyCharm all use same context!
```

### Pattern 3: Full-Stack Development

**Best for:** Backend + Frontend with different frameworks

```bash
# 1. Generate backend context (FastAPI)
skill-seekers scrape --config configs/fastapi.json
skill-seekers package output/fastapi --target markdown

# 2. Generate frontend context (Vue)
skill-seekers scrape --config configs/vue.json
skill-seekers package output/vue --target markdown

# 3. For Cursor (modular rules):
cat output/fastapi-markdown/SKILL.md >> .cursorrules
echo "\n\n# Frontend Framework\n" >> .cursorrules
cat output/vue-markdown/SKILL.md >> .cursorrules

# 4. For Continue.dev (multiple providers):
{
  "contextProviders": [
    {"name": "http", "params": {"url": "http://localhost:8765/docs/fastapi"}},
    {"name": "http", "params": {"url": "http://localhost:8765/docs/vue"}}
  ]
}

# Now AI knows BOTH backend AND frontend patterns!
```

### Pattern 4: Documentation + Codebase Analysis

**Best for:** Custom internal frameworks

```bash
# 1. Scrape public documentation
skill-seekers scrape --config configs/custom-framework.json

# 2. Analyze internal codebase
skill-seekers analyze --directory /path/to/internal/repo --comprehensive

# 3. Merge both:
skill-seekers merge-sources \
  --docs output/custom-framework \
  --codebase output/internal-repo \
  --output output/complete-knowledge

# 4. Package for any platform
skill-seekers package output/complete-knowledge --target [platform]

# Result: Documentation + Real-world code patterns!
```

---

## 💡 Best Practices

### 1. Start Simple, Scale Up

**Phase 1:** Single framework, single tool
```bash
# Week 1: Just Cursor + React
skill-seekers scrape --config configs/react.json
skill-seekers package output/react --target claude
cp output/react-claude/SKILL.md .cursorrules
```

**Phase 2:** Add RAG for deep search
```bash
# Week 2: Add LangChain for complex queries
skill-seekers package output/react --target langchain --chunk-for-rag
# Now you have: Cursor (quick) + RAG (deep)
```

**Phase 3:** Scale to team
```bash
# Week 3: Continue.dev HTTP server for team
python context_server.py --host 0.0.0.0
# Team members configure Continue.dev
```

### 2. Layer Your Context

**Priority order:**

1. **Project conventions** (highest priority)
   - Custom patterns
   - Team standards
   - Company guidelines

2. **Framework documentation** (medium priority)
   - Official best practices
   - Common patterns
   - API reference

3. **RAG search** (lowest priority)
   - Deep documentation search
   - Edge cases
   - Historical context

**Example (Cursor):**
```bash
# Layer 1: Project conventions (loaded first)
cat > .cursorrules << 'EOF'
# Project-Specific Patterns (HIGHEST PRIORITY)
Always use async/await for database operations.
Never use 'any' type in TypeScript.
EOF

# Layer 2: Framework docs (loaded second)
cat output/react-markdown/SKILL.md >> .cursorrules

# Layer 3: RAG search (when needed)
# Query separately for deep questions
```

### 3. Update Regularly

**Monthly:** Framework documentation
```bash
# Check for framework updates
skill-seekers scrape --config configs/react.json
# If new version, re-package
skill-seekers package output/react --target [your-platform]
```

**Quarterly:** Codebase analysis
```bash
# Re-analyze internal codebase for new patterns
skill-seekers analyze --directory . --comprehensive
```

**Yearly:** Architecture review
```bash
# Review and update project conventions
# Check if new integrations are available
```

### 4. Measure Effectiveness

**Track these metrics:**

- **Context hit rate:** How often AI references your documentation
- **Code quality:** Fewer pattern violations after adding context
- **Development speed:** Time saved on common tasks
- **Team consistency:** Similar code patterns across team members

**Example monitoring:**
```python
# Track Cursor suggestions quality
# Compare before/after adding .cursorrules

# Before: 60% generic suggestions, 40% framework-specific
# After:  20% generic suggestions, 80% framework-specific
# Improvement: 2x better context awareness
```

### 5. Share with Team

**Git-tracked configs:**
```bash
# Add to version control
git add .cursorrules
git add .clinerules
git add .continue/config.json
git commit -m "Add AI assistant configuration"

# Team benefits immediately
git pull  # New team member gets context
```

**Documentation:**
```markdown
# README.md

## AI Assistant Setup

This project uses Cursor with custom rules:

1. Install Cursor: https://cursor.sh/
2. Open project: `cursor .`
3. Rules auto-load from `.cursorrules`
4. Start coding with AI context!
```

---

## 📖 Complete Guides

### RAG & Vector Databases
- **[LangChain Integration](LANGCHAIN.md)** - 500K+ users, Document format
- **[LlamaIndex Integration](LLAMA_INDEX.md)** - 200K+ users, TextNode format
- **[Pinecone Integration](PINECONE.md)** - Cloud-native vector database
- **[Weaviate Integration](WEAVIATE.md)** - Enterprise-grade, GraphQL API
- **[Chroma Integration](CHROMA.md)** - Local-first, embeddings included
- **[RAG Pipelines Guide](RAG_PIPELINES.md)** - End-to-end RAG setup

### AI Coding Assistants
- **[Cursor Integration](CURSOR.md)** - VS Code fork with AI (`.cursorrules`)
- **[Windsurf Integration](WINDSURF.md)** - Codeium's IDE with AI flows
- **[Cline Integration](CLINE.md)** - Claude in VS Code (MCP integration)
- **[Continue.dev Integration](CONTINUE_DEV.md)** - Multi-platform, open-source

### AI Chat Platforms
- **[Claude Integration](CLAUDE.md)** - Anthropic's AI assistant
- **[Gemini Integration](GEMINI_INTEGRATION.md)** - Google's AI
- **[ChatGPT Integration](OPENAI_INTEGRATION.md)** - OpenAI

### Advanced Topics
- **[Multi-LLM Support](MULTI_LLM_SUPPORT.md)** - Platform comparison
- **[MCP Setup Guide](../MCP_SETUP.md)** - Model Context Protocol

---

## 🚀 Quick Start Examples

### For RAG Pipelines:
```bash
# Generate LangChain documents
skill-seekers scrape --config configs/react.json
skill-seekers package output/react --target langchain

# Use in RAG pipeline
python examples/langchain-rag-pipeline/quickstart.py
```

### For AI Coding:
```bash
# Generate Cursor rules
skill-seekers scrape --config configs/django.json
skill-seekers package output/django --target claude

# Copy to project
cp output/django-claude/SKILL.md my-project/.cursorrules
```

### For Vector Databases:
```bash
# Generate Pinecone format
skill-seekers scrape --config configs/fastapi.json
skill-seekers package output/fastapi --target pinecone

# Upsert to Pinecone
python examples/pinecone-upsert/quickstart.py
```

### For Multi-IDE Teams:
```bash
# Generate documentation
skill-seekers scrape --config configs/vue.json

# Start HTTP context server
python examples/continue-dev-universal/context_server.py

# Configure Continue.dev (same config, all IDEs)
# ~/.continue/config.json
```

---

## 🎯 Platform Comparison Matrix

| Feature | LangChain | LlamaIndex | Cursor | Windsurf | Cline | Continue.dev | Claude Chat |
|---------|-----------|------------|--------|----------|-------|--------------|-------------|
| **Setup Time** | 5 min | 5 min | 5 min | 5 min | 10 min | 5 min | 3 min |
| **Python Required** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Works Offline** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Multi-IDE** | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Real-time Updates** | ✅ | ✅ | ❌ | ❌ | ✅ (MCP) | ✅ | ❌ |
| **Team Sharing** | Git | Git | Git | Git | Git | HTTP server | Cloud |
| **Context Limit** | No limit | No limit | No limit | 12K chars | No limit | No limit | 200K tokens |
| **Custom Search** | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Best For** | RAG pipelines | Q&A engines | VS Code users | Windsurf users | Claude in VS Code | Multi-IDE teams | Quick chat |

---

## 🤝 Community & Support

- **Questions:** [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)
- **Issues:** [GitHub Issues](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
- **Website:** [skillseekersweb.com](https://skillseekersweb.com/)
- **Examples:** [GitHub Examples](https://github.com/yusufkaraaslan/Skill_Seekers/tree/main/examples)

---

## 📖 What's Next?

1. **Choose your integration** from the table above
2. **Follow the setup guide** (5-10 minutes)
3. **Test with your framework** using provided examples
4. **Customize for your project** with project-specific patterns
5. **Share with your team** via Git or HTTP server

**Need help deciding?** Ask in [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)

---

**Last Updated:** February 7, 2026
**Skill Seekers Version:** v2.10.0+
