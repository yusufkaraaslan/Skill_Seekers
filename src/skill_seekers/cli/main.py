#!/usr/bin/env python3
"""
Skill Seekers - Unified CLI Entry Point

Convert documentation, codebases, and repositories into AI skills.

Usage:
    skill-seekers <command> [options]

Commands:
    create               Create skill from any source (auto-detects type)
    unified              Multi-source scraping from uni_skill_config
    analyze              Analyze local codebase and extract code knowledge
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
import os
import sys
from pathlib import Path

from skill_seekers.cli import __version__


# Command module mapping (command name -> module path)
COMMAND_MODULES = {
    # Skill creation — unified entry point for all 17 source types
    "create": "skill_seekers.cli.create_command",
    # Multi-source config orchestrator
    "unified": "skill_seekers.cli.unified_scraper",
    # Enhancement & packaging
    "enhance": "skill_seekers.cli.enhance_command",
    "enhance-status": "skill_seekers.cli.enhance_status",
    "package": "skill_seekers.cli.package_skill",
    "upload": "skill_seekers.cli.upload_skill",
    "install": "skill_seekers.cli.install_skill",
    "install-agent": "skill_seekers.cli.install_agent",
    # Analysis & utilities
    "analyze": "skill_seekers.cli.codebase_scraper",
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
    # Special handling for analyze --preset-list (no directory required)
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) >= 2 and argv[0] == "analyze" and "--preset-list" in argv:
        from skill_seekers.cli.codebase_scraper import main as analyze_main

        original_argv = sys.argv.copy()
        sys.argv = ["codebase_scraper.py", "--preset-list"]
        try:
            return analyze_main() or 0
        finally:
            sys.argv = original_argv

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

    # Determine enhance_level (simplified - use default or override)
    enhance_level = getattr(args, "enhance_level", 2)  # Default is 2
    if getattr(args, "quick", False):
        enhance_level = 0  # Quick mode disables enhancement

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
    if getattr(args, "quiet", False):
        sys.argv.append("--quiet")
    if getattr(args, "dry_run", False):
        sys.argv.append("--dry-run")
    if getattr(args, "preset", None):
        sys.argv.extend(["--preset", args.preset])
    if getattr(args, "name", None):
        sys.argv.extend(["--name", args.name])
    if getattr(args, "description", None):
        sys.argv.extend(["--description", args.description])
    if getattr(args, "api_key", None):
        sys.argv.extend(["--api-key", args.api_key])
    # Enhancement Workflow arguments
    if getattr(args, "enhance_workflow", None):
        for wf in args.enhance_workflow:
            sys.argv.extend(["--enhance-workflow", wf])
    if getattr(args, "enhance_stage", None):
        for stage in args.enhance_stage:
            sys.argv.extend(["--enhance-stage", stage])
    if getattr(args, "var", None):
        for var in args.var:
            sys.argv.extend(["--var", var])
    if getattr(args, "workflow_dry_run", False):
        sys.argv.append("--workflow-dry-run")

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
                    from skill_seekers.cli.enhance_command import (
                        _is_root,
                        _pick_mode,
                        _run_api_mode,
                        _run_local_mode,
                    )
                    import argparse as _ap

                    # Populate from ExecutionContext if available
                    try:
                        from skill_seekers.cli.execution_context import ExecutionContext as _EC

                        _ctx = _EC.get()
                        _agent = _ctx.enhancement.agent
                        _agent_cmd = _ctx.enhancement.agent_cmd
                        _api_key = _ctx.enhancement.api_key
                        _timeout = _ctx.enhancement.timeout
                    except (RuntimeError, Exception):
                        _agent = None
                        _agent_cmd = None
                        _api_key = None
                        _timeout = 2700

                    _fake_args = _ap.Namespace(
                        skill_directory=str(skill_dir),
                        target=None,
                        api_key=_api_key,
                        dry_run=False,
                        agent=_agent,
                        agent_cmd=_agent_cmd,
                        interactive_enhancement=False,
                        background=False,
                        daemon=False,
                        no_force=False,
                        timeout=_timeout,
                    )
                    _mode, _target = _pick_mode(_fake_args)

                    if _mode == "api":
                        print(f"\n🤖 Enhancement mode: API ({_target})")
                        success = _run_api_mode(_fake_args, _target) == 0
                    elif _is_root():
                        print("\n⚠️  Skipping SKILL.md enhancement: running as root")
                        print("   Set ANTHROPIC_API_KEY / GOOGLE_API_KEY to enable API mode")
                        success = False
                    else:
                        agent_name = (
                            os.environ.get("SKILL_SEEKER_AGENT", "claude").strip() or "claude"
                        )
                        print(f"\n🤖 Enhancement mode: LOCAL ({agent_name})")
                        success = _run_local_mode(_fake_args) == 0

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
