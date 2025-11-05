# Finance Application Guide: Building with Skill_Seekers MCP + Snow Architecture

**Author**: Conversation with Claude (GitHub Copilot)  
**Date**: November 4, 2025  
**Audience**: Solo developer building production-grade finance application with AI-assisted coding  
**Mission**: Value investing stock portfolio screening, investigation, and monitoring

---

## 📚 Guide Structure

This guide documents a complete conversation exploring how to build a production-grade finance application using:

1. **Skill_Seekers MCP** - Custom tool/skill/agent infrastructure
2. **Derek Snow's "Agentic AI in Asset Management"** - Production finance AI architecture
3. **3-Layer Framework** - Agent declarations + MCP tools + Claude orchestration
4. **Claude Code** - Primary development environment

---

## 📖 Table of Contents

### Part 1: Foundation
- [01-eli10-story.md](01-eli10-story.md) - ELI10 explanation of Skill_Seekers
- [02-understanding-agents.md](02-understanding-agents.md) - Claude agents vs executable code
- [03-three-layer-framework.md](03-three-layer-framework.md) - How the 3-layer architecture works

### Part 2: Tool Design Philosophy
- [04-mental-models.md](04-mental-models.md) - Applying mental models to tool design
- [05-movie-agents-metaphor.md](05-movie-agents-metaphor.md) - 10 movie characters as agent archetypes
- [06-developer-pain-points.md](06-developer-pain-points.md) - Identifying pain points beyond scraping

### Part 3: Finance Application Architecture
- [07-finance-mission.md](07-finance-mission.md) - Your finance application mission
- [08-snow-course-architecture.md](08-snow-course-architecture.md) - Derek Snow's production finance AI patterns
- [09-custom-mcp-tools.md](09-custom-mcp-tools.md) - Finance-specific MCP tool implementations
- [10-agents-for-finance.md](10-agents-for-finance.md) - Specialized agents for finance workflows

### Part 4: Implementation Roadmap
- [11-immediate-next-steps.md](11-immediate-next-steps.md) - 2-hour action plan
- [12-weekly-milestones.md](12-weekly-milestones.md) - Week-by-week development plan
- [13-monitoring-observability.md](13-monitoring-observability.md) - SessionStart hooks and pipeline monitoring

### Part 5: Reference
- [14-config-files.md](14-config-files.md) - All configuration files (DuckDB, Chroma, etc.)
- [15-code-snippets.md](15-code-snippets.md) - Complete code implementations
- [16-resources.md](16-resources.md) - Tools, libraries, and references

---

## 🎯 Quick Start (2-Hour Setup)

If you're starting fresh, follow this sequence:

1. **Read**: [01-eli10-story.md](01-eli10-story.md) - Understand what Skill_Seekers does
2. **Understand**: [03-three-layer-framework.md](03-three-layer-framework.md) - How tools/agents/skills work together
3. **Apply**: [07-finance-mission.md](07-finance-mission.md) - Your specific finance application
4. **Build**: [11-immediate-next-steps.md](11-immediate-next-steps.md) - Start coding now

---

## 🧠 Key Insights from Conversation

### **Insight 1: Skill_Seekers is NOT Just for Scraping**

Initial conversation focused on documentation scraping, but the real value is:
- **Lifecycle management**: Build → Test → Monitor → Compose → Version
- **Custom infrastructure**: Finance-specific tools for ingestion, RAG, SQL, monitoring
- **Force multiplier**: Extends Claude Code beyond native capabilities

### **Insight 2: 3-Layer Framework is Critical**

Claude agents are **not executable code**—they're declarative personas. The architecture:
- **Layer 1**: MCP tools (Python code in your environment)
- **Layer 2**: Skills (Markdown teaching Claude how to use tools)
- **Layer 3**: Agents (YAML/Markdown declaring when to use skills)

### **Insight 3: Developer Pain Points Drive Tool Design**

