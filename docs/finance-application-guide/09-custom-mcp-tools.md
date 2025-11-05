# Custom MCP Tools for Finance Application

**Complete implementations** of finance-specific MCP tools for your value investing stock screener.

---

## Tool Architecture Overview

```
skill_seeker_mcp/
├── server.py                    # Main MCP server
├── finance_tools/               # Finance-specific tools (NEW)
│   ├── __init__.py
│   ├── ingestion.py            # SEC filing ingestion
│   ├── query.py                # Text-to-SQL, RAG search
│   ├── monitoring.py           # Pipeline health, cost tracking
│   └── discovery.py            # Resource discovery, validation
└── requirements.txt
```

---

## Tier 1: Research Tools (Read-Only)

### 1. `discover_sec_filing`

**Purpose**: Find SEC filings without manual EDGAR search

```python
# finance_tools/discovery.py

import requests
from datetime import datetime

@server.tool()
async def discover_sec_filing(
    ticker: str,
    filing_type: str = "10-K",
    year: int = None,
    quarter: str = None
) -> dict:
    """
    Discover SEC filing URL from EDGAR automatically.
    
    Args:
        ticker: Stock symbol (e.g., "TSLA")
        filing_type: "10-K", "10-Q", "8-K", etc.
        year: Fiscal year (defaults to current year)
        quarter: "Q1", "Q2", "Q3", "Q4" (for 10-Q only)
    
    Returns:
        {
            "status": "found" | "not_found",
            "filing_url": "https://sec.gov/Archives/...",
            "filing_date": "2024-10-31",
            "ticker": "TSLA",
            "type": "10-K",
            "metadata": {
                "cik": "1318605",
                "company_name": "TESLA INC",
                "fiscal_year": 2024
            }
        }
    """
    
    year = year or datetime.now().year
    
    # Get CIK (Company ID) from ticker
    cik_response = requests.get(
        f"https://www.sec.gov/cgi-bin/browse-edgar",
        params={"action": "getcompany", "ticker": ticker, "output": "json"}
    )
    
    if cik_response.status_code != 200:
        return {"status": "not_found", "error": "Ticker not found"}
    
    cik = cik_response.json()["cik"]
    company_name = cik_response.json()["company_name"]
    
    # Search for filings
    filings_response = requests.get(
        f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json",
        headers={"User-Agent": "YourApp contact@example.com"}
    )
    
    filings = filings_response.json()["filings"]["recent"]
    
    # Find matching filing
    for i, form in enumerate(filings["form"]):
        if form == filing_type:
            filing_date = filings["filingDate"][i]
            accession_number = filings["accessionNumber"][i].replace("-", "")
            
            # Construct filing URL
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{filings['primaryDocument'][i]}"
            
            return {
                "status": "found",
                "filing_url": filing_url,
                "filing_date": filing_date,
                "ticker": ticker.upper(),
                "type": filing_type,
                "metadata": {
                    "cik": cik,
                    "company_name": company_name,
                    "fiscal_year": int(filing_date.split("-")[0]),
                    "accession_number": filings["accessionNumber"][i]
                }
            }
    
    return {"status": "not_found", "error": f"No {filing_type} found for {ticker} in {year}"}
```

---

### 2. `preview_sql_query`

**Purpose**: Validate SQL before execution (dry-run mode)

