"""Install ("port") built skills into AI CLI global locations.

Two install styles exist across CLIs:

- ``dir``  — the skill directory is copied as-is (SKILL.md + references/…),
  e.g. Claude Code's ``~/.claude/skills/<name>/``.
- ``flat`` — the CLI consumes a single markdown file, so SKILL.md and its
  references are flattened into one document, e.g. Cursor ``.mdc`` rules.

Uninstall removes whatever ``install_skill_to_cli`` created.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .clis import invalidate_installed_cache as _invalidate  # noqa: F401
from .clis import spec_by_id

FLAT_SUFFIX = {"cursor": ".mdc", "windsurf": ".md", "codex": ".md", "opencode": ".md"}
MAX_FLAT_BYTES = 512 * 1024


def flatten_skill(skill_dir: Path, max_bytes: int = MAX_FLAT_BYTES) -> str:
    """Concatenate SKILL.md with reference files into one markdown document."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise FileNotFoundError(f"no SKILL.md in {skill_dir}")
    parts = [skill_md.read_text(encoding="utf-8", errors="replace")]
    refs = skill_dir / "references"
    if refs.is_dir():
        for path in sorted(refs.rglob("*.md")):
            rel = path.relative_to(skill_dir)
            parts.append(f"\n\n<!-- {rel} -->\n\n")
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
    text = "".join(parts)
    if len(text.encode("utf-8")) > max_bytes:
        text = text[:max_bytes] + "\n\n<!-- truncated: bundle exceeded flat format limit -->\n"
    return text


def install_skill_to_cli(skill_dir: Path, cli_id: str) -> Path:
    """Install a built skill into a CLI's global location.

    Args:
        skill_dir: Built skill directory containing SKILL.md.
        cli_id: One of the CLI ids from clis.CLI_SPECS.

    Returns:
        Path to the installed artifact (directory or file).

    Raises:
        FileNotFoundError: If skill_dir has no SKILL.md.
    """
    spec = spec_by_id(cli_id)
    name = skill_dir.name
    if not (skill_dir / "SKILL.md").is_file():
        raise FileNotFoundError(f"no SKILL.md in {skill_dir}")

    target_root = spec.global_path
    target_root.mkdir(parents=True, exist_ok=True)

    if spec.kind == "dir":
        dest = target_root / name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        _invalidate()
        return dest

    suffix = FLAT_SUFFIX.get(cli_id, ".md")
    dest = target_root / f"{name}{suffix}"
    dest.write_text(flatten_skill(skill_dir), encoding="utf-8")
    _invalidate()
    return dest


def uninstall_skill_from_cli(name: str, cli_id: str) -> bool:
    """Remove a previously installed skill artifact from a CLI.

    Returns:
        True when something was removed.
    """
    spec = spec_by_id(cli_id)
    removed = False
    if spec.kind == "dir":
        dest = spec.global_path / name
        if dest.is_dir():
            shutil.rmtree(dest)
            removed = True
    else:
        suffix = FLAT_SUFFIX.get(cli_id, ".md")
        dest = spec.global_path / f"{name}{suffix}"
        if dest.is_file():
            dest.unlink()
            removed = True
    if removed:
        _invalidate()
    return removed


def installed_clis_for(name: str) -> list[str]:
    """Return ids of CLIs where a skill named ``name`` is currently installed."""
    from .clis import get_cli_specs, iter_installed_skills

    found: list[str] = []
    for spec in get_cli_specs():
        installed_names = {n for n, _ in iter_installed_skills(spec)}
        if name in installed_names:
            found.append(spec.id)
    return found
