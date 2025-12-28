#!/usr/bin/env python3
"""
OpenAI ChatGPT Adaptor

Implements platform-specific handling for OpenAI ChatGPT Assistants.
Uses Assistants API with Vector Store for file search.
"""

import os
import zipfile
import json
from pathlib import Path
from typing import Dict, Any

from .base import SkillAdaptor, SkillMetadata


class OpenAIAdaptor(SkillAdaptor):
    """
    OpenAI ChatGPT platform adaptor.

    Handles:
    - Assistant instructions format (not YAML frontmatter)
    - ZIP packaging for Assistants API
    - Upload creates Assistant + Vector Store
    - AI enhancement using GPT-4o
    """

    PLATFORM = "openai"
    PLATFORM_NAME = "OpenAI ChatGPT"
    DEFAULT_API_ENDPOINT = "https://api.openai.com/v1/assistants"

    def format_skill_md(self, skill_dir: Path, metadata: SkillMetadata) -> str:
        """
        Format SKILL.md as Assistant instructions.

        OpenAI Assistants use instructions rather than markdown docs.

        Args:
            skill_dir: Path to skill directory
            metadata: Skill metadata

        Returns:
            Formatted instructions for OpenAI Assistant
        """
        # Read existing content (if any)
        existing_content = self._read_existing_content(skill_dir)

        # If existing content is substantial, adapt it to instructions format
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
            # Generate default instructions
            content_body = f"""You are an expert assistant for {metadata.name}.

{metadata.description}

## Your Knowledge Base

You have access to comprehensive documentation files about {metadata.name}. Use these files to provide accurate answers to user questions.

{self._generate_toc(skill_dir)}

## Quick Reference

{self._extract_quick_reference(skill_dir)}

## How to Assist Users

When users ask questions about {metadata.name}:

1. **Search the knowledge files** - Use file_search to find relevant information
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

        # Return plain text instructions (NO frontmatter)
        return content_body

    def package(self, skill_dir: Path, output_path: Path) -> Path:
        """
        Package skill into ZIP file for OpenAI Assistants.

        Creates OpenAI-compatible structure:
        - assistant_instructions.txt (main instructions)
        - vector_store_files/*.md (reference files for vector store)
        - openai_metadata.json (skill metadata)

        Args:
            skill_dir: Path to skill directory
            output_path: Output path/filename for ZIP

        Returns:
            Path to created ZIP file
        """
        skill_dir = Path(skill_dir)

        # Determine output filename
        if output_path.is_dir() or str(output_path).endswith('/'):
            output_path = Path(output_path) / f"{skill_dir.name}-openai.zip"
        elif not str(output_path).endswith('.zip'):
            # Keep .zip extension
            if not str(output_path).endswith('-openai.zip'):
                output_str = str(output_path).replace('.zip', '-openai.zip')
                if not output_str.endswith('.zip'):
                    output_str += '.zip'
                output_path = Path(output_str)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create ZIP file
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add SKILL.md as assistant_instructions.txt
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                instructions = skill_md.read_text(encoding='utf-8')
                zf.writestr("assistant_instructions.txt", instructions)

            # Add references directory as vector_store_files/
            refs_dir = skill_dir / "references"
            if refs_dir.exists():
                for ref_file in refs_dir.rglob("*.md"):
                    if ref_file.is_file() and not ref_file.name.startswith('.'):
                        # Place all reference files in vector_store_files/
                        arcname = f"vector_store_files/{ref_file.name}"
                        zf.write(ref_file, arcname)

            # Create and add metadata file
            metadata = {
                'platform': 'openai',
                'name': skill_dir.name,
                'version': '1.0.0',
                'created_with': 'skill-seekers',
                'model': 'gpt-4o',
                'tools': ['file_search']
            }

            zf.writestr("openai_metadata.json", json.dumps(metadata, indent=2))

        return output_path

    def upload(self, package_path: Path, api_key: str, **kwargs) -> Dict[str, Any]:
        """
        Upload skill ZIP to OpenAI Assistants API.

        Creates:
        1. Vector Store with reference files
        2. Assistant with file_search tool

        Args:
            package_path: Path to skill ZIP file
            api_key: OpenAI API key
            **kwargs: Additional arguments (model, etc.)

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

        if not package_path.suffix == '.zip':
            return {
                'success': False,
                'skill_id': None,
                'url': None,
                'message': f'Not a ZIP file: {package_path}'
            }

        # Check for openai library
        try:
            from openai import OpenAI
        except ImportError:
            return {
                'success': False,
                'skill_id': None,
                'url': None,
                'message': 'openai library not installed. Run: pip install openai'
            }

        # Configure OpenAI client
        try:
            client = OpenAI(api_key=api_key)

            # Extract package to temp directory
            import tempfile
            import shutil

            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract ZIP
                with zipfile.ZipFile(package_path, 'r') as zf:
                    zf.extractall(temp_dir)

                temp_path = Path(temp_dir)

                # Read instructions
                instructions_file = temp_path / "assistant_instructions.txt"
                if not instructions_file.exists():
                    return {
                        'success': False,
                        'skill_id': None,
                        'url': None,
                        'message': 'Invalid package: assistant_instructions.txt not found'
                    }

                instructions = instructions_file.read_text(encoding='utf-8')

                # Read metadata
                metadata_file = temp_path / "openai_metadata.json"
                skill_name = package_path.stem
                model = kwargs.get('model', 'gpt-4o')

                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        skill_name = metadata.get('name', skill_name)
                        model = metadata.get('model', model)

                # Create vector store
                vector_store = client.beta.vector_stores.create(
                    name=f"{skill_name} Documentation"
                )

                # Upload reference files to vector store
                vector_files_dir = temp_path / "vector_store_files"
                file_ids = []

                if vector_files_dir.exists():
                    for ref_file in vector_files_dir.glob("*.md"):
                        # Upload file
                        with open(ref_file, 'rb') as f:
                            uploaded_file = client.files.create(
                                file=f,
                                purpose='assistants'
                            )
                            file_ids.append(uploaded_file.id)

                    # Attach files to vector store
                    if file_ids:
                        client.beta.vector_stores.files.create_batch(
                            vector_store_id=vector_store.id,
                            file_ids=file_ids
                        )

                # Create assistant
                assistant = client.beta.assistants.create(
                    name=skill_name,
                    instructions=instructions,
                    model=model,
                    tools=[{"type": "file_search"}],
                    tool_resources={
                        "file_search": {
                            "vector_store_ids": [vector_store.id]
                        }
                    }
                )

            return {
                'success': True,
                'skill_id': assistant.id,
                'url': f"https://platform.openai.com/assistants/{assistant.id}",
                'message': f'Assistant created with {len(file_ids)} knowledge files'
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
        Validate OpenAI API key format.

        Args:
            api_key: API key to validate

        Returns:
            True if key starts with 'sk-'
        """
        return api_key.strip().startswith('sk-')

    def get_env_var_name(self) -> str:
        """
        Get environment variable name for OpenAI API key.

        Returns:
            'OPENAI_API_KEY'
        """
        return "OPENAI_API_KEY"

    def supports_enhancement(self) -> bool:
        """
        OpenAI supports AI enhancement via GPT-4o.

        Returns:
            True
        """
        return True

    def enhance(self, skill_dir: Path, api_key: str) -> bool:
        """
        Enhance SKILL.md using GPT-4o API.

        Args:
            skill_dir: Path to skill directory
            api_key: OpenAI API key

        Returns:
            True if enhancement succeeded
        """
        # Check for openai library
        try:
            from openai import OpenAI
        except ImportError:
            print("❌ Error: openai package not installed")
            print("Install with: pip install openai")
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

        print("\n🤖 Asking GPT-4o to enhance SKILL.md...")
        print(f"   Input: {len(prompt):,} characters")

        try:
            client = OpenAI(api_key=api_key)

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical writer creating Assistant instructions for OpenAI ChatGPT."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4096
            )

            enhanced_content = response.choices[0].message.content
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
            print(f"❌ Error calling OpenAI API: {e}")
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
        Build OpenAI API prompt for enhancement.

        Args:
            skill_name: Name of the skill
            references: Dictionary of reference content
            current_skill_md: Existing SKILL.md content (optional)

        Returns:
            Enhancement prompt for GPT-4o
        """
        prompt = f"""You are creating Assistant instructions for an OpenAI ChatGPT Assistant about: {skill_name}

I've scraped documentation and organized it into reference files. Your job is to create EXCELLENT Assistant instructions that will help the Assistant use this documentation effectively.

CURRENT INSTRUCTIONS:
{'```' if current_skill_md else '(none - create from scratch)'}
{current_skill_md or 'No existing instructions'}
{'```' if current_skill_md else ''}

REFERENCE DOCUMENTATION:
"""

        for filename, content in references.items():
            prompt += f"\n\n## {filename}\n```markdown\n{content[:30000]}\n```\n"

        prompt += """

YOUR TASK:
Create enhanced Assistant instructions that include:

1. **Clear role definition** - "You are an expert assistant for [topic]"
2. **Knowledge base description** - What documentation is attached
3. **Excellent Quick Reference** - Extract 5-10 of the BEST, most practical code examples from the reference docs
   - Choose SHORT, clear examples that demonstrate common tasks
   - Include both simple and intermediate examples
   - Annotate examples with clear descriptions
   - Use proper language tags (cpp, python, javascript, json, etc.)
4. **Response guidelines** - How the Assistant should help users
5. **Search strategy** - When to use file_search, how to find information
6. **DO NOT use YAML frontmatter** - This is plain text instructions for OpenAI

IMPORTANT:
- Extract REAL examples from the reference docs, don't make them up
- Prioritize SHORT, clear examples (5-20 lines max)
- Make it actionable and practical for the Assistant
- Write clear, direct instructions
- Focus on how the Assistant should behave and respond
- NO YAML frontmatter (no --- blocks)

OUTPUT:
Return ONLY the complete Assistant instructions as plain text.
"""

        return prompt
