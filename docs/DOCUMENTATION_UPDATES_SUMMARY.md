# Documentation Updates Summary

**Date:** 2026-02-22  
**Version:** 3.1.0  
**Purpose:** Document all documentation updates related to CLI flag synchronization

---

## Changes Overview

This document summarizes all documentation updates made to reflect the CLI flag synchronization changes across all 5 scrapers (doc, github, analyze, pdf, unified).

---

## Updated Files

### 1. docs/reference/CLI_REFERENCE.md
**Changes:**
- **analyze command**: Added new flags:
  - `--api-key` - Anthropic API key
  - `--enhance-workflow` - Apply workflow preset
  - `--enhance-stage` - Add inline stage
  - `--var` - Override workflow variable
  - `--workflow-dry-run` - Preview workflow
  - `--dry-run` - Preview analysis

- **pdf command**: Added new flags:
  - `--ocr` - Enable OCR
  - `--pages` - Page range
  - `--enhance-level` - AI enhancement level
  - `--api-key` - Anthropic API key
  - `--dry-run` - Preview extraction

- **unified command**: Added new flags:
  - `--enhance-level` - Override enhancement level
  - `--api-key` - Anthropic API key
  - `--enhance-workflow` - Apply workflow preset
  - `--enhance-stage` - Add inline stage
  - `--var` - Override workflow variable
  - `--workflow-dry-run` - Preview workflow
  - `--skip-codebase-analysis` - Skip C3.x analysis

---

### 2. docs/reference/CONFIG_FORMAT.md
**Changes:**
- Added workflow configuration section for unified configs
- New top-level fields:
  - `workflows` - Array of workflow preset names
  - `workflow_stages` - Array of inline stages
  - `workflow_vars` - Object of variable overrides
  - `workflow_dry_run` - Boolean for preview mode
- Added example JSON showing workflow configuration
- Documented CLI priority (CLI flags override config values)

---

### 3. docs/user-guide/05-workflows.md
**Changes:**
- Added "Workflow Support Across All Scrapers" section
  - Table showing all 5 scrapers support workflows
  - Examples for each source type (web, GitHub, local, PDF, unified)
- Added "Workflows in Config Files" section
  - JSON example with workflows, stages, and vars
  - CLI override example showing priority

---

### 4. docs/features/UNIFIED_SCRAPING.md
**Changes:**
- Updated Phase list to include Phase 5 (Enhancement Workflows)
- Added "Enhancement Workflow Options" section with:
  - Workflow preset examples
  - Multiple workflow chaining
  - Custom enhancement stages
  - Workflow variables
  - Dry run preview
- Added "Global Enhancement Override" section:
  - --enhance-level override
  - --api-key usage
- Added "Workflow Configuration in JSON" section:
  - Complete JSON example
  - CLI priority note
- Updated data flow diagram to include Phase 5
- Added local source to scraper list
- Updated Changelog with v3.1.0 changes

---

## Files Reviewed (No Changes Needed)

### docs/advanced/custom-workflows.md
- Already comprehensive, covers custom workflow creation
- No updates needed for flag synchronization

### docs/advanced/multi-source.md
- Already covers multi-source concepts well
- No updates needed for flag synchronization

### docs/reference/FEATURE_MATRIX.md
- Already comprehensive platform/feature matrix
- No updates needed for flag synchronization

---

## Chinese Translation Updates Required

The following Chinese documentation files should be updated to match the English versions:

### Priority 1 (Must Update)
1. `docs/zh-CN/reference/CLI_REFERENCE.md`
   - Add new flags to analyze, pdf, unified commands

2. `docs/zh-CN/reference/CONFIG_FORMAT.md`
   - Add workflow configuration section

3. `docs/zh-CN/user-guide/05-workflows.md`
   - Add scraper support table
   - Add config file workflow section

### Priority 2 (Should Update)
4. `docs/zh-CN/features/UNIFIED_SCRAPING.md`
   - Add Phase 5 (workflows)
   - Add CLI flag sections

---

## Auto-Translation Workflow

The repository has a GitHub Actions workflow (`.github/workflows/translate-docs.yml`) that can automatically translate documentation to Chinese.

To trigger translation:
1. Push changes to main branch
2. Workflow will auto-translate modified files
3. Review and merge the translation PR

---

## Verification Checklist

- [x] CLI_REFERENCE.md updated with new flags
- [x] CONFIG_FORMAT.md updated with workflow support
- [x] user-guide/05-workflows.md updated with scraper coverage
- [x] features/UNIFIED_SCRAPING.md updated with Phase 5
- [ ] Chinese translations updated (via auto-translate workflow)

---

## Key New Features to Document

1. **All 5 scrapers now support workflows:**
   - doc_scraper (scrape command)
   - github_scraper (github command)
   - codebase_scraper (analyze command) - **NEW**
   - pdf_scraper (pdf command) - **NEW**
   - unified_scraper (unified command) - **NEW**

2. **New CLI flags across scrapers:**
   - `--api-key` - analyze, pdf, unified
   - `--enhance-level` - unified (override)
   - `--enhance-workflow` - analyze, unified
   - `--enhance-stage` - analyze, unified
   - `--var` - analyze, unified
   - `--workflow-dry-run` - analyze, unified
   - `--dry-run` - analyze

3. **Config file workflow support:**
   - Top-level `workflows` array
   - `workflow_stages` for inline stages
   - `workflow_vars` for variables
   - `workflow_dry_run` for preview

---

## Related Commits

- `22bdd4f` - CLI flag sync across analyze/pdf/unified commands
- `4722634` - CONFIG_ARGUMENTS and _route_config fixes
- `4b70c5a` - Workflow support to unified_scraper

---

*For questions or issues, refer to the main README.md or open a GitHub issue.*
