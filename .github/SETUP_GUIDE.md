# GitHub Project Setup Guide

Quick guide to set up GitHub Issues and Project Board for Skill Seeker MCP development.

---

## Step 1: Create GitHub Issues (5 minutes)

### Quick Method:
1. Open: https://github.com/yusufkaraaslan/Skill_Seekers/issues/new
2. Open in another tab: `.github/ISSUES_TO_CREATE.md` (in your repo)
3. Copy title and body for each issue
4. Create 4 issues

### Issues to Create:

**Issue #1:**
- Title: `Fix 3 test failures (warnings vs errors handling)`
- Labels: `bug`, `tests`, `good first issue`
- Body: Copy from ISSUES_TO_CREATE.md (Issue 1)

**Issue #2:**
- Title: `Create comprehensive MCP setup guide for Claude Code`
- Labels: `documentation`, `mcp`, `enhancement`
- Body: Copy from ISSUES_TO_CREATE.md (Issue 2)

**Issue #3:**
- Title: `Test MCP server with actual Claude Code instance`
- Labels: `testing`, `mcp`, `priority-high`
- Body: Copy from ISSUES_TO_CREATE.md (Issue 3)

**Issue #4:**
- Title: `Update all documentation for new monorepo structure`
- Labels: `documentation`, `breaking-change`
- Body: Copy from ISSUES_TO_CREATE.md (Issue 4)

---

## Step 2: Create GitHub Project Board (2 minutes)

### Steps:
1. Go to: https://github.com/yusufkaraaslan/Skill_Seekers/projects
2. Click **"New project"**
3. Choose **"Board"** template
4. Name it: **"Skill Seeker MCP Development"**
5. Click **"Create project"**

### Configure Board:

**Default columns:**
- Todo
- In Progress
- Done

**Add custom column (optional):**
- Testing

**Your board will look like:**
```
📋 Todo          | 🚧 In Progress  | 🧪 Testing  | ✅ Done
-----------------|-----------------│-------------|---------
Issue #1         |                 |             |
Issue #2         |                 |             |
Issue #3         |                 |             |
Issue #4         |                 |             |
```

---

## Step 3: Add Issues to Project

1. In your project board, click **"Add item"**
2. Search for your issues (#1, #2, #3, #4)
3. Add them to "Todo" column
4. Done!

---

## Step 4: Start Working

1. Move **Issue #1** to "In Progress"
2. Work on fixing tests
3. When done, move to "Done"
4. Repeat!

---

## Alternative: Quick Setup Script

```bash
# View issue templates
cat .github/ISSUES_TO_CREATE.md

# Get direct URLs for creating issues
.github/create_issues.sh
```

---

## Tips

### Linking Issues to PRs
When you create a PR, mention the issue:
```
Fixes #1
```

### Closing Issues Automatically
In commit message:
```
Fix test failures

Fixes #1
```

### Project Automation
GitHub Projects can auto-move issues:
- PR opened → Move to "In Progress"
- PR merged → Move to "Done"

Enable in Project Settings → Workflows

---

## Your Workflow

```
Daily:
1. Check Project Board
2. Pick task from "Todo"
3. Move to "In Progress"
4. Work on it
5. Create PR (mention issue number)
6. Move to "Testing"
7. Merge PR → Auto moves to "Done"
```

---

## Quick Links

- **Issues:** https://github.com/yusufkaraaslan/Skill_Seekers/issues
- **Projects:** https://github.com/yusufkaraaslan/Skill_Seekers/projects
- **New Issue:** https://github.com/yusufkaraaslan/Skill_Seekers/issues/new
- **New Project:** https://github.com/yusufkaraaslan/Skill_Seekers/projects/new

---

Need help? Check `.github/ISSUES_TO_CREATE.md` for full issue content!
