"""Detection of AI CLI tools installed on the local machine.

Probes well-known config/skill directories and binaries on PATH, and
extracts a best-effort version string. This powers the Settings → CLI
detection grid and the "installed on" chips across the UI.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CliSpec:
    """Static knowledge about a supported CLI."""

    id: str
    name: str
    short: str
    color: str  # hsl string used by the HUD
    binary: str  # binary probed on PATH for version
    global_path: Path  # where skills/rules are installed globally
    kind: str  # "dir" (skill dir copied) or "flat" (single flattened file)
    alt_paths: tuple[Path, ...] = ()
    scan_roots: tuple[Path, ...] = ()  # extra roots scanned recursively for installed skills


def _build_cli_specs() -> list[CliSpec]:
    """Build CLI specs with paths resolved against the *current* home dir.

    Evaluated lazily (not at import) so tests can redirect HOME.
    """
    home = Path.home()
    return [
        CliSpec(
            id="claude",
            name="Claude Code",
            short="CLA",
            color="24 85% 60%",
            binary="claude",
            global_path=home / ".claude" / "skills",
            kind="dir",
            # plugin bundles + marketplace cache:
            # <plugin>/skills/<name>/SKILL.md and
            # cache/<market>/<plugin>/<ver>/.claude/skills/<name>/SKILL.md
            scan_roots=(home / ".claude" / "plugins",),
        ),
        CliSpec(
            id="kimi",
            name="Kimi CLI",
            short="KIM",
            color="258 90% 66%",
            binary="kimi",
            global_path=home / ".kimi" / "skills",
            kind="dir",
        ),
        CliSpec(
            id="cursor",
            name="Cursor",
            short="CUR",
            color="199 89% 55%",
            binary="cursor",
            global_path=home / ".cursor" / "skills",
            kind="dir",
            alt_paths=(home / ".agents" / "skills",),
        ),
        CliSpec(
            id="windsurf",
            name="Windsurf",
            short="WIN",
            color="172 70% 45%",
            binary="windsurf",
            global_path=home / ".codeium" / "windsurf" / "skills",
            kind="dir",
        ),
        CliSpec(
            id="gemini",
            name="Gemini CLI",
            short="GEM",
            color="217 89% 61%",
            binary="gemini",
            global_path=home / ".gemini" / "skills",
            kind="dir",
        ),
        CliSpec(
            id="codex",
            name="Codex CLI",
            short="CDX",
            color="152 60% 42%",
            binary="codex",
            global_path=home / ".agents" / "skills",
            kind="dir",
            alt_paths=(home / ".codex" / "skills",),
        ),
        CliSpec(
            id="opencode",
            name="OpenCode",
            short="OPC",
            color="330 70% 60%",
            binary="opencode",
            global_path=home / ".config" / "opencode" / "skills",
            kind="dir",
            alt_paths=(home / ".claude" / "skills", home / ".agents" / "skills"),
        ),
    ]


def get_cli_specs() -> list[CliSpec]:
    """Current CLI specs (paths resolved against the live home dir)."""
    return _build_cli_specs()


def spec_by_id(cli_id: str) -> CliSpec:
    """Look up a CliSpec by id (raises KeyError for unknown ids)."""
    for spec in get_cli_specs():
        if spec.id == cli_id:
            return spec
    raise KeyError(f"unknown CLI id: {cli_id}")


def _probe_version(binary: str) -> str | None:
    """Run ``<binary> --version`` and extract a semver-ish token."""
    if not shutil.which(binary):
        return None
    try:
        out = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        text = (out.stdout or out.stderr or "").strip()
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.search(r"\d+\.\d+(?:\.\d+)?(?:[-\w.]*)", text)
    return m.group(0) if m else (text.splitlines()[0][:24] if text else None)


_installed_cache: dict[CliSpec, tuple[float, list[tuple[str, Path]]]] = {}
INSTALLED_CACHE_TTL = 30.0

# Top-level dirs under ~/.claude/plugins that are catalogue clones or state,
# not installed plugins: marketplaces/ is a git clone of the whole registry.
PLUGIN_ROOT_SKIP = frozenset({"marketplaces", "repos", "data"})
_SKIP_ANYWHERE = frozenset({"node_modules", ".git"})


def iter_installed_skills(spec: CliSpec) -> list[tuple[str, Path]]:
    """Yield (name, skill_dir) for every skill installed for a CLI.

    Covers the global skills dir (direct children with SKILL.md) plus any
    scan_roots searched recursively (plugin bundles, marketplace caches).
    Results are deduplicated by resolved location, preserving duplicate names. Cached for
    INSTALLED_CACHE_TTL seconds since recursive scans are expensive.
    """
    import time

    cached = _installed_cache.get(spec)
    now = time.time()
    if cached and now - cached[0] < INSTALLED_CACHE_TTL:
        return cached[1]

    found: dict[Path, tuple[str, Path]] = {}
    if spec.kind == "dir":
        if spec.global_path.is_dir():
            for p in sorted(spec.global_path.iterdir()):
                if not p.name.startswith(".") and p.is_dir() and (p / "SKILL.md").is_file():
                    found.setdefault(p.resolve(), (p.name, p))
                elif spec.id == "opencode" and p.is_file() and p.suffix == ".md":
                    found.setdefault(p.resolve(), (p.stem, p))
        for root in (*spec.scan_roots, spec.global_path, *spec.alt_paths):
            if not root.is_dir():
                continue
            import os

            # Prune catalogue/dependency trees before reading their contents.
            for directory, subdirs, files in os.walk(root, followlinks=False):
                current = Path(directory)
                subdirs[:] = sorted(
                    d
                    for d in subdirs
                    if not d.startswith(".seeker-")
                    and d not in _SKIP_ANYWHERE
                    and (current != root or d not in PLUGIN_ROOT_SKIP)
                )
                if "SKILL.md" in files:
                    found.setdefault(current.resolve(), (current.name, current))
                    subdirs.clear()  # nested SKILL.md files belong to this skill
    else:
        if spec.global_path.is_dir():
            for p in sorted(spec.global_path.iterdir()):
                if p.is_file() and p.suffix in (".md", ".mdc"):
                    found.setdefault(p.resolve(), (p.stem, p))
    for alternate in spec.alt_paths:
        if alternate.is_dir():
            for p in sorted(alternate.iterdir()):
                if spec.kind == "dir" and (p / "SKILL.md").is_file():
                    found.setdefault(p.resolve(), (p.name, p))
                elif spec.kind == "flat" and p.is_file() and p.suffix in (".md", ".mdc"):
                    found.setdefault(p.resolve(), (p.stem, p))
    result = list(found.values())
    _installed_cache[spec] = (now, result)
    return result


def invalidate_installed_cache() -> None:
    """Drop the installed-skills cache (after installs/uninstalls)."""
    _installed_cache.clear()


def _count_installed(spec: CliSpec) -> int:
    """Count skills currently installed in the CLI's known locations."""
    return len(iter_installed_skills(spec))


