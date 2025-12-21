#!/usr/bin/env python3
"""
Skill Seeker MCP Server
Model Context Protocol server for generating Claude AI skills from documentation
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
import httpx

# Import external MCP package
# NOTE: Directory renamed from 'mcp/' to 'skill_seeker_mcp/' to avoid shadowing the external mcp package
MCP_AVAILABLE = False
Server = None
Tool = None
TextContent = None

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError as e:
    if __name__ == "__main__":
        print("❌ Error: mcp package not installed")
        print("Install with: pip install mcp")
        print(f"Import error: {e}")
        sys.exit(1)


# Initialize MCP server (only if MCP is available)
app = Server("skill-seeker") if MCP_AVAILABLE and Server is not None else None

# Path to CLI tools
CLI_DIR = Path(__file__).parent.parent / "cli"

# Import config validator for submit_config validation
sys.path.insert(0, str(CLI_DIR))
try:
    from config_validator import ConfigValidator
except ImportError:
    ConfigValidator = None  # Graceful degradation if not available

# Helper decorator that works even when app is None
def safe_decorator(decorator_func):
    """Returns the decorator if MCP is available, otherwise returns a no-op"""
    if MCP_AVAILABLE and app is not None:
        return decorator_func
    else:
        # Return a decorator that just returns the function unchanged
        def noop_decorator(func):
            return func
        return noop_decorator


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


@safe_decorator(app.list_tools() if app else lambda: lambda f: f)
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
            description="Scrape documentation and build Claude skill. Supports both single-source (legacy) and unified multi-source configs. Creates SKILL.md and reference files. Automatically detects llms.txt files for 10x faster processing. Falls back to HTML scraping if not available.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "Path to config JSON file (e.g., configs/react.json or configs/godot_unified.json)",
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
                    "merge_mode": {
                        "type": "string",
                        "description": "Override merge mode for unified configs: 'rule-based' or 'claude-enhanced' (default: from config)",
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
        Tool(
            name="scrape_github",
            description="Scrape GitHub repository and build Claude skill. Extracts README, Issues, Changelog, Releases, and code structure.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "GitHub repository (owner/repo, e.g., facebook/react)",
                    },
                    "config_path": {
                        "type": "string",
                        "description": "Path to GitHub config JSON file (e.g., configs/react_github.json)",
                    },
                    "name": {
                        "type": "string",
                        "description": "Skill name (default: repo name)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Skill description",
                    },
                    "token": {
                        "type": "string",
                        "description": "GitHub personal access token (or use GITHUB_TOKEN env var)",
                    },
                    "no_issues": {
                        "type": "boolean",
                        "description": "Skip GitHub issues extraction (default: false)",
                        "default": False,
                    },
                    "no_changelog": {
                        "type": "boolean",
                        "description": "Skip CHANGELOG extraction (default: false)",
                        "default": False,
                    },
                    "no_releases": {
                        "type": "boolean",
                        "description": "Skip releases extraction (default: false)",
                        "default": False,
                    },
                    "max_issues": {
                        "type": "integer",
                        "description": "Maximum issues to fetch (default: 100)",
                        "default": 100,
                    },
                    "scrape_only": {
                        "type": "boolean",
                        "description": "Only scrape, don't build skill (default: false)",
                        "default": False,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="install_skill",
            description="Complete one-command workflow: fetch config → scrape docs → AI enhance (MANDATORY) → package → upload. Enhancement required for quality (3/10→9/10). Takes 20-45 min depending on config size. Automatically uploads to Claude if ANTHROPIC_API_KEY is set.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_name": {
                        "type": "string",
                        "description": "Config name from API (e.g., 'react', 'django'). Mutually exclusive with config_path. Tool will fetch this config from the official API before scraping.",
                    },
                    "config_path": {
                        "type": "string",
                        "description": "Path to existing config JSON file (e.g., 'configs/custom.json'). Mutually exclusive with config_name. Use this if you already have a config file.",
                    },
                    "destination": {
                        "type": "string",
                        "description": "Output directory for skill files (default: 'output')",
                        "default": "output",
                    },
                    "auto_upload": {
                        "type": "boolean",
                        "description": "Auto-upload to Claude after packaging (requires ANTHROPIC_API_KEY). Default: true. Set to false to skip upload.",
                        "default": True,
                    },
                    "unlimited": {
                        "type": "boolean",
                        "description": "Remove page limits during scraping (default: false). WARNING: Can take hours for large sites.",
                        "default": False,
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Preview workflow without executing (default: false). Shows all phases that would run.",
                        "default": False,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="fetch_config",
            description="Fetch config from API, git URL, or registered source. Supports three modes: (1) Named source from registry, (2) Direct git URL, (3) API (default). List available configs or download a specific one by name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_name": {
                        "type": "string",
                        "description": "Name of the config to download (e.g., 'react', 'django', 'godot'). Required for git modes. Omit to list all available configs in API mode.",
                    },
                    "destination": {
                        "type": "string",
                        "description": "Directory to save the config file (default: 'configs/')",
                        "default": "configs",
                    },
                    "list_available": {
                        "type": "boolean",
                        "description": "List all available configs from the API (only works in API mode, default: false)",
                        "default": False,
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter configs by category when listing in API mode (e.g., 'web-frameworks', 'game-engines', 'devops')",
                    },
                    "git_url": {
                        "type": "string",
                        "description": "Git repository URL containing configs. If provided, fetches from git instead of API. Supports HTTPS and SSH URLs. Example: 'https://github.com/myorg/configs.git'",
                    },
                    "source": {
                        "type": "string",
                        "description": "Named source from registry (highest priority). Use add_config_source to register sources first. Example: 'team', 'company'",
                    },
                    "branch": {
                        "type": "string",
                        "description": "Git branch to use (default: 'main'). Only used with git_url or source.",
                        "default": "main",
                    },
                    "token": {
                        "type": "string",
                        "description": "Authentication token for private repos (optional). Prefer using environment variables (GITHUB_TOKEN, GITLAB_TOKEN, etc.).",
                    },
                    "refresh": {
                        "type": "boolean",
                        "description": "Force refresh cached git repository (default: false). Deletes cache and re-clones. Only used with git modes.",
                        "default": False,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="submit_config",
            description="Submit a custom config file to the community. Validates config (legacy or unified format) and creates a GitHub issue in skill-seekers-configs repo for review.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "Path to config JSON file to submit (e.g., 'configs/myframework.json')",
                    },
                    "config_json": {
                        "type": "string",
                        "description": "Config JSON as string (alternative to config_path)",
                    },
                    "testing_notes": {
                        "type": "string",
                        "description": "Notes about testing (e.g., 'Tested with 20 pages, works well')",
                    },
                    "github_token": {
                        "type": "string",
                        "description": "GitHub personal access token (or use GITHUB_TOKEN env var)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="add_config_source",
            description="Register a git repository as a config source. Allows fetching configs from private/team repos. Use this to set up named sources that can be referenced by fetch_config. Supports GitHub, GitLab, Gitea, Bitbucket, and custom git servers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Source identifier (lowercase, alphanumeric, hyphens/underscores allowed). Example: 'team', 'company-internal', 'my_configs'",
                    },
                    "git_url": {
                        "type": "string",
                        "description": "Git repository URL (HTTPS or SSH). Example: 'https://github.com/myorg/configs.git' or 'git@github.com:myorg/configs.git'",
                    },
                    "source_type": {
                        "type": "string",
                        "description": "Source type (default: 'github'). Options: 'github', 'gitlab', 'gitea', 'bitbucket', 'custom'",
                        "default": "github",
                    },
                    "token_env": {
                        "type": "string",
                        "description": "Environment variable name for auth token (optional). Auto-detected if not provided. Example: 'GITHUB_TOKEN', 'GITLAB_TOKEN', 'MY_CUSTOM_TOKEN'",
                    },
                    "branch": {
                        "type": "string",
                        "description": "Git branch to use (default: 'main'). Example: 'main', 'master', 'develop'",
                        "default": "main",
                    },
                    "priority": {
                        "type": "integer",
                        "description": "Source priority (lower = higher priority, default: 100). Used for conflict resolution when same config exists in multiple sources.",
                        "default": 100,
                    },
                    "enabled": {
                        "type": "boolean",
                        "description": "Whether source is enabled (default: true)",
                        "default": True,
                    },
                },
                "required": ["name", "git_url"],
            },
        ),
        Tool(
            name="list_config_sources",
            description="List all registered config sources. Shows git repositories that have been registered with add_config_source. Use this to see available sources for fetch_config.",
            inputSchema={
                "type": "object",
                "properties": {
                    "enabled_only": {
                        "type": "boolean",
                        "description": "Only show enabled sources (default: false)",
                        "default": False,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="remove_config_source",
            description="Remove a registered config source. Deletes the source from the registry. Does not delete cached git repository data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Source identifier to remove. Example: 'team', 'company-internal'",
                    },
                },
                "required": ["name"],
            },
        ),
    ]


@safe_decorator(app.call_tool() if app else lambda: lambda f: f)
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
        elif name == "scrape_github":
            return await scrape_github_tool(arguments)
        elif name == "fetch_config":
            return await fetch_config_tool(arguments)
        elif name == "submit_config":
            return await submit_config_tool(arguments)
        elif name == "add_config_source":
            return await add_config_source_tool(arguments)
        elif name == "list_config_sources":
            return await list_config_sources_tool(arguments)
        elif name == "remove_config_source":
            return await remove_config_source_tool(arguments)
        elif name == "install_skill":
            return await install_skill_tool(arguments)
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
    """Scrape documentation - auto-detects unified vs legacy format"""
    config_path = args["config_path"]
    unlimited = args.get("unlimited", False)
    enhance_local = args.get("enhance_local", False)
    skip_scrape = args.get("skip_scrape", False)
    dry_run = args.get("dry_run", False)
    merge_mode = args.get("merge_mode")

    # Load config to detect format
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Detect if unified format (has 'sources' array)
    is_unified = 'sources' in config and isinstance(config['sources'], list)

    # Handle unlimited mode by modifying config temporarily
    if unlimited:
        # Set max_pages to None (unlimited)
        if is_unified:
            # For unified configs, set max_pages on documentation sources
            for source in config.get('sources', []):
                if source.get('type') == 'documentation':
                    source['max_pages'] = None
        else:
            # For legacy configs
            config['max_pages'] = None

        # Create temporary config file
        temp_config_path = config_path.replace('.json', '_unlimited_temp.json')
        with open(temp_config_path, 'w') as f:
            json.dump(config, f, indent=2)

        config_to_use = temp_config_path
    else:
        config_to_use = config_path

    # Choose scraper based on format
    if is_unified:
        scraper_script = "unified_scraper.py"
        progress_msg = f"🔄 Starting unified multi-source scraping...\n"
        progress_msg += f"📦 Config format: Unified (multiple sources)\n"
    else:
        scraper_script = "doc_scraper.py"
        progress_msg = f"🔄 Starting scraping process...\n"
        progress_msg += f"📦 Config format: Legacy (single source)\n"

    # Build command
    cmd = [
        sys.executable,
        str(CLI_DIR / scraper_script),
        "--config", config_to_use
    ]

    # Add merge mode for unified configs
    if is_unified and merge_mode:
        cmd.extend(["--merge-mode", merge_mode])

    # Add --fresh to avoid user input prompts when existing data found
    if not skip_scrape:
        cmd.append("--fresh")

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
            if is_unified:
                # For unified configs, estimate based on all sources
                total_pages = 0
                for source in config.get('sources', []):
                    if source.get('type') == 'documentation':
                        total_pages += source.get('max_pages', 500)
                max_pages = total_pages or 500
            else:
                max_pages = config.get('max_pages', 500)

            # Estimate: 30s per page + buffer
            timeout = max(3600, max_pages * 35)  # Minimum 1 hour, or 35s per page
        except:
            timeout = 14400  # Default: 4 hours

    # Add progress message
    if timeout:
        progress_msg += f"⏱️ Maximum time allowed: {timeout // 60} minutes\n"
    else:
        progress_msg += f"⏱️ Unlimited mode - no timeout\n"
    progress_msg += f"📝 Progress will be shown below:\n\n"

    # Run scraper with streaming
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
        "--no-open",  # Don't open folder in MCP context
        "--skip-quality-check"  # Skip interactive quality checks in MCP context
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
    """Validate a config file - supports both legacy and unified formats"""
    config_path = args["config_path"]

    # Import validation classes
    sys.path.insert(0, str(CLI_DIR))

    try:
        # Check if file exists
        if not Path(config_path).exists():
            return [TextContent(type="text", text=f"❌ Error: Config file not found: {config_path}")]

        # Try unified config validator first
        try:
            from config_validator import validate_config
            validator = validate_config(config_path)

            result = f"✅ Config is valid!\n\n"

            # Show format
            if validator.is_unified:
                result += f"📦 Format: Unified (multi-source)\n"
                result += f"  Name: {validator.config['name']}\n"
                result += f"  Sources: {len(validator.config.get('sources', []))}\n"

                # Show sources
                for i, source in enumerate(validator.config.get('sources', []), 1):
                    result += f"\n  Source {i}: {source['type']}\n"
                    if source['type'] == 'documentation':
                        result += f"    URL: {source.get('base_url', 'N/A')}\n"
                        result += f"    Max pages: {source.get('max_pages', 'Not set')}\n"
                    elif source['type'] == 'github':
                        result += f"    Repo: {source.get('repo', 'N/A')}\n"
                        result += f"    Code depth: {source.get('code_analysis_depth', 'surface')}\n"
                    elif source['type'] == 'pdf':
                        result += f"    Path: {source.get('path', 'N/A')}\n"

                # Show merge settings if applicable
                if validator.needs_api_merge():
                    merge_mode = validator.config.get('merge_mode', 'rule-based')
                    result += f"\n  Merge mode: {merge_mode}\n"
                    result += f"  API merging: Required (docs + code sources)\n"

            else:
                result += f"📦 Format: Legacy (single source)\n"
                result += f"  Name: {validator.config['name']}\n"
                result += f"  Base URL: {validator.config.get('base_url', 'N/A')}\n"
                result += f"  Max pages: {validator.config.get('max_pages', 'Not set')}\n"
                result += f"  Rate limit: {validator.config.get('rate_limit', 'Not set')}s\n"

            return [TextContent(type="text", text=result)]

        except ImportError:
            # Fall back to legacy validation
            from doc_scraper import validate_config
            import json

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
                result += f"📦 Format: Legacy (single source)\n"
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


async def scrape_github_tool(args: dict) -> list[TextContent]:
    """Scrape GitHub repository to Claude skill (C1.11)"""
    repo = args.get("repo")
    config_path = args.get("config_path")
    name = args.get("name")
    description = args.get("description")
    token = args.get("token")
    no_issues = args.get("no_issues", False)
    no_changelog = args.get("no_changelog", False)
    no_releases = args.get("no_releases", False)
    max_issues = args.get("max_issues", 100)
    scrape_only = args.get("scrape_only", False)

    # Build command
    cmd = [sys.executable, str(CLI_DIR / "github_scraper.py")]

    # Mode 1: Config file
    if config_path:
        cmd.extend(["--config", config_path])

    # Mode 2: Direct repo
    elif repo:
        cmd.extend(["--repo", repo])
        if name:
            cmd.extend(["--name", name])
        if description:
            cmd.extend(["--description", description])
        if token:
            cmd.extend(["--token", token])
        if no_issues:
            cmd.append("--no-issues")
        if no_changelog:
            cmd.append("--no-changelog")
        if no_releases:
            cmd.append("--no-releases")
        if max_issues != 100:
            cmd.extend(["--max-issues", str(max_issues)])
        if scrape_only:
            cmd.append("--scrape-only")

    else:
        return [TextContent(type="text", text="❌ Error: Must specify --repo or --config")]

    # Run github_scraper.py with streaming (can take a while)
    timeout = 600  # 10 minutes for GitHub scraping

    progress_msg = "🐙 Scraping GitHub repository...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]


async def fetch_config_tool(args: dict) -> list[TextContent]:
    """Fetch config from API, git URL, or named source"""
    from skill_seekers.mcp.git_repo import GitConfigRepo
    from skill_seekers.mcp.source_manager import SourceManager

    config_name = args.get("config_name")
    destination = args.get("destination", "configs")
    list_available = args.get("list_available", False)
    category = args.get("category")

    # Git mode parameters
    source_name = args.get("source")
    git_url = args.get("git_url")
    branch = args.get("branch", "main")
    token = args.get("token")
    force_refresh = args.get("refresh", False)

    try:
        # MODE 1: Named Source (highest priority)
        if source_name:
            if not config_name:
                return [TextContent(type="text", text="❌ Error: config_name is required when using source parameter")]

            # Get source from registry
            source_manager = SourceManager()
            try:
                source = source_manager.get_source(source_name)
            except KeyError as e:
                return [TextContent(type="text", text=f"❌ {str(e)}")]

            git_url = source["git_url"]
            branch = source.get("branch", branch)
            token_env = source.get("token_env")

            # Get token from environment if not provided
            if not token and token_env:
                token = os.environ.get(token_env)

            # Clone/pull repository
            git_repo = GitConfigRepo()
            try:
                repo_path = git_repo.clone_or_pull(
                    source_name=source_name,
                    git_url=git_url,
                    branch=branch,
                    token=token,
                    force_refresh=force_refresh
                )
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Git error: {str(e)}")]

            # Load config from repository
            try:
                config_data = git_repo.get_config(repo_path, config_name)
            except FileNotFoundError as e:
                return [TextContent(type="text", text=f"❌ {str(e)}")]
            except ValueError as e:
                return [TextContent(type="text", text=f"❌ {str(e)}")]

            # Save to destination
            dest_path = Path(destination)
            dest_path.mkdir(parents=True, exist_ok=True)
            config_file = dest_path / f"{config_name}.json"

            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            result = f"""✅ Config fetched from git source successfully!

