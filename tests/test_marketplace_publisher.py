#!/usr/bin/env python3
"""Tests for MarketplacePublisher class (skill publishing to plugin repos)"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from skill_seekers.services.marketplace_publisher import MarketplacePublisher


@pytest.fixture
def temp_config_dir(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def skill_dir(tmp_path):
    sd = tmp_path / "test-skill"
    sd.mkdir()
    (sd / "SKILL.md").write_text(
        "---\nname: test-skill\ndescription: A test skill for unit testing.\n---\n\n"
        "# Test Skill\n\nThis is a test skill.\n"
    )
    refs = sd / "references" / "documentation"
    refs.mkdir(parents=True)
    (refs / "index.md").write_text("# Documentation\n\nTest docs.\n")
    return sd


@pytest.fixture
def skill_dir_no_frontmatter(tmp_path):
    sd = tmp_path / "plain-skill"
    sd.mkdir()
    (sd / "SKILL.md").write_text("# Plain Skill\n\nNo frontmatter here.\n")
    return sd


@pytest.fixture
def second_skill_dir(tmp_path):
    sd = tmp_path / "second-skill"
    sd.mkdir()
    (sd / "SKILL.md").write_text(
        "---\nname: second-skill\ndescription: Another test skill.\n---\n\n# Second Skill\n"
    )
    return sd


def _make_bare_remote(tmp_path):
    """Create a marketplace repo and a bare clone of it to act as the remote."""
    import git as gitmodule

    working_path = tmp_path / "working"
    working_path.mkdir()
    repo = gitmodule.Repo.init(working_path, initial_branch="main")
    repo.config_writer().set_value("user", "name", "Test").release()
    repo.config_writer().set_value("user", "email", "t@t.com").release()
    mp_dir = working_path / ".claude-plugin"
    mp_dir.mkdir()
    with open(mp_dir / "marketplace.json", "w") as f:
        json.dump({"$schema": "", "name": "t", "description": "", "owner": {}, "plugins": []}, f)
    (working_path / "plugins").mkdir()
    repo.index.add([".claude-plugin/marketplace.json"])
    repo.index.commit("Initial commit")
    bare_repo_path = tmp_path / "remote.git"
    gitmodule.Repo.clone_from(str(working_path), str(bare_repo_path), bare=True)
    return bare_repo_path


def _make_manager(tmp_path, git_url):
    from skill_seekers.services.marketplace_manager import MarketplaceManager

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    manager = MarketplaceManager(config_dir=str(config_dir))
    manager.add_marketplace(
        name="local-test",
        git_url=git_url,
        token_env="DUMMY_TOKEN",
        branch="main",
        author={"name": "Test", "email": "t@t.com"},
    )
    return manager


@pytest.fixture
def mock_marketplace_repo(tmp_path):
    import git

    repo_path = tmp_path / "marketplace_repo"
    repo_path.mkdir()
    repo = git.Repo.init(repo_path)
    mp_dir = repo_path / ".claude-plugin"
    mp_dir.mkdir()
    mp_json = {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": "test-marketplace",
        "description": "Test marketplace",
        "owner": {"name": "Test", "email": "test@example.com"},
        "plugins": [
            {
                "name": "existing-plugin",
                "description": "An existing plugin",
                "author": {"name": "Test", "email": "test@example.com"},
                "source": "./plugins/existing-plugin",
                "category": "development",
            }
        ],
    }
    with open(mp_dir / "marketplace.json", "w") as f:
        json.dump(mp_json, f, indent=2)
    (repo_path / "plugins").mkdir()
    repo.index.add([".claude-plugin/marketplace.json"])
    repo.index.commit("Initial commit")
    return repo_path


class TestReadFrontmatter:
    def test_read_frontmatter_valid(self, skill_dir):
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        fm = publisher._read_frontmatter(skill_dir / "SKILL.md")
        assert fm["name"] == "test-skill"
        assert fm["description"] == "A test skill for unit testing."

    def test_read_frontmatter_no_frontmatter(self, skill_dir_no_frontmatter):
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        fm = publisher._read_frontmatter(skill_dir_no_frontmatter / "SKILL.md")
        assert fm == {}

    def test_read_frontmatter_empty_file(self, tmp_path):
        (tmp_path / "SKILL.md").write_text("")
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        assert publisher._read_frontmatter(tmp_path / "SKILL.md") == {}


class TestCopySkillToPlugin:
    def test_copy_creates_correct_structure(self, skill_dir, tmp_path):
        plugin_dir = tmp_path / "plugin_output"
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        publisher._copy_skill_to_plugin(skill_dir, plugin_dir, "test-skill")
        assert (plugin_dir / "skills" / "test-skill" / "SKILL.md").exists()
        assert (
            plugin_dir / "skills" / "test-skill" / "references" / "documentation" / "index.md"
        ).exists()

    def test_copy_skill_md_content_preserved(self, skill_dir, tmp_path):
        plugin_dir = tmp_path / "plugin_output"
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        publisher._copy_skill_to_plugin(skill_dir, plugin_dir, "test-skill")
        original = (skill_dir / "SKILL.md").read_text()
        copied = (plugin_dir / "skills" / "test-skill" / "SKILL.md").read_text()
        assert original == copied

    def test_copy_without_references(self, tmp_path):
        skill_dir = tmp_path / "skill-no-refs"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill\n")
        plugin_dir = tmp_path / "plugin_output"
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        publisher._copy_skill_to_plugin(skill_dir, plugin_dir, "test-skill")
        assert (plugin_dir / "skills" / "test-skill" / "SKILL.md").exists()
        assert not (plugin_dir / "skills" / "test-skill" / "references").exists()


class TestGeneratePluginJson:
    def test_generate_plugin_json(self):
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        result = publisher._generate_plugin_json(
            "test-skill", "A test skill", {"name": "Test", "email": "test@example.com"}
        )
        assert result == {
            "name": "test-skill",
            "description": "A test skill",
            "author": {"name": "Test", "email": "test@example.com"},
        }


class TestUpdateMarketplaceJson:
    def test_update_appends_new_plugin(self, mock_marketplace_repo):
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        author = {"name": "Test", "email": "test@example.com"}
        publisher._update_marketplace_json(
            mock_marketplace_repo, "new-plugin", "New plugin", author, "development"
        )
        with open(mock_marketplace_repo / ".claude-plugin" / "marketplace.json") as f:
            data = json.load(f)
        assert len(data["plugins"]) == 2
        assert "new-plugin" in [p["name"] for p in data["plugins"]]

    def test_update_existing_plugin(self, mock_marketplace_repo):
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        author = {"name": "Test", "email": "test@example.com"}
        publisher._update_marketplace_json(
            mock_marketplace_repo, "existing-plugin", "Updated", author, "tools"
        )
        with open(mock_marketplace_repo / ".claude-plugin" / "marketplace.json") as f:
            data = json.load(f)
        assert len(data["plugins"]) == 1
        assert data["plugins"][0]["description"] == "Updated"

    def test_update_sorts_plugins_alphabetically(self, mock_marketplace_repo):
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        author = {"name": "Test", "email": "test@example.com"}
        publisher._update_marketplace_json(
            mock_marketplace_repo, "aaa-plugin", "First", author, "dev"
        )
        with open(mock_marketplace_repo / ".claude-plugin" / "marketplace.json") as f:
            data = json.load(f)
        names = [p["name"] for p in data["plugins"]]
        assert names == sorted(names)

    def test_update_creates_marketplace_json_if_missing(self, tmp_path):
        repo_path = tmp_path / "empty_repo"
        repo_path.mkdir()
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        author = {"name": "Test", "email": "test@example.com"}
        publisher._update_marketplace_json(repo_path, "new-plugin", "Desc", author, "development")
        assert (repo_path / ".claude-plugin" / "marketplace.json").exists()


class TestPublishErrors:
    def test_publish_missing_skill_md(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        publisher.git_repo = MagicMock()
        with pytest.raises(FileNotFoundError, match="SKILL.md not found"):
            publisher.publish(skill_dir=empty_dir, marketplace_name="test")

    @patch.dict(os.environ, {}, clear=True)
    def test_publish_missing_token(self, skill_dir, temp_config_dir):
        from skill_seekers.services.marketplace_manager import MarketplaceManager

        manager = MarketplaceManager(config_dir=str(temp_config_dir))
        manager.add_marketplace(
            name="test", git_url="https://github.com/test/repo.git", token_env="NONEXISTENT_TOKEN"
        )
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        publisher.git_repo = MagicMock()
        with (
            patch(
                "skill_seekers.services.marketplace_publisher.MarketplaceManager",
                return_value=manager,
            ),
            pytest.raises(RuntimeError, match="Set NONEXISTENT_TOKEN"),
        ):
            publisher.publish(skill_dir=skill_dir, marketplace_name="test")

    def test_publish_plugin_already_exists(self, skill_dir, tmp_path, temp_config_dir):
        import git as gitmodule
        from skill_seekers.services.marketplace_manager import MarketplaceManager

        manager = MarketplaceManager(config_dir=str(temp_config_dir))
        manager.add_marketplace(
            name="test", git_url="https://github.com/test/repo.git", token_env="TEST_TOKEN"
        )
        # Create a cached repo without .git so publish() takes the clone path
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        publisher.git_repo = MagicMock()
        publisher.git_repo.cache_dir = cache_dir
        publisher.git_repo.inject_token.return_value = "https://fake@github.com/test/repo.git"

        # Mock clone_from to create the dir with existing plugin
        def fake_clone(_url, path, **_kwargs):
            from pathlib import Path

            p = Path(path)
            p.mkdir(parents=True, exist_ok=True)
            (p / "plugins" / "test-skill").mkdir(parents=True)
            r = gitmodule.Repo.init(p, initial_branch="main")
            r.create_remote("origin", _url)
            return r

        with (
            patch.dict(os.environ, {"TEST_TOKEN": "fake-token"}),
            patch(
                "skill_seekers.services.marketplace_publisher.MarketplaceManager",
                return_value=manager,
            ),
            patch.object(gitmodule.Repo, "clone_from", side_effect=fake_clone),
            pytest.raises(ValueError, match="already exists"),
        ):
            publisher.publish(skill_dir=skill_dir, marketplace_name="test")

    def test_publish_marketplace_not_found(self, skill_dir, temp_config_dir):
        from skill_seekers.services.marketplace_manager import MarketplaceManager

        manager = MarketplaceManager(config_dir=str(temp_config_dir))
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        publisher.git_repo = MagicMock()
        with (
            patch(
                "skill_seekers.services.marketplace_publisher.MarketplaceManager",
                return_value=manager,
            ),
            pytest.raises(KeyError, match="not found"),
        ):
            publisher.publish(skill_dir=skill_dir, marketplace_name="nonexistent")


class TestValidateSkillName:
    """Test skill name validation to prevent path traversal."""

    def test_valid_names(self):
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        assert publisher._validate_skill_name("react") == "react"
        assert publisher._validate_skill_name("spine-unity") == "spine-unity"
        assert publisher._validate_skill_name("my_skill_v2") == "my_skill_v2"
        assert publisher._validate_skill_name("skill.v1") == "skill.v1"

    def test_path_traversal_rejected(self):
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        with pytest.raises(ValueError, match="Invalid skill name"):
            publisher._validate_skill_name("../../etc/passwd")
        with pytest.raises(ValueError, match="Invalid skill name"):
            publisher._validate_skill_name("../escape")

    def test_empty_name_rejected(self):
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        with pytest.raises(ValueError, match="Invalid skill name"):
            publisher._validate_skill_name("")

    def test_slash_rejected(self):
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        with pytest.raises(ValueError, match="Invalid skill name"):
            publisher._validate_skill_name("path/traversal")

    def test_special_chars_rejected(self):
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        with pytest.raises(ValueError, match="Invalid skill name"):
            publisher._validate_skill_name("skill;rm -rf")


class TestPublishSuccess:
    """Test publish() success path using a local bare git repo."""

    def test_publish_success_flow(self, skill_dir, tmp_path):
        """Full success path: clone → copy → commit → push."""
        import git as gitmodule

        # Create a working repo with initial marketplace structure, then bare-clone it
        working_path = tmp_path / "working"
        working_path.mkdir()
        repo = gitmodule.Repo.init(working_path, initial_branch="main")
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        mp_dir = working_path / ".claude-plugin"
        mp_dir.mkdir()
        mp_json = {
            "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
            "name": "test",
            "description": "Test",
            "owner": {"name": "Test", "email": "test@test.com"},
            "plugins": [],
        }
        with open(mp_dir / "marketplace.json", "w") as f:
            json.dump(mp_json, f)
        (working_path / "plugins").mkdir()
        repo.index.add([".claude-plugin/marketplace.json"])
        repo.index.commit("Initial commit")

        # Create bare clone as the "remote"
        bare_repo_path = tmp_path / "remote.git"
        gitmodule.Repo.clone_from(str(working_path), str(bare_repo_path), bare=True)

        # Register marketplace with file:// URL
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        from skill_seekers.services.marketplace_manager import MarketplaceManager

        manager = MarketplaceManager(config_dir=str(config_dir))
        manager.add_marketplace(
            name="local-test",
            git_url=f"file://{bare_repo_path}",
            token_env="DUMMY_TOKEN",
            branch="main",
            author={"name": "Test Author", "email": "test@example.com"},
        )

        # Create publisher with custom cache dir
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        from skill_seekers.services.git_repo import GitConfigRepo

        publisher.git_repo = GitConfigRepo(cache_dir=str(cache_dir))

        # Publish — file:// URLs don't need real tokens but we need the env var set
        with (
            patch.dict(os.environ, {"DUMMY_TOKEN": "not-needed-for-file-protocol"}),
            patch(
                "skill_seekers.services.marketplace_publisher.MarketplaceManager",
                return_value=manager,
            ),
        ):
            result = publisher.publish(
                skill_dir=skill_dir,
                marketplace_name="local-test",
                category="testing",
            )

        # Verify result
        assert result["success"] is True
        assert result["plugin_path"] == "plugins/test-skill"
        assert result["branch"] == "main"
        assert len(result["commit_sha"]) == 7

        # Verify files in the cached clone
        cached_repo = cache_dir / "marketplace_local-test"
        assert (
            cached_repo / "plugins" / "test-skill" / "skills" / "test-skill" / "SKILL.md"
        ).exists()
        assert (cached_repo / "plugins" / "test-skill" / ".claude-plugin" / "plugin.json").exists()

        # Verify marketplace.json was updated
        with open(cached_repo / ".claude-plugin" / "marketplace.json") as f:
            data = json.load(f)
        plugin_names = [p["name"] for p in data["plugins"]]
        assert "test-skill" in plugin_names

    def test_publish_with_force_overwrites(self, skill_dir, tmp_path):
        """Test that force=True overwrites an existing plugin."""
        import git as gitmodule

        working_path = tmp_path / "working"
        working_path.mkdir()
        repo = gitmodule.Repo.init(working_path, initial_branch="main")
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "t@t.com").release()

        mp_dir = working_path / ".claude-plugin"
        mp_dir.mkdir()
        with open(mp_dir / "marketplace.json", "w") as f:
            json.dump(
                {"$schema": "", "name": "t", "description": "", "owner": {}, "plugins": []}, f
            )
        (working_path / "plugins" / "test-skill" / ".claude-plugin").mkdir(parents=True)
        repo.index.add([".claude-plugin/marketplace.json"])
        repo.index.commit("Initial")

        bare_repo_path = tmp_path / "remote.git"
        gitmodule.Repo.clone_from(str(working_path), str(bare_repo_path), bare=True)

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        from skill_seekers.services.marketplace_manager import MarketplaceManager

        manager = MarketplaceManager(config_dir=str(config_dir))
        manager.add_marketplace(
            name="local-test",
            git_url=f"file://{bare_repo_path}",
            token_env="DUMMY_TOKEN",
            branch="main",
            author={"name": "Test", "email": "t@t.com"},
        )

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        from skill_seekers.services.git_repo import GitConfigRepo

        publisher.git_repo = GitConfigRepo(cache_dir=str(cache_dir))

        with (
            patch.dict(os.environ, {"DUMMY_TOKEN": "x"}),
            patch(
                "skill_seekers.services.marketplace_publisher.MarketplaceManager",
                return_value=manager,
            ),
        ):
            result = publisher.publish(
                skill_dir=skill_dir,
                marketplace_name="local-test",
                category="testing",
                force=True,
            )

        assert result["success"] is True


class TestPublishCachedRepo:
    """Regression tests for repeated publishes against the persistent cache."""

    def _make_publisher(self, tmp_path, mock_git_repo=False):
        from skill_seekers.services.git_repo import GitConfigRepo

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        publisher = MarketplacePublisher.__new__(MarketplacePublisher)
        if mock_git_repo:
            publisher.git_repo = MagicMock()
            publisher.git_repo.cache_dir = cache_dir
        else:
            publisher.git_repo = GitConfigRepo(cache_dir=str(cache_dir))
        return publisher, cache_dir

    def test_second_publish_pulls_via_token_url(self, skill_dir, second_skill_dir, tmp_path):
        """Regression: the cached-repo pull must use the token-injected URL.

        After the first publish, origin in the cached repo is deliberately reset
        to the tokenless git_url. Here the tokenless URL is unreachable (like a
        private repo without credentials), so pulling through origin fails —
        the second publish only succeeds if the pull goes through the token URL.
        """
        import git as gitmodule

        bare_repo_path = _make_bare_remote(tmp_path)
        tokenless_url = f"file://{tmp_path}/nonexistent-private.git"
        manager = _make_manager(tmp_path, tokenless_url)

        publisher, cache_dir = self._make_publisher(tmp_path, mock_git_repo=True)
        # The "token URL" is the only one that actually reaches the remote
        publisher.git_repo.inject_token.return_value = f"file://{bare_repo_path}"

        with (
            patch.dict(os.environ, {"DUMMY_TOKEN": "x"}),
            patch(
                "skill_seekers.services.marketplace_publisher.MarketplaceManager",
                return_value=manager,
            ),
        ):
            first = publisher.publish(skill_dir=skill_dir, marketplace_name="local-test")
            # First publish strips the token: origin is now the unreachable URL
            cached = gitmodule.Repo(cache_dir / "marketplace_local-test")
            assert cached.remotes.origin.url == tokenless_url
            second = publisher.publish(skill_dir=second_skill_dir, marketplace_name="local-test")

        assert first["success"] is True
        assert second["success"] is True
        bare = gitmodule.Repo(bare_repo_path)
        names = bare.git.ls_tree("--name-only", "main", "plugins/").splitlines()
        assert "plugins/second-skill" in names

    def test_create_branch_publish_restores_base_branch(self, skill_dir, tmp_path):
        """Regression: create_branch=True must not leave the persistent cache
        checked out on the skill/<name> feature branch."""
        import git as gitmodule

        bare_repo_path = _make_bare_remote(tmp_path)
        manager = _make_manager(tmp_path, f"file://{bare_repo_path}")
        publisher, cache_dir = self._make_publisher(tmp_path)

        with (
            patch.dict(os.environ, {"DUMMY_TOKEN": "x"}),
            patch(
                "skill_seekers.services.marketplace_publisher.MarketplaceManager",
                return_value=manager,
            ),
        ):
            result = publisher.publish(
                skill_dir=skill_dir, marketplace_name="local-test", create_branch=True
            )

        assert result["success"] is True
        assert result["branch"] == "skill/test-skill"
        cached = gitmodule.Repo(cache_dir / "marketplace_local-test")
        assert cached.active_branch.name == "main"

    def test_publish_after_create_branch_lands_on_base_branch(
        self, skill_dir, second_skill_dir, tmp_path
    ):
        """Regression: a default-branch publish after a create_branch publish must
        push the new skill to the remote base branch (previously it 'succeeded'
        while committing on the stale feature branch and pushing nothing)."""
        import git as gitmodule

        bare_repo_path = _make_bare_remote(tmp_path)
        manager = _make_manager(tmp_path, f"file://{bare_repo_path}")
        publisher, _cache_dir = self._make_publisher(tmp_path)

        with (
            patch.dict(os.environ, {"DUMMY_TOKEN": "x"}),
            patch(
                "skill_seekers.services.marketplace_publisher.MarketplaceManager",
                return_value=manager,
            ),
        ):
            publisher.publish(
                skill_dir=skill_dir, marketplace_name="local-test", create_branch=True
            )
            second = publisher.publish(skill_dir=second_skill_dir, marketplace_name="local-test")

        assert second["success"] is True
        assert second["branch"] == "main"
        bare = gitmodule.Repo(bare_repo_path)
        names = bare.git.ls_tree("--name-only", "main", "plugins/").splitlines()
        assert "plugins/second-skill" in names
        # The commit reported by the second publish is the new remote main head
        assert bare.commit("main").hexsha[:7] == second["commit_sha"]

    def test_create_branch_republish_after_remote_branch_deleted(self, skill_dir, tmp_path):
        """Regression: republishing the same skill with create_branch=True (e.g.
        after the PR branch was merged and deleted) must not crash on the
        leftover local branch in the persistent cache."""
        import git as gitmodule

        bare_repo_path = _make_bare_remote(tmp_path)
        manager = _make_manager(tmp_path, f"file://{bare_repo_path}")
        publisher, _cache_dir = self._make_publisher(tmp_path)

        with (
            patch.dict(os.environ, {"DUMMY_TOKEN": "x"}),
            patch(
                "skill_seekers.services.marketplace_publisher.MarketplaceManager",
                return_value=manager,
            ),
        ):
            publisher.publish(
                skill_dir=skill_dir, marketplace_name="local-test", create_branch=True
            )
            # Simulate the feature branch being merged + deleted on the remote
            bare = gitmodule.Repo(bare_repo_path)
            bare.git.branch("-D", "skill/test-skill")
            result = publisher.publish(
                skill_dir=skill_dir, marketplace_name="local-test", create_branch=True
            )

        assert result["success"] is True
        assert result["branch"] == "skill/test-skill"

    def test_create_branch_republish_with_remote_branch_still_present(self, skill_dir, tmp_path):
        """Regression: republishing with create_branch=True while the remote
        skill/<name> branch still exists (force update before merge, or retry)
        rebuilds the branch from base, so the push legitimately diverges from
        the remote branch and must be forced — a plain push is rejected
        non-fast-forward."""
        import git as gitmodule

        bare_repo_path = _make_bare_remote(tmp_path)
        manager = _make_manager(tmp_path, f"file://{bare_repo_path}")
        publisher, _cache_dir = self._make_publisher(tmp_path)

        with (
            patch.dict(os.environ, {"DUMMY_TOKEN": "x"}),
            patch(
                "skill_seekers.services.marketplace_publisher.MarketplaceManager",
                return_value=manager,
            ),
        ):
            publisher.publish(
                skill_dir=skill_dir, marketplace_name="local-test", create_branch=True
            )
            # Change the skill so the second commit's tree (and SHA) differs —
            # identical same-second commits would push as a no-op
            # "up-to-date" and hide the non-fast-forward path.
            (skill_dir / "SKILL.md").write_text(
                "---\nname: test-skill\ndescription: A test skill, v2.\n---\n\n# Test Skill v2\n"
            )
            result = publisher.publish(
                skill_dir=skill_dir, marketplace_name="local-test", create_branch=True, force=True
            )

        assert result["success"] is True
        assert result["branch"] == "skill/test-skill"
        # The remote branch must point at the SECOND publish's commit.
        remote = gitmodule.Repo(bare_repo_path)
        blob = remote.commit("skill/test-skill").tree[
            "plugins/test-skill/skills/test-skill/SKILL.md"
        ]
        assert "v2" in blob.data_stream.read().decode()
