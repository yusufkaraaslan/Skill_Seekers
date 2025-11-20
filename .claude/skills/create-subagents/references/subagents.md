<file_format>
Subagent file structure:

```markdown
---
name: your-subagent-name
description: Description of when this subagent should be invoked
tools: tool1, tool2, tool3 # Optional - inherits all tools if omitted
model: sonnet # Optional - specify model alias or 'inherit'
---

<role>
Your subagent's system prompt using pure XML structure. This defines the subagent's role, capabilities, and approach.
</role>

<constraints>
Hard rules using NEVER/MUST/ALWAYS for critical boundaries.
</constraints>

<workflow>
Step-by-step process for consistency.
</workflow>
```

**Critical**: Use pure XML structure in the body. Remove ALL markdown headings (##, ###). Keep markdown formatting within content (bold, lists, code blocks).

<configuration_fields>
| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier using lowercase letters and hyphens |
| `description` | Yes | Natural language description of purpose. Include when Claude should invoke this. |
| `tools` | No | Comma-separated list. If omitted, inherits all tools from main thread |
| `model` | No | `sonnet`, `opus`, `haiku`, or `inherit`. If omitted, uses default subagent model |
</configuration_fields>
</file_format>

<storage_locations>
| Type | Location | Scope | Priority |
|------|----------|-------|----------|
| **Project** | `.claude/agents/` | Current project only | Highest |
| **User** | `~/.claude/agents/` | All projects | Lower |
| **CLI** | `--agents` flag | Current session | Medium |
| **Plugin** | Plugin's `agents/` dir | All projects | Lowest |

When subagent names conflict, higher priority takes precedence.
</storage_locations>

<execution_model>
<black_box_model>
Subagents execute in isolated contexts without user interaction.

**Key characteristics:**
- Subagent receives input parameters from main chat
- Subagent runs autonomously using available tools
- Subagent returns final output/report to main chat
- User only sees final result, not intermediate steps

**This means:**
- ✅ Subagents can use Read, Write, Edit, Bash, Grep, Glob, WebSearch, WebFetch
- ✅ Subagents can access MCP servers (non-interactive tools)
- ✅ Subagents can make decisions based on their prompt and available data
- ❌ **Subagents CANNOT use AskUserQuestion**
- ❌ **Subagents CANNOT present options and wait for user selection**
- ❌ **Subagents CANNOT request confirmations or clarifications from user**
- ❌ **User does not see subagent's tool calls or intermediate reasoning**
</black_box_model>

<workflow_implications>
**When designing subagent workflows:**

Keep user interaction in main chat:
```markdown
# ❌ WRONG - Subagent cannot do this
---
name: requirement-gatherer
description: Gathers requirements from user
tools: AskUserQuestion  # This won't work!
---

You ask the user questions to gather requirements...
```

```markdown
# ✅ CORRECT - Main chat handles interaction
Main chat: Uses AskUserQuestion to gather requirements
  ↓
Launch subagent: Uses requirements to research/build (no interaction)
  ↓
Main chat: Present subagent results to user
```
</workflow_implications>
</execution_model>

<tool_configuration>
<inherit_all_tools>
Omit the `tools` field to inherit all tools from main thread:

```yaml
---
name: code-reviewer
description: Reviews code for quality and security
---
```

Subagent has access to all tools, including MCP tools.
</inherit_all_tools>

<specific_tools>
Specify tools as comma-separated list for granular control:

```yaml
---
name: read-only-analyzer
description: Analyzes code without making changes
tools: Read, Grep, Glob
---
```

Use `/agents` command to see full list of available tools.
</specific_tools>
</tool_configuration>

<model_selection>
<model_capabilities>
**Sonnet 4.5** (`sonnet`):
- "Best model in the world for agents" (Anthropic)
- Exceptional at agentic tasks: 64% problem-solving on coding benchmarks
- SWE-bench Verified: 49.0%
- **Use for**: Planning, complex reasoning, validation, critical decisions

**Haiku 4.5** (`haiku`):
- "Near-frontier performance" - 90% of Sonnet 4.5's capabilities
- SWE-bench Verified: 73.3% (one of world's best coding models)
- Fastest and most cost-efficient
- **Use for**: Task execution, simple transformations, high-volume processing

**Opus** (`opus`):
- Highest performance on evaluation benchmarks
- Most capable but slowest and most expensive
- **Use for**: Highest-stakes decisions, most complex reasoning

**Inherit** (`inherit`):
- Uses same model as main conversation
- **Use for**: Ensuring consistent capabilities throughout session
</model_capabilities>

<orchestration_strategy>
**Sonnet + Haiku orchestration pattern** (optimal cost/performance):

```markdown
1. Sonnet 4.5 (Coordinator):
   - Creates plan
   - Breaks task into subtasks
   - Identifies parallelizable work

2. Multiple Haiku 4.5 instances (Workers):
   - Execute subtasks in parallel
   - Fast and cost-efficient
   - 90% of Sonnet's capability for execution

3. Sonnet 4.5 (Validator):
   - Integrates results
   - Validates output quality
   - Ensures coherence
```

**Benefit**: Use expensive Sonnet only for planning and validation, cheap Haiku for execution.
</orchestration_strategy>

<decision_framework>
**When to use each model**:

| Task Type | Recommended Model | Rationale |
|-----------|------------------|-----------|
| Simple validation | Haiku | Fast, cheap, sufficient capability |
| Code execution | Haiku | 73.3% SWE-bench, very fast |
| Complex analysis | Sonnet | Superior reasoning, worth the cost |
| Multi-step planning | Sonnet | Best for breaking down complexity |
| Quality validation | Sonnet | Critical checkpoint, needs intelligence |
| Batch processing | Haiku | Cost efficiency for high volume |
| Critical security | Sonnet | High stakes require best model |
| Output synthesis | Sonnet | Ensuring coherence across inputs |
</decision_framework>
</model_selection>

<invocation>
<automatic>
Claude automatically selects subagents based on:
- Task description in user's request
- `description` field in subagent configuration
- Current context
</automatic>

<explicit>
Users can explicitly request a subagent:

```
> Use the code-reviewer subagent to check my recent changes
> Have the test-runner subagent fix the failing tests
```
</explicit>
</invocation>

<management>
<using_agents_command>
**Recommended**: Use `/agents` command for interactive management:
- View all available subagents (built-in, user, project, plugin)
- Create new subagents with guided setup
- Edit existing subagents and their tool access
- Delete custom subagents
- See which subagents take priority when names conflict
</using_agents_command>

<direct_file_management>
**Alternative**: Edit subagent files directly:
- Project: `.claude/agents/subagent-name.md`
- User: `~/.claude/agents/subagent-name.md`

Follow the file format specified above (YAML frontmatter + system prompt).
</direct_file_management>

<cli_based_configuration>
**Temporary**: Define subagents via CLI for session-specific use:

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer. Use proactively after code changes.",
    "prompt": "You are a senior code reviewer. Focus on quality, security, and best practices.",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet"
  }
}'
```

Useful for testing configurations before saving them.
</cli_based_configuration>
</management>

<example_subagents>
<test_writer>
```markdown
---
name: test-writer
description: Creates comprehensive test suites. Use when new code needs tests or test coverage is insufficient.
tools: Read, Write, Grep, Glob, Bash
model: sonnet
---

