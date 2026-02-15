# CLI Architecture Refactor Proposal
## Fixing Issue #285 (Parser Sync) and Enabling Issue #268 (Preset System)

**Date:** 2026-02-14  
**Status:** Proposal - Pending Review  
**Related Issues:** #285, #268

---

## Executive Summary

This proposal outlines a unified architecture to:
1. **Fix Issue #285**: Parser definitions are out of sync with scraper modules
2. **Enable Issue #268**: Add a preset system to simplify user experience

**Recommended Approach:** Pure Explicit (shared argument definitions)  
**Estimated Effort:** 2-3 days  
**Breaking Changes:** None (fully backward compatible)

---

## 1. Problem Analysis

### Issue #285: Parser Drift

Current state:
```
src/skill_seekers/cli/
├── doc_scraper.py          # 26 arguments defined here
├── github_scraper.py       # 15 arguments defined here
├── parsers/
│   ├── scrape_parser.py    # 12 arguments (OUT OF SYNC!)
│   ├── github_parser.py    # 10 arguments (OUT OF SYNC!)
```

**Impact:** Users cannot use arguments like `--interactive`, `--url`, `--verbose` via the unified CLI.

**Root Cause:** Code duplication - same arguments defined in two places.

### Issue #268: Flag Complexity

Current `analyze` command has 10+ flags. Users are overwhelmed.

**Proposed Solution:** Preset system (`--preset quick|standard|comprehensive`)

---

## 2. Proposed Architecture: Pure Explicit

### Core Principle

Define arguments **once** in a shared location. Both the standalone scraper and unified CLI parser import and use the same definition.

```
┌─────────────────────────────────────────────────────────────┐
│              SHARED ARGUMENT DEFINITIONS                     │
│         (src/skill_seekers/cli/arguments/*.py)              │
├─────────────────────────────────────────────────────────────┤
│  scrape.py      ← All 26 scrape arguments defined ONCE      │
│  github.py      ← All 15 github arguments defined ONCE      │
│  analyze.py     ← All analyze arguments + presets           │
│  common.py      ← Shared arguments (verbose, config, etc)   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐      ┌─────────────────────────┐
│   Standalone Scrapers   │      │   Unified CLI Parsers   │
├─────────────────────────┤      ├─────────────────────────┤
│ doc_scraper.py          │      │ parsers/scrape_parser.py│
│ github_scraper.py       │      │ parsers/github_parser.py│
│ codebase_scraper.py     │      │ parsers/analyze_parser.py│
└─────────────────────────┘      └─────────────────────────┘
```

### Why "Pure Explicit" Over "Hybrid"

| Approach | Description | Risk Level |
|----------|-------------|------------|
| **Pure Explicit** (Recommended) | Define arguments in shared functions, call from both sides | ✅ Low - Uses only public APIs |
| **Hybrid with Auto-Introspection** | Use `parser._actions` to copy arguments automatically | ⚠️ High - Uses internal APIs |
| **Quick Fix** | Just fix scrape_parser.py | 🔴 Tech debt - Problem repeats |

**Decision:** Use Pure Explicit. Slightly more code, but rock-solid maintainability.

---

## 3. Implementation Details

### 3.1 New Directory Structure

```
src/skill_seekers/cli/
├── arguments/                    # NEW: Shared argument definitions
│   ├── __init__.py
│   ├── common.py                # Shared args: --verbose, --config, etc.
│   ├── scrape.py                # All scrape command arguments
│   ├── github.py                # All github command arguments
│   ├── analyze.py               # All analyze arguments + preset support
│   └── pdf.py                   # PDF arguments
│
├── presets/                     # NEW: Preset system (Issue #268)
│   ├── __init__.py
│   ├── base.py                  # Preset base class
│   └── analyze_presets.py       # Analyze-specific presets
│
├── parsers/                     # EXISTING: Modified to use shared args
│   ├── __init__.py
│   ├── base.py
│   ├── scrape_parser.py         # Now imports from arguments/
│   ├── github_parser.py         # Now imports from arguments/
│   ├── analyze_parser.py        # Adds --preset support
│   └── ...
│
└── scrapers/                    # EXISTING: Modified to use shared args
    ├── doc_scraper.py           # Now imports from arguments/
    ├── github_scraper.py        # Now imports from arguments/
    └── codebase_scraper.py      # Now imports from arguments/
```

### 3.2 Shared Argument Definitions

**File: `src/skill_seekers/cli/arguments/scrape.py`**

