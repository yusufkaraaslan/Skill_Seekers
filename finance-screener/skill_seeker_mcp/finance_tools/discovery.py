"""
SEC filing discovery tool - MCP implementation.

Mental Model: First Principles
- Discovery = Find filing URL from (ticker, filing_type, year)
- Dependencies: SEC EDGAR API, HTML parsing, rate limiting

Mental Model: Inversion
- What can fail? Network errors, rate limits, invalid tickers, missing User-Agent
- Defensive programming: validate inputs, handle errors, respect rate limits
"""

import os
import asyncio
import time
from typing import Dict, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import structlog

logger = structlog.get_logger()

# SEC requires 10 requests/second max, we use 5/second to be conservative
RATE_LIMIT_DELAY = 0.2  # 200ms between requests = 5 req/sec


class SecApiRateLimiter:
    """
    Rate limiter for SEC EDGAR API.
    
    Mental Model: Second Order Effects
    - Exceeding rate limit → IP ban → all future requests fail
    - Conservative rate limiting prevents cascading failures
    """
    
    def __init__(self, delay: float = RATE_LIMIT_DELAY):
        self.delay = delay
        self.last_request_time = 0.0
    
    async def wait(self) -> None:
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay:
            await asyncio.sleep(self.delay - time_since_last)
        
        self.last_request_time = time.time()


# Global rate limiter instance
_rate_limiter = SecApiRateLimiter()


async def discover_sec_filing(
    ticker: str,
    filing_type: str = "10-K",
    fiscal_year: int = 2020
) -> Dict[str, Any]:
    """
    Discover SEC filing URL for given ticker and filing type.
    
    Args:
        ticker: Stock ticker symbol (e.g., "TSLA")
        filing_type: SEC filing type ("10-K", "10-Q", "8-K")
        fiscal_year: Fiscal year of filing
    
    Returns:
        {
            "success": bool,
            "filing_url": str (if success),
            "ticker": str,
            "filing_type": str,
            "fiscal_year": int,
            "filing_date": str (if found),
            "error": str (if failure)
        }
    
    Raises:
        ValueError: If SEC_USER_AGENT not set in environment
    
    Mental Model: Systems Thinking
    - Input validation → API call → response parsing → structured output
    - Each step can fail independently
    """
    
    # Validate environment
    user_agent = os.getenv("SEC_USER_AGENT")
    if not user_agent:
        raise ValueError(
            "SEC_USER_AGENT environment variable required. "
            "Format: 'YourApp/Version (email@example.com)'"
        )
    
    logger.info(
        "discovering_sec_filing",
        ticker=ticker,
        filing_type=filing_type,
        fiscal_year=fiscal_year
    )
    
    try:
        # Respect rate limit
        await _rate_limiter.wait()
        
        # Build SEC EDGAR search URL
        # CIK lookup: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TICKER
        search_url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar"
            f"?action=getcompany&CIK={ticker}&type={filing_type}"
            f"&dateb={fiscal_year}1231&owner=exclude&count=10"
        )
        
        headers = {"User-Agent": user_agent}
        
        # Make request
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            return {
                "success": False,
                "ticker": ticker,
                "filing_type": filing_type,
                "fiscal_year": fiscal_year,
                "error": f"Ticker '{ticker}' not found in SEC EDGAR database"
            }
        
        if response.status_code != 200:
            return {
                "success": False,
                "ticker": ticker,
                "filing_type": filing_type,
                "fiscal_year": fiscal_year,
                "error": f"SEC API returned status {response.status_code}"
            }
        
        # Parse HTML to find filing URL
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find first filing link in results table
        filing_link = None
        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 2:
                # Check if this row contains the filing type we want
                if filing_type in cells[0].get_text():
                    # Extract document link from "Documents" column
                    doc_link = row.find('a', {'id': 'documentsbutton'})
                    if doc_link:
                        filing_link = "https://www.sec.gov" + doc_link['href']
                        break
        
        if not filing_link:
            return {
                "success": False,
                "ticker": ticker,
                "filing_type": filing_type,
                "fiscal_year": fiscal_year,
                "error": f"No {filing_type} filing found for {ticker} in {fiscal_year}"
            }
        
        logger.info(
            "sec_filing_discovered",
            ticker=ticker,
            filing_url=filing_link
        )
        
        return {
            "success": True,
            "filing_url": filing_link,
            "ticker": ticker,
            "filing_type": filing_type,
            "fiscal_year": fiscal_year,
            "filing_date": None  # Would need to parse from page for exact date
        }
    
    except requests.Timeout:
        return {
            "success": False,
            "ticker": ticker,
            "filing_type": filing_type,
            "fiscal_year": fiscal_year,
            "error": "Network timeout while contacting SEC EDGAR API"
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "ticker": ticker,
            "filing_type": filing_type,
            "fiscal_year": fiscal_year,
            "error": f"Network error: {str(e)}"
        }
    
    except Exception as e:
        logger.error(
            "discovery_unexpected_error",
            ticker=ticker,
            error=str(e)
        )
        return {
            "success": False,
            "ticker": ticker,
            "filing_type": filing_type,
            "fiscal_year": fiscal_year,
            "error": f"Unexpected error: {str(e)}"
        }


def estimate_api_cost(
    filing_url: str,
    extract_tables: bool = True,
    estimated_pages: int = 100
) -> Dict[str, Any]:
    """
    Estimate API costs for processing SEC filing.
    
    Args:
        filing_url: URL of SEC filing
        extract_tables: Whether to extract tables with Gemini
        estimated_pages: Estimated number of pages in filing
    
    Returns:
        {
            "estimated_cost_usd": float,
            "service": str ("none" | "gemini"),
            "estimated_pages": int,
            "breakdown": dict
        }
    
    Mental Model: First Principles
    - Cost = pages × tables_per_page × cost_per_table
    - Gemini pricing: ~$0.00001 per 1K tokens, ~1K tokens per table
    """
    
    if not extract_tables:
        return {
            "estimated_cost_usd": 0.0,
            "service": "none",
            "estimated_pages": estimated_pages,
            "breakdown": {"note": "No table extraction requested"}
        }
    
    # Conservative estimates:
    # - 1 table per 5 pages on average
    # - 1000 tokens per table extraction
    # - Gemini Flash pricing: $0.00001 per 1K tokens
    
    estimated_tables = estimated_pages / 5
    tokens_per_table = 1000
    cost_per_1k_tokens = 0.00001
    
    total_tokens = estimated_tables * tokens_per_table
    total_cost = (total_tokens / 1000) * cost_per_1k_tokens
    
    return {
        "estimated_cost_usd": round(total_cost, 6),
        "service": "gemini",
        "estimated_pages": estimated_pages,
        "breakdown": {
            "estimated_tables": int(estimated_tables),
            "tokens_per_table": tokens_per_table,
            "total_tokens": int(total_tokens),
            "cost_per_1k_tokens": cost_per_1k_tokens
        }
    }
