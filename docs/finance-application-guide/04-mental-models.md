# Mental Models for Tool Design

**From CLAUDE.md**: "This project follows a rigorous check → plan → recheck → pause → create → recheck → refine → recheck → exit methodology, enhanced by multiple mental models."

---

## The Five Mental Models

### 1. First Principles Thinking

**Definition**: Break problems down to fundamental truths, then build up from there.

**Application**: Don't copy existing solutions blindly—understand the core problem first.

#### Example: "Why do we need custom MCP tools?"

**Surface-level answer**: "Because LangChain doesn't work well"

**First Principles answer**:
1. **Fundamental truth**: Finance apps need deterministic, auditable data pipelines
2. **Core requirement**: Every transformation must be traceable (SEC filing → chunk → embedding → query)
3. **Reality constraint**: Claude can't execute arbitrary Python code
4. **Solution**: MCP tools = deterministic Python functions Claude can call
5. **Result**: Build tools for: ingest_sec_filing, text_to_sql_query, hybrid_rag_search

#### Finance Application Example

**Problem**: "How do I chunk 10-K filings for RAG?"

**Bad approach**: Use default 512-token chunks

**First Principles approach**:
1. **What's the goal?** Answer questions about specific sections (revenue, risks, MD&A)
2. **What's the structure?** SEC filings have semantic sections with headers
3. **What's optimal?** Section-aware chunking (300-500 tokens, preserve context)
4. **How to implement?** Detect section headers → chunk within sections → add metadata

**Result**: Better retrieval because chunks respect document structure

---

### 2. Second Order Effects

**Definition**: Consider consequences of consequences—what happens AFTER the immediate result?

**Application**: Design for cascading impacts, not just first-order benefits.

#### Example: "Adding table extraction to ingestion pipeline"

**First order effect**: Extract 15 financial tables from 10-K

**Second order effects**:
- ✅ **Positive**: Can answer "What's TSLA revenue?" with exact numbers
- ✅ **Positive**: Enables time-series analysis across multiple filings
- ⚠️ **Negative**: Costs $0.02 per filing (Gemini 2.5 Flash)
- ⚠️ **Negative**: Processing time increases 2x (5s → 10s)
- ✅ **Mitigation**: Make table extraction optional (`extract_tables=False` for free processing)

**Decision**: Include but make optional, track costs explicitly

#### Finance Application Example

**Decision**: "Should I use Postgres with pgvector or Chroma?"

**First order**: Both can store embeddings

**Second order effects**:

**Postgres + pgvector**:
- ✅ Single database (DuckDB for analytics, Postgres for vectors)
- ✅ ACID transactions (data consistency)
- ⚠️ Requires Postgres setup and maintenance
- ⚠️ Vector search slower than specialized DB

**Chroma**:
- ✅ Faster vector search (optimized data structures)
- ✅ Easier setup (pip install chromadb)
- ⚠️ Another system to manage
- ⚠️ Eventual consistency (not ACID)

**Decision**: Start with Chroma (faster iteration), migrate to Postgres if need ACID

---

### 3. Systems Thinking

**Definition**: View the project as an integrated whole—understand relationships and feedback loops.

**Application**: Map dependencies, identify bottlenecks, design for the entire system.

#### System Map: Finance Application

```
┌─────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                            │
│  SEC EDGAR ──┐                                              │
│  News APIs   ├──→ INGESTION ──→ STORAGE ──→ QUERY ──→ UI   │
│  Market Data ┘                                              │
└─────────────────────────────────────────────────────────────┘
       ↓              ↓              ↓           ↓         ↓
   Rate limits   Processing      Disk space   Token     WebSocket
                   cost                        cost     latency

FEEDBACK LOOPS:
• More data → Better answers → More queries → Higher cost
• Slow ingestion → Stale data → Bad answers → User frustration
• Poor chunking → Irrelevant retrieval → User refines query → More cost
```

#### Identifying Bottlenecks

**Bottleneck 1: Ingestion Speed**
- Symptom: 10-K takes 60 seconds to process
- Impact: Can't scale to 100+ companies
- Solution: Async processing + batch ingestion

**Bottleneck 2: Vector Search Latency**
- Symptom: RAG queries take 2-3 seconds
- Impact: Poor UX in chat interface
- Solution: Pre-compute embeddings, use ANN indexes (HNSW)

**Bottleneck 3: API Costs**
- Symptom: $10/day in Gemini calls
- Impact: Unsustainable at scale
- Solution: Cache extracted tables, make extraction optional

---

### 4. Inversion Thinking

**Definition**: Instead of "How do I succeed?", ask "How could I fail?" and avoid those paths.

**Application**: Identify failure modes, then design to prevent them.

#### Example: "What could make my finance app fail?"

**Failure Mode 1: Silent data corruption**
- **Cause**: Chunking truncates mid-sentence, loses context
- **Prevention**: Validate chunks (no truncation), add checksums
- **Tool**: `validate_chunk_quality()` in ingestion pipeline

