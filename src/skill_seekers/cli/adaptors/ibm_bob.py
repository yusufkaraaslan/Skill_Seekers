#!/usr/bin/env python3
"""
IBM Bob Adaptor

Generates skills in IBM Bob-compatible format.
Bob discovers skills in project or global `.bob/skills/` directories.
"""

import re
import shutil
from pathlib import Path
from typing import Any

from .base import SkillAdaptor, SkillMetadata
from skill_seekers.cli.arguments.common import DEFAULT_CHUNK_OVERLAP_TOKENS, DEFAULT_CHUNK_TOKENS


class IBMBobAdaptor(SkillAdaptor):
    """
    IBM Bob platform adaptor.

    Packages a skill into a Bob-ready directory layout:
    `.bob/skills/<skill-name>/SKILL.md`
    """

    PLATFORM = "ibm-bob"
    PLATFORM_NAME = "IBM Bob"
    DEFAULT_API_ENDPOINT = None  # Local file-based, no upload API

    @staticmethod
    def _to_skill_dir_name(name: str) -> str:
        """Normalize a skill name to a filesystem-friendly Bob directory name."""
        result = name.lower()
        result = re.sub(r"[_\s.]+", "-", result)
        result = re.sub(r"[^a-z0-9-]", "", result)
        result = re.sub(r"-+", "-", result)
        result = result.strip("-")
        return result or "skill"

    @staticmethod
    def _quote_yaml(value: str) -> str:
        """Quote a YAML string to safely preserve punctuation."""
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'

    def format_skill_md(self, skill_dir: Path, metadata: SkillMetadata) -> str:
        """
        Format SKILL.md with Bob-compatible YAML frontmatter.

        Bob requires `name` and `description` and accepts additional metadata.
        """
        existing_content = self._read_existing_content(skill_dir)
        body = (
            existing_content
            if existing_content
            else f"# {metadata.name}\n\n{metadata.description}\n"
        )

        tags = metadata.tags or [self._to_skill_dir_name(metadata.name)]
        tag_lines = "\n".join(f"  - {tag}" for tag in tags)
        author_line = f"\nauthor: {self._quote_yaml(metadata.author)}" if metadata.author else ""

        frontmatter = (
            f"---\n"
            f"name: {self._quote_yaml(metadata.name)}\n"
            f"description: {self._quote_yaml(metadata.description)}\n"
            f"version: {self._quote_yaml(metadata.version)}\n"
            f"tags:\n{tag_lines}"
            f"{author_line}\n"
            f"---"
        )

        return f"{frontmatter}\n\n{body.strip()}\n"

    def package(
        self,
        skill_dir: Path,
        output_path: Path,
        enable_chunking: bool = False,
        chunk_max_tokens: int = DEFAULT_CHUNK_TOKENS,
        preserve_code_blocks: bool = True,
        chunk_overlap_tokens: int = DEFAULT_CHUNK_OVERLAP_TOKENS,
    ) -> Path:
        """
        Package a skill as a Bob-ready directory tree.

        Creates:
        `<output>/<name>-ibm-bob/.bob/skills/<normalized-name>/SKILL.md`
        """
        del enable_chunking, chunk_max_tokens, preserve_code_blocks, chunk_overlap_tokens

        skill_dir = Path(skill_dir)
        output_path = Path(output_path)
        dir_name = f"{skill_dir.name}-ibm-bob"

        if output_path.is_dir() or str(output_path).endswith("/"):
            target_dir = output_path / dir_name
        else:
            target_dir = output_path

        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        metadata = self._build_skill_metadata(skill_dir)
        skill_name = self._to_skill_dir_name(metadata.name or skill_dir.name)
        bob_skill_dir = target_dir / ".bob" / "skills" / skill_name
        bob_skill_dir.mkdir(parents=True, exist_ok=True)

        (bob_skill_dir / "SKILL.md").write_text(
            self.format_skill_md(skill_dir, metadata),
            encoding="utf-8",
        )

        for subdir in ("references", "scripts", "assets"):
            source_dir = skill_dir / subdir
            if source_dir.exists():
                shutil.copytree(
                    source_dir,
                    bob_skill_dir / subdir,
                    ignore=shutil.ignore_patterns("*.backup", ".*"),
                )

        return target_dir

    def upload(self, package_path: Path, api_key: str, **kwargs) -> dict[str, Any]:
        """IBM Bob uses local project/global folders rather than an upload API."""
        del api_key, kwargs
        package_path = Path(package_path)
        return {
            "success": True,
            "skill_id": None,
            "url": None,
            "message": f"IBM Bob skill packaged at: {package_path} (local install only)",
        }

    def validate_api_key(self, api_key: str) -> bool:
        """No API key needed for IBM Bob."""
        del api_key
        return True

    def get_env_var_name(self) -> str:
        """IBM Bob packaging does not require an API key."""
        return ""

    def supports_enhancement(self) -> bool:
        """IBM Bob does not expose a packaging-time enhancement API."""
        return False
