#!/bin/bash
# Check if Chinese translations are in sync with English originals
# Usage: ./scripts/check_translation_sync.sh

set -e

echo "🔍 Checking translation sync..."
echo ""

MISSING=0
OUT_OF_SYNC=0

# Find all English docs (excluding zh-CN and archive)
find docs -name "*.md" -not -path "docs/zh-CN/*" -not -path "docs/archive/*" | while read -r en_file; do
    # Calculate corresponding Chinese file path
    rel_path="${en_file#docs/}"
    zh_file="docs/zh-CN/$rel_path"
    
    # Check if Chinese version exists
    if [ ! -f "$zh_file" ]; then
        echo "❌ Missing: $zh_file (source: $en_file)"
        MISSING=$((MISSING + 1))
        continue
    fi
    
    # Get last modification times
    en_mtime=$(git log -1 --format=%ct "$en_file" 2>/dev/null || stat -c %Y "$en_file" 2>/dev/null || echo 0)
    zh_mtime=$(git log -1 --format=%ct "$zh_file" 2>/dev/null || stat -c %Y "$zh_file" 2>/dev/null || echo 0)
    
    # Check if English is newer
    if [ "$en_mtime" -gt "$zh_mtime" ]; then
        echo "⚠️  Out of sync: $zh_file (English updated more recently)"
        OUT_OF_SYNC=$((OUT_OF_SYNC + 1))
    fi
done

echo ""

# Summary
TOTAL_EN=$(find docs -name "*.md" -not -path "docs/zh-CN/*" -not -path "docs/archive/*" | wc -l)
TOTAL_ZH=$(find docs/zh-CN -name "*.md" 2>/dev/null | wc -l)

echo "📊 Summary:"
echo "   English docs: $TOTAL_EN"
echo "   Chinese docs: $TOTAL_ZH"

if [ "$MISSING" -gt 0 ]; then
    echo "   ❌ Missing translations: $MISSING"
fi

if [ "$OUT_OF_SYNC" -gt 0 ]; then
    echo "   ⚠️  Out of sync: $OUT_OF_SYNC"
fi

if [ "$MISSING" -eq 0 ] && [ "$OUT_OF_SYNC" -eq 0 ]; then
    echo ""
    echo "✅ All translations in sync!"
    exit 0
else
    echo ""
    echo "❌ Translation sync issues found"
    exit 1
fi
