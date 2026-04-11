#!/usr/bin/env python3
"""Tests for MarketplaceManager class (marketplace registry management)"""

import json
from pathlib import Path

import pytest

from skill_seekers.mcp.marketplace_manager import MarketplaceManager


@pytest.fixture
def temp_config_dir(tmp_path):
    config_dir = tmp_path / "test_config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def manager(temp_config_dir):
    return MarketplaceManager(config_dir=str(temp_config_dir))


class TestMarketplaceManagerInit:
    def test_init_creates_config_dir(self, tmp_path):
        config_dir = tmp_path / "new_config"
        mgr = MarketplaceManager(config_dir=str(config_dir))
        assert config_dir.exists()
        assert mgr.config_dir == config_dir

    def test_init_creates_registry_file(self, temp_config_dir):
        _mgr = MarketplaceManager(config_dir=str(temp_config_dir))
        registry_file = temp_config_dir / "marketplaces.json"
        assert registry_file.exists()
        with open(registry_file) as f:
            data = json.load(f)
            assert data == {"version": "1.0", "marketplaces": []}

    def test_init_preserves_existing_registry(self, temp_config_dir):
        registry_file = temp_config_dir / "marketplaces.json"
        existing_data = {
            "version": "1.0",
            "marketplaces": [{"name": "test", "git_url": "https://example.com/repo.git"}],
        }
        with open(registry_file, "w") as f:
            json.dump(existing_data, f)
        _mgr = MarketplaceManager(config_dir=str(temp_config_dir))
        with open(registry_file) as f:
            data = json.load(f)
            assert len(data["marketplaces"]) == 1

    def test_init_with_default_config_dir(self):
        mgr = MarketplaceManager()
        assert mgr.config_dir == Path.home() / ".skill-seekers"


class TestAddMarketplace:
    def test_add_marketplace_minimal(self, manager):
        mp = manager.add_marketplace(
            name="spyke", git_url="https://github.com/spykegames/plugins.git"
        )
        assert mp["name"] == "spyke"
        assert mp["git_url"] == "https://github.com/spykegames/plugins.git"
        assert mp["token_env"] == "GITHUB_TOKEN"
        assert mp["branch"] == "main"
        assert mp["enabled"] is True
        assert mp["author"] == {"name": "", "email": ""}

    def test_add_marketplace_full_parameters(self, manager):
        author = {"name": "Spyke Team", "email": "team@spyke.com"}
        mp = manager.add_marketplace(
            name="spyke",
            git_url="https://github.com/spykegames/plugins.git",
            token_env="SPYKE_TOKEN",
            branch="develop",
            author=author,
            enabled=False,
        )
        assert mp["token_env"] == "SPYKE_TOKEN"
        assert mp["branch"] == "develop"
        assert mp["author"] == author
        assert mp["enabled"] is False

    def test_add_marketplace_normalizes_name(self, manager):
        mp = manager.add_marketplace(name="MyMarket", git_url="https://github.com/org/repo.git")
        assert mp["name"] == "mymarket"

    def test_add_marketplace_invalid_name_empty(self, manager):
        with pytest.raises(ValueError, match="Invalid marketplace name"):
            manager.add_marketplace(name="", git_url="https://github.com/org/repo.git")

    def test_add_marketplace_invalid_name_special_chars(self, manager):
        with pytest.raises(ValueError, match="Invalid marketplace name"):
            manager.add_marketplace(name="my@market", git_url="https://github.com/org/repo.git")

    def test_add_marketplace_valid_name_with_hyphens(self, manager):
        mp = manager.add_marketplace(name="my-market", git_url="https://github.com/org/repo.git")
        assert mp["name"] == "my-market"

    def test_add_marketplace_empty_git_url(self, manager):
        with pytest.raises(ValueError, match="git_url cannot be empty"):
            manager.add_marketplace(name="spyke", git_url="")

    def test_add_marketplace_strips_git_url(self, manager):
        mp = manager.add_marketplace(name="spyke", git_url="  https://github.com/org/repo.git  ")
        assert mp["git_url"] == "https://github.com/org/repo.git"

    def test_add_marketplace_updates_existing(self, manager):
        mp1 = manager.add_marketplace(name="spyke", git_url="https://github.com/org/repo1.git")
        mp2 = manager.add_marketplace(name="spyke", git_url="https://github.com/org/repo2.git")
        assert mp2["git_url"] == "https://github.com/org/repo2.git"
        assert mp2["added_at"] == mp1["added_at"]
        assert len(manager.list_marketplaces()) == 1

    def test_add_marketplace_persists_to_file(self, manager, temp_config_dir):
        manager.add_marketplace(name="spyke", git_url="https://github.com/org/repo.git")
        registry_file = temp_config_dir / "marketplaces.json"
        with open(registry_file) as f:
            data = json.load(f)
        assert len(data["marketplaces"]) == 1
        assert data["marketplaces"][0]["name"] == "spyke"


