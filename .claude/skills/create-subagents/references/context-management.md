# Context Management for Subagents

<core_problem>


"Most agent failures are not model failures, they are context failures."

<stateless_nature>
LLMs are stateless by default. Each invocation starts fresh with no memory of previous interactions.

**For subagents, this means**:
- Long-running tasks lose context between tool calls
- Repeated information wastes tokens
- Important decisions from earlier in workflow forgotten
- Context window fills with redundant information
</stateless_nature>

<context_window_limits>
Full conversation history leads to:
- Degraded performance (important info buried in noise)
- High costs (paying for redundant tokens)
- Context limits exceeded (workflow fails)

**Critical threshold**: When context approaches limit, quality degrades before hard failure.
</context_window_limits>
</core_problem>

<memory_architecture>


<short_term_memory>
**Short-term memory (STM)**: Last 5-9 interactions.

**Implementation**: Preserved in context window.

**Use for**:
- Current task state
- Recent tool call results
- Immediate decisions
- Active conversation flow

**Limitation**: Limited capacity, volatile (lost when context cleared).
</short_term_memory>

<long_term_memory>
**Long-term memory (LTM)**: Persistent storage across sessions.

**Implementation**: External storage (files, databases, vector stores).

**Use for**:
- Historical patterns
- Accumulated knowledge
- User preferences
- Past task outcomes

**Access pattern**: Retrieve relevant memories into working memory when needed.
</long_term_memory>

<working_memory>
**Working memory**: Current context + retrieved memories.

**Composition**:
- Core task information (always present)
- Recent interaction history (STM)
- Retrieved relevant memories (from LTM)
- Current tool outputs

**Management**: This is what fits in context window. Optimize aggressively.
</working_memory>

<core_memory>
**Core memory**: Actively used information in current interaction.

**Examples**:
- Current task goal and constraints
- Key facts about the codebase being worked on
- Critical requirements from user
- Active workflow state

**Principle**: Keep core memory minimal and highly relevant. Everything else is retrievable.
</core_memory>

<archival_memory>
**Archival memory**: Persistent storage for less critical data.

**Examples**:
- Complete conversation transcripts
- Full tool output logs
- Historical metrics
- Deprecated approaches that were tried

**Access**: Rarely needed, searchable when required, doesn't consume context window.
</archival_memory>
</memory_architecture>

<context_strategies>


<summarization>
**Pattern**: Move information from context to searchable database, keep summary in memory.

<when_to_summarize>
Trigger summarization when:
- Context reaches 75% of limit
- Task transitions to new phase
- Information is important but no longer actively needed
- Repeated information appears multiple times
</when_to_summarize>

<summary_quality>
**Quality guidelines**:

1. **Highlight important events**
```markdown
Bad: "Reviewed code, found issues, provided fixes"
Good: "Identified critical SQL injection in auth.ts:127, provided parameterized query fix. High-priority: requires immediate attention before deployment."
```

2. **Include timing for sequential reasoning**
```markdown
"First attempt: Direct fix failed due to type mismatch.
Second attempt: Added type conversion, introduced runtime error.
Final approach: Refactored to use type-safe wrapper (successful)."
```

3. **Structure into categories vs long paragraphs**
```markdown
Issues found:
- Security: SQL injection (Critical), XSS (High)
- Performance: N+1 query (Medium)
- Code quality: Duplicate logic (Low)

Actions taken:
- Fixed SQL injection with prepared statements
- Added input sanitization for XSS
- Deferred performance optimization (noted in TODOs)
```

**Benefit**: Organized grouping improves relationship understanding.
</summary_quality>

<example_workflow>
```markdown
<context_management>
When conversation history exceeds 15 turns:
1. Identify information that is:
   - Important (must preserve)
   - Complete (no longer actively changing)
   - Historical (not needed for next immediate step)
2. Create structured summary with categories
3. Store full details in file (archival memory)
4. Replace verbose history with concise summary
5. Continue with reduced context load
</context_management>
```
</example_workflow>
</summarization>

<sliding_window>
**Pattern**: Recent interactions in context, older interactions as vectors for retrieval.

<implementation>
```markdown
<sliding_window_strategy>
Maintain in context:
- Last 5 tool calls and results (short-term memory)
- Current task state and goals (core memory)
- Key facts from user requirements (core memory)

Move to vector storage:
- Tool calls older than 5 steps
- Completed subtask results
- Historical debugging attempts
- Exploration that didn't lead to solution

Retrieval trigger:
- When current issue similar to past issue
- When user references earlier discussion
- When pattern matching suggests relevant history
</sliding_window_strategy>
```

**Benefit**: Bounded context growth, relevant history still accessible.
</implementation>
</sliding_window>

<semantic_context_switching>
**Pattern**: Detect context changes, respond appropriately.

