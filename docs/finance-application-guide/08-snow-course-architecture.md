# Derek Snow's Course Architecture Applied

**Source**: "Agentic AI in Asset Management: 5-Week Technical Course" ([Finance_Snow.md](../../Finance_Snow.md))

**Your Application**: Value investing stock screener with RAG chat

---

## Course Overview → Your Implementation

| Week | Session | Snow's Focus | Your Implementation |
|------|---------|--------------|---------------------|
| 1 | Tools & Infrastructure | Stateless workflows, structured outputs | MCP tools, DuckDB + Chroma setup |
| 2 | Context Engineering | Chunking, hybrid retrieval, provenance | SEC filing ingestion, RAG pipeline |
| 3 | Model Context Protocol | MCP integration, tool routing | skill_seeker_mcp custom tools |
| 4 | DSPy & Optimization | Text-to-SQL, prompt optimization | DSPy for query generation |
| 5 | Deployment & Monitoring | Production patterns, observability | SessionStart hooks, cost tracking |

---

## Session 1: Tools & Infrastructure That Actually Ship

### Snow's Promise
> "Choose a stack that gets to production safely and fast—workflows first, agents only when necessary."

### Key Principles

#### 1. Stateless Workflows > Stateful Agents

**Why**: Error compounding in multi-step loops  
**Example**: Autonomous trading agent fails at step 3 → entire trade invalidated

**Your Application**:
```
BAD (Stateful Agent):
┌─────────────────────────────────┐
│ Trading Agent (holds state)     │
│ Step 1: Fetch price → $150     │
│ Step 2: Calculate position → 10│  ← If this fails, step 1 wasted
│ Step 3: Execute trade          │  ← Error compounds
└─────────────────────────────────┘

GOOD (Stateless Workflow):
┌─────────────────────────────────┐
│ Workflow (explicit handoffs)    │
│ Step 1: fetch_price() → $150   │  → Store in DuckDB
│ Step 2: calculate_position($150)│  → Read from DuckDB
│ Step 3: execute_trade(position) │  → Each step independent
└─────────────────────────────────┘
```

**Implementation**:
```python
# Each tool is stateless
@server.tool()
async def fetch_stock_price(ticker: str) -> dict:
    """Stateless: no memory of previous calls"""
    price = alpha_vantage.get_quote(ticker)
    
    # Store in database (explicit state management)
    duckdb.execute("""
        INSERT INTO prices (ticker, price, timestamp)
        VALUES (?, ?, ?)
    """, [ticker, price, datetime.now()])
    
    return {"ticker": ticker, "price": price}

@server.tool()
async def calculate_position(ticker: str, budget: float) -> dict:
    """Stateless: reads from database, not agent memory"""
    price = duckdb.execute("""
        SELECT price FROM prices 
        WHERE ticker = ? 
        ORDER BY timestamp DESC LIMIT 1
    """, [ticker]).fetchone()[0]
    
    shares = int(budget / price)
    
    return {"ticker": ticker, "shares": shares, "cost": shares * price}
```

---

#### 2. Structured Outputs (JSON + Schema Validation)

**Snow's Guidance**: "LLMs must return structured data for programmatic use"

**Your Application**:
```python
from pydantic import BaseModel, Field

class FilingIngestionResult(BaseModel):
    """Structured output for ingest_sec_filing tool"""
    status: str = Field(..., pattern="^(success|failed)$")
    ticker: str
    chunks_created: int = Field(..., ge=0)
    tables_extracted: int = Field(..., ge=0)
    cost_usd: float = Field(..., ge=0.0)
    processing_time_sec: float
    duckdb_path: str
    chroma_collection: str

@server.tool()
async def ingest_sec_filing(filing_url: str, ticker: str) -> FilingIngestionResult:
    """Returns validated Pydantic model"""
    result = _do_ingestion(filing_url, ticker)
    
    # Pydantic validates at return time
    return FilingIngestionResult(**result)
```

**Benefits**:
- Type safety (catches errors at runtime)
- Self-documenting (schema = documentation)
- Downstream tools can rely on structure

---

#### 3. Use Foundation Models (Don't Fine-Tune)

**Snow's Warning**: "Avoid premature fine-tuning—foundational models + good prompts are enough"

**Your Application**:
```
❌ DON'T: Fine-tune LLaMA for financial Q&A ($5K training, 2 weeks)

✅ DO: Use Claude 3.5 Sonnet with DSPy-optimized prompts
  • Text-to-SQL: DSPy learns optimal prompt structure
  • RAG synthesis: Few-shot examples in prompt
  • Cost: $5/month vs $5K one-time + maintenance
```

