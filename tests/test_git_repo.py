#!/usr/bin/env python3
"""
Tests for GitConfigRepo class (git repository operations)
"""

import json
import pytest
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from git.exc import GitCommandError, InvalidGitRepositoryError

from skill_seekers.mcp.git_repo import GitConfigRepo


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory for tests."""
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def git_repo(temp_cache_dir):
    """Create GitConfigRepo instance with temp cache."""
    return GitConfigRepo(cache_dir=str(temp_cache_dir))


class TestGitConfigRepoInit:
    """Test GitConfigRepo initialization."""

    def test_init_with_custom_cache_dir(self, temp_cache_dir):
        """Test initialization with custom cache directory."""
        repo = GitConfigRepo(cache_dir=str(temp_cache_dir))
        assert repo.cache_dir == temp_cache_dir
        assert temp_cache_dir.exists()

    def test_init_with_env_var(self, tmp_path, monkeypatch):
        """Test initialization with environment variable."""
        env_cache = tmp_path / "env_cache"
        monkeypatch.setenv("SKILL_SEEKERS_CACHE_DIR", str(env_cache))

        repo = GitConfigRepo()
        assert repo.cache_dir == env_cache
        assert env_cache.exists()

    def test_init_with_default(self, monkeypatch):
        """Test initialization with default cache directory."""
        monkeypatch.delenv("SKILL_SEEKERS_CACHE_DIR", raising=False)

        repo = GitConfigRepo()
        expected = Path.home() / ".skill-seekers" / "cache"
        assert repo.cache_dir == expected


class TestValidateGitUrl:
    """Test git URL validation."""

    def test_validate_https_url(self):
        """Test validation of HTTPS URLs."""
        assert GitConfigRepo.validate_git_url("https://github.com/org/repo.git")
        assert GitConfigRepo.validate_git_url("https://gitlab.com/org/repo.git")

    def test_validate_http_url(self):
        """Test validation of HTTP URLs."""
        assert GitConfigRepo.validate_git_url("http://example.com/repo.git")

    def test_validate_ssh_url(self):
        """Test validation of SSH URLs."""
        assert GitConfigRepo.validate_git_url("git@github.com:org/repo.git")
        assert GitConfigRepo.validate_git_url("git@gitlab.com:group/project.git")

    def test_validate_file_url(self):
        """Test validation of file:// URLs."""
        assert GitConfigRepo.validate_git_url("file:///path/to/repo.git")

    def test_invalid_empty_url(self):
        """Test validation rejects empty URLs."""
        assert not GitConfigRepo.validate_git_url("")
        assert not GitConfigRepo.validate_git_url(None)

    def test_invalid_malformed_url(self):
        """Test validation rejects malformed URLs."""
        assert not GitConfigRepo.validate_git_url("not-a-url")
        assert not GitConfigRepo.validate_git_url("ftp://example.com/repo")

    def test_invalid_ssh_without_colon(self):
        """Test validation rejects SSH URLs without colon."""
        assert not GitConfigRepo.validate_git_url("git@github.com/org/repo.git")


class TestInjectToken:
    """Test token injection into git URLs."""

    def test_inject_token_https(self):
        """Test token injection into HTTPS URL."""
        url = "https://github.com/org/repo.git"
        token = "ghp_testtoken123"

        result = GitConfigRepo.inject_token(url, token)
        assert result == "https://ghp_testtoken123@github.com/org/repo.git"

    def test_inject_token_ssh_to_https(self):
        """Test SSH URL conversion to HTTPS with token."""
        url = "git@github.com:org/repo.git"
        token = "ghp_testtoken123"

        result = GitConfigRepo.inject_token(url, token)
        assert result == "https://ghp_testtoken123@github.com/org/repo.git"

    def test_inject_token_with_port(self):
        """Test token injection with custom port."""
        url = "https://gitlab.example.com:8443/org/repo.git"
        token = "token123"

        result = GitConfigRepo.inject_token(url, token)
        assert result == "https://token123@gitlab.example.com:8443/org/repo.git"

    def test_inject_token_gitlab_ssh(self):
        """Test GitLab SSH URL conversion."""
        url = "git@gitlab.com:group/project.git"
        token = "glpat-token123"

        result = GitConfigRepo.inject_token(url, token)
        assert result == "https://glpat-token123@gitlab.com/group/project.git"


