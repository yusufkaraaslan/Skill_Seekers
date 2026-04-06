#!/usr/bin/env python3
"""
OpenAI-Compatible Base Adaptor

Shared base class for all LLM platforms that use OpenAI-compatible APIs.
Subclasses only need to override platform constants (~15 lines each).
"""

import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from .base import SkillAdaptor, SkillMetadata
from skill_seekers.cli.arguments.common import DEFAULT_CHUNK_TOKENS, DEFAULT_CHUNK_OVERLAP_TOKENS


class OpenAICompatibleAdaptor(SkillAdaptor):
    """
    Base class for OpenAI-compatible LLM platform adaptors.

    Subclasses override these constants:
    - PLATFORM: Registry key (e.g., "kimi")
    - PLATFORM_NAME: Display name (e.g., "Kimi (Moonshot AI)")
    - DEFAULT_API_ENDPOINT: API base URL
    - DEFAULT_MODEL: Default model name
    - ENV_VAR_NAME: API key env var name
    - PLATFORM_URL: Dashboard/platform URL
    """

    PLATFORM = "unknown"
    PLATFORM_NAME = "Unknown"
    DEFAULT_API_ENDPOINT = ""
    DEFAULT_MODEL = ""
    ENV_VAR_NAME = ""
    PLATFORM_URL = ""

    def format_skill_md(self, skill_dir: Path, metadata: SkillMetadata) -> str:
        """
        Format SKILL.md as system instructions (no YAML frontmatter).

        Uses plain text format compatible with OpenAI-compatible chat APIs.
        """
        existing_content = self._read_existing_content(skill_dir)

        if existing_content and len(existing_content) > 100:
            return f"""You are an expert assistant for {metadata.name}.

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

        return f"""You are an expert assistant for {metadata.name}.

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
        Package skill into ZIP file for the platform.

        Creates platform-compatible structure:
        - system_instructions.txt (main instructions)
        - knowledge_files/*.md (reference files)
        - {platform}_metadata.json (skill metadata)
        """
        skill_dir = Path(skill_dir)
        output_path = Path(output_path)

        suffix = f"-{self.PLATFORM}.zip"

        if output_path.is_dir() or str(output_path).endswith("/"):
            output_path = Path(output_path) / f"{skill_dir.name}{suffix}"
        elif not str(output_path).endswith(suffix):
            output_str = str(output_path)
            # Strip existing .zip extension if present
            if output_str.endswith(".zip"):
                output_str = output_str[:-4]
            output_path = Path(output_str + suffix)

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
                "platform": self.PLATFORM,
                "name": skill_dir.name,
                "version": "1.0.0",
                "created_with": "skill-seekers",
                "model": self.DEFAULT_MODEL,
                "api_base": self.DEFAULT_API_ENDPOINT,
            }

            zf.writestr(f"{self.PLATFORM}_metadata.json", json.dumps(metadata, indent=2))

        return output_path

    def upload(self, package_path: Path, api_key: str, **kwargs) -> dict[str, Any]:
        """
        Upload/validate packaged skill via OpenAI-compatible API.
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
            from openai import OpenAI, APITimeoutError, APIConnectionError
        except ImportError:
            return {
                "success": False,
                "skill_id": None,
                "url": None,
                "message": "openai library not installed. Run: pip install openai",
            }

        try:
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

                metadata_file = temp_path / f"{self.PLATFORM}_metadata.json"
                skill_name = package_path.stem
                model = kwargs.get("model", self.DEFAULT_MODEL)

                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                        skill_name = metadata.get("name", skill_name)
                        model = metadata.get("model", model)

                knowledge_dir = temp_path / "knowledge_files"
                knowledge_count = 0
                if knowledge_dir.exists():
                    knowledge_count = len(list(knowledge_dir.rglob("*.md")))

                client = OpenAI(
                    api_key=api_key,
                    base_url=self.DEFAULT_API_ENDPOINT,
                )

                client.chat.completions.create(
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
                    "url": self.PLATFORM_URL,
                    "message": f"Skill '{skill_name}' validated with {self.PLATFORM_NAME} {model} ({knowledge_count} knowledge files)",
                }

        except APITimeoutError:
            return {
                "success": False,
                "skill_id": None,
                "url": None,
                "message": "Upload timed out. Try again.",
            }
        except APIConnectionError:
            return {
                "success": False,
                "skill_id": None,
                "url": None,
                "message": "Connection error. Check your internet connection.",
            }
        except Exception as e:
            return {
                "success": False,
                "skill_id": None,
                "url": None,
                "message": f"Upload failed: {str(e)}",
            }

    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key (non-empty, >10 chars)."""
        key = api_key.strip()
        return len(key) > 10

    def get_env_var_name(self) -> str:
        """Get environment variable name for API key."""
        return self.ENV_VAR_NAME

    def supports_enhancement(self) -> bool:
        """OpenAI-compatible platforms support enhancement."""
        return True

    def enhance(self, skill_dir: Path, api_key: str) -> bool:
        """
        Enhance SKILL.md using the platform's OpenAI-compatible API.
        """
        try:
            from openai import OpenAI
        except ImportError:
            print("Error: openai package not installed")
            print("Install with: pip install openai")
            return False

        skill_dir = Path(skill_dir)
        references_dir = skill_dir / "references"
        skill_md_path = skill_dir / "SKILL.md"

        print("Reading reference documentation...")
        references = self._read_reference_files(references_dir)

        if not references:
            print("No reference files found to analyze")
            return False

        print(f"  Read {len(references)} reference files")
        total_size = sum(len(c) for c in references.values())
        print(f"  Total size: {total_size:,} characters\n")

        current_skill_md = None
        if skill_md_path.exists():
            current_skill_md = skill_md_path.read_text(encoding="utf-8")
            print(f"  Found existing SKILL.md ({len(current_skill_md)} chars)")
        else:
            print("  No existing SKILL.md, will create new one")

        prompt = self._build_enhancement_prompt(skill_dir.name, references, current_skill_md)

        print(f"\nAsking {self.PLATFORM_NAME} ({self.DEFAULT_MODEL}) to enhance SKILL.md...")
        print(f"   Input: {len(prompt):,} characters")

        try:
            client = OpenAI(
                api_key=api_key,
                base_url=self.DEFAULT_API_ENDPOINT,
            )

            response = client.chat.completions.create(
                model=self.DEFAULT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert technical writer creating system instructions for {self.PLATFORM_NAME}.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4096,
            )

            enhanced_content = response.choices[0].message.content
            print(f"  Generated enhanced SKILL.md ({len(enhanced_content)} chars)\n")

            if skill_md_path.exists():
                backup_path = skill_md_path.with_suffix(".md.backup")
                skill_md_path.rename(backup_path)
                print(f"  Backed up original to: {backup_path.name}")

            skill_md_path.write_text(enhanced_content, encoding="utf-8")
            print("  Saved enhanced SKILL.md")

            return True

        except Exception as e:
            print(f"Error calling {self.PLATFORM_NAME} API: {e}")
            return False

    def _read_reference_files(
        self, references_dir: Path, max_chars: int = 200000
    ) -> dict[str, str]:
        """Read reference markdown files from skill directory."""
        if not references_dir.exists():
            return {}

        references = {}
        total_chars = 0

        for ref_file in sorted(references_dir.rglob("*.md")):
            if total_chars >= max_chars:
                break

            try:
                content = ref_file.read_text(encoding="utf-8")
                if len(content) > 30000:
                    content = content[:30000] + "\n\n...(truncated)"

                references[ref_file.name] = content
                total_chars += len(content)

            except Exception as e:
                print(f"  Could not read {ref_file.name}: {e}")

        return references

    def _build_enhancement_prompt(
        self, skill_name: str, references: dict[str, str], current_skill_md: str = None
    ) -> str:
        """Build API prompt for enhancement."""
        prompt = f"""You are creating system instructions for a {self.PLATFORM_NAME} assistant about: {skill_name}

I've scraped documentation and organized it into reference files. Your job is to create EXCELLENT system instructions that will help the assistant use this documentation effectively.

CURRENT INSTRUCTIONS:
{"```" if current_skill_md else "(none - create from scratch)"}
{current_skill_md or "No existing instructions"}
{"```" if current_skill_md else ""}

REFERENCE DOCUMENTATION:
"""

        for filename, content in references.items():
            prompt += f"\n\n## {filename}\n```markdown\n{content[:30000]}\n```\n"

        prompt += f"""

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
