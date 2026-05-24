"""Scan subcommand parser (issue #327)."""

from .base import SubcommandParser


class ScanParser(SubcommandParser):
    """Parser for the `skill-seekers scan` subcommand.

    `scan` is an AI-driven discovery step: point it at a project directory
    and it emits one Skill Seekers config per detected framework/library,
    plus a `<project>-codebase.json` for the project itself. Run
    `skill-seekers create <config.json>` afterwards on each emitted file.
    """

    @property
    def name(self) -> str:
        return "scan"

    @property
    def help(self) -> str:
        return "AI-detect a project's tech stack and emit per-framework configs"

    @property
    def description(self) -> str:
        return (
            "Scan a project directory. An AI agent inspects manifests, "
            "README, Dockerfile/CI, sampled source imports and the git "
            "remote to identify frameworks and libraries in use. For each "
            "detection: resolves an existing config (local → user dir → "
            "skillseekersweb.com API) or — if none — generates a fresh "
            "config with AI. Always emits <project>-codebase.json. On "
            "re-scan, reports added / version-bumped / removed items."
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "directory",
            help="Project directory to scan (e.g., '.', './my-app')",
        )
        parser.add_argument(
            "--out",
            default="./configs/scanned/",
            help="Output directory for emitted configs (default: ./configs/scanned/)",
        )
        parser.add_argument(
            "--no-fetch",
            action="store_true",
            help="Skip the skillseekersweb.com API fallback during resolution",
        )
        parser.add_argument(
            "--no-generate",
            action="store_true",
            help="Skip AI generation for unmapped detections (offline-friendly)",
        )
        parser.add_argument(
            "--no-publish-prompt",
            action="store_true",
            help="Suppress the interactive 'Submit to community registry?' prompt",
        )
        parser.add_argument(
            "--agent",
            help=(
                "LOCAL mode agent name (claude | codex | copilot | opencode | "
                "kimi | custom). Defaults to env SKILL_SEEKER_AGENT or 'claude'."
            ),
        )
        parser.add_argument(
            "--min-confidence",
            type=float,
            default=0.4,
            help="Drop detections below this AI confidence (0-1, default 0.4)",
        )
        parser.add_argument(
            "--max-ai-generations",
            type=int,
            default=10,
            help=(
                "Cap AI config generation for unmapped detections (default 10). "
                "Prevents surprise API bills on monorepos with many unmapped deps. "
                "Set to 0 to disable AI generation entirely (same as --no-generate)."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=(
                "Preview what scan WOULD emit without writing anything or calling "
                "the AI for generation. Useful for cost-checking on large projects."
            ),
        )
        parser.add_argument(
            "--probe-urls",
            action="store_true",
            help=(
                "After AI-generating a config, HEAD-probe its base_url and any "
                "GitHub repo URL with a 5s timeout. On 4xx/5xx, ask the AI to "
                "retry with feedback; if still unreachable, stamp the config "
                "with metadata._url_unverified so the user can fix it. Adds "
                "5-10s per generated config."
            ),
        )
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Show detected items and resolution outcomes",
        )
