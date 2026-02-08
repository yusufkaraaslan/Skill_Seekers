#!/usr/bin/env python3
"""
Streaming Ingestion for Large Documentation Sets

Provides memory-efficient processing and batch upload capabilities for large
skill documentation. Handles chunking, progress tracking, and resume functionality.
"""

import json
import hashlib
from pathlib import Path
from collections.abc import Callable, Iterator
from dataclasses import dataclass
import time


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""

    chunk_id: str
    source: str
    category: str
    file: str
    chunk_index: int
    total_chunks: int
    char_start: int
    char_end: int


@dataclass
class IngestionProgress:
    """Progress tracking for streaming ingestion."""

    total_documents: int
    processed_documents: int
    total_chunks: int
    processed_chunks: int
    failed_chunks: int
    bytes_processed: int
    start_time: float

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.total_chunks == 0:
            return 0.0
        return (self.processed_chunks / self.total_chunks) * 100

    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        return time.time() - self.start_time

    @property
    def chunks_per_second(self) -> float:
        """Calculate processing rate."""
        elapsed = self.elapsed_time
        if elapsed == 0:
            return 0.0
        return self.processed_chunks / elapsed

    @property
    def eta_seconds(self) -> float:
        """Estimate time remaining in seconds."""
        rate = self.chunks_per_second
        if rate == 0:
            return 0.0
        remaining = self.total_chunks - self.processed_chunks
        return remaining / rate


