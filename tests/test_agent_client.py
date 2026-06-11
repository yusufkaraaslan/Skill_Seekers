#!/usr/bin/env python3
"""Tests for the AgentClient unified AI client.

NOTE: Uses @patch.dict(os.environ, ..., clear=True) which clears all env vars
during individual tests. This is safe for sequential execution but means this
file should run in a dedicated worker (--dist=loadfile) under pytest-xdist.
"""

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


class TestCallApiTruncation:
    """Regression for ENH-01: a max_tokens-truncated API response must NOT be
    returned — callers overwrite SKILL.md / parse JSON with this text, so a
    truncated body silently corrupts their output."""

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(AgentClient, "_init_api_client", return_value=MagicMock())
    def test_anthropic_truncated_returns_none(self, _mock_init):
        client = AgentClient(mode="api", api_key="sk-ant-x")
        client.provider = "anthropic"
        msg = MagicMock()
        msg.stop_reason = "max_tokens"
        msg.content = [MagicMock(text="half a SKILL.md that was cut off")]
        client.client.messages.create.return_value = msg
        assert client._call_api("prompt", max_tokens=10) is None

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(AgentClient, "_init_api_client", return_value=MagicMock())
    def test_anthropic_complete_returns_text(self, _mock_init):
        client = AgentClient(mode="api", api_key="sk-ant-x")
        client.provider = "anthropic"
        msg = MagicMock()
        msg.stop_reason = "end_turn"
        msg.content = [MagicMock(text="full content")]
        client.client.messages.create.return_value = msg
        assert client._call_api("prompt", max_tokens=4096) == "full content"

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(AgentClient, "_init_api_client", return_value=MagicMock())
    def test_openai_length_finish_returns_none(self, _mock_init):
        client = AgentClient(mode="api", api_key="sk-openai-x")
        client.provider = "openai"
        choice = MagicMock()
        choice.finish_reason = "length"
        choice.message.content = "truncated"
        resp = MagicMock()
        resp.choices = [choice]
        client.client.chat.completions.create.return_value = resp
        assert client._call_api("prompt", max_tokens=10) is None

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(AgentClient, "_init_api_client", return_value=MagicMock())
    def test_openai_forwards_caller_timeout(self, _mock_init):
        """Regression for ENH-06: the OpenAI branch must forward the caller's
        timeout. It alone still hardcoded timeout=120s, so large enhancement
        prompts died at 2 minutes."""
        client = AgentClient(mode="api", api_key="sk-openai-x")
        client.provider = "openai"
        choice = MagicMock()
        choice.finish_reason = "stop"
        choice.message.content = "ok"
        resp = MagicMock()
        resp.choices = [choice]
        client.client.chat.completions.create.return_value = resp

        client._call_api("prompt", max_tokens=4096, timeout=999)

        _, kwargs = client.client.chat.completions.create.call_args
        assert kwargs["timeout"] == 999


class TestCallTruncationRetry:
    """A truncated API response triggers exactly ONE retry with double the
    budget; persistent truncation still returns None (the gate is kept), and
    non-truncation failures don't retry."""

    def _client(self):
        with patch.object(AgentClient, "_init_api_client", return_value=MagicMock()):
            client = AgentClient(mode="api", api_key="sk-ant-x")
        client.provider = "anthropic"
        return client

    @staticmethod
    def _response(stop_reason, text):
        msg = MagicMock()
        msg.stop_reason = stop_reason
        msg.content = [MagicMock(text=text)]
        return msg

    @patch.dict(os.environ, {}, clear=True)
    def test_truncation_retries_once_with_doubled_budget(self):
        client = self._client()
        client.client.messages.create.side_effect = [
            self._response("max_tokens", "half a SKILL.md"),
            self._response("end_turn", "full content"),
        ]
        assert client.call("prompt", max_tokens=4096) == "full content"
        calls = client.client.messages.create.call_args_list
        assert len(calls) == 2
        assert calls[0].kwargs["max_tokens"] == 4096
        assert calls[1].kwargs["max_tokens"] == 8192

    @patch.dict(os.environ, {}, clear=True)
    def test_persistent_truncation_returns_none_after_single_retry(self):
        client = self._client()
        client.client.messages.create.return_value = self._response("max_tokens", "half")
        assert client.call("prompt", max_tokens=4096) is None
        assert client.client.messages.create.call_count == 2

    @patch.dict(os.environ, {}, clear=True)
    def test_non_truncation_failure_does_not_retry(self):
        client = self._client()
        client.client.messages.create.side_effect = RuntimeError("boom")
        assert client.call("prompt", max_tokens=4096) is None
        assert client.client.messages.create.call_count == 1


