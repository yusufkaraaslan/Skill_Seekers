#!/usr/bin/env python3
"""
Marketplace Manager
Manages registry of plugin marketplace repositories for skill publishing.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


class MarketplaceManager:
    """Manages marketplace registry at ~/.skill-seekers/marketplaces.json"""

    def __init__(self, config_dir: str | None = None):
        """
        Initialize marketplace manager.

        Args:
            config_dir: Base config directory. Defaults to ~/.skill-seekers/
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".skill-seekers"

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.config_dir / "marketplaces.json"

        if not self.registry_file.exists():
            self._write_registry({"version": "1.0", "marketplaces": []})

    def add_marketplace(
        self,
        name: str,
        git_url: str,
        token_env: str | None = None,
        branch: str = "main",
        author: dict | None = None,
        enabled: bool = True,
    ) -> dict:
        """
        Add or update a marketplace repository.

        Args:
            name: Marketplace identifier (lowercase, alphanumeric + hyphens/underscores)
            git_url: Git repository URL
            token_env: Environment variable name for auth token
            branch: Git branch to use (default: main)
            author: Default author for plugin.json ({"name": str, "email": str})
            enabled: Whether marketplace is enabled (default: True)

        Returns:
            Marketplace dictionary

        Raises:
            ValueError: If name is invalid or git_url is empty
        """
        if not name or not name.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                f"Invalid marketplace name '{name}'. "
                "Must be alphanumeric with optional hyphens/underscores."
            )

        if not git_url or not git_url.strip():
            raise ValueError("git_url cannot be empty")

        if token_env is None:
            token_env = self._default_token_env(git_url)

        marketplace = {
            "name": name.lower(),
            "git_url": git_url.strip(),
            "token_env": token_env,
            "branch": branch,
            "author": author or {"name": "", "email": ""},
            "enabled": enabled,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        registry = self._read_registry()

        existing_index = None
        for i, existing in enumerate(registry["marketplaces"]):
            if existing["name"] == marketplace["name"]:
                existing_index = i
                marketplace["added_at"] = existing.get("added_at", marketplace["added_at"])
                break

        if existing_index is not None:
            registry["marketplaces"][existing_index] = marketplace
        else:
            registry["marketplaces"].append(marketplace)

        self._write_registry(registry)
        return marketplace

    def get_marketplace(self, name: str) -> dict:
        """
        Get marketplace by name.

        Raises:
            KeyError: If marketplace not found
        """
        registry = self._read_registry()
        name_lower = name.lower()
        for marketplace in registry["marketplaces"]:
            if marketplace["name"] == name_lower:
                return marketplace

        available = [m["name"] for m in registry["marketplaces"]]
        raise KeyError(
            f"Marketplace '{name}' not found. "
            f"Available marketplaces: {', '.join(available) if available else 'none'}"
        )

    def list_marketplaces(self, enabled_only: bool = False) -> list[dict]:
        """List all marketplaces."""
        registry = self._read_registry()
        if enabled_only:
            return [m for m in registry["marketplaces"] if m.get("enabled", True)]
        return registry["marketplaces"]

    def remove_marketplace(self, name: str) -> bool:
        """Remove marketplace by name. Returns True if removed."""
        registry = self._read_registry()
        name_lower = name.lower()
        for i, marketplace in enumerate(registry["marketplaces"]):
            if marketplace["name"] == name_lower:
                del registry["marketplaces"][i]
                self._write_registry(registry)
                return True
        return False

    def update_marketplace(self, name: str, **kwargs) -> dict:
        """
        Update specific fields of an existing marketplace.

        Raises:
            KeyError: If marketplace not found
        """
        marketplace = self.get_marketplace(name)
        allowed_fields = {"git_url", "token_env", "branch", "author", "enabled"}
        for field, value in kwargs.items():
            if field in allowed_fields:
                marketplace[field] = value

        marketplace["updated_at"] = datetime.now(timezone.utc).isoformat()

        registry = self._read_registry()
        for i, m in enumerate(registry["marketplaces"]):
            if m["name"] == marketplace["name"]:
                registry["marketplaces"][i] = marketplace
                break

        self._write_registry(registry)
        return marketplace

    def _read_registry(self) -> dict:
        """Read registry from file."""
        try:
            with open(self.registry_file, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupted registry file: {e}") from e

    def _write_registry(self, registry: dict) -> None:
        """Write registry to file atomically."""
        if "version" not in registry or "marketplaces" not in registry:
            raise ValueError("Invalid registry schema")

        temp_file = self.registry_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.registry_file)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e

    @staticmethod
    def _default_token_env(git_url: str) -> str:
        """Get default token environment variable name from git URL."""
        url_lower = git_url.lower()
        if "github" in url_lower:
            return "GITHUB_TOKEN"
        elif "gitlab" in url_lower:
            return "GITLAB_TOKEN"
        elif "bitbucket" in url_lower:
            return "BITBUCKET_TOKEN"
        elif "gitea" in url_lower:
            return "GITEA_TOKEN"
        return "GIT_TOKEN"
