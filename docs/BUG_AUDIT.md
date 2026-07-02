# Skill Seekers — Bug Audit

> **Addendum (2026-06-11):** Follow-up review during the Grand Unification work
> (see [UNIFICATION_PLAN.md](UNIFICATION_PLAN.md)) found that two fixes claimed
> below were no-ops as shipped and have since been fixed properly:
> 1. **MCP-03 (`dry_run` for unified configs)** — the injected flag never
>    reached `UnifiedScraper`; it is now genuinely honored (constructor param,
>    preview-and-return, no directory creation) for both CLI and MCP paths.
> 2. **ENH timeout fallback** — the raw-config fallbacks for enhancement
>    settings (incl. timeout/"unlimited") were dead code because
>    `ExecutionContext.get()` never raises; the gate now uses
>    `ExecutionContext.is_initialized()`.
>
> The findings below are preserved unchanged as a historical record.

**Date:** 2026-06-10
**Scope:** Full audit of `src/skill_seekers/` (~80K LOC): scan/config pipeline, CLI core & dispatch, platform adaptors, MCP server & tools, codebase-analysis engines (AST/pattern/dependency/guide/router), document & media & remote scrapers, enhancement + unified builder, argument/parser system, and infra (embedding, sync, storage, benchmark, presets).

**Method:** Two-pass. Pass 1 — 10 parallel review agents, one per subsystem, surfaced candidate defects. Pass 2 — a second set of agents (plus manual spot-checks) re-read the actual code behind **every** finding, checked reachability/trigger, marked each `Confirmed` / `Corrected` / `False-Positive`, deepened it, and hunted for additional related bugs. Only `Confirmed` and `Corrected` findings appear in the body; dismissed items are recorded in Appendix A for transparency.

**Severity rubric**
- **Critical** — silent data loss/corruption of the primary output, or a core feature completely (and silently) non-functional.
- **High** — wrong result / broken feature under common conditions, or a crash on realistic input.
- **Medium** — wrong behaviour under specific conditions, misleading output, or latent correctness hazard with a plausible trigger.
- **Low** — cosmetic, rare trigger, dead code, type-annotation, or defensive gap.

**No security/RCE findings.** Subprocess calls use argv arrays (no `shell=True`); path-traversal guards in `config_publisher`, `marketplace_publisher`, and `workflow_tools` were verified present and correct.

---

## Summary counts

| Severity | Count |
|----------|-------|
| Critical | 5 |
| High | 18 |
| Medium | 45 |
| Low | 67 |
| **Total confirmed/corrected** | **135** |
| of which newly found in the verification pass (★) | 33 |
| Dismissed (false-positive / no-impact) | 7 (Appendix A) |

IDs are subsystem-prefixed: `SCAN` (scan+config), `CLI` (core/dispatch), `ADP` (adaptors), `MCP`, `CBA` (codebase-analysis: AST/pattern/dependency), `CBB` (codebase-analysis: example/guide/router), `DOC` (document scrapers), `MED` (media/structured/remote scrapers), `ENH` (enhancement + unified builder), `INF` (args/parsers + infra). `★` marks bugs newly discovered during the verification pass.

---

## Resolution status (this PR)

Worked through the audit Critical → Low. Every Critical and High finding is fixed, and the entire Medium tier is fixed except one deferred item. Each fix carries a regression test where behavioral; the rest are covered by existing suites. Lint + format are clean throughout.

| Tier | Total | Fixed | Remaining |
|------|-------|-------|-----------|
| Critical | 5 | 5 | 0 |
| High | 18 | 18 | 0 |
| Medium | 45* | 44 | 1 (DOC-04) |
| Low | 67* | 0 | 67 (not in scope for this PR) |

\* Medium/Low counts include sub-findings; the body tables enumerate each fixed ID.

**Delivered as 8 commits:**
1. Critical + High behavioral bugs (each with a regression test).
2. `--output` honored for every source type + config-file precedence (CLI-01/02, CFG-01/02).
3. `ExecutionContext` made the real single source of truth (RT-01..11): ~12 inert flags wired, 4 bypasses fixed, dead `rag` section removed, `--languages`/`--dry-run` wired.
4. Medium batch 1 — codebase-analysis, enhancement, infra, scan/config, adaptors.
5. Medium batch 2 — guides + document/remote scrapers.
6. DOC-07/MED-04 — SKILL.md nav links fixed across all 7 scrapers.
7. ADP-01 — `--streaming` wired into the 8 RAG/vector adaptors (was dead for every target).
8. CLI-04 — all 15 commands migrated off `_reconstruct_argv` to namespace dispatch (also fixed a pre-existing live bug: `skill-seekers workflows …` was broken).

**Remaining / out of scope:**
- **DOC-04** (Medium, deferred): `DEFAULT_MAX_PAGES = -1` means a config without `max_pages` crawls unbounded. The fix (a finite default) is a **user-visible behavior change** for existing configs, so it's left for a maintainer product decision rather than changed unilaterally.
- **Low tier (67):** cosmetic / rare-trigger / dead-code / type-annotation items — catalogued in the body, not addressed in this PR.
- **`tests/test_bootstrap_skill*.py`** were hardened (out of band) to guard a fork-bomb: the bootstrap/`create` subprocess tests spawn real `skill-seekers create` runs (and LLM enhance agents). Because of this, the *full* `pytest tests/` is unsafe to run repeatedly; verification used targeted per-module suites + `-m "not slow and not integration"`.

---

## Independent re-review of this PR — 2026-06-10 (second pass)

After the fixes above, every commit in this PR was re-reviewed independently (one reviewer per commit) to verify the fixes are correct, complete, and don't introduce regressions — i.e. not taking the audit's own self-grade at face value. The reviewers confirmed the large majority of fixes are correct, and surfaced the following issues, **all now resolved in this PR** (each with a regression test unless noted):

### Regressions this PR had introduced (now fixed)

| ID | Sev | Fix |
|----|-----|-----|
| **ENH-03-bis** | Blocker | The ENH-03 retry path was mis-indented: when the exit-75 retry failed, `new_mtime` was unbound → `UnboundLocalError`. Re-nested under the returncode/exists guards. Tests: `test_enhance_skill_local.py::TestHeadlessSuccessGate::{test_failed_retry_returns_false_without_crashing,test_successful_retry_counts_as_success}`. |
| **R1 (CLI-04-bis)** | High | `skill-seekers estimate <cfg>` crawled **unlimited** instead of capping at 1000 — the unified `estimate_parser`'s `--max-discovery` had no default (`None`), which `estimate_pages()` treats as unlimited. Added `default=DEFAULT_MAX_DISCOVERY`. Test: `test_estimate_pages.py::TestEstimateParserDefault`. |
| **R2 (CBA-14-bis)** | Medium | The JS method regex required `)` immediately before `{`, silently dropping **TypeScript** class methods with return-type annotations (`greet(): string {`). Made the return type optional in the pattern. Test: `test_code_analyzer.py::...::test_typescript_class_methods_with_return_types_not_dropped`. |
| **R3 (CLI-02-bis)** | Medium | `github_scraper._save_data()` did `os.makedirs("output")` but wrote to a `--output`-derived `data_file`, raising `FileNotFoundError` for `create owner/repo --output <nested/path>`. Now creates `dirname(data_file)`. Test: `test_github_scraper.py::...::test_save_data_creates_nested_output_parent`. |

### Audit fixes that were incomplete / over-claimed (now corrected)

| ID | Sev | Resolution |
|----|-----|-----------|
| **I1 (MCP-03)** | High | `skip_scrape` was a no-op (set an attribute no converter read). Now honored at the `SkillConverter.run()` chokepoint for single-source paths and by `UnifiedScraper.run()` for multi-source configs, which reloads each configured source from `.skillseeker-cache`/cached extraction files before conflict detection and build. Tests: `test_skill_converter.py::TestSkipScrape`, `test_unified_scraper_orchestration.py::TestUnifiedSkipScrape`, `test_unified_mcp_integration.py::test_mcp_scrape_docs_unified_skip_scrape_sets_attribute_without_warning`. |
| **I2 (RT-06)** | Medium | Config-file **inline** `stages` never ran — `_build_inline_engine` re-read `args.enhance_stage` (None for config-only) instead of the resolved list. Now takes the resolved `inline_stages`. Test: `test_workflow_runner.py::...::test_inline_stages_from_config_execute`. |
| **I3 (ENH-06)** | Low | The OpenAI branch of `_call_api` still hardcoded `timeout=120`; now forwards the caller's `request_timeout`. Test: `test_agent_client.py::...::test_openai_forwards_caller_timeout`. |
| **I4 (RT-04)** | Low | RT-04 claimed `--timeout` is wired on `create`, but the flag isn't registered there, so the mapping is inert on that path (it only fires for config dicts carrying `timeout`). **Claim corrected here** — no CLI flag added (avoids new surface area for an over-claim). |

### Low-tier / pre-existing issues fixed opportunistically

| ID | Area | Fix |
|----|------|-----|
| **CBA-09** | Kotlin | `is_suspend` used a substring test, mis-flagging a function *named* `suspendCoroutine`. Now word-boundary (`\bsuspend\b`). Test in `test_kotlin_support.py`. |
| **P1** | chat | Discord 429 retry was unbounded (hang risk) — the Slack path in the same commit was bounded; Discord now caps consecutive 429s at 3 and stops with partial data. |
| **P2** | doc | `_normalize_url` stripped `?ref=`, which is content-bearing on some sites (GitHub `?ref=branch`, SPA routers) → could collapse distinct pages. `ref` removed from the strip set (`ref_src` kept). Tests in `test_scraper_features.py::TestNormalizeUrl`. |
| **P3** | doc | `--dry-run` supplied via config still created empty output dirs (the ctor used the param, not `self.dry_run`). Now uses `self.dry_run`/`self.resume`. |
| **P5** | adaptors | `claude.py` enhancement did rename-then-write, leaving only `SKILL.md.backup` if the write failed. Now writes to a temp file, copies the backup, then `os.replace()` (atomic). |
| **P6** | mcp | `submit_config` dedup used GitHub's fuzzy title search (`[CONFIG] react` matched `react-native`). Added an exact-title guard. |
| **P8** | scrapers | asciidoc/jupyter `_generate_index` still had inline filename logic (drift risk vs the nav helper). Both index generators now route through `_ref_filename`, so index links and reference files share one source of truth. |
| **P9** | config | `config status` omitted the Moonshot key row; added it. |

### Deferred (genuine larger work — not safe to do inline; tracked here)

- **Streaming adaptor format (ADP-01 follow-up):** all 8 RAG/vector adaptors emit a *generic* streamed format rather than each platform's native shape (only the unregistered example classes override the converter). `--streaming` works; per-platform fidelity is a follow-up.
- **Unified multi-source `skip_scrape` (I1 remainder):** fixed in #405 by rebuilding `scraped_data` from cached per-source files before the unified build, and by forwarding `--skip-scrape` through the config-source `create` path.
- **Kotlin brace-depth / `is_suspend` corpus robustness (CBA-08, CBA-11):** the brace-depth nesting check is fooled by braces inside strings/comments; a robust fix needs a string/comment-aware scan (shared with the still-open CBA-11).
### Low-tier disposition (2026-06-11)

After fixing the ~12 impactful Low items above, the remaining Low tier was triaged
and batch-fixed. Issues #405–#408 track the 4 larger deferred items.

