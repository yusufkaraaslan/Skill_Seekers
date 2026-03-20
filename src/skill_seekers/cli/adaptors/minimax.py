#!/usr/bin/env python3
"""
MiniMax AI Adaptor

Implements platform-specific handling for MiniMax AI skills.
Uses MiniMax's OpenAI-compatible API for AI enhancement with M2.7 model.
"""

import json
import zipfile
from pathlib import Path
from typing import Any

from .base import SkillAdaptor, SkillMetadata
from skill_seekers.cli.arguments.common import DEFAULT_CHUNK_TOKENS, DEFAULT_CHUNK_OVERLAP_TOKENS


class MiniMaxAdaptor(SkillAdaptor):
    """
    MiniMax AI platform adaptor.

    Handles:
    - System instructions format (plain text, no YAML frontmatter)
    - ZIP packaging with knowledge files
    - AI enhancement using MiniMax-M2.7
    """

    PLATFORM = "minimax"
    PLATFORM_NAME = "MiniMax AI"
    DEFAULT_API_ENDPOINT = "https://api.minimax.io/v1"

    def format_skill_md(self, skill_dir: Path, metadata: SkillMetadata) -> str:
        """
        Format SKILL.md as system instructions for MiniMax AI.

        MiniMax uses OpenAI-compatible chat completions, so instructions
        are formatted as clear system prompts without YAML frontmatter.

        Args:
            skill_dir: Path to skill directory
            metadata: Skill metadata

        Returns:
            Formatted instructions for MiniMax AI
        """
        existing_content = self._read_existing_content(skill_dir)

        if existing_content and len(existing_content) > 100:
            content_body = f"""You are an expert assistant for {metadata.name}.

{metadata.description}

Use the attached knowledge files to provide accurate, detailed answers about {metadata.name}.

{existing_content}

## How to Assist Users

When users ask questions:
1. Search the knowledge files for relevant information
2. Provide clear, practical answers with code examples
3. Reference specific documentation sections when helpful
4. Be concise but thorough

Always prioritize accuracy by consulting the knowledge base before responding."""
        else:
            content_body = f"""You are an expert assistant for {metadata.name}.

{metadata.description}

## Your Knowledge Base

You have access to comprehensive documentation files about {metadata.name}. Use these files to provide accurate answers to user questions.

{self._generate_toc(skill_dir)}

## Quick Reference

{self._extract_quick_reference(skill_dir)}

## How to Assist Users

When users ask questions about {metadata.name}:

1. **Search the knowledge files** - Find relevant information in the documentation
2. **Provide code examples** - Include practical, working code snippets
3. **Reference documentation** - Cite specific sections when helpful
4. **Be practical** - Focus on real-world usage and best practices
5. **Stay accurate** - Always verify information against the knowledge base

## Response Guidelines

- Keep answers clear and concise
- Use proper code formatting with language tags
- Provide both simple and detailed explanations as needed
- Suggest related topics when relevant
- Admit when information isn't in the knowledge base

Always prioritize accuracy by consulting the attached documentation files before responding."""

        return content_body

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
        Package skill into ZIP file for MiniMax AI.

        Creates MiniMax-compatible structure:
        - system_instructions.txt (main instructions)
        - knowledge_files/*.md (reference files)
        - minimax_metadata.json (skill metadata)

        Args:
            skill_dir: Path to skill directory
            output_path: Output path/filename for ZIP

        Returns:
            Path to created ZIP file
        """
        skill_dir = Path(skill_dir)

        if output_path.is_dir() or str(output_path).endswith("/"):
            output_path = Path(output_path) / f"{skill_dir.name}-minimax.zip"
        elif not str(output_path).endswith(".zip") and not str(output_path).endswith(
            "-minimax.zip"
        ):
            output_str = str(output_path).replace(".zip", "-minimax.zip")
            if not output_str.endswith(".zip"):
                output_str += ".zip"
            output_path = Path(output_str)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                instructions = skill_md.read_text(encoding="utf-8")
                zf.writestr("system_instructions.txt", instructions)

            refs_dir = skill_dir / "references"
            if refs_dir.exists():
                for ref_file in refs_dir.rglob("*.md"):
                    if ref_file.is_file() and not ref_file.name.startswith("."):
                        arcname = f"knowledge_files/{ref_file.name}"
                        zf.write(ref_file, arcname)

            metadata = {
                "platform": "minimax",
                "name": skill_dir.name,
                "version": "1.0.0",
                "created_with": "skill-seekers",
                "model": "MiniMax-M2.7",
                "api_base": "https://api.minimax.io/v1",
            }

            zf.writestr("minimax_metadata.json", json.dumps(metadata, indent=2))

        return output_path

    def upload(self, package_path: Path, api_key: str, **kwargs) -> dict[str, Any]:
        """
        Upload packaged skill to MiniMax AI.

        MiniMax uses an OpenAI-compatible chat completion API.
        This method validates the package and prepares it for use
        with the MiniMax API.

        Args:
            package_path: Path to skill ZIP file
            api_key: MiniMax API key
            **kwargs: Additional arguments (model, etc.)

        Returns:
            Dictionary with upload result
        """
        package_path = Path(package_path)
        if not package_path.exists():
            return {
                "success": False,
                "skill_id": None,
                "url": None,
                "message": f"File not found: {package_path}",
            }

        if package_path.suffix != ".zip":
            return {
                "success": False,
                "skill_id": None,
                "url": None,
                "message": f"Not a ZIP file: {package_path}",
            }

        try:
            from openai import OpenAI
        except ImportError:
            return {
                "success": False,
                "skill_id": None,
                "url": None,
                "message": "openai library not installed. Run: pip install openai",
            }

        try:
            import tempfile

            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(package_path, "r") as zf:
                    zf.extractall(temp_dir)

                temp_path = Path(temp_dir)

                instructions_file = temp_path / "system_instructions.txt"
                if not instructions_file.exists():
                    return {
                        "success": False,
                        "skill_id": None,
                        "url": None,
                        "message": "Invalid package: system_instructions.txt not found",
                    }

                instructions = instructions_file.read_text(encoding="utf-8")

                metadata_file = temp_path / "minimax_metadata.json"
                skill_name = package_path.stem
                model = kwargs.get("model", "MiniMax-M2.7")

                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                        skill_name = metadata.get("name", skill_name)
                        model = metadata.get("model", model)

                knowledge_dir = temp_path / "knowledge_files"
                knowledge_count = 0
                if knowledge_dir.exists():
                    knowledge_count = len(list(knowledge_dir.glob("*.md")))

                client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.minimax.io/v1",
                )

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": instructions},
                        {
                            "role": "user",
                            "content": f"Confirm you are ready to assist with {skill_name}. Reply briefly.",
                        },
                    ],
                    temperature=0.3,
                    max_tokens=100,
                )

                return {
                    "success": True,
                    "skill_id": None,
                    "url": "https://platform.minimaxi.com/",
                    "message": f"Skill '{skill_name}' validated with MiniMax {model} ({knowledge_count} knowledge files)",
                }

        except Exception as e:
            return {
                "success": False,
                "skill_id": None,
                "url": None,
                "message": f"Upload failed: {str(e)}",
            }

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate MiniMax API key format.

        MiniMax API keys typically start with 'eyJ' (JWT format).

        Args:
            api_key: API key to validate

        Returns:
            True if key format appears valid
        """
        key = api_key.strip()
        if not key or len(key) < 10:
            return False
        return True

    def get_env_var_name(self) -> str:
        """
        Get environment variable name for MiniMax API key.

        Returns:
            'MINIMAX_API_KEY'
        """
        return "MINIMAX_API_KEY"

    def supports_enhancement(self) -> bool:
        """
        MiniMax supports AI enhancement via MiniMax-M2.7.

        Returns:
            True
        """
        return True

    def enhance(self, skill_dir: Path, api_key: str) -> bool:
        """
        Enhance SKILL.md using MiniMax-M2.7 API.

        Uses MiniMax's OpenAI-compatible API endpoint for enhancement.

        Args:
            skill_dir: Path to skill directory
            api_key: MiniMax API key

        Returns:
            True if enhancement succeeded
        """
        try:
            from openai import OpenAI
        except ImportError:
            print("❌ Error: openai package not installed")
            print("Install with: pip install openai")
            return False

        skill_dir = Path(skill_dir)
        references_dir = skill_dir / "references"
        skill_md_path = skill_dir / "SKILL.md"

        print("📖 Reading reference documentation...")
        references = self._read_reference_files(references_dir)

        if not references:
            print("❌ No reference files found to analyze")
            return False

        print(f"  ✓ Read {len(references)} reference files")
        total_size = sum(len(c) for c in references.values())
        print(f"  ✓ Total size: {total_size:,} characters\n")

        current_skill_md = None
        if skill_md_path.exists():
            current_skill_md = skill_md_path.read_text(encoding="utf-8")
            print(f"  ℹ Found existing SKILL.md ({len(current_skill_md)} chars)")
        else:
            print("  ℹ No existing SKILL.md, will create new one")

        prompt = self._build_enhancement_prompt(skill_dir.name, references, current_skill_md)

        print("\n🤖 Asking MiniMax-M2.7 to enhance SKILL.md...")
        print(f"   Input: {len(prompt):,} characters")

        try:
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.minimax.io/v1",
            )

            response = client.chat.completions.create(
                model="MiniMax-M2.7",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical writer creating system instructions for MiniMax AI.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4096,
            )

            enhanced_content = response.choices[0].message.content
            print(f"  ✓ Generated enhanced SKILL.md ({len(enhanced_content)} chars)\n")

            if skill_md_path.exists():
                backup_path = skill_md_path.with_suffix(".md.backup")
                skill_md_path.rename(backup_path)
                print(f"  💾 Backed up original to: {backup_path.name}")

            skill_md_path.write_text(enhanced_content, encoding="utf-8")
            print("  ✅ Saved enhanced SKILL.md")

            return True

        except Exception as e:
            print(f"❌ Error calling MiniMax API: {e}")
            return False

    def _read_reference_files(
        self, references_dir: Path, max_chars: int = 200000
    ) -> dict[str, str]:
        """
        Read reference markdown files from skill directory.

        Args:
            references_dir: Path to references directory
            max_chars: Maximum total characters to read

        Returns:
            Dictionary mapping filename to content
        """
        if not references_dir.exists():
            return {}

        references = {}
        total_chars = 0

        for ref_file in sorted(references_dir.glob("*.md")):
            if total_chars >= max_chars:
                break

            try:
                content = ref_file.read_text(encoding="utf-8")
                if len(content) > 30000:
                    content = content[:30000] + "\n\n...(truncated)"

                references[ref_file.name] = content
                total_chars += len(content)

            except Exception as e:
                print(f"  ⚠️  Could not read {ref_file.name}: {e}")

        return references

    def _build_enhancement_prompt(
        self, skill_name: str, references: dict[str, str], current_skill_md: str = None
    ) -> str:
        """
        Build MiniMax API prompt for enhancement.

        Args:
            skill_name: Name of the skill
            references: Dictionary of reference content
            current_skill_md: Existing SKILL.md content (optional)

        Returns:
            Enhancement prompt for MiniMax-M2.7
        """
        prompt = f"""You are creating system instructions for a MiniMax AI assistant about: {skill_name}

I've scraped documentation and organized it into reference files. Your job is to create EXCELLENT system instructions that will help the assistant use this documentation effectively.

CURRENT INSTRUCTIONS:
{"```" if current_skill_md else "(none - create from scratch)"}
{current_skill_md or "No existing instructions"}
{"```" if current_skill_md else ""}

REFERENCE DOCUMENTATION:
"""

        for filename, content in references.items():
            prompt += f"\n\n## {filename}\n```markdown\n{content[:30000]}\n```\n"

        prompt += """

YOUR TASK:
Create enhanced system instructions that include:

1. **Clear role definition** - "You are an expert assistant for [topic]"
2. **Knowledge base description** - What documentation is attached
3. **Excellent Quick Reference** - Extract 5-10 of the BEST, most practical code examples from the reference docs
   - Choose SHORT, clear examples that demonstrate common tasks
   - Include both simple and intermediate examples
   - Annotate examples with clear descriptions
   - Use proper language tags (cpp, python, javascript, json, etc.)
4. **Response guidelines** - How the assistant should help users
5. **Search strategy** - How to find information in the knowledge base
6. **DO NOT use YAML frontmatter** - This is plain text instructions

IMPORTANT:
- Extract REAL examples from the reference docs, don't make them up
- Prioritize SHORT, clear examples (5-20 lines max)
- Make it actionable and practical
- Write clear, direct instructions
- Focus on how the assistant should behave and respond
- NO YAML frontmatter (no --- blocks)

OUTPUT:
Return ONLY the complete system instructions as plain text.
"""

        return prompt
