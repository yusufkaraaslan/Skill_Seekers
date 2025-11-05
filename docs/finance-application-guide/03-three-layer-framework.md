# The 3-Layer Framework: How Tools, Skills, and Agents Work Together

**Core Concept**: Claude Code agents are NOT executable—they're declarative. The 3-layer framework makes them work.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                             │
│              "@hunt-orchestrator build React skill"              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 3: AGENT ORCHESTRATION                  │
│                  (.claude/agents/hunt-orchestrator.md)           │
│                                                                  │
│  Agent Declaration (YAML/Markdown):                             │
│  • Role: Mission orchestration with contingencies               │
│  • Tools Allowed: execute_with_fallback, pre_flight_check       │
│  • Delegates To: []                                             │
│  • Decision Rules: When to use this agent                       │
│                                                                  │
│  ➜ Claude READS this, doesn't EXECUTE it                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 2: SKILL TEACHING                       │
│          (.claude/skills/hunt-orchestrator-skill/SKILL.md)       │
│                                                                  │
│  Teaching Document (Markdown):                                  │
│  • HOW to use tools (examples, patterns, workflows)            │
│  • WHEN to use tools (triggers, conditions)                    │
│  • WHAT results to expect (outputs, edge cases)                │
│                                                                  │
│  Example:                                                       │
│  "When user wants multi-source scraping:                       │
│   1. Call pre_flight_check(config)                            │
│   2. If safe_to_proceed: true → execute_with_fallback         │
│   3. Handle results (success vs degraded)"                     │
│                                                                  │
│  ➜ Claude LEARNS from this how to use tools                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 1: MCP TOOLS                            │
│                  (skill_seeker_mcp/server.py)                    │
│                                                                  │
│  Executable Python Functions:                                   │
│                                                                  │
│  @server.tool()                                                │
│  async def execute_with_fallback(config: str) -> dict:        │
│      fallbacks = [unified, github, docs, cache]               │
│      for tool in fallbacks:                                   │
│          try: return tool(config)                             │
│          except: continue                                     │
│      return {"error": "all failed"}                           │
│                                                                  │
│  ➜ Claude CALLS this via MCP protocol                          │
│  ➜ Runs in YOUR environment (not Claude's)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                       YOUR ENVIRONMENT                           │
│              (Python, DuckDB, Chroma, APIs, etc.)               │
│                                                                  │
│  • Tool executes: python3 cli/unified_scraper.py               │
│  • Accesses: DuckDB, Chroma, file system, network              │
│  • Returns: Structured JSON to Claude                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: MCP Tools (The Executors)

**What they are**: Python functions that run in your environment  
**Who calls them**: Claude (via Model Context Protocol)  
**What they do**: Actual work (scrape, query DB, call APIs)

### Example: Finance Data Ingestion Tool

```python
# skill_seeker_mcp/server.py

from mcp.server import Server
import duckdb
import chromadb

server = Server("finance-pipeline")

@server.tool()
async def ingest_sec_filing(
    filing_url: str,
    ticker: str,
    extract_tables: bool = True
) -> dict:
    """
    Ingest SEC filing (10-K/Q) into DuckDB + Chroma.
    
    Pipeline:
    1. Download PDF from EDGAR
    2. Extract tables (Gemini 2.5 Flash if extract_tables=True)
    3. Chunk (section-aware, 300 tokens/chunk)
    4. Embed (sentence-transformers)
    5. Store (DuckDB + Chroma)
    
    Args:
        filing_url: EDGAR URL
        ticker: Stock ticker (e.g., "TSLA")
        extract_tables: Use Gemini to extract tables (costs ~$0.02)
    
    Returns:
        {
            "status": "success" | "failed",
            "chunks_created": int,
            "tables_extracted": int,
            "duckdb_path": "data/finance.duckdb",
            "chroma_collection": "sec_filings_tsla",
            "cost_usd": float,
            "processing_time_sec": float
        }
    """
    
    # Actual implementation
    result = {
        "status": "success",
        "chunks_created": 342,
        "tables_extracted": 15,
        "duckdb_path": f"data/finance.duckdb",
        "chroma_collection": f"sec_filings_{ticker.lower()}",
        "cost_usd": 0.018,
        "processing_time_sec": 23.4
    }
    
    return result
```

### Tool Registration with MCP

```python
# This happens automatically when you use @server.tool()
# MCP exposes this to Claude Code via JSON-RPC

TOOL_DEFINITION = {
    "name": "ingest_sec_filing",
    "description": "Ingest SEC filing (10-K/Q) into DuckDB + Chroma",
    "input_schema": {
        "type": "object",
        "properties": {
            "filing_url": {"type": "string", "description": "EDGAR URL"},
            "ticker": {"type": "string", "description": "Stock ticker"},
            "extract_tables": {"type": "boolean", "default": True}
        },
        "required": ["filing_url", "ticker"]
    }
}
```

---

## Layer 2: Skills (The Teachers)

**What they are**: Markdown documents teaching Claude how to use tools  
**Who reads them**: Claude (when you attach them or use `@skill`)  
**What they do**: Provide context, examples, patterns, workflows

### Example: Finance Ingestion Skill

```markdown
# Finance Data Ingestion — SEC Filings to RAG Pipeline

**When to use**: User wants to add SEC filings (10-K, 10-Q) to the database for analysis.

---

## Available Tools

### `ingest_sec_filing`

**Purpose**: Download, extract, chunk, embed, and store SEC filings

**Inputs**:
- `filing_url` (required): EDGAR URL to SEC filing PDF
- `ticker` (required): Stock ticker symbol
- `extract_tables` (optional, default=true): Use Gemini to extract financial tables

**Outputs**:
```json
{
  "status": "success",
  "chunks_created": 342,
  "tables_extracted": 15,
  "cost_usd": 0.018,
  "processing_time_sec": 23.4
}
```

**Cost**: ~$0.02 per 10-K if extracting tables, free otherwise

---

## Workflow Examples

### Example 1: Ingest Single Filing

**User**: "Ingest TSLA 10-K from Q3 2024"

**Claude's Workflow**:
1. Search EDGAR for TSLA 10-K filed in Q3 2024
2. Get filing URL: `https://www.sec.gov/Archives/edgar/data/1318605/...`
3. Call tool:
   ```
   ingest_sec_filing(
       filing_url="https://sec.gov/...",
       ticker="TSLA",
       extract_tables=True
   )
   ```
4. Report results:
   - ✅ 342 chunks created
   - ✅ 15 financial tables extracted
   - 💰 Cost: $0.018
   - ⏱️ Time: 23.4 seconds

### Example 2: Batch Ingestion (Multiple Years)

**User**: "Ingest all AAPL 10-Ks from 2020-2024"

**Claude's Workflow**:
1. Search EDGAR for 5 filings
2. Call tool 5 times (one per year)
3. Track total cost and time
4. Report summary:
   - ✅ 5 filings processed
   - ✅ 1,823 total chunks
   - ✅ 67 tables extracted
   - 💰 Total cost: $0.09
   - ⏱️ Total time: 118 seconds

---

## Error Handling

### Common Errors

**Error**: `"EDGAR rate limit exceeded"`
**Fix**: Wait 1 minute, retry with exponential backoff

**Error**: `"PDF extraction failed (corrupted file)"`
**Fix**: Try alternate filing source or manual download

**Error**: `"Gemini API quota exceeded"`
**Fix**: Set `extract_tables=False` for free processing (no table extraction)

---

## Best Practices

1. **Start small**: Ingest 1-2 filings first, verify quality
2. **Monitor costs**: Tables extraction costs money (~$0.02/filing)
3. **Check duplicates**: Tool prevents re-ingesting same filing
4. **Validate results**: Use `@sql-analyst` to query ingested data

---

## Integration with Other Tools

After ingestion, use:
- `@sql-analyst` - Query financial data with text-to-SQL
- `@rag-orchestrator` - Search across all filings
- `monitor_pipeline` - Check database size and health
```

---

## Layer 3: Agents (The Orchestrators)

**What they are**: YAML/Markdown declarations of roles and capabilities  
**Who reads them**: Claude (when you use `@agent-name`)  
**What they do**: Define when to use which tools/skills

### Example: Financial Data Engineer Agent

```yaml
---
name: financial-data-engineer
type: specialist
description: Ingest SEC filings, monitor pipeline, manage data quality. Expert in ETL for finance data.
tools:
  - ingest_sec_filing
  - monitor_pipeline
  - validate_data_quality
  - Bash
  - Read
  - Write
delegates_to: []
---

# Financial Data Engineer

**Role**: Your ETL specialist for SEC filings and financial data

**Mental Models**: First Principles (data quality at source), Systems Thinking (pipeline health)

---

## Capabilities

### Data Ingestion
- Download SEC filings from EDGAR
- Extract financial tables (Gemini 2.5 Flash)
- Chunk with section-awareness (300 tokens/chunk)
- Embed with sentence-transformers
- Store in DuckDB (analytics) + Chroma (vector search)

### Pipeline Monitoring
- Database size and growth
- API quota usage (Gemini, EDGAR)
- Cost tracking (per filing, per day)
- Error rates and failure modes

### Data Quality
- Validate chunk quality (no truncation, proper encoding)
- Check embedding coverage (all chunks embedded)
- Detect duplicates (cosine similarity > 0.95)
- Verify table extraction accuracy

---

## When Claude Uses This Agent

**Trigger phrases**:
- "Ingest SEC filing..."
- "Add 10-K to database..."
- "Download earnings report..."
- "Check pipeline status..."
- "Validate data quality..."

**Workflow**:
1. User requests ingestion
2. Claude reads this agent's capabilities
3. Claude calls appropriate tools (ingest_sec_filing, monitor_pipeline)
4. Agent reports results with cost/time transparency

---

## Decision Rules

**IF** user wants single filing:
→ Call `ingest_sec_filing` once
→ Report: chunks, tables, cost, time

**IF** user wants batch ingestion:
→ Loop: call `ingest_sec_filing` for each filing
→ Track cumulative cost/time
→ Report summary with totals

**IF** ingestion fails:
→ Check error type (rate limit vs. corruption)
→ Suggest mitigation (retry vs. manual download)
→ Log error for debugging

**IF** cost exceeds threshold ($1.00):
→ Warn user before proceeding
→ Offer cheaper alternative (extract_tables=False)

---

## Collaboration

**Delegates to**: (none - specialist agent)

**Works with**:
- `@sql-analyst` - Query ingested data
- `@rag-orchestrator` - Search across filings
- `@finance-screener` - Use data for stock screening

---

## Examples

### Example 1: Simple Ingestion

**User**: "@financial-data-engineer ingest NVDA 10-K Q4 2024"

**Agent Response**:
```
🔍 Searching EDGAR for NVDA 10-K (Q4 2024)...
✅ Found: https://sec.gov/.../nvda-10k-20241231.pdf

📥 Ingesting filing...
  • Downloading PDF (8.2 MB)
  • Extracting 18 financial tables (Gemini 2.5 Flash)
  • Chunking (section-aware, 300 tokens/chunk)
  • Embedding (sentence-transformers)
  • Storing in DuckDB + Chroma

✅ Ingestion complete!
  • Chunks created: 421
  • Tables extracted: 18
  • Cost: $0.021
  • Time: 31.2 seconds
  • Collection: sec_filings_nvda
```

### Example 2: Monitoring

**User**: "@financial-data-engineer check pipeline status"

**Agent Response**:
```
## 💰 Finance Pipeline Status

### DuckDB Analytics Database
- Size: 342.8 MB
- Tables: 5 (filings, tables, chunks, metadata, queries)
- Total rows: 128,431

### Vector Database (Chroma)
- Collections: 12 (one per ticker)
- Total embeddings: 87,234

### API Usage (Today)
- Gemini calls: 47
- EDGAR downloads: 12
- Cost today: $0.94
- Quota remaining: 9,953 (Gemini), unlimited (EDGAR)

### Recent Ingestions (Last 24h)
- TSLA 10-K Q3 2024: ✅ Success (342 chunks)
- AAPL 10-Q Q2 2024: ✅ Success (189 chunks)
- NVDA 10-K Q4 2024: ✅ Success (421 chunks)

All systems operational. 🚀
```

---

## How the 3 Layers Work Together

### User Request Flow

```
User: "@financial-data-engineer ingest TSLA 10-K"
   │
   ▼
[LAYER 3: Agent]
   Claude reads: financial-data-engineer.md
   Sees: tools=[ingest_sec_filing, monitor_pipeline]
   Decides: "I need to use ingest_sec_filing"
   │
   ▼
[LAYER 2: Skill]
   Claude reads: finance-ingestion-skill/SKILL.md
   Learns: How to call ingest_sec_filing
   Sees: Example workflows, error handling
   Prepares: Tool call with correct parameters
   │
   ▼
[LAYER 1: MCP Tool]
   Claude calls: ingest_sec_filing(filing_url, ticker)
   MCP routes to: skill_seeker_mcp/server.py
   Python executes: Download → Extract → Chunk → Embed → Store
   Returns: {"status": "success", "chunks_created": 342, ...}
   │
   ▼
[Claude Synthesis]
   Claude receives: Tool output (JSON)
   Formats: User-friendly response with cost/time
   Returns: "✅ Ingestion complete! 342 chunks, $0.018, 23.4s"
```

---

## Why This Architecture Works

### ✅ Separation of Concerns
- **Tools**: Do the work (Python)
- **Skills**: Teach usage (Markdown)
- **Agents**: Decide when (YAML/MD)
- **Claude**: Orchestrates all three

### ✅ Fallback Logic in Tools (Not Agents)
```python
# ✅ RIGHT: Tool has fallback
@server.tool()
async def hybrid_rag_search(query: str) -> dict:
    try:
        return semantic_search(query)
    except:
        return bm25_search(query)  # Fallback

# ❌ WRONG: Agent can't execute fallback
# Agents are declarations, not code
```

### ✅ Stateless Workflows
- Each tool call is independent
- No hidden state between calls
- Reproducible results (same input → same output)

### ✅ Observability
- Tools log every call (tokens, cost, latency)
- Skills document expected behavior
- Agents declare decision rules
- Transparent to users

---

## Key Takeaways

1. **Agents don't execute** - They declare capabilities
2. **Tools execute** - Python in your environment
3. **Skills teach** - Claude learns patterns from docs
4. **Claude orchestrates** - Reads all three, makes decisions

5. **For your finance app**:
   - Write tools for: ingestion, SQL, RAG, monitoring
   - Write skills for: workflows, patterns, examples
   - Write agents for: coordination, specialization

---

**Next**: [04-mental-models.md](04-mental-models.md) - Applying mental models to tool design
