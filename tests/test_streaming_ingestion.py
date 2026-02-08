#!/usr/bin/env python3
"""
Tests for streaming ingestion functionality.

Validates:
- Chunking strategy (size, overlap)
- Memory-efficient processing
- Progress tracking
- Batch processing
- Resume capability
"""

import pytest
from pathlib import Path
import sys
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skill_seekers.cli.streaming_ingest import StreamingIngester, IngestionProgress


@pytest.fixture
def temp_skill_dir():
    """Create temporary skill directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test_skill"
        skill_dir.mkdir()

        # Create SKILL.md
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("# Test Skill\n\n" + ("This is a test document. " * 200))

        # Create references
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()

        ref1 = refs_dir / "getting_started.md"
        ref1.write_text("# Getting Started\n\n" + ("Step by step guide. " * 100))

        ref2 = refs_dir / "api_reference.md"
        ref2.write_text("# API Reference\n\n" + ("API documentation. " * 150))

        yield skill_dir


def test_chunk_document_single_chunk():
    """Test chunking when document fits in single chunk."""
    ingester = StreamingIngester(chunk_size=1000, chunk_overlap=100)

    content = "Small document"
    metadata = {"source": "test", "file": "test.md", "category": "overview"}

    chunks = list(ingester.chunk_document(content, metadata))

    assert len(chunks) == 1
    chunk_text, chunk_meta = chunks[0]

    assert chunk_text == content
    assert chunk_meta.chunk_index == 0
    assert chunk_meta.total_chunks == 1
    assert chunk_meta.source == "test"


def test_chunk_document_multiple_chunks():
    """Test chunking with multiple chunks."""
    ingester = StreamingIngester(chunk_size=100, chunk_overlap=20)

    content = "A" * 250  # Long content
    metadata = {"source": "test", "file": "test.md", "category": "overview"}

    chunks = list(ingester.chunk_document(content, metadata))

    # Should create multiple chunks
    assert len(chunks) > 1

    # Check overlap
    for i in range(len(chunks) - 1):
        chunk1_text, chunk1_meta = chunks[i]
        chunk2_text, chunk2_meta = chunks[i + 1]

        # Second chunk should start before first ends (overlap)
        assert chunk2_meta.char_start < chunk1_meta.char_end


def test_chunk_document_metadata():
    """Test chunk metadata is correct."""
    ingester = StreamingIngester(chunk_size=100, chunk_overlap=20)

    content = "B" * 250
    metadata = {"source": "test_source", "file": "test_file.md", "category": "test_cat"}

    chunks = list(ingester.chunk_document(content, metadata))

    for i, (chunk_text, chunk_meta) in enumerate(chunks):
        assert chunk_meta.chunk_index == i
        assert chunk_meta.total_chunks == len(chunks)
        assert chunk_meta.source == "test_source"
        assert chunk_meta.file == "test_file.md"
        assert chunk_meta.category == "test_cat"
        assert len(chunk_meta.chunk_id) == 32  # MD5 hash length


def test_stream_skill_directory(temp_skill_dir):
    """Test streaming entire skill directory."""
    ingester = StreamingIngester(chunk_size=500, chunk_overlap=50)

    chunks = list(ingester.stream_skill_directory(temp_skill_dir))

    # Should have chunks from all files
    assert len(chunks) > 0

    # Check progress was tracked
    assert ingester.progress is not None
    assert ingester.progress.total_documents == 3  # SKILL.md + 2 refs
    assert ingester.progress.processed_documents == 3
    assert ingester.progress.total_chunks > 0
    assert ingester.progress.processed_chunks == len(chunks)

    # Check chunk metadata
    sources = set()
    categories = set()

    for chunk_text, chunk_meta in chunks:
        assert chunk_text  # Not empty
        assert chunk_meta["chunk_id"]
        sources.add(chunk_meta["source"])
        categories.add(chunk_meta["category"])

    assert "test_skill" in sources
    assert "overview" in categories


def test_batch_iterator():
    """Test batch processing."""
    ingester = StreamingIngester()

    # Create dummy chunks
    chunks = [(f"chunk_{i}", {"id": i}) for i in range(25)]

    batches = list(ingester.batch_iterator(iter(chunks), batch_size=10))

    # Should have 3 batches (10, 10, 5)
    assert len(batches) == 3
    assert len(batches[0]) == 10
    assert len(batches[1]) == 10
    assert len(batches[2]) == 5


def test_progress_tracking(temp_skill_dir):
    """Test progress tracking during streaming."""
    ingester = StreamingIngester(chunk_size=200, chunk_overlap=20)

    progress_updates = []

    def callback(progress: IngestionProgress):
        progress_updates.append(
            {
                "processed_docs": progress.processed_documents,
                "processed_chunks": progress.processed_chunks,
                "percent": progress.progress_percent,
            }
        )

    list(ingester.stream_skill_directory(temp_skill_dir, callback=callback))

    # Should have received progress updates
    assert len(progress_updates) > 0

    # Progress should increase
    for i in range(len(progress_updates) - 1):
        assert (
            progress_updates[i + 1]["processed_chunks"] >= progress_updates[i]["processed_chunks"]
        )


def test_checkpoint_save_load():
    """Test checkpoint save and load."""
    ingester = StreamingIngester()

    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_path = Path(tmpdir) / "checkpoint.json"

        # Initialize progress
        ingester.progress = IngestionProgress(
            total_documents=10,
            processed_documents=5,
            total_chunks=100,
            processed_chunks=50,
            failed_chunks=2,
            bytes_processed=10000,
            start_time=1234567890.0,
        )

        # Save checkpoint
        state = {"last_processed_file": "test.md", "batch_number": 3}
        ingester.save_checkpoint(checkpoint_path, state)

        assert checkpoint_path.exists()

        # Load checkpoint
        loaded_state = ingester.load_checkpoint(checkpoint_path)

        assert loaded_state == state


def test_format_progress():
    """Test progress formatting."""
    ingester = StreamingIngester()

    ingester.progress = IngestionProgress(
        total_documents=10,
        processed_documents=5,
        total_chunks=100,
        processed_chunks=50,
        failed_chunks=0,
        bytes_processed=10000,
        start_time=0.0,
    )

    progress_str = ingester.format_progress()

    assert "50.0%" in progress_str
    assert "50/100" in progress_str
    assert "5/10" in progress_str


def test_empty_directory():
    """Test handling empty directory."""
    ingester = StreamingIngester()

    with tempfile.TemporaryDirectory() as tmpdir:
        empty_dir = Path(tmpdir) / "empty"
        empty_dir.mkdir()

        chunks = list(ingester.stream_skill_directory(empty_dir))

        assert len(chunks) == 0
        assert ingester.progress.total_documents == 0


def test_chunk_size_validation():
    """Test different chunk sizes."""
    content = "X" * 1000

    # Small chunks
    ingester_small = StreamingIngester(chunk_size=100, chunk_overlap=10)
    chunks_small = list(
        ingester_small.chunk_document(
            content, {"source": "test", "file": "test.md", "category": "test"}
        )
    )

    # Large chunks
    ingester_large = StreamingIngester(chunk_size=500, chunk_overlap=50)
    chunks_large = list(
        ingester_large.chunk_document(
            content, {"source": "test", "file": "test.md", "category": "test"}
        )
    )

    # Smaller chunk size should create more chunks
    assert len(chunks_small) > len(chunks_large)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
