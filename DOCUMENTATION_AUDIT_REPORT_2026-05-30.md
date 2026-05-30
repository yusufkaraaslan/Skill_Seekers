# Skill Seekers Documentation Audit Report
**Date:** 2026-05-30  
**Project Version:** 3.6.0 (from `pyproject.toml`)  
**Auditor:** Agent Swarm Analysis  
**Scope:** All non-generated `.md` files (excludes `output/`, `.skillseeker-cache/`, virtualenvs)

---

## Executive Summary

The Skill Seekers project has **~163 non-generated markdown files** across the repository. While the codebase is actively maintained at **v3.6.0**, the documentation ecosystem suffers from **severe version drift**, **widespread stale CLI references**, **broken internal links**, **incomplete translations**, **near-duplicate files**, and **significant gaps between claimed and actual features**.

### Severity Distribution
| Severity | Count | Description |
|----------|-------|-------------|
| **CRITICAL** | 45+ | Wrong commands, broken links, missing sections, incorrect versions |
| **WARNING** | 60+ | Stale counts, truncated content, minor inaccuracies, deprecated paths |
| **INFO** | 35+ | Missing features from docs, structural suggestions, cosmetic issues |

### Key Finding
> **The English README.md itself is outdated (claims v3.5.0, shows 14 removed CLI subcommands, has 11 broken internal links), and ALL 11 translations lag even further behind (claiming v3.2.0). The documentation as a whole gives new users a systematically incorrect understanding of how to use the tool.**

---

## 1. Version Consistency Crisis

Version numbers are **completely inconsistent** across the documentation ecosystem:

| Location | Claims | Actual | Status |
|----------|--------|--------|--------|
| `pyproject.toml` | — | **3.6.0** | ✅ Source of truth |
| `AGENTS.md` | 3.6.0 | 3.6.0 | ✅ Correct |
| `README.md` (English) | 3.5.0 | 3.6.0 | ❌ Stale |
| **All 11 README translations** | 3.2.0 | 3.6.0 | ❌ **Very stale** |
| `docs/README.md` | 3.2.0 | 3.6.0 | ❌ Stale |
| `docs/getting-started/*.md` | 3.1.0–3.2.0 | 3.6.0 | ❌ Stale |
| `docs/user-guide/*.md` | 3.1.0–3.2.0 | 3.6.0 | ❌ Stale |
| `docs/guides/MCP_SETUP.md` | 2.4.0 | 3.6.0 | ❌ Very stale |
| `docs/reference/MCP_REFERENCE.md` | 3.5.0 | 3.6.0 | ❌ Slightly stale |
| `docs/advanced/mcp-server.md` | 3.2.0 | 3.6.0 | ❌ Stale |
| `ROADMAP.md` | 3.2.0 | 3.6.0 | ❌ Stale |
| `QWEN.md` | 3.3.0 | 3.6.0 | ❌ Stale |
| `integrations/INTEGRATIONS.md` | 2.10.0+ | 3.6.0 | ❌ Very stale |
| `api/configs_repo/STATUS.md` | 2.11.0+ | 3.6.0 | ❌ Very stale |

**Impact:** New users cannot determine which version of the tool they are reading documentation for. Features documented at v3.1.0 may have changed significantly by v3.6.0.

---

## 2. README.md (English) — Deep Analysis

### 2.1 CRITICAL Issues

