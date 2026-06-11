#!/usr/bin/env python3
"""
Config Source Manager
Manages registry of custom config sources (git repositories) and community
config submissions (GitHub issues against the registry repo)
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


class SourceManager:
    """Manages config source registry at ~/.skill-seekers/sources.json"""

    def __init__(self, config_dir: str | None = None):
        """
        Initialize source manager.

        Args:
            config_dir: Base config directory. Defaults to ~/.skill-seekers/
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".skill-seekers"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Registry file path
        self.registry_file = self.config_dir / "sources.json"

        # Initialize registry if it doesn't exist
        if not self.registry_file.exists():
            self._write_registry({"version": "1.0", "sources": []})

    def add_source(
        self,
        name: str,
        git_url: str,
        source_type: str = "github",
        token_env: str | None = None,
        branch: str = "main",
        priority: int = 100,
        enabled: bool = True,
    ) -> dict:
        """
        Add or update a config source.

        Args:
            name: Source identifier (lowercase, alphanumeric + hyphens/underscores)
            git_url: Git repository URL
            source_type: Source type (github, gitlab, bitbucket, custom)
            token_env: Environment variable name for auth token
            branch: Git branch to use (default: main)
            priority: Source priority (lower = higher priority, default: 100)
            enabled: Whether source is enabled (default: True)

        Returns:
            Source dictionary

        Raises:
            ValueError: If name is invalid or git_url is empty
        """
        # Validate name
        if not name or not name.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                f"Invalid source name '{name}'. Must be alphanumeric with optional hyphens/underscores."
            )

        # Validate git_url
        if not git_url or not git_url.strip():
            raise ValueError("git_url cannot be empty")

        # Auto-detect token_env if not provided
        if token_env is None:
            token_env = self._default_token_env(source_type)

        # Create source entry
        source = {
            "name": name.lower(),
            "git_url": git_url.strip(),
            "type": source_type.lower(),
            "token_env": token_env,
            "branch": branch,
            "enabled": enabled,
            "priority": priority,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Load registry
        registry = self._read_registry()

        # Check if source exists
        existing_index = None
        for i, existing_source in enumerate(registry["sources"]):
            if existing_source["name"] == source["name"]:
                existing_index = i
                # Preserve added_at timestamp
                source["added_at"] = existing_source.get("added_at", source["added_at"])
                break

        # Add or update
        if existing_index is not None:
            registry["sources"][existing_index] = source
        else:
            registry["sources"].append(source)

        # Sort by priority (lower first)
        registry["sources"].sort(key=lambda s: s["priority"])

        # Save registry
        self._write_registry(registry)

        return source

    def get_source(self, name: str) -> dict:
        """
        Get source by name.

        Args:
            name: Source identifier

        Returns:
            Source dictionary

        Raises:
            KeyError: If source not found
        """
        registry = self._read_registry()

        # Search for source (case-insensitive)
        name_lower = name.lower()
        for source in registry["sources"]:
            if source["name"] == name_lower:
                return source

        # Not found - provide helpful error
        available = [s["name"] for s in registry["sources"]]
        raise KeyError(
            f"Source '{name}' not found. Available sources: {', '.join(available) if available else 'none'}"
        )

    def list_sources(self, enabled_only: bool = False) -> list[dict]:
        """
        List all config sources.

        Args:
            enabled_only: If True, only return enabled sources

        Returns:
            List of source dictionaries (sorted by priority)
        """
        registry = self._read_registry()

        if enabled_only:
            return [s for s in registry["sources"] if s.get("enabled", True)]

        return registry["sources"]

    def remove_source(self, name: str) -> bool:
        """
        Remove source by name.

        Args:
            name: Source identifier

        Returns:
            True if removed, False if not found
        """
        registry = self._read_registry()

        # Find source index
        name_lower = name.lower()
        for i, source in enumerate(registry["sources"]):
            if source["name"] == name_lower:
                # Remove source
                del registry["sources"][i]
                # Save registry
                self._write_registry(registry)
                return True

        return False

    def update_source(self, name: str, **kwargs) -> dict:
        """
        Update specific fields of an existing source.

        Args:
            name: Source identifier
            **kwargs: Fields to update (git_url, branch, enabled, priority, etc.)

        Returns:
            Updated source dictionary

        Raises:
            KeyError: If source not found
        """
        # Get existing source
        source = self.get_source(name)

        # Update allowed fields
        allowed_fields = {"git_url", "type", "token_env", "branch", "enabled", "priority"}
        for field, value in kwargs.items():
            if field in allowed_fields:
                source[field] = value

        # Update timestamp
        source["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Save changes
        registry = self._read_registry()
        for i, s in enumerate(registry["sources"]):
            if s["name"] == source["name"]:
                registry["sources"][i] = source
                break

        # Re-sort by priority
        registry["sources"].sort(key=lambda s: s["priority"])

        self._write_registry(registry)

        return source

    def _read_registry(self) -> dict:
        """
        Read registry from file.

        Returns:
            Registry dictionary
        """
        try:
            with open(self.registry_file, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupted registry file: {e}") from e

    def _write_registry(self, registry: dict) -> None:
        """
        Write registry to file atomically.

        Args:
            registry: Registry dictionary
        """
        # Validate schema
        if "version" not in registry or "sources" not in registry:
            raise ValueError("Invalid registry schema")

        # Atomic write: write to temp file, then rename
        temp_file = self.registry_file.with_suffix(".tmp")

        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_file.replace(self.registry_file)

        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            raise e

    @staticmethod
    def _default_token_env(source_type: str) -> str:
        """
        Get default token environment variable name for source type.

        Args:
            source_type: Source type (github, gitlab, bitbucket, custom)

        Returns:
            Environment variable name (e.g., GITHUB_TOKEN)
        """
        type_map = {
            "github": "GITHUB_TOKEN",
            "gitlab": "GITLAB_TOKEN",
            "gitea": "GITEA_TOKEN",
            "bitbucket": "BITBUCKET_TOKEN",
            "custom": "GIT_TOKEN",
        }

        return type_map.get(source_type.lower(), "GIT_TOKEN")


# ──────────────────────────────────────────────────────────────────────────
# Community-registry submission — shared engine for the MCP submit_config
# tool and the CLI scan publish flow (both depend downward on this module).
# ──────────────────────────────────────────────────────────────────────────

# Community registry repo for config submissions.
REGISTRY_REPO = "yusufkaraaslan/skill-seekers-configs"


def find_existing_submission(
    config_name: str, github_token: str | None, *, max_scan: int = 30
) -> str | None:
    """Return the URL of an open ``[CONFIG] {name}`` submission issue, if any.

    Idempotency guard shared by ``submit_config`` and scan's publish
    flow. Requires an exact title match: GitHub title search is fuzzy
    substring matching, so "[CONFIG] react" also matches "[CONFIG]
    react-native" and a fuzzy hit would suppress a legitimate distinct
    config. Scans at most ``max_scan`` results — each further page is
    another rate-limited Search API call, and an exact-title duplicate
    will be in the top results.

    Returns None on no match, no token, or any error (a search hiccup
    shouldn't block submission).
    """
    if not github_token:
        return None
    try:
        from github import Github

        gh = Github(github_token)
        expected_title = f"[CONFIG] {config_name}"
        results = gh.search_issues(
            f'repo:{REGISTRY_REPO} is:issue is:open in:title "{expected_title}"'
        )
        for i, found in enumerate(results):
            if i >= max_scan:
                break
            if found.title.strip() == expected_title:
                return found.html_url
    except Exception:
        pass
    return None


def submit_config(
    config_path: str | None = None,
    config_json: str | None = None,
    testing_notes: str = "",
    github_token: str | None = None,
) -> dict:
    """Validate a config and submit it to ``REGISTRY_REPO`` as a GitHub issue.

    Validates the config (both legacy and unified formats) and creates a
    GitHub issue for community review. ``github_token`` falls back to the
    GITHUB_TOKEN environment variable.

    Returns ``{"ok": bool, "message": str}`` — ``message`` is user-facing
    text (the MCP submit_config tool returns it verbatim).
    """
    try:
        from github import Github, GithubException
    except ImportError:
        return {
            "ok": False,
            "message": "❌ Error: PyGithub not installed.\n\nInstall with: pip install PyGithub",
        }

    # Import config validator
    try:
        from skill_seekers.cli.config_validator import ConfigValidator
    except ImportError:
        ConfigValidator = None

    github_token = github_token or os.environ.get("GITHUB_TOKEN")

    try:
        # Load config data
        if config_path:
            config_file = Path(config_path)
            if not config_file.exists():
                return {
                    "ok": False,
                    "message": f"❌ Error: Config file not found: {config_path}",
                }

            with open(config_file) as f:
                config_data = json.load(f)
                config_json = json.dumps(config_data, indent=2)
                config_name = config_data.get("name", config_file.stem)

        elif config_json:
            try:
                config_data = json.loads(config_json)
                config_name = config_data.get("name", "unnamed")
            except json.JSONDecodeError as e:
                return {"ok": False, "message": f"❌ Error: Invalid JSON: {str(e)}"}

        else:
            return {
                "ok": False,
                "message": "❌ Error: Must provide either config_path or config_json",
            }

        # Use ConfigValidator for comprehensive validation
        if ConfigValidator is None:
            return {
                "ok": False,
                "message": "❌ Error: ConfigValidator not available. Please ensure config_validator.py is in the CLI directory.",
            }

        try:
            validator = ConfigValidator(config_data)
            validator.validate()

            # Get format info
            is_unified = validator.is_unified
            config_name = config_data.get("name", "unnamed")

            # Additional format validation (ConfigValidator only checks structure)
            # Validate name format (alphanumeric, hyphens, underscores only)
            if not re.match(r"^[a-zA-Z0-9_-]+$", config_name):
                raise ValueError(
                    f"Invalid name format: '{config_name}'\nNames must contain only alphanumeric characters, hyphens, and underscores"
                )

            # Validate URL formats
            if not is_unified:
                # Legacy config - check base_url
                base_url = config_data.get("base_url", "")
                if base_url and not (
                    base_url.startswith("http://") or base_url.startswith("https://")
                ):
                    raise ValueError(
                        f"Invalid base_url format: '{base_url}'\nURLs must start with http:// or https://"
                    )
            else:
                # Unified config - check URLs in sources
                for idx, source in enumerate(config_data.get("sources", [])):
                    if source.get("type") == "documentation":
                        source_url = source.get("base_url", "")
                        if source_url and not (
                            source_url.startswith("http://") or source_url.startswith("https://")
                        ):
                            raise ValueError(
                                f"Source {idx} (documentation): Invalid base_url format: '{source_url}'\nURLs must start with http:// or https://"
                            )

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
            return {"ok": False, "message": error_msg}

        # Detect category based on config format and content
        if is_unified:
            # For unified configs, look at source types
            source_types = [src.get("type") for src in config_data.get("sources", [])]
            if (
                "documentation" in source_types
                and "github" in source_types
                or "documentation" in source_types
                and "pdf" in source_types
                or len(source_types) > 1
            ):
                category = "multi-source"
            else:
                category = "unified"
        else:
            # For legacy configs, use name-based detection
            name_lower = config_name.lower()
            category = "other"
            if any(
                x in name_lower
                for x in ["react", "vue", "django", "laravel", "fastapi", "astro", "hono"]
            ):
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
            if "max_pages" not in config_data:
                warnings.append("⚠️ No max_pages set - will use default (100)")
            elif config_data.get("max_pages") in (None, -1):
                warnings.append(
                    "⚠️ Unlimited scraping enabled - may scrape thousands of pages and take hours"
                )
        else:
            # Unified config warnings
            for src in config_data.get("sources", []):
                if src.get("type") == "documentation" and "max_pages" not in src:
                    warnings.append(
                        "⚠️ No max_pages set for documentation source - will use default (100)"
                    )
                elif src.get("type") == "documentation" and src.get("max_pages") in (None, -1):
                    warnings.append("⚠️ Unlimited scraping enabled for documentation source")

        # Check for GitHub token
        if not github_token:
            return {
                "ok": False,
                "message": "❌ Error: GitHub token required.\n\nProvide github_token parameter or set GITHUB_TOKEN environment variable.\n\nCreate token at: https://github.com/settings/tokens",
            }

        # Create GitHub issue
        try:
            gh = Github(github_token)
            repo = gh.get_repo(REGISTRY_REPO)

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
{config_json}
```

### Testing Results
{testing_notes if testing_notes else "Not provided"}

### Documentation URL
{config_data.get("base_url") if not is_unified else "See sources in config"}

{"### Validation Warnings" if warnings else ""}
{chr(10).join(f"- {w}" for w in warnings) if warnings else ""}

---

### Checklist
- [x] Config validated with ConfigValidator
- [ ] Test scraping completed
- [ ] Added to appropriate category
- [ ] API updated
"""

            # Idempotency guard: if an open submission already exists for this
            # config (e.g. a retry after a transient failure), return it instead
            # of opening a duplicate.
            existing_url = find_existing_submission(config_name, github_token)
            if existing_url:
                return {
                    "ok": True,
                    "message": (
                        f"ℹ️ A submission for '{config_name}' is already open:\n"
                        f"{existing_url}\n\nNo duplicate issue was created."
                    ),
                }

            # Create issue
            issue = repo.create_issue(
                title=f"[CONFIG] {config_name}",
                body=issue_body,
                labels=["config-submission", "needs-review"],
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

            return {"ok": True, "message": result}

        except GithubException as e:
            return {
                "ok": False,
                "message": f"❌ GitHub Error: {str(e)}\n\nCheck your token permissions (needs 'repo' or 'public_repo' scope).",
            }

    except Exception as e:
        return {"ok": False, "message": f"❌ Error: {str(e)}"}
