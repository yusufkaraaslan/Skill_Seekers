# API Reference - Programmatic Usage

**Version:** 2.7.0
**Last Updated:** 2026-01-18
**Status:** ✅ Production Ready

---

## Overview

Skill Seekers can be used programmatically for integration into other tools, automation scripts, and CI/CD pipelines. This guide covers the public APIs available for developers who want to embed Skill Seekers functionality into their own applications.

**Use Cases:**
- Automated documentation skill generation in CI/CD
- Batch processing multiple documentation sources
- Custom skill generation workflows
- Integration with internal tooling
- Automated skill updates on documentation changes

---

## Installation

### Basic Installation

```bash
pip install skill-seekers
```

### With Platform Dependencies

```bash
# Google Gemini support
pip install skill-seekers[gemini]

# OpenAI ChatGPT support
pip install skill-seekers[openai]

# All platform support
pip install skill-seekers[all-llms]
```

### Development Installation

```bash
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd Skill_Seekers
pip install -e ".[all-llms]"
```

---

## Core APIs

### 1. Documentation Scraping API

Extract content from documentation websites using BFS traversal and smart categorization.

#### Basic Usage

```python
from skill_seekers.cli.doc_scraper import scrape_all, build_skill
import json

# Load configuration
with open('configs/react.json', 'r') as f:
    config = json.load(f)

# Scrape documentation
pages = scrape_all(
    base_url=config['base_url'],
    selectors=config['selectors'],
    config=config,
    output_dir='output/react_data'
)

print(f"Scraped {len(pages)} pages")

# Build skill from scraped data
skill_path = build_skill(
    config_name='react',
    output_dir='output/react',
    data_dir='output/react_data'
)

print(f"Skill created at: {skill_path}")
```

#### Advanced Scraping Options

```python
from skill_seekers.cli.doc_scraper import scrape_all

# Custom scraping with advanced options
pages = scrape_all(
    base_url='https://docs.example.com',
    selectors={
        'main_content': 'article',
        'title': 'h1',
        'code_blocks': 'pre code'
    },
    config={
        'name': 'my-framework',
        'description': 'Custom framework documentation',
        'rate_limit': 0.5,  # 0.5 second delay between requests
        'max_pages': 500,   # Limit to 500 pages
        'url_patterns': {
            'include': ['/docs/'],
            'exclude': ['/blog/', '/changelog/']
        }
    },
    output_dir='output/my-framework_data',
    use_async=True  # Enable async scraping (2-3x faster)
)
```

#### Rebuilding Without Scraping

```python
from skill_seekers.cli.doc_scraper import build_skill

# Rebuild skill from existing data (fast!)
skill_path = build_skill(
    config_name='react',
    output_dir='output/react',
    data_dir='output/react_data',  # Use existing scraped data
    skip_scrape=True  # Don't re-scrape
)
```

---

### 2. GitHub Repository Analysis API

Analyze GitHub repositories with three-stream architecture (Code + Docs + Insights).

#### Basic GitHub Analysis

```python
from skill_seekers.cli.github_scraper import scrape_github_repo

# Analyze GitHub repository
result = scrape_github_repo(
    repo_url='https://github.com/facebook/react',
    output_dir='output/react-github',
    analysis_depth='c3x',  # Options: 'basic' or 'c3x'
    github_token='ghp_...'  # Optional: higher rate limits
)

print(f"Analysis complete: {result['skill_path']}")
print(f"Code files analyzed: {result['stats']['code_files']}")
print(f"Patterns detected: {result['stats']['patterns']}")
```

#### Stream-Specific Analysis

```python
from skill_seekers.cli.github_scraper import scrape_github_repo

# Focus on specific streams
result = scrape_github_repo(
    repo_url='https://github.com/vercel/next.js',
    output_dir='output/nextjs',
    analysis_depth='c3x',
    enable_code_stream=True,      # C3.x codebase analysis
    enable_docs_stream=True,      # README, docs/, wiki
    enable_insights_stream=True,  # GitHub metadata, issues
    include_tests=True,           # Extract test examples
    include_patterns=True,        # Detect design patterns
    include_how_to_guides=True    # Generate guides from tests
)
```

---

### 3. PDF Extraction API

Extract content from PDF documents with OCR and image support.

#### Basic PDF Extraction

