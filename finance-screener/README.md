# Finance Screener

AI-powered value investing stock screener built with Test-Driven Development (TDD).

## 🧪 TDD Approach

This project follows **strict TDD methodology**:

1. ✅ **Tests written FIRST**
2. ✅ **Implementation written AFTER**
3. ✅ **All tests must pass (no skipped tests)**
4. ✅ **Mandatory 80%+ code coverage**

## 🧠 Mental Models Applied

Every component designed using 5 mental models:

1. **First Principles**: Break down to fundamental requirements
2. **Second Order Effects**: Consider consequences of consequences
3. **Systems Thinking**: View as integrated whole
4. **Inversion**: Ask "what can fail?"
5. **Interdependencies**: Map component relationships

## 📁 Project Structure

```
finance-screener/
├── skill_seeker_mcp/           # MCP server implementation
│   └── finance_tools/          # Finance-specific tools
│       ├── discovery.py        # SEC filing discovery
│       ├── ingestion.py        # PDF extraction, chunking, embeddings
│       ├── query.py            # Text-to-SQL, RAG retrieval
│       └── monitoring.py       # Health checks, cost tracking
├── tests/                      # TDD test suite
│   ├── conftest.py            # Shared fixtures
│   ├── test_discovery.py      # Discovery tests (COMPLETE)
│   ├── test_ingestion.py      # Ingestion tests (TODO)
│   ├── test_query.py          # Query tests (TODO)
│   ├── test_monitoring.py     # Monitoring tests (TODO)
│   └── test_integration.py    # End-to-end tests (TODO)
├── pyproject.toml             # Project config + pytest settings
├── .env.example               # Environment variable template
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
cd finance-screener

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (includes pytest)
pip install -e ".[dev]"
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run only unit tests (fast)
pytest -m unit

# Run only integration tests (slow, requires databases)
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Verbose output
pytest -v
```

## ✅ Test Status

| Component | Tests | Status | Coverage |
|-----------|-------|--------|----------|
| Discovery | 8 tests | ✅ Ready | TBD |
| Ingestion | 0 tests | ⏳ TODO | - |
| Query | 0 tests | ⏳ TODO | - |
| Monitoring | 0 tests | ⏳ TODO | - |
| Integration | 0 tests | ⏳ TODO | - |

**Current Status**: Phase 1 complete (discovery tool with TDD)

## 📝 Development Workflow

### TDD Cycle (Red → Green → Refactor)

1. **RED**: Write failing test
   ```bash
   pytest tests/test_discovery.py::test_discover_valid_ticker_10k -v
   # Expected: FAILED (implementation not complete)
   ```

2. **GREEN**: Implement minimum code to pass
   ```python
   # Edit skill_seeker_mcp/finance_tools/discovery.py
   # Run test again
   ```

3. **REFACTOR**: Improve code quality
   ```bash
   pytest --cov  # Ensure coverage maintained
   ruff check .  # Lint code
   black .       # Format code
   ```

### Mental Model Checklist

Before implementing any feature, apply all 5 models:

- [ ] **First Principles**: What is the core functionality?
- [ ] **Second Order Effects**: What are the consequences?
- [ ] **Systems Thinking**: How does this integrate?
- [ ] **Inversion**: What can go wrong?
- [ ] **Interdependencies**: What depends on this?

## 🔧 Available Tools

### 1. Discovery Tool

**Status**: ✅ Complete with tests

```python
from skill_seeker_mcp.finance_tools.discovery import discover_sec_filing

result = await discover_sec_filing("TSLA", "10-K", 2020)
# Returns: {"success": True, "filing_url": "https://..."}
```

**Tests**: `tests/test_discovery.py`
- ✅ Valid ticker discovery
- ✅ Invalid ticker handling
- ✅ Rate limit respect
- ✅ Network error handling
- ✅ User-Agent validation

### 2. Ingestion Tool (TODO)

**Status**: ⏳ Tests not written yet

**Next Steps**:
1. Write `tests/test_ingestion.py`
2. Implement `skill_seeker_mcp/finance_tools/ingestion.py`
3. Ensure all tests pass

### 3. Query Tool (TODO)

**Status**: ⏳ Tests not written yet

### 4. Monitoring Tool (TODO)

**Status**: ⏳ Tests not written yet

## 📊 Test Coverage Goals

- **Unit Tests**: 80%+ coverage (enforced by pytest)
- **Integration Tests**: Critical paths covered
- **No Skipped Tests**: All tests must pass or be removed
- **CI/CD**: GitHub Actions runs full test suite on push

## 🛡️ Test Safety

### Fixtures Prevent:
- ✅ **Test pollution**: Fresh database per test
- ✅ **API costs**: Mocked API clients
- ✅ **Rate limiting**: Controlled request timing
- ✅ **Data leaks**: Temporary directories auto-cleaned

### Test Markers:
- `@pytest.mark.unit`: Fast, isolated tests
- `@pytest.mark.integration`: Requires databases
- `@pytest.mark.slow`: Long-running tests
- `@pytest.mark.api`: Requires API keys

## 🚫 No Shortcuts

This project enforces:

- ❌ No skipped tests (`@pytest.mark.skip` forbidden)
- ❌ No failing tests (CI blocks merge)
- ❌ No coverage bypass (80% minimum enforced)
- ❌ No untested code (TDD: tests first)

## 📚 Related Documentation

- **Complete Guide**: `/docs/finance-application-guide/README.md`
- **Mental Models**: `/docs/finance-application-guide/04-mental-models.md`
- **Derek Snow Course**: `/docs/finance-application-guide/08-snow-course-architecture.md`

## 🎯 Success Metrics

**Phase 1 Complete** when:
- ✅ All discovery tests pass
- ✅ 80%+ coverage on discovery module
- ✅ No lint errors
- ✅ Documentation updated

**Phase 2 Complete** when:
- ✅ All ingestion tests pass
- ✅ DuckDB + ChromaDB integration tests pass
- ✅ Real SEC filing ingestion works end-to-end

**Production Ready** when:
- ✅ All 5 tools have full test coverage
- ✅ Integration tests pass
- ✅ Performance tests meet benchmarks
- ✅ Security audit complete
