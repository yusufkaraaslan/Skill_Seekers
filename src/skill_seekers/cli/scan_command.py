"""skill-seekers scan — AI-driven project knowledge base (issue #327).

Orchestrates: signal collection → AI detection → config resolution / AI
generation → codebase config emission → optional publish to community
registry. AI calls go through ``AgentClient`` so both API and LOCAL agent
modes are supported.

This module is intentionally thin: each layer is a small free function so
tests can exercise pieces independently (signals are deterministic;
detection/generation are AI-driven and stub-friendly).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Markdown code-fence wrapper (```json ... ``` or ``` ... ```) the AI often emits.
_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*\n(.*?)\n```", re.DOTALL)


# ──────────────────────────────────────────────────────────────────────────
# Dataclasses
# ──────────────────────────────────────────────────────────────────────────


@dataclass
class Detection:
    """One framework/library/tool the AI detector identified in the project."""

    name: str
    ecosystem: str  # npm | pypi | cargo | go | gem | maven | composer | hex | system | other
    version: str | None
    kind: str  # framework | library | tool | service
    confidence: float
    evidence: str


@dataclass
class ScanDiff:
    """Diff between a previous scan in ``out_dir`` and the current detections."""

    added: list[str] = field(default_factory=list)
    updated: list[tuple[str, str | None, str | None]] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


@dataclass
class ScanResult:
    """Aggregate result of a scan run."""

    detections: list[Detection] = field(default_factory=list)
    emitted: list[Path] = field(default_factory=list)  # all configs written (resolved + generated)
    resolved: list[Path] = field(default_factory=list)  # subset: came from local/user/API
    generated: list[Path] = field(default_factory=list)  # subset: freshly AI-generated
    failed: list[str] = field(default_factory=list)  # detection names with no config produced
    diff: ScanDiff | None = None
    codebase_config: Path | None = None


# ──────────────────────────────────────────────────────────────────────────
# Deterministic helpers
# ──────────────────────────────────────────────────────────────────────────


def stamp_version(config_path: Path, version: str | None) -> None:
    """Set (or clear, when ``version is None``) the top-level ``detected_version``.

    Top-level placement is intentional — the existing ``metadata.version``
    field means "config schema version" and conflating the two would be
    ambiguous. ``detected_version`` is what re-scan compares to report bumps.
    """
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if version is None:
        data.pop("detected_version", None)
    else:
        data["detected_version"] = version
    config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def emit_codebase_config(root: Path, out_dir: Path) -> Path:
    """Write ``<project>-codebase.json`` wrapping a single ``type: local`` source.

    Shape mirrors the local-source block in ``configs/claude-code-unified.json``
    (lines 175-259 at the time of writing). Sensible defaults for
    file_patterns and skip_patterns so it works on any language tree.
    """
    project_name = root.resolve().name
    cfg_name = f"{project_name}-codebase"
    cfg_path = out_dir / f"{cfg_name}.json"

    config = {
        "name": cfg_name,
        "description": f"Project knowledge base for {project_name} — local codebase scrape.",
        "sources": [
            {
                "type": "local",
                "path": str(root.resolve()),
                "name": cfg_name,
                "description": f"Codebase of {project_name} (auto-emitted by scan).",
                "include_code": True,
                "file_patterns": [
                    "*.py",
                    "*.js",
                    "*.jsx",
                    "*.ts",
                    "*.tsx",
                    "*.go",
                    "*.rs",
                    "*.rb",
                    "*.java",
                    "*.kt",
                    "*.php",
                    "*.ex",
                    "*.cs",
                    "*.swift",
                    "*.md",
                    "*.json",
                    "*.toml",
                    "*.yaml",
                    "*.yml",
                ],
                "skip_patterns": [
                    ".git/",
                    "node_modules/",
                    "__pycache__/",
                    "*.map",
                    "dist/",
                    "build/",
                    ".venv/",
                    "venv/",
                    "target/",
                    ".pytest_cache/",
                    ".mypy_cache/",
                ],
                "analysis_features": {
                    "detect_patterns": True,
                    "extract_tests": True,
                    "build_guides": True,
                    "extract_config": True,
                    "build_api_reference": True,
                    "analyze_dependencies": True,
                    "detect_architecture": True,
                },
            }
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return cfg_path


def diff_against_existing(out_dir: Path, detections: list[Detection]) -> ScanDiff:
    """Compare existing configs in ``out_dir`` to the current detections.

    Compares by ``name`` and the top-level ``detected_version`` field.
    The auto-emitted ``<project>-codebase.json`` is excluded — it's not a
    framework detection, it's always re-emitted.
    """
    existing: dict[str, str | None] = {}
    if out_dir.is_dir():
        for path in sorted(out_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            name = data.get("name")
            if not name or name.endswith("-codebase"):
                continue
            existing[name] = data.get("detected_version")

    current = {d.name: d.version for d in detections}

    diff = ScanDiff()
    for name, version in current.items():
        if name not in existing:
            diff.added.append(name)
        elif existing[name] != version:
            diff.updated.append((name, existing[name], version))

    for name in existing:
        if name not in current:
            diff.removed.append(name)

    diff.added.sort()
    diff.updated.sort()
    diff.removed.sort()
    return diff


# ──────────────────────────────────────────────────────────────────────────
# AI layer — wraps AgentClient with prompts and JSON-extraction
# ──────────────────────────────────────────────────────────────────────────


def _extract_json(text: str) -> Any | None:
    """Pull a JSON object/array out of an LLM response.

    Tries: (1) raw `json.loads`, (2) fenced ```json ... ```, (3) the substring
    between the first ``{``/``[`` and the matching last ``}``/``]``. Returns
    None if nothing parses.
    """
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = _FENCE_RE.search(text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Greedy bracket extraction — try [...] first, then {...}.
    for open_ch, close_ch in (("[", "]"), ("{", "}")):
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue
    return None


def _build_detection_prompt(bundle) -> str:
    """Format a SignalBundle into the detection prompt."""
    lines = [
        f"Project: {bundle.project_name}",
    ]
    if bundle.git_remote:
        lines.append(f"Git remote: {bundle.git_remote}")
    lines.append("")
    lines.append("Signals (each in its own block):")
    for s in bundle.signals:
        lines.append(f"--- {s.kind} :: {s.path.name} ---")
        lines.append(s.content)
        lines.append("")

    lines.append(
        "Task: Identify the frameworks, libraries, tools and services this project "
        "directly uses. Skip transitive dependencies. For each, return: name, "
        "ecosystem (npm | pypi | cargo | go | gem | maven | composer | hex | "
        "system | other), version (or null), kind (framework | library | tool | "
        "service), confidence (0-1), evidence (short reason).\n\n"
        "Respond with ONLY a JSON array, no prose, no markdown fence."
    )
    return "\n".join(lines)


def detect_with_ai(bundle, client, *, min_confidence: float = 0.4) -> list[Detection]:
    """Ask the AI agent to identify technologies in the project.

    Args:
        bundle: a ``SignalBundle`` from ``signal_collectors.collect_signals``.
        client: an ``AgentClient`` instance (or any object with ``.call(prompt)``).
        min_confidence: drop detections with confidence below this.

    Returns:
        List of ``Detection`` objects. Empty on malformed AI output (logged).
    """
    prompt = _build_detection_prompt(bundle)
    raw = client.call(prompt, max_tokens=4096)
    if raw is None:
        logger.warning("AI detector returned no response")
        return []

    data = _extract_json(raw)
    if not isinstance(data, list):
        logger.warning("AI detector returned non-list JSON: %r", type(data).__name__)
        return []

    detections: list[Detection] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        ecosystem = entry.get("ecosystem")
        kind = entry.get("kind")
        if not name or not ecosystem or not kind:
            continue  # required fields missing
        confidence = float(entry.get("confidence", 0.0))
        if confidence < min_confidence:
            continue
        detections.append(
            Detection(
                name=str(name),
                ecosystem=str(ecosystem),
                version=(str(entry["version"]) if entry.get("version") else None),
                kind=str(kind),
                confidence=confidence,
                evidence=str(entry.get("evidence", "")),
            )
        )
    return detections


_GENERATE_SCHEMA_HINT = """\
{
  "name": "<package-name>",
  "description": "When-to-use sentence (1-2 lines).",
  "base_url": "<official docs URL>",
  "sources": [
    {
      "type": "documentation",
      "base_url": "<official docs URL>",
      "selectors": {"main_content": "article, main", "title": "h1", "code_blocks": "pre code"},
      "url_patterns": {"include": [], "exclude": []}
    },
    {
      "type": "github",
      "repo": "<owner/repo>",
      "enable_codebase_analysis": true,
      "code_analysis_depth": "standard",
      "fetch_issues": false
    }
  ],
  "categories": {"<category>": ["<keyword>"]},
  "rate_limit": 0.5,
  "max_pages": 250,
  "metadata": {
    "version": "1.0.0",
    "framework": "<display-name>"
  }
}"""


def _build_generation_prompt(detection: Detection) -> str:
    return (
        f"Generate a Skill Seekers unified config JSON for:\n"
        f"  name: {detection.name}\n"
        f"  version: {detection.version or 'unknown'}\n"
        f"  ecosystem: {detection.ecosystem}\n"
        f"  kind: {detection.kind}\n\n"
        f"Use this exact schema (fill in real values — do NOT include the "
        f"angle-bracket placeholders):\n{_GENERATE_SCHEMA_HINT}\n\n"
        f"Use the OFFICIAL documentation URL and GitHub repo. If you don't "
        f"know them, use sensible guesses based on the package name. Pick "
        f"3-6 category buckets relevant to this kind of library.\n\n"
        f"Respond with ONLY a JSON object, no prose, no markdown fence."
    )


def generate_config_with_ai(detection: Detection, client, *, max_attempts: int = 2) -> dict | None:
    """Ask the AI to produce a fresh unified config for an unmapped detection.

    Validates the result with ``UniSkillConfigValidator``. On invalid output
    re-asks once. Returns ``None`` if no valid config is produced.

    The returned dict has ``detected_version`` already stamped — callers can
    write it directly without a separate ``stamp_version`` call.
    """
    from skill_seekers.cli.config_validator import UniSkillConfigValidator

    prompt = _build_generation_prompt(detection)
    for attempt in range(max_attempts):
        raw = client.call(prompt, max_tokens=4096)
        if raw is None:
            logger.warning("AI generator returned no response (attempt %d)", attempt + 1)
            continue
        data = _extract_json(raw)
        if not isinstance(data, dict):
            logger.warning("AI generator did not return a JSON object (attempt %d)", attempt + 1)
            continue
        try:
            UniSkillConfigValidator(data).validate()
        except Exception as e:
            logger.warning("AI-generated config failed validation: %s", e)
            continue
        data["detected_version"] = detection.version
        return data

    logger.error(
        "AI failed to produce a valid config for %s after %d attempts", detection.name, max_attempts
    )
    return None


# ──────────────────────────────────────────────────────────────────────────
# Resolver — local → user dir → API, falling back to AI generation
# ──────────────────────────────────────────────────────────────────────────


# Re-imported at module level so tests can monkeypatch
# ``skill_seekers.cli.scan_command.resolve_config_path``.
from skill_seekers.cli.config_fetcher import resolve_config_path  # noqa: E402


def _config_filename_for(detection: Detection) -> str:
    """Filename for a detection's emitted config — `<name>.json` slugified."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", detection.name).strip("-")
    return f"{safe}.json"


