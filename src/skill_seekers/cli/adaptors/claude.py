#!/usr/bin/env python3
"""
Claude AI Adaptor

Implements platform-specific handling for Claude AI (Anthropic) skills.
Refactored from upload_skill.py and enhance_skill.py.
"""

import json
import zipfile
from pathlib import Path
from typing import Any

from .base import SkillAdaptor, SkillMetadata
from skill_seekers.cli.arguments.common import DEFAULT_CHUNK_TOKENS, DEFAULT_CHUNK_OVERLAP_TOKENS


class ClaudeAdaptor(SkillAdaptor):
    """
    Claude AI platform adaptor.

    Handles:
    - YAML frontmatter format for SKILL.md
    - ZIP packaging with standard Claude skill structure
    - Upload to Anthropic Skills API
    - AI enhancement using Claude API
    """

    PLATFORM = "claude"
    PLATFORM_NAME = "Claude AI (Anthropic)"
    DEFAULT_API_ENDPOINT = "https://api.anthropic.com/v1/skills"

    def format_skill_md(self, skill_dir: Path, metadata: SkillMetadata) -> str:
        """
        Format SKILL.md with Claude's YAML frontmatter.

        Args:
            skill_dir: Path to skill directory
            metadata: Skill metadata

        Returns:
            Formatted SKILL.md content with YAML frontmatter
        """
        # Read existing content (if any)
        existing_content = self._read_existing_content(skill_dir)

        # If existing content already has proper structure, use it
        if existing_content and len(existing_content) > 100:
            content_body = existing_content
        else:
            # Generate default content
            content_body = f"""# {metadata.name.title()} Documentation Skill

{metadata.description}

## When to use this skill

Use this skill when the user asks about {metadata.name} documentation, including API references, tutorials, examples, and best practices.

## What's included

This skill contains comprehensive documentation organized into categorized reference files.

{self._generate_toc(skill_dir)}

## Quick Reference

{self._extract_quick_reference(skill_dir)}

## Navigation

See `references/index.md` for complete documentation structure.
"""

        # Format with YAML frontmatter. Quote name/description (json.dumps yields
        # a valid double-quoted YAML scalar) so a colon-space or leading special
        # char in the text can't produce invalid YAML.
        return f"""---
name: {json.dumps(metadata.name)}
description: {json.dumps(metadata.description)}
version: {metadata.version}
---

{content_body}
"""

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
        Package skill into ZIP file for Claude.

        Creates standard Claude skill structure:
        - SKILL.md
        - references/*.md
        - scripts/ (optional)
        - assets/ (optional)

        Args:
            skill_dir: Path to skill directory
            output_path: Output path/filename for ZIP

        Returns:
            Path to created ZIP file
        """
        skill_dir = Path(skill_dir)

        # Determine output filename
        if output_path.is_dir() or str(output_path).endswith("/"):
            output_path = Path(output_path) / f"{skill_dir.name}.zip"
        elif not str(output_path).endswith(".zip"):
            output_path = Path(str(output_path) + ".zip")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create ZIP file
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add SKILL.md (required)
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                zf.write(skill_md, "SKILL.md")

            # Add references directory (if exists)
            refs_dir = skill_dir / "references"
            if refs_dir.exists():
                for ref_file in refs_dir.rglob("*"):
                    if ref_file.is_file() and not ref_file.name.startswith("."):
                        arcname = ref_file.relative_to(skill_dir)
                        zf.write(ref_file, str(arcname))

            # Add scripts directory (if exists)
            scripts_dir = skill_dir / "scripts"
            if scripts_dir.exists():
                for script_file in scripts_dir.rglob("*"):
                    if script_file.is_file() and not script_file.name.startswith("."):
                        arcname = script_file.relative_to(skill_dir)
                        zf.write(script_file, str(arcname))

            # Add assets directory (if exists)
            assets_dir = skill_dir / "assets"
            if assets_dir.exists():
                for asset_file in assets_dir.rglob("*"):
                    if asset_file.is_file() and not asset_file.name.startswith("."):
                        arcname = asset_file.relative_to(skill_dir)
                        zf.write(asset_file, str(arcname))

        return output_path

    def upload(self, package_path: Path, api_key: str, **kwargs) -> dict[str, Any]:
        """
        Upload skill ZIP to Anthropic Skills API.

        Args:
            package_path: Path to skill ZIP file
            api_key: Anthropic API key
            **kwargs: Additional arguments (timeout, etc.)

        Returns:
            Dictionary with upload result
        """
        # Check for requests library
        try:
            import requests
        except ImportError:
            return {
                "success": False,
                "skill_id": None,
                "url": None,
                "message": "requests library not installed. Run: pip install requests",
            }

        # Validate ZIP file
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

        # Prepare API request
        api_url = self.DEFAULT_API_ENDPOINT
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "skills-2025-10-02",
        }

        timeout = kwargs.get("timeout", 60)

        try:
            # Read ZIP file
            with open(package_path, "rb") as f:
                zip_data = f.read()

            # Upload skill
            files = {"files[]": (package_path.name, zip_data, "application/zip")}

            response = requests.post(api_url, headers=headers, files=files, timeout=timeout)

            # Check response
            if response.status_code == 200:
                # Extract skill ID if available
                try:
                    response_data = response.json()
                    skill_id = response_data.get("id")
                except Exception:
                    skill_id = None

                return {
                    "success": True,
                    "skill_id": skill_id,
                    "url": "https://claude.ai/skills",
                    "message": "Skill uploaded successfully to Claude AI",
                }

            elif response.status_code == 401:
                return {
                    "success": False,
                    "skill_id": None,
                    "url": None,
                    "message": "Authentication failed. Check your ANTHROPIC_API_KEY",
                }

            elif response.status_code == 400:
                try:
                    error_msg = response.json().get("error", {}).get("message", "Unknown error")
                except Exception:
                    error_msg = "Invalid skill format"

                return {
                    "success": False,
                    "skill_id": None,
                    "url": None,
                    "message": f"Invalid skill format: {error_msg}",
                }

            else:
                try:
                    error_msg = response.json().get("error", {}).get("message", "Unknown error")
                except Exception:
                    error_msg = f"HTTP {response.status_code}"

                return {
                    "success": False,
                    "skill_id": None,
                    "url": None,
                    "message": f"Upload failed: {error_msg}",
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "skill_id": None,
                "url": None,
                "message": "Upload timed out. Try again or use manual upload",
            }

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "skill_id": None,
                "url": None,
                "message": "Connection error. Check your internet connection",
            }

        except Exception as e:
            return {
                "success": False,
                "skill_id": None,
                "url": None,
                "message": f"Unexpected error: {str(e)}",
            }

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate Anthropic API key format.

        Args:
            api_key: API key to validate

        Returns:
            True if key starts with 'sk-ant-'
        """
        return api_key.strip().startswith("sk-ant-")

    def get_env_var_name(self) -> str:
        """
        Get environment variable name for Anthropic API key.

        Returns:
            'ANTHROPIC_API_KEY'
        """
        return "ANTHROPIC_API_KEY"

    def supports_upload(self) -> bool:
        """Claude supports uploading skills via the Anthropic API."""
        return True

    def supports_enhancement(self) -> bool:
        """
        Claude supports AI enhancement via Anthropic API.

        Returns:
            True
        """
        return True

    def enhance(self, skill_dir: Path, api_key: str) -> bool:
        """Enhance SKILL.md using the Claude API (via AgentClient).

        Model chain: config custom_model → ANTHROPIC_MODEL env (inside
        AgentClient.get_model) → default. ANTHROPIC_BASE_URL (GLM-4.x and
        other Claude-compatible endpoints) is honored by AgentClient itself.
        """
        return self._enhance_skill_md_via_client(
            skill_dir,
            api_key,
            provider="anthropic",
            model=self.config.get("custom_model"),
        )

    def _build_enhancement_prompt(
        self, skill_name: str, references: dict[str, str], current_skill_md: str = None
    ) -> str:
        """
        Build Claude API prompt for enhancement.

        Args:
            skill_name: Name of the skill
            references: Dictionary of reference content
            current_skill_md: Existing SKILL.md content (optional)

        Returns:
            Enhancement prompt for Claude
        """
        prompt = f"""You are enhancing a Claude skill's SKILL.md file. This skill is about: {skill_name}

I've scraped documentation and organized it into reference files. Your job is to create an EXCELLENT SKILL.md that will help Claude use this documentation effectively.

CURRENT SKILL.MD:
{"```markdown" if current_skill_md else "(none - create from scratch)"}
{current_skill_md or "No existing SKILL.md"}
{"```" if current_skill_md else ""}

REFERENCE DOCUMENTATION:
"""

        for filename, content in references.items():
            prompt += f"\n\n## {filename}\n```markdown\n{content[:30000]}\n```\n"

        prompt += """

YOUR TASK:
Create an enhanced SKILL.md that includes:

1. **Clear "When to Use This Skill" section** - Be specific about trigger conditions
2. **Excellent Quick Reference section** - Extract 5-10 of the BEST, most practical code examples from the reference docs
   - Choose SHORT, clear examples that demonstrate common tasks
   - Include both simple and intermediate examples
   - Annotate examples with clear descriptions
   - Use proper language tags (cpp, python, javascript, json, etc.)
3. **Detailed Reference Files description** - Explain what's in each reference file
4. **Practical "Working with This Skill" section** - Give users clear guidance on how to navigate the skill
5. **Key Concepts section** (if applicable) - Explain core concepts
6. **Keep the frontmatter** (---\nname: ...\n---) intact

IMPORTANT:
- Extract REAL examples from the reference docs, don't make them up
- Prioritize SHORT, clear examples (5-20 lines max)
- Make it actionable and practical
- Don't be too verbose - be concise but useful
- Maintain the markdown structure for Claude skills
- Keep code examples properly formatted with language tags

OUTPUT:
Return ONLY the complete SKILL.md content, starting with the frontmatter (---).
"""

        return prompt
