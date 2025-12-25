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

    # For test compatibility - create a mock list_tools function
    async def list_tools():
        """Mock list_tools for backward compatibility with tests."""
        from mcp.types import Tool
        tools = [
            Tool(name="generate_config", description="Generate config file", inputSchema={"type": "object"}),
            Tool(name="list_configs", description="List available configs", inputSchema={"type": "object"}),
            Tool(name="validate_config", description="Validate config file", inputSchema={"type": "object"}),
            Tool(name="estimate_pages", description="Estimate page count", inputSchema={"type": "object"}),
            Tool(name="scrape_docs", description="Scrape documentation", inputSchema={"type": "object"}),
            Tool(name="scrape_github", description="Scrape GitHub repository", inputSchema={"type": "object"}),
            Tool(name="scrape_pdf", description="Scrape PDF file", inputSchema={"type": "object"}),
            Tool(name="package_skill", description="Package skill into .zip", inputSchema={"type": "object"}),
            Tool(name="upload_skill", description="Upload skill to Claude", inputSchema={"type": "object"}),
            Tool(name="install_skill", description="Install skill", inputSchema={"type": "object"}),
            Tool(name="split_config", description="Split large config", inputSchema={"type": "object"}),
            Tool(name="generate_router", description="Generate router skill", inputSchema={"type": "object"}),
            Tool(name="fetch_config", description="Fetch config from source", inputSchema={"type": "object"}),
            Tool(name="submit_config", description="Submit config to community", inputSchema={"type": "object"}),
            Tool(name="add_config_source", description="Add config source", inputSchema={"type": "object"}),
            Tool(name="list_config_sources", description="List config sources", inputSchema={"type": "object"}),
            Tool(name="remove_config_source", description="Remove config source", inputSchema={"type": "object"}),
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
