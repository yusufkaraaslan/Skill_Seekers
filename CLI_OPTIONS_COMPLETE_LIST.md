# Complete CLI Options & Flags - Everything Listed

**Date:** 2026-02-15
**Purpose:** Show EVERYTHING to understand the complexity

---

## 🎯 ANALYZE Command (20+ flags)

### Required
- `--directory DIR` - Path to analyze

### Preset System (NEW)
- `--preset quick|standard|comprehensive` - Bundled configuration
- `--preset-list` - Show available presets

### Deprecated Flags (Still Work)
- `--quick` - Quick analysis [DEPRECATED → use --preset quick]
- `--comprehensive` - Full analysis [DEPRECATED → use --preset comprehensive]
- `--depth surface|deep|full` - Analysis depth [DEPRECATED → use --preset]

### AI Enhancement (Multiple Ways)
- `--enhance` - Enable AI enhancement (default level 1)
- `--enhance-level 0|1|2|3` - Specific enhancement level
  - 0 = None
  - 1 = SKILL.md only (default)
  - 2 = + Architecture + Config
  - 3 = Full (all features)

### Feature Toggles (8 flags)
- `--skip-api-reference` - Disable API documentation
- `--skip-dependency-graph` - Disable dependency graph
- `--skip-patterns` - Disable pattern detection
- `--skip-test-examples` - Disable test extraction
- `--skip-how-to-guides` - Disable guide generation
- `--skip-config-patterns` - Disable config extraction
- `--skip-docs` - Disable docs extraction
- `--no-comments` - Skip comment extraction

### Filtering
- `--languages LANGS` - Limit to specific languages
- `--file-patterns PATTERNS` - Limit to file patterns

### Output
- `--output DIR` - Output directory
- `--verbose` - Verbose logging

### **Total: 20+ flags**

---

## 🎯 SCRAPE Command (26+ flags)

### Input (3 ways to specify)
- `url` (positional) - Documentation URL
- `--url URL` - Documentation URL (flag version)
- `--config FILE` - Load from config JSON

### Basic Settings
- `--name NAME` - Skill name
- `--description TEXT` - Skill description

### AI Enhancement (3 overlapping flags)
- `--enhance` - Claude API enhancement
- `--enhance-local` - Claude Code enhancement (no API key)
- `--interactive-enhancement` - Open terminal for enhancement
- `--api-key KEY` - API key for --enhance

### Scraping Control
- `--max-pages N` - Maximum pages to scrape
- `--skip-scrape` - Use cached data
- `--dry-run` - Preview only
- `--resume` - Resume interrupted scrape
- `--fresh` - Start fresh (clear checkpoint)

### Performance (4 flags)
- `--rate-limit SECONDS` - Delay between requests
- `--no-rate-limit` - Disable rate limiting
- `--workers N` - Parallel workers
- `--async` - Async mode

### Interactive
- `--interactive, -i` - Interactive configuration

### RAG Chunking (5 flags)
- `--chunk-for-rag` - Enable RAG chunking
- `--chunk-size TOKENS` - Chunk size (default: 512)
- `--chunk-overlap TOKENS` - Overlap size (default: 50)
- `--no-preserve-code-blocks` - Allow splitting code blocks
- `--no-preserve-paragraphs` - Ignore paragraph boundaries

### Output Control
- `--verbose, -v` - Verbose output
- `--quiet, -q` - Quiet output

### **Total: 26+ flags**

---

## 🎯 GITHUB Command (15+ flags)

### Required
- `--repo OWNER/REPO` - GitHub repository

### Basic Settings
- `--output DIR` - Output directory
- `--api-key KEY` - GitHub API token
- `--profile NAME` - GitHub token profile
- `--non-interactive` - CI/CD mode

### Content Control
- `--max-issues N` - Maximum issues to fetch
- `--include-changelog` - Include CHANGELOG
- `--include-releases` - Include releases
- `--no-issues` - Skip issues

