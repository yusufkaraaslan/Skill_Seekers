# Weekly Milestones (4-Week Development Plan)

**Aligned with Derek Snow's "Agentic AI in Asset Management" course structure**.

Each week builds on the previous, following the stateless workflow → hybrid RAG → DSPy optimization → observability progression.

---

## Overview

```
Week 1 (Research)      → Ingest 5 companies, validate data quality
Week 2 (Analytics)     → Build text-to-SQL with DSPy, 90% accuracy
Week 3 (Chat UI)       → RAG chat interface with WebSockets
Week 4 (Scale)         → 20+ companies, cost optimization, monitoring
```

**Cost tracking** (cumulative):
- Week 1: $0.10 (5 filings × $0.02)
- Week 2: $2.50 (testing + DSPy optimization)
- Week 3: $4.00 (chat sessions)
- Week 4: $6.00 (scale to 20 companies)
- **Total: $12.60 / $50 budget (25% used)**

---

## Week 1: Research & Data Foundation

**Derek Snow Alignment**: Session 1 (Stateless Workflows) + Session 2 (Section-Aware Chunking)

### Goals

- ✅ Ingest 5 value companies (diversified sectors)
- ✅ Validate data quality (chunk relevance > 80%)
- ✅ Establish baseline retrieval accuracy
- ✅ Cost < $0.15

### Day 1-2: Batch Ingestion

**Companies to ingest** (value investing focus):
1. **TSLA** (EV/Technology) - Already done in setup
2. **BRK.B** (Berkshire Hathaway - diversified value)
3. **JNJ** (Johnson & Johnson - healthcare)
4. **V** (Visa - fintech)
5. **DIS** (Disney - media/entertainment)

**Tasks**:

```
# Day 1: Ingest TSLA, BRK.B, JNJ
User: "@financial-data-engineer batch ingest TSLA, BRK.B, JNJ latest 10-K"

Claude:
1. Estimate cost: 3 filings × $0.02 = $0.06
2. Confirm with user: "Proceed with batch ingestion ($0.06)?"
3. Ingest sequentially:
   - TSLA: ✅ 421 chunks, 18 tables (already done)
   - BRK.B: ✅ 587 chunks, 24 tables (35.2s, $0.021)
   - JNJ: ✅ 398 chunks, 15 tables (29.8s, $0.020)
4. Validate: diagnose_pipeline_health()
   → ✅ 3 filings, 1,406 chunks, 0 errors

# Day 2: Ingest V, DIS
User: "@financial-data-engineer batch ingest V, DIS latest 10-K"

Claude:
1. Estimate: $0.04
2. Ingest:
   - V: ✅ 412 chunks, 19 tables
   - DIS: ✅ 453 chunks, 21 tables
3. Final count: 5 filings, 2,271 chunks
```

**Success Metrics**:
- ✅ 5 filings ingested
- ✅ ~2,200+ chunks total
- ✅ Cost < $0.15
- ✅ Pipeline health: "healthy"

---

### Day 3-4: Quality Validation

**Task 1: Chunk Quality Check**

```sql
-- Query to check chunk distribution
SELECT ticker, COUNT(*) as chunk_count, AVG(LENGTH(text)) as avg_chars
FROM chunks
GROUP BY ticker
ORDER BY chunk_count DESC;

Expected results:
BRK.B   587   1,200 chars/chunk
DIS     453   1,150
TSLA    421   1,180
V       412   1,160
JNJ     398   1,170
```

**Task 2: Section Coverage Validation**

```sql
-- Ensure all critical sections captured
SELECT ticker, section, COUNT(*) as chunks
FROM chunks
WHERE section LIKE '%Item 1A%'  -- Risk Factors
   OR section LIKE '%Item 7%'   -- MD&A
   OR section LIKE '%Item 8%'   -- Financial Statements
GROUP BY ticker, section
ORDER BY ticker, section;

Expected: Each ticker should have chunks from Items 1A, 7, 8
```

**Task 3: Retrieval Quality Test**

```
User: "@rag-orchestrator test retrieval quality for all companies"

Claude will:
1. For each company:
   - Query: "What are the main risks?"
   - Hybrid search → top 10 chunks
   - Validate avg_score > 0.7
2. Report:
   TSLA: ✅ avg_score=0.84
   BRK.B: ✅ avg_score=0.79
   JNJ: ✅ avg_score=0.81
   V: ✅ avg_score=0.82
   DIS: ✅ avg_score=0.78
```

