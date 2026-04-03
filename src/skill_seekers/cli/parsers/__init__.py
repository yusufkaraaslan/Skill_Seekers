"""Parser registry and factory.

This module registers all subcommand parsers and provides a factory
function to create them. Individual scraper commands have been removed —
use `skill-seekers create <source>` for all source types.
"""

from .base import SubcommandParser

# Import parser classes (scrapers removed — use create command)
from .create_parser import CreateParser
from .config_parser import ConfigParser
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

# Registry of all parsers
PARSERS = [
    CreateParser(),
    DoctorParser(),
    ConfigParser(),
    UnifiedParser(),
    AnalyzeParser(),
    EnhanceParser(),
    EnhanceStatusParser(),
    PackageParser(),
    UploadParser(),
    EstimateParser(),
    InstallParser(),
    InstallAgentParser(),
    TestExamplesParser(),
    ResumeParser(),
    QualityParser(),
    WorkflowsParser(),
    SyncConfigParser(),
    StreamParser(),
    UpdateParser(),
    MultilangParser(),
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
