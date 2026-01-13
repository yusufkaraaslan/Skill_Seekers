# Skill Quality Fix Plan

**Created:** 2026-01-11
**Status:** Not Started
**Priority:** P0 - Blocking Production Use

---

## 🎯 Executive Summary

The multi-source synthesis architecture successfully:
- ✅ Organizes files cleanly (.skillseeker-cache/ + output/)
- ✅ Collects C3.x codebase analysis data
- ✅ Moves files correctly to cache

But produces poor quality output:
- ❌ Synthesis doesn't truly merge (loses content)
- ❌ Content formatting is broken (walls of text)
- ❌ AI enhancement reads only 13KB out of 30KB references
- ❌ Many accuracy and duplication issues

**Bottom Line:** The engine works, but the output is unusable.

---

## 📊 Quality Assessment

### Current State
| Aspect | Score | Status |
|--------|-------|--------|
| File organization | 10/10 | ✅ Excellent |
| C3.x data collection | 9/10 | ✅ Very Good |
| **Synthesis logic** | **3/10** | ❌ **Failing** |
| **Content formatting** | **2/10** | ❌ **Failing** |
| **AI enhancement** | **2/10** | ❌ **Failing** |
| Overall usability | 4/10 | ❌ Poor |

---

## 🔴 P0: Critical Blocking Issues

### Issue 1: Synthesis Doesn't Merge Content
**File:** `src/skill_seekers/cli/unified_skill_builder.py`
**Lines:** 73-162 (`_generate_skill_md`)

**Problem:**
- Docs source: 155 lines
- GitHub source: 255 lines
- **Output: only 186 lines** (should be ~300-400)

Missing from output:
- GitHub repository metadata (stars, topics, last updated)
- Detailed API reference sections
- Language statistics (says "1 file" instead of "54 files")
- Most C3.x analysis details

**Root Cause:** Synthesis just concatenates specific sections instead of intelligently merging all content.

**Fix Required:**
1. Implement proper section-by-section synthesis
2. Merge "When to Use" sections from both sources
3. Combine "Quick Reference" from both
4. Add GitHub metadata to intro
5. Merge code examples (docs + codebase)
6. Include comprehensive API reference links

**Files to Modify:**
- `unified_skill_builder.py:_generate_skill_md()`
- `unified_skill_builder.py:_synthesize_docs_github()`

---

### Issue 2: Pattern Formatting is Unreadable
**File:** `output/httpx/SKILL.md`
**Lines:** 42-64, 69

**Problem:**
```markdown
**Pattern 1:** httpx.request(method, url, *, params=None, content=None, data=None, files=None, json=None, headers=None, cookies=None, auth=None, proxy=None, timeout=Timeout(timeout=5.0), follow_redirects=False, verify=True, trust_env=True) Sends an HTTP request...
```

- 600+ character single line
- All parameters run together
- No structure
- Completely unusable by LLM

**Fix Required:**
1. Format API patterns with proper structure:
```markdown
### `httpx.request()`

**Signature:**
```python
httpx.request(
    method, url, *,
    params=None,
    content=None,
    ...
)
```

**Parameters:**
- `method`: HTTP method (GET, POST, PUT, etc.)
- `url`: Target URL
- `params`: (optional) Query parameters
...

**Returns:** Response object

**Example:**
```python
>>> import httpx
>>> response = httpx.request('GET', 'https://httpbin.org/get')
```
```

**Files to Modify:**
- `doc_scraper.py:extract_patterns()` - Fix pattern extraction
- `doc_scraper.py:_format_pattern()` - Add proper formatting method

---

### Issue 3: AI Enhancement Missing 57% of References
**File:** `src/skill_seekers/cli/utils.py`
**Lines:** 274-275

**Problem:**
```python
if ref_file.name == "index.md":
    continue  # SKIPS ALL INDEX FILES!
```

**Impact:**
- Reads: 13KB (43% of content)
  - ARCHITECTURE.md
  - issues.md
  - README.md
  - releases.md
- **Skips: 17KB (57% of content)**
  - patterns/index.md (10.5KB) ← HUGE!
  - examples/index.md (5KB)
  - configuration/index.md (933B)
  - guides/index.md
  - documentation/index.md

**Result:**
```
✓ Read 4 reference files
✓ Total size: 24 characters  ← WRONG! Should be ~30KB
```

**Fix Required:**
1. Remove the index.md skip logic
2. Or rename files: index.md → patterns.md, examples.md, etc.
3. Update unified_skill_builder to use non-index names

**Files to Modify:**
- `utils.py:read_reference_files()` line 274-275
- `unified_skill_builder.py:_generate_references()` - Fix file naming

---

## 🟡 P1: Major Quality Issues

### Issue 4: "httpx_docs" Text Not Replaced
**File:** `output/httpx/SKILL.md`
**Lines:** 20-24

**Problem:**
```markdown
- Working with httpx_docs  ← Should be "httpx"
- Asking about httpx_docs features  ← Should be "httpx"
```

**Root Cause:** Docs source SKILL.md has placeholder `{name}` that's not replaced during synthesis.

**Fix Required:**
1. Add text replacement in synthesis: `httpx_docs` → `httpx`
2. Or fix doc_scraper template to use correct name

**Files to Modify:**
- `unified_skill_builder.py:_synthesize_docs_github()` - Add replacement
- Or `doc_scraper.py` template

---

### Issue 5: Duplicate Examples
**File:** `output/httpx/SKILL.md`
**Lines:** 133-143

**Problem:**
Exact same Cookie example shown twice in a row.

**Fix Required:**
Deduplicate examples during synthesis.

