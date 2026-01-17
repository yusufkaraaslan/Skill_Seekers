# Bootstrap Skill - Self-Hosting (v2.7.0)

**Version:** 2.7.0
**Feature:** Bootstrap Skill (Dogfooding)
**Status:** ✅ Production Ready
**Last Updated:** 2026-01-18

---

## Overview

The **Bootstrap Skill** feature allows Skill Seekers to analyze **itself** and generate a Claude Code skill containing its own documentation, API reference, code patterns, and usage examples. This is the ultimate form of "dogfooding" - using the tool to document itself.

**What You Get:**
- Complete Skill Seekers documentation as a Claude Code skill
- CLI command reference with examples
- Auto-generated API documentation from codebase
- Design pattern detection from source code
- Test example extraction for learning
- Installation into Claude Code for instant access

**Use Cases:**
- Learn Skill Seekers by having it explain itself to Claude
- Quick reference for CLI commands while working
- API documentation for programmatic usage
- Code pattern examples from the source
- Self-documenting development workflow

---

## Quick Start

### One-Command Installation

```bash
# Generate and install the bootstrap skill
./scripts/bootstrap_skill.sh
```

This script will:
1. ✅ Analyze the Skill Seekers codebase (C3.x features)
2. ✅ Merge handcrafted header with auto-generated content
3. ✅ Validate YAML frontmatter and structure
4. ✅ Create `output/skill-seekers/` directory
5. ✅ Install to Claude Code (optional)

**Time:** ~2-5 minutes (depending on analysis depth)

### Manual Installation

```bash
# 1. Run codebase analysis
skill-seekers codebase \
  --directory . \
  --output output/skill-seekers \
  --name skill-seekers

# 2. Merge with custom header (optional)
cat scripts/skill_header.md output/skill-seekers/SKILL.md > output/skill-seekers/SKILL_MERGED.md
mv output/skill-seekers/SKILL_MERGED.md output/skill-seekers/SKILL.md

# 3. Install to Claude Code
skill-seekers install-agent \
  --skill-dir output/skill-seekers \
  --agent-dir ~/.claude/skills/skill-seekers
```

---

## How It Works

### Architecture

The bootstrap skill combines three components:

```
┌─────────────────────────────────────────────────────────┐
│              Bootstrap Skill Architecture               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Handcrafted Header (scripts/skill_header.md)       │
│     ├── YAML frontmatter                                │
│     ├── Installation instructions                       │
│     ├── Quick start guide                               │
│     └── Core concepts                                   │
│                                                         │
│  2. Auto-Generated Content (codebase_scraper.py)       │
│     ├── C3.1: Design pattern detection                 │
│     ├── C3.2: Test example extraction                  │
│     ├── C3.3: How-to guide generation                  │
│     ├── C3.4: Configuration extraction                 │
│     ├── C3.5: Architectural overview                   │
│     ├── C3.7: Architectural pattern detection          │
│     ├── C3.8: API reference + dependency graphs        │
│     └── Code analysis (9 languages)                    │
│                                                         │
│  3. Validation System (frontmatter detection)          │
│     ├── YAML frontmatter check                         │
│     ├── Required field validation                      │
│     └── Structure verification                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Step 1: Codebase Analysis

The `codebase_scraper.py` module analyzes the Skill Seekers source code:

```bash
skill-seekers codebase --directory . --output output/skill-seekers
```

**What Gets Analyzed:**
- **Python source files** (`src/skill_seekers/**/*.py`)
- **Test files** (`tests/**/*.py`)
- **Configuration files** (`configs/*.json`)
- **Documentation** (`docs/**/*.md`, `README.md`, etc.)

**C3.x Features Applied:**
- **C3.1:** Detects design patterns (Strategy, Factory, Singleton, etc.)
- **C3.2:** Extracts test examples showing real usage
- **C3.3:** Generates how-to guides from test workflows
- **C3.4:** Extracts configuration patterns (CLI args, env vars)
- **C3.5:** Creates architectural overview of the codebase
- **C3.7:** Detects architectural patterns (MVC, Repository, etc.)
- **C3.8:** Builds API reference and dependency graphs

### Step 2: Header Combination

The bootstrap script merges a handcrafted header with auto-generated content:

```bash
# scripts/bootstrap_skill.sh does this:
cat scripts/skill_header.md output/skill-seekers/SKILL.md > merged.md
```

**Why Two Parts?**
- **Header:** Curated introduction, installation steps, core concepts
- **Auto-generated:** Always up-to-date code patterns, examples, API docs

**Header Structure** (`scripts/skill_header.md`):
```markdown
---
name: skill-seekers
version: 2.7.0
description: |
  Documentation-to-AI skill conversion tool. Use when working with
  Skill Seekers codebase, CLI commands, or API integration.
