# Git-Based Config Sources - Complete Guide

**Version:** v2.2.0
**Feature:** A1.9 - Multi-Source Git Repository Support
**Last Updated:** December 21, 2025

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [MCP Tools Reference](#mcp-tools-reference)
- [Authentication](#authentication)
- [Use Cases](#use-cases)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

---

## Overview

### What is this feature?

Git-based config sources allow you to fetch config files from **private/team git repositories** in addition to the public API. This unlocks:

- 🔐 **Private configs** - Company/internal documentation
- 👥 **Team collaboration** - Share configs across 3-5 person teams
- 🏢 **Enterprise scale** - Support 500+ developers
- 📦 **Custom collections** - Curated config repositories
- 🌐 **Decentralized** - Like npm (public + private registries)

### How it works

```
User → fetch_config(source="team", config_name="react-custom")
    ↓
SourceManager (~/.skill-seekers/sources.json)
    ↓
GitConfigRepo (clone/pull with GitPython)
    ↓
Local cache (~/.skill-seekers/cache/team/)
    ↓
Config JSON returned
```

### Three modes

1. **API Mode** (existing, unchanged)
   - `fetch_config(config_name="react")`
   - Fetches from api.skillseekersweb.com

2. **Source Mode** (NEW - recommended)
   - `fetch_config(source="team", config_name="react-custom")`
   - Uses registered git source

3. **Git URL Mode** (NEW - one-time)
   - `fetch_config(git_url="https://...", config_name="react-custom")`
   - Direct clone without registration

---

## Quick Start

### 1. Set up authentication

```bash
# GitHub
export GITHUB_TOKEN=ghp_your_token_here

# GitLab
export GITLAB_TOKEN=glpat_your_token_here

# Bitbucket
export BITBUCKET_TOKEN=your_token_here
```

### 2. Register a source

Using MCP tools (recommended):

```python
add_config_source(
    name="team",
    git_url="https://github.com/mycompany/skill-configs.git",
    source_type="github",  # Optional, auto-detected
    token_env="GITHUB_TOKEN",  # Optional, auto-detected
    branch="main",  # Optional, default: "main"
    priority=100  # Optional, lower = higher priority
)
```

### 3. Fetch configs

```python
# From registered source
fetch_config(source="team", config_name="react-custom")

# List available sources
list_config_sources()

# Remove when done
remove_config_source(name="team")
```

### 4. Quick test with example repository

```bash
cd /path/to/Skill_Seekers

# Run E2E test
python3 configs/example-team/test_e2e.py

# Or test manually
add_config_source(
    name="example",
    git_url="file://$(pwd)/configs/example-team",
    branch="master"
)

fetch_config(source="example", config_name="react-custom")
```

---

## Architecture

### Storage Locations

**Sources Registry:**
```
~/.skill-seekers/sources.json
```

Example content:
```json
{
  "version": "1.0",
  "sources": [
    {
      "name": "team",
      "git_url": "https://github.com/myorg/configs.git",
      "type": "github",
      "token_env": "GITHUB_TOKEN",
      "branch": "main",
      "enabled": true,
      "priority": 1,
      "added_at": "2025-12-21T10:00:00Z",
      "updated_at": "2025-12-21T10:00:00Z"
    }
  ]
}
```

**Cache Directory:**
```
$SKILL_SEEKERS_CACHE_DIR  (default: ~/.skill-seekers/cache/)
```

Structure:
```
~/.skill-seekers/
├── sources.json       # Source registry
└── cache/             # Git clones
    ├── team/          # One directory per source
    │   ├── .git/
    │   ├── react-custom.json
    │   └── vue-internal.json
    └── company/
        ├── .git/
        └── internal-api.json
```

### Git Strategy

- **Shallow clone**: `git clone --depth 1 --single-branch`
  - 10-50x faster
  - Minimal disk space
  - No history, just latest commit

- **Auto-pull**: Updates cache automatically
  - Checks for changes on each fetch
  - Use `refresh=true` to force re-clone

- **Config discovery**: Recursively scans for `*.json` files
  - No hardcoded paths
  - Flexible repository structure
  - Excludes `.git` directory

---

## MCP Tools Reference

### add_config_source

Register a git repository as a config source.

**Parameters:**
- `name` (required): Source identifier (lowercase, alphanumeric, hyphens/underscores)
- `git_url` (required): Git repository URL (HTTPS or SSH)
- `source_type` (optional): "github", "gitlab", "gitea", "bitbucket", "custom" (auto-detected from URL)
- `token_env` (optional): Environment variable name for token (auto-detected from type)
- `branch` (optional): Git branch (default: "main")
- `priority` (optional): Priority number (default: 100, lower = higher priority)
- `enabled` (optional): Whether source is active (default: true)

**Returns:**
- Source details including registration timestamp

**Examples:**

```python
# Minimal (auto-detects everything)
add_config_source(
    name="team",
    git_url="https://github.com/myorg/configs.git"
)

# Full parameters
add_config_source(
    name="company",
    git_url="https://gitlab.company.com/platform/configs.git",
    source_type="gitlab",
    token_env="GITLAB_COMPANY_TOKEN",
    branch="develop",
    priority=1,
    enabled=true
)

# SSH URL (auto-converts to HTTPS with token)
add_config_source(
    name="team",
    git_url="git@github.com:myorg/configs.git",
    token_env="GITHUB_TOKEN"
)
```

### list_config_sources

List all registered config sources.

**Parameters:**
- `enabled_only` (optional): Only show enabled sources (default: false)

**Returns:**
- List of sources sorted by priority

**Example:**

```python
# List all sources
list_config_sources()

# List only enabled sources
list_config_sources(enabled_only=true)
```

**Output:**
```
📋 Config Sources (2 total)

✓ **team**
  📁 https://github.com/myorg/configs.git
  🔖 Type: github | 🌿 Branch: main
  🔑 Token: GITHUB_TOKEN | ⚡ Priority: 1
  🕒 Added: 2025-12-21 10:00:00

✓ **company**
  📁 https://gitlab.company.com/configs.git
  🔖 Type: gitlab | 🌿 Branch: develop
  🔑 Token: GITLAB_TOKEN | ⚡ Priority: 2
  🕒 Added: 2025-12-21 11:00:00
```

### remove_config_source

Remove a registered config source.

**Parameters:**
- `name` (required): Source identifier

**Returns:**
- Success/failure message

**Note:** Does NOT delete cached git repository data. To free disk space, manually delete `~/.skill-seekers/cache/{source_name}/`

**Example:**

```python
remove_config_source(name="team")
```

### fetch_config

Fetch config from API, git URL, or named source.

**Mode 1: Named Source (highest priority)**

```python
fetch_config(
    source="team",  # Use registered source
    config_name="react-custom",
    destination="configs/",  # Optional
    branch="main",  # Optional, overrides source default
    refresh=false  # Optional, force re-clone
)
```

**Mode 2: Direct Git URL**

```python
fetch_config(
    git_url="https://github.com/myorg/configs.git",
    config_name="react-custom",
    branch="main",  # Optional
    token="ghp_token",  # Optional, prefer env vars
    destination="configs/",  # Optional
    refresh=false  # Optional
)
```

**Mode 3: API (existing, unchanged)**

```python
fetch_config(
    config_name="react",
    destination="configs/"  # Optional
)

# Or list available
fetch_config(list_available=true)
```

---

## Authentication

### Environment Variables Only

Tokens are **ONLY** stored in environment variables. This is:
- ✅ **Secure** - Not in files, not in git
- ✅ **Standard** - Same as GitHub CLI, Docker, etc.
- ✅ **Temporary** - Cleared on logout
- ✅ **Flexible** - Different tokens for different services

### Creating Tokens

**GitHub:**
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scopes: `repo` (for private repos)
4. Copy token: `ghp_xxxxxxxxxxxxx`
5. Export: `export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx`

**GitLab:**
1. Go to https://gitlab.com/-/profile/personal_access_tokens
2. Create token with `read_repository` scope
3. Copy token: `glpat-xxxxxxxxxxxxx`
4. Export: `export GITLAB_TOKEN=glpat-xxxxxxxxxxxxx`

**Bitbucket:**
1. Go to https://bitbucket.org/account/settings/app-passwords/
2. Create app password with `Repositories: Read` permission
3. Copy password
4. Export: `export BITBUCKET_TOKEN=your_password`

### Persistent Tokens

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
# GitHub token
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx

# GitLab token
export GITLAB_TOKEN=glpat-xxxxxxxxxxxxx

# Company GitLab (separate token)
export GITLAB_COMPANY_TOKEN=glpat-yyyyyyyyyyyyy
```

Then: `source ~/.bashrc`

### Token Injection

GitConfigRepo automatically:
1. Converts SSH URLs to HTTPS
2. Injects token into URL
3. Uses token for authentication

**Example:**
- Input: `git@github.com:myorg/repo.git` + token `ghp_xxx`
- Output: `https://ghp_xxx@github.com/myorg/repo.git`

---

## Use Cases

### Small Team (3-5 people)

**Scenario:** Frontend team needs custom React configs for internal docs.

**Setup:**

```bash
# 1. Team lead creates repo
gh repo create myteam/skill-configs --private

# 2. Add configs
cd myteam-skill-configs
cp ../Skill_Seekers/configs/react.json ./react-internal.json

# Edit for internal docs:
# - Change base_url to internal docs site
# - Adjust selectors for company theme
# - Customize categories

git add . && git commit -m "Add internal React config" && git push

# 3. Team members register (one-time)
export GITHUB_TOKEN=ghp_their_token
add_config_source(
    name="team",
    git_url="https://github.com/myteam/skill-configs.git"
)

# 4. Daily usage
fetch_config(source="team", config_name="react-internal")
```

**Benefits:**
- ✅ Shared configs across team
- ✅ Version controlled
- ✅ Private to company
- ✅ Easy updates (git push)

### Enterprise (500+ developers)

**Scenario:** Large company with multiple teams, internal docs, and priority-based config resolution.

**Setup:**

```bash
# IT pre-configures sources for all developers
# (via company setup script or documentation)

# 1. Platform team configs (highest priority)
add_config_source(
    name="platform",
    git_url="https://gitlab.company.com/platform/skill-configs.git",
    source_type="gitlab",
    token_env="GITLAB_COMPANY_TOKEN",
    priority=1
)

# 2. Mobile team configs
add_config_source(
    name="mobile",
    git_url="https://gitlab.company.com/mobile/skill-configs.git",
    source_type="gitlab",
    token_env="GITLAB_COMPANY_TOKEN",
    priority=2
)

# 3. Public/official configs (fallback)
# (API mode, no registration needed, lowest priority)
```

**Developer usage:**

```python
# Automatically finds config with highest priority
fetch_config(config_name="platform-api")  # Found in platform source
fetch_config(config_name="react-native")  # Found in mobile source
fetch_config(config_name="react")  # Falls back to public API
```

**Benefits:**
- ✅ Centralized config management
- ✅ Team-specific overrides
- ✅ Fallback to public configs
- ✅ Priority-based resolution
- ✅ Scales to hundreds of developers

### Open Source Project

**Scenario:** Open source project wants curated configs for contributors.

**Setup:**

```bash
# 1. Create public repo
gh repo create myproject/skill-configs --public

# 2. Add configs for project stack
- react.json (frontend)
- django.json (backend)
- postgres.json (database)
- nginx.json (deployment)

# 3. Contributors use directly (no token needed for public repos)
add_config_source(
    name="myproject",
    git_url="https://github.com/myproject/skill-configs.git"
)

fetch_config(source="myproject", config_name="react")
```

**Benefits:**
- ✅ Curated configs for project
- ✅ No API dependency
- ✅ Community contributions via PR
- ✅ Version controlled

---

## Best Practices

### Config Naming

**Good:**
- `react-internal.json` - Clear purpose
- `api-v2.json` - Version included
- `platform-auth.json` - Specific topic

**Bad:**
- `config1.json` - Generic
- `react.json` - Conflicts with official
- `test.json` - Not descriptive

### Repository Structure

**Flat (recommended for small repos):**
```
skill-configs/
├── README.md
├── react-internal.json
├── vue-internal.json
└── api-v2.json
```

**Organized (recommended for large repos):**
```
skill-configs/
├── README.md
├── frontend/
│   ├── react-internal.json
│   └── vue-internal.json
├── backend/
│   ├── django-api.json
│   └── fastapi-platform.json
└── mobile/
    ├── react-native.json
    └── flutter.json
```

**Note:** Config discovery works recursively, so both structures work!

### Source Priorities

Lower number = higher priority. Use sensible defaults:

- `1-10`: Critical/override configs
- `50-100`: Team configs (default: 100)
- `1000+`: Fallback/experimental

**Example:**
```python
# Override official React config with internal version
add_config_source(name="team", ..., priority=1)  # Checked first
# Official API is checked last (priority: infinity)
```

### Security

✅ **DO:**
- Use environment variables for tokens
- Use private repos for sensitive configs
- Rotate tokens regularly
- Use fine-grained tokens (read-only if possible)

❌ **DON'T:**
- Commit tokens to git
- Share tokens between people
- Use personal tokens for teams (use service accounts)
- Store tokens in config files

### Maintenance

**Regular tasks:**
```bash
# Update configs in repo
cd myteam-skill-configs
# Edit configs...
git commit -m "Update React config" && git push

# Developers get updates automatically on next fetch
fetch_config(source="team", config_name="react-internal")
# ^--- Auto-pulls latest changes
```

**Force refresh:**
```python
# Delete cache and re-clone
fetch_config(source="team", config_name="react-internal", refresh=true)
```

**Clean up old sources:**
```bash
# Remove unused sources
remove_config_source(name="old-team")

# Free disk space
rm -rf ~/.skill-seekers/cache/old-team/
```

---

## Troubleshooting

### Authentication Failures

**Error:** "Authentication failed for https://github.com/org/repo.git"

**Solutions:**
1. Check token is set:
   ```bash
   echo $GITHUB_TOKEN  # Should show token
   ```

2. Verify token has correct permissions:
   - GitHub: `repo` scope for private repos
   - GitLab: `read_repository` scope

3. Check token isn't expired:
   - Regenerate if needed

4. Try direct access:
   ```bash
   git clone https://$GITHUB_TOKEN@github.com/org/repo.git test-clone
   ```

### Config Not Found

**Error:** "Config 'react' not found in repository. Available configs: django, vue"

**Solutions:**
1. List available configs:
   ```python
   # Shows what's actually in the repo
   list_config_sources()
   ```

2. Check config file exists in repo:
   ```bash
   # Clone locally and inspect
   git clone <git_url> temp-inspect
   find temp-inspect -name "*.json"
   ```

3. Verify config name (case-insensitive):
   - `react` matches `React.json` or `react.json`

### Slow Cloning

**Issue:** Repository takes minutes to clone.

**Solutions:**
1. Shallow clone is already enabled (depth=1)

2. Check repository size:
   ```bash
   # See repo size
   gh repo view owner/repo --json diskUsage
   ```

3. If very large (>100MB), consider:
   - Splitting configs into separate repos
   - Using sparse checkout
   - Contacting IT to optimize repo

### Cache Issues

**Issue:** Getting old configs even after updating repo.

**Solutions:**
1. Force refresh:
   ```python
   fetch_config(source="team", config_name="react", refresh=true)
   ```

2. Manual cache clear:
   ```bash
   rm -rf ~/.skill-seekers/cache/team/
   ```

3. Check auto-pull worked:
   ```bash
   cd ~/.skill-seekers/cache/team
   git log -1  # Shows latest commit
   ```

---

## Advanced Topics

### Multiple Git Accounts

Use different tokens for different repos:

```bash
# Personal GitHub
export GITHUB_TOKEN=ghp_personal_xxx

# Work GitHub
export GITHUB_WORK_TOKEN=ghp_work_yyy

# Company GitLab
export GITLAB_COMPANY_TOKEN=glpat-zzz
```

Register with specific tokens:
```python
add_config_source(
    name="personal",
    git_url="https://github.com/myuser/configs.git",
    token_env="GITHUB_TOKEN"
)

add_config_source(
    name="work",
    git_url="https://github.com/mycompany/configs.git",
    token_env="GITHUB_WORK_TOKEN"
)
```

### Custom Cache Location

Set custom cache directory:

```bash
export SKILL_SEEKERS_CACHE_DIR=/mnt/large-disk/skill-seekers-cache
```

Or pass to GitConfigRepo:
```python
from skill_seekers.mcp.git_repo import GitConfigRepo

gr = GitConfigRepo(cache_dir="/custom/path/cache")
```

### SSH URLs

SSH URLs are automatically converted to HTTPS + token:

```python
# Input
add_config_source(
    name="team",
    git_url="git@github.com:myorg/configs.git",
    token_env="GITHUB_TOKEN"
)

# Internally becomes
# https://ghp_xxx@github.com/myorg/configs.git
```

### Priority Resolution

When same config exists in multiple sources:

```python
add_config_source(name="team", ..., priority=1)     # Checked first
add_config_source(name="company", ..., priority=2)  # Checked second
# API mode is checked last (priority: infinity)

fetch_config(config_name="react")
# 1. Checks team source
# 2. If not found, checks company source
# 3. If not found, falls back to API
```

### CI/CD Integration

Use in GitHub Actions:

```yaml
name: Generate Skills

on: push

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Skill Seekers
        run: pip install skill-seekers

      - name: Register config source
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 << EOF
          from skill_seekers.mcp.source_manager import SourceManager
          sm = SourceManager()
          sm.add_source(
              name="team",
              git_url="https://github.com/myorg/configs.git"
          )
          EOF

      - name: Fetch and use config
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # Use MCP fetch_config or direct Python
          skill-seekers scrape --config <fetched_config>
```

---

## API Reference

### GitConfigRepo Class

**Location:** `src/skill_seekers/mcp/git_repo.py`

**Methods:**

```python
def __init__(cache_dir: Optional[str] = None)
    """Initialize with optional cache directory."""

def clone_or_pull(
    source_name: str,
    git_url: str,
    branch: str = "main",
    token: Optional[str] = None,
    force_refresh: bool = False
) -> Path:
    """Clone if not cached, else pull latest changes."""

def find_configs(repo_path: Path) -> list[Path]:
    """Find all *.json files in repository."""

def get_config(repo_path: Path, config_name: str) -> dict:
    """Load specific config by name."""

@staticmethod
def inject_token(git_url: str, token: str) -> str:
    """Inject token into git URL."""

@staticmethod
def validate_git_url(git_url: str) -> bool:
    """Validate git URL format."""
```

### SourceManager Class

**Location:** `src/skill_seekers/mcp/source_manager.py`

**Methods:**

```python
def __init__(config_dir: Optional[str] = None)
    """Initialize with optional config directory."""

def add_source(
    name: str,
    git_url: str,
    source_type: str = "github",
    token_env: Optional[str] = None,
    branch: str = "main",
    priority: int = 100,
    enabled: bool = True
) -> dict:
    """Add or update config source."""

def get_source(name: str) -> dict:
    """Get source by name."""

def list_sources(enabled_only: bool = False) -> list[dict]:
    """List all sources."""

def remove_source(name: str) -> bool:
    """Remove source."""

def update_source(name: str, **kwargs) -> dict:
    """Update specific fields."""
```

---

## See Also

- [README.md](../README.md) - Main documentation
- [MCP_SETUP.md](MCP_SETUP.md) - MCP server setup
- [UNIFIED_SCRAPING.md](UNIFIED_SCRAPING.md) - Multi-source scraping
- [configs/example-team/](../configs/example-team/) - Example repository

---

## Changelog

### v2.2.0 (2025-12-21)
- Initial release of git-based config sources
- 3 fetch modes: API, Git URL, Named Source
- 4 MCP tools: add/list/remove/fetch
- Support for GitHub, GitLab, Bitbucket, Gitea
- Shallow clone optimization
- Priority-based resolution
- 83 tests (100% passing)

---

**Questions?** Open an issue at https://github.com/yusufkaraaslan/Skill_Seekers/issues
