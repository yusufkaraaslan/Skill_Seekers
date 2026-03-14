"""Sync-config command argument definitions.

Shared between sync_config.py (standalone) and parsers/sync_config_parser.py
(unified CLI) so the two entry points never drift out of sync.
"""

import argparse


def add_sync_config_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all sync-config arguments to *parser*."""

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        required=True,
        help="Path to the config JSON file to sync",
        metavar="FILE",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Write updated start_urls back to the config file (default: dry-run)",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="BFS crawl depth from seed pages (default: 2)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=500,
        help="Maximum pages to discover (default: 500)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=None,
        help="Override config rate-limit (seconds between requests)",
    )
    parser.add_argument(
        "--source-index",
        type=int,
        default=0,
        help="Index of the documentation source to sync (default: 0)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Verbose output",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="Suppress informational output",
    )
