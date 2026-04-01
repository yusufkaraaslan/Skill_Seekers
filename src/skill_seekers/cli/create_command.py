"""Unified create command - single entry point for skill creation.

Auto-detects source type (web, GitHub, local, PDF, config) and routes
to appropriate scraper while maintaining full backward compatibility.
"""

import sys
import logging
import argparse

from skill_seekers.cli.source_detector import SourceDetector, SourceInfo
from skill_seekers.cli.arguments.create import (
    get_compatible_arguments,
    get_universal_argument_names,
)
from skill_seekers.cli.arguments.common import DEFAULT_CHUNK_TOKENS, DEFAULT_CHUNK_OVERLAP_TOKENS

logger = logging.getLogger(__name__)


class CreateCommand:
    """Unified create command implementation."""

    def __init__(self, args: argparse.Namespace):
        """Initialize create command.

        Args:
            args: Parsed command-line arguments
        """
        self.args = args
        self.source_info: SourceInfo | None = None

    def execute(self) -> int:
        """Execute the create command.

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # 1. Detect source type
        try:
            self.source_info = SourceDetector.detect(self.args.source)
            logger.info(f"Detected source type: {self.source_info.type}")
            logger.debug(f"Parsed info: {self.source_info.parsed}")
        except ValueError as e:
            logger.error(str(e))
            return 1

        # 2. Validate source accessibility
        try:
            SourceDetector.validate_source(self.source_info)
        except ValueError as e:
            logger.error(f"Source validation failed: {e}")
            return 1

        # 3. Validate and warn about incompatible arguments
        self._validate_arguments()

        # 4. Route to appropriate scraper
        logger.info(f"Routing to {self.source_info.type} scraper...")
        return self._route_to_scraper()

    def _validate_arguments(self) -> None:
        """Validate arguments and warn about incompatible ones."""
        # Get compatible arguments for this source type
        compatible = set(get_compatible_arguments(self.source_info.type))
        universal = get_universal_argument_names()

        # Check all provided arguments
        for arg_name, arg_value in vars(self.args).items():
            # Skip if not explicitly set (has default value)
            if not self._is_explicitly_set(arg_name, arg_value):
                continue

            # Skip if compatible
            if arg_name in compatible:
                continue

            # Skip internal arguments
            if arg_name in ["source", "func", "subcommand"]:
                continue

            # Warn about incompatible argument
            if arg_name not in universal:
                logger.warning(
                    f"--{arg_name.replace('_', '-')} is not applicable for "
                    f"{self.source_info.type} sources and will be ignored"
                )

    def _is_explicitly_set(self, arg_name: str, arg_value: any) -> bool:
        """Check if an argument was explicitly set by the user.

        Args:
            arg_name: Argument name
            arg_value: Argument value

        Returns:
            True if user explicitly set this argument
        """
        # Boolean flags - True means it was set
        if isinstance(arg_value, bool):
            return arg_value

        # None means not set
        if arg_value is None:
            return False

        # Check against common defaults — args with these values were NOT
        # explicitly set by the user and should not be forwarded.
        defaults = {
            "max_issues": 100,
            "chunk_tokens": DEFAULT_CHUNK_TOKENS,
            "chunk_overlap_tokens": DEFAULT_CHUNK_OVERLAP_TOKENS,
            "output": None,
            "enhance_level": 2,
            "doc_version": "",
            "video_languages": "en",
            "whisper_model": "base",
            "platform": "slack",
            "visual_interval": 0.7,
            "visual_min_gap": 0.5,
            "visual_similarity": 3.0,
        }

        if arg_name in defaults:
            return arg_value != defaults[arg_name]

        # Any other non-None value means it was set
        return True

    def _route_to_scraper(self) -> int:
        """Route to appropriate scraper based on source type.

        Returns:
            Exit code from scraper
        """
        if self.source_info.type == "web":
            return self._route_web()
        elif self.source_info.type == "github":
            return self._route_github()
        elif self.source_info.type == "local":
            return self._route_local()
        elif self.source_info.type == "pdf":
            return self._route_pdf()
        elif self.source_info.type == "word":
            return self._route_word()
        elif self.source_info.type == "epub":
            return self._route_epub()
        elif self.source_info.type == "video":
            return self._route_video()
        elif self.source_info.type == "config":
            return self._route_config()
        elif self.source_info.type == "jupyter":
            return self._route_generic("jupyter_scraper", "--notebook")
        elif self.source_info.type == "html":
            return self._route_generic("html_scraper", "--html-path")
        elif self.source_info.type == "openapi":
            return self._route_generic("openapi_scraper", "--spec")
        elif self.source_info.type == "asciidoc":
            return self._route_generic("asciidoc_scraper", "--asciidoc-path")
        elif self.source_info.type == "pptx":
            return self._route_generic("pptx_scraper", "--pptx")
        elif self.source_info.type == "rss":
            return self._route_generic("rss_scraper", "--feed-path")
        elif self.source_info.type == "manpage":
            return self._route_generic("man_scraper", "--man-path")
        elif self.source_info.type == "confluence":
            return self._route_generic("confluence_scraper", "--export-path")
        elif self.source_info.type == "notion":
            return self._route_generic("notion_scraper", "--export-path")
        elif self.source_info.type == "chat":
            return self._route_generic("chat_scraper", "--export-path")
        else:
            logger.error(f"Unknown source type: {self.source_info.type}")
            return 1

    # ── Dynamic argument forwarding ──────────────────────────────────────
    #
    # Instead of manually checking each flag in every _route_*() method,
    # _build_argv() dynamically iterates vars(self.args) and forwards all
    # explicitly-set arguments.  This is the same pattern used by
    # main.py::_reconstruct_argv() and eliminates ~40 missing-flag gaps.

    # Dest names that differ from their CLI flag (dest → flag)
    _DEST_TO_FLAG = {
        "async_mode": "--async",
        "video_url": "--url",
        "video_playlist": "--playlist",
        "video_languages": "--languages",
        "skip_config": "--skip-config-patterns",
    }

    # Internal args that should never be forwarded to sub-scrapers.
    # video_url/video_playlist/video_file are handled as positionals by _route_video().
    # config is forwarded manually only by routes that need it (web, github).
    _SKIP_ARGS = frozenset(
        {
            "source",
            "func",
            "subcommand",
            "command",
            "config",
            "video_url",
            "video_playlist",
            "video_file",
        }
    )

    def _build_argv(self, module_name: str, positional_args: list[str]) -> list[str]:
        """Build argv dynamically by forwarding all explicitly-set arguments.

        Uses the same pattern as main.py::_reconstruct_argv().
        Replaces manual per-flag checking in _route_*() and _add_common_args().

        Args:
            module_name: Scraper module name (e.g., "doc_scraper")
            positional_args: Positional arguments to prepend (e.g., [url] or ["--repo", repo])

        Returns:
            Complete argv list for the scraper
        """
        argv = [module_name] + positional_args

        # Auto-add suggested name if user didn't provide one
        if not self.args.name and self.source_info:
            argv.extend(["--name", self.source_info.suggested_name])

        for key, value in vars(self.args).items():
            if key in self._SKIP_ARGS or key.startswith("_help_"):
                continue
            if not self._is_explicitly_set(key, value):
                continue

            # Use translation map for mismatched dest→flag names, else derive from key
            if key in self._DEST_TO_FLAG:
                arg_flag = self._DEST_TO_FLAG[key]
            else:
                arg_flag = f"--{key.replace('_', '-')}"

            if isinstance(value, bool):
                if value:
                    argv.append(arg_flag)
            elif isinstance(value, list):
                for item in value:
                    argv.extend([arg_flag, str(item)])
            elif value is not None:
                argv.extend([arg_flag, str(value)])

        return argv

    def _call_module(self, module, argv: list[str]) -> int:
        """Call a scraper module with the given argv.

        Swaps sys.argv, calls module.main(), restores sys.argv.
        """
        logger.debug(f"Calling {argv[0]} with argv: {argv}")
        original_argv = sys.argv
        try:
            sys.argv = argv
            result = module.main()
            return result if result is not None else 0
        finally:
            sys.argv = original_argv

    def _route_web(self) -> int:
        """Route to web documentation scraper (doc_scraper.py)."""
        from skill_seekers.cli import doc_scraper

        url = self.source_info.parsed.get("url", self.source_info.raw_source)
        argv = self._build_argv("doc_scraper", [url])

        # Forward config if set (not in _build_argv since it's in SKIP_ARGS
        # to avoid double-forwarding for config-type sources)
        if self.args.config:
            argv.extend(["--config", self.args.config])

        return self._call_module(doc_scraper, argv)

    def _route_github(self) -> int:
        """Route to GitHub repository scraper (github_scraper.py)."""
        from skill_seekers.cli import github_scraper

        repo = self.source_info.parsed.get("repo", self.source_info.raw_source)
        argv = self._build_argv("github_scraper", ["--repo", repo])

        if self.args.config:
            argv.extend(["--config", self.args.config])

        return self._call_module(github_scraper, argv)

    def _route_local(self) -> int:
        """Route to local codebase analyzer (codebase_scraper.py)."""
        from skill_seekers.cli import codebase_scraper

        directory = self.source_info.parsed.get("directory", self.source_info.raw_source)
        argv = self._build_argv("codebase_scraper", ["--directory", directory])
        return self._call_module(codebase_scraper, argv)

    def _route_pdf(self) -> int:
        """Route to PDF scraper (pdf_scraper.py)."""
        from skill_seekers.cli import pdf_scraper

        file_path = self.source_info.parsed.get("file_path", self.source_info.raw_source)
        argv = self._build_argv("pdf_scraper", ["--pdf", file_path])
        return self._call_module(pdf_scraper, argv)

    def _route_word(self) -> int:
        """Route to Word document scraper (word_scraper.py)."""
        from skill_seekers.cli import word_scraper

        file_path = self.source_info.parsed.get("file_path", self.source_info.raw_source)
        argv = self._build_argv("word_scraper", ["--docx", file_path])
        return self._call_module(word_scraper, argv)

    def _route_epub(self) -> int:
        """Route to EPUB scraper (epub_scraper.py)."""
        from skill_seekers.cli import epub_scraper

        file_path = self.source_info.parsed.get("file_path", self.source_info.raw_source)
        argv = self._build_argv("epub_scraper", ["--epub", file_path])
        return self._call_module(epub_scraper, argv)

    def _route_video(self) -> int:
        """Route to video scraper (video_scraper.py)."""
        from skill_seekers.cli import video_scraper

        parsed = self.source_info.parsed
        if parsed.get("source_kind") == "file":
            positional = ["--video-file", parsed["file_path"]]
        elif parsed.get("url"):
            url = parsed["url"]
            flag = "--playlist" if "playlist" in url.lower() else "--url"
            positional = [flag, url]
        else:
            positional = []

        argv = self._build_argv("video_scraper", positional)
        return self._call_module(video_scraper, argv)

    def _route_config(self) -> int:
        """Route to unified scraper for config files (unified_scraper.py)."""
        from skill_seekers.cli import unified_scraper

        config_path = self.source_info.parsed["config_path"]
        argv = self._build_argv("unified_scraper", ["--config", config_path])
        return self._call_module(unified_scraper, argv)

    def _route_generic(self, module_name: str, file_flag: str) -> int:
        """Generic routing for new source types.

        All new source types (jupyter, html, openapi, asciidoc, pptx, rss,
        manpage, confluence, notion, chat) use dynamic argument forwarding.
        """
        import importlib

        module = importlib.import_module(f"skill_seekers.cli.{module_name}")

        file_path = self.source_info.parsed.get("file_path", "")
        positional = [file_flag, file_path] if file_path else []
        argv = self._build_argv(module_name, positional)
        return self._call_module(module, argv)


def main() -> int:
    """Entry point for create command.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    import textwrap
    from skill_seekers.cli.arguments.create import add_create_arguments

    # Parse arguments
    # Custom formatter to prevent line wrapping in epilog
    class NoWrapFormatter(argparse.RawDescriptionHelpFormatter):
        def _split_lines(self, text, width):
            return text.splitlines()

    parser = argparse.ArgumentParser(
        prog="skill-seekers create",
        description="Create skill from any source (auto-detects type)",
        formatter_class=NoWrapFormatter,
        epilog=textwrap.dedent("""\
Examples:
  Web:      skill-seekers create https://docs.react.dev/
  GitHub:   skill-seekers create facebook/react -p standard
  Local:    skill-seekers create ./my-project -p comprehensive
  PDF:      skill-seekers create tutorial.pdf --ocr
  DOCX:     skill-seekers create document.docx
  EPUB:     skill-seekers create ebook.epub
  Video:    skill-seekers create https://youtube.com/watch?v=...
  Video:    skill-seekers create recording.mp4
  Config:   skill-seekers create configs/react.json

Source Auto-Detection:
  URLs/domains -> web scraping
  owner/repo -> GitHub analysis
  ./path -> local codebase
  file.pdf -> PDF extraction
  file.docx -> Word document extraction
  file.epub -> EPUB extraction
  youtube.com/... -> Video transcript extraction
  file.mp4 -> Video file extraction
  file.json -> multi-source config

Progressive Help (13 -> 120+ flags):
  --help-web       Web scraping options
  --help-github    GitHub repository options
  --help-local     Local codebase analysis
  --help-pdf       PDF extraction options
  --help-epub      EPUB extraction options
  --help-video     Video extraction options
  --help-advanced  Rare/advanced options
  --help-all       All options + compatibility

Presets (NEW: Use -p shortcut):
  -p quick              Fast (1-2 min, basic features)
  -p standard           Balanced (5-10 min, recommended)
  -p comprehensive      Full (20-60 min, all features)

Common Workflows:
  skill-seekers create <source> -p quick
  skill-seekers create <source> -p standard --enhance-level 2
  skill-seekers create <source> --chunk-for-rag
        """),
    )

    # Add arguments in default mode (universal only)
    add_create_arguments(parser, mode="default")

    # Add hidden help mode flags (use underscore prefix to match CreateParser)
    parser.add_argument("--help-web", action="store_true", help=argparse.SUPPRESS, dest="_help_web")
    parser.add_argument(
        "--help-github", action="store_true", help=argparse.SUPPRESS, dest="_help_github"
    )
    parser.add_argument(
        "--help-local", action="store_true", help=argparse.SUPPRESS, dest="_help_local"
    )
    parser.add_argument("--help-pdf", action="store_true", help=argparse.SUPPRESS, dest="_help_pdf")
    parser.add_argument(
        "--help-word", action="store_true", help=argparse.SUPPRESS, dest="_help_word"
    )
    parser.add_argument(
        "--help-epub", action="store_true", help=argparse.SUPPRESS, dest="_help_epub"
    )
    parser.add_argument(
        "--help-video", action="store_true", help=argparse.SUPPRESS, dest="_help_video"
    )
    parser.add_argument(
        "--help-config", action="store_true", help=argparse.SUPPRESS, dest="_help_config"
    )
    parser.add_argument(
        "--help-advanced", action="store_true", help=argparse.SUPPRESS, dest="_help_advanced"
    )
    parser.add_argument("--help-all", action="store_true", help=argparse.SUPPRESS, dest="_help_all")

    # Parse arguments
    args = parser.parse_args()

    # Handle source-specific help modes
    if args._help_web:
        # Recreate parser with web-specific arguments
        parser_web = argparse.ArgumentParser(
            prog="skill-seekers create",
            description="Create skill from web documentation",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        add_create_arguments(parser_web, mode="web")
        parser_web.print_help()
        return 0
    elif args._help_github:
        parser_github = argparse.ArgumentParser(
            prog="skill-seekers create",
            description="Create skill from GitHub repository",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        add_create_arguments(parser_github, mode="github")
        parser_github.print_help()
        return 0
    elif args._help_local:
        parser_local = argparse.ArgumentParser(
            prog="skill-seekers create",
            description="Create skill from local codebase",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        add_create_arguments(parser_local, mode="local")
        parser_local.print_help()
        return 0
    elif args._help_pdf:
        parser_pdf = argparse.ArgumentParser(
            prog="skill-seekers create",
            description="Create skill from PDF file",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        add_create_arguments(parser_pdf, mode="pdf")
        parser_pdf.print_help()
        return 0
    elif args._help_word:
        parser_word = argparse.ArgumentParser(
            prog="skill-seekers create",
            description="Create skill from Word document (.docx)",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        add_create_arguments(parser_word, mode="word")
        parser_word.print_help()
        return 0
    elif args._help_epub:
        parser_epub = argparse.ArgumentParser(
            prog="skill-seekers create",
            description="Create skill from EPUB e-book (.epub)",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        add_create_arguments(parser_epub, mode="epub")
        parser_epub.print_help()
        return 0
    elif args._help_video:
        parser_video = argparse.ArgumentParser(
            prog="skill-seekers create",
            description="Create skill from video (YouTube, Vimeo, local files)",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        add_create_arguments(parser_video, mode="video")
        parser_video.print_help()
        return 0
    elif args._help_config:
        parser_config = argparse.ArgumentParser(
            prog="skill-seekers create",
            description="Create skill from multi-source config file (unified scraper)",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        add_create_arguments(parser_config, mode="config")
        parser_config.print_help()
        return 0
    elif args._help_advanced:
        parser_advanced = argparse.ArgumentParser(
            prog="skill-seekers create",
            description="Create skill - advanced options",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        add_create_arguments(parser_advanced, mode="advanced")
        parser_advanced.print_help()
        return 0
    elif args._help_all:
        parser_all = argparse.ArgumentParser(
            prog="skill-seekers create",
            description="Create skill - all options",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        add_create_arguments(parser_all, mode="all")
        parser_all.print_help()
        return 0

    # Setup logging
    log_level = logging.DEBUG if args.verbose else (logging.WARNING if args.quiet else logging.INFO)
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    # Validate source provided (config file can serve as source)
    if not args.source and not args.config:
        parser.error("source is required (or use --config to specify a config file)")

    # If config is provided but no source, peek at the JSON to route correctly
    if not args.source and args.config:
        import json

        try:
            with open(args.config) as f:
                config_peek = json.load(f)
            if "sources" in config_peek:
                # Unified format → route to unified_scraper via config type detection
                args.source = args.config
            elif "base_url" in config_peek:
                # Simple web config → route to doc_scraper by using the base_url
                args.source = config_peek["base_url"]
                # source will be detected as web URL; --config is already set
            else:
                parser.error("Config file must contain 'sources' (unified) or 'base_url' (web)")
        except json.JSONDecodeError as e:
            parser.error(f"Cannot parse config file as JSON: {e}")
        except FileNotFoundError:
            parser.error(f"Config file not found: {args.config}")

    # Execute create command
    command = CreateCommand(args)
    return command.execute()


if __name__ == "__main__":
    sys.exit(main())
