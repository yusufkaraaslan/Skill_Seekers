# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Skill Seekers** converts documentation from 18 source types into production-ready formats for 21+ AI platforms (LLM platforms, RAG frameworks, vector databases, AI coding assistants). Published on PyPI as `skill-seekers`.

**Version:** 3.9.0 (dev; last release 3.8.0) — source of truth is `src/skill_seekers/_version.py` | **Python:** 3.10+ | **Website:** https://skillseekersweb.com/

**Architecture:** See `docs/UML_ARCHITECTURE.md` for UML diagrams and module overview. StarUML project at `docs/UML/skill_seekers.mdj`. Refactor state/history: `docs/UNIFICATION_PLAN.md` (Grand Unification — all 5 phases done; remaining cosmetic items listed there).

## Essential Commands

```bash
# REQUIRED before running tests or CLI (src/ layout)
pip install -e .

# Run all tests (NEVER skip - all must pass before commits)
pytest tests/ -v

# Fast iteration (skip slow MCP tests ~20min)
pytest tests/ --ignore=tests/test_mcp_fastmcp.py --ignore=tests/test_mcp_server.py --ignore=tests/test_install_skill_e2e.py -q

# Single test
pytest tests/test_scraper_features.py::test_detect_language -vv -s

# Code quality (must pass before push - matches CI)
uvx ruff check src/ tests/
uvx ruff format --check src/ tests/
mypy src/skill_seekers  # continue-on-error in CI

# Auto-fix lint/format issues
uvx ruff check --fix --unsafe-fixes src/ tests/
uvx ruff format src/ tests/

# Build & publish
uv build
uv publish
```

## CI Matrix

Runs on push/PR to `main` or `development`. Lint job (Python 3.12, Ubuntu) + Test job (Ubuntu + macOS, Python 3.10/3.11/3.12, excludes macOS+3.10). Both must pass for merge.

## Git Workflow

- **Main branch:** `main` (requires tests + 1 review)
- **Development branch:** `development` (default PR target, requires tests)
- **Feature branches:** `feature/{task-id}-{description}` from `development`
- PRs always target `development`, never `main` directly

## Architecture

### CLI: Unified create command

