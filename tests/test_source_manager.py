#!/usr/bin/env python3
"""
Tests for SourceManager class (config source registry management)
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone

from skill_seekers.mcp.source_manager import SourceManager


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory for tests."""
    config_dir = tmp_path / "test_config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def source_manager(temp_config_dir):
    """Create SourceManager instance with temp config."""
    return SourceManager(config_dir=str(temp_config_dir))


class TestSourceManagerInit:
    """Test SourceManager initialization."""

    def test_init_creates_config_dir(self, tmp_path):
        """Test that initialization creates config directory."""
        config_dir = tmp_path / "new_config"
        manager = SourceManager(config_dir=str(config_dir))

        assert config_dir.exists()
        assert manager.config_dir == config_dir

    def test_init_creates_registry_file(self, temp_config_dir):
        """Test that initialization creates registry file."""
        manager = SourceManager(config_dir=str(temp_config_dir))
        registry_file = temp_config_dir / "sources.json"

        assert registry_file.exists()

        # Verify initial structure
        with open(registry_file, 'r') as f:
            data = json.load(f)
            assert data == {"version": "1.0", "sources": []}

    def test_init_preserves_existing_registry(self, temp_config_dir):
        """Test that initialization doesn't overwrite existing registry."""
        registry_file = temp_config_dir / "sources.json"

        # Create existing registry
        existing_data = {
            "version": "1.0",
            "sources": [{"name": "test", "git_url": "https://example.com/repo.git"}]
        }
        with open(registry_file, 'w') as f:
            json.dump(existing_data, f)

        # Initialize manager
        manager = SourceManager(config_dir=str(temp_config_dir))

        # Verify data preserved
        with open(registry_file, 'r') as f:
            data = json.load(f)
            assert len(data["sources"]) == 1

    def test_init_with_default_config_dir(self):
        """Test initialization with default config directory."""
        manager = SourceManager()

        expected = Path.home() / ".skill-seekers"
        assert manager.config_dir == expected


class TestAddSource:
    """Test adding config sources."""

    def test_add_source_minimal(self, source_manager):
        """Test adding source with minimal parameters."""
        source = source_manager.add_source(
            name="team",
            git_url="https://github.com/myorg/configs.git"
        )

        assert source["name"] == "team"
        assert source["git_url"] == "https://github.com/myorg/configs.git"
        assert source["type"] == "github"
        assert source["token_env"] == "GITHUB_TOKEN"
        assert source["branch"] == "main"
        assert source["enabled"] is True
        assert source["priority"] == 100
        assert "added_at" in source
        assert "updated_at" in source

    def test_add_source_full_parameters(self, source_manager):
        """Test adding source with all parameters."""
        source = source_manager.add_source(
            name="company",
            git_url="https://gitlab.company.com/platform/configs.git",
            source_type="gitlab",
            token_env="CUSTOM_TOKEN",
            branch="develop",
            priority=1,
            enabled=False
        )

        assert source["name"] == "company"
        assert source["type"] == "gitlab"
        assert source["token_env"] == "CUSTOM_TOKEN"
        assert source["branch"] == "develop"
        assert source["priority"] == 1
        assert source["enabled"] is False

    def test_add_source_normalizes_name(self, source_manager):
        """Test that source names are normalized to lowercase."""
        source = source_manager.add_source(
            name="MyTeam",
            git_url="https://github.com/org/repo.git"
        )

        assert source["name"] == "myteam"

    def test_add_source_invalid_name_empty(self, source_manager):
        """Test that empty source names are rejected."""
        with pytest.raises(ValueError, match="Invalid source name"):
            source_manager.add_source(
                name="",
                git_url="https://github.com/org/repo.git"
            )

    def test_add_source_invalid_name_special_chars(self, source_manager):
        """Test that source names with special characters are rejected."""
        with pytest.raises(ValueError, match="Invalid source name"):
            source_manager.add_source(
                name="team@company",
                git_url="https://github.com/org/repo.git"
            )

    def test_add_source_valid_name_with_hyphens(self, source_manager):
        """Test that source names with hyphens are allowed."""
        source = source_manager.add_source(
            name="team-alpha",
            git_url="https://github.com/org/repo.git"
        )

        assert source["name"] == "team-alpha"

    def test_add_source_valid_name_with_underscores(self, source_manager):
        """Test that source names with underscores are allowed."""
        source = source_manager.add_source(
            name="team_alpha",
            git_url="https://github.com/org/repo.git"
        )

        assert source["name"] == "team_alpha"

    def test_add_source_empty_git_url(self, source_manager):
        """Test that empty git URLs are rejected."""
        with pytest.raises(ValueError, match="git_url cannot be empty"):
            source_manager.add_source(name="team", git_url="")

    def test_add_source_strips_git_url(self, source_manager):
        """Test that git URLs are stripped of whitespace."""
        source = source_manager.add_source(
            name="team",
            git_url="  https://github.com/org/repo.git  "
        )

        assert source["git_url"] == "https://github.com/org/repo.git"

    def test_add_source_updates_existing(self, source_manager):
        """Test that adding existing source updates it."""
        # Add initial source
        source1 = source_manager.add_source(
            name="team",
            git_url="https://github.com/org/repo1.git"
        )

        # Update source
        source2 = source_manager.add_source(
            name="team",
            git_url="https://github.com/org/repo2.git"
        )

        # Verify updated
        assert source2["git_url"] == "https://github.com/org/repo2.git"
        assert source2["added_at"] == source1["added_at"]  # Preserved
        assert source2["updated_at"] > source1["added_at"]  # Updated

        # Verify only one source exists
        sources = source_manager.list_sources()
        assert len(sources) == 1

    def test_add_source_persists_to_file(self, source_manager, temp_config_dir):
        """Test that added sources are persisted to file."""
        source_manager.add_source(
            name="team",
            git_url="https://github.com/org/repo.git"
        )

        # Read file directly
        registry_file = temp_config_dir / "sources.json"
        with open(registry_file, 'r') as f:
            data = json.load(f)

        assert len(data["sources"]) == 1
        assert data["sources"][0]["name"] == "team"

    def test_add_multiple_sources_sorted_by_priority(self, source_manager):
        """Test that multiple sources are sorted by priority."""
        source_manager.add_source(name="low", git_url="https://example.com/1.git", priority=100)
        source_manager.add_source(name="high", git_url="https://example.com/2.git", priority=1)
        source_manager.add_source(name="medium", git_url="https://example.com/3.git", priority=50)

        sources = source_manager.list_sources()

        assert [s["name"] for s in sources] == ["high", "medium", "low"]
        assert [s["priority"] for s in sources] == [1, 50, 100]


