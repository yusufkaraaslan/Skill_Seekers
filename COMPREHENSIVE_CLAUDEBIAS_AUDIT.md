# Comprehensive Claude/Anthropic Bias Audit Report

**Date:** 2026-03-31  
**Scope:** Full codebase audit for Claude/Anthropic hardcoded references  
**Objective:** Identify every location where Claude is hardcoded so we can make everything work with all agents/platforms

---

## Executive Summary

Found **extensive** hardcoded references to Claude, Anthropic, and Claude Code CLI across **50+ files**. While many are documentation/comments, **critical functional biases** exist in:

1. **Default values** - "claude" is the default for most platform choices
2. **Model names** - 9+ locations with hardcoded `claude-sonnet-4-20250514`
3. **Subprocess calls** - Direct `claude` CLI invocations in 6+ files
4. **API client usage** - Direct `anthropic` library imports in 8+ files
5. **Help text** - 15+ files mention "ANTHROPIC_API_KEY" and "Claude Code"
6. **Environment variables** - Hardcoded `ANTHROPIC_API_KEY` checks

---

## Category 1: HARD SUBPROCESS CALLS (Critical - Must Fix)

These spawn the `claude` CLI directly and will fail if Claude Code is not installed:

| File | Line(s) | Command | Purpose |
|------|---------|---------|---------|
| `cli/ai_enhancer.py` | 128-129, 197-198 | `["claude", "--version"]`, `subprocess.run(["claude", "--dangerously-skip-permissions", ...])` | Check CLI, run enhancement |
| `cli/config_enhancer.py` | 392-393 | `subprocess.run(["claude", "--dangerously-skip-permissions", ...])` | Config enhancement |
| `cli/guide_enhancer.py` | 150-151, 392-393 | `subprocess.run(["claude", prompt_file])` | Guide enhancement |
| `cli/unified_enhancer.py` | 134-135, 305-307 | `subprocess.run(["claude", "--version"])`, `subprocess.Popen(["claude", "--dangerously-skip-permissions", ...])` | Unified enhancement |
| `cli/codebase_scraper.py` | 1021-1022 | `subprocess.run(["claude", "--dangerously-skip-permissions", "-p", prompt])` | Codebase enhancement |
| `cli/enhance_skill_local.py` | 117 | `AGENT_PRESETS["claude"]["command"]` = `["claude", "{prompt_file}"]` | Agent preset |

**Status:** ⚠️ **Partially mitigated** - `enhance_skill_local.py` now has Kimi support, but other files still directly spawn `claude`

---

## Category 2: HARDCODED MODEL NAMES (Must Fix)

| File | Line | Model | Context |
|------|------|-------|---------|
| `cli/ai_enhancer.py` | 153 | `claude-sonnet-4-20250514` | `_call_claude_api()` |
| `cli/enhance_skill.py` | 76 | `claude-sonnet-4-20250514` | Enhancement |
| `cli/enhance_skill.py` | 381 | `claude-sonnet-4-20250514` | Adaptor enhance |
| `cli/unified_enhancer.py` | 282 | `claude-sonnet-4-20250514` | Unified enhancement |
| `cli/config_enhancer.py` | 145 | `claude-sonnet-4-20250514` | Config enhancement |
| `cli/guide_enhancer.py` | 366 | `claude-sonnet-4-20250514` | Guide enhancement |
| `cli/codebase_scraper.py` | 961 | `claude-sonnet-4-20250514` | Codebase enhancement |
| `cli/video_scraper.py` | 303 | `claude-sonnet-4-20250514` | Video reference cleaning |
| `cli/video_visual.py` | 593 | `claude-haiku-4-5-20251001` | Vision OCR |
| `cli/adaptors/claude.py` | 381 | `claude-sonnet-4-20250514` | Claude adaptor (OK) |

**Recommendation:** Make configurable via:
- Environment variable: `SKILL_SEEKER_MODEL` or provider-specific vars
- Config file setting
- Per-adaptor default models

