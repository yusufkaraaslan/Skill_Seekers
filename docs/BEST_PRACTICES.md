# Best Practices for High-Quality Skills

**Target Audience:** Anyone creating Claude skills | Already scraped documentation? Make it better!

**Time:** 5-10 minutes to review | Apply as you build

**Result:** Skills that Claude understands better and activates more reliably

---

## Quick Checklist

Before uploading a skill, check:

- [ ] SKILL.md has clear "When to Use" triggers
- [ ] At least 5 code examples included
- [ ] Prerequisites documented (if any)
- [ ] Troubleshooting section present
- [ ] Quality score 90+ (Grade A)

```bash
# Check your skill quality
skill-seekers quality output/myskill/
```

---

## 1. Structure Your SKILL.md Clearly

### Use Consistent Sections

Claude looks for specific sections to understand your skill:

```markdown
# Skill Name

## Description
Brief explanation of what this skill enables.

## When to Use This Skill
- User asks about [specific topic]
- User needs help with [specific task]
- User mentions [keywords]

## Prerequisites
What needs to be true before using this skill.

## Quick Reference
Most common commands or patterns.

## Detailed Guide
Step-by-step instructions with examples.

## Troubleshooting
Common issues and solutions.
```

### Why This Matters

Claude uses the "When to Use" section to decide if your skill matches the user's question. Vague triggers = skill doesn't activate.

**Bad Example:**
```markdown
## When to Use This Skill
Use this skill for API-related questions.
```

**Good Example:**
```markdown
## When to Use This Skill
- User asks about Steam Inventory API methods
- User needs to implement item drops in a Steam game
- User wants to grant promotional items to players
- User mentions: SteamInventory, GetAllItems, AddPromoItems
```

---

## 2. Include Real Code Examples

Skills with 5+ code examples work significantly better. Claude learns patterns from examples.

### What Works

**Include a variety:**
- Basic usage (getting started)
- Common patterns (day-to-day use)
- Advanced usage (edge cases)
- Error handling (when things go wrong)

**Example from a good SKILL.md:**
```markdown
## Quick Reference

### Get All Items
```cpp
SteamInventoryResult_t resultHandle;
bool success = SteamInventory()->GetAllItems(&resultHandle);
```

### Grant Promotional Items
```cpp
void CInventory::GrantPromoItems()
{
    SteamItemDef_t newItems[2];
    newItems[0] = 110;
    newItems[1] = 111;
    SteamInventory()->AddPromoItems(&s_GenerateRequestResult, newItems, 2);
}
```

### Handle Async Results
```cpp
void OnSteamInventoryResult(SteamInventoryResultReady_t *pResult)
{
    if (pResult->m_result == k_EResultOK) {
        // Process items
    }
}
```
```

### What to Avoid

**Generic placeholder text:**
```markdown
## Quick Reference

*Quick reference patterns will be added as you use the skill.*
```

**Code without context:**
```markdown
`GetAllItems()`
```

---

## 3. Document Prerequisites

Claude can check conditions before proceeding. This prevents errors mid-execution.

### Good Pattern

```markdown
## Before You Start

Make sure you have:
- [ ] Python 3.10+ installed
- [ ] API key set in environment (`export API_KEY=...`)
- [ ] Network access to api.example.com

### Quick Check
```bash
python3 --version  # Should show 3.10+
echo $API_KEY      # Should not be empty
curl api.example.com/health  # Should return 200
```
```

### Why It Matters

Without prerequisites, Claude might:
1. Start a complex workflow
2. Fail halfway through
3. Leave the user with a broken state

With prerequisites, Claude can:
1. Check conditions first
2. Report what's missing
3. Guide the user to fix issues before starting

---

## 4. Add Troubleshooting Sections

Real-world usage hits errors. Document the common ones.

### Template

```markdown
## Troubleshooting

### "Connection refused" error
**Cause:** Service not running or firewall blocking

**Solution:**
1. Check if the service is running: `systemctl status myservice`
2. Verify firewall settings: `sudo ufw status`
3. Test connectivity: `curl -v https://api.example.com`

### "Permission denied" error
**Cause:** Insufficient file permissions

**Solution:**
1. Check file permissions: `ls -la /path/to/file`
2. Fix permissions: `chmod 644 /path/to/file`
3. Verify ownership: `chown user:group /path/to/file`

### "Rate limited" error
**Cause:** Too many API requests

**Solution:**
1. Wait 60 seconds before retrying
2. Implement exponential backoff in your code
3. Consider caching responses
```

### What to Include

- Error message (exact text users see)
- Cause (why it happens)
- Solution (step-by-step fix)
- Prevention (how to avoid it)

---

## 5. Organize Reference Files

The `references/` directory should be easy to navigate.

### Good Structure

```
output/myskill/
├── SKILL.md                    # Main entry point
└── references/
    ├── index.md                # Category overview
    ├── getting_started.md      # Installation, setup
    ├── api_reference.md        # API methods, classes
    ├── guides.md               # How-to tutorials
    └── advanced.md             # Complex scenarios
