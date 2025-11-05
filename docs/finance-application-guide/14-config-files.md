# Configuration Files

**Copy-paste ready JSON configuration files** for all components of your finance application.

All configs are production-tested and follow Derek Snow's best practices.

---

## File 1: DuckDB Schema Configuration

**File**: `configs/duckdb_schema.sql`

```sql
-- Finance Application DuckDB Schema
-- Version: 1.0.0
-- Compatible with: DuckDB 0.9.0+

-- ============================================================================
-- FILINGS METADATA TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS filings (
    id INTEGER PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    filing_url VARCHAR NOT NULL,
    filing_type VARCHAR NOT NULL,  -- '10-K', '10-Q', '8-K'
    filing_date DATE NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER,  -- NULL for 10-K, 1-4 for 10-Q
    company_name VARCHAR,
    cik VARCHAR,  -- SEC Central Index Key
    num_chunks INTEGER DEFAULT 0,
    num_tables INTEGER DEFAULT 0,
    pdf_size_mb DECIMAL(10, 2),
    processing_time_sec DECIMAL(10, 2),
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,  -- Additional metadata (e.g., {"sector": "Technology"})
    UNIQUE(ticker, filing_url)
);

-- ============================================================================
-- TEXT CHUNKS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    filing_url VARCHAR NOT NULL,
    chunk_index INTEGER NOT NULL,
    text VARCHAR NOT NULL,
    section VARCHAR,  -- e.g., "Item 1A: Risk Factors", "Item 7: MD&A"
    page INTEGER,
    char_count INTEGER,
    token_count INTEGER,  -- Approximate token count (for cost estimation)
    metadata JSON,  -- e.g., {"subsection": "Competition", "importance": "high"}
    embedding_id VARCHAR,  -- Reference to ChromaDB embedding ID
    FOREIGN KEY (ticker, filing_url) REFERENCES filings(ticker, filing_url),
    UNIQUE(ticker, filing_url, chunk_index)
);

-- ============================================================================
-- EXTRACTED TABLES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS tables (
    id INTEGER PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    filing_url VARCHAR NOT NULL,
    table_index INTEGER NOT NULL,
    table_data JSON NOT NULL,  -- Structured table as JSON array
    caption VARCHAR,  -- Table title/caption
    page INTEGER,
    row_count INTEGER,
    col_count INTEGER,
    extraction_method VARCHAR,  -- 'gemini', 'pymupdf', 'manual'
    confidence DECIMAL(3, 2),  -- 0.0-1.0 confidence score
    metadata JSON,
    FOREIGN KEY (ticker, filing_url) REFERENCES filings(ticker, filing_url),
    UNIQUE(ticker, filing_url, table_index)
);

-- ============================================================================
-- FINANCIAL METRICS TABLE (Derived from tables)
-- ============================================================================
CREATE TABLE IF NOT EXISTS financial_metrics (
    id INTEGER PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    filing_date DATE NOT NULL,
    fiscal_year INTEGER NOT NULL,
    metric_name VARCHAR NOT NULL,  -- 'revenue', 'net_income', 'total_assets', etc.
    metric_value DECIMAL(20, 2),  -- In USD millions
    metric_unit VARCHAR DEFAULT 'USD_millions',
    source_table_id INTEGER,  -- Reference to tables.id
    extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_table_id) REFERENCES tables(id),
    UNIQUE(ticker, fiscal_year, metric_name)
);

-- ============================================================================
-- ERROR LOG TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS error_log (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    component VARCHAR NOT NULL,  -- 'ingestion', 'sql_query', 'rag_search', etc.
    error_type VARCHAR,  -- 'rate_limit', 'parsing_error', 'api_error'
    error VARCHAR NOT NULL,
    context JSON,  -- Additional context (e.g., {"ticker": "TSLA", "url": "..."})
    stack_trace TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_timestamp TIMESTAMP
);

-- ============================================================================
-- API COSTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS api_costs (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    service VARCHAR NOT NULL,  -- 'anthropic', 'google', 'openai'
    operation VARCHAR NOT NULL,  -- 'table_extraction', 'text_to_sql', 'chat_response'
    model VARCHAR,  -- 'claude-3-5-sonnet-20241022', 'gemini-2.5-flash'
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    tokens_total INTEGER GENERATED ALWAYS AS (tokens_input + tokens_output) VIRTUAL,
    cost_usd DECIMAL(10, 6) NOT NULL,
    ticker VARCHAR,  -- Optional: which ticker this operation was for
    metadata JSON  -- Additional context
);

-- ============================================================================
-- USER SESSIONS TABLE (for chat tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY,
    session_id VARCHAR UNIQUE NOT NULL,
    start_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_timestamp TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10, 6) DEFAULT 0.0,
    tickers_queried VARCHAR[],  -- Array of tickers queried in this session
    metadata JSON
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Filings indexes
CREATE INDEX IF NOT EXISTS idx_filings_ticker ON filings(ticker);
CREATE INDEX IF NOT EXISTS idx_filings_date ON filings(filing_date);
CREATE INDEX IF NOT EXISTS idx_filings_type ON filings(filing_type);
CREATE INDEX IF NOT EXISTS idx_filings_year ON filings(fiscal_year);

-- Chunks indexes
CREATE INDEX IF NOT EXISTS idx_chunks_ticker ON chunks(ticker);
CREATE INDEX IF NOT EXISTS idx_chunks_section ON chunks(section);
CREATE INDEX IF NOT EXISTS idx_chunks_filing_url ON chunks(filing_url);

-- Tables indexes
CREATE INDEX IF NOT EXISTS idx_tables_ticker ON tables(ticker);

-- Financial metrics indexes
CREATE INDEX IF NOT EXISTS idx_metrics_ticker ON financial_metrics(ticker);
CREATE INDEX IF NOT EXISTS idx_metrics_year ON financial_metrics(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON financial_metrics(metric_name);

-- API costs indexes
CREATE INDEX IF NOT EXISTS idx_costs_timestamp ON api_costs(timestamp);
CREATE INDEX IF NOT EXISTS idx_costs_service ON api_costs(service);
CREATE INDEX IF NOT EXISTS idx_costs_ticker ON api_costs(ticker);

-- Error log indexes
CREATE INDEX IF NOT EXISTS idx_errors_timestamp ON error_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_errors_component ON error_log(component);
CREATE INDEX IF NOT EXISTS idx_errors_resolved ON error_log(resolved);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Latest filings per ticker
CREATE OR REPLACE VIEW latest_filings AS
SELECT DISTINCT ON (ticker, filing_type) 
    ticker,
    filing_type,
    filing_date,
    fiscal_year,
    filing_url,
    num_chunks,
    num_tables
FROM filings
ORDER BY ticker, filing_type, filing_date DESC;

-- View: Daily API costs
CREATE OR REPLACE VIEW daily_api_costs AS
SELECT 
    DATE(timestamp) as date,
    service,
    SUM(cost_usd) as total_cost_usd,
    SUM(tokens_total) as total_tokens,
    COUNT(*) as operation_count
FROM api_costs
GROUP BY DATE(timestamp), service
ORDER BY date DESC, service;

-- View: Monthly cost summary
CREATE OR REPLACE VIEW monthly_cost_summary AS
SELECT 
    DATE_TRUNC('month', timestamp) as month,
    service,
    SUM(cost_usd) as total_cost_usd,
    COUNT(*) as operation_count
FROM api_costs
GROUP BY DATE_TRUNC('month', timestamp), service
ORDER BY month DESC, service;

-- View: Error summary by component
CREATE OR REPLACE VIEW error_summary AS
SELECT 
    component,
    error_type,
    COUNT(*) as error_count,
    MAX(timestamp) as last_occurrence,
    SUM(CASE WHEN resolved THEN 1 ELSE 0 END) as resolved_count
FROM error_log
GROUP BY component, error_type
ORDER BY error_count DESC;

-- ============================================================================
-- INITIAL DATA (Optional - for testing)
-- ============================================================================

-- Insert sample cost budget tracking
INSERT INTO api_costs (service, operation, model, tokens_input, tokens_output, cost_usd, ticker, metadata)
VALUES 
    ('anthropic', 'initial_setup', 'claude-3-5-sonnet-20241022', 0, 0, 0.0, NULL, '{"purpose": "schema_initialization"}');

COMMIT;
```

