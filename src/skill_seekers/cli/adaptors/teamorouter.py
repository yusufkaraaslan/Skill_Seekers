#!/usr/bin/env python3
"""
TeamoRouter Adaptor

OpenAI-compatible LLM platform adaptor for TeamoRouter.
"""

from .openai_compatible import OpenAICompatibleAdaptor


class TeamoRouterAdaptor(OpenAICompatibleAdaptor):
    """TeamoRouter platform adaptor."""

    PLATFORM = "teamorouter"
    PLATFORM_NAME = "TeamoRouter"
    DEFAULT_API_ENDPOINT = "https://api.teamorouter.com/v1"
    DEFAULT_MODEL = "deepseek-v4-flash"
    ENV_VAR_NAME = "TEAMOROUTER_API_KEY"
    PLATFORM_URL = "https://teamorouter.com/"