**Failure Mode 2: Hallucinated financial data**
- **Cause**: RAG retrieves wrong document, LLM invents numbers
- **Prevention**: Always return source URLs, require minimum similarity threshold
- **Tool**: `hybrid_rag_search()` returns provenance metadata

**Failure Mode 3: Runaway costs**
- **Cause**: User ingests 500 filings with table extraction ($10)
- **Prevention**: Warn before expensive operations, track daily budgets
- **Tool**: `pre_flight_check()` estimates cost before execution

**Failure Mode 4: Stale data**
- **Cause**: Filings ingested 6 months ago, market conditions changed
- **Prevention**: Track ingestion timestamps, flag old data
- **Tool**: `monitor_pipeline()` shows data freshness

#### What NOT to Build

**❌ Autonomous trading agent** (Derek Snow: "Finance needs reliability, not autonomy")
- Why: Error compounding in multi-step loops
- Alternative: Guided workflows with human-in-loop

**❌ Custom LLM training** (Derek Snow: "Don't train foundation models")
- Why: Expensive, slow, unnecessary
- Alternative: Use Claude 3.5 Sonnet with good prompts

**❌ Stateful multi-step agents** (Derek Snow: "Avoid error compounding")
- Why: Each failure cascades to next step
- Alternative: Stateless workflows with explicit handoffs

---

### 5. Interdependencies

**Definition**: Map how components depend on each other—changes in one affect many.

**Application**: Design for loose coupling, explicit interfaces.

#### Dependency Map: MCP Tools

```
ingest_sec_filing
    ↓ depends on
    ├─ chunk_and_embed (chunking strategy)
    ├─ extract_tables (optional, costs money)
    └─ DuckDB + Chroma (storage layer)
         ↓ used by
         ├─ text_to_sql_query (DuckDB)
         ├─ hybrid_rag_search (Chroma)
         └─ monitor_pipeline (both)

INSIGHT: Changing chunking strategy affects:
  • RAG retrieval quality
  • Storage size
  • Embedding costs
  • Query latency
```

#### Managing Interdependencies

**Tight coupling (BAD)**:
```python
def ingest_filing(url):
    chunks = chunk_text(extract_pdf(download(url)), size=512)  # Hardcoded
    embed(chunks)  # No control over model
```

**Loose coupling (GOOD)**:
```python
def ingest_filing(
    url: str,
    chunk_strategy: str = "section-aware",  # Configurable
    chunk_size: int = 300,
    embed_model: str = "all-MiniLM-L6-v2"
) -> dict:
    """Explicit parameters = easy to change later"""
    pass
```

---

## Applying Mental Models to Tool Design

### CHECK Phase (First Principles + Systems Thinking)

**Questions to ask**:
1. What's the fundamental problem? (First Principles)
2. How does this fit in the overall system? (Systems Thinking)
3. What are the dependencies? (Interdependencies)

**Example**: Designing `text_to_sql_query` tool

1. **First Principles**: Core problem = translate natural language → SQL
2. **Systems Thinking**: Depends on DuckDB schema, used by chat interface
3. **Interdependencies**: Schema changes break queries, need schema versioning

### PLAN Phase (Second Order Effects + Inversion)

**Questions to ask**:
1. What happens AFTER this succeeds? (Second Order)
2. How could this fail catastrophically? (Inversion)

**Example**: Designing `text_to_sql_query` tool

1. **Second Order**: User gets answer → asks followup → needs conversation context
2. **Inversion**: SQL injection risk → validate queries, use parameterized statements

### CREATE Phase (First Principles)

**Focus**: Build minimal, correct implementation

**Example**: `text_to_sql_query` v1
```python
@server.tool()
async def text_to_sql_query(question: str, schema_path: str) -> dict:
    """Minimal: just translate and execute"""
    sql = translate_to_sql(question, schema_path)  # DSPy optimized
    results = execute_sql(sql)
    return {"sql": sql, "results": results}
```

### RECHECK Phase (All Models)

**Validation**:
1. Does it solve the fundamental problem? (First Principles) ✅
2. Are second-order effects acceptable? (Second Order) ⚠️ No conversation context
3. How does it affect the system? (Systems) ✅ Integrates cleanly
4. What failure modes exist? (Inversion) ⚠️ SQL injection risk
5. What breaks if this changes? (Interdependencies) ✅ Schema is explicit param

### REFINE Phase (Address Gaps)

**Improvements**:
```python
@server.tool()
async def text_to_sql_query(
    question: str,
    schema_path: str,
    conversation_history: list[dict] = None,  # Second Order: context
    validate_sql: bool = True  # Inversion: safety
) -> dict:
    """Refined: handles context + safety"""
    sql = translate_to_sql(question, schema_path, conversation_history)
    
    if validate_sql:
        validate_sql_safety(sql)  # Prevent injection
    
    results = execute_sql(sql)
    
    return {
        "sql": sql,
        "results": results,
        "explanation": explain_query(sql),  # Second Order: transparency
        "execution_time_ms": ...
    }
```

