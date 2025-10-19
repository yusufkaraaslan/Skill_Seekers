# GitHub Issues to Create

Copy these to GitHub Issues manually or use `gh issue create`

---

## Issue 1: Fix 3 Remaining Test Failures

**Title:** Fix 3 test failures (warnings vs errors handling)

**Labels:** bug, tests, good first issue

**Body:**
```markdown
## Problem
3 tests are failing because they check for errors but the validation function returns warnings for these cases:

1. `test_missing_recommended_selectors` - Missing selectors are warnings, not errors
2. `test_invalid_rate_limit_too_high` - Rate limit warnings
3. `test_invalid_max_pages_too_high` - Max pages warnings

**Current:** 68/71 tests passing (95.8%)
**Target:** 71/71 tests passing (100%)

## Location
- `tests/test_config_validation.py`

## Solution
Update tests to check warnings tuple instead of errors:
```python
# Before
errors, _ = validate_config(config)
self.assertTrue(any('title' in error.lower() for error in errors))

# After
_, warnings = validate_config(config)
self.assertTrue(any('title' in warning.lower() for warning in warnings))
```

## Acceptance Criteria
- [ ] All 71 tests passing
- [ ] Tests properly differentiate errors vs warnings
- [ ] No false positives

## Files to Modify
- `tests/test_config_validation.py` (3 test methods)
```

---

## Issue 2: Create MCP Setup Guide

**Title:** Create comprehensive MCP setup guide for Claude Code

**Labels:** documentation, mcp, enhancement

**Body:**
```markdown
## Goal
Create step-by-step guide for users to set up the MCP server with Claude Code.

## Content Needed

### 1. Prerequisites
- Python 3.7+
- Claude Code installed
- Repository cloned

### 2. Installation Steps
- Install dependencies
- Configure MCP in Claude Code
- Verify installation

### 3. Configuration Example
- Complete `~/.config/claude-code/mcp.json` example
- Path configuration
- Troubleshooting common issues

### 4. Usage Examples
- Generate config for new site
- Estimate pages
- Scrape and build skill
- End-to-end workflow

### 5. Screenshots/Video
- Visual guide through setup
- Example interactions

## Deliverables
- [ ] `docs/MCP_SETUP.md` - Main setup guide
- [ ] `.claude/mcp_config.example.json` - Example config
- [ ] Screenshots in `docs/images/`
- [ ] Optional: Quick start video

## Target Audience
Users who have Claude Code but never used MCP before.
```

---

## Issue 3: Test MCP Server Functionality

**Title:** Test MCP server with actual Claude Code instance

**Labels:** testing, mcp, priority-high

**Body:**
```markdown
## Goal
Verify MCP server works correctly with actual Claude Code.

## Test Plan

### Setup
1. Install MCP server locally
2. Configure Claude Code MCP settings
3. Restart Claude Code

### Tests

#### Test 1: List Configs
```
User: "List all available configs"
Expected: Shows 7 configs (godot, react, vue, django, fastapi, kubernetes, steam-economy)
```

#### Test 2: Generate Config
```
User: "Generate config for Tailwind CSS at https://tailwindcss.com/docs"
Expected: Creates configs/tailwind.json
```

#### Test 3: Estimate Pages
```
User: "Estimate pages for configs/tailwind.json"
Expected: Returns estimation results
```

#### Test 4: Validate Config
```
User: "Validate configs/react.json"
Expected: Shows config is valid
```

#### Test 5: Scrape Docs
```
User: "Scrape docs using configs/kubernetes.json with max 10 pages"
Expected: Creates output/kubernetes/ directory with SKILL.md
```

#### Test 6: Package Skill
```
User: "Package skill at output/kubernetes/"
Expected: Creates kubernetes.zip
```

## Success Criteria
- [ ] All 6 tools respond correctly
- [ ] No errors in Claude Code logs
- [ ] Generated files are correct
- [ ] Performance is acceptable (<5s for simple operations)

## Documentation
Document any issues found and solutions in test results.

## Files
- [ ] Create `tests/mcp_integration_test.md` with results
```

---

## Issue 4: Update Documentation for Monorepo

**Title:** Update all documentation for new monorepo structure

**Labels:** documentation, breaking-change

**Body:**
```markdown
## Goal
Update all documentation to reflect cli/ and mcp/ structure.

## Files to Update

### 1. README.md
- [ ] Update file structure diagram
- [ ] Add MCP section
- [ ] Update installation commands
- [ ] Add quick start for both CLI and MCP

### 2. CLAUDE.md
- [ ] Update paths (cli/doc_scraper.py)
- [ ] Add MCP usage section
- [ ] Update examples

### 3. docs/USAGE.md
- [ ] Update all command paths
- [ ] Add MCP usage section
- [ ] Update examples

### 4. docs/TESTING.md
- [ ] Update test run commands
- [ ] Note new import structure

### 5. QUICKSTART.md
- [ ] Update for both CLI and MCP
- [ ] Add decision tree: "Use CLI or MCP?"

## New Documentation Needed
- [ ] `mcp/QUICKSTART.md` - MCP-specific quick start
- [ ] Update diagrams/architecture docs

## Breaking Changes to Document
- CLI tools moved from root to `cli/`
- Import path changes: `from doc_scraper` → `from cli.doc_scraper`
- New MCP-based workflow available

## Validation
- [ ] All code examples work
- [ ] All paths are correct
- [ ] Links are not broken
```

---

## How to Create Issues

### Option 1: GitHub Web UI
1. Go to https://github.com/yusufkaraaslan/Skill_Seekers/issues/new
2. Copy title and body
3. Add labels
4. Create issue

### Option 2: GitHub CLI
```bash
# Issue 1
gh issue create --title "Fix 3 test failures (warnings vs errors handling)" \
  --body-file issue1.md \
  --label "bug,tests,good first issue"

# Issue 2
gh issue create --title "Create comprehensive MCP setup guide for Claude Code" \
  --body-file issue2.md \
  --label "documentation,mcp,enhancement"

# Issue 3
gh issue create --title "Test MCP server with actual Claude Code instance" \
  --body-file issue3.md \
  --label "testing,mcp,priority-high"

# Issue 4
gh issue create --title "Update all documentation for new monorepo structure" \
  --body-file issue4.md \
  --label "documentation,breaking-change"
```

### Option 3: Manual Script
Save each issue body to issue1.md, issue2.md, etc., then use gh CLI as shown above.