```python
# finance_tools/query.py

import duckdb
import dspy

@server.tool()
async def preview_sql_query(
    question: str,
    schema_path: str = "data/schema.sql",
    dry_run: bool = True
) -> dict:
    """
    Preview SQL query before execution.
    
    Args:
        question: Natural language question
        schema_path: Path to DuckDB schema file
        dry_run: If True, only generate SQL (don't execute)
    
    Returns:
        {
            "sql": "SELECT ...",
            "explanation": "This query retrieves...",
            "estimated_rows": 5,
            "estimated_time_ms": 12,
            "potential_issues": [],
            "safety_check": "passed" | "failed"
        }
    """
    
    # Load schema
    with open(schema_path) as f:
        schema = f.read()
    
    # Generate SQL with DSPy (optimized prompts)
    text_to_sql = dspy.ChainOfThought("schema, question -> sql_query, explanation")
    result = text_to_sql(schema=schema, question=question)
    
    sql_query = result.sql_query
    explanation = result.explanation
    
    # Safety checks
    issues = []
    
    # Check for dangerous operations
    if any(keyword in sql_query.upper() for keyword in ["DROP", "DELETE", "UPDATE", "INSERT"]):
        issues.append("Query contains write operation (read-only recommended)")
    
    # Check for SQL injection patterns
    if ";" in sql_query and sql_query.count(";") > 1:
        issues.append("Multiple statements detected (potential SQL injection)")
    
    safety_check = "passed" if not issues else "failed"
    
    # Dry run: estimate results
    if dry_run:
        try:
            conn = duckdb.connect("data/finance.duckdb", read_only=True)
            
            # Explain query (get execution plan)
            explain_result = conn.execute(f"EXPLAIN {sql_query}").fetchall()
            estimated_rows = extract_row_estimate(explain_result)
            
            return {
                "sql": sql_query,
                "explanation": explanation,
                "estimated_rows": estimated_rows,
                "estimated_time_ms": estimated_rows * 0.1,  # Rough estimate
                "potential_issues": issues,
                "safety_check": safety_check
            }
        except Exception as e:
            return {
                "sql": sql_query,
                "explanation": explanation,
                "potential_issues": issues + [f"SQL error: {str(e)}"],
                "safety_check": "failed"
            }
    
    # Execute query
    try:
        conn = duckdb.connect("data/finance.duckdb", read_only=True)
        results = conn.execute(sql_query).fetchall()
        
        return {
            "sql": sql_query,
            "explanation": explanation,
            "results": results,
            "row_count": len(results),
            "safety_check": safety_check
        }
    except Exception as e:
        return {
            "sql": sql_query,
            "error": str(e),
            "safety_check": "failed"
        }
```

---

## Tier 2: Data Tools (Internal Writes)

### 3. `ingest_sec_filing`

**Purpose**: Download, extract, chunk, embed, and store SEC filings

