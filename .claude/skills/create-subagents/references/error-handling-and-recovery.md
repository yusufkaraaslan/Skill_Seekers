# Error Handling and Recovery for Subagents

<common_failure_modes>


Industry research identifies these failure patterns:

<specification_problems>
**32% of failures**: Subagents don't know what to do.

**Causes**:
- Vague or incomplete role definition
- Missing workflow steps
- Unclear success criteria
- Ambiguous constraints

**Symptoms**: Subagent asks clarifying questions (can't if it's a subagent), makes incorrect assumptions, produces partial outputs, or fails to complete task.

**Prevention**: Explicit `<role>`, `<workflow>`, `<focus_areas>`, and `<output_format>` sections in prompt.
</specification_problems>

<inter_agent_misalignment>
**28% of failures**: Coordination breakdowns in multi-agent workflows.

**Causes**:
- Subagents have conflicting objectives
- Handoff points unclear
- No shared context or state
- Assumptions about other agents' outputs

**Symptoms**: Duplicate work, contradictory outputs, infinite loops, tasks falling through cracks.

**Prevention**: Clear orchestration patterns (see [orchestration-patterns.md](orchestration-patterns.md)), explicit handoff protocols.
</inter_agent_misalignment>

<verification_gaps>
**24% of failures**: Nobody checks quality.

**Causes**:
- No validation step in workflow
- Missing output format specification
- No error detection logic
- Blind trust in subagent outputs

**Symptoms**: Incorrect results silently propagated, hallucinations undetected, format errors break downstream processes.

**Prevention**: Include verification steps in subagent workflows, validate outputs before use, implement evaluator agents.
</verification_gaps>

<error_cascading>
**Critical pattern**: Failures in one subagent propagate to others.

**Causes**:
- No error handling in downstream agents
- Assumptions that upstream outputs are valid
- No circuit breakers or fallbacks

**Symptoms**: Single failure causes entire workflow to fail.

**Prevention**: Defensive programming in subagent prompts, graceful degradation strategies, validation at boundaries.
</error_cascading>

<non_determinism>
**Inherent challenge**: Same prompt can produce different outputs.

**Causes**:
- LLM sampling and temperature settings
- API latency variations
- Context window ordering effects

**Symptoms**: Inconsistent behavior across invocations, tests pass sometimes and fail other times.

**Mitigation**: Lower temperature for consistency-critical tasks, comprehensive testing to identify variation patterns, robust validation.
</non_determinism>
</common_failure_modes>

<recovery_strategies>


<graceful_degradation>
**Pattern**: Workflow produces useful result even when ideal path fails.

<example>
```markdown
<workflow>
1. Attempt to fetch latest API documentation from web
2. If fetch fails, use cached documentation (flag as potentially outdated)
3. If no cache available, use local stub documentation (flag as incomplete)
4. Generate code with best available information
5. Add TODO comments indicating what should be verified
</workflow>

<fallback_hierarchy>
- Primary: Live API docs (most accurate)
- Secondary: Cached docs (may be stale, flag date)
- Tertiary: Stub docs (minimal, flag as incomplete)
- Always: Add verification TODOs to generated code
</fallback_hierarchy>
```

**Key principle**: Partial success better than total failure. Always produce something useful.
</example>
</graceful_degradation>

<autonomous_retry>
**Pattern**: Subagent retries failed operations with exponential backoff.

<example>
```markdown
<error_handling>
When a tool call fails:
1. Attempt operation
2. If fails, wait 1 second and retry
3. If fails again, wait 2 seconds and retry
4. If fails third time, proceed with fallback approach
5. Document the failure in output

Maximum 3 retry attempts before falling back.
</error_handling>
```

**Use case**: Transient failures (network issues, temporary file locks, rate limits).

**Anti-pattern**: Infinite retry loops without backoff or max attempts.
</example>
</autonomous_retry>

<circuit_breakers>
**Pattern**: Prevent cascading failures by stopping calls to failing components.

<conceptual_example>
```markdown
<circuit_breaker_logic>
If API endpoint has failed 5 consecutive times:
- Stop calling the endpoint (circuit "open")
- Use fallback data source
- After 5 minutes, attempt one call (circuit "half-open")
- If succeeds, resume normal calls (circuit "closed")
- If fails, keep circuit open for another 5 minutes
</circuit_breaker_logic>
```

**Application to subagents**: Include in prompt when subagent calls external APIs or services.

**Benefit**: Prevents wasting time/tokens on operations known to be failing.
</conceptual_example>
</circuit_breakers>

<timeouts>
**Pattern**: Agents going silent shouldn't block workflow indefinitely.

