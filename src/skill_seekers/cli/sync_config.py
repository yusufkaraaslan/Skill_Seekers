#!/usr/bin/env python3
"""Sync a config file's start_urls against what's currently live on a docs site.

Crawls navigation links from seed pages, diffs them against the config's
``start_urls``, and optionally writes the updated list back.

Usage:
    skill-seekers sync-config --config configs/claude-code.json
    skill-seekers sync-config --config configs/claude-code.json --apply
"""

import argparse
import json
import logging
import sys
import time
from collections import deque
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from skill_seekers.cli.defaults import DEFAULTS
from skill_seekers.cli.utils import sanitize_url, setup_logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# URL filtering (mirrors DocToSkillConverter.is_valid_url logic)
# ---------------------------------------------------------------------------


def _is_valid_url(
    url: str,
    base_url: str,
    include_patterns: list[str],
    exclude_patterns: list[str],
) -> bool:
    """Return True if *url* passes include/exclude pattern filters."""
    if not url.startswith(base_url):
        return False
    if include_patterns and not any(p in url for p in include_patterns):
        return False
    return not any(p in url for p in exclude_patterns)


# ---------------------------------------------------------------------------
# Lightweight BFS link discovery
# ---------------------------------------------------------------------------


def discover_urls(
    base_url: str,
    seed_urls: list[str],
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    depth: int = 2,
    max_pages: int = DEFAULTS["scraping"]["max_pages"],
    rate_limit: float = DEFAULTS["scraping"]["rate_limit"],
) -> set[str]:
    """BFS-crawl *seed_urls* and return all discovered internal URLs.

    Only follows ``<a href>`` links on HTML pages; does not download
    full page content.  Applies the same include/exclude filtering as
    :class:`DocToSkillConverter`.

    Args:
        base_url: Only URLs under this prefix are accepted.
        seed_urls: Starting points for the BFS.
        include_patterns: Substring patterns a URL must contain (any).
        exclude_patterns: Substring patterns that disqualify a URL.
        depth: Maximum number of BFS hops from the seed pages.
        max_pages: Stop after discovering this many unique URLs.
        rate_limit: Seconds to wait between HTTP requests.

    Returns:
        Set of discovered absolute URLs (fragments stripped).
    """
    includes = include_patterns or []
    excludes = exclude_patterns or []

    visited: set[str] = set()
    # Queue entries are (url, current_depth)
    queue: deque[tuple[str, int]] = deque()
    for u in seed_urls:
        u = sanitize_url(u)
        queue.append((u, 0))

    discovered: set[str] = set()

    unlimited = max_pages is None or max_pages < 0
    while queue and (unlimited or len(discovered) < max_pages):
        url, cur_depth = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        if not _is_valid_url(url, base_url, includes, excludes):
            continue

        logger.debug("  [depth %d] %s", cur_depth, url)

        try:
            headers = {"User-Agent": "Mozilla/5.0 (Skill-Seekers sync-config)"}
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            logger.warning("  Could not fetch %s: %s", url, e)
            continue

        # Only mark as "discovered" after a successful fetch — 404s and
        # other errors mean the page no longer exists on the live site.
        discovered.add(url)

        # Follow links if we haven't hit the depth limit
        if cur_depth < depth:
            soup = BeautifulSoup(resp.content, "html.parser")
            for link in soup.find_all("a", href=True):
                href = urljoin(url, link["href"])
                href = href.split("#")[0]  # strip fragment
                href = sanitize_url(href)
                if href not in visited and _is_valid_url(href, base_url, includes, excludes):
                    queue.append((href, cur_depth + 1))

        if rate_limit > 0:
            time.sleep(rate_limit)

    return discovered


# ---------------------------------------------------------------------------
# Diff logic
# ---------------------------------------------------------------------------


def diff_urls(discovered: set[str], configured: list[str]) -> tuple[list[str], list[str]]:
    """Compare *discovered* URLs against a *configured* list.

    Returns:
        ``(added, removed)`` — both sorted lists of URLs.
    """
    configured_set = set(configured)
    added = sorted(discovered - configured_set)
    removed = sorted(configured_set - discovered)
    return added, removed


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------