class TestSkillMdEnhancementBudget:
    """The SKILL.md rewrite call sites must request a 16K-token budget —
    with 4096, any skill whose rewrite exceeds ~16 KB hit the truncation
    gate (None) on every attempt and was permanently un-enhanceable."""

    def test_enhance_skill_requests_16384(self, monkeypatch, tmp_path):
        from skill_seekers.cli import enhance_skill

        mock_client = MagicMock()
        mock_client.client = MagicMock()
        mock_client.call.return_value = "enhanced"
        monkeypatch.setattr(enhance_skill, "AgentClient", MagicMock(return_value=mock_client))

        enhancer = enhance_skill.SkillEnhancer(tmp_path, api_key="sk-ant-x")
        references = {
            "api.md": {
                "source": "web",
                "path": str(tmp_path / "references" / "api.md"),
                "confidence": "high",
                "size": 9,
                "content": "# API doc",
            }
        }
        assert enhancer.enhance_skill_md(references, None) == "enhanced"
        assert mock_client.call.call_args.kwargs["max_tokens"] == 16384

    def test_adaptor_enhance_requests_16384(self, monkeypatch, tmp_path):
        from skill_seekers.cli import agent_client as agent_client_module
        from skill_seekers.cli.adaptors.base import SkillAdaptor

        class _Adaptor(SkillAdaptor):
            PLATFORM = "test"
            PLATFORM_NAME = "Test"

            def format_skill_md(self, skill_dir, metadata):
                return ""

            def package(self, skill_dir, output_path, **kwargs):
                return output_path

            def upload(self, package_path, api_key, **kwargs):
                return {}

            def _build_enhancement_prompt(self, name, references, current):
                return "prompt"

        (tmp_path / "references").mkdir()
        (tmp_path / "references" / "doc.md").write_text("# Doc")

        mock_client = MagicMock()
        mock_client.mode = "api"
        mock_client.client = MagicMock()
        mock_client.call.return_value = "enhanced"
        monkeypatch.setattr(agent_client_module, "AgentClient", MagicMock(return_value=mock_client))

        ok = _Adaptor()._enhance_skill_md_via_client(tmp_path, "sk-ant-x", provider="anthropic")
        assert ok is True
        assert mock_client.call.call_args.kwargs["max_tokens"] == 16384


class TestProviderOverride:
    """Regression for ENH-02: a Moonshot/Kimi sk- key must not be misrouted to
    OpenAI when an explicit provider override is set."""

    @patch.dict(os.environ, {"SKILL_SEEKER_PROVIDER": "moonshot"}, clear=True)
    def test_forced_moonshot_for_sk_key(self):
        assert AgentClient._detect_provider_from_key("sk-somekey") == "moonshot"

    @patch.dict(os.environ, {"SKILL_SEEKER_PROVIDER": "kimi"}, clear=True)
    def test_kimi_alias_maps_to_moonshot(self):
        assert AgentClient._detect_provider_from_key("sk-somekey") == "moonshot"

    @patch.dict(os.environ, {"SKILL_SEEKER_PROVIDER": "gemini"}, clear=True)
    def test_target_alias_maps_to_provider(self):
        """Target names from API_PROVIDERS are accepted as override aliases."""
        assert AgentClient._detect_provider_from_key("some-key") == "google"

    @patch.dict(os.environ, {}, clear=True)
    def test_sk_key_without_override_still_openai(self):
        assert AgentClient._detect_provider_from_key("sk-somekey") == "openai"


