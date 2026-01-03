#!/usr/bin/env python3
"""
Skill Seeker MCP Server - Compatibility Shim

This file provides backward compatibility by delegating to the new server_fastmcp.py implementation.

For new installations, use server_fastmcp.py directly:
    python -m skill_seekers.mcp.server_fastmcp

This shim will be deprecated in v3.0.0 (6+ months after v2.4.0 release).
"""

import sys
import warnings

# Show deprecation warning (can be disabled with PYTHONWARNINGS=ignore)
warnings.warn(
    "The legacy server.py is deprecated and will be removed in v3.0.0. "
    "Please update your MCP configuration to use 'server_fastmcp' instead:\n"
    "  OLD: python -m skill_seekers.mcp.server\n"
    "  NEW: python -m skill_seekers.mcp.server_fastmcp\n"
    "The new server provides the same functionality with improved performance.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export tool functions for backward compatibility with tests
try:
    from skill_seekers.mcp.tools.config_tools import (
        generate_config as generate_config_tool,
        list_configs as list_configs_tool,
        validate_config as validate_config_tool,
    )
    from skill_seekers.mcp.tools.scraping_tools import (
        estimate_pages_tool,
        scrape_docs_tool,
        scrape_github_tool,
        scrape_pdf_tool,
        detect_patterns_tool,
        run_subprocess_with_streaming,
    )
    from skill_seekers.mcp.tools.packaging_tools import (
        package_skill_tool,
        upload_skill_tool,
        install_skill_tool,
    )
    from skill_seekers.mcp.tools.splitting_tools import (
        split_config as split_config_tool,
        generate_router as generate_router_tool,
    )
    from skill_seekers.mcp.tools.source_tools import (
        fetch_config_tool,
        submit_config_tool,
        add_config_source_tool,
        list_config_sources_tool,
        remove_config_source_tool,
    )

    # For test compatibility - create call_tool router function
    async def call_tool(name: str, arguments: dict):
        """Route tool calls to appropriate handlers (backward compatibility)."""
        from mcp.types import TextContent

        try:
            if name == "generate_config":
                return await generate_config_tool(arguments)
            elif name == "estimate_pages":
                return await estimate_pages_tool(arguments)
            elif name == "scrape_docs":
                return await scrape_docs_tool(arguments)
            elif name == "package_skill":
                return await package_skill_tool(arguments)
            elif name == "upload_skill":
                return await upload_skill_tool(arguments)
            elif name == "list_configs":
                return await list_configs_tool(arguments)
            elif name == "validate_config":
                return await validate_config_tool(arguments)
            elif name == "split_config":
                return await split_config_tool(arguments)
            elif name == "generate_router":
                return await generate_router_tool(arguments)
            elif name == "scrape_pdf":
                return await scrape_pdf_tool(arguments)
            elif name == "scrape_github":
                return await scrape_github_tool(arguments)
            elif name == "fetch_config":
                return await fetch_config_tool(arguments)
            elif name == "submit_config":
                return await submit_config_tool(arguments)
            elif name == "add_config_source":
                return await add_config_source_tool(arguments)
            elif name == "list_config_sources":
                return await list_config_sources_tool(arguments)
            elif name == "remove_config_source":
                return await remove_config_source_tool(arguments)
            elif name == "install_skill":
                return await install_skill_tool(arguments)
            elif name == "detect_patterns":
                return await detect_patterns_tool(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # For test compatibility - create a mock list_tools function
    async def list_tools():
        """Mock list_tools for backward compatibility with tests."""
        from mcp.types import Tool
        tools = [
            Tool(
                name="generate_config",
                description="Generate config file",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="list_configs",
                description="List available configs",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="validate_config",
                description="Validate config file",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="estimate_pages",
                description="Estimate page count",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="scrape_docs",
                description="Scrape documentation",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="scrape_github",
                description="Scrape GitHub repository",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="scrape_pdf",
                description="Scrape PDF file",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="package_skill",
                description="Package skill into .zip",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="upload_skill",
                description="Upload skill to Claude",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="install_skill",
                description="Install skill",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="split_config",
                description="Split large config",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="generate_router",
                description="Generate router skill",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="fetch_config",
                description="Fetch config from source",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="submit_config",
                description="Submit config to community",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="add_config_source",
                description="Add config source",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="list_config_sources",
                description="List config sources",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="remove_config_source",
                description="Remove config source",
                inputSchema={"type": "object", "properties": {}}
            ),
        ]
        return tools

except ImportError:
    # If imports fail, provide empty stubs
    pass

# Delegate to the new FastMCP implementation
if __name__ == "__main__":
    try:
        from skill_seekers.mcp import server_fastmcp
        # Run the new server
        server_fastmcp.main()
    except ImportError as e:
        print(f"❌ Error: Could not import server_fastmcp: {e}", file=sys.stderr)
        print("Ensure the package is installed correctly:", file=sys.stderr)
        print("  pip install -e .", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running server: {e}", file=sys.stderr)
        sys.exit(1)
