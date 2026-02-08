#!/usr/bin/env python3
"""
Tests for chunking integration in package command and RAG adaptors.

Tests that RAGChunker is properly integrated into:
- package_skill.py command
- base_adaptor._maybe_chunk_content()
- All 7 RAG adaptors (langchain, llama-index, haystack, weaviate, chroma, faiss, qdrant)
"""

import pytest
import json
from pathlib import Path
from skill_seekers.cli.adaptors import get_adaptor


def create_test_skill(tmp_path: Path, large_doc: bool = False) -> Path:
    """
    Create a test skill directory for chunking tests.

    Args:
        tmp_path: Temporary directory
        large_doc: If True, create a large document (>512 tokens)

    Returns:
        Path to skill directory
    """
    skill_dir = tmp_path / "test_skill"
    skill_dir.mkdir()

    # Create SKILL.md
    if large_doc:
        # Create ~10KB document (>512 tokens estimate: ~2500 tokens)
        content = "# Test Skill\n\n" + ("Lorem ipsum dolor sit amet. " * 2000)
    else:
        # Small document (<512 tokens)
        content = "# Test Skill\n\nThis is a small test document."

    (skill_dir / "SKILL.md").write_text(content)

    # Create references directory
    refs_dir = skill_dir / "references"
    refs_dir.mkdir()

    # Create a reference file
    if large_doc:
        ref_content = "# API Reference\n\n" + ("Function details here. " * 1000)
    else:
        ref_content = "# API Reference\n\nSome API documentation."

    (refs_dir / "api_reference.md").write_text(ref_content)

    return skill_dir


class TestChunkingDisabledByDefault:
    """Test that chunking is disabled by default."""

    def test_langchain_no_chunking_default(self, tmp_path):
        """Test that LangChain doesn't chunk by default."""
        skill_dir = create_test_skill(tmp_path, large_doc=True)

        adaptor = get_adaptor("langchain")
        package_path = adaptor.package(skill_dir, tmp_path)

        with open(package_path) as f:
            data = json.load(f)

        # Should be exactly 2 documents (SKILL.md + 1 reference)
        assert len(data) == 2, f"Expected 2 docs, got {len(data)}"

        # No chunking metadata
        for doc in data:
            assert "is_chunked" not in doc["metadata"]
            assert "chunk_index" not in doc["metadata"]


class TestChunkingEnabled:
    """Test that chunking works when enabled."""

    def test_langchain_chunking_enabled(self, tmp_path):
        """Test that LangChain chunks large documents when enabled."""
        skill_dir = create_test_skill(tmp_path, large_doc=True)

        adaptor = get_adaptor("langchain")
        package_path = adaptor.package(
            skill_dir, tmp_path, enable_chunking=True, chunk_max_tokens=512
        )

        with open(package_path) as f:
            data = json.load(f)

        # Should have multiple chunks (more than 2 docs)
        assert len(data) > 2, f"Large doc should be chunked, got {len(data)} docs"

        # Check for chunking metadata
        chunked_docs = [doc for doc in data if doc["metadata"].get("is_chunked")]
        assert len(chunked_docs) > 0, "Should have chunked documents"

        # Verify chunk metadata structure
        for doc in chunked_docs:
            assert "chunk_index" in doc["metadata"]
            assert "total_chunks" in doc["metadata"]
            assert "chunk_id" in doc["metadata"]

    def test_chunking_preserves_small_docs(self, tmp_path):
        """Test that small documents are not chunked."""
        skill_dir = create_test_skill(tmp_path, large_doc=False)

        adaptor = get_adaptor("langchain")
        package_path = adaptor.package(
            skill_dir, tmp_path, enable_chunking=True, chunk_max_tokens=512
        )

        with open(package_path) as f:
            data = json.load(f)

        # Small docs should not be chunked
        assert len(data) == 2, "Small docs should not be chunked"

        for doc in data:
            assert "is_chunked" not in doc["metadata"]


class TestCodeBlockPreservation:
    """Test that code blocks are preserved during chunking."""

    def test_preserve_code_blocks(self, tmp_path):
        """Test that code blocks are not split during chunking."""
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()

        # Create document with code block
        content = """# Test

Some intro text that needs to be here for context.

```python
def example_function():
    # This code block should not be split
    x = 1
    y = 2
    z = 3
    return x + y + z
```

More content after code block.
""" + ("Lorem ipsum dolor sit amet. " * 1000)  # Make it large enough to force chunking

        (skill_dir / "SKILL.md").write_text(content)

        # Create references dir (required)
        (skill_dir / "references").mkdir()

        adaptor = get_adaptor("langchain")
        package_path = adaptor.package(
            skill_dir,
            tmp_path,
            enable_chunking=True,
            chunk_max_tokens=200,  # Small chunks to force splitting
            preserve_code_blocks=True,
        )

        with open(package_path) as f:
            data = json.load(f)

        # Find chunks with code block
        code_chunks = [doc for doc in data if "```python" in doc["page_content"]]

        # Code block should be in at least one chunk
        assert len(code_chunks) >= 1, "Code block should be preserved"

        # Code block should be complete (opening and closing backticks)
        for chunk in code_chunks:
            content = chunk["page_content"]
            if "```python" in content:
                # Should also have closing backticks
                assert content.count("```") >= 2, "Code block should be complete"


