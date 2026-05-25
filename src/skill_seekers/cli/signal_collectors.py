"""Signal collectors for `skill-seekers scan` (issue #327).

Deterministic, stdlib-only helpers that gather *evidence* from a project
directory: dependency manifests, README excerpts, Dockerfile/CI configs,
sampled source-file imports, and the git remote URL. The collected
`SignalBundle` is the input to the AI detector — collectors do not
classify or interpret, they only sample.

All collectors are size-bounded so the resulting bundle fits comfortably
in an LLM prompt.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from skill_seekers.cli.source_detector import SourceDetector

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """One piece of evidence collected from a project directory."""

    kind: str  # "manifest" | "readme" | "dockerfile" | "ci" | "source_sample"
    path: Path
    content: str


@dataclass
class SignalBundle:
    """Aggregated signals plus project-level metadata."""

    signals: list[Signal] = field(default_factory=list)
    git_remote: str | None = None
    project_name: str = ""


# Manifest filenames that count as code-project markers. Reuses the lowercase
# frozenset from SourceDetector so both stay in sync. Extends it with
# requirements*.txt variants which aren't project markers (presence doesn't
# define a project) but are still relevant signals.
_MANIFEST_NAMES_LOWER = SourceDetector.CODE_PROJECT_MARKERS | {
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-test.txt",
    "requirements.in",
    "requirements-dev.in",
}

# Directories we never sample source files from.
_SKIP_DIRS = {
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".git",
    "__pycache__",
    "dist",
    "build",
    "target",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
}

# Common code source roots, in priority order. Covers:
#   - generic: src, lib, app
#   - Go: cmd, internal, pkg
#   - Rust workspaces: crates
#   - JS monorepos: packages, apps
#   - Backend/frontend splits: backend, frontend, services
#   - Java/Maven layout: source (less common but seen)
# Projects that put code at root (Django apps, flat Python packages, Godot)
# are picked up by `_iter_root_source_files` which walks one level deep.
_SOURCE_DIRS = (
    "src",
    "lib",
    "app",
    "internal",
    "pkg",
    "cmd",
    "crates",
    "packages",
    "apps",
    "services",
    "backend",
    "frontend",
    "source",
    "sources",
)

_SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".rb",
    ".java",
    ".kt",
    ".php",
    ".ex",
    ".cs",
    ".swift",
}


def _safe_read_text(path: Path, max_bytes: int) -> str | None:
    """Read up to ``max_bytes`` of a text file, decoded as UTF-8.

    Opens in binary mode and reads only what we need rather than slurping
    the whole file into memory and slicing. Matters when a manifest or
    source file is huge (some auto-generated package-lock.json files run
    into MB) and the per-kind budget here is only a few KB.

    UTF-8 multi-byte characters straddling the ``max_bytes`` boundary are
    handled by ``errors="replace"`` — a trailing partial sequence becomes
    a replacement char instead of failing the read. Acceptable for AI-prompt
    sampling.
    """
    try:
        with path.open("rb") as f:
            raw = f.read(max_bytes)
    except OSError as e:
        logger.debug("Skipping unreadable file %s: %s", path, e)
        return None
    return raw.decode("utf-8", errors="replace")


def collect_manifests(root: Path, max_bytes_per_file: int = 8192) -> list[Signal]:
    """Read all dependency manifests at the project root.

    Picks up the filenames listed in ``SourceDetector._CODE_PROJECT_MARKERS``
    plus ``requirements*.txt``. Match is case-insensitive to handle macOS
    case-preserving filesystems. Each file is truncated to ``max_bytes_per_file``.
    """
    signals: list[Signal] = []
    try:
        entries = sorted(root.iterdir())
    except OSError:
        return signals

    for entry in entries:
        if not entry.is_file():
            continue
        name_lower = entry.name.lower()
        if name_lower not in _MANIFEST_NAMES_LOWER and not name_lower.startswith("requirements"):
            continue
        content = _safe_read_text(entry, max_bytes_per_file)
        if content is None:
            continue
        signals.append(Signal(kind="manifest", path=entry, content=content))
    return signals


def collect_readme_excerpt(root: Path, max_bytes: int = 4096) -> Signal | None:
    """Return the first README found at root, truncated. None if absent."""
    for candidate in ("README.md", "README.rst", "README.txt", "README"):
        path = root / candidate
        if path.is_file():
            content = _safe_read_text(path, max_bytes)
            if content is not None:
                return Signal(kind="readme", path=path, content=content)
    return None


def collect_dockerfile_and_ci(root: Path, max_bytes_per_file: int = 4096) -> list[Signal]:
    """Collect Dockerfile, docker-compose, CI configs, and Makefile."""
    signals: list[Signal] = []

    direct_files = [
        ("Dockerfile", "dockerfile"),
        ("docker-compose.yml", "ci"),
        ("docker-compose.yaml", "ci"),
        (".gitlab-ci.yml", "ci"),
        ("Makefile", "ci"),
    ]
    for name, kind in direct_files:
        path = root / name
        if path.is_file():
            content = _safe_read_text(path, max_bytes_per_file)
            if content is not None:
                signals.append(Signal(kind=kind, path=path, content=content))

    wf_dir = root / ".github" / "workflows"
    if wf_dir.is_dir():
        try:
            for wf in sorted(wf_dir.iterdir()):
                if wf.is_file() and wf.suffix in (".yml", ".yaml"):
                    content = _safe_read_text(wf, max_bytes_per_file)
                    if content is not None:
                        signals.append(Signal(kind="ci", path=wf, content=content))
        except OSError:
            pass

    return signals


def _iter_source_files(root: Path):
    """Yield source files for sampling.

    Two passes:
      1. Recursively walk each `_SOURCE_DIRS` subdir (canonical layouts).
      2. Walk the project root one level deep (catches Django apps at root,
         flat-layout Python packages, root-level Go entry files, Godot scenes
         scattered at root, etc.).

    Junk dirs (`node_modules`, `.venv`, `dist`, …) are skipped at every level.
    """
    seen: set[Path] = set()

    # Pass 1: well-known source dirs (recursive).
    for src_name in _SOURCE_DIRS:
        src_dir = root / src_name
        if not src_dir.is_dir():
            continue
        for path in src_dir.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in _SOURCE_EXTENSIONS:
                continue
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            if path in seen:
                continue
            seen.add(path)
            yield path

    # Pass 2: root + one level deep. Picks up Django apps, flat packages,
    # root-level entry files. Caps depth at 1 to avoid double-walking
    # _SOURCE_DIRS or wandering into docs/ trees.
    try:
        for entry in root.iterdir():
            if entry.name in _SKIP_DIRS:
                continue
            if entry.is_file():
                if entry.suffix.lower() in _SOURCE_EXTENSIONS and entry not in seen:
                    seen.add(entry)
                    yield entry
            elif entry.is_dir() and entry.name not in _SOURCE_DIRS:
                # One level into directories that aren't already covered.
                try:
                    for child in entry.iterdir():
                        if (
                            child.is_file()
                            and child.suffix.lower() in _SOURCE_EXTENSIONS
                            and not any(part in _SKIP_DIRS for part in child.parts)
                            and child not in seen
                        ):
                            seen.add(child)
                            yield child
                except OSError:
                    continue
    except OSError:
        return


def _safe_size(path: Path) -> int:
    """Return file size, or 0 if the file vanished / is unreadable.

    Used as a sort key: a broken symlink or a file removed between
    enumeration and stat must not crash the whole scan.
    """
    try:
        return path.stat().st_size
    except OSError:
        return 0


def collect_source_samples(
    root: Path,
    max_files: int = 30,
    max_bytes_per_file: int = 2048,
) -> list[Signal]:
    """Sample the first N bytes of the largest source files for the AI.

    Replaces an earlier regex-based "extract import-shaped lines" approach
    that was brittle (missed multi-line Go imports, Rust ``mod``/``extern
    crate``, dynamic imports, etc.). Whole-file sampling delegates parsing
    to the AI, which is strictly better at this than any regex we could
    maintain. Costs ~2-3× more tokens per file in the prompt; bounded by
    `max_bytes_per_file` and the per-kind budget in `collect_signals`.

    Ordering by file size (then path for stability) gives deterministic
    samples across runs.
    """
    candidates = list(_iter_source_files(root))
    if not candidates:
        return []

    candidates.sort(key=lambda p: (-_safe_size(p), str(p)))
    chosen = candidates[:max_files]

    signals: list[Signal] = []
    for path in chosen:
        text = _safe_read_text(path, max_bytes_per_file)
        if text is None or not text.strip():
            continue
        signals.append(Signal(kind="source_sample", path=path, content=text))
    return signals


# Backwards-compatible alias for the old name; deprecated, will be removed
# once external callers update. The kind label changed too — tests should
# look for "source_sample" not "source_imports".
def collect_source_imports(*args, **kwargs):  # pragma: no cover - deprecated alias
    """Deprecated alias — use ``collect_source_samples``."""
    return collect_source_samples(*args, **kwargs)


def get_git_remote(root: Path) -> str | None:
    """Return remote.origin.url for ``root``, or None if not a git repo / unavailable."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    remote = result.stdout.strip()
    return remote or None