def detect_clis() -> list[dict]:
    """Probe all known CLIs; returns UI-ready dicts."""
    home = str(Path.home())
    results = []
    for spec in get_cli_specs():
        version = _probe_version(spec.binary)
        path_exists = spec.global_path.exists() or any(p.exists() for p in spec.alt_paths)
        detected = bool(version) or path_exists
        results.append(
            {
                "id": spec.id,
                "name": spec.name,
                "short": spec.short,
                "color": spec.color,
                "version": version or "—",
                "globalPath": str(spec.global_path).replace(home, "~"),
                "detected": detected,
                "skillCount": _count_installed(spec) if detected else 0,
            }
        )
    return results


# ── plugin path helpers ───────────────────────────────────────────────────────


def _plugins_root() -> Path:
    return Path.home() / ".claude" / "plugins"


def _relative_to_plugins(skill_dir: Path) -> tuple[str, ...] | None:
    try:
        return skill_dir.resolve().relative_to(_plugins_root().resolve()).parts
    except ValueError:
        return None


def is_under_plugins(skill_dir: Path) -> bool:
    """True when the directory lives inside ~/.claude/plugins."""
    return _relative_to_plugins(skill_dir) is not None


def plugin_name_for(skill_dir: Path) -> str | None:
    """Best-effort plugin name for a skill dir under ~/.claude/plugins.

    Layouts handled:
      <plugin>/skills/<skill>
      <plugin>/.claude/skills/<skill>
      cache/<marketplace>/<plugin>/<version>/skills/<skill>
      cache/<marketplace>/<plugin>/<version>/.claude/skills/<skill>
    Returns None for anything else (caller keeps origin "plugin").
    """
    parts = _relative_to_plugins(skill_dir)
    if not parts:
        return None
    if parts[0] == "cache":
        return parts[2] if len(parts) > 2 else None
    if "skills" not in parts:
        return None
    i = parts.index("skills") - 1
    if i >= 0 and parts[i] == ".claude":
        i -= 1
    return parts[i] if i >= 0 else None
