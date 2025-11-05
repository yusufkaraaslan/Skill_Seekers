# Monitoring & Observability

**Comprehensive observability setup** following Derek Snow's Session 5 principles: "If you can't measure it, you can't optimize it."

This guide implements **structured logging, cost tracking, SessionStart hooks, and health dashboards** for production-grade monitoring.

---

## Architecture Overview

```
Observability Stack:
├── Structured Logging (structlog)
│   ├── SessionStart hooks → diagnostics on every Claude session
│   ├── Tool call logging → track every MCP tool invocation
│   └── Error tracking → capture failures with context
├── Cost Tracking (DuckDB)
│   ├── API cost per operation
│   ├── Daily/monthly budgets
│   └── Cost alerts (> $10/day threshold)
├── Health Monitoring (diagnose_pipeline_health)
│   ├── DuckDB health (size, table count, last write)
│   ├── ChromaDB health (collections, embeddings)
│   └── API quota checks (Gemini, Anthropic)
└── Dashboards
    ├── Real-time health status
    ├── Cost trends (daily/monthly)
    └── Error analytics
```

---

## Part 1: Structured Logging Setup

### Install Dependencies

```bash
pip install structlog python-json-logger
```

### Configure Structlog

File: `configs/logging_config.py`

```python
import structlog
import logging
from pathlib import Path

# Create logs directory
Path("logs").mkdir(exist_ok=True)

# Configure structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(file=open("logs/finance_app.log", "a")),
    cache_logger_on_first_use=True,
)

def get_logger(name: str):
    """Get structured logger for module"""
    return structlog.get_logger(name)
```

### Usage in MCP Tools

```python
# skill_seeker_mcp/finance_tools/ingestion.py

from configs.logging_config import get_logger

logger = get_logger("finance_tools.ingestion")

@server.tool()
async def ingest_sec_filing(filing_url: str, ticker: str, extract_tables: bool = True):
    logger.info(
        "ingestion.started",
        ticker=ticker,
        filing_url=filing_url,
        extract_tables=extract_tables
    )
    
    try:
        # ... ingestion logic ...
        
        logger.info(
            "ingestion.completed",
            ticker=ticker,
            chunks_created=len(chunks),
            tables_extracted=len(tables),
            cost_usd=cost_usd,
            processing_time_sec=processing_time
        )
        
        return result
    
    except Exception as e:
        logger.error(
            "ingestion.failed",
            ticker=ticker,
            error=str(e),
            exc_info=True  # Captures stack trace
        )
        raise
```

---

## Part 2: SessionStart Hooks

**Purpose**: Run diagnostics at the start of every Claude Code session to catch issues early.

### Implementation

File: `skill_seeker_mcp/hooks/session_start.py`

