# Documentation Overhaul Plan - Skill Seekers v3.1.0

> **Status:** Draft - Pending Review  
> **Scope:** Complete documentation rewrite  
> **Target:** Eliminate user confusion, remove phantom commands, establish single source of truth

---

## Executive Summary

### Problem Statement (from Issue #286)
- Docs reference removed commands (`python3 cli/doc_scraper.py` pattern)
- Phantom commands documented that don't exist (`merge-sources`, `generate-router`, etc.)
- 83 markdown files with no clear hierarchy
- Users cannot find accurate information

### Solution
Complete documentation rewrite with:
1. **Single source of truth** CLI reference (all 20 commands)
2. **Working** quick start guide (3 commands to first skill)
3. **Clear documentation hierarchy** (4 categories max)
4. **Deprecation strategy** for outdated files

---

## Phase Overview

| Phase | Name | Duration | Output |
|-------|------|----------|--------|
| 1 | Foundation | 3-4 hrs | CLI_REFERENCE.md, MCP reference, new structure |
| 2 | User Guides | 3-4 hrs | Quick start, workflows, troubleshooting |
| 3 | Integration | 2-3 hrs | README rewrite, navigation, redirects |
| 4 | Cleanup | 1-2 hrs | Archive old files, add deprecation notices |
| **Total** | | **10-14 hrs** | Complete documentation overhaul |

---

## Detailed Phase Breakdown

---

## Phase 1: Foundation (CLI Reference & Structure)

### 1.1 Create Master CLI Reference
**File:** `docs/reference/CLI_REFERENCE.md` (NEW)

**Sections:**
```
CLI_REFERENCE.md
├── Overview
│   ├── Installation
│   ├── Global Flags
│   └── Environment Variables
│
├── Command Reference (alphabetical)
│   ├── analyze
│   ├── config
│   ├── create
│   ├── enhance
│   ├── enhance-status
│   ├── estimate
│   ├── github
│   ├── install
│   ├── install-agent
│   ├── multilang
│   ├── package
│   ├── pdf
│   ├── quality
│   ├── resume
│   ├── scrape
│   ├── stream
│   ├── unified
│   ├── update
│   ├── upload
│   └── workflows
│
├── MCP Tools Reference
│   ├── Overview (MCP vs CLI)
│   ├── Transport modes (stdio, HTTP)
│   └── Tool listing (26 tools)
│       ├── Core Tools (9)
│       │   ├── list_configs
│       │   ├── generate_config
│       │   ├── validate_config
│       │   ├── estimate_pages
│       │   ├── scrape_docs
│       │   ├── package_skill
│       │   ├── upload_skill
│       │   ├── enhance_skill
│       │   └── install_skill
│       ├── Extended Tools (9)
│       │   ├── scrape_github
│       │   ├── scrape_pdf
│       │   ├── unified_scrape
│       │   ├── scrape_codebase
│       │   ├── detect_patterns
│       │   ├── extract_test_examples
│       │   ├── build_how_to_guides
│       │   ├── extract_config_patterns
│       │   └── detect_conflicts
│       ├── Config Source Tools (5)
│       │   ├── add_config_source
│       │   ├── list_config_sources
│       │   ├── remove_config_source
│       │   ├── fetch_config
│       │   └── submit_config
│       ├── Config Splitting Tools (2)
│       │   ├── split_config
│       │   └── generate_router
│       ├── Vector Database Tools (4)
│       │   ├── export_to_weaviate
│       │   ├── export_to_chroma
│       │   ├── export_to_faiss
│       │   └── export_to_qdrant
│       └── Workflow Tools (5)
│           ├── list_workflows
│           ├── get_workflow
│           ├── create_workflow
│           ├── update_workflow
│           └── delete_workflow
│
└── Common Workflows
    ├── Workflow 1: Documentation → Skill
    ├── Workflow 2: GitHub → Skill
    ├── Workflow 3: PDF → Skill
    ├── Workflow 4: Local Codebase → Skill
    └── Workflow 5: Multi-Source → Skill
```

**Each command section includes:**
- Purpose (1 sentence)
- Syntax
- Arguments (table: name, required, description)
- Flags (table: short, long, default, description)
- Examples (3-5 real examples)
- Exit codes
- Common errors

