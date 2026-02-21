# Installation Guide

> **Skill Seekers v3.1.0**

Get Skill Seekers installed and running in under 5 minutes.

---

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Python** | 3.10 | 3.11 or 3.12 |
| **RAM** | 4 GB | 8 GB+ |
| **Disk** | 500 MB | 2 GB+ |
| **OS** | Linux, macOS, Windows (WSL) | Linux, macOS |

---

## Quick Install

### Option 1: pip (Recommended)

```bash
# Basic installation
pip install skill-seekers

# With all platform support
pip install skill-seekers[all-llms]

# Verify installation
skill-seekers --version
```

### Option 2: pipx (Isolated)

```bash
# Install pipx if not available
pip install pipx
pipx ensurepath

# Install skill-seekers
pipx install skill-seekers[all-llms]
```

### Option 3: Development (from source)

```bash
# Clone repository
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd Skill_Seekers

# Install in editable mode
pip install -e ".[all-llms,dev]"

# Verify
skill-seekers --version
```

---

## Installation Options

### Minimal Install

Just the core functionality:

```bash
pip install skill-seekers
```

**Includes:**
- Documentation scraping
- Basic packaging
- Local enhancement (Claude Code)

### Full Install

All features and platforms:

```bash
pip install skill-seekers[all-llms]
```

**Includes:**
- Claude AI support
- Google Gemini support
- OpenAI ChatGPT support
- All vector databases
- MCP server
- Cloud storage (S3, GCS, Azure)

### Custom Install

Install only what you need:

```bash
# Specific platform only
pip install skill-seekers[gemini]      # Google Gemini
pip install skill-seekers[openai]      # OpenAI
pip install skill-seekers[chroma]      # ChromaDB

# Multiple extras
pip install skill-seekers[gemini,openai,chroma]

# Development
pip install skill-seekers[dev]
```

---

## Available Extras

| Extra | Description | Install Command |
|-------|-------------|-----------------|
| `gemini` | Google Gemini support | `pip install skill-seekers[gemini]` |
| `openai` | OpenAI ChatGPT support | `pip install skill-seekers[openai]` |
| `mcp` | MCP server | `pip install skill-seekers[mcp]` |
| `chroma` | ChromaDB export | `pip install skill-seekers[chroma]` |
| `weaviate` | Weaviate export | `pip install skill-seekers[weaviate]` |
| `qdrant` | Qdrant export | `pip install skill-seekers[qdrant]` |
| `faiss` | FAISS export | `pip install skill-seekers[faiss]` |
| `s3` | AWS S3 storage | `pip install skill-seekers[s3]` |
| `gcs` | Google Cloud Storage | `pip install skill-seekers[gcs]` |
| `azure` | Azure Blob Storage | `pip install skill-seekers[azure]` |
| `embedding` | Embedding server | `pip install skill-seekers[embedding]` |
| `all-llms` | All LLM platforms | `pip install skill-seekers[all-llms]` |
| `all` | Everything | `pip install skill-seekers[all]` |
| `dev` | Development tools | `pip install skill-seekers[dev]` |

---

## Post-Installation Setup

### 1. Configure API Keys (Optional)

For AI enhancement and uploads:

```bash
# Interactive configuration wizard
skill-seekers config

# Or set environment variables
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...
```

### 2. Verify Installation

```bash
# Check version
skill-seekers --version

# See all commands
skill-seekers --help

# Test configuration
skill-seekers config --test
```

### 3. Quick Test

```bash
# List available presets
skill-seekers estimate --all

# Do a dry run
skill-seekers create https://docs.python.org/3/ --dry-run
```

---

## Platform-Specific Notes

### macOS

```bash
# Using Homebrew Python
brew install python@3.12
pip3.12 install skill-seekers[all-llms]

# Or with pyenv
pyenv install 3.12
pyenv global 3.12
pip install skill-seekers[all-llms]
```

### Linux (Ubuntu/Debian)

```bash
# Install Python and pip
sudo apt update
sudo apt install python3-pip python3-venv

# Install skill-seekers
pip3 install skill-seekers[all-llms]

# Make available system-wide
sudo ln -s ~/.local/bin/skill-seekers /usr/local/bin/
```

### Windows

**Recommended:** Use WSL2

```powershell
# Or use Windows directly (PowerShell)
python -m pip install skill-seekers[all-llms]

# Add to PATH if needed
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:APPDATA\Python\Python312\Scripts", "User")
```

### Docker

```bash
# Pull image
docker pull skillseekers/skill-seekers:latest

# Run
docker run -it --rm \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v $(pwd)/output:/output \
  skillseekers/skill-seekers \
  skill-seekers create https://docs.react.dev/
```

---

## Troubleshooting

### "command not found: skill-seekers"

```bash
# Add pip bin to PATH
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall with --user
pip install --user --force-reinstall skill-seekers
```

### Permission denied

```bash
# Don't use sudo with pip
# Instead:
pip install --user skill-seekers

# Or use a virtual environment
python3 -m venv venv
source venv/bin/activate
pip install skill-seekers[all-llms]
```

### Import errors

```bash
# For development installs, ensure editable mode
pip install -e .

# Check installation
python -c "import skill_seekers; print(skill_seekers.__version__)"
```

### Version conflicts

```bash
# Use virtual environment
python3 -m venv skill-seekers-env
source skill-seekers-env/bin/activate
pip install skill-seekers[all-llms]
```

---

## Upgrade

```bash
# Upgrade to latest
pip install --upgrade skill-seekers

# Upgrade with all extras
pip install --upgrade skill-seekers[all-llms]

# Check current version
skill-seekers --version

# See what's new
pip show skill-seekers
```

---

## Uninstall

```bash
pip uninstall skill-seekers

# Clean up config (optional)
rm -rf ~/.config/skill-seekers/
rm -rf ~/.cache/skill-seekers/
```

---

## Next Steps

- [Quick Start Guide](02-quick-start.md) - Create your first skill in 3 commands
- [Your First Skill](03-your-first-skill.md) - Complete walkthrough

---

## Getting Help

```bash
# Command help
skill-seekers --help
skill-seekers create --help

# Documentation
# https://github.com/yusufkaraaslan/Skill_Seekers/tree/main/docs

# Issues
# https://github.com/yusufkaraaslan/Skill_Seekers/issues
```
