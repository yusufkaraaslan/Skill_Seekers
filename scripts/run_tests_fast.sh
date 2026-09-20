#!/usr/bin/env bash
# Three exhaustive, disjoint test phases with bounded workers and memory.
# Requires the dev dependencies plus pytest-xdist and pytest-timeout.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_PYTHON="${TEST_PYTHON:-python}"
TEST_WORKERS="${TEST_WORKERS:-2}"
TEST_MAX_RSS_MB="${TEST_MAX_RSS_MB:-4096}"

run_tests() {
    "$TEST_PYTHON" "$SCRIPT_DIR/run_tests_safe.py" --max-rss-mb "$TEST_MAX_RSS_MB" -- tests/ "$@"
}

echo "Phase 1: Fast unit tests ($TEST_WORKERS workers)"
run_tests -n "$TEST_WORKERS" --dist=loadfile \
    -m "not slow and not integration and not e2e and not network and not serial and not mcp_only" \
    -q --timeout=120 "$@"

echo "Phase 2: Serial, integration and E2E tests"
run_tests -m "(integration or e2e or slow or network or serial) and not mcp_only" \
    -v --timeout=300 "$@"

echo "Phase 3: MCP tests"
run_tests -m "mcp_only" -v --timeout=180 "$@"

echo "All phases passed."