<example>
```markdown
<context_switch_detection>
Monitor for topic changes:
- User switches from "fix bug" to "add feature"
- Subagent transitions from "analysis" to "implementation"
- Task scope changes mid-execution

On context switch:
1. Summarize current context state
2. Save state to working memory/file
3. Load relevant context for new topic
4. Acknowledge switch: "Switching from bug analysis to feature implementation. Bug analysis results saved for later reference."
</context_switch_detection>
```

**Prevents**: Mixing contexts, applying wrong constraints, forgetting important info when switching tasks.
</example>
</semantic_context_switching>

<scratchpads>
**Pattern**: Record intermediate results outside LLM context.

<use_cases>
**When to use scratchpads**:
- Complex calculations with many steps
- Exploration of multiple approaches
- Detailed analysis that may not all be relevant
- Debugging traces
- Intermediate data transformations

**Implementation**:
```markdown
<scratchpad_workflow>
For complex debugging:
1. Create scratchpad file: `.claude/scratch/debug-session-{timestamp}.md`
2. Log each hypothesis and test result in scratchpad
3. Keep only current hypothesis and key findings in context
4. Reference scratchpad for full debugging history
5. Summarize successful approach in final output
</scratchpad_workflow>
```

**Benefit**: Context contains insights, scratchpad contains exploration. User gets clean summary, full details available if needed.
</use_cases>
</scratchpads>

<smart_memory_management>
**Pattern**: Auto-add key data, retrieve on demand.

<smart_write>
```markdown
<auto_capture>
Automatically save to memory:
- User-stated preferences: "I prefer TypeScript over JavaScript"
- Project conventions: "This codebase uses Jest for testing"
- Critical decisions: "Decided to use OAuth2 for authentication"
- Frequent patterns: "API endpoints follow REST naming: /api/v1/{resource}"

Store in structured format for easy retrieval.
</auto_capture>
```
</smart_write>

<smart_read>
```markdown
<auto_retrieval>
Automatically retrieve from memory when:
- User asks about past decision: "Why did we choose OAuth2?"
- Similar task encountered: "Last time we added auth, we used..."
- Pattern matching: "This looks like the payment flow issue from last week"

Inject relevant memories into working context.
</auto_retrieval>
```
</smart_read>
</smart_memory_management>

<compaction>
**Pattern**: Summarize near-limit conversations, reinitiate with summary.

<workflow>
```markdown
<compaction_workflow>
When context reaches 90% capacity:
1. Identify essential information:
   - Current task and status
   - Key decisions made
   - Critical constraints
   - Important discoveries
2. Generate concise summary (max 20% of context size)
3. Save full context to archival storage
4. Create new conversation initialized with summary
5. Continue task in fresh context

Summary format:
**Task**: [Current objective]
**Status**: [What's been completed, what remains]
**Key findings**: [Important discoveries]
**Decisions**: [Critical choices made]
**Next steps**: [Immediate actions]
</compaction_workflow>
```

**When to use**: Long-running tasks, exploratory analysis, iterative debugging.
</workflow>
</compaction>
</context_strategies>

<framework_support>


<langchain>
**LangChain**: Provides automatic memory management.

**Features**:
- Conversation memory buffers
- Summary memory
- Vector store memory
- Entity extraction

**Use case**: Building subagents that need sophisticated memory without manual implementation.
</langchain>

<llamaindex>
**LlamaIndex**: Indexing for longer conversations.

**Features**:
- Semantic search over conversation history
- Automatic chunking and indexing
- Retrieval augmentation

**Use case**: Subagents working with large codebases, documentation, or extensive conversation history.
</llamaindex>

<file_based>
**File-based memory**: Simple, explicit, debuggable.

```markdown
<memory_structure>
.claude/memory/
  core-facts.md          # Essential project information
  decisions.md           # Key decisions and rationale
  patterns.md            # Discovered patterns and conventions
  {subagent}-state.json  # Subagent-specific state
</memory_structure>

<usage>
Subagent reads relevant files at start, updates during execution, summarizes at end.
</usage>
```

**Benefit**: Transparent, version-controllable, human-readable.
</file_based>
</framework_support>

<subagent_patterns>


<stateful_subagent>
**For long-running or frequently-invoked subagents**:

```markdown
---
name: code-architect
description: Maintains understanding of system architecture across multiple invocations
tools: Read, Write, Grep, Glob
model: sonnet
---

<role>
You are a system architect maintaining coherent design across project evolution.
</role>

<memory_management>
On each invocation:
1. Read `.claude/memory/architecture-state.md` for current system state
2. Perform assigned task with full context
3. Update architecture-state.md with new components, decisions, patterns
4. Maintain concise state (max 500 lines), summarize older decisions

State file structure:
- Current architecture (always up-to-date)
- Recent changes (last 10 modifications)
- Key design decisions (why choices were made)
- Active concerns (issues to address)
</memory_management>
```
</stateful_subagent>

