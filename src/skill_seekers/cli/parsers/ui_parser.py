"""UI subcommand parser."""

import argparse

from .base import SubcommandParser


class UiParser(SubcommandParser):
    """Parser for the ui subcommand."""

    @property
    def name(self) -> str:
        return "ui"

    @property
    def help(self) -> str:
        return "Launch the Seeker HUD web interface"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--port", type=int, default=8770, help="port to serve on (default: 8770)"
        )
        parser.add_argument("--host", default="127.0.0.1", help="bind host (default: 127.0.0.1)")
        parser.add_argument(
            "--root",
            default=None,
            help="workspace root containing output/ and configs/ (default: current directory)",
        )
        parser.add_argument("--no-browser", action="store_true", help="do not open a browser tab")
        parser.add_argument("--log-level", default="warning", help="uvicorn log level")
