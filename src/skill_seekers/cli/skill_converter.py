"""
SkillConverter — Base interface for all source type converters.

Every scraper/converter inherits this and implements extract().
The create command calls converter.run() — same interface for all 18 types.

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
        # Honor an explicit output dir (from --output) when provided; otherwise
        # default to output/<name>. Subclasses that re-assign skill_dir do the
        # same so --output is respected for every source type.
        self.skill_dir = config.get("output_dir") or f"output/{self.name}"

    def run(self) -> int:
        """Main entry point — extract source and build skill.

        Returns:
            Exit code (0 for success, non-zero for failure).
        """
        try:
            # skip_scrape: reuse existing on-disk scraped data and go straight to
            # build (build_skill loads from disk). Previously callers set
            # converter.skip_scrape but run() ignored it, so it was a no-op and
            # cached data was re-scraped from the network anyway.
            if getattr(self, "skip_scrape", False):
                logger.info(
                    f"⏭️  Skipping extraction for {self.SOURCE_TYPE} source: {self.name} "
                    "(skip_scrape set — building from existing data)"
                )
            else:
                logger.info(f"Extracting from {self.SOURCE_TYPE} source: {self.name}")
                self.extract()
            result = self.build_skill()
            if result is False:
                logger.error(f"❌ {self.SOURCE_TYPE} build_skill() reported failure")
                return 1
            logger.info(f"✅ Skill built: {self.skill_dir}/")
            return 0
        except Exception as e:
            logger.exception(f"❌ {self.SOURCE_TYPE} extraction failed: {e}")
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


# Source types backed by an optional dependency. Maps the source type to the
# name of the module-level dependency-check function in its registered scraper
# module (see CONVERTER_REGISTRY). Each such function is the single source of
# truth for its install hint: it raises RuntimeError when the dependency is
# missing and is a no-op otherwise. get_converter() calls it so a missing
# optional dependency fails fast — at converter lookup — instead of partway
# through extraction.
#
# 'chat' is intentionally excluded: its requirement (slack_sdk vs discord.py)
# depends on the configured platform, so it is checked at runtime from config.
OPTIONAL_DEP_CHECKS: dict[str, str] = {
    "word": "_check_word_deps",
    "epub": "_check_epub_deps",
    "video": "check_video_dependencies",
    "jupyter": "_check_jupyter_deps",
    "openapi": "_check_yaml_deps",
    "asciidoc": "_check_asciidoc_deps",
    "pptx": "_check_pptx_deps",
    "rss": "_check_feedparser_deps",
    "confluence": "_check_atlassian_deps",
    "notion": "_check_notion_deps",
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
        RuntimeError: If the source type's optional dependency is not installed
            (raised by the scraper's own dependency check, with an install hint).
    """
    import importlib

    if source_type not in CONVERTER_REGISTRY:
        raise ValueError(
            f"Unknown source type: {source_type}. "
            f"Supported: {', '.join(sorted(CONVERTER_REGISTRY))}"
        )

    module_path, class_name = CONVERTER_REGISTRY[source_type]
    module = importlib.import_module(module_path)

    # Fail fast on a missing optional dependency, delegating to the scraper's
    # own dependency check so the install hint stays defined in one place.
    dep_check_name = OPTIONAL_DEP_CHECKS.get(source_type)
    if dep_check_name is not None:
        dep_check = getattr(module, dep_check_name, None)
        if callable(dep_check):
            dep_check()

    converter_class = getattr(module, class_name, None)
    if converter_class is None:
        raise ValueError(
            f"Class '{class_name}' not found in module '{module_path}'. "
            f"Check CONVERTER_REGISTRY entry for '{source_type}'."
        )
    return converter_class(config)