class StreamingIngester:
    """
    Streaming ingestion manager for large documentation sets.

    Provides memory-efficient processing with chunking, progress tracking,
    and resume capabilities.
    """

    def __init__(
        self,
        chunk_size: int = 4000,
        chunk_overlap: int = 200,
        batch_size: int = 100,
        max_memory_mb: int = 500,
    ):
        """
        Initialize streaming ingester.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks (for context)
            batch_size: Number of chunks per batch
            max_memory_mb: Maximum memory usage in MB
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.batch_size = batch_size
        self.max_memory_mb = max_memory_mb
        self.progress = None

    def chunk_document(
        self,
        content: str,
        metadata: dict,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> Iterator[tuple[str, ChunkMetadata]]:
        """
        Split document into overlapping chunks.

        Args:
            content: Document content
            metadata: Document metadata
            chunk_size: Override default chunk size
            chunk_overlap: Override default overlap

        Yields:
            Tuple of (chunk_text, chunk_metadata)
        """
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap

        if len(content) <= chunk_size:
            # Document fits in single chunk
            chunk_meta = ChunkMetadata(
                chunk_id=self._generate_chunk_id(content, metadata, 0),
                source=metadata.get("source", ""),
                category=metadata.get("category", ""),
                file=metadata.get("file", ""),
                chunk_index=0,
                total_chunks=1,
                char_start=0,
                char_end=len(content),
            )
            yield content, chunk_meta
            return

        # Calculate total chunks
        effective_chunk_size = chunk_size - chunk_overlap
        total_chunks = (len(content) - chunk_overlap) // effective_chunk_size + 1

        # Generate chunks with overlap
        for i in range(total_chunks):
            start = i * effective_chunk_size
            end = start + chunk_size

            # Ensure we don't go past the end
            if end > len(content):
                end = len(content)

            chunk_text = content[start:end]

            # Skip empty chunks
            if not chunk_text.strip():
                continue

            chunk_meta = ChunkMetadata(
                chunk_id=self._generate_chunk_id(chunk_text, metadata, i),
                source=metadata.get("source", ""),
                category=metadata.get("category", ""),
                file=metadata.get("file", ""),
                chunk_index=i,
                total_chunks=total_chunks,
                char_start=start,
                char_end=end,
            )

            yield chunk_text, chunk_meta

    def _generate_chunk_id(self, content: str, metadata: dict, chunk_index: int) -> str:
        """Generate deterministic chunk ID."""
        id_string = (
            f"{metadata.get('source', '')}-{metadata.get('file', '')}-{chunk_index}-{content[:50]}"
        )
        return hashlib.md5(id_string.encode()).hexdigest()

    def stream_skill_directory(
        self, skill_dir: Path, callback: Callable | None = None
    ) -> Iterator[tuple[str, dict]]:
        """
        Stream all documents from skill directory.

        Args:
            skill_dir: Path to skill directory
            callback: Optional progress callback(progress: IngestionProgress)

        Yields:
            Tuple of (chunk_text, chunk_metadata_dict)
        """
        skill_dir = Path(skill_dir)

        # Count total documents first
        doc_files = []

        # SKILL.md
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            doc_files.append(("SKILL.md", "overview", skill_md))

        # Reference files
        refs_dir = skill_dir / "references"
        if refs_dir.exists():
            for ref_file in sorted(refs_dir.glob("*.md")):
                if ref_file.is_file() and not ref_file.name.startswith("."):
                    category = ref_file.stem.replace("_", " ").lower()
                    doc_files.append((ref_file.name, category, ref_file))

        # Initialize progress tracking
        self.progress = IngestionProgress(
            total_documents=len(doc_files),
            processed_documents=0,
            total_chunks=0,  # Will be updated as we chunk
            processed_chunks=0,
            failed_chunks=0,
            bytes_processed=0,
            start_time=time.time(),
        )

        # Process each document
        for filename, category, filepath in doc_files:
            try:
                content = filepath.read_text(encoding="utf-8")

                if not content.strip():
                    self.progress.processed_documents += 1
                    continue

                metadata = {
                    "source": skill_dir.name,
                    "category": category,
                    "file": filename,
                    "type": "documentation" if filename == "SKILL.md" else "reference",
                    "version": "1.0.0",
                }

                # Chunk document and yield chunks
                for chunk_count, (chunk_text, chunk_meta) in enumerate(
                    self.chunk_document(content, metadata), start=1
                ):
                    self.progress.total_chunks += 1

                    # Convert chunk metadata to dict
                    chunk_dict = {
                        "content": chunk_text,
                        "chunk_id": chunk_meta.chunk_id,
                        "source": chunk_meta.source,
                        "category": chunk_meta.category,
                        "file": chunk_meta.file,
                        "chunk_index": chunk_meta.chunk_index,
                        "total_chunks": chunk_meta.total_chunks,
                        "char_start": chunk_meta.char_start,
                        "char_end": chunk_meta.char_end,
                    }

                    yield chunk_text, chunk_dict

                    self.progress.processed_chunks += 1
                    self.progress.bytes_processed += len(chunk_text.encode("utf-8"))

                    # Callback for progress updates
                    if callback:
                        callback(self.progress)

                self.progress.processed_documents += 1

            except Exception as e:
                print(f"⚠️  Warning: Failed to process {filename}: {e}")
                self.progress.failed_chunks += 1
                continue

    def batch_iterator(
        self, chunks: Iterator[tuple[str, dict]], batch_size: int | None = None
    ) -> Iterator[list[tuple[str, dict]]]:
        """
        Group chunks into batches for efficient processing.

        Args:
            chunks: Iterator of (chunk_text, chunk_metadata) tuples
            batch_size: Override default batch size

        Yields:
            List of chunks (batch)
        """
        batch_size = batch_size or self.batch_size
        batch = []

        for chunk in chunks:
            batch.append(chunk)

            if len(batch) >= batch_size:
                yield batch
                batch = []

        # Yield remaining chunks
        if batch:
            yield batch

    def save_checkpoint(self, checkpoint_path: Path, state: dict) -> None:
        """
        Save ingestion checkpoint for resume capability.

        Args:
            checkpoint_path: Path to checkpoint file
            state: State dictionary to save
        """
        checkpoint_path = Path(checkpoint_path)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint_data = {
            "timestamp": time.time(),
            "progress": {
                "total_documents": self.progress.total_documents,
                "processed_documents": self.progress.processed_documents,
                "total_chunks": self.progress.total_chunks,
                "processed_chunks": self.progress.processed_chunks,
                "failed_chunks": self.progress.failed_chunks,
                "bytes_processed": self.progress.bytes_processed,
            },
            "state": state,
        }

        checkpoint_path.write_text(json.dumps(checkpoint_data, indent=2))

    def load_checkpoint(self, checkpoint_path: Path) -> dict | None:
        """
        Load ingestion checkpoint for resume.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            State dictionary or None if not found
        """
        checkpoint_path = Path(checkpoint_path)

        if not checkpoint_path.exists():
            return None

        try:
            checkpoint_data = json.loads(checkpoint_path.read_text())
            return checkpoint_data.get("state")
        except Exception as e:
            print(f"⚠️  Warning: Failed to load checkpoint: {e}")
            return None

    def format_progress(self) -> str:
        """
        Format progress as human-readable string.

        Returns:
            Progress string
        """
        if not self.progress:
            return "No progress data"

        p = self.progress

        lines = [
            f"📊 Progress: {p.progress_percent:.1f}% complete",
            f"   Documents: {p.processed_documents}/{p.total_documents}",
            f"   Chunks: {p.processed_chunks}/{p.total_chunks}",
            f"   Rate: {p.chunks_per_second:.1f} chunks/sec",
            f"   Elapsed: {p.elapsed_time:.1f}s",
        ]

        if p.eta_seconds > 0:
            lines.append(f"   ETA: {p.eta_seconds:.1f}s")

        if p.failed_chunks > 0:
            lines.append(f"   ⚠️  Failed: {p.failed_chunks} chunks")

        return "\n".join(lines)


def main():
    """CLI entry point for streaming ingestion."""
    import argparse

    parser = argparse.ArgumentParser(description="Stream and chunk skill documents")
    parser.add_argument("input", help="Input file or directory path")
    parser.add_argument("--chunk-size", type=int, default=4000, help="Chunk size in characters")
    parser.add_argument(
        "--chunk-overlap", type=int, default=200, help="Chunk overlap in characters"
    )
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--checkpoint", help="Checkpoint file path")
    args = parser.parse_args()

    # Initialize ingester
    ingester = StreamingIngester(
        chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap, batch_size=args.batch_size
    )

    # Progress callback
    def on_progress(progress: IngestionProgress):
        if progress.processed_chunks % 10 == 0:
            print(
                f"Progress: {progress.progress_percent:.1f}% - "
                f"{progress.processed_chunks}/{progress.total_chunks} chunks"
            )

    # Stream input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: Path not found: {input_path}")
        return 1

    if input_path.is_dir():
        chunks = ingester.stream_skill_directory(input_path, callback=on_progress)
    else:
        # Stream single file
        content = input_path.read_text(encoding="utf-8")
        metadata = {"source": input_path.stem, "file": input_path.name}
        file_chunks = ingester.chunk_document(content, metadata)
        # Convert to generator format matching stream_skill_directory
        chunks = (
            (
                text,
                {
                    "content": text,
                    "chunk_id": meta.chunk_id,
                    "source": meta.source,
                    "category": meta.category,
                    "file": meta.file,
                    "chunk_index": meta.chunk_index,
                    "total_chunks": meta.total_chunks,
                    "char_start": meta.char_start,
                    "char_end": meta.char_end,
                },
            )
            for text, meta in file_chunks
        )

    # Process in batches
    all_chunks = []
    for batch in ingester.batch_iterator(chunks, batch_size=args.batch_size):
        print(f"\nProcessing batch of {len(batch)} chunks...")
        all_chunks.extend(batch)

        # Save checkpoint if specified
        if args.checkpoint:
            ingester.save_checkpoint(
                Path(args.checkpoint), {"processed_batches": len(all_chunks) // args.batch_size}
            )

    # Final progress
    print("\n" + ingester.format_progress())
    print(f"\n✅ Processed {len(all_chunks)} total chunks")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