```python
from skill_seekers.cli.pdf_scraper import scrape_pdf

# Extract from single PDF
skill_path = scrape_pdf(
    pdf_path='documentation.pdf',
    output_dir='output/pdf-skill',
    skill_name='my-pdf-skill',
    description='Documentation from PDF'
)

print(f"PDF skill created: {skill_path}")
```

#### Advanced PDF Processing

```python
from skill_seekers.cli.pdf_scraper import scrape_pdf

# PDF extraction with all features
skill_path = scrape_pdf(
    pdf_path='large-manual.pdf',
    output_dir='output/manual',
    skill_name='product-manual',
    description='Product manual documentation',
    enable_ocr=True,              # OCR for scanned PDFs
    extract_images=True,          # Extract embedded images
    extract_tables=True,          # Parse tables
    chunk_size=50,                # Pages per chunk (large PDFs)
    language='eng',               # OCR language
    dpi=300                       # Image DPI for OCR
)
```

---

### 4. Unified Multi-Source Scraping API

Combine multiple sources (docs + GitHub + PDF) into a single unified skill.

#### Unified Scraping

```python
from skill_seekers.cli.unified_scraper import unified_scrape

# Scrape from multiple sources
result = unified_scrape(
    config_path='configs/unified/react-unified.json',
    output_dir='output/react-complete'
)

print(f"Unified skill created: {result['skill_path']}")
print(f"Sources merged: {result['sources']}")
print(f"Conflicts detected: {result['conflicts']}")
```

#### Conflict Detection

```python
from skill_seekers.cli.unified_scraper import detect_conflicts

# Detect discrepancies between sources
conflicts = detect_conflicts(
    docs_dir='output/react_data',
    github_dir='output/react-github',
    pdf_dir='output/react-pdf'
)

for conflict in conflicts:
    print(f"Conflict in {conflict['topic']}:")
    print(f"  Docs say: {conflict['docs_version']}")
    print(f"  Code shows: {conflict['code_version']}")
```

---

### 5. Skill Packaging API

Package skills for different LLM platforms using the platform adaptor architecture.

#### Basic Packaging

```python
from skill_seekers.cli.adaptors import get_adaptor

# Get platform-specific adaptor
adaptor = get_adaptor('claude')  # Options: claude, gemini, openai, markdown

# Package skill
package_path = adaptor.package(
    skill_dir='output/react/',
    output_path='output/'
)

print(f"Claude skill package: {package_path}")
```

#### Multi-Platform Packaging

```python
from skill_seekers.cli.adaptors import get_adaptor

# Package for all platforms
platforms = ['claude', 'gemini', 'openai', 'markdown']

for platform in platforms:
    adaptor = get_adaptor(platform)
    package_path = adaptor.package(
        skill_dir='output/react/',
        output_path='output/'
    )
    print(f"{platform.capitalize()} package: {package_path}")
```

#### Custom Packaging Options

```python
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('gemini')

# Gemini-specific packaging (.tar.gz format)
package_path = adaptor.package(
    skill_dir='output/react/',
    output_path='output/',
    compress_level=9,  # Maximum compression
    include_metadata=True
)
```

---

### 6. Skill Upload API

Upload packaged skills to LLM platforms via their APIs.

#### Claude AI Upload

```python
import os
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('claude')

# Upload to Claude AI
result = adaptor.upload(
    package_path='output/react-claude.zip',
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

print(f"Uploaded to Claude AI: {result['skill_id']}")
```

#### Google Gemini Upload

```python
import os
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('gemini')

# Upload to Google Gemini
result = adaptor.upload(
    package_path='output/react-gemini.tar.gz',
    api_key=os.getenv('GOOGLE_API_KEY')
)

print(f"Gemini corpus ID: {result['corpus_id']}")
```

#### OpenAI ChatGPT Upload

```python
import os
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('openai')

# Upload to OpenAI Vector Store
result = adaptor.upload(
    package_path='output/react-openai.zip',
    api_key=os.getenv('OPENAI_API_KEY')
)

print(f"Vector store ID: {result['vector_store_id']}")
```

---

### 7. AI Enhancement API

Enhance skills with AI-powered improvements using platform-specific models.

#### API Mode Enhancement

```python
import os
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('claude')

# Enhance using Claude API
result = adaptor.enhance(
    skill_dir='output/react/',
    mode='api',
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

print(f"Enhanced skill: {result['enhanced_path']}")
print(f"Quality score: {result['quality_score']}/10")
```

#### LOCAL Mode Enhancement

