"""
Source management tools for MCP server.

This module contains tools for managing config sources:
- fetch_config: Fetch configs from API, git URL, or named sources
- submit_config: Submit configs to the community repository
- add_config_source: Register a git repository as a config source
- list_config_sources: List all registered config sources
- remove_config_source: Remove a registered config source
"""

import json
import os
from pathlib import Path

# MCP types (imported conditionally)
from skill_seekers.mcp.tools._common import TextContent, text_response

# Community-registry submission engine lives in the services layer (shared
# with the CLI scan publish flow). REGISTRY_REPO and find_existing_submission
# stay re-exported here as part of this module's public surface.
from skill_seekers.services.source_manager import (
    REGISTRY_REPO,  # noqa: F401
    find_existing_submission,  # noqa: F401
    submit_config,
)

import httpx

from skill_seekers.cli.utils import retry_with_backoff_async


async def _get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: dict | None = None,
    base_delay: float = 1.0,
) -> httpx.Response:
    """GET with exponential backoff on transient failures (E2.6, #92).

    Retries connection/timeout errors and 5xx responses (3 attempts, then
    1s/2s waits). 4xx responses are returned un-retried — a 404 is a real
    answer the caller handles (e.g. "config not found"), not a fault.
    """

    async def _attempt() -> httpx.Response:
        response = await client.get(url, params=params)
        if response.status_code >= 500:
            response.raise_for_status()
        return response

    return await retry_with_backoff_async(
        _attempt, base_delay=base_delay, operation_name=f"GET {url}"
    )


async def fetch_config_tool(args: dict) -> list[TextContent]:
    """
    Fetch config from API, git URL, or named source.

    Supports three modes:
    1. Named source from registry (highest priority)
    2. Direct git URL
    3. API (default, backward compatible)

    Args:
        args: Dictionary containing:
            - config_name: Name of config to download (optional for API list mode)
            - destination: Directory to save config file (default: "configs")
            - list_available: List all available configs from API (default: false)
            - category: Filter configs by category when listing (optional)
            - git_url: Git repository URL (enables git mode)
            - source: Named source from registry (enables named source mode)
            - branch: Git branch to use (default: "main")
            - token: Authentication token for private repos (optional)
            - refresh: Force refresh cached git repository (default: false)

    Returns:
        List of TextContent with fetch results or config list
    """
    from skill_seekers.services.git_repo import GitConfigRepo
    from skill_seekers.services.source_manager import SourceManager

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
                return [
                    TextContent(
                        type="text",
                        text="❌ Error: config_name is required when using source parameter",
                    )
                ]

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
                    force_refresh=force_refresh,
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

            with open(config_file, "w") as f:
                json.dump(config_data, f, indent=2)

            result = f"""✅ Config fetched from git source successfully!

📦 Config: {config_name}
📂 Saved to: {config_file}
🔗 Source: {source_name}
🌿 Branch: {branch}
📁 Repository: {git_url}
🔄 Refreshed: {"Yes (forced)" if force_refresh else "No (used cache)"}

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
                return [
                    TextContent(
                        type="text",
                        text="❌ Error: config_name is required when using git_url parameter",
                    )
                ]

            # Clone/pull repository
            git_repo = GitConfigRepo()
            source_name_temp = f"temp_{config_name}"

            try:
                repo_path = git_repo.clone_or_pull(
                    source_name=source_name_temp,
                    git_url=git_url,
                    branch=branch,
                    token=token,
                    force_refresh=force_refresh,
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

            with open(config_file, "w") as f:
                json.dump(config_data, f, indent=2)

            result = f"""✅ Config fetched from git URL successfully!

