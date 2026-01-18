# Complete MCP Setup Guide - MCP 2025 (v2.7.0)

Step-by-step guide to set up the Skill Seeker MCP server with 5 supported AI coding agents.

**Version 2.7.0 Highlights:**
- ✅ **MCP SDK v1.25.0** - Latest protocol support (upgraded from v1.18.0)
- ✅ **FastMCP Framework** - Modern, decorator-based server implementation
- ✅ **Dual Transport** - HTTP + stdio support (choose based on agent)
- ✅ **18 MCP Tools** - Expanded from 9 tools (enhance_skill + source management tools)
- ✅ **Multi-Agent Support** - Claude Code, Cursor, Windsurf, VS Code + Cline, IntelliJ IDEA
- ✅ **Auto-Configuration** - One-line setup with `./setup_mcp.sh`
- ✅ **Production Ready** - 700+ comprehensive tests, 100% pass rate

---

## Table of Contents

- [What's New in v2.4.0](#whats-new-in-v240)
- [Migration from v2.3.0](#migration-from-v230)
- [Prerequisites](#prerequisites)
- [Quick Start (Recommended)](#quick-start-recommended)
- [Manual Installation](#manual-installation)
- [Agent-Specific Configuration](#agent-specific-configuration)
- [Transport Modes](#transport-modes)
- [Verification](#verification)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## What's New in v2.4.0

### MCP 2025 Upgrade

**MCP SDK v1.25.0** (upgraded from v1.18.0):
- Latest MCP protocol specification
- Enhanced reliability and performance
- Better error handling and diagnostics

**FastMCP Framework**:
- Decorator-based tool registration (modern Python pattern)
- Simplified server implementation (2200 lines → 708 lines, 68% reduction)
- Modular tool architecture in `tools/` directory
- Easier to maintain and extend

**Dual Transport Support**:
- **stdio transport**: Default, backward compatible with Claude Code and VS Code + Cline
- **HTTP transport**: New, required for Cursor, Windsurf, and IntelliJ IDEA
- Automatic transport detection via agent_detector.py

### New Features

**18 MCP Tools** (expanded from 9):

**Config Tools (3):**
- `generate_config` - Generate config for any documentation site
- `list_configs` - List all available preset configurations
- `validate_config` - Validate config file structure

**Scraping Tools (4):**
- `estimate_pages` - Estimate page count before scraping
- `scrape_docs` - Scrape documentation and build skill
- `scrape_github` - Scrape GitHub repositories
- `scrape_pdf` - Extract content from PDF files

**Packaging Tools (4):**
- `package_skill` - Package skill (supports multi-platform via `target` parameter)
- `upload_skill` - Upload to LLM platform (claude, gemini, openai)
- `enhance_skill` - AI-enhance SKILL.md (NEW - local or API mode)
- `install_skill` - Complete install workflow

**Splitting Tools (2):**
- `split_config` - Split large documentation configs
- `generate_router` - Generate router/hub skills

**Source Tools (5 - NEW):**
- `fetch_config` - Fetch configs from API or git sources
- `submit_config` - Submit new configs to community
- `add_config_source` - Register private git repositories as config sources
- `list_config_sources` - List all registered config sources
- `remove_config_source` - Remove registered config sources

**Multi-Agent Support**:
- **5 supported agents** with automatic detection
- **Auto-configuration script** (`./setup_mcp.sh`) detects and configures all agents
- **Transport auto-selection** based on agent requirements

### Infrastructure

**HTTP Server Features**:
- Health check endpoint: `http://localhost:8000/health`
- SSE endpoint: `http://localhost:8000/sse`
- Configurable host and port
- Production-ready with uvicorn

**New Server Implementation**:
- `server_fastmcp.py` - New FastMCP-based server (recommended)
- `server.py` - Legacy server (deprecated, maintained for compatibility)

---

## Migration from v2.3.0

If you're upgrading from v2.3.0, follow these steps:

### 1. Update Dependencies

```bash
# Navigate to repository
cd /path/to/Skill_Seekers

# Update package
pip install -e . --upgrade

# Verify MCP SDK version
python3 -c "import mcp; print(mcp.__version__)"
# Should show: 1.25.0 or higher
```

### 2. Update Configuration

**For Claude Code (no changes required):**
```json
{
  "mcpServers": {
    "skill-seeker": {
      "command": "python",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp"]
    }
  }
}
```

**For HTTP-based agents (Cursor, Windsurf, IntelliJ):**

Old config (v2.3.0 - DEPRECATED):
```json
{
  "command": "python",
  "args": ["-m", "skill_seekers.mcp.server_fastmcp", "--http", "--port", "3000"]
}
```

New config (v2.4.0+):
```json
# For stdio transport (Claude Code, VS Code + Cline):
{
  "type": "stdio",
  "command": "python3",
  "args": ["-m", "skill_seekers.mcp.server_fastmcp"]
}

# For HTTP transport (Cursor, Windsurf, IntelliJ):
# Run server separately:
# python3 -m skill_seekers.mcp.server_fastmcp --transport http --port 3000
#
# Then configure agent with URL:
{
  "url": "http://localhost:3000/sse"
}
```

The HTTP server now runs separately and agents connect via URL instead of spawning the server.

### 3. Start HTTP Server (if using HTTP agents)

```bash
# Start HTTP server on port 3000
python -m skill_seekers.mcp.server_fastmcp --http --port 3000

# Or use custom host/port
python -m skill_seekers.mcp.server_fastmcp --http --host 0.0.0.0 --port 8080
```

### 4. Test Configuration

In any connected agent:
```
List all available MCP tools
```

You should see 18 tools (up from 9 in v2.3.0).

### 5. Optional: Run Auto-Configuration

The easiest way to update all agents:

```bash
./setup_mcp.sh
```

This will:
- Detect all installed agents
- Configure stdio agents (Claude Code, VS Code + Cline)
- Show HTTP server setup instructions for HTTP agents (Cursor, Windsurf, IntelliJ)

---

## Prerequisites

### Required Software

1. **Python 3.10 or higher**
   ```bash
   python3 --version
   # Should show: Python 3.10.x or higher
   ```

2. **AI Coding Agent** (at least one):
   - **Claude Code** - Download from [claude.ai/code](https://claude.ai/code)
   - **Cursor** - Download from [cursor.sh](https://cursor.sh)
   - **Windsurf** - Download from [codeium.com/windsurf](https://codeium.com/windsurf)
   - **VS Code + Cline** - Install [Cline extension](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev)
   - **IntelliJ IDEA** - Download from [jetbrains.com](https://www.jetbrains.com/idea/)

3. **Skill Seeker repository** (for source installation):
   ```bash
   git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
   cd Skill_Seekers
   ```

   Or install from PyPI:
   ```bash
   pip install skill-seekers
   ```

### System Requirements

- **Operating System**: macOS, Linux, or Windows (WSL)
- **Disk Space**: 100 MB for dependencies + space for generated skills
- **Network**: Internet connection for documentation scraping

---

## Quick Start (Recommended)

The fastest way to set up MCP for all detected agents:

### 1. Run Auto-Configuration Script

```bash
# Navigate to repository
cd /path/to/Skill_Seekers

# Run setup script
./setup_mcp.sh
```

### 2. What the Script Does

1. **Detects Python version** - Ensures Python 3.10+
2. **Installs dependencies** - Installs MCP SDK v1.25.0, FastMCP, uvicorn
3. **Detects agents** - Automatically finds installed AI coding agents
4. **Configures stdio agents** - Auto-configures Claude Code and VS Code + Cline
5. **Shows HTTP setup** - Provides commands for Cursor, Windsurf, IntelliJ IDEA

### 3. Follow On-Screen Instructions

For **stdio agents** (Claude Code, VS Code + Cline):
- Restart the agent
- Configuration is automatic

For **HTTP agents** (Cursor, Windsurf, IntelliJ):
- Start HTTP server: `python -m skill_seekers.mcp.server_fastmcp --http --port 3000`
- Add server URL to agent settings (instructions provided by script)
- Restart the agent

### 4. Verify Setup

In your agent:
```
List all available MCP tools
```

You should see 17 Skill Seeker tools.

---

## Manual Installation

If you prefer manual setup or the auto-configuration script doesn't work:

### Step 1: Install Python Dependencies

```bash
# Navigate to repository root
cd /path/to/Skill_Seekers

# Install package in editable mode (includes all dependencies)
pip install -e .

# Or install specific dependencies manually
pip install "mcp>=1.25,<2" requests beautifulsoup4 uvicorn
```

**Expected output:**
```
Successfully installed mcp-1.25.0 fastmcp-... uvicorn-... requests-2.31.0 beautifulsoup4-4.12.3
```

### Step 2: Verify Installation

```bash
# Test stdio mode
timeout 3 python3 -m skill_seekers.mcp.server_fastmcp || echo "Server OK (timeout expected)"

# Test HTTP mode
python3 -c "import uvicorn; print('HTTP support available')"
```

### Step 3: Note Your Repository Path

```bash
# Get absolute path
pwd

# Example output: /Users/username/Projects/Skill_Seekers
# or: /home/username/Skill_Seekers
```

**Save this path** - you'll need it for configuration!

---

## Agent-Specific Configuration

### Claude Code (stdio transport)

**Config Location:**
- **macOS**: `~/.claude.json`
- **Linux**: `~/.claude.json`
- **Windows**: `~/.claude.json`

**Configuration:**

```json
{
  "mcpServers": {
    "skill-seeker": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp"],
      "env": {}
    }
  }
}
```

**With custom Python path:**
```json
{
  "mcpServers": {
    "skill-seeker": {
      "type": "stdio",
      "command": "/usr/local/bin/python3.11",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp"],
      "env": {}
    }
  }
}
```

**Setup Steps:**
1. Edit config: `nano ~/.claude.json`
3. Paste configuration above
4. Save and exit
5. Restart Claude Code

---

### Cursor (HTTP transport)

**Config Location:**
- **macOS**: `~/Library/Application Support/Cursor/mcp_settings.json`
- **Linux**: `~/.cursor/mcp_settings.json`
- **Windows**: `%APPDATA%\Cursor\mcp_settings.json`

**Step 1: Start HTTP Server**

```bash
# Terminal 1 - Run HTTP server
python -m skill_seekers.mcp.server_fastmcp --http --port 3000

# Should show:
# INFO: Started server process
# INFO: Uvicorn running on http://127.0.0.1:3000
```

**Step 2: Configure Cursor**

```json
{
  "mcpServers": {
    "skill-seeker": {
      "url": "http://localhost:3000/sse"
    }
  }
}
```

**Step 3: Verify Connection**

```bash
# Check health endpoint
curl http://localhost:3000/health

# Should return: {"status": "ok"}
```

**Step 4: Restart Cursor**

---

### Windsurf (HTTP transport)

**Config Location:**
- **macOS**: `~/Library/Application Support/Windsurf/mcp_config.json`
- **Linux**: `~/.windsurf/mcp_config.json`
- **Windows**: `%APPDATA%\Windsurf\mcp_config.json`

**Step 1: Start HTTP Server**

```bash
# Terminal 1 - Run HTTP server
python -m skill_seekers.mcp.server_fastmcp --http --port 3001

# Use different port if Cursor is using 3000
```

**Step 2: Configure Windsurf**

```json
{
  "mcpServers": {
    "skill-seeker": {
      "url": "http://localhost:3001/sse"
    }
  }
}
```

**Step 3: Restart Windsurf**

---

### VS Code + Cline Extension (stdio transport)

**Config Location:**
- **macOS**: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- **Linux**: `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- **Windows**: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

**Configuration:**

```json
{
  "mcpServers": {
    "skill-seeker": {
      "command": "python",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp"]
    }
  }
}
```

**Setup Steps:**
1. Install Cline extension in VS Code
2. Open Cline settings (Cmd/Ctrl + Shift + P → "Cline: Settings")
3. Navigate to MCP settings
4. Add configuration above
5. Reload VS Code window

---

### IntelliJ IDEA (HTTP transport)

**Config Location:**
- **macOS**: `~/Library/Application Support/JetBrains/IntelliJIdea2024.3/mcp.xml`
- **Linux**: `~/.config/JetBrains/IntelliJIdea2024.3/mcp.xml`
- **Windows**: `%APPDATA%\JetBrains\IntelliJIdea2024.3\mcp.xml`

**Step 1: Start HTTP Server**

```bash
# Terminal 1 - Run HTTP server
python -m skill_seekers.mcp.server_fastmcp --http --port 3002
```

**Step 2: Configure IntelliJ**

Edit `mcp.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<application>
  <component name="MCPSettings">
    <servers>
      <server>
        <name>skill-seeker</name>
        <url>http://localhost:3002/sse</url>
      </server>
    </servers>
  </component>
</application>
```

**Step 3: Restart IntelliJ IDEA**

---

## Transport Modes

### stdio Transport (Default)

**How it works:**
- Agent spawns MCP server as subprocess
- Communication via stdin/stdout
- Server lifecycle managed by agent

**Advantages:**
- Automatic process management
- No port conflicts
- Zero configuration after setup

**Supported Agents:**
- Claude Code
- VS Code + Cline

**Usage:**
```json
{
  "command": "python",
  "args": ["-m", "skill_seekers.mcp.server_fastmcp"]
}
```

No additional steps needed - agent handles everything.

---

### HTTP Transport (New)

**How it works:**
- MCP server runs as HTTP server
- Agents connect via SSE (Server-Sent Events)
- Single server can support multiple agents

**Advantages:**
- Multiple agents can share one server
- Easier debugging (can test with curl)
- Production-ready with uvicorn

**Supported Agents:**
- Cursor
- Windsurf
- IntelliJ IDEA

**Usage:**

**Step 1: Start HTTP Server**

```bash
# Default (port 8000)
python -m skill_seekers.mcp.server_fastmcp --http

# Custom port
python -m skill_seekers.mcp.server_fastmcp --http --port 3000

# Custom host and port
python -m skill_seekers.mcp.server_fastmcp --http --host 0.0.0.0 --port 8080

# Debug mode
python -m skill_seekers.mcp.server_fastmcp --http --log-level DEBUG
```

**Step 2: Configure Agent**

```json
{
  "url": "http://localhost:8000/sse"
}
```

**Step 3: Test Endpoints**

```bash
# Health check
curl http://localhost:8000/health
# Returns: {"status": "ok"}

# SSE endpoint (agent connects here)
curl http://localhost:8000/sse
# Returns SSE stream
```

---

## Verification

### Step 1: Check MCP Server Loaded

In your AI coding agent, type:
```
List all available MCP tools
```

You should see **17 Skill Seeker tools**:

**Config Tools:**
- `generate_config` - Generate config for documentation site
- `list_configs` - List available preset configs
- `validate_config` - Validate config structure

**Scraping Tools:**
- `estimate_pages` - Estimate page count
- `scrape_docs` - Scrape documentation
- `scrape_github` - Scrape GitHub repositories
- `scrape_pdf` - Extract PDF content

**Packaging Tools:**
- `package_skill` - Package skill (multi-platform support)
- `upload_skill` - Upload to LLM platform
- `enhance_skill` - AI-enhance SKILL.md
- `install_skill` - Complete install workflow

**Splitting Tools:**
- `split_config` - Split large configs
- `generate_router` - Generate router skills

**Source Tools:**
- `fetch_config` - Fetch configs from sources
- `submit_config` - Submit new configs
- `add_config_source` - Register git sources
- `list_config_sources` - List config sources
- `remove_config_source` - Remove sources

### Step 2: Test a Simple Command

```
List all available configs
```

**Expected response:**
```
Available configurations:
1. godot - Godot Engine documentation
2. react - React framework
3. vue - Vue.js framework
4. django - Django web framework
5. fastapi - FastAPI Python framework
6. kubernetes - Kubernetes documentation
7. steam-economy-complete - Steam Economy API
... (24 total configs)
```

### Step 3: Test Config Generation

```
Generate a config for Tailwind CSS at https://tailwindcss.com/docs
```

**Expected response:**
```
✅ Config created: configs/tailwind.json
```

### Step 4: Test HTTP Server (if using)

```bash
# Health check
curl http://localhost:8000/health

# Should return:
{"status": "ok"}

# Check SSE endpoint
curl -N http://localhost:8000/sse

# Should stream SSE events
```

---

## Usage Examples

### Example 1: Generate Skill from Scratch

```
User: Generate config for Svelte docs at https://svelte.dev/docs

Agent: ✅ Config created: configs/svelte.json

User: Estimate pages for configs/svelte.json

Agent: 📊 Estimated pages: 150
       Recommended max_pages: 180

User: Scrape docs using configs/svelte.json

Agent: ✅ Skill created at output/svelte/

User: Package skill at output/svelte/

Agent: ✅ Created: output/svelte.zip
       Ready to upload to Claude!
```

### Example 2: Use Private Config Repository

```
User: Add config source named "team" with git URL https://github.com/myorg/skill-configs.git

Agent: ✅ Source registered: team
       Type: github
       Priority: 100

User: List config sources

Agent: Registered sources:
       1. team (github, enabled, priority: 100)
       2. official (api, enabled, priority: 200)

User: Fetch config "nextjs" from source "team"

Agent: ✅ Config downloaded: configs/nextjs.json
       Source: team (https://github.com/myorg/skill-configs.git)

User: Scrape docs using configs/nextjs.json

Agent: [Scraping starts...]
```

### Example 3: Multi-Source Workflow

```
User: List config sources

Agent: No sources registered. Use add_config_source to add sources.

User: Add config source "company-internal" with git URL git@gitlab.company.com:configs/ai-skills.git

Agent: ✅ Source registered: company-internal
       Type: gitlab
       Token: GITLAB_TOKEN (environment variable)

User: Fetch config "internal-api" from "company-internal"

Agent: ✅ Config downloaded: configs/internal-api.json

User: Validate configs/internal-api.json

Agent: ✅ Config is valid
       - Base URL: https://docs.company.com/api/
       - Max pages: 1000
       - Categories: 5

User: Scrape docs using configs/internal-api.json

Agent: [Scraping internal documentation...]
```

### Example 4: Multi-Platform Support

Skill Seekers supports packaging and uploading to 4 LLM platforms: Claude AI, Google Gemini, OpenAI ChatGPT, and Generic Markdown.

```
User: Scrape docs using configs/react.json

Agent: ✅ Skill created at output/react/

User: Package skill at output/react/ with target gemini

Agent: ✅ Packaged for Google Gemini
       Saved to: output/react-gemini.tar.gz
       Format: tar.gz (Gemini-specific format)

User: Package skill at output/react/ with target openai

Agent: ✅ Packaged for OpenAI ChatGPT
       Saved to: output/react-openai.zip
       Format: ZIP with vector store

User: Enhance skill at output/react/ with target gemini and mode api

Agent: ✅ Enhanced with Gemini 2.0 Flash
       Backup: output/react/SKILL.md.backup
       Enhanced: output/react/SKILL.md

User: Upload output/react-gemini.tar.gz with target gemini

Agent: ✅ Uploaded to Google Gemini
       Skill ID: gemini_12345
       Access at: https://aistudio.google.com/
```

**Available platforms:**
- `claude` (default) - ZIP format, Anthropic Skills API
- `gemini` - tar.gz format, Google Files API
- `openai` - ZIP format, OpenAI Assistants API + Vector Store
- `markdown` - ZIP format, generic export (no upload)

---

## Troubleshooting

### Issue: MCP Server Not Loading

**Symptoms:**
- Skill Seeker tools don't appear in agent
- No response when asking about configs

**Solutions:**

1. **Check configuration file exists:**
   ```bash
   # Claude Code
   cat ~/Library/Application\ Support/Claude/mcp.json

   # Cursor
   cat ~/Library/Application\ Support/Cursor/mcp_settings.json
   ```

2. **Verify Python path:**
   ```bash
   which python3
   # Should show: /usr/bin/python3 or similar
   ```

3. **Test server manually:**

   **For stdio:**
   ```bash
   timeout 3 python3 -m skill_seekers.mcp.server_fastmcp
   # Should exit cleanly or timeout (both OK)
   ```

   **For HTTP:**
   ```bash
   python3 -m skill_seekers.mcp.server_fastmcp --http --port 8000
   # Should show: Uvicorn running on http://127.0.0.1:8000
   ```

4. **Check agent logs:**

   **Claude Code:**
   - macOS: `~/Library/Logs/Claude/`
   - Linux: `~/.config/claude-code/logs/`

   **Cursor:**
   - macOS: `~/Library/Logs/Cursor/`
   - Linux: `~/.cursor/logs/`

5. **Completely restart agent:**
   - Quit agent (don't just close window)
   - Kill any background processes: `pkill -f skill_seekers`
   - Reopen agent

---

### Issue: "skill-seeker · ✘ failed" Connection Error

**Symptoms:**
- MCP server shows as "failed" when running `/mcp` in Claude Code
- Cannot access Skill Seeker tools
- Error: "ModuleNotFoundError: No module named 'skill_seekers'"

**Solution 1: Install Package and MCP Dependencies**

```bash
# Navigate to Skill Seekers directory
cd /path/to/Skill_Seekers

# Install package with MCP dependencies
pip3 install -e ".[mcp]"
```

**Solution 2: Fix ~/.claude.json Configuration**

Common configuration problems:
- Using `python` instead of `python3` (doesn't exist on macOS)
- Missing `"type": "stdio"` field
- Missing `"cwd"` field for proper working directory
- Using deprecated `server` instead of `server_fastmcp`

**Correct configuration:**

```json
{
  "mcpServers": {
    "skill-seeker": {
      "type": "stdio",
      "command": "python3",
      "args": [
        "-m",
        "skill_seekers.mcp.server_fastmcp"
      ],
      "cwd": "/full/path/to/Skill_Seekers",
      "env": {}
    }
  }
}
```

**Verify Installation:**

```bash
# Test module import
python3 -c "from skill_seekers.mcp import server_fastmcp; print('✓ Module OK')"

# Test server startup
cd /path/to/Skill_Seekers
python3 -m skill_seekers.mcp.server_fastmcp
# Should start without errors (Ctrl+C to stop)
```

**Validate JSON Configuration:**

```bash
# Check JSON syntax
python3 -m json.tool < ~/.claude.json > /dev/null && echo "✓ JSON valid"
```

**Restart Claude Code:**

After fixing configuration:
1. Quit Claude Code completely (don't just close window)
2. Kill any background processes: `pkill -f skill_seekers`
3. Reopen Claude Code
4. Test with `/mcp` command

---

### Issue: "ModuleNotFoundError: No module named 'mcp'"

**Solution:**

```bash
# Install package
pip install -e .

# Or install dependencies manually
pip install "mcp>=1.25,<2" requests beautifulsoup4 uvicorn
```

**Verify installation:**
```bash
python3 -c "import mcp; print(mcp.__version__)"
# Should show: 1.25.0 or higher
```

---

### Issue: HTTP Server Not Starting

**Symptoms:**
- `python -m skill_seekers.mcp.server_fastmcp --http` fails
- "ModuleNotFoundError: No module named 'uvicorn'"

**Solution:**

```bash
# Install uvicorn
pip install uvicorn

# Or install with extras
pip install -e ".[mcp]"
```

**Verify uvicorn:**
```bash
python3 -c "import uvicorn; print('OK')"
```

---

### Issue: Port Already in Use

**Symptoms:**
- "Address already in use" when starting HTTP server

**Solution:**

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
python -m skill_seekers.mcp.server_fastmcp --http --port 8001
```

---

### Issue: Tools Appear But Don't Work

**Symptoms:**
- Tools listed but commands fail
- "Error executing tool" messages

**Solutions:**

1. **Check working directory:**

   For stdio agents, ensure package is installed:
   ```bash
   pip install -e .
   ```

2. **Verify CLI tools exist:**
   ```bash
   python3 -m skill_seekers.cli.doc_scraper --help
   python3 -m skill_seekers.cli.package_skill --help
   ```

3. **Test tool directly:**
   ```bash
   # Test in Python
   python3 -c "from skill_seekers.mcp.tools import list_configs_impl; print('OK')"
   ```

4. **Check HTTP server logs** (if using HTTP transport):
   ```bash
   python -m skill_seekers.mcp.server_fastmcp --http --log-level DEBUG
   ```

---

### Issue: Agent Can't Connect to HTTP Server

**Symptoms:**
- Agent shows connection error
- curl to /health fails

**Solutions:**

1. **Verify server is running:**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "ok"}
   ```

2. **Check firewall:**
   ```bash
   # macOS
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

   # Linux
   sudo ufw status
   ```

3. **Test with different host:**
   ```bash
   # Try 0.0.0.0 instead of 127.0.0.1
   python -m skill_seekers.mcp.server_fastmcp --http --host 0.0.0.0
   ```

4. **Check agent config URL:**
   ```json
   {
     "url": "http://localhost:8000/sse"  // Not /health!
   }
   ```

---

### Issue: Slow or Hanging Operations

**Solutions:**

1. **Check rate limit in config:**
   - Default: 0.5 seconds
   - Increase if needed: 1.0 or 2.0 seconds

2. **Use smaller max_pages for testing:**
   ```
   Generate config with max_pages=20 for testing
   ```

3. **Check network connection:**
   ```bash
   curl -I https://docs.example.com
   ```

4. **Enable debug logging:**
   ```bash
   python -m skill_seekers.mcp.server_fastmcp --http --log-level DEBUG
   ```

---

## Advanced Configuration

### Custom Environment Variables

**For stdio agents:**

```json
{
  "mcpServers": {
    "skill-seeker": {
      "command": "python",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "GITHUB_TOKEN": "ghp_...",
        "GITLAB_TOKEN": "glpat-...",
        "PYTHONPATH": "/custom/path"
      }
    }
  }
}
```

**For HTTP server:**

```bash
# Set environment variables before starting
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...
python -m skill_seekers.mcp.server_fastmcp --http
```

---

### Multiple Python Versions

If you have multiple Python versions:

**Find Python path:**
```bash
which python3.11
# /usr/local/bin/python3.11
```

**Use in config:**
```json
{
  "mcpServers": {
    "skill-seeker": {
      "command": "/usr/local/bin/python3.11",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp"]
    }
  }
}
```

---

### Virtual Environment

To use a Python virtual environment:

```bash
# Create venv
cd /path/to/Skill_Seekers
python3 -m venv venv
source venv/bin/activate

# Install package
pip install -e .

# Get Python path
which python3
# Copy this path
```

**Use in config:**
```json
{
  "mcpServers": {
    "skill-seeker": {
      "command": "/path/to/Skill_Seekers/venv/bin/python3",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp"]
    }
  }
}
```

---

### Running HTTP Server as Service

**systemd (Linux):**

Create `/etc/systemd/system/skill-seeker-mcp.service`:

```ini
[Unit]
Description=Skill Seeker MCP HTTP Server
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/Skill_Seekers
ExecStart=/usr/bin/python3 -m skill_seekers.mcp.server_fastmcp --http --port 8000
Restart=on-failure
Environment="ANTHROPIC_API_KEY=sk-ant-..."

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable skill-seeker-mcp
sudo systemctl start skill-seeker-mcp
sudo systemctl status skill-seeker-mcp
```

**macOS (launchd):**

Create `~/Library/LaunchAgents/com.skillseeker.mcp.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.skillseeker.mcp</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>-m</string>
        <string>skill_seekers.mcp.server_fastmcp</string>
        <string>--http</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/Skill_Seekers</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/skill-seeker-mcp.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/skill-seeker-mcp.error.log</string>
</dict>
</plist>
```

**Load:**
```bash
launchctl load ~/Library/LaunchAgents/com.skillseeker.mcp.plist
launchctl start com.skillseeker.mcp
```

---

### Debug Mode

Enable verbose logging for troubleshooting:

**stdio transport:**
```json
{
  "mcpServers": {
    "skill-seeker": {
      "command": "python",
      "args": [
        "-u",
        "-m",
        "skill_seekers.mcp.server_fastmcp"
      ],
      "env": {
        "DEBUG": "1"
      }
    }
  }
}
```

**HTTP transport:**
```bash
python -m skill_seekers.mcp.server_fastmcp --http --log-level DEBUG
```

---

## Complete Example Configurations

### Minimal (Recommended for Most Users)

**Claude Code (stdio):**
```json
{
  "mcpServers": {
    "skill-seeker": {
      "command": "python",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp"]
    }
  }
}
```

**Cursor (HTTP):**

Start server:
```bash
python -m skill_seekers.mcp.server_fastmcp --http --port 3000
```

Config:
```json
{
  "mcpServers": {
    "skill-seeker": {
      "url": "http://localhost:3000/sse"
    }
  }
}
```

---

### With API Keys and Custom Tokens

**Claude Code:**
```json
{
  "mcpServers": {
    "skill-seeker": {
      "command": "python",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-your-key-here",
        "GITHUB_TOKEN": "ghp_your-token-here"
      }
    }
  }
}
```

**HTTP Server:**
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export GITHUB_TOKEN=ghp_your-token-here
python -m skill_seekers.mcp.server_fastmcp --http --port 3000
```

---

### Multiple Agents Sharing HTTP Server

**Start one HTTP server:**
```bash
python -m skill_seekers.mcp.server_fastmcp --http --port 8000
```

**Configure all HTTP agents to use it:**

**Cursor** (`~/Library/Application Support/Cursor/mcp_settings.json`):
```json
{
  "mcpServers": {
    "skill-seeker": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

**Windsurf** (`~/Library/Application Support/Windsurf/mcp_config.json`):
```json
{
  "mcpServers": {
    "skill-seeker": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

**IntelliJ** (`~/Library/Application Support/JetBrains/IntelliJIdea2024.3/mcp.xml`):
```xml
<component name="MCPSettings">
  <servers>
    <server>
      <name>skill-seeker</name>
      <url>http://localhost:8000/sse</url>
    </server>
  </servers>
</component>
```

All three agents now share the same MCP server instance!

---

## End-to-End Workflow

### Complete Setup and First Skill

```bash
# 1. Install from source
cd ~/Projects
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd Skill_Seekers

# 2. Run auto-configuration
./setup_mcp.sh

# 3. Follow prompts
# - Installs dependencies
# - Detects agents
# - Configures automatically

# 4. For HTTP agents, start server
python -m skill_seekers.mcp.server_fastmcp --http --port 3000

# 5. Restart your AI coding agent

# 6. Test in agent:
```

**In your agent:**
```
User: List all available configs
User: Scrape docs using configs/react.json with max 50 pages
User: Package skill at output/react/
```

**Result:** `output/react.zip` ready to upload!

---

## Next Steps

After successful setup:

1. **Try preset configs:**
   - React: `scrape docs using configs/react.json`
   - Vue: `scrape docs using configs/vue.json`
   - Django: `scrape docs using configs/django.json`

2. **Create custom configs:**
   - `generate config for [framework] at [url]`

3. **Set up private config sources:**
   - `add config source "team" with git URL https://github.com/myorg/configs.git`

4. **Test with small limits first:**
   - Use `max_pages` parameter: `scrape docs using configs/test.json with max 20 pages`

5. **Explore enhancement:**
   - Use `--enhance-local` flag for AI-powered SKILL.md improvement

---

## Getting Help

- **Documentation**:
  - [README.md](../README.md) - User guide
  - [CLAUDE.md](CLAUDE.md) - Technical architecture
  - [ENHANCEMENT.md](ENHANCEMENT.md) - Enhancement guide
  - [UPLOAD_GUIDE.md](UPLOAD_GUIDE.md) - Upload instructions

- **Issues**: [GitHub Issues](https://github.com/yusufkaraaslan/Skill_Seekers/issues)

- **Agent Detection**: See [agent_detector.py](../src/skill_seekers/mcp/agent_detector.py)

- **Auto-Configuration**: See [setup_mcp.sh](../setup_mcp.sh)

---

## Quick Reference Card

```
SETUP:
1. Install: pip install -e .
2. Configure: ./setup_mcp.sh
3. Restart agent

VERIFY:
- "List all available MCP tools" (should show 18 tools)
- "List all available configs" (should show 24 configs)

GENERATE SKILL:
1. "Generate config for [name] at [url]"
2. "Estimate pages for configs/[name].json"
3. "Scrape docs using configs/[name].json"
4. "Package skill at output/[name]/"

PRIVATE CONFIGS:
1. "Add config source [name] with git URL [url]"
2. "List config sources"
3. "Fetch config [name] from [source]"

TRANSPORT MODES:
- stdio: Claude Code, VS Code + Cline (automatic)
- HTTP: Cursor, Windsurf, IntelliJ (requires server)

START HTTP SERVER:
python -m skill_seekers.mcp.server_fastmcp --http --port 3000

TROUBLESHOOTING:
- Check: cat ~/.config/claude-code/mcp.json
- Test stdio: timeout 3 python -m skill_seekers.mcp.server_fastmcp
- Test HTTP: curl http://localhost:8000/health
- Logs (Claude Code): ~/Library/Logs/Claude/
- Kill servers: pkill -f skill_seekers
```

---

Happy skill creating! 🚀