---

## Category 3: HARDCODED DEFAULT VALUES (Must Fix)

### Target Platform Defaults

| File | Line | Current | Should Be |
|------|------|---------|-----------|
| `arguments/package.py` | 57 | `default: "claude"` | `default: None` (auto-detect) |
| `arguments/upload.py` | 26 | `default: "claude"` | `default: None` (auto-detect) |
| `arguments/install_skill.py` | 123 | `default: "claude"` | `default: None` (auto-detect) |

### Agent Selection Defaults

| File | Line | Current | Should Be |
|------|------|---------|-----------|
| `arguments/common.py` | 75 | `choices: ["claude", "codex", ...]` (claude first) | Alphabetical or env-based |
| `arguments/enhance.py` | 58 | `choices: ["claude", "codex", ...]` (claude first) | Alphabetical or env-based |
| `arguments/unified.py` | 80 | `choices: ["claude", "codex", ...]` (claude first) | Alphabetical or env-based |
| `enhance_skill_local.py` | 205 | `agent or env_agent or "claude"` | `agent or env_agent or "kimi"` (first available) |

---

## Category 4: HARDCODED ENVIRONMENT VARIABLES (Must Fix)

### Direct ANTHROPIC_API_KEY checks (not using adaptor pattern)

| File | Line(s) | Issue |
|------|---------|-------|
| `cli/utils.py` | 79-95 | `has_api_key()` and `get_api_key()` ONLY check `ANTHROPIC_API_KEY` |
| `cli/config_manager.py` | 50, 315 | Config structure with anthropic first |
| `cli/doctor.py` | 37, 63 | anthropic as CORE dep, ANTHROPIC_API_KEY first in list |
| `cli/ai_enhancer.py` | 74 | `os.environ.get("ANTHROPIC_API_KEY")` |
| `cli/enhance_skill.py` | 41-43 | `os.environ.get("ANTHROPIC_API_KEY")` or `ANTHROPIC_AUTH_TOKEN` |
| `cli/video_scraper.py` | 275 | `os.environ.get("ANTHROPIC_API_KEY")` |
| `cli/video_visual.py` | 562 | `os.environ.get("ANTHROPIC_API_KEY", "")` |
| `cli/codebase_scraper.py` | 914 | `os.environ.get("ANTHROPIC_API_KEY")` |
| `cli/unified_enhancer.py` | 93 | `os.environ.get("ANTHROPIC_API_KEY")` |
| `cli/guide_enhancer.py` | 87 | `os.environ.get("ANTHROPIC_API_KEY")` |
| `cli/config_enhancer.py` | 78 | `os.environ.get("ANTHROPIC_API_KEY")` |
| `mcp/server_legacy.py` | 869, 1795 | `os.environ.get("ANTHROPIC_API_KEY", "")` |

**Recommendation:** Use adaptor pattern - each adaptor should specify its env var name via `get_env_var_name()` method.

---

## Category 5: HARDCODED "CLAUDE-ENHANCED" MERGE MODE (Must Fix)

| File | Line | Content |
|------|------|---------|
| `arguments/create.py` | 543 | `choices: ["rule-based", "claude-enhanced"]` |
| `arguments/unified.py` | 25 | `"help": "Merge mode (rule-based, claude-enhanced)"` |
| `config_validator.py` | 64 | `VALID_MERGE_MODES = {"rule-based", "claude-enhanced"}` |
| `merge_sources.py` | 7, 445+ | Class `ClaudeEnhancedMerger`, multiple references |
| `mcp/server_fastmcp.py` | 360 | Description mentions `claude-enhanced` |
| `mcp/server_legacy.py` | 233 | Description mentions `claude-enhanced` |

**Recommendation:** Rename to `ai-enhanced` or `llm-enhanced` with backward compatibility alias.

---

## Category 6: HELP TEXT MENTIONS "CLAUDE CODE" / "ANTHROPIC_API_KEY" (Should Fix)

