#!/usr/bin/env python3
"""
Together AI Adaptor

OpenAI-compatible LLM platform adaptor for Together AI.
"""

from .openai_compatible import OpenAICompatibleAdaptor


class TogetherAdaptor(OpenAICompatibleAdaptor):
    """Together AI platform adaptor."""

    PLATFORM = "together"
    PLATFORM_NAME = "Together AI"
    DEFAULT_API_ENDPOINT = "https://api.together.xyz/v1"
    DEFAULT_MODEL = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    ENV_VAR_NAME = "TOGETHER_API_KEY"
    PLATFORM_URL = "https://api.together.xyz/"
