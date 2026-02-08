#!/usr/bin/env python3
"""
Haystack Adaptor

Implements Haystack Document format for RAG pipelines.
Converts Skill Seekers documentation into Haystack-compatible Document objects.
"""

import json
from pathlib import Path
from typing import Any

from .base import SkillAdaptor, SkillMetadata


class HaystackAdaptor(SkillAdaptor):
    """
    Haystack platform adaptor.

    Handles:
    - Haystack Document format (content + meta)
    - JSON packaging with array of documents
    - No upload (users import directly into code)
    - Optimized for Haystack 2.x pipelines
    """

    PLATFORM = "haystack"
    PLATFORM_NAME = "Haystack (RAG Framework)"
    DEFAULT_API_ENDPOINT = None  # No upload endpoint

    def format_skill_md(
        self, skill_dir: Path, metadata: SkillMetadata, enable_chunking: bool = False, **kwargs
    ) -> str:
        """
        Format skill as JSON array of Haystack Documents.

        Converts SKILL.md and all references/*.md into Haystack Document format:
        {
          "content": "...",
          "meta": {"source": "...", "category": "...", ...}
        }

        Args:
            skill_dir: Path to skill directory
            metadata: Skill metadata
            enable_chunking: Enable intelligent chunking for large documents
            **kwargs: Additional chunking parameters

        Returns:
            JSON string containing array of Haystack Documents
        """
        documents = []

        # Convert SKILL.md (main documentation)
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            content = self._read_existing_content(skill_dir)
            if content.strip():
                doc_meta = {
                    "source": metadata.name,
                    "category": "overview",
                    "file": "SKILL.md",
                    "type": "documentation",
                    "version": metadata.version,
                }

                # Chunk if enabled
                chunks = self._maybe_chunk_content(
                    content,
                    doc_meta,
                    enable_chunking=enable_chunking,
                    chunk_max_tokens=kwargs.get("chunk_max_tokens", 512),
                    preserve_code_blocks=kwargs.get("preserve_code_blocks", True),
                    source_file="SKILL.md",
                )

                # Add all chunks as documents
                for chunk_text, chunk_meta in chunks:
                    documents.append(
                        {
                            "content": chunk_text,
                            "meta": chunk_meta,
                        }
                    )

        # Convert all reference files using base helper method
        for ref_file, ref_content in self._iterate_references(skill_dir):
            if ref_content.strip():
                # Derive category from filename
                category = ref_file.stem.replace("_", " ").lower()

                doc_meta = {
                    "source": metadata.name,
                    "category": category,
                    "file": ref_file.name,
                    "type": "reference",
                    "version": metadata.version,
                }

                # Chunk if enabled
                chunks = self._maybe_chunk_content(
                    ref_content,
                    doc_meta,
                    enable_chunking=enable_chunking,
                    chunk_max_tokens=kwargs.get("chunk_max_tokens", 512),
                    preserve_code_blocks=kwargs.get("preserve_code_blocks", True),
                    source_file=ref_file.name,
                )

                # Add all chunks as documents
                for chunk_text, chunk_meta in chunks:
                    documents.append(
                        {
                            "content": chunk_text,
                            "meta": chunk_meta,
                        }
                    )

        # Return as formatted JSON
        return json.dumps(documents, indent=2, ensure_ascii=False)

    def package(
        self,
        skill_dir: Path,
        output_path: Path,
        enable_chunking: bool = False,
        chunk_max_tokens: int = 512,
        preserve_code_blocks: bool = True,
    ) -> Path:
        """
        Package skill into JSON file for Haystack.

        Creates a JSON file containing an array of Haystack Documents ready
        for ingestion into Haystack 2.x pipelines and document stores.

        Args:
            skill_dir: Path to skill directory
            output_path: Output path/filename for JSON file

        Returns:
            Path to created JSON file
        """
        skill_dir = Path(skill_dir)

        # Determine output filename using base helper method
        output_path = self._format_output_path(skill_dir, Path(output_path), "-haystack.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read metadata
        metadata = SkillMetadata(
            name=skill_dir.name,
            description=f"Haystack documents for {skill_dir.name}",
            version="1.0.0",
        )

        # Generate Haystack documents
        documents_json = self.format_skill_md(
            skill_dir,
            metadata,
            enable_chunking=enable_chunking,
            chunk_max_tokens=chunk_max_tokens,
            preserve_code_blocks=preserve_code_blocks,
        )

        # Write to file
        output_path.write_text(documents_json, encoding="utf-8")

        print(f"\n✅ Haystack documents packaged successfully!")
        print(f"📦 Output: {output_path}")

        # Parse and show stats
        documents = json.loads(documents_json)
        print(f"📊 Total documents: {len(documents)}")

        # Show category breakdown
        categories = {}
        for doc in documents:
            cat = doc["meta"].get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        print("📁 Categories:")
        for cat, count in sorted(categories.items()):
            print(f"   - {cat}: {count}")

        return output_path

    def upload(self, package_path: Path, _api_key: str, **_kwargs) -> dict[str, Any]:
        """
        Haystack format does not support direct upload.

        Users should import the JSON file into their Haystack code:

        ```python
        from haystack import Document
        import json

        # Load documents
        with open("skill-haystack.json") as f:
            docs_data = json.load(f)

        # Convert to Haystack Documents
        documents = [
            Document(content=doc["content"], meta=doc["meta"])
            for doc in docs_data
        ]

        # Use with document store
        from haystack.document_stores.in_memory import InMemoryDocumentStore

        document_store = InMemoryDocumentStore()
        document_store.write_documents(documents)

        # Create pipeline
        from haystack.components.retrievers.in_memory import InMemoryBM25Retriever

        retriever = InMemoryBM25Retriever(document_store=document_store)
        results = retriever.run(query="your query here")
        ```

        Args:
            package_path: Path to JSON file
            api_key: Not used
            **kwargs: Not used

        Returns:
            Result indicating no upload capability
        """
        example_code = f"""
# Example: Load into Haystack 2.x

from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
import json

# Load documents
with open("{package_path.name}") as f:
    docs_data = json.load(f)

# Convert to Haystack Documents
documents = [
    Document(content=doc["content"], meta=doc["meta"])
    for doc in docs_data
]

# Create document store
document_store = InMemoryDocumentStore()
document_store.write_documents(documents)

# Create retriever
retriever = InMemoryBM25Retriever(document_store=document_store)

# Query
results = retriever.run(query="your question here")
for doc in results["documents"]:
    print(doc.content)
"""

        return {
            "success": False,
            "skill_id": None,
            "url": str(package_path.absolute()),
            "message": (
                f"Haystack documents packaged at: {package_path.absolute()}\n\n"
                "Load into your code:\n"
                f"{example_code}"
            ),
        }

    def validate_api_key(self, _api_key: str) -> bool:
        """
        Haystack format doesn't use API keys for packaging.

        Args:
            api_key: Not used

        Returns:
            Always False (no API needed for packaging)
        """
        return False

    def get_env_var_name(self) -> str:
        """
        No API key needed for Haystack packaging.

        Returns:
            Empty string
        """
        return ""

    def supports_enhancement(self) -> bool:
        """
        Haystack format doesn't support AI enhancement.

        Enhancement should be done before conversion using:
        skill-seekers enhance output/skill/ --mode LOCAL

        Returns:
            False
        """
        return False

    def enhance(self, _skill_dir: Path, _api_key: str) -> bool:
        """
        Haystack format doesn't support enhancement.

        Args:
            skill_dir: Not used
            api_key: Not used

        Returns:
            False
        """
        print("❌ Haystack format does not support enhancement")
        print("   Enhance before packaging:")
        print("   skill-seekers enhance output/skill/ --mode LOCAL")
        print("   skill-seekers package output/skill/ --target haystack")
        return False
