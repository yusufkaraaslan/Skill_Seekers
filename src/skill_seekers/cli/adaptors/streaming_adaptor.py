#!/usr/bin/env python3
"""
Streaming Adaptor Mixin

Provides streaming ingestion capabilities for platform adaptors.
Enables memory-efficient processing of large documentation sets.
"""

import json
from pathlib import Path
from collections.abc import Callable
from typing import Any
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from streaming_ingest import StreamingIngester, IngestionProgress


class StreamingAdaptorMixin:
    """
    Mixin class to add streaming capabilities to platform adaptors.

    Provides:
    - Chunked document processing
    - Memory-efficient streaming
    - Progress tracking
    - Batch processing
    - Resume capability
    """

    def package_streaming(
        self,
        skill_dir: Path,
        output_path: Path,
        chunk_size: int = 4000,
        chunk_overlap: int = 200,
        batch_size: int = 100,
        progress_callback: Callable | None = None,
    ) -> Path:
        """
        Package skill using streaming ingestion.

        Memory-efficient alternative to standard package() method.
        Suitable for large documentation sets (>100 documents or >10MB).

        Args:
            skill_dir: Path to skill directory
            output_path: Output path/filename
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks (for context)
            batch_size: Number of chunks per batch
            progress_callback: Optional callback(progress: IngestionProgress)

        Returns:
            Path to created package file
        """
        skill_dir = Path(skill_dir)
        output_path = Path(output_path)

        # Initialize streaming ingester
        ingester = StreamingIngester(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, batch_size=batch_size
        )

        print(f"\n📊 Streaming ingestion starting...")
        print(f"   Chunk size: {chunk_size} chars")
        print(f"   Overlap: {chunk_overlap} chars")
        print(f"   Batch size: {batch_size} chunks")

        # Progress tracking
        last_update = 0

        def on_progress(progress: IngestionProgress):
            nonlocal last_update
            # Update every 10 chunks
            if progress.processed_chunks - last_update >= 10:
                print(
                    f"   {progress.progress_percent:.1f}% - "
                    f"{progress.processed_chunks}/{progress.total_chunks} chunks "
                    f"({progress.chunks_per_second:.1f} chunks/sec)"
                )
                last_update = progress.processed_chunks

            if progress_callback:
                progress_callback(progress)

        # Stream and collect chunks
        chunks = ingester.stream_skill_directory(skill_dir, callback=on_progress)
        all_chunks = list(chunks)

        print(f"\n✅ Streaming ingestion complete!")
        print(f"   Total chunks: {len(all_chunks)}")
        print(f"   Total bytes: {ingester.progress.bytes_processed:,}")
        print(f"   Time: {ingester.progress.elapsed_time:.1f}s")
        print(f"   Rate: {ingester.progress.chunks_per_second:.1f} chunks/sec")

        # Convert chunks to platform format
        print(f"\n📦 Converting to {self.PLATFORM_NAME} format...")
        package_data = self._convert_chunks_to_platform_format(all_chunks, skill_dir.name)

        # Determine output filename
        if output_path.is_dir() or str(output_path).endswith("/"):
            output_path = output_path / f"{skill_dir.name}-{self.PLATFORM}-streaming.json"
        elif not str(output_path).endswith(".json"):
            output_str = str(output_path).replace(".zip", ".json").replace(".tar.gz", ".json")
            if f"-{self.PLATFORM}" not in output_str:
                output_str = output_str.replace(".json", f"-{self.PLATFORM}.json")
            output_path = Path(output_str)

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(package_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        print(f"✅ Package created: {output_path}")
        print(f"   Size: {output_path.stat().st_size:,} bytes")

        return output_path

    def _convert_chunks_to_platform_format(
        self, chunks: list[tuple[str, dict]], skill_name: str
    ) -> dict:
        """
        Convert chunks to platform-specific format.

        Subclasses should override this method to customize format.

        Args:
            chunks: List of (chunk_text, chunk_metadata) tuples
            skill_name: Name of the skill

        Returns:
            Platform-specific data structure
        """
        # Default implementation: generic format
        documents = []
        metadatas = []
        ids = []

        for chunk_text, chunk_meta in chunks:
            documents.append(chunk_text)
            metadatas.append(chunk_meta)
            ids.append(chunk_meta["chunk_id"])

        return {
            "skill_name": skill_name,
            "documents": documents,
            "metadatas": metadatas,
            "ids": ids,
            "total_chunks": len(chunks),
            "streaming": True,
        }

    def estimate_chunks(
        self, skill_dir: Path, chunk_size: int = 4000, chunk_overlap: int = 200
    ) -> dict[str, Any]:
        """
        Estimate chunking for a skill directory.

        Useful for planning and validation before processing.

        Args:
            skill_dir: Path to skill directory
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks

        Returns:
            Estimation statistics
        """
        skill_dir = Path(skill_dir)
        StreamingIngester(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # Count files and estimate chunks
        total_docs = 0
        total_chars = 0
        estimated_chunks = 0
        file_stats = []

        # SKILL.md
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            char_count = len(content)
            chunk_count = max(1, (char_count - chunk_overlap) // (chunk_size - chunk_overlap) + 1)

            total_docs += 1
            total_chars += char_count
            estimated_chunks += chunk_count

            file_stats.append(
                {"file": "SKILL.md", "chars": char_count, "estimated_chunks": chunk_count}
            )

        # Reference files
        refs_dir = skill_dir / "references"
        if refs_dir.exists():
            for ref_file in sorted(refs_dir.glob("*.md")):
                if ref_file.is_file() and not ref_file.name.startswith("."):
                    content = ref_file.read_text(encoding="utf-8")
                    char_count = len(content)
                    chunk_count = max(
                        1, (char_count - chunk_overlap) // (chunk_size - chunk_overlap) + 1
                    )

                    total_docs += 1
                    total_chars += char_count
                    estimated_chunks += chunk_count

                    file_stats.append(
                        {
                            "file": ref_file.name,
                            "chars": char_count,
                            "estimated_chunks": chunk_count,
                        }
                    )

        return {
            "skill_name": skill_dir.name,
            "total_documents": total_docs,
            "total_characters": total_chars,
            "estimated_chunks": estimated_chunks,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "file_stats": file_stats,
            "estimated_memory_mb": (total_chars * 2) / (1024 * 1024),  # UTF-8 estimate
            "recommended_streaming": total_chars > 1_000_000 or total_docs > 100,
        }


# Example: Extend existing adaptors with streaming
class StreamingLangChainAdaptor(StreamingAdaptorMixin):
    """LangChain adaptor with streaming support."""

    PLATFORM = "langchain"
    PLATFORM_NAME = "LangChain (Streaming)"

    def _convert_chunks_to_platform_format(self, chunks, skill_name):
        """Convert chunks to LangChain Document format."""
        documents = []

        for chunk_text, chunk_meta in chunks:
            documents.append(
                {
                    "page_content": chunk_text,
                    "metadata": {
                        "source": chunk_meta["source"],
                        "category": chunk_meta["category"],
                        "file": chunk_meta["file"],
                        "chunk_id": chunk_meta["chunk_id"],
                        "chunk_index": chunk_meta["chunk_index"],
                        "total_chunks": chunk_meta["total_chunks"],
                        "type": chunk_meta.get("type", "documentation"),
                        "version": chunk_meta.get("version", "1.0.0"),
                    },
                }
            )

        return {
            "documents": documents,
            "total_chunks": len(chunks),
            "streaming": True,
            "format": "LangChain Document",
        }


class StreamingChromaAdaptor(StreamingAdaptorMixin):
    """Chroma adaptor with streaming support."""

    PLATFORM = "chroma"
    PLATFORM_NAME = "Chroma (Streaming)"

    def _convert_chunks_to_platform_format(self, chunks, skill_name):
        """Convert chunks to Chroma format."""
        documents = []
        metadatas = []
        ids = []

        for chunk_text, chunk_meta in chunks:
            documents.append(chunk_text)
            metadatas.append(
                {
                    "source": chunk_meta["source"],
                    "category": chunk_meta["category"],
                    "file": chunk_meta["file"],
                    "chunk_index": chunk_meta["chunk_index"],
                    "total_chunks": chunk_meta["total_chunks"],
                    "type": chunk_meta.get("type", "documentation"),
                }
            )
            ids.append(chunk_meta["chunk_id"])

        return {
            "documents": documents,
            "metadatas": metadatas,
            "ids": ids,
            "collection_name": skill_name.replace("_", "-"),
            "total_chunks": len(chunks),
            "streaming": True,
        }


def demo_streaming():
    """Demonstrate streaming ingestion."""
    from pathlib import Path

    # Example with LangChain
    adaptor = StreamingLangChainAdaptor()

    # Estimate first
    print("=" * 60)
    print("ESTIMATION")
    print("=" * 60)

    skill_dir = Path("output/ansible")
    estimate = adaptor.estimate_chunks(skill_dir, chunk_size=2000, chunk_overlap=100)

    print(f"\nSkill: {estimate['skill_name']}")
    print(f"Documents: {estimate['total_documents']}")
    print(f"Characters: {estimate['total_characters']:,}")
    print(f"Estimated chunks: {estimate['estimated_chunks']}")
    print(f"Estimated memory: {estimate['estimated_memory_mb']:.2f} MB")
    print(f"Streaming recommended: {estimate['recommended_streaming']}")

    print("\nFile breakdown:")
    for stat in estimate["file_stats"]:
        print(f"  {stat['file']}: {stat['chars']:,} chars → {stat['estimated_chunks']} chunks")

    # Package with streaming
    print("\n" + "=" * 60)
    print("STREAMING INGESTION")
    print("=" * 60)

    output = adaptor.package_streaming(
        skill_dir, Path("output"), chunk_size=2000, chunk_overlap=100, batch_size=50
    )

    print(f"\n✅ Complete! Output: {output}")


if __name__ == "__main__":
    demo_streaming()
