#!/usr/bin/env python3
"""
Qdrant Vector Database Adaptor

Converts skill documentation to Qdrant format for vector similarity search.
Qdrant stores vectors and metadata together in collections with points.
"""

import json
from pathlib import Path
from typing import Any

from .base import SkillAdaptor, SkillMetadata


class QdrantAdaptor(SkillAdaptor):
    """
    Qdrant vector database adaptor.

    Provides format conversion for:
    - Qdrant collections (vector + payload format)
    - Point-based storage with metadata payloads
    - REST API compatible output
    - Collection configuration with distance metrics

    Note: Qdrant supports rich metadata payloads with filtering.
    """

    PLATFORM = "qdrant"
    PLATFORM_NAME = "Qdrant Vector Database"
    DEFAULT_API_ENDPOINT = "http://localhost:6333"

    def _generate_point_id(self, content: str, metadata: dict) -> str:
        """
        Generate deterministic point ID from content and metadata.

        Args:
            content: Document content
            metadata: Document metadata

        Returns:
            UUID string (version 5, deterministic)
        """
        return self._generate_deterministic_id(content, metadata, format="uuid5")

    def format_skill_md(
        self, skill_dir: Path, metadata: SkillMetadata, enable_chunking: bool = False, **kwargs
    ) -> str:
        """
        Format skill as Qdrant collection JSON.

        Creates a package with:
        - collection_name: Collection identifier
        - points: Array of point objects (id, vector, payload)
        - config: Collection configuration (vector size, distance metric)

        Args:
            skill_dir: Path to skill directory
            metadata: Skill metadata
            enable_chunking: Enable intelligent chunking for large documents
            **kwargs: Additional chunking parameters

        Returns:
            JSON string containing Qdrant-compatible data
        """
        points = []

        # Convert SKILL.md (main documentation)
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            content = self._read_existing_content(skill_dir)
            if content.strip():
                payload_meta = {
                    "source": metadata.name,
                    "category": "overview",
                    "file": "SKILL.md",
                    "type": "documentation",
                    "version": metadata.version,
                }

                # Chunk if enabled
                chunks = self._maybe_chunk_content(
                    content,
                    payload_meta,
                    enable_chunking=enable_chunking,
                    chunk_max_tokens=kwargs.get("chunk_max_tokens", 512),
                    preserve_code_blocks=kwargs.get("preserve_code_blocks", True),
                    source_file="SKILL.md",
                )

                # Add all chunks as points
                for chunk_text, chunk_meta in chunks:
                    point_id = self._generate_point_id(
                        chunk_text,
                        {
                            "source": chunk_meta.get("source", metadata.name),
                            "file": chunk_meta.get("file", "SKILL.md"),
                        },
                    )

                    points.append(
                        {
                            "id": point_id,
                            "vector": None,  # User will generate embeddings
                            "payload": {
                                "content": chunk_text,
                                "source": chunk_meta.get("source", metadata.name),
                                "category": chunk_meta.get("category", "overview"),
                                "file": chunk_meta.get("file", "SKILL.md"),
                                "type": chunk_meta.get("type", "documentation"),
                                "version": chunk_meta.get("version", metadata.version),
                            },
                        }
                    )

        # Convert all reference files using base helper method
        for ref_file, ref_content in self._iterate_references(skill_dir):
            if ref_content.strip():
                category = ref_file.stem.replace("_", " ").lower()

                payload_meta = {
                    "source": metadata.name,
                    "category": category,
                    "file": ref_file.name,
                    "type": "reference",
                    "version": metadata.version,
                }

                # Chunk if enabled
                chunks = self._maybe_chunk_content(
                    ref_content,
                    payload_meta,
                    enable_chunking=enable_chunking,
                    chunk_max_tokens=kwargs.get("chunk_max_tokens", 512),
                    preserve_code_blocks=kwargs.get("preserve_code_blocks", True),
                    source_file=ref_file.name,
                )

                # Add all chunks as points
                for chunk_text, chunk_meta in chunks:
                    point_id = self._generate_point_id(
                        chunk_text,
                        {
                            "source": chunk_meta.get("source", metadata.name),
                            "file": chunk_meta.get("file", ref_file.name),
                        },
                    )

                    points.append(
                        {
                            "id": point_id,
                            "vector": None,  # User will generate embeddings
                            "payload": {
                                "content": chunk_text,
                                "source": chunk_meta.get("source", metadata.name),
                                "category": chunk_meta.get("category", category),
                                "file": chunk_meta.get("file", ref_file.name),
                                "type": chunk_meta.get("type", "reference"),
                                "version": chunk_meta.get("version", metadata.version),
                            },
                        }
                    )

        # Qdrant configuration
        config = {
            "vector_size": 1536,  # OpenAI ada-002 default
            "distance": "Cosine",  # Recommended for semantic search
            "description": (
                "Qdrant requires embeddings. Use OpenAI, Cohere, or local models "
                "to generate embeddings before uploading points."
            ),
        }

        # Generate collection name (replace underscores, lowercase)
        collection_name = metadata.name.replace("_", "-").lower()

        return json.dumps(
            {
                "collection_name": collection_name,
                "points": points,
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
        Package skill into JSON file for Qdrant.

        Creates a JSON file containing points, payloads, and config.

        Args:
            skill_dir: Path to skill directory
            output_path: Output path/filename for JSON file

        Returns:
            Path to created JSON file
        """
        skill_dir = Path(skill_dir)

        # Determine output filename using base helper method
        output_path = self._format_output_path(skill_dir, Path(output_path), "-qdrant.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read metadata
        metadata = SkillMetadata(
            name=skill_dir.name,
            description=f"Qdrant data for {skill_dir.name}",
            version="1.0.0",
        )

        # Generate Qdrant data
        qdrant_json = self.format_skill_md(
            skill_dir,
            metadata,
            enable_chunking=enable_chunking,
            chunk_max_tokens=chunk_max_tokens,
            preserve_code_blocks=preserve_code_blocks,
        )

        # Write to file
        output_path.write_text(qdrant_json, encoding="utf-8")

        print(f"\n✅ Qdrant data packaged successfully!")
        print(f"📦 Output: {output_path}")

        # Parse and show stats
        data = json.loads(qdrant_json)

        print(f"📊 Collection: {data['collection_name']}")
        print(f"📐 Total points: {len(data['points'])}")
        print(f"📏 Vector size: {data['config']['vector_size']}")
        print(f"📊 Distance metric: {data['config']['distance']}")

        # Show category breakdown
        categories = {}
        for point in data["points"]:
            cat = point["payload"].get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        print("📁 Categories:")
        for cat, count in sorted(categories.items()):
            print(f"   - {cat}: {count}")

        return output_path

    def upload(self, package_path: Path, _api_key: str, **_kwargs) -> dict[str, Any]:
        """
        Qdrant format does not support direct upload via this tool.

        Users should use the Qdrant client library or REST API.
        Metadata is stored in payloads (native Qdrant feature).

        Args:
            package_path: Path to JSON file
            api_key: Not used (Qdrant can use API keys for cloud)
            **kwargs: Not used

        Returns:
            Result with usage instructions
        """
        example_code = f"""
# Example: Create Qdrant collection and upload points

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import json
from pathlib import Path
from openai import OpenAI

# Load data
with open("{package_path.name}") as f:
    data = json.load(f)

# Connect to Qdrant (local or cloud)
# Option 1: Local instance
client = QdrantClient(host="localhost", port=6333)

# Option 2: Qdrant Cloud
# client = QdrantClient(
#     url="https://your-cluster.qdrant.io",
#     api_key="your-api-key"
# )

# Create collection
collection_name = data["collection_name"]
vector_size = data["config"]["vector_size"]
distance = Distance.COSINE  # or Distance.EUCLID, Distance.DOT

print(f"Creating collection: {{collection_name}}")
client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=vector_size, distance=distance)
)