<role>
You are a test automation specialist creating thorough, maintainable test suites.
</role>

<workflow>
1. Analyze the code to understand functionality
2. Identify test cases (happy path, edge cases, error conditions)
3. Write tests using the project's testing framework
4. Run tests to verify they pass
</workflow>

<test_quality_criteria>
- Test one behavior per test
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Include edge cases and error conditions
- Avoid test interdependencies
</test_quality_criteria>
```
</test_writer>

<debugger>
```markdown
---
name: debugger
description: Investigates and fixes bugs. Use when errors occur or behavior is unexpected.
tools: Read, Edit, Bash, Grep, Glob
model: sonnet
---

<role>
You are a debugging specialist skilled at root cause analysis and systematic problem-solving.
</role>

<workflow>
1. **Reproduce**: Understand and reproduce the issue
2. **Isolate**: Identify the failing component
3. **Analyze**: Examine code, logs, and stack traces
4. **Hypothesize**: Form theories about the cause
5. **Test**: Verify hypotheses systematically
6. **Fix**: Implement and verify the solution
</workflow>

<debugging_techniques>
- Add logging/print statements to trace execution
- Use binary search to isolate the problem
- Check assumptions (inputs, state, environment)
- Review recent changes that might have introduced the bug
- Verify fix doesn't break other functionality
</debugging_techniques>
```
</debugger>
</example_subagents>

<tool_security>
<core_principle>
**"Permission sprawl is the fastest path to unsafe autonomy."** - Anthropic

Treat tool access like production IAM: start from deny-all, allowlist only what's needed.
</core_principle>

<why_it_matters>
**Security risks of over-permissioning**:
- Agent could modify wrong code (production instead of tests)
- Agent could run dangerous commands (rm -rf, data deletion)
- Agent could expose protected information
- Agent could skip critical steps (linting, testing, validation)

**Example vulnerability**:
```markdown
❌ Bad: Agent drafting sales email has full access to all tools
Risk: Could access revenue dashboard data, customer financial info

