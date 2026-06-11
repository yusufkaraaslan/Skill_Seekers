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
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Markdown code-fence wrapper (```json ... ``` or ``` ... ```) the AI often emits.
_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*\n(.*?)\n```", re.DOTALL)


def _atomic_write_json(path: Path, data: dict) -> None:
    """Write JSON to ``path`` atomically.

    A direct ``path.write_text`` opens-truncates-then-writes; if the process
    is interrupted mid-write the file is left half-written, and on the next
    scan ``diff_against_existing`` will silently treat the corrupted file as
    "removed" — potentially losing user edits. ``os.replace`` is atomic on
    POSIX (and on Windows when the target already exists), so a crash leaves
    either the old file or the new file, never a half-written one.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


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
    archived: list[Path] = field(default_factory=list)  # stale configs moved to .archived/


# ──────────────────────────────────────────────────────────────────────────
# Deterministic helpers
# ──────────────────────────────────────────────────────────────────────────


def _get_detected_version(data: dict) -> str | None:
    """Read ``metadata.detected_version`` from a config dict.

    Backwards-compat: also falls back to the top-level ``detected_version``
    field that earlier scan versions wrote, so existing on-disk configs from
    the previous Unreleased build still diff correctly. Top-level always wins
    if both are present — but writes always go to metadata now.
    """
    top = data.get("detected_version")
    if top is not None:
        return top
    return data.get("metadata", {}).get("detected_version")


def _set_detected_version(data: dict, version: str | None) -> None:
    """Write/clear ``metadata.detected_version`` on a config dict in place.

    Also clears any legacy top-level ``detected_version`` to prevent drift
    between the two locations after a re-scan touches the file.
    """
    data.pop("detected_version", None)
    metadata = data.setdefault("metadata", {})
    if version is None:
        metadata.pop("detected_version", None)
    else:
        metadata["detected_version"] = version


def stamp_version(config_path: Path, version: str | None) -> None:
    """Set (or clear, when ``version is None``) ``metadata.detected_version``.

    Nested under ``metadata`` to keep the top-level config schema clean —
    ``metadata.version`` already means "config schema version" so the
    detected framework version belongs in the same namespace, not at root.
    Re-scan diffs read the field via ``_get_detected_version`` so legacy
    top-level placements from the initial Unreleased build still work.
    """
    data = json.loads(config_path.read_text(encoding="utf-8"))
    _set_detected_version(data, version)
    _atomic_write_json(config_path, data)


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
    _atomic_write_json(cfg_path, config)
    return cfg_path


def _archive_removed(out_dir: Path, removed_slugs: list[str]) -> list[Path]:
    """Move stale config files into ``out_dir/.archived/<UTC-timestamp>/``.

    Never deletes — the user may have hand-edited a config they want to keep.
    Move ensures the next scan won't re-diff it as ``added`` immediately.
    """
    if not removed_slugs or not out_dir.is_dir():
        return []
    import datetime
    import shutil

    # ``datetime.UTC`` is Python 3.11+; project supports 3.10+, so use the
    # ``datetime.timezone.utc`` spelling that works on both.
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    archive_dir = out_dir / ".archived" / timestamp
    archived: list[Path] = []
    for slug in removed_slugs:
        src = out_dir / f"{slug}.json"
        if not src.exists():
            continue
        archive_dir.mkdir(parents=True, exist_ok=True)
        dest = archive_dir / src.name
        try:
            shutil.move(str(src), str(dest))
            archived.append(dest)
        except OSError as e:
            logger.warning("Could not archive %s: %s", src, e)
    return archived


def diff_against_existing(out_dir: Path, detections: list[Detection]) -> ScanDiff:
    """Compare existing configs in ``out_dir`` to the current detections.

    Keyed by **filename slug** rather than the config's internal ``name``
    field. The internal ``name`` reflects the resolved canonical preset
    (e.g. ``godot``) but ``Detection.name`` is whatever the AI returned
    (e.g. ``Godot Engine``) — keying off the internal name caused phantom
    ``+ added Godot Engine / - removed godot`` on every re-scan. The
    filename slug is determined by ``_config_filename_for(detection)``, so
    both sides of the diff use the same stable identifier.
    The auto-emitted ``<project>-codebase.json`` is excluded.
    """
    existing: dict[str, str | None] = {}
    if out_dir.is_dir():
        for path in sorted(out_dir.glob("*.json")):
            stem = path.stem
            if stem.endswith("-codebase"):
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as e:
                logger.warning("Skipping unreadable config %s: %s", path, e)
                continue
            existing[stem] = _get_detected_version(data)

    current: dict[str, str | None] = {}
    for d in detections:
        slug = _config_filename_for(d).removesuffix(".json")
        current[slug] = d.version

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
        "directly uses. Skip transitive dependencies. For each, return:\n"
        "  - name: the CANONICAL package-manager slug, NOT a human-readable\n"
        "    display name. Examples:\n"
        "      • 'react'      (not 'React')\n"
        "      • 'fastapi'    (not 'FastAPI')\n"
        "      • 'godot'      (not 'Godot Engine')\n"
        "      • 'tailwindcss' or 'tailwind' (not 'Tailwind CSS')\n"
        "      • 'vue'        (not 'Vue.js')\n"
        "      • 'spring-boot' (not 'Spring Boot')\n"
        "      • '@anthropic-ai/sdk' for npm-scoped packages (keep the scope)\n"
        "    Rule of thumb: what would you type after `npm install`, "
        "`pip install`, `cargo add`, or in a config preset filename?\n"
        "  - ecosystem: one of npm | pypi | cargo | go | gem | maven | "
        "composer | hex | system | other\n"
        "  - version: the version string from the manifest, or null if absent\n"
        "  - kind: framework | library | tool | service\n"
        "  - confidence: 0-1\n"
        "  - evidence: short reason (which signal you used)\n\n"
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
    try:
        raw = client.call(prompt, max_tokens=4096)
    except Exception as e:
        logger.error("AI detector call failed: %s: %s", type(e).__name__, e)
        return []
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
        # The AI sometimes returns a non-numeric confidence (e.g. "high") or
        # null despite the prompt; coerce defensively so one bad entry can't
        # crash the whole scan with an unhandled ValueError/TypeError.
        try:
            confidence = float(entry.get("confidence", 0.0))
        except (TypeError, ValueError):
            logger.warning(
                "Dropping detection %r: non-numeric confidence %r",
                entry.get("name"),
                entry.get("confidence"),
            )
            continue
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
      "code_analysis_depth": "deep",
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


def _probe_urls(config: dict, timeout: float = 5.0) -> list[str]:
    """HEAD-probe each URL in a config; return the list of URLs that failed.

    Failures = HTTP 4xx/5xx, connection error, timeout. 3xx redirects count as
    success. Used by ``generate_config_with_ai`` when ``--probe-urls`` is on
    to flag AI-hallucinated base_urls before the config is written.
    """
    try:
        import httpx
    except ImportError:
        logger.warning("--probe-urls requires httpx (a core dep); skipping probe")
        return []

    urls_to_check: list[str] = []
    base_url = config.get("base_url")
    if isinstance(base_url, str) and base_url.startswith(("http://", "https://")):
        urls_to_check.append(base_url)
    for source in config.get("sources", []):
        if not isinstance(source, dict):
            continue
        src_url = source.get("base_url")
        if (
            isinstance(src_url, str)
            and src_url.startswith(("http://", "https://"))
            and src_url not in urls_to_check
        ):
            urls_to_check.append(src_url)
        repo = source.get("repo")
        if isinstance(repo, str) and "/" in repo:
            gh_url = f"https://github.com/{repo}"
            if gh_url not in urls_to_check:
                urls_to_check.append(gh_url)

    failed: list[str] = []
    with httpx.Client(timeout=timeout, follow_redirects=True) as client_:
        for url in urls_to_check:
            try:
                resp = client_.head(url)
                # Some servers (notably older PyPI mirrors and Cloudflare-fronted
                # sites) reject HEAD with 405 Method Not Allowed even when the
                # URL is perfectly valid. Fall back to GET on 405 to avoid
                # flagging real URLs as unreachable.
                if resp.status_code == 405:
                    resp = client_.get(url)
                if resp.status_code >= 400:
                    failed.append(url)
            except (httpx.HTTPError, OSError) as e:
                logger.debug("URL probe failed for %s: %s", url, e)
                failed.append(url)
    return failed


def generate_config_with_ai(
    detection: Detection,
    client,
    *,
    max_attempts: int = 2,
    probe_urls: bool = False,
) -> dict | None:
    """Ask the AI to produce a fresh unified config for an unmapped detection.

    Validates the result with ``UniSkillConfigValidator``. On invalid output
    re-asks once. Returns ``None`` if no valid config is produced.

    If ``probe_urls=True``, after a valid config is produced, HEAD-probes
    each URL. If any fail, re-asks the AI once with feedback. If they still
    fail, stamps ``metadata._url_unverified = [bad urls]`` and returns the
    config anyway so the user sees the hallucination instead of silently
    using a broken URL.

    The returned dict has ``detected_version`` already stamped.
    """
    from skill_seekers.cli.config_validator import UniSkillConfigValidator

    base_prompt = _build_generation_prompt(detection)
    feedback: str | None = None

    for attempt in range(max_attempts):
        prompt = base_prompt
        if feedback is not None:
            prompt = f"{base_prompt}\n\nIMPORTANT FEEDBACK ON PREVIOUS ATTEMPT:\n{feedback}"
        try:
            raw = client.call(prompt, max_tokens=4096)
        except Exception as e:
            logger.error(
                "AI generator call failed (attempt %d): %s: %s",
                attempt + 1,
                type(e).__name__,
                e,
            )
            continue
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
        # The community submission flow (services.source_manager.submit_config)
        # additionally requires the name to match ^[a-zA-Z0-9_-]+$. Reject here
        # so we don't silently write a config that can't be published.
        name = str(data.get("name", ""))
        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            logger.warning(
                "AI-generated config name %r is not registry-safe "
                "(must match [a-zA-Z0-9_-]+); retrying",
                name,
            )
            continue

        # URL reachability probe (WS9). Always check fresh per-attempt — never
        # carry the previous attempt's bad URLs into this attempt's verdict.
        bad_urls: list[str] = _probe_urls(data) if probe_urls else []
        if bad_urls:
            logger.warning(
                "AI-generated config for %s has %d unreachable URL(s): %s",
                detection.name,
                len(bad_urls),
                ", ".join(bad_urls),
            )
            # Retry available → ask AI to fix and try again. Don't stamp yet.
            if attempt < max_attempts - 1:
                feedback = (
                    f"Your previous response listed these URLs which returned "
                    f"4xx/5xx or did not respond: {bad_urls}. Please verify and "
                    f"replace with the actual official documentation URL and "
                    f"GitHub repo for {detection.name}."
                )
                continue

        _set_detected_version(data, detection.version)
        # If we ran out of retries with still-bad URLs (or this is the final
        # attempt), stamp them so the user sees what to fix instead of silently
        # shipping a broken config.
        if bad_urls:
            data.setdefault("metadata", {})["_url_unverified"] = list(bad_urls)
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

# Community-registry submission engine — shared with the MCP submit_config
# tool via the services layer (CLI must not import skill_seekers.mcp).
from skill_seekers.services.source_manager import (  # noqa: E402
    REGISTRY_REPO,
    find_existing_submission,
    submit_config,
)


def _config_filename_for(detection: Detection) -> str:
    """Filename for a detection's emitted config — lowercase slug + ``.json``.

    Lowercased so the AI's casing flakiness (``React`` one run, ``react`` the
    next) doesn't produce duplicate files that accumulate forever without
    ever being cleaned up by the ``removed`` diff path.
    """
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", detection.name).strip("-").lower()
    return f"{safe}.json"


# Common suffixes appended to display names but absent from preset slugs.
# Internationalised because a large fraction of users work in CJK contexts
# (Chinese, Korean, Japanese) where libraries are commonly referred to with
# native-language descriptors. Without these, "戦闘エンジン" → "戦闘エンジン"
# (unchanged), no candidate ever hits the registry. With them, the suffix
# strips so the bare base name has a chance to resolve.
#
# Suffixes are tried in tuple order — first match wins (single-pass strip).
# Both the space-prefixed and no-space form are listed for CJK where space
# usage is inconsistent.
_NAME_SUFFIXES = (
    # English
    " engine",
    " framework",
    " sdk",
    " library",
    " core",
    " runtime",
    ".js",
    " js",
    " css",
    # Chinese (simplified + traditional — same chars for these words)
    " 引擎",
    "引擎",  # engine
    " 框架",
    "框架",  # framework
    " 库",
    "库",  # library (simplified)
    " 函式庫",
    "函式庫",  # library (traditional)
    " 核心",
    "核心",  # core
    " 运行时",
    "运行时",  # runtime (simplified)
    " 執行階段",
    "執行階段",  # runtime (traditional)
    # Korean
    " 엔진",
    "엔진",  # engine
    " 프레임워크",
    "프레임워크",  # framework
    " 라이브러리",
    "라이브러리",  # library
    " 코어",
    "코어",  # core
    " 런타임",
    "런타임",  # runtime
    # Japanese
    " エンジン",
    "エンジン",  # engine
    " フレームワーク",
    "フレームワーク",  # framework
    " ライブラリ",
    "ライブラリ",  # library
    " コア",
    "コア",  # core
    " ランタイム",
    "ランタイム",  # runtime
    # Spanish / Portuguese (overlap with each other on many of these)
    " motor",  # engine
    " marco",  # framework (es)
    " biblioteca",  # library
    " núcleo",  # core
    " ejecución",  # runtime
    # French
    " moteur",  # engine
    " cadre",  # framework
    " bibliothèque",  # library
    " noyau",  # core
    " exécution",  # runtime
    # German (case-insensitive via lowercasing earlier in the candidate gen)
    " kern",  # core
    " rahmen",  # framework
    " bibliothek",  # library
    " laufzeit",  # runtime
)


def _canonical_name_candidates(name: str) -> list[str]:
    """Yield lookup candidates for a (possibly human-readable) detection name.

    AI detectors don't always return the canonical preset slug — e.g. they say
    ``Godot Engine`` where the registry has ``godot``, or ``Tailwind CSS``
    where it has ``tailwind``. This helper produces up to ~5 variants in
    priority order so the resolver can try each before giving up. The
    original input is always first so an exact-match preset wins.
    """
    if not name or not name.strip() or name.isspace():
        return [name] if name else []

    seen: dict[str, None] = {}  # ordered set

    def _add(candidate: str) -> None:
        candidate = candidate.strip()
        if candidate and candidate not in seen:
            seen[candidate] = None

    # 1. Original — exact match wins if it exists
    _add(name)

    # 2. Lowercase
    lower = name.lower()
    _add(lower)

    # 3. Lowercase + spaces/dots → hyphens
    hyphenated = re.sub(r"[ ._]+", "-", lower).strip("-")
    _add(hyphenated)

    # 4. Strip common suffixes (operate on the lowercase form)
    stripped = lower
    for suffix in _NAME_SUFFIXES:
        if stripped.endswith(suffix):
            stripped = stripped[: -len(suffix)].rstrip()
            break
    if stripped != lower:
        _add(stripped)
        _add(re.sub(r"[ ._]+", "-", stripped).strip("-"))

    # 5. npm-scoped: @scope/name → name + scope-name slug
    if name.startswith("@") and "/" in name:
        scope, _, base = name[1:].partition("/")
        _add(base)
        _add(f"{scope}-{base}".lower())

    return list(seen.keys())


def resolve_or_generate_with_status(
    detection: Detection,
    *,
    out_dir: Path,
    client,
    allow_network: bool = True,
    allow_generate: bool = True,
    probe_urls: bool = False,
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

    target = out_dir / _config_filename_for(detection)

    # If this exact target already exists from a prior scan, reuse it: just
    # re-stamp the detected_version (in case it bumped) and return. Avoids
    # re-fetching from the API and respects any manual edits the user made.
    if target.exists():
        try:
            stamp_version(target, detection.version)
            return target, False
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Existing config %s is unreadable, re-resolving: %s", target, e)

    # Try each canonical name candidate (e.g. 'Godot Engine' → 'godot') so we
    # don't miss matches just because the AI used a human-readable name.
    # ``resolve_config_path`` checks (1) exact path, (2) ``configs/<name>``,
    # (3) user config dir; all three require the ``.json`` suffix to match
    # actual files on disk, so we append it here. The API fallback inside
    # the function strips/re-adds it as needed.
    #
    # Snapshot out_dir first so the intermediate cleanup below can tell an
    # API-fetched cache artifact (created during this run) apart from a
    # pre-existing user-managed file — the latter must never be deleted.
    pre_existing = {p.resolve() for p in out_dir.glob("*.json")}
    resolved: Path | None = None
    for candidate in _canonical_name_candidates(detection.name):
        lookup = candidate if candidate.endswith(".json") else f"{candidate}.json"
        # Fetch into out_dir (scan re-writes there anyway) rather than polluting
        # ./configs/ in the current working directory.
        hit = resolve_config_path(lookup, auto_fetch=allow_network, fetch_destination=str(out_dir))
        if hit is not None and hit.exists():
            resolved = hit
            break

    if resolved is not None:
        try:
            data = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Could not load resolved config %s: %s", resolved, e)
            return None, False
        _set_detected_version(data, detection.version)
        _atomic_write_json(target, data)
        # An API fetch may have landed a canonical-named file inside out_dir
        # (e.g. godot.json next to our godot-engine.json target). Remove that
        # intermediate: scan's diff is keyed by filename slug, so a leftover
        # canonical file shows up as a phantom "removed" config on the next
        # scan and gets archived — churn on every re-scan. Only files this
        # run created qualify: resolve_config_path can also return a
        # pre-existing file inside out_dir (e.g. a user-managed
        # configs/godot.json found via its CWD-relative lookup when
        # out_dir == ./configs) — copy that, never delete it.
        try:
            if (
                resolved != target
                and resolved.parent.resolve() == out_dir.resolve()
                and resolved.resolve() not in pre_existing
            ):
                resolved.unlink()
        except OSError as e:
            logger.debug("Could not remove fetched intermediate %s: %s", resolved, e)
        return target, False

    if not allow_generate:
        return None, False

    generated = generate_config_with_ai(detection, client, probe_urls=probe_urls)
    if generated is None:
        return None, False
    _atomic_write_json(target, generated)
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


_SUBMIT_TIMEOUT_SECONDS = 30
_SUBMIT_RETRY_DELAYS = (5, 15)  # seconds between retries


async def _find_existing_issue(config_name: str, github_token: str | None) -> str | None:
    """Search the community registry for an open submission of ``config_name``.

    Returns the issue URL if found; None on no match, no token, or any error.
    Idempotency guard — prevents opening duplicate submission issues when the
    user runs scan repeatedly. Delegates to the shared (exact-title, bounded)
    check in services.source_manager so this and the MCP submit tool can't
    disagree on what counts as a duplicate.
    """
    if not github_token:
        return None

    import asyncio

    # PyGithub is sync — run in a thread so we don't block the loop.
    return await asyncio.to_thread(find_existing_submission, config_name, github_token)


async def _submit_config(config_path: Path) -> dict:
    """Async wrapper around the shared ``submit_config`` service with timeout + retry.

    Retries on transient failures (rate-limit / 5xx) with backoff per
    ``_SUBMIT_RETRY_DELAYS``. Per-attempt timeout from ``_SUBMIT_TIMEOUT_SECONDS``.
    Returns a dict ``{ok, message}``.
    """
    import asyncio

    last_error: Exception | None = None
    delays = (0,) + _SUBMIT_RETRY_DELAYS  # first attempt fires immediately
    for attempt, delay in enumerate(delays):
        if delay:
            await asyncio.sleep(delay)
        try:
            # The service is sync (PyGithub) — run in a thread so the
            # per-attempt timeout can actually fire.
            result = await asyncio.wait_for(
                asyncio.to_thread(submit_config, config_path=str(config_path)),
                timeout=_SUBMIT_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            last_error = RuntimeError(
                f"Submission timed out after {_SUBMIT_TIMEOUT_SECONDS}s (GitHub API unreachable?)"
            )
            logger.warning("Submission attempt %d timed out", attempt + 1)
            continue
        except Exception as e:
            last_error = e
            logger.warning(
                "Submission attempt %d failed: %s: %s",
                attempt + 1,
                type(e).__name__,
                e,
            )
            continue

        # Transient failure? Retry. Permanent failure? Return immediately.
        text = result["message"]
        transient = any(s in text.lower() for s in ("rate limit", "503", "502", "504"))
        if not result["ok"] and transient and attempt < len(delays) - 1:
            continue
        return result

    # All retries exhausted.
    raise RuntimeError(
        f"Submission failed after {len(delays)} attempts: {last_error}"
    ) from last_error


async def _prompt_async(prompt: str) -> str:
    """``input()`` that doesn't block the event loop."""
    import asyncio

    return await asyncio.to_thread(input, prompt)


async def maybe_publish(generated_paths: list[Path], *, skip_prompt: bool = False) -> None:
    """Async, opt-in prompt to submit freshly AI-generated configs to the
    community registry.

    Pre-checks GITHUB_TOKEN. Searches for an existing open issue for each
    config name to avoid duplicate submissions (idempotency). On submit,
    retries transient failures with backoff.

    ``skip_prompt=True`` skips the whole flow (CI mode).
    """
    if not generated_paths:
        return
    if skip_prompt:
        logger.debug("--no-publish-prompt set; skipping community submission")
        return

    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print()
        print(
            f"ℹ️  Skipping community-registry prompt for "
            f"{len(generated_paths)} AI-generated config(s) — "
            "GITHUB_TOKEN is not set."
        )
        print("   To enable submissions: `export GITHUB_TOKEN=<token>` then re-run.")
        return

    for path in generated_paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            name = data.get("name", path.stem)
        except (OSError, json.JSONDecodeError):
            name = path.stem

        # Idempotency: skip if an open issue already exists.
        existing_url = await _find_existing_issue(name, github_token)
        if existing_url:
            print()
            print(f"ℹ️  Existing community-registry issue for '{name}' — skipping submission.")
            print(f"   {existing_url}")
            continue

        print()
        print(f"📤 Submit '{name}' to the community config registry?")
        print(f"   ({path.name} — opens an issue at {REGISTRY_REPO})")
        try:
            answer = (await _prompt_async("   [y/N] ")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            print("   Cancelled.")
            return

        if answer not in ("y", "yes"):
            continue

        try:
            result = await _submit_config(path)
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
        print(f"    ⚠️  {len(result.failed)} unresolved      ({', '.join(result.failed)})")
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

    # Archive notice (WS10).
    if result.archived:
        # All archive paths share the same .archived/<ts>/ parent.
        archive_root = result.archived[0].parent
        print(f"  📦 Archived {len(result.archived)} stale config(s) → {archive_root.name}/")
        print()

    # Where things landed
    print(f"  Output: {out_dir}")
    if result.codebase_config is not None:
        print(f"    └─ {result.codebase_config.name}  (codebase skill)")
    print()

    # Next step hint
    if result.emitted or result.codebase_config:
        print("  Next: run `skill-seekers create <config.json>` on each config you want to build.")
    elif result.failed:
        print(
            "  Nothing was written. Re-run without --no-fetch / "
            "--no-generate to fetch or generate configs."
        )
    print()


def run_scan(
    directory: Path,
    out_dir: Path,
    *,
    agent_client,
    allow_network: bool = True,
    allow_generate: bool = True,
    skip_publish: bool = False,  # noqa: ARG001 — kept for back-compat; publish is now caller's responsibility
    min_confidence: float = 0.4,
    max_ai_generations: int = 10,
    dry_run: bool = False,
    probe_urls: bool = False,
) -> ScanResult:
    """End-to-end scan, decoupled from argparse so it can be called as a library.

    Args:
        skip_publish: **kept for back-compat with prior callers**; no longer
            consulted here. After WS11 the publish flow is async-native and
            lives in ``ScanCommand.execute``. ``run_scan`` doesn't trigger
            publish at all. Callers should orchestrate ``maybe_publish``
            themselves if needed.
        max_ai_generations: cap on AI-generated configs. Once reached, remaining
            unmapped detections are listed as ``result.failed`` so the user sees
            them but no further AI calls are made. Default 10 to prevent
            surprise API bills on monorepos with many unmapped deps.
        dry_run: if True, no files are written and no AI generation runs.
            ``result.emitted`` / ``result.generated`` / ``result.codebase_config``
            are populated as Path-like previews so the report shows what WOULD
            happen. Resolution-chain hits ARE counted (they're cheap and inform
            the preview), but writes are skipped.
    """
    from skill_seekers.cli.signal_collectors import collect_signals

    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
    bundle = collect_signals(directory)

    detections = detect_with_ai(bundle, agent_client, min_confidence=min_confidence)

    # Dedup detections that map to the same config filename slug (e.g. the AI
    # returns both "Godot" and "Godot Engine" -> both resolve to godot.json).
    # The diff already keys by slug; without deduping here the write loop below
    # would write and count the same config twice.
    _seen_slugs: set[str] = set()
    _deduped_detections = []
    for _det in detections:
        _slug = _config_filename_for(_det)
        if _slug in _seen_slugs:
            continue
        _seen_slugs.add(_slug)
        _deduped_detections.append(_det)
    detections = _deduped_detections

    # Snapshot the prior state of out_dir BEFORE we write anything so the
    # diff reflects changes introduced by this scan, not by the writes
    # we're about to do.
    result = ScanResult(detections=detections)
    result.diff = diff_against_existing(out_dir, detections)

    # Archive stale configs (WS10). Move (never delete) any framework config
    # that disappeared from detections — keeps out_dir clean without losing
    # user edits. Skipped in dry-run.
    if not dry_run and result.diff is not None and result.diff.removed:
        result.archived = _archive_removed(out_dir, result.diff.removed)

    # Effective generation cap. allow_generate=False shortcuts to 0.
    effective_max_gen = 0 if not allow_generate else max_ai_generations
    generations_used = 0

    for det in detections:
        if dry_run:
            # Preview-only: don't write, just check if the resolver would hit
            # cache or local/API. Doesn't run AI generation in any case.
            target = out_dir / _config_filename_for(det)
            if target.exists():
                result.resolved.append(target)
                result.emitted.append(target)
                continue
            # Check resolution chain WITHOUT writing or hitting the network:
            # auto_fetch would download + write ./configs/<name>.json, violating
            # the dry-run "no files written / no network" contract.
            resolved_hit = None
            for candidate in _canonical_name_candidates(det.name):
                lookup = candidate if candidate.endswith(".json") else f"{candidate}.json"
                hit = resolve_config_path(lookup, auto_fetch=False)
                if hit is not None and hit.exists():
                    resolved_hit = hit
                    break
            if resolved_hit is not None:
                result.resolved.append(target)
                result.emitted.append(target)
            else:
                # Would have been AI-generated (subject to cap) or failed.
                if generations_used < effective_max_gen:
                    result.generated.append(target)
                    result.emitted.append(target)
                    generations_used += 1
                else:
                    result.failed.append(det.name)
            continue

        # Cap AI generation count: pass allow_generate=False once we've hit the
        # cap so the resolver doesn't keep firing AI calls.
        local_allow_generate = allow_generate and generations_used < effective_max_gen
        path, was_generated = resolve_or_generate_with_status(
            det,
            out_dir=out_dir,
            client=agent_client,
            allow_network=allow_network,
            allow_generate=local_allow_generate,
            probe_urls=probe_urls,
        )
        if path is None:
            logger.warning("Could not resolve or generate config for %s", det.name)
            result.failed.append(det.name)
            continue
        result.emitted.append(path)
        if was_generated:
            result.generated.append(path)
            generations_used += 1
        else:
            result.resolved.append(path)

    if dry_run:
        # Synthesize a codebase-config preview path without writing.
        result.codebase_config = out_dir / f"{directory.resolve().name}-codebase.json"
    else:
        result.codebase_config = emit_codebase_config(directory, out_dir)

    # Publish is async (WS11) — caller (ScanCommand.execute) awaits it after
    # run_scan returns. run_scan itself stays sync because the rest of the
    # work (file IO, AI calls via AgentClient, signal collection) is sync.
    return result


def _exit_code_for(result: ScanResult) -> int:
    """0 on a useful scan, 1 if every detection failed or nothing emitted.

    A useful scan is one where at least one framework config OR the codebase
    config was written. Returning non-zero on total failure lets CI shell
    pipelines (`scan && build`) detect that the scan didn't produce anything.
    """
    if result.emitted or result.codebase_config:
        # Mixed success — even one resolved/generated config is a win.
        # We still return 0 if some failed; `result.failed` is visible in the
        # report and on stderr via logging.
        return 0
    return 1


class ScanCommand:
    """Entry point for `skill-seekers scan`. Dispatched from `main.py` with
    the already-parsed argparse namespace (no duplicate argparse here).
    """

    def __init__(self, args) -> None:
        self.args = args

    def execute(self) -> int:
        args = self.args

        # Surface our own logger.warning/error to the user. Without basicConfig
        # the root logger has no handlers and every warning we log is silently
        # dropped.
        log_level = logging.INFO if getattr(args, "verbose", False) else logging.WARNING
        logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

        directory = Path(args.directory).resolve()
        if not directory.is_dir():
            print(f"❌ Not a directory: {directory}")
            return 1

        out_dir = Path(args.out).resolve()

        from skill_seekers.cli.agent_client import AgentClient

        client = AgentClient(mode="auto", agent=getattr(args, "agent", None))

        # The publish flow (maybe_publish) is async — see WS11. Wrap the
        # whole orchestration in an asyncio.run at the entry so we have a
        # single event-loop boundary, never nested asyncio.run calls.
        import asyncio

        async def _amain() -> int:
            try:
                result = run_scan(
                    directory,
                    out_dir,
                    agent_client=client,
                    allow_network=not args.no_fetch,
                    allow_generate=not args.no_generate,
                    skip_publish=args.no_publish_prompt,
                    min_confidence=args.min_confidence,
                    max_ai_generations=getattr(args, "max_ai_generations", 10),
                    dry_run=getattr(args, "dry_run", False),
                    probe_urls=getattr(args, "probe_urls", False),
                )
            except KeyboardInterrupt:
                print("\nInterrupted.")
                return 130

            # Publish (await — native async path, with idempotency + retry).
            if not args.no_publish_prompt and not getattr(args, "dry_run", False):
                try:
                    await maybe_publish(result.generated, skip_prompt=False)
                except KeyboardInterrupt:
                    print("\nPublish cancelled.")

            if getattr(args, "dry_run", False):
                print("🔍 DRY RUN — no files written, no AI generation invoked.\n")
            _print_report(result, verbose=getattr(args, "verbose", False), out_dir=out_dir)
            return _exit_code_for(result)

        try:
            return asyncio.run(_amain())
        except RuntimeError as e:
            # Nested event loop (Jupyter, async test harness): surface a clear
            # hint instead of "cannot be called from a running event loop".
            if "running event loop" in str(e):
                print(
                    "❌ Cannot run scan from inside an already-running event "
                    "loop. Invoke from a plain CLI/script context."
                )
                return 1
            raise
