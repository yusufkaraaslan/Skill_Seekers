#!/usr/bin/env python3
"""Tests for doc_scraper network retry with exponential backoff (#97)."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import requests

from skill_seekers.cli.doc_scraper import DocToSkillConverter


def _resp(status_code: int):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(str(status_code))
    return resp


def _hx_resp(status_code: int):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            str(status_code), request=MagicMock(), response=resp
        )
    return resp


class TestScraperRetry(unittest.TestCase):
    def _scraper(self, max_retries=3):
        return DocToSkillConverter(
            {
                "name": "t",
                "base_url": "https://x.test/",
                "max_retries": max_retries,
                "rate_limit": 0,
            }
        )

    def test_default_max_retries_is_three(self):
        self.assertEqual(self._scraper().max_retries, 3)

    def test_max_retries_floor_is_one(self):
        # 0 or negative would make retry_with_backoff never attempt; clamp to 1.
        self.assertEqual(self._scraper(max_retries=0).max_retries, 1)

    @patch("time.sleep")
    def test_transient_errors_are_retried(self, _sleep):
        s = self._scraper()
        with patch(
            "skill_seekers.cli.doc_scraper.requests.get",
            side_effect=[requests.ConnectionError("boom"), requests.Timeout("slow"), _resp(200)],
        ) as g:
            resp = s._get_with_retry("https://x.test/a", {}, 30)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(g.call_count, 3)

    @patch("time.sleep")
    def test_5xx_is_retried(self, _sleep):
        s = self._scraper()
        with patch(
            "skill_seekers.cli.doc_scraper.requests.get",
            side_effect=[_resp(503), _resp(200)],
        ) as g:
            resp = s._get_with_retry("https://x.test/a", {}, 30)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(g.call_count, 2)

    @patch("time.sleep")
    def test_4xx_is_not_retried(self, _sleep):
        s = self._scraper()
        with patch("skill_seekers.cli.doc_scraper.requests.get", return_value=_resp(404)) as g:
            resp = s._get_with_retry("https://x.test/a", {}, 30)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(g.call_count, 1)

    @patch("time.sleep")
    def test_persistent_failure_raises_after_max_attempts(self, _sleep):
        s = self._scraper(max_retries=3)
        with (
            patch(
                "skill_seekers.cli.doc_scraper.requests.get",
                side_effect=requests.ConnectionError("down"),
            ) as g,
            self.assertRaises(requests.ConnectionError),
        ):
            s._get_with_retry("https://x.test/a", {}, 30)
        self.assertEqual(g.call_count, 3)

    @patch("time.sleep")
    def test_max_retries_one_disables_retry(self, _sleep):
        s = self._scraper(max_retries=1)
        with (
            patch(
                "skill_seekers.cli.doc_scraper.requests.get",
                side_effect=requests.ConnectionError("x"),
            ) as g,
            self.assertRaises(requests.ConnectionError),
        ):
            s._get_with_retry("https://x.test/a", {}, 30)
        self.assertEqual(g.call_count, 1)

    def test_async_transient_error_is_retried(self):
        s = self._scraper()
        client = MagicMock()
        client.get = AsyncMock(side_effect=[httpx.ConnectError("boom"), _hx_resp(200)])
        with patch("asyncio.sleep", new=AsyncMock()):
            resp = asyncio.run(s._aget_with_retry(client, "https://x.test/a", {}, 30.0))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(client.get.await_count, 2)

    def test_async_4xx_not_retried(self):
        s = self._scraper()
        client = MagicMock()
        client.get = AsyncMock(return_value=_hx_resp(404))
        with patch("asyncio.sleep", new=AsyncMock()):
            resp = asyncio.run(s._aget_with_retry(client, "https://x.test/a", {}, 30.0))
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(client.get.await_count, 1)


if __name__ == "__main__":
    unittest.main()
