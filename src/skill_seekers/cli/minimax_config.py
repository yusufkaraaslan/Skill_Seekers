"""Shared MiniMax model and endpoint configuration."""

from __future__ import annotations

import os

MINIMAX_MODEL_IDS = ("MiniMax-M3", "MiniMax-M2.7")
MINIMAX_DEFAULT_MODEL = MINIMAX_MODEL_IDS[0]
MINIMAX_IMAGE_MODEL = MINIMAX_DEFAULT_MODEL

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