<implementation>
```markdown
<timeout_handling>
For long-running operations:
1. Set reasonable timeout (e.g., 2 minutes for analysis)
2. If operation exceeds timeout:
   - Abort operation
   - Provide partial results if available
   - Clearly flag as incomplete
   - Suggest manual intervention
</timeout_handling>
```

**Note**: Claude Code has built-in timeouts for tool calls. Subagent prompts should include guidance on what to do when operations approach reasonable time limits.
</implementation>
</timeouts>

<multiple_verification_paths>
**Pattern**: Different validators catch different error types.

<example>
```markdown
<verification_strategy>
After generating code:
1. Syntax check: Parse code to verify valid syntax
2. Type check: Run static type checker (if applicable)
3. Linting: Check for common issues and anti-patterns
4. Security scan: Check for obvious vulnerabilities
5. Test run: Execute tests if available

If any check fails, fix issue and re-run all checks.
Each check catches different error types.
</verification_strategy>
```

**Benefit**: Layered validation catches more issues than single validation pass.
</example>
</multiple_verification_paths>

<reassigning_tasks>
**Pattern**: Invoke alternative agents or escalate to human when primary approach fails.

<example>
```markdown
<escalation_workflow>
If automated fix fails after 2 attempts:
1. Document what was tried and why it failed
2. Provide diagnosis of the problem
3. Recommend human review with specific questions to investigate
4. DO NOT continue attempting automated fixes that aren't working

Know when to escalate rather than thrashing.
</escalation_workflow>
```

**Key insight**: Subagents should recognize their limitations and provide useful handoff information.
</example>
</reassigning_tasks>
</recovery_strategies>

<structured_communication>


Multi-agent systems fail when communication is ambiguous. Structured messaging prevents misunderstandings.

<message_types>
Every message between agents (or from agent to user) should have explicit type:

**Request**: Asking for something
```markdown
Type: Request
From: code-reviewer
To: test-writer
Task: Create tests for authentication module
Context: Recent security review found gaps in auth testing
Expected output: Comprehensive test suite covering auth edge cases
```

**Inform**: Providing information
```markdown
Type: Inform
From: debugger
To: Main chat
Status: Investigation complete
Findings: Root cause identified in line 127, race condition in async handler
```

**Commit**: Promising to do something
```markdown
Type: Commit
From: security-reviewer
Task: Review all changes in PR #342 for security issues
Deadline: Before responding to main chat
```

**Reject**: Declining request with reason
```markdown
Type: Reject
From: test-writer
Reason: Cannot write tests - no testing framework configured in project
Recommendation: Install Jest or similar framework first
```
</message_types>

<schema_validation>
**Pattern**: Validate every payload against expected schema.

<example>
```markdown
<output_validation>
Expected output format:
{
  "vulnerabilities": [
    {
      "severity": "Critical|High|Medium|Low",
      "location": "file:line",
      "type": "string",
      "description": "string",
      "fix": "string"
    }
  ],
  "summary": "string"
}

Before returning output:
1. Verify JSON is valid
2. Check all required fields present
3. Validate severity values are from allowed list
4. Ensure location follows "file:line" format
</output_validation>
```

**Benefit**: Prevents malformed outputs from breaking downstream processes.
</example>
</schema_validation>
</structured_communication>

<observability>


"Most agent failures are not model failures, they are context failures."

<structured_logging>
**What to log**:
- Input prompts and parameters
- Tool calls and their results
- Intermediate reasoning (if visible)
- Final outputs
- Metadata (timestamps, model version, token usage, latency)
- Errors and warnings

**Log structure**:
```markdown
Invocation ID: abc-123-def
Timestamp: 2025-11-15T14:23:01Z
Subagent: security-reviewer
Model: sonnet-4.5
Input: "Review changes in commit a3f2b1c"
Tool calls:
  1. git diff a3f2b1c (success, 234 lines)
  2. Read src/auth.ts (success, 156 lines)
  3. Read src/db.ts (success, 203 lines)
Output: 3 vulnerabilities found (2 High, 1 Medium)
Tokens: 2,341 input, 876 output
Latency: 4.2s
Status: Success
```

**Use case**: Debugging failures, identifying patterns, performance optimization.
</structured_logging>

<correlation_ids>
**Pattern**: Track every message, plan, and tool call for end-to-end reconstruction.

```markdown
Correlation ID: workflow-20251115-abc123

Main chat [abc123]:
  → Launched code-reviewer [abc123-1]
     → Tool: git diff [abc123-1-t1]
     → Tool: Read auth.ts [abc123-1-t2]
     → Returned: 3 issues found
  → Launched test-writer [abc123-2]
     → Tool: Read auth.ts [abc123-2-t1]
     → Tool: Write auth.test.ts [abc123-2-t2]
     → Returned: Test suite created
  → Presented results to user
```

