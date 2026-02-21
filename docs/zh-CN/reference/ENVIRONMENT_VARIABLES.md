# Environment Variables Reference - Skill Seekers

> **Version:** 3.1.0  
> **Last Updated:** 2026-02-16  
> **Complete environment variable reference**

---

## Table of Contents

- [Overview](#overview)
- [API Keys](#api-keys)
- [Platform Configuration](#platform-configuration)
- [Paths and Directories](#paths-and-directories)
- [Scraping Behavior](#scraping-behavior)
- [Enhancement Settings](#enhancement-settings)
- [GitHub Configuration](#github-configuration)
- [Vector Database Settings](#vector-database-settings)
- [Debug and Development](#debug-and-development)
- [MCP Server Settings](#mcp-server-settings)
- [Examples](#examples)

---

## Overview

Skill Seekers uses environment variables for:
- API authentication (Claude, Gemini, OpenAI, GitHub)
- Configuration paths
- Output directories
- Behavior customization
- Debug settings

Variables are read at runtime and override default settings.

---

## API Keys

### ANTHROPIC_API_KEY

**Purpose:** Claude AI API access for enhancement and upload.

**Format:** `sk-ant-api03-...`

**Used by:**
- `skill-seekers enhance` (API mode)
- `skill-seekers upload` (Claude target)
- AI enhancement features

**Example:**
```bash
export ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Alternative:** Use `--api-key` flag per command.

---

### GOOGLE_API_KEY

**Purpose:** Google Gemini API access for upload.

**Format:** `AIza...`

**Used by:**
- `skill-seekers upload` (Gemini target)

**Example:**
```bash
export GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### OPENAI_API_KEY

**Purpose:** OpenAI API access for upload and embeddings.

**Format:** `sk-...`

**Used by:**
- `skill-seekers upload` (OpenAI target)
- Embedding generation for vector DBs

**Example:**
```bash
export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### GITHUB_TOKEN

**Purpose:** GitHub API authentication for higher rate limits.

**Format:** `ghp_...` (personal access token) or `github_pat_...` (fine-grained)

**Used by:**
- `skill-seekers github`
- `skill-seekers unified` (GitHub sources)
- `skill-seekers analyze` (GitHub repos)

**Benefits:**
- 5000 requests/hour vs 60 for unauthenticated
- Access to private repositories
- Higher GraphQL API limits

**Example:**
```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Create token:** https://github.com/settings/tokens

---

## Platform Configuration

### ANTHROPIC_BASE_URL

**Purpose:** Custom Claude API endpoint.

**Default:** `https://api.anthropic.com`

**Use case:** Proxy servers, enterprise deployments, regional endpoints.

**Example:**
```bash
export ANTHROPIC_BASE_URL=https://custom-api.example.com
```

---

## Paths and Directories

### SKILL_SEEKERS_HOME

**Purpose:** Base directory for Skill Seekers data.

**Default:**
- Linux/macOS: `~/.config/skill-seekers/`
- Windows: `%APPDATA%\skill-seekers\`

**Used for:**
- Configuration files
- Workflow presets
- Cache data
- Checkpoints

**Example:**
```bash
export SKILL_SEEKERS_HOME=/opt/skill-seekers
```

---

### SKILL_SEEKERS_OUTPUT

**Purpose:** Default output directory for skills.

**Default:** `./output/`

**Used by:**
- All scraping commands
- Package output
- Skill generation

**Example:**
```bash
export SKILL_SEEKERS_OUTPUT=/var/skills/output
```

---

### SKILL_SEEKERS_CONFIG_DIR

**Purpose:** Directory containing preset configs.

**Default:** `configs/` (relative to working directory)

**Example:**
```bash
export SKILL_SEEKERS_CONFIG_DIR=/etc/skill-seekers/configs
```

---

## Scraping Behavior

### SKILL_SEEKERS_RATE_LIMIT

**Purpose:** Default rate limit for HTTP requests.

**Default:** `0.5` (seconds)

**Unit:** Seconds between requests

**Example:**
```bash
# More aggressive (faster)
export SKILL_SEEKERS_RATE_LIMIT=0.2

# More conservative (slower)
export SKILL_SEEKERS_RATE_LIMIT=1.0
```

**Override:** Use `--rate-limit` flag per command.

---

### SKILL_SEEKERS_MAX_PAGES

**Purpose:** Default maximum pages to scrape.

**Default:** `500`

**Example:**
```bash
export SKILL_SEEKERS_MAX_PAGES=1000
```

**Override:** Use `--max-pages` flag or config file.

---

### SKILL_SEEKERS_WORKERS

**Purpose:** Default number of parallel workers.

**Default:** `1`

**Maximum:** `10`

**Example:**
```bash
export SKILL_SEEKERS_WORKERS=4
```

**Override:** Use `--workers` flag.

---

### SKILL_SEEKERS_TIMEOUT

**Purpose:** HTTP request timeout.

**Default:** `30` (seconds)

**Example:**
```bash
# For slow servers
export SKILL_SEEKERS_TIMEOUT=60
```

---

### SKILL_SEEKERS_USER_AGENT

**Purpose:** Custom User-Agent header.

**Default:** `Skill-Seekers/3.1.0`

**Example:**
```bash
export SKILL_SEEKERS_USER_AGENT="MyBot/1.0 (contact@example.com)"
```

---

## Enhancement Settings

### SKILL_SEEKER_AGENT

**Purpose:** Default local coding agent for enhancement.

**Default:** `claude`

**Options:** `claude`, `cursor`, `windsurf`, `cline`, `continue`

**Used by:**
- `skill-seekers enhance`

**Example:**
```bash
export SKILL_SEEKER_AGENT=cursor
```

---

### SKILL_SEEKERS_ENHANCE_TIMEOUT

**Purpose:** Timeout for AI enhancement operations.

**Default:** `600` (seconds = 10 minutes)

**Example:**
```bash
# For large skills
export SKILL_SEEKERS_ENHANCE_TIMEOUT=1200
```

**Override:** Use `--timeout` flag.

---

### ANTHROPIC_MODEL

**Purpose:** Claude model for API enhancement.

**Default:** `claude-3-5-sonnet-20241022`

**Options:**
- `claude-3-5-sonnet-20241022` (recommended)
- `claude-3-opus-20240229` (highest quality, more expensive)
- `claude-3-haiku-20240307` (fastest, cheapest)

**Example:**
```bash
export ANTHROPIC_MODEL=claude-3-opus-20240229
```

---

## GitHub Configuration

### GITHUB_API_URL

**Purpose:** Custom GitHub API endpoint.

**Default:** `https://api.github.com`

**Use case:** GitHub Enterprise Server.

**Example:**
```bash
export GITHUB_API_URL=https://github.company.com/api/v3
```

---

### GITHUB_ENTERPRISE_TOKEN

**Purpose:** Separate token for GitHub Enterprise.

**Use case:** Different tokens for github.com vs enterprise.

**Example:**
```bash
export GITHUB_TOKEN=ghp_...           # github.com
export GITHUB_ENTERPRISE_TOKEN=...   # enterprise
```

---

## Vector Database Settings

### CHROMA_URL

**Purpose:** ChromaDB server URL.

**Default:** `http://localhost:8000`

**Used by:**
- `skill-seekers upload --target chroma`
- `export_to_chroma` MCP tool

**Example:**
```bash
export CHROMA_URL=http://chroma.example.com:8000
```

---

### CHROMA_PERSIST_DIRECTORY

**Purpose:** Local directory for ChromaDB persistence.

**Default:** `./chroma_db/`

**Example:**
```bash
export CHROMA_PERSIST_DIRECTORY=/var/lib/chroma
```

---

### WEAVIATE_URL

**Purpose:** Weaviate server URL.

**Default:** `http://localhost:8080`

**Used by:**
- `skill-seekers upload --target weaviate`
- `export_to_weaviate` MCP tool

**Example:**
```bash
export WEAVIATE_URL=https://weaviate.example.com
```

---

### WEAVIATE_API_KEY

**Purpose:** Weaviate API key for authentication.

**Used by:**
- Weaviate Cloud
- Authenticated Weaviate instances

**Example:**
```bash
export WEAVIATE_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

### QDRANT_URL

**Purpose:** Qdrant server URL.

**Default:** `http://localhost:6333`

**Example:**
```bash
export QDRANT_URL=http://qdrant.example.com:6333
```

---

### QDRANT_API_KEY

**Purpose:** Qdrant API key for authentication.

**Example:**
```bash
export QDRANT_API_KEY=xxxxxxxxxxxxxxxx
```

---

## Debug and Development

### SKILL_SEEKERS_DEBUG

**Purpose:** Enable debug logging.

**Values:** `1`, `true`, `yes`

**Equivalent to:** `--verbose` flag

**Example:**
```bash
export SKILL_SEEKERS_DEBUG=1
```

---

### SKILL_SEEKERS_LOG_LEVEL

**Purpose:** Set logging level.

**Default:** `INFO`

**Options:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**Example:**
```bash
export SKILL_SEEKERS_LOG_LEVEL=DEBUG
```

---

### SKILL_SEEKERS_LOG_FILE

**Purpose:** Log to file instead of stdout.

**Example:**
```bash
export SKILL_SEEKERS_LOG_FILE=/var/log/skill-seekers.log
```

---

### SKILL_SEEKERS_CACHE_DIR

**Purpose:** Custom cache directory.

**Default:** `~/.cache/skill-seekers/`

**Example:**
```bash
export SKILL_SEEKERS_CACHE_DIR=/tmp/skill-seekers-cache
```

---

### SKILL_SEEKERS_NO_CACHE

**Purpose:** Disable caching.

**Values:** `1`, `true`, `yes`

**Example:**
```bash
export SKILL_SEEKERS_NO_CACHE=1
```

---

## MCP Server Settings

### MCP_TRANSPORT

**Purpose:** Default MCP transport mode.

**Default:** `stdio`

**Options:** `stdio`, `http`

**Example:**
```bash
export MCP_TRANSPORT=http
```

**Override:** Use `--transport` flag.

---

### MCP_PORT

**Purpose:** Default MCP HTTP port.

**Default:** `8765`

**Example:**
```bash
export MCP_PORT=8080
```

**Override:** Use `--port` flag.

---

### MCP_HOST

**Purpose:** Default MCP HTTP host.

**Default:** `127.0.0.1`

**Example:**
```bash
export MCP_HOST=0.0.0.0
```

**Override:** Use `--host` flag.

---

## Examples

### Development Environment

```bash
# Debug mode
export SKILL_SEEKERS_DEBUG=1
export SKILL_SEEKERS_LOG_LEVEL=DEBUG

# Custom paths
export SKILL_SEEKERS_HOME=./.skill-seekers
export SKILL_SEEKERS_OUTPUT=./output

# Faster scraping for testing
export SKILL_SEEKERS_RATE_LIMIT=0.1
export SKILL_SEEKERS_MAX_PAGES=50
```

### Production Environment

```bash
# API keys
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...

# Custom output directory
export SKILL_SEEKERS_OUTPUT=/var/www/skills

# Conservative scraping
export SKILL_SEEKERS_RATE_LIMIT=1.0
export SKILL_SEEKERS_WORKERS=2

# Logging
export SKILL_SEEKERS_LOG_FILE=/var/log/skill-seekers.log
export SKILL_SEEKERS_LOG_LEVEL=WARNING
```

### CI/CD Environment

```bash
# Non-interactive
export SKILL_SEEKERS_LOG_LEVEL=ERROR

# API keys from secrets
export ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY_SECRET}
export GITHUB_TOKEN=${GITHUB_TOKEN_SECRET}

# Fresh runs (no cache)
export SKILL_SEEKERS_NO_CACHE=1
```

### Multi-Platform Setup

```bash
# All API keys
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
export OPENAI_API_KEY=sk-...
export GITHUB_TOKEN=ghp_...

# Vector databases
export CHROMA_URL=http://localhost:8000
export WEAVIATE_URL=http://localhost:8080
export WEAVIATE_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## Configuration File

Environment variables can also be set in a `.env` file:

```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
SKILL_SEEKERS_OUTPUT=./output
SKILL_SEEKERS_RATE_LIMIT=0.5
```

Load with:
```bash
# Automatically loaded if python-dotenv is installed
# Or manually:
export $(cat .env | xargs)
```

---

## Priority Order

Settings are applied in this order (later overrides earlier):

1. Default values
2. Environment variables
3. Configuration file
4. Command-line flags

Example:
```bash
# Default: rate_limit = 0.5
export SKILL_SEEKERS_RATE_LIMIT=1.0  # Env var overrides default
# Config file: rate_limit = 0.2      # Config overrides env
skill-seekers scrape --rate-limit 2.0  # Flag overrides all
```

---

## Security Best Practices

### Never commit API keys

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
```

### Use secret management

```bash
# macOS Keychain
export ANTHROPIC_API_KEY=$(security find-generic-password -s "anthropic-api" -w)

# Linux Secret Service (with secret-tool)
export ANTHROPIC_API_KEY=$(secret-tool lookup service anthropic)

# 1Password CLI
export ANTHROPIC_API_KEY=$(op read "op://vault/anthropic/credential")
```

### File permissions

```bash
# Restrict .env file
chmod 600 .env
```

---

## Troubleshooting

### Variable not recognized

```bash
# Check if set
echo $ANTHROPIC_API_KEY

# Check in Python
python -c "import os; print(os.getenv('ANTHROPIC_API_KEY'))"
```

### Priority issues

```bash
# See effective configuration
skill-seekers config --show
```

### Path expansion

```bash
# Use full path or expand tilde
export SKILL_SEEKERS_HOME=$HOME/.skill-seekers
# NOT: ~/.skill-seekers (may not expand in all shells)
```

---

## See Also

- [CLI Reference](CLI_REFERENCE.md) - Command reference
- [Config Format](CONFIG_FORMAT.md) - JSON configuration

---

*For platform-specific setup, see [Installation Guide](../getting-started/01-installation.md)*
