#!/usr/bin/env python3
"""
Skill Seeker MCP Server
Model Context Protocol server for generating Claude AI skills from documentation
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
except ImportError:
    print("❌ Error: mcp package not installed")
    print("Install with: pip install mcp")
    sys.exit(1)


# Initialize MCP server
app = Server("skill-seeker")

# Path to CLI tools
CLI_DIR = Path(__file__).parent.parent / "cli"


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="generate_config",
            description="Generate a config file for documentation scraping. Interactively creates a JSON config for any documentation website.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Skill name (lowercase, alphanumeric, hyphens, underscores)",
                    },
                    "url": {
                        "type": "string",
                        "description": "Base documentation URL (must include http:// or https://)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of when to use this skill",
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Maximum pages to scrape (default: 100)",
                        "default": 100,
                    },
                    "rate_limit": {
                        "type": "number",
                        "description": "Delay between requests in seconds (default: 0.5)",
                        "default": 0.5,
                    },
                },
                "required": ["name", "url", "description"],
            },
        ),
        Tool(
            name="estimate_pages",
            description="Estimate how many pages will be scraped from a config. Fast preview without downloading content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "Path to config JSON file (e.g., configs/react.json)",
                    },
                    "max_discovery": {
                        "type": "integer",
                        "description": "Maximum pages to discover during estimation (default: 1000)",
                        "default": 1000,
                    },
                },
                "required": ["config_path"],
            },
        ),
        Tool(
            name="scrape_docs",
            description="Scrape documentation and build Claude skill. Creates SKILL.md and reference files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "Path to config JSON file (e.g., configs/react.json)",
                    },
                    "enhance_local": {
                        "type": "boolean",
                        "description": "Open terminal for local enhancement with Claude Code (default: false)",
                        "default": False,
                    },
                    "skip_scrape": {
                        "type": "boolean",
                        "description": "Skip scraping, use cached data (default: false)",
                        "default": False,
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Preview what will be scraped without saving (default: false)",
                        "default": False,
                    },
                },
                "required": ["config_path"],
            },
        ),
        Tool(
            name="package_skill",
            description="Package a skill directory into a .zip file ready for Claude upload.",
            inputSchema={
                "type": "object",
                "properties": {
                    "skill_dir": {
                        "type": "string",
                        "description": "Path to skill directory (e.g., output/react/)",
                    },
                },
                "required": ["skill_dir"],
            },
        ),
        Tool(
            name="list_configs",
            description="List all available preset configurations.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="validate_config",
            description="Validate a config file for errors.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "Path to config JSON file",
                    },
                },
                "required": ["config_path"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    try:
        if name == "generate_config":
            return await generate_config_tool(arguments)
        elif name == "estimate_pages":
            return await estimate_pages_tool(arguments)
        elif name == "scrape_docs":
            return await scrape_docs_tool(arguments)
        elif name == "package_skill":
            return await package_skill_tool(arguments)
        elif name == "list_configs":
            return await list_configs_tool(arguments)
        elif name == "validate_config":
            return await validate_config_tool(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def generate_config_tool(args: dict) -> list[TextContent]:
    """Generate a config file"""
    name = args["name"]
    url = args["url"]
    description = args["description"]
    max_pages = args.get("max_pages", 100)
    rate_limit = args.get("rate_limit", 0.5)

    # Create config
    config = {
        "name": name,
        "description": description,
        "base_url": url,
        "selectors": {
            "main_content": "article",
            "title": "h1",
            "code_blocks": "pre code"
        },
        "url_patterns": {
            "include": [],
            "exclude": []
        },
        "categories": {},
        "rate_limit": rate_limit,
        "max_pages": max_pages
    }

    # Save to configs directory
    config_path = Path("configs") / f"{name}.json"
    config_path.parent.mkdir(exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    result = f"""✅ Config created: {config_path}

Configuration:
  Name: {name}
  URL: {url}
  Max pages: {max_pages}
  Rate limit: {rate_limit}s