**Fixed in this PR (data-loss/crash + minor correctness):**
DOC-11, DOC-13, DOC-14, DOC-15, DOC-17, MED-06, MED-07, MED-08, MED-11, MED-12,
MED-14, MED-17, MED-18, ENH-13, ENH-14, ENH-15, ENH-16, ENH-17, ADP-03, ADP-04,
ADP-05, ADP-06, MCP-11, MCP-15, MCP-16, MCP-17, SCAN-05, SCAN-06, SCAN-07, CLI-08,
CLI-09, INF-06, CBA-12, CBA-16, CBB-09, CBB-10, CBB-11, CBB-14, CBB-15, CBB-16
(plus the re-review R/I/P items). MED-16 was already fixed in batch 2.

**Intentionally NOT changed (with reason):**
- **Product decisions (left as-is, like DOC-04):** MCP-10 (sync caps at 500 — a
  sensible safety bound), CLI-07 (a failed *optional* enhancement returning a
  non-zero exit from `create` is a behavior change — needs a maintainer call).
- **Cosmetic / doc-only (dropped):** ADP-07 (docstring), CLI-05 (a misleading
  success-log path), MED-13 (type-annotation lie), MCP-08 (param typing), MED-09,
  MED-10 (already corrected/dead per Appendix).
- **Still deferred (genuinely larger work):** MED-15 (OpenAPI external/multi-file
  `$ref` bundling — needs a pre-bundle pass; the MED-07 *cycle* guard is fixed),
  MCP-09 (a truly structured MCP error channel — the text already carries ✅/❌
  markers).

