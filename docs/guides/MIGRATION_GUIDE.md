# Migration Guide

**Version:** 2.7.0
**Last Updated:** 2026-01-18
**Status:** ✅ Production Ready

---

## Overview

This guide helps you upgrade Skill Seekers between major versions. Each section covers breaking changes, new features, and step-by-step migration instructions.

**Current Version:** v2.7.0

**Supported Upgrade Paths:**
- v2.6.0 → v2.7.0 (Latest)
- v2.5.0 → v2.6.0 or v2.7.0
- v2.1.0 → v2.5.0+
- v1.0.0 → v2.x.0

---

## Quick Version Check

```bash
# Check installed version
skill-seekers --version

# Check for updates
pip show skill-seekers | grep Version

# Upgrade to latest
pip install --upgrade skill-seekers[all-llms]
```

---

## v2.6.0 → v2.7.0 (Latest)

**Release Date:** January 18, 2026
**Type:** Minor release (backward compatible)

### Summary of Changes

✅ **Fully Backward Compatible** - No breaking changes
- Code quality improvements (21 ruff fixes)
- Version synchronization
- Bug fixes (case-sensitivity, test fixtures)
- Documentation updates

### What's New

1. **Code Quality**
   - All 21 ruff linting errors fixed
   - Zero linting errors across codebase
   - Improved code maintainability

