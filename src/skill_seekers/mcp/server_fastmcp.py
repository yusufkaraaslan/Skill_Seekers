#!/usr/bin/env python3
"""
Skill Seeker MCP Server (FastMCP Implementation)

Modern, decorator-based MCP server using FastMCP for simplified tool registration.
Provides 17 tools for generating Claude AI skills from documentation.

This is a streamlined alternative to server.py (2200 lines → 708 lines, 68% reduction).
All tool implementations are delegated to modular tool files in tools/ directory.

**Architecture:**
- FastMCP server with decorator-based tool registration
- 17 tools organized into 5 categories:
  * Config tools (3): generate_config, list_configs, validate_config
  * Scraping tools (4): estimate_pages, scrape_docs, scrape_github, scrape_pdf
  * Packaging tools (3): package_skill, upload_skill, install_skill
  * Splitting tools (2): split_config, generate_router
  * Source tools (5): fetch_config, submit_config, add_config_source, list_config_sources, remove_config_source

**Usage:**
  # Stdio transport (default, backward compatible)
  python -m skill_seekers.mcp.server_fastmcp

  # HTTP transport (new)
  python -m skill_seekers.mcp.server_fastmcp --http
  python -m skill_seekers.mcp.server_fastmcp --http --port 8080

**MCP Integration:**
  Stdio (default):
  {
    "mcpServers": {
      "skill-seeker": {
        "command": "python",
        "args": ["-m", "skill_seekers.mcp.server_fastmcp"]
      }
    }
  }

  HTTP (alternative):
  {
    "mcpServers": {
      "skill-seeker": {
        "url": "http://localhost:8000/sse"
      }
    }
  }
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Any

# Import FastMCP
MCP_AVAILABLE = False
FastMCP = None
TextContent = None

try:
    from mcp.server import FastMCP
    from mcp.types import TextContent
    MCP_AVAILABLE = True
except ImportError as e:
    # Only exit if running as main module, not when importing for tests
    if __name__ == "__main__":
        print("❌ Error: mcp package not installed")
        print("Install with: pip install mcp")
        print(f"Import error: {e}")
        sys.exit(1)

# Import all tool implementations
try:
    from .tools import (
        # Config tools
        generate_config_impl,
        list_configs_impl,
        validate_config_impl,
        # Scraping tools
        estimate_pages_impl,
        scrape_docs_impl,
        scrape_github_impl,
        scrape_pdf_impl,
        # Packaging tools
        package_skill_impl,
        upload_skill_impl,
        install_skill_impl,
        # Splitting tools
        split_config_impl,
        generate_router_impl,
        # Source tools
        fetch_config_impl,
        submit_config_impl,
        add_config_source_impl,
        list_config_sources_impl,
        remove_config_source_impl,
    )
except ImportError:
    # Fallback for direct script execution
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from tools import (
        generate_config_impl,
        list_configs_impl,
        validate_config_impl,
        estimate_pages_impl,
        scrape_docs_impl,
        scrape_github_impl,
        scrape_pdf_impl,
        package_skill_impl,
        upload_skill_impl,
        install_skill_impl,
        split_config_impl,
        generate_router_impl,
        fetch_config_impl,
        submit_config_impl,
        add_config_source_impl,
        list_config_sources_impl,
        remove_config_source_impl,
    )

# Initialize FastMCP server
mcp = None
if MCP_AVAILABLE and FastMCP is not None:
    mcp = FastMCP(
        name="skill-seeker",
        instructions="Skill Seeker MCP Server - Generate Claude AI skills from documentation",
    )

# Helper decorator for tests (when MCP is not available)
def safe_tool_decorator(*args, **kwargs):
    """Decorator that works when mcp is None (for testing)"""
    if mcp is not None:
        return mcp.tool(*args, **kwargs)
    else:
        # Return a pass-through decorator for testing
        def wrapper(func):
            return func
        return wrapper


# ============================================================================
# CONFIG TOOLS (3 tools)
# ============================================================================


@safe_tool_decorator(
    description="Generate a config file for documentation scraping. Interactively creates a JSON config for any documentation website."
)
async def generate_config(
    name: str,
    url: str,
    description: str,
    max_pages: int = 100,
    unlimited: bool = False,
    rate_limit: float = 0.5,
) -> str:
    """
    Generate a config file for documentation scraping.

    Args:
        name: Skill name (lowercase, alphanumeric, hyphens, underscores)
        url: Base documentation URL (must include http:// or https://)
        description: Description of when to use this skill
        max_pages: Maximum pages to scrape (default: 100, use -1 for unlimited)
        unlimited: Remove all limits - scrape all pages (default: false). Overrides max_pages.
        rate_limit: Delay between requests in seconds (default: 0.5)

    Returns:
        Success message with config path and next steps, or error message.
    """
    args = {
        "name": name,
        "url": url,
        "description": description,
        "max_pages": max_pages,
        "unlimited": unlimited,
        "rate_limit": rate_limit,
    }
    result = await generate_config_impl(args)
    # Extract text from TextContent objects
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


@safe_tool_decorator(
    description="List all available preset configurations."
)
async def list_configs() -> str:
    """
    List all available preset configurations.

    Returns:
        List of available configs with categories and descriptions.
    """
    result = await list_configs_impl({})
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


@safe_tool_decorator(
    description="Validate a config file for errors."
)
async def validate_config(config_path: str) -> str:
    """
    Validate a config file for errors.

    Args:
        config_path: Path to config JSON file

    Returns:
        Validation result with any errors or success message.
    """
    result = await validate_config_impl({"config_path": config_path})
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


# ============================================================================
# SCRAPING TOOLS (4 tools)
# ============================================================================


@safe_tool_decorator(
    description="Estimate how many pages will be scraped from a config. Fast preview without downloading content."
)
async def estimate_pages(
    config_path: str,
    max_discovery: int = 1000,
    unlimited: bool = False,
) -> str:
    """
    Estimate how many pages will be scraped from a config.

    Args:
        config_path: Path to config JSON file (e.g., configs/react.json)
        max_discovery: Maximum pages to discover during estimation (default: 1000, use -1 for unlimited)
        unlimited: Remove discovery limit - estimate all pages (default: false). Overrides max_discovery.

    Returns:
        Estimation results with page count and recommendations.
    """
    args = {
        "config_path": config_path,
        "max_discovery": max_discovery,
        "unlimited": unlimited,
    }
    result = await estimate_pages_impl(args)
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


@safe_tool_decorator(
    description="Scrape documentation and build Claude skill. Supports both single-source (legacy) and unified multi-source configs. Creates SKILL.md and reference files. Automatically detects llms.txt files for 10x faster processing. Falls back to HTML scraping if not available."
)
async def scrape_docs(
    config_path: str,
    unlimited: bool = False,
    enhance_local: bool = False,
    skip_scrape: bool = False,
    dry_run: bool = False,
    merge_mode: str | None = None,
) -> str:
    """
    Scrape documentation and build Claude skill.

    Args:
        config_path: Path to config JSON file (e.g., configs/react.json or configs/godot_unified.json)
        unlimited: Remove page limit - scrape all pages (default: false). Overrides max_pages in config.
        enhance_local: Open terminal for local enhancement with Claude Code (default: false)
        skip_scrape: Skip scraping, use cached data (default: false)
        dry_run: Preview what will be scraped without saving (default: false)
        merge_mode: Override merge mode for unified configs: 'rule-based' or 'claude-enhanced' (default: from config)

    Returns:
        Scraping results with file paths and statistics.
    """
    args = {
        "config_path": config_path,
        "unlimited": unlimited,
        "enhance_local": enhance_local,
        "skip_scrape": skip_scrape,
        "dry_run": dry_run,
    }
    if merge_mode:
        args["merge_mode"] = merge_mode
    result = await scrape_docs_impl(args)
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


@safe_tool_decorator(
    description="Scrape GitHub repository and build Claude skill. Extracts README, Issues, Changelog, Releases, and code structure."
)
async def scrape_github(
    repo: str | None = None,
    config_path: str | None = None,
    name: str | None = None,
    description: str | None = None,
    token: str | None = None,
    no_issues: bool = False,
    no_changelog: bool = False,
    no_releases: bool = False,
    max_issues: int = 100,
    scrape_only: bool = False,
) -> str:
    """
    Scrape GitHub repository and build Claude skill.

    Args:
        repo: GitHub repository (owner/repo, e.g., facebook/react)
        config_path: Path to GitHub config JSON file (e.g., configs/react_github.json)
        name: Skill name (default: repo name)
        description: Skill description
        token: GitHub personal access token (or use GITHUB_TOKEN env var)
        no_issues: Skip GitHub issues extraction (default: false)
        no_changelog: Skip CHANGELOG extraction (default: false)
        no_releases: Skip releases extraction (default: false)
        max_issues: Maximum issues to fetch (default: 100)
        scrape_only: Only scrape, don't build skill (default: false)

    Returns:
        GitHub scraping results with file paths.
    """
    args = {}
    if repo:
        args["repo"] = repo
    if config_path:
        args["config_path"] = config_path
    if name:
        args["name"] = name
    if description:
        args["description"] = description
    if token:
        args["token"] = token
    args["no_issues"] = no_issues
    args["no_changelog"] = no_changelog
    args["no_releases"] = no_releases
    args["max_issues"] = max_issues
    args["scrape_only"] = scrape_only

    result = await scrape_github_impl(args)
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


@safe_tool_decorator(
    description="Scrape PDF documentation and build Claude skill. Extracts text, code, and images from PDF files."
)
async def scrape_pdf(
    config_path: str | None = None,
    pdf_path: str | None = None,
    name: str | None = None,
    description: str | None = None,
    from_json: str | None = None,
) -> str:
    """
    Scrape PDF documentation and build Claude skill.

    Args:
        config_path: Path to PDF config JSON file (e.g., configs/manual_pdf.json)
        pdf_path: Direct PDF path (alternative to config_path)
        name: Skill name (required with pdf_path)
        description: Skill description (optional)
        from_json: Build from extracted JSON file (e.g., output/manual_extracted.json)

    Returns:
        PDF scraping results with file paths.
    """
    args = {}
    if config_path:
        args["config_path"] = config_path
    if pdf_path:
        args["pdf_path"] = pdf_path
    if name:
        args["name"] = name
    if description:
        args["description"] = description
    if from_json:
        args["from_json"] = from_json

    result = await scrape_pdf_impl(args)
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


# ============================================================================
# PACKAGING TOOLS (3 tools)
# ============================================================================


@safe_tool_decorator(
    description="Package a skill directory into a .zip file ready for Claude upload. Automatically uploads if ANTHROPIC_API_KEY is set."
)
async def package_skill(
    skill_dir: str,
    auto_upload: bool = True,
) -> str:
    """
    Package a skill directory into a .zip file.

    Args:
        skill_dir: Path to skill directory (e.g., output/react/)
        auto_upload: Try to upload automatically if API key is available (default: true). If false, only package without upload attempt.

    Returns:
        Packaging results with .zip file path and upload status.
    """
    args = {
        "skill_dir": skill_dir,
        "auto_upload": auto_upload,
    }
    result = await package_skill_impl(args)
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


@safe_tool_decorator(
    description="Upload a skill .zip file to Claude automatically (requires ANTHROPIC_API_KEY)"
)
async def upload_skill(skill_zip: str) -> str:
    """
    Upload a skill .zip file to Claude.

    Args:
        skill_zip: Path to skill .zip file (e.g., output/react.zip)

    Returns:
        Upload results with success/error message.
    """
    result = await upload_skill_impl({"skill_zip": skill_zip})
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


@safe_tool_decorator(
    description="Complete one-command workflow: fetch config → scrape docs → AI enhance (MANDATORY) → package → upload. Enhancement required for quality (3/10→9/10). Takes 20-45 min depending on config size. Automatically uploads to Claude if ANTHROPIC_API_KEY is set."
)
async def install_skill(
    config_name: str | None = None,
    config_path: str | None = None,
    destination: str = "output",
    auto_upload: bool = True,
    unlimited: bool = False,
    dry_run: bool = False,
) -> str:
    """
    Complete one-command workflow to install a skill.

    Args:
        config_name: Config name from API (e.g., 'react', 'django'). Mutually exclusive with config_path. Tool will fetch this config from the official API before scraping.
        config_path: Path to existing config JSON file (e.g., 'configs/custom.json'). Mutually exclusive with config_name. Use this if you already have a config file.
        destination: Output directory for skill files (default: 'output')
        auto_upload: Auto-upload to Claude after packaging (requires ANTHROPIC_API_KEY). Default: true. Set to false to skip upload.
        unlimited: Remove page limits during scraping (default: false). WARNING: Can take hours for large sites.
        dry_run: Preview workflow without executing (default: false). Shows all phases that would run.

    Returns:
        Workflow results with all phase statuses.
    """
    args = {
        "destination": destination,
        "auto_upload": auto_upload,
        "unlimited": unlimited,
        "dry_run": dry_run,
    }
    if config_name:
        args["config_name"] = config_name
    if config_path:
        args["config_path"] = config_path

    result = await install_skill_impl(args)
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


# ============================================================================
# SPLITTING TOOLS (2 tools)
# ============================================================================


@safe_tool_decorator(
    description="Split large documentation config into multiple focused skills. For 10K+ page documentation."
)
async def split_config(
    config_path: str,
    strategy: str = "auto",
    target_pages: int = 5000,
    dry_run: bool = False,
) -> str:
    """
    Split large documentation config into multiple skills.

    Args:
        config_path: Path to config JSON file (e.g., configs/godot.json)
        strategy: Split strategy: auto, none, category, router, size (default: auto)
        target_pages: Target pages per skill (default: 5000)
        dry_run: Preview without saving files (default: false)

    Returns:
        Splitting results with generated config paths.
    """
    args = {
        "config_path": config_path,
        "strategy": strategy,
        "target_pages": target_pages,
        "dry_run": dry_run,
    }
    result = await split_config_impl(args)
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


@safe_tool_decorator(
    description="Generate router/hub skill for split documentation. Creates intelligent routing to sub-skills."
)
async def generate_router(
    config_pattern: str,
    router_name: str | None = None,
) -> str:
    """
    Generate router/hub skill for split documentation.

    Args:
        config_pattern: Config pattern for sub-skills (e.g., 'configs/godot-*.json')
        router_name: Router skill name (optional, inferred from configs)

    Returns:
        Router generation results with file paths.
    """
    args = {"config_pattern": config_pattern}
    if router_name:
        args["router_name"] = router_name

    result = await generate_router_impl(args)
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


# ============================================================================
# SOURCE TOOLS (5 tools)
# ============================================================================


@safe_tool_decorator(
    description="Fetch config from API, git URL, or registered source. Supports three modes: (1) Named source from registry, (2) Direct git URL, (3) API (default). List available configs or download a specific one by name."
)
async def fetch_config(
    config_name: str | None = None,
    destination: str = "configs",
    list_available: bool = False,
    category: str | None = None,
    git_url: str | None = None,
    source: str | None = None,
    branch: str = "main",
    token: str | None = None,
    refresh: bool = False,
) -> str:
    """
    Fetch config from API, git URL, or registered source.

    Args:
        config_name: Name of the config to download (e.g., 'react', 'django', 'godot'). Required for git modes. Omit to list all available configs in API mode.
        destination: Directory to save the config file (default: 'configs/')
        list_available: List all available configs from the API (only works in API mode, default: false)
        category: Filter configs by category when listing in API mode (e.g., 'web-frameworks', 'game-engines', 'devops')
        git_url: Git repository URL containing configs. If provided, fetches from git instead of API. Supports HTTPS and SSH URLs. Example: 'https://github.com/myorg/configs.git'
        source: Named source from registry (highest priority). Use add_config_source to register sources first. Example: 'team', 'company'
        branch: Git branch to use (default: 'main'). Only used with git_url or source.
        token: Authentication token for private repos (optional). Prefer using environment variables (GITHUB_TOKEN, GITLAB_TOKEN, etc.).
        refresh: Force refresh cached git repository (default: false). Deletes cache and re-clones. Only used with git modes.

    Returns:
        Fetch results with config path or list of available configs.
    """
    args = {
        "destination": destination,
        "list_available": list_available,
        "branch": branch,
        "refresh": refresh,
    }
    if config_name:
        args["config_name"] = config_name
    if category:
        args["category"] = category
    if git_url:
        args["git_url"] = git_url
    if source:
        args["source"] = source
    if token:
        args["token"] = token

    result = await fetch_config_impl(args)
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


@safe_tool_decorator(
    description="Submit a custom config file to the community. Validates config (legacy or unified format) and creates a GitHub issue in skill-seekers-configs repo for review."
)
async def submit_config(
    config_path: str | None = None,
    config_json: str | None = None,
    testing_notes: str | None = None,
    github_token: str | None = None,
) -> str:
    """
    Submit a custom config file to the community.

    Args:
        config_path: Path to config JSON file to submit (e.g., 'configs/myframework.json')
        config_json: Config JSON as string (alternative to config_path)
        testing_notes: Notes about testing (e.g., 'Tested with 20 pages, works well')
        github_token: GitHub personal access token (or use GITHUB_TOKEN env var)

    Returns:
        Submission results with GitHub issue URL.
    """
    args = {}
    if config_path:
        args["config_path"] = config_path
    if config_json:
        args["config_json"] = config_json
    if testing_notes:
        args["testing_notes"] = testing_notes
    if github_token:
        args["github_token"] = github_token

    result = await submit_config_impl(args)
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


@safe_tool_decorator(
    description="Register a git repository as a config source. Allows fetching configs from private/team repos. Use this to set up named sources that can be referenced by fetch_config. Supports GitHub, GitLab, Gitea, Bitbucket, and custom git servers."
)
async def add_config_source(
    name: str,
    git_url: str,
    source_type: str = "github",
    token_env: str | None = None,
    branch: str = "main",
    priority: int = 100,
    enabled: bool = True,
) -> str:
    """
    Register a git repository as a config source.

    Args:
        name: Source identifier (lowercase, alphanumeric, hyphens/underscores allowed). Example: 'team', 'company-internal', 'my_configs'
        git_url: Git repository URL (HTTPS or SSH). Example: 'https://github.com/myorg/configs.git' or 'git@github.com:myorg/configs.git'
        source_type: Source type (default: 'github'). Options: 'github', 'gitlab', 'gitea', 'bitbucket', 'custom'
        token_env: Environment variable name for auth token (optional). Auto-detected if not provided. Example: 'GITHUB_TOKEN', 'GITLAB_TOKEN', 'MY_CUSTOM_TOKEN'
        branch: Git branch to use (default: 'main'). Example: 'main', 'master', 'develop'
        priority: Source priority (lower = higher priority, default: 100). Used for conflict resolution when same config exists in multiple sources.
        enabled: Whether source is enabled (default: true)

    Returns:
        Registration results with source details.
    """
    args = {
        "name": name,
        "git_url": git_url,
        "source_type": source_type,
        "branch": branch,
        "priority": priority,
        "enabled": enabled,
    }
    if token_env:
        args["token_env"] = token_env

    result = await add_config_source_impl(args)
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


@safe_tool_decorator(
    description="List all registered config sources. Shows git repositories that have been registered with add_config_source. Use this to see available sources for fetch_config."
)
async def list_config_sources(enabled_only: bool = False) -> str:
    """
    List all registered config sources.

    Args:
        enabled_only: Only show enabled sources (default: false)

    Returns:
        List of registered sources with details.
    """
    result = await list_config_sources_impl({"enabled_only": enabled_only})
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


@safe_tool_decorator(
    description="Remove a registered config source. Deletes the source from the registry. Does not delete cached git repository data."
)
async def remove_config_source(name: str) -> str:
    """
    Remove a registered config source.

    Args:
        name: Source identifier to remove. Example: 'team', 'company-internal'

    Returns:
        Removal results with success/error message.
    """
    result = await remove_config_source_impl({"name": name})
    if isinstance(result, list) and result:
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    return str(result)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Skill Seeker MCP Server - Generate Claude AI skills from documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Transport Modes:
  stdio (default): Standard input/output communication for Claude Desktop
  http: HTTP server with SSE for web-based MCP clients

Examples:
  # Stdio transport (default, backward compatible)
  python -m skill_seekers.mcp.server_fastmcp

  # HTTP transport on default port 8000
  python -m skill_seekers.mcp.server_fastmcp --http

  # HTTP transport on custom port
  python -m skill_seekers.mcp.server_fastmcp --http --port 8080

  # Debug logging
  python -m skill_seekers.mcp.server_fastmcp --http --log-level DEBUG
        """,
    )

    parser.add_argument(
        "--http",
        action="store_true",
        help="Use HTTP transport instead of stdio (default: stdio)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP server (default: 8000)",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host for HTTP server (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)",
    )

    return parser.parse_args()


