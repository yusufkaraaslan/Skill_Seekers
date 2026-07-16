#!/usr/bin/env python3
"""Tests for the MCP fetch retry helper (E2.6, #92)."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

import httpx

from skill_seekers.mcp.tools.source_tools import _get_with_retry


def _response(status_code: int) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"{status_code}", request=MagicMock(), response=resp
        )
    return resp


class TestGetWithRetry(unittest.TestCase):
    def test_transient_connect_errors_are_retried(self):
        """Two connection failures then success -> returns the response."""
        ok = _response(200)
        client = MagicMock()
        client.get = AsyncMock(
            side_effect=[httpx.ConnectError("boom"), httpx.ReadTimeout("slow"), ok]
        )

        result = asyncio.run(_get_with_retry(client, "https://x.test/a", base_delay=0.01))

        self.assertIs(result, ok)
        self.assertEqual(client.get.await_count, 3)

    def test_5xx_is_retried(self):
        """A 500 then success -> retried and returns the good response."""
        ok = _response(200)
        client = MagicMock()
        client.get = AsyncMock(side_effect=[_response(500), ok])

        result = asyncio.run(_get_with_retry(client, "https://x.test/a", base_delay=0.01))

        self.assertIs(result, ok)
        self.assertEqual(client.get.await_count, 2)

    def test_404_is_not_retried(self):
        """4xx is a real answer (e.g. config not found) — returned after one call."""
        not_found = _response(404)
        client = MagicMock()
        client.get = AsyncMock(return_value=not_found)

        result = asyncio.run(_get_with_retry(client, "https://x.test/a", base_delay=0.01))

        self.assertIs(result, not_found)
        self.assertEqual(client.get.await_count, 1)

    def test_persistent_failure_raises_after_three_attempts(self):
        client = MagicMock()
        client.get = AsyncMock(side_effect=httpx.ConnectError("down"))

        with self.assertRaises(httpx.ConnectError):
            asyncio.run(_get_with_retry(client, "https://x.test/a", base_delay=0.01))

        self.assertEqual(client.get.await_count, 3)

    def test_params_are_passed_through(self):
        ok = _response(200)
        client = MagicMock()
        client.get = AsyncMock(return_value=ok)

        asyncio.run(_get_with_retry(client, "https://x.test/a", params={"category": "web"}))

        client.get.assert_awaited_once_with("https://x.test/a", params={"category": "web"})


if __name__ == "__main__":
    unittest.main()
