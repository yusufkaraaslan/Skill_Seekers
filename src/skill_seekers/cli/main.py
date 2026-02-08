#!/usr/bin/env python3
"""
Skill Seekers - Unified CLI Entry Point

Provides a git-style unified command-line interface for all Skill Seekers tools.

Usage:
    skill-seekers <command> [options]

Commands:
    config               Configure GitHub tokens, API keys, and settings
    scrape               Scrape documentation website
    github               Scrape GitHub repository
    pdf                  Extract from PDF file
    unified              Multi-source scraping (docs + GitHub + PDF)
    analyze              Analyze local codebase and extract code knowledge
    enhance              AI-powered enhancement (local, no API key)
    enhance-status       Check enhancement status (for background/daemon modes)
    package              Package skill into .zip file
    upload               Upload skill to Claude
    estimate             Estimate page count before scraping
    extract-test-examples Extract usage examples from test files
    install-agent        Install skill to AI agent directories
    resume               Resume interrupted scraping job

Examples:
    skill-seekers scrape --config configs/react.json
    skill-seekers github --repo microsoft/TypeScript
    skill-seekers unified --config configs/react_unified.json
    skill-seekers extract-test-examples tests/ --language python
    skill-seekers package output/react/
    skill-seekers install-agent output/react/ --agent cursor
"""

import argparse
import importlib
import sys
from pathlib import Path

from skill_seekers.cli import __version__


