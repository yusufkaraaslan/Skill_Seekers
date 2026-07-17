# API Reference - Programmatic Usage

**Version:** 3.7.0
**Last Updated:** 2026-06-11
**Status:** ✅ Verified against v3.7.0 (every import and signature in this document was checked by importing it)

---

## Overview

Skill Seekers can be used programmatically for integration into other tools, automation scripts, and CI/CD pipelines. This guide covers the Python APIs available for developers who want to embed Skill Seekers functionality into their own applications.

> **Stability note — read this first**
>
> The **stable, supported interface of the PyPI package is the `skill-seekers` CLI** (and the MCP server). The Python API documented here is real and importable — it is the same code the CLI runs — but it tracks the implementation: module paths, signatures, and config-dict keys may change between minor releases. **Semver guarantees do not extend to these internals.** If you import these modules, pin an exact version (`skill-seekers==3.7.0`) and re-verify on upgrade.

**Use Cases:**
- Automated documentation skill generation in CI/CD
- Batch processing multiple documentation sources
- Custom skill generation workflows
- Integration with internal tooling
- Automated skill updates on documentation changes

Each example below is marked **[offline]** (no network, no AI), **[network]** (fetches remote content), or **[AI]** (calls an LLM API or spawns a local agent).

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

# All LLM platform support
pip install skill-seekers[all-llms]

# Everything (all source types + platforms, except video-full)
pip install skill-seekers[all]
```

### Development Installation

```bash
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd Skill_Seekers
pip install -e ".[all-llms]"
```

---

## Core APIs

### 1. Skill Conversion API (`get_converter`)

The primary programmatic entry point mirrors the `skill-seekers create` command: a factory returns a `SkillConverter` for any of the 18 source types, and `run()` executes the full extract → build pipeline.

```python
from skill_seekers.cli.skill_converter import get_converter, CONVERTER_REGISTRY

# get_converter(source_type: str, config: dict[str, Any]) -> SkillConverter
# SkillConverter.run() -> int   (0 = success, non-zero = failure)

print(sorted(CONVERTER_REGISTRY))
# ['asciidoc', 'chat', 'config', 'confluence', 'epub', 'github', 'html',
#  'jupyter', 'local', 'manpage', 'notion', 'openapi', 'pdf', 'pptx',
#  'rss', 'video', 'web', 'word']
```

#### Basic Usage — web documentation **[network]**

```python
from skill_seekers.cli.skill_converter import get_converter

config = {
    "name": "django",
    "description": "Use when working with Django web framework",
    "base_url": "https://docs.djangoproject.com/en/5.0/",
    "selectors": {"main_content": "article", "title": "h1", "code_blocks": "pre code"},
    "url_patterns": {"include": ["/en/5.0/"], "exclude": []},
    "max_pages": 50,
    "rate_limit": 0.5,
    "output_dir": "output/django",
}

converter = get_converter("web", config)
exit_code = converter.run()          # scrapes, then builds output/django/SKILL.md
print("ok" if exit_code == 0 else "failed")
```

#### Template method contract

`run()` is a template method on the `SkillConverter` base class:

1. `extract()` — source-specific extraction (scrape, parse, clone, …)
2. `build_skill()` — categorize content and write `SKILL.md` + `references/`

`run()` **returns an exit code instead of raising**: exceptions from `extract()`/`build_skill()` are logged and converted to return value `1`. Check the return value, not a `try/except`.

```python
converter = get_converter("pdf", {"name": "manual", "pdf_path": "manual.pdf"})

# Reuse existing on-disk extracted data (skip extraction, rebuild only):
converter.skip_scrape = True   # run() checks this attribute
converter.run()
```

#### Factory errors **[offline]**

- `ValueError` — unknown source type (message lists supported types)
- `RuntimeError` — the source type's optional dependency is not installed (message includes the `pip install` hint)

#### Unified config through the factory **[offline construction]**

The `"config"` source type wraps the multi-source `UnifiedScraper` (section 4) behind the same factory. It takes the **factory-shaped dict** — only `config_path` is required:

```python
from skill_seekers.cli.skill_converter import get_converter

