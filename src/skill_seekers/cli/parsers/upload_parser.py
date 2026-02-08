"""Upload subcommand parser."""

from .base import SubcommandParser


class UploadParser(SubcommandParser):
    """Parser for upload subcommand."""

    @property
    def name(self) -> str:
        return "upload"

    @property
    def help(self) -> str:
        return "Upload skill to LLM platform or vector database"

    @property
    def description(self) -> str:
        return "Upload skill package to Claude, Gemini, OpenAI, ChromaDB, or Weaviate"

    def add_arguments(self, parser):
        """Add upload-specific arguments."""
        parser.add_argument(
            "package_file", help="Path to skill package file (e.g., output/react.zip)"
        )

        parser.add_argument(
            "--target",
            choices=["claude", "gemini", "openai", "chroma", "weaviate"],
            default="claude",
            help="Target platform (default: claude)",
        )

        parser.add_argument("--api-key", help="Platform API key (or set environment variable)")

        # ChromaDB upload options
        parser.add_argument(
            "--chroma-url",
            help="ChromaDB URL (default: http://localhost:8000 for HTTP, or use --persist-directory for local)",
        )
        parser.add_argument(
            "--persist-directory",
            help="Local directory for persistent ChromaDB storage (default: ./chroma_db)",
        )

        # Embedding options
        parser.add_argument(
            "--embedding-function",
            choices=["openai", "sentence-transformers", "none"],
            help="Embedding function for ChromaDB/Weaviate (default: platform default)",
        )
        parser.add_argument(
            "--openai-api-key", help="OpenAI API key for embeddings (or set OPENAI_API_KEY env var)"
        )

        # Weaviate upload options
        parser.add_argument(
            "--weaviate-url",
            default="http://localhost:8080",
            help="Weaviate URL (default: http://localhost:8080)",
        )
        parser.add_argument(
            "--use-cloud",
            action="store_true",
            help="Use Weaviate Cloud (requires --api-key and --cluster-url)",
        )
        parser.add_argument(
            "--cluster-url", help="Weaviate Cloud cluster URL (e.g., https://xxx.weaviate.network)"
        )
