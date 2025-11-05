"""
SEC filing query tool - Text-to-SQL and Hybrid RAG.

Mental Model: Systems Thinking
- Query pipeline: Question → Classify → Route (SQL/RAG) → Execute → Format
- SQL path: Fast, precise for structured queries (revenue, dates, counts)
- RAG path: Semantic, better for conceptual questions (why, how, explain)

Mental Model: Second Order Effects
- Query quality affects user trust and adoption
- Hybrid search (BM25 + Vector) improves recall
- RRF (Reciprocal Rank Fusion) combines rankings without normalization
"""

import os
from typing import Dict, Any, List, Optional
import duckdb
import chromadb
from rank_bm25 import BM25Okapi
import anthropic
import structlog

logger = structlog.get_logger()

# Constants
DEFAULT_TOP_K = 5
RRF_K = 60  # Standard constant for Reciprocal Rank Fusion


# ============================================================================
# Text-to-SQL (DSPy-powered with Claude)
# ============================================================================

async def generate_sql(
    question: str,
    conn: Optional[duckdb.DuckDBPyConnection] = None
) -> Dict[str, Any]:
    """
    Generate SQL query from natural language question.
    
    Args:
        question: Natural language query
        conn: DuckDB connection (optional, for schema context)
    
    Returns:
        {
            "success": bool,
            "sql": str,
            "error": str
        }
    
    Mental Model: First Principles
    - User intent → SQL components (SELECT, FROM, WHERE)
    - Schema awareness prevents invalid queries
    """
    try:
        if not question or not question.strip():
            return {
                "success": False,
                "error": "Empty question provided"
            }
        
        # Get database schema for context
        schema_context = ""
        if conn:
            try:
                tables = conn.execute("SHOW TABLES").fetchall()
                schema_context = "Available tables:\n"
                for table in tables:
                    table_name = table[0]
                    columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
                    schema_context += f"\n{table_name}:\n"
                    for col in columns:
                        schema_context += f"  - {col[0]} ({col[1]})\n"
            except Exception:
                pass  # Schema context is optional
        
        # Use Claude to generate SQL
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""You are a SQL expert. Convert this natural language question into a SQL query.

Question: {question}

{schema_context}

