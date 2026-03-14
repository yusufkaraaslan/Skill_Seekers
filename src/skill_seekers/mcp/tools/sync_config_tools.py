"""Sync-config MCP tool for Skill Seekers MCP Server.

Provides the ``sync_config`` tool that diffs a config's start_urls against
the live docs site and optionally applies the update.
"""

try:
    from mcp.types import TextContent
except ImportError:

    class TextContent:
        """Fallback TextContent for when MCP is not installed."""

        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text


async def sync_config_tool(args: dict) -> list[TextContent]:
    """Sync a config file's start_urls against what's live on the docs site.

    Crawls seed/nav pages, discovers internal links, diffs against the
    config's existing ``start_urls``, and optionally writes the update.

    Args:
        args: Dictionary containing:
            - config_path (str): Path to the config JSON file.
            - apply (bool, optional): Write changes back (default: False).
            - depth (int, optional): BFS crawl depth (default: 2).
            - max_pages (int, optional): Max URLs to discover (default: 500).
            - rate_limit (float, optional): Seconds between requests.
            - source_index (int, optional): Documentation source index (default: 0).

    Returns:
        List[TextContent]: Report of added/removed URLs, or error message.
    """
    config_path = args.get("config_path", "")
    if not config_path:
        return [TextContent(type="text", text="Error: config_path is required")]

    try:
        from skill_seekers.cli.sync_config import sync_config

        result = sync_config(
            config_path=config_path,
            apply=args.get("apply", False),
            depth=args.get("depth", 2),
            max_pages=args.get("max_pages", 500),
            rate_limit=args.get("rate_limit"),
            source_index=args.get("source_index", 0),
        )
    except FileNotFoundError:
        return [TextContent(type="text", text=f"Error: Config file not found: {config_path}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error syncing config: {e}")]

    if result.get("error"):
        return [TextContent(type="text", text=f"Error: {result['error']}")]

    lines = []
    added = result["added"]
    removed = result["removed"]

    if added:
        lines.append(f"New pages ({len(added)}):")
        for url in added:
            lines.append(f"  + {url}")
    if removed:
        lines.append(f"Removed pages ({len(removed)}):")
        for url in removed:
            lines.append(f"  - {url}")
    if not added and not removed:
        lines.append("Config is up to date. No changes detected.")
    else:
        lines.append(
            f"\nSummary: {len(added)} new, {len(removed)} removed "
            f"(discovered {result['total_discovered']}, "
            f"configured {result['total_configured']})"
        )
        if result["applied"]:
            lines.append(f"Updated {config_path}")
        else:
            lines.append(f"Run with apply=true to update {config_path}")

    return [TextContent(type="text", text="\n".join(lines))]