### 1.2 Create Config Format Reference
**File:** `docs/reference/CONFIG_FORMAT.md` (NEW)

Complete JSON schema documentation:
- Root properties
- Source types (docs, github, pdf, local)
- Selectors
- Categories
- URL patterns
- Rate limiting
- Examples for each source type

### 1.3 Create Environment Variables Reference
**File:** `docs/reference/ENVIRONMENT_VARIABLES.md` (NEW)

Complete env var documentation:
- API keys (Anthropic, Google, OpenAI, GitHub)
- Configuration paths
- Output directories
- Rate limiting
- Debug options

### 1.4 Establish New Directory Structure

```
docs/
├── README.md                         # Documentation entry point
├── ARCHITECTURE.md                   # How docs are organized
│
├── getting-started/                  # New users start here
│   ├── 01-installation.md           # pip install, requirements
│   ├── 02-quick-start.md            # 3 commands to first skill
│   ├── 03-your-first-skill.md       # Complete walkthrough
│   └── 04-next-steps.md             # Where to go from here
│
├── user-guide/                       # Common tasks
│   ├── 01-core-concepts.md          # Skills, configs, sources
│   ├── 02-scraping.md               # Docs, GitHub, PDF, local
│   ├── 03-enhancement.md            # AI enhancement options
│   ├── 04-packaging.md              # Target platforms
│   ├── 05-workflows.md              # Using workflow presets
│   └── 06-troubleshooting.md        # Common issues
│
├── reference/                        # Technical reference
│   ├── CLI_REFERENCE.md             # Complete command reference
│   ├── MCP_REFERENCE.md             # MCP tools reference
│   ├── CONFIG_FORMAT.md             # JSON config specification
│   └── ENVIRONMENT_VARIABLES.md     # Environment variables
│
└── advanced/                         # Power user features
    ├── custom-workflows.md          # Creating YAML workflows
    ├── mcp-server.md                # MCP integration
    ├── multi-source.md              # Unified scraping deep dive
    └── api-reference.md             # Python API (for developers)
```

---

## Phase 2: User Guides

### 2.1 Installation Guide
**File:** `docs/getting-started/01-installation.md`

- System requirements (Python 3.10+)
- Basic install: `pip install skill-seekers`
- With all platforms: `pip install skill-seekers[all-llms]`
- Development setup: `pip install -e ".[all-llms,dev]"`
- Verify installation: `skill-seekers --version`

### 2.2 Quick Start Guide
**File:** `docs/getting-started/02-quick-start.md`

The "3 commands to first skill":
```bash
# 1. Install
pip install skill-seekers

# 2. Create skill (auto-detects source type)
skill-seekers create https://docs.django.com/

# 3. Package for Claude
skill-seekers package output/django --target claude
```

Plus variants:
- GitHub repo: `skill-seekers create django/django`
- Local project: `skill-seekers create ./my-project`
- PDF file: `skill-seekers create manual.pdf`

### 2.3 Your First Skill (Complete Walkthrough)
**File:** `docs/getting-started/03-your-first-skill.md`