class TestCloneOrPull:
    """Test clone and pull operations."""

    @patch('skill_seekers.mcp.git_repo.git.Repo.clone_from')
    def test_clone_new_repo(self, mock_clone, git_repo):
        """Test cloning a new repository."""
        mock_clone.return_value = MagicMock()

        result = git_repo.clone_or_pull(
            source_name="test-source",
            git_url="https://github.com/org/repo.git"
        )

        assert result == git_repo.cache_dir / "test-source"
        mock_clone.assert_called_once()

        # Verify shallow clone parameters
        call_kwargs = mock_clone.call_args[1]
        assert call_kwargs['depth'] == 1
        assert call_kwargs['single_branch'] is True
        assert call_kwargs['branch'] == "main"

    @patch('skill_seekers.mcp.git_repo.git.Repo')
    def test_pull_existing_repo(self, mock_repo_class, git_repo, temp_cache_dir):
        """Test pulling updates to existing repository."""
        # Create fake existing repo
        repo_path = temp_cache_dir / "test-source"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # Mock git.Repo
        mock_repo = MagicMock()
        mock_origin = MagicMock()
        mock_repo.remotes.origin = mock_origin
        mock_repo_class.return_value = mock_repo

        result = git_repo.clone_or_pull(
            source_name="test-source",
            git_url="https://github.com/org/repo.git"
        )

        assert result == repo_path
        mock_origin.pull.assert_called_once_with("main")

    @patch('skill_seekers.mcp.git_repo.git.Repo')
    def test_pull_with_token_update(self, mock_repo_class, git_repo, temp_cache_dir):
        """Test pulling with token updates remote URL."""
        # Create fake existing repo
        repo_path = temp_cache_dir / "test-source"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # Mock git.Repo
        mock_repo = MagicMock()
        mock_origin = MagicMock()
        mock_repo.remotes.origin = mock_origin
        mock_repo_class.return_value = mock_repo

        result = git_repo.clone_or_pull(
            source_name="test-source",
            git_url="https://github.com/org/repo.git",
            token="ghp_token123"
        )

        # Verify URL was updated with token
        mock_origin.set_url.assert_called_once()
        updated_url = mock_origin.set_url.call_args[0][0]
        assert "ghp_token123@github.com" in updated_url

    @patch('skill_seekers.mcp.git_repo.git.Repo.clone_from')
    def test_force_refresh_deletes_cache(self, mock_clone, git_repo, temp_cache_dir):
        """Test force refresh deletes existing cache."""
        # Create fake existing repo
        repo_path = temp_cache_dir / "test-source"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / "config.json").write_text("{}")

        mock_clone.return_value = MagicMock()

        git_repo.clone_or_pull(
            source_name="test-source",
            git_url="https://github.com/org/repo.git",
            force_refresh=True
        )

        # Verify clone was called (not pull)
        mock_clone.assert_called_once()

    @patch('skill_seekers.mcp.git_repo.git.Repo.clone_from')
    def test_clone_with_custom_branch(self, mock_clone, git_repo):
        """Test cloning with custom branch."""
        mock_clone.return_value = MagicMock()

        git_repo.clone_or_pull(
            source_name="test-source",
            git_url="https://github.com/org/repo.git",
            branch="develop"
        )

        call_kwargs = mock_clone.call_args[1]
        assert call_kwargs['branch'] == "develop"

    def test_clone_invalid_url_raises_error(self, git_repo):
        """Test cloning with invalid URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid git URL"):
            git_repo.clone_or_pull(
                source_name="test-source",
                git_url="not-a-valid-url"
            )

    @patch('skill_seekers.mcp.git_repo.git.Repo.clone_from')
    def test_clone_auth_failure_error(self, mock_clone, git_repo):
        """Test authentication failure error handling."""
        mock_clone.side_effect = GitCommandError(
            "clone",
            128,
            stderr="fatal: Authentication failed"
        )

        with pytest.raises(GitCommandError, match="Authentication failed"):
            git_repo.clone_or_pull(
                source_name="test-source",
                git_url="https://github.com/org/repo.git"
            )

    @patch('skill_seekers.mcp.git_repo.git.Repo.clone_from')
    def test_clone_not_found_error(self, mock_clone, git_repo):
        """Test repository not found error handling."""
        mock_clone.side_effect = GitCommandError(
            "clone",
            128,
            stderr="fatal: repository not found"
        )

        with pytest.raises(GitCommandError, match="Repository not found"):
            git_repo.clone_or_pull(
                source_name="test-source",
                git_url="https://github.com/org/nonexistent.git"
            )


class TestFindConfigs:
    """Test config file discovery."""

    def test_find_configs_in_root(self, git_repo, temp_cache_dir):
        """Test finding config files in repository root."""
        repo_path = temp_cache_dir / "test-repo"
        repo_path.mkdir()

        (repo_path / "config1.json").write_text("{}")
        (repo_path / "config2.json").write_text("{}")
        (repo_path / "README.md").write_text("# Readme")

        configs = git_repo.find_configs(repo_path)

        assert len(configs) == 2
        assert all(c.suffix == ".json" for c in configs)
        assert sorted([c.name for c in configs]) == ["config1.json", "config2.json"]

    def test_find_configs_in_subdirs(self, git_repo, temp_cache_dir):
        """Test finding config files in subdirectories."""
        repo_path = temp_cache_dir / "test-repo"
        configs_dir = repo_path / "configs"
        configs_dir.mkdir(parents=True)

        (repo_path / "root.json").write_text("{}")
        (configs_dir / "sub1.json").write_text("{}")
        (configs_dir / "sub2.json").write_text("{}")

        configs = git_repo.find_configs(repo_path)

        assert len(configs) == 3

    def test_find_configs_excludes_git_dir(self, git_repo, temp_cache_dir):
        """Test that .git directory is excluded from config search."""
        repo_path = temp_cache_dir / "test-repo"
        git_dir = repo_path / ".git" / "config"
        git_dir.mkdir(parents=True)

        (repo_path / "config.json").write_text("{}")
        (git_dir / "internal.json").write_text("{}")

        configs = git_repo.find_configs(repo_path)

        assert len(configs) == 1
        assert configs[0].name == "config.json"

    def test_find_configs_empty_repo(self, git_repo, temp_cache_dir):
        """Test finding configs in empty repository."""
        repo_path = temp_cache_dir / "empty-repo"
        repo_path.mkdir()

        configs = git_repo.find_configs(repo_path)

        assert configs == []

    def test_find_configs_nonexistent_repo(self, git_repo, temp_cache_dir):
        """Test finding configs in non-existent repository."""
        repo_path = temp_cache_dir / "nonexistent"

        configs = git_repo.find_configs(repo_path)

        assert configs == []

    def test_find_configs_sorted_by_name(self, git_repo, temp_cache_dir):
        """Test that configs are sorted by filename."""
        repo_path = temp_cache_dir / "test-repo"
        repo_path.mkdir()

        (repo_path / "zebra.json").write_text("{}")
        (repo_path / "alpha.json").write_text("{}")
        (repo_path / "beta.json").write_text("{}")

        configs = git_repo.find_configs(repo_path)

        assert [c.name for c in configs] == ["alpha.json", "beta.json", "zebra.json"]


class TestGetConfig:
    """Test config file loading."""

    def test_get_config_exact_match(self, git_repo, temp_cache_dir):
        """Test loading config with exact filename match."""
        repo_path = temp_cache_dir / "test-repo"
        repo_path.mkdir()

        config_data = {"name": "react", "version": "1.0"}
        (repo_path / "react.json").write_text(json.dumps(config_data))

        result = git_repo.get_config(repo_path, "react")

        assert result == config_data

    def test_get_config_with_json_extension(self, git_repo, temp_cache_dir):
        """Test loading config when .json extension is provided."""
        repo_path = temp_cache_dir / "test-repo"
        repo_path.mkdir()

        config_data = {"name": "vue"}
        (repo_path / "vue.json").write_text(json.dumps(config_data))

        result = git_repo.get_config(repo_path, "vue.json")

        assert result == config_data

    def test_get_config_case_insensitive(self, git_repo, temp_cache_dir):
        """Test loading config with case-insensitive match."""
        repo_path = temp_cache_dir / "test-repo"
        repo_path.mkdir()

        config_data = {"name": "Django"}
        (repo_path / "Django.json").write_text(json.dumps(config_data))

        result = git_repo.get_config(repo_path, "django")

        assert result == config_data

    def test_get_config_in_subdir(self, git_repo, temp_cache_dir):
        """Test loading config from subdirectory."""
        repo_path = temp_cache_dir / "test-repo"
        configs_dir = repo_path / "configs"
        configs_dir.mkdir(parents=True)

        config_data = {"name": "nestjs"}
        (configs_dir / "nestjs.json").write_text(json.dumps(config_data))

        result = git_repo.get_config(repo_path, "nestjs")

        assert result == config_data

    def test_get_config_not_found(self, git_repo, temp_cache_dir):
        """Test error when config not found."""
        repo_path = temp_cache_dir / "test-repo"
        repo_path.mkdir()

        (repo_path / "react.json").write_text("{}")

        with pytest.raises(FileNotFoundError, match="Config 'vue.json' not found"):
            git_repo.get_config(repo_path, "vue")

    def test_get_config_not_found_shows_available(self, git_repo, temp_cache_dir):
        """Test error message shows available configs."""
        repo_path = temp_cache_dir / "test-repo"
        repo_path.mkdir()

        (repo_path / "react.json").write_text("{}")
        (repo_path / "vue.json").write_text("{}")

        with pytest.raises(FileNotFoundError, match="Available configs: react, vue"):
            git_repo.get_config(repo_path, "django")

    def test_get_config_invalid_json(self, git_repo, temp_cache_dir):
        """Test error handling for invalid JSON."""
        repo_path = temp_cache_dir / "test-repo"
        repo_path.mkdir()

        (repo_path / "broken.json").write_text("{ invalid json }")

        with pytest.raises(ValueError, match="Invalid JSON"):
            git_repo.get_config(repo_path, "broken")
