#!/usr/bin/env python3
"""
Config Source Manager
Manages registry of custom config sources (git repositories)
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class SourceManager:
    """Manages config source registry at ~/.skill-seekers/sources.json"""

    def __init__(self, config_dir: Optional[str] = None):
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
        token_env: Optional[str] = None,
        branch: str = "main",
        priority: int = 100,
        enabled: bool = True
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
                f"Invalid source name '{name}'. "
                "Must be alphanumeric with optional hyphens/underscores."
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
            "updated_at": datetime.now(timezone.utc).isoformat()
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
            f"Source '{name}' not found. "
            f"Available sources: {', '.join(available) if available else 'none'}"
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

    def update_source(
        self,
        name: str,
        **kwargs
    ) -> dict:
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
            with open(self.registry_file, 'r', encoding='utf-8') as f:
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
            with open(temp_file, 'w', encoding='utf-8') as f:
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
            "custom": "GIT_TOKEN"
        }

        return type_map.get(source_type.lower(), "GIT_TOKEN")
