# Implementation Plan: Arbitrary Limits & Dead Code

**Generated:** 2026-02-24  
**Scope:** Remove harmful arbitrary limits and implement critical TODO items  
**Priority:** P0 (Critical) - P3 (Backlog)

---

## Part 1: Arbitrary Limits to Remove

### 🔴 P0 - Critical (Fix Immediately)

#### 1.1 Enhancement Code Block Limit
**File:** `src/skill_seekers/cli/enhance_skill_local.py:341`  
**Current:**
```python
for _idx, block in code_blocks[:5]:  # Max 5 code blocks
```
**Problem:** AI enhancement only sees 5 code blocks regardless of skill size. A skill with 100 code examples has 95% ignored during enhancement.

**Solution:**
```python
# Option A: Remove limit, use token counting instead
max_tokens = 4000  # Claude 3.5 Sonnet context for enhancement
current_tokens = 0
selected_blocks = []
for idx, block in code_blocks:
    block_tokens = estimate_tokens(block)
    if current_tokens + block_tokens > max_tokens:
        break
    selected_blocks.append((idx, block))
    current_tokens += block_tokens

for _idx, block in selected_blocks:
```

**Effort:** 2 hours  
**Impact:** High - Massive improvement in enhancement quality  
**Breaking Change:** No

---

### 🟠 P1 - High Priority (Next Sprint)

#### 1.2 Reference File Code Truncation
**Files:**
- `src/skill_seekers/cli/codebase_scraper.py:422, 489, 575, 720, 746`
- `src/skill_seekers/cli/unified_skill_builder.py:1298`

**Current:**
```python
"code": code[:500],  # Truncate long code blocks
```

**Problem:** Reference files should be comprehensive. Truncating code blocks at 500 chars breaks copy-paste functionality and harms skill utility.

**Solution:**
```python
# Remove truncation from reference files
"code": code,  # Full code

# Keep truncation only for SKILL.md summaries (if needed)
```

**Effort:** 1 hour  
**Impact:** High - Reference files become actually usable  
**Breaking Change:** No (output improves)

---

#### 1.3 Table Row Limit in References
**File:** `src/skill_seekers/cli/word_scraper.py:595`  

**Current:**
```python
for row in rows[:5]:
```

**Problem:** Tables in reference files truncated to 5 rows.

**Solution:** Remove `[:5]` limit from reference file generation. Keep limit only for SKILL.md summaries.

**Effort:** 30 minutes  
**Impact:** Medium  
**Breaking Change:** No

---

### 🟡 P2 - Medium Priority (Backlog)

#### 1.4 Pattern/Example Limits in Analysis
**Files:**
- `src/skill_seekers/cli/codebase_scraper.py:1898` - `examples[:10]`
- `src/skill_seekers/cli/github_scraper.py:1145, 1169` - Pattern limits
- `src/skill_seekers/cli/doc_scraper.py:608` - `patterns[:5]`

**Problem:** Pattern detection limited arbitrarily, missing edge cases.

**Solution:** Make configurable via `--max-patterns` flag with sensible default (50 instead of 5-10).

**Effort:** 3 hours  
**Impact:** Medium - Better pattern coverage  
**Breaking Change:** No

---

#### 1.5 Issue/Release Limits in GitHub Scraper
**File:** `src/skill_seekers/cli/github_scraper.py`

**Current:**
```python
for release in releases[:3]:
for issue in issues[:5]:
for issue in open_issues[:20]:
```

**Problem:** Hard limits without user control.

**Solution:** Add CLI flags:
```python
parser.add_argument("--max-issues", type=int, default=50)
parser.add_argument("--max-releases", type=int, default=10)
```

**Effort:** 2 hours  
**Impact:** Medium - User control  
**Breaking Change:** No

---

#### 1.6 Config File Display Limits
**Files:**
- `src/skill_seekers/cli/config_manager.py:540` - `jobs[:5]`
- `src/skill_seekers/cli/config_enhancer.py:165, 302` - Config file limits

**Problem:** Display truncated for UX reasons, but should have `--verbose` override.

**Solution:** Add verbose mode check:
```python
if verbose:
    display_items = items
else:
    display_items = items[:5]  # Truncated for readability
```

**Effort:** 2 hours  
**Impact:** Low-Medium  
**Breaking Change:** No

---

### 🟢 P3 - Low Priority / Keep As Is

These limits are justified and should remain:

