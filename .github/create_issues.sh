#!/bin/bash
# Script to create GitHub issues via web browser
# Since gh CLI is not available, we'll open browser to create issues

REPO="yusufkaraaslan/Skill_Seekers"
BASE_URL="https://github.com/${REPO}/issues/new"

echo "🚀 Creating GitHub Issues for Skill Seeker MCP Development"
echo "=========================================================="
echo ""
echo "Opening browser to create issues..."
echo "Please copy the content from .github/ISSUES_TO_CREATE.md"
echo ""

# Issue 1: Fix test failures
echo "📝 Issue 1: Fix 3 test failures"
echo "URL: ${BASE_URL}?labels=bug,tests,good+first+issue&title=Fix+3+test+failures+(warnings+vs+errors+handling)"
echo ""

# Issue 2: MCP setup guide
echo "📝 Issue 2: Create MCP setup guide"
echo "URL: ${BASE_URL}?labels=documentation,mcp,enhancement&title=Create+comprehensive+MCP+setup+guide+for+Claude+Code"
echo ""

# Issue 3: Test MCP server
echo "📝 Issue 3: Test MCP server"
echo "URL: ${BASE_URL}?labels=testing,mcp,priority-high&title=Test+MCP+server+with+actual+Claude+Code+instance"
echo ""

# Issue 4: Update documentation
echo "📝 Issue 4: Update documentation"
echo "URL: ${BASE_URL}?labels=documentation,breaking-change&title=Update+all+documentation+for+new+monorepo+structure"
echo ""

echo "=========================================================="
echo "📋 Instructions:"
echo "1. Click each URL above (or copy to browser)"
echo "2. Copy the issue body from .github/ISSUES_TO_CREATE.md"
echo "3. Paste into the issue description"
echo "4. Click 'Submit new issue'"
echo ""
echo "Or use this quick link to view all templates:"
echo "cat .github/ISSUES_TO_CREATE.md"