**Files to Modify:**
- `unified_skill_builder.py:_synthesize_docs_github()` - Add deduplication

---

### Issue 6: Wrong Language Tags
**File:** `output/httpx/SKILL.md`
**Lines:** 97-125

**Problem:**
```markdown
**Example 1** (typescript):  ← WRONG, it's Python!
```typescript
with httpx.Client(proxy="http://localhost:8030"):
```

**Example 3** (jsx):  ← WRONG, it's Python!
```jsx
>>> import httpx
```

**Root Cause:** Doc scraper's language detection is failing.

**Fix Required:**
Improve `detect_language()` function in doc_scraper.py.

**Files to Modify:**
- `doc_scraper.py:detect_language()` - Better heuristics

---

### Issue 7: Language Stats Wrong in Architecture
**File:** `output/httpx/references/codebase_analysis/ARCHITECTURE.md`
**Lines:** 11-13

**Problem:**
```markdown
- Python: 1 files  ← Should be "54 files"
- Shell: 1 files   ← Should be "6 files"
```

**Root Cause:** Aggregation logic counting file types instead of files.

**Fix Required:**
Fix language counting in architecture generation.

**Files to Modify:**
- `unified_skill_builder.py:_generate_codebase_analysis_references()`

---

### Issue 8: API Reference Section Incomplete
**File:** `output/httpx/SKILL.md`
**Lines:** 145-157

**Problem:**
Only shows `test_main.py` as example, then cuts off with "---".

Should link to all 54 API reference modules.

**Fix Required:**
Generate proper API reference index with links.

**Files to Modify:**
- `unified_skill_builder.py:_synthesize_docs_github()` - Add API index

---

## 📝 Implementation Phases

### Phase 1: Fix AI Enhancement (30 min)
**Priority:** P0 - Blocks all AI improvements

**Tasks:**
1. Fix `utils.py` to not skip index.md files
2. Or rename reference files to avoid "index.md"
3. Verify enhancement reads all 30KB of references
4. Test enhancement actually updates SKILL.md

**Test:**
```bash
skill-seekers enhance output/httpx/ --mode local
# Should show: "Total size: ~30,000 characters"
# Should update SKILL.md successfully
```

---

### Phase 2: Fix Content Synthesis (90 min)
**Priority:** P0 - Core functionality

**Tasks:**
1. Rewrite `_synthesize_docs_github()` to truly merge
2. Add section-by-section merging logic
3. Include GitHub metadata in intro
4. Merge "When to Use" sections
5. Combine quick reference sections
6. Add API reference index with all modules
7. Fix "httpx_docs" → "httpx" replacement
8. Deduplicate examples

**Test:**
```bash
skill-seekers unified --config configs/httpx_comprehensive.json
wc -l output/httpx/SKILL.md  # Should be 300-400 lines
grep "httpx_docs" output/httpx/SKILL.md  # Should return nothing
```

---

### Phase 3: Fix Content Formatting (60 min)
**Priority:** P0 - Makes output usable

**Tasks:**
1. Fix pattern extraction to format properly
2. Add `_format_pattern()` method with structure
3. Break long lines into readable format
4. Add proper parameter formatting
5. Fix code block language detection

**Test:**
```bash
# Check pattern readability
head -100 output/httpx/SKILL.md
# Should see nicely formatted patterns, not walls of text
```

---

### Phase 4: Fix Data Accuracy (45 min)
**Priority:** P1 - Quality polish

**Tasks:**
1. Fix language statistics aggregation
2. Complete API reference section
3. Improve language tag detection

**Test:**
```bash
# Check accuracy
grep "Python: " output/httpx/references/codebase_analysis/ARCHITECTURE.md
# Should say "54 files" not "1 files"
```

---

## 📊 Success Metrics

### Before Fixes
- Synthesis quality: 3/10
- Content usability: 2/10
- AI enhancement success: 0% (doesn't update file)
- Reference coverage: 43% (skips 57%)

### After Fixes (Target)
- Synthesis quality: 8/10
- Content usability: 9/10
- AI enhancement success: 90%+
- Reference coverage: 100%

### Acceptance Criteria
1. ✅ SKILL.md is 300-400 lines (not 186)
2. ✅ No "httpx_docs" placeholders
3. ✅ Patterns are readable (not walls of text)
4. ✅ AI enhancement reads all 30KB references
5. ✅ AI enhancement successfully updates SKILL.md
6. ✅ No duplicate examples
7. ✅ Correct language tags
8. ✅ Accurate statistics (54 files, not 1)
9. ✅ Complete API reference section
10. ✅ GitHub metadata included (stars, topics)

---

## 🚀 Execution Plan

### Day 1: Fix Blockers
1. Phase 1: Fix AI enhancement (30 min)
2. Phase 2: Fix synthesis (90 min)
3. Test end-to-end (30 min)

### Day 2: Polish Quality
4. Phase 3: Fix formatting (60 min)
5. Phase 4: Fix accuracy (45 min)
6. Final testing (45 min)

**Total estimated time:** ~6 hours

---

## 📌 Notes

### Why This Matters
The infrastructure is excellent, but users will judge based on the final SKILL.md quality. Currently, it's not production-ready.

### Risk Assessment
**Low risk** - All fixes are isolated to specific functions. Won't break existing file organization or C3.x collection.

### Testing Strategy
Test with httpx (current), then validate with:
- React (docs + GitHub)
- Django (docs + GitHub)
- FastAPI (docs + GitHub)

---

**Plan Status:** Ready for implementation
**Estimated Completion:** 2 days (6 hours total work)