tags: [documentation, scraping, ai-skills, mcp]
---

# Skill Seekers - Documentation to AI Skills

## Installation
...

## Quick Start
...

## Core Concepts
...

<!-- AUTO-GENERATED CONTENT STARTS HERE -->
```

### Step 3: Validation

The bootstrap script validates the final skill:

```bash
# Check for YAML frontmatter
if ! grep -q "^---$" output/skill-seekers/SKILL.md; then
    echo "❌ Missing YAML frontmatter"
    exit 1
fi

# Validate required fields
python -c "
import yaml
with open('output/skill-seekers/SKILL.md') as f:
    content = f.read()
    frontmatter = yaml.safe_load(content.split('---')[1])
    required = ['name', 'version', 'description']
    for field in required:
        assert field in frontmatter, f'Missing {field}'
"
```

**Validated Fields:**
- ✅ `name` - Skill name
- ✅ `version` - Version number
- ✅ `description` - When to use this skill
- ✅ `tags` - Categorization tags
- ✅ Proper YAML syntax
- ✅ Content structure

### Step 4: Output

The final skill is created in `output/skill-seekers/`:

```
output/skill-seekers/
├── SKILL.md                    # Main skill file (300-500 lines)
├── references/                 # Detailed references
│   ├── api_reference/          # API documentation
│   │   ├── doc_scraper.md
│   │   ├── github_scraper.md
│   │   └── ...
│   ├── patterns/               # Design patterns detected
│   │   ├── strategy_pattern.md
│   │   ├── factory_pattern.md
│   │   └── ...
│   ├── test_examples/          # Usage examples from tests
│   │   ├── scraping_examples.md
│   │   ├── packaging_examples.md
│   │   └── ...
│   └── how_to_guides/          # Generated guides
│       ├── how_to_scrape_docs.md
│       ├── how_to_package_skills.md
│       └── ...
└── metadata.json               # Skill metadata
```

---

## Advanced Usage

### Customizing the Header

Edit `scripts/skill_header.md` to customize the introduction:

```markdown
---
name: skill-seekers
version: 2.7.0
description: |
  YOUR CUSTOM DESCRIPTION HERE
tags: [your, custom, tags]
custom_field: your_value
---

# Your Custom Title

Your custom introduction...

<!-- AUTO-GENERATED CONTENT STARTS HERE -->
```

**Guidelines:**
- Keep frontmatter in YAML format
- Include required fields: `name`, `version`, `description`
- Add custom fields as needed
- Marker comment preserves auto-generated content location

### Validation Options

The bootstrap script supports custom validation rules:

```bash
# scripts/bootstrap_skill.sh (excerpt)

# Custom validation function
validate_skill() {
    local skill_file=$1

    # Check frontmatter
    if ! has_frontmatter "$skill_file"; then
        echo "❌ Missing frontmatter"
        return 1
    fi

    # Check required fields
    if ! has_required_fields "$skill_file"; then
        echo "❌ Missing required fields"
        return 1
    fi

    # Check content structure
    if ! has_proper_structure "$skill_file"; then
        echo "❌ Invalid structure"
        return 1
    fi

    echo "✅ Validation passed"
    return 0
}
```

**Custom Validation:**
- Add your own validation functions
- Check for custom frontmatter fields
- Validate content structure
- Enforce your own standards

### CI/CD Integration

Automate bootstrap skill generation in your CI/CD pipeline:

```yaml
# .github/workflows/bootstrap-skill.yml
name: Generate Bootstrap Skill

on:
  push:
    branches: [main, development]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  bootstrap:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Skill Seekers
        run: pip install -e .

      - name: Generate Bootstrap Skill
        run: ./scripts/bootstrap_skill.sh

      - name: Upload Artifact
        uses: actions/upload-artifact@v3
        with:
          name: bootstrap-skill
          path: output/skill-seekers/

      - name: Commit to Repository (optional)
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add output/skill-seekers/
          git commit -m "chore: Update bootstrap skill [skip ci]"
          git push
