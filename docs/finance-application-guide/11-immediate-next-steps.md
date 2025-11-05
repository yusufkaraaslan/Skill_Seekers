# Immediate Next Steps (2-Hour Setup)

**Goal**: Get your finance application from zero to first working query in 2 hours.

This is your **Week 0 sprint**—the foundation for Derek Snow's 4-week course implementation.

---

## Prerequisites Checklist

**Before you start**, verify you have:

- ✅ **macOS** with Python 3.10+ installed
  - Check: `python3 --version` (should show 3.10 or higher)
- ✅ **Claude Code** installed (your primary IDE)
  - Download: https://claude.ai/code
- ✅ **Git** for version control
  - Check: `git --version`
- ✅ **50 GB disk space** (DuckDB + Chroma + PDFs)
- ✅ **API keys ready**:
  - Anthropic API key (Claude Sonnet): https://console.anthropic.com/
  - Google AI API key (Gemini 2.5 Flash): https://aistudio.google.com/
  - SEC EDGAR User-Agent email: your-email@example.com

---

## Timeline Overview

```
Hour 1: Environment Setup + First Ingestion
├─ 0:00-0:15  Create project structure
├─ 0:15-0:30  Install dependencies
├─ 0:30-0:45  Configure MCP server
├─ 0:45-1:00  Test first SEC filing ingestion
└─ 1:00       ✅ Milestone: TSLA 10-K ingested

Hour 2: First Query + Validation
├─ 1:00-1:15  Create finance agents
├─ 1:15-1:30  Test SQL query
├─ 1:30-1:45  Test RAG retrieval
├─ 1:45-2:00  Run health diagnostics
└─ 2:00       ✅ Milestone: End-to-end workflow working
```

---

## Hour 1: Environment Setup

### Step 1: Create Project Structure (5 min)

```bash
# Navigate to your workspace
cd ~/Code/skill-test

# Create finance app directory
mkdir finance-screener
cd finance-screener

# Create directory structure
mkdir -p {data,logs,configs,scripts}
mkdir -p .claude/agents
mkdir -p skill_seeker_mcp/finance_tools

# Initialize git
git init
echo "data/" >> .gitignore
echo "logs/" >> .gitignore
echo ".env" >> .gitignore
echo "*.duckdb*" >> .gitignore
echo "chroma/" >> .gitignore
```

**Verify**:
```bash
tree -L 2
# Should show: data/, logs/, configs/, scripts/, .claude/, skill_seeker_mcp/
```

---

### Step 2: Install Dependencies (10 min)

Create `requirements.txt`:

```bash
cat > requirements.txt << 'EOF'
# Core dependencies
anthropic>=0.18.0
google-generativeai>=0.3.0
duckdb>=0.9.0
chromadb>=0.4.0
sentence-transformers>=2.2.0
pydantic>=2.0.0

# MCP server
mcp>=0.9.0

# Data processing
PyMuPDF>=1.23.0        # PDF extraction
beautifulsoup4>=4.12.0  # HTML parsing (for SEC filings)
requests>=2.31.0

# RAG optimization
rank-bm25>=0.2.2       # BM25 lexical search
faiss-cpu>=1.7.4       # Semantic search (or faiss-gpu if you have GPU)

# Text-to-SQL
dspy-ai>=2.0.0

# Monitoring
structlog>=23.0.0
python-dotenv>=1.0.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
EOF
```

Install:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (this will take ~5 minutes)
pip install -r requirements.txt

# Verify installation
python3 -c "import duckdb, chromadb, anthropic; print('✅ Core dependencies installed')"
```

**If errors occur**:
- **Apple Silicon Macs**: Use `faiss-cpu` (not `faiss-gpu`)
- **PyMuPDF fails**: Try `pip install --upgrade pip` first
- **ChromaDB fails**: May need `pip install pysqlite3-binary`

---

### Step 3: Configure Environment Variables (5 min)

Create `.env` file with API keys:

```bash
cat > .env << 'EOF'
# Anthropic (Claude Sonnet for synthesis)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Google AI (Gemini 2.5 Flash for table extraction)
GOOGLE_API_KEY=AIzaSy...

