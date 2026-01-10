# Skill Seekers Feature Matrix

Complete feature support across all platforms and skill modes.

## Platform Support

| Platform | Package Format | Upload | Enhancement | API Key Required |
|----------|---------------|--------|-------------|------------------|
| **Claude AI** | ZIP | ✅ Anthropic API | ✅ Sonnet 4 | ANTHROPIC_API_KEY |
| **Google Gemini** | tar.gz | ✅ Files API | ✅ Gemini 2.0 | GOOGLE_API_KEY |
| **OpenAI ChatGPT** | ZIP | ✅ Assistants API | ✅ GPT-4o | OPENAI_API_KEY |
| **Generic Markdown** | ZIP | ❌ Manual | ❌ None | None |

## Skill Mode Support

| Mode | Description | Platforms | Example Configs |
|------|-------------|-----------|-----------------|
| **Documentation** | Scrape HTML docs | All 4 | react.json, django.json (14 total) |
| **GitHub** | Analyze repositories | All 4 | react_github.json, godot_github.json |
| **PDF** | Extract from PDFs | All 4 | example_pdf.json |
| **Unified** | Multi-source (docs+GitHub+PDF) | All 4 | react_unified.json (5 total) |
| **Local Repo** | Unlimited local analysis | All 4 | deck_deck_go_local.json |

## CLI Command Support

| Command | Platforms | Skill Modes | Multi-Platform Flag |
|---------|-----------|-------------|---------------------|
| `scrape` | All | Docs only | No (output is universal) |
| `github` | All | GitHub only | No (output is universal) |
| `pdf` | All | PDF only | No (output is universal) |
| `unified` | All | Unified only | No (output is universal) |
| `enhance` | Claude, Gemini, OpenAI | All | ✅ `--target` |
| `package` | All | All | ✅ `--target` |
| `upload` | Claude, Gemini, OpenAI | All | ✅ `--target` |
| `estimate` | All | Docs only | No (estimation is universal) |
| `install` | All | All | ✅ `--target` |
| `install-agent` | All | All | No (agent-specific paths) |

## MCP Tool Support

| Tool | Platforms | Skill Modes | Multi-Platform Param |
|------|-----------|-------------|----------------------|
| **Config Tools** |
| `generate_config` | All | All | No (creates generic JSON) |
| `list_configs` | All | All | No |
| `validate_config` | All | All | No |
| `fetch_config` | All | All | No |
| **Scraping Tools** |
| `estimate_pages` | All | Docs only | No |
| `scrape_docs` | All | Docs + Unified | No (output is universal) |
| `scrape_github` | All | GitHub only | No (output is universal) |
| `scrape_pdf` | All | PDF only | No (output is universal) |
| **Packaging Tools** |
| `package_skill` | All | All | ✅ `target` parameter |
| `upload_skill` | Claude, Gemini, OpenAI | All | ✅ `target` parameter |
| `enhance_skill` | Claude, Gemini, OpenAI | All | ✅ `target` parameter |
| `install_skill` | All | All | ✅ `target` parameter |
| **Splitting Tools** |
| `split_config` | All | Docs + Unified | No |
| `generate_router` | All | Docs only | No |

## Feature Comparison by Platform

### Claude AI (Default)
- **Format:** YAML frontmatter + markdown
- **Package:** ZIP with SKILL.md, references/, scripts/, assets/
- **Upload:** POST to https://api.anthropic.com/v1/skills
- **Enhancement:** Claude Sonnet 4 (local or API)
- **Unique Features:** MCP integration, Skills API
- **Limitations:** No vector store, no file search

### Google Gemini
- **Format:** Plain markdown (no frontmatter)
- **Package:** tar.gz with system_instructions.md, references/, metadata
- **Upload:** Google Files API
- **Enhancement:** Gemini 2.0 Flash
- **Unique Features:** Grounding support, long context (1M tokens)
- **Limitations:** tar.gz format only

