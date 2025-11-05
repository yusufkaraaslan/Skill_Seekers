# Your Finance Application Mission

**Mission**: Build a production-grade value investing stock screener with RAG-powered chat interface

**Developer**: Solo, self-taught, AI-assisted coding in Claude Code  
**Timeline**: 4 weeks (following Derek Snow's course structure)  
**Budget**: $50/month for APIs, self-hosted infrastructure

---

## The Complete Stack

### Data Sources
- **SEC EDGAR**: 10-K, 10-Q filings (financial statements)
- **Market Data APIs**: Alpha Vantage, Financial Modeling Prep (FMP)
- **News/Sentiment**: News API, Twitter/X via unofficial APIs
- **Company Data**: Annual reports (PDFs), earnings call transcripts

### Storage Layer
```
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ANALYTICS (OLAP)          VECTOR DB          RELATIONAL    │
│  ┌──────────────┐        ┌──────────────┐   ┌────────────┐ │
│  │   DuckDB     │        │    Chroma    │   │  Postgres  │ │
│  │              │        │              │   │            │ │
│  │ • Filings    │        │ • Embeddings │   │ • Users    │ │
│  │ • Tables     │        │ • Chunks     │   │ • Sessions │ │
│  │ • Metrics    │        │ • Metadata   │   │ • Queries  │ │
│  │ • Time-      │        │              │   │            │ │
│  │   series     │        │              │   │            │ │
│  └──────────────┘        └──────────────┘   └────────────┘ │
│        ↓                        ↓                   ↓       │
│  Parquet files           ChromaDB local      pgvector ext  │
│  (800MB/100 co)          (2GB/10M embed)     (metadata)    │
└─────────────────────────────────────────────────────────────┘
```

### Processing & Query Layer
```
┌─────────────────────────────────────────────────────────────┐
│                  QUERY & PROCESSING LAYER                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  INGESTION            RAG QUERY           TEXT-TO-SQL       │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐ │
│  │ PDF Extract  │   │ Hybrid       │   │ DSPy-Optimized │ │
│  │ (Gemini 2.5) │   │ Retrieval    │   │ Prompts        │ │
│  │              │   │              │   │                │ │
│  │ • Download   │   │ • BM25       │   │ • Schema-aware │ │
│  │ • Tables     │   │ • Semantic   │   │ • Validation   │ │
│  │ • Chunk      │   │ • Rerank     │   │ • Explain      │ │
│  │ • Embed      │   │ • Dedupe     │   │                │ │
│  └──────────────┘   └──────────────┘   └────────────────┘ │
│        ↓                    ↓                     ↓         │
│  sentence-            FAISS + RRF           DuckDB SQL     │
│  transformers         (sub-100ms)           (< 50ms)       │
└─────────────────────────────────────────────────────────────┘
```

### Application Layer
```
┌─────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  BACKEND                  FRONTEND            DEPLOYMENT    │
│  ┌──────────────┐       ┌──────────────┐   ┌────────────┐ │
│  │   FastAPI    │       │    React     │   │   Docker   │ │
│  │              │  ◀──▶ │   or Svelte  │   │            │ │
│  │ • REST API   │  WS   │              │   │ • Backend  │ │
│  │ • WebSockets │       │ • Chat UI    │   │ • Chroma   │ │
│  │ • Auth       │       │ • Screener   │   │ • DuckDB   │ │
│  │ • Rate       │       │ • Portfolio  │   │            │ │
│  │   limiting   │       │   Tracker    │   │            │ │
│  └──────────────┘       └──────────────┘   └────────────┘ │
│        ↓                        ↓                   ↓       │
│  uvicorn (ASGI)         Vite build          Docker Compose│
│  Pydantic validation    TailwindCSS         (dev + prod)  │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Features

### 1. Stock Screening (Value Investing)

**Criteria** (Benjamin Graham / Warren Buffett style):
- P/E ratio < 15 (undervalued)
- P/B ratio < 1.5 (trading below book value)
- ROE > 15% (profitable business)
- Debt-to-Equity < 0.5 (financially stable)
- Free Cash Flow positive (generates cash)
- Dividend yield > 2% (shareholder returns)

**Implementation**:
```sql
-- Generated by text_to_sql_query tool
SELECT 
    ticker,
    company_name,
    pe_ratio,
    pb_ratio,
    roe,
    debt_to_equity,
    fcf,
    dividend_yield,
    
    -- Value score (weighted)
    (
        CASE WHEN pe_ratio < 15 THEN 2 ELSE 0 END +
        CASE WHEN pb_ratio < 1.5 THEN 2 ELSE 0 END +
        CASE WHEN roe > 0.15 THEN 2 ELSE 0 END +
        CASE WHEN debt_to_equity < 0.5 THEN 1 ELSE 0 END +
        CASE WHEN fcf > 0 THEN 1 ELSE 0 END +
        CASE WHEN dividend_yield > 0.02 THEN 1 ELSE 0 END
    ) AS value_score
    
FROM company_metrics
WHERE value_score >= 6  -- At least 6/9 points
ORDER BY value_score DESC, pe_ratio ASC
LIMIT 20;
```

---

### 2. RAG-Powered Chat Interface

**User Queries**:
- "What are TSLA's main revenue sources?"
- "Summarize AAPL's risks from latest 10-K"
- "Compare NVDA and AMD gross margins"
- "Find undervalued semiconductor stocks"

**Hybrid Retrieval Pipeline**:
```
User Query: "What are TSLA's main revenue sources?"
    ↓
1. BM25 Search (lexical)
   → Keywords: "revenue", "sources", "TSLA"
   → Top 50 chunks
    ↓
2. Semantic Search (ANN)
   → Embed query with sentence-transformers
   → FAISS nearest neighbors
   → Top 50 chunks
    ↓
3. Reciprocal Rank Fusion (RRF)
   → Merge BM25 + semantic results
   → Score = 1/(k + rank_bm25) + 1/(k + rank_semantic)
   → Top 20 chunks
    ↓
4. Cross-Encoder Reranking
   → Score query-chunk relevance with BERT
   → Reorder by relevance
   → Top 10 chunks
    ↓
5. Deduplication
   → Remove chunks with cosine similarity > 0.95
   → Final 8 chunks
    ↓
6. Synthesis (Claude 3.5 Sonnet)
   → Context: 8 chunks + metadata (source, page)
   → Prompt: "Answer based ONLY on provided context. Cite sources."
   → Response: "TSLA's main revenue sources are..."
```

---

### 3. Portfolio Monitoring

**Real-Time Tracking**:
- Current holdings (ticker, shares, cost basis)
- Market value vs. book value
- Dividend income (projected annual)
- Portfolio metrics (total return, Sharpe ratio)

**Alerts**:
- Price drops > 10% (buying opportunity)
- New 10-K/Q filed (update analysis)
- Value score changes (e.g., P/E drops below 15)

---

## Data Flow Architecture

### Ingestion Flow
```
SEC EDGAR
    ↓
1. discover_sec_filing("TSLA", "10-K", 2024)
    → filing_url
    ↓
2. ingest_sec_filing(filing_url, "TSLA", extract_tables=True)
    → Download PDF (8.2 MB)
    → Extract tables with Gemini 2.5 Flash (18 tables, $0.021)
    → Chunk (section-aware, 300 tokens/chunk, 421 chunks)
    → Embed (sentence-transformers, 421 embeddings)
    → Store in DuckDB (filings, tables, chunks)
    → Store in Chroma (embeddings, metadata)
    ↓
3. validate_chunk_quality("sec_filings_tsla")
    → Quality score: 94% ✅
    → Issues: 2 chunks missing metadata (fixed)
    ↓
READY FOR QUERY
```

### Query Flow
```
User: "What's TSLA revenue growth?"
    ↓
1. Classify query type
    → SQL query (numerical data)
    ↓
2. text_to_sql_query("What's TSLA revenue growth?", schema_path)
    → SQL: SELECT year, revenue FROM filings WHERE ticker='TSLA' ORDER BY year
    ↓
3. Execute SQL (DuckDB)
    → Results: [
        {"year": 2022, "revenue": 81.5B},
        {"year": 2023, "revenue": 96.8B},
        {"year": 2024, "revenue": 113.2B}
    ]
    ↓
4. Synthesize response (Claude)
    → "TSLA revenue grew from $81.5B (2022) → $113.2B (2024), 
       a 39% increase over 2 years. Source: 10-K filings."
    ↓
User sees answer with sources ✅
```

---

## Cost Model

### API Costs (Monthly)

| Service | Usage | Cost |
|---------|-------|------|
| **Gemini 2.5 Flash** | 50 filings × $0.02 | $1.00 |
| **Embedding (sentence-transformers)** | Self-hosted | $0.00 |
| **Claude 3.5 Sonnet** | 500 queries × $0.01 | $5.00 |
| **Alpha Vantage API** | Free tier (500 calls/day) | $0.00 |
| **News API** | Free tier (100 calls/day) | $0.00 |
| **TOTAL** | | **$6.00/mo** |

**Budget**: $50/month → $44/month headroom for growth

### Infrastructure Costs (Self-Hosted)

| Component | Storage | Cost |
|-----------|---------|------|
| **DuckDB** | 800 MB (100 companies, 3 years) | $0.00 |
| **Chroma** | 2 GB (10M embeddings) | $0.00 |
| **Postgres** | 100 MB (user data) | $0.00 |
| **TOTAL** | ~3 GB disk | **$0.00** |

**Deployment**: Docker Compose on personal laptop or $5/mo VPS

---

## Success Metrics

### Week 1: Data Pipeline
- ✅ Ingest 5 companies (FAANG)
- ✅ 100% chunk quality score
- ✅ DuckDB + Chroma operational
- ✅ Total cost < $0.50

### Week 2: Query Layer
- ✅ Text-to-SQL works (90% accuracy on test queries)
- ✅ RAG retrieval quality > 85%
- ✅ Query latency < 200ms (p95)

### Week 3: Application
- ✅ FastAPI backend deployed
- ✅ React frontend (basic chat UI)
- ✅ WebSocket real-time updates

### Week 4: Production
- ✅ 20+ companies in database
- ✅ Value screener returns accurate results
- ✅ Portfolio tracking working
- ✅ Total monthly cost < $10

---

## Tech Stack Justification (Mental Models Applied)

### DuckDB (OLAP)
**First Principles**: Need fast analytics on time-series financial data  
**Why**: Columnar storage, vectorized execution, embedded (no server)  
**Alternative**: ClickHouse (overkill), Postgres (row-based, slower)

### Chroma (Vector DB)
**First Principles**: Need fast semantic search on 10M+ embeddings  
**Why**: Easy setup, self-hosted, fast enough (<100ms)  
**Alternative**: Qdrant (faster but $50/mo), Pinecone (managed, expensive)

### sentence-transformers (Embeddings)
**First Principles**: Need accurate embeddings, self-hosted  
**Why**: Free, good quality, runs on CPU  
**Alternative**: OpenAI embeddings ($0.0001/1K tokens = $10/10M embeddings)

### Gemini 2.5 Flash (Table Extraction)
**First Principles**: Need structured data from PDFs  
**Why**: Cheapest multimodal model ($0.02/filing), good accuracy  
**Alternative**: GPT-4V ($0.10/filing = 5x more expensive)

### FastAPI (Backend)
**First Principles**: Need async Python API with WebSockets  
**Why**: Fast, native async/await, Pydantic validation  
**Alternative**: Django (overkill), Flask (no async WebSockets)

### React (Frontend)
**First Principles**: Need reactive UI with real-time updates  
**Why**: Large ecosystem, good for chat interfaces  
**Alternative**: Svelte (smaller bundle, fewer libraries)

---

## Key Constraints

### Time Constraints
- Solo developer → 10-15 hours/week
- 4-week timeline → ~50 total hours
- Must follow Derek Snow's course structure

### Budget Constraints
- APIs: $50/month max
- Prefer self-hosted (DuckDB, Chroma, sentence-transformers)
- Avoid managed services until scale demands it

### Technical Constraints
- No ML training (use pre-trained models)
- No complex infrastructure (Docker Compose max)
- No stateful multi-step agents (use workflows)

---

## Next Steps

1. **Read**: [08-snow-course-architecture.md](08-snow-course-architecture.md) - Map this stack to Derek Snow's 5 sessions
2. **Build**: [09-custom-mcp-tools.md](09-custom-mcp-tools.md) - Implement finance-specific MCP tools
3. **Deploy**: [10-agents-for-finance.md](10-agents-for-finance.md) - Create specialized agents
4. **Execute**: [11-immediate-next-steps.md](11-immediate-next-steps.md) - Start building now

---

**Mission Status**: Clearly defined ✅  
**Stack**: Validated with mental models ✅  
**Budget**: Under control ($6/mo) ✅  
**Timeline**: Realistic (4 weeks) ✅

**Ready to build!** 🚀