- The original **DOC-04** decision stands (issue #408): keep `-1` (unbounded).

---

## Fix log — 2026-06-10

All 5 Criticals + all 18 High findings fixed with regression tests (lint/format clean; affected suites green). A few mechanical/wide fixes (CLI-01, CLI-02, CBB-02/03/12, MCP-02..05) are covered by the broad suite rather than dedicated new tests.

### Critical

| ID | Status | Fix summary |
|----|--------|-------------|
| ENH-01 | ✅ Fixed | `enhance_skill.py`, `agent_client.py`, `adaptors/claude.py` refuse to save/return a `max_tokens`-truncated (or empty) response; unified-scraper path covered via `agent_client`. |
| SCAN-01 | ✅ Fixed | Schema hint `code_analysis_depth` `"standard"` → `"deep"`; pinned to the validator by a regression test. |
| CBA-13 | ✅ Fixed | GDScript class dict key `"bases"` → `"base_classes"` (+ `docstring`, `_offset_to_line`). |
| CBB-01 | ✅ Fixed | `guide_enhancer._enhance_via_local` now calls the real `_call_ai`. |
| MCP-01 | ✅ Fixed | `config_publisher` clone/pull/push authenticate via an explicit token URL (origin stays tokenless). |
| ★MCP-12 | ✅ Fixed | `get_source` `KeyError` translated to a helpful `ValueError`. |
| ★MCP-13 | ✅ Fixed | cached-repo re-pull uses the token URL (was tokenless origin). |
| ★MCP-14 | ✅ Fixed | feature branch restored in a `finally` so the cache can't be stranded. |
| MCP-07 | ✅ Fixed | commit `action` uses pre-copy existence (`add` vs `update`). |
| ADP-06 | ✅ Fixed | `adaptors/claude.py` validates non-empty before renaming the original (folded into the ENH-01 fix). |

### High

| ID | Status | Fix summary |
|----|--------|-------------|
| SCAN-02 | ✅ Fixed | Guard the non-numeric `confidence` parse so one bad AI entry can't crash the scan. |
| CLI-01 | ✅ Fixed | `_build_config` reads the negative dests (`not no_issues`/`no_changelog`/`no_releases`); `--no-*` opt-outs now work. |
| CLI-02 | ✅ Fixed | `--output` now honored across the whole single-source create path: base `SkillConverter` + all 16 overriding converters read `config["output_dir"]` (incl. 5 type-annotated `skill_dir: str = …` that a first pass missed), and `data_file`/`data_dir`/`checkpoint` are derived from `skill_dir` so intermediate artifacts follow `--output` too (behavior-preserving fallback to `output/<name>`). `_build_config` passes `output_dir` for every branch. The unified/`config` multi-source path also honors `--output`: `unified_scraper`/`unified_skill_builder` derive the final skill from `config["output_dir"]`, and the docs/github sub-converters now write **straight into the `.skillseeker-cache/` cache** (their sub-config gets `output_dir`), removing the `output/{subname}` hardcodes and the move-to-cache dance. (`pdf_extractor_poc.py` keeps an `output/` *default* but already accepts `image_dir` as a constructor arg — standalone PoC, not the config flow.) |
| CBA-01 | ✅ Fixed | Singleton precedence: `(has_instance_method or has_init_control) and confidence >= 0.5`. |
| CBA-02 | ✅ Fixed | `total_emissions` iterates `.values()` (was `.items()` → always 2×#signals). |
| CBA-03 | ✅ Fixed | JS/TS class body delimited by the matching brace (brace-count), not the first `}`. |
| CBA-04 | ✅ Fixed | New `_base_root`/`_matches_base` normalize generic/qualified bases so subclass detection matches. |
| CBB-02 | ✅ Fixed | Removed the positional verification overwrite that misattributed checks to steps. |
| CBB-03 | ✅ Fixed | `_generate_examples_from_github` works on a copy + index set instead of mutating shared insights. |
| CBB-12 | ✅ Fixed | `dependencies=list(imports)` — per-example copy (no shared mutable list). |
| ENH-02 | ✅ Fixed | `SKILL_SEEKER_PROVIDER` override so a Moonshot/Kimi `sk-` key isn't misrouted to OpenAI. |
| ENH-03 | ✅ Fixed | Headless success gates on mtime advance, not file growth (matches background/daemon). |
| ENH-04 | ✅ Fixed | Kimi parser uses `re.DOTALL` + record-boundary anchor (multi-line / apostrophe safe). |
| ENH-05 | ✅ Fixed | Only read the response file when `output_file` was requested; dropped the stray-`.json` glob. |
| MCP-02 | ✅ Fixed | Package-path regex matches `Output:` / `Package created:` (the strings actually printed). |
| MCP-03 | ✅ Fixed | `scrape_docs` honors `skip_scrape` and applies `dry_run` for unified configs too. |
| MCP-04 | ✅ Fixed | `submit_config` searches for an existing open issue before creating (idempotent). |
| MCP-05 | ✅ Fixed | `install_skill` detects failure by the specific `_run_converter` markers, not any `❌`. |

Regression tests added — Critical: `test_agent_client.py::TestCallApiTruncation`, `test_scan_command.py::TestGenerateSchemaHintDepth`, `test_code_analyzer.py::TestGDScriptParsing`, `test_guide_enhancer.py::TestEnhanceViaLocalRegression`, `test_config_publisher.py` (re-pull + KeyError + add/update). High: `test_agent_client.py` (`TestProviderOverride`, `TestKimiOutputParsing`, `TestCallLocalStrayJson`), `test_scan_command.py` (non-numeric confidence), `test_enhance_skill_local.py::TestHeadlessSuccessGate`, `test_pattern_recognizer.py::TestBaseClassMatching`, `test_code_analyzer.py` (JS multi-method), `test_signal_flow_analyzer.py`. (CBB-02/03/12, CLI-01, MCP-02..05 are covered by the broad suite rather than dedicated new tests.)

### Config-override follow-up (found while auditing "what else is overridden by hardcoded values")

| ID | Status | Fix summary |
|----|--------|-------------|
| CFG-01 | ✅ Fixed | **Web `--config` `selectors`/`url_patterns` silently ignored.** `_merge_json_config` only fills missing keys, but `_build_config` pre-set the hardcoded `selectors`/`url_patterns` before merging → the user's config-file values were shadowed. Now applied via `setdefault` **after** the merge, so the file wins. (Verified `doc_scraper` actually reads `config["selectors"]`/`url_patterns`.) |
| CFG-02 | ✅ Fixed | **Web config-file `workers`/`async_mode`/`browser_wait_until`/`browser_extra_wait` dropped.** `ExecutionContext._load_config_file` copied only `max_pages`/`rate_limit`/`browser`; now copies all scraping-tuning keys. Test: `test_execution_context.py::...test_simple_web_config_format`. |
| CFG-03 | ℹ️ Noted | `--config` is only merged for `web`/`github` source types; for `pdf`/`video`/etc. the documented path is the unified `sources` config (which reads per-source keys correctly). Low impact; left as a design note. |

### Runtime-config (ExecutionContext) audit — is every field wired through args→context→consumer, with no bypasses?

The singleton claims "all components read from this context instead of parsing their own argv." Audit found it was **not** the single source of truth: ~12 registered flags never reached the context, several consumers bypassed it, and two sections were dead. All fixed (regression tests in `test_execution_context.py`).

| ID | Status | Fix summary |
|----|--------|-------------|
| RT-01 | ✅ Fixed | **5 analysis `--skip-*` flags inert.** `--skip-config-patterns`/`--skip-api-reference`/`--skip-dependency-graph`/`--skip-docs`/`--no-comments` were never mapped in `_args_to_data`, yet `create_command` reads those exact `ctx.analysis.*` fields → the skipped steps ran anyway. Now mapped. |
| RT-02 | ✅ Fixed | **`--skip-config` orphan dest** now aliased to `skip_config_patterns`. |
| RT-03 | ✅ Fixed | **`--dry-run` dead on `create`.** `ctx.output.dry_run` was set but never put in the converter config; `_build_config` now passes `"dry_run"`, and `doc_scraper` reads `config["dry_run"]` (was only honoring the unused ctor param). |
| RT-04 | ✅ Fixed | **`--timeout` not wired on `create`** → mapped to `ctx.enhancement.timeout` in `_args_to_data`. |
| RT-05 | ✅ Fixed | **`get_agent_client()` dropped `api_key`** → a CLI `--api-key` was lost and AgentClient env-detected only. Now forwarded. |
| RT-06 | ✅ Fixed | **Config-file `workflows`/`stages`/`workflow_vars` never ran** — `run_workflows`/`collect_workflow_vars` read only argv. Now fall back to `ctx.enhancement.*` so config-declared workflows execute. |
| RT-07 | ✅ Fixed | **Confluence/Notion `max_pages` bypass** — read `getattr(self.args, …)` (dropping config-file `max_pages`); now read `ctx.scraping.max_pages`. |
| RT-08 | ✅ Fixed | **`unified_scraper` dropped `ctx.enhancement.timeout` and `api_key`** (re-read raw config / built `AgentClient(mode="api")`); now use the context. |
| RT-09 | ✅ Fixed | **`scraping.languages` was a dead field with a name collision** (default `["en"]`, read nowhere; `--languages` is a *code*-filter the local converter read from argv, which would have broken if fed `["en"]`). Repurposed the field as the code-language filter (`default=None`), wired `--languages` into it, and `create_command` now reads `ctx.scraping.languages`. |
| RT-10 | ✅ Fixed (removed) | **`rag.*` section was write-only/dead.** Chunking lives in the separate `package` command, which parses its own (richer) args and runs as its own process — the create/scrape context never chunks and `ctx.rag` was read nowhere. Removed `RAGSettings` from the context. As cleanup, `common.py` now sources `DEFAULT_CHUNK_TOKENS`/`_OVERLAP` from `defaults.json` (was hardcoded `512`/`50`), so `defaults.json`'s `rag` block is the single source of truth for package chunking. *(Deviation: the earlier plan said "wire rag via package"; on inspection that's unsound — `create` and `package` are separate processes, so a create-time context can't reach package. Removal is the honest fix.)* |
| RT-11 | ✅ Kept (not a bug) | **`source.*`** is read nowhere in production (consumers use `create_command.self.source_info`), but it is **tested public API** and legitimately belongs in an execution context. Retained — removing tested API to chase a cosmetic dual-representation would be over-reach. |

### Medium tier — batch 1 (codebase-analysis + enhancement + infra + scan/config + adaptors)

All ✅ Fixed; verified by existing suites + new regression tests where behavioral.

| ID | Fix summary |
|----|-------------|
| CBA-05 / CBA-06 | Parenthesized the `A and B or C` precedence so the `"protocol"`/`"event"` clause no longer boosts *every* pattern type. |
| CBA-07 | `_resolve_import` converts dotted module names → slash paths + suffix-matches `file_nodes`, so the dependency graph has edges (cycle detection was empty for all dotted-import languages). |
| CBA-08 | Kotlin top-level-fn detection uses brace-depth, not the brittle `indent > 4`. |
| CBA-09 | Kotlin `is_suspend` reads `match.group(0)` (the matched modifiers), not a fixed look-behind window. |
| CBA-10 | `gd_resource` regex ends with `\s*[\]\s]` so `script_class` is captured on compact headers. |
| CBA-14 | JS method extractor requires a trailing `{` (declarations only) + a fuller keyword blocklist, so call-sites like `setTimeout(...)` aren't counted as methods (unmasked by the CBA-03 brace fix). |
| CBA-15 | GDScript signal doc comment = nearest preceding non-blank line (was always `None` for col-0/indented signals). |
| ENH-06 | `_call_api` threads the caller's `timeout` (was hardcoded 120s, killing large prompts). |
| ENH-07 | `scrape_all_sources` reports the count of items scraped (was the bucket count, always ~17) and returns it. |
| ENH-08 | `run()` aborts with non-zero when every source failed (was building an empty skill + exit 0). |
| ENH-09 | "Official Documentation" URL filters `type == "documentation"` (was `sources[0]`). |
| ENH-10 | `DEBUG:` synthesis logs downgraded to `logger.debug`. |
| ENH-11 | Gemini API honors `max_output_tokens`/`timeout` and rejects a truncated reply. |
| ENH-12 | Moonshot/Kimi added to the auto-detect priority in `enhance_command._pick_mode` + `enhance_skill_local._detect_api_target` (Moonshot-only users were dropped to LOCAL). |
| SCAN-03 | `get_api_key`/`set_api_key` include `moonshot` → `MOONSHOT_API_KEY`. |
| SCAN-04 | `scan --dry-run` resolves with `auto_fetch=False` (no network, no stray `./configs/` write). |
| MCP-06 | `list_configs` falls back to `sources[].base_url` for unified configs. |
| ADP-02 | `chroma`/`pinecone` split `except ImportError` from `except Exception` (don't misreport a broken-but-installed package as "not installed"). |
| CLI-03 | `CreateCommand.execute` calls `ExecutionContext.reset()` first so a 2nd in-process create rebuilds the context. |
| INF-01 | Embedding cache key includes `normalize` (`{model}:{int(normalize)}:{text}`); threaded through `server.py`. |
| INF-02 | `cleanup_old` strips the full `_YYYYMMDD_HHMMSS` timestamp via regex (retention was per-name-per-day). |
| INF-03 | `memory()` samples RSS on a background thread to capture the true peak. |
| INF-04 | `compare()` guards division by zero on instant ops. |
| INF-05 | `check_header_changes` returns `True` when the server provides no `Last-Modified`/`ETag` validators. |

### Medium tier — batch 2 (guides + document scrapers + remote scrapers)

All ✅ Fixed; verified by the guide/scraper suites + new regression tests where behavioral.

| ID | Fix summary |
|----|-------------|
| CBB-04 | `_extract_steps_python` descends one level into the test-function wrapper (else module body) instead of `ast.walk`, which flattened nested control flow out of context. |
| CBB-05 | `ai_enhancer` batch analysis maps back by an echoed `index` (was positional → a dropped/reordered entry shifted every later example's analysis). |
| CBB-06 | `_is_test_class` matches a base that *is* a `TestCase` (bare/`*TestCase`), not the `"Test" in base.id` substring that matched `LatestConfig`/`TestableMixin`. |
| CBB-07 | Index TOC sorts by a difficulty rank map (was alphabetical → advanced/beginner/intermediate). |
| CBB-08 | c3x failure returns `analysis_type="c3x_failed"` (distinct from empty) and the temp dir is removed in `finally` (was leaked every run). |
| CBB-13 | `guide_enhancer` step-enhancements map by the model's explicit `step_index`; positional fallback only when none are indexed (extracted to `_parse_step_enhancements`). |
| DOC-02 | `smart_categorize` assigns to the highest-scoring category (was the first over threshold → config-order dependent). |
| DOC-03 | Link extraction strips tracking params (`utm_*`/`fbclid`/…) + sorts the query before dedup, so tracking variants don't re-crawl the same page (preserves `?lang=`). |
| DOC-05 | PDF cross-page code merge requires a real continuation token / unbalanced bracket / block-opener colon (was `any([...])` ≈ always true) and keeps both pages' `code_blocks_count` consistent. |
| DOC-06 | Async `--dry-run` caps the preview at 20 even for unlimited configs (matches sync; was previewing the whole site). |
| MED-01 | `github_fetcher` follows `Link: rel="next"` pagination (was a single ≤100 page). Regression test added. |
| MED-02 | Slack: per-channel try/except so one channel can't abort all; `conversations_history` retries on 429 with `Retry-After`. |
| MED-03 | Discord: `ClientTimeout(30)`, 429 `Retry-After` retry, and a guarded `before` cursor (`.get("id")`). |

### Medium tier — batch 3 (systemic nav-link fix)

| ID | Status | Fix summary |
|----|--------|-------------|
| DOC-07 + MED-04 | ✅ Fixed | **Broken SKILL.md nav links across all 7 scrapers** (pdf/html/word/epub/jupyter/asciidoc/pptx). Each scraper now routes its SKILL.md nav, `index.md`, and reference-file writer through ONE filename helper (`_reference_filename`, or the pre-existing `_ref_filename` for asciidoc/jupyter), so nav links match the actual range/basename filenames instead of pointing at nonexistent `sanitize(title).md`. Regression test: `test_pdf_scraper.py::...test_reference_filename_matches_nav_and_index`. |
| ADP-01 | ✅ Fixed | **`--streaming` was dead for every target.** `StreamingAdaptorMixin` was never inherited, so `hasattr(adaptor, "package_streaming")` was always False. Fixed the mixin's fragile `sys.path` import (now `from skill_seekers.cli.streaming_ingest import …`) and made all 8 RAG/vector adaptors (langchain, llama-index, chroma, haystack, weaviate, qdrant, faiss, pinecone) inherit it. `--streaming` now produces a real streamed package; non-streaming targets (claude/markdown) still fall back with the announced message. Regression + end-to-end test in `test_adaptors/test_langchain_adaptor.py`. |

| CLI-04 | ✅ Fixed | **`_reconstruct_argv` argv round-trip removed; all 15 legacy commands migrated to namespace dispatch.** Each command's `main(args=None)` now accepts the central parsed namespace (re-parses only when invoked standalone via the `skill-seekers-<cmd>` entry points). The dispatcher calls `module.main(args=args)` directly and `_reconstruct_argv` is deleted. Fixed the drift the round-trip had been masking: aligned 4 central positional dests to the modules (`skill_directory`→`skill_dir`, `input_file`→`input` via `metavar`), added `--welcome` to the config parser, and backfill module-parser defaults for options the central parser doesn't expose. **This also fixed a pre-existing live bug: `skill-seekers workflows …` was broken** (`unrecognized arguments: --workflows-action`) and now works. Verified: 345 command-suite tests + all 16 commands dispatch cleanly. |

Deferred (Medium):
- **DOC-04** — `DEFAULT_MAX_PAGES = -1` (unbounded default crawl). Changing the default to finite is a user-visible behavior change; left for an explicit decision (not selected for fixing).

> **Test-harness note:** the *full* `pytest tests/` run is unsafe to execute repeatedly — `@pytest.mark.slow` tests like `test_bootstrap_skill::test_bootstrap_script_runs` and the `test_create_integration_basic` subprocess tests invoke the real `create` pipeline, which spawns live LLM agents (a fork-bomb). Verify with targeted per-module test files and `-m "not slow and not integration"`.

---

## Triage index — Critical & High

| ID | Sev | Title | File |
|----|-----|-------|------|
| ENH-01 | Critical | Truncated SKILL.md silently overwrites the original | `enhance_skill.py` / `agent_client.py` / `adaptors/claude.py` |
| SCAN-01 | Critical | Scan AI github-config generation always rejected by validator | `scan_command.py:426` |
| CBB-01 | Critical | LOCAL-mode guide enhancement calls a non-existent method (silent no-op) | `guide_enhancer.py:307` |
| MCP-01 | Critical | `push_config` strips its own token → broken for private repos | `mcp/config_publisher.py:170,210` |
| CBA-13 ★ | Critical | GDScript class dicts use `"bases"`; consumer reads `"base_classes"` | `code_analyzer.py:1986` |
| SCAN-02 | High | Non-numeric AI `confidence` crashes the whole scan | `scan_command.py:394` |
| CLI-01 | High | `--no-issues/--no-changelog/--no-releases` are dead on `create` | `create_command.py:270` |
| CLI-02 | High | `--output` ignored for all non-local sources; enhancement targets wrong dir | `create_command.py:215` |
| CBA-01 | High | Singleton precedence bug bypasses the confidence gate | `pattern_recognizer.py:453` |
| CBA-02 | High | `total_emissions` iterates `.items()` → always 2×#signals | `signal_flow_analyzer.py:172` |
| CBA-03 | High | JS/TS class body truncated at first `}` → later methods dropped | `code_analyzer.py:301` |
| CBA-04 | High | Subclass detection misses generic/qualified bases | `pattern_recognizer.py:819` |
| CBB-02 | High | Verification points overwritten/misattributed across steps | `how_to_guide_builder.py:185` |
| MCP-02 | High | `install_skill` package-path regex never matches real output | `tools/packaging_tools.py:602` |
| MCP-03 | High | `scrape_docs` drops `skip_scrape` and `dry_run` (unified) | `tools/scraping_tools.py:144` |
| MCP-04 | High | `submit_config` has no idempotency guard → duplicate issues | `tools/source_tools.py:570` |
| MCP-05 | High | `install_skill` infers failure from `"❌"` substring | `tools/packaging_tools.py:523` |
| ENH-02 | High | Direct Moonshot key misrouted to OpenAI | `agent_client.py:202` |
| ENH-03 | High | Headless "success" requires the file to *grow* | `enhance_skill_local.py:900` |
| ENH-04 | High | Kimi stdout parser drops all multi-line responses | `agent_client.py:467` |
| ENH-05 | High | Stray `.json` in agent cwd returned as the LLM response | `agent_client.py:419` |
| CBB-03 | High | `common_problems.remove()` mutates shared insights | `generate_router.py:421` |
| CBB-12 ★ | High | `dependencies=imports` shares one mutable list across examples | `test_example_extractor.py:394` |

---

# Critical

## ENH-01 — Truncated SKILL.md silently overwrites the original `Confirmed · High`
**Location:** `cli/enhance_skill.py:75-94`; `cli/agent_client.py:286-301`; reachable save path `cli/adaptors/claude.py:384-405`; unified path `cli/unified_scraper.py:2079`.
**Trigger:** Enhancement output exceeds `max_tokens` (4096 in `enhance_skill.py`/`agent_client.py`; 8192 in the unified path), or the model otherwise stops with `stop_reason="max_tokens"`.
**Mechanism:** All call sites read `message.content[0].text` / iterate for `block.text` with **no** check of `message.stop_reason` (Anthropic) or `choices[0].finish_reason` (OpenAI). The reachable save path renames the original to `SKILL.md.backup` **first** (claude.py:400), then writes the new content (claude.py:404). So a truncated body overwrites the live file; the only intact copy is the backup.
**Impact:** Any non-trivial skill gets silently chopped to ~4k output tokens (broken frontmatter/fences) and saved as "complete." Silent data loss of the primary deliverable; the run reports success.
```python
message = client.messages.create(model=..., max_tokens=4096, ...)
enhanced_content = message.content[0].text          # no stop_reason check
if skill_md_path.exists():
    skill_md_path.rename(skill_md_path.with_suffix(".md.backup"))   # original moved away first
skill_md_path.write_text(enhanced_content, ...)      # truncated body wins
```
**Fix:** Check the stop reason before touching the original; abort on truncation. Also write to a temp file and `os.replace` only after a successful, complete write (so failure can never leave the dir without a `SKILL.md`).
```python
if getattr(message, "stop_reason", None) == "max_tokens":
    print("❌ Response truncated (max_tokens); leaving original SKILL.md intact.")
    return False
```

## SCAN-01 — Scan AI github-config generation always rejected by the validator `Confirmed · High`
**Location:** `cli/scan_command.py:426` (`_GENERATE_SCHEMA_HINT`); validated at `scan_command.py:555` via `UniSkillConfigValidator(data).validate()`; rejection at `cli/config_validator.py:266-272` against `VALID_DEPTH_LEVELS` (`config_validator.py:71`).
**Trigger:** Any unmapped detection that falls through to `generate_config_with_ai`. The hint sits inside the `"type": "github"` source block, and `"standard"` is a plain literal, so a prompt-compliant model copies it verbatim.
**Mechanism:** The schema hint tells the AI to emit `"code_analysis_depth": "standard"`, but the validator's github-source branch only accepts `{surface, deep, full}`. `generate_config_with_ai` validates AI output and rejects on raise; the retry reuses the same hint, so attempt 2 reproduces the same invalid value. After `max_attempts` the detection lands in `result.failed`.
**Impact:** The headline `scan` feature — "generate a config for an unmapped framework" — systematically produces nothing for any library with a github source. Two wasted AI calls per detection, zero output.
```python
"code_analysis_depth": "standard",   # scan_command.py:426 — not a valid level
# config_validator.py:71
VALID_DEPTH_LEVELS = {"surface", "deep", "full"}
```
**Fix:** `"code_analysis_depth": "deep",` (or `"surface"`).

## CBB-01 — LOCAL-mode guide enhancement calls a non-existent method `Confirmed · High`
**Location:** `cli/guide_enhancer.py:307`.
**Trigger:** `build-how-to-guides` runs with AI enhancement when no API key is set (`auto` → `AgentClient.mode == "local"`) or `ai_mode="local"`.
**Mechanism:** `_enhance_via_local` calls `self._call_claude_local(prompt)`, which is defined nowhere (only `_call_ai` at :263 exists; every other call site uses it). The `AttributeError` is swallowed by the broad `except Exception` in `enhance_guide` (:106-109), which logs and returns the original `guide_data`.
**Impact:** Every LOCAL-mode (no-API-key) guide build silently returns **unenhanced** guides while logging a generic "AI enhancement failed." Local-mode guide enhancement has never worked.
```python
def _enhance_via_local(self, guide_data: dict) -> dict:
    prompt = self._create_enhancement_prompt(guide_data)
    response = self._call_claude_local(prompt)   # NameError: no such method
```
**Fix:** `response = self._call_ai(prompt)`.

## MCP-01 — `push_config` strips its own auth token → broken for private repos `Confirmed · High`
**Location:** `mcp/config_publisher.py:170,210` (compounded by ★MCP-12 / ★MCP-13).
**Trigger:** Any `push_config` to a private/authenticated source repo.
**Mechanism:** The clone uses a token-injected URL, but line 170 immediately runs `origin.set_url(git_url)` (tokenless) "to scrub the token," and the push at line 210 goes through that tokenless `origin`. `marketplace_publisher.py:160` does it correctly — it pushes to a freshly token-injected URL.
**Impact:** The push fails with an auth error *after* the commit, leaving the cache repo with an orphan commit. `push_config` to the primary (private) config source is effectively non-functional. ★MCP-12 and ★MCP-13 (below) make the second run fail at pull and leave the cache on a stranded branch — together they fully break the feature and corrupt the cache.
```python
repo_obj.remotes.origin.set_url(git_url)   # :170 scrubs token from origin
...
repo.remotes.origin.push(target_branch)    # :210 pushes via tokenless origin
```
**Fix:** `repo.git.push(self.git_repo.inject_token(git_url, token), target_branch)`.

## CBA-13 ★ — GDScript class dicts use key `"bases"`; consumer reads `"base_classes"` `Confirmed · High`
**Location:** `cli/code_analyzer.py:1986` vs `cli/pattern_recognizer.py:367`.
**Trigger:** Any GDScript file with `class_name Foo extends Bar` run through `PatternRecognizer`.
**Mechanism:** `_analyze_gdscript` emits class dicts with the key `"bases"` — the only one of 11 analyzers to do so (the other 10 use `"base_classes"`). `_convert_to_signatures` reads `cls.get("base_classes", [])`, so for GDScript the base list is always `[]`.
**Impact:** All inheritance-based pattern detection (Strategy/Template-Method `subclasses`, Observer/Chain families — every `name in cls.base_classes` check) is silently dead for GDScript, a first-class target (C3.10 signal-flow pipeline).
```python
classes.append({
    "name": class_name,
    "bases": [extends] if extends else [],   # wrong key
    ...
})
```
**Fix:** rename to `"base_classes"`.

---

# High

## SCAN-02 — Non-numeric AI `confidence` crashes the whole scan `Confirmed · High`
**Location:** `cli/scan_command.py:394`; propagates through `run_scan` → `_amain` (only catches `KeyboardInterrupt`/`RuntimeError`).
**Trigger:** AI returns `"confidence": "high"` / a list / explicit `null` (LLMs do this despite the "0-1" instruction). Missing key is safe (defaults to `0.0`).
**Mechanism:** `float(entry.get("confidence", 0.0))` is inside the per-entry loop, which is **not** wrapped in try/except (only `client.call` is). `float("high")` raises `ValueError`; it unwinds out of `asyncio.run`.
**Impact:** One malformed entry aborts the entire command with a traceback, discarding all valid detections.
```python
confidence = float(entry.get("confidence", 0.0))   # unguarded
```
**Fix:** wrap in `try/except (TypeError, ValueError): continue`.

## CLI-01 — `--no-issues/--no-changelog/--no-releases` are dead on `create` `Confirmed · High`
**Location:** `cli/create_command.py:270-283`; dests in `arguments/create.py:298-318` & `arguments/github.py:49-69`; consumer `github_scraper.py:257-266`.
**Trigger:** `skill-seekers create owner/repo --no-issues` (or `--no-changelog`/`--no-releases`).
**Mechanism:** The parser defines the **negative** dests `no_issues/no_changelog/no_releases`, but `_build_config` reads the never-defined positive keys `include_issues/include_changelog/include_releases` via `getattr(..., True)`, so they're always `True`. No `no_*→include_*` translation exists anywhere. `include_code` has no flag at all.
**Impact:** `--no-issues` still fetches every issue (potential rate-limit exhaustion); the three opt-out flags are no-ops on the only entry point that exists.
```python
"include_issues": getattr(self.args, "include_issues", True),   # attr never exists
```
**Fix:** `"include_issues": not getattr(self.args, "no_issues", False)` (and the others).

## CLI-02 — `--output` ignored for all non-local sources; enhancement targets the wrong dir `Confirmed · High`
**Location:** `cli/create_command.py:215-430` (`_build_config`) & `:450-457` (`_run_enhancement`); scrapers `doc_scraper.py:209`, `notion_scraper.py:99`, `pdf_scraper.py:79`, `unified_scraper.py:120`.
**Trigger:** `create <web/github/pdf/... source> --output /tmp/x` (anything but `output/{name}`), especially with `--enhance-level > 0`.
**Mechanism:** `_build_config` only forwards `output_dir` for the `local` branch; the other scrapers hardcode `self.skill_dir = f"output/{name}"`. But `_run_enhancement` computes `skill_dir = ctx.output.output_dir`, which *does* honor `--output`.
**Impact:** Output always lands in `output/{name}` (flag silently ignored); enhancement then runs against the empty `--output` dir and fails — and since `_run_enhancement` swallows exceptions (★CLI-06), the run still exits 0 with an un-enhanced skill in the wrong place.
**Fix:** have every converter read `config.get("output_dir") or f"output/{self.name}"`, and set `config["output_dir"]` in every `_build_config` branch.

## CBA-01 — Singleton precedence bug bypasses the confidence gate `Confirmed · High`
**Location:** `cli/pattern_recognizer.py:453`.
**Mechanism:** `if has_instance_method or has_init_control and confidence >= 0.5:` parses as `has_instance_method or (...)`. Any class with a method named `instance`/`getInstance` is flagged Singleton at confidence 0.4, bypassing the 0.5 gate.
**Impact:** False-positive Singletons for any class exposing an `instance`-style accessor (e.g. ORM models).
**Fix:** `if (has_instance_method or has_init_control) and confidence >= 0.5:`.

## CBA-02 — `total_emissions` iterates `.items()` → always 2× signal count `Confirmed · High`
**Location:** `cli/signal_flow_analyzer.py:172` (line 171 correctly uses `.values()`).
**Mechanism:** `sum(len(emits) for emits in self.signal_emissions.items())` — each `emits` is a `(key, list)` 2-tuple, so `len` is always 2. Result = `2 × (#emitting signals)`, decoupled from real emission count.
**Impact:** "Total Emissions" in every Godot signal-flow report (`signal_flow.json`, `signal_reference.md`) is meaningless.
**Fix:** `.values()`.

## CBA-03 — JS/TS class body truncated at first `}` `Confirmed · High`
**Location:** `cli/code_analyzer.py:301`.
**Mechanism:** `class_block_end = content.find("}", class_block_start)` finds the **first** brace, not the matching one (C#/Java/Kotlin brace-count; JS doesn't). For any real JS class, the body ends at the first method's closing brace.
**Impact:** All methods after the first are dropped from JS/TS classes, breaking method-count pattern heuristics (Builder/Observer/Strategy). (Fixing this surfaces ★CBA-14.)
**Fix:** use the brace-counting loop already used in `_analyze_csharp`/`_analyze_java`.

## CBA-04 — Subclass detection misses generic/qualified bases `Confirmed · High`
**Location:** `cli/pattern_recognizer.py:819` (also 805/926/1297/1324/1476).
**Mechanism:** `class_sig.name in cls.base_classes` is exact-match, but C# bases are stored verbatim (`BaseStrategy<Foo>`), so `"BaseStrategy" in ["BaseStrategy<Foo>"]` is False. (Java strips generics, so Java works; C#/qualified `Namespace.Base` fail.)
**Impact:** Strategy/Template-Method built on C# generic bases are missed entirely; sibling/family evidence lost.
**Fix:** normalize bases before compare: `b.split("<",1)[0].split(".")[-1].strip()`.

## CBB-02 — Verification points overwritten / misattributed across steps `Confirmed · High`
**Location:** `cli/how_to_guide_builder.py:185-187`.
**Mechanism:** `_extract_steps_python` (:222-226) already pairs each step with its following assertion. Then `analyze_workflow` does `step.verification = verifications[i]` positionally, but `steps` (non-assert statements) and `verifications` (assert lines) are different filtered lists with divergent lengths/order.
**Impact:** Guides show verification code under the wrong step (e.g. step 1 shows a check that validates step 4's result), and the correct pairing is thrown away.
**Fix:** remove the positional overwrite loop; rely on the per-step pairing already done.

## CBB-03 — `common_problems.remove()` mutates shared insights `Confirmed · High`
**Location:** `cli/generate_router.py:421,436` (readers at :865, :1022).
**Mechanism:** `common_problems = self.github_issues.get("common_problems", [])` is the shared list (no copy); `.remove(issue)` deletes from it in place for up to 3 skills, **before** the "Common Issues" section and the issues-reference file read it.
**Impact:** Up to 3 of the most label-relevant issues vanish from the summary and `github_issues.md`; output is order-dependent and non-idempotent.
**Fix:** iterate `list(...)` copy and track used issues by id; never `.remove()` the shared list.

## CBB-12 ★ — `dependencies=imports` shares one mutable list across all examples `Corrected · High→Medium (latent)`
**Location:** `cli/test_example_extractor.py:394,446,490,532` (list built once at :191).
**Mechanism:** The same `imports` list object is assigned as `dependencies` to every `TestExample` from a file, and `how_to_guide_builder._detect_prerequisites` aliases it again into `metadata["required_imports"]`. Aliasing is real, **but** all current consumers only read the list — none mutate it — so there is no observable corruption today.
**Impact:** Latent: any future `.append`/`.sort` on one example's `dependencies` would silently affect all siblings (and the guide prerequisites). Reclassified **Medium** (latent) after verification.
**Fix:** `dependencies=list(imports)` at each call site.

## MCP-02 — `install_skill` package-path regex never matches real output `Confirmed · High`
**Location:** `mcp/tools/packaging_tools.py:602` vs `cli/package_skill.py:177`.
**Mechanism:** The regex matches `"saved to:"`, but `package_skill.py` prints `"Output: <path>"` and `"✅ Package created: <path>"`. The match always fails, so `zip_path` falls back to a constructed name (`{name}.zip`) that differs from real adaptor names (`{dir}-gemini.tar.gz`, etc.).
**Impact:** The upload phase receives a guessed/non-existent path while the workflow reports success.
**Fix:** match what is actually printed: `r"(?im)^\s*(?:Output|✅ Package created):\s*(.+\.(?:zip|tar\.gz))\s*$"` (better: return the path structurally).

## MCP-03 — `scrape_docs` drops `skip_scrape` entirely and `dry_run` for unified configs `Confirmed · High`
**Location:** `mcp/tools/scraping_tools.py:144-216` (wrapper `server_fastmcp.py:353-381`).
**Mechanism:** The FastMCP wrapper declares `skip_scrape`, `dry_run`, `enhance_local` and forwards them, but the impl never reads `skip_scrape`/`enhance_local`, and only sets `converter.dry_run` in the non-unified branch. `server_legacy.py` honored all three.
**Impact:** `skip_scrape=True` re-scrapes from the network (20-45 min wasted, ignores cache); `dry_run=True` performs a full scrape for unified configs. Real server_fastmcp ↔ server_legacy drift.
**Fix:** read `skip_scrape`, set `converter.dry_run = dry_run` and `converter.skip_scrape = skip_scrape` in both branches.

## MCP-04 — `submit_config` has no idempotency guard `Confirmed · High`
**Location:** `mcp/tools/source_tools.py:529-574`.
**Mechanism:** Calls `repo.create_issue(title=f"[CONFIG] {name}", ...)` unconditionally; unlike scan's `maybe_publish` (`_find_existing_issue`), it never searches for an existing open issue.
**Impact:** Re-runs create duplicate `[CONFIG] {name}` issues, polluting the review queue.
**Fix:** query `is:issue is:open in:title "{name}"` before creating; return the existing URL if found.

## MCP-05 — `install_skill` infers scrape failure from `"❌"` substring `Confirmed · Medium-High`
**Location:** `mcp/tools/packaging_tools.py:523`.
**Mechanism:** `if "❌" in scrape_output:` discards the structured returncode that `_run_converter` already provides.
**Impact:** A single skipped page logging `❌` aborts the workflow; a real failure without that emoji proceeds to package an empty skill and reports success. (★MCP-15 is the identical issue for the packaging phase, which has no check at all.)
**Fix:** return a status flag from `scrape_docs_tool`/`_run_converter` and branch on it.

## ENH-02 — Direct Moonshot/Kimi key misrouted to OpenAI `Confirmed · High`
**Location:** `cli/agent_client.py:202-217`.
**Mechanism:** `_detect_provider_from_key` returns `"moonshot"` for an `sk-` key only if `MOONSHOT_API_KEY` env equals it; otherwise any `sk-` key → `"openai"`. Moonshot keys are `sk-`-prefixed, so a key passed via `--api-key` without the env var builds an `OpenAI` client with `gpt-4o`.
**Impact:** Direct Moonshot-key usage fails auth (hits `api.openai.com`) or routes to the wrong provider, surfacing as a misleading OpenAI error.
**Fix:** accept an explicit provider hint (e.g. `SKILL_SEEKER_PROVIDER`) before defaulting to OpenAI.

## ENH-03 — Headless "success" requires the file to *grow* `Confirmed · High`
**Location:** `cli/enhance_skill_local.py:900` (headless), `:1087` (background), `:1213` (daemon).
**Mechanism:** Headless gates success on `new_mtime > initial_mtime and new_size > initial_size`; background/daemon gate only on `returncode == 0`. The three modes disagree.
**Impact:** A legitimate condensing/same-size rewrite is reported as failure in the default headless mode ("SKILL.md was not updated"), so CI/automation treats valid runs as errors.
**Fix:** gate on `new_mtime > initial_mtime` (file changed), not strictly larger size; share one predicate across modes.

## ENH-04 — Kimi stdout parser drops all multi-line responses `Confirmed · High`
**Location:** `cli/agent_client.py:467`.
**Mechanism:** `re.findall(r"TextPart\(type='text', text='(.+?)'\)", raw_output)` has no `re.DOTALL`, so `.` doesn't match newlines; every multi-line SKILL.md matches nothing and the function returns the raw `TurnBegin(...)/StepBegin(...)` debug dump. The non-greedy `'` also splits on embedded apostrophes.
**Impact:** With `--agent kimi`, SKILL.md is replaced by Kimi's raw debug log (or fragmented at apostrophes).
**Fix:** add `re.DOTALL` and anchor the terminator to the next record boundary.

## ENH-05 — Stray `.json` in agent cwd returned as the LLM response `Confirmed · High (conditional)`
**Location:** `cli/agent_client.py:385-393, 419-435` *(downgraded from Critical — conditional trigger)*.
**Mechanism:** When `output_file` is None, the prompt is `prompt.md` and no "write response" instruction is added, yet the code returns `temp/response.json` if present, else **any** `*.json` in the temp dir. The guard `!= "prompt.json"` is dead (the file is `prompt.md`). The subprocess cwd is `temp_path`, so any incidental `.json` the agent writes becomes the "response," shadowing stdout.
**Impact:** Non-deterministic: enhancement can return an unrelated JSON file's contents instead of the model's actual output. Conditional on the agent writing a stray `.json`, hence High not Critical.
**Fix:** only consult the response file when `output_file` was explicitly requested (and match exactly that file); otherwise return stdout.

---

# Medium

## Scan + config
- **SCAN-03 — `get_api_key("moonshot")` env fallback dead.** `config_manager.py:314` — `env_map` omits `moonshot`, so a user who exports `MOONSHOT_API_KEY` (no config-file key) gets `None`, while `config_command.py:329` shows "(from environment)". `set_api_key`'s error text also omits moonshot. *Fix:* add `"moonshot": "MOONSHOT_API_KEY"`. `Confirmed`
- **★SCAN-04 — `--dry-run` writes `./configs/` and hits the network.** `scan_command.py:1162` calls `resolve_config_path(lookup, auto_fetch=allow_network)` (default True) in the dry-run branch; on an API hit `fetch_config_from_api` performs HTTP GETs and writes `./configs/<name>.json`, contradicting the "DRY RUN — no files written" promise (`:1287`). *Fix:* pass `auto_fetch=False` in dry-run. `Confirmed`

## CLI core
- **CLI-03 — `ExecutionContext.reset()` never called in production.** `execution_context.py:207-228` — the singleton guard returns the existing instance; `reset()` exists but only tests call it. A 2nd in-process `create` reuses the 1st's name/output/settings. Latent today (MCP runs scrapes in subprocesses; CLI is one-shot). *Fix:* call `reset()` at the top of `CreateCommand.execute()`. `Confirmed`
- **★CLI-04 — Legacy `_reconstruct_argv` round-trips the full namespace.** `main.py:179-186` re-serializes every namespace attribute to argv for ~14 legacy commands; attributes unknown to a sub-parser are emitted as `--unknown-flag value`, which the sub-parser can reject. Brittle; the documented migration to `COMMAND_CLASSES` is the fix. `Confirmed`

## Adaptors
- **ADP-01 — `--streaming` is dead for every adaptor.** `streaming_adaptor.py:21` + `package_skill.py:149` — `StreamingAdaptorMixin` is never imported or inherited by any registered adaptor, so `hasattr(adaptor,"package_streaming")` is always False. *Corrected:* the fallback **announces** "Streaming not supported… using standard packaging" (not silent), but the feature is fully dead. *Fix:* have RAG adaptors inherit the mixin or register the streaming variants. `Corrected`
- **ADP-02 — `except (ImportError, Exception)` masks all import errors.** `chroma.py:236`, `pinecone_adaptor.py:328` — `Exception` subsumes `ImportError`, so a broken-but-installed package (e.g. chromadb/py3.14 pydantic-v1) is misreported as "not installed." *Fix:* split the handlers. `Confirmed`

## MCP
- **MCP-06 — `list_configs` reads top-level `base_url`; unified configs store it under `sources[0]`.** `tools/config_tools.py:136` — every config `generate_config` produces lists a blank URL. *Fix:* fall back to `sources[].base_url`. `Confirmed`
- **★MCP-12 — `config_publisher` `get_source` raises `KeyError`; the `if not source:` branch is dead.** `config_publisher.py:140-143` — an unknown source name raises a raw `KeyError` (quoted message) instead of the curated "Available sources" error. *Fix:* wrap in `try/except KeyError`. `Confirmed`
- **★MCP-13 — `config_publisher` tokenless re-pull on the 2nd run.** `config_publisher.py:161-172` — on a cached repo it pulls via `origin` (scrubbed tokenless by the prior run's :170) before re-injecting the token, so a 2nd push to a private repo fails at pull. Compounds MCP-01. *Fix:* `origin.set_url(clone_url)` before pulling. `Confirmed`

## Codebase analysis (AST / pattern / dependency)
- **CBA-05 — "protocol" boosts ANY pattern.** `pattern_recognizer.py:1538-1542` — `type=="Strategy" and "duck typing" in s or "protocol" in s` precedence → the `"protocol"` clause fires for any Python pattern. *Fix:* parenthesize the OR group. `Confirmed`
- **CBA-06 — "event" boosts ANY pattern (+ false "EventEmitter detected").** `pattern_recognizer.py:1559-1563` — same precedence flaw for JS/TS. `Confirmed`
- **CBA-07 — `_resolve_import` never maps dotted module → file path.** `dependency_analyzer.py:784-814` — `file_nodes` keys are file paths (`src/pkg/mod.py`) while `imported_module` is `pkg.mod`; no dot→slash conversion. The dependency graph is essentially edgeless and cycle detection returns empty for **all dotted-import languages** (Python/Java/C#/Kotlin/Go/Rust/Ruby/PHP). *Corrected:* Godot resource graphs (slash paths) **do** resolve. *Fix:* convert dots to slashes + suffix-match against `file_nodes`. `Confirmed`
- **CBA-08 — Kotlin top-level-fn `indent > 4` heuristic.** `code_analyzer.py:1379-1383` — tab/2-space-indented methods are misclassified as top-level, and indented top-level fns are dropped. *Fix:* track brace depth instead of indentation. `Confirmed`
- **CBA-09 — Kotlin `is_suspend` look-behind reads before the modifier.** `code_analyzer.py:1385` — the 50-char window precedes the match (which already includes `suspend`), so real `suspend fun` reads False and a neighboring `suspend` reads True. *Fix:* `"suspend" in match.group(0)`. `Confirmed`
- **CBA-10 — `gd_resource` regex drops `script_class` on compact headers.** `code_analyzer.py:1875` — trailing `\s+` can't match `]`, so `[gd_resource type="X" script_class="Y"]` yields `script_class=None`. *Fix:* end with `\s*[\]\s]`. `Confirmed`
- **★CBA-14 — JS method extractor matches call-sites and keywords.** `code_analyzer.py:391-419` — `(\w+)\s*\(...\)` matches any `ident(args)`; only 4 keywords are blocklisted, so `this.helper(b)`, `setTimeout(...)` become "methods." Masked today by CBA-03 (truncation); surfaces once CBA-03 is fixed. *Fix:* anchor to `\s*\{` declarations and exclude the full JS keyword set. `Confirmed`
- **★CBA-15 — GDScript signal doc comment read from the wrong line.** `code_analyzer.py:2043-2047` — for a signal at column 0, `content[:start].split("\n")[-1]` is the empty pre-`signal` text; the doc comment is `lines[-2]`. So `## doc \n signal x` always yields `documentation=None`. *Fix:* use `lines[-2]`. `Confirmed`

## Codebase analysis (example / guide / router)
- **CBB-04 — `ast.walk` flattens nested statements.** `how_to_guide_builder.py:204-206` — statements inside `if`/`for`/`with`/`try` are hoisted into the flat step list, losing control-flow context. *Fix:* iterate top-level body only. `Confirmed`
- **CBB-05 — AI `ai_analysis` aligned by position, not `example_id`.** Real site `ai_enhancer.py:360-362` (the extractor re-merge at `test_example_extractor.py:1088` is actually order-safe). If the model drops/reorders an entry, every later example gets another's analysis (and `tutorial_group`, which drives guide grouping). *Fix:* key by `example_id`. `Confirmed`
- **CBB-06 — `_is_test_class` `"Test" in base.id` over-matches.** `test_example_extractor.py:218-225` — any base whose name *contains* "Test" (`LatestConfig`, `TestableMixin`) flags the class as a test. *Fix:* `endswith("TestCase")` / explicit bases. `Confirmed`
- **CBB-07 — Index TOC sorts complexity alphabetically.** `how_to_guide_builder.py:789` — `sorted(..., key=g.complexity_level)` → `advanced, beginner, intermediate`. *Fix:* explicit rank map. `Confirmed`
- **CBB-08 — c3x failures look like empty results; temp dir leaks.** `unified_codebase_analyzer.py:288-305` — broad `except` returns `analysis_type:"c3x"` with empty arrays + an easily-ignored `error` key; `tempfile.mkdtemp` (:255) is never cleaned. *Fix:* mark a distinct failure type and `shutil.rmtree` in `finally`. `Confirmed`
- **★CBB-13 — Guide step-description index trust.** `guide_enhancer.py:552-560` + `how_to_guide_builder.py:1050-1055` — step explanations routed by AI-supplied `step_index` with an enumerate fallback; a dropped entry shifts every subsequent explanation onto the wrong step. *Fix:* require an explicit in-range `step_index`; skip otherwise. `Confirmed`

## Document scrapers
- **DOC-02 — `smart_categorize` assigns to first category over threshold, not max.** `doc_scraper.py:1837-1840` — `break`s on the first category reaching score 2 (config-order dependent); siblings use `max(scores,...)`. *Corrected severity High→Medium.* *Fix:* collect all scores, assign to `max`. `Confirmed`
- **DOC-03 — Link extraction keeps query strings.** `doc_scraper.py:432-437` — only `#fragment` is stripped, so `?lang=`/`?utm=` variants are distinct pages (crawler-trap risk in unlimited mode). *Fix:* drop tracking params / normalize query before dedup. `Confirmed`
- **DOC-04 — `DEFAULT_MAX_PAGES = -1` ⇒ unbounded default crawl.** `doc_scraper.py:1443-1450`; `defaults.json:7` — a config without `max_pages` enters unlimited mode. *Fix:* finite default (e.g. 1000); require explicit `-1` for unlimited. `Confirmed (by-design footgun)`
- **DOC-05 — PDF cross-page code merge heuristic is ~always true; count drift.** `pdf_extractor_poc.py:606-623` — `any([not endswith("}"), not endswith(";"), ...])` merges unrelated adjacent blocks; `code_blocks_count` decremented on next page but not incremented on current. *Fix:* require a real continuation token; recompute counts from `len(code_samples)`. `Confirmed`
- **DOC-06 — Async unlimited dry-run doesn't cap at 20.** `doc_scraper.py:1613-1620` — sets `preview_limit=inf` before checking `dry_run` (sync caps at 20 unconditionally), so async `--dry-run` on a default config previews the entire site. *Fix:* set `preview_limit=20` when `dry_run` first. `Confirmed`
- **DOC-07 — Broken SKILL.md nav links (pdf/html/word/epub).** `pdf_scraper.py:530`, `html_scraper.py:1562`, `word_scraper.py:631`, `epub_scraper.py:800` — nav links to `references/{sanitize(title)}.md` but files are written with range/basename names (`_pX-pY`, `_sX-sY`, raw basename). Dead links for any multi-section/multi-category source. (Same root cause as MED-04 — see systemic pattern S2.) *Fix:* derive nav names from the same filename helper that writes the files. `Confirmed`

## Media / structured / remote scrapers
- **MED-01 — GitHub issues capped at 100 (no Link pagination).** `github_fetcher.py:299-345` — single page, `per_page=min(max,100)`, no `rel="next"`; PR filtering reduces further. *Corrected severity High→Medium.* *Fix:* loop on the `next` link. `Confirmed`
- **MED-02 — Slack 429 aborts all channels.** `chat_scraper.py:648-722` — `conversations_history` has no 429/retry, and the per-channel loop is in one try whose `except SlackApiError` raises a fatal `RuntimeError`, losing already-fetched channels. *Fix:* per-channel try/except + `Retry-After` backoff. `Confirmed`
- **MED-03 — Discord session has no timeout; 429 silently breaks.** `chat_scraper.py:827-878` — no `ClientTimeout`; a 429 is treated as a generic non-200 → silent `break`. *Fix:* add timeout + honor `Retry-After`. `Confirmed`
- **MED-04 — Broken SKILL.md nav links (jupyter/asciidoc/pptx).** `jupyter_scraper.py:966`, `asciidoc_scraper.py:841`, `pptx_scraper.py:1467` — same nav vs file naming mismatch as DOC-07. *Verified:* Confluence/RSS are consistent (not affected). *Fix:* shared filename helper. `Confirmed`

## Enhancement + unified builder
- **ENH-06 — `_call_api` ignores the caller's `timeout`.** `agent_client.py:295-309` — `call()` computes a timeout (default 45 min) but `_call_api` hardcodes `timeout=120`. Large prompts fail at 2 min with a misleading "connection error." *Fix:* thread `timeout` through. `Confirmed`
- **ENH-07 — `scrape_all_sources` reports the bucket count, not sources scraped.** `unified_scraper.py:256` — `len(self.scraped_data)` is always ~17. *Fix:* `sum(len(v) for v in ...)`. `Confirmed`
- **ENH-08 — All-sources-fail still builds and returns 0.** `unified_scraper.py:252-254` — per-source exceptions swallowed; `run()` proceeds to `build_skill` on empty data and exits 0. *Fix:* count scraped sources; return non-zero on zero. `Confirmed`
- **ENH-09 — "Official Documentation" reads `sources[0]` regardless of type.** `unified_skill_builder.py:280` — prints `N/A` (or a non-docs URL) if github is listed first. *Fix:* filter `type == "documentation"`. `Confirmed`
- **ENH-10 — `DEBUG:` log lines left in production synthesis.** `unified_skill_builder.py:327-332` — `logger.info("DEBUG: ...")` and `logger.warning("DEBUG: ... NOT FOUND!")` fire on every docs+github synthesis. *Fix:* `logger.debug`, drop the alarm wording. `Confirmed`
- **★ENH-11 — Gemini API mode ignores `timeout` and `max_tokens`.** `agent_client.py:312-315` — `generate_content(prompt)` with no `generation_config`/timeout; output capped at the model default, request unbounded. With ENH-01 the truncation is doubly invisible. *Fix:* pass `max_output_tokens`/`request_options` and check `finish_reason`. `Confirmed`
- **★ENH-12 — Provider-priority lists are inconsistent; Moonshot dropped in `_pick_mode`.** `agent_client.py:84-90` honors `MOONSHOT_API_KEY`, but `enhance_command._pick_mode` and `enhance_skill_local._detect_api_target` only check claude/gemini/openai. A Moonshot-only user is silently dropped to LOCAL mode by the `enhance` command. *Fix:* add a moonshot/kimi branch; share one priority order. `Confirmed`

## Args / infra
- **INF-01 — Embedding cache key omits `normalize`.** `embedding/generator.py:414-418`; `server.py:138,182,209` — cache keyed `(model,text)` only; a `normalize=False` request after a cached `normalize=True` returns the wrong (normalized) vector. *Fix:* include `int(normalize)` in the key. `Confirmed`
- **INF-02 — `cleanup_old` folds the date into the group key.** `benchmark/runner.py:293-295` — filename is `{name}_{%Y%m%d_%H%M%S}`; `"_".join(parts[:-1])` leaves `{name}_{date}`, so retention is per-name-per-day → old files never pruned. *Fix:* `parts[:-2]`. `Confirmed`
- **INF-03 — `peak_mb` never samples during the op.** `benchmark/framework.py:184-192` — only `max(before, after)`; transient spikes invisible, so leak/memory recommendations under-report. *Fix:* sample RSS on a background thread during `yield`. `Confirmed`
- **INF-04 — `compare()` divides by zero on instant ops.** `benchmark/runner.py:160,195` — no guard on `current.duration == 0`. *Fix:* guard with `float("inf")`. `Confirmed`
- **INF-05 — Header change-detection misses validator-less servers.** `sync/detector.py:270-277` — returns `False` (unchanged) when neither `Last-Modified` nor `ETag` is present, so `batch_check_headers` silently drops genuinely-changed pages (the `except` branch returns `True`, inconsistently). *Fix:* return `True` when no validators are available. `Confirmed`

---

# Low

## Scan + config
- **SCAN-05 — API-fetched configs written to `./configs/` regardless of `--out`.** `config_fetcher.py:196` — hardcoded `destination="configs"` pollutes CWD (scan re-writes to out_dir anyway). *Fix:* thread the out dir / temp dir through. `Confirmed`
- **SCAN-06 — Module-level `logging.basicConfig` in a library.** `config_validator.py:33` — can win over scan's `--verbose` depending on import order. *Fix:* remove from the library module. `Confirmed`
- **SCAN-07 — Duplicate-slug detections double-count.** `scan_command.py:1149-1199` — the diff dedups by slug, but the main loop double-writes/double-counts duplicate-slug detections. *Fix:* dedup detections by `_config_filename_for`. `Confirmed`

## CLI core
- **CLI-05 — `run()` success log prints `output/{name}` for local builds.** `skill_converter.py:46` + `codebase_scraper.py:2154` — artifacts go to `output_dir` (honors `--output`) but the base log shows `skill_dir`. *Fix:* set `self.skill_dir = str(self.output_dir)`. `Confirmed`
- **CLI-06 — confluence/notion `max_pages` dead `DEFAULTS` fallback.** `create_command.py:404,415` — `getattr(..., DEFAULTS[...])` fallback is unreachable (`max_pages` always present as `None`); harmless because `None` is treated as unlimited like `-1`. *Corrected (no behavioral impact).* `Corrected`
- **★CLI-07 — `_run_enhancement`/`_run_workflows` swallow all exceptions; exit 0.** `create_command.py:504-516` — enhancement/workflow failure never affects the exit code (CI can't detect it). Compounds CLI-02. *Fix:* track success, return non-zero or emit a clear failure summary. `Confirmed`
- **★CLI-08 — `merge_sources(mode="ai-enhanced")` not recognized.** `merge_sources.py:766-769` — only `"claude-enhanced"` is special-cased, so the canonical `"ai-enhanced"` falls through to rule-based merging for direct callers. *Fix:* accept both spellings. `Confirmed`
- **★CLI-09 — Module-level `logging.basicConfig` in `merge_sources.py:36`.** Same library-logging hazard as SCAN-06 (imported transitively via `generate_router`). *Fix:* remove. `Confirmed`

## Adaptors
- **ADP-03 — Weaviate adaptor uses v3-only API; pin allows v4.** `weaviate.py:341-379`; pin `weaviate-client>=3.25.0` — `weaviate.Client`, `schema.create_class`, `client.batch` all raise `AttributeError` on v4. *Fix:* cap `<4` or port to the v4 API. `Confirmed`
- **ADP-04 — OpenAI upload uses `client.beta.vector_stores`.** `openai.py:260-280`; pin `openai>=1.0.0` — promoted to `client.vector_stores` in newer SDKs; deprecated path may raise. *Fix:* prefer top-level with fallback; pin a known-good range. `Confirmed (Conf: Low)`
- **ADP-05 — Unquoted YAML name/description in Claude frontmatter.** `claude.py:76-80` — colon-space / leading-quote in `description` produces invalid YAML (OpenCode/IBM-Bob quote; Claude doesn't). *Fix:* quote/escape the values. `Confirmed`
- **ADP-06 — Enhance renames SKILL.md to `.backup` before writing; empty response loses it.** `openai_compatible.py:349-357` (+ openai/gemini/claude) — a successful-but-empty/None response leaves the dir with no `SKILL.md`. *Fix:* validate non-empty before renaming; write-temp-then-swap. `Confirmed`
- **ADP-07 — LlamaIndex uses `format="hex"` while base docstring claims uuid5.** `llama_index.py:43` vs `base.py:481` — doc/behavior mismatch only (hex ids are valid). *Fix:* correct the docstring. `Confirmed`
- *Verified correct:* the thin OpenAI-compatible subclasses (kimi/deepseek/qwen/openrouter/together/fireworks/minimax) have correct, distinct model ids / endpoints / env vars / registry keys; vector-DB dimensions/metrics are consistent.

## MCP
- **MCP-07 — `config_publisher` commit `action` term is meaningless.** `config_publisher.py:204` — `target_file.exists()` is always True post-copy. *Fix:* capture existence before copy, or use `"update" if force else "add"`. `Confirmed`
- **MCP-08 — Three tool params typed `str` but default `None`.** `server_fastmcp.py:1342,1403,1404` — should be `str | None`; schema advertises non-nullable. `Confirmed`
- **MCP-09 — `enhance_skill` returns identical shape on success/failure.** `tools/packaging_tools.py:329-344` — callers can't distinguish without substring scanning. *Fix:* structured error signal. `Confirmed`
- **MCP-10 — `sync_config` wrapper hardcodes `max_pages=500`.** `server_fastmcp.py:279` vs `tools/sync_config_tools.py:40` — the impl's `DEFAULTS` (-1/unlimited) default is dead; MCP path silently caps at 500. *Fix:* default to `None`, forward only if set. `Confirmed`
- **MCP-11 — Unlimited temp path is non-unique and uses `str.replace`.** `tools/scraping_tools.py:169` — `config_path.replace(".json", "_unlimited_temp.json")` collides on concurrency and rewrites any `.json` substring. *Fix:* `tempfile.mkstemp`. `Confirmed`
- **★MCP-14 — `config_publisher` left on the feature branch after a mid-flow exception.** `config_publisher.py:198-219` — no try/finally to restore `branch`; a push failure strands the cache on `config/<name>`. *Fix:* restore branch in `finally`. `Confirmed`
- **★MCP-15 — `package_skill_tool` returncode swallowed in `install_skill`.** `tools/packaging_tools.py:85-143` — no success check after packaging; a failed package still yields a fabricated `zip_path`. *Fix:* structured success signal; abort on failure. `Confirmed`
- **★MCP-16 — `generate_config` silently overwrites an existing config.** `tools/config_tools.py:80-84` — no `exists()`/`force` guard; clobbers hand-edited configs. *Fix:* add a `force` arg and guard. `Confirmed`
- **★MCP-17 — `_run_converter` attaches a handler to the shared `skill_seekers` logger.** `tools/scraping_tools.py:41-70` — concurrent converter tools cross-contaminate captured logs. *Fix:* per-call scoped capture. `Confirmed`

## Codebase analysis
- **CBA-11 — Comment extractors match `//` / `/* */` inside string literals.** `code_analyzer.py:581,588` — URLs in strings yield phantom comments. *Fix:* strip string literals first. `Confirmed`
- **CBA-12 — Single-letter CSS classes `c`/`r` matched as C/R.** `language_detector.py:688,708` — bare-name branch returns confidence 1.0 for ambiguous tokens. *Fix:* require a prefix for `c`/`r`. `Confirmed`
- **★CBA-16 — Go grouped-import line numbers off by one.** `dependency_analyzer.py:495` — uses `match.start()` (at `import`) instead of `match.start(1)` (after `import (\n`). *Fix:* `block_start = match.start(1)`. `Confirmed`

## Codebase analysis (guides)
- **CBB-09 — Duplicate `LANGUAGE_ALIASES`; `c++→cpp` but no `cpp` in `PATTERNS`.** `test_example_extractor.py:731-743` — C++ test files silently yield nothing. *Fix:* remove the dup; add `cpp` patterns or drop the alias. `Confirmed`
- **CBB-10 — Space-form `ENV KEY VALUE` dropped; `_infer_purpose` substring-matches.** `config_extractor.py:601-611,350` — legacy ENV skipped; `"db" in "dbeaver"`. *Fix:* handle space form; token-boundary match. `Confirmed`
- **CBB-11 — Step code fences hardcoded ```python```.** `how_to_guide_builder.py:650,663,679` — wrong highlighting for non-Python guides despite `guide.language`. *Fix:* `f"```{guide.language}"`. `Confirmed`
- **★CBB-14 — Basic-mode maps best_practices onto step explanations by index.** `how_to_guide_builder.py:1098-1101` — unrelated best-practice strings attached to steps positionally. *Fix:* render as a separate list. `Confirmed`
- **★CBB-15 — `ast.unparse(node.body)` on a statement list for `setUp`.** `test_example_extractor.py:266-271` — relies on undocumented unparse-of-list behavior. *Fix:* `"\n".join(ast.unparse(s) for s in node.body)`. `Confirmed`
- **★CBB-16 — Regex `group(1)` assumption → `Test: None` for Kotlin/GDScript/C#.** `test_example_extractor.py:762-769` — alternation patterns put the name in group 2/3; `group(1)` is None, and the body-slice re-search can land inside the current body. *Fix:* `next((g for g in match.groups() if g), match.group(0))`. `Confirmed`
- **★CBB-17 — Redundant triple-fetch of `ai_analysis` with divergent null handling.** `how_to_guide_builder.py:957-961, 995, 1004-1012` — maintenance hazard. *Fix:* fetch once, reuse. `Confirmed`

## Document scrapers
- **DOC-08 — llms.txt sections with identical titles overwrite each other.** `doc_scraper.py:867-875` — same title → same URL → same `{safe_title}_{url_hash}` filename. *Corrected:* narrow (identical-title sections only), not the general case. *Fix:* add a section index/counter. `Corrected`
- **DOC-09 — Parallel/async submit guard off-by-one (`<=` vs `<`).** `doc_scraper.py:1523,1647` vs `1457` — parallel mode over-scrapes `max_pages` by ≥1. *Fix:* use `<`. `Confirmed`
- **DOC-10 — `is_valid_url` rejects the exact base page.** `doc_scraper.py:301-303` — trailing-slash `base_dir` drops the slashless base URL. *Corrected:* negligible — the start page is enqueued directly via `start_urls`. *Fix:* also accept `url == base_url`. `Corrected (negligible)`
- **DOC-11 — EPUB section images written as 0-byte files with broken links.** `epub_scraper.py:984-994` + `598-613` — `data=b""` passes the `isinstance(bytes)` check → 0-byte PNG + `![Image]` link. *Fix:* `if isinstance(...) and len(data) > 0`. `Confirmed`
- **DOC-12 — `_extract_html_as_markdown` returns `links=[]` → BFS dead-ends.** `doc_scraper.py:509-510,667-711` — a `.md` URL serving HTML contributes no further links. *Fix:* extract same-prefix links. `Confirmed`
- **DOC-13 — `_extract_tables` drops body rows equal to the header.** `html_scraper.py:868-872` (+ shared helper, confluence) — `cells != headers` drops legitimate data rows. *Fix:* skip the first row only when it came from `<thead>`. `Confirmed`
- **DOC-14 — Non-atomic checkpoint/page writes corrupt on interrupt.** `doc_scraper.py:334, 874` (the earlier-cited :771 is unrelated) — direct `open(...,'w')`; a second Ctrl-C truncates the checkpoint, and `load_checkpoint` silently starts fresh, losing progress. *Fix:* temp-file + `os.replace`. `Confirmed`
- **DOC-15 — `int(img.get("width") or 0)` crashes on `"100%"`/`"50px"`.** `html_scraper.py:911-912` (crash), `word_scraper.py:826` (silently drops image), `epub_scraper.py:991` (crash). *Fix:* parse leading digits defensively. `Confirmed`
- **★DOC-16 — Async dry-run discovered links bypass the cap.** `doc_scraper.py:1647-1664` — combined with DOC-06, async `--dry-run` issues real GETs across the whole site. *Fix:* the DOC-06 fix bounds this. `Confirmed`
- **★DOC-17 — pdf legacy image branch writes raw `img["data"]` with no guard.** `pdf_scraper.py:341-356` — `b""` → 0-byte file; missing/non-bytes → `KeyError`/`TypeError` aborts the reference-file write. *Fix:* `isinstance`/non-empty guard + `.get`. `Confirmed`
- **★DOC-18 — `smart_categorize` output is config-order-dependent.** `doc_scraper.py:1809-1846` — corollary of DOC-02; identical configs differing only in key order produce different groupings. *Fix:* same as DOC-02 (pick max, stable tiebreak). `Confirmed`

## Media / structured / remote scrapers
- **MED-05 — `VideoScraperResult.to_dict()` drops `config`.** `video_models.py:827-848` — `--from-json` reload loses clip range/languages/whisper model. *Corrected:* latent — no current reader of `result.config`. *Fix:* serialize/restore `config`. `Corrected (latent)`
- **MED-06 — `.man` files dropped when `--sections` is set.** `man_scraper.py:317-353` — section-less `.man` pages have `section_num=None`, never in the list. *Fix:* only filter when `section_num is not None`. `Confirmed`
- **MED-07 — OpenAPI `$ref` has no cycle set.** `openapi_scraper.py:775-855` — self-referential schemas expand to the depth-10 cap (bounded — no hang). *Fix:* track visited ref names; emit a stub on cycle. `Confirmed`
- **MED-08 — RSS link-following has no global time budget.** `rss_scraper.py:191-206,484-489` — serial, 15s/req + 1s sleep; ~13 min on a 50-entry feed with slow hosts. *Fix:* time budget or concurrency. `Confirmed`
- **MED-09 — Confluence pagination compares against constant `limit`.** `confluence_scraper.py:455-528` — `if len(batch) < limit` uses 50, not the requested `min(...)`. *Corrected:* sloppy but not a reachable premature-stop (outer `while` already bounds it). *Fix:* compare against the requested size. `Corrected`
- **MED-10 — OCR keyframe temp JPEGs never deleted.** `video_visual.py:702-715` — `delete=False`, never unlinked. *Corrected:* `extract_keyframes` is dead code (no production caller); the active pipeline writes intended output frames and cleans stale ones. *Fix:* delete the dead function or have it clean up. `Corrected (dead code)`
- **MED-11 — Confluence `created` only set for version-1 pages.** `confluence_scraper.py:494-498` — empty for all edited pages. *Fix:* use `history.createdDate`. `Confirmed`
- **MED-12 — `get_releases()` / file-tree walk uncapped.** `github_scraper.py:686-708, 939-968` — unlike issues' `islice`, can exhaust the rate-limit quota on large repos. *Fix:* `islice` / depth cap. `Confirmed`
- **MED-13 — `max_pages: int` assigned `float("inf")`.** `notion_scraper.py:96-98`, `confluence_scraper.py:241-243` — type-annotation lie; works only because comparisons accept inf. *Fix:* `sys.maxsize` or annotate `float`. `Confirmed`
- **MED-14 — Video AI ref cleaning accepts any response >50% of input.** `video_scraper.py:299-312` — no `stop_reason` check; a truncated (>50%) response overwrites the reference file. *Fix:* require `stop_reason == "end_turn"`. `Confirmed`
- **★MED-15 — OpenAPI external/relative `$ref` left as an unresolved stub.** `openapi_scraper.py:916-943` — only `#/`-refs resolve; multi-file bundles emit stubs with a debug-only log. *Fix:* pre-bundle, or warn + mark `_ref_unresolved`. `Confirmed`
- **★MED-16 — Discord `before = batch[-1]["id"]` `KeyError` on malformed message.** `chat_scraper.py:875` — aborts the whole fetch. *Fix:* `.get("id")` + break. `Confirmed`
- **★MED-17 — Slack `conversations_list` is single-page.** `chat_scraper.py:654-662` — no `next_cursor`; >200 channels truncated. *Fix:* paginate via `response_metadata.next_cursor`. `Confirmed`
- **★MED-18 — GitHub "all" mode `//2` quota split under-fetches.** `github_fetcher.py:289-297` — rigid open/closed split never reallocates unused quota; magnifies MED-01. *Fix:* fetch open then request `max - len(open)` closed. `Confirmed`

## Enhancement + builder
- **ENH-13 — Unknown provider → `_init_api_client` returns None, mode stays "api".** `agent_client.py:219-254` — `_call_api` then silently returns None (no fallback to LOCAL). *Fix:* `else:` raise or set `self.mode = "local"`. `Confirmed`
- **ENH-14 — `quality_metrics --threshold` parsed but never used.** `quality_metrics.py:542` — `main()` always returns 0, so quality gating is a no-op (also a 0-10 vs percentage scale mismatch). *Fix:* compare the score and return non-zero. `Confirmed`
- **ENH-15 — `prompt_file.write_text` missing `encoding="utf-8"`.** `agent_client.py:393` — `UnicodeEncodeError` on non-UTF-8 locales for emoji/CJK prompts (every read uses utf-8). *Fix:* add `encoding="utf-8"`. `Confirmed`
- **★ENH-16 — `_call_api` error classification by name substring.** `agent_client.py:317-353` — `"auth"/"rate" in type-name` misfires; a 429 whose class lacks "rate" gets a generic message. *Fix:* branch on HTTP status / typed SDK exceptions. `Confirmed (diagnostic)`
- **★ENH-17 — PDF content dropped when base SKILL.md lacks a Reference heading.** `unified_skill_builder.py:619-623, 659-663` — `insertion_index == -1` → assembled PDF lines silently discarded (no append-at-end fallback, unlike the docs+github+pdf path). *Fix:* append at end when no heading found. `Confirmed`

## Args / infra
- **INF-06 — `--skip-config` is an orphan flag.** `arguments/create.py:427-433` — dest `skip_config` read nowhere (the real flag is `--skip-config-patterns`). *Fix:* remove or alias. `Confirmed`
- **INF-07 — Azure server-side copy uses an unauthenticated source URL.** `storage/azure_storage.py:223` — `start_copy_from_url(source_blob.url)` (no SAS) → 403 on private containers (S3/GCS are fine). *Fix:* append a short-lived read SAS. `Confirmed`
- **INF-08 — `presets/` package is dead code.** `presets/manager.py`, `presets/analyze_presets.py` — imported by no command (analyze parser not registered). Latent: `resolve_enhance_level` assumes `enhance_level` defaults to `None`, but the analyze parser forces `0`, so `--enhance` would be dead if revived. *Fix:* delete, or set the default back to `None`. `Confirmed`
- **★INF-09 — `create --no-preserve-code-blocks` / `--no-preserve-paragraphs` inert.** `arguments/create.py:810-822` — registered for `create` but read nowhere in `_args_to_data`/`_build_config` (only the `package` command consumes them). *Fix:* wire into the RAG config or drop from `create`. `Confirmed`
- **★INF-10 — `create --preset/-p` consumed nowhere.** `arguments/create.py:75-82` — the only reader lives in the dead `presets` package; `--preset comprehensive` is parsed and discarded. *Fix:* wire to analysis depth/features or remove. `Confirmed`

---

# Appendix A — Investigated and dismissed / corrected severity

These were checked against the source and are **not** defects (or were materially downgraded). Recorded for coverage.

- **C6 → DOC-01 (pdf `next(iter(...))` StopIteration).** *Downgraded Critical → Low (not in body).* The `elif self.categories:` guard means a plain dict is non-empty there, so `next(iter(values()))` cannot raise; it is only a defensive inconsistency vs the siblings (which pass `, None`). Low-priority robustness fix: add the `, None` default at `pdf_scraper.py:192`.
- **CLI `_validate_arguments` false "not applicable" warnings — FALSE POSITIVE.** `create_command.py:111-136`. Verified every argument dict key equals its argparse dest, so the compatible-set membership check aligns; warnings only fire for genuinely-incompatible args.
- **CBA GDScript `class_name` line via `.count("\n")` — FALSE POSITIVE (correctness).** `code_analyzer.py:1988`. Produces the identical line number as `_offset_to_line`; only a style/perf nit.
- **CBB JS/TS config extraction duplicate settings — FALSE POSITIVE.** `config_extractor.py:584-586`. The three regexes are mutually exclusive per declaration; tested, no duplicate emissions. (A separate `version = 1.5` → `1` truncation defect exists but was not the claim.)
- **DOC PDF chapter-boundary chunk inverts start/end — FALSE POSITIVE.** `pdf_extractor_poc.py:660-669`. The non-empty-`current_chunk` guard guarantees `end_page ≥ start_page`.
- **ENH `enhance --model` dropped — CORRECTED (dead path).** `enhance_skill_local.py:1312-1340` does drop `--model`, but it's an unreachable legacy `main()`; the shipped `enhance` command routes through `enhance_command.py`, which forwards `--model` correctly to `enhance_skill.py` (which accepts it).
- **Scan archive/diff ordering & `set_api_key` display name — FALSE POSITIVE.** `scan_command.py:1137-1143` ordering is correct by design; `config_manager.py` `capitalize()` is display-only (the real defect is the env_map omission, SCAN-03).

---

# Appendix B — Systemic patterns

Cross-cutting root causes worth fixing once rather than per-site:

- **S1 — Truncated/empty LLM output accepted as complete.** No `stop_reason`/`finish_reason` check: ENH-01 (`enhance_skill`/`agent_client`), ENH-11 (Gemini), MED-14 (video), ADP-06 (rename-before-write). Add a single "complete and non-empty?" gate before any overwrite, and always write-temp-then-swap.
- **S2 — SKILL.md nav links derived differently from reference filenames.** DOC-07 (pdf/html/word/epub) + MED-04 (jupyter/asciidoc/pptx): 7 scrapers link to `sanitize(title).md` while files use range/basename names. Extract one `_ref_filename()` helper per scraper and use it for both writing and nav. (★MED-N5: PPTX duplicates the naming logic in 3 places.)
- **S3 — Success/failure inferred from emoji/text substrings.** MCP-05 (`"❌"`), MCP-09/★MCP-15 (enhance/package), ENH-04 (Kimi regex). Return structured status/returncodes; never scan stdout for `❌`.
- **S4 — `A or B and C` precedence bugs.** CBA-01, CBA-05, CBA-06, CBB-06. Audit every multi-clause boolean for missing parentheses.
- **S5 — Shared-mutable-list aliasing.** CBB-03 (`common_problems.remove`), CBB-12 (`dependencies=imports`). Copy lists at construction (`list(...)`).
- **S6 — Pagination / `max_pages` inconsistency.** MED-01/★MED-18 (github), MED-02/★MED-17 (slack), MED-03/★MED-16 (discord), MED-09 (confluence), DOC-04/DOC-09 (doc_scraper), MED-13 (`inf`-as-`int`). Standardize a cursor-following helper with explicit caps.
- **S7 — Negative→positive flag translation gaps & inert flags.** CLI-01 (`--no-*`), INF-06/INF-09/INF-10 (`--skip-config`, `--no-preserve-*`, `--preset`). Add a registration test asserting every declared arg's dest is read somewhere.
- **S8 — Library modules calling `logging.basicConfig`.** SCAN-06, ★CLI-09. Only the entry point should configure logging.
- **S9 — Provider/model/timeout plumbing not threaded to the SDK call.** ENH-02, ENH-06, ENH-11, ENH-12. Centralize provider detection and request-option passing in one place.

---

# Suggested fix order

1. **S1 + ENH-01** (silent data loss of the primary artifact) — highest blast radius, low risk.
2. **SCAN-01, CBB-01, MCP-01(+★MCP-12/13/14), CBA-13** (core features silently broken) — small, surgical fixes.
3. **CLI-01, CLI-02(+★CLI-07), SCAN-02** (user-visible flag/crash bugs on the main `create`/`scan` paths).
4. **S3 + S6** (MCP install/upload reliability; scraper pagination correctness).
5. **CBA-01..04 + ★CBA-13..16** (pattern/dependency-analysis correctness — many share the precedence/regex root causes in S4).
6. Medium/Low by subsystem as code is touched.
