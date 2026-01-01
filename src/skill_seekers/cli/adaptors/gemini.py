#!/usr/bin/env python3
"""
Google Gemini Adaptor

Implements platform-specific handling for Google Gemini skills.
Uses Gemini Files API for grounding and Gemini 2.0 Flash for enhancement.
"""

import os
import tarfile
import json
from pathlib import Path
from typing import Dict, Any

from .base import SkillAdaptor, SkillMetadata


class GeminiAdaptor(SkillAdaptor):
    """
    Google Gemini platform adaptor.

    Handles:
    - Plain markdown format (no YAML frontmatter)
    - tar.gz packaging for Gemini Files API
    - Upload to Google AI Studio / Files API
    - AI enhancement using Gemini 2.0 Flash
    """

    PLATFORM = "gemini"
    PLATFORM_NAME = "Google Gemini"
    DEFAULT_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/files"

    def format_skill_md(self, skill_dir: Path, metadata: SkillMetadata) -> str:
        """
        Format SKILL.md with plain markdown (no frontmatter).

        Gemini doesn't use YAML frontmatter - just clean markdown.

        Args:
            skill_dir: Path to skill directory
            metadata: Skill metadata

        Returns:
            Formatted SKILL.md content (plain markdown)
        """
        # Read existing content (if any)
        existing_content = self._read_existing_content(skill_dir)

        # If existing content is substantial, use it
        if existing_content and len(existing_content) > 100:
            content_body = existing_content
        else:
            # Generate default content
            content_body = f"""# {metadata.name.title()} Documentation

**Description:** {metadata.description}

## Quick Reference

{self._extract_quick_reference(skill_dir)}

## Table of Contents

{self._generate_toc(skill_dir)}

## Documentation Structure

This skill contains comprehensive documentation organized into categorized reference files.

### Available References

{self._generate_toc(skill_dir)}

## How to Use This Skill

When asking questions about {metadata.name}:
1. Mention specific topics or features you need help with
2. Reference documentation sections will be automatically consulted
3. You'll receive detailed answers with code examples

## Navigation

See the references directory for complete documentation with examples and best practices.
"""

        # Return plain markdown (NO frontmatter)
        return content_body

    def package(self, skill_dir: Path, output_path: Path) -> Path:
        """
        Package skill into tar.gz file for Gemini.

        Creates Gemini-compatible structure:
        - system_instructions.md (main SKILL.md)
        - references/*.md
        - gemini_metadata.json (skill metadata)

        Args:
            skill_dir: Path to skill directory
            output_path: Output path/filename for tar.gz

        Returns:
            Path to created tar.gz file
        """
        skill_dir = Path(skill_dir)

        # Determine output filename
        if output_path.is_dir() or str(output_path).endswith('/'):
            output_path = Path(output_path) / f"{skill_dir.name}-gemini.tar.gz"
        elif not str(output_path).endswith('.tar.gz'):
            # Replace .zip with .tar.gz if needed
            output_str = str(output_path).replace('.zip', '.tar.gz')
            if not output_str.endswith('.tar.gz'):
                output_str += '.tar.gz'
            output_path = Path(output_str)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create tar.gz file
        with tarfile.open(output_path, 'w:gz') as tar:
            # Add SKILL.md as system_instructions.md
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                tar.add(skill_md, arcname="system_instructions.md")

            # Add references directory (if exists)
            refs_dir = skill_dir / "references"
            if refs_dir.exists():
                for ref_file in refs_dir.rglob("*"):
                    if ref_file.is_file() and not ref_file.name.startswith('.'):
                        arcname = ref_file.relative_to(skill_dir)
                        tar.add(ref_file, arcname=str(arcname))

            # Create and add metadata file
            metadata = {
                'platform': 'gemini',
                'name': skill_dir.name,
                'version': '1.0.0',
                'created_with': 'skill-seekers'
            }

            # Write metadata to temp file and add to archive
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                json.dump(metadata, tmp, indent=2)
                tmp_path = tmp.name

            try:
                tar.add(tmp_path, arcname="gemini_metadata.json")
            finally:
                os.unlink(tmp_path)

        return output_path

    def upload(self, package_path: Path, api_key: str, **kwargs) -> Dict[str, Any]:
        """
        Upload skill tar.gz to Gemini Files API.

        Args:
            package_path: Path to skill tar.gz file
            api_key: Google API key
            **kwargs: Additional arguments

        Returns:
            Dictionary with upload result
        """
        # Validate package file FIRST
        package_path = Path(package_path)
        if not package_path.exists():
            return {
                'success': False,
                'skill_id': None,
                'url': None,
                'message': f'File not found: {package_path}'
            }

        if not package_path.suffix == '.gz':
            return {
                'success': False,
                'skill_id': None,
                'url': None,
                'message': f'Not a tar.gz file: {package_path}'
            }

        # Check for google-generativeai library
        try:
            import google.generativeai as genai
        except ImportError:
            return {
                'success': False,
                'skill_id': None,
                'url': None,
                'message': 'google-generativeai library not installed. Run: pip install google-generativeai'
            }

        # Configure Gemini
        try:
            genai.configure(api_key=api_key)

            # Extract tar.gz to temp directory
            import tempfile
            import shutil

            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract archive
                with tarfile.open(package_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)

                temp_path = Path(temp_dir)

                # Upload main file (system_instructions.md)
                main_file = temp_path / "system_instructions.md"
                if not main_file.exists():
                    return {
                        'success': False,
                        'skill_id': None,
                        'url': None,
                        'message': 'Invalid package: system_instructions.md not found'
                    }

                # Upload to Files API
                uploaded_file = genai.upload_file(
                    path=str(main_file),
                    display_name=f"{package_path.stem}_instructions"
                )

                # Upload reference files (if any)
                refs_dir = temp_path / "references"
                uploaded_refs = []
                if refs_dir.exists():
                    for ref_file in refs_dir.glob("*.md"):
                        ref_uploaded = genai.upload_file(
                            path=str(ref_file),
                            display_name=f"{package_path.stem}_{ref_file.stem}"
                        )
                        uploaded_refs.append(ref_uploaded.name)

            return {
                'success': True,
                'skill_id': uploaded_file.name,
                'url': f"https://aistudio.google.com/app/files/{uploaded_file.name}",
                'message': f'Skill uploaded to Google AI Studio ({len(uploaded_refs) + 1} files)'
            }

        except Exception as e:
            return {
                'success': False,
                'skill_id': None,
                'url': None,
                'message': f'Upload failed: {str(e)}'
            }

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate Google API key format.

        Args:
            api_key: API key to validate

        Returns:
            True if key starts with 'AIza'
        """
        return api_key.strip().startswith('AIza')

    def get_env_var_name(self) -> str:
        """
        Get environment variable name for Google API key.

        Returns:
            'GOOGLE_API_KEY'
        """
        return "GOOGLE_API_KEY"

    def supports_enhancement(self) -> bool:
        """
        Gemini supports AI enhancement via Gemini 2.0 Flash.

        Returns:
            True
        """
        return True

    def enhance(self, skill_dir: Path, api_key: str) -> bool:
        """
        Enhance SKILL.md using Gemini 2.0 Flash API.

        Args:
            skill_dir: Path to skill directory
            api_key: Google API key

        Returns:
            True if enhancement succeeded
        """
        # Check for google-generativeai library
        try:
            import google.generativeai as genai
        except ImportError:
            print("❌ Error: google-generativeai package not installed")
            print("Install with: pip install google-generativeai")
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

        print("\n🤖 Asking Gemini to enhance SKILL.md...")
        print(f"   Input: {len(prompt):,} characters")

        try:
            genai.configure(api_key=api_key)

            model = genai.GenerativeModel('gemini-2.0-flash-exp')

            response = model.generate_content(prompt)

            enhanced_content = response.text
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
            print(f"❌ Error calling Gemini API: {e}")
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
        Build Gemini API prompt for enhancement.

        Args:
            skill_name: Name of the skill
            references: Dictionary of reference content
            current_skill_md: Existing SKILL.md content (optional)

        Returns:
            Enhancement prompt for Gemini
        """
        prompt = f"""You are enhancing a skill's documentation file for use with Google Gemini. This skill is about: {skill_name}

I've scraped documentation and organized it into reference files. Your job is to create an EXCELLENT markdown documentation file that will help Gemini use this documentation effectively.

CURRENT DOCUMENTATION:
{'```markdown' if current_skill_md else '(none - create from scratch)'}
{current_skill_md or 'No existing documentation'}
{'```' if current_skill_md else ''}

REFERENCE DOCUMENTATION:
"""

        for filename, content in references.items():
            prompt += f"\n\n## {filename}\n```markdown\n{content[:30000]}\n```\n"

        prompt += """

YOUR TASK:
Create enhanced documentation that includes:

1. **Clear description** - What this skill covers and when to use it
2. **Excellent Quick Reference section** - Extract 5-10 of the BEST, most practical code examples from the reference docs
   - Choose SHORT, clear examples that demonstrate common tasks
   - Include both simple and intermediate examples
   - Annotate examples with clear descriptions
   - Use proper language tags (cpp, python, javascript, json, etc.)
3. **Table of Contents** - List all reference sections
4. **Practical usage guidance** - Help users navigate the documentation
5. **Key Concepts section** (if applicable) - Explain core concepts
6. **DO NOT use YAML frontmatter** - This is for Gemini, which uses plain markdown

IMPORTANT:
- Extract REAL examples from the reference docs, don't make them up
- Prioritize SHORT, clear examples (5-20 lines max)
- Make it actionable and practical
- Don't be too verbose - be concise but useful
- Use clean markdown formatting
- Keep code examples properly formatted with language tags
- NO YAML frontmatter (no --- blocks)

OUTPUT:
Return ONLY the complete markdown content, starting with the main title (#).
"""

        return prompt