📦 Config: {config_name}
📂 Saved to: {config_file}
🔗 Source: {source_name}
🌿 Branch: {branch}
📁 Repository: {git_url}
🔄 Refreshed: {'Yes (forced)' if force_refresh else 'No (used cache)'}

Next steps:
  1. Review config: cat {config_file}
  2. Estimate pages: Use estimate_pages tool
  3. Scrape docs: Use scrape_docs tool

💡 Manage sources: Use add_config_source, list_config_sources, remove_config_source tools
"""
            return [TextContent(type="text", text=result)]

        # MODE 2: Direct Git URL
        elif git_url:
            if not config_name:
                return [TextContent(type="text", text="❌ Error: config_name is required when using git_url parameter")]

            # Clone/pull repository
            git_repo = GitConfigRepo()
            source_name_temp = f"temp_{config_name}"

            try:
                repo_path = git_repo.clone_or_pull(
                    source_name=source_name_temp,
                    git_url=git_url,
                    branch=branch,
                    token=token,
                    force_refresh=force_refresh
                )
            except ValueError as e:
                return [TextContent(type="text", text=f"❌ Invalid git URL: {str(e)}")]
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Git error: {str(e)}")]

            # Load config from repository
            try:
                config_data = git_repo.get_config(repo_path, config_name)
            except FileNotFoundError as e:
                return [TextContent(type="text", text=f"❌ {str(e)}")]
            except ValueError as e:
                return [TextContent(type="text", text=f"❌ {str(e)}")]

            # Save to destination
            dest_path = Path(destination)
            dest_path.mkdir(parents=True, exist_ok=True)
            config_file = dest_path / f"{config_name}.json"

            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            result = f"""✅ Config fetched from git URL successfully!