```python
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('claude')

# Enhance using Claude Code CLI (free!)
result = adaptor.enhance(
    skill_dir='output/react/',
    mode='LOCAL',
    execution_mode='headless',  # Options: headless, background, daemon
    timeout=300  # 5 minute timeout
)

print(f"Enhanced skill: {result['enhanced_path']}")
```

#### Background Enhancement with Monitoring

```python
from skill_seekers.cli.enhance_skill_local import enhance_skill
from skill_seekers.cli.enhance_status import monitor_enhancement
import time

# Start background enhancement
result = enhance_skill(
    skill_dir='output/react/',
    mode='background'
)

pid = result['pid']
print(f"Enhancement started in background (PID: {pid})")

# Monitor progress
while True:
    status = monitor_enhancement('output/react/')
    print(f"Status: {status['state']}, Progress: {status['progress']}%")

    if status['state'] == 'completed':
        print(f"Enhanced skill: {status['output_path']}")
        break
    elif status['state'] == 'failed':
        print(f"Enhancement failed: {status['error']}")
        break

    time.sleep(5)  # Check every 5 seconds
```

---

### 8. Complete Workflow Automation API

Automate the entire workflow: fetch config → scrape → enhance → package → upload.

#### One-Command Install

```python
import os
from skill_seekers.cli.install_skill import install_skill

# Complete workflow automation
result = install_skill(
    config_name='react',  # Use preset config
    target='claude',      # Target platform
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    enhance=True,         # Enable AI enhancement
    upload=True,          # Upload to platform
    force=True            # Skip confirmations
)

print(f"Skill installed: {result['skill_id']}")
print(f"Package path: {result['package_path']}")
print(f"Time taken: {result['duration']}s")
```

#### Custom Config Install

```python
from skill_seekers.cli.install_skill import install_skill

# Install with custom configuration
result = install_skill(
    config_path='configs/custom/my-framework.json',
    target='gemini',
    api_key=os.getenv('GOOGLE_API_KEY'),
    enhance=True,
    upload=True,
    analysis_depth='c3x',  # Deep codebase analysis
    enable_router=True     # Generate router for large docs
)
```

---

## Configuration Objects

### Config Schema

Skill Seekers uses JSON configuration files to define scraping behavior.

```json
{
  "name": "framework-name",
  "description": "When to use this skill",
  "base_url": "https://docs.example.com/",
  "selectors": {
    "main_content": "article",
    "title": "h1",
    "code_blocks": "pre code",
    "navigation": "nav.sidebar"
  },
  "url_patterns": {
    "include": ["/docs/", "/api/", "/guides/"],
    "exclude": ["/blog/", "/changelog/", "/archive/"]
  },
  "categories": {
    "getting_started": ["intro", "quickstart", "installation"],
    "api": ["api", "reference", "methods"],
    "guides": ["guide", "tutorial", "how-to"],
    "examples": ["example", "demo", "sample"]
  },
  "rate_limit": 0.5,
  "max_pages": 500,
  "llms_txt_url": "https://example.com/llms.txt",
  "enable_async": true
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Skill name (alphanumeric + hyphens) |
| `description` | string | When to use this skill |
| `base_url` | string | Documentation website URL |
| `selectors` | object | CSS selectors for content extraction |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url_patterns.include` | array | `[]` | URL path patterns to include |
| `url_patterns.exclude` | array | `[]` | URL path patterns to exclude |
| `categories` | object | `{}` | Category keywords mapping |
| `rate_limit` | float | `0.5` | Delay between requests (seconds) |
| `max_pages` | int | `500` | Maximum pages to scrape |
| `llms_txt_url` | string | `null` | URL to llms.txt file |
| `enable_async` | bool | `false` | Enable async scraping (faster) |

### Unified Config Schema (Multi-Source)

```json
{
  "name": "framework-unified",
  "description": "Complete framework documentation",
  "sources": {
    "documentation": {
      "type": "docs",
      "base_url": "https://docs.example.com/",
      "selectors": { "main_content": "article" }
    },
    "github": {
      "type": "github",
      "repo_url": "https://github.com/org/repo",
      "analysis_depth": "c3x"
    },
    "pdf": {
      "type": "pdf",
      "pdf_path": "manual.pdf",
      "enable_ocr": true
    }
  },
  "conflict_resolution": "prefer_code",
  "merge_strategy": "smart"
}
```

---

## Advanced Options

### Custom Selectors