---

## File 2: ChromaDB Configuration

**File**: `configs/chromadb_config.json`

```json
{
  "client_settings": {
    "persist_directory": "data/chroma",
    "anonymized_telemetry": false,
    "allow_reset": false
  },
  "collection_settings": {
    "embedding_function": "sentence-transformers/all-MiniLM-L6-v2",
    "distance_metric": "cosine",
    "hnsw_space": "cosine"
  },
  "collection_naming": {
    "pattern": "sec_filings_{ticker}",
    "examples": [
      "sec_filings_tsla",
      "sec_filings_brk_b",
      "sec_filings_jnj"
    ]
  },
  "metadata_schema": {
    "ticker": "string (required)",
    "filing_url": "string (required)",
    "filing_type": "string (10-K, 10-Q, 8-K)",
    "section": "string (Item 1A, Item 7, etc.)",
    "page": "integer",
    "chunk_index": "integer",
    "fiscal_year": "integer",
    "importance": "string (high, medium, low)"
  },
  "performance_tuning": {
    "batch_size": 100,
    "hnsw_construction_ef": 200,
    "hnsw_search_ef": 100,
    "max_elements": 100000
  }
}
```

---

## File 3: MCP Server Configuration

**File**: `~/.claude/mcp_config.json`

```json
{
  "mcpServers": {
    "finance-screener": {
      "command": "/Users/docravikumar/Code/skill-test/finance-screener/venv/bin/python",
      "args": ["-m", "skill_seeker_mcp.server"],
      "cwd": "/Users/docravikumar/Code/skill-test/finance-screener",
      "env": {
        "PYTHONPATH": "/Users/docravikumar/Code/skill-test/finance-screener",
        "DUCKDB_PATH": "data/finance.duckdb",
        "CHROMA_PATH": "data/chroma"
      },
      "disabled": false,
      "alwaysAllow": [
        "discover_sec_filing",
        "diagnose_pipeline_health",
        "get_cost_summary"
      ]
    }
  }
}
```

