#!/bin/bash
# HTTP Transport Examples for Skill Seeker MCP Server
#
# This script shows various ways to start the server with HTTP transport.
# DO NOT run this script directly - copy the commands you need.

# =============================================================================
# BASIC USAGE
# =============================================================================

# Default stdio transport (backward compatible)
python -m skill_seekers.mcp.server_fastmcp

# HTTP transport on default port 8000
python -m skill_seekers.mcp.server_fastmcp --http

# =============================================================================
# CUSTOM PORT
# =============================================================================

# HTTP transport on port 3000
python -m skill_seekers.mcp.server_fastmcp --http --port 3000

# HTTP transport on port 8080
python -m skill_seekers.mcp.server_fastmcp --http --port 8080

# =============================================================================
# CUSTOM HOST
# =============================================================================

# Listen on all interfaces (⚠️ use with caution in production!)
python -m skill_seekers.mcp.server_fastmcp --http --host 0.0.0.0

# Listen on specific interface
python -m skill_seekers.mcp.server_fastmcp --http --host 192.168.1.100

# =============================================================================
# LOGGING
# =============================================================================

# Debug logging
python -m skill_seekers.mcp.server_fastmcp --http --log-level DEBUG

# Warning level only
python -m skill_seekers.mcp.server_fastmcp --http --log-level WARNING

# Error level only
python -m skill_seekers.mcp.server_fastmcp --http --log-level ERROR

# =============================================================================
# COMBINED OPTIONS
# =============================================================================

# HTTP on port 8080 with debug logging
python -m skill_seekers.mcp.server_fastmcp --http --port 8080 --log-level DEBUG

# HTTP on all interfaces with custom port and warning level
python -m skill_seekers.mcp.server_fastmcp --http --host 0.0.0.0 --port 9000 --log-level WARNING

# =============================================================================
# TESTING
# =============================================================================

# Start server in background and test health endpoint
python -m skill_seekers.mcp.server_fastmcp --http --port 8765 &
SERVER_PID=$!
sleep 2
curl http://localhost:8765/health | python -m json.tool
kill $SERVER_PID

# =============================================================================
# CLAUDE DESKTOP CONFIGURATION
# =============================================================================

# For stdio transport (default):
# {
#   "mcpServers": {
#     "skill-seeker": {
#       "command": "python",
#       "args": ["-m", "skill_seekers.mcp.server_fastmcp"]
#     }
#   }
# }

# For HTTP transport on port 8000:
# {
#   "mcpServers": {
#     "skill-seeker": {
#       "url": "http://localhost:8000/sse"
#     }
#   }
# }

# For HTTP transport on custom port 8080:
# {
#   "mcpServers": {
#     "skill-seeker": {
#       "url": "http://localhost:8080/sse"
#     }
#   }
# }

# =============================================================================
# TROUBLESHOOTING
# =============================================================================

# Check if port is already in use
lsof -i :8000

# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Test health endpoint
curl http://localhost:8000/health

# Test with verbose output
curl -v http://localhost:8000/health

# Follow server logs
python -m skill_seekers.mcp.server_fastmcp --http --log-level DEBUG 2>&1 | tee server.log