**Success Metrics**:
- ✅ All companies avg_score > 0.75
- ✅ All critical sections (1A, 7, 8) represented
- ✅ No missing chunks (manual spot-check 5 random pages)

---

### Day 5-7: Baseline Analytics

**Task 1: SQL Accuracy Baseline**

```
User: "@sql-analyst test queries on all 5 companies"

Test queries:
1. "What's TSLA revenue in 2024?"
   Expected: $96.8B
   Actual: (validate against 10-K page 53)

2. "Compare revenue growth: TSLA vs V"
   Expected: TSLA +18.8%, V +10.2%
   Actual: (validate)

3. "Which company has highest P/E ratio?"
   Expected: TSLA (45.2)
   Actual: (validate)
```

Track accuracy:
- **Baseline**: 60-70% correct (before DSPy optimization)
- **Target Week 2**: 90%+ correct (after DSPy)

**Task 2: Cost Tracking Setup**

```sql
-- Insert cost records
INSERT INTO api_costs (service, operation, tokens_used, cost_usd, ticker)
VALUES 
  ('google', 'table_extraction', 15000, 0.021, 'TSLA'),
  ('google', 'table_extraction', 18000, 0.021, 'BRK.B'),
  ...;

-- Query total costs
SELECT 
  SUM(cost_usd) as total_cost,
  COUNT(DISTINCT ticker) as companies_ingested,
  AVG(cost_usd) as avg_cost_per_filing
FROM api_costs
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days';

Expected:
total_cost: $0.10
companies: 5
avg_cost: $0.02
```

**Week 1 Deliverables**:
- ✅ 5 companies ingested with high quality
- ✅ Baseline SQL accuracy: 60-70%
- ✅ Baseline RAG quality: avg_score 0.75+
- ✅ Cost tracking operational
- ✅ Health monitoring dashboard functional

---

## Week 2: Text-to-SQL with DSPy Optimization

**Derek Snow Alignment**: Session 4 (DSPy Text-to-SQL)

### Goals

- ✅ Optimize SQL generation to 90%+ accuracy
- ✅ Handle complex analytical queries
- ✅ Implement query validation pipeline
- ✅ Cost < $3.00 total

---

### Day 8-9: DSPy Setup

**Task 1: Install DSPy**

```bash
pip install dspy-ai
```

**Task 2: Create Training Examples**

File: `data/sql_training_examples.json`

```json
[
  {
    "question": "What is Tesla's total revenue in 2024?",
    "schema": "filings(ticker, filing_date, revenue, ...)",
    "sql": "SELECT revenue FROM filings WHERE ticker = 'TSLA' AND fiscal_year = 2024",
    "explanation": "Retrieve revenue column for TSLA in 2024"
  },
  {
    "question": "Compare revenue growth between TSLA and V over last 3 years",
    "schema": "filings(ticker, filing_date, revenue, ...)",
    "sql": "SELECT ticker, filing_date, revenue, (revenue - LAG(revenue) OVER (PARTITION BY ticker ORDER BY filing_date)) / LAG(revenue) * 100 AS growth_pct FROM filings WHERE ticker IN ('TSLA', 'V') AND fiscal_year >= 2021 ORDER BY ticker, filing_date",
    "explanation": "Calculate YoY revenue growth for TSLA and V using window functions"
  },
  {
    "question": "Which company has the highest net income?",
    "schema": "filings(ticker, net_income, ...)",
    "sql": "SELECT ticker, net_income FROM filings WHERE fiscal_year = 2024 ORDER BY net_income DESC LIMIT 1",
    "explanation": "Find company with max net_income in latest year"
  }
]
```

Create 20-30 examples covering:
- Simple single-column queries
- Aggregations (SUM, AVG, MAX)
- Window functions (LAG, LEAD, ROW_NUMBER)
- JOINs (if you add dimension tables later)
- Complex filters (date ranges, multiple conditions)

---

### Day 10-12: DSPy Optimization

**Task 1: Baseline Evaluation (Pre-Optimization)**