📦 Config: {config_name}
📂 Saved to: {config_file}
📁 Repository: {git_url}
🌿 Branch: {branch}
🔄 Refreshed: {"Yes (forced)" if force_refresh else "No (used cache)"}

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

                    response = await _get_with_retry(client, list_url, params=params)
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

                    result += (
                        "\n💡 To download a config, use: fetch_config with config_name='<name>'\n"
                    )
                    result += f"📚 API Docs: {API_BASE_URL}/docs\n"

                    return [TextContent(type="text", text=result)]

                # Download specific config
                if not config_name:
                    return [
                        TextContent(
                            type="text",
                            text="❌ Error: Please provide config_name or set list_available=true",
                        )
                    ]

                # Get config details first
                detail_url = f"{API_BASE_URL}/api/configs/{config_name}"
                detail_response = await _get_with_retry(client, detail_url)

                if detail_response.status_code == 404:
                    return [
                        TextContent(
                            type="text",
                            text=f"❌ Config '{config_name}' not found. Use list_available=true to see available configs.",
                        )
                    ]

                detail_response.raise_for_status()
                config_info = detail_response.json()

                # Download the actual config file using the download_url from API response
                download_url = config_info.get("download_url")
                if not download_url:
                    return [
                        TextContent(
                            type="text",
                            text=f"❌ Config '{config_name}' has no download_url. Contact support.",
                        )
                    ]

                download_response = await _get_with_retry(client, download_url)
                download_response.raise_for_status()
                config_data = download_response.json()

                # Save to destination
                dest_path = Path(destination)
                dest_path.mkdir(parents=True, exist_ok=True)
                config_file = dest_path / f"{config_name}.json"

                with open(config_file, "w") as f:
                    json.dump(config_data, f, indent=2)

                # Build result message
                result = f"""✅ Config downloaded successfully!

📦 Config: {config_name}
📂 Saved to: {config_file}
📊 Category: {config_info.get("category", "uncategorized")}
🏷️  Tags: {", ".join(config_info.get("tags", []))}
📄 Type: {config_info.get("type", "unknown")}
📝 Description: {config_info.get("description", "No description")}

🔗 Source: {config_info.get("primary_source", "N/A")}
📏 Max pages: {config_info.get("max_pages", "N/A")}
📦 File size: {config_info.get("file_size", "N/A")} bytes
🕒 Last updated: {config_info.get("last_updated", "N/A")}

Next steps:
  1. Review config: cat {config_file}
  2. Estimate pages: Use estimate_pages tool
  3. Scrape docs: Use scrape_docs tool

💡 More configs: Use list_available=true to see all available configs
"""

                return [TextContent(type="text", text=result)]

    except httpx.HTTPError as e:
        return [
            TextContent(
                type="text",
                text=f"❌ HTTP Error: {str(e)}\n\nCheck your internet connection or try again later.",
            )
        ]
    except json.JSONDecodeError as e:
        return [
            TextContent(type="text", text=f"❌ JSON Error: Invalid response from API: {str(e)}")
        ]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def submit_config_tool(args: dict) -> list[TextContent]:
    """
    Submit a custom config to skill-seekers-configs repository via GitHub issue.

    Validates the config (both legacy and unified formats) and creates a GitHub
    issue for community review. Thin MCP wrapper over
    ``services.source_manager.submit_config``.

    Args:
        args: Dictionary containing:
            - config_path: Path to config JSON file (optional)
            - config_json: Config JSON as string (optional, alternative to config_path)
            - testing_notes: Notes about testing (optional)
            - github_token: GitHub personal access token (optional, can use GITHUB_TOKEN env var)

    Returns:
        List of TextContent with submission results
    """
    result = submit_config(
        config_path=args.get("config_path"),
        config_json=args.get("config_json"),
        testing_notes=args.get("testing_notes", ""),
        github_token=args.get("github_token"),
    )
    return text_response(result["message"])


