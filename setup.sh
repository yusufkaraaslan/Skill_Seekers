#!/bin/bash
# Skill Seekers - Global Installation & MCP Setup
# This script installs skill-seekers globally and configures MCP for AI agents

set -e  # Exit on error

echo "=========================================================="
echo "Skill Seekers - Global Installation & MCP Setup"
echo "=========================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global variables
HTTP_PORT=3000
HTTP_AGENTS=()
STDIO_AGENTS=()
SELECTED_AGENTS=()

# =============================================================================
# STEP 1: CHECK PYTHON VERSION
# =============================================================================
echo "Step 1: Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found${NC}"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${YELLOW}⚠ Warning: Python 3.10+ required${NC}"
    echo "Current version: $PYTHON_VERSION"
    exit 1
else
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
fi
echo ""

# =============================================================================
# STEP 2: INSTALL SKILL-SEEKERS GLOBALLY
# =============================================================================
echo "Step 2: Installing skill-seekers globally from PyPI..."
echo ""
echo "This will install skill-seekers and all dependencies:"
echo "  • skill-seekers (latest version)"
echo "  • mcp, fastmcp (MCP server support)"
echo "  • beautifulsoup4, requests, httpx (scraping)"
echo "  • GitPython, PyGithub (GitHub integration)"
echo "  • PyMuPDF (PDF support)"
echo "  • uvicorn (HTTP server)"
echo ""
read -p "Install globally? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing skill-seekers..."

    # Use python3 -m pip to ensure pip matches the python3 that passed the
    # version check. Bare 'pip3' can point to a different Python installation.
    if python3 -m pip install skill-seekers 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Installed successfully via python3 -m pip"
    else
        # Fallback with --break-system-packages (for system Python)
        echo "Standard install failed, trying with --break-system-packages..."
        python3 -m pip install skill-seekers --break-system-packages || {
            echo -e "${RED}❌ Failed to install skill-seekers${NC}"
            echo "Try manually: python3 -m pip install skill-seekers"
            exit 1
        }
        echo -e "${GREEN}✓${NC} Installed successfully with --break-system-packages"
    fi

    # Verify installation
    if command -v skill-seekers &> /dev/null; then
        INSTALLED_VERSION=$(skill-seekers --version 2>/dev/null || echo "unknown")
        echo -e "${GREEN}✓${NC} skill-seekers command available"
        echo "  Version: $INSTALLED_VERSION"
    else
        echo -e "${YELLOW}⚠${NC} skill-seekers command not found in PATH"
        echo "  Add ~/.local/bin to PATH: export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
else
    echo "Installation skipped"
    exit 0
fi
echo ""

# =============================================================================
# STEP 3: TEST MCP SERVER
# =============================================================================
echo "Step 3: Testing MCP server..."

# Test stdio mode
echo "  Testing stdio transport..."
timeout 3 python3 -m skill_seekers.mcp.server_fastmcp 2>/dev/null || {
    if [ $? -eq 124 ]; then
        echo -e "  ${GREEN}✓${NC} Stdio transport working"
    else
        echo -e "  ${YELLOW}⚠${NC} Stdio test inconclusive, but may still work"
    fi
}

# Test HTTP mode
echo "  Testing HTTP transport..."
if python3 -c "import uvicorn" 2>/dev/null; then
    # Start HTTP server in background
    python3 -m skill_seekers.mcp.server_fastmcp --transport http --port 8765 > /dev/null 2>&1 &
    HTTP_TEST_PID=$!
    sleep 2

    # Test health endpoint
    if curl -s http://127.0.0.1:8765/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} HTTP transport working (port 8765)"
        HTTP_AVAILABLE=true
    else
        echo -e "  ${YELLOW}⚠${NC} HTTP transport test failed (may need manual check)"
        HTTP_AVAILABLE=false
    fi

    # Cleanup
    kill $HTTP_TEST_PID 2>/dev/null || true
else
    echo -e "  ${YELLOW}⚠${NC} uvicorn not installed (HTTP transport unavailable)"
    echo "  Install with: pip3 install uvicorn"
    HTTP_AVAILABLE=false