```python
# scripts/evaluate_sql_baseline.py

import dspy
import json

# Load training examples
with open("data/sql_training_examples.json") as f:
    examples = json.load(f)

# Define DSPy signature
class TextToSQL(dspy.Signature):
    """Convert natural language to SQL"""
    schema = dspy.InputField(desc="Database schema")
    question = dspy.InputField(desc="User question")
    sql_query = dspy.OutputField(desc="Valid SQL query")
    explanation = dspy.OutputField(desc="Query explanation")

# Use basic Chain of Thought
text_to_sql = dspy.ChainOfThought(TextToSQL)

# Evaluate
correct = 0
for example in examples:
    result = text_to_sql(schema=example["schema"], question=example["question"])
    
    # Validate SQL matches expected
    if result.sql_query.strip() == example["sql"].strip():
        correct += 1
    else:
        print(f"❌ Failed: {example['question']}")
        print(f"   Expected: {example['sql']}")
        print(f"   Got: {result.sql_query}")

baseline_accuracy = correct / len(examples)
print(f"Baseline accuracy: {baseline_accuracy:.1%}")
```

Expected baseline: **60-70% accuracy**

---

**Task 2: DSPy Optimization with BootstrapFewShot**

```python
# scripts/optimize_sql_with_dspy.py

import dspy
from dspy.teleprompt import BootstrapFewShot

# Configure Claude Sonnet as LLM
lm = dspy.Claude(model="claude-3-5-sonnet-20241022", api_key=os.getenv("ANTHROPIC_API_KEY"))
dspy.settings.configure(lm=lm)

# Load examples
with open("data/sql_training_examples.json") as f:
    examples = [dspy.Example(**ex).with_inputs("schema", "question") for ex in json.load(f)]

# Define metric (exact match)
def sql_exact_match(example, prediction, trace=None):
    return example.sql.strip() == prediction.sql_query.strip()

# Optimize with BootstrapFewShot
optimizer = BootstrapFewShot(
    metric=sql_exact_match,
    max_bootstrapped_demos=8,
    max_labeled_demos=4
)

optimized_text_to_sql = optimizer.compile(
    dspy.ChainOfThought(TextToSQL),
    trainset=examples[:20],  # Use 20 for training
    valset=examples[20:]     # Hold out rest for validation
)

# Save optimized prompts
optimized_text_to_sql.save("configs/dspy_text_to_sql.json")

# Evaluate on validation set
correct = sum(sql_exact_match(ex, optimized_text_to_sql(**ex.inputs())) for ex in examples[20:])
optimized_accuracy = correct / len(examples[20:])

print(f"Baseline: {baseline_accuracy:.1%}")
print(f"Optimized: {optimized_accuracy:.1%}")
print(f"Improvement: +{(optimized_accuracy - baseline_accuracy) * 100:.1f}%")
```

Expected optimized: **85-95% accuracy** (+25-35% improvement)

**Cost**: ~$2.00 for DSPy optimization (Claude API calls during training)

---

### Day 13-14: Integration & Testing

**Task 1: Update `preview_sql_query` Tool**

```python
# skill_seeker_mcp/finance_tools/query.py

import dspy

# Load optimized DSPy model
text_to_sql = dspy.ChainOfThought(TextToSQL)
text_to_sql.load("configs/dspy_text_to_sql.json")

@server.tool()
async def preview_sql_query(question: str, schema_path: str = "data/schema.sql", dry_run: bool = True):
    # Load schema
    with open(schema_path) as f:
        schema = f.read()
    
    # Generate SQL with optimized DSPy
    result = text_to_sql(schema=schema, question=question)
    
    # ... rest of validation logic same as before ...
```

**Task 2: End-to-End Testing**

```
User: "@sql-analyst Compare revenue growth for all 5 companies in my database"

Expected:
1. Load schema
2. Generate SQL with optimized DSPy:
   SELECT ticker, 
          (revenue - LAG(revenue) OVER (PARTITION BY ticker ORDER BY filing_date)) / LAG(revenue) * 100 AS growth_pct
   FROM filings
   ORDER BY growth_pct DESC
3. Validate (safety_check: passed)
4. Execute
5. Format results:
   
   Revenue Growth (2023→2024):
   V:      +12.3%
   JNJ:    +10.7%
   TSLA:   +18.8%
   DIS:    +5.2%
   BRK.B:  +8.9%
```

**Success Metrics**:
- ✅ SQL accuracy: 90%+ on test queries
- ✅ Complex queries working (window functions, aggregations)
- ✅ Query validation catching unsafe operations
- ✅ Cost < $3.00 cumulative

---

## Week 3: RAG Chat UI with WebSockets

**Derek Snow Alignment**: Session 2 (Hybrid RAG) + Session 5 (Observability)

### Goals

- ✅ Build real-time chat interface
- ✅ Implement hybrid RAG (BM25 + semantic + reranking)
- ✅ Add provenance (source citing)
- ✅ WebSocket streaming for responses
- ✅ Cost < $5.00 total