📦 Config: {config_name}
📂 Saved to: {config_file}
📁 Repository: {git_url}
🌿 Branch: {branch}
🔄 Refreshed: {'Yes (forced)' if force_refresh else 'No (used cache)'}

Next steps:
  1. Review config: cat {config_file}
  2. Estimate pages: Use estimate_pages tool
  3. Scrape docs: Use scrape_docs tool

💡 Register this source: Use add_config_source to save for future use
"""
            return [TextContent(type="text", text=result)]

        # MODE 3: API (existing, backward compatible)
        else:
            API_BASE_URL = "https://api.skillseekersweb.com"

            async with httpx.AsyncClient(timeout=30.0) as client:
                # List available configs if requested or no config_name provided
                if list_available or not config_name:
                    # Build API URL with optional category filter
                    list_url = f"{API_BASE_URL}/api/configs"
                    params = {}
                    if category:
                        params["category"] = category

                    response = await client.get(list_url, params=params)
                    response.raise_for_status()
                    data = response.json()

                    configs = data.get("configs", [])
                    total = data.get("total", 0)
                    filters = data.get("filters")

                    # Format list output
                    result = f"📋 Available Configs ({total} total)\n"
                    if filters:
                        result += f"🔍 Filters: {filters}\n"
                    result += "\n"

                    # Group by category
                    by_category = {}
                    for config in configs:
                        cat = config.get("category", "uncategorized")
                        if cat not in by_category:
                            by_category[cat] = []
                        by_category[cat].append(config)

                    for cat, cat_configs in sorted(by_category.items()):
                        result += f"\n**{cat.upper()}** ({len(cat_configs)} configs):\n"
                        for cfg in cat_configs:
                            name = cfg.get("name")
                            desc = cfg.get("description", "")[:60]
                            config_type = cfg.get("type", "unknown")
                            tags = ", ".join(cfg.get("tags", [])[:3])
                            result += f"  • {name} [{config_type}] - {desc}{'...' if len(cfg.get('description', '')) > 60 else ''}\n"
                            if tags:
                                result += f"    Tags: {tags}\n"

                    result += f"\n💡 To download a config, use: fetch_config with config_name='<name>'\n"
                    result += f"📚 API Docs: {API_BASE_URL}/docs\n"

                    return [TextContent(type="text", text=result)]

                # Download specific config
                if not config_name:
                    return [TextContent(type="text", text="❌ Error: Please provide config_name or set list_available=true")]

                # Get config details first
                detail_url = f"{API_BASE_URL}/api/configs/{config_name}"
                detail_response = await client.get(detail_url)

                if detail_response.status_code == 404:
                    return [TextContent(type="text", text=f"❌ Config '{config_name}' not found. Use list_available=true to see available configs.")]

                detail_response.raise_for_status()
                config_info = detail_response.json()

                # Download the actual config file
                download_url = f"{API_BASE_URL}/api/download/{config_name}.json"
                download_response = await client.get(download_url)
                download_response.raise_for_status()
                config_data = download_response.json()

                # Save to destination
                dest_path = Path(destination)
                dest_path.mkdir(parents=True, exist_ok=True)
                config_file = dest_path / f"{config_name}.json"

                with open(config_file, 'w') as f:
                    json.dump(config_data, f, indent=2)

                # Build result message
                result = f"""✅ Config downloaded successfully!