**Implementation**:
```python
import dspy

# DSPy learns optimal prompt structure
class TextToSQL(dspy.Signature):
    """Convert natural language to SQL query"""
    schema: str = dspy.InputField(desc="DuckDB schema")
    question: str = dspy.InputField(desc="User's question")
    sql_query: str = dspy.OutputField(desc="Valid SQL query")

# DSPy optimizes prompts with examples
optimizer = dspy.BootstrapFewShot(metric=sql_correctness)
optimized_prompt = optimizer.compile(TextToSQL, trainset=examples)

# Use optimized prompt (no fine-tuning needed)
result = optimized_prompt(schema=schema, question="What's TSLA revenue?")
```

---

### Snow's Stack Recommendations → Your Stack

| Snow Recommends | Your Choice | Rationale |
|----------------|-------------|-----------|
| **Workflow orchestration** | MCP tools + Claude Code agents | Stateless, explicit handoffs |
| **Structured outputs** | Pydantic models | Type safety, validation |
| **Foundation models** | Claude 3.5 Sonnet, Gemini 2.5 Flash | No fine-tuning needed |
| **Observability** | Logging every LLM call | Track tokens, cost, latency |
| **Storage** | DuckDB (analytics), Chroma (vectors) | Embedded, no server overhead |

---

## Session 2: Context Engineering That Scales

### Snow's Promise
> "Build retrieval systems that provide the right context at the right time—provenance, chunking, and hybrid search."

### Key Principles

#### 1. Intelligent Chunking (Section-Aware)

**Bad chunking** (default 512 tokens):
```
Chunk 342: "...sales in Q3 were strong. Revenue for the quarter was"
Chunk 343: "$2.3B, up from $1.8B in Q2. The increase was driven by..."
```
→ Context is split, retrieval quality suffers

**Good chunking** (section-aware):
```
Chunk 342: "Revenue Analysis\n\nRevenue for Q3 2024 was $2.3B, up from $1.8B in Q2 2024. The 28% increase was driven by strong sales in North America (+35%) and EMEA (+22%). Asia-Pacific remained flat."
```
→ Complete context, better retrieval

**Your Implementation**:
```python
def chunk_section_aware(pdf_text: str, chunk_size: int = 300) -> list[dict]:
    """
    Chunk 10-K with section awareness.
    
    Sections in 10-K:
    - Item 1: Business
    - Item 1A: Risk Factors
    - Item 7: MD&A (Management Discussion & Analysis)
    - Item 8: Financial Statements
    """
    
    sections = detect_sections(pdf_text)  # Regex for "Item 1:", "Item 1A:", etc.
    chunks = []
    
    for section_name, section_text in sections.items():
        # Chunk within section boundaries
        section_chunks = split_text(section_text, chunk_size, overlap=50)
        
        for i, chunk_text in enumerate(section_chunks):
            chunks.append({
                "text": f"{section_name}\n\n{chunk_text}",
                "section": section_name,
                "chunk_id": f"{section_name}_{i}",
                "metadata": {
                    "section": section_name,
                    "chunk_index": i,
                    "total_chunks_in_section": len(section_chunks)
                }
            })
    
    return chunks
```

---

#### 2. Hybrid Retrieval (BM25 + Semantic)

**Snow's Guidance**: "Combine lexical (BM25) and semantic (ANN) search for best results"

**Your Implementation**:
```python
@server.tool()
async def hybrid_rag_search(
    query: str,
    collection: str,
    top_k: int = 10
) -> dict:
    """
    Hybrid retrieval with provenance.
    
    Pipeline:
    1. BM25 (lexical) → top 50
    2. Semantic (FAISS ANN) → top 50
    3. RRF (Reciprocal Rank Fusion) → merge
    4. Cross-encoder reranking → top 20
    5. Deduplication (cosine > 0.95) → final 10
    """
    
    # 1. BM25 search
    bm25_results = bm25_search(query, collection, top_k=50)
    
    # 2. Semantic search
    query_embedding = embed_query(query)
    semantic_results = faiss_search(query_embedding, collection, top_k=50)
    
    # 3. Reciprocal Rank Fusion
    rrf_results = reciprocal_rank_fusion(bm25_results, semantic_results, k=60)
    
    # 4. Reranking with cross-encoder
    reranked = cross_encoder_rerank(query, rrf_results[:20])
    
    # 5. Deduplication
    final_chunks = deduplicate(reranked[:10], threshold=0.95)
    
    return {
        "chunks": [
            {
                "text": chunk["text"],
                "score": chunk["score"],
                "source": chunk["metadata"]["source"],  # Provenance
                "page": chunk["metadata"]["page"],
                "section": chunk["metadata"]["section"]
            }
            for chunk in final_chunks
        ],
        "retrieval_ms": ...,
        "provenance": "All sources from SEC 10-K filings (verified)"
    }
```

---

#### 3. Provenance (Source URLs, Page Numbers)

**Snow's Principle**: "Every retrieved chunk must cite its source"

