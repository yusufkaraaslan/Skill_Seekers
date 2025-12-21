#!/usr/bin/env python3
"""
Complete Skill Installation Workflow
One-command installation: fetch → scrape → enhance → package → upload

This CLI tool orchestrates the complete skill installation workflow by calling
the install_skill MCP tool.

Usage:
    skill-seekers install --config react
    skill-seekers install --config configs/custom.json --no-upload
    skill-seekers install --config django --unlimited
    skill-seekers install --config react --dry-run

Examples:
    # Install React skill from official configs
    skill-seekers install --config react

    # Install from local config file
    skill-seekers install --config configs/custom.json

    # Install without uploading
    skill-seekers install --config django --no-upload

    # Preview workflow without executing
    skill-seekers install --config react --dry-run
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path to import MCP server
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the MCP tool function
from skill_seekers.mcp.server import install_skill_tool


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description="Complete skill installation workflow (fetch → scrape → enhance → package → upload)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install React skill from official API
  skill-seekers install --config react

  # Install from local config file
  skill-seekers install --config configs/custom.json

  # Install without uploading
  skill-seekers install --config django --no-upload

  # Unlimited scraping (no page limits)
  skill-seekers install --config godot --unlimited

  # Preview workflow (dry run)
  skill-seekers install --config react --dry-run

Important:
  - Enhancement is MANDATORY (30-60 sec) for quality (3/10→9/10)
  - Total time: 20-45 minutes (mostly scraping)
  - Auto-uploads to Claude if ANTHROPIC_API_KEY is set

Phases:
  1. Fetch config (if config name provided)
  2. Scrape documentation
  3. AI Enhancement (MANDATORY - no skip option)
  4. Package to .zip
  5. Upload to Claude (optional)
"""
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Config name (e.g., 'react') or path (e.g., 'configs/custom.json')"
    )

    parser.add_argument(
        "--destination",
        default="output",
        help="Output directory for skill files (default: output/)"
    )

    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Skip automatic upload to Claude"
    )

    parser.add_argument(
        "--unlimited",
        action="store_true",
        help="Remove page limits during scraping (WARNING: Can take hours)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview workflow without executing"
    )

    args = parser.parse_args()

    # Determine if config is a name or path
    config_arg = args.config
    if config_arg.endswith('.json') or '/' in config_arg or '\\' in config_arg:
        # It's a path
        config_path = config_arg
        config_name = None
    else:
        # It's a name
        config_name = config_arg
        config_path = None

    # Build arguments for install_skill_tool
    tool_args = {
        "config_name": config_name,
        "config_path": config_path,
        "destination": args.destination,
        "auto_upload": not args.no_upload,
        "unlimited": args.unlimited,
        "dry_run": args.dry_run
    }

    # Run async tool
    try:
        result = asyncio.run(install_skill_tool(tool_args))

        # Print output
        for content in result:
            print(content.text)

        # Return success/failure based on output
        output_text = result[0].text
        if "❌" in output_text and "WORKFLOW COMPLETE" not in output_text:
            return 1
        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