📦 Config: {config_name}
📂 Saved to: {config_file}
📊 Category: {config_info.get('category', 'uncategorized')}
🏷️  Tags: {', '.join(config_info.get('tags', []))}
📄 Type: {config_info.get('type', 'unknown')}
📝 Description: {config_info.get('description', 'No description')}

🔗 Source: {config_info.get('primary_source', 'N/A')}
📏 Max pages: {config_info.get('max_pages', 'N/A')}
📦 File size: {config_info.get('file_size', 'N/A')} bytes
🕒 Last updated: {config_info.get('last_updated', 'N/A')}

Next steps:
  1. Review config: cat {config_file}
  2. Estimate pages: Use estimate_pages tool
  3. Scrape docs: Use scrape_docs tool

💡 More configs: Use list_available=true to see all available configs
"""

                return [TextContent(type="text", text=result)]

    except httpx.HTTPError as e:
        return [TextContent(type="text", text=f"❌ HTTP Error: {str(e)}\n\nCheck your internet connection or try again later.")]
    except json.JSONDecodeError as e:
        return [TextContent(type="text", text=f"❌ JSON Error: Invalid response from API: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def install_skill_tool(args: dict) -> list[TextContent]:
    """
    Complete skill installation workflow.

    Orchestrates the complete workflow:
        1. Fetch config (if config_name provided)
        2. Scrape documentation
        3. AI Enhancement (MANDATORY - no skip option)
        4. Package to .zip
        5. Upload to Claude (optional)

    Args:
        config_name: Config to fetch from API (mutually exclusive with config_path)
        config_path: Path to existing config (mutually exclusive with config_name)
        destination: Output directory (default: "output")
        auto_upload: Upload after packaging (default: True)
        unlimited: Remove page limits (default: False)
        dry_run: Preview only (default: False)

    Returns:
        List of TextContent with workflow progress and results
    """
    import json
    import re

    # Extract and validate inputs
    config_name = args.get("config_name")
    config_path = args.get("config_path")
    destination = args.get("destination", "output")
    auto_upload = args.get("auto_upload", True)
    unlimited = args.get("unlimited", False)
    dry_run = args.get("dry_run", False)

    # Validation: Must provide exactly one of config_name or config_path
    if not config_name and not config_path:
        return [TextContent(
            type="text",
            text="❌ Error: Must provide either config_name or config_path\n\nExamples:\n  install_skill(config_name='react')\n  install_skill(config_path='configs/custom.json')"
        )]

    if config_name and config_path:
        return [TextContent(
            type="text",
            text="❌ Error: Cannot provide both config_name and config_path\n\nChoose one:\n  - config_name: Fetch from API (e.g., 'react')\n  - config_path: Use existing file (e.g., 'configs/custom.json')"
        )]

    # Initialize output
    output_lines = []
    output_lines.append("🚀 SKILL INSTALLATION WORKFLOW")
    output_lines.append("=" * 70)
    output_lines.append("")

    if dry_run:
        output_lines.append("🔍 DRY RUN MODE - Preview only, no actions taken")
        output_lines.append("")

    # Track workflow state
    workflow_state = {
        'config_path': config_path,
        'skill_name': None,
        'skill_dir': None,
        'zip_path': None,
        'phases_completed': []
    }

    try:
        # ===== PHASE 1: Fetch Config (if needed) =====
        if config_name:
            output_lines.append("📥 PHASE 1/5: Fetch Config")
            output_lines.append("-" * 70)
            output_lines.append(f"Config: {config_name}")
            output_lines.append(f"Destination: {destination}/")
            output_lines.append("")

            if not dry_run:
                # Call fetch_config_tool directly
                fetch_result = await fetch_config_tool({
                    "config_name": config_name,
                    "destination": destination
                })

                # Parse result to extract config path
                fetch_output = fetch_result[0].text
                output_lines.append(fetch_output)
                output_lines.append("")

                # Extract config path from output
                # Expected format: "✅ Config saved to: configs/react.json"
                match = re.search(r"saved to:\s*(.+\.json)", fetch_output)
                if match:
                    workflow_state['config_path'] = match.group(1).strip()
                    output_lines.append(f"✅ Config fetched: {workflow_state['config_path']}")
                else:
                    return [TextContent(type="text", text="\n".join(output_lines) + "\n\n❌ Failed to fetch config")]

                workflow_state['phases_completed'].append('fetch_config')
            else:
                output_lines.append("  [DRY RUN] Would fetch config from API")
                workflow_state['config_path'] = f"{destination}/{config_name}.json"

            output_lines.append("")

        # ===== PHASE 2: Scrape Documentation =====
        phase_num = "2/5" if config_name else "1/4"
        output_lines.append(f"📄 PHASE {phase_num}: Scrape Documentation")
        output_lines.append("-" * 70)
        output_lines.append(f"Config: {workflow_state['config_path']}")
        output_lines.append(f"Unlimited mode: {unlimited}")
        output_lines.append("")

        if not dry_run:
            # Load config to get skill name
            try:
                with open(workflow_state['config_path'], 'r') as f:
                    config = json.load(f)
                    workflow_state['skill_name'] = config.get('name', 'unknown')
            except Exception as e:
                return [TextContent(type="text", text="\n".join(output_lines) + f"\n\n❌ Failed to read config: {str(e)}")]

            # Call scrape_docs_tool (does NOT include enhancement)
            output_lines.append("Scraping documentation (this may take 20-45 minutes)...")
            output_lines.append("")

            scrape_result = await scrape_docs_tool({
                "config_path": workflow_state['config_path'],
                "unlimited": unlimited,
                "enhance_local": False,  # Enhancement is separate phase
                "skip_scrape": False,
                "dry_run": False
            })

            scrape_output = scrape_result[0].text
            output_lines.append(scrape_output)
            output_lines.append("")

            # Check for success
            if "❌" in scrape_output:
                return [TextContent(type="text", text="\n".join(output_lines) + "\n\n❌ Scraping failed - see error above")]

            workflow_state['skill_dir'] = f"{destination}/{workflow_state['skill_name']}"
            workflow_state['phases_completed'].append('scrape_docs')
        else:
            output_lines.append("  [DRY RUN] Would scrape documentation")
            workflow_state['skill_name'] = "example"
            workflow_state['skill_dir'] = f"{destination}/example"

        output_lines.append("")

        # ===== PHASE 3: AI Enhancement (MANDATORY) =====
        phase_num = "3/5" if config_name else "2/4"
        output_lines.append(f"✨ PHASE {phase_num}: AI Enhancement (MANDATORY)")
        output_lines.append("-" * 70)
        output_lines.append("⚠️  Enhancement is REQUIRED for quality (3/10→9/10 boost)")
        output_lines.append(f"Skill directory: {workflow_state['skill_dir']}")
        output_lines.append("Mode: Headless (runs in background)")
        output_lines.append("Estimated time: 30-60 seconds")
        output_lines.append("")

        if not dry_run:
            # Run enhance_skill_local in headless mode
            # Build command directly
            cmd = [
                sys.executable,
                str(CLI_DIR / "enhance_skill_local.py"),
                workflow_state['skill_dir']
                # Headless is default, no flag needed
            ]

            timeout = 900  # 15 minutes max for enhancement

            output_lines.append("Running AI enhancement...")

            stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

            if returncode != 0:
                output_lines.append(f"\n❌ Enhancement failed (exit code {returncode}):")
                output_lines.append(stderr if stderr else stdout)
                return [TextContent(type="text", text="\n".join(output_lines))]

            output_lines.append(stdout)
            workflow_state['phases_completed'].append('enhance_skill')
        else:
            output_lines.append("  [DRY RUN] Would enhance SKILL.md with Claude Code")

        output_lines.append("")

        # ===== PHASE 4: Package Skill =====
        phase_num = "4/5" if config_name else "3/4"
        output_lines.append(f"📦 PHASE {phase_num}: Package Skill")
        output_lines.append("-" * 70)
        output_lines.append(f"Skill directory: {workflow_state['skill_dir']}")
        output_lines.append("")

        if not dry_run:
            # Call package_skill_tool (auto_upload=False, we handle upload separately)
            package_result = await package_skill_tool({
                "skill_dir": workflow_state['skill_dir'],
                "auto_upload": False  # We handle upload in next phase
            })

            package_output = package_result[0].text
            output_lines.append(package_output)
            output_lines.append("")

            # Extract zip path from output
            # Expected format: "Saved to: output/react.zip"
            match = re.search(r"Saved to:\s*(.+\.zip)", package_output)
            if match:
                workflow_state['zip_path'] = match.group(1).strip()
            else:
                # Fallback: construct zip path
                workflow_state['zip_path'] = f"{destination}/{workflow_state['skill_name']}.zip"

            workflow_state['phases_completed'].append('package_skill')
        else:
            output_lines.append("  [DRY RUN] Would package to .zip file")
            workflow_state['zip_path'] = f"{destination}/{workflow_state['skill_name']}.zip"

        output_lines.append("")

        # ===== PHASE 5: Upload (Optional) =====
        if auto_upload:
            phase_num = "5/5" if config_name else "4/4"
            output_lines.append(f"📤 PHASE {phase_num}: Upload to Claude")
            output_lines.append("-" * 70)
            output_lines.append(f"Zip file: {workflow_state['zip_path']}")
            output_lines.append("")

            # Check for API key
            has_api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()

            if not dry_run:
                if has_api_key:
                    # Call upload_skill_tool
                    upload_result = await upload_skill_tool({
                        "skill_zip": workflow_state['zip_path']
                    })

                    upload_output = upload_result[0].text
                    output_lines.append(upload_output)

                    workflow_state['phases_completed'].append('upload_skill')
                else:
                    output_lines.append("⚠️  ANTHROPIC_API_KEY not set - skipping upload")
                    output_lines.append("")
                    output_lines.append("To enable automatic upload:")
                    output_lines.append("  1. Get API key from https://console.anthropic.com/")
                    output_lines.append("  2. Set: export ANTHROPIC_API_KEY=sk-ant-...")
                    output_lines.append("")
                    output_lines.append("📤 Manual upload:")
                    output_lines.append("  1. Go to https://claude.ai/skills")
                    output_lines.append("  2. Click 'Upload Skill'")
                    output_lines.append(f"  3. Select: {workflow_state['zip_path']}")
            else:
                output_lines.append("  [DRY RUN] Would upload to Claude (if API key set)")

            output_lines.append("")

        # ===== WORKFLOW SUMMARY =====
        output_lines.append("=" * 70)
        output_lines.append("✅ WORKFLOW COMPLETE")
        output_lines.append("=" * 70)
        output_lines.append("")

        if not dry_run:
            output_lines.append("Phases completed:")
            for phase in workflow_state['phases_completed']:
                output_lines.append(f"  ✓ {phase}")
            output_lines.append("")

            output_lines.append("📁 Output:")
            output_lines.append(f"  Skill directory: {workflow_state['skill_dir']}")
            if workflow_state['zip_path']:
                output_lines.append(f"  Skill package: {workflow_state['zip_path']}")
            output_lines.append("")

            if auto_upload and has_api_key:
                output_lines.append("🎉 Your skill is now available in Claude!")
                output_lines.append("   Go to https://claude.ai/skills to use it")
            elif auto_upload:
                output_lines.append("📝 Manual upload required (see instructions above)")
            else:
                output_lines.append("📤 To upload:")
                output_lines.append("   skill-seekers upload " + workflow_state['zip_path'])
        else:
            output_lines.append("This was a dry run. No actions were taken.")
            output_lines.append("")
            output_lines.append("To execute for real, remove the --dry-run flag:")
            if config_name:
                output_lines.append(f"  install_skill(config_name='{config_name}')")
            else:
                output_lines.append(f"  install_skill(config_path='{config_path}')")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        output_lines.append("")
        output_lines.append(f"❌ Workflow failed: {str(e)}")
        output_lines.append("")
        output_lines.append("Phases completed before failure:")
        for phase in workflow_state['phases_completed']:
            output_lines.append(f"  ✓ {phase}")
        return [TextContent(type="text", text="\n".join(output_lines))]


async def submit_config_tool(args: dict) -> list[TextContent]:
    """Submit a custom config to skill-seekers-configs repository via GitHub issue"""
    try:
        from github import Github, GithubException
    except ImportError:
        return [TextContent(type="text", text="❌ Error: PyGithub not installed.\n\nInstall with: pip install PyGithub")]

    config_path = args.get("config_path")
    config_json_str = args.get("config_json")
    testing_notes = args.get("testing_notes", "")
    github_token = args.get("github_token") or os.environ.get("GITHUB_TOKEN")

    try:
        # Load config data
        if config_path:
            config_file = Path(config_path)
            if not config_file.exists():
                return [TextContent(type="text", text=f"❌ Error: Config file not found: {config_path}")]

            with open(config_file, 'r') as f:
                config_data = json.load(f)
                config_json_str = json.dumps(config_data, indent=2)
                config_name = config_data.get("name", config_file.stem)

        elif config_json_str:
            try:
                config_data = json.loads(config_json_str)
                config_name = config_data.get("name", "unnamed")
            except json.JSONDecodeError as e:
                return [TextContent(type="text", text=f"❌ Error: Invalid JSON: {str(e)}")]

        else:
            return [TextContent(type="text", text="❌ Error: Must provide either config_path or config_json")]

        # Use ConfigValidator for comprehensive validation
        if ConfigValidator is None:
            return [TextContent(type="text", text="❌ Error: ConfigValidator not available. Please ensure config_validator.py is in the CLI directory.")]

        try:
            validator = ConfigValidator(config_data)
            validator.validate()

            # Get format info
            is_unified = validator.is_unified
            config_name = config_data.get("name", "unnamed")

            # Additional format validation (ConfigValidator only checks structure)
            # Validate name format (alphanumeric, hyphens, underscores only)
            if not re.match(r'^[a-zA-Z0-9_-]+$', config_name):
                raise ValueError(f"Invalid name format: '{config_name}'\nNames must contain only alphanumeric characters, hyphens, and underscores")

            # Validate URL formats
            if not is_unified:
                # Legacy config - check base_url
                base_url = config_data.get('base_url', '')
                if base_url and not (base_url.startswith('http://') or base_url.startswith('https://')):
                    raise ValueError(f"Invalid base_url format: '{base_url}'\nURLs must start with http:// or https://")
            else:
                # Unified config - check URLs in sources
                for idx, source in enumerate(config_data.get('sources', [])):
                    if source.get('type') == 'documentation':
                        source_url = source.get('base_url', '')
                        if source_url and not (source_url.startswith('http://') or source_url.startswith('https://')):
                            raise ValueError(f"Source {idx} (documentation): Invalid base_url format: '{source_url}'\nURLs must start with http:// or https://")

        except ValueError as validation_error:
            # Provide detailed validation feedback
            error_msg = f"""❌ Config validation failed:

