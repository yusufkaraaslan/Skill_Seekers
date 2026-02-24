# Scraping Guide

> **Skill Seekers v3.1.0**  
> **Complete guide to all scraping options**

---

## Overview

Skill Seekers can extract knowledge from four types of sources:

| Source | Command | Best For |
|--------|---------|----------|
| **Documentation** | `create <url>` | Web docs, tutorials, API refs |
| **GitHub** | `create <repo>` | Source code, issues, releases |
| **PDF** | `create <file.pdf>` | Manuals, papers, reports |
| **Local** | `create <./path>` | Your projects, internal code |

---

## Documentation Scraping

### Basic Usage

```bash
# Auto-detect and scrape
skill-seekers create https://docs.react.dev/

# With custom name
skill-seekers create https://docs.react.dev/ --name react-docs

# With description
skill-seekers create https://docs.react.dev/ \
  --description "React JavaScript library documentation"
```

### Using Preset Configs

```bash
# List available presets
skill-seekers estimate --all

# Use preset
skill-seekers create --config react
skill-seekers create --config django
skill-seekers create --config fastapi
```

**Available presets:** See `configs/` directory in repository.

### Custom Configuration

```bash
# Create config file
cat > configs/my-docs.json << 'EOF'
{
  "name": "my-framework",
  "base_url": "https://docs.example.com/",
  "description": "My framework documentation",
  "max_pages": 200,
  "rate_limit": 0.5,
  "selectors": {
    "main_content": "article",
    "title": "h1"
  },
  "url_patterns": {
    "include": ["/docs/", "/api/"],
    "exclude": ["/blog/", "/search"]
  }
}
EOF

# Use config
skill-seekers create --config configs/my-docs.json
```

See [Config Format](../reference/CONFIG_FORMAT.md) for all options.

### Advanced Options

```bash
# Limit pages (for testing)
skill-seekers create <url> --max-pages 50

# Adjust rate limit
skill-seekers create <url> --rate-limit 1.0

# Parallel workers (faster)
skill-seekers create <url> --workers 5 --async

# Dry run (preview)
skill-seekers create <url> --dry-run

# Resume interrupted
skill-seekers create <url> --resume

# Fresh start (ignore cache)
skill-seekers create <url> --fresh
```

---

## GitHub Repository Scraping

### Basic Usage

```bash
# By repo name
skill-seekers create facebook/react

# With explicit flag
skill-seekers github --repo facebook/react

# With custom name
skill-seekers github --repo facebook/react --name react-source
```

### With GitHub Token

```bash
# Set token for higher rate limits
export GITHUB_TOKEN=ghp_...

# Use token
skill-seekers github --repo facebook/react
```

**Benefits of token:**
- 5000 requests/hour vs 60
- Access to private repos
- Higher GraphQL limits

### What Gets Extracted

| Data | Default | Flag to Disable |
|------|---------|-----------------|
| Source code | ✅ | `--scrape-only` |
| README | ✅ | - |
| Issues | ✅ | `--no-issues` |
| Releases | ✅ | `--no-releases` |
| Changelog | ✅ | `--no-changelog` |

### Control What to Fetch

```bash
# Skip issues (faster)
skill-seekers github --repo facebook/react --no-issues

# Limit issues
skill-seekers github --repo facebook/react --max-issues 50

# Scrape only (no build)
skill-seekers github --repo facebook/react --scrape-only

# Non-interactive (CI/CD)
skill-seekers github --repo facebook/react --non-interactive
```

---

## PDF Extraction

### Basic Usage

```bash
# Direct file
skill-seekers create manual.pdf --name product-manual

# With explicit command
skill-seekers pdf --pdf manual.pdf --name docs
```

### OCR for Scanned PDFs

```bash
# Enable OCR
skill-seekers pdf --pdf scanned.pdf --enable-ocr
```

**Requirements:**
```bash
pip install skill-seekers[pdf-ocr]
# Also requires: tesseract-ocr (system package)
```

### Password-Protected PDFs

```bash
# In config file
{
  "name": "secure-docs",
  "pdf_path": "protected.pdf",
  "password": "secret123"
}
```

### Page Range

```bash
# Extract specific pages (via config)
{
  "pdf_path": "manual.pdf",
  "page_range": [1, 100]
}
```