class TestKimiOutputParsing:
    """Regression for ENH-04: multi-line / apostrophe-containing Kimi output."""

    def test_multiline_text_part_preserved(self):
        raw = "TurnBegin(x)\nTextPart(type='text', text='line1\nline2\nline3')\nTurnEnd(x)"
        assert AgentClient._parse_kimi_output(raw) == "line1\nline2\nline3"

    def test_apostrophe_in_text_not_truncated(self):
        raw = "TextPart(type='text', text='don't stop')\nTurnEnd()"
        assert AgentClient._parse_kimi_output(raw) == "don't stop"


class TestCallLocalStrayJson:
    """Regression for ENH-05: a stray .json in the agent cwd must NOT shadow the
    real stdout response when no output_file was requested."""

    @patch.dict(os.environ, {}, clear=True)
    def test_stray_json_does_not_shadow_stdout(self):
        from pathlib import Path

        client = AgentClient(mode="local", agent="claude")

        def fake_run(_cmd, **kwargs):
            # Simulate the agent writing an incidental json into its cwd.
            Path(kwargs["cwd"], "scratch.json").write_text('{"junk": true}')
            result = MagicMock()
            result.returncode = 0
            result.stdout = "REAL STDOUT RESPONSE"
            result.stderr = ""
            return result

        with patch("subprocess.run", side_effect=fake_run):
            out = client.call("hello")  # local mode, output_file=None
        assert out == "REAL STDOUT RESPONSE"


class TestCallLocalPromptDelivery:
    """Regression: agents whose command template never consumes {prompt_file}
    (bare ["opencode"], custom commands without the placeholder) must receive
    the prompt on stdin — previously subprocess.run got input=None and the
    prompt sat in an unreferenced temp file."""

    @staticmethod
    def _fake_run(captured):
        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["input"] = kwargs.get("input")
            result = MagicMock()
            result.returncode = 0
            result.stdout = "ok"
            result.stderr = ""
            return result

        return fake_run

    @patch.dict(os.environ, {}, clear=True)
    def test_opencode_receives_prompt_on_stdin(self):
        client = AgentClient(mode="local", agent="opencode")
        captured = {}
        with patch("subprocess.run", side_effect=self._fake_run(captured)):
            assert client.call("the prompt") == "ok"
        assert captured["cmd"][0] == "opencode"
        assert captured["input"] == "the prompt"

    @patch.dict(os.environ, {"SKILL_SEEKER_AGENT_CMD": "mytool run"}, clear=True)
    def test_custom_without_prompt_file_pipes_stdin(self):
        client = AgentClient(mode="local", agent="custom")
        captured = {}
        with patch("subprocess.run", side_effect=self._fake_run(captured)):
            assert client.call("the prompt") == "ok"
        assert captured["cmd"] == ["mytool", "run"]
        assert captured["input"] == "the prompt"

    @patch.dict(
        os.environ,
        {"SKILL_SEEKER_AGENT_CMD": 'mytool --system "be brief" {prompt_file}'},
        clear=True,
    )
    def test_custom_command_is_shlex_split_and_substituted(self):
        """Custom templates go through build_local_agent_command: shlex split
        (no literal quote chars) and {prompt_file} substitution — the same
        path LocalSkillEnhancer already used for the identical env value."""
        client = AgentClient(mode="local", agent="custom")
        captured = {}
        with patch("subprocess.run", side_effect=self._fake_run(captured)):
            assert client.call("the prompt") == "ok"
        assert captured["cmd"][:3] == ["mytool", "--system", "be brief"]
        # {prompt_file} consumed → the prompt travels via the file, not stdin
        assert captured["cmd"][3].endswith("prompt.md")
        assert captured["input"] is None

    @patch.dict(os.environ, {}, clear=True)
    def test_prompt_file_agent_does_not_pipe_stdin(self):
        client = AgentClient(mode="local", agent="claude")
        captured = {}
        with patch("subprocess.run", side_effect=self._fake_run(captured)):
            assert client.call("the prompt") == "ok"
        assert captured["input"] is None


