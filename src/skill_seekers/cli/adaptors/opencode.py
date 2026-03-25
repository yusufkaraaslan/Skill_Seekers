#!/usr/bin/env python3
"""
OpenCode Adaptor

Generates skills in OpenCode-compatible format with YAML frontmatter.
OpenCode searches ~/.opencode/skills/ for SKILL.md files.
"""

import re
import shutil
from pathlib import Path
from typing import Any

from .base import SkillAdaptor, SkillMetadata
from skill_seekers.cli.arguments.common import DEFAULT_CHUNK_TOKENS, DEFAULT_CHUNK_OVERLAP_TOKENS


class OpenCodeAdaptor(SkillAdaptor):
    """
    OpenCode platform adaptor.

    Generates directory-based skill packages with dual-format YAML frontmatter
    compatible with both OpenCode and Claude Code.
    """

    PLATFORM = "opencode"
    PLATFORM_NAME = "OpenCode"
    DEFAULT_API_ENDPOINT = None  # Local file-based, no API

    # OpenCode name validation: kebab-case, 1-64 chars
    NAME_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

    @staticmethod
    def _to_kebab_case(name: str) -> str:
        """
        Convert any title/name to valid OpenCode kebab-case.

        Rules:
        - Lowercase
        - Replace spaces, underscores, dots with hyphens
        - Remove non-alphanumeric chars (except hyphens)
        - Collapse multiple hyphens
        - Strip leading/trailing hyphens
        - Truncate to 64 chars

        Args:
            name: Input name string

        Returns:
            Valid kebab-case name (1-64 chars)
        """
        result = name.lower()
        result = re.sub(r"[_\s.]+", "-", result)
        result = re.sub(r"[^a-z0-9-]", "", result)
        result = re.sub(r"-+", "-", result)
        result = result.strip("-")
        result = result[:64]
        result = result.rstrip("-")
        return result or "skill"

    def format_skill_md(self, skill_dir: Path, metadata: SkillMetadata) -> str:
        """
        Format SKILL.md with OpenCode-compatible YAML frontmatter.

        Generates a superset frontmatter that works with both Claude and OpenCode.
        OpenCode-required fields: kebab-case name, compatibility, metadata map.

        Args:
            skill_dir: Path to skill directory
            metadata: Skill metadata

        Returns:
            Formatted SKILL.md content with YAML frontmatter
        """
        existing_content = self._read_existing_content(skill_dir)
        kebab_name = self._to_kebab_case(metadata.name)
        description = metadata.description[:1024] if metadata.description else ""

        # Quote description to handle colons and special YAML chars
        safe_desc = description.replace('"', '\\"')
        safe_source = metadata.name.replace('"', '\\"')

        frontmatter = f"""---
name: {kebab_name}
description: "{safe_desc}"
version: {metadata.version}
license: MIT
compatibility: opencode
metadata:
  generated-by: skill-seekers
  source: "{safe_source}"
  version: {metadata.version}
---"""

        if existing_content and len(existing_content) > 100:
            return f"{frontmatter}\n\n{existing_content}"

        toc = self._generate_toc(skill_dir)
        quick_ref = self._extract_quick_reference(skill_dir)

        body = f"""# {metadata.name}

{metadata.description}

## Documentation

{toc if toc else "See references/ directory for documentation."}

## Quick Reference

{quick_ref}"""

        return f"{frontmatter}\n\n{body}"

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
        Package skill as a directory (not ZIP) for OpenCode.

        Creates: <output>/<name>-opencode/SKILL.md + references/

        Args:
            skill_dir: Path to skill directory
            output_path: Output path for the package directory

        Returns:
            Path to created directory
        """
        skill_dir = Path(skill_dir)
        output_path = Path(output_path)

        dir_name = f"{skill_dir.name}-opencode"

        if output_path.is_dir() or str(output_path).endswith("/"):
            target_dir = output_path / dir_name
        else:
            target_dir = output_path

        # Clean and create target
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy SKILL.md
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            shutil.copy2(skill_md, target_dir / "SKILL.md")

        # Copy references
        refs_dir = skill_dir / "references"
        if refs_dir.exists():
            target_refs = target_dir / "references"
            shutil.copytree(
                refs_dir,
                target_refs,
                ignore=shutil.ignore_patterns("*.backup", ".*"),
            )

        return target_dir

    def upload(self, package_path: Path, api_key: str, **kwargs) -> dict[str, Any]:
        """
        OpenCode uses local files, no upload needed.

        Returns local path information.
        """
        package_path = Path(package_path)
        return {
            "success": True,
            "skill_id": None,
            "url": None,
            "message": f"OpenCode skill packaged at: {package_path} (local install only)",
        }

    def validate_api_key(self, api_key: str) -> bool:
        """No API key needed for OpenCode."""
        return True

    def supports_enhancement(self) -> bool:
        """OpenCode does not have its own enhancement API."""
        return False
