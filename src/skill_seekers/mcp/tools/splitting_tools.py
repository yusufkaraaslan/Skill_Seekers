"""
Splitting tools for Skill Seeker MCP Server.

This module provides tools for splitting large documentation configs into multiple
focused skills and generating router/hub skills for managing split documentation.
"""

import glob

from skill_seekers.mcp.tools._common import TextContent, run_cli_tool


async def split_config(args: dict) -> list[TextContent]:
    """
    Split large configs into multiple focused skills.

    Supports both documentation and unified (multi-source) configs:
    - Documentation configs: Split by categories, size, or create router skills
    - Unified configs: Split by source type (documentation, github, pdf,
      jupyter, html, openapi, asciidoc, pptx, confluence, notion, rss,
      manpage, chat)

    For large documentation sites (10K+ pages), this tool splits the config into
    multiple smaller configs. For unified configs with multiple sources, splits
    into separate configs per source type.

    Args:
        args: Dictionary containing:
            - config_path (str): Path to config JSON file (e.g., configs/godot.json or configs/react_unified.json)
            - strategy (str, optional): Split strategy: auto, none, source, category, router, size (default: auto)
                                       'source' strategy is for unified configs only
            - target_pages (int, optional): Target pages per skill for doc configs (default: 5000)
            - dry_run (bool, optional): Preview without saving files (default: False)

    Returns:
        List[TextContent]: Split results showing created configs and recommendations,
                          or error message if split failed.

    Note:
        Runs split_config.main() in-process (Phase 5d). The old subprocess
        timeout no longer applies — the "Maximum time" line in the output is
        advisory only.
    """
    config_path = args["config_path"]
    strategy = args.get("strategy", "auto")
    target_pages = args.get("target_pages", 5000)
    dry_run = args.get("dry_run", False)

    argv = [
        config_path,
        "--strategy",
        strategy,
        "--target-pages",
        str(target_pages),
    ]
    if dry_run:
        argv.append("--dry-run")

    # Advisory only (output text); the in-process call is unbounded
    timeout = 300

    progress_msg = "✂️ Splitting configuration...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    # split_config.main() takes no args parameter and parses sys.argv through
    # its own parser — run_cli_main patches sys.argv for the call.
    from skill_seekers.cli import split_config as split_config_cli

    return run_cli_tool(split_config_cli.main, argv, progress_msg)


async def generate_router(args: dict) -> list[TextContent]:
    """
    Generate router/hub skill for split documentation.

    Creates an intelligent routing skill that helps users navigate between split
    sub-skills. The router skill analyzes user queries and directs them to the
    appropriate sub-skill based on content categories.

    Args:
        args: Dictionary containing:
            - config_pattern (str): Config pattern for sub-skills (e.g., 'configs/godot-*.json')
            - router_name (str, optional): Router skill name (optional, inferred from configs)

    Returns:
        List[TextContent]: Router skill creation results with usage instructions,
                          or error message if generation failed.

    Note:
        Runs generate_router.main() in-process (Phase 5d). The old subprocess
        timeout no longer applies — the "Maximum time" line in the output is
        advisory only.
    """
    config_pattern = args["config_pattern"]
    router_name = args.get("router_name")

    # Expand glob pattern
    config_files = glob.glob(config_pattern)

    if not config_files:
        return [
            TextContent(type="text", text=f"❌ No config files match pattern: {config_pattern}")
        ]

    argv = list(config_files)
    if router_name:
        argv.extend(["--name", router_name])

    # Advisory only (output text); the in-process call is unbounded
    timeout = 300

    progress_msg = "🧭 Generating router skill...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    # generate_router.main() takes no args parameter and parses sys.argv
    # through its own parser — run_cli_main patches sys.argv for the call.
    from skill_seekers.cli import generate_router as generate_router_cli

    return run_cli_tool(generate_router_cli.main, argv, progress_msg)
