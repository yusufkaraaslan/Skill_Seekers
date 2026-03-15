# Core Concepts

> **Skill Seekers v3.2.0**  
> **Understanding how Skill Seekers works**

---

## Overview

Skill Seekers transforms documentation, code, and content into **structured knowledge assets** that AI systems can use effectively. It supports **17 source types** including documentation sites, GitHub repos, PDFs, videos, notebooks, wikis, and more.

```
Raw Content → Skill Seekers → AI-Ready Skill
     ↓                              ↓
  (docs, code, PDFs,          (SKILL.md +
   videos, notebooks,          references)
   wikis, feeds, etc.)
```

---

## What is a Skill?

A **skill** is a structured knowledge package containing:

```
output/my-skill/
├── SKILL.md              # Main file (400+ lines typically)
├── references/           # Categorized content
│   ├── index.md         # Navigation
│   ├── getting_started.md
│   ├── api_reference.md
│   └── ...
├── .skill-seekers/      # Metadata
└── assets/              # Images, downloads
```

### SKILL.md Structure

```markdown
# My Framework Skill

## Overview
Brief description of the framework...

## Quick Reference
Common commands and patterns...

## Categories
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Guides](#guides)

## Getting Started
### Installation
```bash
npm install my-framework
```

### First Steps
...

## API Reference
...
```

### Why This Structure?

| Element | Purpose |
|---------|---------|
| **Overview** | Quick context for AI |
| **Quick Reference** | Common patterns at a glance |
| **Categories** | Organized deep dives |
| **Code Examples** | Copy-paste ready snippets |

---

## Source Types

Skill Seekers works with **17 types of sources**:

### 1. Documentation Websites

**What:** Web-based documentation (ReadTheDocs, Docusaurus, GitBook, etc.)

**Examples:**
- React docs (react.dev)
- Django docs (docs.djangoproject.com)
- Kubernetes docs (kubernetes.io)

**Command:**
```bash
skill-seekers create https://docs.example.com/
```

**Best for:**
- Framework documentation
- API references
- Tutorials and guides

---

### 2. GitHub Repositories

**What:** Source code repositories with analysis

**Extracts:**
- Code structure and APIs
- README and documentation
- Issues and discussions
- Releases and changelog

**Command:**
```bash
skill-seekers create owner/repo
skill-seekers github --repo owner/repo
```

**Best for:**
- Understanding codebases
- API implementation details
- Contributing guidelines

---

### 3. PDF Documents

**What:** PDF manuals, papers, documentation

**Handles:**
- Text extraction
- OCR for scanned PDFs
- Table extraction
- Image extraction

**Command:**
```bash
skill-seekers create manual.pdf
skill-seekers pdf --pdf manual.pdf
```

**Best for:**
- Product manuals
- Research papers
- Legacy documentation

---

### 4. Local Codebases

**What:** Your local projects and code

**Analyzes:**
- Source code structure
- Comments and docstrings
- Test files
- Configuration patterns

**Command:**
```bash
skill-seekers create ./my-project
skill-seekers analyze --directory ./my-project
```

**Best for:**
- Your own projects
- Internal tools
- Code review preparation

---

### 5. Word Documents

**What:** Microsoft Word (.docx) files

**Command:**
```bash
skill-seekers create report.docx
```

---

### 6. EPUB Books

**What:** EPUB e-book files

**Command:**
```bash
skill-seekers create book.epub
```

---

### 7. Videos

**What:** YouTube, Vimeo, or local video files (transcripts + visual analysis)

**Command:**
```bash
skill-seekers create https://www.youtube.com/watch?v=...
skill-seekers video --url https://www.youtube.com/watch?v=...
```

---

### 8. Jupyter Notebooks

**What:** `.ipynb` notebook files with code, markdown, and outputs

**Command:**
```bash
skill-seekers create analysis.ipynb
skill-seekers jupyter --notebook analysis.ipynb
```

---

### 9. Local HTML Files

**What:** HTML/HTM files on disk

**Command:**
```bash
skill-seekers create page.html
skill-seekers html --file page.html
```

---

### 10. OpenAPI/Swagger Specs

**What:** OpenAPI YAML/JSON specifications

**Command:**
```bash
skill-seekers create api-spec.yaml
skill-seekers openapi --spec api-spec.yaml
```

---

### 11. AsciiDoc

**What:** AsciiDoc (.adoc, .asciidoc) files

**Command:**
```bash
skill-seekers create guide.adoc
skill-seekers asciidoc --file guide.adoc
```

---

### 12. PowerPoint Presentations

**What:** Microsoft PowerPoint (.pptx) files

**Command:**
```bash
skill-seekers create slides.pptx
skill-seekers pptx --file slides.pptx
```

---

### 13. RSS/Atom Feeds

**What:** RSS or Atom feed files

**Command:**
```bash
skill-seekers create feed.rss
skill-seekers rss --feed feed.rss
```

---

### 14. Man Pages

**What:** Unix manual pages (.1 through .8, .man)

**Command:**
```bash
skill-seekers create grep.1
skill-seekers manpage --file grep.1
```

---

### 15. Confluence Wikis

**What:** Atlassian Confluence spaces (via API or export)

**Command:**
```bash
skill-seekers confluence --space DEV --base-url https://wiki.example.com
```

---

### 16. Notion Workspaces

**What:** Notion pages and databases (via API or export)

**Command:**
```bash
skill-seekers notion --database abc123
```

---

### 17. Slack/Discord Chat

**What:** Chat platform exports or API access

**Command:**
```bash
skill-seekers chat --export slack-export/
```

---

## The Workflow

### Phase 1: Ingest

```
┌─────────────┐     ┌──────────────┐
│   Source    │────▶│   Scraper    │
│ (URL/repo/  │     │ (extracts    │
│  PDF/local) │     │  content)    │
└─────────────┘     └──────────────┘
```

