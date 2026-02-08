"""
Embedding generation with multiple model support.
"""

import os
import hashlib
import numpy as np

# OpenAI support
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Sentence transformers support
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Voyage AI support (recommended by Anthropic for embeddings)
try:
    import voyageai

    VOYAGE_AVAILABLE = True
except ImportError:
    VOYAGE_AVAILABLE = False


class EmbeddingGenerator:
    """
    Generate embeddings using multiple model providers.

    Supported providers:
    - OpenAI (text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002)
    - Sentence Transformers (all-MiniLM-L6-v2, all-mpnet-base-v2, etc.)
    - Anthropic/Voyage AI (voyage-2, voyage-large-2)

    Examples:
        # OpenAI embeddings
        generator = EmbeddingGenerator()
        embedding = generator.generate("Hello world", model="text-embedding-3-small")

        # Sentence transformers (local, no API)
        embedding = generator.generate("Hello world", model="all-MiniLM-L6-v2")

        # Batch generation
        embeddings = generator.generate_batch(
            ["text1", "text2", "text3"],
            model="text-embedding-3-small"
        )
    """

    # Model configurations
    MODELS = {
        # OpenAI models
        "text-embedding-3-small": {
            "provider": "openai",
            "dimensions": 1536,
            "max_tokens": 8191,
            "cost_per_million": 0.02,
        },
        "text-embedding-3-large": {
            "provider": "openai",
            "dimensions": 3072,
            "max_tokens": 8191,
            "cost_per_million": 0.13,
        },
        "text-embedding-ada-002": {
            "provider": "openai",
            "dimensions": 1536,
            "max_tokens": 8191,
            "cost_per_million": 0.10,
        },
        # Voyage AI models (recommended by Anthropic)
        "voyage-3": {
            "provider": "voyage",
            "dimensions": 1024,
            "max_tokens": 32000,
            "cost_per_million": 0.06,
        },
        "voyage-3-lite": {
            "provider": "voyage",
            "dimensions": 512,
            "max_tokens": 32000,
            "cost_per_million": 0.06,
        },
        "voyage-large-2": {
            "provider": "voyage",
            "dimensions": 1536,
            "max_tokens": 16000,
            "cost_per_million": 0.12,
        },
        "voyage-code-2": {
            "provider": "voyage",
            "dimensions": 1536,
            "max_tokens": 16000,
            "cost_per_million": 0.12,
        },
        "voyage-2": {
            "provider": "voyage",
            "dimensions": 1024,
            "max_tokens": 4000,
            "cost_per_million": 0.10,
        },
        # Sentence transformer models (local, free)
        "all-MiniLM-L6-v2": {
            "provider": "sentence-transformers",
            "dimensions": 384,
            "max_tokens": 256,
            "cost_per_million": 0.0,
        },
        "all-mpnet-base-v2": {
            "provider": "sentence-transformers",
            "dimensions": 768,
            "max_tokens": 384,
            "cost_per_million": 0.0,
        },
        "paraphrase-MiniLM-L6-v2": {
            "provider": "sentence-transformers",
            "dimensions": 384,
            "max_tokens": 128,
            "cost_per_million": 0.0,
        },
    }

    def __init__(
        self,
        api_key: str | None = None,
        voyage_api_key: str | None = None,
        cache_dir: str | None = None,
    ):
        """
        Initialize embedding generator.

        Args:
            api_key: API key for OpenAI
            voyage_api_key: API key for Voyage AI (Anthropic's recommended embeddings)
            cache_dir: Directory for caching models (sentence-transformers)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.voyage_api_key = voyage_api_key or os.getenv("VOYAGE_API_KEY")
        self.cache_dir = cache_dir

        # Initialize OpenAI client
        if OPENAI_AVAILABLE and self.api_key:
            self.openai_client = OpenAI(api_key=self.api_key)
        else:
            self.openai_client = None

        # Initialize Voyage AI client
        if VOYAGE_AVAILABLE and self.voyage_api_key:
            self.voyage_client = voyageai.Client(api_key=self.voyage_api_key)
        else:
            self.voyage_client = None

        # Cache for sentence transformer models
        self._st_models = {}

    def get_model_info(self, model: str) -> dict:
        """Get information about a model."""
        if model not in self.MODELS:
            raise ValueError(
                f"Unknown model: {model}. Available models: {', '.join(self.MODELS.keys())}"
            )
        return self.MODELS[model]

    def list_models(self) -> list[dict]:
        """List all available models."""
        models = []
        for name, info in self.MODELS.items():
            models.append(
                {
                    "name": name,
                    "provider": info["provider"],
                    "dimensions": info["dimensions"],
                    "max_tokens": info["max_tokens"],
                    "cost_per_million": info.get("cost_per_million", 0.0),
                }
            )
        return models

    def generate(
        self, text: str, model: str = "text-embedding-3-small", normalize: bool = True
    ) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            model: Model name
            normalize: Whether to normalize to unit length

        Returns:
            Embedding vector

        Raises:
            ValueError: If model is not supported
            Exception: If embedding generation fails
        """
        model_info = self.get_model_info(model)
        provider = model_info["provider"]

        if provider == "openai":
            return self._generate_openai(text, model, normalize)
        elif provider == "voyage":
            return self._generate_voyage(text, model, normalize)
        elif provider == "sentence-transformers":
            return self._generate_sentence_transformer(text, model, normalize)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate_batch(
        self,
        texts: list[str],
        model: str = "text-embedding-3-small",
        normalize: bool = True,
        batch_size: int = 32,
    ) -> tuple[list[list[float]], int]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            model: Model name
            normalize: Whether to normalize to unit length
            batch_size: Batch size for processing

        Returns:
            Tuple of (embeddings list, dimensions)

        Raises:
            ValueError: If model is not supported
            Exception: If embedding generation fails
        """
        model_info = self.get_model_info(model)
        provider = model_info["provider"]

        if provider == "openai":
            return self._generate_openai_batch(texts, model, normalize, batch_size)
        elif provider == "voyage":
            return self._generate_voyage_batch(texts, model, normalize, batch_size)
        elif provider == "sentence-transformers":
            return self._generate_sentence_transformer_batch(texts, model, normalize, batch_size)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _generate_openai(self, text: str, model: str, normalize: bool) -> list[float]:
        """Generate embedding using OpenAI API."""
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI is required for OpenAI embeddings. Install with: pip install openai"
            )

        if not self.openai_client:
            raise ValueError("OpenAI API key not provided")

        try:
            response = self.openai_client.embeddings.create(input=text, model=model)
            embedding = response.data[0].embedding

            if normalize:
                embedding = self._normalize(embedding)

            return embedding
        except Exception as e:
            raise Exception(f"OpenAI embedding generation failed: {e}") from e

    def _generate_openai_batch(
        self, texts: list[str], model: str, normalize: bool, batch_size: int
    ) -> tuple[list[list[float]], int]:
        """Generate embeddings using OpenAI API in batches."""
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI is required for OpenAI embeddings. Install with: pip install openai"
            )

        if not self.openai_client:
            raise ValueError("OpenAI API key not provided")

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            try:
                response = self.openai_client.embeddings.create(input=batch, model=model)

                batch_embeddings = [item.embedding for item in response.data]

                if normalize:
                    batch_embeddings = [self._normalize(emb) for emb in batch_embeddings]

                all_embeddings.extend(batch_embeddings)

            except Exception as e:
                raise Exception(f"OpenAI batch embedding generation failed: {e}") from e

        dimensions = len(all_embeddings[0]) if all_embeddings else 0
        return all_embeddings, dimensions

    def _generate_voyage(self, text: str, model: str, normalize: bool) -> list[float]:
        """Generate embedding using Voyage AI API."""
        if not VOYAGE_AVAILABLE:
            raise ImportError(
                "voyageai is required for Voyage AI embeddings. Install with: pip install voyageai"
            )

        if not self.voyage_client:
            raise ValueError("Voyage API key not provided")

        try:
            result = self.voyage_client.embed(texts=[text], model=model)
            embedding = result.embeddings[0]

            if normalize:
                embedding = self._normalize(embedding)

            return embedding
        except Exception as e:
            raise Exception(f"Voyage AI embedding generation failed: {e}") from e

    def _generate_voyage_batch(
        self, texts: list[str], model: str, normalize: bool, batch_size: int
    ) -> tuple[list[list[float]], int]:
        """Generate embeddings using Voyage AI API in batches."""
        if not VOYAGE_AVAILABLE:
            raise ImportError(
                "voyageai is required for Voyage AI embeddings. Install with: pip install voyageai"
            )

        if not self.voyage_client:
            raise ValueError("Voyage API key not provided")

        all_embeddings = []

        # Process in batches (Voyage AI supports up to 128 texts per request)
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            try:
                result = self.voyage_client.embed(texts=batch, model=model)

                batch_embeddings = result.embeddings

                if normalize:
                    batch_embeddings = [self._normalize(emb) for emb in batch_embeddings]

                all_embeddings.extend(batch_embeddings)

            except Exception as e:
                raise Exception(f"Voyage AI batch embedding generation failed: {e}") from e

        dimensions = len(all_embeddings[0]) if all_embeddings else 0
        return all_embeddings, dimensions

    def _generate_sentence_transformer(self, text: str, model: str, normalize: bool) -> list[float]:
        """Generate embedding using sentence-transformers."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for local embeddings. "
                "Install with: pip install sentence-transformers"
            )

        # Load model (with caching)
        if model not in self._st_models:
            self._st_models[model] = SentenceTransformer(model, cache_folder=self.cache_dir)

        st_model = self._st_models[model]

        # Generate embedding
        embedding = st_model.encode(text, normalize_embeddings=normalize)

        return embedding.tolist()

    def _generate_sentence_transformer_batch(
        self, texts: list[str], model: str, normalize: bool, batch_size: int
    ) -> tuple[list[list[float]], int]:
        """Generate embeddings using sentence-transformers in batches."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for local embeddings. "
                "Install with: pip install sentence-transformers"
            )

        # Load model (with caching)
        if model not in self._st_models:
            self._st_models[model] = SentenceTransformer(model, cache_folder=self.cache_dir)

        st_model = self._st_models[model]

        # Generate embeddings in batches
        embeddings = st_model.encode(
            texts, batch_size=batch_size, normalize_embeddings=normalize, show_progress_bar=False
        )

        dimensions = len(embeddings[0]) if len(embeddings) > 0 else 0
        return embeddings.tolist(), dimensions

    @staticmethod
    def _normalize(embedding: list[float]) -> list[float]:
        """Normalize embedding to unit length."""
        vec = np.array(embedding)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    @staticmethod
    def compute_hash(text: str, model: str) -> str:
        """Compute cache key for text and model."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
