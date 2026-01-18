# Multi-Agent Auto-Configuration Guide

The Skill Seeker MCP server now supports automatic detection and configuration of multiple AI coding agents. This guide explains how to use the enhanced `setup_mcp.sh` script to configure all your installed AI agents at once.

## Supported Agents

The setup script automatically detects and configures:

| Agent | Transport | Config Path (macOS) |
|-------|-----------|---------------------|
| **Claude Code** | stdio | `~/.claude.json` |
| **Cursor** | HTTP | `~/Library/Application Support/Cursor/mcp_settings.json` |
| **Windsurf** | HTTP | `~/Library/Application Support/Windsurf/mcp_config.json` |
| **VS Code + Cline** | stdio | `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` |
| **IntelliJ IDEA** | HTTP (XML) | `~/Library/Application Support/JetBrains/IntelliJIdea2024.3/mcp.xml` |

**Note:** Paths vary by operating system. The script automatically detects the correct paths for Linux, macOS, and Windows.

## Quick Start

### One-Command Setup

```bash
# Run the setup script
./setup_mcp.sh
```

The script will:
1. ✅ Check Python version (3.10+ recommended)
2. ✅ Verify repository path
3. ✅ Install dependencies (with virtual environment option)
4. ✅ Test both stdio and HTTP transports
5. ✅ **Detect installed AI agents automatically**
6. ✅ **Configure all detected agents**
7. ✅ **Start HTTP server if needed**
8. ✅ Validate configurations
9. ✅ Provide next steps

### What's New in Multi-Agent Setup

**Automatic Agent Detection:**
- Scans your system for installed AI coding agents
- Shows which agents were found and their transport types
- Allows you to configure all agents or select individually

**Smart Configuration:**
- Creates backups before modifying existing configs
- Merges with existing configurations (preserves other MCP servers)
- Detects if skill-seeker is already configured
- Uses appropriate transport (stdio or HTTP) for each agent

**HTTP Server Management:**
- Automatically starts HTTP server if HTTP-based agents detected
- Configurable port (default: 3000)
- Background process with health monitoring
- Optional systemd service support (future)

## Workflow Examples

### Example 1: Configure All Detected Agents

```bash
$ ./setup_mcp.sh

Step 5: Detecting installed AI coding agents...

Detected AI coding agents:

  ✓ Claude Code (stdio transport)
    Config: /home/user/.config/claude-code/mcp.json
  ✓ Cursor (HTTP transport)
    Config: /home/user/.cursor/mcp_settings.json

Step 6: Configure detected agents
==================================================

Which agents would you like to configure?

  1. All detected agents (recommended)
  2. Select individual agents
  3. Skip auto-configuration (manual setup)

Choose option (1-3): 1

Configuring all detected agents...

HTTP transport required for some agents.
Enter HTTP server port [default: 3000]: 3000
Using port: 3000

Configuring Claude Code...
  ✓ Config created
  Location: /home/user/.config/claude-code/mcp.json

Configuring Cursor...
  ⚠ Config file already exists
  ✓ Backup created: /home/user/.cursor/mcp_settings.json.backup.20251223_143022
  ✓ Merged with existing config
  Location: /home/user/.cursor/mcp_settings.json

Step 7: HTTP Server Setup
==================================================

Some configured agents require HTTP transport.
The MCP server needs to run in HTTP mode on port 3000.

Options:
  1. Start server now (background process)
  2. Show manual start command (start later)
  3. Skip (I'll manage it myself)

Choose option (1-3): 1

Starting HTTP server on port 3000...
✓ HTTP server started (PID: 12345)
  Health check: http://127.0.0.1:3000/health
  Logs: /tmp/skill-seekers-mcp.log

Setup Complete!
```

### Example 2: Select Individual Agents

```bash
$ ./setup_mcp.sh

Step 6: Configure detected agents
==================================================

Which agents would you like to configure?

  1. All detected agents (recommended)
  2. Select individual agents
  3. Skip auto-configuration (manual setup)

Choose option (1-3): 2

Select agents to configure:
  Configure Claude Code? (y/n) y
  Configure Cursor? (y/n) n
  Configure Windsurf? (y/n) y

Configuring 2 agent(s)...
```

### Example 3: Manual Configuration (No Agents Detected)

```bash
$ ./setup_mcp.sh

Step 5: Detecting installed AI coding agents...

No AI coding agents detected.

Supported agents:
  • Claude Code (stdio)
  • Cursor (HTTP)
  • Windsurf (HTTP)
  • VS Code + Cline extension (stdio)
  • IntelliJ IDEA (HTTP)

Manual configuration will be shown at the end.

[... setup continues ...]

Manual Configuration Required

No agents were auto-configured. Here are configuration examples:

For Claude Code (stdio):
File: ~/.config/claude-code/mcp.json

{
  "mcpServers": {
    "skill-seeker": {
      "command": "python3",
      "args": [
        "/path/to/Skill_Seekers/src/skill_seekers/mcp/server_fastmcp.py"
      ],
      "cwd": "/path/to/Skill_Seekers"
    }
  }
}

For Cursor/Windsurf (HTTP):

1. Start HTTP server:
   python3 -m skill_seekers.mcp.server_fastmcp --http --port 3000

2. Add to agent config:
{
  "mcpServers": {
    "skill-seeker": {
      "url": "http://localhost:3000/sse"
    }
  }
}
```

