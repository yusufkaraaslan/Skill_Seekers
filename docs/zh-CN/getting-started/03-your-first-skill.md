# Your First Skill - Complete Walkthrough

> **Skill Seekers v3.1.0**  
> **Step-by-step guide to creating your first skill**

---

## What We'll Build

A skill from the **Django documentation** that you can use with Claude AI.

**Time required:** ~15-20 minutes  
**Result:** A comprehensive Django skill with ~400 lines of structured documentation

---

## Prerequisites

```bash
# Ensure skill-seekers is installed
skill-seekers --version

# Should output: skill-seekers 3.1.0
```

---

## Step 1: Choose Your Source

For this walkthrough, we'll use Django documentation. You can use any of these:

```bash
# Option A: Django docs (what we'll use)
https://docs.djangoproject.com/

# Option B: React docs
https://react.dev/

# Option C: Your own project
./my-project

# Option D: GitHub repo
facebook/react
```

---

## Step 2: Preview with Dry Run

Before scraping, let's preview what will happen:

```bash
skill-seekers create https://docs.djangoproject.com/ --dry-run
```

**Expected output:**
```
🔍 Dry Run Preview
==================
Source: https://docs.djangoproject.com/
Type: Documentation website
Estimated pages: ~400
Estimated time: 15-20 minutes

Will create:
  - output/django/
  - output/django/SKILL.md
  - output/django/references/

Configuration:
  Rate limit: 0.5s
  Max pages: 500
  Enhancement: Level 2

✅ Preview complete. Run without --dry-run to execute.
```

This shows you exactly what will happen without actually scraping.

---

## Step 3: Create the Skill

Now let's actually create it:

```bash
skill-seekers create https://docs.djangoproject.com/ --name django
```

**What happens:**
1. **Detection** - Recognizes as documentation website
2. **Crawling** - Discovers pages starting from the base URL
3. **Scraping** - Downloads and extracts content (~5-10 min)
4. **Processing** - Organizes into categories
5. **Enhancement** - AI improves SKILL.md quality (~60 sec)

**Progress output:**
```
🚀 Creating skill: django
📍 Source: https://docs.djangoproject.com/
📋 Type: Documentation

⏳ Phase 1/5: Detecting source type...
✅ Detected: Documentation website

⏳ Phase 2/5: Discovering pages...
✅ Discovered: 387 pages

⏳ Phase 3/5: Scraping content...
Progress: [████████████████████░░░░░] 320/387 pages (83%)
Rate: 1.8 pages/sec | ETA: 37 seconds

⏳ Phase 4/5: Processing and categorizing...
✅ Categories: getting_started, models, views, templates, forms, admin, security

⏳ Phase 5/5: AI enhancement (Level 2)...
✅ SKILL.md enhanced: 423 lines

🎉 Skill created successfully!
   Location: output/django/
   SKILL.md: 423 lines
   References: 7 categories, 42 files

⏱️  Total time: 12 minutes 34 seconds
```

---

## Step 4: Explore the Output

Let's see what was created:

```bash
ls -la output/django/
```

**Output:**
```
output/django/
├── .skill-seekers/           # Metadata
│   └── manifest.json
├── SKILL.md                  # Main skill file ⭐
├── references/               # Organized docs
│   ├── index.md
│   ├── getting_started.md
│   ├── models.md
│   ├── views.md
│   ├── templates.md
│   ├── forms.md
│   ├── admin.md
│   └── security.md
└── assets/                   # Images (if any)
```

### View SKILL.md

```bash
head -50 output/django/SKILL.md
```

**You'll see:**
```markdown
# Django Skill

## Overview
Django is a high-level Python web framework that encourages rapid development 
and clean, pragmatic design...

## Quick Reference

### Create a Project
```bash
django-admin startproject mysite
```

### Create an App
```bash
python manage.py startapp myapp
```

## Categories
- [Getting Started](#getting-started)
- [Models](#models)
- [Views](#views)
- [Templates](#templates)
- [Forms](#forms)
- [Admin](#admin)
- [Security](#security)

...
```

### Check References

```bash
ls output/django/references/
cat output/django/references/models.md | head -30
```

---

## Step 5: Package for Claude

