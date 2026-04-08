# Skill Seekers Architecture

> Updated 2026-04-08 | StarUML project: `docs/UML/skill_seekers.mdj`

## Overview

Skill Seekers converts documentation from 18 source types into production-ready formats for 24+ AI platforms. The architecture follows a layered module design with 8 core modules and 5 utility modules. All source types are routed through a single `skill-seekers create` command via the `SkillConverter` base class + factory pattern.

## Package Diagram

![Package Overview](UML/exports/00_package_overview.png)

**Core Modules** (upper area):
- **CLICore** -- Git-style command dispatcher, entry point for all `skill-seekers` commands
- **Scrapers** -- 17 source-type extractors (web, GitHub, PDF, Word, EPUB, video, etc.)
- **Adaptors** -- Strategy+Factory pattern for 20+ output platforms (Claude, Gemini, OpenAI, RAG frameworks)
- **Analysis** -- C3.x codebase analysis pipeline (AST parsing, 10 GoF pattern detectors, guide builders)
- **Enhancement** -- AI-powered skill improvement via `AgentClient` (API mode: Anthropic/Kimi/Gemini/OpenAI + LOCAL mode: Claude Code/Kimi/Codex/Copilot/OpenCode/custom, --enhance-level 0-3)
- **Packaging** -- Package, upload, and install skills to AI agent directories
- **MCP** -- FastMCP server exposing 40 tools via stdio/HTTP transport (includes marketplace and config publishing)
- **Sync** -- Documentation change detection and re-scraping triggers

**Utility Modules** (lower area):
- **Parsers** -- CLI argument parsers (30+ SubcommandParser subclasses)
- **Storage** -- Cloud storage abstraction (S3, GCS, Azure)
- **Embedding** -- Multi-provider vector embedding generation
- **Benchmark** -- Performance measurement framework
- **Utilities** -- Shared helpers (LanguageDetector, RAGChunker, MarkdownCleaner, etc.)

## Core Module Diagrams

### CLICore
![CLICore](UML/exports/01_cli_core.png)

Entry point: `skill-seekers` CLI. `CLIDispatcher` maps subcommands to modules via `COMMAND_MODULES` dict. `CreateCommand` auto-detects source type via `SourceDetector`, initializes `ExecutionContext` singleton (Pydantic model, single source of truth for all config), then calls `get_converter()` → `converter.run()`. Enhancement runs centrally in CreateCommand after the converter completes.

### Scrapers
![Scrapers](UML/exports/02_scrapers.png)

18 converter classes inheriting `SkillConverter` base class (Template Method: `run()` → `extract()` → `build_skill()`). Factory: `get_converter(source_type, config)` via `CONVERTER_REGISTRY`. No `main()` entry points — all routing through `CreateCommand`. Notable: `GitHubScraper` (3-stream fetcher) + `GitHubToSkillConverter` (builder), `UnifiedScraper` (multi-source orchestrator).

### Adaptors
![Adaptors](UML/exports/03_adaptors.png)

`SkillAdaptor` ABC with 3 abstract methods: `format_skill_md()`, `package()`, `upload()`. Two-level hierarchy: direct subclasses (Claude, Gemini, OpenAI, Markdown, OpenCode, RAG adaptors) and `OpenAICompatibleAdaptor` intermediate (MiniMax, Kimi, DeepSeek, Qwen, OpenRouter, Together, Fireworks).

### Analysis (C3.x Pipeline)
![Analysis](UML/exports/04_analysis.png)

`UnifiedCodebaseAnalyzer` controller orchestrates: `CodeAnalyzer` (AST, 9 languages), `PatternRecognizer` (10 GoF detectors via `BasePatternDetector`), `TestExampleExtractor`, `HowToGuideBuilder`, `ConfigExtractor`, `SignalFlowAnalyzer`, `DependencyAnalyzer`, `ArchitecturalPatternDetector`.

### Enhancement
![Enhancement](UML/exports/05_enhancement.png)