#### A. Broken / Outdated Internal Links (11 links)
| Link in README | Actual Location | Status |
|---|---|---|
| `ASYNC_SUPPORT.md` | **Does not exist anywhere** | ❌ Dead |
| `docs/ENHANCEMENT_MODES.md` | `docs/features/ENHANCEMENT_MODES.md` | ❌ Wrong path |
| `docs/FEATURE_MATRIX.md` | `docs/reference/FEATURE_MATRIX.md` | ❌ Wrong path |
| `docs/GIT_CONFIG_SOURCES.md` | `docs/reference/GIT_CONFIG_SOURCES.md` | ❌ Wrong path |
| `docs/HOW_TO_GUIDES.md#ai-enhancement-new` | `docs/features/HOW_TO_GUIDES.md` | ❌ Wrong path |
| `docs/IMPLEMENTATION_SUMMARY_THREE_STREAM.md` | `docs/archive/historical/IMPLEMENTATION_SUMMARY_THREE_STREAM.md` | ❌ Wrong path |
| `docs/LARGE_DOCUMENTATION.md` | `docs/reference/LARGE_DOCUMENTATION.md` | ❌ Wrong path |
| `docs/MCP_SETUP.md` | `docs/guides/MCP_SETUP.md` | ❌ Wrong path |
| `docs/QUICK_REFERENCE.md` | `docs/archive/legacy/QUICK_REFERENCE.md` | ❌ Wrong path |
| `docs/UNIFIED_SCRAPING.md` | `docs/features/UNIFIED_SCRAPING.md` | ❌ Wrong path |
| `QUICKSTART.md` | `docs/archive/legacy/QUICKSTART.md` | ❌ Wrong path |

#### B. Non-Existent CLI Subcommands (14 removed commands still shown)
The README displays **legacy subcommands that were removed** in the unified CLI redesign:

| Invalid Command Shown | Correct Modern Command |
|---|---|
| `skill-seekers scrape --config ...` | `skill-seekers create --config ...` |
| `skill-seekers scrape --url ...` | `skill-seekers create https://...` |
| `skill-seekers video --url ...` | `skill-seekers create ... --video-url ...` |
| `skill-seekers video --setup` | `skill-seekers create --setup` |
| `skill-seekers pdf --pdf ...` | `skill-seekers create ... --pdf ...` |
| `skill-seekers github --repo ...` | `skill-seekers create ...` (auto-detect) |
| `skill-seekers unified --config ...` | `skill-seekers create configs/..._unified.json` |
| `skill-seekers confluence --space ...` | `skill-seekers create ... --space-key ...` |
| `skill-seekers notion --database-id ...` | `skill-seekers create ... --database-id ...` |
| `skill-seekers chat --export-dir ...` | `skill-seekers create ... --chat-export-path ...` |
| `skill-seekers list-configs` | **Does not exist** |
| `skill-seekers analyze --directory ...` | **Does not exist** |

#### C. Wrong CLI Flags in Examples
- `skill-seekers video --url ...` → should use `--video-url`
- `skill-seekers video --playlist ...` → should use `--video-playlist`
- `skill-seekers confluence --space TEAM` → should use `--space-key`
- `skill-seekers chat --export-dir ./slack-export` → should use `--chat-export-path`
- `skill-seekers package ... --format chroma/faiss/qdrant` → should use `--target`

#### D. Inconsistent Test Counts
- Badge: `3194+ Passing`
- "Quality Assurance" prose: `2,540+ tests`
- Actual codebase: ~3,462 test functions
- **Three different numbers cited in different places**

#### E. Missing Major Features
The README **omits** these significant v3.x features:
- `--preset` (`quick` / `standard` / `comprehensive`)
- `--dry-run`, `--fresh`, `--resume`, `--skip-scrape`
- `--chunk-for-rag`, `--chunk-tokens`, `--chunk-overlap-tokens`
- `--streaming`, `--marketplace`, `--marketplace-category`
- `skill-seekers doctor` (health check)
- `skill-seekers sync-config` (config drift detection)
- `skill-seekers stream` (streaming ingestion)
- `skill-seekers update` (incremental updater)
- `skill-seekers multilang` (multi-language support)
- `skill-seekers quality` (quality scoring)
- `skill-seekers extract-test-examples`

### 2.2 WARNING Issues
- MCP tool count: README says 26, AGENTS.md says 40, actual is 40
- LLM platform comparison table shows only 5 of ~21 supported platforms
- Install-agent names: README says `Kimi` but CLI uses `kimi-code`
- `--target claude` description misleadingly claims auto-copy for Cursor/Windsurf

---

## 3. Translation Analysis (All 11 READMEs)

### 3.1 Summary Table

