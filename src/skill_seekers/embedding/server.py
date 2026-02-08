#!/usr/bin/env python3
"""
FastAPI server for embedding generation.

Provides endpoints for:
- Single and batch embedding generation
- Skill content embedding
- Model listing and information
- Cache management
- Health checks

Usage:
    # Start server
    python -m skill_seekers.embedding.server

    # Or with uvicorn
    uvicorn skill_seekers.embedding.server:app --host 0.0.0.0 --port 8000
"""

import os
import sys
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from .models import (
    EmbeddingRequest,
    EmbeddingResponse,
    BatchEmbeddingRequest,
    BatchEmbeddingResponse,
    SkillEmbeddingRequest,
    SkillEmbeddingResponse,
    HealthResponse,
    ModelInfo,
    ModelsResponse,
)
from .generator import EmbeddingGenerator
from .cache import EmbeddingCache


# Initialize FastAPI app
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Skill Seekers Embedding API",
        description="Generate embeddings for text and skill content",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize generator and cache
    cache_dir = os.getenv(
        "EMBEDDING_CACHE_DIR", os.path.expanduser("~/.cache/skill-seekers/embeddings")
    )
    cache_db = os.path.join(cache_dir, "embeddings.db")
    cache_enabled = os.getenv("EMBEDDING_CACHE_ENABLED", "true").lower() == "true"

    generator = EmbeddingGenerator(
        api_key=os.getenv("OPENAI_API_KEY"), voyage_api_key=os.getenv("VOYAGE_API_KEY")
    )
    cache = EmbeddingCache(cache_db) if cache_enabled else None

    @app.get("/", response_model=dict)
    async def root():
        """Root endpoint."""
        return {
            "service": "Skill Seekers Embedding API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health", response_model=HealthResponse)
    async def health():
        """Health check endpoint."""
        models = [m["name"] for m in generator.list_models()]
        cache_size = cache.size() if cache else None

        return HealthResponse(
            status="ok",
            version="1.0.0",
            models=models,
            cache_enabled=cache_enabled,
            cache_size=cache_size,
        )

    @app.get("/models", response_model=ModelsResponse)
    async def list_models():
        """List available embedding models."""
        models_list = generator.list_models()

        model_infos = [
            ModelInfo(
                name=m["name"],
                provider=m["provider"],
                dimensions=m["dimensions"],
                max_tokens=m["max_tokens"],
                cost_per_million=m.get("cost_per_million"),
            )
            for m in models_list
        ]

        return ModelsResponse(models=model_infos, count=len(model_infos))

    @app.post("/embed", response_model=EmbeddingResponse)
    async def embed_text(request: EmbeddingRequest):
        """
        Generate embedding for a single text.

        Args:
            request: Embedding request

        Returns:
            Embedding response

        Raises:
            HTTPException: If embedding generation fails
        """
        try:
            # Check cache
            cached = False
            hash_key = generator.compute_hash(request.text, request.model)

            if cache and cache.has(hash_key):
                embedding = cache.get(hash_key)
                cached = True
            else:
                # Generate embedding
                embedding = generator.generate(
                    request.text, model=request.model, normalize=request.normalize
                )

                # Store in cache
                if cache:
                    cache.set(hash_key, embedding, request.model)

            return EmbeddingResponse(
                embedding=embedding, model=request.model, dimensions=len(embedding), cached=cached
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.post("/embed/batch", response_model=BatchEmbeddingResponse)
    async def embed_batch(request: BatchEmbeddingRequest):
        """
        Generate embeddings for multiple texts.

        Args:
            request: Batch embedding request

        Returns:
            Batch embedding response

        Raises:
            HTTPException: If embedding generation fails
        """
        try:
            # Check cache for each text
            cached_count = 0
            embeddings = []
            texts_to_generate = []
            text_indices = []

            for idx, text in enumerate(request.texts):
                hash_key = generator.compute_hash(text, request.model)

                if cache and cache.has(hash_key):
                    cached_embedding = cache.get(hash_key)
                    embeddings.append(cached_embedding)
                    cached_count += 1
                else:
                    embeddings.append(None)  # Placeholder
                    texts_to_generate.append(text)
                    text_indices.append(idx)

            # Generate embeddings for uncached texts
            if texts_to_generate:
                generated_embeddings, dimensions = generator.generate_batch(
                    texts_to_generate,
                    model=request.model,
                    normalize=request.normalize,
                    batch_size=request.batch_size,
                )

                # Fill in placeholders and cache
                for idx, text, embedding in zip(
                    text_indices, texts_to_generate, generated_embeddings, strict=False
                ):
                    embeddings[idx] = embedding

                    if cache:
                        hash_key = generator.compute_hash(text, request.model)
                        cache.set(hash_key, embedding, request.model)

            dimensions = len(embeddings[0]) if embeddings else 0

            return BatchEmbeddingResponse(
                embeddings=embeddings,
                model=request.model,
                dimensions=dimensions,
                count=len(embeddings),
                cached_count=cached_count,
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.post("/embed/skill", response_model=SkillEmbeddingResponse)
    async def embed_skill(request: SkillEmbeddingRequest):
        """
        Generate embeddings for skill content.

        Args:
            request: Skill embedding request

        Returns:
            Skill embedding response

        Raises:
            HTTPException: If skill embedding fails
        """
        try:
            skill_path = Path(request.skill_path)

            if not skill_path.exists():
                raise HTTPException(
                    status_code=404, detail=f"Skill path not found: {request.skill_path}"
                )

            # Read SKILL.md
            skill_md = skill_path / "SKILL.md"
            if not skill_md.exists():
                raise HTTPException(
                    status_code=404, detail=f"SKILL.md not found in {request.skill_path}"
                )

            skill_content = skill_md.read_text()

            # Simple chunking (split by double newline)
            chunks = [
                chunk.strip()
                for chunk in skill_content.split("\n\n")
                if chunk.strip() and len(chunk.strip()) > 50
            ]

            # Generate embeddings for chunks
            embeddings, dimensions = generator.generate_batch(
                chunks, model=request.model, normalize=True, batch_size=32
            )

            # TODO: Store embeddings in vector database
            # This would integrate with the vector database adaptors

            return SkillEmbeddingResponse(
                skill_name=skill_path.name,
                total_chunks=len(chunks),
                model=request.model,
                dimensions=dimensions,
                metadata={
                    "skill_path": str(skill_path),
                    "chunks": len(chunks),
                    "content_length": len(skill_content),
                },
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/cache/stats", response_model=dict)
    async def cache_stats():
        """Get cache statistics."""
        if not cache:
            raise HTTPException(status_code=404, detail="Cache is disabled")

        return cache.stats()

    @app.post("/cache/clear", response_model=dict)
    async def clear_cache(
        model: str | None = Query(None, description="Model to clear (all if not specified)"),
    ):
        """Clear cache entries."""
        if not cache:
            raise HTTPException(status_code=404, detail="Cache is disabled")

        deleted = cache.clear(model=model)

        return {"status": "ok", "deleted": deleted, "model": model or "all"}

    @app.post("/cache/clear-expired", response_model=dict)
    async def clear_expired():
        """Clear expired cache entries."""
        if not cache:
            raise HTTPException(status_code=404, detail="Cache is disabled")

        deleted = cache.clear_expired()

        return {"status": "ok", "deleted": deleted}

else:
    print("Error: FastAPI not available. Install with: pip install fastapi uvicorn")
    sys.exit(1)


def main():
    """Main entry point."""
    if not FASTAPI_AVAILABLE:
        print("Error: FastAPI not available. Install with: pip install fastapi uvicorn")
        sys.exit(1)

    # Get configuration from environment
    host = os.getenv("EMBEDDING_HOST", "0.0.0.0")
    port = int(os.getenv("EMBEDDING_PORT", "8000"))
    reload = os.getenv("EMBEDDING_RELOAD", "false").lower() == "true"

    print(f"🚀 Starting Embedding API server on {host}:{port}")
    print(f"📚 API documentation: http://{host}:{port}/docs")
    print(f"🔍 Cache enabled: {cache_enabled}")

    if cache_enabled:
        print(f"💾 Cache database: {cache_db}")

    uvicorn.run("skill_seekers.embedding.server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