class TestParseKimiOutputUnknownRecords:
    """Unknown record types must not leak into the extracted text.

    The boundary lookahead is a generic CamelCase-constructor match: kimi's
    record list isn't exhaustive (e.g. ToolCallPart), and enumerating known
    types swallowed unknown records' internals into the captured text.
    """

    def test_toolcallpart_between_textparts(self):
        raw = (
            "TextPart(type='text', text='A')\n"
            "ToolCallPart(type='tool', name='x')\n"
            "TextPart(type='text', text='B')\n"
            "TurnEnd()"
        )
        assert AgentClient._parse_kimi_output(raw) == "A\nB"

    def test_unknown_record_at_end(self):
        raw = "TextPart(type='text', text='only')\nSomeNewRecord(foo=1)"
        assert AgentClient._parse_kimi_output(raw) == "only"


class TestParseKimiOutputInternalBoundaries:
    """Regression: the old single DOTALL regex truncated a TextPart at an
    internal "')" before a Capitalized line (print('done') then Config(...)),
    and garbled/swallowed trailing records when its lookahead failed at the
    true boundary (a non-record line after the closing "')")."""

    def test_internal_close_before_single_capital_identifier(self):
        raw = "TextPart(type='text', text='# Example\nprint('done')\nConfig(path)\nmore text')"
        assert (
            AgentClient._parse_kimi_output(raw)
            == "# Example\nprint('done')\nConfig(path)\nmore text"
        )

    def test_internal_close_with_record_at_end(self):
        raw = (
            "TextPart(type='text', text='# Example\nprint('done')\nConfig(path)\nmore text')\n"
            "TurnEnd()"
        )
        assert (
            AgentClient._parse_kimi_output(raw)
            == "# Example\nprint('done')\nConfig(path)\nmore text"
        )

    def test_non_record_line_before_next_record_yields_exact_text(self):
        raw = (
            "TextPart(type='text', text='Hello')\n"
            "Some deprecation note\n"
            "ThinkPart(type='think', think='...')"
        )
        assert AgentClient._parse_kimi_output(raw) == "Hello"

    def test_trailing_non_record_line_after_last_textpart(self):
        raw = "TextPart(type='text', text='Hello')\ndone."
        assert AgentClient._parse_kimi_output(raw) == "Hello"

    def test_unclosed_textpart_falls_back_to_raw(self):
        raw = "TextPart(type='text', text='never closed"
        assert AgentClient._parse_kimi_output(raw) == raw


class TestProviderRegistry:
    """API_PROVIDERS is the single source for provider detection priority."""

    def _clear_keys(self, monkeypatch):
        for var in (
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_AUTH_TOKEN",
            "GOOGLE_API_KEY",
            "OPENAI_API_KEY",
            "MOONSHOT_API_KEY",
        ):
            monkeypatch.delenv(var, raising=False)

    def test_moonshot_only_detected(self, monkeypatch):
        from skill_seekers.cli.agent_client import detect_api_target

        self._clear_keys(monkeypatch)
        monkeypatch.setenv("MOONSHOT_API_KEY", "sk-moon")
        assert detect_api_target() == ("kimi", "sk-moon")

    def test_anthropic_outranks_moonshot(self, monkeypatch):
        from skill_seekers.cli.agent_client import detect_api_target

        self._clear_keys(monkeypatch)
        monkeypatch.setenv("MOONSHOT_API_KEY", "sk-moon")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-x")
        assert detect_api_target() == ("claude", "sk-ant-x")

    def test_no_keys_returns_none(self, monkeypatch):
        from skill_seekers.cli.agent_client import detect_api_target, get_provider_api_keys

        self._clear_keys(monkeypatch)
        assert detect_api_target() is None
        assert all(v is None for v in get_provider_api_keys().values())

    def test_api_key_map_derived_from_registry(self):
        from skill_seekers.cli.agent_client import API_KEY_MAP, API_PROVIDERS

        for p in API_PROVIDERS:
            for var in p["env_vars"]:
                assert API_KEY_MAP[var] == p["provider"]