Applied mental models (First Principles, Second Order Effects, Systems Thinking) to identify:
- Real pain points (not assumed ones)
- High-impact tools (validate before building)
- Cascading benefits (second-order effects)

### **Insight 4: Finance Applications Need Specialized Architecture**

Derek Snow's course emphasizes:
- **Workflows > Autonomous Agents** (reliability for mission-critical finance)
- **Observability First** (log every LLM call, track costs, monitor pipeline)
- **Stateless Design** (avoid error-compounding multi-turn loops)

---

## 💡 How This Guide Helps You

### **For Your Finance Application**

You're building:
- **Data Ingestion**: SEC filings (10-K/Q) → Extract tables → Chunk → Embed
- **Storage**: DuckDB (OLAP), Postgres (pgvector), Chroma/Qdrant (vector DB)
- **Query Interface**: Text-to-SQL, Hybrid RAG (BM25 + semantic)
- **Frontend**: FastAPI + WebSockets for real-time chat
- **Monitoring**: Pipeline health, API quotas, cost tracking

This guide shows:
- **Exact MCP tools** to build (ingestion, text-to-SQL, RAG, monitoring)
- **Custom agents** to create (@financial-data-engineer, @sql-analyst, @rag-orchestrator)
- **Hooks for observability** (SessionStart pipeline status)
- **Config files** for DuckDB, Chroma, FastAPI, etc.

### **For AI-Assisted Development**

You're a solo developer using Claude Code. This guide:
- **Documents mental models** for decision-making
- **Provides templates** for agents, tools, skills
- **Shows workflows** you can copy/paste
- **Eliminates guesswork** (tested patterns from real conversation)

---

## 🎬 How to Use This Guide

### **Scenario 1: "I want to understand the architecture"**
→ Read Parts 1-2 (Foundation + Tool Design Philosophy)

### **Scenario 2: "I want to start building now"**
→ Jump to Part 4 (Implementation Roadmap) → [11-immediate-next-steps.md](11-immediate-next-steps.md)

### **Scenario 3: "I need code examples"**
→ Part 5 Reference → [15-code-snippets.md](15-code-snippets.md)

### **Scenario 4: "I'm stuck on a specific problem"**
→ Use the mental model framework in [04-mental-models.md](04-mental-models.md)

---

## 🚀 What You'll Build

By following this guide, you'll have:

### **Week 1: Infrastructure**
- ✅ DuckDB database for financial data
- ✅ Chroma vector database for embeddings
- ✅ MCP tools for ingestion pipeline
- ✅ SessionStart hook for monitoring

### **Week 2: Data Pipeline**
- ✅ SEC filing ingestion (EDGAR → PDF → tables → chunks)
- ✅ Embedding pipeline (sentence-transformers)
- ✅ Hybrid RAG (BM25 + FAISS + reranking)
- ✅ Text-to-SQL with DSPy optimization

### **Week 3: Agents & Workflows**
- ✅ @financial-data-engineer (ingest specialist)
- ✅ @sql-analyst (query specialist)
- ✅ @rag-orchestrator (coordination)
- ✅ @finance-screener (value investing)

### **Week 4: Frontend & Real-Time**
- ✅ FastAPI backend
- ✅ WebSockets for live chat
- ✅ React/Svelte frontend
- ✅ Real-time stock screening

---