# SEC EDGAR User-Agent (required by SEC)
SEC_USER_AGENT=YourAppName/1.0 (your-email@example.com)

# Database paths
DUCKDB_PATH=data/finance.duckdb
CHROMA_PATH=data/chroma

# Cost tracking
MONTHLY_BUDGET_USD=50.0
EOF
```

**Get your API keys**:
1. **Anthropic**: https://console.anthropic.com/settings/keys
   - Create new key, copy `sk-ant-api03-...`
2. **Google AI**: https://aistudio.google.com/app/apikey
   - Create API key, copy `AIzaSy...`
3. **SEC User-Agent**: Use format `AppName/Version (email@example.com)`
   - SEC requires this to avoid blocking

Load environment:

```bash
source .env
echo $ANTHROPIC_API_KEY  # Should display your key
```

---

### Step 4: Initialize Databases (10 min)

Create DuckDB schema:

```bash
cat > data/schema.sql << 'EOF'
-- Filings metadata table
CREATE TABLE IF NOT EXISTS filings (
    id INTEGER PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    filing_url VARCHAR NOT NULL,
    filing_type VARCHAR,  -- 10-K, 10-Q, 8-K
    filing_date DATE,
    fiscal_year INTEGER,
    num_chunks INTEGER,
    num_tables INTEGER,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, filing_url)
);

-- Text chunks table
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    filing_url VARCHAR NOT NULL,
    chunk_index INTEGER,
    text VARCHAR,
    section VARCHAR,  -- e.g., "Item 1A: Risk Factors"
    page INTEGER,
    metadata JSON,
    FOREIGN KEY (ticker, filing_url) REFERENCES filings(ticker, filing_url)
);

-- Extracted tables table
CREATE TABLE IF NOT EXISTS tables (
    id INTEGER PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    filing_url VARCHAR NOT NULL,
    table_index INTEGER,
    table_data JSON,  -- Structured table as JSON
    caption VARCHAR,
    page INTEGER,
    FOREIGN KEY (ticker, filing_url) REFERENCES filings(ticker, filing_url)
);

-- Error logging table
CREATE TABLE IF NOT EXISTS error_log (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    component VARCHAR,  -- e.g., "ingestion", "sql_query"
    error VARCHAR,
    context JSON
);

-- Cost tracking table
CREATE TABLE IF NOT EXISTS api_costs (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    service VARCHAR,  -- "anthropic", "google"
    operation VARCHAR,  -- "table_extraction", "text_to_sql"
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),
    ticker VARCHAR
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_filings_ticker ON filings(ticker);
CREATE INDEX IF NOT EXISTS idx_chunks_ticker ON chunks(ticker);
CREATE INDEX IF NOT EXISTS idx_chunks_section ON chunks(section);
CREATE INDEX IF NOT EXISTS idx_tables_ticker ON tables(ticker);
EOF
```

Initialize DuckDB:

```bash
# Create database with schema
python3 << 'PYTHON'
import duckdb

conn = duckdb.connect("data/finance.duckdb")
with open("data/schema.sql") as f:
    conn.execute(f.read())
    
print("✅ DuckDB initialized at data/finance.duckdb")
conn.close()
PYTHON
```

Initialize Chroma:

```bash
# Create Chroma database
python3 << 'PYTHON'
import chromadb

client = chromadb.PersistentClient(path="data/chroma")
print(f"✅ ChromaDB initialized at data/chroma")
print(f"Collections: {len(client.list_collections())}")
PYTHON
```

**Verify**:
```bash
ls -lh data/
# Should show: finance.duckdb, chroma/, schema.sql
```

---

### Step 5: Create MCP Tools (15 min)

Copy the tools from `09-custom-mcp-tools.md` into your project:

**File**: `skill_seeker_mcp/finance_tools/discovery.py`

```python
# Copy the discover_sec_filing function from 09-custom-mcp-tools.md
# (Full implementation provided there)
```

**File**: `skill_seeker_mcp/finance_tools/ingestion.py`

```python
# Copy the ingest_sec_filing function from 09-custom-mcp-tools.md
# (Full implementation provided there)
```

**File**: `skill_seeker_mcp/finance_tools/query.py`

```python
# Copy preview_sql_query and hybrid_rag_search from 09-custom-mcp-tools.md
# (Full implementation provided there)
```

**File**: `skill_seeker_mcp/finance_tools/monitoring.py`

```python
# Copy diagnose_pipeline_health from 09-custom-mcp-tools.md
# (Full implementation provided there)
```

**File**: `skill_seeker_mcp/server.py`

```python
from mcp.server import Server
from finance_tools.discovery import discover_sec_filing
from finance_tools.ingestion import ingest_sec_filing
from finance_tools.query import preview_sql_query, hybrid_rag_search
from finance_tools.monitoring import diagnose_pipeline_health

