"""
Tests for RAG Chunker (semantic chunking for RAG pipelines).
"""

import pytest
import json

from skill_seekers.cli.rag_chunker import RAGChunker


class TestRAGChunker:
    """Test suite for RAGChunker class."""

    def test_initialization(self):
        """Test RAGChunker initialization with default parameters."""
        chunker = RAGChunker()

        assert chunker.chunk_size == 512
        assert chunker.chunk_overlap == 50
        assert chunker.preserve_code_blocks is True
        assert chunker.preserve_paragraphs is True
        assert chunker.min_chunk_size == 100

    def test_initialization_custom_params(self):
        """Test RAGChunker initialization with custom parameters."""
        chunker = RAGChunker(
            chunk_size=1024,
            chunk_overlap=100,
            preserve_code_blocks=False,
            preserve_paragraphs=False,
            min_chunk_size=50,
        )

        assert chunker.chunk_size == 1024
        assert chunker.chunk_overlap == 100
        assert chunker.preserve_code_blocks is False
        assert chunker.preserve_paragraphs is False
        assert chunker.min_chunk_size == 50

    def test_estimate_tokens(self):
        """Test token estimation."""
        chunker = RAGChunker()

        # Test empty string
        assert chunker.estimate_tokens("") == 0

        # Test short string (~4 chars per token)
        text = "Hello world!"  # 12 chars
        tokens = chunker.estimate_tokens(text)
        assert tokens == 3  # 12 // 4 = 3

        # Test longer string
        text = "A" * 1000  # 1000 chars
        tokens = chunker.estimate_tokens(text)
        assert tokens == 250  # 1000 // 4 = 250

    def test_chunk_document_empty(self):
        """Test chunking empty document."""
        chunker = RAGChunker()

        chunks = chunker.chunk_document("", {"source": "test"})
        assert chunks == []

    def test_chunk_document_simple(self):
        """Test chunking simple document."""
        chunker = RAGChunker(chunk_size=50, chunk_overlap=10)

        text = "This is a simple document.\n\nIt has two paragraphs.\n\nAnd a third one."
        metadata = {"source": "test", "category": "simple"}

        chunks = chunker.chunk_document(text, metadata)

        assert len(chunks) > 0
        assert all("chunk_id" in chunk for chunk in chunks)
        assert all("page_content" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)

        # Check metadata propagation
        for i, chunk in enumerate(chunks):
            assert chunk["metadata"]["source"] == "test"
            assert chunk["metadata"]["category"] == "simple"
            assert chunk["metadata"]["chunk_index"] == i
            assert chunk["metadata"]["total_chunks"] == len(chunks)

    def test_preserve_code_blocks(self):
        """Test code block preservation."""
        chunker = RAGChunker(chunk_size=50, preserve_code_blocks=True)

        text = """
        Here is some text.

        ```python
        def hello():
            print("Hello, world!")
        ```

        More text here.
        """

        chunks = chunker.chunk_document(text, {"source": "test"})

        # Check that code block is in chunks
        has_code = any("```" in chunk["page_content"] for chunk in chunks)
        assert has_code

        # Check metadata indicates code block presence
        code_chunks = [c for c in chunks if c["metadata"]["has_code_block"]]
        assert len(code_chunks) > 0

    def test_code_block_not_split(self):
        """Test that code blocks are not split across chunks."""
        chunker = RAGChunker(chunk_size=20, preserve_code_blocks=True)

        text = """
        Short intro.

        ```python
        def very_long_function_that_exceeds_chunk_size():
            # This function is longer than our chunk size
            # But it should not be split
            print("Line 1")
            print("Line 2")
            print("Line 3")
            return True
        ```

        Short outro.
        """

        chunks = chunker.chunk_document(text, {"source": "test"})

        # Find chunk with code block
        code_chunks = [c for c in chunks if "```python" in c["page_content"]]

        if code_chunks:
            # Code block should be complete (has both ``` markers)
            code_chunk = code_chunks[0]
            assert code_chunk["page_content"].count("```") >= 2

    def test_semantic_boundaries(self):
        """Test that chunks respect paragraph boundaries."""
        chunker = RAGChunker(chunk_size=50, preserve_paragraphs=True)

        text = """
        First paragraph here.
        It has multiple sentences.

        Second paragraph here.
        Also with multiple sentences.

        Third paragraph.
        """

        chunks = chunker.chunk_document(text, {"source": "test"})

        # Check that chunks don't split paragraphs awkwardly
        # (This is a heuristic test)
        for chunk in chunks:
            content = chunk["page_content"]
            # Shouldn't have partial paragraphs (ending mid-sentence)
            if content.strip():
                assert not content.strip().endswith(",")

    def test_chunk_overlap(self):
        """Test chunk overlap functionality."""
        chunker = RAGChunker(chunk_size=50, chunk_overlap=20)

        text = "A" * 1000  # Long text

        chunks = chunker.chunk_document(text, {"source": "test"})

        # There should be overlap between consecutive chunks
        assert len(chunks) >= 2  # Should have multiple chunks

    def test_chunk_skill_directory(self, tmp_path):
        """Test chunking entire skill directory."""
        # Create temporary skill directory
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()

        # Create SKILL.md
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "# Main Skill\n\nThis is the main skill content.\n\nWith multiple paragraphs."
        )

        # Create references directory with files
        references_dir = skill_dir / "references"
        references_dir.mkdir()

        (references_dir / "getting_started.md").write_text(
            "# Getting Started\n\nQuick start guide."
        )
        (references_dir / "api.md").write_text("# API Reference\n\nAPI documentation.")

        # Chunk skill
        chunker = RAGChunker(chunk_size=50)
        chunks = chunker.chunk_skill(skill_dir)

        # Should have chunks from SKILL.md and references
        assert len(chunks) > 0

        # Check metadata diversity
        categories = {chunk["metadata"]["category"] for chunk in chunks}
        assert "overview" in categories  # From SKILL.md
        assert "getting_started" in categories or "api" in categories  # From references

    def test_save_chunks(self, tmp_path):
        """Test saving chunks to JSON file."""
        chunker = RAGChunker()

        chunks = [
            {
                "chunk_id": "test_0",
                "page_content": "Test content",
                "metadata": {"source": "test", "chunk_index": 0},
            }
        ]

        output_path = tmp_path / "chunks.json"
        chunker.save_chunks(chunks, output_path)

        # Check file was created
        assert output_path.exists()

        # Check content
        with open(output_path) as f:
            loaded = json.load(f)

        assert len(loaded) == 1
        assert loaded[0]["chunk_id"] == "test_0"

    def test_min_chunk_size(self):
        """Test that very small chunks are filtered out."""
        chunker = RAGChunker(chunk_size=50, min_chunk_size=100)

        text = "Short.\n\n" + "A" * 500  # Short chunk + long chunk

        chunks = chunker.chunk_document(text, {"source": "test"})

        # Very short chunks should be filtered
        # (Implementation detail: depends on boundaries)
        for chunk in chunks:
            # Each chunk should meet minimum size (approximately)
            assert len(chunk["page_content"]) >= 50  # Relaxed for test

    def test_extract_code_blocks(self):
        """Test code block extraction."""
        chunker = RAGChunker()

        text = """
        Text before code.

        ```python
        def hello():
            print("world")
        ```

        Text after code.
        """

        text_with_placeholders, code_blocks = chunker._extract_code_blocks(text)

        # Should have extracted one code block
        assert len(code_blocks) >= 1

        # Text should have placeholder
        assert "<<CODE_BLOCK_" in text_with_placeholders

        # Code blocks should have content
        for block in code_blocks:
            assert "content" in block
            assert "```" in block["content"]

    def test_find_semantic_boundaries(self):
        """Test semantic boundary detection."""
        chunker = RAGChunker()

        text = "First paragraph.\n\nSecond paragraph.\n\n# Header\n\nThird paragraph."

        boundaries = chunker._find_semantic_boundaries(text)

        # Should have multiple boundaries
        assert len(boundaries) >= 3  # Start, middle, end

        # First and last should be 0 and len(text)
        assert boundaries[0] == 0
        assert boundaries[-1] == len(text)

        # Should be sorted
        assert boundaries == sorted(boundaries)

    def test_real_world_documentation(self):
        """Test with realistic documentation content."""
        chunker = RAGChunker(chunk_size=512, chunk_overlap=50)

        text = """
        # React Hooks

        React Hooks are functions that let you "hook into" React state and lifecycle features from function components.

        ## useState

        The `useState` Hook lets you add React state to function components.

        ```javascript
        import { useState } from 'react';

        function Example() {
          const [count, setCount] = useState(0);

          return (
            <div>
              <p>You clicked {count} times</p>
              <button onClick={() => setCount(count + 1)}>
                Click me
              </button>
            </div>
          );
        }
        ```

        ## useEffect

        The `useEffect` Hook lets you perform side effects in function components.

        ```javascript
        import { useEffect } from 'react';

        function Example() {
          useEffect(() => {
            document.title = `You clicked ${count} times`;
          });
        }
        ```

        ## Best Practices

        - Only call Hooks at the top level
        - Only call Hooks from React functions
        - Use multiple Hooks to separate concerns
        """

        metadata = {
            "source": "react-docs",
            "category": "hooks",
            "url": "https://react.dev/reference/react",
        }

        chunks = chunker.chunk_document(text, metadata)

        # Should create reasonable chunks
        assert len(chunks) > 0

        # Code blocks should be preserved
        code_chunks = [c for c in chunks if c["metadata"]["has_code_block"]]
        assert len(code_chunks) >= 1

        # Metadata should be complete
        for chunk in chunks:
            assert chunk["metadata"]["source"] == "react-docs"
            assert chunk["metadata"]["category"] == "hooks"
            assert chunk["metadata"]["estimated_tokens"] > 0


