# MCP Test Script - Run After Claude Code Restart

**Instructions:** After restarting Claude Code, copy and paste each command below one at a time.

---

## Test 1: List Available Configs
```
List all available configs
```

**Expected Result:**
- Shows 7 configurations
- godot, react, vue, django, fastapi, kubernetes, steam-economy-complete

**Result:**
- [ ] Pass
- [ ] Fail

---

## Test 2: Validate Config
```
Validate configs/react.json
```

**Expected Result:**
- Shows "Config is valid"
- Displays base_url, max_pages, rate_limit

**Result:**
- [ ] Pass
- [ ] Fail

---

## Test 3: Generate New Config
```
Generate config for Tailwind CSS at https://tailwindcss.com/docs with description "Tailwind CSS utility-first framework" and max pages 100
```

**Expected Result:**
- Creates configs/tailwind.json
- Shows success message

**Verify with:**
```bash
ls configs/tailwind.json
cat configs/tailwind.json
```

**Result:**
- [ ] Pass
- [ ] Fail

---

## Test 4: Validate Generated Config
```
Validate configs/tailwind.json
```

**Expected Result:**
- Shows config is valid
- Displays configuration details

**Result:**
- [ ] Pass
- [ ] Fail

---

## Test 5: Estimate Pages (Quick)
```
Estimate pages for configs/react.json with max discovery 50
```

**Expected Result:**
- Completes in 20-40 seconds
- Shows discovered pages count
- Shows estimated total

**Result:**
- [ ] Pass
- [ ] Fail
- Time taken: _____ seconds

---

## Test 6: Small Scrape Test (5 pages)
```
Scrape docs using configs/kubernetes.json with max 5 pages
```

**Expected Result:**
- Creates output/kubernetes_data/ directory
- Creates output/kubernetes/ skill directory
- Generates SKILL.md
- Completes in 30-60 seconds

**Verify with:**
```bash
ls output/kubernetes/SKILL.md
ls output/kubernetes/references/
wc -l output/kubernetes/SKILL.md
```

**Result:**
- [ ] Pass
- [ ] Fail
- Time taken: _____ seconds

---

## Test 7: Package Skill
```
Package skill at output/kubernetes/
```

**Expected Result:**
- Creates output/kubernetes.zip
- Completes in < 5 seconds
- File size reasonable (< 5 MB for 5 pages)

**Verify with:**
```bash
ls -lh output/kubernetes.zip
unzip -l output/kubernetes.zip
```

**Result:**
- [ ] Pass
- [ ] Fail

---

## Test 8: Error Handling - Invalid Config
```
Validate configs/nonexistent.json
```

**Expected Result:**
- Shows clear error message
- Does not crash
- Suggests checking file path

**Result:**
- [ ] Pass
- [ ] Fail

---

## Test 9: Error Handling - Invalid URL
```
Generate config for BadTest at not-a-url
```

**Expected Result:**
- Shows error about invalid URL
- Does not create config file
- Does not crash

**Result:**
- [ ] Pass
- [ ] Fail

---

## Test 10: Medium Scrape Test (20 pages)
```
Scrape docs using configs/react.json with max 20 pages
```

**Expected Result:**
- Creates output/react/ directory
- Generates comprehensive SKILL.md
- Creates multiple reference files
- Completes in 1-3 minutes

**Verify with:**
```bash
ls output/react/SKILL.md
ls output/react/references/
cat output/react/references/index.md
```

**Result:**
- [ ] Pass
- [ ] Fail
- Time taken: _____ minutes

---

## Summary

**Total Tests:** 10
**Passed:** _____
**Failed:** _____

**Overall Status:** [ ] All Pass / [ ] Some Failures

---

## Quick Verification Commands (Run in Terminal)

```bash
# Navigate to repository
cd /mnt/1ece809a-2821-4f10-aecb-fcdf34760c0b/Git/Skill_Seekers

# Check created configs
echo "=== Created Configs ==="
ls -la configs/tailwind.json 2>/dev/null || echo "Not created"

# Check created skills
echo ""
echo "=== Created Skills ==="
ls -la output/kubernetes/SKILL.md 2>/dev/null || echo "Not created"
ls -la output/react/SKILL.md 2>/dev/null || echo "Not created"

# Check created packages
echo ""
echo "=== Created Packages ==="
ls -lh output/kubernetes.zip 2>/dev/null || echo "Not created"

# Check reference files
echo ""
echo "=== Reference Files ==="
ls output/kubernetes/references/ 2>/dev/null | wc -l || echo "0"
ls output/react/references/ 2>/dev/null | wc -l || echo "0"

# Summary
echo ""
echo "=== Test Summary ==="
echo "Config created: $([ -f configs/tailwind.json ] && echo '✅' || echo '❌')"
echo "Kubernetes skill: $([ -f output/kubernetes/SKILL.md ] && echo '✅' || echo '❌')"
echo "React skill: $([ -f output/react/SKILL.md ] && echo '✅' || echo '❌')"
echo "Kubernetes.zip: $([ -f output/kubernetes.zip ] && echo '✅' || echo '❌')"
```

---

## Cleanup After Testing (Optional)

```bash
# Remove test artifacts
rm -f configs/tailwind.json
rm -rf output/tailwind*
rm -rf output/kubernetes*
rm -rf output/react_data/

echo "✅ Test cleanup complete"
```

---

## Notes

- All tests should work with Claude Code MCP integration
- If any test fails, note the error message
- Performance times may vary based on network and system

---

**Status:** [ ] Not Started / [ ] In Progress / [ ] Completed

**Tested By:** ___________

**Date:** ___________

**Claude Code Version:** ___________
