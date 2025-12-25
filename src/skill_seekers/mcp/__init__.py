"""Skill Seekers MCP (Model Context Protocol) server package.

This package provides MCP server integration for Claude Code, allowing
natural language interaction with Skill Seekers tools.

Main modules:
    - server_fastmcp: FastMCP-based server with 17 tools (MCP 2025 spec)
    - agent_detector: AI coding agent detection and configuration

Available MCP Tools:
    - list_configs: List all available preset configurations
    - generate_config: Generate a new config file for any docs site
    - validate_config: Validate a config file structure
    - estimate_pages: Estimate page count before scraping
    - scrape_docs: Scrape and build a skill
    - package_skill: Package skill into .zip file (with auto-upload)
    - upload_skill: Upload .zip to Claude
    - split_config: Split large documentation configs
    - generate_router: Generate router/hub skills

Agent Detection:
    - Supports 5 AI coding agents: Claude Code, Cursor, Windsurf, VS Code + Cline, IntelliJ IDEA
    - Auto-detects installed agents on Linux, macOS, and Windows
    - Generates correct MCP config for each agent (stdio vs HTTP)

Usage:
    The MCP server is typically run by Claude Code via configuration
    in ~/.config/claude-code/mcp.json
"""

__version__ = "2.4.0"

__all__ = ["agent_detector"]
