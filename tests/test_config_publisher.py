#!/usr/bin/env python3
"""Tests for ConfigPublisher class (config publishing to source repos)."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from skill_seekers.mcp.config_publisher import ConfigPublisher, detect_category


def _get_default_branch(repo_path):
    """Get the default branch name of a git repo (master or main)."""
    import git

    repo = git.Repo(repo_path)
    return repo.active_branch.name


def _init_repo_with_main_branch(path):
    """Initialize a git repo ensuring the branch is named 'main'."""
    import git

    repo = git.Repo.init(path)
    repo.config_writer().set_value("user", "name", "Test").release()
    repo.config_writer().set_value("user", "email", "test@test.com").release()

    # Create initial commit on whatever default branch
    (path / "README.md").write_text("# Init\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    # Rename branch to 'main' if needed
    if repo.active_branch.name != "main":
        repo.git.branch("-m", repo.active_branch.name, "main")

    return repo


class TestDetectCategory:
    """Test detect_category() keyword scoring."""

    def test_game_engine_detected(self):
        config = {"name": "godot-4", "description": "Godot game engine config"}
        assert detect_category(config) == "game-engines"

    def test_web_framework_detected(self):
        config = {"name": "react-config", "description": "React web framework setup"}
        assert detect_category(config) == "web-frameworks"

    def test_ai_ml_detected(self):
        config = {"name": "pytorch-training", "description": "PyTorch model training config"}
        assert detect_category(config) == "ai-ml"

    def test_database_detected(self):
        config = {"name": "postgres-setup", "description": "PostgreSQL database config"}
        assert detect_category(config) == "databases"

    def test_devops_detected(self):
        config = {"name": "docker-compose", "description": "Docker container orchestration"}
        assert detect_category(config) == "devops"

    def test_cloud_detected(self):
        config = {"name": "aws-deployment", "description": "AWS cloud deployment config"}
        assert detect_category(config) == "cloud"

    def test_mobile_detected(self):
        config = {"name": "flutter-app", "description": "Flutter mobile application config"}
        assert detect_category(config) == "mobile"

    def test_testing_detected(self):
        config = {"name": "pytest-setup", "description": "Pytest testing framework"}
        assert detect_category(config) == "testing"

    def test_unknown_returns_custom(self):
        config = {"name": "my-random-thing", "description": "Something unrelated"}
        assert detect_category(config) == "custom"

    def test_empty_config_returns_custom(self):
        config = {}
        assert detect_category(config) == "custom"

    def test_name_only_matching(self):
        config = {"name": "tailwind-theme"}
        assert detect_category(config) == "css-frameworks"

    def test_description_only_matching(self):
        config = {"name": "my-config", "description": "Uses kubernetes for orchestration"}
        assert detect_category(config) == "devops"

    def test_highest_score_wins(self):
        # "react" and "vue" both in web-frameworks, so web-frameworks should score higher
        config = {"name": "react-vue-toolkit", "description": "React and Vue comparison"}
        assert detect_category(config) == "web-frameworks"

    def test_security_detected(self):
        config = {"name": "oauth-setup", "description": "OAuth and JWT authentication"}
        assert detect_category(config) == "security"

    def test_messaging_detected(self):
        config = {"name": "kafka-config", "description": "Apache Kafka messaging setup"}
        assert detect_category(config) == "messaging"


class TestPublishErrors:
    """Test ConfigPublisher.publish() error cases."""

    def test_publish_missing_config_file(self, tmp_path):
        publisher = ConfigPublisher.__new__(ConfigPublisher)
        publisher.git_repo = MagicMock()
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            publisher.publish(
                config_path=tmp_path / "nonexistent.json",
                source_name="test-source",
            )

    def test_publish_missing_name_field(self, tmp_path):
        config_file = tmp_path / "bad_config.json"
        config_file.write_text(json.dumps({"description": "No name field"}))

        publisher = ConfigPublisher.__new__(ConfigPublisher)
        publisher.git_repo = MagicMock()
        with pytest.raises(ValueError, match="must have a 'name' field"):
            publisher.publish(
                config_path=config_file,
                source_name="test-source",
            )

    @patch.dict(os.environ, {}, clear=True)
    def test_publish_missing_token(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"name": "test-config"}))

        # Create a mock source that returns proper data
        mock_source = {
            "name": "test-source",
            "git_url": "https://github.com/test/repo.git",
            "branch": "main",
            "token_env": "NONEXISTENT_TOKEN",
        }
        mock_manager = MagicMock()
        mock_manager.get_source.return_value = mock_source
        mock_manager.list_sources.return_value = [mock_source]

        publisher = ConfigPublisher.__new__(ConfigPublisher)
        publisher.git_repo = MagicMock()

        with (
            patch("skill_seekers.mcp.source_manager.SourceManager", return_value=mock_manager),
            patch("skill_seekers.cli.config_validator.validate_config", return_value=None),
            pytest.raises(RuntimeError, match="NONEXISTENT_TOKEN"),
        ):
            publisher.publish(config_path=config_file, source_name="test-source")

    def test_publish_source_not_found(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"name": "test-config"}))

        mock_manager = MagicMock()
        mock_manager.get_source.return_value = None
        mock_manager.list_sources.return_value = []

        publisher = ConfigPublisher.__new__(ConfigPublisher)
        publisher.git_repo = MagicMock()

        with (
            patch("skill_seekers.mcp.source_manager.SourceManager", return_value=mock_manager),
            patch("skill_seekers.cli.config_validator.validate_config", return_value=None),
            pytest.raises(ValueError, match="not found"),
        ):
            publisher.publish(config_path=config_file, source_name="nonexistent")

    def test_publish_duplicate_without_force(self, tmp_path):
        """Config already exists in target repo and force=False should raise."""
        import git as gitmodule

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"name": "existing-config"}))

        # Create a working repo with existing config
        working_path = tmp_path / "working"
        working_path.mkdir()
        repo = _init_repo_with_main_branch(working_path)

        # Add existing config
        config_dir_in_repo = working_path / "configs" / "custom"
        config_dir_in_repo.mkdir(parents=True)
        (config_dir_in_repo / "existing-config.json").write_text(
            json.dumps({"name": "existing-config"})
        )
        repo.index.add(["configs/custom/existing-config.json"])
        repo.index.commit("Add existing config")

        bare_repo_path = tmp_path / "remote.git"
        gitmodule.Repo.clone_from(str(working_path), str(bare_repo_path), bare=True)

        # Mock source manager
        mock_source = {
            "name": "test-source",
            "git_url": f"file://{bare_repo_path}",
            "branch": "main",
            "token_env": "DUMMY_TOKEN",
        }
        mock_manager = MagicMock()
        mock_manager.get_source.return_value = mock_source

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        publisher = ConfigPublisher.__new__(ConfigPublisher)
        from skill_seekers.mcp.git_repo import GitConfigRepo

        publisher.git_repo = GitConfigRepo(cache_dir=str(cache_dir))

        with (
            patch.dict(os.environ, {"DUMMY_TOKEN": "fake-token"}),
            patch("skill_seekers.mcp.source_manager.SourceManager", return_value=mock_manager),
            patch("skill_seekers.cli.config_validator.validate_config", return_value=None),
            pytest.raises(ValueError, match="already exists"),
        ):
            publisher.publish(
                config_path=config_file,
                source_name="test-source",
                category="custom",
                force=False,
            )


class TestPublishSuccess:
    """Test ConfigPublisher.publish() success path using a local bare git repo."""

    def test_publish_happy_path(self, tmp_path):
        """Full success path: clone -> copy -> commit -> push."""
        import git as gitmodule

        # Create config file to publish
        config_file = tmp_path / "my-config.json"
        config_data = {"name": "my-config", "description": "A test config for pytest"}
        config_file.write_text(json.dumps(config_data))

        # Create working repo with 'main' branch, then bare-clone as "remote"
        working_path = tmp_path / "working"
        working_path.mkdir()
        _init_repo_with_main_branch(working_path)

        bare_repo_path = tmp_path / "remote.git"
        gitmodule.Repo.clone_from(str(working_path), str(bare_repo_path), bare=True)

        # Mock source manager
        mock_source = {
            "name": "local-test",
            "git_url": f"file://{bare_repo_path}",
            "branch": "main",
            "token_env": "DUMMY_TOKEN",
        }
        mock_manager = MagicMock()
        mock_manager.get_source.return_value = mock_source

        # Create publisher with custom cache dir
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        publisher = ConfigPublisher.__new__(ConfigPublisher)
        from skill_seekers.mcp.git_repo import GitConfigRepo

        publisher.git_repo = GitConfigRepo(cache_dir=str(cache_dir))

        with (
            patch.dict(os.environ, {"DUMMY_TOKEN": "not-needed-for-file-protocol"}),
            patch("skill_seekers.mcp.source_manager.SourceManager", return_value=mock_manager),
            patch("skill_seekers.cli.config_validator.validate_config", return_value=None),
        ):
            result = publisher.publish(
                config_path=config_file,
                source_name="local-test",
                category="testing",
            )

        # Verify result
        assert result["success"] is True
        assert result["config_name"] == "my-config"
        assert result["config_path"] == "configs/testing/my-config.json"
        assert result["source"] == "local-test"
        assert result["category"] == "testing"
        assert len(result["commit_sha"]) == 8
        assert result["branch"] == "main"

        # Verify the file exists in the cached clone
        cached_repo = cache_dir / "source_local-test"
        assert (cached_repo / "configs" / "testing" / "my-config.json").exists()

        # Verify the config content was preserved
        with open(cached_repo / "configs" / "testing" / "my-config.json") as f:
            saved = json.load(f)
        assert saved["name"] == "my-config"

    def test_publish_force_overwrite(self, tmp_path):
        """Test that force=True overwrites an existing config."""
        import git as gitmodule

        config_file = tmp_path / "overwrite-config.json"
        config_data = {"name": "overwrite-config", "description": "Updated version"}
        config_file.write_text(json.dumps(config_data))

        # Create working repo with existing config
        working_path = tmp_path / "working"
        working_path.mkdir()
        repo = _init_repo_with_main_branch(working_path)

        # Pre-populate with existing config
        configs_dir = working_path / "configs" / "custom"
        configs_dir.mkdir(parents=True)
        (configs_dir / "overwrite-config.json").write_text(
            json.dumps({"name": "overwrite-config", "description": "Old version"})
        )
        repo.index.add(["configs/custom/overwrite-config.json"])
        repo.index.commit("Add existing config")

        bare_repo_path = tmp_path / "remote.git"
        gitmodule.Repo.clone_from(str(working_path), str(bare_repo_path), bare=True)

        mock_source = {
            "name": "local-test",
            "git_url": f"file://{bare_repo_path}",
            "branch": "main",
            "token_env": "DUMMY_TOKEN",
        }
        mock_manager = MagicMock()
        mock_manager.get_source.return_value = mock_source

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        publisher = ConfigPublisher.__new__(ConfigPublisher)
        from skill_seekers.mcp.git_repo import GitConfigRepo

        publisher.git_repo = GitConfigRepo(cache_dir=str(cache_dir))

        with (
            patch.dict(os.environ, {"DUMMY_TOKEN": "x"}),
            patch("skill_seekers.mcp.source_manager.SourceManager", return_value=mock_manager),
            patch("skill_seekers.cli.config_validator.validate_config", return_value=None),
        ):
            result = publisher.publish(
                config_path=config_file,
                source_name="local-test",
                category="custom",
                force=True,
            )

        assert result["success"] is True
        assert result["config_name"] == "overwrite-config"

        # Verify the file has updated content
        cached_repo = cache_dir / "source_local-test"
        with open(cached_repo / "configs" / "custom" / "overwrite-config.json") as f:
            saved = json.load(f)
        assert saved["description"] == "Updated version"

    def test_publish_auto_detect_category(self, tmp_path):
        """Test that category='auto' auto-detects from config content."""
        import git as gitmodule

        config_file = tmp_path / "react-config.json"
        config_data = {"name": "react-config", "description": "React web framework config"}
        config_file.write_text(json.dumps(config_data))

        working_path = tmp_path / "working"
        working_path.mkdir()
        _init_repo_with_main_branch(working_path)

        bare_repo_path = tmp_path / "remote.git"
        gitmodule.Repo.clone_from(str(working_path), str(bare_repo_path), bare=True)

        mock_source = {
            "name": "local-test",
            "git_url": f"file://{bare_repo_path}",
            "branch": "main",
            "token_env": "DUMMY_TOKEN",
        }
        mock_manager = MagicMock()
        mock_manager.get_source.return_value = mock_source

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        publisher = ConfigPublisher.__new__(ConfigPublisher)
        from skill_seekers.mcp.git_repo import GitConfigRepo

        publisher.git_repo = GitConfigRepo(cache_dir=str(cache_dir))

        with (
            patch.dict(os.environ, {"DUMMY_TOKEN": "x"}),
            patch("skill_seekers.mcp.source_manager.SourceManager", return_value=mock_manager),
            patch("skill_seekers.cli.config_validator.validate_config", return_value=None),
        ):
            result = publisher.publish(
                config_path=config_file,
                source_name="local-test",
                category="auto",
            )

        assert result["success"] is True
        assert result["category"] == "web-frameworks"
