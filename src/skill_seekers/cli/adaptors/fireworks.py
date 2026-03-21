#!/usr/bin/env python3
"""
Fireworks AI Adaptor

OpenAI-compatible LLM platform adaptor for Fireworks AI.
"""

from .openai_compatible import OpenAICompatibleAdaptor


class FireworksAdaptor(OpenAICompatibleAdaptor):
    """Fireworks AI platform adaptor."""

    PLATFORM = "fireworks"
    PLATFORM_NAME = "Fireworks AI"
    DEFAULT_API_ENDPOINT = "https://api.fireworks.ai/inference/v1"
    DEFAULT_MODEL = "accounts/fireworks/models/llama-v3p1-70b-instruct"
    ENV_VAR_NAME = "FIREWORKS_API_KEY"
    PLATFORM_URL = "https://fireworks.ai/"