# Generate embeddings and upload points
print("Generating embeddings...")
openai_client = OpenAI()
points_to_upload = []

for i, point in enumerate(data["points"]):
    # Generate embedding
    content = point["payload"]["content"]
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=content
    )
    embedding = response.data[0].embedding

    # Create point with vector and payload
    points_to_upload.append(
        PointStruct(
            id=point["id"],
            vector=embedding,
            payload=point["payload"]
        )
    )

    if (i + 1) % 10 == 0:
        print(f"  Generated {{i + 1}}/{{len(data['points'])}} embeddings")

# Upload points in batch
print(f"\\nUploading {{len(points_to_upload)}} points...")
client.upsert(
    collection_name=collection_name,
    points=points_to_upload
)
print(f"✅ Uploaded {{len(points_to_upload)}} points to Qdrant")

# Search with metadata filtering
def search(query_text: str, category_filter: str = None, k: int = 5):
    # Generate query embedding
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=query_text
    )
    query_vector = response.data[0].embedding

    # Build filter
    filter_dict = None
    if category_filter:
        filter_dict = {{
            "must": [
                {{"key": "category", "match": {{"value": category_filter}}}}
            ]
        }}

    # Search
    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=k,
        query_filter=filter_dict
    )

    return results

# Test search
results = search("How do I get started?")
for i, result in enumerate(results, 1):
    print(f"\\nRank {{i}} (score={{result.score:.4f}}):")
    print(f"  Category: {{result.payload['category']}}")
    print(f"  File: {{result.payload['file']}}")
    print(f"  Text: {{result.payload['content'][:200]}}...")

