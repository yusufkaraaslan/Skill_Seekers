#!/usr/bin/env python3
"""
MiniMax AI Adaptor

OpenAI-compatible LLM platform adaptor for MiniMax AI.
Uses MiniMax's OpenAI-compatible API for AI enhancement with the M3 model
(M2.7 is still selectable via ``--model``).
"""

from .openai_compatible import OpenAICompatibleAdaptor


class MiniMaxAdaptor(OpenAICompatibleAdaptor):
    """MiniMax AI platform adaptor."""

    PLATFORM = "minimax"
    PLATFORM_NAME = "MiniMax AI"
    DEFAULT_API_ENDPOINT = "https://api.minimax.io/v1"
    DEFAULT_MODEL = "MiniMax-M3"
    ENV_VAR_NAME = "MINIMAX_API_KEY"
    PLATFORM_URL = "https://platform.minimaxi.com/"
