#!/usr/bin/env python3
"""
Tests for FastMCP server HTTP transport support.
"""

import pytest
import asyncio
import sys

# Skip all tests if mcp package is not installed
pytest.importorskip("mcp.server")

from starlette.testclient import TestClient
from skill_seekers.mcp.server_fastmcp import mcp


class TestFastMCPHTTP:
    """Test FastMCP HTTP transport functionality."""

    def test_health_check_endpoint(self):
        """Test that health check endpoint returns correct response."""
        # Skip if mcp is None (graceful degradation for testing)
        if mcp is None:
            pytest.skip("FastMCP not available (graceful degradation)")

        # Get the SSE app
        app = mcp.sse_app()

        # Add health check endpoint
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        async def health_check(request):
            return JSONResponse(
                {
                    "status": "healthy",
                    "server": "skill-seeker-mcp",
                    "version": "2.1.1",
                    "transport": "http",
                    "endpoints": {
                        "health": "/health",
                        "sse": "/sse",
                        "messages": "/messages/",
                    },
                }
            )

        app.routes.insert(0, Route("/health", health_check, methods=["GET"]))

        # Test with TestClient
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "healthy"
            assert data["server"] == "skill-seeker-mcp"
            assert data["transport"] == "http"
            assert "endpoints" in data
            assert data["endpoints"]["health"] == "/health"
            assert data["endpoints"]["sse"] == "/sse"

    def test_sse_endpoint_exists(self):
        """Test that SSE endpoint is available."""
        # Skip if mcp is None (graceful degradation for testing)
        if mcp is None:
            pytest.skip("FastMCP not available (graceful degradation)")

        app = mcp.sse_app()

        with TestClient(app) as client:
            # SSE endpoint should exist (even if we can't fully test it without MCP client)
            # Just verify the route is registered
            routes = [route.path for route in app.routes if hasattr(route, "path")]
            # The SSE app has routes registered by FastMCP
            assert len(routes) > 0

    def test_cors_middleware(self):
        """Test that CORS middleware can be added."""
        # Skip if mcp is None (graceful degradation for testing)
        if mcp is None:
            pytest.skip("FastMCP not available (graceful degradation)")

        app = mcp.sse_app()

        from starlette.middleware.cors import CORSMiddleware

        # Should be able to add CORS middleware without error
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Verify middleware was added
        assert len(app.user_middleware) > 0


class TestArgumentParsing:
    """Test command-line argument parsing."""

    def test_parse_args_default(self):
        """Test default argument parsing (stdio mode)."""
        from skill_seekers.mcp.server_fastmcp import parse_args
        import sys

        # Save original argv
        original_argv = sys.argv

        try:
            # Test default (no arguments)
            sys.argv = ["server_fastmcp.py"]
            args = parse_args()

            assert args.http is False  # Default is stdio
            assert args.port == 8000
            assert args.host == "127.0.0.1"
            assert args.log_level == "INFO"
        finally:
            sys.argv = original_argv

    def test_parse_args_http_mode(self):
        """Test HTTP mode argument parsing."""
        from skill_seekers.mcp.server_fastmcp import parse_args
        import sys

        original_argv = sys.argv

        try:
            sys.argv = ["server_fastmcp.py", "--http", "--port", "8080", "--host", "0.0.0.0"]
            args = parse_args()

            assert args.http is True
            assert args.port == 8080
            assert args.host == "0.0.0.0"
        finally:
            sys.argv = original_argv

    def test_parse_args_log_level(self):
        """Test log level argument parsing."""
        from skill_seekers.mcp.server_fastmcp import parse_args
        import sys

        original_argv = sys.argv

        try:
            sys.argv = ["server_fastmcp.py", "--log-level", "DEBUG"]
            args = parse_args()

            assert args.log_level == "DEBUG"
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
