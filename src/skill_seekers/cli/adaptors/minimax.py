#!/usr/bin/env python3
"""
MiniMax AI Adaptor

OpenAI-compatible LLM platform adaptor for MiniMax AI.
Uses MiniMax's OpenAI-compatible API for AI enhancement with the M3 model
(M2.7 is still selectable via ``--model``).
"""

from .openai_compatible import OpenAICompatibleAdaptor
from skill_seekers.cli.minimax_config import (
    MINIMAX_DEFAULT_MODEL,
    MINIMAX_ENDPOINTS,
    resolve_minimax_endpoint,
)


class MiniMaxAdaptor(OpenAICompatibleAdaptor):
    """MiniMax AI platform adaptor."""

    PLATFORM = "minimax"
    PLATFORM_NAME = "MiniMax AI"
    # Static fallback (global). Actual requests resolve region from
    # MINIMAX_API_REGION via _api_base_url() so China-issued keys reach
    # api.minimaxi.com instead of 401-ing against the global endpoint.
    DEFAULT_API_ENDPOINT = MINIMAX_ENDPOINTS["global_en"]["openai"]
    DEFAULT_MODEL = MINIMAX_DEFAULT_MODEL
    ENV_VAR_NAME = "MINIMAX_API_KEY"
    PLATFORM_URL = "https://platform.minimaxi.com/"

    def _api_base_url(self) -> str:
        """Resolve the OpenAI-compatible endpoint for the configured region."""
        return resolve_minimax_endpoint(protocol="openai")
