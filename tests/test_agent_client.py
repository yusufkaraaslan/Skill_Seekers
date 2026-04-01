#!/usr/bin/env python3
"""Tests for the AgentClient unified AI client."""

import os
import subprocess
from unittest.mock import MagicMock, patch


from skill_seekers.cli.agent_client import (
    DEFAULT_ENHANCE_TIMEOUT,
    DEFAULT_MODELS,
    UNLIMITED_TIMEOUT,
    AgentClient,
    get_default_timeout,
    normalize_agent_name,
)


class TestNormalizeAgentName:
    """Test normalize_agent_name() alias resolution."""

    def test_claude_aliases(self):
        assert normalize_agent_name("claude-code") == "claude"
        assert normalize_agent_name("claude_code") == "claude"
        assert normalize_agent_name("claude") == "claude"

    def test_kimi_aliases(self):
        assert normalize_agent_name("kimi") == "kimi"
        assert normalize_agent_name("kimi-cli") == "kimi"
        assert normalize_agent_name("kimi_code") == "kimi"
        assert normalize_agent_name("kimi-code") == "kimi"

    def test_codex_aliases(self):
        assert normalize_agent_name("codex") == "codex"
        assert normalize_agent_name("codex-cli") == "codex"

    def test_copilot_aliases(self):
        assert normalize_agent_name("copilot") == "copilot"
        assert normalize_agent_name("copilot-cli") == "copilot"

    def test_opencode_aliases(self):
        assert normalize_agent_name("opencode") == "opencode"
        assert normalize_agent_name("open-code") == "opencode"
        assert normalize_agent_name("open_code") == "opencode"

    def test_custom_passthrough(self):
        assert normalize_agent_name("custom") == "custom"

    def test_unknown_name_passthrough(self):
        assert normalize_agent_name("some-unknown-agent") == "some-unknown-agent"

    def test_empty_string_defaults_to_claude(self):
        assert normalize_agent_name("") == "claude"

    def test_none_defaults_to_claude(self):
        # The docstring says "if not agent_name" which covers None too,
        # but the type hint says str. If called with empty string, it returns "claude".
        assert normalize_agent_name("") == "claude"

    def test_case_insensitive(self):
        assert normalize_agent_name("Claude-Code") == "claude"
        assert normalize_agent_name("KIMI-CLI") == "kimi"
        assert normalize_agent_name("Codex") == "codex"

    def test_whitespace_stripped(self):
        assert normalize_agent_name("  claude  ") == "claude"
        assert normalize_agent_name("  kimi-cli  ") == "kimi"