| Translation | Headings | Version | Test Badge | Architecture Section | Scan Section | IBM Bob | MiniMax | Status |
|-------------|----------|---------|------------|----------------------|--------------|---------|---------|--------|
| English | 210 | 3.5.0 | 3194+ | ✅ | ✅ | ✅ | ✅ | ⚠️ Stale |
| **zh-CN** | 165 | **3.2.0** | **2540+** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | 🔴 Very stale |
| **ja** | 165 | **3.2.0** | **2540+** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | 🔴 Very stale |
| **ko** | 166 | **3.2.0** | **2540+** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | 🔴 Very stale |
| **de** | 166 | **3.2.0** | **2540+** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | 🔴 Very stale |
| **es** | 195 | **3.2.0** | **2540+** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | 🔴 Very stale |
| **fr** | 196 | **3.2.0** | **2540+** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | 🔴 Very stale |
| **pt-BR** | 195 | **3.2.0** | **2540+** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | 🔴 Very stale |
| **ru** | 166 | **3.2.0** | **2540+** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | 🔴 Very stale |
| **tr** | 195 | **3.2.0** | **2540+** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | 🔴 Very stale |
| **ar** | 166 | **3.2.0** | **2540+** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | 🔴 Very stale |
| **hi** | 195 | **3.2.0** | **2540+** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | 🔴 Very stale |

### 3.2 Universal Translation Deficiencies
**Every single translation** is missing these major sections that exist in English:
- `## 📚 Documentation` (early quick-link table)
- `## Architecture` (module overview + UML links)
- `### 🛰️ AI-driven project scan (new)`
- `### 🤖 Agent-Agnostic Skill Generation`
- `### 📦 Marketplace Pipeline`
- `IBM Bob` support (agent count says 18 instead of 19)
- `MiniMax AI` platform comparison row and examples
- `pepy.tech` and `Trendshift` badges

