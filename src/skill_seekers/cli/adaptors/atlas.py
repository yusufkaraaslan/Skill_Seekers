#!/usr/bin/env python3
"""
Atlas Cloud Adaptor

OpenAI-compatible LLM platform adaptor for Atlas Cloud.
"""

from .openai_compatible import OpenAICompatibleAdaptor


class AtlasAdaptor(OpenAICompatibleAdaptor):
    """Atlas Cloud platform adaptor."""

    PLATFORM = "atlas"
    PLATFORM_NAME = "Atlas Cloud"
    DEFAULT_API_ENDPOINT = "https://api.atlascloud.ai/v1"
    DEFAULT_MODEL = "deepseek-ai/deepseek-v4-pro"
    ENV_VAR_NAME = "ATLAS_API_KEY"
    PLATFORM_URL = "https://www.atlascloud.ai/"
