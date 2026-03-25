#!/usr/bin/env python3
"""
Kimi (Moonshot AI) Adaptor

OpenAI-compatible LLM platform adaptor for Kimi/Moonshot AI.
"""

from .openai_compatible import OpenAICompatibleAdaptor


class KimiAdaptor(OpenAICompatibleAdaptor):
    """Kimi (Moonshot AI) platform adaptor."""

    PLATFORM = "kimi"
    PLATFORM_NAME = "Kimi (Moonshot AI)"
    DEFAULT_API_ENDPOINT = "https://api.moonshot.cn/v1"
    DEFAULT_MODEL = "moonshot-v1-128k"
    ENV_VAR_NAME = "MOONSHOT_API_KEY"
    PLATFORM_URL = "https://platform.moonshot.cn/"
