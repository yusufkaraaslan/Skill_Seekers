"""Video subcommand parser.

Uses shared argument definitions from arguments.video to ensure
consistency with the standalone video_scraper module.
"""

from .base import SubcommandParser
from skill_seekers.cli.arguments.video import add_video_arguments


class VideoParser(SubcommandParser):
    """Parser for video subcommand."""

    @property
    def name(self) -> str:
        return "video"

    @property
    def help(self) -> str:
        return "Extract from video (YouTube, local files)"

    @property
    def description(self) -> str:
        return "Extract transcripts and metadata from videos and generate skill"

    def add_arguments(self, parser):
        """Add video-specific arguments.

        Uses shared argument definitions to ensure consistency
        with video_scraper.py (standalone scraper).
        """
        add_video_arguments(parser)
