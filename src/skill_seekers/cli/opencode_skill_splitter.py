#!/usr/bin/env python3
"""
OpenCode Skill Splitter

Splits large documentation skills into multiple focused sub-skills for
OpenCode's on-demand loading. Reuses existing split_config + generate_router patterns.

Usage:
    skill-seekers opencode-split <skill_directory> [--max-size 50000] [--output-dir output/]
"""

import argparse
import contextlib
import re
import sys
from pathlib import Path
from typing import Any

from skill_seekers.cli.adaptors.opencode import OpenCodeAdaptor


class OpenCodeSkillSplitter:
    """
    Splits large skills into multiple focused sub-skills for OpenCode.

    Strategy:
    1. Read SKILL.md and references
    2. Split by H2 sections in SKILL.md (or by reference files if no sections)
    3. Generate a router SKILL.md that lists all sub-skills
    4. Output each sub-skill with OpenCode-compatible frontmatter
    """

    def __init__(self, skill_dir: str | Path, max_chars: int = 50000):
        self.skill_dir = Path(skill_dir)
        self.max_chars = max_chars
        self.adaptor = OpenCodeAdaptor()

    def needs_splitting(self) -> bool:
        """Check if the skill exceeds the size threshold."""
        total = 0
        skill_md = self.skill_dir / "SKILL.md"
        if skill_md.exists():
            total += skill_md.stat().st_size

        refs_dir = self.skill_dir / "references"
        if refs_dir.exists():
            for f in refs_dir.rglob("*.md"):
                total += f.stat().st_size

        return total > self.max_chars

    def _extract_sections(self, content: str) -> list[dict[str, str]]:
        """
        Extract H2 sections from markdown content.

        Returns list of {title, content} dicts.
        """
        # Strip YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2]

        sections = []
        # Split on ## headers
        pattern = re.compile(r"^## (.+)$", re.MULTILINE)
        matches = list(pattern.finditer(content))

        if not matches:
            return [{"title": "main", "content": content.strip()}]

        # Content before first section
        preamble = content[: matches[0].start()].strip()
        if preamble:
            sections.append({"title": "overview", "content": preamble})

        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            section_content = content[start:end].strip()
            if section_content:
                sections.append({"title": title, "content": f"## {title}\n\n{section_content}"})

        return sections

    def _group_small_sections(self, sections: list[dict[str, str]]) -> list[dict[str, str]]:
        """Merge sections that are too small to be standalone skills."""
        if not sections:
            return sections

        grouped = []
        current = None

        for section in sections:
            if current is None:
                current = dict(section)
                continue

            combined_size = len(current["content"]) + len(section["content"])
            if combined_size < self.max_chars // 4:
                # Merge small sections
                current["title"] = f"{current['title']}-and-{section['title']}"
                current["content"] += f"\n\n{section['content']}"
            else:
                grouped.append(current)
                current = dict(section)

        if current:
            grouped.append(current)

        return grouped

    def split(self, output_dir: str | Path | None = None) -> list[Path]:
        """
        Split the skill into multiple sub-skills.

        Args:
            output_dir: Output directory (default: <skill_dir>-split/)

        Returns:
            List of paths to created sub-skill directories
        """
        if output_dir is None:
            output_dir = self.skill_dir.parent / f"{self.skill_dir.name}-opencode-split"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        skill_name = self.skill_dir.name
        base_name = OpenCodeAdaptor._to_kebab_case(skill_name)

        # Read SKILL.md
        skill_md = self.skill_dir / "SKILL.md"
        if not skill_md.exists():
            print(f"Error: SKILL.md not found in {self.skill_dir}")
            return []

        content = skill_md.read_text(encoding="utf-8")

        # Extract and group sections
        sections = self._extract_sections(content)
        sections = self._group_small_sections(sections)

        if len(sections) <= 1:
            # Try splitting by reference files instead
            sections = self._split_by_references()

        if len(sections) <= 1:
            print(f"Skill {skill_name} has only 1 section, no splitting needed")
            return [self.skill_dir]

        created_dirs = []
        sub_skill_names = []

        # Create sub-skills
        for section in sections:
            section_name = OpenCodeAdaptor._to_kebab_case(section["title"])
            sub_name = f"{base_name}-{section_name}"
            sub_dir = output_dir / sub_name
            sub_dir.mkdir(parents=True, exist_ok=True)

            # Write sub-skill SKILL.md with frontmatter (quote values for YAML safety)
            safe_title = section["title"].replace('"', '\\"')
            safe_skill = skill_name.replace('"', '\\"')
            frontmatter = f"""---
name: {sub_name}
description: "{safe_skill} - {safe_title}"
version: 1.0.0
license: MIT
compatibility: opencode
metadata:
  generated-by: skill-seekers
  source: "{safe_skill}"
  parent-skill: {base_name}
  section: "{safe_title}"
---"""

            sub_content = (
                f"{frontmatter}\n\n# {skill_name} - {section['title']}\n\n{section['content']}"
            )
            (sub_dir / "SKILL.md").write_text(sub_content, encoding="utf-8")

            sub_skill_names.append(sub_name)
            created_dirs.append(sub_dir)

        # Create router skill
        router_dir = output_dir / base_name
        router_dir.mkdir(parents=True, exist_ok=True)

        router_content = self._generate_router(base_name, skill_name, sub_skill_names)
        (router_dir / "SKILL.md").write_text(router_content, encoding="utf-8")
        created_dirs.insert(0, router_dir)

        print(f"Split '{skill_name}' into {len(sub_skill_names)} sub-skills + 1 router:")
        print(f"  Router: {base_name}/")
        for name in sub_skill_names:
            print(f"  Sub-skill: {name}/")

        return created_dirs

    def _split_by_references(self) -> list[dict[str, str]]:
        """Split by reference files when SKILL.md doesn't have enough sections."""
        refs_dir = self.skill_dir / "references"
        if not refs_dir.exists():
            return []

        sections = []
        for ref_file in sorted(refs_dir.glob("*.md")):
            if ref_file.name.startswith(".") or ref_file.name == "index.md":
                continue
            try:
                content = ref_file.read_text(encoding="utf-8")
                title = ref_file.stem.replace("_", " ").replace("-", " ")
                sections.append({"title": title, "content": content})
            except Exception:
                continue

        return sections

    def _generate_router(self, base_name: str, skill_name: str, sub_skill_names: list[str]) -> str:
        """Generate a router SKILL.md that lists all sub-skills."""
        safe_skill = skill_name.replace('"', '\\"')
        frontmatter = f"""---
name: {base_name}
description: "Router for {safe_skill} documentation. Directs to specialized sub-skills."
version: 1.0.0
license: MIT
compatibility: opencode
metadata:
  generated-by: skill-seekers
  source: "{safe_skill}"
  is-router: true
  sub-skills: {len(sub_skill_names)}
---"""

        sub_list = "\n".join(
            f"- `{name}` - {name.replace(base_name + '-', '').replace('-', ' ').title()}"
            for name in sub_skill_names
        )

        body = f"""# {skill_name}

This is a router skill that directs to specialized sub-skills.

## Available Sub-Skills

{sub_list}

## Usage

When answering questions about {skill_name}, load the relevant sub-skill for detailed information.
Each sub-skill covers a specific topic area of the documentation."""

        return f"{frontmatter}\n\n{body}"


