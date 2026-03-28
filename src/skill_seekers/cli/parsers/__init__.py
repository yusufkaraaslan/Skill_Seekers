"""Parser registry and factory.

This module registers all subcommand parsers and provides a factory
function to create them.
"""

from .base import SubcommandParser

# Import all parser classes
from .create_parser import CreateParser  # NEW: Unified create command
from .config_parser import ConfigParser
from .scrape_parser import ScrapeParser
from .github_parser import GitHubParser
from .pdf_parser import PDFParser
from .word_parser import WordParser
from .epub_parser import EpubParser
from .video_parser import VideoParser
from .unified_parser import UnifiedParser
from .enhance_parser import EnhanceParser
from .enhance_status_parser import EnhanceStatusParser
from .package_parser import PackageParser
from .upload_parser import UploadParser
from .estimate_parser import EstimateParser
from .test_examples_parser import TestExamplesParser
from .install_agent_parser import InstallAgentParser
from .analyze_parser import AnalyzeParser
from .install_parser import InstallParser
from .resume_parser import ResumeParser
from .stream_parser import StreamParser
from .update_parser import UpdateParser
from .multilang_parser import MultilangParser
from .quality_parser import QualityParser
from .workflows_parser import WorkflowsParser
from .sync_config_parser import SyncConfigParser
from .doctor_parser import DoctorParser

# New source type parsers (v3.2.0+)
from .jupyter_parser import JupyterParser
from .html_parser import HtmlParser
from .openapi_parser import OpenAPIParser
from .asciidoc_parser import AsciiDocParser
from .pptx_parser import PptxParser
from .rss_parser import RssParser
from .manpage_parser import ManPageParser
from .confluence_parser import ConfluenceParser
from .notion_parser import NotionParser
from .chat_parser import ChatParser

# Registry of all parsers (in order of usage frequency)
PARSERS = [
    CreateParser(),  # NEW: Unified create command (placed first for prominence)
    DoctorParser(),
    ConfigParser(),
    ScrapeParser(),
    GitHubParser(),
    PackageParser(),
    UploadParser(),
    AnalyzeParser(),
    EnhanceParser(),
    EnhanceStatusParser(),
    PDFParser(),
    WordParser(),
    EpubParser(),
    VideoParser(),
    UnifiedParser(),
    EstimateParser(),
    InstallParser(),
    InstallAgentParser(),
    TestExamplesParser(),
    ResumeParser(),
    StreamParser(),
    UpdateParser(),
    MultilangParser(),
    QualityParser(),
    WorkflowsParser(),
    SyncConfigParser(),
    # New source types (v3.2.0+)
    JupyterParser(),
    HtmlParser(),
    OpenAPIParser(),
    AsciiDocParser(),
    PptxParser(),
    RssParser(),
    ManPageParser(),
    ConfluenceParser(),
    NotionParser(),
    ChatParser(),
]


def register_parsers(subparsers):
    """Register all subcommand parsers.

    Args:
        subparsers: Subparsers object from main ArgumentParser

    Returns:
        None
    """
    for parser_instance in PARSERS:
        parser_instance.create_parser(subparsers)


def get_parser_names():
    """Get list of all subcommand names.

    Returns:
        List of subcommand names (strings)
    """
    return [p.name for p in PARSERS]


__all__ = [
    "SubcommandParser",
    "PARSERS",
    "register_parsers",
    "get_parser_names",
]
