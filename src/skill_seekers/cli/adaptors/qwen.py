#!/usr/bin/env python3
"""
Qwen (Alibaba) Adaptor

OpenAI-compatible LLM platform adaptor for Qwen/DashScope.
"""

from .openai_compatible import OpenAICompatibleAdaptor


class QwenAdaptor(OpenAICompatibleAdaptor):
    """Qwen (Alibaba Cloud) platform adaptor."""

    PLATFORM = "qwen"
    PLATFORM_NAME = "Qwen (Alibaba)"
    DEFAULT_API_ENDPOINT = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    DEFAULT_MODEL = "qwen-max"
    ENV_VAR_NAME = "DASHSCOPE_API_KEY"
    PLATFORM_URL = "https://dashscope.console.aliyun.com/"
