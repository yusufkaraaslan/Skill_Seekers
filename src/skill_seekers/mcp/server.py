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
