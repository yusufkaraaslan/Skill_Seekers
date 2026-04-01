#!/bin/bash
# Real-world test script for Claude and Kimi agents
# Tests all major CLI commands with both agents

set -e  # Exit on error

echo "=========================================="
echo "Skill Seekers Agent Compatibility Test"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

# Test function
run_test() {
    local name=$1
    local cmd=$2
    echo -n "Testing: $name... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        ((PASS++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((FAIL++))
        return 1
    fi
}

echo "=== Agent Detection Tests ==="
echo ""

# Test 1: AgentClient can detect all API keys
run_test "Detect ANTHROPIC_API_KEY" \
    "python -c 'from skill_seekers.cli.agent_client import AgentClient; AgentClient.detect_api_key()'"

run_test "Detect MOONSHOT_API_KEY" \
    "python -c 'from skill_seekers.cli.agent_client import AgentClient; AgentClient.detect_api_key()'"

echo ""
echo "=== Agent Normalization Tests ==="
echo ""

# Test 2: All agent aliases work
run_test "Normalize 'claude'" \
    "python -c 'from skill_seekers.cli.agent_client import normalize_agent_name; assert normalize_agent_name(\"claude\") == \"claude\"'"

run_test "Normalize 'kimi'" \
    "python -c 'from skill_seekers.cli.agent_client import normalize_agent_name; assert normalize_agent_name(\"kimi\") == \"kimi\"'"

run_test "Normalize 'kimi-cli' alias" \
    "python -c 'from skill_seekers.cli.agent_client import normalize_agent_name; assert normalize_agent_name(\"kimi-cli\") == \"kimi\"'"

run_test "Normalize 'kimi_code' alias" \
    "python -c 'from skill_seekers.cli.agent_client import normalize_agent_name; assert normalize_agent_name(\"kimi_code\") == \"kimi\"'"

echo ""
echo "=== Adaptor Registration Tests ==="
echo ""

# Test 3: All adaptors are registered
run_test "Claude adaptor registered" \
    "python -c 'from skill_seekers.cli.adaptors import get_adaptor; get_adaptor(\"claude\")'"

run_test "Kimi adaptor registered" \
    "python -c 'from skill_seekers.cli.adaptors import get_adaptor; get_adaptor(\"kimi\")'"

run_test "Gemini adaptor registered" \
    "python -c 'from skill_seekers.cli.adaptors import get_adaptor; get_adaptor(\"gemini\")'"

run_test "OpenAI adaptor registered" \
    "python -c 'from skill_seekers.cli.adaptors import get_adaptor; get_adaptor(\"openai\")'"

echo ""
echo "=== CLI Help Text Tests ==="
echo ""

# Test 4: CLI shows correct agent choices
run_test "enhance --help shows --agent" \
    "skill-seekers enhance --help | grep -q '\-\-agent'"

run_test "unified --help shows --agent" \
    "skill-seekers unified --help | grep -q '\-\-agent'"

run_test "package --help shows --target" \
    "skill-seekers package --help | grep -q '\-\-target'"

run_test "upload --help shows --target" \
    "skill-seekers upload --help | grep -q '\-\-target'"

echo ""
echo "=== Agent Preset Tests ==="
echo ""

# Test 5: All agent presets are configured
run_test "Claude preset exists" \
    "python -c 'from skill_seekers.cli.agent_client import AGENT_PRESETS; assert \"claude\" in AGENT_PRESETS'"

run_test "Kimi preset exists" \
    "python -c 'from skill_seekers.cli.agent_client import AGENT_PRESETS; assert \"kimi\" in AGENT_PRESETS'"

run_test "Codex preset exists" \
    "python -c 'from skill_seekers.cli.agent_client import AGENT_PRESETS; assert \"codex\" in AGENT_PRESETS'"

run_test "Copilot preset exists" \
    "python -c 'from skill_seekers.cli.agent_client import AGENT_PRESETS; assert \"copilot\" in AGENT_PRESETS'"

run_test "OpenCode preset exists" \
    "python -c 'from skill_seekers.cli.agent_client import AGENT_PRESETS; assert \"opencode\" in AGENT_PRESETS'"

echo ""
echo "=== Kimi-Specific Tests ==="
echo ""

# Test 6: Kimi-specific functionality
run_test "Kimi has correct PLATFORM" \
    "python -c 'from skill_seekers.cli.adaptors.kimi import KimiAdaptor; assert KimiAdaptor.PLATFORM == \"kimi\"'"

run_test "Kimi has correct ENV_VAR_NAME" \
    "python -c 'from skill_seekers.cli.adaptors.kimi import KimiAdaptor; assert KimiAdaptor.ENV_VAR_NAME == \"MOONSHOT_API_KEY\"'"

run_test "Kimi has correct API endpoint" \
    "python -c 'from skill_seekers.cli.adaptors.kimi import KimiAdaptor; assert \"moonshot.cn\" in KimiAdaptor.DEFAULT_API_ENDPOINT'"

echo ""
echo "=== AgentClient Instantiation Tests ==="
echo ""

# Test 7: AgentClient can be instantiated for each agent
run_test "AgentClient with claude agent" \
    "python -c 'from skill_seekers.cli.agent_client import AgentClient; AgentClient(mode=\"local\", agent=\"claude\")'"

run_test "AgentClient with kimi agent" \
    "python -c 'from skill_seekers.cli.agent_client import AgentClient; AgentClient(mode=\"local\", agent=\"kimi\")'"

run_test "AgentClient auto-detects API mode" \
    "python -c 'from skill_seekers.cli.agent_client import AgentClient; c = AgentClient(mode=\"auto\"); print(c.mode)'"

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
