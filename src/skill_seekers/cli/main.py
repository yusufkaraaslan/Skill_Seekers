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
import sys
from pathlib import Path

from skill_seekers.cli import __version__


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
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

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available Skill Seekers commands",
        help="Command to run",
    )

    # === config subcommand ===
    config_parser = subparsers.add_parser(
        "config",
        help="Configure GitHub tokens, API keys, and settings",
        description="Interactive configuration wizard",
    )
    config_parser.add_argument(
        "--github", action="store_true", help="Go directly to GitHub token setup"
    )
    config_parser.add_argument(
        "--api-keys", action="store_true", help="Go directly to API keys setup"
    )
    config_parser.add_argument(
        "--show", action="store_true", help="Show current configuration and exit"
    )
    config_parser.add_argument("--test", action="store_true", help="Test connections and exit")

    # === scrape subcommand ===
    scrape_parser = subparsers.add_parser(
        "scrape",
        help="Scrape documentation website",
        description="Scrape documentation website and generate skill",
    )
    scrape_parser.add_argument("url", nargs="?", help="Documentation URL (positional argument)")
    scrape_parser.add_argument("--config", help="Config JSON file")
    scrape_parser.add_argument("--name", help="Skill name")
    scrape_parser.add_argument("--description", help="Skill description")
    scrape_parser.add_argument(
        "--max-pages", type=int, dest="max_pages", help="Maximum pages to scrape (override config)"
    )
    scrape_parser.add_argument(
        "--skip-scrape", action="store_true", help="Skip scraping, use cached data"
    )
    scrape_parser.add_argument("--enhance", action="store_true", help="AI enhancement (API)")
    scrape_parser.add_argument(
        "--enhance-local", action="store_true", help="AI enhancement (local)"
    )
    scrape_parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    scrape_parser.add_argument(
        "--async", dest="async_mode", action="store_true", help="Use async scraping"
    )
    scrape_parser.add_argument("--workers", type=int, help="Number of async workers")

    # === github subcommand ===
    github_parser = subparsers.add_parser(
        "github",
        help="Scrape GitHub repository",
        description="Scrape GitHub repository and generate skill",
    )
    github_parser.add_argument("--config", help="Config JSON file")
    github_parser.add_argument("--repo", help="GitHub repo (owner/repo)")
    github_parser.add_argument("--name", help="Skill name")
    github_parser.add_argument("--description", help="Skill description")
    github_parser.add_argument("--enhance", action="store_true", help="AI enhancement (API)")
    github_parser.add_argument(
        "--enhance-local", action="store_true", help="AI enhancement (local)"
    )
    github_parser.add_argument("--api-key", type=str, help="Anthropic API key for --enhance")
    github_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Non-interactive mode (fail fast on rate limits)",
    )
    github_parser.add_argument("--profile", type=str, help="GitHub profile name from config")

    # === pdf subcommand ===
    pdf_parser = subparsers.add_parser(
        "pdf",
        help="Extract from PDF file",
        description="Extract content from PDF and generate skill",
    )
    pdf_parser.add_argument("--config", help="Config JSON file")
    pdf_parser.add_argument("--pdf", help="PDF file path")
    pdf_parser.add_argument("--name", help="Skill name")
    pdf_parser.add_argument("--description", help="Skill description")
    pdf_parser.add_argument("--from-json", help="Build from extracted JSON")

    # === unified subcommand ===
    unified_parser = subparsers.add_parser(
        "unified",
        help="Multi-source scraping (docs + GitHub + PDF)",
        description="Combine multiple sources into one skill",
    )
    unified_parser.add_argument("--config", required=True, help="Unified config JSON file")
    unified_parser.add_argument("--merge-mode", help="Merge mode (rule-based, claude-enhanced)")
    unified_parser.add_argument(
        "--fresh", action="store_true", help="Clear existing data and start fresh"
    )
    unified_parser.add_argument("--dry-run", action="store_true", help="Dry run mode")

    # === enhance subcommand ===
    enhance_parser = subparsers.add_parser(
        "enhance",
        help="AI-powered enhancement (local, no API key)",
        description="Enhance SKILL.md using Claude Code (local)",
    )
    enhance_parser.add_argument("skill_directory", help="Skill directory path")
    enhance_parser.add_argument("--background", action="store_true", help="Run in background")
    enhance_parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    enhance_parser.add_argument(
        "--no-force", action="store_true", help="Disable force mode (enable confirmations)"
    )
    enhance_parser.add_argument("--timeout", type=int, default=600, help="Timeout in seconds")

    # === enhance-status subcommand ===
    enhance_status_parser = subparsers.add_parser(
        "enhance-status",
        help="Check enhancement status (for background/daemon modes)",
        description="Monitor background enhancement processes",
    )
    enhance_status_parser.add_argument("skill_directory", help="Skill directory path")
    enhance_status_parser.add_argument(
        "--watch", "-w", action="store_true", help="Watch in real-time"
    )
    enhance_status_parser.add_argument("--json", action="store_true", help="JSON output")
    enhance_status_parser.add_argument(
        "--interval", type=int, default=2, help="Watch interval in seconds"
    )

    # === package subcommand ===
    package_parser = subparsers.add_parser(
        "package",
        help="Package skill into .zip file",
        description="Package skill directory into uploadable .zip",
    )
    package_parser.add_argument("skill_directory", help="Skill directory path")
    package_parser.add_argument("--no-open", action="store_true", help="Don't open output folder")
    package_parser.add_argument("--upload", action="store_true", help="Auto-upload after packaging")

    # === upload subcommand ===
    upload_parser = subparsers.add_parser(
        "upload",
        help="Upload skill to Claude",
        description="Upload .zip file to Claude via Anthropic API",
    )
    upload_parser.add_argument("zip_file", help=".zip file to upload")
    upload_parser.add_argument("--api-key", help="Anthropic API key")

    # === estimate subcommand ===
    estimate_parser = subparsers.add_parser(
        "estimate",
        help="Estimate page count before scraping",
        description="Estimate total pages for documentation scraping",
    )
    estimate_parser.add_argument("config", nargs="?", help="Config JSON file")
    estimate_parser.add_argument("--all", action="store_true", help="List all available configs")
    estimate_parser.add_argument("--max-discovery", type=int, help="Max pages to discover")

    # === extract-test-examples subcommand ===
    test_examples_parser = subparsers.add_parser(
        "extract-test-examples",
        help="Extract usage examples from test files",
        description="Analyze test files to extract real API usage patterns",
    )
    test_examples_parser.add_argument(
        "directory", nargs="?", help="Directory containing test files"
    )
    test_examples_parser.add_argument("--file", help="Single test file to analyze")
    test_examples_parser.add_argument(
        "--language", help="Filter by programming language (python, javascript, etc.)"
    )
    test_examples_parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.5,
        help="Minimum confidence threshold (0.0-1.0, default: 0.5)",
    )
    test_examples_parser.add_argument(
        "--max-per-file", type=int, default=10, help="Maximum examples per file (default: 10)"
    )
    test_examples_parser.add_argument("--json", action="store_true", help="Output JSON format")
    test_examples_parser.add_argument(
        "--markdown", action="store_true", help="Output Markdown format"
    )

    # === install-agent subcommand ===
    install_agent_parser = subparsers.add_parser(
        "install-agent",
        help="Install skill to AI agent directories",
        description="Copy skill to agent-specific installation directories",
    )
    install_agent_parser.add_argument(
        "skill_directory", help="Skill directory path (e.g., output/react/)"
    )
    install_agent_parser.add_argument(
        "--agent",
        required=True,
        help="Agent name (claude, cursor, vscode, amp, goose, opencode, all)",
    )
    install_agent_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing installation without asking"
    )
    install_agent_parser.add_argument(
        "--dry-run", action="store_true", help="Preview installation without making changes"
    )

    # === analyze subcommand ===
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze local codebase and extract code knowledge",
        description="Standalone codebase analysis with C3.x features (patterns, tests, guides)",
    )
    analyze_parser.add_argument("--directory", required=True, help="Directory to analyze")
    analyze_parser.add_argument(
        "--output", default="output/codebase/", help="Output directory (default: output/codebase/)"
    )
    analyze_parser.add_argument(
        "--quick", action="store_true", help="Quick analysis (1-2 min, basic features only)"
    )
    analyze_parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Comprehensive analysis (20-60 min, all features + AI)",
    )
    analyze_parser.add_argument(
        "--depth",
        choices=["surface", "deep", "full"],
        help="Analysis depth (deprecated - use --quick or --comprehensive instead)",
    )
    analyze_parser.add_argument(
        "--languages", help="Comma-separated languages (e.g., Python,JavaScript,C++)"
    )
    analyze_parser.add_argument("--file-patterns", help="Comma-separated file patterns")
    analyze_parser.add_argument(
        "--enhance",
        action="store_true",
        help="Enable AI enhancement (default level 1 = SKILL.md only)",
    )
    analyze_parser.add_argument(
        "--enhance-level",
        type=int,
        choices=[0, 1, 2, 3],
        default=None,
        help="AI enhancement level: 0=off, 1=SKILL.md only (default), 2=+Architecture+Config, 3=full",
    )
    analyze_parser.add_argument("--skip-api-reference", action="store_true", help="Skip API docs")
    analyze_parser.add_argument(
        "--skip-dependency-graph", action="store_true", help="Skip dep graph"
    )
    analyze_parser.add_argument(
        "--skip-patterns", action="store_true", help="Skip pattern detection"
    )
    analyze_parser.add_argument(
        "--skip-test-examples", action="store_true", help="Skip test examples"
    )
    analyze_parser.add_argument("--skip-how-to-guides", action="store_true", help="Skip guides")
    analyze_parser.add_argument("--skip-config-patterns", action="store_true", help="Skip config")
    analyze_parser.add_argument(
        "--skip-docs", action="store_true", help="Skip project docs (README, docs/)"
    )
    analyze_parser.add_argument("--no-comments", action="store_true", help="Skip comments")
    analyze_parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    # === install subcommand ===
    install_parser = subparsers.add_parser(
        "install",
        help="Complete workflow: fetch → scrape → enhance → package → upload",
        description="One-command skill installation (AI enhancement MANDATORY)",
    )
    install_parser.add_argument(
        "--config",
        required=True,
        help="Config name (e.g., 'react') or path (e.g., 'configs/custom.json')",
    )
    install_parser.add_argument(
        "--destination", default="output", help="Output directory (default: output/)"
    )
    install_parser.add_argument(
        "--no-upload", action="store_true", help="Skip automatic upload to Claude"
    )
    install_parser.add_argument(
        "--unlimited", action="store_true", help="Remove page limits during scraping"
    )
    install_parser.add_argument(
        "--dry-run", action="store_true", help="Preview workflow without executing"
    )

    # === resume subcommand ===
    resume_parser = subparsers.add_parser(
        "resume",
        help="Resume interrupted scraping job",
        description="Continue from saved progress checkpoint",
    )
    resume_parser.add_argument(
        "job_id", nargs="?", help="Job ID to resume (or use --list to see available jobs)"
    )
    resume_parser.add_argument("--list", action="store_true", help="List all resumable jobs")
    resume_parser.add_argument("--clean", action="store_true", help="Clean up old progress files")

    return parser


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

    # Delegate to the appropriate tool
    try:
        if args.command == "config":
            from skill_seekers.cli.config_command import main as config_main

            sys.argv = ["config_command.py"]
            if args.github:
                sys.argv.append("--github")
            if args.api_keys:
                sys.argv.append("--api-keys")
            if args.show:
                sys.argv.append("--show")
            if args.test:
                sys.argv.append("--test")
            return config_main() or 0

        elif args.command == "scrape":
            from skill_seekers.cli.doc_scraper import main as scrape_main

            # Convert args namespace to sys.argv format for doc_scraper
            sys.argv = ["doc_scraper.py"]
            # Add positional URL if provided (positional arg has priority)
            if hasattr(args, "url") and args.url:
                sys.argv.append(args.url)
            if args.config:
                sys.argv.extend(["--config", args.config])
            if args.name:
                sys.argv.extend(["--name", args.name])
            if args.description:
                sys.argv.extend(["--description", args.description])
            if hasattr(args, "max_pages") and args.max_pages:
                sys.argv.extend(["--max-pages", str(args.max_pages)])
            if args.skip_scrape:
                sys.argv.append("--skip-scrape")
            if args.enhance:
                sys.argv.append("--enhance")
            if args.enhance_local:
                sys.argv.append("--enhance-local")
            if args.dry_run:
                sys.argv.append("--dry-run")
            if args.async_mode:
                sys.argv.append("--async")
            if args.workers:
                sys.argv.extend(["--workers", str(args.workers)])
            return scrape_main() or 0

        elif args.command == "github":
            from skill_seekers.cli.github_scraper import main as github_main

            sys.argv = ["github_scraper.py"]
            if args.config:
                sys.argv.extend(["--config", args.config])
            if args.repo:
                sys.argv.extend(["--repo", args.repo])
            if args.name:
                sys.argv.extend(["--name", args.name])
            if args.description:
                sys.argv.extend(["--description", args.description])
            if args.enhance:
                sys.argv.append("--enhance")
            if args.enhance_local:
                sys.argv.append("--enhance-local")
            if args.api_key:
                sys.argv.extend(["--api-key", args.api_key])
            if args.non_interactive:
                sys.argv.append("--non-interactive")
            if args.profile:
                sys.argv.extend(["--profile", args.profile])
            return github_main() or 0

        elif args.command == "pdf":
            from skill_seekers.cli.pdf_scraper import main as pdf_main

            sys.argv = ["pdf_scraper.py"]
            if args.config:
                sys.argv.extend(["--config", args.config])
            if args.pdf:
                sys.argv.extend(["--pdf", args.pdf])
            if args.name:
                sys.argv.extend(["--name", args.name])
            if args.description:
                sys.argv.extend(["--description", args.description])
            if args.from_json:
                sys.argv.extend(["--from-json", args.from_json])
            return pdf_main() or 0

        elif args.command == "unified":
            from skill_seekers.cli.unified_scraper import main as unified_main

            sys.argv = ["unified_scraper.py", "--config", args.config]
            if args.merge_mode:
                sys.argv.extend(["--merge-mode", args.merge_mode])
            if args.fresh:
                sys.argv.append("--fresh")
            if args.dry_run:
                sys.argv.append("--dry-run")
            return unified_main() or 0

        elif args.command == "enhance":
            from skill_seekers.cli.enhance_skill_local import main as enhance_main

            sys.argv = ["enhance_skill_local.py", args.skill_directory]
            if args.background:
                sys.argv.append("--background")
            if args.daemon:
                sys.argv.append("--daemon")
            if args.no_force:
                sys.argv.append("--no-force")
            if args.timeout:
                sys.argv.extend(["--timeout", str(args.timeout)])
            return enhance_main() or 0

        elif args.command == "enhance-status":
            from skill_seekers.cli.enhance_status import main as enhance_status_main

            sys.argv = ["enhance_status.py", args.skill_directory]
            if args.watch:
                sys.argv.append("--watch")
            if args.json:
                sys.argv.append("--json")
            if args.interval:
                sys.argv.extend(["--interval", str(args.interval)])
            return enhance_status_main() or 0

        elif args.command == "package":
            from skill_seekers.cli.package_skill import main as package_main

            sys.argv = ["package_skill.py", args.skill_directory]
            if args.no_open:
                sys.argv.append("--no-open")
            if args.upload:
                sys.argv.append("--upload")
            return package_main() or 0

        elif args.command == "upload":
            from skill_seekers.cli.upload_skill import main as upload_main

            sys.argv = ["upload_skill.py", args.zip_file]
            if args.api_key:
                sys.argv.extend(["--api-key", args.api_key])
            return upload_main() or 0

        elif args.command == "estimate":
            from skill_seekers.cli.estimate_pages import main as estimate_main

            sys.argv = ["estimate_pages.py"]
            if args.all:
                sys.argv.append("--all")
            elif args.config:
                sys.argv.append(args.config)
            if args.max_discovery:
                sys.argv.extend(["--max-discovery", str(args.max_discovery)])
            return estimate_main() or 0

        elif args.command == "extract-test-examples":
            from skill_seekers.cli.test_example_extractor import main as test_examples_main

            sys.argv = ["test_example_extractor.py"]
            if args.directory:
                sys.argv.append(args.directory)
            if args.file:
                sys.argv.extend(["--file", args.file])
            if args.language:
                sys.argv.extend(["--language", args.language])
            if args.min_confidence:
                sys.argv.extend(["--min-confidence", str(args.min_confidence)])
            if args.max_per_file:
                sys.argv.extend(["--max-per-file", str(args.max_per_file)])
            if args.json:
                sys.argv.append("--json")
            if args.markdown:
                sys.argv.append("--markdown")
            return test_examples_main() or 0

        elif args.command == "analyze":
            from skill_seekers.cli.codebase_scraper import main as analyze_main

            sys.argv = ["codebase_scraper.py", "--directory", args.directory]

            if args.output:
                sys.argv.extend(["--output", args.output])

            # Handle preset flags (depth and features)
            if args.quick:
                # Quick = surface depth + skip advanced features + no AI
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
                # Comprehensive = full depth + all features (AI level is separate)
                sys.argv.extend(["--depth", "full"])
            elif args.depth:
                sys.argv.extend(["--depth", args.depth])

            # Determine enhance_level (independent of --comprehensive)
            # Priority: explicit --enhance-level > --enhance (uses config default) > --quick (level 0) > 0
            if args.enhance_level is not None:
                enhance_level = args.enhance_level
            elif args.quick:
                enhance_level = 0  # Quick mode disables AI
            elif args.enhance:
                # Use default from config (default: 1)
                try:
                    from skill_seekers.cli.config_manager import get_config_manager

                    config = get_config_manager()
                    enhance_level = config.get_default_enhance_level()
                except Exception:
                    enhance_level = 1  # Fallback to level 1
            else:
                enhance_level = 0  # Default: no AI

            # Pass enhance_level to codebase_scraper
            sys.argv.extend(["--enhance-level", str(enhance_level)])

            if args.languages:
                sys.argv.extend(["--languages", args.languages])
            if args.file_patterns:
                sys.argv.extend(["--file-patterns", args.file_patterns])

            # Pass through skip flags
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
                        # Use headless mode (runs claude directly, waits for completion)
                        success = enhancer.run(
                            headless=True,
                            timeout=600,  # 10 minute timeout
                        )

                        if success:
                            print("\n✅ SKILL.md enhancement complete!")
                            # Re-read line count
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

        elif args.command == "install-agent":
            from skill_seekers.cli.install_agent import main as install_agent_main

            sys.argv = ["install_agent.py", args.skill_directory, "--agent", args.agent]
            if args.force:
                sys.argv.append("--force")
            if args.dry_run:
                sys.argv.append("--dry-run")
            return install_agent_main() or 0

        elif args.command == "install":
            from skill_seekers.cli.install_skill import main as install_main

            sys.argv = ["install_skill.py"]
            if args.config:
                sys.argv.extend(["--config", args.config])
            if args.destination:
                sys.argv.extend(["--destination", args.destination])
            if args.no_upload:
                sys.argv.append("--no-upload")
            if args.unlimited:
                sys.argv.append("--unlimited")
            if args.dry_run:
                sys.argv.append("--dry-run")
            return install_main() or 0

        elif args.command == "resume":
            from skill_seekers.cli.resume_command import main as resume_main

            sys.argv = ["resume_command.py"]
            if args.job_id:
                sys.argv.append(args.job_id)
            if args.list:
                sys.argv.append("--list")
            if args.clean:
                sys.argv.append("--clean")
            return resume_main() or 0

        else:
            print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        # Provide helpful error message
        error_msg = str(e) if str(e) else f"{type(e).__name__} occurred"
        print(f"Error: {error_msg}", file=sys.stderr)

        # Show traceback in verbose mode (if -v flag exists in args)
        import traceback

        if hasattr(args, "verbose") and getattr(args, "verbose", False):
            traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(main())
