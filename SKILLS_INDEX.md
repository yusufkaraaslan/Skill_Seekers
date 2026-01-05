# Skills Index

A comprehensive index of all available skill configurations for Skill Seekers.

> **Quick Start:** `skill-seekers scrape --config configs/<name>.json --enhance-local`

---

## AI/ML Frameworks

Skills for building AI agents, LLM applications, and machine learning pipelines.

| Skill | Description | Pages | Command |
|-------|-------------|-------|---------|
| **[LangChain](configs/langchain.json)** | Build AI agents with LCEL pipelines, RAG, LangGraph workflows, MCP integration, and LangSmith observability | 400 | `skill-seekers scrape --config configs/langchain.json` |
| **[DSPy](configs/dspy.json)** | Stanford's declarative prompt optimization framework with signatures, modules, teleprompters (MIPRO), and MCP support | 350 | `skill-seekers scrape --config configs/dspy.json` |
| **[AutoGen](configs/autogen.json)** | Microsoft's multi-agent framework with AgentChat, Teams (Swarm, Magentic-One, GraphFlow), and AutoGen Studio | 400 | `skill-seekers scrape --config configs/autogen.json` |
| **[Unsloth](configs/unsloth.json)** | 2-5x faster LLM fine-tuning with LoRA/QLoRA, GRPO/DPO/ORPO reinforcement learning, 500K context, vision models | 250 | `skill-seekers scrape --config configs/unsloth.json` |

---

## Web Frameworks

### Frontend

| Skill | Description | Pages | Command |
|-------|-------------|-------|---------|
| **[React](configs/react.json)** | React framework for building user interfaces with hooks, components, and state management | 300 | `skill-seekers scrape --config configs/react.json` |
| **[Vue](configs/vue.json)** | Progressive JavaScript framework for building UIs with reactive data binding | 200 | `skill-seekers scrape --config configs/vue.json` |
| **[Astro](configs/astro.json)** | Content-focused web framework with islands architecture and zero JS by default | 100 | `skill-seekers scrape --config configs/astro.json` |
| **[Tailwind CSS](configs/tailwind.json)** | Utility-first CSS framework for rapid UI development | 100 | `skill-seekers scrape --config configs/tailwind.json` |

### Backend

| Skill | Description | Pages | Command |
|-------|-------------|-------|---------|
| **[FastAPI](configs/fastapi.json)** | Modern Python web framework with automatic OpenAPI docs, async support, and type hints | 250 | `skill-seekers scrape --config configs/fastapi.json` |
| **[Django](configs/django.json)** | Python web framework with ORM, admin panel, authentication, and batteries included | 500 | `skill-seekers scrape --config configs/django.json` |
| **[Laravel](configs/laravel.json)** | PHP web framework with Eloquent ORM, Blade templates, and artisan CLI | 500 | `skill-seekers scrape --config configs/laravel.json` |
| **[Hono](configs/hono.json)** | Ultrafast web framework for edge computing, Cloudflare Workers, Deno, and Bun | 50 | `skill-seekers scrape --config configs/hono.json` |

---

## DevOps & Infrastructure

| Skill | Description | Pages | Command |
|-------|-------------|-------|---------|
| **[Kubernetes](configs/kubernetes.json)** | Container orchestration for deploying, scaling, and managing containerized applications | 1000 | `skill-seekers scrape --config configs/kubernetes.json` |
| **[Ansible Core](configs/ansible-core.json)** | IT automation for configuration management, application deployment, and orchestration | 800 | `skill-seekers scrape --config configs/ansible-core.json` |

---

## Game Development

| Skill | Description | Pages | Command |
|-------|-------------|-------|---------|
| **[Godot](configs/godot.json)** | Open-source game engine with GDScript, visual scripting, 2D/3D support | 500 | `skill-seekers scrape --config configs/godot.json` |
| **[Godot (Large)](configs/godot-large-example.json)** | Complete Godot documentation including all API references | 40000 | `skill-seekers scrape --config configs/godot-large-example.json` |

