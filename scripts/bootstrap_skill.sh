#!/usr/bin/env bash
# Build Skill Seekers' operational skill. Tests can use isolated source/output dirs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_DIR="$PROJECT_ROOT"
OUTPUT_DIR="$PROJECT_ROOT/output/skill-seekers"
BOOTSTRAP_PYTHON="python3"
ENHANCE_LEVEL=2   # the shipped skill is AI-enhanced; tests pass --enhance-level 0
SYNC=true
while (( $# )); do
    case "$1" in
        --source) SOURCE_DIR="$2"; shift 2 ;;
        --output) OUTPUT_DIR="$2"; shift 2 ;;
        --python) BOOTSTRAP_PYTHON="$2"; shift 2 ;;
        --enhance-level) ENHANCE_LEVEL="$2"; shift 2 ;;
        --no-sync) SYNC=false; shift ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
    esac
done

[[ -d "$SOURCE_DIR" ]] || { echo "Source directory does not exist: $SOURCE_DIR" >&2; exit 1; }
SOURCE_DIR="$(cd "$SOURCE_DIR" && pwd)"
mkdir -p "$(dirname "$OUTPUT_DIR")"
OUTPUT_DIR="$(cd "$(dirname "$OUTPUT_DIR")" && pwd)/$(basename "$OUTPUT_DIR")"
if [[ -d "$OUTPUT_DIR" ]]; then OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"; fi
[[ "$SOURCE_DIR/" != "${OUTPUT_DIR%/}/"* ]] || {
    echo "Output must not replace the source directory or one of its parents" >&2; exit 2;
}
if $SYNC; then
    command -v uv >/dev/null || { echo "Install uv or use --no-sync --python PATH" >&2; exit 1; }
    (cd "$PROJECT_ROOT" && uv sync --quiet)
fi
TEMP_OUTPUT=$(mktemp -d "${OUTPUT_DIR}.tmp.XXXXXX")
trap 'rm -rf -- "$TEMP_OUTPUT"' EXIT

echo "Analyzing $SOURCE_DIR"
if $SYNC; then
    (cd "$PROJECT_ROOT" && uv run --no-sync skill-seekers create "$SOURCE_DIR" \
        --name skill-seekers --output "$TEMP_OUTPUT" --enhance-level "$ENHANCE_LEVEL")
else
    "$BOOTSTRAP_PYTHON" -m skill_seekers.cli.create_command "$SOURCE_DIR" \
        --name skill-seekers --output "$TEMP_OUTPUT" --enhance-level "$ENHANCE_LEVEL"
fi
[[ -s "$TEMP_OUTPUT/SKILL.md" ]] || { echo "Analysis did not produce SKILL.md" >&2; exit 1; }

# Stream the generated body; do not hold the entire skill in a shell variable.
cat "$SCRIPT_DIR/skill_header.md" > "$TEMP_OUTPUT/merged.md"
awk 'BEGIN { delimiters=0 } /^---$/ && delimiters<2 { delimiters++; next } delimiters>=2 { print }' \
    "$TEMP_OUTPUT/SKILL.md" >> "$TEMP_OUTPUT/merged.md"
mv "$TEMP_OUTPUT/merged.md" "$TEMP_OUTPUT/SKILL.md"
grep -q '^name:' "$TEMP_OUTPUT/SKILL.md"
grep -q '^description:' "$TEMP_OUTPUT/SKILL.md"

# Replace output only after successful analysis and validation.
if [[ -e "$OUTPUT_DIR" ]]; then
    BACKUP_DIR=$(mktemp -d "${OUTPUT_DIR}.backup.XXXXXX")
    mv "$OUTPUT_DIR" "$BACKUP_DIR/skill"
    if ! mv "$TEMP_OUTPUT" "$OUTPUT_DIR"; then
        mv "$BACKUP_DIR/skill" "$OUTPUT_DIR"
        rmdir "$BACKUP_DIR"
        exit 1
    fi
    rm -rf -- "$BACKUP_DIR"
else
    mv "$TEMP_OUTPUT" "$OUTPUT_DIR"
fi
echo "Bootstrap complete: $OUTPUT_DIR/SKILL.md ($(wc -l < "$OUTPUT_DIR/SKILL.md") lines)"