scraper = get_converter("config", {
    "config_path": "configs/unified/react-unified.json",
    "output_dir": "output/react-complete",   # optional override
    "merge_mode": "rule-based",              # optional: 'rule-based' | 'claude-enhanced'
    "dry_run": True,                         # optional: preview sources, write nothing
})
scraper.run()
```

---

### 2. Source Detection API

`SourceDetector` is what `skill-seekers create` uses to auto-detect the source type from a raw input string. It returns a `SourceInfo` dataclass.

#### Basic Usage **[offline]**

```python
from skill_seekers.cli.source_detector import SourceDetector

detector = SourceDetector()

# detect(source: str) -> SourceInfo
info = detector.detect("https://docs.djangoproject.com/")
print(info.type)            # 'web'
print(info.parsed)          # {'url': 'https://docs.djangoproject.com/'}
print(info.suggested_name)  # 'djangoproject'
print(info.raw_input)       # original input string

detector.detect("fastapi/fastapi").type   # 'github'  -> parsed: {'repo': 'fastapi/fastapi'}
detector.detect("./manual.pdf").type      # 'pdf'     -> parsed: {'file_path': './manual.pdf'}
detector.detect("./my-project").type      # 'local'   -> parsed: {'directory': '/abs/path/my-project'}
detector.detect("configs/react.json").type  # 'config' -> parsed: {'config_path': 'configs/react.json'}
```

`SourceInfo` fields: `type`, `parsed` (dict, shape depends on `type`), `suggested_name`, `raw_input`.

Note: local-directory detection requires the path to exist on disk — a non-existent `./name` falls through to other detectors (e.g. `owner/repo` GitHub shorthand).

#### Detect-then-convert pipeline **[network for web/github]**

```python
from skill_seekers.cli.source_detector import SourceDetector
from skill_seekers.cli.skill_converter import get_converter

info = SourceDetector().detect("./manual.pdf")

config = {
    "name": info.suggested_name,
    "pdf_path": info.parsed["file_path"],
    "output_dir": f"output/{info.suggested_name}",
}
get_converter(info.type, config).run()
```

(The CLI's `create_command.py:_build_config()` is the canonical mapping from `SourceInfo.parsed` to each converter's config keys.)

---

### 3. Direct Converter Construction

Every converter class can be constructed directly with a config dict (the factory does nothing more than registry lookup + optional-dependency check). The config keys below are read by each converter's `__init__` and are verified against v3.7.0.

#### PDF — `PDFToSkillConverter` **[offline — local file processing]**

```python
from skill_seekers.cli.pdf_scraper import PDFToSkillConverter

converter = PDFToSkillConverter({
    "name": "product-manual",                  # required
    "pdf_path": "manual.pdf",                  # path to the PDF
    "description": "Product manual reference", # optional
    "output_dir": "output/product-manual",     # optional (default: output/<name>)
    "extract_options": {                       # optional
        "chunk_size": 10,         # pages per chunk
        "min_quality": 5.0,       # quality threshold for extracted text
        "extract_images": True,
        "min_image_size": 100,
    },
    "categories": {},                          # optional keyword mapping
})
converter.run()
```

#### Web — `DocToSkillConverter` **[network]**

```python
from skill_seekers.cli.doc_scraper import DocToSkillConverter