```python
import structlog
import duckdb
from datetime import datetime, timedelta
from pathlib import Path

logger = structlog.get_logger("hooks.session_start")

async def on_session_start():
    """
    Diagnostics run on every Claude Code session start:
    1. Pipeline health check
    2. Daily API cost check
    3. Data freshness check
    4. Disk space check
    5. Error summary (last 24h)
    """
    
    logger.info("session_start.triggered")
    
    diagnostics = {
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # 1. Pipeline Health
    try:
        from finance_tools.monitoring import diagnose_pipeline_health
        health = await diagnose_pipeline_health()
        
        diagnostics["checks"]["pipeline_health"] = {
            "status": health["overall_health"],
            "duckdb_filings": health["components"]["duckdb"]["filings"],
            "chroma_embeddings": health["components"]["chroma"]["total_embeddings"]
        }
        
        logger.info(
            "session_start.pipeline_health",
            status=health["overall_health"],
            filings=health["components"]["duckdb"]["filings"]
        )
    
    except Exception as e:
        logger.error("session_start.pipeline_health_failed", error=str(e))
        diagnostics["checks"]["pipeline_health"] = {"status": "failed", "error": str(e)}
    
    # 2. Daily API Cost
    try:
        conn = duckdb.connect("data/finance.duckdb", read_only=True)
        
        today_cost = conn.execute("""
            SELECT SUM(cost_usd) 
            FROM api_costs 
            WHERE DATE(timestamp) = CURRENT_DATE
        """).fetchone()[0] or 0.0
        
        monthly_cost = conn.execute("""
            SELECT SUM(cost_usd)
            FROM api_costs
            WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE)
        """).fetchone()[0] or 0.0
        
        diagnostics["checks"]["api_costs"] = {
            "status": "ok" if today_cost < 10.0 else "warning",
            "today_usd": round(today_cost, 2),
            "monthly_usd": round(monthly_cost, 2),
            "budget_usd": 50.0,
            "budget_remaining_usd": round(50.0 - monthly_cost, 2)
        }
        
        logger.info(
            "session_start.api_costs",
            today_cost=today_cost,
            monthly_cost=monthly_cost,
            budget_remaining=50.0 - monthly_cost
        )
        
        # Alert if exceeding daily threshold
        if today_cost > 10.0:
            logger.warning(
                "session_start.cost_alert",
                message=f"Daily cost ${today_cost:.2f} exceeds $10 threshold",
                today_cost=today_cost
            )
        
        conn.close()
    
    except Exception as e:
        logger.error("session_start.cost_check_failed", error=str(e))
        diagnostics["checks"]["api_costs"] = {"status": "failed", "error": str(e)}
    
    # 3. Data Freshness
    try:
        conn = duckdb.connect("data/finance.duckdb", read_only=True)
        
        last_ingestion = conn.execute("""
            SELECT MAX(ingestion_timestamp) FROM filings
        """).fetchone()[0]
        
        if last_ingestion:
            days_since_update = (datetime.now() - last_ingestion).days
            
            diagnostics["checks"]["data_freshness"] = {
                "status": "ok" if days_since_update < 7 else "warning",
                "last_ingestion": last_ingestion.isoformat(),
                "days_since_update": days_since_update
            }
            
            logger.info(
                "session_start.data_freshness",
                last_ingestion=last_ingestion,
                days_since_update=days_since_update
            )
            
            if days_since_update > 7:
                logger.warning(
                    "session_start.stale_data",
                    message=f"Last ingestion was {days_since_update} days ago",
                    days_since_update=days_since_update
                )
        
        conn.close()
    
    except Exception as e:
        logger.error("session_start.freshness_check_failed", error=str(e))
    
    # 4. Disk Space
    try:
        duckdb_size_mb = Path("data/finance.duckdb").stat().st_size / 1024 / 1024
        chroma_size_mb = sum(f.stat().st_size for f in Path("data/chroma").rglob("*") if f.is_file()) / 1024 / 1024
        total_size_mb = duckdb_size_mb + chroma_size_mb
        
        diagnostics["checks"]["disk_space"] = {
            "status": "ok" if total_size_mb < 5000 else "warning",  # 5GB threshold
            "duckdb_mb": round(duckdb_size_mb, 2),
            "chroma_mb": round(chroma_size_mb, 2),
            "total_mb": round(total_size_mb, 2)
        }
        
        logger.info(
            "session_start.disk_space",
            duckdb_mb=duckdb_size_mb,
            chroma_mb=chroma_size_mb,
            total_mb=total_size_mb
        )
        
        if total_size_mb > 5000:
            logger.warning(
                "session_start.disk_alert",
                message=f"Database size {total_size_mb:.0f}MB exceeds 5GB threshold"
            )
    
    except Exception as e:
        logger.error("session_start.disk_check_failed", error=str(e))
    
    # 5. Error Summary (last 24h)
    try:
        conn = duckdb.connect("data/finance.duckdb", read_only=True)
        
        errors = conn.execute("""
            SELECT component, COUNT(*) as error_count
            FROM error_log
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY component
            ORDER BY error_count DESC
        """).fetchall()
        
        diagnostics["checks"]["errors"] = {
            "status": "ok" if len(errors) == 0 else "warning",
            "error_count_24h": sum(e[1] for e in errors),
            "by_component": {e[0]: e[1] for e in errors}
        }
        
        if errors:
            logger.warning(
                "session_start.errors_detected",
                error_count=sum(e[1] for e in errors),
                by_component={e[0]: e[1] for e in errors}
            )
        
        conn.close()
    
    except Exception as e:
        logger.error("session_start.error_summary_failed", error=str(e))
    
    logger.info("session_start.completed", diagnostics=diagnostics)
    
    return diagnostics
```

### Register Hook in MCP Server

```python
# skill_seeker_mcp/server.py

from hooks.session_start import on_session_start

@server.on_session_start
async def session_start_handler():
    """Triggered when Claude Code session starts"""
    return await on_session_start()
```

**Test**: Restart Claude Code → check `logs/finance_app.log` for session diagnostics.

---

## Part 3: Tool Call Logging

**Track every MCP tool invocation** to identify performance bottlenecks and high-cost operations.

### Decorator for Auto-Logging

File: `skill_seeker_mcp/utils/logging_decorator.py`

