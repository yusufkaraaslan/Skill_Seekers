# Multi-Platform Upload Guide

Skill Seekers supports uploading to **4 LLM platforms**: Claude AI, Google Gemini, OpenAI ChatGPT, and Generic Markdown export.

## Quick Platform Selection

| Platform | Best For | Upload Method | API Key Required |
|----------|----------|---------------|------------------|
| **Claude AI** | General use, MCP integration | API or Manual | ANTHROPIC_API_KEY |
| **Google Gemini** | Long context (1M tokens) | API | GOOGLE_API_KEY |
| **OpenAI ChatGPT** | Vector search, Assistants API | API | OPENAI_API_KEY |
| **Generic Markdown** | Universal compatibility, offline | Manual distribution | None |

---

## Claude AI (Default)

### Prerequisites

```bash
# Option 1: Set API key for automatic upload
export ANTHROPIC_API_KEY=sk-ant-...

# Option 2: No API key (manual upload)
# No setup needed - just package and upload manually
```

### Package for Claude

```bash
# Claude uses ZIP format (default)
skill-seekers package output/react/
```

**Output:** `output/react.zip`

### Upload to Claude

**Option 1: Automatic (with API key)**
```bash
skill-seekers upload output/react.zip
```

**Option 2: Manual (no API key)**
1. Go to https://claude.ai/skills
2. Click "Upload Skill" or "Add Skill"
3. Select `output/react.zip`
4. Done!

**Option 3: MCP (easiest)**
```
In Claude Code, just say:
"Package and upload the React skill"
```

**What's inside the ZIP:**
```
react.zip
├── SKILL.md            ← Main skill file (YAML frontmatter + markdown)
└── references/         ← Reference documentation
    ├── index.md
    ├── api.md
    └── ...
```

---

## Google Gemini

### Prerequisites

```bash
# Install Gemini support
pip install skill-seekers[gemini]

# Set API key
export GOOGLE_API_KEY=AIzaSy...
```

### Package for Gemini

```bash
# Gemini uses tar.gz format
skill-seekers package output/react/ --target gemini
```

**Output:** `output/react-gemini.tar.gz`

### Upload to Gemini

```bash
skill-seekers upload output/react-gemini.tar.gz --target gemini
```

**What happens:**
- Uploads to Google Files API
- Creates grounding resource
- Available in Google AI Studio

**Access your skill:**
- Go to https://aistudio.google.com/
- Your skill is available as grounding data

**What's inside the tar.gz:**
```
react-gemini.tar.gz
├── system_instructions.md  ← Main skill file (plain markdown, no frontmatter)
├── references/             ← Reference documentation
│   ├── index.md
│   ├── api.md
│   └── ...
└── gemini_metadata.json    ← Gemini-specific metadata
```

**Format differences:**
- No YAML frontmatter (Gemini uses plain markdown)
- `SKILL.md` → `system_instructions.md`
- Includes `gemini_metadata.json` for platform integration

---

## OpenAI ChatGPT

### Prerequisites

```bash
# Install OpenAI support
pip install skill-seekers[openai]

# Set API key
export OPENAI_API_KEY=sk-proj-...
```

### Package for OpenAI

```bash
# OpenAI uses ZIP format with vector store
skill-seekers package output/react/ --target openai
```

**Output:** `output/react-openai.zip`

### Upload to OpenAI

```bash
skill-seekers upload output/react-openai.zip --target openai
```

**What happens:**
- Creates OpenAI Assistant via Assistants API
- Creates Vector Store for semantic search
- Uploads reference files to vector store
- Enables `file_search` tool automatically

**Access your assistant:**
- Go to https://platform.openai.com/assistants/
- Your assistant is listed with name based on skill
- Includes file search enabled

**What's inside the ZIP:**
```
react-openai.zip
├── assistant_instructions.txt  ← Main skill file (plain text, no YAML)
├── vector_store_files/         ← Files for vector store
│   ├── index.md
│   ├── api.md
│   └── ...
└── openai_metadata.json        ← OpenAI-specific metadata
```

**Format differences:**
- No YAML frontmatter (OpenAI uses plain text)
- `SKILL.md` → `assistant_instructions.txt`
- Reference files packaged separately for Vector Store
- Includes `openai_metadata.json` for assistant configuration

**Unique features:**
- ✅ Semantic search across documentation
- ✅ Vector Store for efficient retrieval
- ✅ File search tool enabled by default

---

## Generic Markdown (Universal Export)

### Package for Markdown

```bash
# Generic markdown for manual distribution
skill-seekers package output/react/ --target markdown
```

**Output:** `output/react-markdown.zip`

### Distribution

**No upload API available** - Use for manual distribution:
- Share ZIP file directly
- Upload to documentation hosting
- Include in git repositories
- Use with any LLM that accepts markdown

**What's inside the ZIP:**
```
react-markdown.zip
├── README.md               ← Getting started guide
├── DOCUMENTATION.md        ← Combined documentation
├── references/             ← Separate reference files
│   ├── index.md
│   ├── api.md
│   └── ...
└── manifest.json           ← Skill metadata
```

**Format differences:**
- No platform-specific formatting
- Pure markdown - works anywhere
- Combined `DOCUMENTATION.md` for easy reading
- Separate `references/` for modular access

**Use cases:**
- Works with **any LLM** (local models, other platforms)
- Documentation website hosting
- Offline documentation
- Share via git/email
- Include in project repositories

---

## Complete Workflow

### Single Platform (Claude)

```bash
# 1. Scrape documentation
skill-seekers scrape --config configs/react.json

# 2. Enhance (recommended)
skill-seekers enhance output/react/

# 3. Package for Claude (default)
skill-seekers package output/react/

# 4. Upload to Claude
skill-seekers upload output/react.zip
```