class TestDetectApiKey:
    """Test AgentClient.detect_api_key() static method."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"}, clear=True)
    def test_detects_anthropic_key(self):
        key, provider = AgentClient.detect_api_key()
        assert key == "sk-ant-test123"
        assert provider == "anthropic"

    @patch.dict(os.environ, {"MOONSHOT_API_KEY": "moonshot-key-abc"}, clear=True)
    def test_detects_moonshot_key(self):
        key, provider = AgentClient.detect_api_key()
        assert key == "moonshot-key-abc"
        assert provider == "moonshot"

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "AIzaSyTest123"}, clear=True)
    def test_detects_google_key(self):
        key, provider = AgentClient.detect_api_key()
        assert key == "AIzaSyTest123"
        assert provider == "google"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-openai"}, clear=True)
    def test_detects_openai_key(self):
        key, provider = AgentClient.detect_api_key()
        assert key == "sk-test-openai"
        assert provider == "openai"

    @patch.dict(os.environ, {"ANTHROPIC_AUTH_TOKEN": "sk-ant-auth"}, clear=True)
    def test_detects_anthropic_auth_token(self):
        key, provider = AgentClient.detect_api_key()
        assert key == "sk-ant-auth"
        assert provider == "anthropic"

    @patch.dict(os.environ, {}, clear=True)
    def test_no_key_returns_none(self):
        key, provider = AgentClient.detect_api_key()
        assert key is None
        assert provider is None

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "  "}, clear=True)
    def test_whitespace_only_key_returns_none(self):
        key, provider = AgentClient.detect_api_key()
        assert key is None
        assert provider is None

    @patch.dict(
        os.environ,
        {"ANTHROPIC_API_KEY": "first-key", "OPENAI_API_KEY": "second-key"},
        clear=True,
    )
    def test_priority_order_anthropic_first(self):
        """API_KEY_MAP is iterated in order; ANTHROPIC_API_KEY comes first."""
        key, provider = AgentClient.detect_api_key()
        assert key == "first-key"
        assert provider == "anthropic"


class TestAgentClientInit:
    """Test AgentClient.__init__() mode auto-detection."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}, clear=True)
    @patch.object(AgentClient, "_init_api_client", return_value=MagicMock())
    def test_auto_mode_with_api_key_sets_api(self, mock_init):
        client = AgentClient(mode="auto")
        assert client.mode == "api"
        assert client.api_key == "sk-ant-test"

    @patch.dict(os.environ, {}, clear=True)
    def test_auto_mode_without_api_key_sets_local(self):
        client = AgentClient(mode="auto")
        assert client.mode == "local"
        assert client.api_key is None

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}, clear=True)
    def test_explicit_local_mode_overrides_api_key(self):
        client = AgentClient(mode="local")
        assert client.mode == "local"

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(AgentClient, "_init_api_client", return_value=MagicMock())
    def test_explicit_api_mode_with_provided_key(self, mock_init):
        client = AgentClient(mode="api", api_key="sk-ant-explicit")
        assert client.mode == "api"
        assert client.api_key == "sk-ant-explicit"

    @patch.dict(os.environ, {}, clear=True)
    def test_default_agent_is_claude(self):
        client = AgentClient(mode="local")
        assert client.agent == "claude"
        assert client.agent_display == "Claude Code"

    @patch.dict(os.environ, {"SKILL_SEEKER_AGENT": "kimi"}, clear=True)
    def test_env_agent_override(self):
        client = AgentClient(mode="local")
        assert client.agent == "kimi"

    @patch.dict(os.environ, {"SKILL_SEEKER_AGENT": "kimi"}, clear=True)
    def test_explicit_agent_overrides_env(self):
        client = AgentClient(mode="local", agent="codex")
        assert client.agent == "codex"

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(AgentClient, "_init_api_client", return_value=MagicMock())
    def test_explicit_api_key_detects_provider(self, mock_init):
        client = AgentClient(mode="api", api_key="sk-ant-mykey")
        assert client.provider == "anthropic"

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(AgentClient, "_init_api_client", return_value=MagicMock())
    def test_explicit_openai_key_detects_provider(self, mock_init):
        client = AgentClient(mode="api", api_key="sk-openai-key")
        assert client.provider == "openai"


class TestDetectProviderFromKey:
    """Test AgentClient._detect_provider_from_key() static method."""

    def test_anthropic_prefix(self):
        assert AgentClient._detect_provider_from_key("sk-ant-abc123") == "anthropic"

    def test_openai_prefix(self):
        assert AgentClient._detect_provider_from_key("sk-abc123") == "openai"

    def test_google_prefix(self):
        assert AgentClient._detect_provider_from_key("AIzaSyTest") == "google"

    @patch.dict(os.environ, {"MOONSHOT_API_KEY": "sk-moonshot-key"}, clear=True)
    def test_moonshot_via_env_match(self):
        result = AgentClient._detect_provider_from_key("sk-moonshot-key")
        assert result == "moonshot"

    @patch.dict(os.environ, {}, clear=True)
    def test_sk_prefix_without_moonshot_env_defaults_to_openai(self):
        result = AgentClient._detect_provider_from_key("sk-some-key")
        assert result == "openai"

    @patch.dict(os.environ, {}, clear=True)
    def test_unknown_prefix_defaults_to_anthropic(self):
        result = AgentClient._detect_provider_from_key("unknown-prefix-key")
        assert result == "anthropic"

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "custom-google-key"}, clear=True)
    def test_env_var_match_for_unknown_prefix(self):
        result = AgentClient._detect_provider_from_key("custom-google-key")
        assert result == "google"


