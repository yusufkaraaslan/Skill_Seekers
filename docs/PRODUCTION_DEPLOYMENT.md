# Production Deployment Guide

Complete guide for deploying Skill Seekers in production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Deployment Options](#deployment-options)
- [Monitoring & Observability](#monitoring--observability)
- [Security](#security)
- [Scaling](#scaling)
- [Backup & Disaster Recovery](#backup--disaster-recovery)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB
- Python: 3.10+

**Recommended (for production):**
- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 50+ GB SSD
- Python: 3.12+

### Dependencies

**Required:**
```bash
# System packages (Ubuntu/Debian)
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip \
  git curl wget build-essential libssl-dev

# System packages (RHEL/CentOS)
sudo yum install -y python312 python312-devel git curl wget \
  gcc gcc-c++ openssl-devel
```

**Optional (for specific features):**
```bash
# OCR support (PDF scraping)
sudo apt install -y tesseract-ocr

# Cloud storage
# (Install provider-specific SDKs via pip)

# Embedding generation
# (GPU support requires CUDA)
```

## Installation

### 1. Production Installation

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash skillseekers
sudo su - skillseekers

# Create virtual environment
python3.12 -m venv /opt/skillseekers/venv
source /opt/skillseekers/venv/bin/activate

# Install package
pip install --upgrade pip
pip install skill-seekers[all]

# Verify installation
skill-seekers --version
```

### 2. Configuration Directory

```bash
# Create config directory
mkdir -p ~/.config/skill-seekers/{configs,output,logs,cache}

# Set permissions
chmod 700 ~/.config/skill-seekers
```

### 3. Environment Variables

Create `/opt/skillseekers/.env`:

```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
OPENAI_API_KEY=sk-...
VOYAGE_API_KEY=...

# GitHub Tokens (use skill-seekers config --github for multiple)
GITHUB_TOKEN=ghp_...

# Cloud Storage (optional)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcs-key.json
AZURE_STORAGE_CONNECTION_STRING=...

# MCP Server
MCP_TRANSPORT=http
MCP_PORT=8765

# Sync Monitoring (optional)
SYNC_WEBHOOK_URL=https://...
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/skillseekers/app.log
```

**Security Note:** Never commit `.env` files to version control!

```bash
# Secure the env file
chmod 600 /opt/skillseekers/.env
```

## Configuration

### 1. GitHub Configuration

Use the interactive configuration wizard:

```bash
skill-seekers config --github
```

This will:
- Add GitHub personal access tokens
- Configure rate limit strategies
- Test token validity
- Support multiple profiles (work, personal, etc.)

### 2. API Keys Configuration

```bash
skill-seekers config --api-keys
```

Configure:
- Claude API (Anthropic)
- Gemini API (Google)
- OpenAI API
- Voyage AI (embeddings)

### 3. Connection Testing

```bash
skill-seekers config --test
```

Verifies:
- ✅ GitHub token(s) validity and rate limits
- ✅ Claude API connectivity
- ✅ Gemini API connectivity
- ✅ OpenAI API connectivity
- ✅ Cloud storage access (if configured)

## Deployment Options

### Option 1: Systemd Service (Recommended)

Create `/etc/systemd/system/skillseekers-mcp.service`:

```ini
[Unit]
Description=Skill Seekers MCP Server
After=network.target

[Service]
Type=simple
User=skillseekers
Group=skillseekers
WorkingDirectory=/opt/skillseekers
EnvironmentFile=/opt/skillseekers/.env
ExecStart=/opt/skillseekers/venv/bin/python -m skill_seekers.mcp.server_fastmcp --transport http --port 8765
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=skillseekers-mcp

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/skillseekers /var/log/skillseekers

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable skillseekers-mcp
sudo systemctl start skillseekers-mcp
sudo systemctl status skillseekers-mcp
```

### Option 2: Docker Deployment

See [Docker Deployment Guide](./DOCKER_DEPLOYMENT.md) for detailed instructions.

**Quick Start:**

```bash
# Build image
docker build -t skillseekers:latest .

# Run container
docker run -d \
  --name skillseekers-mcp \
  -p 8765:8765 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -v /opt/skillseekers/data:/app/data \
  --restart unless-stopped \
  skillseekers:latest
```

### Option 3: Kubernetes Deployment

See [Kubernetes Deployment Guide](./KUBERNETES_DEPLOYMENT.md) for detailed instructions.

**Quick Start:**

```bash
# Install with Helm
helm install skillseekers ./helm/skillseekers \
  --namespace skillseekers \
  --create-namespace \
  --set secrets.anthropicApiKey=$ANTHROPIC_API_KEY \
  --set secrets.githubToken=$GITHUB_TOKEN
```

### Option 4: Docker Compose

See [Docker Compose Guide](./DOCKER_COMPOSE.md) for multi-service deployment.

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Monitoring & Observability

### 1. Health Checks

**MCP Server Health:**

```bash
# HTTP transport
curl http://localhost:8765/health

# Expected response:
{
  "status": "healthy",
  "version": "2.9.0",
  "uptime": 3600,
  "tools": 25
}
```

### 2. Logging

**Configure structured logging:**

```python
# config/logging.yaml
version: 1
formatters:
  json:
    format: '{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}'
handlers:
  file:
    class: logging.handlers.RotatingFileHandler
    filename: /var/log/skillseekers/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
    formatter: json
loggers:
  skill_seekers:
    level: INFO
    handlers: [file]
```

**Log aggregation options:**
- **ELK Stack:** Elasticsearch + Logstash + Kibana
- **Grafana Loki:** Lightweight log aggregation
- **CloudWatch Logs:** For AWS deployments
- **Stackdriver:** For GCP deployments

### 3. Metrics

**Prometheus metrics endpoint:**

```bash
# Add to MCP server
from prometheus_client import start_http_server, Counter, Histogram

# Metrics
scraping_requests = Counter('scraping_requests_total', 'Total scraping requests')
scraping_duration = Histogram('scraping_duration_seconds', 'Scraping duration')

# Start metrics server
start_http_server(9090)
```

**Key metrics to monitor:**
- Request rate
- Response time (p50, p95, p99)
- Error rate
- Memory usage
- CPU usage
- Disk I/O
- GitHub API rate limit remaining
- Claude API token usage

### 4. Alerting

**Example Prometheus alert rules:**

```yaml
groups:
  - name: skillseekers
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes > 2e9  # 2GB
        for: 10m
        annotations:
          summary: "Memory usage above 2GB"

      - alert: GitHubRateLimitLow
        expr: github_rate_limit_remaining < 100
        for: 1m
        annotations:
          summary: "GitHub rate limit low"
```

## Security

### 1. API Key Management

**Best Practices:**

✅ **DO:**
- Store keys in environment variables or secret managers
- Use different keys for dev/staging/prod
- Rotate keys regularly (quarterly minimum)
- Use least-privilege IAM roles for cloud services
- Monitor key usage for anomalies

❌ **DON'T:**
- Commit keys to version control
- Share keys via email/Slack
- Use production keys in development
- Grant overly broad permissions

**Recommended Secret Managers:**
- **Kubernetes Secrets** (for K8s deployments)
- **AWS Secrets Manager** (for AWS)
- **Google Secret Manager** (for GCP)
- **Azure Key Vault** (for Azure)
- **HashiCorp Vault** (cloud-agnostic)

### 2. Network Security

**Firewall Rules:**

```bash
# Allow only necessary ports
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8765/tcp  # MCP server (if public)
sudo ufw deny incoming
sudo ufw allow outgoing
```

**Reverse Proxy (Nginx):**

```nginx
# /etc/nginx/sites-available/skillseekers
server {
    listen 80;
    server_name api.skillseekers.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.skillseekers.example.com;

    ssl_certificate /etc/letsencrypt/live/api.skillseekers.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.skillseekers.example.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://localhost:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 3. TLS/SSL

**Let's Encrypt (free certificates):**

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.skillseekers.example.com

# Auto-renewal (cron)
0 12 * * * /usr/bin/certbot renew --quiet
```

### 4. Authentication & Authorization

**API Key Authentication (optional):**

```python
# Add to MCP server
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    if token != os.getenv("API_SECRET_KEY"):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token
```

## Scaling

### 1. Vertical Scaling

**Increase resources:**

```yaml
# Kubernetes resource limits
resources:
  requests:
    cpu: "2"
    memory: "4Gi"
  limits:
    cpu: "4"
    memory: "8Gi"
```

### 2. Horizontal Scaling

**Deploy multiple instances:**

```bash
# Kubernetes HPA (Horizontal Pod Autoscaler)
kubectl autoscale deployment skillseekers-mcp \
  --cpu-percent=70 \
  --min=2 \
  --max=10
```

**Load Balancing:**

```nginx
# Nginx load balancer
upstream skillseekers {
    least_conn;
    server 10.0.0.1:8765;
    server 10.0.0.2:8765;
    server 10.0.0.3:8765;
}

server {
    listen 80;
    location / {
        proxy_pass http://skillseekers;
    }
}
```

### 3. Database/Storage Scaling

**Distributed caching:**

```python
# Redis for distributed cache
import redis

cache = redis.Redis(host='redis.example.com', port=6379, db=0)
```

**Object storage:**
- Use S3/GCS/Azure Blob for skill packages
- Enable CDN for static assets
- Use read replicas for databases

### 4. Rate Limit Management

**Multiple GitHub tokens:**

```bash
# Configure multiple profiles
skill-seekers config --github

# Automatic token rotation on rate limit
# (handled by rate_limit_handler.py)
```

## Backup & Disaster Recovery

### 1. Data Backup

**What to backup:**
- Configuration files (`~/.config/skill-seekers/`)
- Generated skills (`output/`)
- Database/cache (if applicable)
- Logs (for forensics)

**Backup script:**

```bash
#!/bin/bash
# /opt/skillseekers/scripts/backup.sh

BACKUP_DIR="/backups/skillseekers"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup
tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" \
  ~/.config/skill-seekers \
  /opt/skillseekers/output \
  /opt/skillseekers/.env

# Retain last 30 days
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" \
  s3://backups/skillseekers/
```

**Schedule backups:**

```bash
# Crontab
0 2 * * * /opt/skillseekers/scripts/backup.sh
```

### 2. Disaster Recovery Plan

**Recovery steps:**

1. **Provision new infrastructure**
   ```bash
   # Deploy from backup
   terraform apply
   ```

2. **Restore configuration**
   ```bash
   tar -xzf backup_20250207.tar.gz -C /
   ```

3. **Verify services**
   ```bash
   skill-seekers config --test
   systemctl status skillseekers-mcp
   ```

4. **Test functionality**
   ```bash
   skill-seekers scrape --config configs/test.json --max-pages 10
   ```

**RTO/RPO targets:**
- **RTO (Recovery Time Objective):** < 2 hours
- **RPO (Recovery Point Objective):** < 24 hours

## Troubleshooting

### Common Issues

#### 1. High Memory Usage

**Symptoms:**
- OOM kills
- Slow performance
- Swapping

**Solutions:**

```bash
# Check memory usage
ps aux --sort=-%mem | head -10

# Reduce batch size
skill-seekers scrape --config config.json --batch-size 10

# Enable memory limits
docker run --memory=4g skillseekers:latest
```

#### 2. GitHub Rate Limits

**Symptoms:**
- `403 Forbidden` errors
- "API rate limit exceeded" messages

**Solutions:**

```bash
# Check rate limit
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit

# Add more tokens
skill-seekers config --github

# Use rate limit strategy
# (automatic with multi-token config)
```

#### 3. Slow Scraping

**Symptoms:**
- Long scraping times
- Timeouts

**Solutions:**

```bash
# Enable async scraping (2-3x faster)
skill-seekers scrape --config config.json --async

# Increase concurrency
# (adjust in config: "concurrency": 10)

# Use caching
skill-seekers scrape --config config.json --use-cache
```

#### 4. API Errors

**Symptoms:**
- `401 Unauthorized`
- `429 Too Many Requests`

**Solutions:**

```bash
# Verify API keys
skill-seekers config --test

# Check API key validity
# Claude API: https://console.anthropic.com/
# OpenAI: https://platform.openai.com/api-keys
# Google: https://console.cloud.google.com/apis/credentials

# Rotate keys if compromised
```

#### 5. Service Won't Start

**Symptoms:**
- systemd service fails
- Container exits immediately

**Solutions:**

```bash
# Check logs
journalctl -u skillseekers-mcp -n 100

# Or for Docker
docker logs skillseekers-mcp

# Common causes:
# - Missing environment variables
# - Port already in use
# - Permission issues

# Verify config
skill-seekers config --show
```

### Debug Mode

Enable detailed logging:

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Run with verbose output
skill-seekers scrape --config config.json --verbose
```

### Getting Help

**Community Support:**
- GitHub Issues: https://github.com/yusufkaraaslan/Skill_Seekers/issues
- Documentation: https://skillseekersweb.com/

**Log Collection:**

```bash
# Collect diagnostic info
tar -czf skillseekers-debug.tar.gz \
  /var/log/skillseekers/ \
  ~/.config/skill-seekers/configs/ \
  /opt/skillseekers/.env
```

## Performance Tuning

### 1. Scraping Performance

**Optimization techniques:**

```python
# Enable async scraping
"async_scraping": true,
"concurrency": 20,  # Adjust based on resources

# Optimize selectors
"selectors": {
    "main_content": "article",  # More specific = faster
    "code_blocks": "pre code"
}

# Enable caching
"use_cache": true,
"cache_ttl": 86400  # 24 hours
```

### 2. Embedding Performance

**GPU acceleration (if available):**

```python
# Use GPU for sentence-transformers
pip install sentence-transformers[gpu]

# Configure
export CUDA_VISIBLE_DEVICES=0
```

**Batch processing:**

```python
# Generate embeddings in batches
generator.generate_batch(texts, batch_size=32)
```

### 3. Storage Performance

**Use SSD for:**
- SQLite databases
- Cache directories
- Log files

**Use object storage for:**
- Skill packages
- Backup archives
- Large datasets

## Next Steps

1. **Review** deployment option that fits your infrastructure
2. **Configure** monitoring and alerting
3. **Set up** backups and disaster recovery
4. **Test** failover procedures
5. **Document** your specific deployment
6. **Train** your team on operations

---

**Need help?** See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) or open an issue on GitHub.
