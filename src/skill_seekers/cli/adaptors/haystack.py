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

    def format_skill_md(self, skill_dir: Path, metadata: SkillMetadata) -> str:
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

        Returns:
            JSON string containing array of Haystack Documents
        """
        documents = []

        # Convert SKILL.md (main documentation)
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            content = self._read_existing_content(skill_dir)
            if content.strip():
                documents.append(
                    {
                        "content": content,
                        "meta": {
                            "source": metadata.name,
                            "category": "overview",
                            "file": "SKILL.md",
                            "type": "documentation",
                            "version": metadata.version,
                        },
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

                            documents.append(
                                {
                                    "content": ref_content,
                                    "meta": {
                                        "source": metadata.name,
                                        "category": category,
                                        "file": ref_file.name,
                                        "type": "reference",
                                        "version": metadata.version,
                                    },
                                }
                            )
                    except Exception as e:
                        print(f"⚠️  Warning: Could not read {ref_file.name}: {e}")
                        continue

        # Return as formatted JSON
        return json.dumps(documents, indent=2, ensure_ascii=False)

    def package(self, skill_dir: Path, output_path: Path) -> Path:
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

        # Determine output filename
        if output_path.is_dir() or str(output_path).endswith("/"):
            output_path = Path(output_path) / f"{skill_dir.name}-haystack.json"
        elif not str(output_path).endswith(".json"):
            # Replace extension if needed
            output_str = str(output_path).replace(".zip", ".json").replace(".tar.gz", ".json")
            if not output_str.endswith("-haystack.json"):
                output_str = output_str.replace(".json", "-haystack.json")
            if not output_str.endswith(".json"):
                output_str += ".json"
            output_path = Path(output_str)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read metadata
        metadata = SkillMetadata(
            name=skill_dir.name,
            description=f"Haystack documents for {skill_dir.name}",
            version="1.0.0",
        )

        # Generate Haystack documents
        documents_json = self.format_skill_md(skill_dir, metadata)

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
        example_code = """
# Example: Load into Haystack 2.x

from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
import json

# Load documents
with open("{path}") as f:
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
""".format(
            path=package_path.name
        )

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