Two enhancement hierarchies: `AIEnhancer` (API mode, multi-provider via `AgentClient`) and `UnifiedEnhancer` (C3.x pipeline enhancers). Each has specialized subclasses for patterns, test examples, guides, and configs. `WorkflowEngine` orchestrates multi-stage `EnhancementWorkflow`. The `AgentClient` (`cli/agent_client.py`) centralizes all AI invocations, supporting API mode (Anthropic, Moonshot/Kimi, Gemini, OpenAI) and LOCAL mode (Claude Code, Kimi Code, Codex, Copilot, OpenCode, custom agents).

### Packaging
![Packaging](UML/exports/06_packaging.png)

`PackageSkill` delegates to adaptors for format-specific packaging. `UploadSkill` handles platform API uploads. `InstallSkill`/`InstallAgent` install to AI agent directories. `OpenCodeSkillSplitter` handles large file splitting.

### MCP Server
![MCP Server](UML/exports/07_mcp_server.png)

`SkillSeekerMCPServer` (FastMCP) with 40 tools in 10 categories. Supporting classes: `SourceManager` (config CRUD), `AgentDetector` (environment detection), `GitConfigRepo` (community configs), `MarketplacePublisher` (publish skills to marketplace repos), `MarketplaceManager` (marketplace registry CRUD), `ConfigPublisher` (push configs to registered source repos).

### Sync
![Sync](UML/exports/08_sync.png)

`SyncMonitor` controller schedules periodic checks via `ChangeDetector` (SHA-256 hashing, HTTP headers, content diffing). `Notifier` sends alerts when changes are found. Pydantic models: `PageChange`, `ChangeReport`, `SyncConfig`, `SyncState`.

## Utility Module Diagrams

### Parsers
![Parsers](UML/exports/09_parsers.png)

`SubcommandParser` ABC with 18 subclasses — individual scraper parsers removed after Grand Unification (all source types route through `CreateParser`). Remaining: Create, Doctor, Config, Enhance, EnhanceStatus, Package, Upload, Estimate, Install, InstallAgent, TestExamples, Resume, Quality, Workflows, SyncConfig, Stream, Update, Multilang.

### Storage
![Storage](UML/exports/10_storage.png)

`BaseStorageAdaptor` ABC with `S3StorageAdaptor`, `GCSStorageAdaptor`, `AzureStorageAdaptor`. `StorageObject` dataclass for file metadata.

### Embedding
![Embedding](UML/exports/11_embedding.png)

`EmbeddingGenerator` (multi-provider: OpenAI, Sentence Transformers, Voyage AI). `EmbeddingPipeline` coordinates provider, caching, and cost tracking. `EmbeddingProvider` ABC with OpenAI and Local implementations.

### Benchmark
![Benchmark](UML/exports/12_benchmark.png)

`BenchmarkRunner` orchestrates `Benchmark` instances. `BenchmarkResult` collects timings/memory/metrics and produces `BenchmarkReport`. Supporting data types: `Metric`, `TimingResult`, `MemoryUsage`, `ComparisonReport`.

### Utilities
![Utilities](UML/exports/13_utilities.png)

16 shared helper classes: `LanguageDetector`, `MarkdownCleaner`, `RAGChunker`, `RateLimitHandler`, `ConfigManager`, `ConfigValidator`, `SkillQualityChecker`, `QualityAnalyzer`, `LlmsTxtDetector`/`Downloader`/`Parser`, `ConfigSplitter`, `ConflictDetector`, `IncrementalUpdater`, `MultiLanguageManager`, `StreamingIngester`.

## Key Design Patterns

| Pattern | Where | Classes |
|---------|-------|---------|
| Strategy + Factory | Adaptors | `SkillAdaptor` ABC + `get_adaptor()` factory + 20+ implementations |
| Strategy + Factory | Storage | `BaseStorageAdaptor` ABC + S3/GCS/Azure |
| Strategy + Factory | Embedding | `EmbeddingProvider` ABC + OpenAI/Local |
| Template Method + Factory | Scrapers | `SkillConverter` base + `get_converter()` factory + 18 converter subclasses |
| Singleton | Configuration | `ExecutionContext` Pydantic model — single source of truth for all config |
| Command | CLI | `CLIDispatcher` + `COMMAND_MODULES` lazy dispatch |
| Template Method | Pattern Detection | `BasePatternDetector` + 10 GoF detectors |
| Template Method | Parsers | `SubcommandParser` + 18 subclasses |

## Behavioral Diagrams