converter = DocToSkillConverter({
    "name": "react",                                  # required
    "base_url": "https://react.dev/",                 # required
    "selectors": {"main_content": "article", "title": "h1", "code_blocks": "pre code"},
    "url_patterns": {"include": ["/learn", "/reference"], "exclude": ["/blog"]},
    "categories": {},          # optional; smart categorization fills the gap
    "rate_limit": 0.5,         # seconds between requests
    "max_pages": 200,          # -1 = unlimited
    "start_urls": [],          # optional explicit seed URLs
    "llms_txt_url": None,      # optional llms.txt source
    "browser": False,          # Playwright rendering for JS-heavy sites
    "workers": 1,              # parallel scrape workers
    "async_mode": False,       # asyncio scraping (faster on large sites)
    "doc_version": "",         # stamped into SKILL.md metadata
    "output_dir": "output/react",
})
converter.run()
```

Constructor also accepts `dry_run=True` / `resume=True` keyword arguments (or the same keys in the config dict).

#### GitHub — `GitHubScraper` **[network — GitHub API; set `GITHUB_TOKEN` for higher rate limits]**

```python
from skill_seekers.cli.github_scraper import GitHubScraper

converter = GitHubScraper({
    "repo": "fastapi/fastapi",        # required, owner/repo
    "name": "fastapi",                # optional (default: repo short name)
    "local_repo_path": None,          # optional local clone => unlimited analysis, no API limits
    "include_code": True,
    "include_issues": True,
    "max_issues": 20,                 # token economy: keep issue payload small
    "max_comments": 0,
    "issue_labels": [],               # filter issues by label
    "issue_state": "open",            # 'open' | 'closed' | 'all' (open-only by default)
    "include_issue_labels": False,    # include per-issue labels (off = less bloat)
    "include_issue_milestones": False,  # include per-issue milestone
    "include_changelog": True,
    "include_releases": True,
    "output_dir": "output/fastapi",
})
converter.run()
```

The remaining 15 converters follow the same pattern; see `CONVERTER_REGISTRY` in `src/skill_seekers/cli/skill_converter.py` for the module/class of each, and each class's `__init__` for its config keys (e.g. `word` reads `docx_path`, `local` reads `directory` + the C3.x `detect_patterns`/`extract_test_examples`/… toggles).

---

### 4. Unified Multi-Source Scraping API

`UnifiedScraper` combines multiple sources (any of the 18 supported types) into a single merged skill. It is itself a `SkillConverter` (registered as source type `"config"`).

#### Construction forms

```python
from skill_seekers.cli.unified_scraper import UnifiedScraper

# 1. Path to a unified config JSON file
scraper = UnifiedScraper("configs/unified/react-unified.json")

# 2. Already-loaded unified config dict (name + description required)
scraper = UnifiedScraper({"name": "react-complete", "description": "...", "sources": [...]})

# 3. Factory-shaped dict (what get_converter("config", ...) passes through)
scraper = UnifiedScraper({"config_path": "configs/unified/react-unified.json"})

# Keyword overrides (win over the config file's values)
scraper = UnifiedScraper(
    "configs/unified/react-unified.json",
    merge_mode="rule-based",        # or 'claude-enhanced' (AI merge)
    output_dir="output/react-complete",
    dry_run=False,
)
```

#### Running **[network — scrapes each source; AI if merge_mode='claude-enhanced']**

```python
scraper = UnifiedScraper("configs/unified/react-unified.json")
scraper.run()    # scrape all sources -> merge -> detect conflicts -> build skill
```

#### Dry run preview **[offline]**

```python
UnifiedScraper("configs/unified/react-unified.json", dry_run=True).run()
# Logs the sources that WOULD be scraped and the output directory; writes nothing.
```

#### Conflict detection

Conflict detection is a **method on the instance**, not a module-level function. It is called automatically by `run()` after merging; you can also drive the phases manually:

```python
scraper = UnifiedScraper("configs/unified/react-unified.json")
scraper.scrape_all_sources()              # [network]
merged = scraper.merge_sources()
conflicts = scraper.detect_conflicts()    # -> list of conflict records
scraper.build_skill(merged)
```

---

### 5. Skill Packaging API

Package skills for different platforms using the adaptor architecture (Strategy + Factory).

#### Basic Packaging **[offline]**

```python
from pathlib import Path
from skill_seekers.cli.adaptors import get_adaptor, ADAPTORS