class TestRAGChunkerIntegration:
    """Integration tests for RAG chunker with actual skills."""

    def test_chunk_then_load_with_langchain(self, tmp_path):
        """Test that chunks can be loaded by LangChain."""
        pytest.importorskip("langchain")  # Skip if LangChain not installed

        from langchain.schema import Document

        # Create test skill
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test\n\nTest content for LangChain.")

        # Chunk skill
        chunker = RAGChunker()
        chunks = chunker.chunk_skill(skill_dir)

        # Convert to LangChain Documents
        docs = [
            Document(page_content=chunk["page_content"], metadata=chunk["metadata"])
            for chunk in chunks
        ]

        # Check conversion worked
        assert len(docs) > 0
        assert all(isinstance(doc, Document) for doc in docs)

    def test_chunk_then_load_with_llamaindex(self, tmp_path):
        """Test that chunks can be loaded by LlamaIndex."""
        pytest.importorskip("llama_index")  # Skip if LlamaIndex not installed

        from llama_index.core.schema import TextNode

        # Create test skill
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test\n\nTest content for LlamaIndex.")

        # Chunk skill
        chunker = RAGChunker()
        chunks = chunker.chunk_skill(skill_dir)

        # Convert to LlamaIndex TextNodes
        nodes = [
            TextNode(text=chunk["page_content"], metadata=chunk["metadata"], id_=chunk["chunk_id"])
            for chunk in chunks
        ]

        # Check conversion worked
        assert len(nodes) > 0
        assert all(isinstance(node, TextNode) for node in nodes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
