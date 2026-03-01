#!/usr/bin/env python3
"""
Base Adaptor for Multi-LLM Support

Defines the abstract interface that all platform-specific adaptors must implement.
This enables Skill Seekers to generate skills for multiple LLM platforms (Claude, Gemini, ChatGPT).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from skill_seekers.cli.arguments.common import DEFAULT_CHUNK_TOKENS, DEFAULT_CHUNK_OVERLAP_TOKENS


@dataclass
class SkillMetadata:
    """Universal skill metadata used across all platforms"""

    name: str
    description: str
    version: str = "1.0.0"
    doc_version: str = ""  # Documentation version (e.g., "16.2") for RAG metadata filtering
    author: str | None = None
    tags: list[str] = field(default_factory=list)


class SkillAdaptor(ABC):
    """
    Abstract base class for platform-specific skill adaptors.

    Each platform (Claude, Gemini, OpenAI) implements this interface to handle:
    - Platform-specific SKILL.md formatting
    - Platform-specific package structure (ZIP, tar.gz, etc.)
    - Platform-specific upload endpoints and authentication
    - Optional AI enhancement capabilities
    """

    # Platform identifiers (override in subclasses)
    PLATFORM: str = "unknown"  # e.g., "claude", "gemini", "openai"
    PLATFORM_NAME: str = "Unknown"  # e.g., "Claude AI (Anthropic)"
    DEFAULT_API_ENDPOINT: str | None = None

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize adaptor with optional configuration.

        Args:
            config: Platform-specific configuration options
        """
        self.config = config or {}

    @abstractmethod
    def format_skill_md(self, skill_dir: Path, metadata: SkillMetadata) -> str:
        """
        Format SKILL.md content with platform-specific frontmatter/structure.

        Different platforms require different formats:
        - Claude: YAML frontmatter + markdown
        - Gemini: Plain markdown (no frontmatter)
        - OpenAI: Assistant instructions format

        Args:
            skill_dir: Path to skill directory containing references/
            metadata: Skill metadata (name, description, version, etc.)

        Returns:
            Formatted SKILL.md content as string
        """
        pass

    @abstractmethod
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
        Package skill for platform (ZIP, tar.gz, etc.).

        Different platforms require different package formats:
        - Claude: .zip with SKILL.md, references/, scripts/, assets/
        - Gemini: .tar.gz with system_instructions.md, references/
        - OpenAI: .zip with assistant_instructions.txt, vector_store_files/

        Args:
            skill_dir: Path to skill directory to package
            output_path: Path for output package (file or directory)
            enable_chunking: Enable intelligent chunking for large documents
            chunk_max_tokens: Maximum tokens per chunk (default: 512)
            preserve_code_blocks: Preserve code blocks during chunking

        Returns:
            Path to created package file
        """
        pass

    @abstractmethod
    def upload(self, package_path: Path, api_key: str, **kwargs) -> dict[str, Any]:
        """
        Upload packaged skill to platform.

        Returns a standardized response dictionary for all platforms.

        Args:
            package_path: Path to packaged skill file
            api_key: Platform API key
            **kwargs: Additional platform-specific arguments

        Returns:
            Dictionary with keys:
            - success (bool): Whether upload succeeded
            - skill_id (str|None): Platform-specific skill/assistant ID
            - url (str|None): URL to view/manage skill
            - message (str): Success or error message
        """
        pass

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key format for this platform.

        Default implementation just checks if key is non-empty.
        Override for platform-specific validation.

        Args:
            api_key: API key to validate

        Returns:
            True if key format is valid
        """
        return bool(api_key and api_key.strip())

    def get_env_var_name(self) -> str:
        """
        Get expected environment variable name for API key.

        Returns:
            Environment variable name (e.g., "ANTHROPIC_API_KEY", "GOOGLE_API_KEY")
        """
        return f"{self.PLATFORM.upper()}_API_KEY"

    def supports_enhancement(self) -> bool:
        """
        Whether this platform supports AI-powered SKILL.md enhancement.

        Returns:
            True if platform can enhance skills
        """
        return False

    def enhance(self, _skill_dir: Path, _api_key: str) -> bool:
        """
        Optionally enhance SKILL.md using platform's AI.

        Only called if supports_enhancement() returns True.

        Args:
            skill_dir: Path to skill directory
            api_key: Platform API key

        Returns:
            True if enhancement succeeded
        """
        return False

    def _read_existing_content(self, skill_dir: Path) -> str:
        """
        Helper to read existing SKILL.md content (without frontmatter).

        Args:
            skill_dir: Path to skill directory

        Returns:
            SKILL.md content without YAML frontmatter
        """
        skill_md_path = skill_dir / "SKILL.md"
        if not skill_md_path.exists():
            return ""

        content = skill_md_path.read_text(encoding="utf-8")

        # Strip YAML frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()

        return content

    def _extract_quick_reference(self, skill_dir: Path) -> str:
        """
        Helper to extract quick reference section from references.

        Args:
            skill_dir: Path to skill directory

        Returns:
            Quick reference content as markdown string
        """
        index_path = skill_dir / "references" / "index.md"
        if not index_path.exists():
            return "See references/ directory for documentation."

        # Read index and extract relevant sections
        content = index_path.read_text(encoding="utf-8")
        return content[:500] + "..." if len(content) > 500 else content

    def _read_skill_md(self, skill_dir: Path) -> str:
        """
        Read SKILL.md file with error handling.

        Args:
            skill_dir: Path to skill directory

        Returns:
            SKILL.md contents

        Raises:
            FileNotFoundError: If SKILL.md doesn't exist
        """
        skill_md_path = skill_dir / "SKILL.md"

        if not skill_md_path.exists():
            # Return empty string instead of raising - let adaptors decide how to handle
            return ""

        return skill_md_path.read_text(encoding="utf-8")

    def _read_frontmatter(self, skill_dir: Path) -> dict[str, str]:
        """Read YAML frontmatter from SKILL.md.

        Args:
            skill_dir: Path to skill directory

        Returns:
            Dict of key-value pairs from the frontmatter block.
        """
        content = self._read_skill_md(skill_dir)
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter: dict[str, str] = {}
                for line in parts[1].strip().splitlines():
                    if ":" in line:
                        key, _, value = line.partition(":")
                        frontmatter[key.strip()] = value.strip()
                return frontmatter
        return {}

    def _build_skill_metadata(self, skill_dir: Path) -> SkillMetadata:
        """Build SkillMetadata from SKILL.md frontmatter.

        Reads name, description, version, and doc_version from frontmatter
        instead of using hardcoded defaults.

        Args:
            skill_dir: Path to skill directory

        Returns:
            SkillMetadata populated from frontmatter values.
        """
        fm = self._read_frontmatter(skill_dir)
        return SkillMetadata(
            name=skill_dir.name,
            description=fm.get("description", f"Documentation for {skill_dir.name}"),
            version=fm.get("version", "1.0.0"),
            doc_version=fm.get("doc_version", ""),
        )

    def _iterate_references(self, skill_dir: Path):
        """
        Iterate over all reference files in skill directory.

        Args:
            skill_dir: Path to skill directory

        Yields:
            Tuple of (file_path, file_content)
        """
        references_dir = skill_dir / "references"

        if not references_dir.exists():
            return

        for ref_file in sorted(references_dir.glob("*.md")):
            if ref_file.is_file() and not ref_file.name.startswith("."):
                try:
                    content = ref_file.read_text(encoding="utf-8")
                    yield ref_file, content
                except Exception as e:
                    print(f"⚠️  Warning: Could not read {ref_file.name}: {e}")
                    continue

    def _build_metadata_dict(self, metadata: SkillMetadata, **extra: Any) -> dict[str, Any]:
        """
        Build standard metadata dictionary from SkillMetadata.

        Args:
            metadata: SkillMetadata object
            **extra: Additional platform-specific fields

        Returns:
            Metadata dictionary
        """
        base_meta = {
            "source": metadata.name,
            "version": metadata.version,
            "doc_version": metadata.doc_version,
            "description": metadata.description,
        }
        if metadata.author:
            base_meta["author"] = metadata.author
        if metadata.tags:
            base_meta["tags"] = metadata.tags
        base_meta.update(extra)
        return base_meta

    def _maybe_chunk_content(
        self,
        content: str,
        metadata: dict,
        enable_chunking: bool = False,
        chunk_max_tokens: int = DEFAULT_CHUNK_TOKENS,
        preserve_code_blocks: bool = True,
        source_file: str = None,
        chunk_overlap_tokens: int = DEFAULT_CHUNK_OVERLAP_TOKENS,
    ) -> list[tuple[str, dict]]:
        """
        Optionally chunk content for RAG platforms.

        Args:
            content: Document content to chunk
            metadata: Base metadata for document
            enable_chunking: Whether to enable chunking
            chunk_max_tokens: Maximum tokens per chunk
            preserve_code_blocks: Preserve code blocks during chunking
            source_file: Source file name for tracking

        Returns:
            List of (chunk_text, chunk_metadata) tuples
            If chunking disabled or doc small: [(content, metadata)]
            If chunking enabled: [(chunk1, meta1), (chunk2, meta2), ...]
        """
        # Skip chunking if disabled or document is small
        if not enable_chunking:
            return [(content, metadata)]

        # Estimate tokens (~4 chars per token)
        estimated_tokens = len(content) // 4

        # Add some buffer for safety (20%)
        if estimated_tokens < (chunk_max_tokens * 0.8):
            # Document fits in single chunk (with buffer)
            return [(content, metadata)]

        # Initialize chunker with current settings (don't reuse to allow different settings per call)
        try:
            from skill_seekers.cli.rag_chunker import RAGChunker
        except ImportError:
            # RAGChunker not available - fall back to no chunking
            print("⚠️  Warning: RAGChunker not available, chunking disabled")
            return [(content, metadata)]

        # RAGChunker uses TOKENS (it converts to chars internally)
        # If overlap is at the default value but chunk size was customized,
        # scale overlap proportionally (10% of chunk size, min DEFAULT_CHUNK_OVERLAP_TOKENS)
        effective_overlap = chunk_overlap_tokens
        if (
            chunk_overlap_tokens == DEFAULT_CHUNK_OVERLAP_TOKENS
            and chunk_max_tokens != DEFAULT_CHUNK_TOKENS
        ):
            effective_overlap = max(DEFAULT_CHUNK_OVERLAP_TOKENS, chunk_max_tokens // 10)

        chunker = RAGChunker(
            chunk_size=chunk_max_tokens,
            chunk_overlap=effective_overlap,
            preserve_code_blocks=preserve_code_blocks,
            preserve_paragraphs=True,
            min_chunk_size=100,  # 100 tokens minimum
        )

        # Chunk the document
        chunks = chunker.chunk_document(
            text=content,
            metadata=metadata,
            source_file=source_file or metadata.get("file", "unknown"),
        )

        # Convert RAGChunker output format to (text, metadata) tuples
        result = []
        for chunk_dict in chunks:
            chunk_text = chunk_dict["page_content"]
            chunk_meta = {
                **metadata,  # Base metadata
                **chunk_dict["metadata"],  # RAGChunker metadata (chunk_index, etc.)
                "is_chunked": True,
                "chunk_id": chunk_dict["chunk_id"],
            }
            result.append((chunk_text, chunk_meta))

        return result

    def _format_output_path(self, skill_dir: Path, output_path: Path, suffix: str) -> Path:
        """
        Generate standardized output path with intelligent format handling.

        Handles three cases:
        1. output_path is a directory → generate filename with suffix
        2. output_path is a file without correct suffix → fix extension and add suffix
        3. output_path is already correct → use as-is

        Args:
            skill_dir: Input skill directory
            output_path: Output path (file or directory)
            suffix: Platform-specific suffix (e.g., "-langchain.json")

        Returns:
            Output file path with correct extension and suffix
        """
        skill_name = skill_dir.name

        # Case 1: Directory path - generate filename
        if output_path.is_dir() or str(output_path).endswith("/"):
            return Path(output_path) / f"{skill_name}{suffix}"

        # Case 2: File path without correct extension - fix it
        output_str = str(output_path)

        # Extract the file extension from suffix (e.g., ".json" from "-langchain.json")
        correct_ext = suffix.split(".")[-1] if "." in suffix else ""

        if correct_ext and not output_str.endswith(f".{correct_ext}"):
            # Replace common incorrect extensions
            output_str = output_str.replace(".zip", f".{correct_ext}").replace(
                ".tar.gz", f".{correct_ext}"
            )

            # Ensure platform suffix is present
            if not output_str.endswith(suffix):
                output_str = output_str.replace(f".{correct_ext}", suffix)

            # Add extension if still missing
            if not output_str.endswith(f".{correct_ext}"):
                output_str += f".{correct_ext}"

        return Path(output_str)

    def _generate_deterministic_id(self, content: str, metadata: dict, format: str = "hex") -> str:
        """
        Generate deterministic ID from content and metadata.

        Provides consistent ID generation across all RAG adaptors with platform-specific formatting.

        Args:
            content: Document content
            metadata: Document metadata
            format: ID format - 'hex', 'uuid', or 'uuid5'
                - 'hex': Plain MD5 hex digest (32 chars) - used by Chroma, FAISS
                - 'uuid': UUID format from MD5 (8-4-4-4-12) - used by Weaviate, Qdrant
                - 'uuid5': RFC 4122 UUID v5 (SHA-1 based) - used by LlamaIndex

        Returns:
            Generated ID string in requested format
        """
        import hashlib
        import uuid

        # Create stable input for hashing
        id_string = f"{metadata.get('source', '')}-{metadata.get('file', '')}-{content[:100]}"

        if format == "uuid5":
            # UUID v5 (SHA-1 based, RFC 4122 compliant)
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, id_string))

        # For hex and uuid formats, use MD5
        hash_obj = hashlib.md5(id_string.encode())
        hash_hex = hash_obj.hexdigest()

        if format == "uuid":
            # Format as UUID (8-4-4-4-12)
            return f"{hash_hex[:8]}-{hash_hex[8:12]}-{hash_hex[12:16]}-{hash_hex[16:20]}-{hash_hex[20:32]}"
        else:  # format == "hex"
            # Plain hex digest
            return hash_hex

    def _generate_openai_embeddings(
        self, documents: list[str], api_key: str | None = None
    ) -> list[list[float]]:
        """Generate embeddings using OpenAI text-embedding-3-small.

        Args:
            documents: List of document texts
            api_key: OpenAI API key (or uses OPENAI_API_KEY env var)

        Returns:
            List of embedding vectors
        """
        import os

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai") from None

        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set. Set via env var or --openai-api-key")

        client = OpenAI(api_key=api_key)
        embeddings: list[list[float]] = []
        batch_size = 100

        print(f"  Generating OpenAI embeddings for {len(documents)} documents...")

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            try:
                response = client.embeddings.create(input=batch, model="text-embedding-3-small")
                embeddings.extend([item.embedding for item in response.data])
                print(f"  ✓ Embedded {min(i + batch_size, len(documents))}/{len(documents)}")
            except Exception as e:
                raise Exception(f"OpenAI embedding generation failed: {e}") from e

        return embeddings

    def _generate_st_embeddings(self, documents: list[str]) -> list[list[float]]:
        """Generate embeddings using sentence-transformers (all-MiniLM-L6-v2).

        Args:
            documents: List of document texts

        Returns:
            List of embedding vectors
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. Run: pip install sentence-transformers"
            ) from None

        print(f"  Generating sentence-transformer embeddings for {len(documents)} documents...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(documents, show_progress_bar=True)
        return [emb.tolist() for emb in embeddings]

    def _generate_toc(self, skill_dir: Path) -> str:
        """
        Helper to generate table of contents from references.

        Args:
            skill_dir: Path to skill directory

        Returns:
            Table of contents as markdown string
        """
        refs_dir = skill_dir / "references"
        if not refs_dir.exists():
            return ""

        toc_lines = []
        for ref_file in sorted(refs_dir.glob("*.md")):
            if ref_file.name == "index.md":
                continue
            title = ref_file.stem.replace("_", " ").title()
            toc_lines.append(f"- [{title}](references/{ref_file.name})")

        return "\n".join(toc_lines)
