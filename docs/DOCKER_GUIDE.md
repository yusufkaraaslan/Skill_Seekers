# Docker Deployment Guide

Complete guide for deploying Skill Seekers using Docker and Docker Compose.

## Quick Start

### 1. Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- 2GB+ available RAM
- 5GB+ available disk space

```bash
# Check Docker installation
docker --version
docker-compose --version
```

### 2. Clone Repository

```bash
git clone https://github.com/your-org/skill-seekers.git
cd skill-seekers
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or your preferred editor
```

**Minimum Required:**
- `ANTHROPIC_API_KEY` - For AI enhancement features

### 4. Start Services

```bash
# Start all services (CLI + MCP server + vector DBs)
docker-compose up -d

# Or start specific services
docker-compose up -d mcp-server weaviate
```

### 5. Verify Deployment

```bash
# Check service status
docker-compose ps

# Test CLI
docker-compose run skill-seekers skill-seekers --version

# Test MCP server
curl http://localhost:8765/health
```

---

## Available Images

### 1. skill-seekers (CLI)

**Purpose:** Main CLI application for documentation scraping and skill generation

**Usage:**
```bash
# Run CLI command
docker run --rm \
  -v $(pwd)/output:/output \
  -e ANTHROPIC_API_KEY=your-key \
  skill-seekers skill-seekers scrape --config /configs/react.json

# Interactive shell
docker run -it --rm skill-seekers bash
```

**Image Size:** ~400MB
**Platforms:** linux/amd64, linux/arm64

### 2. skill-seekers-mcp (MCP Server)

**Purpose:** MCP server with 25 tools for AI assistants

**Usage:**
```bash
# HTTP mode (default)
docker run -d -p 8765:8765 \
  -e ANTHROPIC_API_KEY=your-key \
  skill-seekers-mcp

# Stdio mode
docker run -it \
  -e ANTHROPIC_API_KEY=your-key \
  skill-seekers-mcp \
  python -m skill_seekers.mcp.server_fastmcp --transport stdio
```

**Image Size:** ~450MB
**Platforms:** linux/amd64, linux/arm64
**Health Check:** http://localhost:8765/health

---

## Docker Compose Services

### Service Architecture

```
┌─────────────────────┐
│   skill-seekers     │  CLI Application
└─────────────────────┘

┌─────────────────────┐
│    mcp-server       │  MCP Server (25 tools)
│    Port: 8765       │
└─────────────────────┘

┌─────────────────────┐
│     weaviate        │  Vector DB (hybrid search)
│    Port: 8080       │
└─────────────────────┘

┌─────────────────────┐
│      qdrant         │  Vector DB (native filtering)
│    Ports: 6333/6334 │
└─────────────────────┘

┌─────────────────────┐
│      chroma         │  Vector DB (local-first)
│    Port: 8000       │
└─────────────────────┘
```

### Service Commands

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d mcp-server weaviate

# Stop all services
docker-compose down

# View logs
docker-compose logs -f mcp-server

# Restart service
docker-compose restart mcp-server

# Scale service (if supported)
docker-compose up -d --scale mcp-server=3
```

---

## Common Use Cases

### Use Case 1: Scrape Documentation

```bash
# Create skill from React documentation
docker-compose run skill-seekers \
  skill-seekers scrape --config /configs/react.json

# Output will be in ./output/react/
```

### Use Case 2: Export to Vector Databases

```bash
# Export React skill to all vector databases
docker-compose run skill-seekers bash -c "
  skill-seekers scrape --config /configs/react.json &&
  python -c '