### OpenAI ChatGPT
- **Format:** Assistant instructions (plain text)
- **Package:** ZIP with assistant_instructions.txt, vector_store_files/, metadata
- **Upload:** Assistants API + Vector Store creation
- **Enhancement:** GPT-4o
- **Unique Features:** Vector store, file_search tool, semantic search
- **Limitations:** Requires Assistants API structure

### Generic Markdown
- **Format:** Pure markdown (universal)
- **Package:** ZIP with README.md, DOCUMENTATION.md, references/
- **Upload:** None (manual distribution)
- **Enhancement:** None
- **Unique Features:** Works with any LLM, no API dependencies
- **Limitations:** No upload, no enhancement

## Workflow Coverage

### Single-Source Workflow
```
Config → Scrape → Build → [Enhance] → Package --target X → [Upload --target X]
```
**Platforms:** All 4
**Modes:** Docs, GitHub, PDF

### Unified Multi-Source Workflow
```
Config → Scrape All → Detect Conflicts → Merge → Build → [Enhance] → Package --target X → [Upload --target X]
```
**Platforms:** All 4
**Modes:** Unified only

### Complete Installation Workflow
```
install --target X → Fetch → Scrape → Enhance → Package → Upload
```
**Platforms:** All 4
**Modes:** All (via config type detection)

## API Key Requirements

| Platform | Environment Variable | Key Format | Required For |
|----------|---------------------|------------|--------------|
| Claude | `ANTHROPIC_API_KEY` | `sk-ant-*` | Upload, API Enhancement |
| Gemini | `GOOGLE_API_KEY` | `AIza*` | Upload, API Enhancement |
| OpenAI | `OPENAI_API_KEY` | `sk-*` | Upload, API Enhancement |
| Markdown | None | N/A | Nothing |

**Note:** Local enhancement (Claude Code Max) requires no API key for any platform.

## Installation Options

```bash
# Core package (Claude only)
pip install skill-seekers

# With Gemini support
pip install skill-seekers[gemini]

# With OpenAI support
pip install skill-seekers[openai]

# With all platforms
pip install skill-seekers[all-llms]
```

## Examples

### Package for Multiple Platforms (Same Skill)
```bash
# Scrape once (platform-agnostic)
skill-seekers scrape --config configs/react.json

# Package for all platforms
skill-seekers package output/react/ --target claude
skill-seekers package output/react/ --target gemini
skill-seekers package output/react/ --target openai
skill-seekers package output/react/ --target markdown

# Result:
# - react.zip (Claude)
# - react-gemini.tar.gz (Gemini)
# - react-openai.zip (OpenAI)
# - react-markdown.zip (Universal)
```

### Upload to Multiple Platforms
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIzaSy...
export OPENAI_API_KEY=sk-proj-...

skill-seekers upload react.zip --target claude
skill-seekers upload react-gemini.tar.gz --target gemini
skill-seekers upload react-openai.zip --target openai
```

### Use MCP Tools for Any Platform
```python
# In Claude Code or any MCP client

# Package for Gemini
package_skill(skill_dir="output/react", target="gemini")

# Upload to OpenAI
upload_skill(skill_zip="output/react-openai.zip", target="openai")

# Enhance with Gemini
enhance_skill(skill_dir="output/react", target="gemini", mode="api")
```

### Complete Workflow with Different Platforms
```bash
# Install React skill for Claude (default)
skill-seekers install --config react

# Install Django skill for Gemini
skill-seekers install --config django --target gemini

# Install FastAPI skill for OpenAI
skill-seekers install --config fastapi --target openai

# Install Vue skill as generic markdown
skill-seekers install --config vue --target markdown
```

### Split Unified Config by Source
```bash
# Split multi-source config into separate configs
skill-seekers split --config configs/react_unified.json --strategy source

# Creates:
# - react-documentation.json (docs only)
# - react-github.json (GitHub only)