---

## Local Codebase Analysis

### Basic Usage

```bash
# Current directory
skill-seekers create .

# Specific directory
skill-seekers create ./my-project

# With explicit command
skill-seekers analyze --directory ./my-project
```

### Analysis Presets

```bash
# Quick analysis (1-2 min)
skill-seekers analyze --directory ./my-project --preset quick

# Standard analysis (5-10 min) - default
skill-seekers analyze --directory ./my-project --preset standard

# Comprehensive (20-60 min)
skill-seekers analyze --directory ./my-project --preset comprehensive
```

### What Gets Analyzed

| Feature | Quick | Standard | Comprehensive |
|---------|-------|----------|---------------|
| Code structure | ✅ | ✅ | ✅ |
| API extraction | ✅ | ✅ | ✅ |
| Comments | - | ✅ | ✅ |
| Patterns | - | ✅ | ✅ |
| Test examples | - | - | ✅ |
| How-to guides | - | - | ✅ |
| Config patterns | - | - | ✅ |

### Language Filtering

```bash
# Specific languages
skill-seekers analyze --directory ./my-project \
  --languages Python,JavaScript

# File patterns
skill-seekers analyze --directory ./my-project \
  --file-patterns "*.py,*.js"
```

### Skip Features

```bash
# Skip heavy features
skill-seekers analyze --directory ./my-project \
  --skip-dependency-graph \
  --skip-patterns \
  --skip-test-examples
```

---

## Common Scraping Patterns

### Pattern 1: Test First

```bash
# Dry run to preview
skill-seekers create <source> --dry-run

# Small test scrape
skill-seekers create <source> --max-pages 10

# Full scrape
skill-seekers create <source>
```

### Pattern 2: Iterative Development

```bash
# Scrape without enhancement (fast)
skill-seekers create <source> --enhance-level 0

# Review output
ls output/my-skill/
cat output/my-skill/SKILL.md

# Enhance later
skill-seekers enhance output/my-skill/
```

### Pattern 3: Parallel Processing

```bash
# Fast async scraping
skill-seekers create <url> --async --workers 5

# Even faster (be careful with rate limits)
skill-seekers create <url> --async --workers 10 --rate-limit 0.2
```

### Pattern 4: Resume Capability

```bash
# Start scraping
skill-seekers create <source>
# ...interrupted...

# Resume later
skill-seekers resume --list
skill-seekers resume <job-id>
```

---

## Troubleshooting Scraping

### "No content extracted"

**Problem:** Wrong CSS selectors

**Solution:**
```bash
# Find correct selectors
curl -s <url> | grep -i 'article\|main\|content'

# Update config
{
  "selectors": {
    "main_content": "div.content"  // or "article", "main", etc.
  }
}
```

### "Rate limit exceeded"

**Problem:** Too many requests

**Solution:**
```bash
# Slow down
skill-seekers create <url> --rate-limit 2.0

# Or use GitHub token for GitHub repos
export GITHUB_TOKEN=ghp_...
```

### "Too many pages"

**Problem:** Site is larger than expected

**Solution:**
```bash
# Estimate first
skill-seekers estimate configs/my-config.json

# Limit pages
skill-seekers create <url> --max-pages 100

# Adjust URL patterns
{
  "url_patterns": {
    "exclude": ["/blog/", "/archive/", "/search"]
  }
}
```

### "Memory error"

**Problem:** Site too large for memory

**Solution:**
```bash
# Use streaming mode
skill-seekers create <url> --streaming

# Or smaller chunks
skill-seekers create <url> --chunk-tokens 500
```

---

## Performance Tips

| Tip | Command | Impact |
|-----|---------|--------|
| Use presets | `--config react` | Faster setup |
| Async mode | `--async --workers 5` | 3-5x faster |
| Skip enhancement | `--enhance-level 0` | Skip 60 sec |
| Use cache | `--skip-scrape` | Instant rebuild |
| Resume | `--resume` | Continue interrupted |

---

## Next Steps

- [Enhancement Guide](03-enhancement.md) - Improve skill quality
- [Packaging Guide](04-packaging.md) - Export to platforms
- [Config Format](../reference/CONFIG_FORMAT.md) - Advanced configuration
