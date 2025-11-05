Title: 

URL Source: https://www.agenticfinance.ai/assets/Genai_and_Agentic_Finance-1.pdf

Published Time: Mon, 03 Nov 2025 14:02:49 GMT

Markdown Content:
# Agentic AI in Asset Management: 5-Week Technical Course     

> A syllabus for building production-grade, reliable AI systems for finance. Authored by Derek Snow.
> Audience: Quantitative Researchers, Portfolio Managers, AI Engineers ·Format: Technical Deep-Dive Sessions ·Objective: From Prototype to Production

1 Tools & Infrastructure That Actually Ship 

PROMISE 

Choose a stack that gets to production safely and fast—workflows first, agents only when necessary. 

DO 

• Adopt stateless, workflow-first pat-terns for reliability. 

• Standardize structured outputs (JSON + schema validation). 

• Use foundational models; avoid premature fine-tuning. 

• Instrument observability (logs, traces, cost/tokens) from day one. 

SKIP 

• Training your own foundation models. 

• Over-frameworking with demo-ware that won’t survive prod. 

• Building stateful, multi-step agents that compound er-rors. 

HACKS & CHEATS 

• Single-pass first; add loops only if accuracy demands it. 

• Thin DIY orchestration > heavy frameworks for latency/control. 

DELIVERABLE 

Reference architecture + 30-day plan to ship one workflow. 

“Finance needs reliability. Autonomous agents are risky for mission-critical tasks; use guided workflows that embed expertise.” 

2 MCPs, Multi-Agents & Security Boundaries 

PROMISE 

Standardize tool access without chaos, ensuring tools are governed, auditable, and reusable across the enterprise. 

DO 

• Master the 4 primitives: Tools (ac-tions), Resources (read), Prompts 

(flows), Sampling (host-side rea-soning). 

• Design a three-environment secu-rity model (Research/Data/Execu-tion). 

• Expose business-level tools (e.g., 

run_scenario ) instead of raw APIs. 

SKIP 

• Letting LLMs call vendor APIs directly without governance. 

• Exposing 50+ tools with no namespacing or collision pol-icy. 

HACKS & CHEATS 

• A Meta-MCP hub for routing, secrets, and unified logging. 

• Keep tools async; offload CPU-heavy calls from the main loop. 

DELIVERABLE 

Governed MCP tool catalog + sample policies & approval flows. 

“Agents only need four pieces: an LLM client, function-calling tools, a vector store, and observability — no heavy framework required.” 

3 Context Engineering (RAG That Isn’t a Toy) 

PROMISE 

Build a retrieval system that’s clean, hybrid, deduped, and cited—so portfolio managers actually trust the output. 

DO 

• Convert messy PDFs/HTML into clean, structured Markdown. 

• Use hybrid retrieval (key-word+vector), then rerank and dedupe. 

• Pack context to fit: summa-rize/trim, cache state, write to memory. 

• Always attach sources and page numbers to every claim. 

SKIP 

• Shipping vector-only demos with unclean, unvetted docu-ments. 

• Stuffing the context window without clear provenance. 

HACKS & CHEATS 

• Start with a local Parquet+RAM index before scaling to a vector DB. 

• Blend content and metadata embeddings for better retrieval. 

DELIVERABLE 

Hardened retrieval checklist + a ready-to-run local RAG starter kit. 

“Context is king. Don’t tune weights, tune what the model sees: clean chunks, hybrid retrieval, and cited sources.” 

4 Programmatic Prompting with DSPy 

PROMISE 

Move from brittle, manual prompts to structured, self-optimizing pro-grams that are robust to model updates. 

DO 

• Use DSPy’s Signatures (intent), Modules (logic), and Optimizers. 

• Define a "golden dataset" and clear evaluation metrics first. 

• Decompose large tasks into smaller, classifiable sub-problems. 

• Enforce structured JSON output with Pydantic models. 

SKIP 

• Manual, trial-and-error prompting that breaks on every update. 

• One-shot mega-prompts with hidden, untestable assump-tions. 

HACKS & CHEATS 

• A few high-quality, edge-case examples beat many generic ones. 

• Manual tuning is fine for one-offs; use DSPy for production systems. 

DELIVERABLE 

DSPy program templates + evaluation harness for desk workflows. 

“DSPy transforms manual prompting into a structured machine learning workflow: dataset, model, train, evaluate, test.” 

Week 5 Focus Area The final session covers deploying systems and navigating the open-source tooling landscape. 

5 Deployment, GUIs, and CLIs 

PROMISE 

Navigate the open-source landscape to build, deploy, and operate agentic systems effectively. 

FOCUS 

• Deployment: Deploy agents to the cloud (e.g., Google Agent Engines) with full observability (tracing, logging, monitoring). 

• GUIs & Dashboards: Survey the Python stack from simple (Streamlit) to complex (Reflex) for building custom frontends. 

• CLI Agents: Compare and contrast Claude Code, Gemini CLI, and Codex for autonomous, terminal-based coding tasks. 

“Prototype in minutes: fetch filings → extract ratios → draft a factor note.” Session 1: Tools & Infrastructure That Actually Ship 

CORE CONCEPTS Agentic AI in finance succeeds when simple, stateless workflows ship reliably, while looping, stateful agents are reserved for scenarios with measurable value. This session emphasizes code-driven orchestration (prompt chaining, routing, tool-use) over heavy frameworks, with observability and cost discipline instrumented from day one. The fundamental architecture is AAI =

LLM + Actions , where Actions encompass Tool-use, Memory, and Planning capabilities. 

LEARNING OBJECTIVES 

• Build prompt-chained workflows that decompose financial tasks (extraction, synthesis, reporting) without fragile agent loops, achieving predictable token costs and error rates. 

• Run parallel specialists for fundamentals/valuation/sentiment analysis using async patterns (Python asyncio) or ADK parallelism, reducing latency by 3-5x. 

• Implement routing + tool-use for finance APIs (FMP, Alpha Vantage) and search services (Scrapingdog, Reuters), with clear approval scopes, structured logging, and cost tracking. 

• Instrument observability (traces, logs, token/cost metrics) as part of the development loop using LangSmith, Weights & Biases, or custom telemetry. 

• Analyze failure modes: Error compounding (99% per-step accuracy → 82% over 20 steps) and quadratic token scaling in multi-turn conversations. 

TECHNICAL AGENDA & REPOSITORY MAPPING 

• Prompt Chaining Patterns (CourseMaterial/workflows/1-prompt-chaining/ )

– Prompt_Chaining_Agent.ipynb : Production ADK workflow with 5 specialist agents for financial PDF processing 