server = Server("finance-mcp")

# Tools are auto-registered via @server.tool() decorators

if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    asyncio.run(stdio_server(server))
```

**Configure MCP in Claude Code**:

Add to `~/.claude/mcp_config.json`:

```json
{
  "mcpServers": {
    "finance-screener": {
      "command": "/Users/docravikumar/Code/skill-test/finance-screener/venv/bin/python",
      "args": ["-m", "skill_seeker_mcp.server"],
      "cwd": "/Users/docravikumar/Code/skill-test/finance-screener"
    }
  }
}
```

**Restart Claude Code** to load MCP server.

---

### Step 6: Test First Ingestion (15 min)

**In Claude Code**, test the MCP tools:

```
User: "Ingest TSLA 10-K from 2024"

Expected Claude Response (using agents):
@financial-data-engineer will handle this...

1. Discovering TSLA 10-K 2024...
   Tool: discover_sec_filing("TSLA", "10-K", 2024)
   Result: ✅ Found at https://sec.gov/Archives/...

2. Estimating cost...
   Tool: estimate_api_cost(filing_url, extract_tables=True)
   Result: $0.021 (Gemini table extraction)

3. Ingesting filing...
   Tool: ingest_sec_filing(filing_url, "TSLA", extract_tables=True)
   Progress: Downloading PDF... Extracting tables... Chunking... Embedding... Storing...
   Result: ✅ Ingested TSLA 10-K (421 chunks, 18 tables, $0.021, 31.2s)

4. Validating pipeline...
   Tool: diagnose_pipeline_health()
   Result: ✅ Pipeline healthy (1 filing, 421 chunks, 0 errors)

✅ TSLA 10-K 2024 successfully ingested!
```

**If errors**:
- **SEC 403 Forbidden**: Check `SEC_USER_AGENT` in `.env` (must include email)
- **Gemini quota exceeded**: Set `extract_tables=False` in tool call
- **DuckDB locked**: Close any DuckDB connections (`conn.close()`)

---

## Hour 2: First Queries

### Step 7: Create Finance Agents (15 min)

Copy YAML content from `10-agents-for-finance.md` to `.claude/agents/`:

```bash
# Create agent files
touch .claude/agents/financial-data-engineer.md
touch .claude/agents/sql-analyst.md
touch .claude/agents/rag-orchestrator.md
touch .claude/agents/finance-screener.md

# Copy YAML from 10-agents-for-finance.md into each file
```

**Restart Claude Code** to load agents.

**Verify agents loaded**:

```
User: "@finance-screener hello"

Expected response:
Hello! I'm your finance screener. I can help you:
- Ingest SEC filings (10-K, 10-Q, 8-K)
- Analyze financial metrics (revenue, P/E ratio, growth)
- Compare companies
- Retrieve qualitative insights (risks, competitive advantages)

What would you like to analyze today?
```

---

### Step 8: Test SQL Query (15 min)

```
User: "@sql-analyst What's TSLA revenue growth over the last 3 years?"

Expected flow:
1. Load schema from data/schema.sql
2. Generate SQL with DSPy:
   SELECT filing_date, revenue, 
          (revenue - LAG(revenue) OVER (ORDER BY filing_date)) / LAG(revenue) * 100 AS growth_pct
   FROM filings
   WHERE ticker = 'TSLA'
   ORDER BY filing_date
3. Validate (dry_run=True) → safety_check: passed
4. Execute (dry_run=False)
5. Format results:

   TSLA Revenue Growth:
   - 2021: $53.8B
   - 2022: $81.5B (+51.4%)
   - 2023: $96.8B (+18.8%)
   - 2024: $96.8B (0.0%)
