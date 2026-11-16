#!/usr/bin/env python3
"""
Requesty Adaptor

OpenAI-compatible LLM platform adaptor for Requesty.
"""

from .openai_compatible import OpenAICompatibleAdaptor


class RequestyAdaptor(OpenAICompatibleAdaptor):
    """Requesty platform adaptor."""

    PLATFORM = "requesty"
    PLATFORM_NAME = "Requesty"
    DEFAULT_API_ENDPOINT = "https://router.requesty.ai/v1"
    DEFAULT_MODEL = "openai/gpt-4o-mini"
    ENV_VAR_NAME = "REQUESTY_API_KEY"
    PLATFORM_URL = "https://app.requesty.ai/"