## Configuration Details

### Stdio Transport (Claude Code, VS Code + Cline)

**Generated Config:**
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

**Features:**
- Each agent gets its own server process
- No network configuration needed
- More secure (local only)
- Faster startup (~100ms)

### HTTP Transport (Cursor, Windsurf, IntelliJ)

**Generated Config (JSON):**
```json
{
  "mcpServers": {
    "skill-seeker": {
      "url": "http://localhost:3000/sse"
    }
  }
}
```

**Generated Config (XML for IntelliJ):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<application>
  <component name="MCPSettings">
    <servers>
      <server>
        <name>skill-seeker</name>
        <url>http://localhost:3000</url>
        <enabled>true</enabled>
      </server>
    </servers>
  </component>
</application>
```

**Features:**
- Single server process for all agents
- Network-based (can be remote)
- Health monitoring endpoint
- Requires server to be running

### Config Merging Strategy

The setup script **preserves existing MCP server configurations**:

**Before (existing config):**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
  }
}
```

**After (merged config):**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    },
    "skill-seeker": {
      "command": "python",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp"]
    }
  }
}
```

**Safety Features:**
- ✅ Creates timestamped backups before modifying
- ✅ Detects if skill-seeker already exists
- ✅ Asks for confirmation before overwriting
- ✅ Validates JSON after writing

## HTTP Server Management

### Starting the Server

**Option 1: During setup (recommended)**
```bash
./setup_mcp.sh
# Choose option 1 when prompted for HTTP server
```

**Option 2: Manual start**
```bash
# Foreground (for testing)
python3 -m skill_seekers.mcp.server_fastmcp --http --port 3000

# Background (for production)
nohup python3 -m skill_seekers.mcp.server_fastmcp --http --port 3000 > /tmp/skill-seekers-mcp.log 2>&1 &
```

### Monitoring the Server

**Health Check:**
```bash
curl http://localhost:3000/health
```

**Response:**
```json
{
  "status": "healthy",
  "server": "skill-seeker-mcp",
  "version": "2.1.1",
  "transport": "http",
  "endpoints": {
    "health": "/health",
    "sse": "/sse",
    "messages": "/messages/"
  }
}
```

**View Logs:**
```bash
tail -f /tmp/skill-seekers-mcp.log
```

**Stop Server:**
```bash
# If you know the PID
kill 12345

# Find and kill
pkill -f "skill_seekers.mcp.server_fastmcp"
```

## Troubleshooting

### Agent Not Detected

**Problem:** Your agent is installed but not detected.

**Solution:**
1. Check if the agent's config directory exists:
   ```bash
   # Claude Code (macOS)
   ls ~/Library/Application\ Support/Claude/

   # Cursor (Linux)
   ls ~/.cursor/
   ```

2. If directory doesn't exist, the agent may not be installed or uses a different path.

3. Manual configuration:
   - Note the actual config path
   - Create the directory if needed
   - Use manual configuration examples from setup script output

### Config Merge Failed

**Problem:** Error merging with existing config.

**Solution:**
1. Check the backup file:
   ```bash
   cat ~/.config/claude-code/mcp.json.backup.20251223_143022
   ```

2. Manually edit the config:
   ```bash
   nano ~/.config/claude-code/mcp.json
   ```

3. Ensure valid JSON:
   ```bash
   jq empty ~/.config/claude-code/mcp.json
   ```

### HTTP Server Won't Start

**Problem:** HTTP server fails to start on configured port.

**Solution:**
1. Check if port is already in use:
   ```bash
   lsof -i :3000
   ```

2. Kill process using the port:
   ```bash
   lsof -ti:3000 | xargs kill -9
   ```

3. Use a different port:
   ```bash
   python3 -m skill_seekers.mcp.server_fastmcp --http --port 8080
   ```

4. Update agent configs with new port.

### Agent Can't Connect to HTTP Server

**Problem:** HTTP-based agent shows connection errors.

**Solution:**
1. Verify server is running:
   ```bash
   curl http://localhost:3000/health
   ```

2. Check server logs:
   ```bash
   tail -f /tmp/skill-seekers-mcp.log
   ```

3. Restart the server:
   ```bash
   pkill -f skill_seekers.mcp.server_fastmcp
   python3 -m skill_seekers.mcp.server_fastmcp --http --port 3000 &
   ```

4. Check firewall settings (if remote connection).

## Advanced Usage

### Custom HTTP Port

```bash
# During setup, enter custom port when prompted
Enter HTTP server port [default: 3000]: 8080