Return ONLY the SQL query, nothing else. Use standard SQL syntax compatible with DuckDB.
If the question is vague, use reasonable defaults (e.g., LIMIT 10).
"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        sql = response.content[0].text.strip()
        
        # Clean up SQL (remove markdown code blocks if present)
        if sql.startswith("```sql"):
            sql = sql.replace("```sql", "").replace("```", "").strip()
        elif sql.startswith("```"):
            sql = sql.replace("```", "").strip()
        
        logger.info("sql_generated", question=question[:100])
        
        return {
            "success": True,
            "sql": sql
        }
    
    except Exception as e:
        logger.error("sql_generation_failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


async def execute_sql(
    sql: str,
    conn: duckdb.DuckDBPyConnection
) -> Dict[str, Any]:
    """
    Execute SQL query and return results.
    
    Args:
        sql: SQL query string
        conn: DuckDB connection
    
    Returns:
        {
            "success": bool,
            "rows": list[dict],
            "error": str
        }
    
    Mental Model: First Principles
    - SQL execution: Parse → Optimize → Execute → Format
    - Results must be JSON-serializable
    """
    try:
        # Execute query
        result = conn.execute(sql).fetchall()
        
        # Get column names
        description = conn.description
        column_names = [desc[0] for desc in description] if description else []
        
        # Format as list of dictionaries
        rows = []
        for row in result:
            row_dict = {}
            for i, value in enumerate(row):
                row_dict[column_names[i]] = value
            rows.append(row_dict)
        
        logger.info("sql_executed", num_rows=len(rows))
        
        return {
            "success": True,
            "rows": rows
        }
    
    except Exception as e:
        logger.error("sql_execution_failed", error=str(e))
        return {
            "success": False,
            "rows": [],
            "error": str(e)
        }


# ============================================================================
# Hybrid RAG (BM25 + Vector Search + RRF)
# ============================================================================

async def bm25_search(
    query: str,
    conn: duckdb.DuckDBPyConnection,
    top_k: int = DEFAULT_TOP_K
) -> Dict[str, Any]:
    """
    BM25 keyword-based search.
    
    Args:
        query: Search query
        conn: DuckDB connection
        top_k: Number of results to return
    
    Returns:
        {
            "success": bool,
            "chunks": list[dict],
            "error": str
        }
    
    Mental Model: First Principles
    - BM25 = TF-IDF + document length normalization
    - Exact keyword matches rank higher
    """
    try:
        # Fetch all chunks from DuckDB
        result = conn.execute("SELECT id, text, section FROM chunks").fetchall()
        
        if not result:
            return {
                "success": True,
                "chunks": []
            }
        
        # Prepare documents for BM25
        chunk_ids = [row[0] for row in result]
        documents = [row[1] for row in result]
        sections = [row[2] for row in result]
        
        # Tokenize documents
        tokenized_docs = [doc.lower().split() for doc in documents]
        
        # Create BM25 index
        bm25 = BM25Okapi(tokenized_docs)
        
        # Search
        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)
        
        # Get top-k results
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        chunks = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include non-zero scores
                chunks.append({
                    "chunk_id": chunk_ids[idx],
                    "text": documents[idx],
                    "section": sections[idx],
                    "score": float(scores[idx]),
                    "method": "bm25"
                })
        
        logger.info("bm25_search_completed", num_results=len(chunks))
        
        return {
            "success": True,
            "chunks": chunks
        }
    
    except Exception as e:
        logger.error("bm25_search_failed", error=str(e))
        return {
            "success": False,
            "chunks": [],
            "error": str(e)
        }


async def vector_search(
    query: str,
    chroma_client: chromadb.Client,
    collection_name: str = "test_chunks",
    top_k: int = DEFAULT_TOP_K
) -> Dict[str, Any]:
    """
    Vector semantic search using ChromaDB.
    
    Args:
        query: Search query
        chroma_client: ChromaDB client
        collection_name: Collection name
        top_k: Number of results to return
    
    Returns:
        {
            "success": bool,
            "chunks": list[dict],
            "error": str
        }
    
    Mental Model: First Principles
    - Embeddings capture semantic meaning
    - Cosine similarity measures closeness
    """
    try:
        # Get or create collection
        collection = chroma_client.get_or_create_collection(collection_name)
        
        # Search (ChromaDB handles embedding generation internally)
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        chunks = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                chunk_data = {
                    "text": doc,
                    "score": 1.0 - results["distances"][0][i] if results["distances"] else 0.0,  # Convert distance to similarity
                    "method": "vector"
                }
                
                # Add metadata if available
                if results["metadatas"] and results["metadatas"][0]:
                    chunk_data.update(results["metadatas"][0][i])
                
                chunks.append(chunk_data)
        
        logger.info("vector_search_completed", num_results=len(chunks))
        
        return {
            "success": True,
            "chunks": chunks
        }
    
    except Exception as e:
        logger.error("vector_search_failed", error=str(e))
        return {
            "success": False,
            "chunks": [],
            "error": str(e)
        }