class TestGetSource:
    """Test retrieving config sources."""

    def test_get_source_exact_match(self, source_manager):
        """Test getting source with exact name match."""
        source_manager.add_source(name="team", git_url="https://github.com/org/repo.git")

        source = source_manager.get_source("team")

        assert source["name"] == "team"

    def test_get_source_case_insensitive(self, source_manager):
        """Test getting source is case-insensitive."""
        source_manager.add_source(name="MyTeam", git_url="https://github.com/org/repo.git")

        source = source_manager.get_source("myteam")

        assert source["name"] == "myteam"

    def test_get_source_not_found(self, source_manager):
        """Test error when source not found."""
        with pytest.raises(KeyError, match="Source 'nonexistent' not found"):
            source_manager.get_source("nonexistent")

    def test_get_source_not_found_shows_available(self, source_manager):
        """Test error message shows available sources."""
        source_manager.add_source(name="team1", git_url="https://example.com/1.git")
        source_manager.add_source(name="team2", git_url="https://example.com/2.git")

        with pytest.raises(KeyError, match="Available sources: team1, team2"):
            source_manager.get_source("team3")

    def test_get_source_empty_registry(self, source_manager):
        """Test error when registry is empty."""
        with pytest.raises(KeyError, match="Available sources: none"):
            source_manager.get_source("team")


class TestListSources:
    """Test listing config sources."""

    def test_list_sources_empty(self, source_manager):
        """Test listing sources when registry is empty."""
        sources = source_manager.list_sources()

        assert sources == []

    def test_list_sources_multiple(self, source_manager):
        """Test listing multiple sources."""
        source_manager.add_source(name="team1", git_url="https://example.com/1.git")
        source_manager.add_source(name="team2", git_url="https://example.com/2.git")
        source_manager.add_source(name="team3", git_url="https://example.com/3.git")

        sources = source_manager.list_sources()

        assert len(sources) == 3

    def test_list_sources_sorted_by_priority(self, source_manager):
        """Test that sources are sorted by priority."""
        source_manager.add_source(name="low", git_url="https://example.com/1.git", priority=100)
        source_manager.add_source(name="high", git_url="https://example.com/2.git", priority=1)

        sources = source_manager.list_sources()

        assert sources[0]["name"] == "high"
        assert sources[1]["name"] == "low"

    def test_list_sources_enabled_only(self, source_manager):
        """Test listing only enabled sources."""
        source_manager.add_source(name="enabled1", git_url="https://example.com/1.git", enabled=True)
        source_manager.add_source(name="disabled", git_url="https://example.com/2.git", enabled=False)
        source_manager.add_source(name="enabled2", git_url="https://example.com/3.git", enabled=True)

        sources = source_manager.list_sources(enabled_only=True)

        assert len(sources) == 2
        assert all(s["enabled"] for s in sources)
        assert sorted([s["name"] for s in sources]) == ["enabled1", "enabled2"]

    def test_list_sources_all_when_some_disabled(self, source_manager):
        """Test listing all sources includes disabled ones."""
        source_manager.add_source(name="enabled", git_url="https://example.com/1.git", enabled=True)
        source_manager.add_source(name="disabled", git_url="https://example.com/2.git", enabled=False)

        sources = source_manager.list_sources(enabled_only=False)

        assert len(sources) == 2


