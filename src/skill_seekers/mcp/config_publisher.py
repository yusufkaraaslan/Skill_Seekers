#!/usr/bin/env python3
"""
Config Publisher
Pushes validated config files to registered config source repositories.

Follows the same pattern as MarketplacePublisher but for configs.
"""

import json
import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

# Category keywords for auto-detection
CATEGORY_KEYWORDS = {
    "game-engines": ["unity", "godot", "unreal", "gamemaker", "spine", "dotween", "addressable"],
    "web-frameworks": [
        "react",
        "vue",
        "angular",
        "next",
        "nuxt",
        "svelte",
        "django",
        "flask",
        "fastapi",
        "express",
    ],
    "ai-ml": ["tensorflow", "pytorch", "langchain", "llama", "openai", "anthropic", "huggingface"],
    "databases": ["postgres", "mysql", "mongo", "redis", "sqlite", "prisma", "drizzle"],
    "devops": ["docker", "kubernetes", "terraform", "ansible", "jenkins", "github-actions"],
    "cloud": ["aws", "gcp", "azure", "vercel", "netlify", "cloudflare"],
    "mobile": ["flutter", "react-native", "swift", "kotlin", "expo"],
    "testing": ["jest", "pytest", "cypress", "playwright", "vitest"],
    "build-tools": ["webpack", "vite", "esbuild", "turbo", "nx"],
    "css-frameworks": ["tailwind", "bootstrap", "material-ui", "chakra"],
    "security": ["oauth", "jwt", "auth0", "keycloak"],
    "development-tools": ["git", "vscode", "neovim", "cursor"],
    "messaging": ["kafka", "rabbitmq", "nats", "redis-streams"],
}


def detect_category(config: dict) -> str:
    """Auto-detect category from config name and description.

    Args:
        config: Parsed config dictionary

    Returns:
        Category string (e.g., "game-engines") or "custom" if undetected
    """
    name = config.get("name", "").lower()
    description = config.get("description", "").lower()
    text = f"{name} {description}"

    best_category = "custom"
    best_score = 0

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_category = category

    return best_category


class ConfigPublisher:
    """Pushes validated configs to registered config source repositories."""

    def __init__(self, cache_dir: str | None = None):
        """Initialize publisher.

        Args:
            cache_dir: Base cache directory. Defaults to ~/.skill-seekers/cache/
        """
        from skill_seekers.mcp.git_repo import GitConfigRepo

        self.git_repo = GitConfigRepo(cache_dir)

    def publish(
        self,
        config_path: str | Path,
        source_name: str,
        category: str = "auto",
        create_branch: bool = False,
        force: bool = False,
    ) -> dict:
        """Publish a config to a registered config source repository.

        Args:
            config_path: Path to config JSON file
            source_name: Registered source name (e.g., "spyke")
            category: Category directory (e.g., "game-engines") or "auto" to detect
            create_branch: Create feature branch instead of committing to main
            force: Overwrite existing config if it exists

        Returns:
            Dict with success, config_path, commit_sha, branch, message
        """
        import git

        config_path = Path(config_path)

        # 1. Validate config file exists
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # 2. Load and validate config
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)

        config_name = config.get("name")
        if not config_name:
            raise ValueError("Config JSON must have a 'name' field")

        # Validate config_name to prevent path traversal
        if "/" in config_name or "\\" in config_name or ".." in config_name:
            raise ValueError(
                f"Invalid config name '{config_name}'. "
                "Path separators (/, \\) and traversal sequences (..) are not allowed."
            )

        try:
            from skill_seekers.cli.config_validator import validate_config

            validate_config(str(config_path))
            logger.info(f"✅ Config validated: {config_name}")
        except ValueError as e:
            logger.warning(f"⚠️  Config validation warning: {e}")
            # Continue — validation warnings shouldn't block push

        # 3. Resolve source from registry
        from skill_seekers.mcp.source_manager import SourceManager

        manager = SourceManager()
        source = manager.get_source(source_name)
        if not source:
            available = [s["name"] for s in manager.list_sources()]
            raise ValueError(f"Source '{source_name}' not found. Available sources: {available}")

        git_url = source["git_url"]
        branch = source.get("branch", "main")
        token_env = source.get("token_env")

        # 4. Get token
        token = os.environ.get(token_env) if token_env else None
        if not token:
            raise RuntimeError(
                f"Token not found. Set {token_env} environment variable for source '{source_name}'"
            )

        # 5. Clone/pull source repo (full clone for push support)
        cache_name = f"source_{source_name}"
        repo_path = self.git_repo.cache_dir / cache_name
        clone_url = self.git_repo.inject_token(git_url, token) if token else git_url

        try:
            if repo_path.exists() and (repo_path / ".git").exists():
                repo_obj = git.Repo(repo_path)
                repo_obj.remotes.origin.pull(branch)
                logger.info(f"📥 Pulled latest from {source_name}/{branch}")
            else:
                repo_obj = git.Repo.clone_from(clone_url, repo_path, branch=branch)
                logger.info(f"📥 Cloned {source_name} repo")
            # Clear token from cached .git/config by resetting to non-token URL
            repo_obj.remotes.origin.set_url(git_url)
        except git.GitCommandError as e:
            raise RuntimeError(f"Failed to clone/pull source repo: {e}") from e

        # 6. Auto-detect category
        if category == "auto":
            category = detect_category(config)
            logger.info(f"📂 Auto-detected category: {category}")

        # 7. Check if config already exists
        target_dir = repo_path / "configs" / category
        target_file = target_dir / f"{config_name}.json"

        if target_file.exists() and not force:
            raise ValueError(
                f"Config '{config_name}' already exists in {source_name}/configs/{category}/. "
                "Use force=True to overwrite."
            )

        # 8. Copy config to target directory
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config_path, target_file)
        logger.info(f"📄 Placed config at configs/{category}/{config_name}.json")

        # 9. Git commit and push
        repo = git.Repo(repo_path)

        target_branch = branch
        if create_branch:
            target_branch = f"config/{config_name}"
            repo.git.checkout("-b", target_branch)

        repo.index.add([str(target_file.relative_to(repo_path))])

        action = "update" if target_file.exists() and force else "add"
        commit_msg = f"feat: {action} {config_name} config in {category}"
        commit = repo.index.commit(commit_msg)

        # Push
        try:
            repo.remotes.origin.push(target_branch)
            logger.info(f"🚀 Pushed to {source_name}/{target_branch}")
        except git.GitCommandError as e:
            raise RuntimeError(
                f"Failed to push to {source_name}. Check permissions for {token_env}. Error: {e}"
            ) from e

        # Switch back to main if we created a branch
        if create_branch:
            repo.git.checkout(branch)

        return {
            "success": True,
            "config_name": config_name,
            "config_path": f"configs/{category}/{config_name}.json",
            "source": source_name,
            "category": category,
            "commit_sha": str(commit.hexsha)[:8],
            "branch": target_branch,
            "message": commit_msg,
        }
