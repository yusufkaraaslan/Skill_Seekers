"""Tests for skill_seekers.cors_config.resolve_cors_config."""

import pytest

from skill_seekers.cors_config import resolve_cors_config


@pytest.mark.parametrize(
    "raw, origins, credentials",
    [
        # Wildcard / empty -> public, credentials disabled (browsers reject the combo).
        ("*", ["*"], False),
        ("", ["*"], False),
        ("   ", ["*"], False),
        (" * ", ["*"], False),
        # A wildcard mixed into a list must still collapse to public, no credentials.
        ("*,https://a.com", ["*"], False),
        ("https://a.com, *", ["*"], False),
        # Explicit origins -> credentials enabled.
        ("https://a.com", ["https://a.com"], True),
        ("https://a.com,https://b.com", ["https://a.com", "https://b.com"], True),
        # Whitespace and empty segments are trimmed/dropped.
        ("https://a.com, https://b.com", ["https://a.com", "https://b.com"], True),
        ("https://a.com,,https://b.com", ["https://a.com", "https://b.com"], True),
    ],
)
def test_resolve_cors_config_explicit(raw, origins, credentials):
    assert resolve_cors_config(raw) == (origins, credentials)


def test_resolve_cors_config_env_default(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert resolve_cors_config() == (["*"], False)


def test_resolve_cors_config_env_explicit(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://x.com,https://y.com")
    assert resolve_cors_config() == (["https://x.com", "https://y.com"], True)