```python
import time
import structlog
from functools import wraps

logger = structlog.get_logger("tool_calls")

def log_tool_call(func):
    """Decorator to log all tool calls with timing and arguments"""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        tool_name = func.__name__
        start_time = time.time()
        
        logger.info(
            "tool_call.started",
            tool=tool_name,
            args=str(args)[:200],  # Truncate long args
            kwargs={k: str(v)[:100] for k, v in kwargs.items()}
        )
        
        try:
            result = await func(*args, **kwargs)
            elapsed_ms = (time.time() - start_time) * 1000
            
            logger.info(
                "tool_call.completed",
                tool=tool_name,
                elapsed_ms=round(elapsed_ms, 2),
                result_size=len(str(result))
            )
            
            # Track slow tools
            if elapsed_ms > 5000:  # > 5 seconds
                logger.warning(
                    "tool_call.slow",
                    tool=tool_name,
                    elapsed_ms=round(elapsed_ms, 2),
                    message=f"Tool {tool_name} took {elapsed_ms/1000:.1f}s"
                )
            
            return result
        
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            
            logger.error(
                "tool_call.failed",
                tool=tool_name,
                elapsed_ms=round(elapsed_ms, 2),
                error=str(e),
                exc_info=True
            )
            
            # Log to error_log table
            import duckdb
            conn = duckdb.connect("data/finance.duckdb")
            conn.execute("""
                INSERT INTO error_log (component, error, context)
                VALUES (?, ?, ?)
            """, [tool_name, str(e), str(kwargs)])
            conn.close()
            
            raise
    
    return wrapper
```

### Apply to Tools

```python
# skill_seeker_mcp/finance_tools/ingestion.py

from utils.logging_decorator import log_tool_call

@server.tool()
@log_tool_call
async def ingest_sec_filing(filing_url: str, ticker: str, extract_tables: bool = True):
    # ... implementation ...
```

**Logs will show**:

```json
{
  "event": "tool_call.started",
  "tool": "ingest_sec_filing",
  "kwargs": {"filing_url": "https://sec.gov/...", "ticker": "TSLA", "extract_tables": true},
  "timestamp": "2024-01-15T10:30:00Z"
}
{
  "event": "tool_call.completed",
  "tool": "ingest_sec_filing",
  "elapsed_ms": 31200,
  "result_size": 1450,
  "timestamp": "2024-01-15T10:30:31Z"
}
```

---

## Part 4: Cost Tracking & Alerts

### Track API Costs in Real-Time

```python
# skill_seeker_mcp/utils/cost_tracker.py

import duckdb
import structlog
from datetime import datetime

logger = structlog.get_logger("cost_tracker")

async def track_cost(service: str, operation: str, tokens_used: int, cost_usd: float, ticker: str = None):
    """
    Record API cost to DuckDB.
    
    Args:
        service: "anthropic", "google"
        operation: "table_extraction", "text_to_sql", "chat_response"
        tokens_used: Token count
        cost_usd: Cost in USD
        ticker: Optional ticker (e.g., "TSLA")
    """
    
    conn = duckdb.connect("data/finance.duckdb")
    
    conn.execute("""
        INSERT INTO api_costs (service, operation, tokens_used, cost_usd, ticker)
        VALUES (?, ?, ?, ?, ?)
    """, [service, operation, tokens_used, cost_usd, ticker])
    
    # Get today's total
    today_total = conn.execute("""
        SELECT SUM(cost_usd) FROM api_costs WHERE DATE(timestamp) = CURRENT_DATE
    """).fetchone()[0] or 0.0
    
    logger.info(
        "cost_tracked",
        service=service,
        operation=operation,
        cost_usd=cost_usd,
        today_total_usd=round(today_total, 2)
    )
    
    # Alert if exceeding threshold
    if today_total > 10.0:
        logger.warning(
            "cost_alert",
            message=f"Daily cost ${today_total:.2f} exceeds $10 threshold",
            today_total_usd=today_total
        )
    
    conn.close()

async def get_cost_summary(period: str = "today"):
    """
    Get cost summary for period.
    
    Args:
        period: "today", "week", "month"
    
    Returns:
        {
            "total_usd": 4.50,
            "by_service": {"anthropic": 3.20, "google": 1.30},
            "by_operation": {"table_extraction": 0.40, "chat_response": 4.10}
        }
    """
    
    conn = duckdb.connect("data/finance.duckdb", read_only=True)
    
    # Date filter
    if period == "today":
        date_filter = "DATE(timestamp) = CURRENT_DATE"
    elif period == "week":
        date_filter = "timestamp >= NOW() - INTERVAL '7 days'"
    elif period == "month":
        date_filter = "timestamp >= DATE_TRUNC('month', CURRENT_DATE)"
    else:
        raise ValueError(f"Invalid period: {period}")
    
    # Total cost
    total_usd = conn.execute(f"""
        SELECT SUM(cost_usd) FROM api_costs WHERE {date_filter}
    """).fetchone()[0] or 0.0
    
    # By service
    by_service = conn.execute(f"""
        SELECT service, SUM(cost_usd) as cost
        FROM api_costs
        WHERE {date_filter}
        GROUP BY service
    """).fetchall()
    
    # By operation
    by_operation = conn.execute(f"""
        SELECT operation, SUM(cost_usd) as cost
        FROM api_costs
        WHERE {date_filter}
        GROUP BY operation
    """).fetchall()
    
    conn.close()
    
    return {
        "total_usd": round(total_usd, 2),
        "by_service": {s[0]: round(s[1], 2) for s in by_service},
        "by_operation": {o[0]: round(o[1], 2) for o in by_operation}
    }
```