Entry point `src/skill_seekers/cli/main.py`. The `create` command is the **primary** entry point for skill creation — it auto-detects source type and routes to the appropriate `SkillConverter`. The `scan` command (added in #327) is a separate discovery step for projects with multiple frameworks; it emits one config file per detected framework and you then run `create` on each.

```
skill-seekers create <source>     # Auto-detect: URL, owner/repo, ./path, file.pdf, etc.
skill-seekers scan <dir>          # AI-driven discovery → emits one config per detected framework + <project>-codebase.json
skill-seekers package <dir>       # Package for platform (--target claude/gemini/openai/markdown/minimax/opencode/kimi/deepseek/qwen/openrouter/together/fireworks/atlas/langchain/llama-index/haystack/chroma/faiss/weaviate/qdrant/pinecone/ibm-bob)
```

### Scan command (issue #327)

`skill-seekers scan <dir>` is an AI-driven project knowledge-base bootstrapper. Pipeline in `src/skill_seekers/cli/scan_command.py`:

1. `collect_signals()` in `signal_collectors.py` — deterministic, bounded gathering of manifests + README + Dockerfile/CI + sampled source files + git remote. **Per-kind byte budgets** (24 KB manifest / 6 KB README / 6 KB CI / 28 KB samples, total 64 KB) so a fat package.json can't crowd out other kinds. `_SOURCE_DIRS` covers ~14 layouts (Go `cmd/`, Rust `crates/`, JS monorepo `apps/packages/`, Maven `source/`, Django at root); also walks root one level deep for flat-layout Python.
2. `detect_with_ai(bundle, AgentClient)` — one LLM call, structured JSON output. **Source signals are first-2-KB of each file** (whole-file sampling, no regex parsing — added in WS4 because regex missed Go multi-line imports + Rust `mod`/`extern crate`). Canonical-slug prompt + the canonical-name resolver are coupled — change one, update the other.
3. `resolve_or_generate_with_status()` — for each detection: try `out_dir/<slug>.json` (cache from prior run), then `resolve_config_path` from `config_fetcher` with multiple canonical name candidates (`_canonical_name_candidates` handles `"Godot Engine"` → `"godot"`, plus CJK / European suffixes like `"Godot 引擎"`, `"React フレームワーク"`, `"Lodash Bibliothek"`), then `generate_config_with_ai` as the last resort. Always appends `.json` to lookup names so local-disk and user-dir resolution actually finds files. Always stamps `metadata.detected_version` (nested, not top-level — `metadata.version` already exists and means config-schema version).
4. `emit_codebase_config()` — always writes `<project>-codebase.json` (a `type: local` source pointed at the project root).
5. `diff_against_existing()` — keyed by **filename slug** (not internal `data["name"]`) so re-scans don't churn when the AI returns a display name vs the registry canonical slug.
6. `_archive_removed()` — when a config disappears from detections, MOVE (not delete — user may have hand-edited) to `out_dir/.archived/<UTC-timestamp>/`. Runs after diff, before fresh writes.
7. `maybe_publish()` — **native async** (WS11). Opt-in submission of freshly AI-generated configs to the community registry. Pre-checks `GITHUB_TOKEN`. Idempotency guard: `_find_existing_issue` queries GitHub Search API for an existing open issue with the same config name before submitting. Retries transient failures (rate limit, 5xx) with 0s/5s/15s backoff. `_prompt_async` wraps `input()` via `asyncio.to_thread` so the event loop isn't blocked.

**CLI dispatch** uses the `COMMAND_CLASSES` table in `main.py` (added in WS1). `scan` and `doctor` are dispatched as `Cls(args).execute()` consuming the parsed argparse namespace directly — no `_reconstruct_argv` hack, no duplicate argparse. `ScanCommand.execute()` is the single `asyncio.run` boundary wrapping `run_scan` (sync) + `maybe_publish` (async). Remaining ~14 commands still use the legacy `COMMAND_MODULES` dispatch; they're flagged for migration.

**Cost guardrails**: `--max-ai-generations N` (default 10) caps unbounded AI generation; `--dry-run` previews without writing or invoking AI; `--probe-urls` HEAD-checks AI-generated URLs with retry-on-404 and stamps `metadata._url_unverified` on confirmed-bad URLs.

**Safety**: All writes use `_atomic_write_json` (`os.replace` after writing to `.tmp`) so a `KeyboardInterrupt` mid-write can't corrupt configs. `_safe_size` guards `stat()` so broken symlinks don't crash the scan. `ScanCommand.execute` calls `logging.basicConfig` so `logger.warning`/`error` is visible; exit code is non-zero when no configs and no codebase config were emitted.

**Public constant**: `SourceDetector.CODE_PROJECT_MARKERS` (was `_CODE_PROJECT_MARKERS`) — shared between source_detector + signal_collectors. ~50 manifest types now (Pipfile, environment.yml, deno.json, flake.nix, Chart.yaml, deps.edn, dune-project, BUILD.bazel, …). Public so cross-module access doesn't reach into a private attribute.

### SkillConverter Pattern (Template Method + Factory)

All 18 source types implement the `SkillConverter` base class (`skill_converter.py`):

```python
converter = get_converter("web", config)  # Factory lookup
converter.run()  # Template: extract() → build_skill()
```

Registry in `CONVERTER_REGISTRY` maps source type → (module, class). `create_command.py` builds config from `ExecutionContext`, calls `get_converter()`, then runs centralized enhancement. `get_converter("config", {...})` constructs `UnifiedScraper` from the same factory-shaped dict (no special cases in create_command/MCP). The base resolves `skill_dir` once (strips trailing separators) and derives `data_file` via `data_file_for()` — subclasses must not re-derive paths.

### DocumentSkillBuilder (build side of 9 document scrapers)

`cli/document_skill_builder.py:DocumentSkillBuilder` sits between `SkillConverter` and the 9 document scrapers (epub, word, pptx, html, pdf, jupyter, man, rss, chat). It owns `categorize_content`, reference-file writing (tables, truncation, image guard), `index.md` + `SKILL.md` generation, and `load_extracted_data`. Variation points are class attrs (`DOC_NOUN`, `SOURCE_LABEL`, `LOAD_TOTAL_KEY`, `PATTERN_KEYWORDS`, `RANGE_LABEL`, …) and small hook methods (`category_stem`, `_write_reference_section`, `_write_skill_md_metadata`). Output is pinned **byte-identical** by golden trees in `tests/golden/phase2/` — `UPDATE_GOLDENS=1` rewrites them, only do that deliberately. Surviving full-method overrides are domain-shaped and commented per scraper.

### UnifiedScraper (multi-source configs)

`unified_scraper.py` dispatches via the class-level `SOURCE_DISPATCH` table; `_scrape_with_converter()` is the shared engine for the 13 mechanical source types (`get_converter()` + public `converter.extract()` + cache copy + sub-skill build), so **new types registered in `CONVERTER_REGISTRY` work in unified configs automatically**. documentation/github/local stay bespoke (commented why). `run()` deliberately does NOT follow the base template (TestRunOrchestration pins that run() triggers workflows).

### Data Flow (5 phases)

1. **Scrape** - Source-specific scraper extracts content to `output/{name}_data/pages/*.json`
2. **Build** - `build_skill()` categorizes pages, extracts patterns, generates `output/{name}/SKILL.md`
3. **Enhance** (optional) - LLM rewrites SKILL.md (`--enhance-level 0-3`, auto-detects API vs LOCAL mode)
4. **Package** - Platform adaptor formats output (`.zip`, `.tar.gz`, JSON, vector index)
5. **Upload** (optional) - Platform API upload

### Platform Adaptor Pattern (Strategy + Factory)

Factory: `get_adaptor(platform, config)` in `adaptors/__init__.py` returns a `SkillAdaptor` instance. Base class `SkillAdaptor` + `SkillMetadata` in `adaptors/base.py`.

```
src/skill_seekers/cli/adaptors/
├── __init__.py              # Factory: get_adaptor(platform, config), ADAPTORS registry
├── base.py                  # Abstract base: SkillAdaptor, SkillMetadata
├── openai_compatible.py     # Shared base for OpenAI-compatible platforms
├── claude.py                # --target claude
├── gemini.py                # --target gemini
├── openai.py                # --target openai
├── markdown.py              # --target markdown
├── minimax.py               # --target minimax
├── opencode.py              # --target opencode
├── kimi.py                  # --target kimi
├── deepseek.py              # --target deepseek
├── qwen.py                  # --target qwen
├── openrouter.py            # --target openrouter
├── together.py              # --target together
├── fireworks.py             # --target fireworks
├── langchain.py             # --target langchain
├── llama_index.py           # --target llama-index
├── haystack.py              # --target haystack
├── chroma.py                # --target chroma
├── faiss_helpers.py         # --target faiss
├── qdrant.py                # --target qdrant
├── weaviate.py              # --target weaviate
├── pinecone_adaptor.py      # --target pinecone
└── streaming_adaptor.py     # --target streaming
```

All adaptors use `--target`. All adaptors are imported with `try/except ImportError` so missing optional deps don't break the registry.

### 18 Source Type Converters

Each in `src/skill_seekers/cli/{type}_scraper.py` as a `SkillConverter` subclass (no `main()`). The `create_command.py` uses `source_detector.py` to auto-detect, then calls `get_converter()`. Converters: web (doc_scraper), github, pdf, word, epub, video, local (codebase_scraper), jupyter, html, openapi, asciidoc, pptx, rss, manpage, confluence, notion, chat, config (unified_scraper).

### CLI Argument System (single-definition parsers)

```
src/skill_seekers/cli/
├── parsers/              # Central SubcommandParser classes — the ONLY definition of each command's flags
│   └── create_parser.py  # Progressive help disclosure (--help-web, --help-github, etc.)
├── arguments/            # Argument definitions
│   ├── common.py         # add_all_standard_arguments() - shared across all scrapers
│   └── create.py         # UNIVERSAL_ARGUMENTS, WEB_ARGUMENTS, GITHUB_ARGUMENTS, etc.
├── exit_codes.py         # EXIT_SUCCESS/ERROR/VALIDATION/INTERRUPT
└── source_detector.py    # Auto-detect source type from input string
```

Command modules' standalone `main(args=None)` paths build their parser FROM the central `SubcommandParser` class — **add/change a flag in `parsers/*.py` only**. Drift guards (`tests/test_cli_parsers.py::TestCentralModuleParserSync` and `TestCentralParserSingleSource`) fail CI on any divergence of dests/defaults/option strings.

`ExecutionContext.override()` is context-local (a `ContextVar` layered over the unchanged base singleton) — thread/async safe for the MCP server; propagate to worker threads via `copy_context`.

### Standalone subsystems (outside `cli/`)

Four top-level packages sit beside `cli/` and are largely independent of the scrape→build→package flow:

- `embedding/` — FastAPI embedding-generation server (`python -m skill_seekers.embedding.server`) with a caching layer (`cache.py`) and multi-backend generators (OpenAI, sentence-transformers, Anthropic). Feeds the vector-DB adaptors.
- `sync/` — real-time doc-sync system: `detector.py` (content-hash / last-modified change detection), `monitor.py` (scheduled incremental re-scrapes), `notifier.py` (email/Slack/webhook). Keeps generated skills fresh as upstream docs change.
- `benchmark/` — performance suite (`runner.py`, `framework.py`) measuring scrape/embedding/storage/e2e timing, memory, and CPU; emits comparison + optimization reports.
- `workflows/` — bundled default enhancement-workflow presets consumed by the enhancement step.

### C3.x Codebase Analysis Pipeline

Local codebase analysis features, all opt-out (`--skip-*` flags):
- C3.1 `pattern_recognizer.py` - Design pattern detection (10 GoF patterns, 9 languages)
- C3.2 `test_example_extractor.py` - Usage examples from tests
- C3.3 `how_to_guide_builder.py` - AI-enhanced educational guides
- C3.4 `config_extractor.py` - Configuration pattern extraction
- C3.5 `generate_router.py` - Architecture overview generation
- C3.10 `signal_flow_analyzer.py` - Godot signal flow analysis

### MCP Server

`src/skill_seekers/mcp/server_fastmcp.py` - 40 tools via FastMCP. Transport: stdio (Claude Code) or HTTP (Cursor/Windsurf). Optional dependency: `pip install -e ".[mcp]"`

- **Tools run in-process** via `run_cli_main()` in `mcp/tools/_common.py`: same argv parsed by the command's REAL parser (sys.argv patch under a lock), stdout/stderr capture + contextvar log capture, identical `(stdout, stderr, returncode)` contract. No subprocess startup; old hard timeouts are advisory.
- **Exceptions BY DESIGN**: `enhance_skill` (LOCAL agent) and `install_skill`'s enhancement step stay subprocess — the agent must be a real child process for the fork-bomb-guard env semantics (`SKILL_SEEKER_ENHANCE_ACTIVE`). Never make these in-process.
- **Domain logic lives in `skill_seekers.services/`** (marketplace_manager, marketplace_publisher, config_publisher, source_manager, git_repo) — importable by CLI without the `[mcp]` extra; old `skill_seekers.mcp.*` paths are back-compat shims. No `sys.path` hacks anywhere in `mcp/`.

### Enhancement (AgentClient is the single AI transport)

Every AI call goes through `AgentClient` (`src/skill_seekers/cli/agent_client.py`): central truncation gate, timeout policy, error classification. `API_PROVIDERS` (provider registry) and `AGENT_PRESETS` (local-agent command templates) live ONLY there. Each `API_PROVIDERS` entry declares its wire `protocol` (`anthropic`/`openai`/`google`) and `supports_images` capability — `_call_api` branches on the resolved protocol, NOT the provider name, so an OpenAI/Anthropic-compatible provider needs no new branch. Adaptors declare provider/endpoint/model/prompt and route through `SkillAdaptor._enhance_skill_md_via_client` (atomic save with backup). Multimodal image input goes through `AgentClient.call_with_image()` (used by `video_visual` frame OCR across all image-capable providers); it no longer bypasses AgentClient with a direct SDK call.

- **API mode** (if API key set): Anthropic, Google Gemini, OpenAI, Moonshot/Kimi, MiniMax — detected in registry order; `SKILL_SEEKER_PROVIDER` forces one. Models: `SKILL_SEEKER_MODEL` (global) or `ANTHROPIC_MODEL`/`GOOGLE_MODEL`/`OPENAI_MODEL`/`MOONSHOT_MODEL`/`MINIMAX_MODEL`; `ANTHROPIC_BASE_URL` for compatible endpoints. MiniMax adds `MINIMAX_API_REGION` (`global_en`/`cn_zh`) and `MINIMAX_API_PROTOCOL` (`openai`/`anthropic`). Vision OCR provider: `SKILL_SEEKER_VISION_PROVIDER` (`auto` picks the first image-capable provider with a key).
- **LOCAL mode** (fallback): Claude Code, Kimi Code, Codex, Copilot, OpenCode, custom agents — command built by `build_local_agent_command()`.
- Control: `--enhance-level 0` (off) / `1` (SKILL.md only) / `2` (default, balanced) / `3` (full)
- Agent selection: `--agent claude|codex|copilot|opencode|kimi|custom`

## Key Implementation Details

### Smart Categorization (`doc_scraper.py:smart_categorize()`)

Scores pages against category keywords: 3 points for URL match, 2 for title, 1 for content. Threshold of 2+ required. Falls back to "other".

### Content Extraction (`doc_scraper.py`)

`FALLBACK_MAIN_SELECTORS` constant + `_find_main_content()` helper handle CSS selector fallback. Links are extracted from the full page before early return (not just main content). `body` is deliberately excluded from fallbacks.

### Three-Stream GitHub Architecture (`unified_codebase_analyzer.py`)

Stream 1: Code Analysis (AST, patterns, tests, guides). Stream 2: Documentation (README, docs/, wiki). Stream 3: Community (issues, PRs, metadata). Depth control: `basic` (1-2 min) or `c3x` (20-60 min).

## Testing

### Test markers (pytest.ini)

```bash
pytest tests/ -v                                    # Default: fast tests only
pytest tests/ -v -m slow                            # Include slow tests (>5s)
pytest tests/ -v -m integration                     # External services required
pytest tests/ -v -m e2e                             # Resource-intensive
pytest tests/ -v -m "not slow and not integration"  # Fastest subset
```

### Known legitimate skips (~11)

- 2: chromadb incompatible with Python 3.14 (pydantic v1)
- 2: weaviate-client not installed
- 2: Qdrant not running (requires docker)
- 2: langchain/llama_index not installed
- 3: GITHUB_TOKEN not set

### sys.modules gotcha

`test_swift_detection.py` deletes `skill_seekers.cli` modules from `sys.modules`. It must save and restore both `sys.modules` entries AND parent package attributes (`setattr`). See the test file for the pattern.

## Dependencies

Core deps include `langchain`, `llama-index`, `anthropic`, `httpx`, `PyMuPDF`, `pydantic`. Platform-specific deps are optional:

```bash
pip install -e ".[mcp]"       # MCP server
pip install -e ".[gemini]"    # Google Gemini
pip install -e ".[openai]"    # OpenAI
pip install -e ".[docx]"      # Word documents
pip install -e ".[epub]"      # EPUB books
pip install -e ".[video]"     # Video (lightweight)
pip install -e ".[video-full]"# Video (Whisper + visual)
pip install -e ".[jupyter]"   # Jupyter notebooks
pip install -e ".[pptx]"      # PowerPoint
pip install -e ".[rss]"       # RSS/Atom feeds
pip install -e ".[confluence]"# Confluence wiki
pip install -e ".[notion]"    # Notion pages
pip install -e ".[chroma]"    # ChromaDB
pip install -e ".[all]"       # Everything (except video-full)
```

Dev dependencies use PEP 735 `[dependency-groups]` in pyproject.toml.

## Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...          # Claude AI (or compatible endpoint)
ANTHROPIC_BASE_URL=https://...        # Optional: Claude-compatible API endpoint
GOOGLE_API_KEY=AIza...                # Google Gemini (optional)
OPENAI_API_KEY=sk-...                 # OpenAI (optional)
GITHUB_TOKEN=ghp_...                  # Higher GitHub rate limits
```

## Adding New Features

### New platform adaptor
1. Create `src/skill_seekers/cli/adaptors/{platform}.py` inheriting `SkillAdaptor` from `base.py`
2. Register in `adaptors/__init__.py` (add try/except import + add to `ADAPTORS` dict)
3. Add optional dep to `pyproject.toml`
4. Add tests in `tests/`

### New source type converter
1. Create `src/skill_seekers/cli/{type}_scraper.py` — for document-shaped sources inherit `DocumentSkillBuilder` (categorization/references/index/SKILL.md come free; implement `extract()` + hooks), otherwise inherit `SkillConverter` and implement `extract()` and `build_skill()`. Set `SOURCE_TYPE`.
2. Register in `CONVERTER_REGISTRY` in `skill_converter.py` — this also makes the type work in unified configs automatically (UnifiedScraper engine)
3. Add source type config building in `create_command.py:_build_config()`
4. Add auto-detection in `source_detector.py`
5. Add optional dep if needed
6. Add tests

### New CLI argument
- Subcommand flag: define ONLY in the central parser class (`parsers/{cmd}_parser.py`) — module `main()` builds from it; the drift-guard test fails otherwise
- Universal: `UNIVERSAL_ARGUMENTS` in `arguments/create.py`
- Source-specific: appropriate dict (`WEB_ARGUMENTS`, `GITHUB_ARGUMENTS`, etc.)
- Shared across scrapers: `add_all_standard_arguments()` in `arguments/common.py`