```python
"""Shared argument definitions for scrape command.

This module defines ALL arguments for the scrape command in ONE place.
Both doc_scraper.py and parsers/scrape_parser.py use these definitions.
"""

import argparse


def add_scrape_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all scrape command arguments to a parser.
    
    This is the SINGLE SOURCE OF TRUTH for scrape arguments.
    Used by:
    - doc_scraper.py (standalone scraper)
    - parsers/scrape_parser.py (unified CLI)
    """
    # Positional argument
    parser.add_argument(
        "url",
        nargs="?",
        help="Documentation URL (positional argument)"
    )
    
    # Core options
    parser.add_argument(
        "--url",
        type=str,
        help="Base documentation URL (alternative to positional)"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive configuration mode"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Load configuration from JSON file"
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Skill name"
    )
    parser.add_argument(
        "--description", "-d",
        type=str,
        help="Skill description"
    )
    
    # Scraping options
    parser.add_argument(
        "--max-pages",
        type=int,
        dest="max_pages",
        metavar="N",
        help="Maximum pages to scrape (overrides config)"
    )
    parser.add_argument(
        "--rate-limit", "-r",
        type=float,
        metavar="SECONDS",
        help="Override rate limit in seconds"
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        metavar="N",
        help="Number of parallel workers (default: 1, max: 10)"
    )
    parser.add_argument(
        "--async",
        dest="async_mode",
        action="store_true",
        help="Enable async mode for better performance"
    )
    parser.add_argument(
        "--no-rate-limit",
        action="store_true",
        help="Disable rate limiting"
    )
    
    # Control options
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip scraping, use existing data"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what will be scraped without scraping"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint"
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Clear checkpoint and start fresh"
    )
    
    # Enhancement options
    parser.add_argument(
        "--enhance",
        action="store_true",
        help="Enhance SKILL.md using Claude API (requires API key)"
    )
    parser.add_argument(
        "--enhance-local",
        action="store_true",
        help="Enhance using Claude Code (no API key needed)"
    )
    parser.add_argument(
        "--interactive-enhancement",
        action="store_true",
        help="Open terminal for enhancement (with --enhance-local)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Anthropic API key (or set ANTHROPIC_API_KEY)"
    )
    
    # Output options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimize output"
    )
    
    # RAG chunking options
    parser.add_argument(
        "--chunk-for-rag",
        action="store_true",
        help="Enable semantic chunking for RAG"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=512,
        metavar="TOKENS",
        help="Target chunk size in tokens (default: 512)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        metavar="TOKENS",
        help="Overlap between chunks (default: 50)"
    )
    parser.add_argument(
        "--no-preserve-code-blocks",
        action="store_true",
        help="Allow splitting code blocks"
    )
    parser.add_argument(
        "--no-preserve-paragraphs",
        action="store_true",
        help="Ignore paragraph boundaries"
    )
```

### 3.3 How Existing Files Change

**Before (doc_scraper.py):**
```python
def create_argument_parser():
    parser = argparse.ArgumentParser(...)
    parser.add_argument("url", nargs="?", help="...")
    parser.add_argument("--interactive", "-i", action="store_true", help="...")
    # ... 24 more add_argument calls ...
    return parser
```

**After (doc_scraper.py):**
```python
from skill_seekers.cli.arguments.scrape import add_scrape_arguments

def create_argument_parser():
    parser = argparse.ArgumentParser(...)
    add_scrape_arguments(parser)  # ← Single function call
    return parser
```

**Before (parsers/scrape_parser.py):**
```python
class ScrapeParser(SubcommandParser):
    def add_arguments(self, parser):
        parser.add_argument("url", nargs="?", help="...")  # ← Duplicate!
        parser.add_argument("--config", help="...")         # ← Duplicate!
        # ... only 12 args, missing many!
```

**After (parsers/scrape_parser.py):**
```python
from skill_seekers.cli.arguments.scrape import add_scrape_arguments

class ScrapeParser(SubcommandParser):
    def add_arguments(self, parser):
        add_scrape_arguments(parser)  # ← Same function as doc_scraper!
```

### 3.4 Preset System (Issue #268)

**File: `src/skill_seekers/cli/presets/analyze_presets.py`**

```python
"""Preset definitions for analyze command."""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class AnalysisPreset:
    """Definition of an analysis preset."""
    name: str
    description: str
    depth: str  # "surface", "deep", "full"
    features: Dict[str, bool]
    enhance_level: int
    estimated_time: str


# Preset definitions
PRESETS = {
    "quick": AnalysisPreset(
        name="Quick",
        description="Fast basic analysis (~1-2 min)",
        depth="surface",
        features={
            "api_reference": True,
            "dependency_graph": False,
            "patterns": False,
            "test_examples": False,
            "how_to_guides": False,
            "config_patterns": False,
        },
        enhance_level=0,
        estimated_time="1-2 minutes"
    ),
    
    "standard": AnalysisPreset(
        name="Standard",
        description="Balanced analysis with core features (~5-10 min)",
        depth="deep",
        features={
            "api_reference": True,
            "dependency_graph": True,
            "patterns": True,
            "test_examples": True,
            "how_to_guides": False,
            "config_patterns": True,
        },
        enhance_level=0,
        estimated_time="5-10 minutes"
    ),
    
    "comprehensive": AnalysisPreset(
        name="Comprehensive",
        description="Full analysis with AI enhancement (~20-60 min)",
        depth="full",
        features={
            "api_reference": True,
            "dependency_graph": True,
            "patterns": True,
            "test_examples": True,
            "how_to_guides": True,
            "config_patterns": True,
        },
        enhance_level=1,
        estimated_time="20-60 minutes"
    ),
}


def apply_preset(args, preset_name: str) -> None:
    """Apply a preset to args namespace."""
    preset = PRESETS[preset_name]
    args.depth = preset.depth
    args.enhance_level = preset.enhance_level
    
    for feature, enabled in preset.features.items():
        setattr(args, f"skip_{feature}", not enabled)
```

