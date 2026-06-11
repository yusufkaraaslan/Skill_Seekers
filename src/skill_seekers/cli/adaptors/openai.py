#!/usr/bin/env python3
"""
OpenAI ChatGPT Adaptor

Implements platform-specific handling for OpenAI ChatGPT Assistants.
Uses Assistants API with Vector Store for file search.
"""

import json
import zipfile
from pathlib import Path
from typing import Any

from .base import SkillAdaptor, SkillMetadata
from skill_seekers.cli.arguments.common import DEFAULT_CHUNK_TOKENS, DEFAULT_CHUNK_OVERLAP_TOKENS


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
        if output_path.is_dir() or str(output_path).endswith("/"):
            output_path = Path(output_path) / f"{skill_dir.name}-openai.zip"
        elif not str(output_path).endswith(".zip") and not str(output_path).endswith("-openai.zip"):
            # Keep .zip extension
            output_str = str(output_path).replace(".zip", "-openai.zip")
            if not output_str.endswith(".zip"):
                output_str += ".zip"
            output_path = Path(output_str)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create ZIP file
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add SKILL.md as assistant_instructions.txt
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                instructions = skill_md.read_text(encoding="utf-8")
                zf.writestr("assistant_instructions.txt", instructions)

            # Add references directory as vector_store_files/
            refs_dir = skill_dir / "references"
            if refs_dir.exists():
                for ref_file in refs_dir.rglob("*.md"):
                    if ref_file.is_file() and not ref_file.name.startswith("."):
                        # Place all reference files in vector_store_files/
                        arcname = f"vector_store_files/{ref_file.name}"
                        zf.write(ref_file, arcname)

            # Create and add metadata file
            metadata = {
                "platform": "openai",
                "name": skill_dir.name,
                "version": "1.0.0",
                "created_with": "skill-seekers",
                "model": "gpt-4o",
                "tools": ["file_search"],
            }

            zf.writestr("openai_metadata.json", json.dumps(metadata, indent=2))

        return output_path

    def upload(self, package_path: Path, api_key: str, **kwargs) -> dict[str, Any]:
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

        # Check for openai library
        try:
            from openai import OpenAI
        except ImportError:
            return {
                "success": False,
                "skill_id": None,
                "url": None,
                "message": "openai library not installed. Run: pip install openai",
            }

        # Configure OpenAI client
        try:
            client = OpenAI(api_key=api_key)

            # Extract package to temp directory
            import tempfile

            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract ZIP
                with zipfile.ZipFile(package_path, "r") as zf:
                    zf.extractall(temp_dir)

                temp_path = Path(temp_dir)

                # Read instructions
                instructions_file = temp_path / "assistant_instructions.txt"
                if not instructions_file.exists():
                    return {
                        "success": False,
                        "skill_id": None,
                        "url": None,
                        "message": "Invalid package: assistant_instructions.txt not found",
                    }

                instructions = instructions_file.read_text(encoding="utf-8")

                # Read metadata
                metadata_file = temp_path / "openai_metadata.json"
                skill_name = package_path.stem
                model = kwargs.get("model", "gpt-4o")

                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                        skill_name = metadata.get("name", skill_name)
                        model = metadata.get("model", model)

                # Vector Stores were promoted from client.beta.vector_stores to
                # the top-level client.vector_stores in newer OpenAI SDKs; prefer
                # the top-level path and fall back to beta on older SDKs.
                vs_api = getattr(client, "vector_stores", None) or client.beta.vector_stores

                # Create vector store
                vector_store = vs_api.create(name=f"{skill_name} Documentation")

                # Upload reference files to vector store
                vector_files_dir = temp_path / "vector_store_files"
                file_ids = []

                if vector_files_dir.exists():
                    for ref_file in vector_files_dir.rglob("*.md"):
                        # Upload file
                        with open(ref_file, "rb") as f:
                            uploaded_file = client.files.create(file=f, purpose="assistants")
                            file_ids.append(uploaded_file.id)

                    # Attach files to vector store (batch attach lives on
                    # file_batches.create in both old and new SDKs)
                    if file_ids:
                        vs_api.file_batches.create(
                            vector_store_id=vector_store.id, file_ids=file_ids
                        )

                # Create assistant
                assistant = client.beta.assistants.create(
                    name=skill_name,
                    instructions=instructions,
                    model=model,
                    tools=[{"type": "file_search"}],
                    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
                )

            return {
                "success": True,
                "skill_id": assistant.id,
                "url": f"https://platform.openai.com/assistants/{assistant.id}",
                "message": f"Assistant created with {len(file_ids)} knowledge files",
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
        Validate OpenAI API key format.

        Args:
            api_key: API key to validate

        Returns:
            True if key starts with 'sk-'
        """
        return api_key.strip().startswith("sk-")

    def get_env_var_name(self) -> str:
        """
        Get environment variable name for OpenAI API key.

        Returns:
            'OPENAI_API_KEY'
        """
        return "OPENAI_API_KEY"

    def supports_upload(self) -> bool:
        """OpenAI supports uploading assistants via the OpenAI API."""
        return True

    def supports_enhancement(self) -> bool:
        """
        OpenAI supports AI enhancement via GPT-4o.

        Returns:
            True
        """
        return True

    def enhance(self, skill_dir: Path, api_key: str) -> bool:
        """Enhance SKILL.md using the OpenAI API (via AgentClient)."""
        return self._enhance_skill_md_via_client(
            skill_dir,
            api_key,
            provider="openai",
            model=self.config.get("custom_model") or "gpt-4o",
            system=(
                "You are an expert technical writer creating Assistant "
                "instructions for OpenAI ChatGPT."
            ),
        )

    def _build_enhancement_prompt(
        self, skill_name: str, references: dict[str, str], current_skill_md: str = None
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
{"```" if current_skill_md else "(none - create from scratch)"}
{current_skill_md or "No existing instructions"}
{"```" if current_skill_md else ""}

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
