"""Parser for the sync-config subcommand."""

import argparse

from .base import SubcommandParser


class SyncConfigParser(SubcommandParser):
    """Subcommand parser for ``skill-seekers sync-config``."""

    @property
    def name(self) -> str:
        return "sync-config"

    @property
    def help(self) -> str:
        return "Diff/update a config's start_urls against the live docs site"

    @property
    def description(self) -> str:
        return (
            "Crawl navigation links from a docs site, compare them against "
            "the config's start_urls, and optionally write the updated list "
            "back with --apply."
        )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        from skill_seekers.cli.arguments.sync_config import add_sync_config_arguments

        add_sync_config_arguments(parser)