def setup_logging(log_level: str):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def run_http_server(host: str, port: int):
    """Run the MCP server with HTTP transport using uvicorn."""
    try:
        import uvicorn
    except ImportError:
        logging.error("❌ Error: uvicorn package not installed")
        logging.error("Install with: pip install uvicorn")
        sys.exit(1)

    try:
        # Get the SSE Starlette app from FastMCP
        app = mcp.sse_app()

        # Add CORS middleware for cross-origin requests
        try:
            from starlette.middleware.cors import CORSMiddleware

            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            logging.info("✓ CORS middleware enabled")
        except ImportError:
            logging.warning("⚠ CORS middleware not available (starlette not installed)")

        # Add health check endpoint
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        async def health_check(request):
            """Health check endpoint."""
            return JSONResponse(
                {
                    "status": "healthy",
                    "server": "skill-seeker-mcp",
                    "version": "2.1.1",
                    "transport": "http",
                    "endpoints": {
                        "health": "/health",
                        "sse": "/sse",
                        "messages": "/messages/",
                    },
                }
            )

        # Add route before the catch-all SSE route
        app.routes.insert(0, Route("/health", health_check, methods=["GET"]))

        logging.info(f"🚀 Starting Skill Seeker MCP Server (HTTP mode)")
        logging.info(f"📡 Server URL: http://{host}:{port}")
        logging.info(f"🔗 SSE Endpoint: http://{host}:{port}/sse")
        logging.info(f"💚 Health Check: http://{host}:{port}/health")
        logging.info(f"📝 Messages: http://{host}:{port}/messages/")
        logging.info("")
        logging.info("Claude Desktop Configuration (HTTP):")
        logging.info('{')
        logging.info('  "mcpServers": {')
        logging.info('    "skill-seeker": {')
        logging.info(f'      "url": "http://{host}:{port}/sse"')
        logging.info('    }')
        logging.info('  }')
        logging.info('}')
        logging.info("")
        logging.info("Press Ctrl+C to stop the server")

        # Run the uvicorn server
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level=logging.getLogger().level,
            access_log=True,
        )
        server = uvicorn.Server(config)
        await server.serve()

    except Exception as e:
        logging.error(f"❌ Failed to start HTTP server: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def main():
    """Run the MCP server with stdio or HTTP transport."""
    import asyncio

    # Check if MCP is available
    if not MCP_AVAILABLE or mcp is None:
        print("❌ Error: mcp package not installed or FastMCP not available")
        print("Install with: pip install mcp>=1.25")
        sys.exit(1)

    # Parse command-line arguments
    args = parse_args()

    # Setup logging
    setup_logging(args.log_level)

    if args.http:
        # HTTP transport mode
        logging.info(f"🌐 Using HTTP transport on {args.host}:{args.port}")
        try:
            asyncio.run(run_http_server(args.host, args.port))
        except KeyboardInterrupt:
            logging.info("\n👋 Server stopped by user")
            sys.exit(0)
    else:
        # Stdio transport mode (default, backward compatible)
        logging.info("📺 Using stdio transport (default)")
        try:
            asyncio.run(mcp.run_stdio_async())
        except KeyboardInterrupt:
            logging.info("\n👋 Server stopped by user")
            sys.exit(0)


if __name__ == "__main__":
    main()
