# Multi-Source Scraping Guide

> **Skill Seekers v3.1.0**  
> **Combine documentation, code, and PDFs into one skill**

---

## What is Multi-Source Scraping?

Combine multiple sources into a single, comprehensive skill:

```
┌──────────────┐
│  Documentation │──┐
│  (Web docs)    │  │
└──────────────┘  │
                   │
┌──────────────┐  │     ┌──────────────────┐
│  GitHub Repo │──┼────▶│  Unified Skill   │
│  (Source code)│  │     │  (Single source  │
└──────────────┘  │     │   of truth)      │
                   │     └──────────────────┘
┌──────────────┐  │
│  PDF Manual  │──┘
│  (Reference) │
└──────────────┘
```

---

## When to Use Multi-Source

### Use Cases

| Scenario | Sources | Benefit |
|----------|---------|---------|
| Framework + Examples | Docs + GitHub repo | Theory + practice |
| Product + API | Docs + OpenAPI spec | Usage + reference |
| Legacy + Current | PDF + Web docs | Complete history |
| Internal + External | Local code + Public docs | Full context |

### Benefits

- **Single source of truth** - One skill with all context
- **Conflict detection** - Find doc/code discrepancies
- **Cross-references** - Link between sources
- **Comprehensive** - No gaps in knowledge

---

## Creating Unified Configs

### Basic Structure

```json
{
  "name": "my-framework-complete",
  "description": "Complete documentation and code",
  "merge_mode": "claude-enhanced",
  
  "sources": [
    {
      "type": "docs",
      "name": "documentation",
      "base_url": "https://docs.example.com/"
    },
    {
      "type": "github",
      "name": "source-code",
      "repo": "owner/repo"
    }
  ]
}
```

---

## Source Types

### 1. Documentation

```json
{
  "type": "docs",
  "name": "official-docs",
  "base_url": "https://docs.framework.com/",
  "max_pages": 500,
  "categories": {
    "getting_started": ["intro", "quickstart"],
    "api": ["reference", "api"]
  }
}
```

### 2. GitHub Repository

```json
{
  "type": "github",
  "name": "source-code",
  "repo": "facebook/react",
  "fetch_issues": true,
  "max_issues": 100,
  "enable_codebase_analysis": true
}
```

### 3. PDF Document

```json
{
  "type": "pdf",
  "name": "legacy-manual",
  "pdf_path": "docs/legacy-manual.pdf",
  "enable_ocr": false
}
```

### 4. Local Codebase

```json
{
  "type": "local",
  "name": "internal-tools",
  "directory": "./internal-lib",
  "languages": ["Python", "JavaScript"]
}
```

---

## Complete Example

### React Complete Skill

```json
{
  "name": "react-complete",
  "description": "React - docs, source, and guides",
  "merge_mode": "claude-enhanced",
  
  "sources": [
    {
      "type": "docs",
      "name": "react-docs",
      "base_url": "https://react.dev/",
      "max_pages": 300,
      "categories": {
        "getting_started": ["learn", "tutorial"],
        "api": ["reference", "hooks"],
        "advanced": ["concurrent", "suspense"]
      }
    },
    {
      "type": "github",
      "name": "react-source",
      "repo": "facebook/react",
      "fetch_issues": true,
      "max_issues": 50,
      "enable_codebase_analysis": true,
      "code_analysis_depth": "deep"
    },
    {
      "type": "pdf",
      "name": "react-patterns",
      "pdf_path": "downloads/react-patterns.pdf"
    }
  ],
  
  "conflict_detection": {
    "enabled": true,
    "rules": [
      {
        "field": "api_signature",
        "action": "flag_mismatch"
      },
      {
        "field": "version",
        "action": "warn_outdated"
      }
    ]
  },
  
  "output_structure": {
    "group_by_source": false,
    "cross_reference": true
  }
}
```

---

## Running Unified Scraping

### Basic Command

```bash
skill-seekers unified --config react-complete.json
```

### With Options

```bash
# Fresh start (ignore cache)
skill-seekers unified --config react-complete.json --fresh

# Dry run
skill-seekers unified --config react-complete.json --dry-run

# Rule-based merging
skill-seekers unified --config react-complete.json --merge-mode rule-based
```

