#!/usr/bin/env bash
#
# Bootstrap Skill Seekers into an Operational Skill for Claude Code
#
# Usage: ./scripts/bootstrap_skill.sh
# Output: output/skill-seekers/ (skill directory)
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_NAME="skill-seekers"
OUTPUT_DIR="$PROJECT_ROOT/output/$SKILL_NAME"
HEADER_FILE="$SCRIPT_DIR/skill_header.md"

echo "============================================"
echo "  Skill Seekers Bootstrap"
echo "============================================"

# Step 1: Sync dependencies
echo "Step 1: uv sync..."
command -v uv &> /dev/null || { echo "Error: uv not installed"; exit 1; }
cd "$PROJECT_ROOT"
uv sync --quiet
echo "✓ Done"

# Step 2: Run codebase analysis
echo "Step 2: Analyzing codebase..."
rm -rf "$OUTPUT_DIR" 2>/dev/null || true
uv run skill-seekers-codebase \
    --directory "$PROJECT_ROOT" \
    --output "$OUTPUT_DIR" \
    --depth deep \
    --ai-mode none 2>&1 | grep -E "^(INFO|✅)" || true
echo "✓ Done"

# Step 3: Prepend header to SKILL.md
echo "Step 3: Adding operational header..."
if [[ -f "$HEADER_FILE" ]]; then
    # Get auto-generated content (skip its frontmatter)
    AUTO_CONTENT=$(tail -n +6 "$OUTPUT_DIR/SKILL.md")
    # Combine: header + auto-generated
    cat "$HEADER_FILE" > "$OUTPUT_DIR/SKILL.md"
    echo "$AUTO_CONTENT" >> "$OUTPUT_DIR/SKILL.md"
    echo "✓ Done ($(wc -l < "$OUTPUT_DIR/SKILL.md") lines)"
else
    echo "Warning: $HEADER_FILE not found, using auto-generated only"
fi

echo ""
echo "============================================"
echo "  Bootstrap Complete!"
echo "============================================"
echo ""
echo "Output: $OUTPUT_DIR/"
echo "  - SKILL.md ($(wc -l < "$OUTPUT_DIR/SKILL.md") lines)"
echo "  - references/ (API docs, patterns, examples)"
echo ""
echo "Install to Claude Code:"
echo "  cp -r output/$SKILL_NAME ~/.claude/skills/"
echo ""
echo "Verify:"
echo "  ls ~/.claude/skills/$SKILL_NAME/SKILL.md"
echo ""