# Then scrape each separately
skill-seekers unified --config react-documentation.json
skill-seekers unified --config react-github.json

# Or scrape in parallel for speed
skill-seekers unified --config react-documentation.json &
skill-seekers unified --config react-github.json &
wait
```

## Verification Checklist

Before release, verify all combinations:

### CLI Commands × Platforms
- [ ] scrape → package claude → upload claude
- [ ] scrape → package gemini → upload gemini
- [ ] scrape → package openai → upload openai
- [ ] scrape → package markdown
- [ ] github → package (all platforms)
- [ ] pdf → package (all platforms)
- [ ] unified → package (all platforms)
- [ ] enhance claude
- [ ] enhance gemini
- [ ] enhance openai

### MCP Tools × Platforms
- [ ] package_skill target=claude
- [ ] package_skill target=gemini
- [ ] package_skill target=openai
- [ ] package_skill target=markdown
- [ ] upload_skill target=claude
- [ ] upload_skill target=gemini
- [ ] upload_skill target=openai
- [ ] enhance_skill target=claude
- [ ] enhance_skill target=gemini
- [ ] enhance_skill target=openai
- [ ] install_skill target=claude
- [ ] install_skill target=gemini
- [ ] install_skill target=openai

### Skill Modes × Platforms
- [ ] Docs → Claude
- [ ] Docs → Gemini
- [ ] Docs → OpenAI
- [ ] Docs → Markdown
- [ ] GitHub → All platforms
- [ ] PDF → All platforms
- [ ] Unified → All platforms
- [ ] Local Repo → All platforms

## Platform-Specific Notes

### Claude AI
- **Best for:** General-purpose skills, MCP integration
- **When to use:** Default choice, best MCP support
- **File size limit:** 25 MB per skill package

### Google Gemini
- **Best for:** Large context skills, grounding support
- **When to use:** Need long context (1M tokens), grounding features
- **File size limit:** 100 MB per upload

### OpenAI ChatGPT
- **Best for:** Vector search, semantic retrieval
- **When to use:** Need semantic search across documentation
- **File size limit:** 512 MB per vector store

### Generic Markdown
- **Best for:** Universal compatibility, no API dependencies
- **When to use:** Using non-Claude/Gemini/OpenAI LLMs, offline use
- **Distribution:** Manual - share ZIP file directly

## Frequently Asked Questions

**Q: Can I package once and upload to multiple platforms?**
A: No. Each platform requires a platform-specific package format. You must:
1. Scrape once (universal)
2. Package separately for each platform (`--target` flag)
3. Upload each platform-specific package

**Q: Do I need to scrape separately for each platform?**
A: No! Scraping is platform-agnostic. Scrape once, then package for multiple platforms.

**Q: Which platform should I choose?**
A:
- **Claude:** Best default choice, excellent MCP integration
- **Gemini:** Choose if you need long context (1M tokens) or grounding
- **OpenAI:** Choose if you need vector search and semantic retrieval
- **Markdown:** Choose for universal compatibility or offline use

**Q: Can I enhance a skill for different platforms?**
A: Yes! Enhancement adds platform-specific formatting:
- Claude: YAML frontmatter + markdown
- Gemini: Plain markdown with system instructions
- OpenAI: Plain text assistant instructions

**Q: Do all skill modes work with all platforms?**
A: Yes! All 5 skill modes (Docs, GitHub, PDF, Unified, Local Repo) work with all 4 platforms.

## See Also

- **[README.md](../README.md)** - Complete user documentation
- **[UNIFIED_SCRAPING.md](UNIFIED_SCRAPING.md)** - Multi-source scraping guide
- **[ENHANCEMENT.md](ENHANCEMENT.md)** - AI enhancement guide
- **[UPLOAD_GUIDE.md](UPLOAD_GUIDE.md)** - Upload instructions
- **[MCP_SETUP.md](MCP_SETUP.md)** - MCP server setup