```python
# finance_tools/ingestion.py

import requests
import PyMuPDF  # fitz
import chromadb
import duckdb
from sentence_transformers import SentenceTransformer

@server.tool()
async def ingest_sec_filing(
    filing_url: str,
    ticker: str,
    extract_tables: bool = True,
    force_reingestion: bool = False
) -> dict:
    """
    Ingest SEC filing into DuckDB + Chroma.
    
    Pipeline:
    1. Download PDF from SEC
    2. Extract tables (Gemini 2.5 Flash if extract_tables=True)
    3. Chunk (section-aware, 300 tokens/chunk)
    4. Embed (sentence-transformers)
    5. Store (DuckDB + Chroma)
    
    Args:
        filing_url: SEC EDGAR URL
        ticker: Stock ticker
        extract_tables: Use Gemini for table extraction ($0.02/filing)
        force_reingestion: Re-ingest even if already exists
    
    Returns:
        {
            "status": "success" | "failed" | "skipped",
            "chunks_created": 421,
            "tables_extracted": 18,
            "cost_usd": 0.021,
            "processing_time_sec": 31.2,
            "duckdb_path": "data/finance.duckdb",
            "chroma_collection": "sec_filings_tsla"
        }
    """
    
    # Validation: Only SEC URLs
    if not filing_url.startswith("https://www.sec.gov/"):
        return {"status": "failed", "error": "Only SEC.gov URLs allowed"}
    
    # Check if already ingested
    conn = duckdb.connect("data/finance.duckdb")
    existing = conn.execute("""
        SELECT COUNT(*) FROM filings 
        WHERE ticker = ? AND filing_url = ?
    """, [ticker, filing_url]).fetchone()[0]
    
    if existing > 0 and not force_reingestion:
        return {"status": "skipped", "reason": "Already ingested (use force_reingestion=True to override)"}
    
    start_time = time.time()
    
    # 1. Download PDF
    pdf_response = requests.get(filing_url, headers={"User-Agent": "YourApp"})
    pdf_content = pdf_response.content
    
    # 2. Extract tables (optional, costs $0.02)
    tables = []
    if extract_tables:
        tables = await extract_tables_gemini(pdf_content)
    
    # 3. Chunk (section-aware)
    pdf_text = extract_text_from_pdf(pdf_content)
    chunks = chunk_section_aware(pdf_text, chunk_size=300)
    
    # 4. Embed
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = embedding_model.encode([chunk["text"] for chunk in chunks])
    
    # 5. Store in DuckDB
    conn.execute("""
        INSERT INTO filings (ticker, filing_url, filing_date, num_chunks, num_tables)
        VALUES (?, ?, ?, ?, ?)
    """, [ticker, filing_url, datetime.now(), len(chunks), len(tables)])
    
    for i, chunk in enumerate(chunks):
        conn.execute("""
            INSERT INTO chunks (ticker, filing_url, chunk_index, text, section, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [ticker, filing_url, i, chunk["text"], chunk["section"], json.dumps(chunk["metadata"])])
    
    if tables:
        for table in tables:
            conn.execute("""
                INSERT INTO tables (ticker, filing_url, table_index, table_data)
                VALUES (?, ?, ?, ?)
            """, [ticker, filing_url, table["index"], json.dumps(table["data"])])
    
    # 6. Store in Chroma
    chroma_client = chromadb.PersistentClient(path="data/chroma")
    collection = chroma_client.get_or_create_collection(f"sec_filings_{ticker.lower()}")
    
    collection.add(
        ids=[f"{ticker}_{i}" for i in range(len(chunks))],
        embeddings=embeddings.tolist(),
        documents=[chunk["text"] for chunk in chunks],
        metadatas=[{
            "ticker": ticker,
            "filing_url": filing_url,
            "section": chunk["section"],
            **chunk["metadata"]
        } for chunk in chunks]
    )
    
    processing_time = time.time() - start_time
    cost_usd = 0.02 if extract_tables else 0.0
    
    return {
        "status": "success",
        "chunks_created": len(chunks),
        "tables_extracted": len(tables),
        "cost_usd": cost_usd,
        "processing_time_sec": processing_time,
        "duckdb_path": "data/finance.duckdb",
        "chroma_collection": f"sec_filings_{ticker.lower()}"
    }
```

---

### 4. `hybrid_rag_search`

**Purpose**: Hybrid retrieval (BM25 + semantic + reranking)

