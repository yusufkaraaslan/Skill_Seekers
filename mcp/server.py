#!/usr/bin/env python3
"""
Skill Seeker MCP Server
Model Context Protocol server for generating Claude AI skills from documentation
"""

import asyncio
import json
import os
import subprocess
import sys
import time
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


def run_subprocess_with_streaming(cmd, timeout=None):
    """
    Run subprocess with real-time output streaming.
    Returns (stdout, stderr, returncode).

    This solves the blocking issue where long-running processes (like scraping)
    would cause MCP to appear frozen. Now we stream output as it comes.
    """
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        stdout_lines = []
        stderr_lines = []
        start_time = time.time()

        # Read output line by line as it comes
        while True:
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                process.kill()
                stderr_lines.append(f"\n⚠️ Process killed after {timeout}s timeout")
                break

            # Check if process finished
            if process.poll() is not None:
                break

            # Read available output (non-blocking)
            try:
                import select
                readable, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)

                if process.stdout in readable:
                    line = process.stdout.readline()
                    if line:
                        stdout_lines.append(line)

                if process.stderr in readable:
                    line = process.stderr.readline()
                    if line:
                        stderr_lines.append(line)
            except:
                # Fallback for Windows (no select)
                time.sleep(0.1)

        # Get any remaining output
        remaining_stdout, remaining_stderr = process.communicate()
        if remaining_stdout:
            stdout_lines.append(remaining_stdout)
        if remaining_stderr:
            stderr_lines.append(remaining_stderr)

        stdout = ''.join(stdout_lines)
        stderr = ''.join(stderr_lines)
        returncode = process.returncode

        return stdout, stderr, returncode

    except Exception as e:
        return "", f"Error running subprocess: {str(e)}", 1


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
                        "description": "Maximum pages to scrape (default: 100, use -1 for unlimited)",
                        "default": 100,
                    },
                    "unlimited": {
                        "type": "boolean",
                        "description": "Remove all limits - scrape all pages (default: false). Overrides max_pages.",
                        "default": False,
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
                        "description": "Maximum pages to discover during estimation (default: 1000, use -1 for unlimited)",
                        "default": 1000,
                    },
                    "unlimited": {
                        "type": "boolean",
                        "description": "Remove discovery limit - estimate all pages (default: false). Overrides max_discovery.",
                        "default": False,
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
                    "unlimited": {
                        "type": "boolean",
                        "description": "Remove page limit - scrape all pages (default: false). Overrides max_pages in config.",
                        "default": False,
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
            description="Package a skill directory into a .zip file ready for Claude upload. Automatically uploads if ANTHROPIC_API_KEY is set.",
            inputSchema={
                "type": "object",
                "properties": {
                    "skill_dir": {
                        "type": "string",
                        "description": "Path to skill directory (e.g., output/react/)",
                    },
                    "auto_upload": {
                        "type": "boolean",
                        "description": "Try to upload automatically if API key is available (default: true). If false, only package without upload attempt.",
                        "default": True,
                    },
                },
                "required": ["skill_dir"],
            },
        ),
        Tool(
            name="upload_skill",
            description="Upload a skill .zip file to Claude automatically (requires ANTHROPIC_API_KEY)",
            inputSchema={
                "type": "object",
                "properties": {
                    "skill_zip": {
                        "type": "string",
                        "description": "Path to skill .zip file (e.g., output/react.zip)",
                    },
                },
                "required": ["skill_zip"],
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
        Tool(
            name="split_config",
            description="Split large documentation config into multiple focused skills. For 10K+ page documentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "Path to config JSON file (e.g., configs/godot.json)",
                    },
                    "strategy": {
                        "type": "string",
                        "description": "Split strategy: auto, none, category, router, size (default: auto)",
                        "default": "auto",
                    },
                    "target_pages": {
                        "type": "integer",
                        "description": "Target pages per skill (default: 5000)",
                        "default": 5000,
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Preview without saving files (default: false)",
                        "default": False,
                    },
                },
                "required": ["config_path"],
            },
        ),
        Tool(
            name="generate_router",
            description="Generate router/hub skill for split documentation. Creates intelligent routing to sub-skills.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_pattern": {
                        "type": "string",
                        "description": "Config pattern for sub-skills (e.g., 'configs/godot-*.json')",
                    },
                    "router_name": {
                        "type": "string",
                        "description": "Router skill name (optional, inferred from configs)",
                    },
                },
                "required": ["config_pattern"],
            },
        ),
        Tool(
            name="scrape_pdf",
            description="Scrape PDF documentation and build Claude skill. Extracts text, code, and images from PDF files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "Path to PDF config JSON file (e.g., configs/manual_pdf.json)",
                    },
                    "pdf_path": {
                        "type": "string",
                        "description": "Direct PDF path (alternative to config_path)",
                    },
                    "name": {
                        "type": "string",
                        "description": "Skill name (required with pdf_path)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Skill description (optional)",
                    },
                    "from_json": {
                        "type": "string",
                        "description": "Build from extracted JSON file (e.g., output/manual_extracted.json)",
                    },
                },
                "required": [],
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
        elif name == "upload_skill":
            return await upload_skill_tool(arguments)
        elif name == "list_configs":
            return await list_configs_tool(arguments)
        elif name == "validate_config":
            return await validate_config_tool(arguments)
        elif name == "split_config":
            return await split_config_tool(arguments)
        elif name == "generate_router":
            return await generate_router_tool(arguments)
        elif name == "scrape_pdf":
            return await scrape_pdf_tool(arguments)
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
    unlimited = args.get("unlimited", False)
    rate_limit = args.get("rate_limit", 0.5)

    # Handle unlimited mode
    if unlimited:
        max_pages = None
        limit_msg = "unlimited (no page limit)"
    elif max_pages == -1:
        max_pages = None
        limit_msg = "unlimited (no page limit)"
    else:
        limit_msg = str(max_pages)

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
  Max pages: {limit_msg}
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
    unlimited = args.get("unlimited", False)

    # Handle unlimited mode
    if unlimited or max_discovery == -1:
        max_discovery = -1
        timeout = 1800  # 30 minutes for unlimited discovery
    else:
        # Estimate: 0.5s per page discovered
        timeout = max(300, max_discovery // 2)  # Minimum 5 minutes

    # Run estimate_pages.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "estimate_pages.py"),
        config_path,
        "--max-discovery", str(max_discovery)
    ]

    progress_msg = f"🔄 Estimating page count...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]