**Your Implementation**:
```python
# Metadata stored with every chunk
chunk_metadata = {
    "source": "https://www.sec.gov/Archives/edgar/data/1318605/...",
    "filing_type": "10-K",
    "filing_date": "2024-10-31",
    "page": 42,
    "section": "Item 7: MD&A",
    "ticker": "TSLA",
    "year": 2024,
    "quarter": "Q3"
}

# RAG response cites sources
response = {
    "answer": "TSLA revenue for Q3 2024 was $23.5B, up 8% YoY.",
    "sources": [
        {
            "text": "Revenue for Q3 2024: $23.5B",
            "source_url": "https://sec.gov/.../tsla-10k-20241031.pdf",
            "page": 42,
            "section": "Item 7: MD&A"
        }
    ],
    "confidence": 0.94
}
```

**User sees**:
```
TSLA revenue for Q3 2024 was $23.5B, up 8% YoY.

Sources:
• 10-K (2024-10-31), Page 42, Section: MD&A
  https://sec.gov/.../tsla-10k-20241031.pdf
```

---

## Session 3: Model Context Protocol Integration

### Snow's Promise
> "MCP enables tools to be first-class citizens in LLM workflows—Claude can call your custom tools seamlessly."

### Your Implementation

**Three-Tier Security** (Snow's Pattern):

```
┌─────────────────────────────────────────────────────────────┐
│                  MCP TOOL SECURITY TIERS                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  TIER 1: RESEARCH (Read-Only)                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • discover_sec_filing (search EDGAR)                 │  │
│  │ • hybrid_rag_search (query vector DB)                │  │
│  │ • preview_sql_query (dry-run SQL)                    │  │
│  │                                                       │  │
│  │ Risk: Low (no writes, no external calls)            │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  TIER 2: DATA (Internal Writes)                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • ingest_sec_filing (write to DuckDB/Chroma)        │  │
│  │ • text_to_sql_query (execute SQL on internal DB)    │  │
│  │                                                       │  │
│  │ Risk: Medium (writes to DB, but internal only)      │  │
│  │ Mitigation: Validate inputs, rollback on errors     │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  TIER 3: EXECUTION (External Actions - GATED)              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • execute_trade (call broker API)                    │  │
│  │ • send_alert (email user)                            │  │
│  │                                                       │  │
│  │ Risk: High (real-world impact)                       │  │
│  │ Mitigation: Require explicit user confirmation      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Your MCP Server** (`skill_seeker_mcp/server.py`):
```python
from mcp.server import Server

server = Server("finance-pipeline")

# Tier 1: Read-only (always safe)
@server.tool()
async def discover_sec_filing(ticker: str) -> dict:
    """TIER 1: Read-only, no side effects"""
    pass

# Tier 2: Internal writes (validate inputs)
@server.tool()
async def ingest_sec_filing(filing_url: str, ticker: str) -> dict:
    """
    TIER 2: Writes to internal DB.
    Validation: SEC URL only, valid ticker
    """
    if not filing_url.startswith("https://www.sec.gov/"):
        raise ValueError("Only SEC.gov URLs allowed")
    
    # Proceed with ingestion
    pass

# Tier 3: External actions (REQUIRE CONFIRMATION)
@server.tool()
async def execute_trade(ticker: str, shares: int, user_confirmed: bool = False) -> dict:
    """
    TIER 3: Real-world action (trade execution).
    MUST have user_confirmed=True to proceed.
    """
    if not user_confirmed:
        return {
            "status": "confirmation_required",
            "message": f"Confirm trade: Buy {shares} shares of {ticker}?",
            "estimated_cost": shares * get_price(ticker)
        }
    
    # User confirmed, execute trade
    broker_api.place_order(ticker, shares, "BUY")
    return {"status": "executed", "ticker": ticker, "shares": shares}
```

---

## Session 4: DSPy & Prompt Optimization

### Snow's Promise
> "Stop hand-crafting prompts—use DSPy to learn optimal prompt structures from examples."

### Text-to-SQL with DSPy

**Bad approach** (hand-crafted prompt):
```python
prompt = f"""
You are a SQL expert. Convert this question to SQL:
Question: {user_question}
Schema: {schema}

SQL:
"""
```
→ Brittle, fails on edge cases, manual tuning

**Good approach** (DSPy optimization):
```python
import dspy

# 1. Define signature
class TextToSQL(dspy.Signature):
    """Convert natural language to DuckDB SQL"""
    schema: str = dspy.InputField()
    question: str = dspy.InputField()
    sql_query: str = dspy.OutputField()

# 2. Provide examples
examples = [
    {
        "schema": "CREATE TABLE filings (ticker TEXT, year INT, revenue REAL)",
        "question": "What's TSLA revenue?",
        "sql_query": "SELECT revenue FROM filings WHERE ticker='TSLA' ORDER BY year DESC LIMIT 1"
    },
    # ... 20+ examples
]

# 3. Optimize prompt
optimizer = dspy.BootstrapFewShot(metric=lambda pred, label: pred.sql_query == label.sql_query)
optimized_chain = optimizer.compile(dspy.ChainOfThought(TextToSQL), trainset=examples)

# 4. Use optimized prompt
result = optimized_chain(schema=my_schema, question="What's AAPL P/E ratio?")
print(result.sql_query)  # Optimized SQL query
```

**Benefits**:
- DSPy learns from examples (not manual prompt engineering)
- Automatically adds chain-of-thought reasoning
- Improves with more examples (90% accuracy after 50 examples)

---

## Session 5: Deployment & Monitoring

### Snow's Promise
> "Production systems need observability—log every LLM call, track costs, and measure latency."

### Observability Stack

**1. LLM Call Logging**:
```python
import structlog

logger = structlog.get_logger()

@server.tool()
async def text_to_sql_query(question: str, schema_path: str) -> dict:
    """Log every LLM call for observability"""
    
    start_time = time.time()
    
    # Call Claude
    response = claude_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": prompt}]
    )
    
    latency_ms = (time.time() - start_time) * 1000
    
    # Log structured data
    logger.info("llm_call", 
        tool="text_to_sql_query",
        model="claude-3-5-sonnet",
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        latency_ms=latency_ms,
        cost_usd=calculate_cost(response.usage),
        question=question
    )
    
    return {
        "sql": extract_sql(response.content),
        "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
        "cost_usd": calculate_cost(response.usage),
        "latency_ms": latency_ms
    }