### Create Pipeline Sequence
![Create Pipeline](UML/exports/14_create_pipeline_sequence.png)

`CreateCommand` is now the pipeline orchestrator. Flow: User → `execute()` → `SourceDetector.detect(source)` → `validate_source()` → `ExecutionContext.initialize()` → `_validate_arguments()` → `get_converter(type, config)` → `converter.run()` (extract + build_skill) → `_run_enhancement(ctx)` → `_run_workflows()`. Enhancement is centralized in CreateCommand, not inside each converter.

### GitHub Unified Flow + C3.x
![GitHub Unified](UML/exports/15_github_unified_sequence.png)

`UnifiedScraper` orchestrates GitHub scraping (3-stream fetch) then delegates to `analyze_codebase(enhance_level)` for C3.x analysis. Shows all 5 C3.x stages: `PatternRecognizer` (C3.1), `TestExampleExtractor` (C3.2), `HowToGuideBuilder` with examples from C3.2 (C3.3), `ConfigExtractor` (C3.4), and `ArchitecturalPatternDetector` (C3.5). Note: `enhance_level` is the sole AI control parameter — `enhance_with_ai`/`ai_mode` are internal to C3.x classes only.

### Source Auto-Detection
![Source Detection](UML/exports/16_source_detection_activity.png)

Activity diagram showing `source_detector.py` decision tree in correct code order: file extension first (.json config, .pdf/.docx/.epub/.ipynb/.html/.pptx/etc) → video URL → `os.path.isdir()` (Codebase) → GitHub pattern (owner/repo or github.com URL) → http/https URL (Web) → bare domain inference → error.

### MCP Tool Invocation
![MCP Invocation](UML/exports/17_mcp_invocation_sequence.png)

MCP Client (Claude Code/Cursor) → FastMCPServer (stdio/HTTP) with two invocation paths: **Path A** (scraping tools) uses `get_converter(type, config).run()` in-process via `_run_converter()` helper, **Path B** (packaging/config tools) uses direct Python imports (`get_adaptor()`, `sync_config()`). Both return TextContent → JSON-RPC.

### Enhancement Pipeline
![Enhancement Pipeline](UML/exports/18_enhancement_activity.png)

`--enhance-level` decision flow with precise internal variable mapping: Level 0 sets `ai_mode=none`, skips all AI. Level >= 1 selects `ai_mode=api` (if any supported API key set: Anthropic, Moonshot/Kimi, Gemini, OpenAI) or `ai_mode=local` (via `AgentClient` with configurable agent: Claude Code, Kimi, Codex, Copilot, OpenCode, or custom), then SKILL.md enhancement happens post-build via `enhance_command`. Level >= 2 enables `enhance_config=True`, `enhance_architecture=True` inside `analyze_codebase()`. Level 3 adds `enhance_patterns=True`, `enhance_tests=True`.

### Runtime Components
![Runtime Components](UML/exports/19_runtime_components.png)

Component diagram with runtime dependencies. Key flows: `CLI Core` dispatches to `Scrapers` via `get_converter()` → `converter.run()` (in-process, no subprocess). `Scrapers` call `Codebase Analysis` via `analyze_codebase(enhance_level)`. `Codebase Analysis` uses `C3.x Classes` internally and `Enhancement` when level ≥ 2. `MCP Server` reaches `Scrapers` via `get_converter()` in-process and `Adaptors` via direct import. `Scrapers` optionally use `Browser Renderer (Playwright)` via `render_page()` when `--browser` flag is set for JavaScript SPA sites.

### Browser Rendering Flow
![Browser Rendering](UML/exports/20_browser_rendering_sequence.png)

When `--browser` flag is set, `DocScraper.scrape_page()` delegates to `BrowserRenderer.render_page(url)` instead of `requests.get()`. The renderer auto-installs Chromium on first use, navigates with `wait_until='networkidle'` to let JavaScript execute, then returns the fully-rendered HTML. The rest of the pipeline (BeautifulSoup → `extract_content()` → `save_page()`) remains unchanged. Optional dependency: `pip install "skill-seekers[browser]"`.

## File Locations

- **StarUML project**: `docs/UML/skill_seekers.mdj`
- **Diagram exports**: `docs/UML/exports/*.png`
- **Source code**: `src/skill_seekers/`