```

---

## Troubleshooting

### Common Issues

#### 1. Missing YAML Frontmatter

**Error:**
```
❌ Missing YAML frontmatter in output/skill-seekers/SKILL.md
```

**Solution:**
```bash
# Check if scripts/skill_header.md has frontmatter
cat scripts/skill_header.md | head -10

# Should start with:
# ---
# name: skill-seekers
# version: 2.7.0
# ...
# ---
```

#### 2. Validation Failure

**Error:**
```
❌ Missing required fields in frontmatter
```

**Solution:**
```bash
# Check frontmatter fields
python -c "
import yaml
with open('output/skill-seekers/SKILL.md') as f:
    content = f.read()
    fm = yaml.safe_load(content.split('---')[1])
    print('Fields:', list(fm.keys()))
"

# Ensure: name, version, description are present
```

#### 3. Codebase Analysis Fails

**Error:**
```
❌ skill-seekers codebase failed with exit code 1
```

**Solution:**
```bash
# Run analysis manually to see error
skill-seekers codebase --directory . --output output/test

# Common causes:
# - Missing dependencies: pip install -e ".[all-llms]"
# - Invalid Python files: check syntax errors
# - Permission issues: check file permissions
```

#### 4. Header Merge Issues

**Error:**
```
Auto-generated content marker not found
```

**Solution:**
```bash
# Ensure marker exists in header
grep "AUTO-GENERATED CONTENT STARTS HERE" scripts/skill_header.md

# If missing, add it:
echo "<!-- AUTO-GENERATED CONTENT STARTS HERE -->" >> scripts/skill_header.md
```

### Debugging

Enable verbose output for debugging:

```bash
# Run with bash -x for debugging
bash -x ./scripts/bootstrap_skill.sh

# Or add debug statements
set -x  # Enable debugging
./scripts/bootstrap_skill.sh
set +x  # Disable debugging
```

**Debug Checklist:**
1. ✅ Skill Seekers installed: `skill-seekers --version`
2. ✅ Python 3.10+: `python --version`
3. ✅ Dependencies installed: `pip install -e ".[all-llms]"`
4. ✅ Header file exists: `ls scripts/skill_header.md`
5. ✅ Output directory writable: `touch output/test && rm output/test`

---

## Testing

### Running Tests

The bootstrap skill feature has comprehensive test coverage:

```bash
# Unit tests for bootstrap logic
pytest tests/test_bootstrap_skill.py -v

# End-to-end tests
pytest tests/test_bootstrap_skill_e2e.py -v

# Full test suite (10 tests for bootstrap feature)
pytest tests/test_bootstrap*.py -v
```

**Test Coverage:**
- ✅ Header parsing and validation
- ✅ Frontmatter detection
- ✅ Required field validation
- ✅ Content merging
- ✅ Output directory structure
- ✅ Codebase analysis integration
- ✅ Error handling
- ✅ Edge cases (missing files, invalid YAML, etc.)

### E2E Test Example

```python
def test_bootstrap_skill_e2e(tmp_path):
    """Test complete bootstrap skill workflow."""
    # Setup
    output_dir = tmp_path / "skill-seekers"
    header_file = "scripts/skill_header.md"

    # Run bootstrap
    result = subprocess.run(
        ["./scripts/bootstrap_skill.sh"],
        capture_output=True,
        text=True
    )

    # Verify
    assert result.returncode == 0
    assert (output_dir / "SKILL.md").exists()
    assert has_valid_frontmatter(output_dir / "SKILL.md")
    assert has_required_fields(output_dir / "SKILL.md")
```

### Test Coverage Report

```bash
# Run with coverage
pytest tests/test_bootstrap*.py --cov=scripts --cov-report=html

# View report
open htmlcov/index.html
```

---

## Examples

### Example 1: Basic Bootstrap

```bash
# Generate bootstrap skill
./scripts/bootstrap_skill.sh

# Output:
# ✅ Analyzing Skill Seekers codebase...
# ✅ Detected 15 design patterns
# ✅ Extracted 45 test examples
# ✅ Generated 12 how-to guides
# ✅ Merging with header...
# ✅ Validating skill...
# ✅ Bootstrap skill created: output/skill-seekers/SKILL.md
```

### Example 2: Custom Analysis Depth

```bash
# Run with basic analysis (faster)
skill-seekers codebase \
  --directory . \
  --output output/skill-seekers \
  --skip-patterns \
  --skip-how-to-guides

