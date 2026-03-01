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
from skill_seekers.cli.arguments.common import DEFAULT_CHUNK_TOKENS, DEFAULT_CHUNK_OVERLAP_TOKENS


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
                    "description": "Skill package version",
                    "indexFilterable": True,
                    "indexSearchable": False,
                },
                {
                    "name": "doc_version",
                    "dataType": ["text"],
                    "description": "Documentation version (e.g., 16.2)",
                    "indexFilterable": True,
                    "indexSearchable": False,
                },
            ],
        }

    def format_skill_md(
        self, skill_dir: Path, metadata: SkillMetadata, enable_chunking: bool = False, **kwargs
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
            enable_chunking: Enable intelligent chunking for large documents
            **kwargs: Additional chunking parameters

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
                    "doc_version": metadata.doc_version,
                }

                # Chunk if enabled
                chunks = self._maybe_chunk_content(
                    content,
                    obj_metadata,
                    enable_chunking=enable_chunking,
                    chunk_max_tokens=kwargs.get("chunk_max_tokens", DEFAULT_CHUNK_TOKENS),
                    preserve_code_blocks=kwargs.get("preserve_code_blocks", True),
                    source_file="SKILL.md",
                    chunk_overlap_tokens=kwargs.get(
                        "chunk_overlap_tokens", DEFAULT_CHUNK_OVERLAP_TOKENS
                    ),
                )

                # Add all chunks as objects
                for chunk_text, chunk_meta in chunks:
                    objects.append(
                        {
                            "id": self._generate_uuid(chunk_text, chunk_meta),
                            "properties": {
                                "content": chunk_text,
                                "source": chunk_meta.get("source", metadata.name),
                                "category": chunk_meta.get("category", "overview"),
                                "file": chunk_meta.get("file", "SKILL.md"),
                                "type": chunk_meta.get("type", "documentation"),
                                "version": chunk_meta.get("version", metadata.version),
                                "doc_version": chunk_meta.get("doc_version", ""),
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
                    "doc_version": metadata.doc_version,
                }

                # Chunk if enabled
                chunks = self._maybe_chunk_content(
                    ref_content,
                    obj_metadata,
                    enable_chunking=enable_chunking,
                    chunk_max_tokens=kwargs.get("chunk_max_tokens", DEFAULT_CHUNK_TOKENS),
                    preserve_code_blocks=kwargs.get("preserve_code_blocks", True),
                    source_file=ref_file.name,
                    chunk_overlap_tokens=kwargs.get(
                        "chunk_overlap_tokens", DEFAULT_CHUNK_OVERLAP_TOKENS
                    ),
                )

                # Add all chunks as objects
                for chunk_text, chunk_meta in chunks:
                    objects.append(
                        {
                            "id": self._generate_uuid(chunk_text, chunk_meta),
                            "properties": {
                                "content": chunk_text,
                                "source": chunk_meta.get("source", metadata.name),
                                "category": chunk_meta.get("category", category),
                                "file": chunk_meta.get("file", ref_file.name),
                                "type": chunk_meta.get("type", "reference"),
                                "version": chunk_meta.get("version", metadata.version),
                                "doc_version": chunk_meta.get("doc_version", ""),
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
        chunk_max_tokens: int = DEFAULT_CHUNK_TOKENS,
        preserve_code_blocks: bool = True,
        chunk_overlap_tokens: int = DEFAULT_CHUNK_OVERLAP_TOKENS,
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

        # Read metadata from SKILL.md frontmatter
        metadata = self._build_skill_metadata(skill_dir)

        # Generate Weaviate objects
        weaviate_json = self.format_skill_md(
            skill_dir,
            metadata,
            enable_chunking=enable_chunking,
            chunk_max_tokens=chunk_max_tokens,
            preserve_code_blocks=preserve_code_blocks,
            chunk_overlap_tokens=chunk_overlap_tokens,
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

    def upload(self, package_path: Path, api_key: str | None = None, **kwargs) -> dict[str, Any]:
        """
        Upload packaged skill to Weaviate.

        Args:
            package_path: Path to packaged JSON
            api_key: Weaviate API key (for Weaviate Cloud)
            **kwargs:
                weaviate_url: Weaviate URL (default: http://localhost:8080)
                use_cloud: Use Weaviate Cloud (default: False)
                cluster_url: Weaviate Cloud cluster URL
                embedding_function: "openai", "sentence-transformers", or None
                openai_api_key: For OpenAI embeddings

        Returns:
            {"success": bool, "message": str, "class_name": str, "count": int}
        """
        try:
            import weaviate
        except ImportError:
            return {
                "success": False,
                "message": "weaviate-client not installed. Run: pip install weaviate-client",
            }

        # Load package
        with open(package_path) as f:
            data = json.load(f)

        # Connect to Weaviate
        try:
            if kwargs.get("use_cloud") and api_key:
                # Weaviate Cloud
                print(f"🌐 Connecting to Weaviate Cloud: {kwargs.get('cluster_url')}")
                client = weaviate.Client(
                    url=kwargs.get("cluster_url"),
                    auth_client_secret=weaviate.AuthApiKey(api_key=api_key),
                )
            else:
                # Local Weaviate instance
                weaviate_url = kwargs.get("weaviate_url", "http://localhost:8080")
                print(f"🌐 Connecting to Weaviate at: {weaviate_url}")
                client = weaviate.Client(url=weaviate_url)

            # Test connection
            if not client.is_ready():
                return {
                    "success": False,
                    "message": "Weaviate server not ready. Make sure Weaviate is running:\n  docker run -p 8080:8080 semitechnologies/weaviate:latest",
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to connect to Weaviate: {e}\n\nMake sure Weaviate is running or provide correct credentials.",
            }

        # Create schema
        try:
            client.schema.create_class(data["schema"])
            print(f"✅ Created schema: {data['class_name']}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"ℹ️  Schema already exists: {data['class_name']}")
            else:
                return {"success": False, "message": f"Schema creation failed: {e}"}

        # Handle embeddings
        embedding_function = kwargs.get("embedding_function")

        try:
            with client.batch as batch:
                batch.batch_size = 100

                if embedding_function == "openai":
                    # Generate embeddings with OpenAI
                    print("🔄 Generating OpenAI embeddings and uploading...")
                    embeddings = self._generate_openai_embeddings(
                        [obj["properties"]["content"] for obj in data["objects"]],
                        api_key=kwargs.get("openai_api_key"),
                    )

                    for i, obj in enumerate(data["objects"]):
                        batch.add_data_object(
                            data_object=obj["properties"],
                            class_name=data["class_name"],
                            uuid=obj["id"],
                            vector=embeddings[i],
                        )

                        if (i + 1) % 100 == 0:
                            print(f"  ✓ Uploaded {i + 1}/{len(data['objects'])} objects")

                elif embedding_function == "sentence-transformers":
                    # Use sentence-transformers (via shared base method)
                    contents = [obj["properties"]["content"] for obj in data["objects"]]
                    embeddings = self._generate_st_embeddings(contents)

                    for i, obj in enumerate(data["objects"]):
                        batch.add_data_object(
                            data_object=obj["properties"],
                            class_name=data["class_name"],
                            uuid=obj["id"],
                            vector=embeddings[i],
                        )

                        if (i + 1) % 100 == 0:
                            print(f"  ✓ Uploaded {i + 1}/{len(data['objects'])} objects")

                else:
                    # No embeddings - Weaviate will use its configured vectorizer
                    print("🔄 Uploading objects (Weaviate will generate embeddings)...")
                    for i, obj in enumerate(data["objects"]):
                        batch.add_data_object(
                            data_object=obj["properties"],
                            class_name=data["class_name"],
                            uuid=obj["id"],
                        )

                        if (i + 1) % 100 == 0:
                            print(f"  ✓ Uploaded {i + 1}/{len(data['objects'])} objects")

            count = len(data["objects"])
            print(f"✅ Upload complete! {count} objects added to Weaviate")

            return {
                "success": True,
                "message": f"Uploaded {count} objects to Weaviate class '{data['class_name']}'",
                "url": None,
                "class_name": data["class_name"],
                "count": count,
            }

        except ImportError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            return {"success": False, "message": f"Upload failed: {e}"}

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
