"""
Test suite for query tool - Text-to-SQL and Hybrid RAG.

Mental Model: Systems Thinking
- Query pipeline: Question → SQL/RAG → Results → Rerank
- Each component tested independently, then integrated

Mental Model: Second Order Effects
- Query quality affects user trust
- Slow queries affect user experience
- Cost per query affects scalability

Test-Driven Development:
1. Write tests FIRST (this file)
2. Run tests (all should fail)
3. Implement query.py
4. Run tests (all should pass)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import duckdb
import chromadb


# ============================================================================
# Text-to-SQL Tests (DSPy-powered)
# ============================================================================

@pytest.mark.unit
class TestTextToSQL:
    """Test SQL generation from natural language queries."""
    
    @pytest.mark.asyncio
    async def test_generate_sql_revenue_query(self, env_vars: dict) -> None:
        """
        Test SQL generation for revenue queries.
        
        Given: Natural language query about revenue
        When: generate_sql is called
        Then: Returns valid SQL query
        
        Mental Model: First Principles
        - User intent: Find revenue data
        - SQL: SELECT revenue FROM filings WHERE ...
        """
        from skill_seeker_mcp.finance_tools.query import generate_sql
        
        question = "What was Tesla's revenue in 2020?"
        
        with patch('anthropic.Anthropic') as mock_anthropic:
            # Mock Claude API response with SQL
            mock_response = Mock()
            mock_response.content = [Mock(text="""
            SELECT ticker, fiscal_year, revenue 
            FROM filings 
            WHERE ticker = 'TSLA' AND fiscal_year = 2020
            """)]
            mock_anthropic.return_value.messages.create.return_value = mock_response
            
            result = await generate_sql(question=question)
        
        assert result["success"] is True
        assert "SELECT" in result["sql"].upper()
        assert "revenue" in result["sql"].lower()
        assert "TSLA" in result["sql"] or "Tesla" in result["sql"]
    
    @pytest.mark.asyncio
    async def test_generate_sql_with_schema_context(
        self,
        duckdb_conn,
        env_vars: dict
    ) -> None:
        """
        Test SQL generation uses database schema.
        
        Given: Database with schema (filings, chunks, tables)
        When: generate_sql is called
        Then: SQL uses correct table/column names
        
        Mental Model: Systems Thinking
        - Schema awareness prevents SQL errors
        - Correct column names improve query success
        """
        from skill_seeker_mcp.finance_tools.query import generate_sql
        
        question = "Show me all 10-K filings from 2020"
        
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_response = Mock()
            mock_response.content = [Mock(text="""
            SELECT ticker, filing_type, fiscal_year, filing_date
            FROM filings
            WHERE filing_type = '10-K' AND fiscal_year = 2020
            """)]
            mock_anthropic.return_value.messages.create.return_value = mock_response
            
            result = await generate_sql(
                question=question,
                conn=duckdb_conn
            )
        
        assert result["success"] is True
        assert "filings" in result["sql"].lower()
        assert "10-K" in result["sql"] or "10K" in result["sql"]
    
    @pytest.mark.asyncio
    async def test_generate_sql_handles_ambiguous_query(self, env_vars: dict) -> None:
        """
        Test SQL generation handles ambiguous questions.
        
        Given: Vague query without specifics
        When: generate_sql is called
        Then: Returns SQL with reasonable defaults
        
        Mental Model: Inversion
        - What makes a query fail? → Ambiguity
        - Solution: Provide clarifying defaults
        """
        from skill_seeker_mcp.finance_tools.query import generate_sql
        
        question = "Show me some data"
        
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_response = Mock()
            mock_response.content = [Mock(text="""
            SELECT * FROM filings LIMIT 10
            """)]
            mock_anthropic.return_value.messages.create.return_value = mock_response
            
            result = await generate_sql(question=question)
        
        assert result["success"] is True
        assert "LIMIT" in result["sql"].upper()


# ============================================================================
# Hybrid RAG Tests (BM25 + Vector Search + RRF)
# ============================================================================

@pytest.mark.unit
class TestHybridRAG:
    """Test hybrid retrieval-augmented generation."""
    
    @pytest.mark.asyncio
    async def test_hybrid_search_combines_bm25_and_vector(
        self,
        duckdb_conn,
        chroma_client,
        sample_chunks: list[dict]
    ) -> None:
        """
        Test hybrid search combines BM25 and vector search.
        
        Given: Chunks in DuckDB and ChromaDB
        When: hybrid_search is called
        Then: Returns results from both methods (BM25 + vector)
        
        Mental Model: Systems Thinking
        - BM25: Keyword-based (fast, exact matches)
        - Vector: Semantic (slower, meaning matches)
        - Hybrid: Best of both worlds
        """
        from skill_seeker_mcp.finance_tools.query import hybrid_search
        
        # Store sample chunks in databases
        for chunk in sample_chunks:
            # Store in DuckDB
            duckdb_conn.execute(
                "INSERT INTO chunks (ticker, filing_url, chunk_index, text, section) VALUES (?, ?, ?, ?, ?)",
                ['TSLA', 'https://sec.gov/test.htm', chunk["chunk_index"], chunk["text"], chunk["section"]]
            )
            
            # Store in ChromaDB
            chroma_collection = chroma_client.get_or_create_collection("test_chunks")
            chroma_collection.add(
                ids=[f"chunk_{chunk['chunk_index']}"],
                documents=[chunk["text"]],
                embeddings=[[0.1] * 384],  # Mock embedding
                metadatas=[{"section": chunk["section"]}]
            )
        
        query = "What are Tesla's main risks?"
        
        results = await hybrid_search(
            query=query,
            conn=duckdb_conn,
            chroma_client=chroma_client,
            top_k=5
        )
        
        assert results["success"] is True
        assert len(results["chunks"]) > 0
        assert all("text" in chunk for chunk in results["chunks"])
        assert all("score" in chunk for chunk in results["chunks"])
        assert all("method" in chunk for chunk in results["chunks"])  # 'bm25', 'vector', or 'rrf'
    
    @pytest.mark.asyncio
    async def test_bm25_search_keyword_matching(
        self,
        duckdb_conn,
        sample_chunks: list[dict]
    ) -> None:
        """
        Test BM25 search for keyword matching.
        
        Given: Text chunks in DuckDB
        When: bm25_search is called with keywords
        Then: Returns chunks with matching keywords (ranked)
        
        Mental Model: First Principles
        - BM25 = TF-IDF + document length normalization
        - Exact keyword matches rank higher
        """
        from skill_seeker_mcp.finance_tools.query import bm25_search
        
        # Store sample chunks
        for chunk in sample_chunks:
            duckdb_conn.execute(
                "INSERT INTO chunks (ticker, filing_url, chunk_index, text, section) VALUES (?, ?, ?, ?, ?)",
                ['TSLA', 'https://sec.gov/test.htm', chunk["chunk_index"], chunk["text"], chunk["section"]]
            )
        
        query = "revenue growth"
        
        results = await bm25_search(
            query=query,
            conn=duckdb_conn,
            top_k=3
        )
        
        assert results["success"] is True
        assert len(results["chunks"]) <= 3
        # Check that results contain 'revenue' keyword
        assert any("revenue" in chunk["text"].lower() for chunk in results["chunks"])
    
    @pytest.mark.asyncio
    async def test_vector_search_semantic_similarity(
        self,
        chroma_client,
        sample_chunks: list[dict]
    ) -> None:
        """
        Test vector search for semantic similarity.
        
        Given: Embeddings in ChromaDB
        When: vector_search is called
        Then: Returns semantically similar chunks
        
        Mental Model: First Principles
        - Embeddings capture meaning, not just keywords
        - Cosine similarity measures semantic closeness
        """
        from skill_seeker_mcp.finance_tools.query import vector_search
        
        # Store sample chunks with embeddings
        chroma_collection = chroma_client.get_or_create_collection("test_chunks")
        for chunk in sample_chunks:
            chroma_collection.add(
                ids=[f"chunk_{chunk['chunk_index']}"],
                documents=[chunk["text"]],
                embeddings=[[0.1] * 384],  # Mock embedding
                metadatas={"section": chunk["section"]}
            )
        
        query = "financial risks and challenges"
        
        results = await vector_search(
            query=query,
            chroma_client=chroma_client,
            top_k=3
        )
        
        assert results["success"] is True
        assert len(results["chunks"]) <= 3
        assert all("text" in chunk for chunk in results["chunks"])
        assert all("score" in chunk for chunk in results["chunks"])
    
    @pytest.mark.asyncio
    async def test_reciprocal_rank_fusion(self) -> None:
        """
        Test Reciprocal Rank Fusion (RRF) for combining rankings.
        
        Given: Results from BM25 and vector search
        When: reciprocal_rank_fusion is called
        Then: Returns fused rankings (RRF scores)
        
        Mental Model: Systems Thinking
        - RRF combines multiple rankings without score normalization
        - Formula: RRF(d) = Σ 1/(k + rank_i(d)) for each ranker i
        - k=60 is standard constant
        """
        from skill_seeker_mcp.finance_tools.query import reciprocal_rank_fusion
        
        bm25_results = [
            {"chunk_id": 1, "text": "Revenue grew 28%", "score": 15.5},
            {"chunk_id": 2, "text": "Production scaling risks", "score": 12.3},
            {"chunk_id": 3, "text": "EV tax credits", "score": 8.7}
        ]
        
        vector_results = [
            {"chunk_id": 2, "text": "Production scaling risks", "score": 0.92},
            {"chunk_id": 1, "text": "Revenue grew 28%", "score": 0.85},
            {"chunk_id": 4, "text": "Regulatory changes", "score": 0.78}
        ]
        
        fused_results = reciprocal_rank_fusion(
            bm25_results=bm25_results,
            vector_results=vector_results,
            k=60
        )
        
        assert len(fused_results) == 4  # Unique chunks across both
        assert all("rrf_score" in chunk for chunk in fused_results)
        # Check RRF scoring: chunk_id=2 appears in both, should rank high
        chunk_2 = next(c for c in fused_results if c["chunk_id"] == 2)
        assert chunk_2["rrf_score"] > 0


# ============================================================================
# Query Execution Tests
# ============================================================================

@pytest.mark.unit
class TestQueryExecution:
    """Test SQL query execution and result formatting."""
    
    @pytest.mark.asyncio
    async def test_execute_sql_returns_results(
        self,
        duckdb_conn
    ) -> None:
        """
        Test SQL execution returns formatted results.
        
        Given: Valid SQL query
        When: execute_sql is called
        Then: Returns query results as list of dicts
        
        Mental Model: First Principles
        - SQL execution = parse → optimize → execute → format
        - Results should be JSON-serializable
        """
        from skill_seeker_mcp.finance_tools.query import execute_sql
        
        # Insert test data
        duckdb_conn.execute("""
            INSERT INTO filings (ticker, filing_url, filing_type, fiscal_year, filing_date)
            VALUES ('TSLA', 'https://sec.gov/test.htm', '10-K', 2020, '2021-02-08')
        """)
        
        sql = "SELECT ticker, fiscal_year FROM filings WHERE ticker = 'TSLA'"
        
        result = await execute_sql(sql=sql, conn=duckdb_conn)
        
        assert result["success"] is True
        assert len(result["rows"]) == 1
        assert result["rows"][0]["ticker"] == "TSLA"
        assert result["rows"][0]["fiscal_year"] == 2020
    
    @pytest.mark.asyncio
    async def test_execute_sql_handles_syntax_errors(
        self,
        duckdb_conn
    ) -> None:
        """
        Test SQL execution handles syntax errors gracefully.
        
        Given: Invalid SQL (syntax error)
        When: execute_sql is called
        Then: Returns error message (doesn't crash)
        
        Mental Model: Inversion
        - What causes failure? → Invalid SQL
        - Solution: Try-except with clear error messages
        """
        from skill_seeker_mcp.finance_tools.query import execute_sql
        
        invalid_sql = "SELCT * FORM filings"  # Typos
        
        result = await execute_sql(sql=invalid_sql, conn=duckdb_conn)
        
        assert result["success"] is False
        assert "error" in result
        assert len(result.get("rows", [])) == 0


# ============================================================================
# Answer Generation Tests (RAG with Claude)
# ============================================================================

@pytest.mark.unit
class TestAnswerGeneration:
    """Test answer generation from retrieved context."""
    
    @pytest.mark.asyncio
    async def test_generate_answer_from_chunks(self, env_vars: dict) -> None:
        """
        Test answer generation from retrieved chunks.
        
        Given: User question + retrieved chunks
        When: generate_answer is called
        Then: Returns natural language answer citing sources
        
        Mental Model: Systems Thinking
        - RAG = Retrieve (chunks) + Augment (context) + Generate (answer)
        - Citations provide provenance
        """
        from skill_seeker_mcp.finance_tools.query import generate_answer
        
        question = "What are Tesla's main risks?"
        chunks = [
            {
                "text": "Tesla's main risks include production scaling challenges and regulatory changes.",
                "section": "Item 1A: Risk Factors",
                "page": 42,
                "score": 0.95
            },
            {
                "text": "Revenue grew 28% year-over-year to $31.5 billion in 2020.",
                "section": "Item 7: MD&A",
                "page": 67,
                "score": 0.82
            }
        ]
        
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_response = Mock()
            mock_response.content = [Mock(text="""
            Tesla's main risks include production scaling challenges and regulatory changes [1].
            
            Sources:
            [1] Item 1A: Risk Factors, page 42
            """)]
            mock_anthropic.return_value.messages.create.return_value = mock_response
            
            result = await generate_answer(
                question=question,
                chunks=chunks
            )
        
        assert result["success"] is True
        assert "answer" in result
        assert len(result["answer"]) > 0
        # Check for citations (either [1] references or "Sources:" section)
        assert "[1]" in result["answer"] or "sources" in result["answer"].lower()
    
    @pytest.mark.asyncio
    async def test_generate_answer_handles_no_context(self) -> None:
        """
        Test answer generation when no relevant chunks found.
        
        Given: Question with empty chunk list
        When: generate_answer is called
        Then: Returns "no information found" message
        
        Mental Model: Inversion
        - What if retrieval fails? → No context to generate from
        - Solution: Graceful degradation with helpful message
        """
        from skill_seeker_mcp.finance_tools.query import generate_answer
        
        question = "What is Tesla's quantum computing strategy?"
        chunks = []  # No relevant chunks found
        
        result = await generate_answer(
            question=question,
            chunks=chunks
        )
        
        assert result["success"] is True
        assert "no information" in result["answer"].lower() or \
               "not found" in result["answer"].lower()


# ============================================================================
# End-to-End Query Pipeline Tests
# ============================================================================

@pytest.mark.slow
@pytest.mark.integration
class TestQueryPipeline:
    """Test complete query pipeline (SQL + RAG)."""
    
    @pytest.mark.asyncio
    async def test_query_pipeline_sql_path(
        self,
        duckdb_conn,
        env_vars: dict
    ) -> None:
        """
        Test query pipeline with SQL question.
        
        Given: Structured question (revenue, dates, numbers)
        When: query_pipeline is called
        Then: Routes to text-to-SQL → executes → returns data
        
        Mental Model: Systems Thinking
        - Pipeline: Classify → Route → Execute → Format
        - SQL path: Faster, precise for structured queries
        """
        from skill_seeker_mcp.finance_tools.query import query_pipeline
        
        # Insert test data
        duckdb_conn.execute("""
            INSERT INTO filings (ticker, filing_url, filing_type, fiscal_year, filing_date)
            VALUES ('TSLA', 'https://sec.gov/test.htm', '10-K', 2020, '2021-02-08')
        """)
        
        question = "What filings do we have for Tesla in 2020?"
        
        with patch('anthropic.Anthropic') as mock_anthropic:
            # Mock SQL generation
            mock_response = Mock()
            mock_response.content = [Mock(text="""
            SELECT ticker, filing_type, fiscal_year
            FROM filings
            WHERE ticker = 'TSLA' AND fiscal_year = 2020
            """)]
            mock_anthropic.return_value.messages.create.return_value = mock_response
            
            result = await query_pipeline(
                question=question,
                conn=duckdb_conn,
                method="sql"
            )
        
        assert result["success"] is True
        assert result["method"] == "sql"
        assert len(result["results"]) > 0
    
    @pytest.mark.asyncio
    async def test_query_pipeline_rag_path(
        self,
        duckdb_conn,
        chroma_client,
        sample_chunks: list[dict],
        env_vars: dict
    ) -> None:
        """
        Test query pipeline with RAG question.
        
        Given: Unstructured question (why, how, explain)
        When: query_pipeline is called
        Then: Routes to hybrid RAG → retrieve → generate answer
        
        Mental Model: Systems Thinking
        - Pipeline: Classify → Retrieve (hybrid) → Generate (Claude)
        - RAG path: Better for conceptual questions
        """
        from skill_seeker_mcp.finance_tools.query import query_pipeline
        
        # Store sample chunks
        for chunk in sample_chunks:
            duckdb_conn.execute(
                "INSERT INTO chunks (ticker, filing_url, chunk_index, text, section) VALUES (?, ?, ?, ?, ?)",
                ['TSLA', 'https://sec.gov/test.htm', chunk["chunk_index"], chunk["text"], chunk["section"]]
            )
        
        question = "Why is Tesla facing production risks?"
        
        with patch('anthropic.Anthropic') as mock_anthropic:
            # Mock answer generation
            mock_response = Mock()
            mock_response.content = [Mock(text="""
            Tesla faces production scaling challenges due to rapid growth
            and complex manufacturing processes [1].
            
            Sources:
            [1] Item 1A: Risk Factors
            """)]
            mock_anthropic.return_value.messages.create.return_value = mock_response
            
            result = await query_pipeline(
                question=question,
                conn=duckdb_conn,
                chroma_client=chroma_client,
                method="rag"
            )
        
        assert result["success"] is True
        assert result["method"] == "rag"
        assert "answer" in result
        assert len(result["chunks"]) > 0


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.unit
class TestQueryErrorHandling:
    """Test error handling in query pipeline."""
    
    @pytest.mark.asyncio
    async def test_database_connection_failure(self) -> None:
        """
        Test query handles database connection errors.
        
        Mental Model: Inversion
        - What can go wrong? → Database unavailable
        - Solution: Try-except with clear error
        """
        from skill_seeker_mcp.finance_tools.query import execute_sql
        
        # Create closed connection
        conn = duckdb.connect(":memory:")
        conn.close()
        
        result = await execute_sql(
            sql="SELECT * FROM filings",
            conn=conn
        )
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_empty_query_handling(self) -> None:
        """
        Test query handles empty/null questions.
        
        Mental Model: First Principles
        - Invalid input → Invalid output
        - Validate early, fail fast
        """
        from skill_seeker_mcp.finance_tools.query import generate_sql
        
        result = await generate_sql(question="")
        
        assert result["success"] is False
        assert "error" in result
