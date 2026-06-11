"""Tests for the shared adaptor enhance flow (Phase 3).

All four API-capable adaptors now delegate enhance() to
SkillAdaptor._enhance_skill_md_via_client, whose only AI transport is
AgentClient — these tests mock AgentClient and pin the contract:
read refs → per-adaptor prompt → client.call → validate → atomic save.
"""

from unittest.mock import MagicMock, patch

import pytest

from skill_seekers.cli.adaptors.claude import ClaudeAdaptor
from skill_seekers.cli.adaptors.gemini import GeminiAdaptor
from skill_seekers.cli.adaptors.openai import OpenAIAdaptor


@pytest.fixture
def skill_dir(tmp_path):
    d = tmp_path / "myskill"
    (d / "references").mkdir(parents=True)
    (d / "SKILL.md").write_text("# Original", encoding="utf-8")
    (d / "references" / "guide.md").write_text("# Guide\nSome docs", encoding="utf-8")
    return d


def _mock_client(response):
    client = MagicMock()
    client.mode = "api"
    client.client = object()
    client.call.return_value = response
    return client


class TestSharedEnhanceFlow:
    def test_success_saves_atomically_with_backup(self, skill_dir):
        adaptor = ClaudeAdaptor()
        with patch(
            "skill_seekers.cli.agent_client.AgentClient", return_value=_mock_client("# Enhanced")
        ) as cls:
            assert adaptor.enhance(skill_dir, "sk-ant-x") is True
        assert (skill_dir / "SKILL.md").read_text() == "# Enhanced"
        assert (skill_dir / "SKILL.md.backup").read_text() == "# Original"
        assert not (skill_dir / "SKILL.md.tmp").exists()
        # provider routed explicitly — no key-prefix guessing
        assert cls.call_args.kwargs["provider"] == "anthropic"

    def test_truncated_or_failed_call_leaves_skill_md_intact(self, skill_dir):
        adaptor = ClaudeAdaptor()
        # AgentClient returns None on truncation/rate-limit/auth errors
        with patch("skill_seekers.cli.agent_client.AgentClient", return_value=_mock_client(None)):
            assert adaptor.enhance(skill_dir, "sk-ant-x") is False
        assert (skill_dir / "SKILL.md").read_text() == "# Original"
        assert not (skill_dir / "SKILL.md.backup").exists()

    def test_empty_response_leaves_skill_md_intact(self, skill_dir):
        adaptor = OpenAIAdaptor()
        with patch("skill_seekers.cli.agent_client.AgentClient", return_value=_mock_client("   ")):
            assert adaptor.enhance(skill_dir, "sk-x") is False
        assert (skill_dir / "SKILL.md").read_text() == "# Original"

    def test_no_references_fails_before_any_api_call(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        adaptor = ClaudeAdaptor()
        with patch("skill_seekers.cli.agent_client.AgentClient") as cls:
            assert adaptor.enhance(empty, "sk-ant-x") is False
        cls.assert_not_called()

    def test_sdk_fallback_to_local_is_refused(self, skill_dir):
        """A missing SDK flips AgentClient to LOCAL mode — adaptor enhancement
        must fail rather than spawn a CLI agent."""
        client = _mock_client("ignored")
        client.mode = "local"
        client.client = None
        adaptor = GeminiAdaptor()
        with patch("skill_seekers.cli.agent_client.AgentClient", return_value=client):
            assert adaptor.enhance(skill_dir, "AIza-x") is False
        client.call.assert_not_called()
        assert (skill_dir / "SKILL.md").read_text() == "# Original"

    def test_per_adaptor_routing_parameters(self, skill_dir):
        cases = [
            (ClaudeAdaptor(), "sk-ant-x", {"provider": "anthropic"}),
            (OpenAIAdaptor(), "sk-x", {"provider": "openai", "model": "gpt-4o"}),
            (GeminiAdaptor(), "AIza", {"provider": "google", "model": "gemini-2.5-flash"}),
        ]
        for adaptor, key, expected in cases:
            with patch(
                "skill_seekers.cli.agent_client.AgentClient",
                return_value=_mock_client("# E"),
            ) as cls:
                assert adaptor.enhance(skill_dir, key) is True
            for k, v in expected.items():
                assert cls.call_args.kwargs[k] == v, (type(adaptor).__name__, k)

    def test_openai_compatible_uses_platform_endpoint(self, skill_dir):
        from skill_seekers.cli.adaptors.openai_compatible import OpenAICompatibleAdaptor

        class FakePlatform(OpenAICompatibleAdaptor):
            PLATFORM = "fake"
            PLATFORM_NAME = "FakeAI"
            DEFAULT_API_ENDPOINT = "https://api.fake.ai/v1"
            DEFAULT_MODEL = "fake-large"

            def supports_enhancement(self):
                return True

        adaptor = FakePlatform()
        with patch(
            "skill_seekers.cli.agent_client.AgentClient", return_value=_mock_client("# E")
        ) as cls:
            assert adaptor.enhance(skill_dir, "whatever-key-shape") is True
        kwargs = cls.call_args.kwargs
        assert kwargs["provider"] == "openai"
        assert kwargs["base_url"] == "https://api.fake.ai/v1"
        assert kwargs["model"] == "fake-large"
        # system prompt names the platform
        client = cls.return_value
        assert "FakeAI" in client.call.call_args.kwargs["system"]
