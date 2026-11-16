"""Bounded document input and durable output for enhancement workflows."""

import json
import logging
import re
from pathlib import Path

from skill_seekers.cli.adaptors.base import save_skill_md_atomic

logger = logging.getLogger(__name__)
MAX_DOCUMENT_CHARS = 32_000
MAX_CONTEXT_CHARS = 100_000
MAX_DOCUMENTS = 64
_FRONTMATTER = re.compile(r"\A---\r?\n.*?\r?\n---(?:\r?\n|\Z)", re.DOTALL)


def load_workflow_documents(skill_dir: Path) -> dict:
    """Read SKILL.md and Markdown references with explicit size limits.

    Symlinks outside the skill directory are excluded. Paths in the model's
    response or prompt variables never select files for reading or writing.
    """
    root = skill_dir.resolve()
    documents = []
    remaining = MAX_CONTEXT_CHARS
    truncated = False
    skill_truncated = False
    paths = [root / "SKILL.md", *sorted((root / "references").rglob("*.md"))]
    for path in paths:
        if not path.is_file() or not path.resolve().is_relative_to(root):
            continue
        if len(documents) >= MAX_DOCUMENTS or remaining <= 0:
            truncated = True
            break
        limit = min(MAX_DOCUMENT_CHARS, remaining)
        with path.open(encoding="utf-8", errors="replace") as stream:
            text = stream.read(limit + 1)
        cut = len(text) > limit
        relative = path.relative_to(root).as_posix()
        documents.append({"path": relative, "content": text[:limit], "truncated": cut})
        truncated |= cut
        if relative == "SKILL.md":
            skill_truncated = cut
        remaining -= len(text[:limit])
    if truncated:
        logger.warning("Workflow document input was truncated to its size limits.")
    return {
        "skill_dir": str(root),
        "skill_md_path": str(root / "SKILL.md"),
        "source_name": root.name,
        "source_files": "\n".join(doc["path"] for doc in documents),
        "documents": documents,
        "documents_truncated": truncated,
        "skill_truncated": skill_truncated,
    }


def save_workflow_results(skill_dir: Path, records: list[dict], context: dict) -> None:
    """Save analysis results and apply only an explicit, complete skill replacement."""
    root = skill_dir.resolve()
    if not root.is_dir():
        raise ValueError(f"Workflow output directory does not exist: {root}")
    results = records[-1]["results"]
    replacement = results.get("skill_md")
    # Existing presets also return structured advice under this target. Keep
    # those results in the report; only an explicit Markdown string is a rewrite.
    if not isinstance(replacement, str):
        replacement = None
    skill_path = root / "SKILL.md"
    if replacement is not None:
        if not isinstance(replacement, str) or not replacement.strip():
            raise ValueError("skill_md must be a nonempty string containing the complete Markdown")
        if context.get("skill_truncated"):
            raise ValueError("Cannot replace SKILL.md from truncated input")
        if not skill_path.is_file() or skill_path.is_symlink():
            raise ValueError("Workflow replacement requires an existing, regular SKILL.md")
        original = skill_path.read_text(encoding="utf-8")
        # Preserve identity/metadata even if the model omits or changes it.
        frontmatter = _FRONTMATTER.match(original)
        if frontmatter:
            replacement = (
                frontmatter.group() + "\n" + _FRONTMATTER.sub("", replacement, count=1).lstrip()
            )
        if not re.search(r"^#{1,6} \S", _FRONTMATTER.sub("", replacement, count=1), re.MULTILINE):
            raise ValueError("skill_md must contain a Markdown heading, not just a status message")
    report = root / "workflow_results.json"
    temporary = report.with_suffix(".json.tmp")
    if report.is_symlink() or temporary.is_symlink():
        raise ValueError("Workflow result files must not be symlinks")
    try:
        temporary.write_text(
            json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        if replacement is not None:
            if (
                skill_path.with_suffix(".md.tmp").is_symlink()
                or skill_path.with_suffix(".md.backup").is_symlink()
            ):
                raise ValueError("Workflow skill backup/temp paths must not be symlinks")
            save_skill_md_atomic(skill_path, replacement)
        temporary.replace(report)
    finally:
        temporary.unlink(missing_ok=True)