Now package it for Claude AI:

```bash
skill-seekers package output/django/ --target claude
```

**Output:**
```
📦 Packaging skill: django
🎯 Target: Claude AI

✅ Validated: SKILL.md (423 lines)
✅ Packaged: output/django-claude.zip
📊 Size: 245 KB

Next steps:
  1. Upload to Claude: skill-seekers upload output/django-claude.zip
  2. Or manually: Use "Create Skill" in Claude Code
```

---

## Step 6: Upload to Claude

### Option A: Auto-Upload

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers upload output/django-claude.zip --target claude
```

### Option B: Manual Upload

1. Open [Claude Code](https://claude.ai/code) or Claude Desktop
2. Go to "Skills" or "Projects"
3. Click "Create Skill" or "Upload"
4. Select `output/django-claude.zip`

---

## Step 7: Use Your Skill

Once uploaded, you can ask Claude:

```
"How do I create a Django model with foreign keys?"
"Show me how to use class-based views"
"What's the best way to handle forms in Django?"
"Explain Django's ORM query optimization"
```

Claude will use your skill to provide accurate, contextual answers.

---

## Alternative: Skip Enhancement for Speed

If you want faster results (no AI enhancement):

```bash
# Create without enhancement
skill-seekers create https://docs.djangoproject.com/ --name django --enhance-level 0

# Package
skill-seekers package output/django/ --target claude

# Enhances later if needed
skill-seekers enhance output/django/
```

---

## Alternative: Use a Preset Config

Instead of auto-detection, use a preset:

```bash
# See available presets
skill-seekers estimate --all

# Use Django preset
skill-seekers create --config django
skill-seekers package output/django/ --target claude
```

---

## What You Learned

✅ **Create** - `skill-seekers create <source>` auto-detects and scrapes  
✅ **Dry Run** - `--dry-run` previews without executing  
✅ **Enhancement** - AI automatically improves SKILL.md quality  
✅ **Package** - `skill-seekers package <dir> --target <platform>`  
✅ **Upload** - Direct upload or manual import  

---

## Common Variations

### GitHub Repository

```bash
skill-seekers create facebook/react --name react
skill-seekers package output/react/ --target claude
```

### Local Project

```bash
cd ~/projects/my-api
skill-seekers create . --name my-api
skill-seekers package output/my-api/ --target claude
```

### PDF Document

```bash
skill-seekers create manual.pdf --name docs
skill-seekers package output/docs/ --target claude
```

### Multi-Platform

```bash
# Create once
skill-seekers create https://docs.djangoproject.com/ --name django

# Package for multiple platforms
skill-seekers package output/django/ --target claude
skill-seekers package output/django/ --target gemini
skill-seekers package output/django/ --target openai

# Upload to each
skill-seekers upload output/django-claude.zip --target claude
skill-seekers upload output/django-gemini.tar.gz --target gemini
```

---

## Troubleshooting

### Scraping Interrupted

```bash
# Resume from checkpoint
skill-seekers resume --list
skill-seekers resume <job-id>
```

### Too Many Pages

```bash
# Limit pages
skill-seekers create https://docs.djangoproject.com/ --max-pages 100
```

### Wrong Content Extracted

```bash
# Use custom config with selectors
cat > configs/django.json << 'EOF'
{
  "name": "django",
  "base_url": "https://docs.djangoproject.com/",
  "selectors": {
    "main_content": "#docs-content"
  }
}
EOF

skill-seekers create --config configs/django.json
```

---

## Next Steps

- [Next Steps](04-next-steps.md) - Where to go from here
- [Core Concepts](../user-guide/01-core-concepts.md) - Understand the system
- [Scraping Guide](../user-guide/02-scraping.md) - Advanced scraping options
- [Enhancement Guide](../user-guide/03-enhancement.md) - AI enhancement deep dive

---

## Summary

| Step | Command | Time |
|------|---------|------|
| 1 | `skill-seekers create https://docs.djangoproject.com/` | ~15 min |
| 2 | `skill-seekers package output/django/ --target claude` | ~5 sec |
| 3 | `skill-seekers upload output/django-claude.zip` | ~10 sec |

**Total:** ~15 minutes to a production-ready AI skill! 🎉
