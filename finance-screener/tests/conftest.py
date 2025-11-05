"""
Pytest configuration and shared fixtures for finance-screener tests.

Mental Model Applied: First Principles
- Break testing down to fundamental reusable components
- Fixtures represent core test dependencies (databases, API mocks, sample data)

Mental Model Applied: Systems Thinking
- Test fixtures form an integrated whole
- Changes to fixtures propagate across all tests
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator
import pytest
import duckdb
import chromadb
from unittest.mock import Mock, AsyncMock, MagicMock

# Mock sentence_transformers module (unavailable in Python 3.13)
# Create a mock class that can be instantiated and called
class MockSentenceTransformer:
    def __init__(self, model_name):
        pass
    
    def encode(self, texts, show_progress_bar=False):
        # Return a list matching the input size with 384-dim vectors
        return [[0.1] * 384 for _ in texts]

# Mock the module
mock_st_module = MagicMock()
mock_st_module.SentenceTransformer = MockSentenceTransformer
sys.modules['sentence_transformers'] = mock_st_module


# ============================================================================
# Session-scoped fixtures (created once per test session)
# ============================================================================

@pytest.fixture(scope="session")
def test_data_dir() -> Generator[Path, None, None]:
    """Temporary directory for test data (cleaned up after session)."""
    with tempfile.TemporaryDirectory(prefix="finance_screener_test_") as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create test.pdf with financial content
        import fitz  # PyMuPDF
        pdf_path = tmpdir_path / "test.pdf"
        doc = fitz.open()  # Create empty PDF
        page = doc.new_page()  # Add blank page
        
        # Add text with table indicators for extract_tables_with_gemini
        text_content = """Test PDF Content
        
Item 1A. Risk Factors
Production risks exist.

Revenue Table
Year    Revenue    Income
2020    $31.5B     $721M
2021    $53.8B     $5.5B
"""
        page.insert_text((72, 72), text_content)  # Insert text at 1" from top-left
        
        doc.save(str(pdf_path))
        doc.close()
        
        yield tmpdir_path


@pytest.fixture(scope="session")
def sample_sec_filing_url() -> str:
    """Sample SEC filing URL for testing."""
    return "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"


@pytest.fixture(scope="session")
def sample_sec_filing_html() -> str:
    """Sample SEC EDGAR search results HTML (mimics browse-edgar response)."""
    return """
    <html>
    <head><title>EDGAR Search Results</title></head>
    <body>
        <table class="tableFile2">
            <tr>
                <td nowrap="nowrap">10-K</td>
                <td>Annual Report</td>
                <td nowrap="nowrap">2021-02-08</td>
                <td nowrap="nowrap">
                    <a href="/cgi-bin/viewer?action=view&amp;cik=1318605&amp;accession_number=0001564590-21-004599&amp;xbrl_type=v" id="documentsbutton">Documents</a>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


@pytest.fixture(scope="session")
def sample_chunks() -> list[dict]:
    """Sample text chunks for testing embeddings and retrieval."""
    return [
        {
            "chunk_index": 0,
            "text": "Tesla's main risks include production scaling challenges and regulatory changes.",
            "section": "Item 1A: Risk Factors",
            "page": 42,
            "metadata": {"filing_type": "10-K", "fiscal_year": 2020}
        },
        {
            "chunk_index": 1,
            "text": "Revenue grew 28% year-over-year to $31.5 billion in 2020.",
            "section": "Item 7: Management Discussion",
            "page": 67,
            "metadata": {"filing_type": "10-K", "fiscal_year": 2020}
        },
        {
            "chunk_index": 2,
            "text": "EV tax credit changes could materially impact demand for our vehicles.",
            "section": "Item 1A: Risk Factors",
            "page": 47,
            "metadata": {"filing_type": "10-K", "fiscal_year": 2020}
        },
    ]


# ============================================================================
# Function-scoped fixtures (created fresh for each test)
# ============================================================================