| Location | Limit | Justification |
|----------|-------|---------------|
| `word_scraper.py:553` | `all_code[:15]` | SKILL.md summary - full code in references |
| `word_scraper.py:567` | `examples[:5]` | Per-language summary in SKILL.md |
| `pdf_scraper.py:453, 472` | Same as above | Consistent with Word scraper |
| `word_scraper.py:658, 664` | `[:10], [:15]` | Key concepts list (justified for readability) |
| `adaptors/*.py` | `[:30000]` | API token limits (Claude/Gemini/OpenAI) |
| `base.py:208` | `[:500]` | Preview/summary text (not reference) |

---

## Part 1b: Hardcoded Language Issues

These are **data flow bugs** - the correct language is available upstream but hardcoded to `"python"` downstream.

### 🔴 P0 - Critical

#### 1.b.1 Test Example Code Snippets
**File:** `src/skill_seekers/cli/unified_skill_builder.py:1298`

**Current:**
```python
f.write(f"\n```python\n{ex['code_snippet'][:300]}\n```\n")
```

**Problem:** Hardcoded to `python` regardless of actual language.

**Available Data:** The `ex` dict from `TestExample.to_dict()` includes a `language` field.

**Fix:**
```python
lang = ex.get("language", "text")
f.write(f"\n```{lang}\n{ex['code_snippet'][:300]}\n```\n")
```

**Effort:** 1 minute  
**Impact:** Medium - Syntax highlighting now correct  
**Breaking Change:** No

---

#### 1.b.2 How-To Guide Language
**File:** `src/skill_seekers/cli/how_to_guide_builder.py:1018`

**Current:**
```python
"language": "python",  # TODO: Detect from code
```

**Problem:** Language hardcoded in guide data sent to AI enhancement.

**Solution (3 one-line changes):**

1. **Add field to dataclass** (around line 70):
```python
@dataclass
class HowToGuide:
    # ... existing fields ...
    language: str = "python"  # Source file language
```

2. **Set at creation** (line 955, in `_create_guide_from_workflow`):
```python
HowToGuide(
    # ... other fields ...
    language=primary_workflow.get("language", "python"),
)
```

3. **Use the field** (line 1018):
```python
"language": guide.language,
```

**Note:** The `primary_workflow` dict already carries the language field (populated by test example extractor upstream at line 169). Zero new imports needed.

**Effort:** 5 minutes  
**Impact:** Medium - AI receives correct language context  
**Breaking Change:** No

---

## Part 2: Dead Code / TODO Implementation

### 🔴 P0 - Critical TODOs (Implement Now)

#### 2.1 SMTP Email Notifications
**File:** `src/skill_seekers/sync/notifier.py:138`  

**Current:**
```python
# TODO: Implement SMTP email sending
```

**Implementation:**
```python
def _send_email_smtp(self, to_email: str, subject: str, body: str) -> bool:
    """Send email via SMTP."""
    import smtplib
    from email.mime.text import MIMEText
    
    smtp_host = os.environ.get("SKILL_SEEKERS_SMTP_HOST", "localhost")
    smtp_port = int(os.environ.get("SKILL_SEEKERS_SMTP_PORT", "587"))
    smtp_user = os.environ.get("SKILL_SEEKERS_SMTP_USER")
    smtp_pass = os.environ.get("SKILL_SEEKERS_SMTP_PASS")
    
    if not all([smtp_user, smtp_pass]):
        logger.warning("SMTP credentials not configured")
        return False
    
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to_email
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
```

**Effort:** 4 hours  
**Dependencies:** Environment variables for SMTP config  
**Breaking Change:** No

---

### 🟠 P1 - High Priority (Next Sprint)

#### 2.2 Auto-Update Integration
**File:** `src/skill_seekers/sync/monitor.py:201`

**Current:**
```python
# TODO: Integrate with doc_scraper to rebuild skill
```

**Implementation:** Call existing scraper commands when changes detected.

```python
def _rebuild_skill(self, config_path: str) -> bool:
    """Rebuild skill when changes detected."""
    import subprocess
    
    # Use existing create command
    result = subprocess.run(
        ["skill-seekers", "create", config_path, "--force"],
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )
    
    return result.returncode == 0
```

**Effort:** 3 hours  
**Dependencies:** Ensure `skill-seekers` CLI available in PATH  
**Breaking Change:** No

---

#### 2.3 Language Detection in How-To Guides
**File:** `src/skill_seekers/cli/how_to_guide_builder.py:1018`

**Current:**
```python
"language": "python",  # TODO: Detect from code
```

**Implementation:** Use existing `LanguageDetector`:

```python
from skill_seekers.cli.language_detector import LanguageDetector

detector = LanguageDetector(min_confidence=0.3)
language, confidence = detector.detect_from_text(code)
if confidence < 0.3:
    language = "text"  # Fallback
```