def infer_project_name(root: Path) -> str:
    """Best-effort project name: directory basename."""
    return root.resolve().name


# Per-kind byte budgets. A global FIFO caused a 50 KB package.json to
# starve README + source samples. Per-kind allocations guarantee each
# signal category gets a fair slice of the prompt. Unused budget in
# earlier kinds is re-allocated to source samples (which scale with the
# project size). Total stays at 64 KB by default.
_DEFAULT_BUDGETS = {
    "manifest": 24_000,
    "readme": 6_000,
    "dockerfile_ci": 6_000,
    "source_sample": 28_000,
}


def collect_signals(
    root: Path,
    max_source_files: int = 30,
    total_byte_budget: int = 64_000,
    budgets: dict[str, int] | None = None,
) -> SignalBundle:
    """Aggregate all signal collectors into a single bundle.

    Signals are partitioned by kind, each with its own byte budget so no
    single fat file (a 50 KB ``package.json``) can crowd out other
    categories. Unused budget in earlier kinds is re-allocated to source
    samples (which scale with project size, unlike manifests/README).

    Args:
        root: project root
        max_source_files: cap for source-sample file count
        total_byte_budget: total prompt-content budget (default 64 KB).
            Kind-specific caps from ``_DEFAULT_BUDGETS`` are scaled
            proportionally if this differs from 64 KB.
        budgets: override per-kind allocations directly. When set,
            ``total_byte_budget`` is ignored.
    """
    bundle = SignalBundle(
        git_remote=get_git_remote(root),
        project_name=infer_project_name(root),
    )

    # Resolve per-kind allocations.
    if budgets is not None:
        kind_budgets = dict(budgets)
    elif total_byte_budget == 64_000:
        kind_budgets = dict(_DEFAULT_BUDGETS)
    else:
        # Scale defaults proportionally to honor a custom total budget.
        scale = total_byte_budget / 64_000
        kind_budgets = {k: max(1, int(v * scale)) for k, v in _DEFAULT_BUDGETS.items()}

    def _add_bounded(signals_in: list[Signal], kind_cap: int) -> int:
        """Add ``signals_in`` up to ``kind_cap`` total bytes. Returns
        unused budget (positive) for downstream re-allocation."""
        used = 0
        for s in signals_in:
            if used + len(s.content) > kind_cap:
                remaining = kind_cap - used
                if remaining > 0:
                    bundle.signals.append(
                        Signal(kind=s.kind, path=s.path, content=s.content[:remaining])
                    )
                    used = kind_cap
                break
            bundle.signals.append(s)
            used += len(s.content)
        return kind_cap - used

    # Manifests first — most reliable signal of declared dependencies.
    surplus = _add_bounded(collect_manifests(root), kind_budgets["manifest"])

    # README — high-signal prose about project intent.
    readme = collect_readme_excerpt(root, max_bytes=kind_budgets["readme"])
    if readme is not None:
        surplus += _add_bounded([readme], kind_budgets["readme"])
    else:
        surplus += kind_budgets["readme"]

    # Dockerfile + CI — captures tools not in manifests (Docker, GHA, …).
    surplus += _add_bounded(
        collect_dockerfile_and_ci(
            root, max_bytes_per_file=kind_budgets["dockerfile_ci"] // 4 or 1024
        ),
        kind_budgets["dockerfile_ci"],
    )

    # Source samples — re-allocate all upstream surplus here so small
    # projects (no Dockerfile/CI) still saturate the budget with actual code.
    samples_budget = kind_budgets["source_sample"] + max(0, surplus)
    _add_bounded(
        collect_source_samples(root, max_files=max_source_files),
        samples_budget,
    )

    return bundle