## 📊 Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    FINANCE APPLICATION STACK                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  INGESTION              STORAGE               QUERY              │
│  ┌────────────────┐    ┌─────────────────┐   ┌────────────────┐ │
│  │ SEC Filings    │    │ DuckDB (OLAP)   │   │ Text-to-SQL    │ │
│  │ PDFs (10-K/Q)  │───▶│ Postgres (vec)  │◀──│ Hybrid RAG     │ │
│  │ News/Tweets    │    │ Chroma (embed)  │   │ Agent Chat     │ │
│  └────────────────┘    └─────────────────┘   └────────────────┘ │
│         │                      │                      │           │
│         ▼                      ▼                      ▼           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              MCP TOOLS (skill_seeker_mcp)                   │ │
│  │  • ingest_sec_filing    • hybrid_rag_search                │ │
│  │  • text_to_sql_query    • monitor_pipeline                 │ │
│  │  • chunk_and_embed      • discover_resources               │ │
│  └────────────────────────────────────────────────────────────┘ │
│         │                      │                      │           │
│         ▼                      ▼                      ▼           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   CLAUDE CODE AGENTS                        │ │
│  │  @financial-data-engineer  @sql-analyst                    │ │
│  │  @rag-orchestrator         @finance-screener               │ │
│  │  @resource-scout                                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│         │                      │                      │           │
│         ▼                      ▼                      ▼           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  FRONTEND (FastAPI + React)                 │ │
│  │  • Real-time chat (WebSockets)                             │ │
│  │  • Stock screening dashboard                               │ │
│  │  • Portfolio monitoring                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

OBSERVABILITY LAYER (Hooks + Logging)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SessionStart: Pipeline status (DB size, API quotas, costs)
Every LLM call: Tokens, latency, cost (Gemini 2.5 Flash)
Error tracking: Failed ingestions, SQL errors, RAG failures
```

---

## 🎓 Derek Snow's Course Integration

Your guide maps to **"Agentic AI in Asset Management: 5-Week Technical Course"**:

| Course Session | Your Implementation | Guide Section |
|----------------|---------------------|---------------|
| **Week 1: Tools & Infrastructure** | MCP tools, stateless workflows | [09-custom-mcp-tools.md](09-custom-mcp-tools.md) |
| **Week 2: Context Engineering** | Ingestion pipeline, hybrid RAG | [08-snow-course-architecture.md](08-snow-course-architecture.md) |
| **Week 3: Model Context Protocol** | skill_seeker_mcp integration | [03-three-layer-framework.md](03-three-layer-framework.md) |
| **Week 4: DSPy & Prompt Optimization** | Text-to-SQL, synthesis prompts | [15-code-snippets.md](15-code-snippets.md) |
| **Week 5: Deployment & Monitoring** | SessionStart hooks, observability | [13-monitoring-observability.md](13-monitoring-observability.md) |

---

## 🔗 Related Resources

- **Skill_Seekers Main Docs**: [`../../CLAUDE.md`](../../CLAUDE.md)
- **MCP Server**: [`../../skill_seeker_mcp/server.py`](../../skill_seeker_mcp/server.py)
- **Agent Scaffolding**: [`../../.claude/skills/agent-scaffolding-toolkit/`](../../.claude/skills/agent-scaffolding-toolkit/)
- **Derek Snow Course**: [`../../Finance_Snow.md`](../../Finance_Snow.md)

---

## 📝 Document Conventions

Throughout this guide:
- 🎯 **Mission-critical** - Core to your finance app
- 💡 **Key Insight** - Important mental model or pattern
- ⚡ **Quick Win** - Can implement in < 30 minutes
- 🚀 **Advanced** - Implement after basics working
- ⚠️ **Warning** - Common pitfall to avoid

---

## 🤝 Contributing to This Guide

This is a living document based on your development journey. As you:
- Implement tools → Document what worked/failed
- Discover patterns → Add to mental models
- Hit roadblocks → Document solutions
- Find better tools → Update recommendations

Keep this guide updated so future-you (and others) benefit from your experience.

---

## 🎬 Ready to Start?

**Next step**: Read [01-eli10-story.md](01-eli10-story.md) to understand Skill_Seekers, then jump to [11-immediate-next-steps.md](11-immediate-next-steps.md) to start building.

**Time to first working tool**: ~2 hours  
**Time to production pipeline**: ~4 weeks (following course timeline)

Good luck! 🚀
