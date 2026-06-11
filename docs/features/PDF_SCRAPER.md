# PDF Scraper CLI Tool (Tasks B1.6 + B1.8)

**Status:** ✅ Completed
**Date:** October 21, 2025
**Tasks:** B1.6 - Create pdf_scraper.py CLI tool, B1.8 - PDF config format

---

## Overview

The PDF scraper (`pdf_scraper.py`) is a complete CLI tool that converts PDF documentation into Claude AI skills. It integrates all PDF extraction features (B1.1-B1.5) with the Skill Seeker workflow to produce packaged, uploadable skills.

## Features

### ✅ Complete Workflow

1. **Extract** - Uses `pdf_extractor_poc.py` for extraction
2. **Categorize** - Organizes content by chapters or keywords
3. **Build** - Creates skill structure (SKILL.md, references/)
4. **Package** - Ready for `package_skill.py`

### ✅ Three Usage Modes

1. **Config File** - Use JSON configuration (recommended)
2. **Direct PDF** - Quick conversion from PDF file
3. **From JSON** - Build skill from pre-extracted data

### ✅ Automatic Categorization

- Chapter-based (from PDF structure)
- Keyword-based (configurable)
- Fallback to single category

### ✅ Quality Filtering

- Uses quality scores from B1.4
- Extracts top code examples
- Filters by minimum quality threshold

---

## Usage

### Mode 1: Config File (Recommended)

```bash
# Create config file
cat > configs/my_manual.json <<EOF
{
  "name": "mymanual",
  "description": "My Manual documentation",
  "pdf_path": "docs/manual.pdf",
  "extract_options": {
    "chunk_size": 10,
    "min_quality": 6.0,
    "extract_images": true,
    "min_image_size": 150
  },
  "categories": {
    "getting_started": ["introduction", "setup"],
    "api": ["api", "reference", "function"],
    "tutorial": ["tutorial", "example", "guide"]
  }
}
EOF

# Run scraper
skill-seekers create --config configs/my_manual.json
```

**Output:**
```
🔍 Extracting from PDF: docs/manual.pdf
📄 Extracting from: docs/manual.pdf
   Pages: 150
   ...
✅ Extraction complete

💾 Saved extracted data to: output/mymanual_extracted.json

🏗️  Building skill: mymanual
📋 Categorizing content...
✅ Created 3 categories
   - Getting Started: 25 pages
   - Api: 80 pages
   - Tutorial: 45 pages

📝 Generating reference files...
   Generated: output/mymanual/references/getting_started.md
   Generated: output/mymanual/references/api.md
   Generated: output/mymanual/references/tutorial.md
   Generated: output/mymanual/references/index.md
   Generated: output/mymanual/SKILL.md

✅ Skill built successfully: output/mymanual/

📦 Next step: Package with: skill-seekers package output/mymanual/
```

### Mode 2: Direct PDF

```bash
# Quick conversion without config file
skill-seekers create --pdf manual.pdf --name mymanual --description "My Manual Docs"
```

**Uses default settings:**
- Chunk size: 10
- Min quality: 5.0
- Extract images: true
- Min image size: 100px
- No custom categories (chapter-based)

### Mode 3: From Extracted JSON

```bash
# Step 1: Extract only (saves JSON)
python -m skill_seekers.cli.pdf_extractor_poc manual.pdf -o manual_extracted.json --extract-images

# Step 2: Build skill from JSON (fast, can iterate)
skill-seekers create --from-json manual_extracted.json
```

**Benefits:**
- Separate extraction and building
- Iterate on skill structure without re-extracting
- Faster development cycle

---

## Config File Format (Task B1.8)

### Complete Example

```json
{
  "name": "godot_manual",
  "description": "Godot Engine documentation from PDF manual",
  "pdf_path": "docs/godot_manual.pdf",
  "extract_options": {
    "chunk_size": 15,
    "min_quality": 6.0,
    "extract_images": true,
    "min_image_size": 200
  },
  "categories": {
    "getting_started": [
      "introduction",
      "getting started",
      "installation",
      "first steps"
    ],
    "scripting": [
      "gdscript",
      "scripting",
      "code",
      "programming"
    ],
    "3d": [
      "3d",
      "spatial",
      "mesh",
      "shader"
    ],
    "2d": [
      "2d",
      "sprite",
      "tilemap",
      "animation"
    ],
    "api": [
      "api",
      "class reference",
      "method",
      "property"
    ]
  }
}
```

### Field Reference

#### Required Fields

- **`name`** (string): Skill identifier
  - Used for directory names
  - Should be lowercase, no spaces
  - Example: `"python_guide"`

- **`pdf_path`** (string): Path to PDF file
  - Absolute or relative to working directory
  - Example: `"docs/manual.pdf"`

