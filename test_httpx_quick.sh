#!/bin/bash
# Quick Test - HTTPX Skill (Documentation Only, No GitHub)
# For faster testing without full C3.x analysis

set -e

echo "🚀 Quick HTTPX Skill Test (Docs Only)"
echo "======================================"
echo ""

# Simple config - docs only
CONFIG_FILE="configs/httpx_quick.json"

# Create quick config (docs only)
cat > "$CONFIG_FILE" << 'EOF'
{
  "name": "httpx_quick",
  "description": "HTTPX HTTP client for Python - Quick test version",
  "base_url": "https://www.python-httpx.org/",
  "selectors": {
    "main_content": "article.md-content__inner",
    "title": "h1",
    "code_blocks": "pre code"
  },
  "url_patterns": {
    "include": ["/quickstart/", "/advanced/", "/api/"],
    "exclude": ["/changelog/", "/contributing/"]
  },
  "categories": {
    "getting_started": ["quickstart", "install"],
    "api": ["api", "reference"],
    "advanced": ["async", "http2"]
  },
  "rate_limit": 0.3,
  "max_pages": 50
}
EOF

echo "✓ Created quick config (docs only, max 50 pages)"
echo ""

# Run scraper
echo "🔍 Scraping documentation..."
START_TIME=$(date +%s)

skill-seekers scrape --config "$CONFIG_FILE" --output output/httpx_quick

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "✅ Complete in ${DURATION}s"
echo ""
echo "📊 Results:"
echo "   Output: output/httpx_quick/"
echo "   SKILL.md: $(wc -l < output/httpx_quick/SKILL.md) lines"
echo "   References: $(find output/httpx_quick/references -name "*.md" 2>/dev/null | wc -l) files"
echo ""
echo "🔍 Preview:"
head -30 output/httpx_quick/SKILL.md
echo ""
echo "📦 Next: skill-seekers package output/httpx_quick/"