{str(validation_error)}

Please fix these issues and try again.

💡 Validation help:
- Names: alphanumeric, hyphens, underscores only (e.g., "my-framework", "react_docs")
- URLs: must start with http:// or https://
- Selectors: should be a dict with keys like 'main_content', 'title', 'code_blocks'
- Rate limit: non-negative number (default: 0.5)
- Max pages: positive integer or -1 for unlimited

📚 Example configs: https://github.com/yusufkaraaslan/skill-seekers-configs/tree/main/official
"""
            return [TextContent(type="text", text=error_msg)]

        # Detect category based on config format and content
        if is_unified:
            # For unified configs, look at source types
            source_types = [src.get('type') for src in config_data.get('sources', [])]
            if 'documentation' in source_types and 'github' in source_types:
                category = "multi-source"
            elif 'documentation' in source_types and 'pdf' in source_types:
                category = "multi-source"
            elif len(source_types) > 1:
                category = "multi-source"
            else:
                category = "unified"
        else:
            # For legacy configs, use name-based detection
            name_lower = config_name.lower()
            category = "other"
            if any(x in name_lower for x in ["react", "vue", "django", "laravel", "fastapi", "astro", "hono"]):
                category = "web-frameworks"
            elif any(x in name_lower for x in ["godot", "unity", "unreal"]):
                category = "game-engines"
            elif any(x in name_lower for x in ["kubernetes", "ansible", "docker"]):
                category = "devops"
            elif any(x in name_lower for x in ["tailwind", "bootstrap", "bulma"]):
                category = "css-frameworks"

        # Collect validation warnings
        warnings = []
        if not is_unified:
            # Legacy config warnings
            if 'max_pages' not in config_data:
                warnings.append("⚠️ No max_pages set - will use default (100)")
            elif config_data.get('max_pages') in (None, -1):
                warnings.append("⚠️ Unlimited scraping enabled - may scrape thousands of pages and take hours")
        else:
            # Unified config warnings
            for src in config_data.get('sources', []):
                if src.get('type') == 'documentation' and 'max_pages' not in src:
                    warnings.append(f"⚠️ No max_pages set for documentation source - will use default (100)")
                elif src.get('type') == 'documentation' and src.get('max_pages') in (None, -1):
                    warnings.append(f"⚠️ Unlimited scraping enabled for documentation source")

        # Check for GitHub token
        if not github_token:
            return [TextContent(type="text", text="❌ Error: GitHub token required.\n\nProvide github_token parameter or set GITHUB_TOKEN environment variable.\n\nCreate token at: https://github.com/settings/tokens")]

        # Create GitHub issue
        try:
            gh = Github(github_token)
            repo = gh.get_repo("yusufkaraaslan/skill-seekers-configs")

            # Build issue body
            issue_body = f"""## Config Submission

