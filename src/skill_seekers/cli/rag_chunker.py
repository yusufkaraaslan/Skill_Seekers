"""
RAG Chunker - Semantic chunking for RAG pipelines.

This module provides intelligent chunking of documentation with:
- Code block preservation (never split mid-code)
- Paragraph boundary respect (semantic chunking)
- Configurable chunk size and overlap
- Rich metadata injection

Usage:
    from skill_seekers.cli.rag_chunker import RAGChunker

    chunker = RAGChunker(chunk_size=512, chunk_overlap=50)
    chunks = chunker.chunk_skill(Path("output/react"))
"""

import re
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class RAGChunker:
    """
    Semantic chunker for RAG pipelines.

    Features:
    - Preserves code blocks (don't split mid-code)
    - Preserves paragraphs (semantic boundaries)
    - Adds metadata (source, category, chunk_id)
    - Configurable chunk size and overlap
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        preserve_code_blocks: bool = True,
        preserve_paragraphs: bool = True,
        min_chunk_size: int = 100,
    ):
        """
        Initialize RAG chunker.

        Args:
            chunk_size: Target chunk size in tokens (approximate)
            chunk_overlap: Overlap size between chunks in tokens
            preserve_code_blocks: Keep code blocks intact
            preserve_paragraphs: Split at paragraph boundaries
            min_chunk_size: Minimum chunk size (avoid tiny chunks)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_code_blocks = preserve_code_blocks
        self.preserve_paragraphs = preserve_paragraphs
        self.min_chunk_size = min_chunk_size

        # Approximate tokens per character (average for English)
        self.chars_per_token = 4

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses simple heuristic: ~4 chars per token for English.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // self.chars_per_token

    def chunk_document(
        self, text: str, metadata: dict, source_file: str | None = None
    ) -> list[dict]:
        """
        Chunk single document into RAG-ready chunks.

        Args:
            text: Document content
            metadata: Source metadata (url, category, etc.)
            source_file: Optional source filename

        Returns:
            List of chunks with metadata
        """
        if not text or not text.strip():
            logger.warning(f"Empty document: {source_file or 'unknown'}")
            return []

        # Extract code blocks if preserving them
        if self.preserve_code_blocks:
            text, code_blocks = self._extract_code_blocks(text)
        else:
            code_blocks = []

        # Find semantic boundaries
        boundaries = self._find_semantic_boundaries(text)

        # Split with overlap at boundaries
        chunks = self._split_with_overlap(text, boundaries)

        # Re-insert code blocks
        if self.preserve_code_blocks:
            chunks = self._reinsert_code_blocks(chunks, code_blocks)

        # Add metadata to each chunk
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "estimated_tokens": self.estimate_tokens(chunk_text),
                "has_code_block": "```" in chunk_text,
            }

            if source_file:
                chunk_metadata["source_file"] = source_file

            result.append(
                {
                    "chunk_id": f"{metadata.get('source', 'unknown')}_{i}",
                    "page_content": chunk_text.strip(),
                    "metadata": chunk_metadata,
                }
            )

        logger.info(
            f"Created {len(result)} chunks from {source_file or 'document'} "
            f"({self.estimate_tokens(text)} tokens → {len(chunks)} chunks)"
        )

        return result

    def chunk_skill(self, skill_dir: Path) -> list[dict]:
        """
        Chunk entire skill directory.

        Args:
            skill_dir: Path to skill directory (contains SKILL.md and references/)

        Returns:
            List of all chunks with metadata
        """
        all_chunks = []

        # Chunk main SKILL.md
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            with open(skill_md, encoding="utf-8") as f:
                content = f.read()

            metadata = {"source": skill_dir.name, "category": "overview", "file_type": "skill_md"}

            chunks = self.chunk_document(content, metadata, source_file="SKILL.md")
            all_chunks.extend(chunks)

        # Chunk reference files
        references_dir = skill_dir / "references"
        if references_dir.exists():
            for ref_file in references_dir.glob("*.md"):
                with open(ref_file, encoding="utf-8") as f:
                    content = f.read()

                metadata = {
                    "source": skill_dir.name,
                    "category": ref_file.stem,
                    "file_type": "reference",
                }

                chunks = self.chunk_document(
                    content, metadata, source_file=str(ref_file.relative_to(skill_dir))
                )
                all_chunks.extend(chunks)

        logger.info(f"Chunked skill directory {skill_dir.name}: {len(all_chunks)} total chunks")

        return all_chunks

    def _extract_code_blocks(self, text: str) -> tuple[str, list[dict]]:
        """
        Extract code blocks and replace with placeholders.

        Args:
            text: Document content

        Returns:
            Tuple of (text with placeholders, list of code blocks)
        """
        code_blocks = []
        placeholder_pattern = "<<CODE_BLOCK_{idx}>>"

        # Match code blocks (``` fenced blocks)
        # Use DOTALL flag to match across newlines
        code_block_pattern = r"```[^\n]*\n.*?```"

        def replacer(match):
            idx = len(code_blocks)
            code_blocks.append(
                {
                    "index": idx,
                    "content": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                }
            )
            return placeholder_pattern.format(idx=idx)

        text_with_placeholders = re.sub(code_block_pattern, replacer, text, flags=re.DOTALL)

        return text_with_placeholders, code_blocks

    def _reinsert_code_blocks(self, chunks: list[str], code_blocks: list[dict]) -> list[str]:
        """
        Re-insert code blocks into chunks.

        Args:
            chunks: Text chunks with placeholders
            code_blocks: Extracted code blocks

        Returns:
            Chunks with code blocks re-inserted
        """
        result = []
        for chunk in chunks:
            # Find all placeholders in this chunk
            for block in code_blocks:
                placeholder = f"<<CODE_BLOCK_{block['index']}>>"
                if placeholder in chunk:
                    chunk = chunk.replace(placeholder, block["content"])
            result.append(chunk)

        return result

    def _find_semantic_boundaries(self, text: str) -> list[int]:
        """
        Find paragraph and section boundaries.

        Args:
            text: Document content

        Returns:
            List of character positions for boundaries (sorted)
        """
        boundaries = [0]  # Start is always a boundary

        # Paragraph boundaries (double newline)
        if self.preserve_paragraphs:
            for match in re.finditer(r"\n\n+", text):
                boundaries.append(match.end())

        # Section headers (# Header)
        for match in re.finditer(r"\n#{1,6}\s+.+\n", text):
            boundaries.append(match.start())

        # Single newlines (less preferred, but useful)
        for match in re.finditer(r"\n", text):
            boundaries.append(match.start())

        # Add artificial boundaries for large documents
        # This ensures chunking works even when natural boundaries are sparse/clustered
        target_size_chars = self.chunk_size * self.chars_per_token

        # Only add artificial boundaries if:
        # 1. Document is large enough (> target_size_chars)
        # 2. We have sparse boundaries (< 1 boundary per chunk_size on average)
        if len(text) > target_size_chars:
            expected_chunks = len(text) // target_size_chars
            # If we don't have at least one boundary per expected chunk, add artificial ones
            if len(boundaries) < expected_chunks:
                for i in range(target_size_chars, len(text), target_size_chars):
                    if i not in boundaries:  # Don't duplicate existing boundaries
                        boundaries.append(i)

        # End is always a boundary
        boundaries.append(len(text))

        # Remove duplicates and sort
        boundaries = sorted(set(boundaries))

        return boundaries

    def _split_with_overlap(self, text: str, boundaries: list[int]) -> list[str]:
        """
        Split text at semantic boundaries with overlap.

        Args:
            text: Document content
            boundaries: Character positions for boundaries

        Returns:
            List of text chunks
        """
        chunks = []
        target_size_chars = self.chunk_size * self.chars_per_token
        overlap_chars = self.chunk_overlap * self.chars_per_token
        min_size_chars = self.min_chunk_size * self.chars_per_token

        # If text is smaller than target size, return it as single chunk
        if len(text) <= target_size_chars:
            if text.strip():
                return [text]
            return []

        i = 0
        while i < len(boundaries) - 1:
            start_pos = boundaries[i]

            # Find boundaries that fit within chunk_size
            j = i + 1
            while j < len(boundaries):
                potential_end = boundaries[j]
                potential_chunk = text[start_pos:potential_end]

                if len(potential_chunk) > target_size_chars:
                    # Use previous boundary if we have one
                    if j > i + 1:
                        j -= 1
                    break

                j += 1

            # If we didn't advance, force at least one boundary
            if j == i + 1:
                j = min(i + 2, len(boundaries))

            # Extract chunk
            end_pos = boundaries[min(j, len(boundaries) - 1)]
            chunk_text = text[start_pos:end_pos]

            # Add chunk if it meets minimum size requirement
            # (unless the entire text is smaller than target size)
            if chunk_text.strip() and (
                len(text) <= target_size_chars or len(chunk_text) >= min_size_chars
            ):
                chunks.append(chunk_text)

            # Move to next chunk with overlap
            if j < len(boundaries) - 1:
                # Find boundary for overlap
                overlap_start = max(start_pos, end_pos - overlap_chars)
                # Find nearest boundary to overlap_start
                overlap_boundary_idx = min(j - 1, i + 1)
                for k in range(i + 1, j):
                    if boundaries[k] >= overlap_start:
                        overlap_boundary_idx = k
                        break

                i = overlap_boundary_idx if overlap_boundary_idx > i else i + 1
            else:
                # No more chunks
                break

        return chunks

    def save_chunks(self, chunks: list[dict], output_path: Path) -> None:
        """
        Save chunks to JSON file.

        Args:
            chunks: List of chunks with metadata
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(chunks)} chunks to {output_path}")


def main():
    """CLI entry point for testing RAG chunker."""
    import argparse

    parser = argparse.ArgumentParser(
        description="RAG Chunker - Semantic chunking for RAG pipelines"
    )
    parser.add_argument("skill_dir", type=Path, help="Path to skill directory")
    parser.add_argument("--output", "-o", type=Path, help="Output JSON file")
    parser.add_argument("--chunk-size", type=int, default=512, help="Target chunk size in tokens")
    parser.add_argument("--chunk-overlap", type=int, default=50, help="Overlap size in tokens")
    parser.add_argument("--no-code-blocks", action="store_true", help="Don't preserve code blocks")
    parser.add_argument("--no-paragraphs", action="store_true", help="Don't preserve paragraphs")

    args = parser.parse_args()

    # Create chunker
    chunker = RAGChunker(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        preserve_code_blocks=not args.no_code_blocks,
        preserve_paragraphs=not args.no_paragraphs,
    )

    # Chunk skill
    chunks = chunker.chunk_skill(args.skill_dir)

    # Save to file
    output_path = args.output or args.skill_dir / "rag_chunks.json"
    chunker.save_chunks(chunks, output_path)

    print(f"✅ Created {len(chunks)} chunks")
    print(f"📄 Saved to: {output_path}")


if __name__ == "__main__":
    main()
