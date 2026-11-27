#!/usr/bin/env python3
"""
OpenAI ChatGPT Adaptor

Package instructions and publish searchable references for the OpenAI Responses API.
"""

import json
from contextlib import ExitStack
import zipfile
from pathlib import Path
from typing import Any

from .base import SkillAdaptor, SkillMetadata
from skill_seekers.cli.agent_client import AgentClient
from skill_seekers.cli.arguments.common import DEFAULT_CHUNK_TOKENS, DEFAULT_CHUNK_OVERLAP_TOKENS


class OpenAIAdaptor(SkillAdaptor):
    """
    OpenAI ChatGPT platform adaptor.

    Handles:
    - Assistant instructions format (not YAML frontmatter)
    - ZIP packaging for the Responses API
    - Upload publishes instructions and an indexed vector store
    - AI enhancement using GPT-4o
    """

    PLATFORM = "openai"
    PLATFORM_NAME = "OpenAI ChatGPT"
    DEFAULT_API_ENDPOINT = "https://api.openai.com/v1/vector_stores"

    def format_skill_md(self, skill_dir: Path, metadata: SkillMetadata) -> str:
        """
        Format SKILL.md as Assistant instructions.

        The Responses API accepts instructions as text.

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
        Package instructions and reference files for OpenAI.

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
                        arcname = f"vector_store_files/{ref_file.relative_to(refs_dir).as_posix()}"
                        zf.write(ref_file, arcname)

            # Create and add metadata file
            metadata = {
                "platform": "openai",
                "name": skill_dir.name,
                "version": "1.0.0",
                "created_with": "skill-seekers",
                "model": self.config.get("custom_model") or AgentClient.get_model("openai"),
                "tools": ["file_search"],
            }

            zf.writestr("openai_metadata.json", json.dumps(metadata, indent=2))

        return output_path

    def upload(self, package_path: Path, api_key: str, **kwargs) -> dict[str, Any]:
        """Publish a Responses API knowledge base and return its vector store ID.

        Store metadata identifies the instructions file and model. Only reference
        files are indexed. Each upload owns its resources until indexing succeeds.
        """
        package_path = Path(package_path)
        failure = {"success": False, "skill_id": None, "url": None}
        if not package_path.is_file():
            return {**failure, "message": f"File not found: {package_path}"}
        if package_path.suffix != ".zip":
            return {**failure, "message": f"Not a ZIP file: {package_path}"}

        try:
            from openai import NotFoundError, OpenAI
        except ImportError:
            return {
                **failure,
                "message": "OpenAI SDK not installed or outdated. Install skill-seekers[openai].",
            }

        cleanup_errors = []

        def delete_resource(delete, resource_id):
            try:
                delete(resource_id)
            except NotFoundError:
                pass  # The resource is already gone.
            except Exception as exc:
                cleanup_errors.append(f"{resource_id} ({exc})")

        try:
            with zipfile.ZipFile(package_path) as archive:
                if "assistant_instructions.txt" not in archive.namelist():
                    raise ValueError("Invalid package: assistant_instructions.txt not found")
                instructions = archive.read("assistant_instructions.txt").decode("utf-8")
                if not instructions.strip():
                    raise ValueError("Invalid package: assistant_instructions.txt is empty")
                metadata = {}
                if "openai_metadata.json" in archive.namelist():
                    metadata = json.loads(archive.read("openai_metadata.json"))
                if not isinstance(metadata, dict):
                    raise ValueError("Invalid package: openai_metadata.json must be an object")
                model = (
                    kwargs.get("model")
                    or self.config.get("custom_model")
                    or metadata.get("model")
                    or AgentClient.get_model("openai")
                )
                name = metadata.get("name") or package_path.stem
                references = [
                    info
                    for info in archive.infolist()
                    if info.filename.startswith("vector_store_files/")
                    and info.filename.endswith(".md")
                ]

                # A lost response to a create request can leave an unknown resource.
                # Do not automatically repeat such requests.
                with OpenAI(api_key=api_key, max_retries=0) as client, ExitStack() as rollback:
                    stores = client.vector_stores
                    instructions_file = client.files.create(
                        file=("assistant_instructions.txt", instructions.encode("utf-8")),
                        purpose="user_data",
                    )
                    rollback.callback(delete_resource, client.files.delete, instructions_file.id)
                    store = stores.create(
                        name=f"{name} Documentation",
                        metadata={"instructions_file_id": instructions_file.id, "model": model},
                    )
                    rollback.callback(delete_resource, stores.delete, store.id)

                    # Batch ingestion accepts up to 500 file IDs per request.
                    for offset in range(0, len(references), 500):
                        file_ids = []
                        for info in references[offset : offset + 500]:
                            with archive.open(info) as ref:
                                uploaded = client.files.create(
                                    file=(Path(info.filename).name, ref), purpose="user_data"
                                )
                            rollback.callback(delete_resource, client.files.delete, uploaded.id)
                            file_ids.append(uploaded.id)
                        batch = stores.file_batches.create_and_poll(
                            vector_store_id=store.id, file_ids=file_ids
                        )
                        if batch.status != "completed" or batch.file_counts.completed != len(
                            file_ids
                        ):
                            raise RuntimeError(
                                f"Indexing batch {batch.id} ended with status {batch.status}: "
                                f"{batch.file_counts.completed}/{len(file_ids)} files indexed"
                            )
                    rollback.pop_all()

            return {
                "success": True,
                "skill_id": store.id,
                "vector_store_id": store.id,
                "instructions_file_id": instructions_file.id,
                "model": model,
                "url": None,
                "message": f"Responses API vector store {store.id} is ready with {len(references)} reference files. "
                f"Instructions file: {instructions_file.id}.",
            }
        except Exception as exc:
            message = f"Upload failed: {exc}"
            if cleanup_errors:
                message += ". Cleanup failed for: " + ", ".join(cleanup_errors)
            return {**failure, "message": message}

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
        """OpenAI supports publishing Responses API knowledge bases."""
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
            model=self.config.get("custom_model") or AgentClient.get_model("openai"),
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
