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
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed"
    echo ""
    echo "Install uv:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  # or"
    echo "  pip install uv"
    echo ""
    exit 1
fi
cd "$PROJECT_ROOT"
uv sync --quiet
echo "✓ Done"

# Step 2: Run codebase analysis
echo "Step 2: Analyzing codebase..."
rm -rf "$OUTPUT_DIR" 2>/dev/null || true
uv run skill-seekers analyze \
    --directory "$PROJECT_ROOT" \
    --output "$OUTPUT_DIR" 2>&1 | grep -E "^(INFO|✅)" || true
echo "✓ Done"

# Step 3: Prepend header to SKILL.md
echo "Step 3: Adding operational header..."
if [[ -f "$HEADER_FILE" ]]; then
    # Detect end of frontmatter dynamically
    # Look for second occurrence of '---'
    FRONTMATTER_END=$(grep -n '^---$' "$OUTPUT_DIR/SKILL.md" | sed -n '2p' | cut -d: -f1)

    if [[ -n "$FRONTMATTER_END" ]]; then
        # Skip frontmatter + blank line
        AUTO_CONTENT=$(tail -n +$((FRONTMATTER_END + 2)) "$OUTPUT_DIR/SKILL.md")
    else
        # Fallback to line 6 if no frontmatter found
        AUTO_CONTENT=$(tail -n +6 "$OUTPUT_DIR/SKILL.md")
    fi

    # Combine: header + auto-generated
    cat "$HEADER_FILE" > "$OUTPUT_DIR/SKILL.md"
    echo "$AUTO_CONTENT" >> "$OUTPUT_DIR/SKILL.md"
    echo "✓ Done ($(wc -l < "$OUTPUT_DIR/SKILL.md") lines)"
else
    echo "Warning: $HEADER_FILE not found, using auto-generated only"
fi

# Step 4: Validate merged SKILL.md
echo "Step 4: Validating SKILL.md..."
if [[ -f "$OUTPUT_DIR/SKILL.md" ]]; then
    # Check file not empty
    if [[ ! -s "$OUTPUT_DIR/SKILL.md" ]]; then
        echo "❌ Error: SKILL.md is empty"
        exit 1
    fi

    # Check frontmatter exists
    if ! head -1 "$OUTPUT_DIR/SKILL.md" | grep -q '^---$'; then
        echo "⚠️  Warning: SKILL.md missing frontmatter delimiter"
    fi

    # Check required fields
    if ! grep -q '^name:' "$OUTPUT_DIR/SKILL.md"; then
        echo "❌ Error: SKILL.md missing 'name:' field"
        exit 1
    fi

    if ! grep -q '^description:' "$OUTPUT_DIR/SKILL.md"; then
        echo "❌ Error: SKILL.md missing 'description:' field"
        exit 1
    fi

    echo "✓ Validation passed"
else
    echo "❌ Error: SKILL.md not found"
    exit 1
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