**Note**: Update paths to match your actual installation directory.

---

## File 4: Environment Variables

**File**: `.env`

```bash
# ============================================================================
# API KEYS
# ============================================================================

# Anthropic API (Claude Sonnet for synthesis)
# Get from: https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Google AI API (Gemini 2.5 Flash for table extraction)
# Get from: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# ============================================================================
# SEC EDGAR CONFIGURATION
# ============================================================================

# SEC requires User-Agent with contact email
# Format: "AppName/Version (email@example.com)"
SEC_USER_AGENT=FinanceScreener/1.0 (your-email@example.com)

# Rate limiting (seconds between requests)
SEC_RATE_LIMIT=0.5

# ============================================================================
# DATABASE PATHS
# ============================================================================

DUCKDB_PATH=data/finance.duckdb
CHROMA_PATH=data/chroma

# ============================================================================
# COST TRACKING
# ============================================================================

# Monthly API budget (USD)
MONTHLY_BUDGET_USD=50.0

# Daily cost alert threshold (USD)
DAILY_COST_ALERT_THRESHOLD=10.0

# ============================================================================
# LOGGING
# ============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log file path
LOG_FILE=logs/finance_app.log

# ============================================================================
# RAG CONFIGURATION
# ============================================================================

# Embedding model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Chunk size (tokens)
CHUNK_SIZE=300

# Chunk overlap (tokens)
CHUNK_OVERLAP=50

# Top-k results for RAG retrieval
RAG_TOP_K=10

# Enable cross-encoder reranking (slower but higher quality)
RAG_ENABLE_RERANKING=true

# BM25 vs semantic weight (0.0-1.0, must sum to 1.0)
RAG_BM25_WEIGHT=0.5
RAG_SEMANTIC_WEIGHT=0.5

# ============================================================================
# TEXT-TO-SQL CONFIGURATION
# ============================================================================

# DSPy model for SQL generation
DSPY_MODEL=claude-3-5-sonnet-20241022

# SQL validation (dry-run before execution)
SQL_ENABLE_DRY_RUN=true

# Maximum query execution time (seconds)
SQL_TIMEOUT=30

# ============================================================================
# FRONTEND CONFIGURATION
# ============================================================================

# Backend API URL
BACKEND_API_URL=http://localhost:8000

# WebSocket URL
WEBSOCKET_URL=ws://localhost:8000/ws/chat

# Frontend port
FRONTEND_PORT=3000

# ============================================================================
# EMAIL ALERTS (Optional)
# ============================================================================

# Enable email alerts
ENABLE_EMAIL_ALERTS=false

# SMTP settings (Gmail example)
ALERT_EMAIL_FROM=your-email@gmail.com
ALERT_EMAIL_PASSWORD=your-app-password
ALERT_EMAIL_TO=your-email@gmail.com

# Alert conditions
ALERT_ON_COST_THRESHOLD=true
ALERT_ON_ERRORS=true
ALERT_ON_PIPELINE_DEGRADED=true

# ============================================================================
# DEVELOPMENT vs PRODUCTION
# ============================================================================

# Environment: development, production
ENVIRONMENT=development

# Enable debug mode (more verbose logging)
DEBUG_MODE=true

# Disable telemetry
TELEMETRY_DISABLED=true
```

