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
        self, skill_dir: Path, metadata: SkillMetadata, enable_chunking: bool = False, **kwargs
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
                    chunk_max_tokens=kwargs.get("chunk_max_tokens", 512),
                    preserve_code_blocks=kwargs.get("preserve_code_blocks", True),
                    source_file=ref_file.name,
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
        preserve_code_blocks: bool = True,
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
            preserve_code_blocks=preserve_code_blocks,
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

    def upload(self, package_path: Path, api_key: str = None, **kwargs) -> dict[str, Any]:
        """
        Upload packaged skill to ChromaDB.

        Args:
            package_path: Path to packaged JSON
            api_key: Not used for Chroma (uses URL instead)
            **kwargs:
                chroma_url: ChromaDB URL (default: http://localhost:8000)
                collection_name: Override collection name
                distance_function: "cosine", "l2", or "ip" (default: "cosine")
                embedding_function: "openai", "sentence-transformers", or None
                openai_api_key: For OpenAI embeddings
                persist_directory: Local directory for persistent storage

        Returns:
            {"success": bool, "message": str, "collection": str, "count": int}
        """
        try:
            import chromadb
        except ImportError:
            return {
                "success": False,
                "message": "chromadb not installed. Run: pip install chromadb",
            }

        # Load package
        with open(package_path) as f:
            data = json.load(f)

        # Determine client type and configuration
        persist_directory = kwargs.get("persist_directory")
        chroma_url = kwargs.get("chroma_url")

        try:
            if persist_directory:
                # Local persistent storage
                print(f"📁 Using persistent storage: {persist_directory}")
                client = chromadb.PersistentClient(path=persist_directory)
            elif chroma_url:
                # Remote HTTP client
                print(f"🌐 Connecting to ChromaDB at: {chroma_url}")
                # Parse URL
                if "://" in chroma_url:
                    parts = chroma_url.split("://")
                    parts[0]
                    host_port = parts[1]
                else:
                    host_port = chroma_url

                if ":" in host_port:
                    host, port = host_port.rsplit(":", 1)
                    port = int(port)
                else:
                    host = host_port
                    port = 8000

                client = chromadb.HttpClient(host=host, port=port)
            else:
                # Default: local persistent client
                print("📁 Using default persistent storage: ./chroma_db")
                client = chromadb.PersistentClient(path="./chroma_db")

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to connect to ChromaDB: {e}\n\nTry:\n  pip install chromadb\n  chroma run  # Start local server",
            }

        # Get or create collection
        collection_name = kwargs.get("collection_name", data.get("collection_name", "skill_docs"))
        distance_function = kwargs.get("distance_function", "cosine")

        try:
            # Try to get existing collection
            collection = client.get_collection(name=collection_name)
            print(f"ℹ️  Using existing collection: {collection_name}")
        except Exception:
            try:
                # Create new collection
                metadata = {"hnsw:space": distance_function}
                collection = client.create_collection(name=collection_name, metadata=metadata)
                print(f"✅ Created collection: {collection_name} (distance: {distance_function})")
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Failed to create collection '{collection_name}': {e}",
                }

        # Handle embeddings
        embedding_function = kwargs.get("embedding_function")

        try:
            if embedding_function == "openai":
                # Generate embeddings with OpenAI
                print("🔄 Generating OpenAI embeddings...")
                embeddings = self._generate_openai_embeddings(
                    data["documents"], api_key=kwargs.get("openai_api_key")
                )
                collection.add(
                    documents=data["documents"],
                    metadatas=data["metadatas"],
                    ids=data["ids"],
                    embeddings=embeddings,
                )
            elif embedding_function == "sentence-transformers":
                # Use sentence-transformers
                print("🔄 Generating sentence-transformer embeddings...")
                try:
                    from chromadb.utils import embedding_functions

                    ef = embedding_functions.SentenceTransformerEmbeddingFunction()
                    embeddings = [ef([doc])[0] for doc in data["documents"]]
                    collection.add(
                        documents=data["documents"],
                        metadatas=data["metadatas"],
                        ids=data["ids"],
                        embeddings=embeddings,
                    )
                except ImportError:
                    return {
                        "success": False,
                        "message": "sentence-transformers not installed. Run: pip install sentence-transformers",
                    }
            else:
                # No embeddings - Chroma will auto-generate
                print("🔄 Using Chroma's default embedding function...")
                collection.add(
                    documents=data["documents"], metadatas=data["metadatas"], ids=data["ids"]
                )

            count = len(data["documents"])
            print(f"✅ Uploaded {count} documents to ChromaDB")
            print(f"📊 Collection '{collection_name}' now has {collection.count()} total documents")

            return {
                "success": True,
                "message": f"Uploaded {count} documents to ChromaDB collection '{collection_name}'",
                "collection": collection_name,
                "count": count,
                "url": f"{chroma_url}/collections/{collection_name}" if chroma_url else None,
            }

        except Exception as e:
            return {"success": False, "message": f"Upload failed: {e}"}

    def _generate_openai_embeddings(
        self, documents: list[str], api_key: str = None
    ) -> list[list[float]]:
        """
        Generate embeddings using OpenAI API.

        Args:
            documents: List of document texts
            api_key: OpenAI API key (or uses OPENAI_API_KEY env var)

        Returns:
            List of embedding vectors
        """
        import os

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai") from None

        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set. Set via env var or --openai-api-key")

        client = OpenAI(api_key=api_key)

        # Batch process (OpenAI allows up to 2048 inputs)
        embeddings = []
        batch_size = 100

        print(f"  Generating embeddings for {len(documents)} documents...")

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            try:
                response = client.embeddings.create(
                    input=batch,
                    model="text-embedding-3-small",  # Cheapest, fastest
                )
                embeddings.extend([item.embedding for item in response.data])
                print(f"  ✓ Processed {min(i + batch_size, len(documents))}/{len(documents)}")
            except Exception as e:
                raise Exception(f"OpenAI embedding generation failed: {e}") from e

        return embeddings

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