Next steps:
  1. Review/edit config: cat {config_path}
  2. Estimate pages: Use estimate_pages tool
  3. Scrape docs: Use scrape_docs tool

Note: Default selectors may need adjustment for your documentation site.
"""

    return [TextContent(type="text", text=result)]


async def estimate_pages_tool(args: dict) -> list[TextContent]:
    """Estimate page count"""
    config_path = args["config_path"]
    max_discovery = args.get("max_discovery", 1000)

    # Run estimate_pages.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "estimate_pages.py"),
        config_path,
        "--max-discovery", str(max_discovery)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return [TextContent(type="text", text=result.stdout)]
    else:
        return [TextContent(type="text", text=f"Error: {result.stderr}")]


async def scrape_docs_tool(args: dict) -> list[TextContent]:
    """Scrape documentation"""
    config_path = args["config_path"]
    enhance_local = args.get("enhance_local", False)
    skip_scrape = args.get("skip_scrape", False)
    dry_run = args.get("dry_run", False)

    # Build command
    cmd = [
        sys.executable,
        str(CLI_DIR / "doc_scraper.py"),
        "--config", config_path
    ]

    if enhance_local:
        cmd.append("--enhance-local")
    if skip_scrape:
        cmd.append("--skip-scrape")
    if dry_run:
        cmd.append("--dry-run")

    # Run doc_scraper.py
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return [TextContent(type="text", text=result.stdout)]
    else:
        return [TextContent(type="text", text=f"Error: {result.stderr}\n{result.stdout}")]


async def package_skill_tool(args: dict) -> list[TextContent]:
    """Package skill to .zip"""
    skill_dir = args["skill_dir"]

    # Run package_skill.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "package_skill.py"),
        skill_dir
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return [TextContent(type="text", text=result.stdout)]
    else:
        return [TextContent(type="text", text=f"Error: {result.stderr}")]


async def list_configs_tool(args: dict) -> list[TextContent]:
    """List available configs"""
    configs_dir = Path("configs")

    if not configs_dir.exists():
        return [TextContent(type="text", text="No configs directory found")]

    configs = list(configs_dir.glob("*.json"))

    if not configs:
        return [TextContent(type="text", text="No config files found")]

    result = "📋 Available Configs:\n\n"

    for config_file in sorted(configs):
        try:
            with open(config_file) as f:
                config = json.load(f)
                name = config.get("name", config_file.stem)
                desc = config.get("description", "No description")
                url = config.get("base_url", "")

                result += f"  • {config_file.name}\n"
                result += f"    Name: {name}\n"
                result += f"    URL: {url}\n"
                result += f"    Description: {desc}\n\n"
        except Exception as e:
            result += f"  • {config_file.name} - Error reading: {e}\n\n"

    return [TextContent(type="text", text=result)]


async def validate_config_tool(args: dict) -> list[TextContent]:
    """Validate a config file"""
    config_path = args["config_path"]

    # Import validation function
    sys.path.insert(0, str(CLI_DIR))
    from doc_scraper import validate_config
    import json

    try:
        # Load config manually to avoid sys.exit() calls
        if not Path(config_path).exists():
            return [TextContent(type="text", text=f"❌ Error: Config file not found: {config_path}")]

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Validate config - returns (errors, warnings) tuple
        errors, warnings = validate_config(config)

        if errors:
            result = f"❌ Config validation failed:\n\n"
            for error in errors:
                result += f"  • {error}\n"
        else:
            result = f"✅ Config is valid!\n\n"
            result += f"  Name: {config['name']}\n"
            result += f"  Base URL: {config['base_url']}\n"
            result += f"  Max pages: {config.get('max_pages', 'Not set')}\n"
            result += f"  Rate limit: {config.get('rate_limit', 'Not set')}s\n"

            if warnings:
                result += f"\n⚠️  Warnings:\n"
                for warning in warnings:
                    result += f"  • {warning}\n"

        return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