---

## Merge Modes

### claude-enhanced (Default)

Uses AI to intelligently merge sources:

- Detects relationships between content
- Resolves conflicts intelligently
- Creates cross-references
- Best quality, slower

```bash
skill-seekers unified --config my-config.json --merge-mode claude-enhanced
```

### rule-based

Uses defined rules for merging:

- Faster
- Deterministic
- Less sophisticated

```bash
skill-seekers unified --config my-config.json --merge-mode rule-based
```

---

## Conflict Detection

### Automatic Detection

Finds discrepancies between sources:

```json
{
  "conflict_detection": {
    "enabled": true,
    "rules": [
      {
        "field": "api_signature",
        "action": "flag_mismatch"
      },
      {
        "field": "version",
        "action": "warn_outdated"
      },
      {
        "field": "deprecation",
        "action": "highlight"
      }
    ]
  }
}
```

### Conflict Report

After scraping, check for conflicts:

```bash
# Conflicts are reported in output
ls output/react-complete/conflicts.json

# Or use MCP tool
detect_conflicts({
  "docs_source": "output/react-docs",
  "code_source": "output/react-source"
})
```

---

## Output Structure

### Merged Output

```
output/react-complete/
├── SKILL.md                    # Combined skill
├── references/
│   ├── index.md               # Master index
│   ├── getting_started.md     # From docs
│   ├── api_reference.md       # From docs
│   ├── source_overview.md     # From GitHub
│   ├── code_examples.md       # From GitHub
│   └── patterns.md            # From PDF
├── .skill-seekers/
│   ├── manifest.json          # Metadata
│   ├── sources.json           # Source list
│   └── conflicts.json         # Detected conflicts
└── cross-references.json      # Links between sources
```

---

## Best Practices

### 1. Name Sources Clearly

```json
{
  "sources": [
    {"type": "docs", "name": "official-docs"},
    {"type": "github", "name": "source-code"},
    {"type": "pdf", "name": "legacy-reference"}
  ]
}
```

### 2. Limit Source Scope

```json
{
  "type": "github",
  "name": "core-source",
  "repo": "owner/repo",
  "file_patterns": ["src/**/*.py"],  // Only core files
  "exclude_patterns": ["tests/**", "docs/**"]
}
```

### 3. Enable Conflict Detection

```json
{
  "conflict_detection": {
    "enabled": true
  }
}
```

### 4. Use Appropriate Merge Mode

- **claude-enhanced** - Best quality, for important skills
- **rule-based** - Faster, for testing or large datasets

### 5. Test Incrementally

```bash
# Test with one source first
skill-seekers create <source1>

# Then add sources
skill-seekers unified --config my-config.json --dry-run
```

---

## Troubleshooting

### "Source not found"

```bash
# Check all sources exist
curl -I https://docs.example.com/
ls downloads/manual.pdf
```

### "Merge conflicts"

```bash
# Check conflicts report
cat output/my-skill/conflicts.json

# Adjust merge_mode
skill-seekers unified --config my-config.json --merge-mode rule-based
```

### "Out of memory"

```bash
# Process sources separately
# Then merge manually
```

---

## Examples

### Framework + Examples

```json
{
  "name": "django-complete",
  "sources": [
    {"type": "docs", "base_url": "https://docs.djangoproject.com/"},
    {"type": "github", "repo": "django/django", "fetch_issues": false}
  ]
}
```

### API + Documentation

```json
{
  "name": "stripe-complete",
  "sources": [
    {"type": "docs", "base_url": "https://stripe.com/docs"},
    {"type": "pdf", "pdf_path": "stripe-api-reference.pdf"}
  ]
}
```

### Legacy + Current

```json
{
  "name": "product-docs",
  "sources": [
    {"type": "docs", "base_url": "https://docs.example.com/v2/"},
    {"type": "pdf", "pdf_path": "v1-legacy-manual.pdf"}
  ]
}
```

---

## See Also

- [Config Format](../reference/CONFIG_FORMAT.md) - Full JSON specification
- [Scraping Guide](../user-guide/02-scraping.md) - Individual source options
- [MCP Reference](../reference/MCP_REFERENCE.md) - unified_scrape tool