class TestGetDefaultTimeout:
    """Test get_default_timeout() function."""

    @patch.dict(os.environ, {}, clear=True)
    def test_default_without_env(self):
        assert get_default_timeout() == DEFAULT_ENHANCE_TIMEOUT

    @patch.dict(os.environ, {"SKILL_SEEKER_ENHANCE_TIMEOUT": "unlimited"}, clear=True)
    def test_unlimited_string(self):
        assert get_default_timeout() == UNLIMITED_TIMEOUT

    @patch.dict(os.environ, {"SKILL_SEEKER_ENHANCE_TIMEOUT": "none"}, clear=True)
    def test_none_string(self):
        assert get_default_timeout() == UNLIMITED_TIMEOUT

    @patch.dict(os.environ, {"SKILL_SEEKER_ENHANCE_TIMEOUT": "0"}, clear=True)
    def test_zero_string(self):
        assert get_default_timeout() == UNLIMITED_TIMEOUT

    @patch.dict(os.environ, {"SKILL_SEEKER_ENHANCE_TIMEOUT": "600"}, clear=True)
    def test_valid_int_string(self):
        assert get_default_timeout() == 600

    @patch.dict(os.environ, {"SKILL_SEEKER_ENHANCE_TIMEOUT": "-5"}, clear=True)
    def test_negative_value_returns_unlimited(self):
        assert get_default_timeout() == UNLIMITED_TIMEOUT

    @patch.dict(os.environ, {"SKILL_SEEKER_ENHANCE_TIMEOUT": "not_a_number"}, clear=True)
    def test_invalid_string_returns_default(self):
        assert get_default_timeout() == DEFAULT_ENHANCE_TIMEOUT

    @patch.dict(os.environ, {"SKILL_SEEKER_ENHANCE_TIMEOUT": "  UNLIMITED  "}, clear=True)
    def test_unlimited_with_whitespace_and_case(self):
        assert get_default_timeout() == UNLIMITED_TIMEOUT

    @patch.dict(os.environ, {"SKILL_SEEKER_ENHANCE_TIMEOUT": ""}, clear=True)
    def test_empty_env_returns_default(self):
        assert get_default_timeout() == DEFAULT_ENHANCE_TIMEOUT


class TestGetModel:
    """Test AgentClient.get_model() static method."""

    @patch.dict(os.environ, {}, clear=True)
    def test_default_anthropic_model(self):
        model = AgentClient.get_model("anthropic")
        assert model == DEFAULT_MODELS["anthropic"]

    @patch.dict(os.environ, {}, clear=True)
    def test_default_openai_model(self):
        model = AgentClient.get_model("openai")
        assert model == DEFAULT_MODELS["openai"]

    @patch.dict(os.environ, {}, clear=True)
    def test_default_google_model(self):
        model = AgentClient.get_model("google")
        assert model == DEFAULT_MODELS["google"]

    @patch.dict(os.environ, {}, clear=True)
    def test_default_moonshot_model(self):
        model = AgentClient.get_model("moonshot")
        assert model == DEFAULT_MODELS["moonshot"]

    @patch.dict(os.environ, {"SKILL_SEEKER_MODEL": "my-custom-model"}, clear=True)
    def test_global_override(self):
        model = AgentClient.get_model("anthropic")
        assert model == "my-custom-model"

    @patch.dict(os.environ, {"ANTHROPIC_MODEL": "claude-opus-4-20250514"}, clear=True)
    def test_provider_specific_env_var(self):
        model = AgentClient.get_model("anthropic")
        assert model == "claude-opus-4-20250514"

    @patch.dict(
        os.environ,
        {"SKILL_SEEKER_MODEL": "global-model", "ANTHROPIC_MODEL": "provider-model"},
        clear=True,
    )
    def test_global_override_takes_precedence_over_provider(self):
        model = AgentClient.get_model("anthropic")
        assert model == "global-model"

    @patch.dict(os.environ, {}, clear=True)
    def test_unknown_provider_falls_back_to_anthropic_default(self):
        model = AgentClient.get_model("unknown-provider")
        assert model == "claude-sonnet-4-20250514"

    @patch.dict(os.environ, {"OPENAI_MODEL": "gpt-5"}, clear=True)
    def test_openai_model_env_var(self):
        model = AgentClient.get_model("openai")
        assert model == "gpt-5"

    @patch.dict(os.environ, {"GOOGLE_MODEL": "gemini-ultra"}, clear=True)
    def test_google_model_env_var(self):
        model = AgentClient.get_model("google")
        assert model == "gemini-ultra"


