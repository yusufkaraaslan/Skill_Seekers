#!/usr/bin/env python3
"""
DeepSeek AI Adaptor

OpenAI-compatible LLM platform adaptor for DeepSeek.
"""

from .openai_compatible import OpenAICompatibleAdaptor


class DeepSeekAdaptor(OpenAICompatibleAdaptor):
    """DeepSeek AI platform adaptor."""

    PLATFORM = "deepseek"
    PLATFORM_NAME = "DeepSeek AI"
    DEFAULT_API_ENDPOINT = "https://api.deepseek.com/v1"
    DEFAULT_MODEL = "deepseek-chat"
    ENV_VAR_NAME = "DEEPSEEK_API_KEY"
    PLATFORM_URL = "https://platform.deepseek.com/"