def _get_doc_source(config: dict, source_index: int = 0) -> dict | None:
    """Extract the documentation source dict from *config*.

    Handles both the unified format (``sources`` array) and legacy flat
    format (fields at the top level).
    """
    sources = config.get("sources")
    if sources:
        doc_sources = [s for s in sources if s.get("type") == "documentation"]
        if source_index < len(doc_sources):
            return doc_sources[source_index]
        return None

    # Legacy flat format — treat the whole config as a single source
    if config.get("base_url"):
        return config
    return None


def _set_start_urls(config: dict, source_index: int, urls: list[str]) -> None:
    """Write *urls* into the correct ``start_urls`` field in *config*."""
    sources = config.get("sources")
    if sources:
        doc_sources = [s for s in sources if s.get("type") == "documentation"]
        if source_index < len(doc_sources):
            doc_sources[source_index]["start_urls"] = urls
            return
    # Legacy flat format
    config["start_urls"] = urls


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def sync_config(
    config_path: str,
    apply: bool = False,
    depth: int = 2,
    max_pages: int = DEFAULTS["scraping"]["max_pages"],
    rate_limit: float | None = None,
    source_index: int = 0,
) -> dict:
    """Run the sync-config workflow.

    Returns:
        Dict with keys ``added``, ``removed``, ``total_discovered``,
        ``total_configured``, ``applied``.
    """
    # Load config
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    source = _get_doc_source(config, source_index)
    if source is None:
        logger.error("No documentation source found at index %d in %s", source_index, config_path)
        return {
            "added": [],
            "removed": [],
            "total_discovered": 0,
            "total_configured": 0,
            "applied": False,
            "error": "No documentation source found",
        }

    base_url: str = source["base_url"]
    configured_urls: list[str] = source.get("start_urls") or []
    seed_urls: list[str] = source.get("nav_seed_urls") or configured_urls or [base_url]
    url_patterns = source.get("url_patterns", {})
    includes: list[str] = url_patterns.get("include", [])
    excludes: list[str] = url_patterns.get("exclude", [])
    effective_rate = (
        rate_limit
        if rate_limit is not None
        else source.get("rate_limit", DEFAULTS["scraping"]["rate_limit"])
    )

    logger.info("Syncing config: %s", config_path)
    logger.info("  Base URL:      %s", base_url)
    logger.info("  Seed URLs:     %d", len(seed_urls))
    logger.info("  Configured:    %d start_urls", len(configured_urls))
    logger.info("  Depth:         %d", depth)
    logger.info("  Rate limit:    %.1fs", effective_rate)
    logger.info("")

    # Discover
    discovered = discover_urls(
        base_url=base_url,
        seed_urls=seed_urls,
        include_patterns=includes,
        exclude_patterns=excludes,
        depth=depth,
        max_pages=max_pages,
        rate_limit=effective_rate,
    )

    # Diff
    added, removed = diff_urls(discovered, configured_urls)

    # Report
    if added:
        logger.info("New pages (%d):", len(added))
        for url in added:
            path = url.replace(base_url, "/")
            logger.info("  + %s", path)
    if removed:
        logger.info("Removed pages (%d):", len(removed))
        for url in removed:
            path = url.replace(base_url, "/")
            logger.info("  - %s", path)

    if not added and not removed:
        logger.info("Config is up to date. No changes detected.")
    else:
        logger.info("")
        logger.info(
            "Summary: %d new, %d removed (discovered %d total, configured %d)",
            len(added),
            len(removed),
            len(discovered),
            len(configured_urls),
        )

    applied = False
    if apply and (added or removed):
        new_urls = sorted(discovered)
        _set_start_urls(config, source_index, new_urls)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.write("\n")
        logger.info("Updated %s (%d start_urls)", config_path, len(new_urls))
        applied = True
    elif added or removed:
        logger.info("Run with --apply to update %s", config_path)

    return {
        "added": added,
        "removed": removed,
        "total_discovered": len(discovered),
        "total_configured": len(configured_urls),
        "applied": applied,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for ``skill-seekers sync-config``."""
    from skill_seekers.cli.arguments.sync_config import add_sync_config_arguments

    parser = argparse.ArgumentParser(
        prog="skill-seekers-sync-config",
        description="Sync a config's start_urls against what's live on the docs site.",
    )
    add_sync_config_arguments(parser)
    args = parser.parse_args()

    setup_logging(verbose=args.verbose, quiet=args.quiet)

    result = sync_config(
        config_path=args.config,
        apply=args.apply,
        depth=args.depth,
        max_pages=args.max_pages,
        rate_limit=args.rate_limit,
        source_index=args.source_index,
    )

    if result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
