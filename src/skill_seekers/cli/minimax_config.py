"""Shared MiniMax model and endpoint configuration."""

from __future__ import annotations

import os

# Ordinary text choices; explicit custom/legacy model IDs remain valid overrides.
MINIMAX_MODEL_IDS = ("MiniMax-M3.1-Flash", "MiniMax-M3")
MINIMAX_DEFAULT_MODEL = MINIMAX_MODEL_IDS[0]
# Keep the existing media workflows on M3 independently of the text default.
MINIMAX_IMAGE_MODEL = "MiniMax-M3"

# Video input (OpenAI-compatible ``video_url`` parts) is M3-only; base64 or URL
# videos are capped at 50 MB by the API. M3 accepts explicit ``adaptive`` or
# ``disabled`` thinking; Flash accepts only ``adaptive``.
MINIMAX_VIDEO_MODELS = ("MiniMax-M3",)
MINIMAX_VIDEO_MAX_BYTES = 50 * 1024 * 1024
MINIMAX_THINKING_MODES = ("adaptive", "disabled")

MINIMAX_DEFAULT_REGION = "global_en"
MINIMAX_DEFAULT_PROTOCOL = "openai"
MINIMAX_ENDPOINTS = {
    "global_en": {
        "openai": "https://api.minimax.io/v1",
        "anthropic": "https://api.minimax.io/anthropic",
    },
    "cn_zh": {
        "openai": "https://api.minimaxi.com/v1",
        "anthropic": "https://api.minimaxi.com/anthropic",
    },
}


def resolve_minimax_region(region: str | None = None) -> str:
    """Return a validated MiniMax API region."""
    resolved = (region or os.environ.get("MINIMAX_API_REGION") or MINIMAX_DEFAULT_REGION).strip()
    if resolved not in MINIMAX_ENDPOINTS:
        choices = ", ".join(MINIMAX_ENDPOINTS)
        raise ValueError(f"Unsupported MiniMax API region {resolved!r}; choose one of: {choices}")
    return resolved


def resolve_minimax_protocol(protocol: str | None = None) -> str:
    """Return a validated MiniMax API protocol."""
    resolved = (
        (protocol or os.environ.get("MINIMAX_API_PROTOCOL") or MINIMAX_DEFAULT_PROTOCOL)
        .strip()
        .lower()
    )
    if resolved not in ("openai", "anthropic"):
        raise ValueError(
            f"Unsupported MiniMax API protocol {resolved!r}; choose one of: openai, anthropic"
        )
    return resolved


def resolve_minimax_endpoint(
    region: str | None = None,
    protocol: str | None = None,
) -> str:
    """Resolve the public MiniMax API base URL for a region and protocol."""
    resolved_region = resolve_minimax_region(region)
    resolved_protocol = resolve_minimax_protocol(protocol)
    return MINIMAX_ENDPOINTS[resolved_region][resolved_protocol]


def resolve_minimax_thinking(thinking: str | None = None) -> str | None:
    """Return a validated MiniMax thinking mode, or None for the API default.

    Precedence: explicit argument, then ``MINIMAX_THINKING``, then None (the
    API's own default, which depends on the model and protocol).
    """
    resolved = (thinking or os.environ.get("MINIMAX_THINKING") or "").strip().lower()
    if not resolved:
        return None
    if resolved not in MINIMAX_THINKING_MODES:
        choices = ", ".join(MINIMAX_THINKING_MODES)
        raise ValueError(
            f"Unsupported MiniMax thinking mode {resolved!r}; choose one of: {choices}"
        )
    return resolved
