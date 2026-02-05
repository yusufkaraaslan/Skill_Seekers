#!/usr/bin/env python3
"""
LlamaIndex Adaptor

Implements LlamaIndex Node format for RAG pipelines.
Converts Skill Seekers documentation into LlamaIndex-compatible Node objects.
"""

import json
from pathlib import Path
from typing import Any
import hashlib

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
        # Create deterministic ID from content + source + file
        id_string = f"{metadata.get('source', '')}-{metadata.get('file', '')}-{content[:100]}"
        return hashlib.md5(id_string.encode()).hexdigest()

    def format_skill_md(self, skill_dir: Path, metadata: SkillMetadata) -> str:
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
                nodes.append(
                    {
                        "text": content,
                        "metadata": node_metadata,
                        "id_": self._generate_node_id(content, node_metadata),
                        "embedding": None,
                    }
                )

        # Convert all reference files
        refs_dir = skill_dir / "references"
        if refs_dir.exists():
            for ref_file in sorted(refs_dir.glob("*.md")):
                if ref_file.is_file() and not ref_file.name.startswith("."):
                    try:
                        ref_content = ref_file.read_text(encoding="utf-8")
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

                            nodes.append(
                                {
                                    "text": ref_content,
                                    "metadata": node_metadata,
                                    "id_": self._generate_node_id(ref_content, node_metadata),
                                    "embedding": None,
                                }
                            )
                    except Exception as e:
                        print(f"⚠️  Warning: Could not read {ref_file.name}: {e}")
                        continue

        # Return as formatted JSON
        return json.dumps(nodes, indent=2, ensure_ascii=False)

    def package(self, skill_dir: Path, output_path: Path) -> Path:
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

        # Determine output filename
        if output_path.is_dir() or str(output_path).endswith("/"):
            output_path = Path(output_path) / f"{skill_dir.name}-llama-index.json"
        elif not str(output_path).endswith(".json"):
            # Replace extension if needed
            output_str = str(output_path).replace(".zip", ".json").replace(".tar.gz", ".json")
            if not output_str.endswith("-llama-index.json"):
                output_str = output_str.replace(".json", "-llama-index.json")
            if not output_str.endswith(".json"):
                output_str += ".json"
            output_path = Path(output_str)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read metadata
        metadata = SkillMetadata(
            name=skill_dir.name,
            description=f"LlamaIndex nodes for {skill_dir.name}",
            version="1.0.0",
        )

        # Generate LlamaIndex nodes
        nodes_json = self.format_skill_md(skill_dir, metadata)

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
        example_code = """
# Example: Load into LlamaIndex

from llama_index.core.schema import TextNode
from llama_index.core import VectorStoreIndex
import json

# Load nodes
with open("{path}") as f:
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
""".format(
            path=package_path.name
        )

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