# Advanced filtering examples
# Filter by multiple conditions
results = search(
    "configuration options",
    category_filter="api"  # Only search in "api" category
)

# Complex filter with multiple conditions
from qdrant_client.models import Filter, FieldCondition, MatchValue

filter_complex = Filter(
    must=[
        FieldCondition(key="category", match=MatchValue(value="api")),
        FieldCondition(key="type", match=MatchValue(value="documentation"))
    ]
)

results = client.search(
    collection_name=collection_name,
    query_vector=query_vector,
    limit=5,
    query_filter=filter_complex
)

# Update point payload
client.set_payload(
    collection_name=collection_name,
    payload={{"updated": True, "last_updated": "2026-02-05"}},
    points=["point-id-1", "point-id-2"]
)

# Delete points by filter
client.delete(
    collection_name=collection_name,
    points_selector={{"filter": {{"must": [{{"key": "category", "match": {{"value": "deprecated"}}}}]}}}}
)

# Get collection info
info = client.get_collection(collection_name)
print(f"\\nCollection stats:")
print(f"  Points: {{info.points_count}}")
print(f"  Vectors: {{info.vectors_count}}")
print(f"  Status: {{info.status}}")

# Scroll through all points (pagination)
offset = None
all_points = []

while True:
    records, next_offset = client.scroll(
        collection_name=collection_name,
        limit=100,
        offset=offset
    )
    all_points.extend(records)

    if next_offset is None:
        break
    offset = next_offset

print(f"\\nRetrieved {{len(all_points)}} total points")

# Create snapshot (backup)
snapshot_info = client.create_snapshot(collection_name)
print(f"\\nSnapshot created: {{snapshot_info.name}}")

# Recommend similar documents
similar = client.recommend(
    collection_name=collection_name,
    positive=["point-id-1"],  # Similar to this
    negative=["point-id-2"],  # But not this
    limit=5
)
"""

        return {
            "success": False,
            "skill_id": None,
            "url": str(package_path.absolute()),
            "message": (
                f"Qdrant data packaged at: {package_path.absolute()}\n\n"
                "Create Qdrant collection and upload points:\n"
                f"{example_code}"
            ),
        }

    def validate_api_key(self, _api_key: str) -> bool:
        """Qdrant Cloud uses API keys, local instances don't."""
        return False

    def get_env_var_name(self) -> str:
        """Qdrant Cloud API key (optional)."""
        return "QDRANT_API_KEY"

    def supports_enhancement(self) -> bool:
        """Qdrant format doesn't support AI enhancement."""
        return False

    def enhance(self, _skill_dir: Path, _api_key: str) -> bool:
        """Qdrant format doesn't support enhancement."""
        print("❌ Qdrant format does not support enhancement")
        print("   Enhance before packaging:")
        print("   skill-seekers enhance output/skill/ --mode LOCAL")
        print("   skill-seekers package output/skill/ --target qdrant")
        return False