### Usage in Tools

```python
# After Gemini table extraction
await track_cost(
    service="google",
    operation="table_extraction",
    tokens_used=15000,
    cost_usd=0.021,
    ticker=ticker
)

# After Claude chat response
await track_cost(
    service="anthropic",
    operation="chat_response",
    tokens_used=usage.input_tokens + usage.output_tokens,
    cost_usd=usage.input_tokens * 0.003 / 1000 + usage.output_tokens * 0.015 / 1000,
    ticker=ticker
)
```

---

## Part 5: Health Dashboard

### Backend API

File: `backend/monitoring.py`

```python
from fastapi import APIRouter
from utils.cost_tracker import get_cost_summary
from finance_tools.monitoring import diagnose_pipeline_health

router = APIRouter()

@router.get("/health")
async def health():
    """Pipeline health check"""
    return await diagnose_pipeline_health()

@router.get("/costs/{period}")
async def costs(period: str = "today"):
    """Cost summary for period (today, week, month)"""
    return await get_cost_summary(period)

@router.get("/metrics")
async def metrics():
    """Combined metrics for dashboard"""
    
    health = await diagnose_pipeline_health()
    today_costs = await get_cost_summary("today")
    month_costs = await get_cost_summary("month")
    
    return {
        "health": health,
        "costs": {
            "today": today_costs,
            "month": month_costs,
            "budget_usd": 50.0,
            "budget_remaining_usd": round(50.0 - month_costs["total_usd"], 2)
        }
    }
```

Register routes:

```python
# backend/main.py

from monitoring import router as monitoring_router

app.include_router(monitoring_router, prefix="/api/monitoring")
```

---

### Frontend Dashboard

File: `frontend/src/MonitoringDashboard.js`

```javascript
import React, { useState, useEffect } from 'react';
import './MonitoringDashboard.css';

function MonitoringDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000);  // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/monitoring/metrics');
      const data = await response.json();
      setMetrics(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  };

  if (loading) return <div>Loading metrics...</div>;

  const { health, costs } = metrics;

  return (
    <div className="monitoring-dashboard">
      <h1>Finance Screener Monitoring</h1>
      
      {/* Pipeline Health */}
      <section className="health-section">
        <h2>Pipeline Health</h2>
        <div className={`status-badge ${health.overall_health}`}>
          {health.overall_health.toUpperCase()}
        </div>
        
        <div className="health-metrics">
          <div className="metric">
            <h3>DuckDB</h3>
            <p className="value">{health.components.duckdb.filings}</p>
            <p className="label">filings ingested</p>
            <p className="meta">{health.components.duckdb.size_mb} MB</p>
          </div>
          
          <div className="metric">
            <h3>ChromaDB</h3>
            <p className="value">{health.components.chroma.total_embeddings}</p>
            <p className="label">embeddings stored</p>
            <p className="meta">{health.components.chroma.collections} collections</p>
          </div>
          
          <div className="metric">
            <h3>Errors</h3>
            <p className="value">{health.errors_last_24h.length}</p>
            <p className="label">in last 24h</p>
          </div>
        </div>
      </section>
      
      {/* Cost Tracking */}
      <section className="cost-section">
        <h2>API Costs</h2>
        
        <div className="cost-overview">
          <div className="cost-card">
            <h3>Today</h3>
            <p className="cost-value">${costs.today.total_usd}</p>
            <div className="cost-breakdown">
              {Object.entries(costs.today.by_service).map(([service, cost]) => (
                <div key={service} className="breakdown-item">
                  <span>{service}</span>
                  <span>${cost}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="cost-card">
            <h3>This Month</h3>
            <p className="cost-value">${costs.month.total_usd}</p>
            <div className="budget-bar">
              <div 
                className="budget-progress"
                style={{ width: `${(costs.month.total_usd / 50) * 100}%` }}
              />
            </div>
            <p className="budget-text">
              ${costs.budget_remaining_usd} remaining of $50 budget
            </p>
          </div>
        </div>
        
        <div className="cost-by-operation">
          <h3>By Operation</h3>
          {Object.entries(costs.month.by_operation).map(([operation, cost]) => (
            <div key={operation} className="operation-row">
              <span className="operation-name">{operation}</span>
              <span className="operation-cost">${cost}</span>
            </div>
          ))}
        </div>
      </section>
      
      {/* Recent Errors */}
      {health.errors_last_24h.length > 0 && (
        <section className="errors-section">
          <h2>Recent Errors</h2>
          {health.errors_last_24h.slice(0, 5).map((error, i) => (
            <div key={i} className="error-item">
              <span className="error-time">{new Date(error.timestamp).toLocaleString()}</span>
              <span className="error-component">{error.component}</span>
              <span className="error-message">{error.error}</span>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}

export default MonitoringDashboard;
```

