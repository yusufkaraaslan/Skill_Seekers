# Skill Seeker MCP Server

Model Context Protocol (MCP) server for Skill Seeker - Generate Claude AI skills from documentation websites directly from Claude Code.

## What is MCP?

MCP (Model Context Protocol) allows Claude Code to use external tools. This server provides tools for:
- Generating config files for documentation sites
- Estimating page counts before scraping
- Scraping documentation and building skills
- Packaging skills for upload
- Managing configurations

## Installation

### 1. Install Dependencies

```bash
cd mcp
pip install -r requirements.txt
```

### 2. Configure Claude Code

Add to your Claude Code MCP settings (`~/.config/claude-code/mcp.json`):

```json
{
  "mcpServers": {
    "skill-seeker": {
      "command": "python3",
      "args": [
        "/path/to/Skill_Seekers/mcp/server.py"
      ],
      "cwd": "/path/to/Skill_Seekers"
    }
  }
}
```

**Replace `/path/to/Skill_Seekers` with your actual repository path!**

### 3. Restart Claude Code

Restart Claude Code to load the MCP server.

## Available Tools

### 1. `generate_config`

Generate a config file for any documentation website.

**Parameters:**
- `name` (required): Skill name (lowercase, alphanumeric, hyphens, underscores)
- `url` (required): Base documentation URL (must include http:// or https://)
- `description` (required): Description of when to use this skill
- `max_pages` (optional): Maximum pages to scrape (default: 100)
- `rate_limit` (optional): Delay between requests in seconds (default: 0.5)

**Example:**
```
Generate config for Tailwind CSS docs at https://tailwindcss.com/docs
```

### 2. `estimate_pages`

Estimate how many pages will be scraped from a config.

**Parameters:**
- `config_path` (required): Path to config JSON file
- `max_discovery` (optional): Maximum pages to discover (default: 1000)

**Example:**
```
Estimate pages for configs/tailwind.json
```

### 3. `scrape_docs`

Scrape documentation and build Claude skill.

**Parameters:**
- `config_path` (required): Path to config JSON file
- `enhance_local` (optional): Open terminal for local enhancement (default: false)
- `skip_scrape` (optional): Skip scraping, use cached data (default: false)
- `dry_run` (optional): Preview without saving (default: false)

**Example:**
```
Scrape docs using configs/tailwind.json
```

### 4. `package_skill`

Package a skill directory into a .zip file.

**Parameters:**
- `skill_dir` (required): Path to skill directory

**Example:**
```
Package skill at output/tailwind/
```

### 5. `list_configs`

List all available preset configurations.

**Example:**
```
Show me all available configs
```

### 6. `validate_config`

Validate a config file for errors.

**Parameters:**
- `config_path` (required): Path to config JSON file

**Example:**
```
Validate configs/tailwind.json
```

## Usage Workflow

### Quick Start

```
1. "Generate config for Next.js docs at https://nextjs.org/docs"
2. "Estimate pages for configs/nextjs.json"
3. "Scrape docs using configs/nextjs.json"
4. "Package skill at output/nextjs/"
5. Upload nextjs.zip to Claude!
```

### With Enhancement

```
1. "Generate config for Svelte docs at https://svelte.dev/docs"
2. "Scrape docs using configs/svelte.json with local enhancement"
3. (Terminal opens for Claude Code to enhance SKILL.md)
4. "Package skill at output/svelte/"
```

### Using Presets

```
1. "List all available configs"
2. "Scrape docs using configs/react.json"
3. "Package skill at output/react/"
```

## Troubleshooting

### MCP Server Not Loading

1. Check MCP config path: `cat ~/.config/claude-code/mcp.json`
2. Verify Python path: `which python3`
3. Test server manually: `python3 mcp/server.py`
4. Check Claude Code logs

### Tools Not Appearing

1. Restart Claude Code completely
2. Verify mcp package is installed: `pip show mcp`
3. Check server.py has execute permissions: `chmod +x mcp/server.py`

### Import Errors

Make sure you're running commands from the repository root:
```bash
cd /path/to/Skill_Seekers
python3 mcp/server.py
```

## Architecture

```
Skill_Seekers/
├── cli/                    # CLI tools (used by MCP)
│   ├── doc_scraper.py
│   ├── estimate_pages.py
│   ├── enhance_skill.py
│   ├── package_skill.py
│   └── ...
├── mcp/                    # MCP server
│   ├── server.py          # Main MCP server
│   ├── requirements.txt   # MCP dependencies
│   └── README.md         # This file
├── configs/               # Shared configs
└── output/                # Generated skills
```

## Development

### Adding New Tools

Edit `mcp/server.py`:

```python
# 1. Add tool definition to list_tools()
Tool(
    name="my_tool",
    description="Tool description",
    inputSchema={...}
)

# 2. Add tool handler to call_tool()
elif name == "my_tool":
    return await my_tool_handler(arguments)

# 3. Implement handler
async def my_tool_handler(args: dict) -> list[TextContent]:
    # Tool logic here
    return [TextContent(type="text", text=result)]
```

### Testing

```bash
# Test server manually
python3 mcp/server.py

# Test with MCP inspector (if available)
mcp-inspector mcp/server.py
```

## Links

- [Main CLI Documentation](../README.md)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Claude Code](https://claude.ai/code)

## License

Same as parent project (see ../LICENSE)