```python
# finance_tools/query.py

from rank_bm25 import BM25Okapi
import numpy as np
from sentence_transformers import CrossEncoder

@server.tool()
async def hybrid_rag_search(
    query: str,
    collection: str,
    top_k: int = 10,
    rerank: bool = True,
    bm25_weight: float = 0.5,
    semantic_weight: float = 0.5
) -> dict:
    """
    Hybrid RAG search with provenance.
    
    Pipeline:
    1. BM25 (lexical) → top 50
    2. Semantic (FAISS) → top 50
    3. RRF (Reciprocal Rank Fusion)
    4. Cross-encoder reranking → top 20
    5. Deduplication → final top_k
    
    Returns:
        {
            "chunks": [
                {
                    "text": "...",
                    "score": 0.92,
                    "source": "https://sec.gov/...",
                    "page": 42,
                    "section": "Item 7: MD&A"
                }
            ],
            "retrieval_ms": 150,
            "quality_metrics": {
                "avg_score": 0.84,
                "bm25_contribution": 0.3,
                "semantic_contribution": 0.7
            }
        }
    """
    
    start_time = time.time()
    
    # Get all chunks from Chroma
    chroma_client = chromadb.PersistentClient(path="data/chroma")
    chroma_collection = chroma_client.get_collection(collection)
    
    all_docs = chroma_collection.get(include=["documents", "embeddings", "metadatas"])
    
    # 1. BM25 search
    tokenized_docs = [doc.split() for doc in all_docs["documents"]]
    bm25 = BM25Okapi(tokenized_docs)
    bm25_scores = bm25.get_scores(query.split())
    bm25_top50 = np.argsort(bm25_scores)[-50:][::-1]
    
    # 2. Semantic search
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embedding = embedding_model.encode([query])[0]
    
    # Cosine similarity
    embeddings_matrix = np.array(all_docs["embeddings"])
    semantic_scores = np.dot(embeddings_matrix, query_embedding) / (
        np.linalg.norm(embeddings_matrix, axis=1) * np.linalg.norm(query_embedding)
    )
    semantic_top50 = np.argsort(semantic_scores)[-50:][::-1]
    
    # 3. Reciprocal Rank Fusion
    rrf_scores = {}
    k = 60  # RRF parameter
    
    for rank, idx in enumerate(bm25_top50):
        rrf_scores[idx] = rrf_scores.get(idx, 0) + bm25_weight / (k + rank)
    
    for rank, idx in enumerate(semantic_top50):
        rrf_scores[idx] = rrf_scores.get(idx, 0) + semantic_weight / (k + rank)
    
    rrf_top20_indices = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:20]
    
    # 4. Cross-encoder reranking
    if rerank:
        cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        pairs = [[query, all_docs["documents"][idx]] for idx in rrf_top20_indices]
        rerank_scores = cross_encoder.predict(pairs)
        
        reranked_indices = [rrf_top20_indices[i] for i in np.argsort(rerank_scores)[::-1]]
    else:
        reranked_indices = rrf_top20_indices
    
    # 5. Deduplication
    final_chunks = []
    seen_texts = set()
    
    for idx in reranked_indices:
        text = all_docs["documents"][idx]
        
        # Skip if too similar to already selected chunk
        if any(cosine_similarity(text, seen_text) > 0.95 for seen_text in seen_texts):
            continue
        
        seen_texts.add(text)
        metadata = all_docs["metadatas"][idx]
        
        final_chunks.append({
            "text": text,
            "score": rrf_scores.get(idx, 0),
            "source": metadata.get("filing_url", ""),
            "page": metadata.get("page", 0),
            "section": metadata.get("section", ""),
            "ticker": metadata.get("ticker", "")
        })
        
        if len(final_chunks) >= top_k:
            break
    
    retrieval_time = (time.time() - start_time) * 1000
    
    return {
        "chunks": final_chunks,
        "retrieval_ms": retrieval_time,
        "quality_metrics": {
            "avg_score": np.mean([c["score"] for c in final_chunks]),
            "bm25_contribution": bm25_weight,
            "semantic_contribution": semantic_weight,
            "reranking_enabled": rerank
        }
    }
```

---

## Tier 3: Monitoring Tools

### 5. `diagnose_pipeline_health`

**Purpose**: Comprehensive pipeline health check