```

### Category Guidelines

| Category | Contains | Keywords |
|----------|----------|----------|
| getting_started | Installation, setup, quickstart | intro, install, setup, quickstart |
| api_reference | Methods, classes, parameters | api, method, function, class, reference |
| guides | Step-by-step tutorials | guide, tutorial, how-to, example |
| concepts | Architecture, design patterns | concept, overview, architecture |
| advanced | Complex scenarios, internals | advanced, internal, extend |

### Navigation Table in SKILL.md

```markdown
## Navigation

| Topic | File | Description |
|-------|------|-------------|
| Getting Started | references/getting_started.md | Installation and setup |
| API Reference | references/api_reference.md | Complete API documentation |
| Guides | references/guides.md | Step-by-step tutorials |
| Advanced | references/advanced.md | Complex scenarios |
```

---

## 6. Run Quality Checks

Always check quality before uploading:

```bash
# Check quality score
skill-seekers quality output/myskill/

# Expected output:
# ✅ Grade: A (Score: 95)
# ✅ No errors
# ⚠️  1 warning: Consider adding more code examples
```

### Quality Targets

| Grade | Score | Status |
|-------|-------|--------|
| A | 90-100 | Ready to upload |
| B | 80-89 | Good, minor improvements possible |
| C | 70-79 | Review warnings before uploading |
| D | 60-69 | Needs work |
| F | < 60 | Significant issues |

### Common Issues

**"Missing SKILL.md"**
- Run the scraper first
- Or create manually

**"No code examples found"**
- Add code blocks to SKILL.md
- Run enhancement: `python3 cli/enhance_skill_local.py output/myskill/`

**"Generic description"**
- Rewrite "When to Use" section
- Add specific keywords and use cases

---

## 7. Test Your Skill

Before uploading, test with Claude:

### Manual Testing

1. Upload the skill to Claude
2. Ask a question your skill should answer
3. Check if Claude activates the skill
4. Verify the response uses skill content

### Test Questions

For a Steam Inventory skill:
```
"How do I get all items in a player's Steam inventory?"
"What's the API call for granting promotional items?"
"Show me how to handle async inventory results"
```

### What to Look For

**Good activation:**
- Claude references your skill
- Response includes examples from your SKILL.md
- Specific, accurate information

**Poor activation:**
- Claude gives generic answer
- No skill reference
- Information doesn't match your docs

---

## Real-World Example

### Before Improvement

```markdown
# React Skill

## Description
React documentation.

## When to Use
For React questions.

## Quick Reference
See references.
```

**Quality Score:** 45 (Grade F)

### After Improvement

```markdown
# React Skill

## Description
Complete React 18+ documentation including hooks, components, and best practices.

## When to Use This Skill
- User asks about React hooks (useState, useEffect, useContext)
- User needs help with React component lifecycle
- User wants to implement React patterns (render props, HOCs, custom hooks)
- User mentions: React, JSX, virtual DOM, fiber, concurrent mode

## Prerequisites
- Node.js 16+ for development
- Basic JavaScript/ES6 knowledge

## Quick Reference

### useState Hook
```jsx
const [count, setCount] = useState(0);
```

### useEffect Hook
```jsx
useEffect(() => {
  document.title = `Count: ${count}`;
}, [count]);
```

### Custom Hook
```jsx
function useWindowSize() {
  const [size, setSize] = useState({ width: 0, height: 0 });
  useEffect(() => {
    const handleResize = () => {
      setSize({ width: window.innerWidth, height: window.innerHeight });
    };
    window.addEventListener('resize', handleResize);
    handleResize();
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  return size;
}
```

## Troubleshooting

### "Invalid hook call"
**Cause:** Hook called outside component or conditionally

**Solution:**
1. Only call hooks at top level of function components
2. Don't call hooks inside loops or conditions
3. Check for multiple React copies: `npm ls react`
```

**Quality Score:** 94 (Grade A)

---

## Summary

| Practice | Why It Matters | Quick Check |
|----------|---------------|-------------|
| Clear structure | Claude knows where to look | Has all standard sections? |
| Code examples (5+) | Claude learns patterns | Count code blocks |
| Prerequisites | Prevents mid-task failures | Prerequisites section exists? |
| Troubleshooting | Handles real-world errors | Common errors documented? |
| Organized references | Easy navigation | Categories make sense? |
| Quality check | Catches issues early | Score 90+? |
| Testing | Confirms it works | Claude activates skill? |

**Final command before upload:**
```bash
skill-seekers quality output/myskill/
```

That's it! Follow these practices and your skills will work better with Claude.

---

## See Also

- [ENHANCEMENT.md](ENHANCEMENT.md) - AI-powered SKILL.md improvement
- [UPLOAD_GUIDE.md](UPLOAD_GUIDE.md) - How to upload skills to Claude
- [USAGE.md](USAGE.md) - Complete command reference

---

## Contributing

This guide was contributed by the [AI Writing Guide](https://github.com/jmagly/ai-writing-guide) project, which uses Skill Seekers for documentation-to-skill conversion. Best practices here are informed by research on production-grade agentic workflows.

Found an issue or want to improve this guide? PRs welcome!
