#!/usr/bin/env python3
"""
Chroma Adaptor

Implements Chroma vector database format for RAG pipelines.
Converts Skill Seekers documentation into Chroma-compatible format.
"""

import json
from pathlib import Path
from typing import Any

from .base import SkillAdaptor, SkillMetadata


class ChromaAdaptor(SkillAdaptor):
    """
    Chroma vector database adaptor.

    Handles:
    - Chroma-compatible document format
    - ID generation for documents
    - Metadata structure
    - Collection configuration hints
    - Persistent collection support
    """

    PLATFORM = "chroma"
    PLATFORM_NAME = "Chroma (Vector Database)"
    DEFAULT_API_ENDPOINT = None  # Chroma runs locally or self-hosted

    def _generate_id(self, content: str, metadata: dict) -> str:
        """
        Generate deterministic ID from content and metadata.

        Args:
            content: Document content
            metadata: Document metadata

        Returns:
            ID string (hex digest)
        """
        return self._generate_deterministic_id(content, metadata, format="hex")

    def format_skill_md(
        self,
        skill_dir: Path,
        metadata: SkillMetadata,
        enable_chunking: bool = False,
        **kwargs
    ) -> str:
        """
        Format skill as JSON for Chroma ingestion.

        Converts SKILL.md and all references/*.md into Chroma-compatible format:
        {
          "documents": [...],
          "metadatas": [...],
          "ids": [...]
        }

        Args:
            skill_dir: Path to skill directory
            metadata: Skill metadata
            enable_chunking: Enable intelligent chunking for large documents
            **kwargs: Additional chunking parameters (chunk_max_tokens, preserve_code_blocks)

        Returns:
            JSON string containing Chroma-compatible data
        """
        documents = []
        metadatas = []
        ids = []

        # Convert SKILL.md (main documentation)
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            content = self._read_existing_content(skill_dir)
            if content.strip():
                doc_metadata = {
                    "source": metadata.name,
                    "category": "overview",
                    "file": "SKILL.md",
                    "type": "documentation",
                    "version": metadata.version,
                }

                # Chunk if enabled
                chunks = self._maybe_chunk_content(
                    content,
                    doc_metadata,
                    enable_chunking=enable_chunking,
                    chunk_max_tokens=kwargs.get('chunk_max_tokens', 512),
                    preserve_code_blocks=kwargs.get('preserve_code_blocks', True),
                    source_file="SKILL.md"
                )

                # Add all chunks to parallel arrays
                for chunk_text, chunk_meta in chunks:
                    documents.append(chunk_text)
                    metadatas.append(chunk_meta)
                    ids.append(self._generate_id(chunk_text, chunk_meta))

        # Convert all reference files using base helper method
        for ref_file, ref_content in self._iterate_references(skill_dir):
            if ref_content.strip():
                # Derive category from filename
                category = ref_file.stem.replace("_", " ").lower()

                doc_metadata = {
                    "source": metadata.name,
                    "category": category,
                    "file": ref_file.name,
                    "type": "reference",
                    "version": metadata.version,
                }

                # Chunk if enabled
                chunks = self._maybe_chunk_content(
                    ref_content,
                    doc_metadata,
                    enable_chunking=enable_chunking,
                    chunk_max_tokens=kwargs.get('chunk_max_tokens', 512),
                    preserve_code_blocks=kwargs.get('preserve_code_blocks', True),
                    source_file=ref_file.name
                )

                # Add all chunks to parallel arrays
                for chunk_text, chunk_meta in chunks:
                    documents.append(chunk_text)
                    metadatas.append(chunk_meta)
                    ids.append(self._generate_id(chunk_text, chunk_meta))

        # Return Chroma-compatible format
        return json.dumps(
            {
                "documents": documents,
                "metadatas": metadatas,
                "ids": ids,
                "collection_name": metadata.name.replace("_", "-"),  # Chroma prefers hyphens
            },
            indent=2,
            ensure_ascii=False,
        )

    def package(
        self,
        skill_dir: Path,
        output_path: Path,
        enable_chunking: bool = False,
        chunk_max_tokens: int = 512,
        preserve_code_blocks: bool = True
    ) -> Path:
        """
        Package skill into JSON file for Chroma.

        Creates a JSON file containing documents, metadatas, and ids ready
        for Chroma collection import.

        Args:
            skill_dir: Path to skill directory
            output_path: Output path/filename for JSON file

        Returns:
            Path to created JSON file
        """
        skill_dir = Path(skill_dir)

        # Determine output filename using base helper method
        output_path = self._format_output_path(skill_dir, Path(output_path), "-chroma.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read metadata
        metadata = SkillMetadata(
            name=skill_dir.name,
            description=f"Chroma collection data for {skill_dir.name}",
            version="1.0.0",
        )

        # Generate Chroma data
        chroma_json = self.format_skill_md(
            skill_dir,
            metadata,
            enable_chunking=enable_chunking,
            chunk_max_tokens=chunk_max_tokens,
            preserve_code_blocks=preserve_code_blocks
        )

        # Write to file
        output_path.write_text(chroma_json, encoding="utf-8")

        print(f"\n✅ Chroma data packaged successfully!")
        print(f"📦 Output: {output_path}")

        # Parse and show stats
        data = json.loads(chroma_json)

        print(f"📊 Total documents: {len(data['documents'])}")
        print(f"📂 Collection name: {data['collection_name']}")

        # Show category breakdown
        categories = {}
        for meta in data["metadatas"]:
            cat = meta.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        print("📁 Categories:")
        for cat, count in sorted(categories.items()):
            print(f"   - {cat}: {count}")

        return output_path

    def upload(self, package_path: Path, _api_key: str, **_kwargs) -> dict[str, Any]:
        """
        Chroma format does not support direct upload.

        Users should import the JSON file into their Chroma instance:

        ```python
        import chromadb
        import json

        # Create client (persistent)
        client = chromadb.PersistentClient(path="./chroma_db")

        # Load data
        with open("skill-chroma.json") as f:
            data = json.load(f)

        # Create or get collection
        collection = client.get_or_create_collection(
            name=data["collection_name"]
        )

        # Add documents (Chroma generates embeddings automatically)
        collection.add(
            documents=data["documents"],
            metadatas=data["metadatas"],
            ids=data["ids"]
        )
        ```

        Args:
            package_path: Path to JSON file
            api_key: Not used
            **kwargs: Not used

        Returns:
            Result indicating no upload capability
        """
        example_code = """
# Example: Import into Chroma

import chromadb
import json
from openai import OpenAI

# Load data
with open("{path}") as f:
    data = json.load(f)

# Option 1: Persistent client (recommended)
client = chromadb.PersistentClient(path="./chroma_db")

# Option 2: In-memory client (for testing)
# client = chromadb.Client()

# Create or get collection
collection = client.get_or_create_collection(
    name=data["collection_name"],
    metadata={{"description": "Documentation from Skill Seekers"}}
)

# Option A: Let Chroma generate embeddings (default)
collection.add(
    documents=data["documents"],
    metadatas=data["metadatas"],
    ids=data["ids"]
)

# Option B: Use custom embeddings (OpenAI)
openai_client = OpenAI()
embeddings = []
for doc in data["documents"]:
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=doc
    )
    embeddings.append(response.data[0].embedding)

collection.add(
    documents=data["documents"],
    embeddings=embeddings,
    metadatas=data["metadatas"],
    ids=data["ids"]
)

print(f"✅ Added {{len(data['documents'])}} documents to collection")
print(f"📊 Total documents in collection: {{collection.count()}}")

# Query example (semantic search)
results = collection.query(
    query_texts=["your search query"],
    n_results=3
)

# Query with metadata filter
results = collection.query(
    query_texts=["search query"],
    n_results=5,
    where={{"category": "api"}}  # Filter by category
)

# Query with multiple filters (AND)
results = collection.query(
    query_texts=["search query"],
    n_results=5,
    where={{
        "$and": [
            {{"category": "api"}},
            {{"type": "reference"}}
        ]
    }}
)

# Get documents by ID
docs = collection.get(ids=[data["ids"][0]])

# Update collection (re-add with same IDs)
collection.update(
    ids=[data["ids"][0]],
    documents=["updated content"],
    metadatas=[data["metadatas"][0]]
)

# Delete documents
collection.delete(ids=[data["ids"][0]])

# Persist collection (if using PersistentClient, automatic on exit)
# Collection is automatically persisted to disk
""".format(
            path=package_path.name
        )

        return {
            "success": False,
            "skill_id": None,
            "url": str(package_path.absolute()),
            "message": (
                f"Chroma data packaged at: {package_path.absolute()}\n\n"
                "Import into Chroma:\n"
                f"{example_code}"
            ),
        }

    def validate_api_key(self, _api_key: str) -> bool:
        """
        Chroma format doesn't use API keys for packaging.

        Args:
            api_key: Not used

        Returns:
            Always False (no API needed for packaging)
        """
        return False

    def get_env_var_name(self) -> str:
        """
        No API key needed for Chroma packaging.

        Returns:
            Empty string
        """
        return ""

    def supports_enhancement(self) -> bool:
        """
        Chroma format doesn't support AI enhancement.

        Enhancement should be done before conversion using:
        skill-seekers enhance output/skill/ --mode LOCAL

        Returns:
            False
        """
        return False

    def enhance(self, _skill_dir: Path, _api_key: str) -> bool:
        """
        Chroma format doesn't support enhancement.

        Args:
            skill_dir: Not used
            api_key: Not used

        Returns:
            False
        """
        print("❌ Chroma format does not support enhancement")
        print("   Enhance before packaging:")
        print("   skill-seekers enhance output/skill/ --mode LOCAL")
        print("   skill-seekers package output/skill/ --target chroma")
        return False