### Multi-Platform (Same Skill)

```bash
# 1. Scrape once (universal)
skill-seekers scrape --config configs/react.json

# 2. Enhance once (or per-platform if desired)
skill-seekers enhance output/react/

# 3. Package for ALL platforms
skill-seekers package output/react/ --target claude
skill-seekers package output/react/ --target gemini
skill-seekers package output/react/ --target openai
skill-seekers package output/react/ --target markdown

# 4. Upload to platforms
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIzaSy...
export OPENAI_API_KEY=sk-proj-...

skill-seekers upload output/react.zip --target claude
skill-seekers upload output/react-gemini.tar.gz --target gemini
skill-seekers upload output/react-openai.zip --target openai

# Result:
# - react.zip (Claude)
# - react-gemini.tar.gz (Gemini)
# - react-openai.zip (OpenAI)
# - react-markdown.zip (Universal)
```

---

## File Size Limits

### Platform Limits

| Platform | File Size Limit | Typical Skill Size |
|----------|----------------|-------------------|
| Claude AI | ~25 MB per skill | 10-500 KB |
| Google Gemini | ~100 MB per file | 10-500 KB |
| OpenAI ChatGPT | ~512 MB vector store | 10-500 KB |
| Generic Markdown | No limit | 10-500 KB |

**Check package size:**
```bash
ls -lh output/react.zip
```

**Most skills are small:**
- Small skill: 5-20 KB
- Medium skill: 20-100 KB
- Large skill: 100-500 KB

---

## Troubleshooting

### "SKILL.md not found"

Make sure you scraped and built first:
```bash
skill-seekers scrape --config configs/react.json
skill-seekers package output/react/
```

### "Invalid target platform"

Use valid platform names:
```bash
# Valid
--target claude
--target gemini
--target openai
--target markdown

# Invalid
--target anthropic  ❌
--target google     ❌
```

### "API key not set"

**Claude:**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**Gemini:**
```bash
export GOOGLE_API_KEY=AIzaSy...
pip install skill-seekers[gemini]
```

**OpenAI:**
```bash
export OPENAI_API_KEY=sk-proj-...
pip install skill-seekers[openai]
```

### Upload fails

If API upload fails, you can always use manual upload:
- **Claude:** https://claude.ai/skills
- **Gemini:** https://aistudio.google.com/
- **OpenAI:** https://platform.openai.com/assistants/

### Wrong file format

Each platform requires specific format:
- Claude/OpenAI/Markdown: `.zip` file
- Gemini: `.tar.gz` file

Make sure to use `--target` parameter when packaging.

---

## Platform Comparison

### Format Comparison

| Feature | Claude | Gemini | OpenAI | Markdown |
|---------|--------|--------|--------|----------|
| **File Format** | ZIP | tar.gz | ZIP | ZIP |
| **Main File** | SKILL.md | system_instructions.md | assistant_instructions.txt | README.md + DOCUMENTATION.md |
| **Frontmatter** | ✅ YAML | ❌ Plain MD | ❌ Plain Text | ❌ Plain MD |
| **References** | references/ | references/ | vector_store_files/ | references/ |
| **Metadata** | In frontmatter | gemini_metadata.json | openai_metadata.json | manifest.json |

### Upload Comparison

| Feature | Claude | Gemini | OpenAI | Markdown |
|---------|--------|--------|--------|----------|
| **API Upload** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ Manual only |
| **Manual Upload** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes (distribute) |
| **MCP Support** | ✅ Full | ✅ Full | ✅ Full | ✅ Package only |
| **Web Interface** | claude.ai/skills | aistudio.google.com | platform.openai.com/assistants | N/A |

### Enhancement Comparison

| Feature | Claude | Gemini | OpenAI | Markdown |
|---------|--------|--------|--------|----------|
| **AI Enhancement** | ✅ Sonnet 4 | ✅ Gemini 2.0 | ✅ GPT-4o | ❌ No |
| **Local Mode** | ✅ Yes (free) | ❌ No | ❌ No | ❌ N/A |
| **API Mode** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ N/A |
| **Format Changes** | Keeps YAML | → Plain MD | → Plain Text | N/A |

---

## API Key Setup

### Get API Keys

**Claude (Anthropic):**
1. Go to https://console.anthropic.com/
2. Create API key
3. Copy key (starts with `sk-ant-`)
4. `export ANTHROPIC_API_KEY=sk-ant-...`

**Gemini (Google):**
1. Go to https://aistudio.google.com/
2. Get API key
3. Copy key (starts with `AIza`)
4. `export GOOGLE_API_KEY=AIzaSy...`

**OpenAI:**
1. Go to https://platform.openai.com/
2. Create API key
3. Copy key (starts with `sk-proj-`)
4. `export OPENAI_API_KEY=sk-proj-...`

### Persist API Keys

Add to shell profile to keep them set:
```bash
# macOS/Linux (bash)
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc
echo 'export GOOGLE_API_KEY=AIzaSy...' >> ~/.bashrc
echo 'export OPENAI_API_KEY=sk-proj-...' >> ~/.bashrc

# macOS (zsh)
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.zshrc
echo 'export GOOGLE_API_KEY=AIzaSy...' >> ~/.zshrc
echo 'export OPENAI_API_KEY=sk-proj-...' >> ~/.zshrc
```

Then restart your terminal or run:
```bash
source ~/.bashrc  # or ~/.zshrc
```

---

## See Also

- [FEATURE_MATRIX.md](FEATURE_MATRIX.md) - Complete feature comparison
- [MULTI_LLM_SUPPORT.md](MULTI_LLM_SUPPORT.md) - Multi-platform guide
- [ENHANCEMENT.md](ENHANCEMENT.md) - AI enhancement guide
- [README.md](../README.md) - Main documentation