### Framework/Tool Name
{config_name}

### Category
{category}

### Config Format
{"Unified (multi-source)" if is_unified else "Legacy (single-source)"}

### Configuration JSON
```json
{config_json_str}
```

### Testing Results
{testing_notes if testing_notes else "Not provided"}

### Documentation URL
{config_data.get('base_url') if not is_unified else 'See sources in config'}

{"### Validation Warnings" if warnings else ""}
{chr(10).join(f"- {w}" for w in warnings) if warnings else ""}

---

### Checklist
- [x] Config validated with ConfigValidator
- [ ] Test scraping completed
- [ ] Added to appropriate category
- [ ] API updated
"""

            # Create issue
            issue = repo.create_issue(
                title=f"[CONFIG] {config_name}",
                body=issue_body,
                labels=["config-submission", "needs-review"]
            )

            result = f"""✅ Config submitted successfully!

📝 Issue created: {issue.html_url}
🏷️  Issue #{issue.number}
📦 Config: {config_name}
📊 Category: {category}
🏷️  Labels: config-submission, needs-review

What happens next:
  1. Maintainers will review your config
  2. They'll test it with the actual documentation
  3. If approved, it will be added to official/{category}/
  4. The API will auto-update and your config becomes available!

💡 Track your submission: {issue.html_url}
📚 All configs: https://github.com/yusufkaraaslan/skill-seekers-configs
"""

            return [TextContent(type="text", text=result)]

        except GithubException as e:
            return [TextContent(type="text", text=f"❌ GitHub Error: {str(e)}\n\nCheck your token permissions (needs 'repo' or 'public_repo' scope).")]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def add_config_source_tool(args: dict) -> list[TextContent]:
    """Register a git repository as a config source"""
    from skill_seekers.mcp.source_manager import SourceManager

    name = args.get("name")
    git_url = args.get("git_url")
    source_type = args.get("source_type", "github")
    token_env = args.get("token_env")
    branch = args.get("branch", "main")
    priority = args.get("priority", 100)
    enabled = args.get("enabled", True)

    try:
        # Validate required parameters
        if not name:
            return [TextContent(type="text", text="❌ Error: 'name' parameter is required")]
        if not git_url:
            return [TextContent(type="text", text="❌ Error: 'git_url' parameter is required")]

        # Add source
        source_manager = SourceManager()
        source = source_manager.add_source(
            name=name,
            git_url=git_url,
            source_type=source_type,
            token_env=token_env,
            branch=branch,
            priority=priority,
            enabled=enabled
        )

        # Check if this is an update
        is_update = "updated_at" in source and source["added_at"] != source["updated_at"]

        result = f"""✅ Config source {'updated' if is_update else 'registered'} successfully!

