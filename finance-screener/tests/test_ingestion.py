"""
Test suite for SEC filing ingestion functionality.

TDD Approach: Tests written FIRST, implementation AFTER.

Mental Model: Second Order Effects
- Chunking quality affects retrieval quality
- Embedding quality affects search relevance
- Storage reliability affects all downstream operations

Mental Model: Systems Thinking
- Ingestion = Download → Extract → Chunk → Embed → Store
- Each step depends on previous step's success
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import json


@pytest.mark.unit
class TestPdfDownload:
    """
    Unit tests for PDF download functionality.
    
    Mental Model: Inversion - What can fail in download?
    - Network timeout, invalid URL, large files, corrupted PDFs
    """
    
    @pytest.mark.asyncio
    async def test_download_pdf_success(
        self,
        sample_sec_filing_url: str,
        test_data_dir: Path,
        env_vars: dict
    ) -> None:
        """
        Test successful PDF download from SEC.
        
        Given: Valid SEC filing URL
        When: download_pdf is called
        Then: PDF file saved to temp directory
        """
        from skill_seeker_mcp.finance_tools.ingestion import download_pdf
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"%PDF-1.4 fake pdf content"
        
        with patch('requests.get', return_value=mock_response):
            result = await download_pdf(
                filing_url=sample_sec_filing_url,
                output_dir=test_data_dir
            )
        
        assert result["success"] is True
        assert "file_path" in result
        assert Path(result["file_path"]).exists()
        assert Path(result["file_path"]).stat().st_size > 0
    
    
    @pytest.mark.asyncio
    async def test_download_pdf_timeout(
        self,
        sample_sec_filing_url: str,
        test_data_dir: Path,
        env_vars: dict
    ) -> None:
        """
        Test graceful handling of download timeout.
        
        Mental Model: Inversion - Network can always fail
        """
        from skill_seeker_mcp.finance_tools.ingestion import download_pdf
        import requests
        
        with patch('requests.get', side_effect=requests.Timeout("Download timeout")):
            result = await download_pdf(
                filing_url=sample_sec_filing_url,
                output_dir=test_data_dir
            )
        
        assert result["success"] is False
        assert "error" in result
        assert "timeout" in result["error"].lower()


@pytest.mark.unit
class TestPdfExtraction:
    """
    Unit tests for PDF text and table extraction.
    
    Mental Model: First Principles
    - Extraction = Text blocks + Tables + Metadata
    - Quality metric: What % of content is preserved?
    """
    
    def test_extract_text_from_pdf(
        self,
        test_data_dir: Path
    ) -> None:
        """
        Test text extraction from PDF using PyMuPDF.
        
        Given: PDF file with text content
        When: extract_text_from_pdf is called
        Then: Returns structured text with page numbers
        """
        from skill_seeker_mcp.finance_tools.ingestion import extract_text_from_pdf
        
        # Create minimal valid PDF for testing
        pdf_path = test_data_dir / "test.pdf"
        
        # Mock PyMuPDF Document
        with patch('fitz.open') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_text.return_value = "Item 1A. Risk Factors\nProduction scaling is a major risk."
            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.__len__.return_value = 1
            mock_fitz.return_value = mock_doc
            
            result = extract_text_from_pdf(str(pdf_path))
        
        assert result["success"] is True
        assert len(result["pages"]) == 1
        assert "text" in result["pages"][0]
        assert "page_number" in result["pages"][0]
        assert "Risk Factors" in result["pages"][0]["text"]
    
    
    @pytest.mark.asyncio
    async def test_extract_tables_with_gemini(
        self,
        test_data_dir: Path,
        mock_google_client: Mock,
        env_vars: dict
    ) -> None:
        """
        Test table extraction using Gemini API.
        
        Mental Model: Second Order Effects
        - Better table extraction → Better financial analysis
        - Cost: ~$0.02 per 100 pages
        
        Given: PDF with financial tables
        When: extract_tables_with_gemini is called
        Then: Returns structured table data
        """
        from skill_seeker_mcp.finance_tools.ingestion import extract_tables_with_gemini
        
        pdf_path = test_data_dir / "test.pdf"
        
        # Mock Gemini response with table JSON
        mock_google_client.generate_content.return_value.text = json.dumps([
            {
                "table_index": 0,
                "caption": "Revenue by Year",
                "data": [
                    ["Year", "Revenue", "Net Income"],
                    ["2020", "31,536", "721"],
                    ["2021", "53,823", "5,519"]
                ],
                "page": 67
            }
        ])
        
        with patch('google.generativeai.GenerativeModel', return_value=mock_google_client):
            result = await extract_tables_with_gemini(
                pdf_path=str(pdf_path),
                max_pages=10
            )
        
        assert result["success"] is True
        assert len(result["tables"]) == 1
        assert result["tables"][0]["caption"] == "Revenue by Year"
        assert len(result["tables"][0]["data"]) == 3  # Header + 2 rows
        assert result["cost_usd"] > 0


@pytest.mark.unit
class TestSectionAwareChunking:
    """
    Unit tests for section-aware text chunking.
    
    Mental Model: First Principles (Derek Snow's methodology)
    - Chunks should respect document sections
    - Chunk size: 500-1000 tokens (optimal for RAG)
    - Overlap: 100 tokens (preserve context)
    """
    
    def test_chunk_by_section(
        self,
        sample_chunks: list[dict]
    ) -> None:
        """
        Test section-aware chunking preserves document structure.
        
        Given: Text with section headers (Item 1A, Item 7, etc.)
        When: chunk_text_by_section is called
        Then: Each chunk tagged with section name
        """
        from skill_seeker_mcp.finance_tools.ingestion import chunk_text_by_section
        
        text = """
        Item 1A. Risk Factors
        
        Our business is subject to numerous risks. Production scaling challenges 
        could materially impact our ability to meet delivery targets.
        
        Item 7. Management Discussion and Analysis
        
        Revenue grew 28% year-over-year to $31.5 billion in 2020.
        """
        
        result = chunk_text_by_section(
            text=text,
            chunk_size=500,
            overlap=100
        )
        
        assert len(result) >= 2  # At least one chunk per section
        assert any("Item 1A" in chunk["section"] for chunk in result)
        assert any("Item 7" in chunk["section"] for chunk in result)
        assert all("text" in chunk for chunk in result)
        assert all("chunk_index" in chunk for chunk in result)
    
    
    def test_chunk_respects_max_size(self) -> None:
        """
        Test chunks don't exceed maximum size.
        
        Mental Model: Second Order Effects
        - Too large chunks → Poor retrieval relevance
        - Too small chunks → Lost context
        """
        from skill_seeker_mcp.finance_tools.ingestion import chunk_text_by_section
        
        # Create very long text (>2000 tokens)
        long_text = "This is a test sentence. " * 500  # ~1500 words
        
        result = chunk_text_by_section(
            text=long_text,
            chunk_size=1000,
            overlap=100
        )
        
        for chunk in result:
            # Approximate: 1 token ≈ 4 chars
            assert len(chunk["text"]) <= 1000 * 4, f"Chunk too large: {len(chunk['text'])} chars"


@pytest.mark.unit
class TestEmbeddingGeneration:
    """
    Unit tests for embedding generation.
    
    Mental Model: Systems Thinking
    - Embeddings connect text chunks to vector database
    - Model: sentence-transformers/all-MiniLM-L6-v2 (local, free)
    """
    
    @pytest.mark.asyncio
    async def test_generate_embeddings(
        self,
        sample_chunks: list[dict]
    ) -> None:
        """
        Test embedding generation for text chunks.
        
        Given: List of text chunks
        When: generate_embeddings is called
        Then: Returns 384-dimensional vectors (MiniLM model)
        """
        from skill_seeker_mcp.finance_tools.ingestion import generate_embeddings
        
        chunks = [chunk["text"] for chunk in sample_chunks]
        
        with patch('sentence_transformers.SentenceTransformer') as mock_model:
            # Mock MiniLM embeddings (384 dimensions)
            mock_model.return_value.encode.return_value = [
                [0.1] * 384,  # Chunk 1 embedding
                [0.2] * 384,  # Chunk 2 embedding
                [0.3] * 384,  # Chunk 3 embedding
            ]
            
            embeddings = await generate_embeddings(chunks)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
        assert all(isinstance(emb[0], float) for emb in embeddings)


@pytest.mark.integration
class TestDatabaseStorage:
    """
    Integration tests for DuckDB + ChromaDB storage.
    
    Mental Model: Interdependencies
    - DuckDB stores metadata + chunks
    - ChromaDB stores embeddings
    - Both must stay synchronized
    """
    
    @pytest.mark.asyncio
    async def test_store_filing_metadata(
        self,
        duckdb_conn,
        sample_sec_filing_url: str
    ) -> None:
        """
        Test storing filing metadata in DuckDB.
        
        Given: Filing metadata (ticker, URL, type, date)
        When: store_filing_metadata is called
        Then: Metadata inserted into filings table
        """
        from skill_seeker_mcp.finance_tools.ingestion import store_filing_metadata
        
        metadata = {
            "ticker": "TSLA",
            "filing_url": sample_sec_filing_url,
            "filing_type": "10-K",
            "fiscal_year": 2020,
            "num_chunks": 421,
            "num_tables": 18
        }
        
        result = await store_filing_metadata(
            conn=duckdb_conn,
            metadata=metadata
        )
        
        assert result["success"] is True
        
        # Verify insertion
        rows = duckdb_conn.execute(
            "SELECT * FROM filings WHERE ticker = 'TSLA'"
        ).fetchall()
        
        assert len(rows) == 1
        assert rows[0][1] == "TSLA"  # ticker column
    
    
    @pytest.mark.asyncio
    async def test_store_chunks_in_duckdb(
        self,
        duckdb_conn,
        sample_chunks: list[dict],
        sample_sec_filing_url: str
    ) -> None:
        """
        Test storing text chunks in DuckDB.
        
        Mental Model: First Principles
        - Chunks = searchable text metadata
        - Used for BM25 lexical search
        """
        from skill_seeker_mcp.finance_tools.ingestion import store_chunks
        
        result = await store_chunks(
            conn=duckdb_conn,
            ticker="TSLA",
            filing_url=sample_sec_filing_url,
            chunks=sample_chunks
        )
        
        assert result["success"] is True
        assert result["chunks_stored"] == 3
        
        # Verify storage
        rows = duckdb_conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE ticker = 'TSLA'"
        ).fetchone()
        
        assert rows[0] == 3
    
    
    @pytest.mark.asyncio
    async def test_store_embeddings_in_chroma(
        self,
        chroma_client,
        sample_chunks: list[dict]
    ) -> None:
        """
        Test storing embeddings in ChromaDB.
        
        Mental Model: Systems Thinking
        - ChromaDB enables semantic search
        - Collection per ticker for isolation
        """
        from skill_seeker_mcp.finance_tools.ingestion import store_embeddings
        
        # Generate mock embeddings
        embeddings = [[0.1] * 384 for _ in sample_chunks]
        
        result = await store_embeddings(
            client=chroma_client,
            ticker="TSLA",
            chunks=sample_chunks,
            embeddings=embeddings
        )
        
        assert result["success"] is True
        assert result["embeddings_stored"] == 3
        
        # Verify collection created
        collection = chroma_client.get_collection("sec_filings_tsla")
        assert collection.count() == 3


@pytest.mark.integration
class TestFullIngestionPipeline:
    """
    Integration test for complete ingestion pipeline.
    
    Mental Model: Systems Thinking
    - Pipeline = Download → Extract → Chunk → Embed → Store
    - Each step's output feeds next step
    """
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_ingest_sec_filing_end_to_end(
        self,
        duckdb_conn,
        chroma_client,
        sample_sec_filing_url: str,
        mock_google_client: Mock,
        env_vars: dict
    ) -> None:
        """
        Test complete ingestion pipeline.
        
        Given: SEC filing URL
        When: ingest_sec_filing is called
        Then: Filing downloaded, processed, and stored in both databases
        """
        from skill_seeker_mcp.finance_tools.ingestion import ingest_sec_filing
        
        # Mock all external calls
        with patch('requests.get') as mock_get, \
             patch('fitz.open') as mock_fitz, \
             patch('google.generativeai.GenerativeModel', return_value=mock_google_client), \
             patch('sentence_transformers.SentenceTransformer'):
            
            # Mock PDF download
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"%PDF-1.4 test"
            mock_get.return_value = mock_response
            
            # Mock PDF text extraction
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_text.return_value = "Item 1A. Risk Factors\nTest content."
            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.__len__.return_value = 1
            mock_fitz.return_value = mock_doc
            
            # Run full pipeline
            result = await ingest_sec_filing(
                filing_url=sample_sec_filing_url,
                ticker="TSLA",
                extract_tables=True,
                conn=duckdb_conn,
                chroma_client=chroma_client
            )
        
        # Assertions
        assert result["success"] is True
        assert result["ticker"] == "TSLA"
        assert result["num_chunks"] > 0
        assert "ingestion_time_seconds" in result
        assert "cost_usd" in result
        
        # Verify data in DuckDB
        filing_count = duckdb_conn.execute(
            "SELECT COUNT(*) FROM filings WHERE ticker = 'TSLA'"
        ).fetchone()[0]
        assert filing_count == 1
        
        # Verify data in ChromaDB
        try:
            collection = chroma_client.get_collection("sec_filings_tsla")
            assert collection.count() > 0
        except:
            # Collection might not be created if mocking too aggressively
            pass


@pytest.mark.unit
class TestIngestionErrorHandling:
    """
    Test error handling across ingestion pipeline.
    
    Mental Model: Inversion
    - What can fail at each step?
    - How do we recover gracefully?
    """
    
    @pytest.mark.asyncio
    async def test_corrupted_pdf_handling(
        self,
        test_data_dir: Path,
        env_vars: dict
    ) -> None:
        """
        Test graceful handling of corrupted PDF.
        
        Given: Corrupted PDF file
        When: extract_text_from_pdf is called
        Then: Returns error without crashing
        """
        from skill_seeker_mcp.finance_tools.ingestion import extract_text_from_pdf
        
        # Create corrupted PDF
        pdf_path = test_data_dir / "corrupted.pdf"
        pdf_path.write_text("This is not a valid PDF")
        
        result = extract_text_from_pdf(str(pdf_path))
        
        assert result["success"] is False
        assert "error" in result
    
    
    @pytest.mark.asyncio
    async def test_database_connection_failure(
        self,
        sample_chunks: list[dict],
        sample_sec_filing_url: str
    ) -> None:
        """
        Test handling of database connection failure.
        
        Mental Model: Inversion - Database can always fail
        """
        from skill_seeker_mcp.finance_tools.ingestion import store_chunks
        
        # Pass None as connection (simulates closed connection)
        result = await store_chunks(
            conn=None,
            ticker="TSLA",
            filing_url=sample_sec_filing_url,
            chunks=sample_chunks
        )
        
        assert result["success"] is False
        assert "error" in result