---

### Day 15-16: Backend Setup

**Task 1: Create FastAPI Backend**

File: `backend/main.py`

```python
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import anthropic
import os

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        # Receive user message
        message = await websocket.receive_text()
        
        # Call hybrid_rag_search MCP tool
        rag_results = await hybrid_rag_search(message, "sec_filings_tsla")
        
        # Construct prompt with retrieved chunks
        context = "\n\n".join([
            f"[Source: {chunk['source']}, Page {chunk['page']}]\n{chunk['text']}"
            for chunk in rag_results["chunks"]
        ])
        
        prompt = f"""You are a financial analyst. Answer the user's question using only the provided SEC filing excerpts.

Context from SEC filings:
{context}

User question: {message}

Instructions:
- Only use information from the provided context
- Cite sources with [Source: URL, Page X] format
- If context doesn't contain answer, say "I don't have that information in the filings"
"""
        
        # Stream response
        with client.messages.stream(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                await websocket.send_text(text)
        
        # Send end-of-stream marker
        await websocket.send_text("[DONE]")

@app.get("/health")
async def health_check():
    # Call diagnose_pipeline_health MCP tool
    health = await diagnose_pipeline_health()
    return health
```

**Run backend**:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

---

### Day 17-18: Frontend Chat UI

**Task 1: Create React Frontend**

```bash
npx create-react-app frontend
cd frontend
npm install --save socket.io-client
```

File: `frontend/src/App.js`

```javascript
import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    ws.current = new WebSocket('ws://localhost:8000/ws/chat');
    
    ws.current.onmessage = (event) => {
      if (event.data === '[DONE]') {
        setIsStreaming(false);
      } else {
        // Append streaming text to last message
        setMessages(prev => {
          const newMessages = [...prev];
          if (newMessages[newMessages.length - 1]?.role === 'assistant') {
            newMessages[newMessages.length - 1].content += event.data;
          } else {
            newMessages.push({ role: 'assistant', content: event.data });
          }
          return newMessages;
        });
      }
    };

    return () => ws.current.close();
  }, []);

  const sendMessage = () => {
    if (!input.trim()) return;
    
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    
    // Send to backend
    ws.current.send(input);
    setIsStreaming(true);
    setInput('');
  };

  return (
    <div className="App">
      <header>
        <h1>Finance Screener Chat</h1>
      </header>
      
      <div className="chat-container">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="content">{msg.content}</div>
          </div>
        ))}
        {isStreaming && <div className="typing-indicator">Analyzing...</div>}
      </div>
      
      <div className="input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask about SEC filings..."
          disabled={isStreaming}
        />
        <button onClick={sendMessage} disabled={isStreaming}>Send</button>
      </div>
    </div>
  );
}

export default App;
```

**Run frontend**:

```bash
npm start  # Opens http://localhost:3000
```

---

### Day 19-21: Testing & Refinement

**Task 1: Test Chat Interactions**

Example conversations:

```
User: "What are Tesla's main risks?"

Assistant (streaming):
Based on Tesla's 10-K filing from 2024, here are the main risks:

**1. Production and Manufacturing** [Source: 10-K 2024, Page 42]
Tesla faces challenges in scaling production across its Gigafactories. The company states: "Our ability to achieve production targets depends on successful scaling of manufacturing capacity..."

**2. Regulatory Environment** [Source: 10-K 2024, Page 47]
Changes to government incentives could impact demand. From the filing: "Changes to EV tax credits could materially impact demand for our vehicles..."

**3. Competition** [Source: 10-K 2024, Page 51]
Increasing competition from traditional automakers and new EV startups: "We face increasing competition as both traditional automotive manufacturers and new entrants introduce electric vehicles..."
```

**Task 2: Add Multi-Company Support**

Update backend to auto-detect ticker in question:

```python
# backend/main.py

import re

def detect_ticker(question: str) -> str:
    """Extract ticker from question"""
    tickers = ["TSLA", "BRK.B", "JNJ", "V", "DIS"]
    
    for ticker in tickers:
        if ticker.lower() in question.lower():
            return ticker
    
    # Default to TSLA
    return "TSLA"

@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    # ... (same as before) ...
    
    # Detect ticker
    ticker = detect_ticker(message)
    collection = f"sec_filings_{ticker.lower().replace('.', '_')}"
    
    # RAG search with detected collection
    rag_results = await hybrid_rag_search(message, collection)
    
    # ... (rest same) ...
```

**Task 3: Cost Optimization**