class TestGetMarketplace:
    def test_get_marketplace_exact_match(self, manager):
        manager.add_marketplace(name="spyke", git_url="https://github.com/org/repo.git")
        mp = manager.get_marketplace("spyke")
        assert mp["name"] == "spyke"

    def test_get_marketplace_case_insensitive(self, manager):
        manager.add_marketplace(name="Spyke", git_url="https://github.com/org/repo.git")
        mp = manager.get_marketplace("spyke")
        assert mp["name"] == "spyke"

    def test_get_marketplace_not_found(self, manager):
        with pytest.raises(KeyError, match="Marketplace 'nonexistent' not found"):
            manager.get_marketplace("nonexistent")

    def test_get_marketplace_not_found_shows_available(self, manager):
        manager.add_marketplace(name="mp1", git_url="https://example.com/1.git")
        manager.add_marketplace(name="mp2", git_url="https://example.com/2.git")
        with pytest.raises(KeyError, match="Available marketplaces: mp1, mp2"):
            manager.get_marketplace("mp3")

    def test_get_marketplace_empty_registry(self, manager):
        with pytest.raises(KeyError, match="Available marketplaces: none"):
            manager.get_marketplace("spyke")


class TestListMarketplaces:
    def test_list_marketplaces_empty(self, manager):
        assert manager.list_marketplaces() == []

    def test_list_marketplaces_multiple(self, manager):
        manager.add_marketplace(name="mp1", git_url="https://example.com/1.git")
        manager.add_marketplace(name="mp2", git_url="https://example.com/2.git")
        assert len(manager.list_marketplaces()) == 2

    def test_list_marketplaces_enabled_only(self, manager):
        manager.add_marketplace(name="enabled", git_url="https://example.com/1.git", enabled=True)
        manager.add_marketplace(name="disabled", git_url="https://example.com/2.git", enabled=False)
        marketplaces = manager.list_marketplaces(enabled_only=True)
        assert len(marketplaces) == 1
        assert marketplaces[0]["name"] == "enabled"


class TestRemoveMarketplace:
    def test_remove_marketplace_exists(self, manager):
        manager.add_marketplace(name="spyke", git_url="https://github.com/org/repo.git")
        assert manager.remove_marketplace("spyke") is True
        assert len(manager.list_marketplaces()) == 0

    def test_remove_marketplace_not_found(self, manager):
        assert manager.remove_marketplace("nonexistent") is False

    def test_remove_marketplace_persists_to_file(self, manager, temp_config_dir):
        manager.add_marketplace(name="mp1", git_url="https://example.com/1.git")
        manager.add_marketplace(name="mp2", git_url="https://example.com/2.git")
        manager.remove_marketplace("mp1")
        registry_file = temp_config_dir / "marketplaces.json"
        with open(registry_file) as f:
            data = json.load(f)
        assert len(data["marketplaces"]) == 1
        assert data["marketplaces"][0]["name"] == "mp2"


class TestUpdateMarketplace:
    def test_update_marketplace_git_url(self, manager):
        manager.add_marketplace(name="spyke", git_url="https://github.com/org/repo1.git")
        updated = manager.update_marketplace(
            name="spyke", git_url="https://github.com/org/repo2.git"
        )
        assert updated["git_url"] == "https://github.com/org/repo2.git"

    def test_update_marketplace_author(self, manager):
        manager.add_marketplace(name="spyke", git_url="https://github.com/org/repo.git")
        new_author = {"name": "New Author", "email": "new@example.com"}
        updated = manager.update_marketplace(name="spyke", author=new_author)
        assert updated["author"] == new_author

    def test_update_marketplace_updates_timestamp(self, manager):
        mp = manager.add_marketplace(name="spyke", git_url="https://github.com/org/repo.git")
        updated = manager.update_marketplace(name="spyke", branch="develop")
        assert updated["updated_at"] > mp["updated_at"]

    def test_update_marketplace_not_found(self, manager):
        with pytest.raises(KeyError, match="Marketplace 'nonexistent' not found"):
            manager.update_marketplace(name="nonexistent", branch="main")


class TestDefaultTokenEnv:
    def test_github_url(self, manager):
        mp = manager.add_marketplace(name="test", git_url="https://github.com/org/repo.git")
        assert mp["token_env"] == "GITHUB_TOKEN"

    def test_gitlab_url(self, manager):
        mp = manager.add_marketplace(name="test", git_url="https://gitlab.com/org/repo.git")
        assert mp["token_env"] == "GITLAB_TOKEN"

    def test_bitbucket_url(self, manager):
        mp = manager.add_marketplace(name="test", git_url="https://bitbucket.org/org/repo.git")
        assert mp["token_env"] == "BITBUCKET_TOKEN"

    def test_unknown_url(self, manager):
        mp = manager.add_marketplace(
            name="test", git_url="https://custom-git.example.com/org/repo.git"
        )
        assert mp["token_env"] == "GIT_TOKEN"

    def test_override_token_env(self, manager):
        mp = manager.add_marketplace(
            name="test",
            git_url="https://github.com/org/repo.git",
            token_env="MY_CUSTOM_TOKEN",
        )
        assert mp["token_env"] == "MY_CUSTOM_TOKEN"


class TestRegistryPersistence:
    def test_registry_atomic_write(self, manager, temp_config_dir):
        manager.add_marketplace(name="spyke", git_url="https://github.com/org/repo.git")
        assert len(list(temp_config_dir.glob("*.tmp"))) == 0

    def test_registry_corrupted_file(self, temp_config_dir):
        mgr = MarketplaceManager(config_dir=str(temp_config_dir))
        (temp_config_dir / "marketplaces.json").write_text("{ invalid json }")
        with pytest.raises(ValueError, match="Corrupted registry file"):
            mgr._read_registry()