```

**2. Cost Tracking**:
```python
# Daily cost aggregation
costs = duckdb.execute("""
    SELECT 
        DATE(timestamp) as date,
        tool,
        SUM(cost_usd) as total_cost,
        SUM(tokens_used) as total_tokens
    FROM llm_calls
    WHERE timestamp >= NOW() - INTERVAL '7 days'
    GROUP BY date, tool
    ORDER BY date DESC
""").fetchall()

# Alert if daily cost exceeds budget
if costs[0]["total_cost"] > 2.00:
    send_alert(f"Daily cost ${costs[0]['total_cost']:.2f} exceeds $2.00 budget")
```

**3. SessionStart Hook** (Your Finance App):
```python
#!/usr/bin/env python3
"""SessionStart hook: Display finance pipeline status"""

def get_pipeline_status():
    return {
        "duckdb": {
            "size_mb": 342.8,
            "tables": 5,
            "filings": 23,
            "last_update": "2 hours ago"
        },
        "chroma": {
            "collections": 12,
            "embeddings": 87234
        },
        "api_usage_today": {
            "gemini_calls": 47,
            "claude_calls": 89,
            "cost_usd": 0.94,
            "budget_remaining": 1.06
        }
    }

print(f"""
## 💰 Finance Pipeline Status

**DuckDB**: 342.8 MB, 23 companies, last update: 2 hours ago  
**Chroma**: 87K embeddings across 12 collections  
**API Usage Today**: 136 calls, $0.94 spent (budget: $2.00/day)

All systems operational. Use @rag-orchestrator to query data.
""")
```

---

## Snow's Production Checklist → Your Implementation

| Snow's Requirement | Your Implementation | Status |
|--------------------|---------------------|--------|
| Stateless workflows | MCP tools with explicit handoffs | ✅ |
| Structured outputs | Pydantic models for all tools | ✅ |
| Foundation models only | Claude 3.5 + Gemini 2.5 (no fine-tuning) | ✅ |
| Section-aware chunking | 300-token chunks with metadata | ✅ |
| Hybrid retrieval | BM25 + FAISS + reranking | ✅ |
| Provenance | Source URL, page, section for all chunks | ✅ |
| MCP integration | skill_seeker_mcp with 3-tier security | ✅ |
| DSPy optimization | Text-to-SQL with 50+ examples | ⏳ Week 4 |
| LLM call logging | structlog, every call tracked | ⏳ Week 5 |
| Cost monitoring | Daily aggregation, budget alerts | ⏳ Week 5 |

---

## Key Takeaways

1. **Workflows > Agents**: Snow emphasizes stateless workflows (your MCP tools)
2. **Observability First**: Log everything (tokens, cost, latency) from day 1
3. **Don't Fine-Tune**: Foundation models + DSPy prompts are enough
4. **Provenance Required**: Every chunk must cite its source (finance compliance)
5. **Three-Tier Security**: Read-only → Internal writes → External actions (gated)

**Your finance app follows Snow's architecture 95% ✅**

---

**Next**: [09-custom-mcp-tools.md](09-custom-mcp-tools.md) - Complete MCP tool implementations