class OpenCodeSkillConverter:
    """
    Bi-directional skill format converter.

    Converts between Skill Seekers format and OpenCode ecosystem format.
    """

    @staticmethod
    def import_opencode_skill(source_dir: str | Path) -> dict[str, Any]:
        """
        Import a skill from OpenCode format into Skill Seekers format.

        Reads an OpenCode skill directory and returns a normalized dict
        suitable for further processing by Skill Seekers adaptors.

        Args:
            source_dir: Path to OpenCode skill directory

        Returns:
            Dict with keys: name, description, version, content, references, metadata
        """
        source_dir = Path(source_dir)

        skill_md = source_dir / "SKILL.md"
        if not skill_md.exists():
            raise FileNotFoundError(f"SKILL.md not found in {source_dir}")

        raw = skill_md.read_text(encoding="utf-8")

        # Parse frontmatter
        frontmatter = {}
        content = raw
        if raw.startswith("---"):
            parts = raw.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].strip().splitlines():
                    if ":" in line:
                        key, _, value = line.partition(":")
                        frontmatter[key.strip()] = value.strip()
                content = parts[2].strip()

        # Read references
        references = {}
        refs_dir = source_dir / "references"
        if refs_dir.exists():
            for ref_file in sorted(refs_dir.glob("*.md")):
                if not ref_file.name.startswith("."):
                    with contextlib.suppress(Exception):
                        references[ref_file.name] = ref_file.read_text(encoding="utf-8")

        return {
            "name": frontmatter.get("name", source_dir.name),
            "description": frontmatter.get("description", ""),
            "version": frontmatter.get("version", "1.0.0"),
            "content": content,
            "references": references,
            "metadata": frontmatter,
            "source_format": "opencode",
        }

    @staticmethod
    def export_to_target(
        skill_data: dict[str, Any],
        target: str,
        output_dir: str | Path,
    ) -> Path:
        """
        Export an imported skill to a target platform format.

        Args:
            skill_data: Normalized skill dict from import_opencode_skill()
            target: Target platform ('claude', 'gemini', 'openai', 'markdown', etc.)
            output_dir: Output directory

        Returns:
            Path to the exported skill directory
        """
        from skill_seekers.cli.adaptors import get_adaptor
        from skill_seekers.cli.adaptors.base import SkillMetadata

        output_dir = Path(output_dir)
        skill_dir = output_dir / skill_data["name"]
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Write SKILL.md (raw content without frontmatter for now)
        (skill_dir / "SKILL.md").write_text(skill_data["content"], encoding="utf-8")

        # Write references
        if skill_data.get("references"):
            refs_dir = skill_dir / "references"
            refs_dir.mkdir(exist_ok=True)
            for name, content in skill_data["references"].items():
                (refs_dir / name).write_text(content, encoding="utf-8")

        # Format using target adaptor
        adaptor = get_adaptor(target)
        metadata = SkillMetadata(
            name=skill_data["name"],
            description=skill_data.get("description", ""),
            version=skill_data.get("version", "1.0.0"),
        )

        formatted = adaptor.format_skill_md(skill_dir, metadata)
        (skill_dir / "SKILL.md").write_text(formatted, encoding="utf-8")

        return skill_dir


