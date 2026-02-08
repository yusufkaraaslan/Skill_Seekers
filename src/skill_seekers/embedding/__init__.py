"""
Embedding generation system for Skill Seekers.

Provides:
- FastAPI server for embedding generation
- Multiple embedding model support (OpenAI, sentence-transformers, Anthropic)
- Batch processing for efficiency
- Caching layer for embeddings
- Vector database integration

Usage:
    # Start server
    python -m skill_seekers.embedding.server

    # Generate embeddings
    curl -X POST http://localhost:8000/embed \
         -H "Content-Type: application/json" \
         -d '{"texts": ["Hello world"], "model": "text-embedding-3-small"}'
"""

from .models import EmbeddingRequest, EmbeddingResponse, BatchEmbeddingRequest
from .generator import EmbeddingGenerator
from .cache import EmbeddingCache

__all__ = [
    "EmbeddingRequest",
    "EmbeddingResponse",
    "BatchEmbeddingRequest",
    "EmbeddingGenerator",
    "EmbeddingCache",
]