### Enhancement
- `--enhance` - AI enhancement
- `--enhance-local` - Local enhancement

### Other
- `--languages LANGS` - Filter languages
- `--dry-run` - Preview mode
- `--verbose` - Verbose logging

### **Total: 15+ flags**

---

## 🎯 PACKAGE Command (12+ flags)

### Required
- `skill_directory` - Skill directory to package

### Target Platform (12 choices)
- `--target PLATFORM` - Target platform:
  - claude (default)
  - gemini
  - openai
  - markdown
  - langchain
  - llama-index
  - haystack
  - weaviate
  - chroma
  - faiss
  - qdrant

### Options
- `--upload` - Auto-upload after packaging
- `--no-open` - Don't open output folder
- `--skip-quality-check` - Skip quality checks
- `--streaming` - Use streaming for large docs
- `--chunk-size N` - Chunk size for streaming

### **Total: 12+ flags + 12 platform choices**

---

## 🎯 UPLOAD Command (10+ flags)

### Required
- `package_path` - Package file to upload

### Platform
- `--target PLATFORM` - Upload target
- `--api-key KEY` - Platform API key

### Options
- `--verify` - Verify upload
- `--retry N` - Retry attempts
- `--timeout SECONDS` - Upload timeout

### **Total: 10+ flags**

---

## 🎯 ENHANCE Command (7+ flags)

### Required
- `skill_directory` - Skill to enhance

### Mode Selection
- `--mode api|local` - Enhancement mode
- `--enhance-level 0|1|2|3` - Enhancement level

### Execution Control
- `--background` - Run in background
- `--daemon` - Detached daemon mode
- `--timeout SECONDS` - Timeout
- `--force` - Skip confirmations

### **Total: 7+ flags**

---

## 📊 GRAND TOTAL ACROSS ALL COMMANDS

| Command | Flags | Status |
|---------|-------|--------|
| **analyze** | 20+ | ⚠️ Confusing (presets + deprecated + granular) |
| **scrape** | 26+ | ⚠️ Most complex |
| **github** | 15+ | ⚠️ Multiple overlaps |
| **package** | 12+ platforms | ✅ Reasonable |
| **upload** | 10+ | ✅ Reasonable |
| **enhance** | 7+ | ⚠️ Mode confusion |
| **Other commands** | ~30+ | ✅ Various |

**Total unique flags: 90+**
**Total with variations: 120+**

---

## 🚨 OVERLAPPING CONCEPTS (Confusion Points)

### 1. **AI Enhancement - 4 Different Ways**

```bash
# In ANALYZE:
--enhance               # Turn on (uses level 1)
--enhance-level 0|1|2|3 # Specific level

# In SCRAPE:
--enhance               # Claude API
--enhance-local         # Claude Code
--interactive-enhancement  # Terminal mode

# In ENHANCE command:
--mode api|local        # Which system
--enhance-level 0|1|2|3 # How much

# Which one do I use? 🤔
```

### 2. **Preset vs Manual - Competing Systems**

```bash
# ANALYZE command has BOTH:

# Preset way:
--preset quick|standard|comprehensive

# Manual way (deprecated but still there):
--quick
--comprehensive
--depth surface|deep|full

# Granular way:
--skip-patterns
--skip-test-examples
--enhance-level 2

# Three ways to do the same thing! 🤔
```

### 3. **RAG/Chunking - Spread Across Commands**

```bash
# In SCRAPE:
--chunk-for-rag
--chunk-size 512
--chunk-overlap 50

# In PACKAGE:
--streaming
--chunk-size 4000  # Different default!

# In PACKAGE --format:
--format chroma|faiss|qdrant  # Vector DBs

# Where do RAG options belong? 🤔
```

### 4. **Output Control - Inconsistent**

```bash
# SCRAPE has:
--verbose
--quiet

# ANALYZE has:
--verbose  (no --quiet)

# GITHUB has:
--verbose

# PACKAGE has:
--no-open  (different pattern)

# Why different patterns? 🤔
```