async def add_config_source_tool(args: dict) -> list[TextContent]:
    """
    Register a git repository as a config source.

    Allows fetching configs from private/team repos. Use this to set up named
    sources that can be referenced by fetch_config.

    Args:
        args: Dictionary containing:
            - name: Source identifier (required)
            - git_url: Git repository URL (required)
            - source_type: Source type (default: "github")
            - token_env: Environment variable name for auth token (optional)
            - branch: Git branch to use (default: "main")
            - priority: Source priority (default: 100, lower = higher priority)
            - enabled: Whether source is enabled (default: true)

    Returns:
        List of TextContent with registration results
    """
    from skill_seekers.services.source_manager import SourceManager

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
            enabled=enabled,
        )

        # Check if this is an update
        is_update = "updated_at" in source and source["added_at"] != source["updated_at"]

        result = f"""✅ Config source {"updated" if is_update else "registered"} successfully!

📛 Name: {source["name"]}
📁 Repository: {source["git_url"]}
🔖 Type: {source["type"]}
🌿 Branch: {source["branch"]}
🔑 Token env: {source.get("token_env", "None")}
⚡ Priority: {source["priority"]} (lower = higher priority)
✓ Enabled: {source["enabled"]}
🕒 Added: {source["added_at"][:19]}

Usage:
  # Fetch config from this source
  fetch_config(source="{source["name"]}", config_name="your-config")

  # List all sources
  list_config_sources()

  # Remove this source
  remove_config_source(name="{source["name"]}")

💡 Make sure to set {source.get("token_env", "GIT_TOKEN")} environment variable for private repos
"""

        return [TextContent(type="text", text=result)]

    except ValueError as e:
        return [TextContent(type="text", text=f"❌ Validation Error: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def list_config_sources_tool(args: dict) -> list[TextContent]:
    """
    List all registered config sources.

    Shows git repositories that have been registered with add_config_source.

    Args:
        args: Dictionary containing:
            - enabled_only: Only show enabled sources (default: false)

    Returns:
        List of TextContent with source list
    """
    from skill_seekers.services.source_manager import SourceManager

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
    """
    Remove a registered config source.

    Deletes the source from the registry. Does not delete cached git repository data.

    Args:
        args: Dictionary containing:
            - name: Source identifier to remove (required)

    Returns:
        List of TextContent with removal results
    """
    from skill_seekers.services.source_manager import SourceManager

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

Available sources: {", ".join(available) if available else "none"}

To see all sources:
  list_config_sources()
"""
            return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def push_config_tool(args: dict) -> list[TextContent]:
    """
    Push a config to a registered config source repository.

    Validates the config, places it in the correct category directory,
    commits, and pushes to the source repo.

    Args:
        args: Dictionary containing:
            - config_path: Path to config JSON file (required)
            - source_name: Registered source name, e.g., "spyke" (required)
            - category: Category directory (e.g., "game-engines"). Auto-detected if omitted.
            - create_branch: Create feature branch instead of pushing to main (default: false)
            - force: Overwrite existing config (default: false)

    Returns:
        List of TextContent with push results
    """
    config_path = args.get("config_path")
    source_name = args.get("source_name")
    category = args.get("category", "auto")
    create_branch = args.get("create_branch", False)
    force = args.get("force", False)

    if not config_path:
        return [TextContent(type="text", text="❌ Missing required parameter: config_path")]
    if not source_name:
        return [TextContent(type="text", text="❌ Missing required parameter: source_name")]

    try:
        from skill_seekers.services.config_publisher import ConfigPublisher

        publisher = ConfigPublisher()
        result = publisher.publish(
            config_path=config_path,
            source_name=source_name,
            category=category,
            create_branch=create_branch,
            force=force,
        )

        output = f"""✅ Config pushed successfully!

📄 Config: {result["config_name"]}
📂 Path: {result["config_path"]}
🏷️  Category: {result["category"]}
📦 Source: {result["source"]}
🔀 Branch: {result["branch"]}
📝 Commit: {result["commit_sha"]}
💬 Message: {result["message"]}

To fetch this config:
  fetch_config(source="{result["source"]}", config_name="{result["config_name"]}")
"""
        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Push failed: {str(e)}")]