def reciprocal_rank_fusion(
    bm25_results: List[Dict[str, Any]],
    vector_results: List[Dict[str, Any]],
    k: int = RRF_K
) -> List[Dict[str, Any]]:
    """
    Combine BM25 and vector search results using Reciprocal Rank Fusion.
    
    Args:
        bm25_results: Results from BM25 search
        vector_results: Results from vector search
        k: RRF constant (default 60)
    
    Returns:
        List of fused results with RRF scores
    
    Mental Model: Systems Thinking
    - RRF combines rankings without score normalization
    - Formula: RRF(d) = Σ 1/(k + rank_i(d)) for each ranker i
    """
    # Build RRF scores
    rrf_scores = {}
    
    # Process BM25 results
    for rank, result in enumerate(bm25_results, start=1):
        chunk_id = result.get("chunk_id", id(result))  # Use chunk_id or object id
        if chunk_id not in rrf_scores:
            rrf_scores[chunk_id] = {
                "chunk_id": chunk_id,
                "text": result.get("text", ""),
                "section": result.get("section", ""),
                "rrf_score": 0.0,
                "bm25_rank": rank,
                "bm25_score": result.get("score", 0.0)
            }
        rrf_scores[chunk_id]["rrf_score"] += 1.0 / (k + rank)
    
    # Process vector results
    for rank, result in enumerate(vector_results, start=1):
        chunk_id = result.get("chunk_id", id(result))
        if chunk_id not in rrf_scores:
            rrf_scores[chunk_id] = {
                "chunk_id": chunk_id,
                "text": result.get("text", ""),
                "section": result.get("section", ""),
                "rrf_score": 0.0,
                "vector_rank": rank,
                "vector_score": result.get("score", 0.0)
            }
        else:
            rrf_scores[chunk_id]["vector_rank"] = rank
            rrf_scores[chunk_id]["vector_score"] = result.get("score", 0.0)
        
        rrf_scores[chunk_id]["rrf_score"] += 1.0 / (k + rank)
    
    # Sort by RRF score (descending)
    fused_results = sorted(rrf_scores.values(), key=lambda x: x["rrf_score"], reverse=True)
    
    # Add "score" field for compatibility
    for result in fused_results:
        result["score"] = result["rrf_score"]
        result["method"] = "rrf"
    
    logger.info("rrf_fusion_completed", num_results=len(fused_results))
    
    return fused_results


async def hybrid_search(
    query: str,
    conn: duckdb.DuckDBPyConnection,
    chroma_client: chromadb.Client,
    top_k: int = DEFAULT_TOP_K
) -> Dict[str, Any]:
    """
    Hybrid search combining BM25 and vector search with RRF.
    
    Args:
        query: Search query
        conn: DuckDB connection
        chroma_client: ChromaDB client
        top_k: Number of final results
    
    Returns:
        {
            "success": bool,
            "chunks": list[dict],
            "error": str
        }
    
    Mental Model: Systems Thinking
    - BM25: Fast, keyword-based (exact matches)
    - Vector: Semantic understanding (meaning)
    - RRF: Best of both worlds
    """
    try:
        # Run both searches in parallel
        bm25_result = await bm25_search(query, conn, top_k=top_k * 2)
        vector_result = await vector_search(query, chroma_client, top_k=top_k * 2)
        
        if not bm25_result["success"] or not vector_result["success"]:
            return {
                "success": False,
                "chunks": [],
                "error": "Search failed"
            }
        
        # Fuse results with RRF
        fused_chunks = reciprocal_rank_fusion(
            bm25_results=bm25_result["chunks"],
            vector_results=vector_result["chunks"]
        )
        
        # Return top-k
        final_chunks = fused_chunks[:top_k]
        
        logger.info("hybrid_search_completed", num_results=len(final_chunks))
        
        return {
            "success": True,
            "chunks": final_chunks
        }
    
    except Exception as e:
        logger.error("hybrid_search_failed", error=str(e))
        return {
            "success": False,
            "chunks": [],
            "error": str(e)
        }


# ============================================================================
# Answer Generation (RAG with Claude)
# ============================================================================