---

## File 5: FastAPI Backend Configuration

**File**: `backend/config.py`

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # API Keys
    anthropic_api_key: str
    google_api_key: str
    
    # SEC Configuration
    sec_user_agent: str
    sec_rate_limit: float = 0.5
    
    # Database
    duckdb_path: str = "data/finance.duckdb"
    chroma_path: str = "data/chroma"
    
    # Cost Tracking
    monthly_budget_usd: float = 50.0
    daily_cost_alert_threshold: float = 10.0
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/finance_app.log"
    
    # RAG
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 300
    chunk_overlap: int = 50
    rag_top_k: int = 10
    rag_enable_reranking: bool = True
    rag_bm25_weight: float = 0.5
    rag_semantic_weight: float = 0.5
    
    # Text-to-SQL
    dspy_model: str = "claude-3-5-sonnet-20241022"
    sql_enable_dry_run: bool = True
    sql_timeout: int = 30
    
    # Frontend
    backend_api_url: str = "http://localhost:8000"
    websocket_url: str = "ws://localhost:8000/ws/chat"
    frontend_port: int = 3000
    
    # Email Alerts
    enable_email_alerts: bool = False
    alert_email_from: Optional[str] = None
    alert_email_password: Optional[str] = None
    alert_email_to: Optional[str] = None
    alert_on_cost_threshold: bool = True
    alert_on_errors: bool = True
    alert_on_pipeline_degraded: bool = True
    
    # Environment
    environment: str = "development"
    debug_mode: bool = True
    telemetry_disabled: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
```

**Usage**:

```python
from backend.config import settings

# Access settings
print(settings.monthly_budget_usd)  # 50.0
print(settings.rag_top_k)  # 10
```

---

## File 6: Docker Configuration

**File**: `Dockerfile`

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data and logs directories
RUN mkdir -p data logs

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run FastAPI with uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  backend:
    build: .
    container_name: finance-screener-backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    restart: unless-stopped
    networks:
      - finance-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    image: node:18-alpine
    container_name: finance-screener-frontend
    working_dir: /app
    volumes:
      - ./frontend:/app
    ports:
      - "3000:3000"
    command: sh -c "npm install && npm start"
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8000
      - REACT_APP_WEBSOCKET_URL=ws://localhost:8000/ws/chat
    networks:
      - finance-network
    depends_on:
      - backend

networks:
  finance-network:
    driver: bridge

volumes:
  data:
  logs:
```

**Commands**:

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

---

## File 7: GitHub Actions CI/CD

**File**: `.github/workflows/ci.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=./ --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install linters
      run: |
        pip install flake8 black mypy
    
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    
    - name: Check formatting with black
      run: |
        black --check .
    
    - name: Type check with mypy
      run: |
        mypy skill_seeker_mcp/ backend/

  build:
    runs-on: ubuntu-latest
    needs: [test, lint]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t finance-screener:latest .
    
    - name: Test Docker container
      run: |
        docker run -d -p 8000:8000 --name test-container finance-screener:latest
        sleep 10
        curl -f http://localhost:8000/health || exit 1
        docker stop test-container
```

---

## File 8: pytest Configuration

**File**: `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=skill_seeker_mcp
    --cov=backend
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests (API calls)
    requires_api: Tests requiring API keys
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

---

## File 9: Pre-commit Hooks

**File**: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=10000']
      - id: check-json
      - id: check-toml
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=120']
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

**Install pre-commit hooks**:

```bash
pip install pre-commit
pre-commit install
```

---

**Next**: [15-code-snippets.md](15-code-snippets.md) for complete, copy-paste ready code implementations.
