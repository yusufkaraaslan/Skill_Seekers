#!/usr/bin/env python3
"""
Skill Seekers - Unified CLI Entry Point

Convert documentation, codebases, and repositories into AI skills.

Usage:
    skill-seekers <command> [options]

Commands:
    create               Create skill from any source (auto-detects type)
    enhance              AI-powered enhancement (auto: API or LOCAL mode)
    enhance-status       Check enhancement status (for background/daemon modes)
    package              Package skill into .zip file
    upload               Upload skill to target platform
    install              One-command workflow (scrape + enhance + package + upload)
    install-agent        Install skill to AI agent directories
    estimate             Estimate page count before scraping
    extract-test-examples Extract usage examples from test files
    resume               Resume interrupted scraping job
    config               Configure GitHub tokens, API keys, and settings
    doctor               Health check for dependencies and configuration

Examples:
    skill-seekers create https://react.dev
    skill-seekers create owner/repo
    skill-seekers create ./document.pdf
    skill-seekers create configs/unity-spine.json
    skill-seekers create configs/unity-spine.json --enhance-workflow unity-game-dev
    skill-seekers enhance output/react/
    skill-seekers package output/react/
"""

import argparse
import importlib
import sys

from skill_seekers.cli import __version__


# Command module mapping (command name -> module path)
COMMAND_MODULES = {
    # Skill creation — unified entry point for all 18 source types
    "create": "skill_seekers.cli.create_command",
    # Enhancement & packaging
    "enhance": "skill_seekers.cli.enhance_command",
    "enhance-status": "skill_seekers.cli.enhance_status",
    "package": "skill_seekers.cli.package_skill",
    "upload": "skill_seekers.cli.upload_skill",
    "install": "skill_seekers.cli.install_skill",
    "install-agent": "skill_seekers.cli.install_agent",
    # Utilities
    "estimate": "skill_seekers.cli.estimate_pages",
    "extract-test-examples": "skill_seekers.cli.test_example_extractor",
    "resume": "skill_seekers.cli.resume_command",
    "quality": "skill_seekers.cli.quality_metrics",
    # Configuration & workflows
    "config": "skill_seekers.cli.config_command",
    "doctor": "skill_seekers.cli.doctor",
    "workflows": "skill_seekers.cli.workflows_command",
    "sync-config": "skill_seekers.cli.sync_config",
    # Advanced (less common)
    "stream": "skill_seekers.cli.streaming_ingest",
    "update": "skill_seekers.cli.incremental_updater",
    "multilang": "skill_seekers.cli.multilang_support",
}


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    from skill_seekers.cli.parsers import register_parsers

    parser = argparse.ArgumentParser(
        prog="skill-seekers",
        description="Convert documentation, GitHub repos, and PDFs into AI skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create skill from documentation (auto-detects source type)
  skill-seekers create https://docs.react.dev --name react

  # Create skill from GitHub repository
  skill-seekers create microsoft/TypeScript --name typescript

  # Create skill from PDF file
  skill-seekers create ./documentation.pdf --name mydocs

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

    DEPRECATED: Use ExecutionContext instead. This function is kept for
    backward compatibility and will be removed in a future version.

    Args:
        command: Command name
        args: Parsed arguments namespace

    Returns:
        List of command-line arguments for the command module
    """
    import warnings

    warnings.warn(
        "_reconstruct_argv is deprecated. Use ExecutionContext instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    argv = [f"{command}_command.py"]

    # Convert args to sys.argv format
    for key, value in vars(args).items():
        if key == "command":
            continue

        # Handle internal/progressive help flags for create command
        # Convert _help_web to --help-web etc.
        if key.startswith("_help_"):
            if value:
                # Convert _help_web -> --help-web
                help_flag = key.replace("_help_", "help-")
                argv.append(f"--{help_flag}")
            continue

        # Handle positional arguments (no -- prefix)
        if key in [
            "source",  # create command
            "directory",
            "file",
            "job_id",
            "skill_directory",
            "zip_file",
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
    if argv is None:
        argv = sys.argv[1:]

    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    # Note: ExecutionContext is initialized by individual commands (e.g., create_command,
    # enhance_command) with the correct config_path and source_info. Do NOT initialize
    # it here — commands need to set config_path which requires source detection first.

    # Get command module
    module_name = COMMAND_MODULES.get(args.command)
    if not module_name:
        print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
        parser.print_help()
        return 1

    # create command: call directly with parsed args (no argv reconstruction)
    if args.command == "create":
        # Handle --help-* flags before execute (no source needed for help)
        from skill_seekers.cli.arguments.create import add_create_arguments

        help_modes = {
            "_help_web": "web",
            "_help_github": "github",
            "_help_local": "local",
            "_help_pdf": "pdf",
            "_help_word": "word",
            "_help_epub": "epub",
            "_help_video": "video",
            "_help_config": "config",
            "_help_advanced": "advanced",
            "_help_all": "all",
        }
        for attr, mode in help_modes.items():
            if getattr(args, attr, False):
                help_parser = argparse.ArgumentParser(
                    prog="skill-seekers create",
                    description=f"Create skill — {mode} options",
                    formatter_class=argparse.RawDescriptionHelpFormatter,
                )
                add_create_arguments(help_parser, mode=mode)
                help_parser.print_help()
                return 0

        from skill_seekers.cli.create_command import CreateCommand

        command = CreateCommand(args)
        return command.execute()

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


if __name__ == "__main__":
    sys.exit(main())