# get_adaptor(platform: str, config: dict = None) -> SkillAdaptor
print(sorted(ADAPTORS))
# ['atlas', 'chroma', 'claude', 'deepseek', 'faiss', 'fireworks', 'gemini',
#  'haystack', 'ibm-bob', 'kimi', 'langchain', 'llama-index', 'markdown',
#  'minimax', 'openai', 'opencode', 'openrouter', 'pinecone', 'qdrant',
#  'qwen', 'together', 'weaviate']

adaptor = get_adaptor("claude")

# package(skill_dir: Path, output_path: Path, ...) -> Path
package_path = adaptor.package(Path("output/react"), Path("output"))
print(package_path)   # output/react.zip
```

`get_adaptor` raises `ValueError` for an unknown platform, and `ImportError` if the platform's optional dependency is missing (with an install hint).

#### Packaging with chunking (RAG/vector targets) **[offline]**

```python
package_path = adaptor.package(
    Path("output/react"),
    Path("output"),
    enable_chunking=True,        # split content into token-bounded chunks
    chunk_max_tokens=512,
    preserve_code_blocks=True,   # never split inside a code fence
    chunk_overlap_tokens=50,
)
```

#### Multi-Platform Packaging **[offline]**

```python
from pathlib import Path
from skill_seekers.cli.adaptors import get_adaptor

for platform in ["claude", "gemini", "openai", "markdown"]:
    adaptor = get_adaptor(platform)
    pkg = adaptor.package(Path("output/react"), Path("output"))
    print(f"{platform}: {pkg}")
```

#### Formatting and capability checks **[offline]**

```python
from pathlib import Path
from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.adaptors.base import SkillAdaptor, SkillMetadata

adaptor = get_adaptor("claude")

adaptor.PLATFORM               # 'claude'
adaptor.supports_upload()      # True
adaptor.supports_enhancement() # True
adaptor.get_env_var_name()     # 'ANTHROPIC_API_KEY'

# format_skill_md(skill_dir: Path, metadata: SkillMetadata) -> str
meta = SkillMetadata(name="my-skill", description="When to use this skill")
text = adaptor.format_skill_md(Path("output/my-skill"), meta)
```

`SkillMetadata` fields: `name`, `description`, `version` (default `"1.0.0"`), `doc_version`, `author`, `tags`.

#### Shared Embedding Methods

The base `SkillAdaptor` class provides two shared embedding helpers inherited by all vector database adaptors (chroma, weaviate, pinecone, qdrant, faiss):

- `_generate_openai_embeddings(texts, model)` — generate embeddings via the OpenAI API. **[network]**
- `_generate_st_embeddings(texts, model)` — generate embeddings using a local sentence-transformers model. **[offline]**

These are underscore-prefixed (internal) but shared deliberately, so vector adaptors do not re-implement embedding logic.

---

### 6. Skill Upload API

Upload packaged skills to LLM platforms via their APIs. Signature on the base class:

```python
# upload(package_path: Path, api_key: str, **kwargs) -> dict[str, Any]
```

The returned dict's keys are **platform-specific** — inspect the concrete adaptor's `upload()` (e.g. `src/skill_seekers/cli/adaptors/claude.py`) for the exact shape. Check `adaptor.supports_upload()` first: adaptors that don't support upload (e.g. `markdown`) return a result dict with `"success": False` and an explanatory `"message"` instead of uploading.

#### Claude AI Upload **[network — Anthropic API]**

```python
import os
from pathlib import Path
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor("claude")
result = adaptor.upload(
    Path("output/react.zip"),
    api_key=os.environ["ANTHROPIC_API_KEY"],
)
```

#### Google Gemini Upload **[network — requires `pip install skill-seekers[gemini]`]**

```python
adaptor = get_adaptor("gemini")
result = adaptor.upload(Path("output/react.tar.gz"), api_key=os.environ["GOOGLE_API_KEY"])
```

#### OpenAI Upload **[network — requires `pip install skill-seekers[openai]`]**

```python
adaptor = get_adaptor("openai")
result = adaptor.upload(Path("output/react-openai.zip"), api_key=os.environ["OPENAI_API_KEY"])
```

Use `adaptor.get_env_var_name()` to discover which environment variable a platform conventionally reads, and `adaptor.validate_api_key(key)` for a cheap format check before uploading.

---

### 7. AI Enhancement API

Enhance skills with AI-powered improvements. All API-mode enhancement routes
through the shared `AgentClient` (`skill_seekers.cli.agent_client`), which
centralizes provider selection (Anthropic/Gemini/OpenAI/Moonshot), model and
base-URL overrides, the truncation gate, timeout policy, and atomic
backup-then-save of SKILL.md.

#### API Mode Enhancement (per-platform adaptor) **[AI — provider API call]**

```python
import os
from pathlib import Path
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('claude')  # also: gemini, openai, and OpenAI-compatible targets

