# Understanding Claude Agents: Not Executable Code

**Critical Insight**: Claude agents are **declarative personas**, not executable Python classes.

---

## The Misconception

When you first hear "agent," you might think:

```python
class HuntAgent:
    def execute_mission(self, tasks):
        # This code runs when agent is called
        return self.primary_execution(tasks)
```

**This is WRONG**. Claude agents don't work this way.

---

## The Reality

Claude agents are **YAML/Markdown files** that declare:
- **Role**: What this agent does
- **Tools allowed**: Which tools it can call
- **Decision rules**: When to use this agent
- **Delegation**: Which other agents it can coordinate

### Example: Hunt Orchestrator Agent

```yaml
---
name: hunt-orchestrator
type: orchestrator
description: Mission orchestration with adaptive contingencies (Ethan Hunt style)
tools:
  - estimate_pages
  - scrape_docs
  - scrape_github
  - package_skill
delegates_to:
  - github-analyst
  - pdf-extractor
---

# Hunt Orchestrator

I coordinate complex scraping missions with built-in fallback strategies.

## Decision Logic

**IF** primary source fails:
- TRY source 2 (GitHub)
- IF that fails: TRY source 3 (PDF)
- IF all fail: Use cached data

**IF** rate limit hit:
- Wait + resume from checkpoint
- Switch to async mode

**IF** conflict detected:
- Use @referee-agent-csp to synthesize
```

### What Happens When Claude Uses This Agent

1. **User**: "Build React skill from docs + GitHub"
2. **Claude reads** `hunt-orchestrator.md`
3. **Claude thinks**: "This needs fallback logic, I should use @hunt-orchestrator"
4. **Claude calls tools**: `estimate_pages` → `scrape_docs` → (if fails) → `scrape_github`
5. **Claude synthesizes**: Creates response based on tool outputs

---

## The 3-Layer Architecture (Reality-Based)

### ❌ What DOESN'T Work

```
Agent.execute() → Runs Python code → Returns result
```

### ✅ What ACTUALLY Works

```
Layer 1: MCP Tools (Python code in YOUR environment)
   ↓
Layer 2: Skills (Markdown teaching Claude HOW to use tools)
   ↓
Layer 3: Agents (YAML/MD declaring WHEN to use skills)
   ↓
Claude's Reasoning (decides which agent + tools to use)
```

---

## Concrete Example: Hunt-Style Contingency

### Layer 1: MCP Tool (Executable Python)

```python
# skill_seeker_mcp/server.py

@server.tool()
async def execute_with_fallback(config_path: str) -> dict:
    """Execute scrape with automatic fallback chain"""
    
    fallback_chain = [
        ('unified_scraper', config_path),
        ('github_scraper', config_path),
        ('doc_scraper', config_path),
        ('cached_mode', config_path),
    ]
    
    for tool_name, config in fallback_chain:
        try:
            logger.info(f"🎯 Executing: {tool_name}")
            result = _execute_tool(tool_name, config)
            logger.info(f"✅ {tool_name} succeeded")
            return {'status': 'success', 'tool': tool_name, 'result': result}
        except Exception as e:
            logger.warning(f"⚠️ {tool_name} failed: {e}")
            continue
    
    return {'status': 'failed', 'error': 'All fallbacks exhausted'}
```

### Layer 2: Skill (Teaching Document)

```markdown
# How to Use Hunt Orchestrator

## When Claude Sees a Scraping Task

1. **Check**: Call `pre_flight_check` to assess risks
2. **Plan**: Review recommended mitigations
3. **Execute**: Use `execute_with_fallback` tool
4. **Monitor**: If it fails, tool automatically tries next in chain
5. **Synthesize**: Return results to user

## Tool Fallback Chain

Primary → Backup 1 → Backup 2 → Backup 3 → Graceful Degrade

- **Primary**: Unified (docs + GitHub + PDF)
- **Backup 1**: GitHub code analysis only
- **Backup 2**: HTML docs only
- **Backup 3**: Cached output from last run

## Example

User: "Build React skill from docs + GitHub"

→ Claude thinks: "This needs @hunt-orchestrator"
→ Calls: execute_with_fallback("configs/react.json")
→ Tool tries: unified_scraper
→ If fails: Tool tries github_scraper automatically
→ Returns: Working skill (degraded but functional)
```

