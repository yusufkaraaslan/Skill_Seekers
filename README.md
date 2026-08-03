<p align="center">
  <img src="docs/assets/logo.png" alt="Skill Seekers" width="200"/>
</p>

# Skill Seekers

English | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Türkçe](README.tr.md) | [العربية](README.ar.md) | [हिन्दी](README.hi.md) | [Русский](README.ru.md)

[![Version](https://img.shields.io/badge/version-3.9.0-blue.svg)](https://github.com/yusufkaraaslan/Skill_Seekers/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Integration](https://img.shields.io/badge/MCP-40-Tools-blue.svg)](https://modelcontextprotocol.io)
[![Tested](https://img.shields.io/badge/Tests-3900%2B%20Passing-brightgreen.svg)](tests/)
[![PyPI version](https://badge.fury.io/py/skill-seekers.svg)](https://pypi.org/project/skill-seekers/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/skill-seekers.svg)](https://pypi.org/project/skill-seekers/)
[![Website](https://img.shields.io/badge/Website-skillseekersweb.com-blue.svg)](https://skillseekersweb.com/)
[![GitHub Repo stars](https://img.shields.io/github/stars/yusufkaraaslan/Skill_Seekers?style=social)](https://github.com/yusufkaraaslan/Skill_Seekers)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/skill-seekers?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/skill-seekers)

<a href="https://trendshift.io/repositories/18329" target="_blank"><img src="https://trendshift.io/api/badge/repositories/18329" alt="yusufkaraaslan%2FSkill_Seekers | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

**🧠 The data layer for AI systems.** Skill Seekers turns documentation sites, GitHub repos, PDFs, videos, notebooks, wikis, and more — **18 source types** — into structured knowledge assets, ready to power AI Skills (Claude, Gemini, OpenAI), RAG pipelines (LangChain, LlamaIndex, Pinecone), and AI coding assistants (Cursor, Windsurf, Cline). Prepare once, export to **22 targets**.

## 💛 Sponsors

<!-- SPONSORS:START -->
### Launch Partner

<p align="center">
  <a href="https://www.atlascloud.ai/"><img src="docs/assets/sponsors/atlas-cloud.png" alt="Atlas Cloud" width="200"></a><br/><sub><b>Launch Partner</b></sub>
</p>

[Atlas Cloud](https://www.atlascloud.ai/) — A full-modal, OpenAI-compatible AI inference platform. Skill Seekers supports it as a packaging/enhancement target via `--target atlas` with `ATLAS_API_KEY`.

### Silver Sponsors

<p align="center">
  <a href="https://www.rapidproxy.io/?utm_source=skillseekers&utm_medium=sponsor"><img src="docs/assets/sponsors/rapidproxy.png" alt="RapidProxy" width="140"></a><br/><sub><b>Sponsor — Silver</b></sub>
</p>
<!-- SPONSORS:END -->

**[Become a sponsor](SPONSORSHIP.md)** · [GitHub Sponsors](https://github.com/sponsors/yusufkaraaslan)

---

## 🚀 Quick Start

```bash
# 1. Install
pip install skill-seekers

# 2. Create a skill from any source
skill-seekers create https://docs.djangoproject.com/

# 3. Package it for your AI platform
skill-seekers package output/django --target claude
```

You now have `output/django-claude.zip`, ready to use.

```bash
# Pick a different AI agent for enhancement (default: claude)
skill-seekers create https://docs.djangoproject.com/ --agent kimi
skill-seekers create https://docs.djangoproject.com/ --agent-cmd "my-custom-agent run"
```

### 🛰️ AI-driven project scan

Point `scan` at a project and an AI agent reads its manifests, README, Dockerfile/CI and sampled source imports — then emits one config per detected framework, plus a `<project>-codebase.json` for your own code:

```bash
skill-seekers scan ./my-react-app --out ./configs/scanned/
# → react.json, vite.json, tailwind.json, jest.json, my-react-app-codebase.json

skill-seekers create ./configs/scanned/react.json
```

If a detection has no existing preset, the AI generates a fresh config; on exit you can optionally publish it back to the [community registry](https://github.com/yusufkaraaslan/skill-seekers-configs).

### All 18 source types

```bash
skill-seekers create facebook/react            # GitHub repository
skill-seekers create ./my-project              # Local codebase
skill-seekers create manual.pdf                # PDF
skill-seekers create report.docx               # Word
skill-seekers create book.epub                 # EPUB
skill-seekers create notebook.ipynb            # Jupyter
skill-seekers create openapi.yaml              # OpenAPI/Swagger
skill-seekers create presentation.pptx         # PowerPoint
skill-seekers create guide.adoc                # AsciiDoc
skill-seekers create page.html                 # Local HTML (or a whole dir)
skill-seekers create feed.rss                  # RSS/Atom
skill-seekers create curl.1                    # Man page

# Video (YouTube, Vimeo, or local — needs skill-seekers[video])
skill-seekers create --video-url https://www.youtube.com/watch?v=... --name mytutorial
skill-seekers create --setup                   # auto-install GPU-aware visual deps

skill-seekers create --space-key TEAM --name wiki               # Confluence
skill-seekers create --database-id ... --name docs              # Notion
skill-seekers create --chat-export-path ./slack-export --name team-chat  # Slack/Discord
```

See the [Scraping Guide](docs/user-guide/02-scraping.md) for every source type and its options.

---

## 📦 Installation

```bash
pip install skill-seekers              # Core: scraping, GitHub, PDF, packaging
pip install skill-seekers[all-llms]    # + every LLM platform
pip install skill-seekers[mcp]         # + MCP server
pip install skill-seekers[all]         # Everything
```

**Not sure what you need?** Run the wizard: `skill-seekers-setup`

<details>
<summary><b>All installation extras</b></summary>

| Install | Adds |
|---------|------|
| `skill-seekers[gemini]` | Google Gemini support |
| `skill-seekers[openai]` | OpenAI ChatGPT support |
| `skill-seekers[all-llms]` | All LLM platforms |
| `skill-seekers[mcp]` | MCP server for Claude Code, Cursor, etc. |
| `skill-seekers[video]` | YouTube/Vimeo transcript & metadata extraction |
| `skill-seekers[video-full]` | + Whisper transcription & visual frame extraction |
| `skill-seekers[jupyter]` | Jupyter Notebook support |
| `skill-seekers[pptx]` | PowerPoint support |
| `skill-seekers[confluence]` | Confluence wiki support |
| `skill-seekers[notion]` | Notion pages support |
| `skill-seekers[rss]` | RSS/Atom feed support |
| `skill-seekers[chat]` | Slack/Discord chat export support |
| `skill-seekers[asciidoc]` | AsciiDoc support |
| `skill-seekers[all]` | Everything |

> **Video visual deps (GPU-aware):** after installing `skill-seekers[video-full]`, run `skill-seekers create --setup` to auto-detect your GPU and install the matching PyTorch variant + easyocr.

</details>

**Prerequisites:** Python 3.10+, Git. New here? → **[Bulletproof Quick Start](docs/getting-started/BULLETPROOF_QUICKSTART.md)** 🎯

---

## 📚 Documentation

| I want to... | Read this |
|--------------|-----------|
| **Get started quickly** | [Quick Start](docs/getting-started/02-quick-start.md) — 3 commands to your first skill |
| **Understand the concepts** | [Core Concepts](docs/user-guide/01-core-concepts.md) |
| **Scrape sources** | [Scraping Guide](docs/user-guide/02-scraping.md) — all 18 source types |
| **Enhance skills with AI** | [Enhancement Guide](docs/user-guide/03-enhancement.md) · [Enhancement Modes](docs/features/ENHANCEMENT_MODES.md) |
| **Export skills** | [Packaging Guide](docs/user-guide/04-packaging.md) |
| **Build workflows** | [Workflows](docs/user-guide/05-workflows.md) |
| **Look up a command** | [CLI Reference](docs/reference/CLI_REFERENCE.md) — all 19 commands |
| **Configure** | [Config Format](docs/reference/CONFIG_FORMAT.md) · [Environment Variables](docs/reference/ENVIRONMENT_VARIABLES.md) |
| **Set up MCP** | [MCP Setup](docs/guides/MCP_SETUP.md) · [MCP Reference](docs/reference/MCP_REFERENCE.md) |
| **Integrate with RAG / IDEs** | [LangChain](docs/integrations/LANGCHAIN.md) · [RAG Pipelines](docs/integrations/RAG_PIPELINES.md) · [Cursor](docs/integrations/CURSOR.md) · [Windsurf](docs/integrations/WINDSURF.md) · [Cline](docs/integrations/CLINE.md) |
| **Handle huge doc sets** | [Large Documentation](docs/reference/LARGE_DOCUMENTATION.md) — 10K–40K+ pages |
| **Understand the architecture** | [UML Architecture](docs/UML_ARCHITECTURE.md) — 14 diagrams |
| **Fix a problem** | [Troubleshooting](docs/user-guide/06-troubleshooting.md) |

**Complete documentation index:** [docs/README.md](docs/README.md)

---

## 🎯 What you get

| Use case | Output | Powers |
|----------|--------|--------|
| **AI Skills** | Comprehensive `SKILL.md` + reference files | Claude Code, Gemini, GPT |
| **RAG pipelines** | Chunked documents with rich metadata | LangChain, LlamaIndex, Haystack |
| **Vector databases** | Pre-formatted data ready for upsert | Pinecone, Chroma, Weaviate, FAISS, Qdrant |
| **AI coding assistants** | Context files your IDE AI reads automatically | Cursor, Windsurf, Cline, Continue.dev |

### Export targets (22)

```bash
skill-seekers package output/react --target claude      # → Claude Skill (ZIP + YAML)
skill-seekers package output/react --target langchain   # → LangChain Documents
skill-seekers package output/react --target llama-index # → LlamaIndex TextNodes
skill-seekers package output/react --target ibm-bob     # → IBM Bob skill directory
```

**LLM platforms (12):** `claude` · `gemini` · `openai` · `minimax` · `opencode` · `kimi` · `deepseek` · `qwen` · `openrouter` · `together` · `fireworks` · `markdown`
**RAG & vector (8):** `langchain` · `llama-index` · `haystack` · `chroma` · `faiss` · `weaviate` · `qdrant` · `pinecone`
**Other (2):** `atlas` · `ibm-bob`

See the [Feature Matrix](docs/reference/FEATURE_MATRIX.md) for per-platform support details.

### Why it matters

- ⚡ **99% faster** — days of manual data prep → 15–45 minutes
- 🎯 **Real skill quality** — 500+ line `SKILL.md` files with examples, patterns, and guides
- 📊 **RAG-ready chunks** — smart chunking preserves code blocks and context
- 🔄 **Multi-source** — combine docs + GitHub + PDFs + videos into one knowledge asset
- 🌐 **One prep, every target** — export to 22 targets without re-scraping
- ✅ **Battle-tested** — 3,900+ tests, 68 workflow presets, production-ready

---

## ✨ Key capabilities

<details>
<summary><b>Documentation scraping</b> — SPA discovery, llms.txt, smart categorization</summary>

Three-layer discovery for JavaScript SPA sites (`sitemap.xml` → `llms.txt` → headless browser rendering), automatic `llms.txt` detection (10× faster when present), smart topic categorization, and a lenient HTML parser fallback so broken markup still scrapes.

→ [Scraping Guide](docs/user-guide/02-scraping.md) · [llms.txt Support](docs/reference/LLMS_TXT_SUPPORT.md)
</details>

<details>
<summary><b>GitHub & codebase analysis (C3.x)</b> — AST parsing, pattern detection, how-to guides</summary>

Three-stream architecture: code analysis (AST, design patterns, tests), documentation (README, `docs/`, wiki), and community (issues, PRs, metadata). The C3.x pipeline adds 10 GoF pattern detectors across 9 languages, usage examples extracted from tests, AI-written how-to guides, config extraction, and architecture overviews.

```bash
skill-seekers create ./my-project --preset quick          # 1–2 min, surface level
skill-seekers create ./my-project --preset standard       # balanced (default)
skill-seekers create ./my-project --preset comprehensive  # deep, exhaustive
```

→ [Pattern Detection](docs/features/PATTERN_DETECTION.md) · [How-To Guides](docs/features/HOW_TO_GUIDES.md) · [Test Example Extraction](docs/features/TEST_EXAMPLE_EXTRACTION.md)
</details>

<details>
<summary><b>AI enhancement</b> — API or local agents, 68 workflow presets</summary>

Every AI call runs through one transport, in **API mode** (Anthropic, Google Gemini, OpenAI, Moonshot/Kimi, MiniMax) or **LOCAL mode** (Claude Code, Kimi Code, Codex, Copilot, OpenCode, custom agents — no API costs). Control depth with `--enhance-level 0-3` and pick an agent with `--agent`.

→ [Enhancement Guide](docs/user-guide/03-enhancement.md) · [Enhancement Modes](docs/features/ENHANCEMENT_MODES.md) · [Multi-Agent Setup](docs/guides/MULTI_AGENT_SETUP.md)
</details>

<details>
<summary><b>Unified multi-source scraping</b> — combine many sources into one skill</summary>

One config can pull documentation, GitHub, PDFs, videos, and more into a single knowledge asset, with conflict detection and pairwise synthesis across sources.

→ [Unified Scraping](docs/features/UNIFIED_SCRAPING.md)
</details>

<details>
<summary><b>Video extraction</b> — transcripts, frames, on-screen code</summary>

YouTube, Vimeo, and local files. Three-tier transcript fallback (subtitles → YouTube transcript API → local Whisper), plus optional visual extraction that OCRs on-screen code from sampled frames.

→ [Video Guide](docs/VIDEO_GUIDE.md)
</details>

<details>
<summary><b>Quality, sync & scale</b></summary>

Quality scoring with a gate (`skill-seekers quality output/react/ --threshold 7`), provisional English readability metrics (informational — they never affect the score), doc-change detection with scheduled re-scrapes and notifications, streaming ingestion for very large doc sets, and incremental updates.

→ [Large Documentation](docs/reference/LARGE_DOCUMENTATION.md) · [Code Quality](docs/reference/CODE_QUALITY.md)
</details>

---

## 🔌 MCP Integration (40 tools)

Skill Seekers ships an MCP server for Claude Code, Cursor, Windsurf, VS Code + Cline, and IntelliJ IDEA.

```bash
# stdio mode (Claude Code, VS Code + Cline)
python -m skill_seekers.mcp.server_fastmcp

# HTTP mode (Cursor, Windsurf, IntelliJ)
python -m skill_seekers.mcp.server_fastmcp --transport http --port 8765
```

Then just ask your assistant: *"Package and upload the React skill."*

→ [MCP Setup](docs/guides/MCP_SETUP.md) · [MCP Reference](docs/reference/MCP_REFERENCE.md) · [HTTP Transport](docs/guides/HTTP_TRANSPORT.md)

---

## 🤖 Installing to AI agents

Skills install automatically into **19 AI coding agents**:

```bash
skill-seekers install-agent output/react/ --agent cursor
skill-seekers install-agent output/react/ --agent all      # every detected agent
skill-seekers install-agent output/react/ --agent cursor --dry-run
```

| Agent | Path | Scope |
|-------|------|-------|
| Claude Code | `~/.claude/skills/` | Global |
| Cursor | `.cursor/skills/` | Project |
| VS Code / Copilot | `.github/skills/` | Project |
| Amp | `~/.amp/skills/` | Global |
| Goose | `~/.config/goose/skills/` | Global |
| OpenCode | `~/.opencode/skills/` | Global |
| Letta | `~/.letta/skills/` | Global |
| Aide | `~/.aide/skills/` | Global |
| Windsurf | `~/.windsurf/skills/` | Global |
| Neovate | `~/.neovate/skills/` | Global |
| Roo Code | `.roo/skills/` | Project |
| Cline | `.cline/skills/` | Project |
| Aider | `~/.aider/skills/` | Global |
| Bolt | `.bolt/skills/` | Project |
| Kilo Code | `.kilo/skills/` | Project |
| Continue | `~/.continue/skills/` | Global |
| Kimi Code | `~/.kimi/skills/` | Global |
| IBM Bob | `.bob/skills/` | Project |

### Uploading to Claude

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers package output/react/ --upload   # package + upload
skill-seekers upload output/react.zip          # upload an existing zip
```

No API key? Package it and upload `output/react.zip` manually at [claude.ai/skills](https://claude.ai/skills).

→ [Upload Guide](docs/guides/UPLOAD_GUIDE.md)

---

## ⚙️ How it works

```mermaid
graph LR
    A[Documentation Website] --> B[Skill Seekers]
    B --> C[Scraper]
    B --> D[AI Enhancement]
    B --> E[Packager]
    C --> F[Organized References]
    D --> F
    F --> E
    E --> G[AI Skill .zip]
    G --> H[Upload to AI Platform]
```

1. **Scrape** — extract every page (checking `llms.txt` first)
2. **Categorize** — organize content into topics (API, guides, tutorials, …)
3. **Enhance** — AI writes a comprehensive `SKILL.md` with examples
4. **Package** — bundle into a platform-ready artifact
5. **Upload** — ship it to your AI platform (optional)

### Architecture

**8 core modules + 5 utility modules** (~200 classes):

| Module | Purpose |
|--------|---------|
| **CLICore** | Git-style command dispatcher, source auto-detection |
| **Scrapers** | 18 source-type extractors on a shared build layer |
| **Adaptors** | 22 output platform formats behind one `SkillAdaptor` ABC |
| **Analysis** | C3.x codebase pipeline, 10 GoF pattern detectors |
| **Enhancement** | AI improvement via a single `AgentClient` transport |
| **Packaging** | Package, upload, and install skills |
| **MCP** | FastMCP server (40 tools, 10 tool modules) |
| **Sync** | Doc change detection and notification |

→ [UML Architecture](docs/UML_ARCHITECTURE.md) · [API Reference](docs/reference/API_REFERENCE.md) · [Skill Architecture](docs/reference/SKILL_ARCHITECTURE.md)

---

## 🆕 New in v3.9.0

- **HTML parser fallback for broken markup** (#96) — severely malformed pages no longer scrape as empty; well-formed pages are byte-identical.
- **Transient-failure retries** — the doc scraper (#97) and MCP `fetch_config` (#92) now retry connection blips and 5xx with backoff; 4xx still fails fast.
- **Whisper transcription fallback** (#420) — local videos without subtitles finally get a real transcript.
- **MiniMax image OCR + registry-driven multimodal providers** (#423) — providers declare their wire protocol and image capability; China-issued keys work against the right endpoint.
- **Token-lean GitHub issue defaults** (#169) — GitHub skills no longer bundle full closed-issue history by default.
- **Env-driven CORS across all three servers** (#422, #424) — no more wildcard origins with credentials.

Full history: **[CHANGELOG.md](CHANGELOG.md)**

---

## 📈 Performance

| Documentation size | Time | Output |
|---|---|---|
| Small (< 100 pages) | 5–10 min | ~2 MB |
| Medium (100–500 pages) | 15–30 min | ~10 MB |
| Large (500–2,000 pages) | 30–60 min | ~40 MB |
| Huge (10K–40K+ pages) | Use `stream` | See [Large Documentation](docs/reference/LARGE_DOCUMENTATION.md) |

---

## 🐛 Troubleshooting

```bash
skill-seekers doctor          # diagnose installation & environment
skill-seekers sync-config     # detect config drift
```

Common issues and fixes: **[Troubleshooting Guide](docs/user-guide/06-troubleshooting.md)** · [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## 🤝 Contributing

Contributions are welcome — see **[CONTRIBUTING.md](CONTRIBUTING.md)**.

- 📋 **[Development Roadmap & Tasks](https://github.com/users/yusufkaraaslan/projects/2)** — pick any task
- 💬 **[Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)** — questions and ideas
- 🐛 **[Issues](https://github.com/yusufkaraaslan/Skill_Seekers/issues)** — bugs and feature requests

---

## 📝 License

MIT — see [LICENSE](LICENSE).

## 🔒 Security

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/yusufkaraaslan-skill-seekers-badge.png)](https://mseep.ai/app/yusufkaraaslan-skill-seekers)

---

## 🌐 Ecosystem

Skill Seekers is a multi-repo project:

| Repository | Description | Links |
|-----------|-------------|-------|
| **[Skill_Seekers](https://github.com/yusufkaraaslan/Skill_Seekers)** | Core CLI & MCP server (this repo) | [PyPI](https://pypi.org/project/skill-seekers/) |
| **[skillseekersweb](https://github.com/yusufkaraaslan/skillseekersweb)** | Website & documentation | [Live](https://skillseekersweb.com/) |
| **[skill-seekers-configs](https://github.com/yusufkaraaslan/skill-seekers-configs)** | Community config repository | |
| **[skill-seekers-action](https://github.com/yusufkaraaslan/skill-seekers-action)** | GitHub Action for CI/CD | |
| **[skill-seekers-plugin](https://github.com/yusufkaraaslan/skill-seekers-plugin)** | Claude Code plugin | |
| **[homebrew-skill-seekers](https://github.com/yusufkaraaslan/homebrew-skill-seekers)** | Homebrew tap for macOS | |

> **Want to contribute?** The website and configs repos are great starting points for new contributors!
