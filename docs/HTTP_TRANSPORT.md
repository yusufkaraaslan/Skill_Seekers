# HTTP Transport for FastMCP Server

The Skill Seeker MCP server now supports both **stdio** (default) and **HTTP** transports, giving you flexibility in how you connect Claude Desktop or other MCP clients.

## Quick Start

### Stdio Transport (Default)

```bash
# Traditional stdio transport (backward compatible)
python -m skill_seekers.mcp.server_fastmcp
```

### HTTP Transport (New!)

```bash
# HTTP transport on default port 8000
python -m skill_seekers.mcp.server_fastmcp --http

# HTTP transport on custom port
python -m skill_seekers.mcp.server_fastmcp --http --port 8080

# HTTP transport with debug logging
python -m skill_seekers.mcp.server_fastmcp --http --log-level DEBUG
```

## Why Use HTTP Transport?

### Advantages
- **Web-based clients**: Connect from browser-based MCP clients
- **Cross-origin requests**: Built-in CORS support for web applications
- **Health monitoring**: Dedicated `/health` endpoint for service monitoring
- **Multiple connections**: Support multiple simultaneous client connections
- **Remote access**: Can be accessed over network (use with caution!)
- **Debugging**: Easier to debug with browser developer tools

### When to Use Stdio
- **Claude Desktop integration**: Default and recommended for desktop clients
- **Process isolation**: Each client gets isolated server process
- **Security**: More secure for local-only access
- **Simplicity**: No network configuration needed

## Configuration

### Claude Desktop Configuration

#### Stdio (Default)
```json
{
  "mcpServers": {
    "skill-seeker": {
      "command": "python",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp"]
    }
  }
}
```

#### HTTP (Alternative)
```json
{
  "mcpServers": {
    "skill-seeker": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## Endpoints

When running in HTTP mode, the server exposes the following endpoints:

### Health Check
**Endpoint:** `GET /health`

Returns server health status and metadata.

**Example:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "server": "skill-seeker-mcp",
  "version": "2.1.1",
  "transport": "http",
  "endpoints": {
    "health": "/health",
    "sse": "/sse",
    "messages": "/messages/"
  }
}
```

### SSE Endpoint
**Endpoint:** `GET /sse`

Server-Sent Events endpoint for MCP communication. This is the main endpoint used by MCP clients.

**Usage:**
- Connect with MCP-compatible client
- Supports bidirectional communication via SSE

### Messages Endpoint
**Endpoint:** `POST /messages/`

Handles tool invocation and message passing from MCP clients.

## Command-Line Options

```bash
python -m skill_seekers.mcp.server_fastmcp --help
```

### Options

- `--http`: Enable HTTP transport (default: stdio)
- `--port PORT`: HTTP server port (default: 8000)
- `--host HOST`: HTTP server host (default: 127.0.0.1)
- `--log-level LEVEL`: Logging level (choices: DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Examples

### Basic HTTP Server
```bash
# Start on default port 8000
python -m skill_seekers.mcp.server_fastmcp --http
```

### Custom Port
```bash
# Start on port 3000
python -m skill_seekers.mcp.server_fastmcp --http --port 3000
```

### Allow External Connections
```bash
# Listen on all interfaces (⚠️ use with caution!)
python -m skill_seekers.mcp.server_fastmcp --http --host 0.0.0.0 --port 8000
```

### Debug Mode
```bash
# Enable debug logging
python -m skill_seekers.mcp.server_fastmcp --http --log-level DEBUG
```

## Security Considerations

### Local Development
- Default binding to `127.0.0.1` ensures localhost-only access
- Safe for local development and testing

### Remote Access
- **⚠️ Warning**: Binding to `0.0.0.0` allows network access
- Implement authentication/authorization for production
- Consider using reverse proxy (nginx, Apache) with SSL/TLS
- Use firewall rules to restrict access
- Consider VPN for remote team access

### CORS
- HTTP transport includes CORS middleware
- Configured to allow all origins in development
- Customize CORS settings for production in `server_fastmcp.py`

## Testing

### Automated Tests
```bash
# Run HTTP transport tests
pytest tests/test_server_fastmcp_http.py -v
```

### Manual Testing
```bash
# Run manual test script
python examples/test_http_server.py
```

### Health Check Test
```bash
# Start server
python -m skill_seekers.mcp.server_fastmcp --http &

# Test health endpoint
curl http://localhost:8000/health

# Stop server
killall python
```

## Troubleshooting

### Port Already in Use
```
Error: [Errno 48] Address already in use
```

**Solution:** Use a different port
```bash
python -m skill_seekers.mcp.server_fastmcp --http --port 8001
```

### Cannot Connect from Browser
- Ensure server is running: `curl http://localhost:8000/health`
- Check firewall settings
- Verify port is not blocked
- For remote access, ensure using correct IP (not 127.0.0.1)

### uvicorn Not Installed
```
Error: uvicorn package not installed
```

**Solution:** Install uvicorn
```bash
pip install uvicorn
```

## Architecture

### Transport Flow

#### Stdio Mode
```
Claude Desktop → stdin/stdout → MCP Server → Tools
```

#### HTTP Mode
```
Claude Desktop/Browser → HTTP/SSE → MCP Server → Tools
                        ↓
                   Health Check
```

### Components
- **FastMCP**: Underlying MCP server framework
- **Starlette**: ASGI web framework for HTTP
- **uvicorn**: ASGI server for production
- **SSE**: Server-Sent Events for real-time communication

## Performance

### Benchmarks (Local Testing)
- **Startup time**: ~200ms (HTTP), ~100ms (stdio)
- **Health check latency**: ~5-10ms
- **Tool invocation overhead**: ~20-50ms (HTTP), ~10-20ms (stdio)

### Recommendations
- **Single user**: Use stdio (simpler, faster)
- **Multiple users**: Use HTTP (connection pooling)
- **Production**: Use HTTP with reverse proxy
- **Development**: Use stdio for simplicity

## Migration Guide

### From Stdio to HTTP

1. **Update server startup:**
   ```bash
   # Before
   python -m skill_seekers.mcp.server_fastmcp

   # After
   python -m skill_seekers.mcp.server_fastmcp --http
   ```

2. **Update Claude Desktop config:**
   ```json
   {
     "mcpServers": {
       "skill-seeker": {
         "url": "http://localhost:8000/sse"
       }
     }
   }
   ```

3. **Restart Claude Desktop**

### Backward Compatibility
- Stdio remains the default transport
- No breaking changes to existing configurations
- HTTP is opt-in via `--http` flag

## Related Documentation

- [MCP Setup Guide](MCP_SETUP.md)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Skill Seeker Documentation](../README.md)

## Support

For issues or questions:
- GitHub Issues: https://github.com/yusufkaraaslan/Skill_Seekers/issues
- MCP Documentation: https://modelcontextprotocol.io/

## Changelog

### Version 2.1.1+
- ✅ Added HTTP transport support
- ✅ Added health check endpoint
- ✅ Added CORS middleware
- ✅ Added command-line argument parsing
- ✅ Maintained backward compatibility with stdio
