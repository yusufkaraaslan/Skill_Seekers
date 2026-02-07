#!/usr/bin/env python3
"""
Multi-LLM Adaptor Registry

Provides factory function to get platform-specific adaptors for skill generation.
Supports Claude AI, Google Gemini, OpenAI ChatGPT, and generic Markdown export.
"""

from .base import SkillAdaptor, SkillMetadata

# Import adaptors (some may not be implemented yet)
try:
    from .claude import ClaudeAdaptor
except ImportError:
    ClaudeAdaptor = None

try:
    from .gemini import GeminiAdaptor
except ImportError:
    GeminiAdaptor = None

try:
    from .openai import OpenAIAdaptor
except ImportError:
    OpenAIAdaptor = None

try:
    from .markdown import MarkdownAdaptor
except ImportError:
    MarkdownAdaptor = None

try:
    from .langchain import LangChainAdaptor
except ImportError:
    LangChainAdaptor = None

try:
    from .llama_index import LlamaIndexAdaptor
except ImportError:
    LlamaIndexAdaptor = None

try:
    from .weaviate import WeaviateAdaptor
except ImportError:
    WeaviateAdaptor = None

try:
    from .chroma import ChromaAdaptor
except ImportError:
    ChromaAdaptor = None

try:
    from .faiss_helpers import FAISSHelpers
except ImportError:
    FAISSHelpers = None

try:
    from .qdrant import QdrantAdaptor
except ImportError:
    QdrantAdaptor = None

try:
    from .haystack import HaystackAdaptor
except ImportError:
    HaystackAdaptor = None


# Registry of available adaptors
ADAPTORS: dict[str, type[SkillAdaptor]] = {}

# Register adaptors that are implemented
if ClaudeAdaptor:
    ADAPTORS["claude"] = ClaudeAdaptor
if GeminiAdaptor:
    ADAPTORS["gemini"] = GeminiAdaptor
if OpenAIAdaptor:
    ADAPTORS["openai"] = OpenAIAdaptor
if MarkdownAdaptor:
    ADAPTORS["markdown"] = MarkdownAdaptor
if LangChainAdaptor:
    ADAPTORS["langchain"] = LangChainAdaptor
if LlamaIndexAdaptor:
    ADAPTORS["llama-index"] = LlamaIndexAdaptor
if WeaviateAdaptor:
    ADAPTORS["weaviate"] = WeaviateAdaptor
if ChromaAdaptor:
    ADAPTORS["chroma"] = ChromaAdaptor
if FAISSHelpers:
    ADAPTORS["faiss"] = FAISSHelpers
if QdrantAdaptor:
    ADAPTORS["qdrant"] = QdrantAdaptor
if HaystackAdaptor:
    ADAPTORS["haystack"] = HaystackAdaptor


def get_adaptor(platform: str, config: dict = None) -> SkillAdaptor:
    """
    Factory function to get platform-specific adaptor instance.

    Args:
        platform: Platform identifier ('claude', 'gemini', 'openai', 'markdown')
        config: Optional platform-specific configuration

    Returns:
        SkillAdaptor instance for the specified platform

    Raises:
        ValueError: If platform is not supported or not yet implemented

    Examples:
        >>> adaptor = get_adaptor('claude')
        >>> adaptor = get_adaptor('gemini', {'api_version': 'v1beta'})
    """
    if platform not in ADAPTORS:
        available = ", ".join(ADAPTORS.keys())
        if not ADAPTORS:
            raise ValueError(
                f"No adaptors are currently implemented. Platform '{platform}' is not available."
            )
        raise ValueError(
            f"Platform '{platform}' is not supported or not yet implemented. Available platforms: {available}"
        )

    adaptor_class = ADAPTORS[platform]
    return adaptor_class(config)


def list_platforms() -> list[str]:
    """
    List all supported platforms.

    Returns:
        List of platform identifiers

    Examples:
        >>> list_platforms()
        ['claude', 'gemini', 'openai', 'markdown']
    """
    return list(ADAPTORS.keys())


def is_platform_available(platform: str) -> bool:
    """
    Check if a platform adaptor is available.

    Args:
        platform: Platform identifier to check

    Returns:
        True if platform is available

    Examples:
        >>> is_platform_available('claude')
        True
        >>> is_platform_available('unknown')
        False
    """
    return platform in ADAPTORS


# Export public interface
__all__ = [
    "SkillAdaptor",
    "SkillMetadata",
    "get_adaptor",
    "list_platforms",
    "is_platform_available",
    "ADAPTORS",
]