- Detects source type automatically
- Crawls and downloads content
- Respects rate limits
- Extracts text, code, metadata

---

### Phase 2: Structure

```
┌──────────────┐     ┌──────────────┐
│   Raw Data   │────▶│   Builder    │
│ (pages/files/│     │ (organizes   │
│  commits)    │     │  by category)│
└──────────────┘     └──────────────┘
```

- Categorizes content by topic
- Extracts code examples
- Builds navigation structure
- Creates reference files

---

### Phase 3: Enhance (Optional)

```
┌──────────────┐     ┌──────────────┐
│   SKILL.md   │────▶│  Enhancer    │
│  (basic)     │     │ (AI improves │
│              │     │  quality)    │
└──────────────┘     └──────────────┘
```

- AI reviews and improves content
- Adds examples and patterns
- Fixes formatting
- Enhances navigation

**Modes:**
- **API:** Uses Claude API (fast, costs ~$0.10-0.30)
- **LOCAL:** Uses Claude Code (free, requires Claude Code Max)

---

### Phase 4: Package

```
┌──────────────┐     ┌──────────────┐
│   Skill Dir  │────▶│   Packager   │
│ (structured  │     │ (creates     │
│  content)    │     │  platform    │
│              │     │  format)     │
└──────────────┘     └──────────────┘
```

- Formats for target platform
- Creates archives (ZIP, tar.gz)
- Optimizes for size
- Validates structure

---

### Phase 5: Upload (Optional)

```
┌──────────────┐     ┌──────────────┐
│   Package    │────▶│   Platform   │
│ (.zip/.tar)  │     │ (Claude/     │
│              │     │  Gemini/etc) │
└──────────────┘     └──────────────┘
```

- Uploads to target platform
- Configures settings
- Returns skill ID/URL

---

## Enhancement Levels

Control how much AI enhancement is applied:

| Level | What Happens | Use Case |
|-------|--------------|----------|
| **0** | No enhancement | Fast scraping, manual review |
| **1** | SKILL.md only | Basic improvement |
| **2** | + architecture/config | **Recommended** - good balance |
| **3** | Full enhancement | Maximum quality, takes longer |

**Default:** Level 2

```bash
# Skip enhancement (fastest)
skill-seekers create <source> --enhance-level 0

# Full enhancement (best quality)
skill-seekers create <source> --enhance-level 3
```

---

## Target Platforms

Package skills for different AI systems:

| Platform | Format | Use |
|----------|--------|-----|
| **Claude AI** | ZIP + YAML | Claude Code, Claude API |
| **Gemini** | tar.gz | Google Gemini |
| **OpenAI** | ZIP + Vector | ChatGPT, Assistants API |
| **LangChain** | Documents | RAG pipelines |
| **LlamaIndex** | TextNodes | Query engines |
| **ChromaDB** | Collection | Vector search |
| **Weaviate** | Objects | Vector database |
| **Cursor** | .cursorrules | IDE AI assistant |
| **Windsurf** | .windsurfrules | IDE AI assistant |

---

## Configuration

### Simple (Auto-Detect)

```bash
# Just provide the source
skill-seekers create https://docs.react.dev/
```

### Preset Configs

```bash
# Use predefined configuration
skill-seekers create --config react
```

**Available presets:** `react`, `vue`, `django`, `fastapi`, `godot`, etc.

### Custom Config

```bash
# Create custom config
cat > configs/my-docs.json << 'EOF'
{
  "name": "my-docs",
  "base_url": "https://docs.example.com/",
  "max_pages": 200
}
EOF

skill-seekers create --config configs/my-docs.json
```

See [Config Format](../reference/CONFIG_FORMAT.md) for full specification.

---

## Multi-Source Skills

Combine multiple sources into one skill:

```bash
# Create unified config
cat > configs/my-project.json << 'EOF'
{
  "name": "my-project",
  "sources": [
    {"type": "docs", "base_url": "https://docs.example.com/"},
    {"type": "github", "repo": "owner/repo"},
    {"type": "pdf", "pdf_path": "manual.pdf"}
  ]
}
EOF

# Run unified scraping
skill-seekers unified --config configs/my-project.json
```

**Benefits:**
- Single skill with complete context
- Automatic conflict detection
- Cross-referenced content

---

## Caching and Resumption

### How Caching Works

```
First scrape:    Downloads all pages → saves to output/{name}_data/
Second scrape:   Reuses cached data → fast rebuild
```

### Skip Scraping

```bash
# Use cached data, just rebuild
skill-seekers create --config react --skip-scrape
```

### Resume Interrupted Jobs

```bash
# List resumable jobs
skill-seekers resume --list

# Resume specific job
skill-seekers resume job-abc123
```

---

## Rate Limiting

Be respectful to servers:

```bash
# Default: 0.5 seconds between requests
skill-seekers create <source>

# Faster (for your own servers)
skill-seekers create <source> --rate-limit 0.1

# Slower (for rate-limited sites)
skill-seekers create <source> --rate-limit 2.0
```

**Why it matters:**
- Prevents being blocked
- Respects server resources
- Good citizenship

---

## Key Takeaways

1. **Skills are structured knowledge** - Not just raw text
2. **Auto-detection works** - Usually don't need custom configs
3. **Enhancement improves quality** - Level 2 is the sweet spot
4. **Package once, use everywhere** - Same skill, multiple platforms
5. **Cache saves time** - Rebuild without re-scraping

---

## Next Steps

- [Scraping Guide](02-scraping.md) - Deep dive into source options
- [Enhancement Guide](03-enhancement.md) - AI enhancement explained
- [Config Format](../reference/CONFIG_FORMAT.md) - Custom configurations