**Benefit**: Can trace entire workflow execution, identify where failures occurred, understand cascading effects.
</correlation_ids>

<metrics_monitoring>
**Key metrics to track**:
- Success rate (completed tasks / total invocations)
- Error rate by error type
- Average token usage (spikes indicate prompt issues)
- Latency trends (increases suggest inefficiency)
- Tool call patterns (unusual patterns indicate problems)
- Retry rates (how often users re-invoke after failure)

**Alert thresholds**:
- Success rate drops below 80%
- Error rate exceeds 15%
- Token usage increases >50% without prompt changes
- Latency exceeds 2x baseline
- Same error type occurs >5 times in 24 hours
</metrics_monitoring>

<evaluator_agents>
**Pattern**: Dedicated quality guardrail agents validate outputs.

<example>
```markdown
---
name: output-validator
description: Validates subagent outputs against expected schemas and quality criteria. Use after any subagent produces structured output.
tools: Read
model: haiku
---

<role>
You are an output validation specialist. Check subagent outputs for:
- Schema compliance
- Completeness
- Internal consistency
- Format correctness
</role>

<workflow>
1. Receive subagent output and expected schema
2. Validate structure matches schema
3. Check for required fields
4. Verify value constraints (enums, formats, ranges)
5. Test internal consistency (references valid, no contradictions)
6. Return validation report: Pass/Fail with specific issues
</workflow>

<validation_criteria>
Pass: All checks succeed
Fail: Any check fails - provide detailed error report
Partial: Minor issues that don't prevent use - flag warnings
</validation_criteria>
```

**Use case**: Critical workflows where output quality is essential, high-risk operations, compliance requirements.
</example>
</evaluator_agents>
</observability>

<anti_patterns>


<anti_pattern name="silent_failures">
❌ Subagent fails but doesn't indicate failure in output

**Example**:
```markdown
Task: Review 10 files for security issues
Reality: Only reviewed 3 files due to errors, returned results anyway
Output: "No issues found" (incomplete review, but looks successful)
```

**Fix**: Explicitly state what was reviewed, flag partial completion, include error summary.
</anti_pattern>

<anti_pattern name="no_fallback">
❌ When ideal path fails, subagent gives up entirely

**Example**:
```markdown
Task: Generate code from API documentation
Error: API docs unavailable
Output: "Cannot complete task, API docs not accessible"
```

**Better**:
```markdown
Error: API docs unavailable
Fallback: Using cached documentation (last updated: 2025-11-01)
Output: Code generated with note: "Verify against current API docs, using cached version"
```

**Principle**: Provide best possible output given constraints, clearly flag limitations.
</anti_pattern>

<anti_pattern name="infinite_retry">
❌ Retrying failed operations without backoff or limit

**Risk**: Wastes tokens, time, and may hit rate limits.

**Fix**: Maximum retry count (typically 2-3), exponential backoff, fallback after exhausting retries.
</anti_pattern>

<anti_pattern name="error_cascading">
❌ Downstream agents assume upstream outputs are valid

**Example**:
```markdown
Agent 1: Generates code (contains syntax error)
  ↓
Agent 2: Writes tests (assumes code is syntactically valid, tests fail)
  ↓
Agent 3: Runs tests (all tests fail due to syntax error in code)
  ↓
Total workflow failure from single upstream error
```

**Fix**: Each agent validates inputs before processing, includes error handling for invalid inputs.
</anti_pattern>

<anti_pattern name="no_error_context">
❌ Error messages without diagnostic context

**Bad**: "Failed to complete task"

**Good**: "Failed to complete task: Unable to access file src/auth.ts (file not found). Attempted to review authentication code but file missing from expected location. Recommendation: Verify file path or check if file was moved/deleted."

**Principle**: Error messages should help diagnose root cause and suggest remediation.
</anti_pattern>
</anti_patterns>

<recovery_checklist>


Include these patterns in subagent prompts:

**Error detection**:
- [ ] Validate inputs before processing
- [ ] Check tool call results for errors
- [ ] Verify outputs match expected format
- [ ] Test assumptions (file exists, data valid, etc.)

**Recovery mechanisms**:
- [ ] Define fallback approach for primary path failure
- [ ] Include retry logic for transient failures
- [ ] Graceful degradation (partial results better than none)
- [ ] Clear error messages with diagnostic context

**Failure communication**:
- [ ] Explicitly state when task cannot be completed
- [ ] Explain what was attempted and why it failed
- [ ] Provide partial results if available
- [ ] Suggest remediation or next steps

**Quality gates**:
- [ ] Validation steps before returning output
- [ ] Self-checking (does output make sense?)
- [ ] Format compliance verification
- [ ] Completeness check (all required components present?)
</recovery_checklist>