Add cost tracking to each chat:

```python
# Log API costs
async def log_chat_cost(ticker: str, tokens_used: int, cost_usd: float):
    conn = duckdb.connect("data/finance.duckdb")
    conn.execute("""
        INSERT INTO api_costs (service, operation, tokens_used, cost_usd, ticker)
        VALUES (?, ?, ?, ?, ?)
    """, ["anthropic", "chat_response", tokens_used, cost_usd, ticker])
    conn.close()

# After streaming response
usage = stream.get_final_message().usage
cost = usage.input_tokens * 0.003 / 1000 + usage.output_tokens * 0.015 / 1000
await log_chat_cost(ticker, usage.input_tokens + usage.output_tokens, cost)
```

**Week 3 Deliverables**:
- ✅ Real-time chat UI with streaming responses
- ✅ Hybrid RAG retrieval with provenance
- ✅ Multi-company support (auto-detect ticker)
- ✅ Cost tracking per chat session
- ✅ Cumulative cost < $5.00

---

## Week 4: Scale & Production Readiness

**Derek Snow Alignment**: Session 3 (Security) + Session 5 (Monitoring)

### Goals

- ✅ Scale to 20+ companies
- ✅ Implement observability (SessionStart hooks)
- ✅ Cost optimization (< $10/month)
- ✅ Production deployment ready

---

### Day 22-24: Batch Scaling

**Task 1: Ingest 15 Additional Companies**

Target companies (value investing screeners often track):
- Tech: AAPL, MSFT, GOOGL, META, NVDA
- Finance: JPM, BAC, WFC
- Healthcare: UNH, PFE, ABBV
- Consumer: PG, KO, WMT
- Industrial: BA, CAT

```
User: "@financial-data-engineer batch ingest AAPL, MSFT, GOOGL, META, NVDA, JPM, BAC, WFC, UNH, PFE, ABBV, PG, KO, WMT, BA, CAT latest 10-K"

Claude:
1. Estimate: 15 filings × $0.02 = $0.30
2. User confirms
3. Ingest sequentially (avoid rate limiting):
   - Progress: ✅ 5/15 complete (AAPL, MSFT, GOOGL, META, NVDA)
   - Progress: ✅ 10/15 complete (+ JPM, BAC, WFC, UNH, PFE)
   - Progress: ✅ 15/15 complete
4. Final stats:
   - 20 total companies
   - ~9,000 chunks
   - Cost: $0.40 total (20 filings × $0.02)
```

---

### Day 25-26: SessionStart Hooks (Observability)

**Task 1: Implement SessionStart Hook**

File: `skill_seeker_mcp/hooks/session_start.py`

```python
import structlog
import duckdb
from datetime import datetime

logger = structlog.get_logger()

async def on_session_start():
    """Run diagnostics at start of every Claude Code session"""
    
    logger.info("session_start_hook.triggered")
    
    # 1. Check pipeline health
    health = await diagnose_pipeline_health()
    logger.info("pipeline_health", status=health["overall_health"])
    
    # 2. Check daily API spend
    conn = duckdb.connect("data/finance.duckdb", read_only=True)
    today_cost = conn.execute("""
        SELECT SUM(cost_usd) 
        FROM api_costs 
        WHERE DATE(timestamp) = CURRENT_DATE
    """).fetchone()[0] or 0.0
    
    logger.info("daily_api_cost", cost_usd=today_cost, budget_usd=50.0)
    
    # 3. Alert if approaching budget
    if today_cost > 10.0:
        logger.warning("daily_budget_alert", 
                      message=f"Daily spend ${today_cost:.2f} exceeds $10 threshold")
    
    # 4. Data freshness check
    last_ingestion = conn.execute("""
        SELECT MAX(ingestion_timestamp) FROM filings
    """).fetchone()[0]
    
    days_since_update = (datetime.now() - last_ingestion).days
    
    if days_since_update > 7:
        logger.warning("stale_data", 
                      message=f"Last ingestion was {days_since_update} days ago")
    
    conn.close()
    
    return {
        "status": "session_initialized",
        "pipeline_health": health["overall_health"],
        "today_cost_usd": today_cost,
        "companies": health["components"]["duckdb"]["filings"],
        "data_freshness_days": days_since_update
    }
```

**Register hook in MCP server**:

```python
# skill_seeker_mcp/server.py

from hooks.session_start import on_session_start

@server.on_session_start
async def session_start_handler():
    return await on_session_start()
```

