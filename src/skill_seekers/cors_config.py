"""Shared CORS configuration resolver.

Browsers reject ``Access-Control-Allow-Credentials: true`` combined with a
wildcard ``Access-Control-Allow-Origin: *``. This module resolves a safe
``(allow_origins, allow_credentials)`` pair from the ``CORS_ORIGINS`` env var
so every FastAPI/Starlette server in the project shares one policy.
"""

from __future__ import annotations

import os

DEFAULT_CORS_ORIGINS = "*"


def resolve_cors_config(raw: str | None = None) -> tuple[list[str], bool]:
    """Resolve ``(allow_origins, allow_credentials)`` from a CORS_ORIGINS value.

    - unset / empty / ``"*"`` (or any list containing ``"*"``) -> ``(["*"], False)``
      Public access; credentials are disabled because browsers reject the
      wildcard-plus-credentials combination.
    - ``"https://a.com, https://b.com"`` -> ``(["https://a.com", "https://b.com"], True)``
      Explicit origins; credentials enabled.

    ``raw`` defaults to the ``CORS_ORIGINS`` environment variable.
    """
    if raw is None:
        raw = os.environ.get("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if not origins or "*" in origins:
        return ["*"], False
    return origins, True
