#!/usr/bin/env python3
"""
Pinecone Adaptor

Implements Pinecone vector database format for RAG pipelines.
Converts Skill Seekers documentation into Pinecone-compatible format
with namespace support and batch upsert.
"""

import json
from pathlib import Path
from typing import Any

from .base import SkillAdaptor, SkillMetadata
from skill_seekers.cli.arguments.common import DEFAULT_CHUNK_TOKENS, DEFAULT_CHUNK_OVERLAP_TOKENS

# Pinecone metadata value limit: 40 KB per vector
PINECONE_METADATA_BYTES_LIMIT = 40_000


class PineconeAdaptor(SkillAdaptor):
    """
    Pinecone vector database adaptor.

    Handles:
    - Pinecone-compatible vector format with metadata
    - Namespace support for multi-tenant indexing
    - Batch upsert (100 vectors per batch)
    - OpenAI and sentence-transformers embedding generation
    - Metadata truncation to stay within Pinecone's 40KB limit
    """

    PLATFORM = "pinecone"
    PLATFORM_NAME = "Pinecone (Vector Database)"
    DEFAULT_API_ENDPOINT = None

    def _generate_id(self, content: str, metadata: dict) -> str:
        """Generate deterministic ID from content and metadata."""
        return self._generate_deterministic_id(content, metadata, format="hex")

    def _truncate_text_for_metadata(
        self, text: str, max_bytes: int = PINECONE_METADATA_BYTES_LIMIT
    ) -> str:
        """Truncate text to fit within Pinecone's metadata byte limit.

        Pinecone limits metadata to 40KB per vector. This truncates
        the text field (largest metadata value) to stay within limits,
        leaving room for other metadata fields (~1KB overhead).

        Args:
            text: Text content to potentially truncate
            max_bytes: Maximum bytes for the text field

        Returns:
            Truncated text that fits within the byte limit
        """
        # Reserve ~2KB for other metadata fields
        available = max_bytes - 2000
        encoded = text.encode("utf-8")
        if len(encoded) <= available:
            return text
        # Truncate at byte boundary, decode safely
        truncated = encoded[:available].decode("utf-8", errors="ignore")
        return truncated

    def format_skill_md(
        self, skill_dir: Path, metadata: SkillMetadata, enable_chunking: bool = False, **kwargs
    ) -> str:
        """
        Format skill as JSON for Pinecone ingestion.

        Creates a package with vectors ready for upsert:
        {
          "index_name": "...",
          "namespace": "...",
          "dimension": 1536,
          "metric": "cosine",
          "vectors": [
            {
              "id": "hex-id",
              "metadata": {
                "text": "content",
                "source": "...",
                "category": "...",
                ...
              }
            }
          ]
        }

        No ``values`` field — embeddings are added at upload time.

        Args:
            skill_dir: Path to skill directory
            metadata: Skill metadata
            enable_chunking: Enable intelligent chunking for large documents
            **kwargs: Additional chunking parameters

        Returns:
            JSON string containing Pinecone-compatible data
        """
        vectors: list[dict[str, Any]] = []

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
                    "doc_version": metadata.doc_version,
                }

                chunks = self._maybe_chunk_content(
                    content,
                    doc_metadata,
                    enable_chunking=enable_chunking,
                    chunk_max_tokens=kwargs.get("chunk_max_tokens", DEFAULT_CHUNK_TOKENS),
                    preserve_code_blocks=kwargs.get("preserve_code_blocks", True),
                    source_file="SKILL.md",
                    chunk_overlap_tokens=kwargs.get(
                        "chunk_overlap_tokens", DEFAULT_CHUNK_OVERLAP_TOKENS
                    ),
                )

                for chunk_text, chunk_meta in chunks:
                    vectors.append(
                        {
                            "id": self._generate_id(chunk_text, chunk_meta),
                            "metadata": {
                                **chunk_meta,
                                "text": self._truncate_text_for_metadata(chunk_text),
                            },
                        }
                    )

        # Convert all reference files
        for ref_file, ref_content in self._iterate_references(skill_dir):
            if ref_content.strip():
                category = ref_file.stem.replace("_", " ").lower()

                doc_metadata = {
                    "source": metadata.name,
                    "category": category,
                    "file": ref_file.name,
                    "type": "reference",
                    "version": metadata.version,
                    "doc_version": metadata.doc_version,
                }

                chunks = self._maybe_chunk_content(
                    ref_content,
                    doc_metadata,
                    enable_chunking=enable_chunking,
                    chunk_max_tokens=kwargs.get("chunk_max_tokens", DEFAULT_CHUNK_TOKENS),
                    preserve_code_blocks=kwargs.get("preserve_code_blocks", True),
                    source_file=ref_file.name,
                    chunk_overlap_tokens=kwargs.get(
                        "chunk_overlap_tokens", DEFAULT_CHUNK_OVERLAP_TOKENS
                    ),
                )

                for chunk_text, chunk_meta in chunks:
                    vectors.append(
                        {
                            "id": self._generate_id(chunk_text, chunk_meta),
                            "metadata": {
                                **chunk_meta,
                                "text": self._truncate_text_for_metadata(chunk_text),
                            },
                        }
                    )

        index_name = metadata.name.replace("_", "-").lower()

        return json.dumps(
            {
                "index_name": index_name,
                "namespace": index_name,
                "dimension": 1536,
                "metric": "cosine",
                "vectors": vectors,
            },
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
        Package skill into JSON file for Pinecone.

        Creates a JSON file containing vectors with metadata, ready for
        embedding generation and upsert to a Pinecone index.

        Args:
            skill_dir: Path to skill directory
            output_path: Output path/filename for JSON file
            enable_chunking: Enable intelligent chunking for large documents
            chunk_max_tokens: Maximum tokens per chunk (default: 512)
            preserve_code_blocks: Preserve code blocks during chunking

        Returns:
            Path to created JSON file
        """
        skill_dir = Path(skill_dir)

        output_path = self._format_output_path(skill_dir, Path(output_path), "-pinecone.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read metadata from SKILL.md frontmatter
        metadata = self._build_skill_metadata(skill_dir)

        pinecone_json = self.format_skill_md(
            skill_dir,
            metadata,
            enable_chunking=enable_chunking,
            chunk_max_tokens=chunk_max_tokens,
            preserve_code_blocks=preserve_code_blocks,
            chunk_overlap_tokens=chunk_overlap_tokens,
        )

        output_path.write_text(pinecone_json, encoding="utf-8")

        print(f"\n✅ Pinecone data packaged successfully!")
        print(f"📦 Output: {output_path}")

        data = json.loads(pinecone_json)
        print(f"📊 Total vectors: {len(data['vectors'])}")
        print(f"🗂️  Index name: {data['index_name']}")
        print(f"📁 Namespace: {data['namespace']}")
        print(f"📐 Default dimension: {data['dimension']} (auto-detected at upload time)")

        # Show category breakdown
        categories: dict[str, int] = {}
        for vec in data["vectors"]:
            cat = vec["metadata"].get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        print("📁 Categories:")
        for cat, count in sorted(categories.items()):
            print(f"   - {cat}: {count}")

        return output_path

    def upload(self, package_path: Path, api_key: str | None = None, **kwargs) -> dict[str, Any]:
        """
        Upload packaged skill to Pinecone.

        Args:
            package_path: Path to packaged JSON
            api_key: Pinecone API key (or uses PINECONE_API_KEY env var)
            **kwargs:
                index_name: Override index name from JSON
                namespace: Override namespace from JSON
                dimension: Embedding dimension (default: 1536)
                metric: Distance metric (default: "cosine")
                embedding_function: "openai" or "sentence-transformers"
                cloud: Cloud provider (default: "aws")
                region: Cloud region (default: "us-east-1")

        Returns:
            {"success": bool, "index": str, "namespace": str, "count": int}
        """
        import os

        try:
            from pinecone import Pinecone, ServerlessSpec
        except (ImportError, Exception):
            return {
                "success": False,
                "message": "pinecone not installed. Run: pip install 'pinecone>=5.0.0'",
            }

        api_key = api_key or os.getenv("PINECONE_API_KEY")
        if not api_key:
            return {
                "success": False,
                "message": ("PINECONE_API_KEY not set. Set via env var or pass api_key parameter."),
            }

        # Load package
        with open(package_path) as f:
            data = json.load(f)

        index_name = kwargs.get("index_name", data.get("index_name", "skill-docs"))
        namespace = kwargs.get("namespace", data.get("namespace", ""))
        metric = kwargs.get("metric", data.get("metric", "cosine"))
        cloud = kwargs.get("cloud", "aws")
        region = kwargs.get("region", "us-east-1")

        # Auto-detect dimension from embedding model
        embedding_function = kwargs.get("embedding_function", "openai")
        EMBEDDING_DIMENSIONS = {
            "openai": 1536,  # text-embedding-3-small
            "sentence-transformers": 384,  # all-MiniLM-L6-v2
        }
        # Priority: explicit kwarg > model-based auto-detect > JSON file > fallback
        # Note: format_skill_md() hardcodes dimension=1536 in the JSON, so we must
        # give EMBEDDING_DIMENSIONS priority over the file to handle sentence-transformers (384).
        dimension = kwargs.get(
            "dimension",
            EMBEDDING_DIMENSIONS.get(embedding_function, data.get("dimension", 1536)),
        )

        try:
            # Generate embeddings FIRST — before creating the index.
            # This avoids leaving an empty Pinecone index behind when
            # embedding generation fails (e.g. missing API key).
            texts = [vec["metadata"]["text"] for vec in data["vectors"]]

            if embedding_function == "openai":
                embeddings = self._generate_openai_embeddings(texts)
            elif embedding_function == "sentence-transformers":
                embeddings = self._generate_st_embeddings(texts)
            else:
                return {
                    "success": False,
                    "message": f"Unknown embedding_function: {embedding_function}. Use 'openai' or 'sentence-transformers'.",
                }

            pc = Pinecone(api_key=api_key)

            # Create index if it doesn't exist
            existing_indexes = [idx.name for idx in pc.list_indexes()]
            if index_name not in existing_indexes:
                print(
                    f"🔧 Creating Pinecone index: {index_name} (dimension={dimension}, metric={metric})"
                )
                pc.create_index(
                    name=index_name,
                    dimension=dimension,
                    metric=metric,
                    spec=ServerlessSpec(cloud=cloud, region=region),
                )
                print(f"✅ Index '{index_name}' created")
            else:
                print(f"ℹ️  Using existing index: {index_name}")

            index = pc.Index(index_name)

            # Batch upsert (100 per batch — Pinecone recommendation)
            batch_size = 100
            vectors_to_upsert = []
            for i, vec in enumerate(data["vectors"]):
                vectors_to_upsert.append(
                    {
                        "id": vec["id"],
                        "values": embeddings[i],
                        "metadata": vec["metadata"],
                    }
                )

            total = len(vectors_to_upsert)
            print(f"🔄 Upserting {total} vectors to Pinecone...")

            for i in range(0, total, batch_size):
                batch = vectors_to_upsert[i : i + batch_size]
                index.upsert(vectors=batch, namespace=namespace)
                print(f"  ✓ Upserted {min(i + batch_size, total)}/{total}")

            print(f"✅ Uploaded {total} vectors to Pinecone index '{index_name}'")

            return {
                "success": True,
                "message": f"Uploaded {total} vectors to Pinecone index '{index_name}' (namespace: '{namespace}')",
                "url": None,
                "index": index_name,
                "namespace": namespace,
                "count": total,
            }

        except Exception as e:
            return {"success": False, "message": f"Pinecone upload failed: {e}"}

    def validate_api_key(self, _api_key: str) -> bool:
        """Pinecone doesn't need API key for packaging."""
        return False

    def get_env_var_name(self) -> str:
        """Return the expected env var for Pinecone API key."""
        return "PINECONE_API_KEY"

    def supports_enhancement(self) -> bool:
        """Pinecone format doesn't support AI enhancement."""
        return False

    def enhance(self, _skill_dir: Path, _api_key: str) -> bool:
        """Pinecone format doesn't support enhancement."""
        print("❌ Pinecone format does not support enhancement")
        print("   Enhance before packaging:")
        print("   skill-seekers enhance output/skill/ --mode LOCAL")
        print("   skill-seekers package output/skill/ --target pinecone")
        return False