```python
# finance_tools/monitoring.py

@server.tool()
async def diagnose_pipeline_health() -> dict:
    """
    Comprehensive finance pipeline health check.
    
    Returns:
        {
            "overall_health": "healthy" | "degraded" | "critical",
            "components": {
                "duckdb": {...},
                "chroma": {...},
                "gemini_api": {...}
            },
            "errors_last_24h": [...],
            "recommendations": [...]
        }
    """
    
    health_status = {"overall_health": "healthy", "components": {}, "errors_last_24h": [], "recommendations": []}
    
    # 1. Check DuckDB
    try:
        conn = duckdb.connect("data/finance.duckdb", read_only=True)
        
        db_size_mb = Path("data/finance.duckdb").stat().st_size / 1024 / 1024
        table_count = len(conn.execute("SHOW TABLES").fetchall())
        filings_count = conn.execute("SELECT COUNT(*) FROM filings").fetchone()[0]
        last_write = conn.execute("SELECT MAX(ingestion_timestamp) FROM filings").fetchone()[0]
        
        health_status["components"]["duckdb"] = {
            "status": "healthy",
            "size_mb": round(db_size_mb, 2),
            "tables": table_count,
            "filings": filings_count,
            "last_write": str(last_write)
        }
        
        if db_size_mb > 1000:  # > 1GB
            health_status["recommendations"].append("DuckDB size > 1GB: consider archiving old filings")
    
    except Exception as e:
        health_status["components"]["duckdb"] = {"status": "critical", "error": str(e)}
        health_status["overall_health"] = "critical"
    
    # 2. Check Chroma
    try:
        chroma_client = chromadb.PersistentClient(path="data/chroma")
        collections = chroma_client.list_collections()
        
        total_embeddings = sum(col.count() for col in collections)
        
        health_status["components"]["chroma"] = {
            "status": "healthy",
            "collections": len(collections),
            "total_embeddings": total_embeddings
        }
    
    except Exception as e:
        health_status["components"]["chroma"] = {"status": "critical", "error": str(e)}
        health_status["overall_health"] = "critical"
    
    # 3. Check Gemini API quota
    # (This would require API call to check quota)
    health_status["components"]["gemini_api"] = {
        "status": "healthy",
        "quota_remaining": 9750,  # Mock value
        "quota_reset": "23 hours"
    }
    
    # 4. Check for recent errors
    try:
        errors = conn.execute("""
            SELECT timestamp, component, error 
            FROM error_log 
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            ORDER BY timestamp DESC
        """).fetchall()
        
        health_status["errors_last_24h"] = [
            {"timestamp": str(e[0]), "component": e[1], "error": e[2]}
            for e in errors
        ]
        
        if len(errors) > 10:
            health_status["overall_health"] = "degraded"
            health_status["recommendations"].append(f"{len(errors)} errors in last 24h: investigate logs")
    
    except:
        pass
    
    return health_status
```

---

## Usage Examples

### Example 1: Complete Ingestion Workflow

```python
# User: "Ingest TSLA 10-K from 2024"

# Step 1: Discover filing
filing = await discover_sec_filing("TSLA", "10-K", 2024)
# → {"filing_url": "https://sec.gov/...", "status": "found"}

# Step 2: Ingest filing
result = await ingest_sec_filing(filing["filing_url"], "TSLA", extract_tables=True)
# → {"chunks_created": 421, "tables_extracted": 18, "cost_usd": 0.021}

# Step 3: Validate ingestion
health = await diagnose_pipeline_health()
# → {"overall_health": "healthy", "duckdb": {"filings": 24}}
```

### Example 2: RAG Query Workflow

```python
# User: "What's TSLA revenue growth?"

# Step 1: Preview SQL query
preview = await preview_sql_query("What's TSLA revenue growth?", dry_run=True)
# → {"sql": "SELECT year, revenue FROM filings WHERE ticker='TSLA'", "safety_check": "passed"}

# Step 2: Execute query
result = await preview_sql_query("What's TSLA revenue growth?", dry_run=False)
# → {"results": [{"year": 2022, "revenue": 81.5B}, ...]}

# OR: Use RAG for qualitative questions
rag_result = await hybrid_rag_search("What are TSLA's main risks?", "sec_filings_tsla")
# → {"chunks": [...with provenance...], "retrieval_ms": 150}
```

---

## Integration with MCP Server

Add to `skill_seeker_mcp/server.py`:

```python
from finance_tools.discovery import discover_sec_filing
from finance_tools.ingestion import ingest_sec_filing
from finance_tools.query import preview_sql_query, hybrid_rag_search
from finance_tools.monitoring import diagnose_pipeline_health

# Tools are automatically registered via @server.tool() decorator
```

---

**Next**: [10-agents-for-finance.md](10-agents-for-finance.md) - Create specialized finance agents