#### Optional Fields

- **`description`** (string): Skill description
  - Shows in SKILL.md
  - Explains when to use the skill
  - Default: `"Documentation skill for {name}"`

- **`extract_options`** (object): Extraction settings
  - `chunk_size` (number): Pages per chunk (default: 10)
  - `min_quality` (number): Minimum code quality 0-10 (default: 5.0)
  - `extract_images` (boolean): Extract images to files (default: true)
  - `min_image_size` (number): Minimum image dimension in pixels (default: 100)

- **`categories`** (object): Keyword-based categorization
  - Keys: Category names (will be sanitized for filenames)
  - Values: Arrays of keywords to match
  - If omitted: Uses chapter-based categorization from PDF

---

## Output Structure

### Generated Files

```
output/
├── mymanual_extracted.json          # Raw extraction data (B1.5 format)
└── mymanual/                        # Skill directory
    ├── SKILL.md                     # Main skill file
    ├── references/                  # Reference documentation
    │   ├── index.md                 # Category index
    │   ├── getting_started.md       # Category 1
    │   ├── api.md                   # Category 2
    │   └── tutorial.md              # Category 3
    ├── scripts/                     # Empty (for user scripts)
    └── assets/                      # Assets directory
        └── images/                  # Extracted images (if enabled)
            ├── mymanual_page5_img1.png
            └── mymanual_page12_img2.jpeg
```

### SKILL.md Format

```markdown
# Mymanual Documentation Skill

My Manual documentation

## When to use this skill

Use this skill when the user asks about mymanual documentation,
including API references, tutorials, examples, and best practices.

## What's included

This skill contains:

- **Getting Started**: 25 pages
- **Api**: 80 pages
- **Tutorial**: 45 pages

## Quick Reference

### Top Code Examples

**Example 1** (Quality: 8.5/10):

```python
def initialize_system():
    config = load_config()
    setup_logging(config)
    return System(config)
```

**Example 2** (Quality: 8.2/10):

```javascript
const app = createApp({
  data() {
    return { count: 0 }
  }
})
```

## Navigation

See `references/index.md` for complete documentation structure.

## Languages Covered

- python: 45 examples
- javascript: 32 examples
- shell: 8 examples
```

### Reference File Format

Each category gets its own reference file:

```markdown
# Getting Started

## Installation

This guide will walk you through installing the software...

### Code Examples

```bash
curl -O https://example.com/install.sh
bash install.sh
```

---

## Configuration

After installation, configure your environment...

### Code Examples

```yaml
server:
  port: 8080
  host: localhost
```

---
```

---

## Categorization Logic

### Chapter-Based (Automatic)

If PDF has detectable chapters (from B1.3):

1. Extract chapter titles and page ranges
2. Create one category per chapter
3. Assign pages to chapters by page number

**Advantages:**
- Automatic, no config needed
- Respects document structure
- Accurate page assignment

**Example chapters:**
- "Chapter 1: Introduction" → `chapter_1_introduction.md`
- "Part 2: Advanced Topics" → `part_2_advanced_topics.md`

### Keyword-Based (Configurable)

If `categories` config is provided:

1. Score each page against keyword lists
2. Assign to highest-scoring category
3. Fall back to "other" if no match

**Advantages:**
- Flexible, customizable
- Works with PDFs without clear chapters
- Can combine related sections

**Scoring:**
- Keyword in page text: +1 point
- Keyword in page heading: +2 points
- Assigned to category with highest score

---

## Integration with Skill Seeker

### Complete Workflow

```bash
# 1. Create PDF config
cat > configs/api_manual.json <<EOF
{
  "name": "api_manual",
  "pdf_path": "docs/api.pdf",
  "extract_options": {
    "min_quality": 7.0,
    "extract_images": true
  }
}
EOF

# 2. Run PDF scraper
skill-seekers create --config configs/api_manual.json

# 3. Package skill
skill-seekers package output/api_manual/

# 4. Upload to Claude (if ANTHROPIC_API_KEY set)
skill-seekers package output/api_manual/ --upload

# Result: api_manual.zip ready for Claude!
```

### Enhancement (Optional)

```bash
# After building, enhance with AI
skill-seekers enhance output/api_manual/

# Or with API
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers enhance output/api_manual/
```

---

## Performance

### Benchmark

| PDF Size | Pages | Extraction | Building | Total |
|----------|-------|------------|----------|-------|
| Small | 50 | 30s | 5s | 35s |
| Medium | 200 | 2m | 15s | 2m 15s |
| Large | 500 | 5m | 45s | 5m 45s |

**Extraction**: PDF → JSON (cpu-intensive)
**Building**: JSON → Skill (fast, i/o-bound)