---

## Decision Framework Template

Use this for EVERY tool you design:

### 1. First Principles Check
- [ ] What's the fundamental problem?
- [ ] What's the simplest solution that could work?
- [ ] Am I building what's needed, not what's trendy?

### 2. Second Order Effects Check
- [ ] What happens after immediate success?
- [ ] What are the positive cascading effects?
- [ ] What are the negative cascading effects?
- [ ] How do I mitigate negatives?

### 3. Systems Thinking Check
- [ ] Where does this fit in the overall architecture?
- [ ] What are the upstream dependencies?
- [ ] What are the downstream consumers?
- [ ] Are there feedback loops?

### 4. Inversion Check
- [ ] How could this fail catastrophically?
- [ ] What should I NOT build?
- [ ] What are the worst-case scenarios?
- [ ] How do I prevent each failure mode?

### 5. Interdependencies Check
- [ ] What components does this depend on?
- [ ] What components depend on this?
- [ ] If this changes, what breaks?
- [ ] Are interfaces explicit and versioned?

---

## Real Example: Designing `ingest_sec_filing`

### First Principles
**Problem**: Get SEC filing data into queryable format

**Solution**: Download → Extract → Chunk → Embed → Store

### Second Order Effects
**Positive**: Enables RAG queries, time-series analysis  
**Negative**: Costs money (Gemini), takes time (30s/filing)  
**Mitigation**: Make table extraction optional, add cost warnings

### Systems Thinking
**Upstream**: SEC EDGAR (rate limits)  
**Downstream**: RAG search, SQL queries, monitoring  
**Bottleneck**: Gemini API quota (10K calls/day)

### Inversion (Failure Modes)
1. **PDF download fails** → Retry with exponential backoff
2. **Table extraction fails** → Continue without tables, log error
3. **Embedding fails** → Store raw chunks, embed later
4. **Storage fails** → Rollback transaction, don't lose data

### Interdependencies
**Depends on**: DuckDB schema, Chroma collections, Gemini API  
**Used by**: `hybrid_rag_search`, `monitor_pipeline`, `@sql-analyst`  
**If changed**: Must migrate existing data, update schema version

### Result: Robust Tool Design
```python
@server.tool()
async def ingest_sec_filing(
    filing_url: str,
    ticker: str,
    extract_tables: bool = True,  # Second Order: optional cost
    force_reingestion: bool = False  # Inversion: prevent duplicates
) -> dict:
    """
    Ingest SEC filing with:
    - Retry logic (Inversion)
    - Cost transparency (Second Order)
    - Explicit dependencies (Interdependencies)
    - Schema versioning (Systems Thinking)
    """
    
    # Check if already ingested (Inversion: prevent duplicates)
    if not force_reingestion and already_exists(ticker, filing_url):
        return {"status": "skipped", "reason": "already_ingested"}
    
    # Estimate cost (Second Order: transparency)
    estimated_cost = 0.02 if extract_tables else 0.0
    
    try:
        # Download with retry (Inversion: handle failures)
        pdf = download_with_retry(filing_url, max_retries=3)
        
        # Extract tables (optional, costs money)
        tables = extract_tables_gemini(pdf) if extract_tables else []
        
        # Chunk (First Principles: section-aware)
        chunks = chunk_section_aware(pdf, chunk_size=300)
        
        # Embed (Systems: use configured model)
        embeddings = embed_chunks(chunks, model="all-MiniLM-L6-v2")
        
        # Store (Interdependencies: explicit schema)
        store_in_duckdb(chunks, tables, schema_version="1.0")
        store_in_chroma(chunks, embeddings, collection=f"sec_{ticker}")
        
        return {
            "status": "success",
            "chunks_created": len(chunks),
            "tables_extracted": len(tables),
            "cost_usd": estimated_cost,
            "schema_version": "1.0"
        }
    
    except Exception as e:
        # Inversion: fail gracefully
        return {"status": "failed", "error": str(e)}
```

---

## Key Takeaways

1. **First Principles**: Understand the problem before building
2. **Second Order**: Design for cascading effects, not just first win
3. **Systems**: View as integrated whole, not isolated components
4. **Inversion**: Prevent failure modes, don't just chase success
5. **Interdependencies**: Explicit interfaces, loose coupling

**For your finance app**: Apply all 5 models to EVERY tool you design. This prevents:
- Building the wrong thing (First Principles)
- Unexpected costs/failures (Second Order + Inversion)
- Brittle architecture (Systems + Interdependencies)

---

**Next**: [05-movie-agents-metaphor.md](05-movie-agents-metaphor.md) - Movie characters as agent archetypes