class TestRemoveSource:
    """Test removing config sources."""

    def test_remove_source_exists(self, source_manager):
        """Test removing existing source."""
        source_manager.add_source(name="team", git_url="https://github.com/org/repo.git")

        result = source_manager.remove_source("team")

        assert result is True
        assert len(source_manager.list_sources()) == 0

    def test_remove_source_case_insensitive(self, source_manager):
        """Test removing source is case-insensitive."""
        source_manager.add_source(name="MyTeam", git_url="https://github.com/org/repo.git")

        result = source_manager.remove_source("myteam")

        assert result is True

    def test_remove_source_not_found(self, source_manager):
        """Test removing non-existent source returns False."""
        result = source_manager.remove_source("nonexistent")

        assert result is False

    def test_remove_source_persists_to_file(self, source_manager, temp_config_dir):
        """Test that source removal is persisted to file."""
        source_manager.add_source(name="team1", git_url="https://example.com/1.git")
        source_manager.add_source(name="team2", git_url="https://example.com/2.git")

        source_manager.remove_source("team1")

        # Read file directly
        registry_file = temp_config_dir / "sources.json"
        with open(registry_file, 'r') as f:
            data = json.load(f)

        assert len(data["sources"]) == 1
        assert data["sources"][0]["name"] == "team2"

    def test_remove_source_from_multiple(self, source_manager):
        """Test removing one source from multiple."""
        source_manager.add_source(name="team1", git_url="https://example.com/1.git")
        source_manager.add_source(name="team2", git_url="https://example.com/2.git")
        source_manager.add_source(name="team3", git_url="https://example.com/3.git")

        source_manager.remove_source("team2")

        sources = source_manager.list_sources()
        assert len(sources) == 2
        assert sorted([s["name"] for s in sources]) == ["team1", "team3"]


class TestUpdateSource:
    """Test updating config sources."""

    def test_update_source_git_url(self, source_manager):
        """Test updating source git URL."""
        source_manager.add_source(name="team", git_url="https://github.com/org/repo1.git")

        updated = source_manager.update_source(name="team", git_url="https://github.com/org/repo2.git")

        assert updated["git_url"] == "https://github.com/org/repo2.git"

    def test_update_source_branch(self, source_manager):
        """Test updating source branch."""
        source_manager.add_source(name="team", git_url="https://github.com/org/repo.git")

        updated = source_manager.update_source(name="team", branch="develop")

        assert updated["branch"] == "develop"

    def test_update_source_enabled(self, source_manager):
        """Test updating source enabled status."""
        source_manager.add_source(name="team", git_url="https://github.com/org/repo.git", enabled=True)

        updated = source_manager.update_source(name="team", enabled=False)

        assert updated["enabled"] is False

    def test_update_source_priority(self, source_manager):
        """Test updating source priority."""
        source_manager.add_source(name="team", git_url="https://github.com/org/repo.git", priority=100)

        updated = source_manager.update_source(name="team", priority=1)

        assert updated["priority"] == 1

    def test_update_source_multiple_fields(self, source_manager):
        """Test updating multiple fields at once."""
        source_manager.add_source(name="team", git_url="https://github.com/org/repo.git")

        updated = source_manager.update_source(
            name="team",
            git_url="https://gitlab.com/org/repo.git",
            type="gitlab",
            branch="develop",
            priority=1
        )

        assert updated["git_url"] == "https://gitlab.com/org/repo.git"
        assert updated["type"] == "gitlab"
        assert updated["branch"] == "develop"
        assert updated["priority"] == 1

    def test_update_source_updates_timestamp(self, source_manager):
        """Test that update modifies updated_at timestamp."""
        source = source_manager.add_source(name="team", git_url="https://github.com/org/repo.git")
        original_updated = source["updated_at"]

        updated = source_manager.update_source(name="team", branch="develop")

        assert updated["updated_at"] > original_updated

    def test_update_source_not_found(self, source_manager):
        """Test error when updating non-existent source."""
        with pytest.raises(KeyError, match="Source 'nonexistent' not found"):
            source_manager.update_source(name="nonexistent", branch="main")

    def test_update_source_resorts_by_priority(self, source_manager):
        """Test that updating priority re-sorts sources."""
        source_manager.add_source(name="team1", git_url="https://example.com/1.git", priority=1)
        source_manager.add_source(name="team2", git_url="https://example.com/2.git", priority=2)

        # Change team2 to higher priority
        source_manager.update_source(name="team2", priority=0)

        sources = source_manager.list_sources()
        assert sources[0]["name"] == "team2"
        assert sources[1]["name"] == "team1"