# Enhance SKILL.md via the platform's API (returns True on success).
# The original is backed up to SKILL.md.backup and the save is atomic.
ok = adaptor.enhance(
    Path('output/react/'),
    os.getenv('ANTHROPIC_API_KEY'),
)
```

#### Direct AgentClient usage **[AI]**

```python
from skill_seekers.cli.agent_client import AgentClient

client = AgentClient(mode='api')          # or mode='local' (spawns a local agent)
reply = client.call('Summarize this skill...', timeout=600)
```

`AgentClient(mode='auto'|'api'|'local', agent=None, api_key=None, provider=None, base_url=None, model=None)`; `call(prompt, max_tokens=4096, timeout=None, output_file=None, cwd=None, system=None, temperature=None) -> str | None`. Also: `is_available()`, `get_model()`, `detect_api_key()`.

#### LOCAL Mode Enhancement (local coding agent, free) **[AI — spawns local agent]**

```python
from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

enhancer = LocalSkillEnhancer(
    'output/react/',
    agent='claude',        # claude, codex, copilot, opencode, kimi, custom
)
enhancer.run(background=True)   # or headless=True (default), daemon=True
```

Monitor background runs from the CLI:

```bash
skill-seekers enhance-status output/react/ --watch
```

> LOCAL mode sets `SKILL_SEEKER_ENHANCE_ACTIVE=1` in the spawned agent's
> environment and refuses to start when it is already set, preventing
> recursive agent spawns.

---

### 8. Execution Context

`ExecutionContext` is the centralized, pydantic-validated settings singleton the CLI builds from argparse + config files. Converters and enhancement read from it; programmatic callers can initialize and override it.

```python
from skill_seekers.cli.execution_context import ExecutionContext

# Classmethods:
#   initialize(args=None, config_path=None, source_info=None) -> ExecutionContext
#   get() -> ExecutionContext          (active override, else base singleton)
#   is_initialized() -> bool
#   reset() -> None                    (mainly for tests)

ExecutionContext.is_initialized()   # False until initialize() is called
ctx = ExecutionContext.initialize() # defaults when args is None

ctx.enhancement.level    # 2
ctx.scraping.max_pages   # -1 (unlimited)
ctx.output.output_dir    # None
ctx.analysis.depth       # 'surface'
```

#### Temporary overrides (context manager) **[offline]**

`override(**kwargs)` is a context manager; double-underscore keys address nested settings groups (`source`, `enhancement`, `output`, `scraping`, `analysis`). Overrides are **context-local** (stored in a `contextvars.ContextVar`), so concurrent asyncio tasks each see only their own override, and nested overrides stack and unwind cleanly:

```python
ctx = ExecutionContext.get()

with ctx.override(enhancement__level=3, scraping__max_pages=100):
    active = ExecutionContext.get()
    assert active.enhancement.level == 3      # inside: overridden

