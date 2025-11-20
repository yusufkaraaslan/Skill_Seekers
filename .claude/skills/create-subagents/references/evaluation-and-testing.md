# Evaluation and Testing for Subagents

<evaluation_framework>


<task_completion>
**Primary metric**: Proportion of tasks completed correctly and satisfactorily.

Measure:
- Did the subagent complete the requested task?
- Did it produce the expected output?
- Would a human consider the task "done"?

**Testing approach**: Create test cases with known expected outcomes, invoke subagent, compare results.
</task_completion>

<tool_correctness>
**Secondary metric**: Whether subagent calls correct tools for given task.

Measure:
- Are tool selections appropriate for the task?
- Does it use tools efficiently (not calling unnecessary tools)?
- Does it use tools in correct sequence?

**Testing approach**: Review tool call patterns in execution logs.
</tool_correctness>

<output_quality>
**Quality metric**: Assess quality of subagent-generated outputs.

Measure:
- Accuracy of analysis
- Completeness of coverage
- Clarity of communication
- Adherence to specified format

**Testing approach**: Human review or LLM-as-judge evaluation.
</output_quality>

<robustness>
**Resilience metric**: How well subagent handles failures and edge cases.

Measure:
- Graceful handling of missing files
- Recovery from tool failures
- Appropriate responses to unexpected inputs
- Boundary condition handling

**Testing approach**: Inject failures (missing files, malformed data) and verify responses.
</robustness>

<efficiency>
**Performance metrics**: Response time and resource usage.

Measure:
- Token usage (cost)
- Latency (response time)
- Number of tool calls

**Testing approach**: Monitor metrics across multiple invocations, track trends.
</efficiency>
</evaluation_framework>

<g_eval>


**G-Eval**: Use LLMs with chain-of-thought to evaluate outputs against ANY custom criteria defined in natural language.

<example>
**Custom criterion**: "Security review completeness"

```markdown
Evaluate the security review output on a 1-5 scale:

1. Missing critical vulnerability types
2. Covers basic vulnerabilities but misses some common patterns
3. Covers standard OWASP Top 10 vulnerabilities
4. Comprehensive coverage including framework-specific issues
5. Exceptional coverage including business logic vulnerabilities

Think step-by-step about which vulnerabilities were checked and which were missed.
```

**Implementation**: Pass subagent output and criteria to Claude, get structured evaluation.
</example>

**When to use**: Complex quality metrics that can't be measured programmatically (thoroughness, insight quality, appropriateness of recommendations).
</g_eval>

<validation_strategies>


<offline_testing>
**Offline validation**: Test before deployment with synthetic scenarios.

**Process**:
1. Create representative test cases covering:
   - Happy path scenarios
   - Edge cases (boundary conditions, unusual inputs)
   - Error conditions (missing data, tool failures)
   - Adversarial inputs (malformed, malicious)
2. Invoke subagent with each test case
3. Compare outputs to expected results
4. Document failures and iterate on prompt

**Example test suite for code-reviewer subagent**:
```markdown
Test 1 (Happy path): Recent commit with SQL injection vulnerability
Expected: Identifies SQL injection, provides fix, rates as Critical

Test 2 (Edge case): No recent code changes
Expected: Confirms review completed, no issues found

Test 3 (Error condition): Git repository not initialized
Expected: Gracefully handles missing git, provides helpful message

Test 4 (Adversarial): Obfuscated code with hidden vulnerability
Expected: Identifies pattern despite obfuscation
```
</offline_testing>

<simulation>
**Simulation testing**: Run subagent in realistic but controlled environments.

**Use cases**:
- Testing against historical issues (can it find bugs that were previously fixed?)
- Benchmark datasets (SWE-bench for code agents)
- Controlled codebases with known vulnerabilities

**Benefit**: Higher confidence than synthetic tests, safer than production testing.
</simulation>

<online_monitoring>
**Production monitoring**: Track metrics during real usage.

**Key metrics**:
- Success rate (completed vs failed tasks)
- User satisfaction (explicit feedback)
- Retry rate (how often users reinvoke after failure)
- Token usage trends (increasing = potential prompt issues)
- Error rates by error type

**Implementation**: Log all invocations with context, outcomes, and metrics. Review regularly for patterns.
</online_monitoring>
</validation_strategies>

<evaluation_driven_development>


**Philosophy**: Integrate evaluation throughout subagent lifecycle, not just at validation stage.

<workflow>
1. **Initial creation**: Define success criteria before writing prompt
2. **Development**: Test after each prompt iteration
3. **Pre-deployment**: Comprehensive offline testing
4. **Deployment**: Online monitoring with metrics collection
5. **Iteration**: Regular review of failures, update prompt based on learnings
6. **Continuous**: Ongoing evaluation → feedback → refinement cycles
</workflow>

**Anti-pattern**: Writing subagent, deploying, never measuring effectiveness or iterating.

**Best practice**: Treat subagent prompts as living documents that evolve based on real-world performance data.
</evaluation_driven_development>

<testing_checklist>


<before_deployment>
Before deploying a subagent, complete this validation:

**Basic functionality**:
- [ ] Invoke with representative task, verify completion
- [ ] Check output format matches specification
- [ ] Verify workflow steps are followed in sequence
- [ ] Confirm constraints are respected

