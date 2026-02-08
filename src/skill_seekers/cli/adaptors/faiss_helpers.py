#!/usr/bin/env python3
"""
FAISS Helpers

Utilities for working with FAISS indexes for RAG pipelines.
Provides easy-to-use wrappers around FAISS with metadata management.
"""

import json
from pathlib import Path
from typing import Any

from .base import SkillAdaptor, SkillMetadata


class FAISSHelpers(SkillAdaptor):
    """
    FAISS helper adaptor.

    Provides utilities for:
    - FAISS index creation (multiple types)
    - Metadata management (JSON storage - safe and portable)
    - Save/load indexes with metadata
    - Batch document addition
    - Search with metadata filtering
    - Index optimization

    Note: FAISS doesn't have built-in metadata support, so we manage it separately.
    """

    PLATFORM = "faiss"
    PLATFORM_NAME = "FAISS (Similarity Search)"
    DEFAULT_API_ENDPOINT = None  # FAISS runs locally

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
        self, skill_dir: Path, metadata: SkillMetadata, enable_chunking: bool = False, **kwargs
    ) -> str:
        """
        Format skill as JSON for FAISS ingestion.

        Creates a package with:
        - documents: Array of document strings
        - metadatas: Array of metadata dicts
        - ids: Array of IDs
        - config: FAISS configuration hints

        Args:
            skill_dir: Path to skill directory
            metadata: Skill metadata
            enable_chunking: Enable intelligent chunking for large documents
            **kwargs: Additional chunking parameters

        Returns:
            JSON string containing FAISS-compatible data
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
                    chunk_max_tokens=kwargs.get("chunk_max_tokens", 512),
                    preserve_code_blocks=kwargs.get("preserve_code_blocks", True),
                    source_file="SKILL.md",
                )

                # Add all chunks to parallel arrays
                for chunk_text, chunk_meta in chunks:
                    documents.append(chunk_text)
                    metadatas.append(chunk_meta)
                    ids.append(self._generate_id(chunk_text, chunk_meta))

        # Convert all reference files using base helper method
        for ref_file, ref_content in self._iterate_references(skill_dir):
            if ref_content.strip():
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
                    chunk_max_tokens=kwargs.get("chunk_max_tokens", 512),
                    preserve_code_blocks=kwargs.get("preserve_code_blocks", True),
                    source_file=ref_file.name,
                )

                # Add all chunks to parallel arrays
                for chunk_text, chunk_meta in chunks:
                    documents.append(chunk_text)
                    metadatas.append(chunk_meta)
                    ids.append(self._generate_id(chunk_text, chunk_meta))

        # FAISS configuration hints
        config = {
            "index_type": "IndexFlatL2",  # Recommended starting point
            "dimension": 1536,  # OpenAI ada-002 default
            "metric": "L2",  # Euclidean distance
            "description": (
                "FAISS requires embeddings. Use OpenAI, Cohere, or local models "
                "to generate embeddings before adding to index."
            ),
        }

        return json.dumps(
            {
                "documents": documents,
                "metadatas": metadatas,
                "ids": ids,
                "config": config,
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
        preserve_code_blocks: bool = True,
    ) -> Path:
        """
        Package skill into JSON file for FAISS.

        Creates a JSON file containing documents, metadata, and FAISS config.

        Args:
            skill_dir: Path to skill directory
            output_path: Output path/filename for JSON file

        Returns:
            Path to created JSON file
        """
        skill_dir = Path(skill_dir)

        # Determine output filename using base helper method
        output_path = self._format_output_path(skill_dir, Path(output_path), "-faiss.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read metadata
        metadata = SkillMetadata(
            name=skill_dir.name,
            description=f"FAISS data for {skill_dir.name}",
            version="1.0.0",
        )

        # Generate FAISS data
        faiss_json = self.format_skill_md(
            skill_dir,
            metadata,
            enable_chunking=enable_chunking,
            chunk_max_tokens=chunk_max_tokens,
            preserve_code_blocks=preserve_code_blocks,
        )

        # Write to file
        output_path.write_text(faiss_json, encoding="utf-8")

        print(f"\n✅ FAISS data packaged successfully!")
        print(f"📦 Output: {output_path}")

        # Parse and show stats
        data = json.loads(faiss_json)

        print(f"📊 Total documents: {len(data['documents'])}")
        print(f"📐 Recommended index: {data['config']['index_type']}")
        print(f"📏 Embedding dimension: {data['config']['dimension']}")

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
        FAISS format does not support direct upload.

        Users should import the JSON file and create FAISS index.
        Metadata is stored as JSON (safe and portable).

        Args:
            package_path: Path to JSON file
            api_key: Not used
            **kwargs: Not used

        Returns:
            Result with usage instructions
        """
        example_code = f"""
# Example: Create FAISS index with JSON metadata (safe & portable)

import faiss
import json
import numpy as np
from openai import OpenAI
from pathlib import Path

# Load data
with open("{package_path.name}") as f:
    data = json.load(f)

# Generate embeddings (using OpenAI)
print("Generating embeddings...")
openai_client = OpenAI()
embeddings = []

for i, doc in enumerate(data["documents"]):
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=doc
    )
    embeddings.append(response.data[0].embedding)
    if (i + 1) % 10 == 0:
        print(f"  Generated {{i + 1}}/{{len(data['documents'])}} embeddings")

# Create FAISS index
dimension = len(embeddings[0])
print(f"\\nCreating FAISS index (dimension={{dimension}})...")

# Option 1: Flat index (exact search, best for <1M vectors)
index = faiss.IndexFlatL2(dimension)

# Option 2: IVF index (faster, approximate, for >100k vectors)
# quantizer = faiss.IndexFlatL2(dimension)
# index = faiss.IndexIVFFlat(quantizer, dimension, 100)
# index.train(np.array(embeddings).astype('float32'))

# Option 3: HNSW index (graph-based, very fast)
# index = faiss.IndexHNSWFlat(dimension, 32)

# Add vectors to index
vectors = np.array(embeddings).astype('float32')
index.add(vectors)
print(f"✅ Added {{index.ntotal}} vectors to index")

# Save index and metadata (using JSON - safe!)
output_dir = Path("faiss_db")
output_dir.mkdir(exist_ok=True)

faiss.write_index(index, str(output_dir / "docs.index"))

# Save metadata as JSON (secure and portable)
with open(output_dir / "metadata.json", "w") as f:
    json.dump({{
        "documents": data["documents"],
        "metadatas": data["metadatas"],
        "ids": data["ids"]
    }}, f, indent=2)

print(f"✅ Saved index to: {{output_dir}}/")

# Search with metadata
def search(query_text: str, k: int = 5):
    # Generate query embedding
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=query_text
    )
    query_vector = np.array([response.data[0].embedding]).astype('float32')

    # Search index
    distances, indices = index.search(query_vector, k)

    # Load metadata from JSON
    with open(output_dir / "metadata.json") as f:
        metadata_store = json.load(f)

    # Return results
    results = []
    for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
        results.append({{
            "rank": i + 1,
            "distance": float(dist),
            "metadata": metadata_store["metadatas"][idx],
            "text": metadata_store["documents"][idx][:200] + "..."
        }})

    return results

# Test search
results = search("How do I get started?")
for result in results:
    print(f"\\nRank {{result['rank']}} (distance={{result['distance']:.4f}}):")
    print(f"  Category: {{result['metadata']['category']}}")
    print(f"  File: {{result['metadata']['file']}}")
    print(f"  Text: {{result['text']}}")

# Load saved index (for later use)
def load_index(index_dir: str):
    index = faiss.read_index(str(Path(index_dir) / "docs.index"))
    with open(Path(index_dir) / "metadata.json") as f:
        metadata = json.load(f)
    return index, metadata

# Filtered search (post-processing with metadata)
def search_with_filter(query_text: str, category: str = None, k: int = 5):
    # Get more results for filtering
    results = search(query_text, k=50)

    # Filter by metadata
    if category:
        results = [r for r in results if r["metadata"]["category"] == category]

    return results[:k]

# Add new documents
def add_documents(new_docs: list, new_metadatas: list):
    # Generate embeddings
    new_embeddings = []
    for doc in new_docs:
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=doc
        )
        new_embeddings.append(response.data[0].embedding)

    # Add to index
    vectors = np.array(new_embeddings).astype('float32')
    index.add(vectors)

    # Update metadata (JSON)
    with open(output_dir / "metadata.json") as f:
        metadata = json.load(f)

    metadata["documents"].extend(new_docs)
    metadata["metadatas"].extend(new_metadatas)

    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # Save updated index
    faiss.write_index(index, str(output_dir / "docs.index"))
    print(f"✅ Added {{len(new_docs)}} documents")

# Index statistics
print(f"\\nIndex stats:")
print(f"  Total vectors: {{index.ntotal}}")
print(f"  Dimension: {{dimension}}")
print(f"  Type: {{type(index).__name__}}")
"""

        return {
            "success": False,
            "skill_id": None,
            "url": str(package_path.absolute()),
            "message": (
                f"FAISS data packaged at: {package_path.absolute()}\n\n"
                "Create FAISS index with JSON metadata (secure & portable):\n"
                f"{example_code}"
            ),
        }

    def validate_api_key(self, _api_key: str) -> bool:
        """FAISS doesn't use API keys."""
        return False

    def get_env_var_name(self) -> str:
        """FAISS doesn't use API keys."""
        return ""

    def supports_enhancement(self) -> bool:
        """FAISS format doesn't support AI enhancement."""
        return False

    def enhance(self, _skill_dir: Path, _api_key: str) -> bool:
        """FAISS format doesn't support enhancement."""
        print("❌ FAISS format does not support enhancement")
        print("   Enhance before packaging:")
        print("   skill-seekers enhance output/skill/ --mode LOCAL")
        print("   skill-seekers package output/skill/ --target faiss")
        return False
