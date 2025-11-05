# ELI10: What is Skill_Seekers?

**Audience**: 10-year-old or someone brand new to the project  
**Goal**: Understand what Skill_Seekers does in a simple, story-driven way

---

## The Story of Sam and the Magic Documentation Factory

Imagine Sam, a curious developer who finds a messy online documentation site and wants a friendly Claude skill that can answer questions about it. Sam uses Skill_Seekers like a small factory: feed it the docs, and it makes a neat Claude skill.

### Step 1: Get Ready (Setup)

Sam creates a Python virtual environment and installs requirements so tools behave the same on every computer.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Ask "How Big Is It?" (Estimation)

Before scraping, Sam runs a quick estimator to see how many pages and how long it might take. This avoids surprises.

```bash
python3 cli/estimate_pages.py configs/react.json
```

### Step 3: Scrape the Docs (Data Collection)

Sam runs the scraper with a config that tells it where the docs are and what selectors to use. The scraper visits pages, extracts titles, text, and code blocks, and saves structured JSON under `output/`.

```bash
python3 cli/doc_scraper.py --config configs/react.json
# or multi-source
python3 cli/unified_scraper.py --config configs/react_unified.json
```

### Step 4: Make It Smart (Enhancement)

The tool automatically:
- Categorizes pages (getting_started, api, etc.)
- Detects code languages
- Extracts common patterns
- Can run a local enhancement step that rewrites and improves the skill content so answers become clearer

```bash
python3 cli/doc_scraper.py --config configs/react.json --enhance-local
```

### Step 5: Find Problems Early (Quality Assurance)

Sam runs conflict detection to compare docs vs. code (if analyzing a GitHub repo too). The system flags:
- "Missing in docs"
- "Missing in code"
- Signature mismatches
- Description mismatches

```bash
python3 demo_conflicts.py
```

### Step 6: Package and Share (Distribution)

When satisfied, Sam packages the generated skill into a `.zip` ready for upload to Claude, or uses the repo's MCP server to integrate tools for automation.

```bash
python3 cli/package_skill.py output/react/
./setup_mcp.sh
python3 skill_seeker_mcp/server.py
```

### Step 7: Test and Iterate (Validation)

Sam runs the test suite to ensure changes didn't break anything, and re-scrapes or adjusts selectors if content quality needs improvement.

```bash
python3 cli/run_tests.py
pytest tests/ -v
```

---

## Why This Feels Like Magic

The repo acts like a **copying-and-organizing robot**:
- It reads pages
- Groups them
- Cleans examples
- Builds a friendly instruction manual (`SKILL.md`) that Claude can use to answer questions

Sam only needs to:
1. Point it at sources
2. Tweak a few settings
3. The robot does the heavy sorting and polishing

---

## Quick Checklist

- ✅ Create venv, install deps
- ✅ Run estimate_pages
- ✅ Pick or create a config (selectors matter)
- ✅ Scrape (sync or unified)
- ✅ Enhance (local or API)
- ✅ Run conflict detection
- ✅ Package and upload
- ✅ Run tests and iterate

---

## The User Journey

**From**: Messy docs scattered across a website  
**To**: A tidy, testable Claude skill

**Time**: Fast (minutes to hours, not days)  
**Control**: Repeatable and configurable  
**Quality**: Tested with 299 tests (100% pass rate)

---

## For Your Finance Application

Instead of **documentation sites**, you'll feed Skill_Seekers:
- SEC filings (10-K, 10-Q PDFs)
- Financial API documentation (Alpha Vantage, FMP)
- Vector database docs (Chroma, Qdrant)
- SQL database docs (DuckDB, Postgres)

**Output**: Skills that teach Claude how to work with your finance stack.

---

**Next**: [02-understanding-agents.md](02-understanding-agents.md) - How Claude agents actually work
