"""
SkillConverter — Base interface for all source type converters.

Every scraper/converter inherits this and implements extract().
The create command calls converter.run() — same interface for all 17 types.

Usage:
    converter = get_converter("web", config)
    converter.run()  # extract + build + return exit code
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SkillConverter:
    """Base interface for all skill converters.

    Subclasses must implement extract() at minimum.
    build_skill() has a default implementation that most converters override.
    """

    # Override in subclass
    SOURCE_TYPE: str = "unknown"

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.name = config.get("name", "unnamed")
        self.skill_dir = f"output/{self.name}"

    def run(self) -> int:
        """Main entry point — extract source and build skill.

        Returns:
            Exit code (0 for success, non-zero for failure).
        """
        try:
            logger.info(f"Extracting from {self.SOURCE_TYPE} source: {self.name}")
            self.extract()
            self.build_skill()
            logger.info(f"✅ Skill built: {self.skill_dir}/")
            return 0
        except Exception as e:
            logger.error(f"❌ {self.SOURCE_TYPE} extraction failed: {e}")
            return 1

    def extract(self):
        """Extract content from source. Override in subclass."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement extract()")

    def build_skill(self):
        """Build SKILL.md from extracted data. Override in subclass."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement build_skill()")


# Registry mapping source type → (module_path, class_name)
CONVERTER_REGISTRY: dict[str, tuple[str, str]] = {
    "web": ("skill_seekers.cli.doc_scraper", "DocToSkillConverter"),
    "github": ("skill_seekers.cli.github_scraper", "GitHubScraper"),
    "pdf": ("skill_seekers.cli.pdf_scraper", "PDFToSkillConverter"),
    "word": ("skill_seekers.cli.word_scraper", "WordToSkillConverter"),
    "epub": ("skill_seekers.cli.epub_scraper", "EpubToSkillConverter"),
    "video": ("skill_seekers.cli.video_scraper", "VideoToSkillConverter"),
    "local": ("skill_seekers.cli.codebase_scraper", "CodebaseAnalyzer"),
    "jupyter": ("skill_seekers.cli.jupyter_scraper", "JupyterToSkillConverter"),
    "html": ("skill_seekers.cli.html_scraper", "HtmlToSkillConverter"),
    "openapi": ("skill_seekers.cli.openapi_scraper", "OpenAPIToSkillConverter"),
    "asciidoc": ("skill_seekers.cli.asciidoc_scraper", "AsciiDocToSkillConverter"),
    "pptx": ("skill_seekers.cli.pptx_scraper", "PptxToSkillConverter"),
    "rss": ("skill_seekers.cli.rss_scraper", "RssToSkillConverter"),
    "manpage": ("skill_seekers.cli.man_scraper", "ManPageToSkillConverter"),
    "confluence": ("skill_seekers.cli.confluence_scraper", "ConfluenceToSkillConverter"),
    "notion": ("skill_seekers.cli.notion_scraper", "NotionToSkillConverter"),
    "chat": ("skill_seekers.cli.chat_scraper", "ChatToSkillConverter"),
    # NOTE: UnifiedScraper takes (config_path: str), not (config: dict).
    # Callers must construct it directly, not via get_converter().
    "config": ("skill_seekers.cli.unified_scraper", "UnifiedScraper"),
}


def get_converter(source_type: str, config: dict[str, Any]) -> SkillConverter:
    """Get the appropriate converter for a source type.

    Args:
        source_type: Source type from SourceDetector (web, github, pdf, etc.)
        config: Configuration dict for the converter.

    Returns:
        Initialized converter instance.

    Raises:
        ValueError: If source type is not supported.
    """
    import importlib

    if source_type not in CONVERTER_REGISTRY:
        raise ValueError(
            f"Unknown source type: {source_type}. "
            f"Supported: {', '.join(sorted(CONVERTER_REGISTRY))}"
        )

    module_path, class_name = CONVERTER_REGISTRY[source_type]
    module = importlib.import_module(module_path)
    converter_class = getattr(module, class_name)
    return converter_class(config)