# Or modify config manually after setup
{
  "mcpServers": {
    "skill-seeker": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

### Virtual Environment vs System Install

**Virtual Environment (Recommended):**
```bash
# Setup creates/activates venv automatically
./setup_mcp.sh

# Config uses Python module execution
"command": "python",
"args": ["-m", "skill_seekers.mcp.server_fastmcp"]
```

**System Install:**
```bash
# Install globally via pip
pip install skill-seekers

# Config uses CLI command
"command": "skill-seekers",
"args": ["mcp"]
```

### Multiple HTTP Agents on Different Ports

If you need different ports for different agents:

1. Start multiple server instances:
   ```bash
   # Server 1 for Cursor
   python3 -m skill_seekers.mcp.server_fastmcp --http --port 3000 &

   # Server 2 for Windsurf
   python3 -m skill_seekers.mcp.server_fastmcp --http --port 3001 &
   ```

2. Configure each agent with its own port:
   ```json
   // Cursor config
   {"url": "http://localhost:3000/sse"}

   // Windsurf config
   {"url": "http://localhost:3001/sse"}
   ```

**Note:** Usually not necessary - one HTTP server can handle multiple clients.

### Programmatic Configuration

Use the Python API directly:

```python
from skill_seekers.mcp.agent_detector import AgentDetector

detector = AgentDetector()

# Detect all installed agents
agents = detector.detect_agents()
print(f"Found {len(agents)} agents:")
for agent in agents:
    print(f"  - {agent['name']} ({agent['transport']})")

# Generate config for specific agent
config = detector.generate_config(
    agent_id="cursor",
    server_command="skill-seekers mcp",
    http_port=3000
)
print(config)

# Check if agent is installed
if detector.is_agent_installed("claude-code"):
    print("Claude Code detected!")
```

## Testing the Setup

After setup completes:

### 1. Restart Your Agent(s)

**Important:** Completely quit and reopen (don't just close window).

### 2. Test Basic Functionality

Try these commands in your agent:

```
List all available configs
```

Expected: List of 24+ preset configurations

```
Generate config for React at https://react.dev
```

Expected: Generated React configuration

```
Validate configs/godot.json
```

Expected: Validation results

### 3. Test Advanced Features

```
Estimate pages for configs/react.json
```

```
Scrape documentation using configs/vue.json with max 20 pages
```

```
Package the skill at output/react/
```

### 4. Verify HTTP Transport (if applicable)

```bash
# Check server health
curl http://localhost:3000/health

# Expected output:
{
  "status": "healthy",
  "server": "skill-seeker-mcp",
  "version": "2.1.1",
  "transport": "http"
}
```

## Migration from Old Setup

If you previously used `setup_mcp.sh`, the new version is fully backward compatible:

**Old behavior:**
- Only configured Claude Code
- Manual stdio configuration
- No HTTP support

**New behavior:**
- Detects and configures multiple agents
- Automatic transport selection
- HTTP server management
- Config merging (preserves existing servers)

**Migration steps:**
1. Run `./setup_mcp.sh`
2. Choose "All detected agents"
3. Your existing configs will be backed up and merged
4. No manual intervention needed

## Next Steps

After successful setup:

1. **Read the MCP Setup Guide**: [docs/MCP_SETUP.md](MCP_SETUP.md)
2. **Learn HTTP Transport**: [docs/HTTP_TRANSPORT.md](HTTP_TRANSPORT.md)
3. **Explore Agent Detection**: [src/skill_seekers/mcp/agent_detector.py](../src/skill_seekers/mcp/agent_detector.py)
4. **Try the Quick Start**: [QUICKSTART.md](../QUICKSTART.md)

## Related Documentation

- [MCP Setup Guide](MCP_SETUP.md) - Detailed MCP integration guide
- [HTTP Transport](HTTP_TRANSPORT.md) - HTTP transport documentation
- [Agent Detector API](../src/skill_seekers/mcp/agent_detector.py) - Python API reference
- [README](../README.md) - Main documentation

## Support

For issues or questions:
- **GitHub Issues**: https://github.com/yusufkaraaslan/Skill_Seekers/issues
- **GitHub Discussions**: https://github.com/yusufkaraaslan/Skill_Seekers/discussions
- **MCP Documentation**: https://modelcontextprotocol.io/

## Changelog

### Version 2.1.2+ (Current)
- ✅ Multi-agent auto-detection
- ✅ Smart configuration merging
- ✅ HTTP server management
- ✅ Backup and safety features
- ✅ Cross-platform support (Linux, macOS, Windows)
- ✅ 5 supported agents (Claude Code, Cursor, Windsurf, VS Code + Cline, IntelliJ)
- ✅ Automatic transport selection (stdio vs HTTP)
- ✅ Interactive and non-interactive modes
