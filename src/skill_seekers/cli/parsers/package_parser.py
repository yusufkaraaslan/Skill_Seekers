"""Package subcommand parser."""

from .base import SubcommandParser


class PackageParser(SubcommandParser):
    """Parser for package subcommand."""

    @property
    def name(self) -> str:
        return "package"

    @property
    def help(self) -> str:
        return "Package skill into platform-specific format"

    @property
    def description(self) -> str:
        return "Package skill directory into uploadable format for various LLM platforms"

    def add_arguments(self, parser):
        """Add package-specific arguments."""
        parser.add_argument("skill_directory", help="Skill directory path (e.g., output/react/)")
        parser.add_argument(
            "--no-open", action="store_true", help="Don't open output folder after packaging"
        )
        parser.add_argument(
            "--skip-quality-check", action="store_true", help="Skip quality checks before packaging"
        )
        parser.add_argument(
            "--target",
            choices=[
                "claude",
                "gemini",
                "openai",
                "markdown",
                "langchain",
                "llama-index",
                "haystack",
                "weaviate",
                "chroma",
                "faiss",
                "qdrant",
            ],
            default="claude",
            help="Target LLM platform (default: claude)",
        )
        parser.add_argument(
            "--upload",
            action="store_true",
            help="Automatically upload after packaging (requires platform API key)",
        )

        # Streaming options
        parser.add_argument(
            "--streaming",
            action="store_true",
            help="Use streaming ingestion for large docs (memory-efficient)",
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=4000,
            help="Maximum characters per chunk (streaming mode, default: 4000)",
        )
        parser.add_argument(
            "--chunk-overlap",
            type=int,
            default=200,
            help="Overlap between chunks (streaming mode, default: 200)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of chunks per batch (streaming mode, default: 100)",
        )

        # RAG chunking options
        parser.add_argument(
            "--chunk",
            action="store_true",
            help="Enable intelligent chunking for RAG platforms (auto-enabled for RAG adaptors)",
        )
        parser.add_argument(
            "--chunk-tokens", type=int, default=512, help="Maximum tokens per chunk (default: 512)"
        )
        parser.add_argument(
            "--no-preserve-code",
            action="store_true",
            help="Allow code block splitting (default: code blocks preserved)",
        )
