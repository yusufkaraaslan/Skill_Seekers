# How to Upload Skills to Claude

## Quick Answer

**You upload the `.zip` file created by `package_skill.py`**

```bash
# Create the zip file
python3 package_skill.py output/steam-economy/

# This creates: output/steam-economy.zip
# Upload this file to Claude!
```

## What's Inside the Zip?

The `.zip` file contains:

```
steam-economy.zip
├── SKILL.md              ← Main skill file (Claude reads this first)
└── references/           ← Reference documentation
    ├── index.md          ← Category index
    ├── api_reference.md  ← API docs
    ├── pricing.md        ← Pricing docs
    ├── trading.md        ← Trading docs
    └── ...               ← Other categorized docs
```

**Note:** The zip only includes what Claude needs. It excludes:
- `.backup` files
- Build artifacts
- Temporary files

## What Does package_skill.py Do?

The package script:

1. **Finds your skill directory** (e.g., `output/steam-economy/`)
2. **Validates SKILL.md exists** (required!)
3. **Creates a .zip file** with the same name
4. **Includes all files** except backups
5. **Saves to** `output/` directory

**Example:**
```bash
python3 package_skill.py output/steam-economy/

📦 Packaging skill: steam-economy
   Source: output/steam-economy
   Output: output/steam-economy.zip
   + SKILL.md
   + references/api_reference.md
   + references/pricing.md
   + references/trading.md
   + ...

✅ Package created: output/steam-economy.zip
   Size: 14,290 bytes (14.0 KB)
```

## Complete Workflow

### Step 1: Scrape & Build
```bash
python3 doc_scraper.py --config configs/steam-economy.json
```

**Output:**
- `output/steam-economy_data/` (raw scraped data)
- `output/steam-economy/` (skill directory)

### Step 2: Enhance (Recommended)
```bash
python3 enhance_skill_local.py output/steam-economy/
```

**What it does:**
- Analyzes reference files
- Creates comprehensive SKILL.md
- Backs up original to SKILL.md.backup

**Output:**
- `output/steam-economy/SKILL.md` (enhanced)
- `output/steam-economy/SKILL.md.backup` (original)

### Step 3: Package
```bash
python3 package_skill.py output/steam-economy/
```

**Output:**
- `output/steam-economy.zip` ← **THIS IS WHAT YOU UPLOAD**

### Step 4: Upload to Claude
1. Go to Claude (claude.ai)
2. Click "Add Skill" or skill upload button
3. Select `output/steam-economy.zip`
4. Done!

## What Files Are Required?

**Minimum required structure:**
```
your-skill/
└── SKILL.md          ← Required! Claude reads this first
```

**Recommended structure:**
```
your-skill/
├── SKILL.md          ← Main skill file (required)
└── references/       ← Reference docs (highly recommended)
    ├── index.md
    └── *.md          ← Category files
```

**Optional (can add manually):**
```
your-skill/
├── SKILL.md
├── references/
├── scripts/          ← Helper scripts
│   └── *.py
└── assets/           ← Templates, examples
    └── *.txt
```

## File Size Limits

The package script shows size after packaging:
```
✅ Package created: output/steam-economy.zip
   Size: 14,290 bytes (14.0 KB)
```

**Typical sizes:**
- Small skill: 5-20 KB
- Medium skill: 20-100 KB
- Large skill: 100-500 KB

Claude has generous size limits, so most documentation-based skills fit easily.

## Quick Reference

### Package a Skill
```bash
python3 package_skill.py output/steam-economy/
```

### Package Multiple Skills
```bash
# Package all skills in output/
for dir in output/*/; do
  if [ -f "$dir/SKILL.md" ]; then
    python3 package_skill.py "$dir"
  fi
done
```

### Check What's in a Zip
```bash
unzip -l output/steam-economy.zip
```

### Test a Packaged Skill Locally
```bash
# Extract to temp directory
mkdir temp-test
unzip output/steam-economy.zip -d temp-test/
cat temp-test/SKILL.md
```

## Troubleshooting

### "SKILL.md not found"
```bash
# Make sure you scraped and built first
python3 doc_scraper.py --config configs/steam-economy.json

# Then package
python3 package_skill.py output/steam-economy/
```

### "Directory not found"
```bash
# Check what skills are available
ls output/

# Use correct path
python3 package_skill.py output/YOUR-SKILL-NAME/
```

### Zip is Too Large
Most skills are small, but if yours is large:
```bash
# Check size
ls -lh output/steam-economy.zip

# If needed, check what's taking space
unzip -l output/steam-economy.zip | sort -k1 -rn | head -20
```

Reference files are usually small. Large sizes often mean:
- Many images (skills typically don't need images)
- Large code examples (these are fine, just be aware)

## What Does Claude Do With the Zip?

When you upload a skill zip:

1. **Claude extracts it**
2. **Reads SKILL.md first** - This tells Claude:
   - When to activate this skill
   - What the skill does
   - Quick reference examples
   - How to navigate the references
3. **Indexes reference files** - Claude can search through:
   - `references/*.md` files
   - Find specific APIs, examples, concepts
4. **Activates automatically** - When you ask about topics matching the skill

## Example: Using the Packaged Skill

After uploading `steam-economy.zip`:

**You ask:** "How do I implement microtransactions in my Steam game?"

**Claude:**
- Recognizes this matches steam-economy skill
- Reads SKILL.md for quick reference
- Searches references/microtransactions.md
- Provides detailed answer with code examples

## Summary

**What you need to do:**
1. ✅ Scrape: `python3 doc_scraper.py --config configs/YOUR-CONFIG.json`
2. ✅ Enhance: `python3 enhance_skill_local.py output/YOUR-SKILL/`
3. ✅ Package: `python3 package_skill.py output/YOUR-SKILL/`
4. ✅ Upload: Upload the `.zip` file to Claude

**What you upload:**
- The `.zip` file from `output/` directory
- Example: `output/steam-economy.zip`

**What's in the zip:**
- `SKILL.md` (required)
- `references/*.md` (recommended)
- Any scripts/assets you added (optional)

That's it! 🚀