2. **Version Synchronization**
   - All `__init__.py` files now show correct version
   - Fixed version mismatch bug (Issue #248)

3. **Bug Fixes**
   - Case-insensitive regex in install workflow (Issue #236)
   - Test fixture issues resolved
   - 1200+ tests passing (up from 700+)

4. **Documentation**
   - Comprehensive documentation overhaul
   - New API reference guide
   - Bootstrap skill documentation
   - Code quality standards
   - Testing guide

### Migration Steps

**No migration required!** This is a drop-in replacement.

```bash
# Upgrade
pip install --upgrade skill-seekers[all-llms]

# Verify
skill-seekers --version  # Should show 2.7.0

# Run tests (optional)
pytest tests/ -v
```

### Compatibility

| Feature | v2.6.0 | v2.7.0 | Notes |
|---------|--------|--------|-------|
| CLI commands | ✅ | ✅ | Fully compatible |
| Config files | ✅ | ✅ | No changes needed |
| MCP tools | 17 tools | 18 tools | `enhance_skill` added |
| Platform adaptors | ✅ | ✅ | No API changes |
| Python versions | 3.10-3.13 | 3.10-3.13 | Same support |

---

## v2.5.0 → v2.6.0

**Release Date:** January 14, 2026
**Type:** Minor release

### Summary of Changes

✅ **Mostly Backward Compatible** - One minor breaking change

**Breaking Change:**
- Codebase analysis features changed from opt-in (`--build-*`) to opt-out (`--skip-*`)
- Default behavior: All C3.x features enabled

### What's New

1. **C3.x Codebase Analysis Suite** (C3.1-C3.8)
   - Pattern detection (10 GoF patterns, 9 languages)
   - Test example extraction
   - How-to guide generation
   - Configuration extraction
   - Architectural overview
   - Architectural pattern detection
   - API reference + dependency graphs

2. **Multi-Platform Support**
   - Claude AI, Google Gemini, OpenAI ChatGPT, Generic Markdown
   - Platform adaptor architecture
   - Unified packaging and upload

3. **MCP Expansion**
   - 18 MCP tools (up from 9)
   - New tools: `enhance_skill`, `merge_sources`, etc.

4. **Test Improvements**
   - 700+ tests passing
   - Improved test coverage

### Migration Steps

#### 1. Upgrade Package

```bash
pip install --upgrade skill-seekers[all-llms]
```

#### 2. Update Codebase Analysis Commands

**Before (v2.5.0 - opt-in):**
```bash
# Had to enable features explicitly
skill-seekers codebase --directory . --build-api-reference --build-dependency-graph
```

**After (v2.6.0 - opt-out):**
```bash
# All features enabled by default
skill-seekers codebase --directory .

# Or skip specific features
skill-seekers codebase --directory . --skip-patterns --skip-how-to-guides
```

#### 3. Legacy Flags (Deprecated but Still Work)

Old flags still work but show warnings:
```bash
# Works with deprecation warning
skill-seekers codebase --directory . --build-api-reference

# Recommended: Remove old flags
skill-seekers codebase --directory .
```

#### 4. Verify MCP Configuration

If using MCP server, note new tools:
```bash
# Test new enhance_skill tool
python -m skill_seekers.mcp.server

# In Claude Code:
# "Use enhance_skill tool to improve the react skill"
```

### Compatibility

| Feature | v2.5.0 | v2.6.0 | Migration Required |
|---------|--------|--------|-------------------|
| CLI commands | ✅ | ✅ | No |
| Config files | ✅ | ✅ | No |
| Codebase flags | `--build-*` | `--skip-*` | Yes (but backward compatible) |
| MCP tools | 9 tools | 18 tools | No (additive) |
| Platform support | Claude only | 4 platforms | No (opt-in) |

---

## v2.1.0 → v2.5.0

**Release Date:** November 29, 2025
**Type:** Minor release

### Summary of Changes

✅ **Backward Compatible**
- Unified multi-source scraping
- GitHub repository analysis
- PDF extraction
- Test coverage improvements

### What's New

1. **Unified Scraping**
   - Combine docs + GitHub + PDF
   - Conflict detection
   - Smart merging

2. **GitHub Integration**
   - Full repository analysis
   - Unlimited local analysis (no API limits)

3. **PDF Support**
   - Extract from PDF documents
   - OCR for scanned PDFs
   - Image extraction

4. **Testing**
   - 427 tests passing
   - Improved coverage

### Migration Steps

```bash
# Upgrade
pip install --upgrade skill-seekers

# New unified scraping
skill-seekers unified --config configs/unified/react-unified.json

# GitHub analysis
skill-seekers github https://github.com/facebook/react
```

### Compatibility

All v2.1.0 commands work in v2.5.0. New features are additive.

---

## v1.0.0 → v2.0.0+

**Release Date:** October 19, 2025 → Present
**Type:** Major version upgrade

### Summary of Changes

⚠️ **Major Changes** - Some breaking changes

**Breaking Changes:**
1. CLI structure changed to git-style
2. Config format updated for unified scraping
3. MCP server architecture redesigned

### What Changed

#### 1. CLI Structure (Breaking)

**Before (v1.0.0):**
```bash
# Separate commands
doc-scraper --config react.json
github-scraper https://github.com/facebook/react
pdf-scraper manual.pdf
```

**After (v2.0.0+):**
```bash
# Unified CLI
skill-seekers scrape --config react
skill-seekers github https://github.com/facebook/react
skill-seekers pdf manual.pdf
```

**Migration:**
- Replace command prefixes with `skill-seekers <subcommand>`
- Update scripts/CI/CD workflows

#### 2. Config Format (Additive)

**v1.0.0 Config:**
```json
{
  "name": "react",
  "base_url": "https://react.dev",
  "selectors": {...}
}
```

**v2.0.0+ Unified Config:**
```json
{
  "name": "react",
  "sources": {
    "documentation": {
      "type": "docs",
      "base_url": "https://react.dev",
      "selectors": {...}
    },
    "github": {
      "type": "github",
      "repo_url": "https://github.com/facebook/react"
    }
  }
}
```

**Migration:**
- Old configs still work for single-source scraping
- Use new format for multi-source scraping

#### 3. MCP Server (Breaking)

**Before (v1.0.0):**
- 9 basic MCP tools
- stdio transport only

**After (v2.0.0+):**
- 18 comprehensive MCP tools
- stdio + HTTP transports
- FastMCP framework

**Migration:**
- Update MCP server configuration in `claude_desktop_config.json`
- Use `skill-seekers-mcp` instead of custom server script

### Migration Steps

#### Step 1: Upgrade Package

```bash
# Uninstall old version
pip uninstall skill-seekers

# Install latest
pip install skill-seekers[all-llms]

# Verify
skill-seekers --version
```

#### Step 2: Update Scripts

**Before:**
```bash
#!/bin/bash
doc-scraper --config react.json
package-skill output/react/ claude
upload-skill output/react-claude.zip
```

**After:**
```bash
#!/bin/bash
skill-seekers scrape --config react
skill-seekers package output/react/ --target claude
skill-seekers upload output/react-claude.zip --target claude

# Or use one command
skill-seekers install react --target claude --upload
```

#### Step 3: Update Configs (Optional)

**Convert to unified format:**
```python
# Old config (still works)
{
  "name": "react",
  "base_url": "https://react.dev"
}

# New unified config (recommended)
{
  "name": "react",
  "sources": {
    "documentation": {
      "type": "docs",
      "base_url": "https://react.dev"
    }
  }
}
```

#### Step 4: Update MCP Configuration

**Before (`claude_desktop_config.json`):**
```json
{
  "mcpServers": {
    "skill-seekers": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"]
    }
  }
}
```

**After:**
```json
{
  "mcpServers": {
    "skill-seekers": {
      "command": "skill-seekers-mcp"
    }
  }
}
```

### Compatibility

| Feature | v1.0.0 | v2.0.0+ | Migration |
|---------|--------|---------|-----------|
| CLI commands | Separate | Unified | Update scripts |
| Config format | Basic | Unified | Old still works |
| MCP server | 9 tools | 18 tools | Update config |
| Platforms | Claude only | 4 platforms | Opt-in |

---

## Common Migration Issues

### Issue 1: Command Not Found

**Problem:**
```bash
doc-scraper --config react.json
# command not found: doc-scraper
```

**Solution:**
```bash
# Use new CLI
skill-seekers scrape --config react
```

### Issue 2: Config Validation Errors

**Problem:**
```
InvalidConfigError: Missing 'sources' key
```

**Solution:**
```bash
# Old configs still work for single-source
skill-seekers scrape --config configs/react.json

# Or convert to unified format
# Add 'sources' wrapper
```

### Issue 3: MCP Server Not Starting

**Problem:**
```
ModuleNotFoundError: No module named 'skill_seekers.mcp'
```

**Solution:**
```bash
# Reinstall with latest version
pip install --upgrade skill-seekers[all-llms]

# Use correct command
skill-seekers-mcp
```

### Issue 4: API Key Errors

**Problem:**
```
APIError: Invalid API key
```

**Solution:**
```bash
# Set environment variables
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
export OPENAI_API_KEY=sk-...

# Verify
echo $ANTHROPIC_API_KEY
```

---

## Best Practices for Migration

### 1. Test in Development First

```bash
# Create test environment
python -m venv test-env
source test-env/bin/activate

# Install new version
pip install skill-seekers[all-llms]

# Test your workflows
skill-seekers scrape --config react --dry-run
```

### 2. Backup Existing Configs

```bash
# Backup before migration
cp -r configs/ configs.backup/
cp -r output/ output.backup/
```

### 3. Update in Stages

```bash
# Stage 1: Upgrade package
pip install --upgrade skill-seekers[all-llms]

# Stage 2: Update CLI commands
# Update scripts one by one

# Stage 3: Test workflows
pytest tests/ -v

# Stage 4: Update production
```

### 4. Version Pinning in Production

```bash
# Pin to specific version in requirements.txt
skill-seekers==2.7.0

# Or use version range
skill-seekers>=2.7.0,<3.0.0
```

---

## Rollback Instructions

If migration fails, rollback to previous version:

```bash
# Rollback to v2.6.0
pip install skill-seekers==2.6.0

# Rollback to v2.5.0
pip install skill-seekers==2.5.0

# Restore configs
cp -r configs.backup/* configs/
```

---

## Getting Help

### Resources

- **[CHANGELOG](../../CHANGELOG.md)** - Full version history
- **[Troubleshooting](../../TROUBLESHOOTING.md)** - Common issues
- **[GitHub Issues](https://github.com/yusufkaraaslan/Skill_Seekers/issues)** - Report problems
- **[Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)** - Ask questions

### Reporting Migration Issues

When reporting migration issues:
1. Include both old and new versions
2. Provide config files (redact sensitive data)
3. Share error messages and stack traces
4. Describe what worked before vs. what fails now

**Issue Template:**
```markdown
**Old Version:** 2.5.0
**New Version:** 2.7.0
**Python Version:** 3.11.7
**OS:** Ubuntu 22.04

**What I did:**
1. Upgraded with pip install --upgrade skill-seekers
2. Ran skill-seekers scrape --config react

**Expected:** Scraping completes successfully
**Actual:** Error: ...

**Error Message:**
[paste full error]

**Config File:**
[paste config.json]
```

---

## Version History

| Version | Release Date | Type | Key Changes |
|---------|-------------|------|-------------|
| v2.7.0 | 2026-01-18 | Minor | Code quality, bug fixes, docs |
| v2.6.0 | 2026-01-14 | Minor | C3.x suite, multi-platform |
| v2.5.0 | 2025-11-29 | Minor | Unified scraping, GitHub, PDF |
| v2.1.0 | 2025-10-19 | Minor | Test coverage, quality |
| v1.0.0 | 2025-10-19 | Major | Production release |

---

**Version:** 2.7.0
**Last Updated:** 2026-01-18
**Status:** ✅ Production Ready
