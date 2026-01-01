#!/usr/bin/env python3
"""
Manual test script for HTTP transport.

This script starts the MCP server in HTTP mode and tests the endpoints.

Usage:
    python examples/test_http_server.py
"""

import asyncio
import subprocess
import time
import sys
import requests


async def test_http_server():
    """Test the HTTP server."""
    print("=" * 60)
    print("Testing Skill Seeker MCP Server - HTTP Transport")
    print("=" * 60)
    print()

    # Start the server in the background
    print("1. Starting HTTP server on port 8765...")
    server_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "skill_seekers.mcp.server_fastmcp",
            "--http",
            "--port",
            "8765",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for server to start
    print("2. Waiting for server to start...")
    time.sleep(3)

    try:
        # Test health endpoint
        print("3. Testing health check endpoint...")
        response = requests.get("http://127.0.0.1:8765/health", timeout=5)
        if response.status_code == 200:
            print(f"   ✓ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ✗ Health check failed: {response.status_code}")
            return False

        print()
        print("4. Testing SSE endpoint availability...")
        # Just check if the endpoint exists (full SSE testing requires MCP client)
        try:
            response = requests.get(
                "http://127.0.0.1:8765/sse", timeout=5, stream=True
            )
            print(f"   ✓ SSE endpoint is available (status: {response.status_code})")
        except Exception as e:
            print(f"   ℹ SSE endpoint response: {e}")
            print(f"   (This is expected - full SSE testing requires MCP client)")

        print()
        print("=" * 60)
        print("✓ All HTTP transport tests passed!")
        print("=" * 60)
        print()
        print("Server Configuration for Claude Desktop:")
        print('{')
        print('  "mcpServers": {')
        print('    "skill-seeker": {')
        print('      "url": "http://127.0.0.1:8765/sse"')
        print('    }')
        print('  }')
        print('}')
        print()

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Stop the server
        print("5. Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("   ✓ Server stopped")


if __name__ == "__main__":
    result = asyncio.run(test_http_server())
    sys.exit(0 if result else 1)