fi
echo ""

# =============================================================================
# STEP 4: DETECT INSTALLED AI AGENTS
# =============================================================================
echo "Step 4: Detecting installed AI coding agents..."
echo ""

# Use Python agent detector
DETECTED_AGENTS=$(python3 -c "
from skill_seekers.mcp.agent_detector import AgentDetector
detector = AgentDetector()
agents = detector.detect_agents()
if agents:
    for agent in agents:
        print(f\"{agent['agent']}|{agent['name']}|{agent['config_path']}|{agent['transport']}\")
else:
    print('NONE')
" 2>/dev/null || echo "ERROR")

if [ "$DETECTED_AGENTS" = "ERROR" ]; then
    echo -e "${RED}❌ Error: Failed to run agent detector${NC}"
    echo "Falling back to manual configuration..."
    DETECTED_AGENTS="NONE"
fi

# Parse detected agents
if [ "$DETECTED_AGENTS" = "NONE" ]; then
    echo -e "${YELLOW}No AI coding agents detected.${NC}"
    echo ""
    echo "Supported agents:"
    echo "  • Claude Code (stdio)"
    echo "  • Cursor (HTTP)"
    echo "  • Windsurf (HTTP)"
    echo "  • VS Code + Cline extension (stdio)"
    echo "  • IntelliJ IDEA (HTTP)"
    echo ""
    echo "Manual configuration will be shown at the end."
else
    echo -e "${GREEN}Detected AI coding agents:${NC}"
    echo ""

    # Display detected agents
    IFS=$'\n'
    for agent_line in $DETECTED_AGENTS; do
        IFS='|' read -r agent_id agent_name config_path transport <<< "$agent_line"

        if [ "$transport" = "http" ]; then
            HTTP_AGENTS+=("$agent_id|$agent_name|$config_path")
            echo -e "  ${CYAN}✓${NC} $agent_name (HTTP transport)"
        else
            STDIO_AGENTS+=("$agent_id|$agent_name|$config_path")
            echo -e "  ${CYAN}✓${NC} $agent_name (stdio transport)"
        fi
        echo "    Config: $config_path"
    done
    unset IFS
fi
echo ""

# =============================================================================
# STEP 5: AUTO-CONFIGURE DETECTED AGENTS
# =============================================================================
if [ "$DETECTED_AGENTS" != "NONE" ]; then
    echo "Step 5: Configure detected agents"
    echo "=================================================="
    echo ""

    # Ask which agents to configure
    echo "Which agents would you like to configure?"
    echo ""
    echo "  1. All detected agents (recommended)"
    echo "  2. Select individual agents"
    echo "  3. Skip auto-configuration (manual setup)"
    echo ""
    read -p "Choose option (1-3): " -n 1 -r
    echo ""
    echo ""

    CONFIGURE_ALL=false
    CONFIGURE_SELECT=false

    case $REPLY in
        1)
            CONFIGURE_ALL=true
            echo "Configuring all detected agents..."
            ;;
        2)
            CONFIGURE_SELECT=true
            echo "Select agents to configure:"
            ;;
        3)
            echo "Skipping auto-configuration"
            echo "Manual configuration instructions will be shown at the end."
            ;;
        *)
            echo "Invalid option. Skipping auto-configuration."
            ;;
    esac
    echo ""

    # Build selection list
    if [ "$CONFIGURE_ALL" = true ] || [ "$CONFIGURE_SELECT" = true ]; then
        # Combine all agents
        ALL_AGENTS=("${STDIO_AGENTS[@]}" "${HTTP_AGENTS[@]}")

        if [ "$CONFIGURE_ALL" = true ]; then
            SELECTED_AGENTS=("${ALL_AGENTS[@]}")
        else
            # Individual selection
            for agent_line in "${ALL_AGENTS[@]}"; do
                IFS='|' read -r agent_id agent_name config_path <<< "$agent_line"
                read -p "  Configure $agent_name? (y/n) " -n 1 -r
                echo ""
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    SELECTED_AGENTS+=("$agent_line")
                fi
            done
            unset IFS
            echo ""
        fi

        # Configure selected agents
        if [ ${#SELECTED_AGENTS[@]} -eq 0 ]; then
            echo "No agents selected for configuration."
        else
            echo "Configuring ${#SELECTED_AGENTS[@]} agent(s)..."
            echo ""

            # Check if HTTP transport needed
            NEED_HTTP=false
            for agent_line in "${SELECTED_AGENTS[@]}"; do
                IFS='|' read -r agent_id agent_name config_path <<< "$agent_line"

                # Check if this is an HTTP agent
                for http_agent in "${HTTP_AGENTS[@]}"; do
                    if [ "$agent_line" = "$http_agent" ]; then
                        NEED_HTTP=true
                        break 2
                    fi
                done
            done
            unset IFS

            # Configure HTTP port if needed
            if [ "$NEED_HTTP" = true ]; then
                echo "HTTP transport required for some agents."
                read -p "Enter HTTP server port [default: 3000]: " PORT_INPUT
                if [ -n "$PORT_INPUT" ]; then
                    HTTP_PORT=$PORT_INPUT
                fi
                echo "Using port: $HTTP_PORT"
                echo ""
            fi

            # Configure each selected agent
            for agent_line in "${SELECTED_AGENTS[@]}"; do
                IFS='|' read -r agent_id agent_name config_path <<< "$agent_line"

                echo "Configuring $agent_name..."

                # Check if config already exists
                if [ -f "$config_path" ]; then
                    echo -e "  ${YELLOW}⚠ Config file already exists${NC}"

                    # Create backup
                    BACKUP_PATH="${config_path}.backup.$(date +%Y%m%d_%H%M%S)"
                    cp "$config_path" "$BACKUP_PATH"
                    echo -e "  ${GREEN}✓${NC} Backup created: $BACKUP_PATH"

                    # Check if skill-seeker already configured
                    if grep -q "skill-seeker" "$config_path" 2>/dev/null; then
                        echo -e "  ${YELLOW}⚠ skill-seeker already configured${NC}"
                        read -p "  Overwrite existing skill-seeker config? (y/n) " -n 1 -r
                        echo ""
                        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                            echo "  Skipping $agent_name"
                            continue
                        fi
                    fi
                fi

                # Generate config using Python (with global command)
                GENERATED_CONFIG=$(python3 -c "
from skill_seekers.mcp.agent_detector import AgentDetector
detector = AgentDetector()

# Use global skill-seekers command (not local repo path)
server_command = 'python3 -m skill_seekers.mcp.server_fastmcp'

config = detector.generate_config('$agent_id', server_command, $HTTP_PORT)
print(config)
" 2>/dev/null)

                if [ -n "$GENERATED_CONFIG" ]; then
                    # Create parent directory if needed
                    mkdir -p "$(dirname "$config_path")"

                    # Write or merge configuration
                    if [ -f "$config_path" ]; then
                        # Merge with existing config
                        python3 -c "
import json

# Read existing config
try:
    with open('$config_path', 'r') as f:
        existing = json.load(f)
except:
    existing = {}

# Parse new config
new = json.loads('''$GENERATED_CONFIG''')

# Merge (add skill-seeker, preserve others)
if 'mcpServers' not in existing:
    existing['mcpServers'] = {}
existing['mcpServers']['skill-seeker'] = new['mcpServers']['skill-seeker']

# Write back
with open('$config_path', 'w') as f:
    json.dump(existing, f, indent=2)
" 2>/dev/null || {
                            echo -e "  ${RED}✗${NC} Failed to merge config"
                            continue
                        }
                        echo -e "  ${GREEN}✓${NC} Merged with existing config"
                    else
                        # Write new config
                        echo "$GENERATED_CONFIG" > "$config_path"
                        echo -e "  ${GREEN}✓${NC} Config created"
                    fi

                    echo "  Location: $config_path"
                else
                    echo -e "  ${RED}✗${NC} Failed to generate config"
                fi
                echo ""
            done
            unset IFS
        fi
    fi
else
    echo "Step 5: Auto-configuration skipped (no agents detected)"
    echo ""
fi

# =============================================================================
# STEP 6: START HTTP SERVER (IF NEEDED)
# =============================================================================
if [ ${#SELECTED_AGENTS[@]} -gt 0 ]; then
    # Check if any selected agent needs HTTP
    NEED_HTTP_SERVER=false
    for agent_line in "${SELECTED_AGENTS[@]}"; do
        for http_agent in "${HTTP_AGENTS[@]}"; do
            if [ "$agent_line" = "$http_agent" ]; then
                NEED_HTTP_SERVER=true
                break 2
            fi
        done
    done

    if [ "$NEED_HTTP_SERVER" = true ]; then
        echo "Step 6: HTTP Server Setup"
        echo "=================================================="
        echo ""
        echo "Some configured agents require HTTP transport."
        echo "The MCP server needs to run in HTTP mode on port $HTTP_PORT."
        echo ""
        echo "Options:"
        echo "  1. Start server now (background process)"
        echo "  2. Show manual start command (start later)"
        echo "  3. Skip (I'll manage it myself)"
        echo ""
        read -p "Choose option (1-3): " -n 1 -r
        echo ""
        echo ""

        case $REPLY in
            1)
                echo "Starting HTTP server on port $HTTP_PORT..."

                # Start server in background
                nohup python3 -m skill_seekers.mcp.server_fastmcp --transport http --port $HTTP_PORT > /tmp/skill-seekers-mcp.log 2>&1 &
                SERVER_PID=$!

                sleep 2

                # Check if server started
                if curl -s http://127.0.0.1:$HTTP_PORT/health > /dev/null 2>&1; then
                    echo -e "${GREEN}✓${NC} HTTP server started (PID: $SERVER_PID)"
                    echo "  Health check: http://127.0.0.1:$HTTP_PORT/health"
                    echo "  Logs: /tmp/skill-seekers-mcp.log"
                    echo ""
                    echo -e "${YELLOW}Note:${NC} Server is running in background. To stop:"
                    echo "  kill $SERVER_PID"
                else
                    echo -e "${RED}✗${NC} Failed to start HTTP server"
                    echo "  Check logs: /tmp/skill-seekers-mcp.log"
                fi
                ;;
            2)
                echo "Manual start command:"
                echo ""
                echo -e "${GREEN}python3 -m skill_seekers.mcp.server_fastmcp --transport http --port $HTTP_PORT${NC}"
                echo ""
                echo "Or run in background:"
                echo -e "${GREEN}nohup python3 -m skill_seekers.mcp.server_fastmcp --transport http --port $HTTP_PORT > /tmp/skill-seekers-mcp.log 2>&1 &${NC}"
                ;;
            3)
                echo "Skipping HTTP server start"
                ;;
        esac
        echo ""
    else
        echo "Step 6: HTTP Server not needed (all agents use stdio)"
        echo ""
    fi
else
    echo "Step 6: HTTP Server setup skipped"
    echo ""
fi

# =============================================================================
# STEP 7: FINAL INSTRUCTIONS
# =============================================================================
echo "=========================================================="
echo "Setup Complete!"
echo "=========================================================="
echo ""

if [ ${#SELECTED_AGENTS[@]} -gt 0 ]; then
    echo -e "${GREEN}Next Steps:${NC}"
    echo ""
    echo "1. ${YELLOW}Restart your AI coding agent(s)${NC}"
    echo "   (Completely quit and reopen, don't just close window)"
    echo ""
    echo "2. ${YELLOW}Test the integration${NC}"
    echo "   Try commands like:"
    echo "   • ${CYAN}List all available configs${NC}"
    echo "   • ${CYAN}Generate config for React at https://react.dev${NC}"
    echo "   • ${CYAN}Scrape docs for configs/godot.json${NC}"
    echo ""

    # HTTP-specific instructions
    if [ "$NEED_HTTP_SERVER" = true ]; then
        echo "3. ${YELLOW}HTTP Server${NC}"
        echo "   Make sure HTTP server is running on port $HTTP_PORT"
        echo "   Test with: ${CYAN}curl http://127.0.0.1:$HTTP_PORT/health${NC}"
        echo ""
    fi
else
    echo -e "${YELLOW}Manual Configuration Required${NC}"
    echo ""
    echo "No agents were auto-configured. Here are configuration examples:"
    echo ""

    # Show stdio example
    echo "${CYAN}For Claude Code (stdio):${NC}"
    echo "File: ~/.config/claude-code/mcp.json"
    echo ""
    echo -e "${GREEN}{"
    echo "  \"mcpServers\": {"
    echo "    \"skill-seeker\": {"
    echo "      \"command\": \"python3\","
    echo "      \"args\": [\"-m\", \"skill_seekers.mcp.server_fastmcp\"]"
    echo "    }"
    echo "  }"
    echo -e "}${NC}"
    echo ""

    # Show HTTP example if available
    if [ "$HTTP_AVAILABLE" = true ]; then
        echo "${CYAN}For Cursor/Windsurf (HTTP):${NC}"
        echo ""
        echo "1. Start HTTP server:"
        echo "   ${GREEN}python3 -m skill_seekers.mcp.server_fastmcp --transport http --port 3000${NC}"
        echo ""
        echo "2. Add to agent config:"
        echo -e "${GREEN}{"
        echo "  \"mcpServers\": {"
        echo "    \"skill-seeker\": {"
        echo "      \"url\": \"http://localhost:3000/sse\""
        echo "    }"
        echo "  }"
        echo -e "}${NC}"
        echo ""
    fi
fi

echo "=========================================================="
echo "Available MCP Tools (18 total):"
echo "=========================================================="
echo ""
echo "${CYAN}Config Tools:${NC}"
echo "  • generate_config    - Create config files for any docs site"
echo "  • list_configs       - Show all available preset configs"
echo "  • validate_config    - Validate config file structure"
echo ""
echo "${CYAN}Scraping Tools:${NC}"
echo "  • estimate_pages     - Estimate page count before scraping"
echo "  • scrape_docs        - Scrape documentation and build skills"
echo "  • scrape_github      - Scrape GitHub repositories"
echo "  • scrape_pdf         - Extract content from PDF files"
echo "  • unified_scrape     - Multi-source scraping (docs + github + pdf)"
echo ""
echo "${CYAN}Packaging Tools:${NC}"
echo "  • package_skill      - Package skills into .zip files"
echo "  • upload_skill       - Upload skills to platforms"
echo "  • install_skill      - Complete workflow automation"
echo ""
echo "${CYAN}Splitting Tools:${NC}"
echo "  • split_config       - Split large documentation configs"
echo "  • generate_router    - Generate router/hub skills"
echo ""
echo "${CYAN}Config Source Tools:${NC}"
echo "  • fetch_config       - Download configs from remote sources"
echo "  • submit_config      - Submit configs to community"
echo "  • add_config_source  - Add custom config sources"
echo "  • list_config_sources - Show available config sources"
echo "  • remove_config_source - Remove config sources"
echo ""

echo "=========================================================="
echo "CLI Commands:"
echo "=========================================================="
echo "  ${GREEN}skill-seekers --help${NC}             # Show all commands"
echo "  ${GREEN}skill-seekers scrape${NC}             # Scrape documentation"
echo "  ${GREEN}skill-seekers github${NC}             # Scrape GitHub repos"
echo "  ${GREEN}skill-seekers unified${NC}            # Multi-source scraping"
echo "  ${GREEN}skill-seekers install${NC}            # One-command workflow"
echo ""

echo "=========================================================="
echo "Troubleshooting:"
echo "=========================================================="
echo "  • Test MCP server:"
echo "    ${CYAN}python3 -m skill_seekers.mcp.server_fastmcp${NC}"
echo ""
echo "  • Test HTTP server:"
echo "    ${CYAN}python3 -m skill_seekers.mcp.server_fastmcp --transport http --port 8000${NC}"
echo "    ${CYAN}curl http://127.0.0.1:8000/health${NC}"
echo ""
echo "  • View server logs (if HTTP):"
echo "    ${CYAN}tail -f /tmp/skill-seekers-mcp.log${NC}"
echo ""

echo "Happy skill creating! 🚀"
echo ""