async def scrape_docs_tool(args: dict) -> list[TextContent]:
    """Scrape documentation"""
    config_path = args["config_path"]
    unlimited = args.get("unlimited", False)
    enhance_local = args.get("enhance_local", False)
    skip_scrape = args.get("skip_scrape", False)
    dry_run = args.get("dry_run", False)

    # Handle unlimited mode by modifying config temporarily
    if unlimited:
        # Load config
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Set max_pages to None (unlimited)
        config['max_pages'] = None

        # Create temporary config file
        temp_config_path = config_path.replace('.json', '_unlimited_temp.json')
        with open(temp_config_path, 'w') as f:
            json.dump(config, f, indent=2)

        config_to_use = temp_config_path
    else:
        config_to_use = config_path

    # Build command
    cmd = [
        sys.executable,
        str(CLI_DIR / "doc_scraper.py"),
        "--config", config_to_use
    ]

    if enhance_local:
        cmd.append("--enhance-local")
    if skip_scrape:
        cmd.append("--skip-scrape")
    if dry_run:
        cmd.append("--dry-run")

    # Determine timeout based on operation type
    if dry_run:
        timeout = 300  # 5 minutes for dry run
    elif skip_scrape:
        timeout = 600  # 10 minutes for building from cache
    elif unlimited:
        timeout = None  # No timeout for unlimited mode (user explicitly requested)
    else:
        # Read config to estimate timeout
        try:
            with open(config_to_use, 'r') as f:
                config = json.load(f)
            max_pages = config.get('max_pages', 500)
            # Estimate: 30s per page + buffer
            timeout = max(3600, max_pages * 35)  # Minimum 1 hour, or 35s per page
        except:
            timeout = 14400  # Default: 4 hours

    # Add progress message
    progress_msg = f"🔄 Starting scraping process...\n"
    if timeout:
        progress_msg += f"⏱️ Maximum time allowed: {timeout // 60} minutes\n"
    else:
        progress_msg += f"⏱️ Unlimited mode - no timeout\n"
    progress_msg += f"📝 Progress will be shown below:\n\n"

    # Run doc_scraper.py with streaming
    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    # Clean up temporary config
    if unlimited and Path(config_to_use).exists():
        Path(config_to_use).unlink()

    output = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output)]
    else:
        error_output = output + f"\n\n❌ Error:\n{stderr}"
        return [TextContent(type="text", text=error_output)]


