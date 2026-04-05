"""Unified create command - single entry point for skill creation.

Auto-detects source type (web, GitHub, local, PDF, config) and routes
to appropriate converter via get_converter().
"""

import sys
import logging
import argparse
from typing import Any

from skill_seekers.cli.source_detector import SourceDetector, SourceInfo
from skill_seekers.cli.execution_context import ExecutionContext
from skill_seekers.cli.skill_converter import get_converter
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

        # 3. Initialize ExecutionContext with source info
        # This provides a single source of truth for all configuration
        # Resolve config path from args or source detection
        config_path = getattr(self.args, "config", None) or (
            self.source_info.parsed.get("config_path") if self.source_info else None
        )
        ExecutionContext.initialize(
            args=self.args,
            config_path=config_path,
            source_info=self.source_info,
        )

        # 4. Validate and warn about incompatible arguments
        self._validate_arguments()

        # 5. Route to appropriate converter
        logger.info(f"Routing to {self.source_info.type} converter...")
        result = self._route_to_scraper()
        if result != 0:
            return result

        # 6. Centralized enhancement (runs after converter, not inside each scraper)
        ctx = ExecutionContext.get()
        if ctx.enhancement.enabled and ctx.enhancement.level > 0:
            self._run_enhancement(ctx)

        # 7. Centralized workflows
        self._run_workflows()

        return 0

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
        """Route to appropriate converter based on source type.

        Builds a config dict from ExecutionContext + source_info, then
        calls converter.run() directly — no sys.argv swap needed.

        Returns:
            Exit code from converter
        """
        source_type = self.source_info.type
        ctx = ExecutionContext.get()

        # UnifiedScraper is special — it takes config_path, not a config dict
        if source_type == "config":
            from skill_seekers.cli.unified_scraper import UnifiedScraper

            config_path = self.source_info.parsed["config_path"]
            merge_mode = getattr(self.args, "merge_mode", None)
            converter = UnifiedScraper(config_path, merge_mode=merge_mode)
            return converter.run()

        config = self._build_config(source_type, ctx)
        converter = get_converter(source_type, config)
        return converter.run()

    def _build_config(self, source_type: str, ctx: ExecutionContext) -> dict[str, Any]:
        """Build a config dict for the converter from ExecutionContext.

        Each converter reads specific keys from the config dict passed to
        its __init__. This method constructs that dict from the centralized
        ExecutionContext, which already holds all CLI args + config file values.

        Args:
            source_type: Detected source type (web, github, pdf, etc.)
            ctx: Initialized ExecutionContext

        Returns:
            Config dict suitable for the converter's __init__.
        """
        parsed = self.source_info.parsed
        name = ctx.output.name or self.source_info.suggested_name

        # Common keys shared by all converters
        config: dict[str, Any] = {
            "name": name,
            "description": getattr(self.args, "description", None)
            or f"Use when working with {name}",
        }

        if source_type == "web":
            url = parsed.get("url", parsed.get("base_url", self.source_info.raw_input))
            config.update(
                {
                    "base_url": url,
                    "doc_version": ctx.output.doc_version,
                    "max_pages": ctx.scraping.max_pages,
                    "rate_limit": ctx.scraping.rate_limit,
                    "browser": ctx.scraping.browser,
                    "browser_wait_until": ctx.scraping.browser_wait_until,
                    "browser_extra_wait": ctx.scraping.browser_extra_wait,
                    "workers": ctx.scraping.workers,
                    "async_mode": ctx.scraping.async_mode,
                    "resume": ctx.scraping.resume,
                    "fresh": ctx.scraping.fresh,
                    "skip_scrape": ctx.scraping.skip_scrape,
                    "selectors": {"title": "title", "code_blocks": "pre code"},
                    "url_patterns": {"include": [], "exclude": []},
                }
            )
            # Load from config file if provided
            config_path = getattr(self.args, "config", None)
            if config_path:
                self._merge_json_config(config, config_path)

        elif source_type == "github":
            repo = parsed.get("repo", self.source_info.raw_input)
            config.update(
                {
                    "repo": repo,
                    "local_repo_path": getattr(self.args, "local_repo_path", None),
                    "include_issues": getattr(self.args, "include_issues", True),
                    "max_issues": getattr(self.args, "max_issues", 100),
                    "include_changelog": getattr(self.args, "include_changelog", True),
                    "include_releases": getattr(self.args, "include_releases", True),
                    "include_code": getattr(self.args, "include_code", False),
                }
            )
            config_path = getattr(self.args, "config", None)
            if config_path:
                self._merge_json_config(config, config_path)

        elif source_type == "local":
            directory = parsed.get("directory", self.source_info.raw_input)
            config.update(
                {
                    "directory": directory,
                    "depth": ctx.analysis.depth,
                    "output_dir": ctx.output.output_dir or f"output/{name}",
                    "languages": getattr(self.args, "languages", None),
                    "file_patterns": ctx.analysis.file_patterns,
                    "detect_patterns": not ctx.analysis.skip_patterns,
                    "extract_test_examples": not ctx.analysis.skip_test_examples,
                    "build_how_to_guides": not ctx.analysis.skip_how_to_guides,
                    "extract_config_patterns": not ctx.analysis.skip_config_patterns,
                    "build_api_reference": not ctx.analysis.skip_api_reference,
                    "build_dependency_graph": not ctx.analysis.skip_dependency_graph,
                    "extract_docs": not ctx.analysis.skip_docs,
                    "extract_comments": not ctx.analysis.no_comments,
                    "enhance_level": ctx.enhancement.level if ctx.enhancement.enabled else 0,
                    "skill_name": name,
                    "doc_version": ctx.output.doc_version,
                }
            )

        elif source_type == "pdf":
            config.update(
                {
                    "pdf_path": parsed.get("file_path", self.source_info.raw_input),
                    "extract_options": {
                        "chunk_size": 10,
                        "min_quality": 5.0,
                        "extract_images": True,
                        "min_image_size": 100,
                    },
                }
            )

        elif source_type == "word":
            config["docx_path"] = parsed.get("file_path", self.source_info.raw_input)

        elif source_type == "epub":
            config["epub_path"] = parsed.get("file_path", self.source_info.raw_input)

        elif source_type == "video":
            config.update(
                {
                    "languages": getattr(self.args, "video_languages", "en"),
                    "visual": getattr(self.args, "visual", False),
                    "whisper_model": getattr(self.args, "whisper_model", "base"),
                    "visual_interval": getattr(self.args, "visual_interval", 0.7),
                    "visual_min_gap": getattr(self.args, "visual_min_gap", 0.5),
                    "visual_similarity": getattr(self.args, "visual_similarity", 3.0),
                }
            )
            # Video source can be URL, playlist, or file
            if parsed.get("source_kind") == "file":
                config["video_file"] = parsed["file_path"]
            elif parsed.get("url"):
                url = parsed["url"]
                if "playlist" in url.lower():
                    config["playlist"] = url
                else:
                    config["url"] = url
            else:
                # Fallback: treat raw input as URL
                config["url"] = self.source_info.raw_input

        elif source_type == "jupyter":
            config["notebook_path"] = parsed.get("file_path", self.source_info.raw_input)

        elif source_type == "html":
            config["html_path"] = parsed.get("file_path", self.source_info.raw_input)

        elif source_type == "openapi":
            file_path = parsed.get("file_path", self.source_info.raw_input)
            if file_path.startswith(("http://", "https://")):
                config["spec_url"] = file_path
            else:
                config["spec_path"] = file_path

        elif source_type == "asciidoc":
            config["asciidoc_path"] = parsed.get("file_path", self.source_info.raw_input)

        elif source_type == "pptx":
            config["pptx_path"] = parsed.get("file_path", self.source_info.raw_input)

        elif source_type == "rss":
            file_path = parsed.get("file_path", self.source_info.raw_input)
            if file_path.startswith(("http://", "https://")):
                config["feed_url"] = file_path
            else:
                config["feed_path"] = file_path
            config["follow_links"] = getattr(self.args, "follow_links", True)
            config["max_articles"] = getattr(self.args, "max_articles", 50)

        elif source_type == "manpage":
            file_path = parsed.get("file_path", "")
            if file_path:
                config["man_path"] = file_path
            man_names = parsed.get("man_names", [])
            if man_names:
                config["man_names"] = man_names

        elif source_type == "confluence":
            config.update(
                {
                    "export_path": parsed.get("file_path", ""),
                    "base_url": getattr(self.args, "confluence_url", ""),
                    "space_key": getattr(self.args, "space_key", ""),
                    "username": getattr(self.args, "username", ""),
                    "token": getattr(self.args, "token", ""),
                    "max_pages": getattr(self.args, "max_pages", 500),
                }
            )

        elif source_type == "notion":
            config.update(
                {
                    "export_path": parsed.get("file_path"),
                    "database_id": getattr(self.args, "database_id", None),
                    "page_id": getattr(self.args, "page_id", None),
                    "token": getattr(self.args, "notion_token", None),
                    "max_pages": getattr(self.args, "max_pages", 100),
                }
            )

        elif source_type == "chat":
            config.update(
                {
                    "export_path": parsed.get("file_path", ""),
                    "platform": getattr(self.args, "platform", "slack"),
                    "token": getattr(self.args, "token", ""),
                    "channel": getattr(self.args, "channel", ""),
                    "max_messages": getattr(self.args, "max_messages", 1000),
                }
            )

        return config

    @staticmethod
    def _merge_json_config(config: dict[str, Any], config_path: str) -> None:
        """Merge a JSON config file into the config dict.

        Config file values are used as defaults — CLI args (already in config) take precedence.
        """
        import json

        try:
            with open(config_path, encoding="utf-8") as f:
                file_config = json.load(f)
            # Only set keys that aren't already in config
            for key, value in file_config.items():
                if key not in config:
                    config[key] = value
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load config file {config_path}: {e}")

    def _run_enhancement(self, ctx: ExecutionContext) -> None:
        """Run centralized AI enhancement after converter completes."""
        from pathlib import Path

        name = ctx.output.name or (
            self.source_info.suggested_name if self.source_info else "unnamed"
        )
        skill_dir = ctx.output.output_dir or f"output/{name}"

        logger.info("\n" + "=" * 60)
        logger.info(f"Enhancing SKILL.md (level {ctx.enhancement.level})")
        logger.info("=" * 60)

        try:
            from skill_seekers.cli.agent_client import AgentClient

            client = AgentClient(
                mode=ctx.enhancement.mode,
                agent=ctx.enhancement.agent,
                api_key=ctx.enhancement.api_key,
            )

            if client.mode == "api" and client.client:
                from skill_seekers.cli.enhance_skill import enhance_skill_md

                api_key = ctx.enhancement.api_key or client.api_key
                if api_key:
                    enhance_skill_md(skill_dir, api_key)
                    logger.info("API enhancement complete!")
                else:
                    logger.warning("No API key available for enhancement")
            else:
                from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

                enhancer = LocalSkillEnhancer(
                    Path(skill_dir),
                    agent=ctx.enhancement.agent,
                    agent_cmd=ctx.enhancement.agent_cmd,
                )
                success = enhancer.run(headless=True, timeout=ctx.enhancement.timeout)
                if success:
                    agent_name = ctx.enhancement.agent or "claude"
                    logger.info(f"Local enhancement complete! (via {agent_name})")
                else:
                    logger.warning("Local enhancement did not complete")
        except Exception as e:
            logger.warning(f"Enhancement failed: {e}")

    def _run_workflows(self) -> None:
        """Run enhancement workflows if configured."""
        try:
            from skill_seekers.cli.workflow_runner import run_workflows

            run_workflows(self.args)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Workflow execution failed: {e}")


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
