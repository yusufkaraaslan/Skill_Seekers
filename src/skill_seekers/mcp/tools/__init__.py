"""
MCP Tool Implementations

This package contains modular tool implementations for the Skill Seekers MCP server.
Tools are organized by functionality:

- config_tools: Configuration management (generate, list, validate)
- scraping_tools: Scraping operations (docs, GitHub, PDF, estimation)
- packaging_tools: Skill packaging and upload
- splitting_tools: Config splitting and router generation
- source_tools: Config source management (fetch, submit, add/remove sources)
"""

__version__ = "2.4.0"

from .config_tools import (
    generate_config as generate_config_impl,
    list_configs as list_configs_impl,
    validate_config as validate_config_impl,
)

from .scraping_tools import (
    estimate_pages_tool as estimate_pages_impl,
    scrape_docs_tool as scrape_docs_impl,
    scrape_github_tool as scrape_github_impl,
    scrape_pdf_tool as scrape_pdf_impl,
)

from .packaging_tools import (
    package_skill_tool as package_skill_impl,
    upload_skill_tool as upload_skill_impl,
    install_skill_tool as install_skill_impl,
)

from .splitting_tools import (
    split_config as split_config_impl,
    generate_router as generate_router_impl,
)

from .source_tools import (
    fetch_config_tool as fetch_config_impl,
    submit_config_tool as submit_config_impl,
    add_config_source_tool as add_config_source_impl,
    list_config_sources_tool as list_config_sources_impl,
    remove_config_source_tool as remove_config_source_impl,
)

__all__ = [
    # Config tools
    "generate_config_impl",
    "list_configs_impl",
    "validate_config_impl",
    # Scraping tools
    "estimate_pages_impl",
    "scrape_docs_impl",
    "scrape_github_impl",
    "scrape_pdf_impl",
    # Packaging tools
    "package_skill_impl",
    "upload_skill_impl",
    "install_skill_impl",
    # Splitting tools
    "split_config_impl",
    "generate_router_impl",
    # Source tools
    "fetch_config_impl",
    "submit_config_impl",
    "add_config_source_impl",
    "list_config_sources_impl",
    "remove_config_source_impl",
]
