# Developer Pain Points → Tool Solutions

**From conversation**: "Assume the role of a developer using AI tools, use your internal knowledge and this repo and apply our mental model framework to create user journeys."

---

## Your Developer Journey: Finance Application

**Who you are**: Solo developer, self-taught with AI-assisted coding  
**Environment**: Claude Code  
**Mission**: Build value investing stock screener with RAG chat interface  
**Stack**: DuckDB (OLAP), Chroma/Qdrant (vector), FastAPI (backend), WebSockets (real-time)

---

## Pain Point Mapping (Beyond Scraping)

### Phase 1: Data Ingestion

#### Pain Point 1: "Where do I even start with SEC filings?"

**Root cause**: No clear path from EDGAR → queryable database

**Mental model**: First Principles (what's the minimal path?)

**Solution: `discover_sec_filing` tool**
```python
@server.tool()
async def discover_sec_filing(
    ticker: str,
    filing_type: str = "10-K",
    year: int = 2024
) -> dict:
    """
    Discover SEC filings without manual EDGAR search.
    
    Returns:
        {
            "filing_url": "https://sec.gov/...",
            "filing_date": "2024-10-31",
            "ticker": "TSLA",
            "type": "10-K",
            "metadata": {...}
        }
    """
    pass
```

**Impact**: User goes from "how do I find filings?" → "here's the URL" in 1 tool call

---

#### Pain Point 2: "I don't know if chunking worked correctly"

**Root cause**: No visibility into chunk quality after ingestion

**Mental model**: Systems Thinking (need feedback loop)

**Solution: `validate_chunk_quality` tool**
```python
@server.tool()
async def validate_chunk_quality(
    collection: str,
    sample_size: int = 10
) -> dict:
    """
    Validate chunk quality after ingestion.
    
    Checks:
    - No truncation mid-sentence
    - Metadata present (source, page, section)
    - Embedding coverage (all chunks embedded)
    - Duplicate detection (cosine sim > 0.95)
    
    Returns:
        {
            "quality_score": 0.92,
            "issues": [
                {"chunk_id": 123, "issue": "missing metadata"},
                {"chunk_id": 456, "issue": "truncated mid-sentence"}
            ],
            "recommendations": ["Re-chunk with larger context window"]
        }
    """
    pass
```

**Impact**: Catch bad chunking BEFORE user sees hallucinations

---

#### Pain Point 3: "Ingestion takes forever, and I don't know why it failed"

**Root cause**: No progress tracking or error visibility

**Mental model**: Second Order Effects (user frustration → abandonment)

**Solution: `monitor_ingestion_progress` tool**
```python
@server.tool()
async def monitor_ingestion_progress(
    job_id: str
) -> dict:
    """
    Real-time ingestion progress tracking.
    
    Returns:
        {
            "status": "in_progress",
            "progress": 0.67,  # 67% complete
            "current_step": "embedding_chunks",
            "eta_seconds": 45,
            "chunks_processed": 342,
            "chunks_total": 512,
            "errors": []
        }
    """
    pass
```

**Impact**: User knows "it's working" vs "it's stuck"

---

### Phase 2: Query & Retrieval

#### Pain Point 4: "RAG returns irrelevant chunks"

**Root cause**: No tuning knobs for retrieval quality

**Mental model**: Inversion (what makes retrieval bad?)

**Solution: `tune_rag_retrieval` tool**
```python
@server.tool()
async def tune_rag_retrieval(
    query: str,
    collection: str,
    top_k: int = 10,
    rerank: bool = True,
    bm25_weight: float = 0.5,
    semantic_weight: float = 0.5
) -> dict:
    """
    Tunable hybrid retrieval with diagnostics.
    
    Returns:
        {
            "chunks": [...],
            "retrieval_quality": {
                "avg_score": 0.84,
                "bm25_contribution": 0.3,
                "semantic_contribution": 0.7,
                "reranking_impact": 0.15
            },
            "recommendations": [
                "Increase semantic_weight to 0.7 for this query type"
            ]
        }
    """
    pass
```

**Impact**: User can debug WHY retrieval is bad and how to fix it

---

#### Pain Point 5: "I don't know if SQL query is correct before running it"

**Root cause**: No preview or validation for text-to-SQL

**Mental model**: Inversion (prevent bad queries)

**Solution: `preview_sql_query` tool**
```python
@server.tool()
async def preview_sql_query(
    natural_language: str,
    schema_path: str,
    dry_run: bool = True
) -> dict:
    """
    Preview SQL before execution (dry-run mode).
    
    Returns:
        {
            "sql": "SELECT revenue FROM filings WHERE ticker='TSLA'",
            "explanation": "Retrieves revenue for Tesla",
            "estimated_rows": 5,
            "estimated_time_ms": 12,
            "potential_issues": [],
            "safety_check": "passed"
        }
    """
    pass
```

**Impact**: User validates SQL BEFORE execution, avoids costly errors

---

### Phase 3: Cost & Performance

#### Pain Point 6: "I don't know how much this will cost until it's too late"

**Root cause**: No cost estimation for Gemini API calls

**Mental model**: Second Order Effects (unexpected costs → budget blown)

**Solution: `estimate_api_cost` tool**
```python
@server.tool()
async def estimate_api_cost(
    operation: str,  # "ingest_filing", "embed_chunks", "extract_tables"
    num_items: int,  # Number of filings, chunks, etc.
    include_tables: bool = True
) -> dict:
    """
    Estimate API costs BEFORE execution.
    
    Returns:
        {
            "estimated_cost_usd": 0.45,
            "breakdown": {
                "gemini_calls": 23,
                "embedding_calls": 512,
                "table_extraction": 15
            },
            "estimated_time_minutes": 8,
            "recommendation": "Safe to proceed" | "Consider batching to reduce cost"
        }
    """
    pass
```

**Impact**: No surprise bills, user controls costs

---

#### Pain Point 7: "My RAG queries are too slow for real-time chat"

**Root cause**: No performance profiling or optimization guidance

**Mental model**: Systems Thinking (identify bottlenecks)

**Solution: `profile_rag_performance` tool**
```python
@server.tool()
async def profile_rag_performance(
    query: str,
    collection: str
) -> dict:
    """
    Profile RAG query performance and suggest optimizations.
    
    Returns:
        {
            "total_time_ms": 2340,
            "breakdown": {
                "embedding_query": 120,
                "vector_search": 1800,  # BOTTLENECK
                "reranking": 350,
                "synthesis": 70
            },
            "bottleneck": "vector_search",
            "optimizations": [
                "Use HNSW index (10x faster)",
                "Reduce top_k from 50 to 20",
                "Cache frequent queries"
            ]
        }
    """
    pass
```

**Impact**: User knows EXACTLY where to optimize (vector search is slow → use HNSW)

---

### Phase 4: Discovery & Learning

#### Pain Point 8: "I don't know which vector database to use"

**Root cause**: No comparison tool for tech stack decisions

**Mental model**: First Principles (evaluate on fundamentals)

**Solution: `compare_vector_databases` tool**
```python
@server.tool()
async def compare_vector_databases(
    requirements: dict  # {"embeddings": 10_000_000, "latency_ms": 100, "budget_usd": 50}
) -> dict:
    """
    Compare vector DBs based on your requirements.
    
    Returns:
        {
            "recommendations": [
                {
                    "name": "Chroma",
                    "score": 0.92,
                    "pros": ["Easy setup", "Self-hosted", "$0/mo"],
                    "cons": ["Slower than Qdrant at 10M+ embeddings"],
                    "estimated_latency_ms": 150,
                    "estimated_cost_usd": 0
                },
                {
                    "name": "Qdrant",
                    "score": 0.95,
                    "pros": ["Fastest", "Scales to 100M+", "Metadata filtering"],
                    "cons": ["Managed = $50/mo", "More complex setup"],
                    "estimated_latency_ms": 80,
                    "estimated_cost_usd": 50
                }
            ],
            "winner": "Qdrant",
            "rationale": "Meets latency requirement (<100ms), worth $50/mo for performance"
        }
    """
    pass
```

**Impact**: User makes informed decisions instead of guessing

---

#### Pain Point 9: "I don't know if my chunking strategy is good"

**Root cause**: No benchmarking tool for RAG quality

**Mental model**: Systems Thinking (measure retrieval quality)

**Solution: `benchmark_rag_quality` tool**
```python
@server.tool()
async def benchmark_rag_quality(
    test_queries: list[str],
    collection: str,
    ground_truth: dict = None  # Optional: known good answers
) -> dict:
    """
    Benchmark RAG quality with test queries.
    
    Returns:
        {
            "avg_retrieval_score": 0.84,
            "queries_tested": 20,
            "results": [
                {
                    "query": "What's TSLA revenue?",
                    "top_chunk_score": 0.92,
                    "relevant_chunks_in_top10": 8,
                    "ground_truth_match": True
                }
            ],
            "recommendations": [
                "Increase chunk size to 500 tokens (better context)",
                "Add section headers to metadata (better filtering)"
            ]
        }
    """
    pass
```

**Impact**: User knows chunking strategy is good BEFORE building whole app

---

### Phase 5: Debugging & Maintenance

#### Pain Point 10: "My pipeline broke and I don't know why"

**Root cause**: No centralized error tracking

**Mental model**: Systems Thinking (need observability)

**Solution: `diagnose_pipeline_health` tool**
```python
@server.tool()
async def diagnose_pipeline_health() -> dict:
    """
    Comprehensive pipeline health check.
    
    Returns:
        {
            "overall_health": "degraded",
            "components": {
                "duckdb": {"status": "healthy", "size_mb": 342, "last_write": "2 mins ago"},
                "chroma": {"status": "healthy", "collections": 12, "embeddings": 87234},
                "gemini_api": {"status": "degraded", "quota_remaining": 234, "quota_reset": "23 hours"},
                "edgar_scraper": {"status": "healthy", "last_success": "5 mins ago"}
            },
            "errors_last_24h": [
                {"timestamp": "2024-11-04 10:30", "component": "gemini_api", "error": "quota exceeded"}
            ],
            "recommendations": [
                "Gemini quota low: disable table extraction until reset",
                "DuckDB size growing: consider archiving old filings"
            ]
        }
    """
    pass
```

**Impact**: User diagnoses issues in 1 tool call instead of 30 mins debugging

---

## Tool Priority Matrix

### Tier 1: Must-Have (Immediate Impact)

| Tool | Pain Point | Impact | Effort |
|------|------------|--------|--------|
| `discover_sec_filing` | "Where to start?" | ⭐⭐⭐⭐⭐ | Low |
| `estimate_api_cost` | "Surprise costs" | ⭐⭐⭐⭐⭐ | Low |
| `diagnose_pipeline_health` | "Pipeline broken" | ⭐⭐⭐⭐⭐ | Medium |
| `preview_sql_query` | "Bad SQL" | ⭐⭐⭐⭐ | Medium |

### Tier 2: High-Value (Week 2)

| Tool | Pain Point | Impact | Effort |
|------|------------|--------|--------|
| `validate_chunk_quality` | "Bad chunks" | ⭐⭐⭐⭐ | Medium |
| `tune_rag_retrieval` | "Irrelevant results" | ⭐⭐⭐⭐ | Medium |
| `profile_rag_performance` | "Slow queries" | ⭐⭐⭐⭐ | Medium |

### Tier 3: Nice-to-Have (Week 3+)

| Tool | Pain Point | Impact | Effort |
|------|------------|--------|--------|
| `compare_vector_databases` | "Which DB?" | ⭐⭐⭐ | Low |
| `benchmark_rag_quality` | "Is chunking good?" | ⭐⭐⭐ | High |
| `monitor_ingestion_progress` | "Is it working?" | ⭐⭐⭐ | High |

---

## Developer Workflow (With Tools)

### Before Tools: Painful Journey

```
1. Google "how to download SEC filings" (30 mins)
2. Manually find EDGAR URL (15 mins)
3. Download PDF, hope it's not corrupted (5 mins)
4. Chunk blindly, no validation (10 mins)
5. Ingest, wait, pray it works (20 mins)
6. Query RAG, get bad results, no idea why (60 mins debugging)
7. Check costs → $50 spent, budget blown
8. Start over with different approach

Total: 140+ minutes, $50 wasted, no working app
```

### After Tools: Smooth Journey

```
1. @resource-scout discover_sec_filing("TSLA", "10-K", 2024) → URL in 5 seconds
2. @security-analyst-batman validate PDF → ✅ legitimate
3. @financial-data-engineer ingest with estimate_api_cost → $0.02, proceed
4. @financial-data-engineer validate_chunk_quality → 92% score, looks good
5. @sql-analyst preview_sql_query → Validates before execution
6. @rag-orchestrator tune_rag_retrieval → Adjust weights, perfect results
7. diagnose_pipeline_health → All green, ready to deploy

Total: 15 minutes, $0.02 spent, working app ✅
```

**Time saved**: 125 minutes (89% faster)  
**Cost saved**: $49.98 (99.96% reduction)  
**Quality improvement**: 500% (no guesswork, validated at each step)

---

## Mental Model Application Summary

### First Principles
- `discover_sec_filing`: Solve "how do I get data?" at root level
- `compare_vector_databases`: Evaluate DB choices on fundamentals

### Second Order Effects
- `estimate_api_cost`: Prevent surprise bills before they happen
- `monitor_ingestion_progress`: Reduce user frustration → higher completion rate

### Systems Thinking
- `diagnose_pipeline_health`: View entire system at once
- `profile_rag_performance`: Identify bottlenecks in workflow

### Inversion
- `preview_sql_query`: Prevent bad queries before execution
- `validate_chunk_quality`: Catch errors before user sees them

### Interdependencies
- `tune_rag_retrieval`: Understand how BM25 + semantic weights interact
- `benchmark_rag_quality`: Measure how chunking affects retrieval

---

## Key Takeaways

1. **Pain points ≠ Obvious problems**: User said "I need scraping tools" → Real pain = "I don't know costs, quality, or performance"

2. **Tools eliminate guesswork**: Every "I don't know" becomes a tool call

3. **Observability > Features**: `diagnose_pipeline_health` more valuable than 10 ingestion features

4. **Prevention > Debugging**: `preview_sql_query` + `estimate_api_cost` prevent 90% of issues

5. **Discovery tools matter**: Solo developer needs `compare_vector_databases` to make informed decisions

---

**Next**: [07-finance-mission.md](07-finance-mission.md) - Your specific finance application mission