```python
from skill_seekers.cli.doc_scraper import scrape_all

# Custom CSS selectors for complex sites
pages = scrape_all(
    base_url='https://complex-site.com',
    selectors={
        'main_content': 'div.content-wrapper > article',
        'title': 'h1.page-title',
        'code_blocks': 'pre.highlight code',
        'navigation': 'aside.sidebar nav',
        'metadata': 'meta[name="description"]'
    },
    config={'name': 'complex-site'}
)
```

### URL Pattern Matching

```python
# Advanced URL filtering
config = {
    'url_patterns': {
        'include': [
            '/docs/',           # Exact path match
            '/api/**',          # Wildcard: all subpaths
            '/guides/v2.*'      # Regex: version-specific
        ],
        'exclude': [
            '/blog/',
            '/changelog/',
            '**/*.png',         # Exclude images
            '**/*.pdf'          # Exclude PDFs
        ]
    }
}
```

### Category Inference

```python
from skill_seekers.cli.doc_scraper import infer_categories

# Auto-detect categories from URL structure
categories = infer_categories(
    pages=[
        {'url': 'https://docs.example.com/getting-started/intro'},
        {'url': 'https://docs.example.com/api/authentication'},
        {'url': 'https://docs.example.com/guides/tutorial'}
    ]
)

print(categories)
# Output: {
#   'getting-started': ['intro'],
#   'api': ['authentication'],
#   'guides': ['tutorial']
# }
```

---

## Error Handling

### Common Exceptions

```python
from skill_seekers.cli.doc_scraper import scrape_all
from skill_seekers.exceptions import (
    NetworkError,
    InvalidConfigError,
    ScrapingError,
    RateLimitError
)

try:
    pages = scrape_all(
        base_url='https://docs.example.com',
        selectors={'main_content': 'article'},
        config={'name': 'example'}
    )
except NetworkError as e:
    print(f"Network error: {e}")
    # Retry with exponential backoff
except InvalidConfigError as e:
    print(f"Invalid config: {e}")
    # Fix configuration and retry
except RateLimitError as e:
    print(f"Rate limited: {e}")
    # Increase rate_limit in config
except ScrapingError as e:
    print(f"Scraping failed: {e}")
    # Check selectors and URL patterns
```

### Retry Logic

```python
from skill_seekers.cli.doc_scraper import scrape_all
from skill_seekers.utils import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=1.0)
def scrape_with_retry(base_url, config):
    return scrape_all(
        base_url=base_url,
        selectors=config['selectors'],
        config=config
    )

# Automatically retries on network errors
pages = scrape_with_retry(
    base_url='https://docs.example.com',
    config={'name': 'example', 'selectors': {...}}
)
```

---

## Testing Your Integration

### Unit Tests

```python
import pytest
from skill_seekers.cli.doc_scraper import scrape_all

def test_basic_scraping():
    """Test basic documentation scraping."""
    pages = scrape_all(
        base_url='https://docs.example.com',
        selectors={'main_content': 'article'},
        config={
            'name': 'test-framework',
            'max_pages': 10  # Limit for testing
        }
    )

    assert len(pages) > 0
    assert all('title' in p for p in pages)
    assert all('content' in p for p in pages)

def test_config_validation():
    """Test configuration validation."""
    from skill_seekers.cli.config_validator import validate_config

    config = {
        'name': 'test',
        'base_url': 'https://example.com',
        'selectors': {'main_content': 'article'}
    }

    is_valid, errors = validate_config(config)
    assert is_valid
    assert len(errors) == 0
```

### Integration Tests

```python
import pytest
import os
from skill_seekers.cli.install_skill import install_skill

@pytest.mark.integration
def test_end_to_end_workflow():
    """Test complete skill installation workflow."""
    result = install_skill(
        config_name='react',
        target='markdown',  # No API key needed for markdown
        enhance=False,      # Skip AI enhancement
        upload=False,       # Don't upload
        force=True
    )

    assert result['success']
    assert os.path.exists(result['package_path'])
    assert result['package_path'].endswith('.zip')

@pytest.mark.integration
def test_multi_platform_packaging():
    """Test packaging for multiple platforms."""
    from skill_seekers.cli.adaptors import get_adaptor

    platforms = ['claude', 'gemini', 'openai', 'markdown']

    for platform in platforms:
        adaptor = get_adaptor(platform)
        package_path = adaptor.package(
            skill_dir='output/test-skill/',
            output_path='output/'
        )
        assert os.path.exists(package_path)
```

---

## Performance Optimization

### Async Scraping