### 15+ argument files with identical pattern:

All these files have help text:
```python
"Mode selection: uses API if ANTHROPIC_API_KEY is set, otherwise LOCAL (Claude Code, Kimi, etc.)"
```

Affected files:
- `arguments/common.py:58`
- `arguments/create.py:60`
- `arguments/video.py:159`
- `arguments/jupyter.py:60-61`
- `arguments/pptx.py:60-61`
- `arguments/word.py:59`
- `arguments/epub.py:59`
- `arguments/notion.py:93-94`
- `arguments/asciidoc.py:60-61`
- `arguments/chat.py:94-95`
- `arguments/pdf.py:67`
- `arguments/html.py:60-61`
- `arguments/confluence.py:101-102`
- `arguments/rss.py:93-94`
- `arguments/manpage.py:76-77`
- `arguments/openapi.py:68-69`

**Recommendation:** Change to:
```python
"Mode selection: uses API if API key is set (ANTHROPIC_API_KEY, MOONSHOT_API_KEY, etc.), otherwise LOCAL (AI agent, Kimi, etc.)"
```

---

## Category 7: MCP SERVER CLAUDE-SPECIFIC REFERENCES (Must Fix)

### server_fastmcp.py

| Line | Content | Issue |
|------|---------|-------|
| 6 | `Provides 34 tools for generating Claude AI skills` | Should be "LLM skills" |
| 166 | `instructions="...Generate Claude AI skills..."` | Server instructions |
| 341, 352 | Tool descriptions mention "Claude skill" | 10+ occurrences |
| 357 | `enhance_local: Open terminal for local enhancement with Claude Code` | Hardcoded to Claude Code |
| 360 | `merge_mode: 'rule-based' or 'claude-enhanced'` | Hardcoded mode name |
| 796-797 | Enhance parameter descriptions mention Claude Code CLI | Should be generic |
| 940 | Description mentions "Claude Code Max" | Hardcoded |
| 954 | `mode: local (Claude Code, no API)` | Hardcoded |

### server_legacy.py

| Line | Content | Issue |
|------|---------|-------|
| 4 | `Model Context Protocol server for generating Claude AI skills` | Module docstring |
| 203-447 | 20+ tool descriptions mention "Claude" | All tool descriptions |
| 869, 1795 | Direct ANTHROPIC_API_KEY checks | Env var |
| 901, 917 | URLs to `claude.ai/skills` | Hardcoded URL |
| 1746 | `[DRY RUN] Would enhance SKILL.md with Claude Code` | Hardcoded |

### packaging_tools.py

| Line | Content | Issue |
|------|---------|-------|
| 640 | `[DRY RUN] Would enhance SKILL.md with Claude Code` | Hardcoded |
| 175-214 | Platform-specific success messages for Claude | Should adapt to target |

---

## Category 8: DOCUMENTATION/DOCS (Low Priority)

### README.md (mcp/README.md)
- 60+ references to "Claude", "Claude Code", "anthropic.com"
- All example outputs use "Claude:" persona
- All URLs point to Claude resources

### Module docstrings
- Most scrapers: `"XXX to Claude Skill Converter"`
- Most tools: `"Build Claude skill..."`

**Recommendation:** These are lower priority as they're documentation, not functional code.

---

## Category 9: VIDEO MIDDLE-LAYER AI (Partial Support)

### video_scraper.py

| Line | Issue |
|------|-------|
| 267-313 | `_ai_clean_reference()` function hardcoded to use Claude API |
| 871 | Comment acknowledges: "Middle-layer AI cleaning currently only supports Claude API" |

**Status:** ✅ **Acknowledged limitation** - enhancement at SKILL.md level works with any agent, but per-reference-file cleaning is Claude-only.

---

## Category 10: ENHANCEMENT WORKFLOW (Minor Fix)

### enhancement_workflow.py

| Line | Issue |
|------|-------|
| 396 | `response = self.enhancer._call_claude(formatted_prompt, max_tokens=3000)` | Direct method call |