import sys
from pathlib import Path
sys.path.insert(0, \"/app/src\")
from skill_seekers.cli.adaptors import get_adaptor

for target in [\"weaviate\", \"chroma\", \"faiss\", \"qdrant\"]:
    adaptor = get_adaptor(target)
    adaptor.package(Path(\"/output/react\"), Path(\"/output\"))
    print(f\"✅ Exported to {target}\")
  '
"
```

### Use Case 3: Run Quality Analysis

```bash
# Generate quality report for a skill
docker-compose run skill-seekers bash -c "
  python3 <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, '/app/src')
from skill_seekers.cli.quality_metrics import QualityAnalyzer

analyzer = QualityAnalyzer(Path('/output/react'))
report = analyzer.generate_report()
print(analyzer.format_report(report))
EOF
"
```

### Use Case 4: MCP Server Integration

```bash
# Start MCP server
docker-compose up -d mcp-server

# Configure Claude Desktop
# Add to ~/Library/Application Support/Claude/claude_desktop_config.json:
{
  "mcpServers": {
    "skill-seekers": {
      "url": "http://localhost:8765/sse"
    }
  }
}
```

---

## Volume Management

### Default Volumes

| Volume | Path | Purpose |
|--------|------|---------|
| `./data` | `/data` | Persistent data (cache, logs) |
| `./configs` | `/configs` | Configuration files (read-only) |
| `./output` | `/output` | Generated skills and exports |
| `weaviate-data` | N/A | Weaviate database storage |
| `qdrant-data` | N/A | Qdrant database storage |
| `chroma-data` | N/A | Chroma database storage |

### Backup Volumes

```bash
# Backup vector database data
docker run --rm -v skill-seekers_weaviate-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/weaviate-backup.tar.gz -C /data .

# Restore from backup
docker run --rm -v skill-seekers_weaviate-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/weaviate-backup.tar.gz -C /data
```

### Clean Up Volumes

```bash
# Remove all volumes (WARNING: deletes all data)
docker-compose down -v

# Remove specific volume
docker volume rm skill-seekers_weaviate-data
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude AI API key | `sk-ant-...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Gemini API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `GITHUB_TOKEN` | GitHub API token | - |
| `MCP_TRANSPORT` | MCP transport mode | `http` |
| `MCP_PORT` | MCP server port | `8765` |

### Setting Variables

**Option 1: .env file (recommended)**
```bash
cp .env.example .env
# Edit .env with your keys
```

**Option 2: Export in shell**
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key
docker-compose up -d
```

**Option 3: Inline**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key docker-compose up -d
```

---

## Building Images Locally

### Build CLI Image

```bash
docker build -t skill-seekers:local -f Dockerfile .
```

### Build MCP Server Image

```bash
docker build -t skill-seekers-mcp:local -f Dockerfile.mcp .
```

### Build with Custom Base Image

```bash
# Use slim base (smaller)
docker build -t skill-seekers:slim \
  --build-arg BASE_IMAGE=python:3.12-slim \
  -f Dockerfile .

# Use alpine base (smallest)
docker build -t skill-seekers:alpine \
  --build-arg BASE_IMAGE=python:3.12-alpine \
  -f Dockerfile .
```

---

## Troubleshooting

### Issue: MCP Server Won't Start

**Symptoms:**
- Container exits immediately
- Health check fails

**Solutions:**
```bash
# Check logs
docker-compose logs mcp-server

# Verify port is available
lsof -i :8765

# Test MCP package installation
docker-compose run mcp-server python -c "import mcp; print('OK')"
```

### Issue: Permission Denied

**Symptoms:**
- Cannot write to /output
- Cannot access /configs

**Solutions:**
```bash
# Fix permissions
chmod -R 777 data/ output/

# Or use specific user ID
docker-compose run -u $(id -u):$(id -g) skill-seekers ...
```

### Issue: Out of Memory

**Symptoms:**
- Container killed
- OOMKilled in `docker-compose ps`

**Solutions:**
```bash
# Increase Docker memory limit
# Edit docker-compose.yml, add:
services:
  skill-seekers:
    mem_limit: 4g
    memswap_limit: 4g

# Or use streaming for large docs
docker-compose run skill-seekers \
  skill-seekers scrape --config /configs/react.json --streaming
```

### Issue: Vector Database Connection Failed

**Symptoms:**
- Cannot connect to Weaviate/Qdrant/Chroma
- Connection refused errors

**Solutions:**
```bash
# Check if services are running
docker-compose ps

# Test connectivity
docker-compose exec skill-seekers curl http://weaviate:8080
docker-compose exec skill-seekers curl http://qdrant:6333
docker-compose exec skill-seekers curl http://chroma:8000

# Restart services
docker-compose restart weaviate qdrant chroma
```

### Issue: Slow Performance

**Symptoms:**
- Long scraping times
- Slow container startup

**Solutions:**
```bash
# Use smaller image
docker pull skill-seekers:slim

# Enable BuildKit cache
export DOCKER_BUILDKIT=1
docker build -t skill-seekers:local .

# Increase CPU allocation
docker-compose up -d --scale skill-seekers=1 --cpu-shares=2048
```

---

## Production Deployment

### Security Hardening

1. **Use secrets management**
```bash
# Docker secrets (Swarm mode)
echo "sk-ant-your-key" | docker secret create anthropic_key -

# Kubernetes secrets
kubectl create secret generic skill-seekers-secrets \
  --from-literal=anthropic-api-key=sk-ant-your-key
```

2. **Run as non-root**
```dockerfile
# Already configured in Dockerfile
USER skillseeker  # UID 1000
```

3. **Read-only filesystems**
```yaml
# docker-compose.yml
services:
  mcp-server:
    read_only: true
    tmpfs:
      - /tmp
```

4. **Resource limits**
```yaml
services:
  mcp-server:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Monitoring

1. **Health checks**
```bash
# Check all services
docker-compose ps

# Detailed health status
docker inspect --format='{{.State.Health.Status}}' skill-seekers-mcp
```

2. **Logs**
```bash
# Stream logs
docker-compose logs -f --tail=100

# Export logs
docker-compose logs > skill-seekers-logs.txt
```

3. **Metrics**
```bash
# Resource usage
docker stats

# Container inspect
docker-compose exec mcp-server ps aux
docker-compose exec mcp-server df -h
```

### Scaling

1. **Horizontal scaling**
```bash
# Scale MCP servers
docker-compose up -d --scale mcp-server=3

# Use load balancer
# Add nginx/haproxy in docker-compose.yml
```

2. **Vertical scaling**
```yaml
# Increase resources
services:
  mcp-server:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
```

---

## Best Practices

### 1. Use Multi-Stage Builds
✅ Already implemented in Dockerfile
- Builder stage for dependencies
- Runtime stage for production

### 2. Minimize Image Size
- Use slim base images
- Clean up apt cache
- Remove unnecessary files via .dockerignore

### 3. Security
- Run as non-root user (UID 1000)
- Use secrets for sensitive data
- Keep images updated

### 4. Persistence
- Use named volumes for databases
- Mount ./output for generated skills
- Regular backups of vector DB data

### 5. Monitoring
- Enable health checks
- Stream logs to external service
- Monitor resource usage

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Skill Seekers Documentation](https://skillseekersweb.com/)
- [MCP Server Setup](docs/MCP_SETUP.md)
- [Vector Database Integration](docs/strategy/WEEK2_COMPLETE.md)

---

**Last Updated:** February 7, 2026
**Docker Version:** 20.10+
**Compose Version:** 2.0+