class TestAgentPresetsSingleSource:
    """agent_client.AGENT_PRESETS is the single source of truth; the copy in
    enhance_skill_local (whose kimi preset had silently diverged) is gone."""

    def test_enhance_skill_local_shares_the_same_dict(self):
        from skill_seekers.cli import agent_client, enhance_skill_local

        assert enhance_skill_local.AGENT_PRESETS is agent_client.AGENT_PRESETS

    def test_presets_have_required_shared_fields(self):
        from skill_seekers.cli.agent_client import AGENT_PRESETS

        for name, preset in AGENT_PRESETS.items():
            assert "display_name" in preset, name
            assert "command" in preset and preset["command"], name
            assert "supports_skip_permissions" in preset, name
        # The fields whose absence caused the original divergence:
        assert AGENT_PRESETS["kimi"]["parse_output"] == "kimi"
        assert "{cwd}" in AGENT_PRESETS["kimi"]["command"]


class TestAgentClientOverrides:
    """provider/base_url/model overrides + system/temperature passthrough —
    what the platform adaptors need to route their enhance() calls through
    AgentClient instead of hand-rolled SDK clients."""

    def _client(self, monkeypatch, **kwargs):
        # Avoid real SDK init: patch _init_api_client and inject a fake client.
        from unittest.mock import MagicMock

        from skill_seekers.cli.agent_client import AgentClient

        monkeypatch.setattr(AgentClient, "_init_api_client", lambda _self: MagicMock())
        return AgentClient(mode="api", api_key="sk-whatever", **kwargs)

    def test_provider_override_beats_key_prefix(self, monkeypatch):
        client = self._client(monkeypatch, provider="openai")
        assert client.provider == "openai"  # "sk-whatever" would detect as openai anyway
        client2 = self._client(monkeypatch, provider="anthropic")
        assert client2.provider == "anthropic"

    def test_model_override_used_in_api_call(self, monkeypatch):
        client = self._client(monkeypatch, provider="anthropic", model="my-model")
        msg = client.client.messages.create.return_value
        msg.stop_reason = "end_turn"
        msg.content = [type("B", (), {"text": "out"})()]
        assert client.call("hi") == "out"
        assert client.client.messages.create.call_args.kwargs["model"] == "my-model"

    def test_system_and_temperature_anthropic(self, monkeypatch):
        client = self._client(monkeypatch, provider="anthropic")
        msg = client.client.messages.create.return_value
        msg.stop_reason = "end_turn"
        msg.content = [type("B", (), {"text": "out"})()]
        client.call("hi", system="be terse", temperature=0.3)
        kwargs = client.client.messages.create.call_args.kwargs
        assert kwargs["system"] == "be terse"
        assert kwargs["temperature"] == 0.3

    def test_system_and_temperature_openai(self, monkeypatch):
        client = self._client(monkeypatch, provider="openai")
        resp = client.client.chat.completions.create.return_value
        resp.choices = [
            type(
                "C", (), {"finish_reason": "stop", "message": type("M", (), {"content": "out"})()}
            )()
        ]
        client.call("hi", system="be terse", temperature=0.3)
        kwargs = client.client.chat.completions.create.call_args.kwargs
        assert kwargs["messages"][0] == {"role": "system", "content": "be terse"}
        assert kwargs["messages"][1]["role"] == "user"
        assert kwargs["temperature"] == 0.3

    def test_base_url_reaches_openai_client(self, monkeypatch):
        import sys
        from unittest.mock import MagicMock

        from skill_seekers.cli.agent_client import AgentClient

        fake_openai = MagicMock()
        monkeypatch.setitem(sys.modules, "openai", fake_openai)
        AgentClient(
            mode="api",
            api_key="sk-x",
            provider="openai",
            base_url="https://api.example.com/v1",
        )
        assert fake_openai.OpenAI.call_args.kwargs["base_url"] == "https://api.example.com/v1"
