# Quick Start Guide

> **Skill Seekers v3.1.0**  
> **Create your first skill in 3 commands**

---

## The 3 Commands

```bash
# 1. Install Skill Seekers
pip install skill-seekers

# 2. Create a skill from any source
skill-seekers create https://docs.django.com/

# 3. Package it for your AI platform
skill-seekers package output/django --target claude
```

**That's it!** You now have `output/django-claude.zip` ready to upload.

---

## What You Can Create From

The `create` command auto-detects your source:

| Source Type | Example Command |
|-------------|-----------------|
| **Documentation** | `skill-seekers create https://docs.react.dev/` |
| **GitHub Repo** | `skill-seekers create facebook/react` |
| **Local Code** | `skill-seekers create ./my-project` |
| **PDF File** | `skill-seekers create manual.pdf` |
| **Config File** | `skill-seekers create configs/custom.json` |

---

## Examples by Source

### Documentation Website

```bash
# React documentation
skill-seekers create https://react.dev/
skill-seekers package output/react --target claude

# Django documentation  
skill-seekers create https://docs.djangoproject.com/
skill-seekers package output/django --target claude
```

### GitHub Repository

```bash
# React source code
skill-seekers create facebook/react
skill-seekers package output/react --target claude

# Your own repo
skill-seekers create yourusername/yourrepo
skill-seekers package output/yourrepo --target claude
```

### Local Project

```bash
# Your codebase
skill-seekers create ./my-project
skill-seekers package output/my-project --target claude

# Specific directory
cd ~/projects/my-api
skill-seekers create .
skill-seekers package output/my-api --target claude
```

### PDF Document

```bash
# Technical manual
skill-seekers create manual.pdf --name product-docs
skill-seekers package output/product-docs --target claude

# Research paper
skill-seekers create paper.pdf --name research
skill-seekers package output/research --target claude
```

---

## Common Options

### Specify a Name

```bash
skill-seekers create https://docs.example.com/ --name my-docs
```

### Add Description

```bash
skill-seekers create facebook/react --description "React source code analysis"
```

### Dry Run (Preview)

```bash
skill-seekers create https://docs.react.dev/ --dry-run
```

### Skip Enhancement (Faster)

```bash
skill-seekers create https://docs.react.dev/ --enhance-level 0
```

### Use a Preset

```bash
# Quick analysis (1-2 min)
skill-seekers create ./my-project --preset quick

# Comprehensive analysis (20-60 min)
skill-seekers create ./my-project --preset comprehensive
```

---

## Package for Different Platforms

### Claude AI (Default)

```bash
skill-seekers package output/my-skill/
# Creates: output/my-skill-claude.zip
```

### Google Gemini

```bash
skill-seekers package output/my-skill/ --target gemini
# Creates: output/my-skill-gemini.tar.gz
```

### OpenAI ChatGPT

```bash
skill-seekers package output/my-skill/ --target openai
# Creates: output/my-skill-openai.zip
```

### LangChain

```bash
skill-seekers package output/my-skill/ --target langchain
# Creates: output/my-skill-langchain/ directory
```

### Multiple Platforms

```bash
for platform in claude gemini openai; do
  skill-seekers package output/my-skill/ --target $platform
done
```

---

## Upload to Platform

### Upload to Claude

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers upload output/my-skill-claude.zip --target claude
```

### Upload to Gemini

```bash
export GOOGLE_API_KEY=AIza...
skill-seekers upload output/my-skill-gemini.tar.gz --target gemini
```

### Auto-Upload After Package

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers package output/my-skill/ --target claude --upload
```

---

## Complete One-Command Workflow

Use `install` for everything in one step:

```bash
# Complete: scrape → enhance → package → upload
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers install --config react --target claude

# Skip upload
skill-seekers install --config react --target claude --no-upload
```

---

## Output Structure

After running `create`, you'll have:

```
output/
├── django/                    # The skill
│   ├── SKILL.md              # Main skill file
│   ├── references/           # Organized documentation
│   │   ├── index.md
│   │   ├── getting_started.md
│   │   └── api_reference.md
│   └── .skill-seekers/       # Metadata
│
└── django-claude.zip         # Packaged skill (after package)
```

---

## Time Estimates

| Source Type | Size | Time |
|-------------|------|------|
| Small docs (< 50 pages) | ~10 MB | 2-5 min |
| Medium docs (50-200 pages) | ~50 MB | 10-20 min |
| Large docs (200-500 pages) | ~200 MB | 30-60 min |
| GitHub repo (< 1000 files) | varies | 5-15 min |
| Local project | varies | 2-10 min |
| PDF (< 100 pages) | ~5 MB | 1-3 min |

*Times include scraping + enhancement (level 2). Use `--enhance-level 0` to skip enhancement.*

---

## Quick Tips

### Test First with Dry Run

```bash
skill-seekers create https://docs.example.com/ --dry-run
```

### Use Presets for Faster Results

```bash
# Quick mode for testing
skill-seekers create https://docs.react.dev/ --preset quick
```

### Skip Enhancement for Speed

```bash
skill-seekers create https://docs.react.dev/ --enhance-level 0
skill-seekers enhance output/react/  # Enhance later
```

### Check Available Configs

```bash
skill-seekers estimate --all
```

### Resume Interrupted Jobs

```bash
skill-seekers resume --list
skill-seekers resume <job-id>
```

---

## Next Steps

- [Your First Skill](03-your-first-skill.md) - Complete walkthrough
- [Core Concepts](../user-guide/01-core-concepts.md) - Understand how it works
- [Scraping Guide](../user-guide/02-scraping.md) - All scraping options

---

## Troubleshooting

### "command not found"

```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

### "No module named 'skill_seekers'"

```bash
# Reinstall
pip install --force-reinstall skill-seekers
```

### Scraping too slow

```bash
# Use async mode
skill-seekers create https://docs.react.dev/ --async --workers 5
```

### Out of memory

```bash
# Use streaming mode
skill-seekers package output/large-skill/ --streaming
```

---

## See Also

- [Installation Guide](01-installation.md) - Detailed installation
- [CLI Reference](../reference/CLI_REFERENCE.md) - All commands
- [Config Format](../reference/CONFIG_FORMAT.md) - Custom configurations
