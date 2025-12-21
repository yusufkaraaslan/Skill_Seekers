#!/usr/bin/env python3
"""
Git Config Repository Manager
Handles git clone/pull operations for custom config sources
"""

import json
import os
import shutil
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
import git
from git.exc import GitCommandError, InvalidGitRepositoryError


class GitConfigRepo:
    """Manages git operations for config repositories."""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize git repository manager.

        Args:
            cache_dir: Base cache directory. Defaults to $SKILL_SEEKERS_CACHE_DIR
                      or ~/.skill-seekers/cache/
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Use environment variable or default
            env_cache = os.environ.get("SKILL_SEEKERS_CACHE_DIR")
            if env_cache:
                self.cache_dir = Path(env_cache).expanduser()
            else:
                self.cache_dir = Path.home() / ".skill-seekers" / "cache"

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def clone_or_pull(
        self,
        source_name: str,
        git_url: str,
        branch: str = "main",
        token: Optional[str] = None,
        force_refresh: bool = False
    ) -> Path:
        """
        Clone repository if not cached, else pull latest changes.

        Args:
            source_name: Source identifier (used for cache path)
            git_url: Git repository URL
            branch: Branch to clone/pull (default: main)
            token: Optional authentication token
            force_refresh: If True, delete cache and re-clone

        Returns:
            Path to cloned repository

        Raises:
            GitCommandError: If clone/pull fails
            ValueError: If git_url is invalid
        """
        # Validate URL
        if not self.validate_git_url(git_url):
            raise ValueError(f"Invalid git URL: {git_url}")

        # Determine cache path
        repo_path = self.cache_dir / source_name

        # Force refresh: delete existing cache
        if force_refresh and repo_path.exists():
            shutil.rmtree(repo_path)

        # Inject token if provided
        clone_url = git_url
        if token:
            clone_url = self.inject_token(git_url, token)

        try:
            if repo_path.exists() and (repo_path / ".git").exists():
                # Repository exists - pull latest
                try:
                    repo = git.Repo(repo_path)
                    origin = repo.remotes.origin

                    # Update remote URL if token provided
                    if token:
                        origin.set_url(clone_url)

                    # Pull latest changes
                    origin.pull(branch)
                    return repo_path
                except (InvalidGitRepositoryError, GitCommandError) as e:
                    # Corrupted repo - delete and re-clone
                    shutil.rmtree(repo_path)
                    raise  # Re-raise to trigger clone below

            # Repository doesn't exist - clone
            git.Repo.clone_from(
                clone_url,
                repo_path,
                branch=branch,
                depth=1,  # Shallow clone
                single_branch=True  # Only clone one branch
            )
            return repo_path

        except GitCommandError as e:
            error_msg = str(e)

            # Provide helpful error messages
            if "authentication failed" in error_msg.lower() or "403" in error_msg:
                raise GitCommandError(
                    f"Authentication failed for {git_url}. "
                    f"Check your token or permissions.",
                    128
                ) from e
            elif "not found" in error_msg.lower() or "404" in error_msg:
                raise GitCommandError(
                    f"Repository not found: {git_url}. "
                    f"Verify the URL is correct and you have access.",
                    128
                ) from e
            else:
                raise GitCommandError(
                    f"Failed to clone repository: {error_msg}",
                    128
                ) from e

    def find_configs(self, repo_path: Path) -> list[Path]:
        """
        Find all config files (*.json) in repository.

        Args:
            repo_path: Path to cloned repo

        Returns:
            List of paths to *.json files (sorted by name)
        """
        if not repo_path.exists():
            return []

        # Find all .json files, excluding .git directory
        configs = []
        for json_file in repo_path.rglob("*.json"):
            # Skip files in .git directory
            if ".git" in json_file.parts:
                continue
            configs.append(json_file)

        # Sort by filename
        return sorted(configs, key=lambda p: p.name)

    def get_config(self, repo_path: Path, config_name: str) -> dict:
        """
        Load specific config by name from repository.

        Args:
            repo_path: Path to cloned repo
            config_name: Config name (without .json extension)

        Returns:
            Config dictionary

        Raises:
            FileNotFoundError: If config not found
            ValueError: If config is invalid JSON
        """
        # Ensure .json extension
        if not config_name.endswith(".json"):
            config_name = f"{config_name}.json"

        # Search for config file
        all_configs = self.find_configs(repo_path)

        # Try exact filename match first
        for config_path in all_configs:
            if config_path.name == config_name:
                return self._load_config_file(config_path)

        # Try case-insensitive match
        config_name_lower = config_name.lower()
        for config_path in all_configs:
            if config_path.name.lower() == config_name_lower:
                return self._load_config_file(config_path)

        # Config not found - provide helpful error
        available = [p.stem for p in all_configs]  # Just filenames without .json
        raise FileNotFoundError(
            f"Config '{config_name}' not found in repository. "
            f"Available configs: {', '.join(available) if available else 'none'}"
        )

    def _load_config_file(self, config_path: Path) -> dict:
        """
        Load and validate config JSON file.

        Args:
            config_path: Path to config file

        Returns:
            Config dictionary

        Raises:
            ValueError: If JSON is invalid
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file {config_path.name}: {e}") from e

    @staticmethod
    def inject_token(git_url: str, token: str) -> str:
        """
        Inject authentication token into git URL.

        Converts SSH URLs to HTTPS and adds token for authentication.

        Args:
            git_url: Original git URL
            token: Authentication token

        Returns:
            URL with token injected

        Examples:
            https://github.com/org/repo.git → https://TOKEN@github.com/org/repo.git
            git@github.com:org/repo.git → https://TOKEN@github.com/org/repo.git
        """
        # Convert SSH to HTTPS
        if git_url.startswith("git@"):
            # git@github.com:org/repo.git → github.com/org/repo.git
            parts = git_url.replace("git@", "").replace(":", "/", 1)
            git_url = f"https://{parts}"

        # Parse URL
        parsed = urlparse(git_url)

        # Inject token
        if parsed.hostname:
            # https://github.com/org/repo.git → https://TOKEN@github.com/org/repo.git
            netloc = f"{token}@{parsed.hostname}"
            if parsed.port:
                netloc = f"{netloc}:{parsed.port}"

            return f"{parsed.scheme}://{netloc}{parsed.path}"

        return git_url

    @staticmethod
    def validate_git_url(git_url: str) -> bool:
        """
        Validate git URL format.

        Args:
            git_url: Git repository URL

        Returns:
            True if valid, False otherwise
        """
        if not git_url:
            return False

        # Accept HTTPS URLs
        if git_url.startswith("https://") or git_url.startswith("http://"):
            parsed = urlparse(git_url)
            return bool(parsed.hostname and parsed.path)

        # Accept SSH URLs
        if git_url.startswith("git@"):
            # git@github.com:org/repo.git
            return ":" in git_url and len(git_url.split(":")) == 2

        # Accept file:// URLs (for local testing)
        if git_url.startswith("file://"):
            return True

        return False
