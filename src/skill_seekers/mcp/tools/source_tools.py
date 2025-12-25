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
import re
from pathlib import Path
from typing import Any, List

# MCP types (imported conditionally)
try:
    from mcp.types import TextContent
    MCP_AVAILABLE = True
except ImportError:
    TextContent = None
    MCP_AVAILABLE = False

import httpx


async def fetch_config_tool(args: dict) -> List[TextContent]:
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


async def submit_config_tool(args: dict) -> List[TextContent]:
    """
    Submit a custom config to skill-seekers-configs repository via GitHub issue.

    Validates the config (both legacy and unified formats) and creates a GitHub
    issue for community review.

    Args:
        args: Dictionary containing:
            - config_path: Path to config JSON file (optional)
            - config_json: Config JSON as string (optional, alternative to config_path)
            - testing_notes: Notes about testing (optional)
            - github_token: GitHub personal access token (optional, can use GITHUB_TOKEN env var)

    Returns:
        List of TextContent with submission results
    """
    try:
        from github import Github, GithubException
    except ImportError:
        return [TextContent(type="text", text="❌ Error: PyGithub not installed.\n\nInstall with: pip install PyGithub")]

    # Import config validator
    try:
        from pathlib import Path
        import sys
        CLI_DIR = Path(__file__).parent.parent.parent / "cli"
        sys.path.insert(0, str(CLI_DIR))
        from config_validator import ConfigValidator
    except ImportError:
        ConfigValidator = None

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


async def add_config_source_tool(args: dict) -> List[TextContent]:
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


async def list_config_sources_tool(args: dict) -> List[TextContent]:
    """
    List all registered config sources.

    Shows git repositories that have been registered with add_config_source.

    Args:
        args: Dictionary containing:
            - enabled_only: Only show enabled sources (default: false)

    Returns:
        List of TextContent with source list
    """
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


async def remove_config_source_tool(args: dict) -> List[TextContent]:
    """
    Remove a registered config source.

    Deletes the source from the registry. Does not delete cached git repository data.

    Args:
        args: Dictionary containing:
            - name: Source identifier to remove (required)

    Returns:
        List of TextContent with removal results
    """
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