def resolve_or_generate_with_status(
    detection: Detection,
    *,
    out_dir: Path,
    client,
    allow_network: bool = True,
    allow_generate: bool = True,
) -> tuple[Path | None, bool]:
    """Find or build a config for ``detection`` and write it under ``out_dir``.

    Resolution chain:
      1. ``resolve_config_path(name)`` — handles local repo / user dir / API.
      2. If miss and ``allow_generate``: call ``generate_config_with_ai``.
      3. Else: return (None, False).

    Returns ``(path, was_generated)``. ``was_generated`` distinguishes a
    fresh AI-generated config (eligible for the publish prompt) from one
    that came out of the resolution chain. ``path`` is None on total miss.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    resolved = resolve_config_path(detection.name, auto_fetch=allow_network)
    target = out_dir / _config_filename_for(detection)

    if resolved is not None and resolved.exists():
        data = json.loads(resolved.read_text(encoding="utf-8"))
        data["detected_version"] = detection.version
        target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return target, False

    if not allow_generate:
        return None, False

    generated = generate_config_with_ai(detection, client)
    if generated is None:
        return None, False
    target.write_text(json.dumps(generated, indent=2) + "\n", encoding="utf-8")
    return target, True


def resolve_or_generate(
    detection: Detection,
    *,
    out_dir: Path,
    client,
    allow_network: bool = True,
    allow_generate: bool = True,
) -> Path | None:
    """Thin wrapper around ``resolve_or_generate_with_status`` returning only the path."""
    path, _ = resolve_or_generate_with_status(
        detection,
        out_dir=out_dir,
        client=client,
        allow_network=allow_network,
        allow_generate=allow_generate,
    )
    return path


# ──────────────────────────────────────────────────────────────────────────
# Publish prompt — opt-in submission of freshly generated configs to the
# community registry (opens a GitHub issue against skill-seekers-configs).
# ──────────────────────────────────────────────────────────────────────────


def _submit_config_sync(config_path: Path) -> dict:
    """Synchronously submit a config via the MCP `submit_config_tool`.

    Wraps the async MCP tool so the CLI can call it without an event loop.
    Returns a dict with at least ``{"ok": bool, "message": str}``. Raises
    on import errors so callers can present a clear "install [mcp] extra"
    hint.
    """
    import asyncio

    try:
        from skill_seekers.mcp.tools.source_tools import submit_config_tool
    except ImportError as e:
        raise RuntimeError(
            "MCP extras not installed — `pip install -e .[mcp]` to enable community submission"
        ) from e

    async def _run():
        return await submit_config_tool({"config_path": str(config_path)})

    result = asyncio.run(_run())

    # submit_config_tool returns a list of mcp.types.TextContent; we expose
    # only the first message back to the CLI caller.
    if result and hasattr(result[0], "text"):
        text = result[0].text
        ok = not text.lstrip().startswith("❌")
        return {"ok": ok, "message": text}
    return {"ok": False, "message": "Empty response from submit_config_tool"}


def maybe_publish(generated_paths: list[Path], *, skip_prompt: bool = False) -> None:
    """Optionally prompt the user to publish freshly AI-generated configs.

    For each path in ``generated_paths`` (typically the subset that came back
    from ``resolve_or_generate_with_status`` with ``was_generated=True``),
    asks ``Submit <name> to community registry? [y/N]`` and on yes invokes
    the GitHub-issue submission flow.

    ``skip_prompt=True`` is the CI/automation switch — never prompts, never
    submits.
    """
    if not generated_paths:
        return
    if skip_prompt:
        logger.debug("--no-publish-prompt set; skipping community submission")
        return

    for path in generated_paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            name = data.get("name", path.stem)
        except (OSError, json.JSONDecodeError):
            name = path.stem

        print()
        print(f"📤 Submit '{name}' to the community config registry?")
        print(f"   ({path.name} — opens an issue at yusufkaraaslan/skill-seekers-configs)")
        try:
            answer = input("   [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            print("   Cancelled.")
            return

        if answer not in ("y", "yes"):
            continue

        try:
            result = _submit_config_sync(path)
        except Exception as e:
            print(f"   ❌ Submission failed: {e}")
            continue

        if result.get("ok"):
            print(f"   ✅ {result.get('message', 'Submitted.')}")
        else:
            print(f"   ⚠️  {result.get('message', 'Submission did not complete.')}")


# ──────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────


def _pluralize(n: int, singular: str, plural: str | None = None) -> str:
    return singular if n == 1 else (plural or singular + "s")


def _print_report(result: ScanResult, *, verbose: bool, out_dir: Path) -> None:
    n_det = len(result.detections)
    print()
    print("=" * 60)
    print(f"  skill-seekers scan — {n_det} {_pluralize(n_det, 'detection')}")
    print("=" * 60)
    print()

    if verbose and result.detections:
        for d in result.detections:
            print(
                f"  • {d.name} ({d.ecosystem}) {d.version or '—'}  "
                f"[{d.kind}, conf={d.confidence:.2f}]"
            )
            if d.evidence:
                print(f"      evidence: {d.evidence}")
        print()

    # Resolution summary
    print("  Configs:")
    print(f"    ✅ {len(result.resolved)} resolved        (from local / user / API)")
    print(f"    🤖 {len(result.generated)} AI-generated    (no existing preset)")
    if result.failed:
        print(
            f"    ⚠️  {len(result.failed)} unresolved      "
            f"({', '.join(result.failed)})"
        )
    if result.codebase_config is not None:
        print("    📂 1 codebase config (always emitted)")
    print()

    # Diff vs previous scan
    if result.diff is not None:
        diff = result.diff
        if diff.added or diff.updated or diff.removed:
            print("  Diff vs previous scan:")
            for name in diff.added:
                print(f"    + added       {name}")
            for name, old, new in diff.updated:
                print(f"    ↻ updated     {name}  {old or '—'} → {new or '—'}")
            for name in diff.removed:
                print(f"    - removed     {name}")
            print()
        else:
            print("  No changes since last scan.")
            print()

    # Where things landed
    print(f"  Output: {out_dir}")
    if result.codebase_config is not None:
        print(f"    └─ {result.codebase_config.name}  (codebase skill)")
    print()

    # Next step hint
    if result.emitted or result.codebase_config:
        print("  Next: run `skill-seekers create <config.json>` on each "
              "config you want to build.")
    elif result.failed:
        print("  Nothing was written. Re-run without --no-fetch / "
              "--no-generate to fetch or generate configs.")
    print()


def run_scan(
    directory: Path,
    out_dir: Path,
    *,
    agent_client,
    allow_network: bool = True,
    allow_generate: bool = True,
    skip_publish: bool = False,
    min_confidence: float = 0.4,
) -> ScanResult:
    """End-to-end scan, decoupled from argparse so it can be called as a library."""
    from skill_seekers.cli.signal_collectors import collect_signals

    out_dir.mkdir(parents=True, exist_ok=True)
    bundle = collect_signals(directory)

    detections = detect_with_ai(bundle, agent_client, min_confidence=min_confidence)

    # Snapshot the prior state of out_dir BEFORE we write anything so the
    # diff reflects changes introduced by this scan, not by the writes
    # we're about to do.
    result = ScanResult(detections=detections)
    result.diff = diff_against_existing(out_dir, detections)

    for det in detections:
        path, was_generated = resolve_or_generate_with_status(
            det,
            out_dir=out_dir,
            client=agent_client,
            allow_network=allow_network,
            allow_generate=allow_generate,
        )
        if path is None:
            logger.warning("Could not resolve or generate config for %s", det.name)
            result.failed.append(det.name)
            continue
        result.emitted.append(path)
        if was_generated:
            result.generated.append(path)
        else:
            result.resolved.append(path)

    result.codebase_config = emit_codebase_config(directory, out_dir)

    if not skip_publish:
        maybe_publish(result.generated, skip_prompt=False)

    return result


def main() -> int:
    """CLI entry point for `skill-seekers scan`."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="skill-seekers scan",
        description="AI-detect a project's tech stack and emit per-framework configs",
    )
    parser.add_argument("directory")
    parser.add_argument("--out", default="./configs/scanned/")
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--no-generate", action="store_true")
    parser.add_argument("--no-publish-prompt", action="store_true")
    parser.add_argument("--agent", default=None)
    parser.add_argument("--min-confidence", type=float, default=0.4)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        print(f"❌ Not a directory: {directory}")
        return 1

    out_dir = Path(args.out).resolve()

    from skill_seekers.cli.agent_client import AgentClient

    client = AgentClient(mode="auto", agent=args.agent)

    try:
        result = run_scan(
            directory,
            out_dir,
            agent_client=client,
            allow_network=not args.no_fetch,
            allow_generate=not args.no_generate,
            skip_publish=args.no_publish_prompt,
            min_confidence=args.min_confidence,
        )
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130

    _print_report(result, verbose=args.verbose, out_dir=out_dir)
    return 0


if __name__ == "__main__":  # pragma: no cover
    import sys

    sys.exit(main())
