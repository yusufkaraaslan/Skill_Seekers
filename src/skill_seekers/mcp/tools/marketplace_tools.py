"""
Marketplace management tools for MCP server.

This module contains tools for managing plugin marketplace repositories:
- add_marketplace: Register a plugin marketplace repository
- list_marketplaces: List all registered marketplace repositories
- remove_marketplace: Remove a registered marketplace
- publish_to_marketplace: Publish a packaged skill to a marketplace
"""

# MCP types (imported conditionally)
try:
    from mcp.types import TextContent

    MCP_AVAILABLE = True
except ImportError:

    class TextContent:
        """Fallback TextContent for when MCP is not installed"""

        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text

    MCP_AVAILABLE = False


async def add_marketplace_tool(args: dict) -> list[TextContent]:
    """Register a plugin marketplace repository."""
    from skill_seekers.mcp.marketplace_manager import MarketplaceManager

    name = args.get("name")
    git_url = args.get("git_url")
    token_env = args.get("token_env")
    branch = args.get("branch", "main")
    author_name = args.get("author_name", "")
    author_email = args.get("author_email", "")
    enabled = args.get("enabled", True)

    try:
        if not name:
            return [TextContent(type="text", text="❌ Error: 'name' parameter is required")]
        if not git_url:
            return [TextContent(type="text", text="❌ Error: 'git_url' parameter is required")]

        author = {"name": author_name, "email": author_email}

        manager = MarketplaceManager()
        marketplace = manager.add_marketplace(
            name=name,
            git_url=git_url,
            token_env=token_env,
            branch=branch,
            author=author,
            enabled=enabled,
        )

        is_update = marketplace["added_at"] != marketplace["updated_at"]

        result = f"""✅ Marketplace {"updated" if is_update else "registered"} successfully!

📛 Name: {marketplace["name"]}
📁 Repository: {marketplace["git_url"]}
🌿 Branch: {marketplace["branch"]}
🔑 Token env: {marketplace["token_env"]}
👤 Author: {marketplace["author"]["name"]} <{marketplace["author"]["email"]}>
✓ Enabled: {marketplace["enabled"]}
🕒 Added: {marketplace["added_at"][:19]}

Usage:
  # Publish a skill to this marketplace
  publish_to_marketplace(skill_dir="output/my-skill", marketplace="{marketplace["name"]}")

  # List all marketplaces
  list_marketplaces()

💡 Set {marketplace["token_env"]} environment variable for private repos
"""
        return [TextContent(type="text", text=result)]

    except ValueError as e:
        return [TextContent(type="text", text=f"❌ Validation Error: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def list_marketplaces_tool(args: dict) -> list[TextContent]:
    """List all registered plugin marketplace repositories."""
    from skill_seekers.mcp.marketplace_manager import MarketplaceManager

    enabled_only = args.get("enabled_only", False)

    try:
        manager = MarketplaceManager()
        marketplaces = manager.list_marketplaces(enabled_only=enabled_only)

        if not marketplaces:
            result = """📋 No marketplaces registered

To add a marketplace:
  add_marketplace(
    name="my-plugins",
    git_url="https://github.com/myorg/plugins.git",
    author_name="My Team",
    author_email="team@example.com"
  )

💡 Once added, use: publish_to_marketplace(skill_dir="...", marketplace="my-plugins")
"""
            return [TextContent(type="text", text=result)]

        result = f"📋 Plugin Marketplaces ({len(marketplaces)} total"
        if enabled_only:
            result += ", enabled only"
        result += ")\n\n"

        for mp in marketplaces:
            status_icon = "✓" if mp.get("enabled", True) else "✗"
            author = mp.get("author", {})
            author_str = f"{author.get('name', '')} <{author.get('email', '')}>"
            result += f"{status_icon} **{mp['name']}**\n"
            result += f"  📁 {mp['git_url']}\n"
            result += f"  🌿 Branch: {mp['branch']} | 🔑 Token: {mp['token_env']}\n"
            result += f"  👤 Author: {author_str}\n"
            result += f"  🕒 Added: {mp['added_at'][:19]}\n"
            result += "\n"

        result += """Usage:
  # Publish skill to a marketplace
  publish_to_marketplace(skill_dir="output/my-skill", marketplace="MARKETPLACE_NAME")

  # Add new marketplace
  add_marketplace(name="...", git_url="...")

  # Remove marketplace
  remove_marketplace(name="MARKETPLACE_NAME")
"""
        return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def remove_marketplace_tool(args: dict) -> list[TextContent]:
    """Remove a registered plugin marketplace."""
    from skill_seekers.mcp.marketplace_manager import MarketplaceManager

    name = args.get("name")

    try:
        if not name:
            return [TextContent(type="text", text="❌ Error: 'name' parameter is required")]

        manager = MarketplaceManager()
        removed = manager.remove_marketplace(name)

        if removed:
            result = f"""✅ Marketplace removed successfully!

📛 Removed: {name}

⚠️  Note: Cached repository data is NOT deleted
To free disk space, manually delete: ~/.skill-seekers/cache/marketplace_{name}/
"""
            return [TextContent(type="text", text=result)]
        else:
            sources = manager.list_marketplaces()
            available = [m["name"] for m in sources]
            result = f"""❌ Marketplace '{name}' not found

Available marketplaces: {", ".join(available) if available else "none"}
"""
            return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def publish_to_marketplace_tool(args: dict) -> list[TextContent]:
    """Publish a packaged skill to a plugin marketplace repository."""
    from skill_seekers.mcp.marketplace_publisher import MarketplacePublisher

    skill_dir = args.get("skill_dir")
    marketplace = args.get("marketplace")
    category = args.get("category", "development")
    skill_name = args.get("skill_name")
    description = args.get("description")
    create_branch = args.get("create_branch", False)
    force = args.get("force", False)

    try:
        if not skill_dir:
            return [TextContent(type="text", text="❌ Error: 'skill_dir' parameter is required")]
        if not marketplace:
            return [TextContent(type="text", text="❌ Error: 'marketplace' parameter is required")]

        publisher = MarketplacePublisher()
        result = publisher.publish(
            skill_dir=skill_dir,
            marketplace_name=marketplace,
            category=category,
            skill_name=skill_name,
            description=description,
            create_branch=create_branch,
            force=force,
        )

        if result["success"]:
            output = f"""✅ Skill published to marketplace successfully!

📦 Plugin: {result["plugin_path"]}
🏪 Marketplace: {marketplace}
🏷️  Category: {category}
🌿 Branch: {result["branch"]}
📝 Commit: {result["commit_sha"]}

{result["message"]}
"""
            return [TextContent(type="text", text=output)]
        else:
            return [TextContent(type="text", text=f"❌ Publish failed: {result['message']}")]

    except (FileNotFoundError, KeyError, ValueError, RuntimeError) as e:
        return [TextContent(type="text", text=f"❌ {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
