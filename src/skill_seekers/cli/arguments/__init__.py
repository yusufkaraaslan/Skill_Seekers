"""Shared CLI argument definitions.

This module provides a single source of truth for all CLI argument definitions.
Both standalone modules and unified CLI parsers import from here.

Usage:
    from skill_seekers.cli.arguments.scrape import add_scrape_arguments
    from skill_seekers.cli.arguments.github import add_github_arguments
    from skill_seekers.cli.arguments.pdf import add_pdf_arguments
    from skill_seekers.cli.arguments.analyze import add_analyze_arguments
    from skill_seekers.cli.arguments.unified import add_unified_arguments
    from skill_seekers.cli.arguments.package import add_package_arguments
    from skill_seekers.cli.arguments.upload import add_upload_arguments
    from skill_seekers.cli.arguments.enhance import add_enhance_arguments

    parser = argparse.ArgumentParser()
    add_scrape_arguments(parser)
"""

from .common import add_common_arguments, COMMON_ARGUMENTS
from .scrape import add_scrape_arguments, SCRAPE_ARGUMENTS
from .github import add_github_arguments, GITHUB_ARGUMENTS
from .pdf import add_pdf_arguments, PDF_ARGUMENTS
from .analyze import add_analyze_arguments, ANALYZE_ARGUMENTS
from .unified import add_unified_arguments, UNIFIED_ARGUMENTS
from .package import add_package_arguments, PACKAGE_ARGUMENTS
from .upload import add_upload_arguments, UPLOAD_ARGUMENTS
from .enhance import add_enhance_arguments, ENHANCE_ARGUMENTS

__all__ = [
    # Functions
    "add_common_arguments",
    "add_scrape_arguments",
    "add_github_arguments",
    "add_pdf_arguments",
    "add_analyze_arguments",
    "add_unified_arguments",
    "add_package_arguments",
    "add_upload_arguments",
    "add_enhance_arguments",
    # Data
    "COMMON_ARGUMENTS",
    "SCRAPE_ARGUMENTS",
    "GITHUB_ARGUMENTS",
    "PDF_ARGUMENTS",
    "ANALYZE_ARGUMENTS",
    "UNIFIED_ARGUMENTS",
    "PACKAGE_ARGUMENTS",
    "UPLOAD_ARGUMENTS",
    "ENHANCE_ARGUMENTS",
]
