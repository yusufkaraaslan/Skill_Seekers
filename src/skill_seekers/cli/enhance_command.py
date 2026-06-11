#!/usr/bin/env python3
"""
Smart Enhancement Dispatcher

Routes `skill-seekers enhance` to the correct backend:

  API mode  — when an API key is available (Anthropic/Gemini/OpenAI).
              Calls enhance_skill.py which uses platform adaptors.

  LOCAL mode — when no API key is found.
              Calls LocalSkillEnhancer from enhance_skill_local.py.
              Supports: Claude Code, OpenAI Codex, GitHub Copilot, OpenCode, Kimi, and other agents.

Decision priority:
  1. Explicit --target flag → API mode with that platform.
  2. Config ai_enhancement.default_agent + matching env key → API mode.
  3. Auto-detect from env vars (agent_client.API_PROVIDERS priority order).
     Skipped with a notice if the detected provider's Python SDK isn't
     installed (it's an optional dependency for gemini/openai/kimi).
  4. No API keys (or no usable SDK) → LOCAL mode (AI coding agent).
  5. LOCAL mode + running as root → clear error (AI coding agent refuses root).
"""

import importlib.util
import os
import sys
from pathlib import Path

from skill_seekers.cli.agent_client import (
    detect_api_target,
    get_default_timeout,
    get_provider_api_keys,
)


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
    """Collect API keys from environment (single source: agent_client registry)."""
    return get_provider_api_keys()


# Python SDK module each API target's enhancement adaptor imports. claude
# rides the core `anthropic` dep; kimi uses the OpenAI-compatible client
# (adaptors/openai_compatible.py), so it needs the optional `openai` SDK.
TARGET_SDK_MODULES: dict[str, str] = {
    "claude": "anthropic",
    "gemini": "google.generativeai",
    "openai": "openai",
    "kimi": "openai",
}


def api_sdk_available(target: str) -> bool:
    """Return True if the Python SDK required for `target`'s API mode is importable.

    Uses find_spec (no import side effects) so a missing optional dependency
    is caught before committing to API mode instead of hard-failing later.
    """
    module = TARGET_SDK_MODULES.get(target)
    if module is None:
        return True  # Unknown target — let the adaptor surface its own error.
    try:
        return importlib.util.find_spec(module) is not None
    except ImportError:
        # find_spec on a dotted name imports the parent package; a missing
        # parent (e.g. no `google` namespace at all) means the SDK is absent.
        return False


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
    from skill_seekers.cli.adaptors import get_enhancement_platforms

    config_agent = _get_config_default_agent()
    if config_agent in get_enhancement_platforms() and api_keys.get(config_agent):
        return "api", config_agent

    # 3. Auto-detect from environment variables, in the priority order defined
    #    by agent_client.API_PROVIDERS (the single provider registry). Only
    #    commit to API mode if the provider's SDK is actually installed —
    #    otherwise (e.g. MOONSHOT_API_KEY set but the optional `openai`
    #    package missing) fall through to LOCAL mode instead of hard-failing.
    detected = detect_api_target()
    if detected:
        target = detected[0]
        if api_sdk_available(target):
            return "api", target
        module = TARGET_SDK_MODULES[target]
        print(
            f"⚠️  API key found for '{target}' but its SDK ('{module}') is not "
            "installed — falling back to LOCAL mode."
        )
        print(f"   For API mode: pip install {module.replace('.', '-')}")

    # 4. No usable API provider found → LOCAL mode.
    return "local", None


# ---------------------------------------------------------------------------
# API mode runner
# ---------------------------------------------------------------------------


def _run_api_mode(args, target: str) -> int:
    """Delegate to enhance_skill.py (platform adaptor path)."""
    from skill_seekers.cli.enhance_skill import main as enhance_api_main

    api_key = getattr(args, "api_key", None)
    if not api_key:
        # Explicit key > env var for the selected platform (target → key map
        # comes from the agent_client provider registry).
        api_key = _get_api_keys().get(target)

    # Reconstruct sys.argv for enhance_skill.main()
    argv = [
        "enhance_skill.py",
        str(args.skill_directory),
        "--target",
        target,
    ]
    if api_key:
        argv.extend(["--api-key", api_key])
    model = getattr(args, "model", None)
    if model:
        argv.extend(["--model", model])
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
        timeout=getattr(args, "timeout", None) or get_default_timeout(),
        background=getattr(args, "background", False),
        daemon=getattr(args, "daemon", False),
    )
    return 0 if success else 1


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(args=None) -> int:
    import argparse

    from skill_seekers.cli.arguments.enhance import add_enhance_arguments

    parser = argparse.ArgumentParser(
        description=(
            "Enhance SKILL.md using AI. "
            "Automatically selects API mode (Anthropic/Gemini/OpenAI API) when an API key "
            "is available, or falls back to LOCAL mode (AI coding agent)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Mode selection (automatic — no flags required):
  API mode  : Set ANTHROPIC_API_KEY, GOOGLE_API_KEY, or OPENAI_API_KEY.
              Or use --target to force a platform.
  LOCAL mode: Falls back when no API keys are found. Requires AI coding agent.
              Does NOT work as root (Docker/VPS) — use API mode instead.

Examples:
  # Auto-detect (API mode if any key is set, else LOCAL)
  skill-seekers enhance output/react/

  # Force Gemini API
  skill-seekers enhance output/react/ --target gemini

  # Force Anthropic API with explicit key
  skill-seekers enhance output/react/ --target claude --api-key sk-ant-...

  # LOCAL mode options
  skill-seekers enhance output/react/ --background
  skill-seekers enhance output/react/ --timeout 1200

  # Dry run (preview only)
  skill-seekers enhance output/react/ --dry-run
""",
    )
    add_enhance_arguments(parser)
    if args is None:
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
        print("   AI coding agent refuses to execute as root (Docker/VPS security policy).")
        print("   Use API mode instead by setting one of these environment variables:")
        print()
        print("     export ANTHROPIC_API_KEY=sk-ant-...   # Anthropic")
        print("     export GOOGLE_API_KEY=AIza...          # Gemini")
        print("     export OPENAI_API_KEY=sk-proj-...      # OpenAI")
        print()
        print("   Then retry:")
        print(f"     skill-seekers enhance {args.skill_directory}")
        return 1

    agent_name = os.environ.get("SKILL_SEEKER_AGENT", "claude").strip() or "claude"
    print(f"🤖 Enhancement mode: LOCAL ({agent_name})")
    return _run_local_mode(args)


if __name__ == "__main__":
    sys.exit(main())
