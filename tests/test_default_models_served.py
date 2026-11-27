"""Built-in default models must be ones the providers still serve.

Anthropic retired claude-sonnet-4-20250514 on 2026-06-15
(https://platform.claude.com/docs/en/about-claude/model-deprecations); Google shut
down gemini-2.0-flash on 2026-06-01 and shuts down gemini-2.5-flash on 2026-12-01
(https://ai.google.dev/gemini-api/docs/deprecations).
"""

import os
from unittest.mock import patch

import pytest

from skill_seekers.cli.agent_client import DEFAULT_MODELS, AgentClient
from skill_seekers.cli.video_visual import _VISION_PROVIDERS

SHUT_DOWN = {
    "claude-sonnet-4-20250514",
    "claude-opus-4-20250514",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
}


@pytest.mark.parametrize("provider", sorted(DEFAULT_MODELS))
def test_api_default_model_is_served(provider):
    assert DEFAULT_MODELS[provider] not in SHUT_DOWN


@patch.dict(os.environ, {}, clear=True)
def test_unknown_provider_fallback_is_the_anthropic_default():
    assert AgentClient.get_model("unknown-provider") == DEFAULT_MODELS["anthropic"]


@pytest.mark.parametrize("provider", sorted(_VISION_PROVIDERS))
def test_vision_default_model_is_served(provider):
    assert _VISION_PROVIDERS[provider]["default_model"] not in SHUT_DOWN