File: `frontend/src/MonitoringDashboard.css`

```css
.monitoring-dashboard {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.status-badge {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 4px;
  font-weight: bold;
  margin-bottom: 20px;
}

.status-badge.healthy {
  background-color: #10b981;
  color: white;
}

.status-badge.degraded {
  background-color: #f59e0b;
  color: white;
}

.status-badge.critical {
  background-color: #ef4444;
  color: white;
}

.health-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.metric {
  background: #f9fafb;
  padding: 20px;
  border-radius: 8px;
}

.metric h3 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #6b7280;
}

.metric .value {
  font-size: 32px;
  font-weight: bold;
  margin: 0;
  color: #111827;
}

.metric .label {
  font-size: 12px;
  color: #9ca3af;
  margin: 5px 0 0 0;
}

.cost-overview {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin: 20px 0;
}

.cost-card {
  background: #f9fafb;
  padding: 20px;
  border-radius: 8px;
}

.cost-value {
  font-size: 36px;
  font-weight: bold;
  color: #059669;
  margin: 10px 0;
}

.budget-bar {
  height: 20px;
  background: #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  margin: 10px 0;
}

.budget-progress {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #059669);
  transition: width 0.3s ease;
}

.error-item {
  display: grid;
  grid-template-columns: 150px 120px 1fr;
  gap: 10px;
  padding: 10px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
}

.error-time {
  color: #6b7280;
}

.error-component {
  font-weight: 600;
  color: #ef4444;
}
```

**Access dashboard**: http://localhost:3000/monitoring

---

## Part 6: Alerting (Email/Slack)

### Email Alerts (Optional)

```bash
pip install python-dotenv smtplib
```

File: `skill_seeker_mcp/utils/alerts.py`

```python
import smtplib
from email.mime.text import MIMEText
import os

def send_email_alert(subject: str, body: str):
    """Send email alert via SMTP"""
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = os.getenv("ALERT_EMAIL_FROM")
    msg['To'] = os.getenv("ALERT_EMAIL_TO")
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(
            os.getenv("ALERT_EMAIL_FROM"),
            os.getenv("ALERT_EMAIL_PASSWORD")
        )
        smtp.send_message(msg)

# Usage in SessionStart hook
if today_cost > 10.0:
    send_email_alert(
        subject="Finance App: Daily Cost Alert",
        body=f"Daily API cost ${today_cost:.2f} exceeds $10 threshold.\n\nCheck dashboard: http://localhost:3000/monitoring"
    )
```

---

## Summary

**Observability Components Implemented**:

✅ **Structured Logging**:
- JSON logs at `logs/finance_app.log`
- Tool call tracking with timing
- Error logs with stack traces

✅ **SessionStart Hooks**:
- Pipeline health check
- Daily cost tracking
- Data freshness validation
- Disk space monitoring
- Error summaries

✅ **Cost Tracking**:
- Per-operation cost logging
- Daily/monthly budgets
- Real-time alerts (> $10/day)
- Cost breakdown by service/operation

✅ **Health Monitoring**:
- DuckDB health (size, tables, filings)
- ChromaDB health (collections, embeddings)
- API quota checks
- Error analytics

✅ **Dashboards**:
- Real-time health status
- Cost trends visualization
- Budget tracking
- Recent errors display

**Next**: [14-config-files.md](14-config-files.md) for complete JSON configuration files.
