# Unification Plan — 5 Phases

> Created 2026-06-11 from the full-repo architecture review (see PR for
> `fix/code-review-findings`). Goal: finish the Grand Unification — one
> dispatch, one config source, one build pipeline, one AI client.
> Each phase is independently shippable; do them in order.

## Status

| Phase | State | Branch / PR |
|---|---|---|
| 1 — CLI drift & preset bugs | **done** (2026-06-11) | `refactor/phase-1-quick-fixes` |
| 2 — DocumentSkillBuilder | **done** (2026-06-11) | `refactor/phase-2-document-skill-builder` |
| 3 — Enhancement consolidation | **done** (2026-06-11; 3.1 deferred) | `refactor/phase-3-enhancement-consolidation` |
| 4 — UnifiedScraper conformance | **done** (2026-06-11; 4.1 deferred) | `refactor/phase-3-enhancement-consolidation` (same branch) |
| 5 — Config / dispatch / MCP platform | **done** (2026-06-11) | `refactor/phase-3-enhancement-consolidation` (same branch) |

Phase 1 notes: all 5 parser drifts fixed + a programmatic drift-guard test
(`tests/test_cli_parsers.py::TestCentralModuleParserSync`) that fails if any
module flag is ever missing from its central parser again. `stream --output`
and `multilang --languages` were central-parser fictions — now implemented in
the modules. `AGENT_PRESETS` and agent-name normalization now live ONLY in
`agent_client.py` (claude's skip-permissions flag became preset metadata so
interactive callers can omit it). unified_enhancer's zero-importer
"backward compat" subclasses (which shadowed the real PatternEnhancer /
TestExampleEnhancer / GuideEnhancer / ConfigEnhancer) were deleted; a guard
test prevents reintroduction.

## Phase 1 — Stop the bleeding: shipping bugs from drift (small)