class TestDefaultTokenEnv:
    """Test default token environment variable detection."""

    def test_default_token_env_github(self, source_manager):
        """Test GitHub sources get GITHUB_TOKEN."""
        source = source_manager.add_source(
            name="team",
            git_url="https://github.com/org/repo.git",
            source_type="github"
        )

        assert source["token_env"] == "GITHUB_TOKEN"

    def test_default_token_env_gitlab(self, source_manager):
        """Test GitLab sources get GITLAB_TOKEN."""
        source = source_manager.add_source(
            name="team",
            git_url="https://gitlab.com/org/repo.git",
            source_type="gitlab"
        )

        assert source["token_env"] == "GITLAB_TOKEN"

    def test_default_token_env_gitea(self, source_manager):
        """Test Gitea sources get GITEA_TOKEN."""
        source = source_manager.add_source(
            name="team",
            git_url="https://gitea.example.com/org/repo.git",
            source_type="gitea"
        )

        assert source["token_env"] == "GITEA_TOKEN"

    def test_default_token_env_bitbucket(self, source_manager):
        """Test Bitbucket sources get BITBUCKET_TOKEN."""
        source = source_manager.add_source(
            name="team",
            git_url="https://bitbucket.org/org/repo.git",
            source_type="bitbucket"
        )

        assert source["token_env"] == "BITBUCKET_TOKEN"

    def test_default_token_env_custom(self, source_manager):
        """Test custom sources get GIT_TOKEN."""
        source = source_manager.add_source(
            name="team",
            git_url="https://git.example.com/org/repo.git",
            source_type="custom"
        )

        assert source["token_env"] == "GIT_TOKEN"

    def test_override_token_env(self, source_manager):
        """Test that custom token_env overrides default."""
        source = source_manager.add_source(
            name="team",
            git_url="https://github.com/org/repo.git",
            source_type="github",
            token_env="MY_CUSTOM_TOKEN"
        )

        assert source["token_env"] == "MY_CUSTOM_TOKEN"


class TestRegistryPersistence:
    """Test registry file I/O."""

    def test_registry_atomic_write(self, source_manager, temp_config_dir):
        """Test that registry writes are atomic (temp file + rename)."""
        source_manager.add_source(name="team", git_url="https://github.com/org/repo.git")

        # Verify no .tmp file left behind
        temp_files = list(temp_config_dir.glob("*.tmp"))
        assert len(temp_files) == 0

    def test_registry_json_formatting(self, source_manager, temp_config_dir):
        """Test that registry JSON is properly formatted."""
        source_manager.add_source(name="team", git_url="https://github.com/org/repo.git")

        registry_file = temp_config_dir / "sources.json"
        content = registry_file.read_text()

        # Verify it's pretty-printed
        assert "  " in content  # Indentation
        data = json.loads(content)
        assert "version" in data
        assert "sources" in data

    def test_registry_corrupted_file(self, temp_config_dir):
        """Test error handling for corrupted registry file."""
        registry_file = temp_config_dir / "sources.json"
        registry_file.write_text("{ invalid json }")

        # The constructor will fail when trying to read the corrupted file
        # during initialization, but it actually creates a new valid registry
        # So we need to test reading a corrupted file after construction
        manager = SourceManager(config_dir=str(temp_config_dir))

        # Corrupt the file after initialization
        registry_file.write_text("{ invalid json }")

        # Now _read_registry should fail
        with pytest.raises(ValueError, match="Corrupted registry file"):
            manager._read_registry()
