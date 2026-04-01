#!/usr/bin/env python3
"""
Marketplace Publisher
Publishes packaged skills to Claude Code plugin marketplace repositories.
"""

import json
import logging
import os
import re
import shutil
from pathlib import Path

import yaml

from skill_seekers.mcp.marketplace_manager import MarketplaceManager

logger = logging.getLogger(__name__)


class MarketplacePublisher:
    """Publishes skills to registered plugin marketplace repositories."""

    def __init__(self, cache_dir: str | None = None):
        """
        Initialize publisher.

        Args:
            cache_dir: Base cache directory. Defaults to ~/.skill-seekers/cache/
        """
        from skill_seekers.mcp.git_repo import GitConfigRepo

        self.git_repo = GitConfigRepo(cache_dir)

    def publish(
        self,
        skill_dir: str | Path,
        marketplace_name: str,
        category: str = "development",
        skill_name: str | None = None,
        description: str | None = None,
        create_branch: bool = False,
        force: bool = False,
    ) -> dict:
        """
        Publish a skill to a plugin marketplace repository.

        Args:
            skill_dir: Path to skill directory (contains SKILL.md + references/)
            marketplace_name: Registered marketplace name
            category: Plugin category in marketplace (default: "development")
            skill_name: Override skill name (defaults to SKILL.md frontmatter or dir name)
            description: Override description (defaults to SKILL.md frontmatter)
            create_branch: Create feature branch instead of committing to main
            force: Overwrite existing plugin if it exists

        Returns:
            Dict with success, plugin_path, commit_sha, branch, message
        """
        import git

        skill_dir = Path(skill_dir)

        # 1. Validate skill directory
        skill_md_path = skill_dir / "SKILL.md"
        if not skill_md_path.exists():
            raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

        # 2. Read frontmatter for metadata
        frontmatter = self._read_frontmatter(skill_md_path)
        if not skill_name:
            skill_name = frontmatter.get("name") or skill_dir.name
        if not description:
            description = frontmatter.get("description", f"Skill for {skill_name}")

        # 2b. Validate skill_name to prevent path traversal
        skill_name = self._validate_skill_name(skill_name)

        # 3. Resolve marketplace
        manager = MarketplaceManager()
        marketplace = manager.get_marketplace(marketplace_name)
        git_url = marketplace["git_url"]
        branch = marketplace["branch"]
        token_env = marketplace["token_env"]
        author = marketplace.get("author", {"name": "", "email": ""})

        # 4. Get token
        token = os.environ.get(token_env) if token_env else None
        if not token:
            raise RuntimeError(
                f"Token not found. Set {token_env} environment variable "
                f"for marketplace '{marketplace_name}'"
            )

        # 5. Clone/pull marketplace repo
        cache_name = f"marketplace_{marketplace_name}"
        try:
            repo_path = self.git_repo.clone_or_pull(
                source_name=cache_name,
                git_url=git_url,
                branch=branch,
                token=token,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to clone/pull marketplace repo: {e}") from e

        # 6. Check for existing plugin
        plugin_dir = repo_path / "plugins" / skill_name
        if plugin_dir.exists() and not force:
            raise ValueError(
                f"Plugin '{skill_name}' already exists in marketplace '{marketplace_name}'. "
                "Use force=True to overwrite."
            )

        # 7. Create plugin directory structure + commit + push
        # Wrap in try/finally to clean up partial plugin dir on failure
        plugin_created = False
        try:
            self._copy_skill_to_plugin(skill_dir, plugin_dir, skill_name)
            plugin_created = True

            # 8. Generate plugin.json
            plugin_json = self._generate_plugin_json(skill_name, description, author)
            plugin_json_dir = plugin_dir / ".claude-plugin"
            plugin_json_dir.mkdir(parents=True, exist_ok=True)
            with open(plugin_json_dir / "plugin.json", "w", encoding="utf-8") as f:
                json.dump(plugin_json, f, indent=2, ensure_ascii=False)

            # 9. Update marketplace.json
            self._update_marketplace_json(repo_path, skill_name, description, author, category)

            # 10. Git commit and push
            repo = git.Repo(repo_path)

            target_branch = branch
            if create_branch:
                target_branch = f"skill/{skill_name}"
                repo.git.checkout("-b", target_branch)

            repo.git.add("-A")

            action = "update" if force else "add"
            commit_msg = f"feat: {action} {skill_name} skill plugin"
            repo.index.commit(commit_msg)
            commit_sha = repo.head.commit.hexsha[:7]

            push_url = self.git_repo.inject_token(git_url, token)
            repo.git.push(push_url, target_branch)

            return {
                "success": True,
                "plugin_path": f"plugins/{skill_name}",
                "commit_sha": commit_sha,
                "branch": target_branch,
                "message": f"Published '{skill_name}' to marketplace '{marketplace_name}'",
            }

        except git.GitCommandError as e:
            # Reset git state on push/commit failure
            try:
                repo = git.Repo(repo_path)
                repo.git.checkout("--", ".")
                repo.git.clean("-fd", "plugins/" + skill_name)
            except Exception:
                pass
            raise RuntimeError(f"Git operation failed: {e}") from e
        except Exception:
            # Clean up partial plugin directory on non-git failure
            if plugin_created and plugin_dir.exists() and not force:
                shutil.rmtree(plugin_dir, ignore_errors=True)
            raise

    @staticmethod
    def _validate_skill_name(name: str) -> str:
        """
        Validate skill name to prevent path traversal and injection.

        Args:
            name: Skill name to validate

        Returns:
            Validated skill name

        Raises:
            ValueError: If name contains invalid characters
        """
        if not name or not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$", name):
            raise ValueError(
                f"Invalid skill name '{name}'. "
                "Must start with alphanumeric and contain only alphanumeric, hyphens, underscores, or dots."
            )
        if ".." in name or "/" in name or "\\" in name:
            raise ValueError(f"Invalid skill name '{name}'. Path traversal characters not allowed.")
        return name

    def _read_frontmatter(self, skill_md_path: Path) -> dict:
        """Parse YAML frontmatter from SKILL.md."""
        content = skill_md_path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return {}

        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}

        try:
            return yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError:
            return {}

    def _copy_skill_to_plugin(self, skill_dir: Path, plugin_dir: Path, skill_name: str) -> None:
        """Copy skill files into plugin directory structure."""
        skills_dest = plugin_dir / "skills" / skill_name

        if skills_dest.exists():
            shutil.rmtree(skills_dest)

        skills_dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_dir / "SKILL.md", skills_dest / "SKILL.md")

        refs_src = skill_dir / "references"
        if refs_src.exists() and refs_src.is_dir():
            shutil.copytree(refs_src, skills_dest / "references", dirs_exist_ok=True)

    def _generate_plugin_json(self, skill_name: str, description: str, author: dict) -> dict:
        """Generate plugin.json content."""
        return {
            "name": skill_name,
            "description": description,
            "author": author,
        }

    def _update_marketplace_json(
        self,
        repo_path: Path,
        skill_name: str,
        description: str,
        author: dict,
        category: str,
    ) -> None:
        """Update root .claude-plugin/marketplace.json with new plugin entry."""
        marketplace_json_path = repo_path / ".claude-plugin" / "marketplace.json"

        if marketplace_json_path.exists():
            with open(marketplace_json_path, encoding="utf-8") as f:
                data = json.load(f)
        else:
            marketplace_json_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
                "name": repo_path.name,
                "description": "",
                "owner": author,
                "plugins": [],
            }

        entry = {
            "name": skill_name,
            "description": description,
            "author": author,
            "source": f"./plugins/{skill_name}",
            "category": category,
        }

        updated = False
        for i, plugin in enumerate(data["plugins"]):
            if plugin["name"] == skill_name:
                data["plugins"][i] = entry
                updated = True
                break

        if not updated:
            data["plugins"].append(entry)

        data["plugins"].sort(key=lambda p: p["name"])

        with open(marketplace_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