**Test**:
Restart Claude Code → check logs for session start diagnostics

---

### Day 27-28: Cost Optimization

**Task 1: Optimize Gemini Table Extraction**

Strategy: Only extract tables when needed (not all filings have useful tables)

```python
# skill_seeker_mcp/finance_tools/ingestion.py

async def ingest_sec_filing(filing_url: str, ticker: str, extract_tables: bool = "auto"):
    """
    extract_tables options:
    - True: Always extract (costs $0.02)
    - False: Never extract (free)
    - "auto": Smart detection (free for most filings)
    """
    
    if extract_tables == "auto":
        # Heuristic: Only extract for 10-K (not 10-Q, 8-K)
        if "10-K" in filing_url or "10-k" in filing_url:
            extract_tables = True
        else:
            extract_tables = False
    
    # ... rest same ...
```

**Savings**: $0.02 × 60% of filings = ~$0.012/filing average (40% reduction)

**Task 2: Cache Embeddings**

Avoid re-embedding same text:

```python
# Embeddings cache (in-memory for session)
embedding_cache = {}

def embed_with_cache(text: str) -> list:
    cache_key = hash(text)
    
    if cache_key in embedding_cache:
        return embedding_cache[cache_key]
    
    embedding = embedding_model.encode([text])[0]
    embedding_cache[cache_key] = embedding
    return embedding
```

**Savings**: ~20% fewer embedding calls on duplicate chunks

---

### Day 29-30: Production Deployment Prep

**Task 1: Docker Containerization**

File: `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

File: `docker-compose.yml`

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    env_file:
      - .env
  
  frontend:
    image: node:18
    working_dir: /app
    volumes:
      - ./frontend:/app
    ports:
      - "3000:3000"
    command: npm start
```

**Deploy**:

```bash
docker-compose up -d
```

**Task 2: Monitoring Dashboard**

Create simple health dashboard:

File: `frontend/src/Dashboard.js`

```javascript
import React, { useState, useEffect } from 'react';

function Dashboard() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => setHealth(data));
  }, []);

  if (!health) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      <h2>Pipeline Health</h2>
      <div className={`status ${health.overall_health}`}>
        {health.overall_health.toUpperCase()}
      </div>
      
      <div className="metrics">
        <div className="metric">
          <h3>Companies</h3>
          <p>{health.components.duckdb.filings}</p>
        </div>
        <div className="metric">
          <h3>Total Chunks</h3>
          <p>{health.components.chroma.total_embeddings}</p>
        </div>
        <div className="metric">
          <h3>Errors (24h)</h3>
          <p>{health.errors_last_24h.length}</p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
```

---

**Week 4 Deliverables**:
- ✅ 20+ companies ingested
- ✅ SessionStart hooks for observability
- ✅ Cost optimization (< $10/month projected)
- ✅ Docker deployment ready
- ✅ Health monitoring dashboard

---

## Final Success Metrics (End of Week 4)

**Data**:
- ✅ 20+ companies (diverse sectors)
- ✅ 9,000+ chunks embedded
- ✅ 300+ tables extracted

**Accuracy**:
- ✅ SQL queries: 90%+ accurate (DSPy-optimized)
- ✅ RAG retrieval: 0.80+ avg_score
- ✅ Chat responses: Cited sources, factually correct

**Performance**:
- ✅ Query latency: < 2s (SQL), < 3s (RAG)
- ✅ Chat streaming: Real-time response

**Cost**:
- ✅ Total API spend: $6-$10 (well under $50 budget)
- ✅ Monthly projection: $6-$10 (88% under budget)

**Observability**:
- ✅ SessionStart hooks running
- ✅ Cost tracking per operation
- ✅ Error logging operational
- ✅ Health dashboard live

---

## Next Steps (Post-Week 4)

### Enhancements (Optional)

1. **Add more companies**: Expand to S&P 500 (500 companies × $0.02 = $10)
2. **Historical analysis**: Ingest 3+ years of filings per company
3. **Alerting**: Email/Slack notifications for new filings
4. **Advanced analytics**: Sector comparisons, peer analysis
5. **Frontend polish**: Charts (revenue trends), export to PDF

### Maintenance (Ongoing)

- **Weekly**: Ingest new 10-Q filings (quarterly earnings)
- **Monthly**: Re-optimize DSPy with new examples
- **Quarterly**: Review cost trends, optimize expensive operations

---

**Continue to**: [13-monitoring-observability.md](13-monitoring-observability.md) for comprehensive monitoring setup.