### Optimization Tips

1. **Use `--from-json` for iteration**
   - Extract once, build many times
   - Test categorization without re-extraction

2. **Adjust chunk size**
   - Larger chunks: Faster extraction
   - Smaller chunks: Better chapter detection

3. **Filter aggressively**
   - Higher `min_quality`: Fewer low-quality code blocks
   - Higher `min_image_size`: Fewer small images

---

## Examples

### Example 1: Programming Language Manual

```json
{
  "name": "python_reference",
  "description": "Python 3.12 Language Reference",
  "pdf_path": "python-3.12-reference.pdf",
  "extract_options": {
    "chunk_size": 20,
    "min_quality": 7.0,
    "extract_images": false
  },
  "categories": {
    "basics": ["introduction", "basic", "syntax", "types"],
    "functions": ["function", "lambda", "decorator"],
    "classes": ["class", "object", "inheritance"],
    "modules": ["module", "package", "import"],
    "stdlib": ["library", "standard library", "built-in"]
  }
}
```

### Example 2: API Documentation

```json
{
  "name": "rest_api_docs",
  "description": "REST API Documentation",
  "pdf_path": "api_docs.pdf",
  "extract_options": {
    "chunk_size": 10,
    "min_quality": 6.0,
    "extract_images": true,
    "min_image_size": 200
  },
  "categories": {
    "authentication": ["auth", "login", "token", "oauth"],
    "users": ["user", "account", "profile"],
    "products": ["product", "catalog", "inventory"],
    "orders": ["order", "purchase", "checkout"],
    "webhooks": ["webhook", "event", "callback"]
  }
}
```

### Example 3: Framework Documentation

```json
{
  "name": "django_docs",
  "description": "Django Web Framework Documentation",
  "pdf_path": "django-4.2-docs.pdf",
  "extract_options": {
    "chunk_size": 15,
    "min_quality": 6.5,
    "extract_images": true
  }
}
```
*Note: No categories - uses chapter-based categorization*

---

## Troubleshooting

### No Categories Created

**Problem:** Only "content" or "other" category

**Possible causes:**
1. No chapters detected in PDF
2. Keywords don't match content
3. Config has empty categories

**Solution:**
```bash
# Check extracted chapters
cat output/mymanual_extracted.json | jq '.chapters'

# If empty, add keyword categories to config
# Or let it create single "content" category (OK for small PDFs)
```

### Low-Quality Code Blocks

**Problem:** Too many poor code examples

**Solution:**
```json
{
  "extract_options": {
    "min_quality": 7.0  // Increase threshold
  }
}
```

### Images Not Extracted

**Problem:** No images in `assets/images/`

**Solution:**
```json
{
  "extract_options": {
    "extract_images": true,  // Enable extraction
    "min_image_size": 50     // Lower threshold
  }
}
```

---

## Comparison with Web Scraper

| Feature | Web Scraper | PDF Scraper |
|---------|-------------|-------------|
| Input | HTML websites | PDF files |
| Crawling | Multi-page BFS | Single-file extraction |
| Structure detection | CSS selectors | Font/heading analysis |
| Categorization | URL patterns | Chapters/keywords |
| Images | Referenced | Embedded (extracted) |
| Code detection | `<pre><code>` | Font/indent/pattern |
| Language detection | CSS classes | Pattern matching |
| Quality scoring | No | Yes (B1.4) |
| Chunking | No | Yes (B1.3) |

---

## Next Steps

### Task B1.7: MCP Tool Integration

The PDF scraper will be available through MCP:

```python
# Future: MCP tool
result = mcp.scrape_pdf(
    config_path="configs/manual.json"
)

# Or direct
result = mcp.scrape_pdf(
    pdf_path="manual.pdf",
    name="mymanual",
    extract_images=True
)
```

---

## Conclusion

Tasks B1.6 and B1.8 successfully implement:

**B1.6 - PDF Scraper CLI:**
- ✅ Complete extraction → building workflow
- ✅ Three usage modes (config, direct, from-json)
- ✅ Automatic categorization (chapter or keyword-based)
- ✅ Integration with Skill Seeker workflow
- ✅ Quality filtering and top examples

**B1.8 - PDF Config Format:**
- ✅ JSON configuration format
- ✅ Extraction options (chunk size, quality, images)
- ✅ Category definitions (keyword-based)
- ✅ Compatible with web scraper config style

**Impact:**
- Complete PDF documentation support
- Parallel workflow to web scraping
- Reusable extraction results
- High-quality skill generation

**Ready for B1.7:** MCP tool integration

---

**Tasks Completed:** October 21, 2025
**Next Task:** B1.7 - Add MCP tool `scrape_pdf`
