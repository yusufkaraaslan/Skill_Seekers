"""
Pydantic models for embedding API.
"""

from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class EmbeddingRequest(BaseModel):
    """Request model for single embedding generation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "This is a test document about Python programming.",
                "model": "text-embedding-3-small",
                "normalize": True,
            }
        }
    )

    text: str = Field(..., description="Text to generate embedding for")
    model: str = Field(default="text-embedding-3-small", description="Embedding model to use")
    normalize: bool = Field(default=True, description="Normalize embeddings to unit length")


class BatchEmbeddingRequest(BaseModel):
    """Request model for batch embedding generation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "texts": [
                    "First document about Python",
                    "Second document about JavaScript",
                    "Third document about Rust",
                ],
                "model": "text-embedding-3-small",
                "normalize": True,
                "batch_size": 32,
            }
        }
    )

    texts: list[str] = Field(..., description="List of texts to embed")
    model: str = Field(default="text-embedding-3-small", description="Embedding model to use")
    normalize: bool = Field(default=True, description="Normalize embeddings to unit length")
    batch_size: int | None = Field(
        default=32, description="Batch size for processing (default: 32)"
    )


class EmbeddingResponse(BaseModel):
    """Response model for embedding generation."""

    embedding: list[float] = Field(..., description="Generated embedding vector")
    model: str = Field(..., description="Model used for generation")
    dimensions: int = Field(..., description="Embedding dimensions")
    cached: bool = Field(default=False, description="Whether embedding was retrieved from cache")


class BatchEmbeddingResponse(BaseModel):
    """Response model for batch embedding generation."""

    embeddings: list[list[float]] = Field(..., description="List of embedding vectors")
    model: str = Field(..., description="Model used for generation")
    dimensions: int = Field(..., description="Embedding dimensions")
    count: int = Field(..., description="Number of embeddings generated")
    cached_count: int = Field(default=0, description="Number of embeddings retrieved from cache")


class SkillEmbeddingRequest(BaseModel):
    """Request model for skill content embedding."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "skill_path": "/path/to/skill/react",
                "model": "text-embedding-3-small",
                "chunk_size": 512,
                "overlap": 50,
            }
        }
    )

    skill_path: str = Field(..., description="Path to skill directory")
    model: str = Field(default="text-embedding-3-small", description="Embedding model to use")
    chunk_size: int = Field(default=512, description="Chunk size for splitting documents (tokens)")
    overlap: int = Field(default=50, description="Overlap between chunks (tokens)")


class SkillEmbeddingResponse(BaseModel):
    """Response model for skill content embedding."""

    skill_name: str = Field(..., description="Name of the skill")
    total_chunks: int = Field(..., description="Total number of chunks embedded")
    model: str = Field(..., description="Model used for generation")
    dimensions: int = Field(..., description="Embedding dimensions")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Skill metadata")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    models: list[str] = Field(..., description="Available embedding models")
    cache_enabled: bool = Field(..., description="Whether cache is enabled")
    cache_size: int | None = Field(None, description="Number of cached embeddings")


class ModelInfo(BaseModel):
    """Information about an embedding model."""

    name: str = Field(..., description="Model name")
    provider: str = Field(
        ..., description="Model provider (openai, anthropic, sentence-transformers)"
    )
    dimensions: int = Field(..., description="Embedding dimensions")
    max_tokens: int = Field(..., description="Maximum input tokens")
    cost_per_million: float | None = Field(
        None, description="Cost per million tokens (if applicable)"
    )


class ModelsResponse(BaseModel):
    """Response model for listing available models."""

    models: list[ModelInfo] = Field(..., description="List of available models")
    count: int = Field(..., description="Number of available models")
