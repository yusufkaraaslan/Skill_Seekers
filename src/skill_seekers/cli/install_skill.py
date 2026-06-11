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
import sys

# Import the MCP tool function (with lazy loading)
try:
    from skill_seekers.mcp.server import install_skill_tool

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    install_skill_tool = None


def main(args=None):
    """Main entry point for CLI"""
    from skill_seekers.cli.exit_codes import EXIT_ERROR, EXIT_INTERRUPT, EXIT_SUCCESS

    # Check MCP availability first
    if not MCP_AVAILABLE:
        print("\n❌ Error: MCP package not installed")
        print("\nThe 'install' command requires MCP support.")
        print("Install with:")
        print("  pip install skill-seekers[mcp]")
        print("\nOr use these alternatives:")
        print("  skill-seekers scrape --config react")
        print("  skill-seekers package output/react/")
        print()
        sys.exit(EXIT_ERROR)

    if args is None:
        # Single source of flags: the central InstallParser.
        from skill_seekers.cli.parsers.install_parser import InstallParser

        parser = InstallParser().build_standalone()
        args = parser.parse_args()

    # Auto-detect target platform if not specified
    if args.target is None:
        from skill_seekers.cli.agent_client import AgentClient

        args.target = AgentClient.detect_default_target()

    # Determine if config is a name or path
    config_arg = args.config
    if config_arg.endswith(".json") or "/" in config_arg or "\\" in config_arg:
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
        "dry_run": args.dry_run,
        "target": args.target,
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
            return EXIT_ERROR
        return EXIT_SUCCESS

    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
        return EXIT_INTERRUPT
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