**Recommendation:** Use generic `call_ai()` method instead of `_call_claude()`.

---

## Full Action Items List

### 🔴 Critical (Breaks functionality with non-Claude agents)

1. **Fix subprocess calls** - Replace direct `claude` CLI invocations with configurable agent commands
2. **Fix hardcoded model names** - Make models configurable via env vars/config
3. **Fix ANTHROPIC_API_KEY checks** - Use adaptor pattern for API key detection
4. **Rename "claude-enhanced"** → "ai-enhanced" with backward compatibility

### 🟠 High (Defaults favor Claude)

5. **Fix default values** - Change `default: "claude"` to `default: None` with auto-detection
6. **Fix help text** - Replace "Claude Code" / "ANTHROPIC_API_KEY" with generic terms in 15+ files
7. **Fix MCP server descriptions** - Generalize tool descriptions

### 🟡 Medium (Documentation/comments)

8. **Fix module docstrings** - "XXX to Claude Skill Converter" → "XXX to AI Skill"
9. **Fix README** - Show multi-platform examples, not just Claude

### 🟢 Low (Cosmetic)

10. **Reorder choices** - Alphabetize platform/agent choices instead of Claude first

---

## Files Requiring Changes (Priority Order)

### 🔴 Critical (12 files)
1. `cli/ai_enhancer.py`
2. `cli/config_enhancer.py`
3. `cli/guide_enhancer.py`
4. `cli/unified_enhancer.py`
5. `cli/codebase_scraper.py`
6. `cli/enhance_skill.py`
7. `cli/merge_sources.py`
8. `cli/enhancement_workflow.py`
9. `cli/video_scraper.py` (middle-layer AI)
10. `cli/video_visual.py`
11. `mcp/server_fastmcp.py`
12. `mcp/server_legacy.py`

### 🟠 High (20+ files)
13. `arguments/package.py`
14. `arguments/upload.py`
15. `arguments/install_skill.py`
16. `arguments/common.py`
17. `arguments/enhance.py`
18. `arguments/unified.py`
19. `arguments/create.py`
20. `arguments/video.py`
21-33. All other argument files (jupyter, pptx, word, epub, notion, asciidoc, chat, pdf, html, confluence, rss, manpage, openapi)
34. `config_validator.py`
35. `mcp/tools/packaging_tools.py`
36. `utils.py`

### 🟡 Medium (10+ files)
37-46. All scraper module docstrings (doc_scraper.py, github_scraper.py, etc.)
47. `mcp/README.md`
48. `main.py`

---

## Implementation Strategy

### Phase 1: Critical Fixes (Subprocess + Models)
- Abstract subprocess calls through agent presets
- Centralize model names in configuration
- Use adaptor pattern for all API calls

### Phase 2: High Priority (Defaults + Help Text)
- Change defaults to auto-detect
- Generalize help text
- Fix MCP server descriptions

### Phase 3: Medium/Low (Documentation)
- Update module docstrings
- Rewrite README with multi-platform focus

---

## Current Status of Kimi Support

✅ **Working:**
- KimiAdaptor properly extends OpenAICompatibleAdaptor
- Agent preset for `kimi` in `enhance_skill_local.py`
- `--agent kimi` CLI argument support
- `MOONSHOT_API_KEY` detection in config

⚠️ **Partial:**
- Video middle-layer AI cleaning (Claude-only, documented limitation)
- Some help text still mentions "Claude Code" exclusively

❌ **Not Working (requires fixes from this audit):**
- Default platform is still "claude"
- Some subprocess calls bypass agent abstraction
- Model names hardcoded to Claude versions

---

## Conclusion

The codebase has **systemic Claude bias** from being developed primarily for Claude. While Kimi support has been added, **true multi-platform support requires the fixes outlined in this audit**.

**Estimated effort:** 2-3 days for critical fixes, 1 week for full audit completion.
