---
name: skill-seekers
description: Generate LLM skills from documentation, codebases, and GitHub repositories
---

# Skill Seekers

## Prerequisites

```bash
pip install skill-seekers
# Or: uv pip install skill-seekers
```

## Commands

| Source | Command |
|--------|---------|
| Local code | `skill-seekers-codebase --directory ./path` |
| Docs URL | `skill-seekers scrape --url https://...` |
| GitHub | `skill-seekers github --repo owner/repo` |
| PDF | `skill-seekers pdf --file doc.pdf` |

## Quick Start

```bash
# Analyze local codebase
skill-seekers-codebase --directory /path/to/project --output output/my-skill/

# Package for Claude
yes | skill-seekers package output/my-skill/ --no-open
```

## Options

| Flag | Description |
|------|-------------|
| `--depth surface/deep/full` | Analysis depth |
| `--skip-patterns` | Skip pattern detection |
| `--skip-test-examples` | Skip test extraction |
| `--ai-mode none/api/local` | AI enhancement |

---