* ExtractionAgent : Parses 10-K/10-Q PDFs, extracts revenue/EBITDA/FCF tables with 95%+ accuracy 

* SynthesisAgent : Reconciles multi-year tables, handles restated financials, identifies discontinuities 

* GroundingAgent : Searches Google for forward estimates, validates against consensus (FactSet/Bloomberg patterns) 

* ReconciliationAgent : Cross-checks extracted vs. grounded data, flags >10% deviations 

* ReportingAgent : Generates HTML dashboard with interactive charts (Plotly), styled CSS, CEO commentary integration 

Key Pattern: Each agent maintains stateless context via structured JSON handoff; no conversational history accumulation. Average pipeline: 15K tokens, $0.03 per document. 

– Prompt_Chaining_LLM.ipynb : Framework-free implementation using Gemini 2.5 Flash on Vertex AI 

* Direct genai.GenerativeModel calls with generation_config for temperature (0.1 extraction, 0.7 synthesis) and top-p tuning 

* Manual prompt engineering with chain-of-thought for complex reconciliations 

* Demonstrates 40% lower latency vs. ADK due to reduced abstraction overhead 

• Parallel Agent Architectures (CourseMaterial/workflows/2-parallel-agents/ )

– Parallel_Agents.ipynb : Concurrent equity research with ADK orchestration 

* Three specialists execute simultaneously: FundamentalsAgent (P/E, ROE, margins), ValuationAgent (DCF, comps), SentimentAgent 

(news NLP, social signals) 

* SynthesizerAgent receives all outputs, generates unified investment thesis with confidence scoring 

* Implements ADK’s Session.run_parallel() for true concurrency; 3x speedup over sequential 

* Error handling: Individual agent failures don’t crash pipeline; synthesizer works with partial data 

– Parallel_LLM.ipynb : Pure Python async/await pattern without frameworks 

* Uses asyncio.gather() with aiohttp for concurrent API calls to multiple LLM providers 

* Demonstrates load balancing across Gemini/Claude/GPT-4 for cost optimization 

* Token bucket rate limiting to respect API quotas (e.g., 10K TPM for Gemini Flash) 

* Example: Analyze 50 stocks in parallel (10 concurrent workers) in 45 seconds vs. 6 minutes sequential 

• Routing & Tool Integration (CourseMaterial/workflows/3-routing-and-tool-use/ )

– Gemini Implementations: 

* Routing_Financial_Agents.ipynb : Orchestrator/manager pattern with ADK 

· OrchestratorAgent classifies intent (fundamental data | news | market data), routes to specialists 

· Financial Modeling Prep (FMP) integration: /api/v3/profile/ , /income-statement/ , /ratios/ 

· Implements retry logic (exponential backoff), caching (Redis), and structured logging (JSON with trace IDs) 

* Routing_Financial_LLM.ipynb : Stateless function-calling with Gemini Pro 

· Uses tools parameter with function declarations (JSON Schema for validation) 

· Session management: Maintains conversation state in-memory dict, prunes after 10 turns to prevent token bloat 

· Tool approval gate: User confirms high-impact actions (e.g., execute_trade ) via callback 

* Routing_News_Agents.ipynb : Multi-source news aggregation with validation 

· Reuters API + Scrapingdog web scraping for comprehensive coverage 

· EvaluatorAgent checks: Date within query range, URL accessibility, content relevance (cosine similarity > 0.7) 

· Self-healing: Re-queries on validation failure, max 3 retries with exponential backoff  

> Agentic AI in Asset Management Syllabus Page 2

– OpenAI Implementations: 

* openai_agents_finance_tutorial.ipynb : OpenAI Agents SDK patterns 

· Agent handoffs: /transfer_to_analyst , /transfer_to_risk with context preservation 

· Guardrails: Input validation (no PII), output filtering (no investment advice disclaimers), cost limits ($0.50/query) 

· Custom tools: fetch_earnings_transcript() , calculate_sharpe_ratio() , screen_stocks() 

· Tracing: LangSmith integration with custom metadata (user_id, session_id, trade_intent) 

* openai_agents_llm_judge_tutorial.ipynb : LLM-as-a-Judge evaluation loop 

· EvaluatorAgent scores outputs (relevance 0-10, accuracy 0-10, completeness 0-10) with reasoning 

· OptimizerAgent refines prompts based on scores < 7, suggests retrieval improvements 

· Iterative refinement: Max 3 optimization cycles, convergence when all scores ≥ 8

· Example: News workflow improved from 6.2 → 8.7 avg score after 2 iterations 

KEY ARCHITECTURAL DECISIONS 

• Workflow vs. Agent: Use workflows for >90% of cases; reserve agentic loops for truly non-deterministic exploration (e.g., multi-hop research) 

• Token Economics: Single-pass workflows cost O(n) tokens; multi-turn agents cost O(n2) due to history accumulation 

• Error Mitigation: Prefer retry + fallback over complex self-correction loops; simpler is more reliable 

• Observability First: Log every LLM call (prompt, response, tokens, latency, cost) to a time-series DB for analysis 

HANDS-ON MATERIALS 

• Slides: Week 1 Google Slides | slides/Week1-AIToolReview&Infrastructure.pdf 

• Code: CourseMaterial/workflows/ (6 notebooks, 4000 lines total) 

• Dependencies: google-generativeai , openai , aiohttp , pandas , plotly , pydantic  

> Agentic AI in Asset Management Syllabus Page 3

# Session 2: Context Engineering (RAG That Isn’t a Toy) 

CORE CONCEPTS Context engineering treats the LLM’s context window as operating system RAM with four fundamental operations: 

Write (persist to external storage), Select (intelligent retrieval), Compress (summarize/trim), and Isolate (partition across agents). Performance bottlenecks in finance AI stem from poor document hygiene, inadequate retrieval strategies, and missing provenance—not base model limitations. The optimization problem: ctx ∗ = arg max ctx ∈U Q(ctx ) subject to token budgets and latency constraints. 

LEARNING OBJECTIVES 

• Build an async collection pipeline with rate limiting (100 req/min), retry logic (5 attempts with exp. backoff), and URL hygiene (dedup, robots.txt compliance) across 5+ data sources. 

• Implement AI-powered ingestion using Gemini 2.5 Flash for table extraction (95%+ accuracy on SEC filings), chart OCR, and metadata enrichment (sector, market cap, filing type). 

• Deploy a production vector database with Parquet persistence (10M+ embeddings, 2GB RAM), binary encoding (8x compression vs. float32), metadata blending (30% weight), and sub-100ms retrieval. 

