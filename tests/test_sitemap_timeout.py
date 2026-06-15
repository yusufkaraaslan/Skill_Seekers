#!/usr/bin/env python3
"""The pre-crawl sitemap probe must fail fast on unreachable hosts.

`_try_sitemap` runs up to two blocking probes before the crawl starts. With a
single scalar timeout an unreachable host blocked the full window each time,
making `create <url>` look hung before any output. A (connect, read) timeout
bounds the connect phase tightly while still allowing a slow real sitemap to
download.
"""

from skill_seekers.cli import doc_scraper


def test_sitemap_probe_uses_connect_read_timeout(monkeypatch):
    seen_timeouts = []

    class _Resp:
        status_code = 404
        headers = {"content-type": "text/html"}
        text = ""

    def fake_get(_url, **kwargs):
        seen_timeouts.append(kwargs.get("timeout"))
        return _Resp()

    monkeypatch.setattr(doc_scraper.requests, "get", fake_get)
    converter = doc_scraper.DocToSkillConverter(
        {"name": "t", "base_url": "https://example.com/"}, dry_run=True
    )
    converter._try_sitemap()

    assert seen_timeouts, "sitemap probe made no request"
    for timeout in seen_timeouts:
        assert isinstance(timeout, tuple) and len(timeout) == 2, (
            f"expected a (connect, read) timeout tuple, got {timeout!r}"
        )
        connect, read = timeout
        assert connect <= read
