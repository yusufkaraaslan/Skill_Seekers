"""Parser registry and factory.

This module registers all subcommand parsers and provides a factory
function to create them.
"""

from .base import SubcommandParser

# Import all parser classes
from .config_parser import ConfigParser
from .scrape_parser import ScrapeParser
from .github_parser import GitHubParser
from .pdf_parser import PDFParser
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


# Registry of all parsers (in order of usage frequency)
PARSERS = [
    ConfigParser(),
    ScrapeParser(),
    GitHubParser(),
    PackageParser(),
    UploadParser(),
    AnalyzeParser(),
    EnhanceParser(),
    EnhanceStatusParser(),
    PDFParser(),
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