**Usage in analyze_parser.py:**
```python
from skill_seekers.cli.arguments.analyze import add_analyze_arguments
from skill_seekers.cli.presets.analyze_presets import PRESETS

class AnalyzeParser(SubcommandParser):
    def add_arguments(self, parser):
        # Add all base arguments
        add_analyze_arguments(parser)
        
        # Add preset argument
        parser.add_argument(
            "--preset",
            choices=list(PRESETS.keys()),
            help=f"Analysis preset ({', '.join(PRESETS.keys())})"
        )
```

---

## 4. Testing Strategy

### 4.1 Parser Sync Test (Prevents Regression)

**File: `tests/test_parser_sync.py`**

```python
"""Test that parsers stay in sync with scraper modules."""

import argparse
import pytest


class TestScrapeParserSync:
    """Ensure scrape_parser has all arguments from doc_scraper."""
    
    def test_scrape_arguments_in_sync(self):
        """Verify unified CLI parser has all doc_scraper arguments."""
        from skill_seekers.cli.doc_scraper import create_argument_parser
        from skill_seekers.cli.parsers.scrape_parser import ScrapeParser
        
        # Get source arguments from doc_scraper
        source_parser = create_argument_parser()
        source_dests = {a.dest for a in source_parser._actions}
        
        # Get target arguments from unified CLI parser
        target_parser = argparse.ArgumentParser()
        ScrapeParser().add_arguments(target_parser)
        target_dests = {a.dest for a in target_parser._actions}
        
        # Check for missing arguments
        missing = source_dests - target_dests
        assert not missing, f"scrape_parser missing arguments: {missing}"


class TestGitHubParserSync:
    """Ensure github_parser has all arguments from github_scraper."""
    
    def test_github_arguments_in_sync(self):
        """Verify unified CLI parser has all github_scraper arguments."""
        from skill_seekers.cli.github_scraper import create_argument_parser
        from skill_seekers.cli.parsers.github_parser import GitHubParser
        
        source_parser = create_argument_parser()
        source_dests = {a.dest for a in source_parser._actions}
        
        target_parser = argparse.ArgumentParser()
        GitHubParser().add_arguments(target_parser)
        target_dests = {a.dest for a in target_parser._actions}
        
        missing = source_dests - target_dests
        assert not missing, f"github_parser missing arguments: {missing}"
```

### 4.2 Preset System Tests

```python
"""Test preset system functionality."""

import pytest
from skill_seekers.cli.presets.analyze_presets import (
    PRESETS, 
    apply_preset,
    AnalysisPreset
)


class TestAnalyzePresets:
    """Test analyze preset definitions."""
    
    def test_all_presets_have_required_fields(self):
        """Verify all presets have required attributes."""
        required_fields = ['name', 'description', 'depth', 'features', 
                          'enhance_level', 'estimated_time']
        
        for preset_name, preset in PRESETS.items():
            for field in required_fields:
                assert hasattr(preset, field), \
                    f"Preset '{preset_name}' missing field '{field}'"
    
    def test_preset_quick_has_minimal_features(self):
        """Verify quick preset disables most features."""
        preset = PRESETS['quick']
        
        assert preset.depth == 'surface'
        assert preset.enhance_level == 0
        assert preset.features['dependency_graph'] is False
        assert preset.features['patterns'] is False
    
    def test_preset_comprehensive_has_all_features(self):
        """Verify comprehensive preset enables all features."""
        preset = PRESETS['comprehensive']
        
        assert preset.depth == 'full'
        assert preset.enhance_level == 1
        assert all(preset.features.values()), \
            "Comprehensive preset should enable all features"
    
    def test_apply_preset_modifies_args(self):
        """Verify apply_preset correctly modifies args."""
        from argparse import Namespace
        
        args = Namespace()
        apply_preset(args, 'quick')
        
        assert args.depth == 'surface'
        assert args.enhance_level == 0
        assert args.skip_dependency_graph is True
```