### 3.3 Per-Translation Nuances
- **zh-CN, ja, ko** (CJK): Most severely truncated. Installation table has 13 rows vs English 15. Performance table missing Video rows. Smart Rate Limit Management heavily truncated.
- **ko** is the *best* CJK translation: includes Security section at bottom, has correct 15-row install table, includes Video performance rows.
- **fr, tr** (European): Include the early Documentation table (most others don't). Otherwise similar gaps.
- **hi** (Devanagari): Most complete non-European translation. Has all 5 print statements in Three-Stream example. Bootstrap "What you get" bullets present. Good technical transliteration.
- **ar** (Arabic): Most truncated. Three-Stream example has only 2 print statements. Missing Rate Limit Strategies Explained. Some bidi rendering issues in code comments.
- **ru** (Cyrillic): Has some untranslated English fragments ("OpenAPI/Swagger", "README"). Uses Latin "API"/"LOCAL" inconsistently.

---

## 4. Core Project Documentation

### 4.1 AGENTS.md — ✅ MOSTLY ACCURATE
- Version 3.6.0 ✅
- Source types count (17 + config) ✅
- 40 MCP tools ✅
- Minor: Claims "~14 legacy commands" but actual is 16

### 4.2 CLAUDE.md — ✅ ACCURATE
- Architecture descriptions match codebase
- File paths correct
- 24 adaptor files match actual
- Minor: Uses `uvx ruff` while AGENTS.md uses `ruff`

### 4.3 CHANGELOG.md — ✅ ACCURATE
- Latest version [3.6.0] correctly listed
- `[Unreleased]` section holds post-3.6.0 changes appropriately
- Format consistent

### 4.4 ROADMAP.md — 🔴 SEVERELY OUTDATED
- Claims `v3.2.0` is current (actual: 3.6.0)
- Lists `v2.7.0`, `v2.8.0`, `v2.9.0` as future releases
- **Completed tasks NOT checked off**:
  - A1.3 `submit_config` MCP tool — EXISTS
  - C3.3 "Build how-to guides" — `how_to_guide_builder.py` EXISTS
  - C3.4 "Extract configuration patterns" — `config_extractor.py` EXISTS
  - C3.5 "Create architectural overview" — `generate_router.py` EXISTS
  - E1.1 `fetch_config` MCP tool — EXISTS
- Wrong metrics: "1,880+ tests" (actual: ~3,445), "24 preset configs" (actual: 12), "5 bundled workflows" (actual: 68 YAML files)

### 4.5 TROUBLESHOOTING.md — 🔴 BROKEN PATHS
- Uses **pre-`src/` layout paths** that no longer exist:
  - `cli/doc_scraper.py` (×3)
  - `python3 mcp/server.py` (×2)
  - `pip3 install -r mcp/requirements.txt` — file does not exist
- **Missing critical step**: Never mentions `pip install -e .` which `conftest.py` hard-requires

### 4.6 CONTRIBUTING.md — 🔴 WRONG SETUP
- Tells contributors: `pip install requests beautifulsoup4` and `pip install -r mcp/requirements.txt`
- **Should say**: `pip install -e .` / `pip install -e ".[dev]"` (as AGENTS.md states)
- Coverage paths wrong: `--cov=cli --cov=mcp` should be `--cov=src/skill_seekers`
- **Contradicts AGENTS.md**: Describes pre-commit hook setup, but AGENTS.md says "**No pre-commit hooks, no Makefile**"
- Branch naming: uses `feature/my-awesome-feature` without task ID; AGENTS.md specifies `feature/{task-id}-{description}`

### 4.7 QWEN.md — 🔴 REDUNDANT & OUTDATED
- Version says `v3.3.0` (actual: 3.6.0)
- Claims 26+ MCP tools (actual: 40)
- Shows `skill-seekers package --target langchain` — `langchain` is a `--format` value, not `--target`
- Shows `--target cursor` — not a valid standalone `--target`
- **Omits `scan` and `doctor` entirely**
- Stale numbers: 67 YAML presets (actual: 68), 123 test files (actual: 143)
- **Recommendation**: Update to 3.6.0 or remove (largely duplicates CLAUDE.md/AGENTS.md)

---

## 5. docs/ Directory Analysis

### 5.1 Structural Issues

#### A. docs/README.md Omits ~40% of Actual Content
The docs hub README lists only a subset of directories. It **omits**:
- `guides/` (7 files)
- `integrations/` (15 files)
- `features/` (5 files)
- `archive/`, `blog/`, `case-studies/`, `plans/`, `roadmap/`, `strategy/`, `agents/`, `superpowers/`
- `zh-CN/` (entire translation tree)
- `UML/`

#### B. Phantom Link
`docs/README.md` links to `advanced/mcp-tools.md` — **does not exist**. Only `advanced/mcp-server.md` exists.

### 5.2 Near-Duplicate File Pairs

**Pair 1:** `DOCKER_GUIDE.md` (575 lines) ↔ `DOCKER_DEPLOYMENT.md` (762 lines)
- Both cover Docker deployment, Compose, volumes, networking, monitoring, troubleshooting
- `DOCKER_DEPLOYMENT.md` is more detailed (adds embedding server, sync monitor, Prometheus/Grafana/Loki)
- `DOCKER_GUIDE.md` has broken link: `[Vector Database Integration](docs/strategy/WEEK2_COMPLETE.md)` — `WEEK2_COMPLETE.md` does not exist
- **Recommendation**: Merge into single file

**Pair 2:** `KUBERNETES_GUIDE.md` (957 lines) ↔ `KUBERNETES_DEPLOYMENT.md` (933 lines)
- Both cover Helm charts, manual deployment, scaling, HA, monitoring, security
- `KUBERNETES_DEPLOYMENT.md` adds Velero backup/restore, cost optimization
- `KUBERNETES_GUIDE.md` uses `skillseekers` namespace; `KUBERNETES_DEPLOYMENT.md` uses `skill-seekers`
- **Recommendation**: Merge into single file

### 5.3 Partial Duplication: Troubleshooting
- `user-guide/06-troubleshooting.md` (~200 lines, v3.1.0)
- Top-level `TROUBLESHOOTING.md` (1094 lines, no version stamp)
- **Significant overlap** in installation, configuration, scraping, enhancement sections
- **Recommendation**: Consolidate or clearly differentiate scope

### 5.4 Stale MCP Documentation
Three different MCP docs claim three different tool counts:

| File | Claims | Actual |
|------|--------|--------|
| `guides/MCP_SETUP.md` | 26 tools / v2.4.0 | 40 tools / v3.6.0 |
| `advanced/mcp-server.md` | 27 tools / v3.2.0 | 40 tools / v3.6.0 |
| `reference/MCP_REFERENCE.md` | 40 tools / v3.5.0 | 40 tools / v3.6.0 |

`guides/MCP_SETUP.md` also claims MCP SDK v1.25.0 and miscounts tool categories (says 27 but lists 28).

### 5.5 Stale Guide Content
- `guides/MIGRATION_GUIDE.md` header says `v3.1.0-dev` but discusses migrating **to v2.7.0** as "latest"
- `integrations/INTEGRATIONS.md` says "Skill Seekers Version: v2.10.0+"
- `integrations/LANGCHAIN.md` says "Skill Seekers Version: v2.9.0+"
- `features/BOOTSTRAP_SKILL.md` says version 2.7.0 in frontmatter example

### 5.6 FEATURE_MATRIX Undercount
Lists only 12 platforms but CLI supports 21+ packaging targets. Missing: DeepSeek, Qwen, OpenRouter, Together, Fireworks, IBM Bob, OpenCode, Kimi, and others.

---

## 6. docs/zh-CN/ Translation Quality — 🔴 CRITICAL FINDING

### 6.1 The Shocking Truth
**The `docs/zh-CN/` directory does NOT contain Chinese translations.**

Out of **21 files audited**:
- **0 files (0%)** are fully translated to Chinese
- **1 file (~15%)** has partial Chinese (`advanced/mcp-server.md` — just section headers and some tool descriptions)
- **20 files (95%)** are **English copies** with minor divergence

### 6.2 Content Drift Pattern
The zh-CN files fall into three categories:

| Category | Files | Description |
|----------|-------|-------------|
| **zh-CN LAGS** | README, CLI_REFERENCE, API_REFERENCE, packaging | English docs are newer (v3.5.0 vs v3.2.0) |
| **zh-CN LEADS** | ARCHITECTURE, core-concepts, scraping, CONFIG_FORMAT, workflows, MCP_REFERENCE, multi-source | zh-CN documents features not yet in English docs (17 sources, unified config, new platforms) |
| **Identical** | 03-your-first-skill, 06-troubleshooting, SKILL_ARCHITECTURE, custom-workflows | Perfect copies |

### 6.3 Broken Link
- `zh-CN/getting-started/04-next-steps.md` links to `05-scan-a-project.md` — **does not exist in zh-CN/** (only in `docs/getting-started/`)

### 6.4 Recommendation
If the goal is Chinese-language documentation: **entire directory needs professional translation**.  
If the goal is parallel English documentation: **rename directory** (e.g., `docs/extended/`) to avoid misleading users.

---

## 7. Archive, Plans, Strategy & Roadmap Relevance

### 7.1 docs/archive/ — Mostly Appropriate

**Historical (8 files):** All are completed verification reports. Correctly archived. Could compress further.  
**Legacy (4 files + index):** Self-aware deprecated docs with redirects. Correctly archived.  
**Plans (2 files):** Active skills design from Oct 2025. Status unclear — **verify if implemented**.  
**Research (4 files):** PDF research from Oct 2025. Informed current implementation. Keep as historical record.

### 7.2 docs/plans/video/ — 🔴 MISLEADING
All 8 files still say "Status: Planning" but **video support IS implemented** (`video_scraper.py`, `video_models.py`, `video_setup.py`, 60 tests).  
**Action:** Update headers to "Implemented" and verify code alignment. Consider moving to `docs/features/`.

### 7.3 docs/strategy/ — Mixed

| File | Verdict |
|------|---------|
| `README.md` | Update — integration guides WERE created (18 files) but doc still says "to be created" |
| `ACTION_PLAN.md` | Archive — historical 4-week plan, partially executed |
| `ARBITRARY_LIMITS_AND_DEAD_CODE_PLAN.md` | Update — Stage 1 completed, Stages 2-3 status unknown |
| `INTEGRATION_STRATEGY.md` | Update — much executed, should reflect success |
| `KIMI_ANALYSIS_COMPARISON.md` | Archive — analysis complete, strategy adopted |
| `STAGE_1_*.md` (3 files) | Archive deeper — historical implementation records |
| `DEEPWIKI_ANALYSIS.md`, `INTEGRATION_TEMPLATES.md` | Keep — still valuable |

### 7.4 docs/roadmap/ — ✅ APPROPRIATE (Future Design)
Intelligence System roadmap (4 files, Jan 2026). No `skill_seekers/intelligence/` package exists yet. These are **future design docs** — correctly kept as research/planning.

### 7.5 docs/agents/ — Archive
EPUB implementation plans (Mar 2026). EPUB scraper EXISTS and is tested (107 tests). These are completed agent-driven development records — **archive deeper**.

### 7.6 docs/superpowers/ — Verify
Scrape-count and SPA detection plan (Mar 2026). References `doc_scraper.py` line numbers. **Verify if implemented** and update status.

---

## 8. Distribution & Examples

### 8.1 distribution/ — 🔴 BROKEN EXAMPLES

#### github-action/README.md
- Lists CLI commands: `scrape`, `github`, `pdf`, `video`, `analyze`, `unified`
- **None exist in v3.6.0**
- Users copying these workflow examples will get `error: argument command: invalid choice`

#### claude-plugin/commands/install-skill.md
- Lists targets: `cursor`, `windsurf`, `continue`, `cline`
- **Not registered adaptors** — will fail

#### claude-plugin/README.md & skills/skill-builder/SKILL.md
- Claims "35 MCP tools" — actual is **40**

### 8.2 examples/ — 🔴 ALL EXAMPLES USE REMOVED COMMANDS

**Every example README** (chroma, cline, continue-dev, cursor, haystack, langchain, llama-index, pinecone, weaviate, windsurf) references:
- `skill-seekers scrape --config ...` → should be `skill-seekers create --config ...`
- `skill-seekers github --repo ...` → should be `skill-seekers create ...`

#### windsurf-fastapi-context/
- References `--split-rules` and `--max-chars` flags on `skill-seekers package`
- **These flags do not exist**

#### Other Example Issues
- Many reference `skill-seekers v2.10.0` — current is 3.6.0
- `cursor-react-skill/README.md`: Uses `--target claude` for Cursor. Cursor uses `.cursorrules` (plain markdown); `--target markdown` would be more appropriate
- `continue-dev-universal/README.md`: References `~/.continue/config.json` for HTTP context providers. Continue.dev has shifted toward YAML config and MCP servers

### 8.3 api/configs_repo/ — 🔴 SEVERELY STALE

#### STATUS.md
- "Last Updated: 2024-12-21"
- "Total Configs: 90 unified format"
- "Format Version: Unified (v2.11.0+)"
- Actual: v3.6.0, submodule shows 22+ official categories

#### Divergence Between Copies
- `api/configs_repo/README.md`: Claims **178 configs / 21 categories / v3.1.0+**
- `skill-seekers-configs/README.md` (root copy): Claims **24 configs / 7 categories**
- **These wildly diverge**

#### CONTRIBUTING.md (configs_repo)
- References `skill-seekers scrape --config` — command removed

### 8.4 skill-seekers-configs/ — 🔴 COUNTS DON'T ADD UP

All TODO files claim `✅ COMPLETE` but counts are contradictory:

| File | Claims | Actually Lists |
|------|--------|----------------|
| `TODO-ai-ml.md` | 40 configs | 34 items |
| `TODO-build-tools.md` | 9 configs | ~15 items |
| `TODO-cloud.md` | 10 configs | ~15 items |
| `TODO-databases.md` | 9 configs | ~20 items |
| `TODO-development-tools.md` | 6 configs | ~12 items |
| `TODO-devops.md` | 7 configs | ~12 items |
| `TODO-game-engines.md` | 7 configs | ~20 items |
| `TODO-testing.md` | 4 configs | ~10 items |
| `TODO-web-frameworks.md` | 12 configs | ~18 items |

---

## 9. Tests, Scripts, Skills, src docs

### 9.1 tests/mcp_integration_test.md — 🔴 BROKEN PATHS
- `python3 mcp/server.py` → should be `python -m skill_seekers.mcp.server_fastmcp`
- `pip3 install -r mcp/requirements.txt` → file doesn't exist
- `python3 cli/doc_scraper.py`, `python3 cli/package_skill.py` → pre-`src/` layout

### 9.2 scripts/skill_header.md — 🔴 DEPRECATED FLAGS
- References `--depth surface/deep/full` → **deprecated** (use `--preset`)
- References `--ai-mode none/api/local` → **does not exist** in current CLI

### 9.3 skills/skill-seekers/SKILL.md — ⚠️ STALE COUNT
- Claims **35 MCP tools** — actual is **40**
- Otherwise well-structured

### 9.4 src/skill_seekers/mcp/README.md — 🔴 INCONSISTENT & BROKEN LINKS
- Header says "34 tools", later says "40 tools" — inconsistent
- References `docs/MCP_SETUP.md`, `docs/USAGE.md`, `docs/TESTING.md` — **none exist**
- References `cli/doc_scraper.py`, `cli/estimate_pages.py`, `cli/package_skill.py` — pre-`src/` layout
- Claims "34 tests | Pass rate: 100%" and "25 tests" in different sections

---

## 10. Missing Documentation

These features exist in the codebase but are **under-documented or undocumented** in user-facing docs:

| Feature | Code Evidence | Doc Status |
|---------|---------------|------------|
| `doctor` command | `doctor_command.py` | Not mentioned in README, getting-started, or user-guide |
| `--preset` flag | Major UX feature in `create` | Mentioned in CLI_REFERENCE but not in README or getting-started |
| `--dry-run`, `--fresh`, `--resume` | Lifecycle management | Undocumented in user guides |
| `--chunk-for-rag`, `--chunk-tokens` | RAG chunking on `package` | Undocumented in packaging guides |
| `--streaming` | Memory-efficient packaging | Undocumented |
| `--marketplace`, `--marketplace-category` | Marketplace publishing | Undocumented |
| `scan` command deep guide | `scan_command.py` | Brief mention only; no deep guide |
| `video` source type deep guide | 7 `video_*.py` files | Mentioned but not deeply documented |
| `epub` source type | `epub_scraper.py` (107 tests) | Unclear coverage in user guides |
| `browser` extra dependency | Playwright for SPA sites | Not in installation table |
| `embedding` extra | Embedding server support | Not in installation table |
| Cloud extras (`s3`, `gcs`, `azure`) | Cloud storage upload | Not in installation table |
| All 68 YAML workflow presets | `workflows/` directory | Only mentioned as "67" or "68" |

---

## 11. Unneeded / Redundant Documentation

| File(s) | Issue | Recommendation |
|---------|-------|----------------|
| `DOCKER_GUIDE.md` + `DOCKER_DEPLOYMENT.md` | Near-duplicates | Merge into one |
| `KUBERNETES_GUIDE.md` + `KUBERNETES_DEPLOYMENT.md` | Near-duplicates | Merge into one |
| `user-guide/06-troubleshooting.md` + `TROUBLESHOOTING.md` | Heavy overlap | Consolidate or differentiate scope |
| `QWEN.md` | Duplicates CLAUDE.md/AGENTS.md, less accurate | Update or remove |
| `docs/archive/historical/*` (8 files) | Historical artifacts | Compress or move to external wiki |
| `docs/strategy/STAGE_1_*.md` (3 files) | Implementation records | Merge into one summary |
| `docs/agents/*` (2 files) | Completed EPUB plans | Archive deeper |
| `skill-seekers-configs/README.md` (root copy) | Wildly diverges from submodule | Remove or sync with `api/configs_repo/` |

---

## 12. Recommendations (Prioritized)

### P0 — Critical (Fix Immediately)
1. **Update English README.md** to v3.6.0 and remove all 14 legacy CLI subcommand examples
2. **Fix all 11 broken internal links** in README.md
3. **Update or remove ALL 11 README translations** — they are 4 minor versions behind and missing major sections
4. **Update ALL example READMEs** to use `skill-seekers create` instead of removed `scrape`/`github`/`video`/`pdf`/`unified` commands
5. **Fix `distribution/github-action/README.md`** to use valid CLI commands
6. **Update `ROADMAP.md`** version header, check off completed tasks, remove obsolete v2.x release planning
7. **Rewrite `TROUBLESHOOTING.md`** for `src/` layout and modern CLI paths
8. **Fix `CONTRIBUTING.md`** setup instructions to match AGENTS.md (`pip install -e .`)

### P1 — High (Fix Soon)
9. **Unify version stamps** to 3.6.0 across all docs (or automate via CI build step)
10. **Consolidate Docker and K8s duplicate files**
11. **Update MCP tool counts** to consistently say **40** across all docs
12. **Update `guides/MCP_SETUP.md`** to match current v3.6.0 reality
13. **Update `integrations/INTEGRATIONS.md`** from v2.10.0+ to v3.6.0
14. **Fix `tests/mcp_integration_test.md`** paths to `server_fastmcp.py`
15. **Fix `src/skill_seekers/mcp/README.md`** broken links and inconsistent counts
16. **Update `FEATURE_MATRIX.md`** to include all 21+ packaging targets
17. **Update `scripts/skill_header.md`** to remove deprecated `--depth` and non-existent `--ai-mode`
18. **Sync or remove `skill-seekers-configs/README.md`** (root copy)

### P2 — Medium (Quality Improvements)
19. **Update `docs/README.md`** to reflect actual directory structure (add missing directories)
20. **Update `docs/plans/video/*.md`** from "Planning" to "Implemented"
21. **Update `docs/strategy/README.md`** and `INTEGRATION_STRATEGY.md` to show executed deliverables
22. **Add missing features to README**: `--preset`, `--dry-run`, `doctor`, `sync-config`, `stream`, `update`, `multilang`, `quality`
23. **Add missing optional deps** to installation table: `browser`, `embedding`, `s3`, `gcs`, `azure`, `rag-upload`
24. **Add `scan` and `doctor` deep guides** to getting-started or user-guide
25. **Update `guides/MIGRATION_GUIDE.md`** to discuss actual v3.5→v3.6 migration

### P3 — Low (Nice to Have)
26. **Automate version stamping** in CI to prevent future drift
27. **Archive completed agent plans** (EPUB, scrape-count) deeper or compress
28. **Add documentation update checklist** to `.github/PULL_REQUEST_TEMPLATE.md`
29. **Regenerate UML diagrams** to reflect scan feature and other recent changes
30. **Consider professional translation** of `docs/zh-CN/` or rename to `docs/extended/` if not actually Chinese

---

## Appendix: Files Audited by Area

| Area | Files Count | Key Finding |
|------|-------------|-------------|
| Root READMEs | 12 | All translations 4 versions behind |
| Core docs | 7 | ROADMAP, TROUBLESHOOTING, CONTRIBUTING severely outdated |
| docs/ main | ~86 | Version inconsistency, duplicate files, missing structure |
| docs/zh-CN/ | 21 | **0% actually translated to Chinese** |
| docs/archive/ | 18 | Appropriately archived, some could compress deeper |
| docs/plans/video/ | 8 | Misleadingly labeled "Planning" — already implemented |
| docs/strategy/ | 11 | Partially executed, needs update |
| docs/roadmap/ | 4 | Future design docs — appropriately kept |
| docs/integrations/ | 18 | Successfully created strategy deliverables |
| distribution/ | 6 | GitHub Action uses removed commands |
| examples/ | 13 | ALL use removed CLI commands |
| api/configs_repo/ | 6 | STATUS.md severely stale |
| skill-seekers-configs/ | 13 | Counts don't add up |
| .github/ | 5 | Templates functional but could reference `doctor` |
| tests/ | 1 | Broken paths to old MCP server |
| scripts/ | 1 | Deprecated flags |
| skills/ | 1 | Stale MCP tool count |
| src/ | 1 | Broken links, inconsistent counts |

---

*End of Report*