class TestParseKimiOutput:
    """Test AgentClient._parse_kimi_output() static method."""

    def test_valid_textpart_output(self):
        raw = (
            "TurnBegin(turn_id=1)\n"
            "StepBegin(step_id=1)\n"
            "TextPart(type='text', text='Hello world')\n"
            "ThinkPart(type='think', think='...')\n"
            "TextPart(type='text', text='Second line')\n"
        )
        result = AgentClient._parse_kimi_output(raw)
        assert result == "Hello world\nSecond line"

    def test_single_textpart(self):
        raw = "TextPart(type='text', text='Only one part')\n"
        result = AgentClient._parse_kimi_output(raw)
        assert result == "Only one part"

    def test_no_textpart_falls_back_to_raw(self):
        raw = "Some random output without TextPart markers"
        result = AgentClient._parse_kimi_output(raw)
        assert result == raw

    def test_empty_string_returns_empty(self):
        result = AgentClient._parse_kimi_output("")
        assert result == ""

    def test_thinkpart_only_falls_back(self):
        raw = "ThinkPart(type='think', think='internal thinking')"
        result = AgentClient._parse_kimi_output(raw)
        assert result == raw


class TestIsAvailable:
    """Test AgentClient.is_available() method."""

    @patch.dict(os.environ, {}, clear=True)
    def test_api_mode_with_client_is_available(self):
        client = AgentClient(mode="local")
        # Force to api mode with a client
        client.mode = "api"
        client.client = MagicMock()
        assert client.is_available() is True

    @patch.dict(os.environ, {}, clear=True)
    def test_api_mode_without_client_is_not_available(self):
        client = AgentClient(mode="local")
        client.mode = "api"
        client.client = None
        assert client.is_available() is False

    @patch.dict(os.environ, {}, clear=True)
    @patch("subprocess.run")
    def test_local_mode_claude_available(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        client = AgentClient(mode="local", agent="claude")
        assert client.is_available() is True
        mock_run.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_local_mode_cli_not_found(self, mock_run):
        client = AgentClient(mode="local", agent="claude")
        assert client.is_available() is False

    @patch.dict(os.environ, {}, clear=True)
    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=5))
    def test_local_mode_timeout(self, mock_run):
        client = AgentClient(mode="local", agent="claude")
        assert client.is_available() is False

    @patch.dict(os.environ, {}, clear=True)
    def test_local_mode_unknown_agent_not_available(self):
        client = AgentClient(mode="local")
        client.agent = "nonexistent-agent"
        assert client.is_available() is False

    @patch.dict(os.environ, {}, clear=True)
    @patch("subprocess.run")
    def test_local_mode_nonzero_returncode(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        client = AgentClient(mode="local", agent="codex")
        assert client.is_available() is False


class TestDetectDefaultTarget:
    """Test AgentClient.detect_default_target() static method."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}, clear=True)
    def test_anthropic_maps_to_claude(self):
        assert AgentClient.detect_default_target() == "claude"

    @patch.dict(os.environ, {"MOONSHOT_API_KEY": "moon-key"}, clear=True)
    def test_moonshot_maps_to_kimi(self):
        assert AgentClient.detect_default_target() == "kimi"

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "AIzaTest"}, clear=True)
    def test_google_maps_to_gemini(self):
        assert AgentClient.detect_default_target() == "gemini"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True)
    def test_openai_maps_to_openai(self):
        assert AgentClient.detect_default_target() == "openai"

    @patch.dict(os.environ, {}, clear=True)
    def test_no_key_defaults_to_markdown(self):
        assert AgentClient.detect_default_target() == "markdown"