```python
from skill_seekers.cli.doc_scraper import scrape_all

# Enable async for 2-3x speed improvement
pages = scrape_all(
    base_url='https://docs.example.com',
    selectors={'main_content': 'article'},
    config={'name': 'example'},
    use_async=True  # 2-3x faster
)
```

### Caching and Rebuilding

```python
from skill_seekers.cli.doc_scraper import build_skill

# First scrape (slow - 15-45 minutes)
build_skill(config_name='react', output_dir='output/react')

# Rebuild without re-scraping (fast - <1 minute)
build_skill(
    config_name='react',
    output_dir='output/react',
    data_dir='output/react_data',
    skip_scrape=True  # Use cached data
)
```

### Batch Processing

```python
from concurrent.futures import ThreadPoolExecutor
from skill_seekers.cli.install_skill import install_skill

configs = ['react', 'vue', 'angular', 'svelte']

def install_config(config_name):
    return install_skill(
        config_name=config_name,
        target='markdown',
        enhance=False,
        upload=False,
        force=True
    )

# Process 4 configs in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(install_config, configs))

for config, result in zip(configs, results):
    print(f"{config}: {result['success']}")
```

---

## CI/CD Integration Examples

### GitHub Actions

```yaml
name: Generate Skills

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
  workflow_dispatch:

jobs:
  generate-skills:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Skill Seekers
        run: pip install skill-seekers[all-llms]

      - name: Generate Skills
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          skill-seekers install react --target claude --enhance --upload
          skill-seekers install vue --target gemini --enhance --upload

      - name: Archive Skills
        uses: actions/upload-artifact@v3
        with:
          name: skills
          path: output/**/*.zip
```

### GitLab CI

```yaml
generate_skills:
  image: python:3.11
  script:
    - pip install skill-seekers[all-llms]
    - skill-seekers install react --target claude --enhance --upload
    - skill-seekers install vue --target gemini --enhance --upload
  artifacts:
    paths:
      - output/
  only:
    - schedules
```

---

## Best Practices

### 1. **Use Configuration Files**
Store configs in version control for reproducibility:
```python
import json
with open('configs/my-framework.json') as f:
    config = json.load(f)
scrape_all(config=config)
```

### 2. **Enable Async for Large Sites**
```python
pages = scrape_all(base_url=url, config=config, use_async=True)
```

### 3. **Cache Scraped Data**
```python
# Scrape once
scrape_all(config=config, output_dir='output/data')

# Rebuild many times (fast!)
build_skill(config_name='framework', data_dir='output/data', skip_scrape=True)
```

### 4. **Use Platform Adaptors**
```python
# Good: Platform-agnostic
adaptor = get_adaptor(target_platform)
adaptor.package(skill_dir)

# Bad: Hardcoded for one platform
# create_zip_for_claude(skill_dir)
```

### 5. **Handle Errors Gracefully**
```python
try:
    result = install_skill(config_name='framework', target='claude')
except NetworkError:
    # Retry logic
except InvalidConfigError:
    # Fix config
```

### 6. **Monitor Background Enhancements**
```python
# Start enhancement
enhance_skill(skill_dir='output/react/', mode='background')

# Monitor progress
monitor_enhancement('output/react/', watch=True)
```

---

## API Reference Summary

| API | Module | Use Case |
|-----|--------|----------|
| **Documentation Scraping** | `doc_scraper` | Extract from docs websites |
| **GitHub Analysis** | `github_scraper` | Analyze code repositories |
| **PDF Extraction** | `pdf_scraper` | Extract from PDF files |
| **Unified Scraping** | `unified_scraper` | Multi-source scraping |
| **Skill Packaging** | `adaptors` | Package for LLM platforms |
| **Skill Upload** | `adaptors` | Upload to platforms |
| **AI Enhancement** | `adaptors` | Improve skill quality |
| **Complete Workflow** | `install_skill` | End-to-end automation |

---

## Additional Resources

- **[Main Documentation](../../README.md)** - Complete user guide
- **[Usage Guide](../guides/USAGE.md)** - CLI usage examples
- **[MCP Setup](../guides/MCP_SETUP.md)** - MCP server integration
- **[Multi-LLM Support](../integrations/MULTI_LLM_SUPPORT.md)** - Platform comparison
- **[CHANGELOG](../../CHANGELOG.md)** - Version history and API changes

---

**Version:** 2.7.0
**Last Updated:** 2026-01-18
**Status:** ✅ Production Ready