# Command module mapping (command name -> module path)
COMMAND_MODULES = {
    "config": "skill_seekers.cli.config_command",
    "scrape": "skill_seekers.cli.doc_scraper",
    "github": "skill_seekers.cli.github_scraper",
    "pdf": "skill_seekers.cli.pdf_scraper",
    "unified": "skill_seekers.cli.unified_scraper",
    "enhance": "skill_seekers.cli.enhance_skill_local",
    "enhance-status": "skill_seekers.cli.enhance_status",
    "package": "skill_seekers.cli.package_skill",
    "upload": "skill_seekers.cli.upload_skill",
    "estimate": "skill_seekers.cli.estimate_pages",
    "extract-test-examples": "skill_seekers.cli.test_example_extractor",
    "install-agent": "skill_seekers.cli.install_agent",
    "analyze": "skill_seekers.cli.codebase_scraper",
    "install": "skill_seekers.cli.install_skill",
    "resume": "skill_seekers.cli.resume_command",
    "stream": "skill_seekers.cli.streaming_ingest",
    "update": "skill_seekers.cli.incremental_updater",
    "multilang": "skill_seekers.cli.multilang_support",
    "quality": "skill_seekers.cli.quality_metrics",
}


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    from skill_seekers.cli.parsers import register_parsers

    parser = argparse.ArgumentParser(
        prog="skill-seekers",
        description="Convert documentation, GitHub repos, and PDFs into Claude AI skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape documentation
  skill-seekers scrape --config configs/react.json

  # Scrape GitHub repository
  skill-seekers github --repo microsoft/TypeScript --name typescript

  # Multi-source scraping (unified)
  skill-seekers unified --config configs/react_unified.json

  # AI-powered enhancement
  skill-seekers enhance output/react/

  # Package and upload
  skill-seekers package output/react/
  skill-seekers upload output/react.zip

For more information: https://github.com/yusufkaraaslan/Skill_Seekers
        """,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Create subparsers
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available Skill Seekers commands",
        help="Command to run",
    )

    # Register all subcommand parsers
    register_parsers(subparsers)

    return parser


def _reconstruct_argv(command: str, args: argparse.Namespace) -> list[str]:
    """Reconstruct sys.argv from args namespace for command module.

    Args:
        command: Command name
        args: Parsed arguments namespace

    Returns:
        List of command-line arguments for the command module
    """
    argv = [f"{command}_command.py"]

    # Convert args to sys.argv format
    for key, value in vars(args).items():
        if key == "command":
            continue

        # Handle positional arguments (no -- prefix)
        if key in [
            "url",
            "directory",
            "file",
            "job_id",
            "skill_directory",
            "zip_file",
            "config",
            "input_file",
        ]:
            if value is not None and value != "":
                argv.append(str(value))
            continue

        # Handle flags and options
        arg_name = f"--{key.replace('_', '-')}"

        if isinstance(value, bool):
            if value:
                argv.append(arg_name)
        elif isinstance(value, list):
            for item in value:
                argv.extend([arg_name, str(item)])
        elif value is not None:
            argv.extend([arg_name, str(value)])

    return argv


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the unified CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    # Get command module
    module_name = COMMAND_MODULES.get(args.command)
    if not module_name:
        print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
        parser.print_help()
        return 1

    # Special handling for 'analyze' command (has post-processing)
    if args.command == "analyze":
        return _handle_analyze_command(args)

    # Standard delegation for all other commands
    try:
        # Import and execute command module
        module = importlib.import_module(module_name)

        # Reconstruct sys.argv for command module
        original_argv = sys.argv.copy()
        sys.argv = _reconstruct_argv(args.command, args)

        # Execute command
        try:
            result = module.main()
            return result if result is not None else 0
        finally:
            sys.argv = original_argv

    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        error_msg = str(e) if str(e) else f"{type(e).__name__} occurred"
        print(f"Error: {error_msg}", file=sys.stderr)

        # Show traceback in verbose mode
        import traceback

        if hasattr(args, "verbose") and getattr(args, "verbose", False):
            traceback.print_exc()

        return 1


def _handle_analyze_command(args: argparse.Namespace) -> int:
    """Handle analyze command with special post-processing logic.

    Args:
        args: Parsed arguments

    Returns:
        Exit code
    """
    from skill_seekers.cli.codebase_scraper import main as analyze_main

    # Reconstruct sys.argv for analyze command
    original_argv = sys.argv.copy()
    sys.argv = ["codebase_scraper.py", "--directory", args.directory]

    if args.output:
        sys.argv.extend(["--output", args.output])

    # Handle preset flags (depth and features)
    if args.quick:
        sys.argv.extend(
            [
                "--depth",
                "surface",
                "--skip-patterns",
                "--skip-test-examples",
                "--skip-how-to-guides",
                "--skip-config-patterns",
            ]
        )
    elif args.comprehensive:
        sys.argv.extend(["--depth", "full"])
    elif args.depth:
        sys.argv.extend(["--depth", args.depth])

    # Determine enhance_level
    if args.enhance_level is not None:
        enhance_level = args.enhance_level
    elif args.quick:
        enhance_level = 0
    elif args.enhance:
        try:
            from skill_seekers.cli.config_manager import get_config_manager

            config = get_config_manager()
            enhance_level = config.get_default_enhance_level()
        except Exception:
            enhance_level = 1
    else:
        enhance_level = 0

    sys.argv.extend(["--enhance-level", str(enhance_level)])

    # Pass through remaining arguments
    if args.languages:
        sys.argv.extend(["--languages", args.languages])
    if args.file_patterns:
        sys.argv.extend(["--file-patterns", args.file_patterns])
    if args.skip_api_reference:
        sys.argv.append("--skip-api-reference")
    if args.skip_dependency_graph:
        sys.argv.append("--skip-dependency-graph")
    if args.skip_patterns:
        sys.argv.append("--skip-patterns")
    if args.skip_test_examples:
        sys.argv.append("--skip-test-examples")
    if args.skip_how_to_guides:
        sys.argv.append("--skip-how-to-guides")
    if args.skip_config_patterns:
        sys.argv.append("--skip-config-patterns")
    if args.skip_docs:
        sys.argv.append("--skip-docs")
    if args.no_comments:
        sys.argv.append("--no-comments")
    if args.verbose:
        sys.argv.append("--verbose")

    try:
        result = analyze_main() or 0

        # Enhance SKILL.md if enhance_level >= 1
        if result == 0 and enhance_level >= 1:
            skill_dir = Path(args.output)
            skill_md = skill_dir / "SKILL.md"

            if skill_md.exists():
                print("\n" + "=" * 60)
                print(f"ENHANCING SKILL.MD WITH AI (Level {enhance_level})")
                print("=" * 60 + "\n")

                try:
                    from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

                    enhancer = LocalSkillEnhancer(str(skill_dir), force=True)
                    success = enhancer.run(headless=True, timeout=600)

                    if success:
                        print("\n✅ SKILL.md enhancement complete!")
                        with open(skill_md) as f:
                            lines = len(f.readlines())
                        print(f"   Enhanced SKILL.md: {lines} lines")
                    else:
                        print("\n⚠️  SKILL.md enhancement did not complete")
                        print("   You can retry with: skill-seekers enhance " + str(skill_dir))
                except Exception as e:
                    print(f"\n⚠️  SKILL.md enhancement failed: {e}")
                    print("   You can retry with: skill-seekers enhance " + str(skill_dir))
            else:
                print(f"\n⚠️  SKILL.md not found at {skill_md}, skipping enhancement")

        return result
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    sys.exit(main())
