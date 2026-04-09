# Documentation Architecture

> **How Skill Seekers documentation is organized (v3.2.0 - 17 source types)**

---

## Philosophy

Our documentation follows these principles:

1. **Progressive Disclosure** - Start simple, add complexity as needed
2. **Task-Oriented** - Organized by what users want to do
3. **Single Source of Truth** - One authoritative reference per topic
4. **Version Current** - Always reflect the latest release

---

## Directory Structure

```
docs/
├── README.md              # Entry point - navigation hub
├── ARCHITECTURE.md        # This file
│
├── getting-started/       # New users (lowest cognitive load)
│   ├── 01-installation.md
│   ├── 02-quick-start.md
│   ├── 03-your-first-skill.md
│   └── 04-next-steps.md
│
├── user-guide/            # Common tasks (practical focus)
│   ├── 01-core-concepts.md
│   ├── 02-scraping.md
│   ├── 03-enhancement.md
│   ├── 04-packaging.md
│   ├── 05-workflows.md
│   └── 06-troubleshooting.md
│
├── reference/             # Technical details (comprehensive)
│   ├── CLI_REFERENCE.md
│   ├── MCP_REFERENCE.md
│   ├── CONFIG_FORMAT.md
│   └── ENVIRONMENT_VARIABLES.md
│
└── advanced/              # Power users (specialized)
    ├── mcp-server.md
    ├── mcp-tools.md
    ├── custom-workflows.md
    └── multi-source.md
```

---

## Category Guidelines

### Getting Started

**Purpose:** Get new users to their first success quickly

**Characteristics:**
- Minimal prerequisites
- Step-by-step instructions
- Copy-paste ready commands
- Screenshots/output examples

**Files:**
- `01-installation.md` - Install the tool
- `02-quick-start.md` - 3 commands to first skill
- `03-your-first-skill.md` - Complete walkthrough
- `04-next-steps.md` - Where to go after first success

---

### User Guide

**Purpose:** Teach common tasks and concepts

**Characteristics:**
- Task-oriented
- Practical examples
- Best practices
- Common patterns

**Files:**
- `01-core-concepts.md` - How it works
- `02-scraping.md` - All 17 source types (docs, GitHub, PDF, video, Word, EPUB, Jupyter, HTML, OpenAPI, AsciiDoc, PPTX, RSS, man pages, Confluence, Notion, Slack/Discord, local codebase)
- `03-enhancement.md` - AI enhancement
- `04-packaging.md` - Platform export
- `05-workflows.md` - Workflow presets
- `06-troubleshooting.md` - Problem solving

---

### Reference

**Purpose:** Authoritative technical information

**Characteristics:**
- Comprehensive
- Precise
- Organized for lookup
- Always accurate

**Files:**
- `CLI_REFERENCE.md` - All CLI commands (including 17 source-type subcommands)
- `MCP_REFERENCE.md` - 40 MCP tools
- `CONFIG_FORMAT.md` - JSON schema (covers all 17 source types)
- `ENVIRONMENT_VARIABLES.md` - All env vars (including Confluence, Notion, Slack tokens)

---

### Advanced

**Purpose:** Specialized topics for power users

**Characteristics:**
- Assumes basic knowledge
- Deep dives
- Complex scenarios
- Integration topics

**Files:**
- `mcp-server.md` - MCP server setup
- `mcp-tools.md` - Advanced MCP usage
- `custom-workflows.md` - Creating workflows
- `multi-source.md` - Unified scraping

---

## Naming Conventions

### Files

- **getting-started:** `01-topic.md` (numbered for order)
- **user-guide:** `01-topic.md` (numbered for order)
- **reference:** `TOPIC_REFERENCE.md` (uppercase, descriptive)
- **advanced:** `topic.md` (lowercase, specific)

### Headers

- H1: Title with version
- H2: Major sections
- H3: Subsections
- H4: Details

Example:
```markdown
# Topic Guide

> **Skill Seekers v3.1.0**

## Major Section

### Subsection

#### Detail
```

---

## Cross-References

Link to related docs using relative paths:

```markdown
<!-- Within same directory -->
See [Troubleshooting](06-troubleshooting.md)

<!-- Up one directory, then into reference -->
See [CLI Reference](../reference/CLI_REFERENCE.md)

<!-- Up two directories (to root) -->
See [Contributing](../../CONTRIBUTING.md)
```

---

## Maintenance

### Keeping Docs Current

1. **Update with code changes** - Docs must match implementation
2. **Version in header** - Keep version current
3. **Last updated date** - Track freshness
4. **Deprecate old files** - Don't delete, redirect

### Review Checklist

Before committing docs:

- [ ] Commands actually work (tested)
- [ ] No phantom commands documented
- [ ] Links work
- [ ] Version number correct
- [ ] Date updated

---

## Adding New Documentation

### New User Guide

1. Add to `user-guide/` with next number
2. Update `docs/README.md` navigation
3. Add to table of contents
4. Link from related guides

### New Reference

1. Add to `reference/` with `_REFERENCE` suffix
2. Update `docs/README.md` navigation
3. Link from user guides
4. Add to troubleshooting if relevant

### New Advanced Topic

1. Add to `advanced/` with descriptive name
2. Update `docs/README.md` navigation
3. Link from appropriate user guide

---

## Deprecation Strategy

When content becomes outdated:

1. **Don't delete immediately** - Breaks external links
2. **Add deprecation notice**:
   ```markdown
   > ⚠️ **DEPRECATED**: This document is outdated.
   > See [New Guide](path/to/new.md) for current information.
   ```
3. **Move to archive** after 6 months:
   ```
   docs/archive/legacy/
   ```
4. **Update navigation** to remove deprecated links

---

## Contributing

### Doc Changes

1. Edit relevant file
2. Test all commands
3. Update version/date
4. Submit PR

### New Doc

1. Choose appropriate category
2. Follow naming conventions
3. Add to README.md
4. Cross-link related docs

---

## See Also

- [Docs README](README.md) - Navigation hub
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute
- [Repository README](../README.md) - Project overview

## 9. Code Quality Metrics

This section provides quantitative insights into the codebase to help evaluate maintainability, complexity, and testing quality.

### 1. Cyclomatic Complexity
Measures the number of decision paths in the code (if/else/loops).

- Average: Moderate (3–5)
- Indicates manageable complexity and testability

---

### 2. Lines of Code (LoC) Distribution
Analyzes function and class sizes.

- Average function length: 15–25 lines
- Large functions (>50 lines) should be refactored

---

### 3. Nesting Depth
Represents how deeply logic is nested.

- Recommended max depth: 3–4 levels
- Deep nesting reduces readability

---

### 4. Test Coverage Estimation
Estimates ratio of test files to source files.

- Suggested ratio: ~1:1
- Higher ratio improves reliability

---

### 5. Code Duplication Detection
Identifies repeated logic across files.

- Duplicate code should be minimized
- Encourages reusable components

---

### Summary
These metrics help developers:
- Identify complex areas
- Improve code readability
- Maintain scalable architecture