---

## Developer Tools

| Skill | Description | Pages | Command |
|-------|-------------|-------|---------|
| **[Claude Code](configs/claude-code.json)** | Anthropic's AI coding assistant CLI with agentic capabilities | 200 | `skill-seekers scrape --config configs/claude-code.json` |

---

## Gaming & Economy

| Skill | Description | Pages | Command |
|-------|-------------|-------|---------|
| **[Steam Economy](configs/steam-economy-complete.json)** | Steam partner documentation for in-game economies, trading, and marketplace integration | 1000 | `skill-seekers scrape --config configs/steam-economy-complete.json` |

---

## Unified Configs (Multi-Source)

These configs combine documentation + GitHub code analysis for comprehensive skills with conflict detection.

| Skill | Sources | Command |
|-------|---------|---------|
| **[React Unified](configs/react_unified.json)** | Docs + GitHub | `skill-seekers unified --config configs/react_unified.json` |
| **[Django Unified](configs/django_unified.json)** | Docs + GitHub | `skill-seekers unified --config configs/django_unified.json` |
| **[FastAPI Unified](configs/fastapi_unified.json)** | Docs + GitHub | `skill-seekers unified --config configs/fastapi_unified.json` |
| **[Godot Unified](configs/godot_unified.json)** | Docs + GitHub | `skill-seekers unified --config configs/godot_unified.json` |

---

## Test & Example Configs

These are for testing purposes and not recommended for production use.

| Config | Purpose |
|--------|---------|
| `python-tutorial-test.json` | Small test config (10 pages) |
| `test-manual.json` | Manual testing |
| `example_pdf.json` | PDF extraction example |
| `fastapi_unified_test.json` | Unified scraping test |
| `godot_github.json` | GitHub-only scraping test |
| `react_github.json` | GitHub-only scraping test |
| `deck_deck_go_local.json` | Local repository test |

---

## Quick Reference

### Scrape a Skill
```bash
# Basic scraping
skill-seekers scrape --config configs/react.json

# With AI enhancement (recommended)
skill-seekers scrape --config configs/react.json --enhance-local

# Async mode (2-3x faster)
skill-seekers scrape --config configs/react.json --async --workers 8

# One-command install (scrape + enhance + package + upload)
skill-seekers install --config react
```

### Estimate Before Scraping
```bash
skill-seekers estimate configs/kubernetes.json
```

### Package and Upload
```bash
# Package only
skill-seekers package output/react/

# Package and upload (requires ANTHROPIC_API_KEY)
skill-seekers package output/react/ --upload
```

### Unified Multi-Source
```bash
# Combine docs + GitHub + PDF
skill-seekers unified --config configs/react_unified.json

# With Claude-enhanced merging
skill-seekers unified --config configs/django_unified.json --merge-mode claude-enhanced
```

---

## Skill Categories by Use Case

### Building AI Agents
- **LangChain** - Production-ready agent framework with tools and memory
- **AutoGen** - Multi-agent orchestration with team patterns
- **DSPy** - Optimized prompts with automatic tuning

### Fine-tuning LLMs
- **Unsloth** - Fast fine-tuning with LoRA, RLHF, vision models

### Web Development
- **React/Vue/Astro** - Frontend frameworks
- **FastAPI/Django/Laravel** - Backend frameworks
- **Tailwind** - CSS utilities

### DevOps
- **Kubernetes** - Container orchestration
- **Ansible** - Infrastructure automation

### Game Development
- **Godot** - Open-source game engine

---

## Contributing New Configs

1. Create a new JSON file in `configs/`
2. Use an existing config as template
3. Test with `--dry-run` first:
   ```bash
   skill-seekers scrape --config configs/new.json --dry-run
   ```
4. Estimate page count:
   ```bash
   skill-seekers estimate configs/new.json
   ```
5. Submit PR with the new config

See [CLAUDE.md](CLAUDE.md) for detailed configuration documentation.