✅ Good: Agent drafting sales email has Read access to Salesforce only
Scope: Can draft email, cannot access sensitive financial data
```
</why_it_matters>

<permission_patterns>
**Tool access patterns by trust level**:

**Trusted data processing**:
- Full tool access appropriate
- Working with user's own code
- Example: refactoring user's codebase

**Untrusted data processing**:
- Restricted tool access essential
- Processing external inputs
- Example: analyzing third-party API responses
- Limit: Read-only tools, no execution
</permission_patterns>

<audit_checklist>
**Tool access audit**:
- [ ] Does this subagent need Write/Edit, or is Read sufficient?
- [ ] Should it execute code (Bash), or just analyze?
- [ ] Are all granted tools necessary for the task?
- [ ] What's the worst-case misuse scenario?
- [ ] Can we restrict further without blocking legitimate use?

**Default**: Grant minimum necessary. Add tools only when lack of access blocks task.
</audit_checklist>
</tool_security>

<prompt_caching>
<benefits>
Prompt caching for frequently-invoked subagents:
- **90% cost reduction** on cached tokens
- **85% latency reduction** for cache hits
- Cached content: ~10% cost of uncached tokens
- Cache TTL: 5 minutes (default) or 1 hour (extended)
</benefits>

<cache_structure>
**Structure prompts for caching**:

```markdown
---
name: security-reviewer
description: ...
tools: ...
model: sonnet
---

[CACHEABLE SECTION - Stable content]
<role>
You are a senior security engineer...
</role>

<focus_areas>
- SQL injection
- XSS attacks
...
</focus_areas>

<workflow>
1. Read modified files
2. Identify risks
...
</workflow>

<severity_ratings>
...
</severity_ratings>

--- [CACHE BREAKPOINT] ---

[VARIABLE SECTION - Task-specific content]
Current task: {dynamic context}
Recent changes: {varies per invocation}
```

**Principle**: Stable instructions at beginning (cached), variable context at end (fresh).
</cache_structure>

<when_to_use>
**Best candidates for caching**:
- Frequently-invoked subagents (multiple times per session)
- Large, stable prompts (extensive guidelines, examples)
- Consistent tool definitions across invocations
- Long-running sessions with repeated subagent use

**Not beneficial**:
- Rarely-used subagents (once per session)
- Prompts that change frequently
- Very short prompts (caching overhead > benefit)
</when_to_use>

<cache_management>
**Cache lifecycle**:
- First invocation: Writes to cache (25% cost premium)
- Subsequent invocations: 90% cheaper on cached portion
- Cache refreshes on each use (extends TTL)
- Expires after 5 minutes of non-use (or 1 hour for extended TTL)

**Invalidation triggers**:
- Subagent prompt modified
- Tool definitions changed
- Cache TTL expires
</cache_management>
</prompt_caching>

<best_practices>
<be_specific>
Create task-specific subagents, not generic helpers.

❌ Bad: "You are a helpful assistant"
✅ Good: "You are a React performance optimizer specializing in hooks and memoization"
</be_specific>

<clear_triggers>
Make the `description` clear about when to invoke:

❌ Bad: "Helps with code"
✅ Good: "Reviews code for security vulnerabilities. Use proactively after any code changes involving authentication, data access, or user input."
</clear_triggers>

<focused_tools>
Grant only the tools needed for the task (least privilege):

- Read-only analysis: `Read, Grep, Glob`
- Code modification: `Read, Edit, Bash, Grep`
- Test running: `Read, Write, Bash`

**Security note**: Over-permissioning is primary risk vector. Start minimal, add only when necessary.
</focused_tools>

<structured_prompts>
Use XML tags to structure the system prompt for clarity:

```markdown
<role>
You are a senior security engineer specializing in web application security.
</role>

<focus_areas>
- SQL injection
- XSS attacks
- CSRF vulnerabilities
- Authentication/authorization flaws
</focus_areas>

<workflow>
1. Analyze code changes
2. Identify security risks
3. Provide specific remediation
4. Rate severity
</workflow>
```
</structured_prompts>
</best_practices>