---

## 5. Migration Plan

### Phase 1: Foundation (Day 1)

1. **Create `arguments/` module**
   - `arguments/__init__.py`
   - `arguments/common.py` - shared arguments
   - `arguments/scrape.py` - all 26 scrape arguments

2. **Update `doc_scraper.py`**
   - Replace inline argument definitions with import from `arguments/scrape.py`
   - Test: `python -m skill_seekers.cli.doc_scraper --help` works

3. **Update `parsers/scrape_parser.py`**
   - Replace inline definitions with import from `arguments/scrape.py`
   - Test: `skill-seekers scrape --help` shows all 26 arguments

### Phase 2: Extend to Other Commands (Day 2)

1. **Create `arguments/github.py`**
2. **Update `github_scraper.py` and `parsers/github_parser.py`**
3. **Repeat for `pdf`, `analyze`, `unified` commands**
4. **Add parser sync tests** (`tests/test_parser_sync.py`)

### Phase 3: Preset System (Day 2-3)

1. **Create `presets/` module**
   - `presets/__init__.py`
   - `presets/base.py`
   - `presets/analyze_presets.py`

2. **Update `parsers/analyze_parser.py`**
   - Add `--preset` argument
   - Add preset resolution logic

3. **Update `codebase_scraper.py`**
   - Handle preset mapping in main()

4. **Add preset tests**

### Phase 4: Documentation & Cleanup (Day 3)

1. **Update docstrings**
2. **Update README.md** with preset examples
3. **Run full test suite**
4. **Verify backward compatibility**

---

## 6. Backward Compatibility

### Fully Maintained

| Aspect | Compatibility |
|--------|---------------|
| Command-line interface | ✅ 100% compatible - no removed arguments |
| JSON configs | ✅ No changes |
| Python API | ✅ No changes to public functions |
| Existing scripts | ✅ Continue to work |

### New Capabilities

| Feature | Availability |
|---------|--------------|
| `--interactive` flag | Now works in unified CLI |
| `--url` flag | Now works in unified CLI |
| `--preset quick` | New capability |
| All scrape args | Now available in unified CLI |

---

## 7. Benefits Summary

| Benefit | How Achieved |
|---------|--------------|
| **Fixes #285** | Single source of truth - parsers cannot drift |
| **Enables #268** | Preset system built on clean foundation |
| **Maintainable** | Explicit code, no magic, no internal APIs |
| **Testable** | Easy to verify sync with automated tests |
| **Extensible** | Easy to add new commands or presets |
| **Type-safe** | Functions can be type-checked |
| **Documented** | Arguments defined once, documented once |

---

## 8. Trade-offs

| Aspect | Trade-off |
|--------|-----------|
| **Lines of code** | ~200 more lines than hybrid approach (acceptable) |
| **Import overhead** | One extra import per module (negligible) |
| **Refactoring effort** | 2-3 days vs 2 hours for quick fix (worth it) |

---

## 9. Decision Required

Please review this proposal and indicate:

1. **✅ Approve** - Start implementation of Pure Explicit approach
2. **🔄 Modify** - Request changes to the approach
3. **❌ Reject** - Choose alternative (Hybrid or Quick Fix)

**Questions to consider:**
- Does this architecture meet your long-term maintainability goals?
- Is the 2-3 day timeline acceptable?
- Should we include any additional commands in the refactor?

---

## Appendix A: Alternative Approaches Considered

### A.1 Quick Fix (Rejected)

Just fix `scrape_parser.py` to match `doc_scraper.py`.

**Why rejected:** Problem will recur. No systematic solution.

### A.2 Hybrid with Auto-Introspection (Rejected)

Use `parser._actions` to copy arguments automatically.

**Why rejected:** Uses internal argparse APIs (`_actions`). Fragile.

```python
# FRAGILE - Uses internal API
for action in source_parser._actions:
    if action.dest not in common_dests:
        # How to clone? _clone_argument doesn't exist!
```

### A.3 Click Framework (Rejected)

Migrate entire CLI to Click.

**Why rejected:** Major refactor, breaking changes, too much effort.

---

## Appendix B: Example User Experience

### After Fix (Issue #285)

```bash
# Before: ERROR
$ skill-seekers scrape --interactive
error: unrecognized arguments: --interactive

# After: WORKS
$ skill-seekers scrape --interactive
? Enter documentation URL: https://react.dev
? Skill name: react
...
```

### With Presets (Issue #268)

```bash
# Before: Complex flags
$ skill-seekers analyze --directory . --depth full \
    --skip-patterns --skip-test-examples ...

# After: Simple preset
$ skill-seekers analyze --directory . --preset comprehensive
🚀 Comprehensive analysis mode: all features + AI enhancement (~20-60 min)
```

---

*End of Proposal*
