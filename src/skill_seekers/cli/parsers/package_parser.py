"""Package subcommand parser."""
from .base import SubcommandParser


class PackageParser(SubcommandParser):
    """Parser for package subcommand."""

    @property
    def name(self) -> str:
        return "package"

    @property
    def help(self) -> str:
        return "Package skill into .zip file"

    @property
    def description(self) -> str:
        return "Package skill directory into uploadable .zip"

    def add_arguments(self, parser):
        """Add package-specific arguments."""
        parser.add_argument("skill_directory", help="Skill directory path")
        parser.add_argument("--no-open", action="store_true", help="Don't open output folder")
        parser.add_argument("--upload", action="store_true", help="Auto-upload after packaging")
        parser.add_argument(
            "--target",
            choices=[
                "claude", "gemini", "openai", "markdown",
                "langchain", "llama-index", "haystack",
                "weaviate", "chroma", "faiss", "qdrant"
            ],
            default="claude",
            help="Target LLM platform (default: claude)",
        )