Step-by-step with screenshots/description:
1. Choose source (we'll use React docs)
2. Run create command
3. Wait for scraping (explain what's happening)
4. Review output structure
5. Optional: enhance with AI
6. Package skill
7. Upload to Claude (or use locally)

Include actual output examples.

### 2.4 Core Concepts
**File:** `docs/user-guide/01-core-concepts.md`

- What is a skill? (SKILL.md + references/)
- What is a config? (JSON file defining source)
- Source types (docs, github, pdf, local)
- Enhancement (why and when)
- Packaging (target platforms)

### 2.5 Scraping Guide
**File:** `docs/user-guide/02-scraping.md`

Four sections:
1. **Documentation Scraping**
   - Using presets (`--config`)
   - Quick mode (`--base-url`, `--name`)
   - Dry run (`--dry-run`)
   - Rate limiting

2. **GitHub Repository Analysis**
   - Basic analysis
   - Analysis depth options
   - With GitHub token

3. **PDF Extraction**
   - Basic extraction
   - OCR for scanned PDFs
   - Large PDF handling

4. **Local Codebase Analysis**
   - Analyzing local projects
   - Language detection
   - Pattern detection

### 2.6 Enhancement Guide
**File:** `docs/user-guide/03-enhancement.md`

- What is enhancement? (improves SKILL.md quality)
- API mode vs LOCAL mode
- Using workflow presets
- Multi-workflow chaining
- When to skip enhancement

### 2.7 Packaging Guide
**File:** `docs/user-guide/04-packaging.md`

- Supported platforms (table)
- Platform-specific packaging
- Multi-platform packaging loop
- Output formats explained

### 2.8 Workflows Guide
**File:** `docs/user-guide/05-workflows.md`

- What are workflow presets?
- Built-in presets (default, minimal, security-focus, architecture-comprehensive, api-documentation)
- Using presets (`--enhance-workflow`)
- Chaining multiple presets
- Listing available workflows
- Creating custom workflows

### 2.9 Troubleshooting Guide
**File:** `docs/user-guide/06-troubleshooting.md`

Common issues with solutions:

| Issue | Cause | Solution |
|-------|-------|----------|
| ImportError | Package not installed | `pip install -e .` |
| Rate limit exceeded | Too fast | Increase `rate_limit` in config |
| No content extracted | Wrong selectors | Check selectors with browser dev tools |
| Enhancement fails | No API key / Claude Code not running | Set key or install Claude Code |
| Package fails | Missing SKILL.md | Run build first |

Plus:
- How to get help
- Debug mode (`--verbose`)
- Log files location
- Creating a minimal reproduction

---

## Phase 3: Integration

### 3.1 Main README Rewrite
**File:** `README.md` (UPDATE)

**Structure:**
```markdown
# Skill Seekers

[Badges - keep current]

## 🚀 Quick Start (3 commands)
[The 3-command quick start]

## What is Skill Seekers?
[1-paragraph explanation]

## 📚 Documentation

| I want to... | Read this |
|--------------|-----------|
| Get started quickly | [Quick Start](docs/getting-started/02-quick-start.md) |
| Learn common workflows | [User Guide](docs/user-guide/) |
| Look up a command | [CLI Reference](docs/reference/CLI_REFERENCE.md) |
| Create custom configs | [Config Format](docs/reference/CONFIG_FORMAT.md) |
| Set up MCP | [MCP Guide](docs/advanced/mcp-server.md) |

## Installation
[Basic install instructions]

## Features
[Keep current features table]

## Contributing
[Link to CONTRIBUTING.md]
```

### 3.2 Docs Entry Point
**File:** `docs/README.md` (NEW)

Navigation hub:
- Welcome message
- "Where should I start?" flowchart
- Quick links to all sections
- Version info
- How to contribute to docs

### 3.3 Architecture Document
**File:** `docs/ARCHITECTURE.md` (NEW)

Explains how documentation is organized:
- 4 categories explained
- When to use each
- File naming conventions
- How to contribute

---

## Phase 4: Cleanup

### 4.1 Files to Archive

Move to `docs/archive/legacy/`:
- `docs/guides/USAGE.md` - Uses old CLI pattern
- `docs/QUICK_REFERENCE.md` - Has phantom commands
- `QUICKSTART.md` (root) - Outdated, redirect to new quick start

### 4.2 Add Deprecation Notices

For files kept but outdated, add header:

```markdown
> ⚠️ **DEPRECATED**: This document references older CLI patterns.
> 
> For up-to-date documentation, see:
> - [Quick Start](docs/getting-started/02-quick-start.md)
> - [CLI Reference](docs/reference/CLI_REFERENCE.md)
```

Files needing deprecation notice:
- `docs/guides/USAGE.md`
- Any other docs using `python3 cli/X.py` pattern

### 4.3 Update AGENTS.md

Update `AGENTS.md` documentation section to reflect new structure.

### 4.4 Chinese Documentation Strategy

**Goal:** Maintain parity between English and Chinese documentation.

**Approach:**
- **Primary:** English docs are source of truth (in `docs/`)
- **Secondary:** Chinese translations in `docs.zh-CN/` or `docs/locales/zh-CN/`

**Files to Translate (Priority Order):**
1. `docs/getting-started/02-quick-start.md` - Most accessed
2. `docs/README.md` - Entry point
3. `docs/user-guide/06-troubleshooting.md` - Reduces support burden
4. `docs/reference/CLI_REFERENCE.md` - Command reference

**Translation Workflow:**
```
English doc updated → Mark for translation → Translate → Review → Publish
```

**Options for Implementation:**
- **Option A:** Separate `docs.zh-CN/` directory (mirrors `docs/` structure)
- **Option B:** Side-by-side files (`README.md` + `README.zh-CN.md` in same dir)
- **Option C:** Keep existing `README.zh-CN.md` pattern, translate key docs only

**Recommendation:** Option C for now - translate only:
- `README.zh-CN.md` (update existing)
- `docs/getting-started/02-quick-start.zh-CN.md` (new)
- `docs/user-guide/06-troubleshooting.zh-CN.md` (new)

**Long-term:** Consider i18n framework if user base grows.

**Chinese README.md Updates Needed:**
- Update installation instructions
- Update command examples (new CLI pattern)
- Update navigation links to new docs structure
- Remove phantom commands

**Sync Strategy:**
- English docs: Always current (source of truth)
- Chinese docs: Best effort, marked with "Last translated: DATE"
- Community contributions welcome for translations

---

## Files to Create/Modify

### New Files (16)

| File | Phase | Purpose |
|------|-------|---------|
| `docs/reference/CLI_REFERENCE.md` | 1 | Master command reference |
| `docs/reference/MCP_REFERENCE.md` | 1 | MCP tools reference |
| `docs/reference/CONFIG_FORMAT.md` | 1 | JSON config spec |
| `docs/reference/ENVIRONMENT_VARIABLES.md` | 1 | Env vars reference |
| `docs/README.md` | 3 | Docs entry point |
| `docs/ARCHITECTURE.md` | 3 | Documentation organization |
| `docs/getting-started/01-installation.md` | 2 | Install guide |
| `docs/getting-started/02-quick-start.md` | 2 | 3-command quick start |
| `docs/getting-started/03-your-first-skill.md` | 2 | Complete walkthrough |
| `docs/getting-started/04-next-steps.md` | 2 | Where to go next |
| `docs/user-guide/01-core-concepts.md` | 2 | Core concepts |
| `docs/user-guide/02-scraping.md` | 2 | Scraping guide |
| `docs/user-guide/03-enhancement.md` | 2 | Enhancement guide |
| `docs/user-guide/04-packaging.md` | 2 | Packaging guide |
| `docs/user-guide/05-workflows.md` | 2 | Workflows guide |
| `docs/user-guide/06-troubleshooting.md` | 2 | Troubleshooting |

### Modified Files (2)

| File | Phase | Changes |
|------|-------|---------|
| `README.md` | 3 | New structure, navigation table |
| `AGENTS.md` | 4 | Update documentation section |

### Archived Files (3+)

| File | Destination | Action |
|------|-------------|--------|
| `docs/guides/USAGE.md` | `docs/archive/legacy/` | Move + deprecation notice |
| `docs/QUICK_REFERENCE.md` | `docs/archive/legacy/` | Move + deprecation notice |
| `QUICKSTART.md` | `docs/archive/legacy/` | Move + create redirect |

---

## Success Metrics

After implementation, documentation should:

- [ ] Zero references to `python3 cli/X.py` pattern
- [ ] Zero phantom commands documented
- [ ] All 20 CLI commands documented with examples
- [ ] Quick start works with copy-paste
- [ ] Clear navigation from README
- [ ] Troubleshooting covers top 10 issues
- [ ] User can find any command in < 3 clicks

---

## Review Checklist

Before implementation, review this plan for:

- [ ] **Completeness**: All 20 commands covered?
- [ ] **Accuracy**: No phantom commands?
- [ ] **Organization**: Clear hierarchy?
- [ ] **Scope**: Not too much / too little?
- [ ] **Priority**: Right order of phases?

---

## Next Steps

1. **Review this plan** - Comment, modify, approve
2. **Say "good to go"** - I'll switch to implementation mode
3. **Implementation** - I'll create todos and start writing

---

*Plan Version: 1.1*  
*Created: 2026-02-16*  
*Status: Awaiting Review*