class TestAutoChunkingForRAGPlatforms:
    """Test that chunking is auto-enabled for RAG platforms."""

    @pytest.mark.parametrize(
        "platform",
        [
            "langchain",
            # Add others after they're updated:
            # 'llama-index', 'haystack', 'weaviate', 'chroma', 'faiss', 'qdrant'
        ],
    )
    def test_rag_platforms_auto_chunk(self, platform, tmp_path):
        """Test that RAG platforms auto-enable chunking."""
        skill_dir = create_test_skill(tmp_path, large_doc=True)

        # Import package_skill function
        from skill_seekers.cli.package_skill import package_skill

        # Package with RAG platform (should auto-enable chunking)
        success, package_path = package_skill(
            skill_dir=skill_dir,
            open_folder_after=False,
            skip_quality_check=True,
            target=platform,
            enable_chunking=False,  # Explicitly disabled, but should be auto-enabled
        )

        assert success, f"Packaging failed for {platform}"
        assert package_path.exists(), f"Package not created for {platform}"

        # Verify chunking occurred
        with open(package_path) as f:
            data = json.load(f)

        # Should have multiple documents/chunks
        if isinstance(data, list):
            assert len(data) > 2, f"{platform}: Should auto-chunk large docs"
        elif isinstance(data, dict) and "documents" in data:
            assert len(data["documents"]) > 2, f"{platform}: Should auto-chunk large docs"


class TestBaseAdaptorChunkingHelper:
    """Test the base adaptor's _maybe_chunk_content method."""

    def test_maybe_chunk_content_disabled(self):
        """Test that _maybe_chunk_content returns single chunk when disabled."""
        from skill_seekers.cli.adaptors.langchain import LangChainAdaptor

        adaptor = LangChainAdaptor()

        content = "Test content " * 1000  # Large content
        metadata = {"source": "test"}

        chunks = adaptor._maybe_chunk_content(content, metadata, enable_chunking=False)

        # Should return single chunk
        assert len(chunks) == 1
        assert chunks[0][0] == content
        assert chunks[0][1] == metadata

    def test_maybe_chunk_content_small_doc(self):
        """Test that small docs are not chunked even when enabled."""
        from skill_seekers.cli.adaptors.langchain import LangChainAdaptor

        adaptor = LangChainAdaptor()

        content = "Small test content"  # <512 tokens
        metadata = {"source": "test"}

        chunks = adaptor._maybe_chunk_content(
            content, metadata, enable_chunking=True, chunk_max_tokens=512
        )

        # Should return single chunk
        assert len(chunks) == 1

    def test_maybe_chunk_content_large_doc(self):
        """Test that large docs are chunked when enabled."""
        from skill_seekers.cli.adaptors.langchain import LangChainAdaptor

        adaptor = LangChainAdaptor()

        content = "Lorem ipsum dolor sit amet. " * 2000  # >512 tokens
        metadata = {"source": "test", "file": "test.md"}

        chunks = adaptor._maybe_chunk_content(
            content,
            metadata,
            enable_chunking=True,
            chunk_max_tokens=512,
            preserve_code_blocks=True,
            source_file="test.md",
        )

        # Should return multiple chunks
        assert len(chunks) > 1, f"Large doc should be chunked, got {len(chunks)} chunks"

        # Verify chunk metadata
        for chunk_text, chunk_meta in chunks:
            assert isinstance(chunk_text, str)
            assert isinstance(chunk_meta, dict)
            assert chunk_meta["is_chunked"]
            assert "chunk_index" in chunk_meta
            assert "chunk_id" in chunk_meta
            # Original metadata preserved
            assert chunk_meta["source"] == "test"
            assert chunk_meta["file"] == "test.md"


class TestChunkingCLIIntegration:
    """Test chunking via CLI arguments."""

    def test_chunk_flag(self, tmp_path):
        """Test --chunk flag enables chunking."""
        from skill_seekers.cli.package_skill import package_skill

        skill_dir = create_test_skill(tmp_path, large_doc=True)

        success, package_path = package_skill(
            skill_dir=skill_dir,
            open_folder_after=False,
            skip_quality_check=True,
            target="langchain",
            enable_chunking=True,  # --chunk flag
            chunk_max_tokens=512,
            preserve_code_blocks=True,
        )

        assert success
        assert package_path.exists()

        with open(package_path) as f:
            data = json.load(f)

        # Should have chunked documents
        assert len(data) > 2

    def test_chunk_tokens_parameter(self, tmp_path):
        """Test --chunk-tokens parameter controls chunk size."""
        from skill_seekers.cli.package_skill import package_skill

        skill_dir = create_test_skill(tmp_path, large_doc=True)

        # Package with small chunk size
        success, package_path = package_skill(
            skill_dir=skill_dir,
            open_folder_after=False,
            skip_quality_check=True,
            target="langchain",
            enable_chunking=True,
            chunk_max_tokens=256,  # Small chunks
            preserve_code_blocks=True,
        )

        assert success

        with open(package_path) as f:
            data_small = json.load(f)

        # Package with large chunk size
        success, package_path2 = package_skill(
            skill_dir=skill_dir,
            open_folder_after=False,
            skip_quality_check=True,
            target="langchain",
            enable_chunking=True,
            chunk_max_tokens=1024,  # Large chunks
            preserve_code_blocks=True,
        )

        assert success

        with open(package_path2) as f:
            data_large = json.load(f)

        # Small chunk size should produce more chunks
        assert len(data_small) > len(data_large), (
            f"Small chunks ({len(data_small)}) should be more than large chunks ({len(data_large)})"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