<stateless_subagent>
**For simple, focused subagents**:

```markdown
---
name: syntax-checker
description: Validates code syntax without maintaining state
tools: Read, Bash
model: haiku
---

<role>
You are a syntax validator. Check code for syntax errors.
</role>

<workflow>
1. Read specified files
2. Run syntax checker (language-specific linter)
3. Report errors with line numbers
4. No memory needed - each invocation is independent
</workflow>
```

**When to use stateless**: Single-purpose validators, formatters, simple transformations.
</stateless_subagent>

<context_inheritance>
**Inheriting context from main chat**:

Subagents automatically have access to:
- User's original request
- Any context provided in invocation

```markdown
Main chat: "Review the authentication changes for security issues.
           Context: We recently switched from JWT to session-based auth."

Subagent receives:
- Task: Review authentication changes
- Context: Recent switch from JWT to session-based auth
- This context informs review focus without explicit memory management
```
</context_inheritance>
</subagent_patterns>

<anti_patterns>


<anti_pattern name="context_dumping">
❌ Including everything in context "just in case"

**Problem**: Buries important information in noise, wastes tokens, degrades performance.

**Fix**: Include only what's relevant for current task. Everything else is retrievable.
</anti_pattern>

<anti_pattern name="no_summarization">
❌ Letting context grow unbounded until limit hit

**Problem**: Sudden context overflow mid-task, quality degradation before failure.

**Fix**: Proactive summarization at 75% capacity, continuous compaction.
</anti_pattern>

<anti_pattern name="lossy_summarization">
❌ Summaries that discard critical information

**Example**:
```markdown
Bad summary: "Tried several approaches, eventually fixed bug"
Lost information: What approaches failed, why, what the successful fix was
```

**Fix**: Summaries preserve essential facts, decisions, and rationale. Details go to archival storage.
</anti_pattern>

<anti_pattern name="no_memory_structure">
❌ Unstructured memory (long paragraphs, no organization)

**Problem**: Hard to retrieve relevant information, poor for LLM reasoning.

**Fix**: Structured memory with categories, bullet points, clear sections.
</anti_pattern>

<anti_pattern name="context_failure_ignorance">
❌ Assuming all failures are model limitations

**Reality**: "Most agent failures are context failures, not model failures."

Check context quality before blaming model:
- Is relevant information present?
- Is it organized clearly?
- Is important info buried in noise?
- Has context been properly maintained?
</anti_pattern>
</anti_patterns>

<best_practices>


<principle name="core_memory_minimal">
Keep core memory minimal and highly relevant.

**Rule of thumb**: If information isn't needed for next 3 steps, it doesn't belong in core memory.
</principle>

<principle name="summaries_structured">
Summaries should be structured, categorized, and scannable.

**Template**:
```markdown

**Status**: [Progress]
**Completed**:
- [Key accomplishment 1]
- [Key accomplishment 2]

**Active**:
- [Current work]

**Decisions**:
- [Important choice 1]: [Rationale]
- [Important choice 2]: [Rationale]

**Next**: [Immediate next steps]
```
</principle>

<principle name="timing_matters">
Include timing for sequential reasoning.

"First tried X (failed), then tried Y (worked)" is more useful than "Used approach Y".
</principle>

<principle name="retrieval_over_retention">
Better to retrieve information on-demand than keep it in context always.

**Exception**: Frequently-used core facts (task goal, critical constraints).
</principle>

<principle name="external_storage">
Use filesystem for:
- Full logs and traces
- Detailed exploration results
- Historical data
- Intermediate work products

Use context for:
- Current task state
- Key decisions
- Active workflow
- Immediate next steps
</principle>
</best_practices>

<prompt_caching_interaction>


Prompt caching (see [subagents.md](subagents.md#prompt_caching)) works best with stable context.

<cache_friendly_context>
**Structure context for caching**:

```markdown
[CACHEABLE: Stable subagent instructions]
<role>...</role>
<focus_areas>...</focus_areas>
<workflow>...</workflow>
---
[CACHE BREAKPOINT]
---
[VARIABLE: Task-specific context]
Current task: ...
Recent context: ...
```

**Benefit**: Stable instructions cached, task-specific context fresh. 90% cost reduction on cached portion.
</cache_friendly_context>

<cache_invalidation>
**When context changes invalidate cache**:
- Subagent prompt updated
- Core memory structure changed
- Context reorganization

**Mitigation**: Keep stable content (role, workflow, constraints) separate from variable content (current task, recent history).
</cache_invalidation>
</prompt_caching_interaction>
