#!/usr/bin/env python3
"""
OpenRouter Adaptor

OpenAI-compatible LLM platform adaptor for OpenRouter.
"""

from .openai_compatible import OpenAICompatibleAdaptor


class OpenRouterAdaptor(OpenAICompatibleAdaptor):
    """OpenRouter platform adaptor."""

    PLATFORM = "openrouter"
    PLATFORM_NAME = "OpenRouter"
    DEFAULT_API_ENDPOINT = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "openrouter/auto"
    ENV_VAR_NAME = "OPENROUTER_API_KEY"
    PLATFORM_URL = "https://openrouter.ai/"