async def generate_answer(
    question: str,
    chunks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate natural language answer from retrieved chunks.
    
    Args:
        question: User question
        chunks: Retrieved context chunks
    
    Returns:
        {
            "success": bool,
            "answer": str,
            "error": str
        }
    
    Mental Model: Systems Thinking
    - RAG = Retrieve + Augment + Generate
    - Citations provide provenance
    """
    try:
        # Handle empty context
        if not chunks:
            return {
                "success": True,
                "answer": "No information found to answer this question."
            }
        
        # Build context from chunks
        context = "Context from SEC filings:\n\n"
        for i, chunk in enumerate(chunks, start=1):
            section = chunk.get("section", "Unknown")
            page = chunk.get("page", "?")
            text = chunk.get("text", "")
            context += f"[{i}] {section} (page {page}):\n{text}\n\n"
        
        # Use Claude to generate answer
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""Answer the following question using ONLY the provided context from SEC filings.
Cite your sources using [1], [2], etc.

Question: {question}

{context}

Provide a clear, concise answer with citations."""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        
        answer = response.content[0].text.strip()
        
        logger.info("answer_generated", question=question[:100])
        
        return {
            "success": True,
            "answer": answer
        }
    
    except Exception as e:
        logger.error("answer_generation_failed", error=str(e))
        return {
            "success": False,
            "answer": f"Error generating answer: {str(e)}",
            "error": str(e)
        }


# ============================================================================
# Query Pipeline (End-to-End)
# ============================================================================

async def query_pipeline(
    question: str,
    conn: Optional[duckdb.DuckDBPyConnection] = None,
    chroma_client: Optional[chromadb.Client] = None,
    method: str = "auto"
) -> Dict[str, Any]:
    """
    Complete query pipeline with automatic routing.
    
    Args:
        question: User question
        conn: DuckDB connection (optional)
        chroma_client: ChromaDB client (optional)
        method: "sql", "rag", or "auto"
    
    Returns:
        {
            "success": bool,
            "method": str,
            "results": list (for SQL) or None,
            "answer": str (for RAG) or None,
            "chunks": list (for RAG) or None,
            "error": str
        }
    
    Mental Model: Systems Thinking
    - Pipeline: Classify → Route → Execute → Format
    - SQL: Fast, precise for structured queries
    - RAG: Better for conceptual questions
    """
    try:
        # Auto-route based on question type
        if method == "auto":
            # Simple heuristic: SQL for when/what/count, RAG for why/how/explain
            question_lower = question.lower()
            sql_keywords = ["when", "what year", "how many", "count", "list", "show"]
            rag_keywords = ["why", "how does", "explain", "describe", "what are"]
            
            if any(kw in question_lower for kw in sql_keywords):
                method = "sql"
            elif any(kw in question_lower for kw in rag_keywords):
                method = "rag"
            else:
                method = "rag"  # Default to RAG
        
        # SQL path
        if method == "sql":
            if not conn:
                return {
                    "success": False,
                    "error": "Database connection required for SQL queries"
                }
            
            # Generate SQL
            sql_result = await generate_sql(question, conn)
            if not sql_result["success"]:
                return {
                    "success": False,
                    "method": "sql",
                    "error": sql_result.get("error", "SQL generation failed")
                }
            
            # Execute SQL
            exec_result = await execute_sql(sql_result["sql"], conn)
            
            return {
                "success": exec_result["success"],
                "method": "sql",
                "sql": sql_result["sql"],
                "results": exec_result.get("rows", []),
                "error": exec_result.get("error")
            }
        
        # RAG path
        elif method == "rag":
            if not conn or not chroma_client:
                return {
                    "success": False,
                    "error": "Database and ChromaDB required for RAG queries"
                }
            
            # Hybrid search
            search_result = await hybrid_search(question, conn, chroma_client, top_k=5)
            if not search_result["success"]:
                return {
                    "success": False,
                    "method": "rag",
                    "error": search_result.get("error", "Search failed")
                }
            
            # Generate answer
            answer_result = await generate_answer(question, search_result["chunks"])
            
            return {
                "success": answer_result["success"],
                "method": "rag",
                "answer": answer_result.get("answer"),
                "chunks": search_result["chunks"],
                "error": answer_result.get("error")
            }
        
        else:
            return {
                "success": False,
                "error": f"Invalid method: {method}. Use 'sql', 'rag', or 'auto'"
            }
    
    except Exception as e:
        logger.error("query_pipeline_failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }
