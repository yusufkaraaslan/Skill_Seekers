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
import json
import tempfile
import uuid
from pathlib import Path

from .clis import invalidate_installed_cache as _invalidate  # noqa: F401
from .clis import spec_by_id
from .paths import atomic_write, safe_name, state_transaction

FLAT_SUFFIX = {"cursor": ".mdc", "windsurf": ".md", "codex": ".md", "opencode": ".md"}
MAX_FLAT_BYTES = 512 * 1024


def flatten_skill(skill_dir: Path, max_bytes: int = MAX_FLAT_BYTES) -> str:
    """Concatenate SKILL.md with reference files into one markdown document."""
    skill_md = skill_dir if skill_dir.is_file() else skill_dir / "SKILL.md"
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
        raise ValueError("Skill exceeds the flat format limit; use a directory-based target")
    return text


def install_skill_to_cli(skill_dir: Path, cli_id: str, replace: bool = False) -> Path:
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
    name = safe_name(skill_dir.stem if skill_dir.is_file() else skill_dir.name)
    if not skill_dir.is_file() and not (skill_dir / "SKILL.md").is_file():
        raise FileNotFoundError(f"no SKILL.md in {skill_dir}")

    target_root = spec.global_path
    target_root.mkdir(parents=True, exist_ok=True)

    dest = installation_path(name, cli_id)
    with state_transaction():
        if dest.resolve() == skill_dir.resolve():
            return dest
        if dest.is_symlink():
            raise ValueError(f"Refusing to replace a symlink: {dest}")
        if dest.exists() and not replace:
            raise FileExistsError(f"{dest} already exists; enable replacement to overwrite it")
        if spec.kind == "dir":
            staging = Path(tempfile.mkdtemp(prefix=".seeker-install-", dir=target_root))
            staged = staging / name
            backup = target_root / f".seeker-backup-{uuid.uuid4().hex}"
            try:
                if skill_dir.is_file():
                    staged.mkdir()
                    shutil.copy2(skill_dir, staged / "SKILL.md")
                else:
                    shutil.copytree(skill_dir, staged)
                (staged / ".seeker-install.json").write_text(
                    json.dumps({"source": str(skill_dir.resolve())}), encoding="utf-8"
                )
                if dest.exists():
                    dest.rename(backup)
                try:
                    staged.rename(dest)
                except OSError:
                    if backup.exists():
                        backup.rename(dest)
                    raise
                if backup.exists():
                    shutil.rmtree(backup)
            finally:
                shutil.rmtree(staging, ignore_errors=True)
        else:
            atomic_write(dest, flatten_skill(skill_dir).encode("utf-8"))
            atomic_write(
                dest.with_suffix(dest.suffix + ".seeker-install.json"),
                json.dumps({"source": str(skill_dir.resolve())}).encode("utf-8"),
            )
    _invalidate()
    return dest


def installation_path(name: str, cli_id: str) -> Path:
    """Return the exact destination without creating or modifying it."""
    spec = spec_by_id(cli_id)
    safe_name(name)
    return spec.global_path / (
        name if spec.kind == "dir" else name + FLAT_SUFFIX.get(cli_id, ".md")
    )


def uninstall_skill_from_cli(name: str, cli_id: str) -> bool:
    """Remove a previously installed skill artifact from a CLI.

    Returns:
        True when something was removed.
    """
    spec = spec_by_id(cli_id)
    safe_name(name)
    removed = False
    if spec.kind == "dir":
        dest = spec.global_path / name
        if dest.is_dir() and not dest.is_symlink():
            shutil.rmtree(dest)
            removed = True
    else:
        suffix = FLAT_SUFFIX.get(cli_id, ".md")
        dest = spec.global_path / f"{name}{suffix}"
        if dest.is_file():
            dest.unlink()
            dest.with_suffix(dest.suffix + ".seeker-install.json").unlink(missing_ok=True)
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