📛 Name: {source['name']}
📁 Repository: {source['git_url']}
🔖 Type: {source['type']}
🌿 Branch: {source['branch']}
🔑 Token env: {source.get('token_env', 'None')}
⚡ Priority: {source['priority']} (lower = higher priority)
✓ Enabled: {source['enabled']}
🕒 Added: {source['added_at'][:19]}

Usage:
  # Fetch config from this source
  fetch_config(source="{source['name']}", config_name="your-config")

  # List all sources
  list_config_sources()

  # Remove this source
  remove_config_source(name="{source['name']}")

💡 Make sure to set {source.get('token_env', 'GIT_TOKEN')} environment variable for private repos
"""

        return [TextContent(type="text", text=result)]

    except ValueError as e:
        return [TextContent(type="text", text=f"❌ Validation Error: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def list_config_sources_tool(args: dict) -> list[TextContent]:
    """List all registered config sources"""
    from skill_seekers.mcp.source_manager import SourceManager

    enabled_only = args.get("enabled_only", False)

    try:
        source_manager = SourceManager()
        sources = source_manager.list_sources(enabled_only=enabled_only)

        if not sources:
            result = """📋 No config sources registered

To add a source:
  add_config_source(
    name="team",
    git_url="https://github.com/myorg/configs.git"
  )

