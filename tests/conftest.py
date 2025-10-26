"""
Pytest configuration for tests.

Configures anyio to only use asyncio backend (not trio).
"""

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    """Override anyio backend to only use asyncio (not trio)."""
    return "asyncio"
