#!/usr/bin/env python3
"""
Claude AI Adaptor

Implements platform-specific handling for Claude AI (Anthropic) skills.
Refactored from upload_skill.py and enhance_skill.py.
"""

import os
import zipfile
from pathlib import Path
from typing import Dict, Any

from .base import SkillAdaptor, SkillMetadata


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

        # Format with YAML frontmatter
        return f"""---
name: {metadata.name}
description: {metadata.description}
version: {metadata.version}
---

{content_body}
"""

    def package(self, skill_dir: Path, output_path: Path) -> Path:
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
        if output_path.is_dir() or str(output_path).endswith('/'):
            output_path = Path(output_path) / f"{skill_dir.name}.zip"
        elif not str(output_path).endswith('.zip'):
            output_path = Path(str(output_path) + '.zip')

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create ZIP file
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add SKILL.md (required)
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                zf.write(skill_md, "SKILL.md")

            # Add references directory (if exists)
            refs_dir = skill_dir / "references"
            if refs_dir.exists():
                for ref_file in refs_dir.rglob("*"):
                    if ref_file.is_file() and not ref_file.name.startswith('.'):
                        arcname = ref_file.relative_to(skill_dir)
                        zf.write(ref_file, str(arcname))

            # Add scripts directory (if exists)
            scripts_dir = skill_dir / "scripts"
            if scripts_dir.exists():
                for script_file in scripts_dir.rglob("*"):
                    if script_file.is_file() and not script_file.name.startswith('.'):
                        arcname = script_file.relative_to(skill_dir)
                        zf.write(script_file, str(arcname))

            # Add assets directory (if exists)
            assets_dir = skill_dir / "assets"
            if assets_dir.exists():
                for asset_file in assets_dir.rglob("*"):
                    if asset_file.is_file() and not asset_file.name.startswith('.'):
                        arcname = asset_file.relative_to(skill_dir)
                        zf.write(asset_file, str(arcname))

        return output_path

    def upload(self, package_path: Path, api_key: str, **kwargs) -> Dict[str, Any]:
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
                'success': False,
                'skill_id': None,
                'url': None,
                'message': 'requests library not installed. Run: pip install requests'
            }

        # Validate ZIP file
        package_path = Path(package_path)
        if not package_path.exists():
            return {
                'success': False,
                'skill_id': None,
                'url': None,
                'message': f'File not found: {package_path}'
            }

        if not package_path.suffix == '.zip':
            return {
                'success': False,
                'skill_id': None,
                'url': None,
                'message': f'Not a ZIP file: {package_path}'
            }

        # Prepare API request
        api_url = self.DEFAULT_API_ENDPOINT
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "skills-2025-10-02"
        }

        timeout = kwargs.get('timeout', 60)

        try:
            # Read ZIP file
            with open(package_path, 'rb') as f:
                zip_data = f.read()

            # Upload skill
            files = {
                'files[]': (package_path.name, zip_data, 'application/zip')
            }

            response = requests.post(
                api_url,
                headers=headers,
                files=files,
                timeout=timeout
            )

            # Check response
            if response.status_code == 200:
                # Extract skill ID if available
                try:
                    response_data = response.json()
                    skill_id = response_data.get('id')
                except:
                    skill_id = None

                return {
                    'success': True,
                    'skill_id': skill_id,
                    'url': 'https://claude.ai/skills',
                    'message': 'Skill uploaded successfully to Claude AI'
                }

            elif response.status_code == 401:
                return {
                    'success': False,
                    'skill_id': None,
                    'url': None,
                    'message': 'Authentication failed. Check your ANTHROPIC_API_KEY'
                }

            elif response.status_code == 400:
                try:
                    error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                except:
                    error_msg = 'Invalid skill format'

                return {
                    'success': False,
                    'skill_id': None,
                    'url': None,
                    'message': f'Invalid skill format: {error_msg}'
                }

            else:
                try:
                    error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                except:
                    error_msg = f'HTTP {response.status_code}'

                return {
                    'success': False,
                    'skill_id': None,
                    'url': None,
                    'message': f'Upload failed: {error_msg}'
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'skill_id': None,
                'url': None,
                'message': 'Upload timed out. Try again or use manual upload'
            }

        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'skill_id': None,
                'url': None,
                'message': 'Connection error. Check your internet connection'
            }

        except Exception as e:
            return {
                'success': False,
                'skill_id': None,
                'url': None,
                'message': f'Unexpected error: {str(e)}'
            }

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate Anthropic API key format.

        Args:
            api_key: API key to validate

        Returns:
            True if key starts with 'sk-ant-'
        """
        return api_key.strip().startswith('sk-ant-')

    def get_env_var_name(self) -> str:
        """
        Get environment variable name for Anthropic API key.

        Returns:
            'ANTHROPIC_API_KEY'
        """
        return "ANTHROPIC_API_KEY"

    def supports_enhancement(self) -> bool:
        """
        Claude supports AI enhancement via Anthropic API.

        Returns:
            True
        """
        return True

    def enhance(self, skill_dir: Path, api_key: str) -> bool:
        """
        Enhance SKILL.md using Claude API.

        Reads reference files, sends them to Claude, and generates
        an improved SKILL.md with real examples and better organization.

        Args:
            skill_dir: Path to skill directory
            api_key: Anthropic API key

        Returns:
            True if enhancement succeeded
        """
        # Check for anthropic library
        try:
            import anthropic
        except ImportError:
            print("❌ Error: anthropic package not installed")
            print("Install with: pip install anthropic")
            return False

        skill_dir = Path(skill_dir)
        references_dir = skill_dir / "references"
        skill_md_path = skill_dir / "SKILL.md"

        # Read reference files
        print("📖 Reading reference documentation...")
        references = self._read_reference_files(references_dir)

        if not references:
            print("❌ No reference files found to analyze")
            return False

        print(f"  ✓ Read {len(references)} reference files")
        total_size = sum(len(c) for c in references.values())
        print(f"  ✓ Total size: {total_size:,} characters\n")

        # Read current SKILL.md
        current_skill_md = None
        if skill_md_path.exists():
            current_skill_md = skill_md_path.read_text(encoding='utf-8')
            print(f"  ℹ Found existing SKILL.md ({len(current_skill_md)} chars)")
        else:
            print(f"  ℹ No existing SKILL.md, will create new one")

        # Build enhancement prompt
        prompt = self._build_enhancement_prompt(
            skill_dir.name,
            references,
            current_skill_md
        )

        print("\n🤖 Asking Claude to enhance SKILL.md...")
        print(f"   Input: {len(prompt):,} characters")

        try:
            client = anthropic.Anthropic(api_key=api_key)

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            enhanced_content = message.content[0].text
            print(f"  ✓ Generated enhanced SKILL.md ({len(enhanced_content)} chars)\n")

            # Backup original
            if skill_md_path.exists():
                backup_path = skill_md_path.with_suffix('.md.backup')
                skill_md_path.rename(backup_path)
                print(f"  💾 Backed up original to: {backup_path.name}")

            # Save enhanced version
            skill_md_path.write_text(enhanced_content, encoding='utf-8')
            print(f"  ✅ Saved enhanced SKILL.md")

            return True

        except Exception as e:
            print(f"❌ Error calling Claude API: {e}")
            return False

    def _read_reference_files(self, references_dir: Path, max_chars: int = 200000) -> Dict[str, str]:
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

        # Read all .md files
        for ref_file in sorted(references_dir.glob("*.md")):
            if total_chars >= max_chars:
                break

            try:
                content = ref_file.read_text(encoding='utf-8')
                # Limit individual file size
                if len(content) > 30000:
                    content = content[:30000] + "\n\n...(truncated)"

                references[ref_file.name] = content
                total_chars += len(content)

            except Exception as e:
                print(f"  ⚠️  Could not read {ref_file.name}: {e}")

        return references

    def _build_enhancement_prompt(
        self,
        skill_name: str,
        references: Dict[str, str],
        current_skill_md: str = None
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
{'```markdown' if current_skill_md else '(none - create from scratch)'}
{current_skill_md or 'No existing SKILL.md'}
{'```' if current_skill_md else ''}

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