@pytest.fixture
def duckdb_conn(test_data_dir: Path) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    DuckDB connection with test schema.
    
    Mental Model: Inversion - What can go wrong?
    - Isolate each test with fresh database
    - Auto-cleanup prevents test pollution
    """
    db_path = test_data_dir / "test_finance.duckdb"
    conn = duckdb.connect(str(db_path))
    
    # Create test schema with auto-incrementing IDs
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS filings_id_seq
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS filings (
            id INTEGER PRIMARY KEY DEFAULT nextval('filings_id_seq'),
            ticker VARCHAR NOT NULL,
            filing_url VARCHAR NOT NULL,
            filing_type VARCHAR,
            filing_date DATE,
            fiscal_year INTEGER,
            num_chunks INTEGER,
            num_tables INTEGER,
            ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, filing_url)
        )
    """)
    
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS chunks_id_seq
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY DEFAULT nextval('chunks_id_seq'),
            ticker VARCHAR NOT NULL,
            filing_url VARCHAR NOT NULL,
            chunk_index INTEGER,
            text VARCHAR,
            section VARCHAR,
            page INTEGER,
            metadata JSON
        )
    """)
    
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS tables_id_seq
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY DEFAULT nextval('tables_id_seq'),
            ticker VARCHAR NOT NULL,
            filing_url VARCHAR NOT NULL,
            table_index INTEGER,
            table_data JSON,
            caption VARCHAR,
            page INTEGER
        )
    """)
    
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS error_log_id_seq
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS error_log (
            id INTEGER PRIMARY KEY DEFAULT nextval('error_log_id_seq'),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            component VARCHAR,
            error VARCHAR,
            context JSON
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_costs (
            id INTEGER PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            service VARCHAR,
            operation VARCHAR,
            tokens_used INTEGER,
            cost_usd DECIMAL(10, 6),
            ticker VARCHAR
        )
    """)
    
    yield conn
    
    # Cleanup
    conn.close()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def chroma_client(test_data_dir: Path) -> Generator[chromadb.ClientAPI, None, None]:
    """
    ChromaDB client with test collections.
    
    Mental Model: Second Order Effects
    - Embedding tests affect retrieval tests
    - Isolated client prevents cascading failures
    """
    chroma_path = test_data_dir / "test_chroma"
    client = chromadb.PersistentClient(path=str(chroma_path))
    
    yield client
    
    # Cleanup
    for collection in client.list_collections():
        client.delete_collection(collection.name)


@pytest.fixture
def mock_anthropic_client() -> Mock:
    """
    Mock Anthropic API client for testing without API calls.
    
    Mental Model: Inversion - Avoid what we don't want
    - Don't make real API calls in tests (cost, speed, reliability)
    - Mock provides deterministic responses
    """
    mock = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text="Mocked Claude response")]
    mock_response.usage = Mock(input_tokens=100, output_tokens=50)
    mock.messages.create = AsyncMock(return_value=mock_response)
    return mock


@pytest.fixture
def mock_google_client() -> Mock:
    """
    Mock Google Generative AI client for testing without API calls.
    """
    mock = Mock()
    mock_response = Mock()
    mock_response.text = "Mocked Gemini response with table extraction"
    mock_response.usage_metadata = Mock(prompt_token_count=80, candidates_token_count=40)
    mock.generate_content = Mock(return_value=mock_response)
    return mock


@pytest.fixture
def mock_sec_response(sample_sec_filing_html: str) -> Mock:
    """
    Mock SEC API response for testing without network calls.
    """
    mock = Mock()
    mock.status_code = 200
    mock.text = sample_sec_filing_html
    mock.headers = {"Content-Type": "text/html"}
    return mock


@pytest.fixture
def env_vars(test_data_dir: Path, monkeypatch) -> dict[str, str]:
    """
    Set test environment variables.
    
    Mental Model: Interdependencies
    - All components depend on config
    - Centralized fixture ensures consistency
    """
    env = {
        "ANTHROPIC_API_KEY": "test-key-anthropic",
        "GOOGLE_API_KEY": "test-key-google",
        "SEC_USER_AGENT": "TestApp/1.0 (test@example.com)",
        "DUCKDB_PATH": str(test_data_dir / "test_finance.duckdb"),
        "CHROMA_PATH": str(test_data_dir / "test_chroma"),
        "MONTHLY_BUDGET_USD": "50.0",
        "TEST_MODE": "true",
    }
    
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    
    return env


# ============================================================================
# Custom assertions and utilities
# ============================================================================

def assert_valid_filing_metadata(metadata: dict) -> None:
    """
    Assert filing metadata has required fields.
    
    Mental Model: First Principles
    - What is the minimal valid filing structure?
    """
    required_fields = ["ticker", "filing_url", "filing_type"]
    for field in required_fields:
        assert field in metadata, f"Missing required field: {field}"
        assert metadata[field], f"Empty value for field: {field}"


def assert_valid_chunk(chunk: dict) -> None:
    """
    Assert chunk has required fields and valid structure.
    """
    required_fields = ["chunk_index", "text", "section"]
    for field in required_fields:
        assert field in chunk, f"Missing required field: {field}"
    
    assert isinstance(chunk["chunk_index"], int), "chunk_index must be integer"
    assert len(chunk["text"]) > 0, "Chunk text cannot be empty"
    assert len(chunk["text"]) <= 2000, "Chunk text too long (max 2000 chars)"


def assert_no_errors_logged(duckdb_conn: duckdb.DuckDBPyConnection) -> None:
    """
    Assert no errors were logged during test execution.
    
    Mental Model: Inversion
    - Success = absence of errors
    """
    result = duckdb_conn.execute("SELECT COUNT(*) FROM error_log").fetchone()
    assert result[0] == 0, f"Found {result[0]} errors in error_log"


# ============================================================================
# Test markers configuration
# ============================================================================

def pytest_configure(config):
    """
    Register custom markers.
    """
    config.addinivalue_line(
        "markers", "unit: Unit tests (no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (requires databases)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (API calls, large file processing)"
    )
    config.addinivalue_line(
        "markers", "api: Tests requiring API keys"
    )