**Effort:** 1 hour  
**Dependencies:** Existing LanguageDetector class  
**Breaking Change:** No

---

### 🟡 P2 - Medium Priority (Backlog)

#### 2.4 Custom Transform System
**File:** `src/skill_seekers/cli/enhancement_workflow.py:439`

**Current:**
```python
# TODO: Implement custom transform system
```

**Purpose:** Allow users to define custom code transformations in workflow YAML.

**Implementation Sketch:**
```yaml
# Example workflow addition
transforms:
  - name: "Remove boilerplate"
    pattern: "Copyright \(c\) \d+"
    action: "remove"
  - name: "Normalize headers"
    pattern: "^#{1,6} "
    replacement: "## "
```

**Effort:** 8 hours  
**Impact:** Medium - Power user feature  
**Breaking Change:** No

---

#### 2.5 Vector Database Storage for Embeddings
**File:** `src/skill_seekers/embedding/server.py:268`

**Current:**
```python
# TODO: Store embeddings in vector database
```

**Implementation Options:**
- Option A: ChromaDB integration (already have adaptor)
- Option B: Qdrant integration (already have adaptor)
- Option C: SQLite with vector extension (simplest)

**Recommendation:** Start with SQLite + `sqlite-vec` for zero-config setup.

**Effort:** 6 hours  
**Dependencies:** New dependency `sqlite-vec`  
**Breaking Change:** No

---

### 🟢 P3 - Backlog / Low Priority

#### 2.6 URL Resolution in Sync Monitor
**File:** `src/skill_seekers/sync/monitor.py:136`

**Current:**
```python
# TODO: In real implementation, get actual URLs from scraper
```

**Note:** Current implementation uses placeholder URLs. Full implementation requires scraper to expose URL list.

**Effort:** 4 hours  
**Impact:** Low - Current implementation works for basic use  
**Breaking Change:** No

---

## Implementation Schedule

### Week 1: Critical Fixes
- [ ] Remove `[:5]` limit in `enhance_skill_local.py` (P0)
- [ ] Remove `[:500]` truncation from reference files (P1)
- [ ] Remove `[:5]` table row limit (P1)

### Week 2: Notifications & Integration
- [ ] Implement SMTP notifications (P0)
- [ ] Implement auto-update in sync monitor (P1)
- [ ] Fix language detection in how-to guides (P1)

### Week 3: Configurability
- [ ] Add `--max-patterns`, `--max-issues` CLI flags (P2)
- [ ] Add verbose mode for display limits (P2)
- [ ] Add `--max-code-blocks` for enhancement (P2)

### Backlog
- [ ] Custom transform system (P2)
- [ ] Vector DB storage for embeddings (P2)
- [ ] URL resolution in sync monitor (P3)

---

## Testing Strategy

### For Limit Removal
1. Create test skill with 100+ code blocks
2. Verify enhancement sees all code (or token-based limit)
3. Verify reference files contain complete code
4. Verify SKILL.md still has appropriate summaries

### For Hardcoded Language Fixes
1. Create skill from JavaScript/Go/Rust test examples
2. Verify `unified_skill_builder.py` outputs correct language tag in markdown
3. Verify `how_to_guide_builder.py` uses correct language in AI prompt

### For TODO Implementation
1. SMTP: Mock SMTP server test
2. Auto-update: Mock subprocess test
3. Language detection: Test with mixed-language code samples

---

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| Code blocks in enhancement | 5 max | Token-based (40+) |
| Code truncation in refs | 500 chars | Full code |
| Table rows in refs | 5 max | All rows |
| Code snippet language | Always "python" | Correct language |
| Guide language | Always "python" | Source file language |
| Email notifications | Webhook only | SMTP + webhook |
| Auto-update | Manual only | Automatic |

---

## Appendix: Files Modified

### Limit Removals
- `src/skill_seekers/cli/enhance_skill_local.py`
- `src/skill_seekers/cli/codebase_scraper.py`
- `src/skill_seekers/cli/unified_skill_builder.py`
- `src/skill_seekers/cli/word_scraper.py`

### Hardcoded Language Fixes
- `src/skill_seekers/cli/unified_skill_builder.py` (line 1298)
- `src/skill_seekers/cli/how_to_guide_builder.py` (dataclass + lines 955, 1018)

### TODO Implementations
- `src/skill_seekers/sync/notifier.py`
- `src/skill_seekers/sync/monitor.py`
- `src/skill_seekers/cli/how_to_guide_builder.py`
- `src/skill_seekers/cli/github_scraper.py` (new flags)
- `src/skill_seekers/cli/config_manager.py` (verbose mode)

---

*This document should be reviewed and updated after each implementation phase.*