💡 Once added, use: fetch_config(source="team", config_name="...")
"""
            return [TextContent(type="text", text=result)]

        # Format sources list
        result = f"📋 Config Sources ({len(sources)} total"
        if enabled_only:
            result += ", enabled only"
        result += ")\n\n"

        for source in sources:
            status_icon = "✓" if source.get("enabled", True) else "✗"
            result += f"{status_icon} **{source['name']}**\n"
            result += f"  📁 {source['git_url']}\n"
            result += f"  🔖 Type: {source['type']} | 🌿 Branch: {source['branch']}\n"
            result += f"  🔑 Token: {source.get('token_env', 'None')} | ⚡ Priority: {source['priority']}\n"
            result += f"  🕒 Added: {source['added_at'][:19]}\n"
            result += "\n"

        result += """Usage:
  # Fetch config from a source
  fetch_config(source="SOURCE_NAME", config_name="CONFIG_NAME")

  # Add new source
  add_config_source(name="...", git_url="...")

  # Remove source
  remove_config_source(name="SOURCE_NAME")
"""

        return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def remove_config_source_tool(args: dict) -> list[TextContent]:
    """Remove a registered config source"""
    from skill_seekers.mcp.source_manager import SourceManager

    name = args.get("name")

    try:
        # Validate required parameter
        if not name:
            return [TextContent(type="text", text="❌ Error: 'name' parameter is required")]

        # Remove source
        source_manager = SourceManager()
        removed = source_manager.remove_source(name)

        if removed:
            result = f"""✅ Config source removed successfully!

📛 Removed: {name}

⚠️  Note: Cached git repository data is NOT deleted
To free up disk space, manually delete: ~/.skill-seekers/cache/{name}/

Next steps:
  # List remaining sources
  list_config_sources()

  # Add a different source
  add_config_source(name="...", git_url="...")
"""
            return [TextContent(type="text", text=result)]
        else:
            # Not found - show available sources
            sources = source_manager.list_sources()
            available = [s["name"] for s in sources]

            result = f"""❌ Source '{name}' not found

Available sources: {', '.join(available) if available else 'none'}

To see all sources:
  list_config_sources()
"""
            return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def main():
    """Run the MCP server"""
    if not MCP_AVAILABLE or app is None:
        print("❌ Error: MCP server cannot start - MCP package not available")
        sys.exit(1)

    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