async def package_skill_tool(args: dict) -> list[TextContent]:
    """Package skill to .zip and optionally auto-upload"""
    skill_dir = args["skill_dir"]
    auto_upload = args.get("auto_upload", True)

    # Check if API key exists - only upload if available
    has_api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    should_upload = auto_upload and has_api_key

    # Run package_skill.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "package_skill.py"),
        skill_dir,
        "--no-open"  # Don't open folder in MCP context
    ]

    # Add upload flag only if we have API key
    if should_upload:
        cmd.append("--upload")

    # Timeout: 5 minutes for packaging + upload
    timeout = 300

    progress_msg = "📦 Packaging skill...\n"
    if should_upload:
        progress_msg += "📤 Will auto-upload if successful\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output = progress_msg + stdout

    if returncode == 0:
        if should_upload:
            # Upload succeeded
            output += "\n\n✅ Skill packaged and uploaded automatically!"
            output += "\n   Your skill is now available in Claude!"
        elif auto_upload and not has_api_key:
            # User wanted upload but no API key
            output += "\n\n📝 Skill packaged successfully!"
            output += "\n"
            output += "\n💡 To enable automatic upload:"
            output += "\n   1. Get API key from https://console.anthropic.com/"
            output += "\n   2. Set: export ANTHROPIC_API_KEY=sk-ant-..."
            output += "\n"
            output += "\n📤 Manual upload:"
            output += "\n   1. Find the .zip file in your output/ folder"
            output += "\n   2. Go to https://claude.ai/skills"
            output += "\n   3. Click 'Upload Skill' and select the .zip file"
        else:
            # auto_upload=False, just packaged
            output += "\n\n✅ Skill packaged successfully!"
            output += "\n   Upload manually to https://claude.ai/skills"

        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]


async def upload_skill_tool(args: dict) -> list[TextContent]:
    """Upload skill .zip to Claude"""
    skill_zip = args["skill_zip"]

    # Run upload_skill.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "upload_skill.py"),
        skill_zip
    ]

    # Timeout: 5 minutes for upload
    timeout = 300

    progress_msg = "📤 Uploading skill to Claude...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]


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


async def split_config_tool(args: dict) -> list[TextContent]:
    """Split large config into multiple focused configs"""
    config_path = args["config_path"]
    strategy = args.get("strategy", "auto")
    target_pages = args.get("target_pages", 5000)
    dry_run = args.get("dry_run", False)

    # Run split_config.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "split_config.py"),
        config_path,
        "--strategy", strategy,
        "--target-pages", str(target_pages)
    ]

    if dry_run:
        cmd.append("--dry-run")

    # Timeout: 5 minutes for config splitting
    timeout = 300

    progress_msg = "✂️ Splitting configuration...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]


async def generate_router_tool(args: dict) -> list[TextContent]:
    """Generate router skill for split documentation"""
    import glob

    config_pattern = args["config_pattern"]
    router_name = args.get("router_name")

    # Expand glob pattern
    config_files = glob.glob(config_pattern)

    if not config_files:
        return [TextContent(type="text", text=f"❌ No config files match pattern: {config_pattern}")]

    # Run generate_router.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "generate_router.py"),
    ] + config_files

    if router_name:
        cmd.extend(["--name", router_name])

    # Timeout: 5 minutes for router generation
    timeout = 300

    progress_msg = "🧭 Generating router skill...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]


async def scrape_pdf_tool(args: dict) -> list[TextContent]:
    """Scrape PDF documentation and build skill"""
    config_path = args.get("config_path")
    pdf_path = args.get("pdf_path")
    name = args.get("name")
    description = args.get("description")
    from_json = args.get("from_json")

    # Build command
    cmd = [sys.executable, str(CLI_DIR / "pdf_scraper.py")]

    # Mode 1: Config file
    if config_path:
        cmd.extend(["--config", config_path])

    # Mode 2: Direct PDF
    elif pdf_path and name:
        cmd.extend(["--pdf", pdf_path, "--name", name])
        if description:
            cmd.extend(["--description", description])

    # Mode 3: From JSON
    elif from_json:
        cmd.extend(["--from-json", from_json])

    else:
        return [TextContent(type="text", text="❌ Error: Must specify --config, --pdf + --name, or --from-json")]

    # Run pdf_scraper.py with streaming (can take a while)
    timeout = 600  # 10 minutes for PDF extraction

    progress_msg = "📄 Scraping PDF documentation...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]


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
