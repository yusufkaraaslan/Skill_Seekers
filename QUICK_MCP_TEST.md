# Quick MCP Test - After Restart

**Just say to Claude Code:** "Run the MCP tests from MCP_TEST_SCRIPT.md"

Or copy/paste these commands one by one:

---

## Quick Test Sequence (Copy & Paste Each Line)

```
List all available configs
```

```
Validate configs/react.json
```

```
Generate config for Tailwind CSS at https://tailwindcss.com/docs with max pages 50
```

```
Estimate pages for configs/react.json with max discovery 30
```

```
Scrape docs using configs/kubernetes.json with max 5 pages
```

```
Package skill at output/kubernetes/
```

---

## Verify Results (Run in Terminal)

```bash
cd /mnt/1ece809a-2821-4f10-aecb-fcdf34760c0b/Git/Skill_Seekers
ls configs/tailwind.json
ls output/kubernetes/SKILL.md
ls output/kubernetes.zip
echo "✅ All tests complete!"
```

---

**That's it!** All 6 core tests in ~3-5 minutes.
