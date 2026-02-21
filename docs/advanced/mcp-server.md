# MCP Server Setup Guide

> **Skill Seekers v3.1.0**  
> **Integrate with AI agents via Model Context Protocol**

---

## What is MCP?

MCP (Model Context Protocol) lets AI agents like Claude Code control Skill Seekers through natural language:

```
You: "Scrape the React documentation"
Claude: ▶️ scrape_docs({"url": "https://react.dev/"})
        ✅ Done! Created output/react/
```

---

## Installation

```bash
# Install with MCP support
pip install skill-seekers[mcp]

# Verify
skill-seekers-mcp --version
```

---

## Transport Modes

### stdio Mode (Default)

For Claude Code, VS Code + Cline:

```bash
skill-seekers-mcp
```

**Use when:**
- Running in Claude Code
- Direct integration with terminal-based agents
- Simple local setup

---

### HTTP Mode

For Cursor, Windsurf, HTTP clients:

```bash
# Start HTTP server
skill-seekers-mcp --transport http --port 8765

# Custom host
skill-seekers-mcp --transport http --host 0.0.0.0 --port 8765
```

**Use when:**
- IDE integration (Cursor, Windsurf)
- Remote access needed
- Multiple clients

---

## Claude Code Integration

### Automatic Setup

```bash
# In Claude Code, run:
/claude add-mcp-server skill-seekers
```

Or manually add to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "skill-seekers": {
      "command": "skill-seekers-mcp",
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "GITHUB_TOKEN": "ghp_..."
      }
    }
  }
}
```

### Usage

Once connected, ask Claude:

```
"List available configs"
"Scrape the Django documentation"
"Package output/react for Gemini"
"Enhance output/my-skill with security-focus workflow"
```

---

## Cursor IDE Integration

### Setup

1. Start MCP server:
```bash
skill-seekers-mcp --transport http --port 8765
```

2. In Cursor Settings → MCP:
   - Name: `skill-seekers`
   - URL: `http://localhost:8765`

### Usage

In Cursor chat:

```
"Create a skill from the current project"
"Analyze this codebase and generate a cursorrules file"
```

---

## Windsurf Integration

### Setup

1. Start MCP server:
```bash
skill-seekers-mcp --transport http --port 8765
```

2. In Windsurf Settings:
   - Add MCP server endpoint: `http://localhost:8765`

---

## Available Tools

26 tools organized by category:

### Core Tools (9)
- `list_configs` - List presets
- `generate_config` - Create config from URL
- `validate_config` - Check config
- `estimate_pages` - Page estimation
- `scrape_docs` - Scrape documentation
- `package_skill` - Package skill
- `upload_skill` - Upload to platform
- `enhance_skill` - AI enhancement
- `install_skill` - Complete workflow

### Extended Tools (9)
- `scrape_github` - GitHub repo
- `scrape_pdf` - PDF extraction
- `scrape_codebase` - Local code
- `unified_scrape` - Multi-source
- `detect_patterns` - Pattern detection
- `extract_test_examples` - Test examples
- `build_how_to_guides` - How-to guides
- `extract_config_patterns` - Config patterns
- `detect_conflicts` - Doc/code conflicts

### Config Sources (5)
- `add_config_source` - Register git source
- `list_config_sources` - List sources
- `remove_config_source` - Remove source
- `fetch_config` - Fetch configs
- `submit_config` - Submit configs

### Vector DB (4)
- `export_to_weaviate`
- `export_to_chroma`
- `export_to_faiss`
- `export_to_qdrant`

See [MCP Reference](../reference/MCP_REFERENCE.md) for full details.

---

## Common Workflows

### Workflow 1: Documentation Skill

```
User: "Create a skill from React docs"
Claude: ▶️ scrape_docs({"url": "https://react.dev/"})
        ⏳ Scraping...
        ✅ Created output/react/
        
        ▶️ package_skill({"skill_directory": "output/react/", "target": "claude"})
        ✅ Created output/react-claude.zip
        
        Skill ready! Upload to Claude?
```

### Workflow 2: GitHub Analysis

```
User: "Analyze the facebook/react repo"
Claude: ▶️ scrape_github({"repo": "facebook/react"})
        ⏳ Analyzing...
        ✅ Created output/react/
        
        ▶️ enhance_skill({"skill_directory": "output/react/", "workflow": "architecture-comprehensive"})
        ✅ Enhanced with architecture analysis
```

### Workflow 3: Multi-Platform Export

```
User: "Create Django skill for all platforms"
Claude: ▶️ scrape_docs({"config": "django"})
        ✅ Created output/django/
        
        ▶️ package_skill({"skill_directory": "output/django/", "target": "claude"})
        ▶️ package_skill({"skill_directory": "output/django/", "target": "gemini"})
        ▶️ package_skill({"skill_directory": "output/django/", "target": "openai"})
        ✅ Created packages for all platforms
```

---

## Configuration

### Environment Variables

Set in `~/.claude/mcp.json` or before starting server:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
export OPENAI_API_KEY=sk-...
export GITHUB_TOKEN=ghp_...
```

### Server Options

```bash
# Debug mode
skill-seekers-mcp --verbose

# Custom port
skill-seekers-mcp --port 8080

# Allow all origins (CORS)
skill-seekers-mcp --cors
```

---

## Security

### Local Only (stdio)

```bash
# Only accessible by local Claude Code
skill-seekers-mcp
```

### HTTP with Auth

```bash
# Use reverse proxy with auth
# nginx, traefik, etc.
```

### API Key Protection

```bash
# Don't hardcode keys
# Use environment variables
# Or secret management
```

---

## Troubleshooting

### "Server not found"

```bash
# Check if running
curl http://localhost:8765/health

# Restart
skill-seekers-mcp --transport http --port 8765
```

### "Tool not available"

```bash
# Check version
skill-seekers-mcp --version

# Update
pip install --upgrade skill-seekers[mcp]
```

### "Connection refused"

```bash
# Check port
lsof -i :8765

# Use different port
skill-seekers-mcp --port 8766
```

---

## See Also

- [MCP Reference](../reference/MCP_REFERENCE.md) - Complete tool reference
- [MCP Tools Deep Dive](mcp-tools.md) - Advanced usage
- [MCP Protocol](https://modelcontextprotocol.io/) - Official MCP docs
