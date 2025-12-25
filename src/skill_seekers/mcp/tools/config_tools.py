"""
Config management tools for Skill Seeker MCP Server.

This module provides tools for generating, listing, and validating configuration files
for documentation scraping.
"""

import json
import sys
from pathlib import Path
from typing import Any, List

try:
    from mcp.types import TextContent
except ImportError:
    TextContent = None

# Path to CLI tools
CLI_DIR = Path(__file__).parent.parent.parent / "cli"

# Import config validator for validation
sys.path.insert(0, str(CLI_DIR))
try:
    from config_validator import ConfigValidator
except ImportError:
    ConfigValidator = None  # Graceful degradation if not available


async def generate_config(args: dict) -> List[TextContent]:
    """
    Generate a config file for documentation scraping.

    Interactively creates a JSON config for any documentation website with default
    selectors and sensible defaults. The config can be further customized after creation.

    Args:
        args: Dictionary containing:
            - name (str): Skill name (lowercase, alphanumeric, hyphens, underscores)
            - url (str): Base documentation URL (must include http:// or https://)
            - description (str): Description of when to use this skill
            - max_pages (int, optional): Maximum pages to scrape (default: 100, use -1 for unlimited)
            - unlimited (bool, optional): Remove all limits - scrape all pages (default: False). Overrides max_pages.
            - rate_limit (float, optional): Delay between requests in seconds (default: 0.5)

    Returns:
        List[TextContent]: Success message with config path and next steps, or error message.
    """
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


async def list_configs(args: dict) -> List[TextContent]:
    """
    List all available preset configurations.

    Scans the configs directory and lists all available config files with their
    basic information (name, URL, description).

    Args:
        args: Dictionary (empty, no parameters required)

    Returns:
        List[TextContent]: Formatted list of available configs with details, or error if no configs found.
    """
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


async def validate_config(args: dict) -> List[TextContent]:
    """
    Validate a config file for errors.

    Validates both legacy (single-source) and unified (multi-source) config formats.
    Checks for required fields, valid URLs, proper structure, and provides detailed
    feedback on any issues found.

    Args:
        args: Dictionary containing:
            - config_path (str): Path to config JSON file to validate

    Returns:
        List[TextContent]: Validation results with format details and any errors/warnings, or error message.
    """
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