assert ExecutionContext.get().enhancement.level == 2  # outside: restored
```

Caveat: contextvars flow into asyncio tasks automatically but into worker threads only via `contextvars.copy_context().run(...)` — a bare `threading.Thread` sees the base singleton, not your override.

---

### 9. Services Layer (`skill_seekers.services`)

Domain logic shared by the CLI and the MCP server. Importable **without** the `[mcp]` extra. Import from the submodules:

```python
from skill_seekers.services.marketplace_manager import MarketplaceManager
from skill_seekers.services.source_manager import SourceManager
from skill_seekers.services.config_publisher import ConfigPublisher, detect_category
from skill_seekers.services.git_repo import GitConfigRepo
```

#### Marketplace registry CRUD **[offline — local registry file]**

```python
mm = MarketplaceManager()        # or MarketplaceManager(config_dir="~/.skill-seekers")
mm.list_marketplaces()           # -> list[dict]; also: add/get/update/remove_marketplace
```

#### Config source registry CRUD **[offline]**

```python
sm = SourceManager()
sm.list_sources()                # also: add/get/update/remove_source
```

#### Config category detection **[offline]**

```python
detect_category({"name": "react", "description": "React frontend UI library docs"})
# 'web-frameworks'   (keyword scoring over CATEGORY_KEYWORDS)
```

#### Git-backed config repositories **[network — clones/pulls]**

```python
repo = GitConfigRepo()                       # or GitConfigRepo(cache_dir=...)
repo.validate_git_url("https://github.com/owner/configs.git")   # offline check
path = repo.clone_or_pull("https://github.com/owner/configs.git")  # [network]
configs = repo.find_configs(path)
```

`ConfigPublisher` (`ConfigPublisher(cache_dir=None)`) pushes configs to registered config-source repos; `MarketplacePublisher` publishes packaged skills to plugin-marketplace repos. Both perform git pushes **[network]**.

---

## Configuration Objects

The full config-file schema (single-source and unified) is documented in **[CONFIG_FORMAT.md](CONFIG_FORMAT.md)** — that is the authoritative reference. Summary:

### Web (single-source) config keys

These are the keys `DocToSkillConverter` reads (same dict whether loaded from a `configs/*.json` file or built in code):

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | *required* | Skill name (alphanumeric + hyphens) |
| `base_url` | string | *required* | Documentation website URL |
| `description` | string | generated | When to use this skill |
| `selectors` | object | `{}` | CSS selectors (`main_content`, `title`, `code_blocks`) |
| `url_patterns` | object | `{}` | `include` / `exclude` URL substring lists |
| `categories` | object | `{}` | Category keywords mapping |
| `rate_limit` | float | `0.5` | Delay between requests (seconds) |
| `max_pages` | int | `-1` | Maximum pages to scrape (-1 = unlimited) |
| `start_urls` | array | `[]` | Explicit seed URLs |
| `llms_txt_url` | string | `null` | URL to llms.txt file |
| `async_mode` | bool | `false` | Asyncio scraping (faster on large sites) |
| `browser` | bool | `false` | Playwright rendering for JS-heavy sites |
| `workers` | int | `1` | Parallel scrape workers |
| `output_dir` | string | `output/<name>` | Where the skill is written |

### Unified Config Schema (Multi-Source)

Supports all 18 source types: `documentation`, `github`, `pdf`, `local`, `word`, `video`, `epub`, `jupyter`, `html`, `openapi`, `asciidoc`, `pptx`, `rss`, `manpage`, `confluence`, `notion`, `chat`, `config`.

```json
{
  "name": "framework-unified",
  "description": "Complete framework documentation",
  "merge_mode": "rule-based",
  "sources": [
    {
      "type": "documentation",
      "base_url": "https://docs.example.com/",
      "selectors": { "main_content": "article" }
    },
    {
      "type": "github",
      "repo": "org/repo",
      "include_code": true
    },
    {
      "type": "pdf",
      "path": "manual.pdf"
    },
    {
      "type": "openapi",
      "path": "specs/openapi.yaml"
    },
    {
      "type": "video",
      "url": "https://www.youtube.com/watch?v=example"
    },
    {
      "type": "jupyter",
      "path": "notebooks/examples.ipynb"
    },
    {
      "type": "confluence",
      "base_url": "https://company.atlassian.net/wiki",
      "space_key": "DOCS"
    }
  ]
}
```

Configs are validated on load by `skill_seekers.cli.config_validator.validate_config(config_path)`, which the CLI and `UnifiedScraper` call for you.

---

## Error Handling

The Python API signals failure three different ways — match on the layer you call:

```python
from pathlib import Path
from skill_seekers.cli.skill_converter import get_converter
from skill_seekers.cli.adaptors import get_adaptor

# 1. Factory-time errors RAISE:
try:
    converter = get_converter("web", config)
except ValueError as e:      # unknown source type
    print(e)
except RuntimeError as e:    # missing optional dependency (includes pip install hint)
    print(e)

try:
    adaptor = get_adaptor("chroma")
except ValueError as e:      # unknown platform
    print(e)
except ImportError as e:     # optional dependency not installed
    print(e)

# 2. Conversion errors are RETURN CODES (run() catches and logs exceptions):
if converter.run() != 0:
    raise SystemExit("skill build failed — see log output")

# 3. Adaptor operations either RAISE (network/API errors during real uploads)
#    or report failure in the returned dict — gate on capability and check
#    result["success"]:
if adaptor.supports_upload():
    result = adaptor.upload(Path("output/react.zip"), api_key=key)
    if not result.get("success"):
        print(result.get("message"))
```

There is no `skill_seekers.exceptions` module — standard exceptions (`ValueError`, `RuntimeError`, `ImportError`, `FileNotFoundError`) are used throughout.

---

## Testing Your Integration

Use `dry_run` and small `max_pages` limits to keep tests fast and offline-friendly:

```python
from skill_seekers.cli.skill_converter import get_converter
from skill_seekers.cli.source_detector import SourceDetector


def test_source_detection():            # [offline]
    info = SourceDetector().detect("https://docs.example.com/")
    assert info.type == "web"
    assert info.parsed["url"] == "https://docs.example.com/"


def test_unified_dry_run(tmp_path):     # [offline] — previews without scraping
    import json
    cfg = tmp_path / "unified.json"
    cfg.write_text(json.dumps({
        "name": "test",
        "description": "Test skill",   # name + description are required
        "sources": [{"type": "github", "repo": "owner/repo"}],
    }))
    scraper = get_converter("config", {"config_path": str(cfg), "dry_run": True})
    assert scraper.run() == 0


def test_packaging(tmp_path):           # [offline]
    from pathlib import Path
    from skill_seekers.cli.adaptors import get_adaptor

    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\nname: t\ndescription: d\n---\n# T\n")
    pkg = get_adaptor("markdown").package(skill, tmp_path)
    assert pkg.exists()
```

---

## Performance Notes

- **Async scraping**: set `"async_mode": True` in a web config for 2–3x faster scraping on large sites; `"workers": N` parallelizes the thread-based scraper.
- **Rebuild without re-scraping**: set `converter.skip_scrape = True` before `run()` to rebuild `SKILL.md` from existing on-disk extracted data (`output/<name>_data/`).
- **Resume**: web configs support checkpointing — pass `resume=True` to `DocToSkillConverter` (or `"resume": True` in the config) to continue an interrupted scrape.
- **Batch processing**: converters are independent; run several `get_converter(...).run()` calls in a `ThreadPoolExecutor`. Don't share one `ExecutionContext.override()` across plain threads (see section 8 caveat).

---

## CI/CD Integration Examples

For pipelines, prefer the CLI — it is the stable interface:

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
          skill-seekers install --config react --target claude
          skill-seekers install --config vue --target gemini

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
    - skill-seekers install --config react --target claude
    - skill-seekers install --config vue --target gemini --no-upload
  artifacts:
    paths:
      - output/
  only:
    - schedules
```

---

## Best Practices

### 1. **Prefer the CLI for automation; pin the version for Python imports**
```bash
pip install skill-seekers==3.7.0   # internals can shift between minors
```

### 2. **Use the factory, not hardcoded classes**
```python
# Good: registry-driven
converter = get_converter(info.type, config)
adaptor = get_adaptor(target_platform)

# Brittle: hardcoded imports break when modules move
```

### 3. **Check run() return codes**
```python
if get_converter("web", config).run() != 0:
    raise SystemExit(1)   # run() logs the exception; it does not re-raise
```

### 4. **Cache scraped data, rebuild cheaply**
```python
converter = get_converter("web", config)
converter.run()                 # first run: scrape + build (slow)

converter = get_converter("web", config)
converter.skip_scrape = True
converter.run()                 # rebuild from output/<name>_data/ (fast)
```

### 5. **Probe adaptor capabilities before calling**
```python
adaptor = get_adaptor(platform)
if adaptor.supports_upload():
    adaptor.upload(pkg, api_key=os.environ[adaptor.get_env_var_name()])
```

### 6. **Use dry runs in tests**
```python
get_converter("config", {"config_path": cfg, "dry_run": True}).run()
```

---

## API Reference Summary

| API | Import | Use Case |
|-----|--------|----------|
| **Skill conversion factory** | `skill_seekers.cli.skill_converter.get_converter` | Any of the 18 source types → skill |
| **Converter registry** | `skill_seekers.cli.skill_converter.CONVERTER_REGISTRY` | Source type → (module, class) lookup |
| **Source detection** | `skill_seekers.cli.source_detector.SourceDetector` | Auto-detect type from raw input |
| **Web docs** | `skill_seekers.cli.doc_scraper.DocToSkillConverter` | Documentation websites |
| **GitHub repos** | `skill_seekers.cli.github_scraper.GitHubScraper` | Code + docs + community analysis |
| **PDF** | `skill_seekers.cli.pdf_scraper.PDFToSkillConverter` | PDF documents |
| **Local codebase** | `skill_seekers.cli.codebase_scraper.CodebaseAnalyzer` | Local directories (C3.x pipeline) |
| **Multi-source** | `skill_seekers.cli.unified_scraper.UnifiedScraper` | Merge 18 source types + conflict detection |
| **Packaging / upload / enhance** | `skill_seekers.cli.adaptors.get_adaptor` | 22 platform targets |
| **AI enhancement** | `skill_seekers.cli.agent_client.AgentClient` | API or local-agent LLM calls |
| **Local-agent enhancement** | `skill_seekers.cli.enhance_skill_local.LocalSkillEnhancer` | Free enhancement via coding agents |
| **Settings singleton** | `skill_seekers.cli.execution_context.ExecutionContext` | Initialize / get / override settings |
| **Marketplace registry** | `skill_seekers.services.marketplace_manager.MarketplaceManager` | Marketplace CRUD |
| **Config sources** | `skill_seekers.services.source_manager.SourceManager` | Config source registry CRUD |
| **Config publishing** | `skill_seekers.services.config_publisher` | Push configs; `detect_category()` |
| **Git config repos** | `skill_seekers.services.git_repo.GitConfigRepo` | Clone/pull + config discovery |

The other 14 converter classes (word, epub, video, jupyter, html, openapi, asciidoc, pptx, rss, manpage, confluence, notion, chat) are listed in `CONVERTER_REGISTRY`.

---

## Additional Resources

- **[Main Documentation](../../README.md)** - Complete user guide
- **[CLI Reference](CLI_REFERENCE.md)** - The stable command-line interface
- **[Config Format](CONFIG_FORMAT.md)** - Authoritative config schema
- **[MCP Setup](../guides/MCP_SETUP.md)** - MCP server integration
- **[Multi-LLM Support](../integrations/MULTI_LLM_SUPPORT.md)** - Platform comparison
- **[CHANGELOG](../../CHANGELOG.md)** - Version history and API changes

---

**Version:** 3.7.0
**Last Updated:** 2026-06-11