• Attach provenance metadata (source URL, page number, extraction timestamp, confidence score) to every retrieved chunk, enabling drill-down and audit trails. 

• Formalize hybrid retrieval: Combine BM25 (lexical) + ANN (semantic), apply reciprocal rank fusion (RRF), cross-encoder reranking, and cosine deduplication (threshold 0.95). 

TECHNICAL AGENDA & IMPLEMENTATION DETAILS 

Phase 1: Data Collection (CourseMaterial/collection/Data_Collection_Tutorial.ipynb )

• Firecrawl Integration (PDF Discovery & Extraction) 

– Crawl corporate IR pages: /api/v1/crawl with depth=3, max_pages=50, filters for .pdf 

– PDF link extraction with regex patterns for 10-K/10-Q: /edgar/.*10-[KQ].*˙ pdf 

– Async download with aiofiles , rate limiting (10 concurrent), progress bars (tqdm) 

– Example: Collected 230 filings from 50 S&P 500 companies in 12 minutes 

• Apify Actors (Structured Web Scraping) 

– Google Search Actor: Keywords + date filters, extracts title/URL/snippet with schema validation 

– LinkedIn Company Actor: Employee counts, growth rates, job postings (signal for hiring trends) 

– Batch operations: Queue 100+ tasks, poll for completion, handle rate limits (100 API calls/hour) 

– Cost optimization: Use cheapest actors first, fallback to premium for complex pages 

• Nosible (Glassdoor Sentiment Mining) 

– Scrape employee reviews: Rating, title, pros/cons, date, role, location 

– NLP preprocessing: Clean HTML entities, normalize ratings (1-5 scale), extract entities (product names) 

– Aggregate metrics: Avg rating by quarter, sentiment trends (VADER scores), keyword frequencies 

– Use case: Track employee satisfaction as proxy for operational health (correlation with stock returns) 

• Scrapestack (Google SERP Collection) 

– Query construction: "COMPANY_NAME" + "quarterly results" + date:YYYY-MM-DD..YYYY-MM-DD 

– Extract organic results: Title, URL, snippet, position (for ranking analysis) 

– Handle pagination: Up to 10 pages (100 results), detect "no more results" signal 

– Anti-bot measures: Rotate proxies (10 IPs), random delays (2-5s), realistic user-agents 

• Anchor Browser (Dynamic Content Extraction) 

– Headless Chrome automation via Playwright: Wait for networkidle , execute JS, screenshot for debugging 

– Target investor decks: Navigate multi-page presentations, extract slide text + images 

– Handle auth walls: Cookie injection, session management, captcha solving (2Captcha integration) 

– Output: JSON with page_number, text_blocks, image_urls, metadata (fonts, colors for layout analysis) 

• Cross-Source URL Hygiene – Deduplication: Canonical URL normalization (strip query params, lowercase, trailing slash) 

– Robots.txt compliance: Fetch /robots.txt , parse User-agent: * rules, skip disallowed paths 

– Light scoring: Domain authority (MOZ/Ahrefs API), recency (prefer last 90 days), source type (prioritize SEC > news > blogs) 

– Async batching: Process 1000 URLs in <30s using asyncio.gather with semaphore (max 50 concurrent) 

Phase 2: AI-Powered Ingestion (CourseMaterial/ingestion/Ingestion_Tutorial.ipynb , 3000 lines) 

• GCS & Local Ingestion – GCS client: google-cloud-storage with service account auth, list blobs by prefix ( filings/2024/ )

– Local fallback: Scan directories recursively, filter by extension (.pdf, .html), maintain manifest (CSV) 

– File validation: Check magic bytes (PDF: %PDF-, HTML: <html ), reject corrupted files 

• Gemini-Assisted Cleanup – Table extraction prompt: "Extract all tables as Markdown. Use | separators, maintain alignment, label columns clearly."  

> Agentic AI in Asset Management Syllabus Page 4

– Chart OCR: Send image to Gemini 2.0 Pro Vision, prompt: "Describe chart type, axes, data points, key insights." 

– Metadata generation: "Analyze this document. Extract: Company name, filing type, fiscal period, key metrics mentioned." 

– Batch processing: 50 docs/minute with async_chat.send_message_async() , retry on 429/503 errors 

– Quality control: Validate extracted tables (min 2 rows, max 50 columns), flag low-confidence outputs (threshold 0.6) 

• Canonicalization & Deduplication – Content hashing: SHA256 on normalized text (lowercase, strip whitespace, remove punctuation) 

– Near-duplicate detection: MinHash LSH with 128 permutations, Jaccard similarity threshold 0.8 

– Clustering: DBSCAN on LSH signatures, eps=0.2, min_samples=2, assign cluster IDs 

– Keep-one strategy: Within each cluster, select doc with highest source score + most recent timestamp 

• Markdown Conversion Pipeline – selectolax : Fast HTML parsing (10x faster than BeautifulSoup), CSS selector-based extraction 

– lxml : Handle malformed HTML, XPath queries for complex structures, namespace resolution 

– pyhtml2md : Convert to Markdown with options: heading_style="atx" , bullet_style="-" 

– Post-processing: Collapse multiple newlines, fix broken links (resolve relative URLs), normalize headers (max depth 4) 

– Output format: Frontmatter (YAML) + body (Markdown), save as processed/COMPANY_YYYYMM_hash.md 

• API Key Rotation & Rate Management – Multi-key pool: Load 5 Gemini API keys, round-robin assignment, track usage per key 

– Quota monitoring: Parse X-RateLimit-Remaining header, sleep when <10 requests left 

– Fallback strategy: On 429 error, switch key immediately, log exhaustion events, alert on all-keys-exhausted 

– Progress tracking: SQLite DB with columns: file_path, status (pending|processing|complete|failed), retry_count, error_msg 

Phase 3: Production Vector Database (CourseMaterial/vectorized/Vectorized_DB_Tutorial.ipynb )

• Single-Parquet Architecture – Schema: id (str), text (str), embedding (bytes), metadata (json), hash (str) 

– Binary embeddings: Convert float32[384] to bytes with numpy.tobytes() , 8x compression (1.5KB → 192 bytes) 

– Read performance: pyarrow.parquet.read_table loads 1M rows in 0.8s, filters on metadata with predicate pushdown 

– Write pattern: Accumulate embeddings in memory (batches of 10K), append to Parquet every 100K docs to avoid file fragmentation 

