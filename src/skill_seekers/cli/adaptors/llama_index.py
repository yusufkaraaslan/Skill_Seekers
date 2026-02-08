#!/usr/bin/env python3
"""
LlamaIndex Adaptor

Implements LlamaIndex Node format for RAG pipelines.
Converts Skill Seekers documentation into LlamaIndex-compatible Node objects.
"""

import json
from pathlib import Path
from typing import Any

from .base import SkillAdaptor, SkillMetadata


class LlamaIndexAdaptor(SkillAdaptor):
    """
    LlamaIndex platform adaptor.

    Handles:
    - LlamaIndex Node format (text + metadata + id)
    - JSON packaging with array of nodes
    - No upload (users import directly into code)
    - Optimized for query engines and indexes
    """

    PLATFORM = "llama-index"
    PLATFORM_NAME = "LlamaIndex (RAG Framework)"
    DEFAULT_API_ENDPOINT = None  # No upload endpoint

    def _generate_node_id(self, content: str, metadata: dict) -> str:
        """
        Generate a stable unique ID for a node.

        Args:
            content: Node content
            metadata: Node metadata

        Returns:
            Unique node ID (hash-based)
        """
        return self._generate_deterministic_id(content, metadata, format="hex")

    def format_skill_md(
        self, skill_dir: Path, metadata: SkillMetadata, enable_chunking: bool = False, **kwargs
    ) -> str:
        """
        Format skill as JSON array of LlamaIndex Nodes.

        Converts SKILL.md and all references/*.md into LlamaIndex Node format:
        {
          "text": "...",
          "metadata": {"source": "...", "category": "...", ...},
          "id_": "unique-hash-id",
          "embedding": null
        }

        Args:
            skill_dir: Path to skill directory
            metadata: Skill metadata
            enable_chunking: Enable intelligent chunking for large documents
            **kwargs: Additional chunking parameters (chunk_max_tokens, preserve_code_blocks)

        Returns:
            JSON string containing array of LlamaIndex Nodes
        """
        nodes = []

        # Convert SKILL.md (main documentation)
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            content = self._read_existing_content(skill_dir)
            if content.strip():
                node_metadata = {
                    "source": metadata.name,
                    "category": "overview",
                    "file": "SKILL.md",
                    "type": "documentation",
                    "version": metadata.version,
                }

                # Chunk if enabled
                chunks = self._maybe_chunk_content(
                    content,
                    node_metadata,
                    enable_chunking=enable_chunking,
                    chunk_max_tokens=kwargs.get("chunk_max_tokens", 512),
                    preserve_code_blocks=kwargs.get("preserve_code_blocks", True),
                    source_file="SKILL.md",
                )

                # Add all chunks as nodes
                for chunk_text, chunk_meta in chunks:
                    nodes.append(
                        {
                            "text": chunk_text,
                            "metadata": chunk_meta,
                            "id_": self._generate_node_id(chunk_text, chunk_meta),
                            "embedding": None,
                        }
                    )

        # Convert all reference files using base helper method
        for ref_file, ref_content in self._iterate_references(skill_dir):
            if ref_content.strip():
                # Derive category from filename
                category = ref_file.stem.replace("_", " ").lower()

                node_metadata = {
                    "source": metadata.name,
                    "category": category,
                    "file": ref_file.name,
                    "type": "reference",
                    "version": metadata.version,
                }

                # Chunk if enabled
                chunks = self._maybe_chunk_content(
                    ref_content,
                    node_metadata,
                    enable_chunking=enable_chunking,
                    chunk_max_tokens=kwargs.get("chunk_max_tokens", 512),
                    preserve_code_blocks=kwargs.get("preserve_code_blocks", True),
                    source_file=ref_file.name,
                )

                # Add all chunks as nodes
                for chunk_text, chunk_meta in chunks:
                    nodes.append(
                        {
                            "text": chunk_text,
                            "metadata": chunk_meta,
                            "id_": self._generate_node_id(chunk_text, chunk_meta),
                            "embedding": None,
                        }
                    )

        # Return as formatted JSON
        return json.dumps(nodes, indent=2, ensure_ascii=False)

    def package(
        self,
        skill_dir: Path,
        output_path: Path,
        enable_chunking: bool = False,
        chunk_max_tokens: int = 512,
        preserve_code_blocks: bool = True,
    ) -> Path:
        """
        Package skill into JSON file for LlamaIndex.

        Creates a JSON file containing an array of LlamaIndex Nodes ready
        for creating indexes, query engines, or vector stores.

        Args:
            skill_dir: Path to skill directory
            output_path: Output path/filename for JSON file

        Returns:
            Path to created JSON file
        """
        skill_dir = Path(skill_dir)

        # Determine output filename using base helper method
        output_path = self._format_output_path(skill_dir, Path(output_path), "-llama-index.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read metadata
        metadata = SkillMetadata(
            name=skill_dir.name,
            description=f"LlamaIndex nodes for {skill_dir.name}",
            version="1.0.0",
        )

        # Generate LlamaIndex nodes
        nodes_json = self.format_skill_md(
            skill_dir,
            metadata,
            enable_chunking=enable_chunking,
            chunk_max_tokens=chunk_max_tokens,
            preserve_code_blocks=preserve_code_blocks,
        )

        # Write to file
        output_path.write_text(nodes_json, encoding="utf-8")

        print(f"\n✅ LlamaIndex nodes packaged successfully!")
        print(f"📦 Output: {output_path}")

        # Parse and show stats
        nodes = json.loads(nodes_json)
        print(f"📊 Total nodes: {len(nodes)}")

        # Show category breakdown
        categories = {}
        for node in nodes:
            cat = node["metadata"].get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        print("📁 Categories:")
        for cat, count in sorted(categories.items()):
            print(f"   - {cat}: {count}")

        return output_path

    def upload(self, package_path: Path, _api_key: str, **_kwargs) -> dict[str, Any]:
        """
        LlamaIndex format does not support direct upload.

        Users should import the JSON file into their LlamaIndex code:

        ```python
        from llama_index.core.schema import TextNode
        import json

        # Load nodes
        with open("skill-llama-index.json") as f:
            nodes_data = json.load(f)

        # Convert to LlamaIndex Nodes
        nodes = [
            TextNode(
                text=node["text"],
                metadata=node["metadata"],
                id_=node["id_"]
            )
            for node in nodes_data
        ]

        # Create index
        from llama_index.core import VectorStoreIndex

        index = VectorStoreIndex(nodes)
        query_engine = index.as_query_engine()

        # Query
        response = query_engine.query("your question here")
        ```

        Args:
            package_path: Path to JSON file
            api_key: Not used
            **kwargs: Not used

        Returns:
            Result indicating no upload capability
        """
        example_code = f"""
# Example: Load into LlamaIndex

from llama_index.core.schema import TextNode
from llama_index.core import VectorStoreIndex
import json

# Load nodes
with open("{package_path.name}") as f:
    nodes_data = json.load(f)

# Convert to LlamaIndex Nodes
nodes = [
    TextNode(
        text=node["text"],
        metadata=node["metadata"],
        id_=node["id_"]
    )
    for node in nodes_data
]

# Create index
index = VectorStoreIndex(nodes)

# Create query engine
query_engine = index.as_query_engine()

# Query
response = query_engine.query("your question here")
print(response)
"""

        return {
            "success": False,
            "skill_id": None,
            "url": str(package_path.absolute()),
            "message": (
                f"LlamaIndex nodes packaged at: {package_path.absolute()}\n\n"
                "Load into your code:\n"
                f"{example_code}"
            ),
        }

    def validate_api_key(self, _api_key: str) -> bool:
        """
        LlamaIndex format doesn't use API keys for packaging.

        Args:
            api_key: Not used

        Returns:
            Always False (no API needed for packaging)
        """
        return False

    def get_env_var_name(self) -> str:
        """
        No API key needed for LlamaIndex packaging.

        Returns:
            Empty string
        """
        return ""

    def supports_enhancement(self) -> bool:
        """
        LlamaIndex format doesn't support AI enhancement.

        Enhancement should be done before conversion using:
        skill-seekers enhance output/skill/ --mode LOCAL

        Returns:
            False
        """
        return False

    def enhance(self, _skill_dir: Path, _api_key: str) -> bool:
        """
        LlamaIndex format doesn't support enhancement.

        Args:
            skill_dir: Not used
            api_key: Not used

        Returns:
            False
        """
        print("❌ LlamaIndex format does not support enhancement")
        print("   Enhance before packaging:")
        print("   skill-seekers enhance output/skill/ --mode LOCAL")
        print("   skill-seekers package output/skill/ --target llama-index")
        return False
