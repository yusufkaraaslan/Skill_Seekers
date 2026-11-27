#!/usr/bin/env python3
"""
Straitly Adaptor

OpenAI-compatible LLM platform adaptor for Straitly.
"""

from .openai_compatible import OpenAICompatibleAdaptor


class StraitlyAdaptor(OpenAICompatibleAdaptor):
    """Straitly platform adaptor."""

    PLATFORM = "straitly"
    PLATFORM_NAME = "Straitly"
    DEFAULT_API_ENDPOINT = "https://api.straitly.ai/v1"
    DEFAULT_MODEL = "deepseek/deepseek-v4-1-flash-1017"
    ENV_VAR_NAME = "STRAITLY_API_KEY"
    PLATFORM_URL = "https://straitly.ai/"