### Layer 3: Agent (Declarative Persona)

```yaml
---
name: hunt-orchestrator
type: orchestrator
description: Ethan Hunt-style mission orchestration with contingencies
tools:
  - execute_with_fallback
  - pre_flight_check
  - package_skill
delegates_to: []
---

# Hunt Orchestrator Agent

**Role**: Your mission commander with contingency planning

## Capabilities
- Assess mission risks before execution
- Execute with automatic fallback chain
- Resume from checkpoints on failures
- Graceful degradation (degraded output > no output)

## When to Use
- Multi-source scraping (docs + GitHub + PDF)
- Large documentation (> 1000 pages)
- Unreliable sources (rate limits, timeouts)
- Production-critical skills (can't afford failures)
```

---

## How Claude Orchestrates (The Magic)

When you say: **"@hunt-orchestrator build React skill"**

Claude's internal reasoning:
```
1. Read hunt-orchestrator.md → "This agent handles fallbacks"
2. Read hunt-orchestrator-skill.md → "Tool: execute_with_fallback"
3. Check MCP tools → "execute_with_fallback is available"
4. Call tool: execute_with_fallback("configs/react.json")
5. Tool returns: {"status": "success", "tool": "unified_scraper"}
6. Synthesize response: "✅ Built React skill using unified scraper"
```

If unified_scraper failed:
```
4. Call tool: execute_with_fallback("configs/react.json")
5. Tool returns: {"status": "success", "tool": "github_scraper"}
6. Synthesize: "⚠️ Docs scraping failed, used GitHub-only mode. Skill is limited to code analysis."
```

---

## Why This Matters for Your Finance App

You're building tools like:
- `ingest_sec_filing` (Python function)
- `text_to_sql_query` (Python function)
- `hybrid_rag_search` (Python function)

**Wrong approach**:
```python
class FinanceAgent:
    def ingest(self):  # ❌ Claude can't execute this
        pass
```

**Right approach**:
```python
# Layer 1: MCP tool (skill_seeker_mcp/server.py)
@server.tool()
async def ingest_sec_filing(filing_url: str) -> dict:
    # This runs in YOUR environment when Claude calls it
    pass
```

```yaml
# Layer 3: Agent (.claude/agents/financial-data-engineer.md)
---
name: financial-data-engineer
tools:
  - ingest_sec_filing
  - monitor_pipeline
---

I ingest SEC filings and monitor the data pipeline.
```

```markdown
# Layer 2: Skill (.claude/skills/finance-ingestion/SKILL.md)

## How to Ingest SEC Filings

**Tool**: `ingest_sec_filing`

**When to use**: User wants to add a 10-K/Q to the database

**Example**:
User: "Ingest TSLA 10-K from Q3 2024"
→ Call: ingest_sec_filing("https://sec.gov/...")
→ Returns: {"chunks_created": 342, "tables_extracted": 15}
```

---

## Key Takeaways

1. **Agents are NOT code** - They're declarations that Claude reads
2. **Tools ARE code** - Python functions in your environment (via MCP)
3. **Skills teach usage** - Markdown docs explaining when/how to use tools
4. **Claude orchestrates** - Reads agents/skills, calls tools, synthesizes responses

5. **Fallback logic goes in tools**, not agents:
   ```python
   # ✅ RIGHT: Fallback in tool
   async def execute_with_fallback():
       try: method1()
       except: try: method2()
   
   # ❌ WRONG: Fallback in agent
   # Agents can't execute logic
   ```

---

**Next**: [03-three-layer-framework.md](03-three-layer-framework.md) - Deep dive into the 3-layer architecture
