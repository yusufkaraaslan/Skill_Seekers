"""Unified create command - single entry point for skill creation.

Auto-detects source type (web, GitHub, local, PDF, config) and routes
to appropriate scraper while maintaining full backward compatibility.
"""

import sys
import logging
import argparse
from typing import List, Optional

from skill_seekers.cli.source_detector import SourceDetector, SourceInfo
from skill_seekers.cli.arguments.create import (
    get_compatible_arguments,
    get_universal_argument_names,
)

logger = logging.getLogger(__name__)


class CreateCommand:
    """Unified create command implementation."""

    def __init__(self, args: argparse.Namespace):
        """Initialize create command.

        Args:
            args: Parsed command-line arguments
        """
        self.args = args
        self.source_info: Optional[SourceInfo] = None

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
            if arg_name in ['source', 'func', 'subcommand']:
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

        # Check against common defaults
        defaults = {
            'max_issues': 100,
            'chunk_size': 512,
            'chunk_overlap': 50,
            'output': None,
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
        if self.source_info.type == 'web':
            return self._route_web()
        elif self.source_info.type == 'github':
            return self._route_github()
        elif self.source_info.type == 'local':
            return self._route_local()
        elif self.source_info.type == 'pdf':
            return self._route_pdf()
        elif self.source_info.type == 'config':
            return self._route_config()
        else:
            logger.error(f"Unknown source type: {self.source_info.type}")
            return 1

    def _route_web(self) -> int:
        """Route to web documentation scraper (doc_scraper.py)."""
        from skill_seekers.cli import doc_scraper

        # Reconstruct argv for doc_scraper
        argv = ['doc_scraper']

        # Add URL
        url = self.source_info.parsed['url']
        argv.append(url)

        # Add universal arguments
        self._add_common_args(argv)

        # Add web-specific arguments
        if self.args.max_pages:
            argv.extend(['--max-pages', str(self.args.max_pages)])
        if getattr(self.args, 'skip_scrape', False):
            argv.append('--skip-scrape')
        if getattr(self.args, 'resume', False):
            argv.append('--resume')
        if getattr(self.args, 'fresh', False):
            argv.append('--fresh')
        if getattr(self.args, 'rate_limit', None):
            argv.extend(['--rate-limit', str(self.args.rate_limit)])
        if getattr(self.args, 'workers', None):
            argv.extend(['--workers', str(self.args.workers)])
        if getattr(self.args, 'async_mode', False):
            argv.append('--async')
        if getattr(self.args, 'no_rate_limit', False):
            argv.append('--no-rate-limit')

        # Call doc_scraper with modified argv
        logger.debug(f"Calling doc_scraper with argv: {argv}")
        original_argv = sys.argv
        try:
            sys.argv = argv
            return doc_scraper.main()
        finally:
            sys.argv = original_argv

    def _route_github(self) -> int:
        """Route to GitHub repository scraper (github_scraper.py)."""
        from skill_seekers.cli import github_scraper

        # Reconstruct argv for github_scraper
        argv = ['github_scraper']

        # Add repo
        repo = self.source_info.parsed['repo']
        argv.extend(['--repo', repo])

        # Add universal arguments
        self._add_common_args(argv)

        # Add GitHub-specific arguments
        if getattr(self.args, 'token', None):
            argv.extend(['--token', self.args.token])
        if getattr(self.args, 'profile', None):
            argv.extend(['--profile', self.args.profile])
        if getattr(self.args, 'non_interactive', False):
            argv.append('--non-interactive')
        if getattr(self.args, 'no_issues', False):
            argv.append('--no-issues')
        if getattr(self.args, 'no_changelog', False):
            argv.append('--no-changelog')
        if getattr(self.args, 'no_releases', False):
            argv.append('--no-releases')
        if getattr(self.args, 'max_issues', None) and self.args.max_issues != 100:
            argv.extend(['--max-issues', str(self.args.max_issues)])
        if getattr(self.args, 'scrape_only', False):
            argv.append('--scrape-only')

        # Call github_scraper with modified argv
        logger.debug(f"Calling github_scraper with argv: {argv}")
        original_argv = sys.argv
        try:
            sys.argv = argv
            return github_scraper.main()
        finally:
            sys.argv = original_argv

    def _route_local(self) -> int:
        """Route to local codebase analyzer (codebase_scraper.py)."""
        from skill_seekers.cli import codebase_scraper

        # Reconstruct argv for codebase_scraper
        argv = ['codebase_scraper']

        # Add directory
        directory = self.source_info.parsed['directory']
        argv.extend(['--directory', directory])

        # Add universal arguments
        self._add_common_args(argv)

        # Add local-specific arguments
        if getattr(self.args, 'languages', None):
            argv.extend(['--languages', self.args.languages])
        if getattr(self.args, 'file_patterns', None):
            argv.extend(['--file-patterns', self.args.file_patterns])
        if getattr(self.args, 'skip_patterns', False):
            argv.append('--skip-patterns')
        if getattr(self.args, 'skip_test_examples', False):
            argv.append('--skip-test-examples')
        if getattr(self.args, 'skip_how_to_guides', False):
            argv.append('--skip-how-to-guides')
        if getattr(self.args, 'skip_config', False):
            argv.append('--skip-config')
        if getattr(self.args, 'skip_docs', False):
            argv.append('--skip-docs')

        # Call codebase_scraper with modified argv
        logger.debug(f"Calling codebase_scraper with argv: {argv}")
        original_argv = sys.argv
        try:
            sys.argv = argv
            return codebase_scraper.main()
        finally:
            sys.argv = original_argv

    def _route_pdf(self) -> int:
        """Route to PDF scraper (pdf_scraper.py)."""
        from skill_seekers.cli import pdf_scraper

        # Reconstruct argv for pdf_scraper
        argv = ['pdf_scraper']

        # Add PDF file
        file_path = self.source_info.parsed['file_path']
        argv.extend(['--pdf', file_path])

        # Add universal arguments
        self._add_common_args(argv)

        # Add PDF-specific arguments
        if getattr(self.args, 'ocr', False):
            argv.append('--ocr')
        if getattr(self.args, 'pages', None):
            argv.extend(['--pages', self.args.pages])

        # Call pdf_scraper with modified argv
        logger.debug(f"Calling pdf_scraper with argv: {argv}")
        original_argv = sys.argv
        try:
            sys.argv = argv
            return pdf_scraper.main()
        finally:
            sys.argv = original_argv

    def _route_config(self) -> int:
        """Route to unified scraper for config files (unified_scraper.py)."""
        from skill_seekers.cli import unified_scraper

        # Reconstruct argv for unified_scraper
        argv = ['unified_scraper']

        # Add config file
        config_path = self.source_info.parsed['config_path']
        argv.extend(['--config', config_path])

        # Add universal arguments (unified scraper supports most)
        self._add_common_args(argv)

        # Call unified_scraper with modified argv
        logger.debug(f"Calling unified_scraper with argv: {argv}")
        original_argv = sys.argv
        try:
            sys.argv = argv
            return unified_scraper.main()
        finally:
            sys.argv = original_argv

    def _add_common_args(self, argv: List[str]) -> None:
        """Add common/universal arguments to argv list.

        Args:
            argv: Argument list to append to
        """
        # Identity arguments
        if self.args.name:
            argv.extend(['--name', self.args.name])
        elif hasattr(self, 'source_info') and self.source_info:
            # Use suggested name from source detection
            argv.extend(['--name', self.source_info.suggested_name])

        if self.args.description:
            argv.extend(['--description', self.args.description])
        if self.args.output:
            argv.extend(['--output', self.args.output])

        # Enhancement arguments (consolidated to --enhance-level only)
        if self.args.enhance_level > 0:
            argv.extend(['--enhance-level', str(self.args.enhance_level)])
        if self.args.api_key:
            argv.extend(['--api-key', self.args.api_key])

        # Behavior arguments
        if self.args.dry_run:
            argv.append('--dry-run')
        if self.args.verbose:
            argv.append('--verbose')
        if self.args.quiet:
            argv.append('--quiet')

        # RAG arguments (NEW - universal!)
        if getattr(self.args, 'chunk_for_rag', False):
            argv.append('--chunk-for-rag')
        if getattr(self.args, 'chunk_size', None) and self.args.chunk_size != 512:
            argv.extend(['--chunk-size', str(self.args.chunk_size)])
        if getattr(self.args, 'chunk_overlap', None) and self.args.chunk_overlap != 50:
            argv.extend(['--chunk-overlap', str(self.args.chunk_overlap)])

        # Preset argument
        if getattr(self.args, 'preset', None):
            argv.extend(['--preset', self.args.preset])

        # Config file
        if self.args.config:
            argv.extend(['--config', self.args.config])

        # Advanced arguments
        if getattr(self.args, 'no_preserve_code_blocks', False):
            argv.append('--no-preserve-code-blocks')
        if getattr(self.args, 'no_preserve_paragraphs', False):
            argv.append('--no-preserve-paragraphs')
        if getattr(self.args, 'interactive_enhancement', False):
            argv.append('--interactive-enhancement')


def main() -> int:
    """Entry point for create command.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    from skill_seekers.cli.arguments.create import add_create_arguments

    # Parse arguments
    parser = argparse.ArgumentParser(
        prog='skill-seekers create',
        description='Create skill from any source (auto-detects type)',
        epilog="""
Examples:
  Web documentation:
    skill-seekers create https://docs.react.dev/
    skill-seekers create docs.vue.org --preset quick

  GitHub repository:
    skill-seekers create facebook/react
    skill-seekers create github.com/vuejs/vue --preset standard

  Local codebase:
    skill-seekers create ./my-project
    skill-seekers create /path/to/repo --preset comprehensive

  PDF file:
    skill-seekers create tutorial.pdf --ocr
    skill-seekers create guide.pdf --pages 1-10

  Config file (multi-source):
    skill-seekers create configs/react.json

Source type is auto-detected. Use --help-web, --help-github, etc. for source-specific options.
        """
    )

    # Add arguments in default mode (universal only)
    add_create_arguments(parser, mode='default')

    # Parse arguments
    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else (
        logging.WARNING if args.quiet else logging.INFO
    )
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s'
    )

    # Validate source provided
    if not args.source:
        parser.error("source is required")

    # Execute create command
    command = CreateCommand(args)
    return command.execute()


if __name__ == '__main__':
    sys.exit(main())
