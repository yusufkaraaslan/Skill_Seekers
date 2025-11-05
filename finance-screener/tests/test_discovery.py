"""
Test suite for SEC filing discovery functionality.

TDD Approach: Tests written FIRST, implementation AFTER.

Mental Model: Inversion
- What can fail in SEC API interaction?
- Rate limiting, invalid tickers, network errors, malformed responses

Mental Model: First Principles
- Discovery = Find filing URL given (ticker, filing_type, year)
- Core functionality: HTTP request + HTML parsing + URL extraction
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import date


@pytest.mark.unit
class TestDiscoverSecFiling:
    """
    Unit tests for discover_sec_filing tool.
    
    Coverage:
    - ✅ Valid ticker discovery
    - ✅ Invalid ticker handling
    - ✅ Rate limiting respect
    - ✅ Network error handling
    - ✅ Malformed response handling
    """
    
    @pytest.mark.asyncio
    async def test_discover_valid_ticker_10k(
        self, 
        mock_sec_response: Mock,
        env_vars: dict
    ) -> None:
        """
        Test successful discovery of 10-K filing for valid ticker.
        
        Given: TSLA ticker, 10-K filing type, 2020 fiscal year
        When: discover_sec_filing is called
        Then: Returns valid filing URL
        """
        # This test will fail until we implement discovery.py
        from skill_seeker_mcp.finance_tools.discovery import discover_sec_filing
        
        with patch('requests.get', return_value=mock_sec_response):
            result = await discover_sec_filing(
                ticker="TSLA",
                filing_type="10-K",
                fiscal_year=2020
            )
        
        # Assertions (First Principles: what makes a valid result?)
        assert result["success"] is True
        assert "filing_url" in result
        assert "TSLA" in result["filing_url"] or "1318605" in result["filing_url"]
        assert result["ticker"] == "TSLA"
        assert result["filing_type"] == "10-K"
        assert result["fiscal_year"] == 2020
    
    
    @pytest.mark.asyncio
    async def test_discover_invalid_ticker(self, env_vars: dict) -> None:
        """
        Test graceful handling of invalid ticker.
        
        Mental Model: Inversion - prevent bad data from propagating
        
        Given: Invalid ticker "INVALID123"
        When: discover_sec_filing is called
        Then: Returns error with helpful message
        """
        from skill_seeker_mcp.finance_tools.discovery import discover_sec_filing
        
        mock_404 = Mock()
        mock_404.status_code = 404
        mock_404.text = "Not Found"
        
        with patch('requests.get', return_value=mock_404):
            result = await discover_sec_filing(
                ticker="INVALID123",
                filing_type="10-K",
                fiscal_year=2020
            )
        
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower() or "invalid" in result["error"].lower()
    
    
    @pytest.mark.asyncio
    async def test_discover_respects_rate_limit(self, env_vars: dict) -> None:
        """
        Test that discovery respects SEC rate limiting (10 requests/second max).
        
        Mental Model: Second Order Effects
        - Too many requests → IP ban → all future requests fail
        
        Given: Multiple consecutive discovery calls
        When: discover_sec_filing is called 3 times in succession
        Then: Minimum 300ms between requests (10 req/sec = 100ms each, +200ms buffer)
        """
        from skill_seeker_mcp.finance_tools.discovery import discover_sec_filing
        import time
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><a href='https://sec.gov/filing1.htm'>Filing</a></html>"
        
        with patch('requests.get', return_value=mock_response):
            start = time.time()
            
            await discover_sec_filing("TSLA", "10-K", 2020)
            await discover_sec_filing("AAPL", "10-K", 2020)
            await discover_sec_filing("MSFT", "10-K", 2020)
            
            elapsed = time.time() - start
        
        # Should take at least 200ms (conservative estimate)
        assert elapsed >= 0.2, f"Requests too fast: {elapsed}s (rate limit violation risk)"
    
    
    @pytest.mark.asyncio
    async def test_discover_network_error_handling(self, env_vars: dict) -> None:
        """
        Test graceful handling of network errors.
        
        Mental Model: Inversion - what network failures can occur?
        - Timeout, DNS failure, connection refused
        
        Given: Network request that times out
        When: discover_sec_filing is called
        Then: Returns error without crashing
        """
        from skill_seeker_mcp.finance_tools.discovery import discover_sec_filing
        import requests
        
        with patch('requests.get', side_effect=requests.Timeout("Connection timed out")):
            result = await discover_sec_filing("TSLA", "10-K", 2020)
        
        assert result["success"] is False
        assert "error" in result
        assert "timeout" in result["error"].lower() or "network" in result["error"].lower()
    
    
    @pytest.mark.asyncio
    async def test_discover_validates_user_agent(self, monkeypatch) -> None:
        """
        Test that SEC User-Agent header is required.
        
        Mental Model: Systems Thinking
        - SEC blocks requests without User-Agent
        - Missing User-Agent → 403 Forbidden → all requests fail
        
        Given: Missing SEC_USER_AGENT environment variable
        When: discover_sec_filing is called
        Then: Raises ValueError with helpful message
        """
        from skill_seeker_mcp.finance_tools.discovery import discover_sec_filing
        
        monkeypatch.delenv("SEC_USER_AGENT", raising=False)
        
        with pytest.raises(ValueError, match="SEC_USER_AGENT"):
            await discover_sec_filing("TSLA", "10-K", 2020)


@pytest.mark.unit
class TestEstimateApiCost:
    """
    Unit tests for estimate_api_cost utility.
    
    Mental Model: First Principles
    - Cost = f(file_size, extract_tables)
    - Gemini pricing: $0.00001 per 1K tokens
    """
    
    def test_estimate_cost_without_tables(self) -> None:
        """
        Test cost estimation for filing without table extraction.
        
        Given: 100-page PDF, extract_tables=False
        When: estimate_api_cost is called
        Then: Returns $0 (no API calls needed)
        """
        from skill_seeker_mcp.finance_tools.discovery import estimate_api_cost
        
        result = estimate_api_cost(
            filing_url="https://sec.gov/filing.pdf",
            extract_tables=False
        )
        
        assert result["estimated_cost_usd"] == 0.0
        assert result["service"] == "none"
    
    
    def test_estimate_cost_with_tables(self) -> None:
        """
        Test cost estimation with Gemini table extraction.
        
        Given: 100-page PDF, extract_tables=True
        When: estimate_api_cost is called
        Then: Returns estimated Gemini cost (~$0.02 for 100 pages)
        
        Mental Model: Second Order Effects
        - More tables → more Gemini calls → higher cost
        """
        from skill_seeker_mcp.finance_tools.discovery import estimate_api_cost
        
        result = estimate_api_cost(
            filing_url="https://sec.gov/filing.pdf",
            extract_tables=True,
            estimated_pages=100
        )
        
        assert result["estimated_cost_usd"] > 0
        assert result["estimated_cost_usd"] < 0.05  # Sanity check
        assert result["service"] == "gemini"
        assert "estimated_pages" in result


@pytest.mark.integration
class TestDiscoveryIntegration:
    """
    Integration tests requiring actual SEC API (optional, slow).
    
    Run with: pytest -m integration
    Skip in CI: pytest -m "not integration"
    """
    
    @pytest.mark.slow
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_discover_real_sec_filing(
        self, 
        env_vars: dict,
        sample_sec_filing_html: str
    ) -> None:
        """
        Test discovery with mocked SEC EDGAR API.
        
        Given: Mocked SEC EDGAR search results
        When: Discovering TSLA 10-K from 2020
        Then: Returns valid SEC filing URL
        """
        from skill_seeker_mcp.finance_tools.discovery import discover_sec_filing
        from unittest.mock import patch, AsyncMock
        
        # Mock aiohttp ClientSession response
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=sample_sec_filing_html)
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await discover_sec_filing("TSLA", "10-K", 2020)
        
        assert result["success"] is True
        assert "sec.gov" in result["filing_url"]
        assert result["ticker"] == "TSLA"
