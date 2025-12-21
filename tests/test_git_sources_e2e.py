#!/usr/bin/env python3
"""
E2E Tests for A1.9 Git Source Features

Tests the complete workflow with temporary files and repositories:
1. GitConfigRepo - clone/pull operations
2. SourceManager - registry CRUD operations
3. MCP Tools - all 4 git-related tools
4. Integration - complete user workflows
5. Error handling - authentication, not found, etc.

All tests use temporary directories and actual git repositories.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import git
import pytest

from skill_seekers.mcp.git_repo import GitConfigRepo
from skill_seekers.mcp.source_manager import SourceManager

# Check if MCP is available
try:
    import mcp
    from mcp.types import TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


class TestGitSourcesE2E:
    """End-to-end tests for git source features."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for cache and config."""
        cache_dir = tempfile.mkdtemp(prefix="ss_cache_")
        config_dir = tempfile.mkdtemp(prefix="ss_config_")
        yield cache_dir, config_dir
        # Cleanup
        shutil.rmtree(cache_dir, ignore_errors=True)
        shutil.rmtree(config_dir, ignore_errors=True)

    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary git repository with sample configs."""
        repo_dir = tempfile.mkdtemp(prefix="ss_repo_")

        # Initialize git repository
        repo = git.Repo.init(repo_dir)

        # Create sample config files
        configs = {
            "react.json": {
                "name": "react",
                "description": "React framework for UIs",
                "base_url": "https://react.dev/",
                "selectors": {
                    "main_content": "article",
                    "title": "h1",
                    "code_blocks": "pre code"
                },
                "url_patterns": {
                    "include": [],
                    "exclude": []
                },
                "categories": {
                    "getting_started": ["learn", "start"],
                    "api": ["reference", "api"]
                },
                "rate_limit": 0.5,
                "max_pages": 100
            },
            "vue.json": {
                "name": "vue",
                "description": "Vue.js progressive framework",
                "base_url": "https://vuejs.org/",
                "selectors": {
                    "main_content": "main",
                    "title": "h1"
                },
                "url_patterns": {
                    "include": [],
                    "exclude": []
                },
                "categories": {},
                "rate_limit": 0.5,
                "max_pages": 50
            },
            "django.json": {
                "name": "django",
                "description": "Django web framework",
                "base_url": "https://docs.djangoproject.com/",
                "selectors": {
                    "main_content": "div[role='main']",
                    "title": "h1"
                },
                "url_patterns": {
                    "include": [],
                    "exclude": []
                },
                "categories": {},
                "rate_limit": 0.5,
                "max_pages": 200
            }
        }

        # Write config files
        for filename, config_data in configs.items():
            config_path = Path(repo_dir) / filename
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)

        # Add and commit
        repo.index.add(['*.json'])
        repo.index.commit("Initial commit with sample configs")

        yield repo_dir, repo

        # Cleanup
        shutil.rmtree(repo_dir, ignore_errors=True)

    def test_e2e_workflow_direct_git_url(self, temp_dirs, temp_git_repo):
        """
        E2E Test 1: Direct git URL workflow (no source registration)

        Steps:
        1. Clone repository via direct git URL
        2. List available configs
        3. Fetch specific config
        4. Verify config content
        """
        cache_dir, config_dir = temp_dirs
        repo_dir, repo = temp_git_repo

        git_url = f"file://{repo_dir}"

        # Step 1: Clone repository
        git_repo = GitConfigRepo(cache_dir=cache_dir)
        repo_path = git_repo.clone_or_pull(
            source_name="test-direct",
            git_url=git_url,
            branch="master"  # git.Repo.init creates 'master' by default
        )

        assert repo_path.exists()
        assert (repo_path / ".git").exists()

        # Step 2: List available configs
        configs = git_repo.find_configs(repo_path)
        assert len(configs) == 3
        config_names = [c.stem for c in configs]
        assert set(config_names) == {"react", "vue", "django"}

        # Step 3: Fetch specific config
        config = git_repo.get_config(repo_path, "react")

        # Step 4: Verify config content
        assert config["name"] == "react"
        assert config["description"] == "React framework for UIs"
        assert config["base_url"] == "https://react.dev/"
        assert "selectors" in config
        assert "categories" in config
        assert config["max_pages"] == 100

    def test_e2e_workflow_with_source_registration(self, temp_dirs, temp_git_repo):
        """
        E2E Test 2: Complete workflow with source registration

        Steps:
        1. Add source to registry
        2. List sources
        3. Get source details
        4. Clone via source name
        5. Fetch config
        6. Update source (re-add with different priority)
        7. Remove source
        8. Verify removal
        """
        cache_dir, config_dir = temp_dirs
        repo_dir, repo = temp_git_repo

        git_url = f"file://{repo_dir}"

        # Step 1: Add source to registry
        source_manager = SourceManager(config_dir=config_dir)
        source = source_manager.add_source(
            name="team-configs",
            git_url=git_url,
            source_type="custom",
            branch="master",
            priority=10
        )

        assert source["name"] == "team-configs"
        assert source["git_url"] == git_url
        assert source["type"] == "custom"
        assert source["branch"] == "master"
        assert source["priority"] == 10
        assert source["enabled"] is True

        # Step 2: List sources
        sources = source_manager.list_sources()
        assert len(sources) == 1
        assert sources[0]["name"] == "team-configs"

        # Step 3: Get source details
        retrieved_source = source_manager.get_source("team-configs")
        assert retrieved_source["git_url"] == git_url

        # Step 4: Clone via source name
        git_repo = GitConfigRepo(cache_dir=cache_dir)
        repo_path = git_repo.clone_or_pull(
            source_name=source["name"],
            git_url=source["git_url"],
            branch=source["branch"]
        )

        assert repo_path.exists()

        # Step 5: Fetch config
        config = git_repo.get_config(repo_path, "vue")
        assert config["name"] == "vue"
        assert config["base_url"] == "https://vuejs.org/"

        # Step 6: Update source (re-add with different priority)
        updated_source = source_manager.add_source(
            name="team-configs",
            git_url=git_url,
            source_type="custom",
            branch="master",
            priority=5  # Changed priority
        )
        assert updated_source["priority"] == 5

        # Step 7: Remove source
        removed = source_manager.remove_source("team-configs")
        assert removed is True

        # Step 8: Verify removal
        sources = source_manager.list_sources()
        assert len(sources) == 0

        with pytest.raises(KeyError, match="Source 'team-configs' not found"):
            source_manager.get_source("team-configs")

    def test_e2e_multiple_sources_priority_resolution(self, temp_dirs, temp_git_repo):
        """
        E2E Test 3: Multiple sources with priority resolution

        Steps:
        1. Add multiple sources with different priorities
        2. Verify sources are sorted by priority
        3. Enable/disable sources
        4. List enabled sources only
        """
        cache_dir, config_dir = temp_dirs
        repo_dir, repo = temp_git_repo

        git_url = f"file://{repo_dir}"
        source_manager = SourceManager(config_dir=config_dir)

        # Step 1: Add multiple sources with different priorities
        source_manager.add_source(
            name="low-priority",
            git_url=git_url,
            priority=100
        )
        source_manager.add_source(
            name="high-priority",
            git_url=git_url,
            priority=1
        )
        source_manager.add_source(
            name="medium-priority",
            git_url=git_url,
            priority=50
        )

        # Step 2: Verify sources are sorted by priority
        sources = source_manager.list_sources()
        assert len(sources) == 3
        assert sources[0]["name"] == "high-priority"
        assert sources[1]["name"] == "medium-priority"
        assert sources[2]["name"] == "low-priority"

        # Step 3: Enable/disable sources
        source_manager.add_source(
            name="high-priority",
            git_url=git_url,
            priority=1,
            enabled=False
        )

        # Step 4: List enabled sources only
        enabled_sources = source_manager.list_sources(enabled_only=True)
        assert len(enabled_sources) == 2
        assert all(s["enabled"] for s in enabled_sources)
        assert "high-priority" not in [s["name"] for s in enabled_sources]

    def test_e2e_pull_existing_repository(self, temp_dirs, temp_git_repo):
        """
        E2E Test 4: Pull updates from existing repository

        Steps:
        1. Clone repository
        2. Add new commit to original repo
        3. Pull updates
        4. Verify new config is available
        """
        cache_dir, config_dir = temp_dirs
        repo_dir, repo = temp_git_repo

        git_url = f"file://{repo_dir}"
        git_repo = GitConfigRepo(cache_dir=cache_dir)

        # Step 1: Clone repository
        repo_path = git_repo.clone_or_pull(
            source_name="test-pull",
            git_url=git_url,
            branch="master"
        )

        initial_configs = git_repo.find_configs(repo_path)
        assert len(initial_configs) == 3

        # Step 2: Add new commit to original repo
        new_config = {
            "name": "fastapi",
            "description": "FastAPI framework",
            "base_url": "https://fastapi.tiangolo.com/",
            "selectors": {"main_content": "article"},
            "url_patterns": {"include": [], "exclude": []},
            "categories": {},
            "rate_limit": 0.5,
            "max_pages": 150
        }

        new_config_path = Path(repo_dir) / "fastapi.json"
        with open(new_config_path, 'w') as f:
            json.dump(new_config, f, indent=2)

        repo.index.add(['fastapi.json'])
        repo.index.commit("Add FastAPI config")

        # Step 3: Pull updates
        updated_repo_path = git_repo.clone_or_pull(
            source_name="test-pull",
            git_url=git_url,
            branch="master",
            force_refresh=False  # Should pull, not re-clone
        )

        # Step 4: Verify new config is available
        updated_configs = git_repo.find_configs(updated_repo_path)
        assert len(updated_configs) == 4

        fastapi_config = git_repo.get_config(updated_repo_path, "fastapi")
        assert fastapi_config["name"] == "fastapi"
        assert fastapi_config["max_pages"] == 150

    def test_e2e_force_refresh(self, temp_dirs, temp_git_repo):
        """
        E2E Test 5: Force refresh (delete and re-clone)

        Steps:
        1. Clone repository
        2. Modify local cache manually
        3. Force refresh
        4. Verify cache was reset
        """
        cache_dir, config_dir = temp_dirs
        repo_dir, repo = temp_git_repo

        git_url = f"file://{repo_dir}"
        git_repo = GitConfigRepo(cache_dir=cache_dir)

        # Step 1: Clone repository
        repo_path = git_repo.clone_or_pull(
            source_name="test-refresh",
            git_url=git_url,
            branch="master"
        )

        # Step 2: Modify local cache manually
        corrupt_file = repo_path / "CORRUPTED.txt"
        with open(corrupt_file, 'w') as f:
            f.write("This file should not exist after refresh")

        assert corrupt_file.exists()

        # Step 3: Force refresh
        refreshed_repo_path = git_repo.clone_or_pull(
            source_name="test-refresh",
            git_url=git_url,
            branch="master",
            force_refresh=True  # Delete and re-clone
        )

        # Step 4: Verify cache was reset
        assert not corrupt_file.exists()
        configs = git_repo.find_configs(refreshed_repo_path)
        assert len(configs) == 3

    def test_e2e_config_not_found(self, temp_dirs, temp_git_repo):
        """
        E2E Test 6: Error handling - config not found

        Steps:
        1. Clone repository
        2. Try to fetch non-existent config
        3. Verify helpful error message with suggestions
        """
        cache_dir, config_dir = temp_dirs
        repo_dir, repo = temp_git_repo

        git_url = f"file://{repo_dir}"
        git_repo = GitConfigRepo(cache_dir=cache_dir)

        # Step 1: Clone repository
        repo_path = git_repo.clone_or_pull(
            source_name="test-not-found",
            git_url=git_url,
            branch="master"
        )

        # Step 2: Try to fetch non-existent config
        with pytest.raises(FileNotFoundError) as exc_info:
            git_repo.get_config(repo_path, "nonexistent")

        # Step 3: Verify helpful error message with suggestions
        error_msg = str(exc_info.value)
        assert "nonexistent.json" in error_msg
        assert "not found" in error_msg
        assert "react" in error_msg  # Should suggest available configs
        assert "vue" in error_msg
        assert "django" in error_msg

    def test_e2e_invalid_git_url(self, temp_dirs):
        """
        E2E Test 7: Error handling - invalid git URL

        Steps:
        1. Try to clone with invalid URL
        2. Verify validation error
        """
        cache_dir, config_dir = temp_dirs
        git_repo = GitConfigRepo(cache_dir=cache_dir)

        # Invalid URLs
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://invalid.com/repo.git",
            "javascript:alert('xss')"
        ]

        for invalid_url in invalid_urls:
            with pytest.raises(ValueError, match="Invalid git URL"):
                git_repo.clone_or_pull(
                    source_name="test-invalid",
                    git_url=invalid_url,
                    branch="master"
                )

    def test_e2e_source_name_validation(self, temp_dirs):
        """
        E2E Test 8: Error handling - invalid source names

        Steps:
        1. Try to add sources with invalid names
        2. Verify validation errors
        """
        cache_dir, config_dir = temp_dirs
        source_manager = SourceManager(config_dir=config_dir)

        # Invalid source names
        invalid_names = [
            "",
            "name with spaces",
            "name/with/slashes",
            "name@with@symbols",
            "name.with.dots",
            "123-only-numbers-start-is-ok",  # This should actually work
            "name!exclamation"
        ]

        valid_git_url = "https://github.com/test/repo.git"

        for invalid_name in invalid_names[:-2]:  # Skip the valid one
            if invalid_name == "123-only-numbers-start-is-ok":
                continue
            with pytest.raises(ValueError, match="Invalid source name"):
                source_manager.add_source(
                    name=invalid_name,
                    git_url=valid_git_url
                )

    def test_e2e_registry_persistence(self, temp_dirs, temp_git_repo):
        """
        E2E Test 9: Registry persistence across instances

        Steps:
        1. Add source with one SourceManager instance
        2. Create new SourceManager instance
        3. Verify source persists
        4. Modify source with new instance
        5. Verify changes persist
        """
        cache_dir, config_dir = temp_dirs
        repo_dir, repo = temp_git_repo

        git_url = f"file://{repo_dir}"

        # Step 1: Add source with one instance
        manager1 = SourceManager(config_dir=config_dir)
        manager1.add_source(
            name="persistent-source",
            git_url=git_url,
            priority=25
        )

        # Step 2: Create new instance
        manager2 = SourceManager(config_dir=config_dir)

        # Step 3: Verify source persists
        sources = manager2.list_sources()
        assert len(sources) == 1
        assert sources[0]["name"] == "persistent-source"
        assert sources[0]["priority"] == 25

        # Step 4: Modify source with new instance
        manager2.add_source(
            name="persistent-source",
            git_url=git_url,
            priority=50  # Changed
        )

        # Step 5: Verify changes persist
        manager3 = SourceManager(config_dir=config_dir)
        source = manager3.get_source("persistent-source")
        assert source["priority"] == 50

    def test_e2e_cache_isolation(self, temp_dirs, temp_git_repo):
        """
        E2E Test 10: Cache isolation between different cache directories

        Steps:
        1. Clone to cache_dir_1
        2. Clone same repo to cache_dir_2
        3. Verify both caches are independent
        4. Modify one cache
        5. Verify other cache is unaffected
        """
        config_dir = temp_dirs[1]
        repo_dir, repo = temp_git_repo

        cache_dir_1 = tempfile.mkdtemp(prefix="ss_cache1_")
        cache_dir_2 = tempfile.mkdtemp(prefix="ss_cache2_")

        try:
            git_url = f"file://{repo_dir}"

            # Step 1: Clone to cache_dir_1
            git_repo_1 = GitConfigRepo(cache_dir=cache_dir_1)
            repo_path_1 = git_repo_1.clone_or_pull(
                source_name="test-source",
                git_url=git_url,
                branch="master"
            )

            # Step 2: Clone same repo to cache_dir_2
            git_repo_2 = GitConfigRepo(cache_dir=cache_dir_2)
            repo_path_2 = git_repo_2.clone_or_pull(
                source_name="test-source",
                git_url=git_url,
                branch="master"
            )

            # Step 3: Verify both caches are independent
            assert repo_path_1 != repo_path_2
            assert repo_path_1.exists()
            assert repo_path_2.exists()

            # Step 4: Modify one cache
            marker_file = repo_path_1 / "MARKER.txt"
            with open(marker_file, 'w') as f:
                f.write("Cache 1 marker")

            # Step 5: Verify other cache is unaffected
            assert marker_file.exists()
            assert not (repo_path_2 / "MARKER.txt").exists()

            configs_1 = git_repo_1.find_configs(repo_path_1)
            configs_2 = git_repo_2.find_configs(repo_path_2)
            assert len(configs_1) == len(configs_2) == 3

        finally:
            shutil.rmtree(cache_dir_1, ignore_errors=True)
            shutil.rmtree(cache_dir_2, ignore_errors=True)

    def test_e2e_auto_detect_token_env(self, temp_dirs):
        """
        E2E Test 11: Auto-detect token_env based on source type

        Steps:
        1. Add GitHub source without token_env
        2. Verify GITHUB_TOKEN was auto-detected
        3. Add GitLab source without token_env
        4. Verify GITLAB_TOKEN was auto-detected
        """
        cache_dir, config_dir = temp_dirs
        source_manager = SourceManager(config_dir=config_dir)

        # Step 1: Add GitHub source
        github_source = source_manager.add_source(
            name="github-test",
            git_url="https://github.com/test/repo.git",
            source_type="github"
            # No token_env specified
        )

        # Step 2: Verify GITHUB_TOKEN was auto-detected
        assert github_source["token_env"] == "GITHUB_TOKEN"

        # Step 3: Add GitLab source
        gitlab_source = source_manager.add_source(
            name="gitlab-test",
            git_url="https://gitlab.com/test/repo.git",
            source_type="gitlab"
            # No token_env specified
        )

        # Step 4: Verify GITLAB_TOKEN was auto-detected
        assert gitlab_source["token_env"] == "GITLAB_TOKEN"

        # Also test custom type (defaults to GIT_TOKEN)
        custom_source = source_manager.add_source(
            name="custom-test",
            git_url="https://custom.com/test/repo.git",
            source_type="custom"
        )
        assert custom_source["token_env"] == "GIT_TOKEN"

    def test_e2e_complete_user_workflow(self, temp_dirs, temp_git_repo):
        """
        E2E Test 12: Complete real-world user workflow

        Simulates a team using the feature end-to-end:
        1. Team lead creates config repository
        2. Team lead registers source
        3. Developer 1 clones and uses config
        4. Developer 2 uses same source (cached)
        5. Team lead updates repository
        6. Developers pull updates
        7. Config is removed from repo
        8. Error handling works correctly
        """
        cache_dir, config_dir = temp_dirs
        repo_dir, repo = temp_git_repo

        git_url = f"file://{repo_dir}"

        # Step 1: Team lead creates repository (already done by fixture)

        # Step 2: Team lead registers source
        source_manager = SourceManager(config_dir=config_dir)
        source_manager.add_source(
            name="team-configs",
            git_url=git_url,
            source_type="custom",
            branch="master",
            priority=1
        )

        # Step 3: Developer 1 clones and uses config
        git_repo = GitConfigRepo(cache_dir=cache_dir)
        source = source_manager.get_source("team-configs")
        repo_path = git_repo.clone_or_pull(
            source_name=source["name"],
            git_url=source["git_url"],
            branch=source["branch"]
        )

        react_config = git_repo.get_config(repo_path, "react")
        assert react_config["name"] == "react"

        # Step 4: Developer 2 uses same source (should use cache, not re-clone)
        # Simulate by checking if pull works (not re-clone)
        repo_path_2 = git_repo.clone_or_pull(
            source_name=source["name"],
            git_url=source["git_url"],
            branch=source["branch"]
        )
        assert repo_path == repo_path_2

        # Step 5: Team lead updates repository
        updated_react_config = react_config.copy()
        updated_react_config["max_pages"] = 500  # Increased limit

        react_config_path = Path(repo_dir) / "react.json"
        with open(react_config_path, 'w') as f:
            json.dump(updated_react_config, f, indent=2)

        repo.index.add(['react.json'])
        repo.index.commit("Increase React config max_pages to 500")

        # Step 6: Developers pull updates
        git_repo.clone_or_pull(
            source_name=source["name"],
            git_url=source["git_url"],
            branch=source["branch"]
        )

        updated_config = git_repo.get_config(repo_path, "react")
        assert updated_config["max_pages"] == 500

        # Step 7: Config is removed from repo
        react_config_path.unlink()
        repo.index.remove(['react.json'])
        repo.index.commit("Remove react.json")

        git_repo.clone_or_pull(
            source_name=source["name"],
            git_url=source["git_url"],
            branch=source["branch"]
        )

        # Step 8: Error handling works correctly
        with pytest.raises(FileNotFoundError, match="react.json"):
            git_repo.get_config(repo_path, "react")

        # But other configs still work
        vue_config = git_repo.get_config(repo_path, "vue")
        assert vue_config["name"] == "vue"


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP not installed")
class TestMCPToolsE2E:
    """E2E tests for MCP tools integration."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for cache and config."""
        cache_dir = tempfile.mkdtemp(prefix="ss_mcp_cache_")
        config_dir = tempfile.mkdtemp(prefix="ss_mcp_config_")

        # Set environment variables for tools to use
        os.environ["SKILL_SEEKERS_CACHE_DIR"] = cache_dir
        os.environ["SKILL_SEEKERS_CONFIG_DIR"] = config_dir

        yield cache_dir, config_dir

        # Cleanup
        os.environ.pop("SKILL_SEEKERS_CACHE_DIR", None)
        os.environ.pop("SKILL_SEEKERS_CONFIG_DIR", None)
        shutil.rmtree(cache_dir, ignore_errors=True)
        shutil.rmtree(config_dir, ignore_errors=True)

    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary git repository with sample configs."""
        repo_dir = tempfile.mkdtemp(prefix="ss_mcp_repo_")

        # Initialize git repository
        repo = git.Repo.init(repo_dir)

        # Create sample config
        config = {
            "name": "test-framework",
            "description": "Test framework for E2E",
            "base_url": "https://example.com/docs/",
            "selectors": {
                "main_content": "article",
                "title": "h1"
            },
            "url_patterns": {"include": [], "exclude": []},
            "categories": {},
            "rate_limit": 0.5,
            "max_pages": 50
        }

        config_path = Path(repo_dir) / "test-framework.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        repo.index.add(['*.json'])
        repo.index.commit("Initial commit")

        yield repo_dir, repo

        shutil.rmtree(repo_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_mcp_add_list_remove_source_e2e(self, temp_dirs, temp_git_repo):
        """
        MCP E2E Test 1: Complete add/list/remove workflow via MCP tools
        """
        from skill_seekers.mcp.server import (
            add_config_source_tool,
            list_config_sources_tool,
            remove_config_source_tool
        )

        cache_dir, config_dir = temp_dirs
        repo_dir, repo = temp_git_repo
        git_url = f"file://{repo_dir}"

        # Add source
        add_result = await add_config_source_tool({
            "name": "mcp-test-source",
            "git_url": git_url,
            "source_type": "custom",
            "branch": "master"
        })

        assert len(add_result) == 1
        assert "✅" in add_result[0].text
        assert "mcp-test-source" in add_result[0].text

        # List sources
        list_result = await list_config_sources_tool({})

        assert len(list_result) == 1
        assert "mcp-test-source" in list_result[0].text

        # Remove source
        remove_result = await remove_config_source_tool({
            "name": "mcp-test-source"
        })

        assert len(remove_result) == 1
        assert "✅" in remove_result[0].text
        assert "removed" in remove_result[0].text.lower()

    @pytest.mark.asyncio
    async def test_mcp_fetch_config_git_url_mode_e2e(self, temp_dirs, temp_git_repo):
        """
        MCP E2E Test 2: fetch_config with direct git URL
        """
        from skill_seekers.mcp.server import fetch_config_tool

        cache_dir, config_dir = temp_dirs
        repo_dir, repo = temp_git_repo
        git_url = f"file://{repo_dir}"

        # Create destination directory
        dest_dir = Path(config_dir) / "configs"
        dest_dir.mkdir(parents=True, exist_ok=True)

        result = await fetch_config_tool({
            "config_name": "test-framework",
            "git_url": git_url,
            "branch": "master",
            "destination": str(dest_dir)
        })

        assert len(result) == 1
        assert "✅" in result[0].text
        assert "test-framework" in result[0].text

        # Verify config was saved
        saved_config = dest_dir / "test-framework.json"
        assert saved_config.exists()

        with open(saved_config) as f:
            config_data = json.load(f)

        assert config_data["name"] == "test-framework"

    @pytest.mark.asyncio
    async def test_mcp_fetch_config_source_mode_e2e(self, temp_dirs, temp_git_repo):
        """
        MCP E2E Test 3: fetch_config with registered source
        """
        from skill_seekers.mcp.server import (
            add_config_source_tool,
            fetch_config_tool
        )

        cache_dir, config_dir = temp_dirs
        repo_dir, repo = temp_git_repo
        git_url = f"file://{repo_dir}"

        # Register source first
        await add_config_source_tool({
            "name": "test-source",
            "git_url": git_url,
            "source_type": "custom",
            "branch": "master"
        })

        # Fetch via source name
        dest_dir = Path(config_dir) / "configs"
        dest_dir.mkdir(parents=True, exist_ok=True)

        result = await fetch_config_tool({
            "config_name": "test-framework",
            "source": "test-source",
            "destination": str(dest_dir)
        })

        assert len(result) == 1
        assert "✅" in result[0].text
        assert "test-framework" in result[0].text

        # Verify config was saved
        saved_config = dest_dir / "test-framework.json"
        assert saved_config.exists()

    @pytest.mark.asyncio
    async def test_mcp_error_handling_e2e(self, temp_dirs, temp_git_repo):
        """
        MCP E2E Test 4: Error handling across all tools
        """
        from skill_seekers.mcp.server import (
            add_config_source_tool,
            list_config_sources_tool,
            remove_config_source_tool,
            fetch_config_tool
        )

        cache_dir, config_dir = temp_dirs
        repo_dir, repo = temp_git_repo
        git_url = f"file://{repo_dir}"

        # Test 1: Add source without name
        result = await add_config_source_tool({
            "git_url": git_url
        })
        assert "❌" in result[0].text
        assert "name" in result[0].text.lower()

        # Test 2: Add source without git_url
        result = await add_config_source_tool({
            "name": "test"
        })
        assert "❌" in result[0].text
        assert "git_url" in result[0].text.lower()

        # Test 3: Remove non-existent source
        result = await remove_config_source_tool({
            "name": "non-existent"
        })
        assert "❌" in result[0].text or "not found" in result[0].text.lower()

        # Test 4: Fetch config from non-existent source
        dest_dir = Path(config_dir) / "configs"
        dest_dir.mkdir(parents=True, exist_ok=True)

        result = await fetch_config_tool({
            "config_name": "test",
            "source": "non-existent-source",
            "destination": str(dest_dir)
        })
        assert "❌" in result[0].text or "not found" in result[0].text.lower()

        # Test 5: Fetch non-existent config from valid source
        await add_config_source_tool({
            "name": "valid-source",
            "git_url": git_url,
            "branch": "master"
        })

        result = await fetch_config_tool({
            "config_name": "non-existent-config",
            "source": "valid-source",
            "destination": str(dest_dir)
        })
        assert "❌" in result[0].text or "not found" in result[0].text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
