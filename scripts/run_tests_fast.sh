#!/bin/bash
# Fast parallel test runner for local development.
# Phase 1: Fast unit tests with xdist (~2-3 min)
# Phase 2: Serial/Integration/E2E tests (~10-15 min)
# Phase 3: MCP tests (if MCP installed)
set -e

MCP_SKIP="--ignore=tests/test_mcp_server.py --ignore=tests/test_mcp_fastmcp.py --ignore=tests/test_install_skill_e2e.py --ignore=tests/test_unified_mcp_integration.py --ignore=tests/test_mcp_git_sources.py --ignore=tests/test_mcp_vector_dbs.py --ignore=tests/test_mcp_workflow_tools.py --ignore=tests/test_server_fastmcp_http.py"

INTEGRATION_SKIP="--ignore=tests/test_real_world_fastmcp.py --ignore=tests/test_issue_277_discord_e2e.py --ignore=tests/test_browser_renderer.py --ignore=tests/test_integration_adaptors.py --ignore=tests/test_bootstrap_skill_e2e.py --ignore=tests/test_git_sources_e2e.py --ignore=tests/test_marketplace_publisher.py --ignore=tests/test_sync_config_e2e.py --ignore=tests/test_estimate_pages.py"

echo "=== Phase 1: Fast Unit Tests (parallel) ==="
pytest tests/ -n auto --dist=loadfile \
  ${MCP_SKIP} ${INTEGRATION_SKIP} \
  -m "not slow and not integration and not e2e and not network and not serial" \
  -q --timeout=120 "$@"

echo ""
echo "=== Phase 2: Serial/Integration/E2E Tests ==="
pytest tests/ \
  -m "integration or e2e or slow or network or serial" \
  -v --timeout=300 "$@"

echo ""
echo "=== Phase 3: MCP Tests ==="
python -c "import mcp" 2>/dev/null && {
    pytest tests/test_mcp_server.py tests/test_mcp_fastmcp.py \
      tests/test_mcp_git_sources.py tests/test_mcp_vector_dbs.py \
      tests/test_mcp_workflow_tools.py tests/test_unified_mcp_integration.py \
      tests/test_server_fastmcp_http.py tests/test_install_skill.py \
      tests/test_install_skill_e2e.py \
      -v --timeout=180 "$@"
} || echo "MCP not installed — skipping Phase 3"

echo ""
echo "All phases complete."