User-facing flags broken TODAY because central parsers (parsers/*.py) drifted
from module parsers (each command's `main(args=None)`):

1. `estimate` central parser missing `--unlimited`, `--timeout` → CLI rejects them.
2. `update` central parser missing `--generate-package`, `--apply-update`.
3. `quality` central parser missing `--output`.
4. `stream` central/module drift (`--overlap-chars`, `--batch-size`, `--checkpoint`; verify both directions).
5. `multilang` bidirectional drift (`--report`/`--export` missing centrally; `--languages` central-only).

Also:
6. `AGENT_PRESETS` duplicated between `agent_client.py` and
   `enhance_skill_local.py` — the kimi preset has already diverged
   (`{cwd}` vs `{skill_dir}`, missing `parse_output`). Make
   `agent_client.AGENT_PRESETS` the single source; enhance_skill_local layers
   its extra metadata (supports_skip_permissions) on top.
7. `GuideEnhancer` name collision: `guide_enhancer.py:GuideEnhancer`
   (standalone) vs `unified_enhancer.py:GuideEnhancer` (subclass). Rename the
   unified_enhancer one (it's the newer, less-referenced alias).

Each fix gets a regression test. The durable fix for the parser-drift class
is Phase 5 (single argument registry); Phase 1 just makes the flags work.

### Phase 2 results (2026-06-11)

All 9 document scrapers (epub, word, pptx, html, pdf, man, rss, chat,
jupyter) now inherit `cli/document_skill_builder.py:DocumentSkillBuilder`.
Net −1,859/+424 lines across the scrapers; the shared machinery lives once.
Every port is **byte-identical**, proven by golden trees captured from the
pre-refactor code (`tests/golden/phase2/*`, harness in
`tests/phase2_golden_utils.py`, protocol: `UPDATE_GOLDENS=1` only on purpose).
Dedup depth varies by tier: epub/word/pptx/html share nearly everything;
pdf/jupyter share orchestration + several generators; man/rss/chat share the
`build_skill` spine and helpers, keeping their domain-shaped reference/SKILL
writers as overrides.

Follow-up hook candidates surfaced by the ports (do as a small Phase 2.1 —
each removes a full-method override that exists only for wording/keys):
- `DOC_NOUN` ("documentation"/"presentation"/"chat") + index title hook
- `PATTERN_KEYWORDS` class attr on `_format_patterns_from_content`
- `LOAD_TOTAL_KEY` on `load_extracted_data` (man/pdf use `total_pages`)
- `category_stem(cat_key)` hook in `_reference_filename` (chat)
- sectioned `_generate_skill_md` (metadata block / when-to-use bullets /
  extra-stats hooks) — would let html/pptx/chat drop their full overrides
- footer "Skill Seeker" vs "Skill Seekers" inconsistency (man)

## Phase 2 — Unify the build side of scrapers (LARGE, highest ROI)

The 8-9 document scrapers (epub, word, pptx, html, man, rss, chat, jupyter,
pdf) carry ~90%-identical build machinery (~6k+ avoidable LOC) with
user-visible inconsistencies (truncation: 500 vs 1000 vs none; frontmatter
keys; code-example ordering).

1. Normalize extracted-data schema: one page/section dict shape
   (`section_number` everywhere; pdf's `page_number` mapped). Consider a
   shared `ExtractedDocument` model.
2. Extract `DocumentSkillBuilder` (base class between SkillConverter and the
   document scrapers, or composable builder owned by the base) owning:
   `categorize_content`, reference-file writing (incl. table rendering,
   truncation policy), `index.md` generation, `SKILL.md` generation
   (frontmatter incl. json.dumps quoting + version keys).
   Per-scraper hooks: source_type_label, base stem, metadata keys.
3. Port scrapers one at a time, golden-file tests comparing pre/post output.

### Phase 3 results (2026-06-11)

AgentClient is now the single AI transport for every text-based call:
- AgentClient gained provider/base_url/model overrides, system prompts,
  temperature, and a ThinkingBlock-safe anthropic response reader.
- `SkillAdaptor._enhance_skill_md_via_client` (adaptors/base.py) is the one
  SKILL.md enhancement flow; claude/openai/gemini/openai_compatible
  `enhance()` are now ~10-line routing declarations. This also FIXED two
  latent bugs: gemini and openai adaptors had no truncation gate and used
  the destructive rename-then-write save. One canonical
  `_read_reference_files` (was 4 copies).
- enhance_skill.SkillEnhancer routed through AgentClient (import-time
  sys.exit removed); unified_scraper Phase-6 API save is atomic;
  doc_scraper's path already routed via adaptors.
- video_scraper's reference cleaner goes through AgentClient.
  video_visual's frame OCR goes through AgentClient.call_with_image()
  (multimodal support landed with the MiniMax image work; the former
  text-only exception is gone).
- `build_local_agent_command()` in agent_client is the single
  preset-template/permissions-flag handler; LocalSkillEnhancer delegates.

Deferred to **Phase 3.1** (consumers depend on per-feature prompts/output
contracts — blind merges would silently change AI quality):
- Collapse AIEnhancer (ai_enhancer.py) / UnifiedEnhancer hierarchies and
  merge guide_enhancer/config_enhancer; extract their duplicated
  parallel-batching first.
- LocalSkillEnhancer terminal/background/daemon orchestration is kept; the
  remaining overlap with AgentClient._call_local is the prompt-file +
  subprocess loop (small).
- ~~AgentClient multimodal support (would absorb video_visual).~~ DONE —
  `AgentClient.call_with_image()` serves all image-capable providers;
  `_call_api` branches on a registry `protocol`/`supports_images`.

## Phase 3 — Enhancement consolidation (medium-large)

Vision: AgentClient is the ONLY AI transport.

1. `SkillMarkdownEnhancer`: one implementation of read-references →
   build-prompt → call AgentClient → validate → atomic save. Replaces the 5
   copies in enhance_skill.py + adaptors (claude/openai/gemini/
   openai_compatible `enhance()`).
2. Route video_scraper._clean_reference_with_ai and
   video_visual frame classification through AgentClient.
3. LocalSkillEnhancer → thin orchestration (terminal/background/daemon UI)
   over AgentClient._call_local; delete its duplicated presets/command
   building.
4. Collapse hierarchies: unified_enhancer.py is canonical; delete
   ai_enhancer.py duplicates; merge guide_enhancer.py.
5. All 6 SKILL.md-enhancement entry points call SkillMarkdownEnhancer.

### Phase 4 results (2026-06-11)

- `scrape_all_sources()` dispatches via a class-level SOURCE_DISPATCH table
  (was a 17-branch if/elif).
- `_scrape_with_converter()` is the shared engine for the 13 mechanical
  source types (pdf, word, epub, jupyter, html, openapi, asciidoc, pptx,
  confluence, notion, rss, manpage, chat): get_converter() + PUBLIC
  converter.extract() + data-file load + cache copy + record append +
  standalone sub-skill build (kept — the unified build consumes sub-skill
  references from the cache). Thin per-type wrappers own only id
  resolution, config keys, and record keys. unified_scraper.py −280 lines.
- `_scrape_video` uses the public extract() (which now returns the result).
- documentation / github / local stay bespoke WITH comments explaining why
  (function-based scrape_documentation + ExecutionContext override;
  clone/C3.x/dual-write; function-based analyze_codebase).

Deferred to **Phase 4.1**:
- run() template-method conformance (move phases into extract()/build_skill()
  and use base run()) — run()'s orchestration, error strings, and arg
  handling are pinned by tests; needs its own careful pass.
- Config-dict constructor so get_converter() can build UnifiedScraper
  (removes the create_command/scraping_tools special-cases).
- Bring GitHubToSkillConverter / UnifiedSkillBuilder into the hierarchy.
- Wrap documentation/local in converter-shaped adapters so they join the
  engine.

## Phase 4 — UnifiedScraper conformance (medium)

1. Replace 17 `_scrape_*` methods with a data-driven loop:
   `get_converter(source["type"], sub_config)` + public `converter.extract()`
   + standard `data_file_for()` retrieval. New converter types then work in
   unified configs automatically.
2. Move phase logic (scrape-all → conflicts → merge) into `extract()`, build
   into `build_skill()`; stop overriding `run()` (base template provides
   skip_scrape/dry_run/error handling).
3. Constructor takes a config dict (config_path inside it) so the factory
   special-case in create_command dies.
4. Bring GitHubToSkillConverter and UnifiedSkillBuilder into the
   SkillConverter hierarchy (or make them explicit builder strategies the
   base invokes).

### Phase 5 results so far (2026-06-11)

**5a — MCP services layer + import hygiene (done):**
- New `src/skill_seekers/services/` package: marketplace_manager,
  marketplace_publisher, config_publisher (the ONLY category-detection
  logic), source_manager, git_repo — importable by CLI and MCP alike;
  a regression test proves importing services never loads skill_seekers.mcp.
- Back-compat shims at the old mcp/ paths (named re-exports, identity
  tests); 29 import sites updated; patch targets retargeted.
- All 7 sys.path.insert hacks in mcp/ removed (incl. server_legacy);
  server_fastmcp's 100-line import fallback collapsed to one absolute
  import block. CLI_DIR remains only where subprocess tools still need
  script paths (goes away with 5d).

**5b — contextvars ExecutionContext.override (done):**
- override() activates via a ContextVar layered over the unchanged base
  singleton — concurrent threads/asyncio tasks no longer clobber each
  other's overrides; nesting stacks; exceptions restore; is_initialized()
  semantics unchanged. Thread propagation contract documented
  (copy_context, same pattern as the MCP log capture). +6 tests.

**5c — single-definition parsers + exit codes (done 2026-06-11):**
- 13 legacy command modules (config, enhance-status, upload, install,
  install-agent, estimate, extract-test-examples, resume, quality,
  workflows, stream, update, multilang) no longer define their own
  add_argument blocks: `main(args=None)`'s standalone path builds its
  parser FROM the central SubcommandParser class, so every flag is defined
  exactly once (kills the Phase-1 drift class permanently). enhance,
  package, and sync-config were already single-source via shared
  `arguments/*` modules and were left as-is.
- `backfill_parser_defaults` else-branches removed from all 7 modules that
  had them (the central dispatch namespace has every dest by construction);
  the helper stays in arguments/common.py.
- Two real drift bugs fixed by completing the central parsers:
  `install --target` and `extract-test-examples --recursive` were
  module-only and REJECTED by the unified CLI. `update --force` remains a
  central-parser no-op (accepted, unread) — now accepted identically in
  both paths; implementing it is a separate feature.
- workflows' standalone subparser dest unified to `workflows_action`
  (was `action`); main() reads it via getattr in both call styles.
- New `cli/exit_codes.py` (EXIT_SUCCESS/ERROR/VALIDATION/INTERRUPT);
  test_example_extractor.main now returns 0 instead of None; constants
  applied across the touched modules.
- Drift guard upgraded: `tests/test_cli_parsers.py::
  TestCentralParserSingleSource` asserts module-built and central parsers
  have IDENTICAL option dests, defaults, and option strings for all 13.

**5d — MCP subprocess→in-process (done 2026-06-11):**
- 9 tools migrated (estimate_pages, detect_patterns, extract_test_examples,
  extract_config_patterns, build_how_to_guides, split_config,
  generate_router, package_skill, upload_skill) via the shared
  run_cli_main() helper in mcp/tools/_common.py: real-parser argv parsing
  (sys.argv patch under a lock), redirect_stdout/stderr + the contextvar
  log-capture pattern, SystemExit/KeyboardInterrupt containment, and an
  identical (stdout, stderr, returncode) contract so output formats
  (incl. the "❌ Error:" sniffing in install_skill's workflow) stay
  byte-identical. Bonus fix: extract_config_patterns_tool had been passing
  flags the CLI parser rejects — it ALWAYS failed; now mapped to the real
  flags and pinned by a regression test.
- enhance_skill_tool (LOCAL agent) and install_skill_tool's enhancement
  step stay subprocess BY DESIGN (long-running real agent; fork-bomb-guard
  env semantics) — documented at the call sites.

**4.1 follow-ups (done 2026-06-11, run() conformance deliberately dropped):**
- UnifiedScraper accepts the factory-shaped dict ({"config_path": ...,
  "merge_mode", "output_dir", "dry_run"}); get_converter("config", {...})
  works; the special-cases in create_command._route_to_scraper and
  scrape_docs_tool are GONE; legacy str-positional construction still
  supported (+4 tests).
- GitHubToSkillConverter / UnifiedSkillBuilder documented as builder
  strategies (deliberately not SkillConverters — no extract() phase).
- run() template conformance DROPPED deliberately: TestRunOrchestration
  pins that run() itself (not build_skill) triggers workflows; conformance
  would require weakening those tests.

**2.1 hook polish (done 2026-06-11):** LOAD_TOTAL_KEY / DOC_NOUN /
PATTERN_KEYWORDS / RANGE_LABEL / category_stem / sectioned-SKILL.md hooks
added to DocumentSkillBuilder; full-method overrides collapsed in pdf
(−61), html (−202), pptx (−106), jupyter (−48), man (−16), chat (−12
structural), all under byte-identical golden protection (24/24 trees).
Overrides that survive are genuinely domain-shaped (documented per scraper).

**3.1 safe slice (done 2026-06-11):** cli/parallel_batches.py
run_batches_parallel() replaced the 3 duplicated ThreadPoolExecutor blocks
in ai_enhancer/unified_enhancer (contextvars propagation preserved; net
−75). The full hierarchy merge remains deliberately deferred — consumers
depend on per-feature prompts; a blind merge would silently change AI
quality.

**Remaining (small, cosmetic):**
- Move the ~14 legacy commands from COMMAND_MODULES to COMMAND_CLASSES
  dispatch (`Cls(args).execute()`) — aesthetic now that parsers are
  single-definition and dispatch passes namespaces.
- Declarative per-source-type config models replacing
  create_command._build_config's if/elif chain.
- Per-request ExecutionContext initialization at the MCP boundary —
  lower urgency since the converters' raw-config fallback (fixed earlier)
  plus the contextvars override (5b) cover the known divergences.
- ~~AgentClient multimodal support (absorbs video_visual).~~ DONE (see Phase 3).

## Phase 5 — Platform unification: config, dispatch, MCP (medium)

1. ExecutionContext = the single runtime config source. Initialized once per
   entry point (CLI AND MCP server request layer), merging: args/request →
   config file → ConfigManager (~/.config) → defaults.json. Nothing else
   reads os.environ directly (env reads live in the context/agent_client
   provider registry only).
2. `override()` reimplemented on contextvars (thread/async-safe); forbid
   global singleton mutation.
3. Replace create_command._build_config's 227-line if/elif with per-source-
   type config models (Pydantic) derived from the context.
4. Finish COMMAND_CLASSES migration for the ~14 legacy commands; single
   argument registry so every flag is defined exactly once (kills the Phase-1
   drift class permanently); standardize exit codes.
5. MCP: `services/` layer (MarketplaceManager, MarketplacePublisher,
   ConfigPublisher + detect_category, SourceManager) importable by CLI and
   MCP; replace 11 subprocess tools with in-process dispatch; remove all 6
   sys.path.insert hacks; scraping_tools uses SourceDetector instead of its
   hardcoded 4-case detection.

## Invariants for every phase

- `pytest tests/` fast subset green before each commit; full suite before PR.
- `uvx ruff check` + `format` clean.
- No behavior change without a regression test pinning the new behavior.
- Update docs/UML_ARCHITECTURE.md when a phase changes the real structure.
