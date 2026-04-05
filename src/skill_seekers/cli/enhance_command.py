#!/usr/bin/env python3
"""
Smart Enhancement Dispatcher

Routes `skill-seekers enhance` to the correct backend:

  API mode  — when an API key is available (Claude/Gemini/OpenAI).
              Calls enhance_skill.py which uses platform adaptors.

  LOCAL mode — when no API key is found.
              Calls LocalSkillEnhancer from enhance_skill_local.py.

Decision priority:
  1. Explicit --target flag → API mode with that platform.
  2. Config ai_enhancement.default_agent + matching env key → API mode.
  3. Auto-detect from env vars: ANTHROPIC_API_KEY → claude,
     GOOGLE_API_KEY → gemini, OPENAI_API_KEY → openai.
  4. No API keys → LOCAL mode (Claude Code CLI).
  5. LOCAL mode + running as root → clear error (Claude Code refuses root).
"""

import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_root() -> bool:
    """Return True if the current process is running as root (UID 0)."""
    try:
        return os.getuid() == 0
    except AttributeError:
        return False  # Windows has no getuid


def _get_api_keys() -> dict[str, str | None]:
    """Collect API keys from environment."""
    return {
        "claude": (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")),
        "gemini": os.environ.get("GOOGLE_API_KEY"),
        "openai": os.environ.get("OPENAI_API_KEY"),
    }


def _get_config_default_agent() -> str | None:
    """Read ai_enhancement.default_agent from config manager (best-effort)."""
    try:
        from skill_seekers.cli.config_manager import get_config_manager

        return get_config_manager().get_default_agent()
    except Exception:
        return None


def _pick_mode(args) -> tuple[str, str | None]:
    """Decide between 'api' and 'local' mode.

    Returns:
        (mode, target) — mode is "api" or "local";
                         target is the platform name ("claude", "gemini", "openai")
                         or None for local mode.
    """
    api_keys = _get_api_keys()

    # 1. Explicit --target flag always forces API mode.
    target = getattr(args, "target", None)
    if target:
        return "api", target

    # 2. Config default_agent preference (if a matching key is available).
    config_agent = _get_config_default_agent()
    if config_agent in ("claude", "gemini", "openai") and api_keys.get(config_agent):
        return "api", config_agent

    # 3. Auto-detect from environment variables.
    #    Priority: Claude > Gemini > OpenAI (Claude is Anthropic's native platform).
    if api_keys["claude"]:
        return "api", "claude"
    if api_keys["gemini"]:
        return "api", "gemini"
    if api_keys["openai"]:
        return "api", "openai"

    # 4. No API keys found → LOCAL mode.
    return "local", None


# ---------------------------------------------------------------------------
# API mode runner
# ---------------------------------------------------------------------------


def _run_api_mode(args, target: str) -> int:
    """Delegate to enhance_skill.py (platform adaptor path)."""
    from skill_seekers.cli.enhance_skill import main as enhance_api_main

    api_keys = _get_api_keys()
    api_key = getattr(args, "api_key", None)
    if not api_key:
        # Explicit key > env var for the selected platform
        env_map = {
            "claude": api_keys["claude"],
            "gemini": api_keys["gemini"],
            "openai": api_keys["openai"],
        }
        api_key = env_map.get(target)

    # Reconstruct sys.argv for enhance_skill.main()
    argv = [
        "enhance_skill.py",
        str(args.skill_directory),
        "--target",
        target,
    ]
    if api_key:
        argv.extend(["--api-key", api_key])
    if getattr(args, "dry_run", False):
        argv.append("--dry-run")

    original_argv = sys.argv.copy()
    sys.argv = argv
    try:
        enhance_api_main()
        return 0
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 0
    finally:
        sys.argv = original_argv


# ---------------------------------------------------------------------------
# LOCAL mode runner
# ---------------------------------------------------------------------------


def _run_local_mode(args) -> int:
    """Delegate to LocalSkillEnhancer from enhance_skill_local.py."""
    from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

    try:
        enhancer = LocalSkillEnhancer(
            args.skill_directory,
            force=not getattr(args, "no_force", False),
            agent=getattr(args, "agent", None),
            agent_cmd=getattr(args, "agent_cmd", None),
        )
    except ValueError as exc:
        print(f"❌ Error: {exc}")
        return 1

    interactive = getattr(args, "interactive_enhancement", False)
    headless = not interactive
    success = enhancer.run(
        headless=headless,
        timeout=getattr(args, "timeout", 600),
        background=getattr(args, "background", False),
        daemon=getattr(args, "daemon", False),
    )
    return 0 if success else 1


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> int:
    import argparse

    from skill_seekers.cli.arguments.enhance import add_enhance_arguments

    parser = argparse.ArgumentParser(
        description=(
            "Enhance SKILL.md using AI. "
            "Automatically selects API mode (Gemini/OpenAI/Claude API) when an API key "
            "is available, or falls back to LOCAL mode (Claude Code CLI)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Mode selection (automatic — no flags required):
  API mode  : Set ANTHROPIC_API_KEY, GOOGLE_API_KEY, or OPENAI_API_KEY.
              Or use --target to force a platform.
  LOCAL mode: Falls back when no API keys are found. Requires Claude Code CLI.
              Does NOT work as root (Docker/VPS) — use API mode instead.

Examples:
  # Auto-detect (API mode if any key is set, else LOCAL)
  skill-seekers enhance output/react/

  # Force Gemini API
  skill-seekers enhance output/react/ --target gemini

  # Force Claude API with explicit key
  skill-seekers enhance output/react/ --target claude --api-key sk-ant-...

  # LOCAL mode options
  skill-seekers enhance output/react/ --background
  skill-seekers enhance output/react/ --timeout 1200

  # Dry run (preview only)
  skill-seekers enhance output/react/ --dry-run
""",
    )
    add_enhance_arguments(parser)
    args = parser.parse_args()

    # Validate skill directory
    skill_dir = Path(args.skill_directory)
    if not skill_dir.exists():
        print(f"❌ Error: Directory not found: {skill_dir}")
        return 1
    if not skill_dir.is_dir():
        print(f"❌ Error: Not a directory: {skill_dir}")
        return 1

    mode, target = _pick_mode(args)

    # Dry run — just show what would happen
    if getattr(args, "dry_run", False):
        print("🔍 DRY RUN MODE")
        print(f"   Skill directory : {skill_dir}")
        print(f"   Selected mode   : {mode.upper()}")
        if mode == "api":
            print(f"   Platform        : {target}")
        else:
            agent = getattr(args, "agent", None) or os.environ.get("SKILL_SEEKER_AGENT", "claude")
            print(f"   Agent           : {agent}")
        refs_dir = skill_dir / "references"
        if refs_dir.exists():
            ref_files = list(refs_dir.glob("*.md"))
            print(f"   Reference files : {len(ref_files)}")
        print("\nTo actually run: remove --dry-run")
        return 0

    if mode == "api":
        print(f"🤖 Enhancement mode: API ({target})")
        return _run_api_mode(args, target)

    # LOCAL mode — check for root before attempting
    if _is_root():
        print("❌ Cannot run LOCAL enhancement as root.")
        print()
        print("   Claude Code CLI refuses to execute as root (Docker/VPS security policy).")
        print("   Use API mode instead by setting one of these environment variables:")
        print()
        print("     export ANTHROPIC_API_KEY=sk-ant-...   # Claude")
        print("     export GOOGLE_API_KEY=AIza...          # Gemini")
        print("     export OPENAI_API_KEY=sk-proj-...      # OpenAI")
        print()
        print("   Then retry:")
        print(f"     skill-seekers enhance {args.skill_directory}")
        return 1

    print("🤖 Enhancement mode: LOCAL (Claude Code CLI)")
    return _run_local_mode(args)


if __name__ == "__main__":
    sys.exit(main())