def main():
    parser = argparse.ArgumentParser(
        prog="skill-seekers-opencode-split",
        description="Split large skills into OpenCode-compatible sub-skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-split a large skill
  skill-seekers opencode-split output/react/

  # Custom size threshold
  skill-seekers opencode-split output/react/ --max-size 30000

  # Custom output directory
  skill-seekers opencode-split output/react/ --output-dir output/react-split/

  # Import an OpenCode skill and convert to Claude format
  skill-seekers opencode-convert ~/.opencode/skills/my-skill/ --target claude --output-dir output/

  # Check if splitting is needed
  skill-seekers opencode-split output/react/ --dry-run
        """,
    )

    subparsers = parser.add_subparsers(dest="command")

    # Split command
    split_parser = subparsers.add_parser("split", help="Split large skill into sub-skills")
    split_parser.add_argument("skill_directory", help="Path to skill directory")
    split_parser.add_argument(
        "--max-size", type=int, default=50000, help="Max chars before splitting (default: 50000)"
    )
    split_parser.add_argument("--output-dir", help="Output directory")
    split_parser.add_argument(
        "--dry-run", action="store_true", help="Check if splitting is needed without making changes"
    )

    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert between skill formats")
    convert_parser.add_argument("source_directory", help="Path to source skill directory")
    convert_parser.add_argument(
        "--target", required=True, help="Target platform (claude, gemini, openai, markdown, etc.)"
    )
    convert_parser.add_argument("--output-dir", required=True, help="Output directory")

    args = parser.parse_args()

    if args.command == "split" or (not hasattr(args, "command") or args.command is None):
        # Default to split if no subcommand but has positional arg
        if not hasattr(args, "skill_directory"):
            parser.print_help()
            return 1

        splitter = OpenCodeSkillSplitter(args.skill_directory, args.max_size)

        if args.dry_run:
            if splitter.needs_splitting():
                print(f"Skill needs splitting (exceeds {args.max_size} chars)")
            else:
                print(f"Skill does not need splitting (under {args.max_size} chars)")
            return 0

        result = splitter.split(args.output_dir)
        return 0 if result else 1

    elif args.command == "convert":
        try:
            skill_data = OpenCodeSkillConverter.import_opencode_skill(args.source_directory)
            result = OpenCodeSkillConverter.export_to_target(
                skill_data, args.target, args.output_dir
            )
            print(f"Converted skill to {args.target} format: {result}")
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