# Then merge with header
cat scripts/skill_header.md output/skill-seekers/SKILL.md > merged.md
```

### Example 3: Install to Claude Code

```bash
# Generate and install
./scripts/bootstrap_skill.sh

# Install to Claude Code
skill-seekers install-agent \
  --skill-dir output/skill-seekers \
  --agent-dir ~/.claude/skills/skill-seekers

# Now use in Claude Code:
# "Use the skill-seekers skill to explain how to scrape documentation"
```

### Example 4: Programmatic Usage

```python
from skill_seekers.cli.codebase_scraper import scrape_codebase
from skill_seekers.cli.install_agent import install_to_agent

# 1. Analyze codebase
result = scrape_codebase(
    directory='.',
    output_dir='output/skill-seekers',
    name='skill-seekers',
    enable_patterns=True,
    enable_how_to_guides=True
)

print(f"Skill created: {result['skill_path']}")

# 2. Merge with header
with open('scripts/skill_header.md') as f:
    header = f.read()

with open(result['skill_path']) as f:
    content = f.read()

merged = header + "\n\n<!-- AUTO-GENERATED -->\n\n" + content

with open(result['skill_path'], 'w') as f:
    f.write(merged)

# 3. Install to Claude Code
install_to_agent(
    skill_dir='output/skill-seekers',
    agent_dir='~/.claude/skills/skill-seekers'
)

print("✅ Bootstrap skill installed to Claude Code!")
```

---

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Codebase analysis | 1-3 min | With all C3.x features |
| Header merging | <1 sec | Simple concatenation |
| Validation | <1 sec | YAML parsing + checks |
| Installation | <1 sec | Copy to agent directory |
| **Total** | **2-5 min** | End-to-end bootstrap |

**Analysis Breakdown:**
- Pattern detection (C3.1): ~30 sec
- Test extraction (C3.2): ~20 sec
- How-to guides (C3.3): ~40 sec
- Config extraction (C3.4): ~10 sec
- Architecture overview (C3.5): ~30 sec
- Arch pattern detection (C3.7): ~20 sec
- API reference (C3.8): ~30 sec

---

## Best Practices

### 1. Keep Header Minimal

The header should provide context and quick start, not duplicate auto-generated content:

```markdown
---
name: skill-seekers
version: 2.7.0
description: Brief description
---

# Quick Introduction

Essential information only.

<!-- AUTO-GENERATED CONTENT STARTS HERE -->
```

### 2. Regenerate Regularly

Keep the bootstrap skill up-to-date with codebase changes:

```bash
# Weekly or on major changes
./scripts/bootstrap_skill.sh

# Or automate in CI/CD
```

### 3. Version Header with Code

Keep `scripts/skill_header.md` in version control:

```bash
git add scripts/skill_header.md
git commit -m "docs: Update bootstrap skill header"
```

### 4. Validate Before Committing

Always validate the generated skill:

```bash
# Run validation
python -c "
import yaml
with open('output/skill-seekers/SKILL.md') as f:
    content = f.read()
    assert '---' in content, 'Missing frontmatter'
    fm = yaml.safe_load(content.split('---')[1])
    assert 'name' in fm
    assert 'version' in fm
"
echo "✅ Validation passed"
```

---

## Related Features

- **[Codebase Scraping](../guides/USAGE.md#codebase-scraping)** - Analyze local codebases
- **[C3.x Features](PATTERN_DETECTION.md)** - Pattern detection and analysis
- **[Install Agent](../guides/USAGE.md#install-to-claude-code)** - Install skills to Claude Code
- **[API Reference](../reference/API_REFERENCE.md)** - Programmatic usage

---

## Changelog

### v2.7.0 (2026-01-18)
- ✅ Bootstrap skill feature introduced
- ✅ Dynamic frontmatter detection (not hardcoded)
- ✅ Comprehensive validation system
- ✅ CI/CD integration examples
- ✅ 10 unit tests + 8-12 E2E tests

---

**Version:** 2.7.0
**Last Updated:** 2026-01-18
**Status:** ✅ Production Ready