• Intelligent Chunking – Section-aware splitting: Detect headers ( ## ), split on header boundaries, keep headers in chunks as context 

– Size control: Target 300 tokens/chunk (embedding model sweet spot), max 512, min 50 (discard short chunks) 

– Overlap strategy: 50 tokens overlap between adjacent chunks to preserve context at boundaries 

– Metadata inheritance: Each chunk inherits doc-level metadata (source, date) + adds chunk_number, parent_section 

• Embedding Pipeline – Model: sentence-transformers/all-MiniLM-L6-v2 (384 dims, 22M params, 80MB, 14K tokens/sec on T4 GPU) 

– Metadata blending: Embed title + first 50 chars of text, weight 30% metadata + 70% content, normalize to unit sphere 

– Batch processing: Encode 64 chunks/batch, GPU acceleration with device=’cuda:0’ , prefetch next batch during encoding 

– Cost: 1M chunks embedded in 45 minutes on single GPU, negligible cost vs. API-based embedding 

• Retrieval & Deduplication – Hybrid search: BM25 on text (Elasticsearch), ANN on embeddings (FAISS with IVF + PQ), retrieve top-50 from each 

– Reciprocal Rank Fusion: Score s(d) = P  

> r∈rankings 1
> k+r(d)

with k = 60 , sort by s(d)

– Cross-encoder reranking: ms-marco-MiniLM-L-6-v2 on top-20 candidates, re-sort by relevance score 

– Deduplication: Compute pairwise cosine similarity on top-20, merge chunks with sim > 0.95, keep highest-scored 

– Final output: Top-10 unique chunks with provenance (source, page, score, rerank_score) 

• GCS-Scale Ingestion – Bulk load: Stream 10K+ SEC filings from GCS (10-Ks, 10-Qs, 8-Ks), parse with sec-edgar-downloader 

– Incremental updates: Daily cron job fetches new filings, embeds, appends to Parquet, rebuilds FAISS index (5 min/day) 

– Partitioning: Separate Parquet files by year (2020-2024), load relevant partitions at query time 

– Backup strategy: Daily snapshot to GCS cold storage, weekly full rebuild from source documents 

PERFORMANCE BENCHMARKS 

• Collection: 500 web pages + 200 PDFs in 25 minutes (async, rate-limited) 

• Ingestion: 1000 documents cleaned and embedded in 40 minutes (Gemini API, GPU embedding) 

• Retrieval: Query latency <100ms (BM25 + FAISS), <300ms with cross-encoder reranking 

• Accuracy: 92% relevant docs in top-5, 78% in top-1 (measured on 500-query benchmark) 

HANDS-ON MATERIALS 

• Slides: Week 2 Google Slides | slides/Week2-ContextEngineering.pdf 

• Code: 3 notebooks ( 5000 lines), sample datasets (100MB), pre-trained models 

• Dependencies: firecrawl-py , apify-client , google-cloud-storage , sentence-transformers , faiss-cpu , pandas , pyarrow  

> Agentic AI in Asset Management Syllabus Page 5

# Session 3: MCPs, Multi-Agents & Security Boundaries 

CORE CONCEPTS The Model Context Protocol (MCP) solves the M × N integration problem—connecting M AI models to N tools—by establishing a universal standard analogous to USB for hardware. MCP defines four primitives: Tools (model-invoked actions with side effects), Resources (app-provided read-only data), Prompts (user-initiated workflows), and Sampling (server-requested LLM reasoning). The design philosophy: Expose "cooked" business-level operations (e.g., schedule_meeting ) rather than "raw" API endpoints to reduce complexity, failure rates, and security surface area. 

LEARNING OBJECTIVES 

• Stand up an in-process FastMCP server (no network, <100 lines) and invoke it from notebooks/CLIs, demonstrating tool/resource/prompt patterns. 

• Build a production MCP server with multi-transport support (STDIO for Claude Desktop/Cline, SSE for web, WebSocket for real-time), auth middleware (API Key/OAuth2/Bearer), and rate limiting (token bucket, 100 req/hour). 

• Integrate MCP with Gemini/ADK : Configure agent tools to call MCP endpoints, debug with MCP Inspector (Chrome extension), and trace function calls through observability stack. 

• Implement three-environment security model : Research (internet-enabled, read-only tools), Data (internal APIs, write-restricted), Execution (air-gapped, approval-gated trades). 

• Differentiate MCP (tool orchestration) from A2A (agent-to-agent) protocols: MCP for single-agent tool access, A2A for multi-agent coordination with message passing. 

TECHNICAL AGENDA & IMPLEMENTATION PATTERNS 

Quick Example: FastMCP Finance VaR (CourseMaterial/modelcontextprotocol/quickexample/FastMCP_Finance_VaR.ipynb )

• In-Process Server Setup – Initialize: mcp = FastMCP("finance-risk-server") , no external dependencies, runs in-memory 

– Decorator pattern: @mcp.tool() for functions, @mcp.resource() for data endpoints 

• Financial Risk Tools – calculate_historical_var(returns: List[float], confidence: float = 0.95) :

* Sort returns, find percentile cutoff, return VaR value + percentile rank 

* Example: 1000 daily returns, 95% confidence → VaR = -2.3%, "Worst 5% of days" 

– stress_test_pnl(positions: Dict[str, float], shocks: Dict[str, float]) :

* Apply market shocks (e.g., SPY: -10%, TLT: +5%) to positions, calculate portfolio impact 

* Return: Total P&L, per-position P&L, largest contributor 

– check_position_limits(positions: Dict[str, float], limits: Dict[str, float]) :

* Compare current exposures vs. risk limits, flag violations with severity (warning | breach) 

* Example: If AAPL position $5M but limit $3M → "BREACH: Over by $2M (67%)" 

• Compliance Resources – /compliance/limits : JSON document with position limits by asset class, sector, single-name 

– /compliance/restricted : List of restricted tickers (insider trading, regulatory), updated daily 

– No-approval needed: Resources are read-only, safe to expose broadly 

• Risk Brief Prompts – daily_risk_brief : Template prompt: "Calculate VaR, check limits, summarize top 5 positions, note any breaches" 

– stress_scenario : Parameterized prompt: "Run stress test with market_shock={shock}, report P&L impact and hedging recommen-dations" 

• Interactive Widgets (Colab) – ipywidgets.Textarea for returns input (CSV), FloatSlider for confidence level 

– Button.on_click() triggers calculate_historical_var , displays result in Output widget 

– Real-time computation: Update VaR/stress results as user adjusts inputs, <100ms latency 

Production MCP Server: Investment Screening (CourseMaterial/modelcontextprotocol/mcp/investment-screening-mcp-serve 

• Multi-Transport Architecture – STDIO : For CLI tools (Claude Desktop, Cline) via sys.stdin.buffer.read() , sys.stdout.buffer.write() 

* Message framing: JSON-RPC 2.0 with \r\n delimiter, handle fragmented reads 

* Example config (Claude Desktop): {"command": "python", "args": ["server.py"], "transport": "stdio"} 

– SSE (Server-Sent Events) : For web dashboards, unidirectional server → client 

* FastAPI route: @app.get("/events") with StreamingResponse , Content-Type: text/event-stream 

* Keep-alive: Send data: {"type": "heartbeat"} every 30s to prevent connection timeout 

– WebSocket : For interactive apps, bidirectional with low latency (<50ms round-trip) 

* FastAPI route: @app.websocket("/ws") , accept connection, await websocket.receive_json() 

* Error handling: Catch WebSocketDisconnect , log session ID, clean up resources  

> Agentic AI in Asset Management Syllabus Page 6

• Investment Data Tools – get_financial_news(query: str, sources: str = "", days_back: int = 7) :

* NewsAPI integration: /v2/everything endpoint, filter by publishedAt, sort by relevancy 

* Return schema: {title, description, url, source, publishedAt, sentiment_score} 

* Rate limiting: 100 calls/day on free tier, cache results for 1 hour (Redis) 

– get_stock_quote(symbol: str) :

* Alpha Vantage: GLOBAL_QUOTE function, parse JSON for open/high/low/close/volume 

* Enrichment: Add 52-week high/low from TIME_SERIES_DAILY cache, calculate distance from high 

– get_company_overview(symbol: str) :

* Alpha Vantage: OVERVIEW function, extract fundamentals (P/E, div yield, ROE, profit margin) 

* Validation: Check for null fields, retry on incomplete data, fallback to Yahoo Finance 

– get_earnings_data(symbol: str) :

* Alpha Vantage: EARNINGS function, quarterly/annual EPS, surprise, estimate 

* Post-process: Calculate surprise %, trend over 4 quarters, flag consensus misses 

– investment_screening_analysis(symbol: str, include_news: bool = True) :

* Orchestration: Parallel calls to quote + overview + earnings + news (if enabled) 

* Synthesis: Combine data, generate summary with bullet points (valuation, momentum, sentiment, catalysts) 

* Example output: "AAPL: Strong fundamentals (P/E 28), +12% YTD momentum, positive news sentiment (15/20 articles), upcoming iPhone launch catalyst" 

• Authentication Middleware – API Key : Header X-API-Key , validate against hash in SQLite DB, log usage per key 

– OAuth2 : Standard flow with /authorize , /token , /refresh endpoints, JWT tokens with 1-hour expiry 

– Bearer Token : Header Authorization: Bearer <token> , validate with identity provider (Auth0, Okta) 

– Basic Auth : Header Authorization: Basic <base64(user:pass)> , bcrypt password hashing, rate limit by IP 

– FastAPI dependency: @app.get("/tool", dependencies=[Depends(verify_api_key)]) 

• Rate Limiting (Token Bucket) – Algorithm: Bucket capacity 100 tokens, refill rate 1 token/36s (100 req/hour), consume 1 token per request 

– Implementation: Redis with INCR + EXPIRE , atomic operations, key= rate_limit:{user_id}:{hour} 

– Response: On limit exceeded, return 429 with Retry-After header (seconds until next token) 

– Tiering: Free (100/hour), Pro (1000/hour), Enterprise (unlimited), check user tier on each request 

• Reliability Patterns – Retry Logic : Exponential backoff on 429/503 errors, jitter to prevent thundering herd, max 5 attempts 

– Circuit Breaker : Open circuit after 10 consecutive failures, half-open after 60s, close on 3 successes 

– Timeouts : HTTP requests timeout after 10s, tool calls timeout after 30s, return partial results on timeout 

– Structured Errors : JSON schema: {code: str, message: str, details: dict, trace_id: str} , log all errors 

• Testing & Integration – Unit Tests : pytest with pytest-mock , mock external APIs, test auth/rate limiting/error handling 

– Integration Tests : Real API calls with test keys, validate response schemas, check idempotency 

– Gemini Integration (test_gemini_integration.py ): 

* FastMCP client: client = MCPClient(server_url) , call tools via Gemini function-calling 

* Example: gemini.generate_content("Get AAPL overview", tools=[client.get_tools()]) 

– Google ADK Integration (test_google_adk_integration.py ): 

* Agent with MCP toolset: agent = Agent(tools=mcp_client.to_adk_tools()) 

* Conversation loop: agent.send_message("Screen tech stocks") , ADK auto-invokes tools 

– MCP Inspector : Chrome extension for debugging, view tool calls, inspect request/response, profile latency 

• Deployment – Docker : Multi-stage build (build deps, runtime image), alpine base (50MB), health check endpoint 

– Cloud Run : Deploy with gcloud run deploy , auto-scaling (1-100 instances), 2 vCPU, 2GB RAM 

– Production Logging : Structured JSON logs (timestamp, level, message, context), send to Cloud Logging, set up alerts on ERROR/-CRITICAL 

– Monitoring : Prometheus metrics (request_count, latency_p95, error_rate), Grafana dashboards, PagerDuty on SLO breaches 

SECURITY ARCHITECTURE: THREE-ENVIRONMENT MODEL 

• Research Environment : Internet access, read-only tools (news, search, public data), no PII, log all queries 

• Data Environment : Internal network only, read/write to data warehouse, audit trail for all writes, no external API calls 

• Execution Environment : Air-gapped, approval-gated actions (trades, fund transfers), human-in-the-loop for $10K+ transactions, immutable audit log 

MCP VS. A2A: WHEN TO USE EACH  

> Agentic AI in Asset Management Syllabus Page 7

• Use MCP when : Single agent needs to access multiple tools, tools are stateless, no agent-to-agent communication required 

• Use A2A when : Multiple agents collaborate (e.g., analyst ↔ risk manager), agents have distinct memory/state, message-passing paradigm fits naturally 

HANDS-ON MATERIALS 

• Code: 1 quick example (200 lines), 1 production server (2000+ lines), integration tests, deployment configs 

• Dependencies: fastmcp , fastapi , uvicorn , redis , alpha-vantage , newsapi-python , pytest 

• Live demo: MCP Inspector debugging session, Claude Desktop integration  

> Agentic AI in Asset Management Syllabus Page 8

# Session 4: Programmatic Prompting with DSPy 

CORE CONCEPTS DSPy (Declarative Self-improving Python) transforms prompt engineering from manual trial-and-error into a structured ML workflow with three abstractions: Signatures (declarative I/O contracts), Modules (composable reasoning strategies), and 

Optimizers (algorithms that auto-tune prompts). The core insight: Separate program logic (what the LLM should do) from parameterization (how to prompt it), enabling automatic optimization against defined metrics. Hand-crafted prompts break with model updates; DSPy programs adapt by recompiling against new models with the same dataset and metric. 

LEARNING OBJECTIVES 

• Build a multi-step DSPy program by composing modules ( dspy.Predict , dspy.ChainOfThought , dspy.ReAct ) with custom control flow and error handling. 

• Define Signatures with Pydantic models for structured I/O: question: str, context: List[str] -> answer: str, confidence: float, reasoning: str .

• Implement custom evaluation metrics (ROC-AUC, precision-recall, F1, BLEU, exact match) that quantify business objectives (e.g., "minimize false positives in credit risk"). 

• Apply DSPy optimizers (BootstrapFewShot, GEPA, MIPROv2) to auto-generate few-shot examples and refine prompts, improving metrics by 20-40% over baseline. 

• Determine when to use DSPy : Production systems with repeated workflows and evaluation harnesses benefit most; one-off analyses often better served by manual prompting. 

TECHNICAL AGENDA & FINANCIAL USE CASES 

Case Study 1: Bank Marketing Optimization (Prompt_Engineering_Bank_Transactions.ipynb )

• Problem Statement – Predict term deposit subscriptions from customer profiles (age, job, balance, campaign history) 

– Output: Subscription likelihood (0-1), key influence factors (ranked), recommended actions 

– Success metric: ROC-AUC (measures ranking quality) + accuracy (classification) 

• DSPy Implementation – Signature : CustomerProfile -> SubscriptionAnalysis 

* Input fields: age: int, job: str, marital: str, balance: int, campaign_count: int, prev_outcome: str 

* Output fields: likelihood: float, factors: List[str], recommendation: str, confidence: float 

– Module : Custom dspy.Module with dspy.ChainOfThought for reasoning 

* Forward method: Extract features → reason about patterns → predict + justify 

* Constraint: Likelihood must be in [0,1], factors ranked by importance, recommendation actionable 

– Training Data : 500 labeled examples (actual subscriptions), 80/20 train/val split 

– Evaluation Metric : roc_auc_score(y_true, predictions.likelihood) , threshold at 0.5 for accuracy 

• Optimization Process – Baseline (zero-shot): 0.68 AUC, 72% accuracy 

– BootstrapFewShot (5 examples, 10 bootstrap rounds): 0.79 AUC, 81% accuracy 

* Selects informative examples (high uncertainty, diverse profiles), adds to prompt 

* Example selection: Customer A (high balance, rejected last time → no subscription), Customer B (low balance, successful campaign 

→ subscription) 

– GEPA (Grounded Example Prompting Augmentation) : 0.82 AUC, 84% accuracy 

* Uses LLM to generate additional synthetic examples, filters by quality (confidence > 0.7) 

* Augments training set from 500 → 1200 examples, improves coverage of edge cases 

– Final compiled program: 12-shot prompt with chain-of-thought, optimized for AUC 

• Production Deployment – Export compiled prompt as JSON, load in FastAPI service, cache predictions (1 hour TTL) 

– Monitoring: Track AUC on daily predictions vs. actuals, retrain weekly if AUC < 0.75 

– A/B test: 50% manual prompts, 50% DSPy, measure conversion lift (DSPy: +12% conversions) 

Case Study 2: Credit Risk Assessment (Low-Correlation Features) (Prompt_Engineering_Loan_Classification,_Low_Correlation. ipynb )

• Problem Statement – Classify loan default risk (low | medium | high) from applicant data with weak feature correlations 

– Features: Income, credit score, debt-to-income ratio, employment length, past delinquencies 

– Challenge: Low correlation makes pattern recognition difficult, requires reasoning chains 

• DSPy Architecture – Signature : LoanApplication -> RiskAssessment 

* Input: Applicant features as structured dict  

> Agentic AI in Asset Management Syllabus Page 9

* Output: risk_bucket: str, key_drivers: List[str], credit_memo: str, confidence: float 

– Module : Multi-step reasoning with dspy.ChainOfThought 

* Step 1: Assess each feature independently (income risk, credit score risk, etc.) 

* Step 2: Synthesize holistic risk considering feature interactions 

* Step 3: Generate credit memo with specific recommendations (e.g., "Require co-signer due to high DTI") 

– Training Data : 1000 loans with known outcomes, balanced across risk buckets (33% each) 

• Metric Design – Primary: ROC-AUC on ordinal risk buckets (low=0, medium=1, high=2), measures ranking quality 

– Secondary: Classification accuracy (exact bucket match) 

– Challenge: Model achieves good ordering (AUC 0.81) but poor probability calibration (accuracy 68%) 

– Solution: Optimize for AUC primarily, apply isotonic regression post-hoc for calibration if needed 

• Optimization with MIPROv2 – Baseline (zero-shot): 0.72 AUC, 61% accuracy 

– MIPROv2 (Meta In-context Prompt Optimization, 20 iterations): 

* Phase 1: Generate 50 candidate prompts with varied instructions ("reason step-by-step", "consider feature interactions", etc.) 

* Phase 2: Evaluate each on val set, select top-5 by AUC 

* Phase 3: Mutate top-5 (paraphrase, add constraints), re-evaluate, repeat 20 rounds 

– Result: 0.81 AUC, 68% accuracy, 8-shot prompt with explicit reasoning chain 

– Key insight: MIPROv2 discovers effective prompt structure ("List 3 supporting factors, 2 mitigating factors, then decide") not found manually 

• Production Governance – Explainability: Credit memo required for all high-risk classifications, audited by compliance 

– Bias testing: Monitor approval rates by protected class (race, gender), flag disparate impact >1.25x 

– Model drift: Weekly AUC checks, trigger recompile if <0.75, retrain on last 3 months of data 

Advanced Technique: Second-Order DSPy (Second_Order_DSPY.ipynb )

• Concept : Use DSPy to generate DSPy programs from natural language specifications 

• SignatureGenerator Module – Input: Natural language task description ("Analyze investment opportunities from earnings call transcripts") 

– Output: DSPy signature as Python code ( EarningsTranscript -> InvestmentAnalysis )

– Implementation: dspy.ChainOfThought with examples of (description, signature) pairs 

• ModuleGenerator – Input: Generated signature + task complexity ("needs multi-hop reasoning") 

– Output: Complete dspy.Module with appropriate submodules ( dspy.ReAct , dspy.Predict )

– Example: For complex task, generates module with retrieval step, reasoning step, synthesis step 

• Use Case: Rapid Prototyping – PM describes task: "Extract M&A deals from news, classify by deal type, estimate deal value" 

– SignatureGenerator creates: NewsArticle -> MergerExtraction (deal_type: str, companies: List[str], value_estimate float) 

– ModuleGenerator builds: 3-step module (classify article relevance, extract entities, estimate value from text) 

– Developer reviews generated code, tweaks constraints, compiles with optimizer 

– Time saved: 30 minutes vs. 3 hours manual DSPy programming 

• Importing Helpers from GitHub – Pattern: !wget https://raw.githubusercontent.com/stanfordnlp/dspy/main/examples/signature_generator.py 

– Enables rapid iteration: Import cutting-edge DSPy utilities without local installation 

– Example utilities: BootstrapFewShotWithRandomSearch , SignatureOptimizerV2 , EnsembleModule 

WHEN TO USE DSPY VS. MANUAL PROMPTING 

• Use DSPy when :

– Task will be repeated >100 times with evaluation data available 

– Prompt brittleness is costly (production system, model upgrades expected) 

– Optimization metric is clear and measurable (AUC, F1, BLEU) 

– Team has engineering resources to maintain pipelines 

• Use manual prompting when :

– One-off analysis or ad-hoc queries 

– No evaluation dataset or metric definition 

– Task is too creative/subjective for automated optimization 

– Time-to-first-result is critical (DSPy setup overhead 2-4 hours) 

PRODUCTION BENEFITS & ROI  

> Agentic AI in Asset Management Syllabus Page 10

• Repeatability: Same input → same output (given model/data), enables regression testing 

• Auditability: Compiled prompts are versioned artifacts, can diff changes, roll back if needed 

• Maintainability: Model upgrade = recompile against same dataset, no manual prompt rewriting 

• Performance: Typical 20-40% improvement in task metrics over manual prompts after optimization 

• Cost: Small upfront investment (2-4 hours setup), large ongoing savings (no manual tuning on model updates) 

HANDS-ON MATERIALS 

• Code: 3 notebooks ( 2500 lines total), sample datasets (bank, credit, news), pre-trained optimizers 

• Dependencies: dspy-ai , scikit-learn , pandas , pydantic , openai /anthropic 

• Resources: DSPy docs (dspy-docs.vercel.app), example library (github.com/stanfordnlp/dspy/examples)  

> Agentic AI in Asset Management Syllabus Page 11

# Session 5: Deployment, GUIs, and CLIs 

CORE CONCEPTS Production AI systems require scalable deployment infrastructure, comprehensive observability, and user-friendly interfaces. This session covers deploying agents as managed services on Google Cloud’s Vertex AI Agent Engine , implementing full observability stacks (tracing, logging, metrics), and comparing autonomous CLI coding agents for different use cases. The workflow: Prototype in notebook → deploy as API → wrap in UI → monitor in production. 

LEARNING OBJECTIVES 

• Deploy a Python-based ADK agent as a managed service on Vertex AI with session management, artifact persistence to GCS, and API versioning. 

• Implement comprehensive observability : Gantt-style trace visualization, structured logging (JSON with trace IDs), token/cost metering, and performance dashboards (latency p95, error rate). 

• Operate CLI coding agents (Claude Code, Gemini CLI, Codex) safely with directory scoping, minimal tool allow-lists, and approval gates for destructive operations. 

• Serve agent outputs (HTML reports, charts) via GCS public objects with lifecycle rules (auto-delete after 90 days) and signed URLs for temporary access. 

• Navigate the open-source ecosystem : Chat interfaces (LobeChat, Chainlit), dashboarding (Streamlit, Reflex), workflow orchestration (Prefect, Temporal), LLM gateways (LiteLLM, OpenRouter). 

TECHNICAL AGENDA & DEPLOYMENT PATTERNS 

Deploying to Vertex AI Agent Engine (CourseMaterial/deployment/Prompt_Chaining_Agent_w_Deployment.ipynb )

• Agent Packaging – Convert notebook workflow to standalone Python module: agent_app.py with main() entry point 

– Dependencies: requirements.txt with pinned versions ( google-generativeai==0.3.2 , vertexai==1.40.0 )

– Configuration: config.yaml with model settings (temperature, top_p), tool endpoints, GCS paths 

• Vertex AI Deployment – Create Agent Engine: aiplatform.Agent.create(display_name="financial-analysis-agent", tools=tool_registry) 

– Configure compute: 2 vCPU, 4GB RAM, auto-scaling 1-10 instances, cold start <5s 

– Deploy version: agent.deploy(version="v1.2.3", traffic_split={"v1.2.3": 100}) , blue-green deployment 

– Endpoint URL: https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/us-central1/agents 

• Session Management – Session creation: session = agent.create_session(user_id="user123", ttl=3600) 

– State persistence: Sessions stored in Firestore, automatic cleanup after TTL 

– Message API: session.send_message(text="Analyze TSLA Q3 earnings", attachments=[pdf_uri]) 

– Response streaming: Server-sent events for real-time output, for chunk in response: print(chunk) 

• GCS Artifact Management – Bucket setup: gs://PROJECT-agent-artifacts/ with IAM binding (agent SA has objectCreator role) 

– Save outputs: blob = bucket.blob(f"reports/{session_id}/report.html"); blob.upload_from_string(html, content_typ 

– Public access: blob.make_public() , generates public URL https://storage.googleapis.com/... 

– Lifecycle policy: Auto-delete objects >90 days, transition to Nearline after 30 days (cost optimization) 

– Signed URLs: blob.generate_signed_url(expiration=timedelta(hours=1)) for temporary access 

• API Versioning – Semantic versioning: MAJOR.MINOR.PATCH (e.g., v1.2.3) 

– Breaking changes: Increment MAJOR (v1 → v2), deprecate old version after 6 months 

– Traffic splitting: Canary deploy new version to 10%, monitor error rate, ramp to 100% if stable 

– Rollback: agent.update_traffic_split({"v1.2.2": 100, "v1.2.3": 0}) , instant rollback on critical bugs 

Observability Stack Implementation 

• Distributed Tracing – OpenTelemetry SDK: Instrument all LLM calls, tool invocations, external API requests 

– Trace structure: Root span (session), child spans (agent steps), grandchild spans (tool calls) 

– Attributes: user_id , model_name , input_tokens , output_tokens , latency_ms , cost_usd 

– Visualization: Gantt charts in Cloud Trace, identify bottlenecks (e.g., tool call taking 3s vs. 0.5s expected) 

– Example insight: "Parallel tool calls reduced latency from 8s to 2.5s, 70% improvement" 

• Structured Logging – Format: JSON with fields {timestamp, level, message, context, trace_id, span_id} 

– Log levels: DEBUG (dev only), INFO (user actions), WARNING (retries), ERROR (failures), CRITICAL (service down) 

– Contextual info: Log input prompts (truncated to 500 chars), output summaries, tool results, errors with stack traces 

– Aggregation: Send to Cloud Logging, index on trace_id + user_id, set up log-based metrics (error rate, p95 latency)  

> Agentic AI in Asset Management Syllabus Page 12

• Token & Cost Metering – Track per-call: Parse response metadata ( usage.prompt_tokens , usage.completion_tokens )

– Cost calculation: Gemini Flash $0.075/1M input tokens, $0.30/1M output; store in BigQuery 

– Aggregation: Daily cost by user, by agent, by model; alert if daily cost >2x rolling 7-day average 

– Budget controls: Hard limit $100/day per user, soft limit $50/day with warning, graceful degradation (switch to cheaper model) 

• Performance Dashboards – Metrics: Request rate (QPS), latency (p50/p95/p99), error rate, token usage, cost, cache hit rate 

– Visualization: Grafana with Prometheus data source, 7-day rolling window, hourly granularity 

– Alerts: PagerDuty on error rate >5%, p95 latency >10s, cost spike >3x baseline 

– SLOs: 99.5% availability, p95 latency <5s, error rate <1%, measured over 28-day windows 

CLI Coding Agents (CourseMaterial/aisystem/Gemini_Claude_Api_Empty.ipynb )

• Comparative Analysis – Claude Code : Best for project automation, robust refactoring, large file edits 

* Strengths: Strong code understanding, multi-file changes, test generation 

* Weaknesses: Aggressive (can delete files), requires –dangerously-skip-permissions for automation 

* Use case: "Migrate Flask app to FastAPI across 20 files" 

– Gemini CLI : Best for large repos, good routing with ADK integration 

* Strengths: Handles 100K+ line codebases, context-aware routing, tool-use 

* Weaknesses: Slower iteration, less aggressive refactoring 

* Use case: "Find all SQL injection vulnerabilities in Django app" 

– Codex CLI (GitHub Copilot) : Best for controlled integration, explicit allow-lists 

* Strengths: Tight IDE integration, fine-grained permissions, incremental suggestions 

* Weaknesses: Less autonomous, requires more human guidance 

* Use case: "Implement OAuth2 flow following company security guidelines" 

• Execution Model: Local Harness, Cloud Brain – Local harness: Python script that manages file system, runs commands, enforces safety 

– Cloud brain: LLM API (Claude, Gemini) that generates commands, edits files, reasons about errors 

– Communication: JSON-RPC or custom protocol, local harness filters/approves commands before execution 

– Sandboxing: Run in Docker container, limit network access, readonly mounts for sensitive dirs 

• Safety Practices – Directory scoping: –workspace=/path/to/project , refuse operations outside workspace 

– Tool allow-lists: Whitelist safe commands ( git , python , npm ), block rm -rf , sudo , curl | bash 

– Approval gates: Human confirmation required for: file deletion, >100 line changes, network requests, environment variables 

– Dry-run mode: –dry-run flag shows planned changes without execution, review before apply 

– Version control: Auto-commit after each agent iteration, easy rollback with git reset –hard HEAD 1 

• Practical Example: Financial PDF Extraction – Task: Download quarterly filings (TSLA, AMZN, AAPL), extract revenue/EPS, generate HTML charts 

– Command-line: claude-code –prompt "Download 10-Qs, extract financials, chart revenue trends" –workspace=./fili –yolo 

– Programmatic: subprocess.run(["claude-code", "–api", "–prompt", prompt, "–workspace", workspace]) 

– Output: HTML report with Plotly charts, saved to ./filings/report.html , auto-uploaded to GCS 

– Security: Sandboxed Docker container, no network after download, readonly mount for PDFs 

Open-Source Ecosystem Survey 

• Chat Interfaces – LobeChat : Self-hosted, multi-provider (OpenAI/Anthropic/Google), plugin system, 10K+ stars 

– Chainlit : Python framework for conversational AI UIs, streaming support, custom actions 

– Deployment: Docker Compose, Kubernetes, or serverless (Cloud Run), auth via OAuth2 

• Python Dashboarding – Streamlit : Simplest, pure Python, rapid prototyping, limited customization 

– Taipy : State-binding UI (React-like), good for complex workflows, steeper learning curve 

– Dash (Plotly) : Callback-driven, production-ready, strong enterprise adoption 

– Reflex : Full-stack Python (FastAPI backend + React frontend), compile to JS 

– Selection criteria: Streamlit for MVPs, Dash for production, Reflex for full control 

• Low-Code Platforms – Tooljet : Open-source Retool alternative, drag-and-drop, 50+ data sources 

– Windmill : Workflow automation with Python/TypeScript, self-hosted, 5K+ stars 

– Use case: Internal tools for ops team (user management, data exports, agent controls)  

> Agentic AI in Asset Management Syllabus Page 13

• Workflow Orchestration – Prefect : Python-native, modern UI, dynamic workflows, strong observability 

– Temporal : Durable execution, workflow-as-code, handles long-running tasks (days/weeks) 

– Mage : Notebook-style, data pipeline focus, good for ETL + ML 

– Selection: Prefect for most cases, Temporal for mission-critical workflows with strict reliability requirements 

• LLM Gateways & Routers – OpenRouter : Unified API for 100+ models, automatic fallback, usage analytics 

– LiteLLM : Open-source proxy, cost tracking, load balancing, caching 

– Use case: Single codebase supports GPT-4, Claude, Gemini; switch model via config without code changes 

– Cost optimization: Route cheap queries (summarization) to Flash, complex queries to Pro 

PRODUCTION CHECKLIST 

✓ Deploy agent to managed service with auto-scaling 

✓ Implement distributed tracing with OpenTelemetry 

✓ Set up structured logging with trace correlation 

✓ Monitor token usage and costs with alerts 

✓ Create performance dashboard with SLO tracking 

✓ Configure CLI agents with safety guardrails 

✓ Set up artifact storage with lifecycle policies 

✓ Implement API versioning and canary deployments 

✓ Build user-facing UI (Streamlit/Dash/Chainlit) 

✓ Document API, write runbooks, train ops team 

HANDS-ON MATERIALS 

• Code: 2 notebooks ( 1500 lines), deployment scripts, Docker configs, Grafana dashboards 

• Dependencies: vertexai , google-cloud-storage , opentelemetry-sdk , streamlit , subprocess 

• Resources: GCP deployment guide, CLI agent comparison matrix, ecosystem tool directory