**Edge cases**:
- [ ] Test with missing/incomplete data
- [ ] Test with unusual but valid inputs
- [ ] Test with boundary conditions (empty files, large files, etc.)

**Error handling**:
- [ ] Test with unavailable tools (if tool access restricted)
- [ ] Test with malformed inputs
- [ ] Verify graceful degradation when ideal path fails

**Quality checks**:
- [ ] Human review of outputs for accuracy
- [ ] Verify no hallucinations or fabricated information
- [ ] Check output is actionable and useful

**Security**:
- [ ] Verify tool access follows least privilege
- [ ] Check for potential unsafe operations
- [ ] Ensure sensitive data handling is appropriate

**Documentation**:
- [ ] Description field clearly indicates when to use
- [ ] Role and focus areas are specific
- [ ] Workflow is complete and logical
</before_deployment>
</testing_checklist>

<synthetic_data>


<when_to_use>
Synthetic data generation useful for:
- **Cold starts**: No real usage data yet
- **Edge cases**: Rare scenarios hard to capture from real data
- **Adversarial testing**: Security, robustness testing
- **Scenario coverage**: Systematic coverage of input space
</when_to_use>

<generation_approaches>
**Persona-based generation**: Create test cases from different user personas.

```markdown
Persona: Junior developer
Task: "Fix the bug where the login page crashes"
Expected behavior: Subagent provides detailed debugging steps

Persona: Senior engineer
Task: "Investigate authentication flow security"
Expected behavior: Subagent performs deep security analysis
```

**Scenario simulation**: Generate variations of common scenarios.

```markdown
Scenario: SQL injection vulnerability review
Variations:
- Direct SQL concatenation
- ORM with raw queries
- Prepared statements (should pass)
- Stored procedures with dynamic SQL
```
</generation_approaches>

<critical_limitation>
**Never rely exclusively on synthetic data.**

Maintain a validation set of real usage examples. Synthetic data can miss:
- Real-world complexity
- Actual user intent patterns
- Production environment constraints
- Emergent usage patterns

**Best practice**: 70% synthetic (for coverage), 30% real (for reality check).
</critical_limitation>
</synthetic_data>

<llm_as_judge>


<basic_pattern>
Use LLM to evaluate subagent outputs when human review is impractical at scale.

**Example evaluation prompt**:
```markdown
You are evaluating a security code review performed by an AI subagent.

Review output:
{subagent_output}

Code that was reviewed:
{code}

Evaluate on these criteria:
1. Accuracy: Are identified vulnerabilities real? (Yes/Partial/No)
2. Completeness: Were obvious vulnerabilities missed? (None missed/Some missed/Many missed)
3. Actionability: Are fixes specific and implementable? (Very/Somewhat/Not really)

Provide:
- Overall grade (A/B/C/D/F)
- Specific issues with the review
- What a human reviewer would have done differently
```
</basic_pattern>

<comparison_pattern>
**Ground truth comparison**: When correct answer is known.

```markdown
Expected vulnerabilities in test code:
1. SQL injection on line 42
2. XSS vulnerability on line 67
3. Missing authentication check on line 103

Subagent identified:
{subagent_findings}

Calculate:
- Precision: % of identified issues that are real
- Recall: % of real issues that were identified
- F1 score: Harmonic mean of precision and recall
```
</comparison_pattern>
</llm_as_judge>

<test_driven_development>


Anthropic guidance: "Test-driven development becomes even more powerful with agentic coding."

<approach>
**Before writing subagent prompt**:
1. Define expected input/output pairs
2. Create test cases that subagent must pass
3. Write initial prompt
4. Run tests, observe failures
5. Refine prompt based on failures
6. Repeat until all tests pass

**Example for test-writer subagent**:
```markdown
Test 1:
Input: Function that adds two numbers
Expected output: Test file with:
  - Happy path (2 + 2 = 4)
  - Edge cases (0 + 0, negative numbers)
  - Type errors (string + number)

Test 2:
Input: Async function that fetches user data
Expected output: Test file with:
  - Successful fetch
  - Network error handling
  - Invalid user ID handling
  - Mocked HTTP calls (no real API calls)
```

**Invoke subagent → check if outputs match expectations → iterate on prompt.**
</approach>

**Benefit**: Clear acceptance criteria before development, objective measure of prompt quality.
</test_driven_development>

<anti_patterns>


<anti_pattern name="no_testing">
❌ Deploying subagents without any validation

**Risk**: Subagent fails on real tasks, wastes user time, damages trust.

**Fix**: Minimum viable testing = invoke with 3 representative tasks before deploying.
</anti_pattern>

<anti_pattern name="only_happy_path">
❌ Testing only ideal scenarios

**Risk**: Subagent fails on edge cases, error conditions, or unusual (but valid) inputs.

**Fix**: Test matrix covering happy path, edge cases, and error conditions.
</anti_pattern>

<anti_pattern name="no_metrics">
❌ No measurement of effectiveness

**Risk**: Can't tell if prompt changes improve or degrade performance.

**Fix**: Define at least one quantitative metric (task completion rate, output quality score).
</anti_pattern>

<anti_pattern name="test_once_deploy_forever">
❌ Testing once at creation, never revisiting

**Risk**: Subagent degrades over time as usage patterns shift, codebases change, or models update.

**Fix**: Periodic re-evaluation with current usage patterns and edge cases.
</anti_pattern>
</anti_patterns>