```

**If no results**:
- Check: `SELECT * FROM filings WHERE ticker = 'TSLA'` returns rows
- Verify ingestion completed in Step 6

---

### Step 9: Test RAG Retrieval (15 min)

```
User: "@rag-orchestrator What are TSLA's main risks?"

Expected flow:
1. Query: "TSLA main risks"
2. Collection: "sec_filings_tsla"
3. Hybrid search:
   - BM25 (lexical) → 50 candidates
   - Semantic (FAISS) → 50 candidates
   - RRF fusion → 20 candidates
   - Cross-encoder rerank → 10 final chunks
4. Synthesize answer with provenance:

   TSLA's Main Risks (from 10-K 2024):

   1. Production Scaling (Item 1A, page 42):
      "Our ability to achieve production targets depends on successful scaling..."
      Source: [10-K 2024, page 42](https://sec.gov/...)

   2. Regulatory Changes (Item 1A, page 47):
      "Changes to EV tax credits could materially impact demand..."
      Source: [10-K 2024, page 47](https://sec.gov/...)

   Quality: avg_score=0.84, retrieval_ms=150
```

---

### Step 10: Run Health Diagnostics (15 min)

```
User: "@financial-data-engineer check pipeline health"

Expected output:
Tool: diagnose_pipeline_health()

Pipeline Health Report:
✅ Overall Health: Healthy

Components:
- DuckDB: ✅ Healthy
  - Size: 45.2 MB
  - Tables: 5 (filings, chunks, tables, error_log, api_costs)
  - Filings: 1 (TSLA)
  - Last write: 2024-01-15 14:32:10

- ChromaDB: ✅ Healthy
  - Collections: 1 (sec_filings_tsla)
  - Total embeddings: 421

- Gemini API: ✅ Healthy
  - Quota remaining: 9,750 requests
  - Quota reset: 23 hours

Errors (last 24h): 0

Recommendations: None
```

---

## Success Validation

After 2 hours, you should have:

✅ **Infrastructure**:
- DuckDB database with schema (`data/finance.duckdb`)
- ChromaDB initialized (`data/chroma`)
- MCP server running in Claude Code

✅ **Data**:
- 1 SEC filing ingested (TSLA 10-K 2024)
- 421 chunks embedded
- 18 tables extracted

✅ **Agents**:
- 4 finance agents loaded in Claude Code
- Delegation working (@finance-screener → specialists)

✅ **Queries**:
- SQL query working (revenue growth)
- RAG retrieval working (risk factors)
- Health diagnostics passing

✅ **Cost**:
- API spend: ~$0.021 (well under $50/month budget)

---

## Troubleshooting

### Issue: MCP tools not appearing in Claude Code

**Solution**:
1. Check `~/.claude/mcp_config.json` has correct paths
2. Verify `python` command points to venv: `which python`
3. Restart Claude Code completely (quit and reopen)
4. Check logs: `~/.claude/logs/mcp-server-finance-screener.log`

### Issue: SEC filing download fails (403 Forbidden)

**Solution**:
1. Add valid email to `SEC_USER_AGENT` in `.env`
2. Format: `"MyApp/1.0 (your-email@example.com)"`
3. Reload environment: `source .env`

### Issue: Gemini API quota exceeded

**Solution**:
1. Check quota: https://aistudio.google.com/app/apikey
2. Temporary fix: Set `extract_tables=False` in `ingest_sec_filing` calls
3. Free tier: 1,500 requests/day (resets daily)

### Issue: ChromaDB "no such table" error

**Solution**:
1. Install: `pip install pysqlite3-binary`
2. Delete and recreate: `rm -rf data/chroma && python3 -c "import chromadb; chromadb.PersistentClient(path='data/chroma')"`

---

## Next Steps

After completing this 2-hour setup:

1. **Week 1**: Ingest 5 companies → [12-weekly-milestones.md](12-weekly-milestones.md)
2. **Week 2**: Build text-to-SQL with DSPy optimization
3. **Week 3**: Build RAG chat UI with WebSockets
4. **Week 4**: Scale to 20+ companies, optimize costs

**Continue to**: [12-weekly-milestones.md](12-weekly-milestones.md) for detailed 4-week plan.