### 5. **Dry Run - Inconsistent**

```bash
# SCRAPE has:
--dry-run

# GITHUB has:
--dry-run

# ANALYZE has:
(no --dry-run)  # Missing!

# Why not in analyze? 🤔
```

---

## 🎯 REAL USAGE SCENARIOS

### Scenario 1: New User Wants to Analyze Codebase

**What they see:**
```bash
$ skill-seekers analyze --help

# 20+ options shown
# Multiple ways to do same thing
# No clear "start here" guidance
```

**What they're thinking:**
- 😵 "Do I use --preset or --depth?"
- 😵 "What's the difference between --enhance and --enhance-level?"
- 😵 "Should I use --quick or --preset quick?"
- 😵 "What do all these --skip-* flags mean?"

**Result:** Analysis paralysis, overwhelmed

---

### Scenario 2: Experienced User Wants Fast Scrape

**What they try:**
```bash
# Try 1:
skill-seekers scrape https://docs.com --preset quick
# ERROR: unrecognized arguments: --preset

# Try 2:
skill-seekers scrape https://docs.com --quick
# ERROR: unrecognized arguments: --quick

# Try 3:
skill-seekers scrape https://docs.com --max-pages 50 --workers 5 --async
# WORKS! But hard to remember

# Try 4 (later discovers):
# Oh, scrape doesn't have presets yet? Only analyze does?
```

**Result:** Inconsistent experience across commands

---

### Scenario 3: User Wants RAG Output

**What they're confused about:**
```bash
# Step 1: Scrape with RAG chunking?
skill-seekers scrape https://docs.com --chunk-for-rag

# Step 2: Package for vector DB?
skill-seekers package output/docs/ --format chroma

# Wait, chunk-for-rag in scrape sets chunk-size to 512
# But package --streaming uses chunk-size 4000
# Which one applies? Do they override each other?
```

**Result:** Unclear data flow

---

## 🎨 THE CORE PROBLEM

### **Too Many Layers:**

```
Layer 1: Required args (--directory, url, etc.)
Layer 2: Preset system (--preset quick|standard|comprehensive)
Layer 3: Deprecated shortcuts (--quick, --comprehensive, --depth)
Layer 4: Granular controls (--skip-*, --enable-*)
Layer 5: AI controls (--enhance, --enhance-level, --enhance-local)
Layer 6: Performance (--workers, --async, --rate-limit)
Layer 7: RAG options (--chunk-for-rag, --chunk-size)
Layer 8: Output (--verbose, --quiet, --output)
```

**8 conceptual layers!** No wonder it's confusing.

---

## ✅ WHAT USERS ACTUALLY NEED

### **90% of users:**
```bash
# Just want it to work
skill-seekers analyze --directory .
skill-seekers scrape https://docs.com
skill-seekers github --repo owner/repo

# Good defaults = Happy users
```

### **9% of users:**
```bash
# Want to tweak ONE thing
skill-seekers analyze --directory . --enhance-level 3
skill-seekers scrape https://docs.com --max-pages 100

# Simple overrides = Happy power users
```

### **1% of users:**
```bash
# Want full control
skill-seekers analyze --directory . \
  --depth full \
  --skip-patterns \
  --enhance-level 2 \
  --languages Python,JavaScript

# Granular flags = Happy experts
```

---

## 🎯 THE QUESTION

**Do we need:**
- ❌ Preset system? (adds layer)
- ❌ Deprecated flags? (adds confusion)
- ❌ Multiple AI flags? (inconsistent)
- ❌ Granular --skip-* for everything? (too many flags)

**Or do we just need:**
- ✅ Good defaults (works out of box)
- ✅ 3-5 key flags to adjust (depth, enhance-level, max-pages)
- ✅ Clear help text (show common usage)
- ✅ Consistent patterns (same flags across commands)

**That's your question, right?** 🎯

