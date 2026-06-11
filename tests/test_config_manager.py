"""Tests for ConfigManager API-key handling.

The env-var fallback in get_api_key() is derived from the agent_client
provider registry (API_PROVIDERS) so key aliases and newly registered
providers stay in sync with AgentClient.detect_api_key().
"""

import pytest

from skill_seekers.cli.agent_client import API_PROVIDERS
from skill_seekers.cli.config_manager import ConfigManager

ALL_KEY_VARS = [var for p in API_PROVIDERS for var in p["env_vars"]]


@pytest.fixture
def manager(tmp_path, monkeypatch):
    monkeypatch.setattr(ConfigManager, "CONFIG_DIR", tmp_path / "cfg")
    monkeypatch.setattr(ConfigManager, "CONFIG_FILE", tmp_path / "cfg" / "config.json")
    monkeypatch.setattr(ConfigManager, "PROGRESS_DIR", tmp_path / "prog")
    for var in ALL_KEY_VARS:
        monkeypatch.delenv(var, raising=False)
    return ConfigManager()


class TestGetApiKey:
    @pytest.mark.parametrize(
        "provider,env_var",
        [(p["provider"], var) for p in API_PROVIDERS for var in p["env_vars"]],
    )
    def test_every_registry_env_var_honored(self, manager, monkeypatch, provider, env_var):
        """Each env var in API_PROVIDERS works, including aliases like
        ANTHROPIC_AUTH_TOKEN (parity with AgentClient.detect_api_key)."""
        monkeypatch.setenv(env_var, "env-key-123")
        assert manager.get_api_key(provider) == "env-key-123"

    def test_env_var_beats_config_file(self, manager, monkeypatch):
        manager.set_api_key("openai", "config-key")
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        assert manager.get_api_key("openai") == "env-key"

    def test_config_file_when_no_env(self, manager):
        manager.set_api_key("google", "config-key")
        assert manager.get_api_key("google") == "config-key"

    def test_missing_key_returns_none(self, manager):
        assert manager.get_api_key("anthropic") is None

    def test_unknown_provider_returns_none(self, manager):
        assert manager.get_api_key("not-a-provider") is None
