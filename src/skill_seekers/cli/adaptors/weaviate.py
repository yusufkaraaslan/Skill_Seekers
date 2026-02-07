#!/usr/bin/env python3
"""
Weaviate Adaptor

Implements Weaviate vector database format for RAG pipelines.
Converts Skill Seekers documentation into Weaviate-compatible objects with schema.
"""

import json
from pathlib import Path
from typing import Any

from .base import SkillAdaptor, SkillMetadata


class WeaviateAdaptor(SkillAdaptor):
    """
    Weaviate vector database adaptor.

    Handles:
    - Weaviate object format with properties
    - Auto-generated schema definition
    - UUID generation for objects
    - Cross-reference support
    - Metadata as properties for filtering
    - Hybrid search optimization (vector + keyword)
    """

    PLATFORM = "weaviate"
    PLATFORM_NAME = "Weaviate (Vector Database)"
    DEFAULT_API_ENDPOINT = None  # User provides their own Weaviate instance

    def _generate_uuid(self, content: str, metadata: dict) -> str:
        """
        Generate deterministic UUID from content and metadata.

        Args:
            content: Document content
            metadata: Document metadata

        Returns:
            UUID string (RFC 4122 format)
        """
        return self._generate_deterministic_id(content, metadata, format="uuid")

    def _generate_schema(self, class_name: str) -> dict:
        """
        Generate Weaviate schema for documentation class.

        Args:
            class_name: Name of the Weaviate class (e.g., "DocumentationChunk")

        Returns:
            Schema dictionary
        """
        return {
            "class": class_name,
            "description": "Documentation chunks from Skill Seekers",
            "vectorizer": "none",  # User provides vectors
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Full document content",
                    "indexFilterable": False,
                    "indexSearchable": True,
                },
                {
                    "name": "source",
                    "dataType": ["text"],
                    "description": "Source framework/project name",
                    "indexFilterable": True,
                    "indexSearchable": True,
                },
                {
                    "name": "category",
                    "dataType": ["text"],
                    "description": "Content category",
                    "indexFilterable": True,
                    "indexSearchable": True,
                },
                {
                    "name": "file",
                    "dataType": ["text"],
                    "description": "Source file name",
                    "indexFilterable": True,
                    "indexSearchable": False,
                },
                {
                    "name": "type",
                    "dataType": ["text"],
                    "description": "Document type (documentation/reference/code)",
                    "indexFilterable": True,
                    "indexSearchable": False,
                },
                {
                    "name": "version",
                    "dataType": ["text"],
                    "description": "Documentation version",
                    "indexFilterable": True,
                    "indexSearchable": False,
                },
            ],
        }

    def format_skill_md(
        self,
        skill_dir: Path,
        metadata: SkillMetadata,
        enable_chunking: bool = False,
        **kwargs
    ) -> str:
        """
        Format skill as JSON for Weaviate ingestion.

        Converts SKILL.md and all references/*.md into Weaviate objects:
        {
          "objects": [...],
          "schema": {...}
        }

        Args:
            skill_dir: Path to skill directory
            metadata: Skill metadata

        Returns:
            JSON string containing Weaviate objects and schema
        """
        objects = []

        # Convert SKILL.md (main documentation)
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            content = self._read_existing_content(skill_dir)
            if content.strip():
                obj_metadata = {
                    "source": metadata.name,
                    "category": "overview",
                    "file": "SKILL.md",
                    "type": "documentation",
                    "version": metadata.version,
                }

                objects.append(
                    {
                        "id": self._generate_uuid(content, obj_metadata),
                        "properties": {
                            "content": content,
                            "source": obj_metadata["source"],
                            "category": obj_metadata["category"],
                            "file": obj_metadata["file"],
                            "type": obj_metadata["type"],
                            "version": obj_metadata["version"],
                        },
                    }
                )

        # Convert all reference files using base helper method
        for ref_file, ref_content in self._iterate_references(skill_dir):
            if ref_content.strip():
                # Derive category from filename
                category = ref_file.stem.replace("_", " ").lower()

                obj_metadata = {
                    "source": metadata.name,
                    "category": category,
                    "file": ref_file.name,
                    "type": "reference",
                    "version": metadata.version,
                }

                objects.append(
                    {
                        "id": self._generate_uuid(ref_content, obj_metadata),
                        "properties": {
                            "content": ref_content,
                            "source": obj_metadata["source"],
                            "category": obj_metadata["category"],
                            "file": obj_metadata["file"],
                            "type": obj_metadata["type"],
                            "version": obj_metadata["version"],
                        },
                    }
                )

        # Generate schema
        class_name = "".join(word.capitalize() for word in metadata.name.split("_"))
        schema = self._generate_schema(class_name)

        # Return complete package
        return json.dumps(
            {"schema": schema, "objects": objects, "class_name": class_name},
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
        Package skill into JSON file for Weaviate.

        Creates a JSON file containing:
        - Schema definition
        - Objects ready for batch import
        - Helper metadata

        Args:
            skill_dir: Path to skill directory
            output_path: Output path/filename for JSON file

        Returns:
            Path to created JSON file
        """
        skill_dir = Path(skill_dir)

        # Determine output filename using base helper method
        output_path = self._format_output_path(skill_dir, Path(output_path), "-weaviate.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read metadata
        metadata = SkillMetadata(
            name=skill_dir.name,
            description=f"Weaviate objects for {skill_dir.name}",
            version="1.0.0",
        )

        # Generate Weaviate objects
        weaviate_json = self.format_skill_md(
            skill_dir,
            metadata,
            enable_chunking=enable_chunking,
            chunk_max_tokens=chunk_max_tokens,
            preserve_code_blocks=preserve_code_blocks
        )

        # Write to file
        output_path.write_text(weaviate_json, encoding="utf-8")

        print(f"\n✅ Weaviate objects packaged successfully!")
        print(f"📦 Output: {output_path}")

        # Parse and show stats
        data = json.loads(weaviate_json)
        objects = data["objects"]
        schema = data["schema"]

        print(f"📊 Total objects: {len(objects)}")
        print(f"📐 Schema class: {data['class_name']}")
        print(f"📋 Properties: {len(schema['properties'])}")

        # Show category breakdown
        categories = {}
        for obj in objects:
            cat = obj["properties"].get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        print("📁 Categories:")
        for cat, count in sorted(categories.items()):
            print(f"   - {cat}: {count}")

        return output_path

    def upload(self, package_path: Path, _api_key: str, **_kwargs) -> dict[str, Any]:
        """
        Weaviate format does not support direct upload.

        Users should import the JSON file into their Weaviate instance:

        ```python
        import weaviate
        import json

        # Connect to Weaviate
        client = weaviate.Client("http://localhost:8080")

        # Load data
        with open("skill-weaviate.json") as f:
            data = json.load(f)

        # Create schema
        client.schema.create_class(data["schema"])

        # Batch import objects
        with client.batch as batch:
            for obj in data["objects"]:
                batch.add_data_object(
                    data_object=obj["properties"],
                    class_name=data["class_name"],
                    uuid=obj["id"]
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
# Example: Import into Weaviate

import weaviate
import json
from openai import OpenAI

# Connect to Weaviate
client = weaviate.Client("http://localhost:8080")

# Load data
with open("{path}") as f:
    data = json.load(f)

# Create schema (first time only)
try:
    client.schema.create_class(data["schema"])
    print(f"✅ Created class: {{data['class_name']}}")
except Exception as e:
    print(f"Schema already exists or error: {{e}}")

# Generate embeddings and batch import
openai_client = OpenAI()

with client.batch as batch:
    batch.batch_size = 100
    for obj in data["objects"]:
        # Generate embedding
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=obj["properties"]["content"]
        )
        vector = response.data[0].embedding

        # Add to Weaviate with vector
        batch.add_data_object(
            data_object=obj["properties"],
            class_name=data["class_name"],
            uuid=obj["id"],
            vector=vector
        )

print(f"✅ Imported {{len(data['objects'])}} objects")

# Query example (semantic search)
result = client.query.get(
    data["class_name"],
    ["content", "category", "source"]
).with_near_text({{"concepts": ["your search query"]}}).with_limit(3).do()

# Query with filter (category = "api")
result = client.query.get(
    data["class_name"],
    ["content", "category"]
).with_where({{
    "path": ["category"],
    "operator": "Equal",
    "valueText": "api"
}}).with_near_text({{"concepts": ["search query"]}}).do()

# Hybrid search (vector + keyword)
result = client.query.get(
    data["class_name"],
    ["content", "source"]
).with_hybrid(
    query="search query",
    alpha=0.5  # 0=keyword only, 1=vector only
).do()
""".format(
            path=package_path.name
        )

        return {
            "success": False,
            "skill_id": None,
            "url": str(package_path.absolute()),
            "message": (
                f"Weaviate objects packaged at: {package_path.absolute()}\n\n"
                "Import into Weaviate:\n"
                f"{example_code}"
            ),
        }

    def validate_api_key(self, _api_key: str) -> bool:
        """
        Weaviate format doesn't use API keys for packaging.

        Args:
            api_key: Not used

        Returns:
            Always False (no API needed for packaging)
        """
        return False

    def get_env_var_name(self) -> str:
        """
        No API key needed for Weaviate packaging.

        Returns:
            Empty string
        """
        return ""

    def supports_enhancement(self) -> bool:
        """
        Weaviate format doesn't support AI enhancement.

        Enhancement should be done before conversion using:
        skill-seekers enhance output/skill/ --mode LOCAL

        Returns:
            False
        """
        return False

    def enhance(self, _skill_dir: Path, _api_key: str) -> bool:
        """
        Weaviate format doesn't support enhancement.

        Args:
            skill_dir: Not used
            api_key: Not used

        Returns:
            False
        """
        print("❌ Weaviate format does not support enhancement")
        print("   Enhance before packaging:")
        print("   skill-seekers enhance output/skill/ --mode LOCAL")
        print("   skill-seekers package output/skill/ --target weaviate")
        return False
