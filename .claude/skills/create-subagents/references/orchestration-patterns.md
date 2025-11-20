# Orchestration Patterns for Multi-Agent Systems

<core_concept>
Orchestration defines how multiple subagents coordinate to complete complex tasks.

**Single agent**: Sequential execution within one context.
**Multi-agent**: Coordination between multiple specialized agents, each with focused expertise.
</core_concept>

<pattern_catalog>


<sequential>
**Sequential pattern**: Agents chained in predefined, linear order.

<characteristics>
- Each agent processes output from previous agent
- Pipeline of specialized transformations
- Deterministic flow (A → B → C)
- Easy to reason about and debug
</characteristics>

<when_to_use>
**Ideal for**:
- Document review workflows (security → performance → style)
- Data processing pipelines (extract → transform → validate → load)
- Multi-stage reasoning (research → analyze → synthesize → recommend)

**Example**:
```markdown
Task: Comprehensive code review

Flow:
1. security-reviewer: Check for vulnerabilities
   ↓ (security report)
2. performance-analyzer: Identify performance issues
   ↓ (performance report)
3. test-coverage-checker: Assess test coverage
   ↓ (coverage report)
4. report-synthesizer: Combine all findings into actionable review
```
</when_to_use>

<implementation>
```markdown
<sequential_workflow>
Main chat orchestrates:
1. Launch security-reviewer with code changes
2. Wait for security report
3. Launch performance-analyzer with code changes + security report context
4. Wait for performance report
5. Launch test-coverage-checker with code changes
6. Wait for coverage report
7. Synthesize all reports for user
</sequential_workflow>
```

**Benefits**: Clear dependencies, each stage builds on previous.
**Drawbacks**: Slower than parallel (sequential latency), one failure blocks pipeline.
</implementation>
</sequential>

<parallel>
**Parallel/Concurrent pattern**: Multiple specialized subagents perform tasks simultaneously.

<characteristics>
- Agents execute independently and concurrently
- Outputs synthesized for final response
- Significant speed improvements
- Requires synchronization
</characteristics>

<when_to_use>
**Ideal for**:
- Independent analyses of same input (security + performance + quality)
- Processing multiple independent items (review multiple files)
- Research tasks (gather information from multiple sources)

**Performance data**: Anthropic's research system with 3-5 subagents in parallel achieved 90% time reduction.

**Example**:
```markdown
Task: Comprehensive code review (parallel approach)

Launch simultaneously:
- security-reviewer (analyzes auth.ts)
- performance-analyzer (analyzes auth.ts)
- test-coverage-checker (analyzes auth.ts test coverage)

Wait for all three to complete → synthesize findings.

Time: max(agent_1, agent_2, agent_3) vs sequential: agent_1 + agent_2 + agent_3
```
</when_to_use>

<implementation>
```markdown
<parallel_workflow>
Main chat orchestrates:
1. Launch all agents simultaneously with same context
2. Collect outputs as they complete
3. Synthesize results when all complete

Synchronization challenges:
- Handling different completion times
- Dealing with partial failures (some agents fail, others succeed)
- Combining potentially conflicting outputs
</parallel_workflow>
```

**Benefits**: Massive speed improvement, efficient resource utilization.
**Drawbacks**: Increased complexity, synchronization challenges, higher cost (multiple agents running).
</implementation>
</parallel>

<hierarchical>
**Hierarchical pattern**: Agents organized in layers, higher-level agents oversee lower-level.

<characteristics>
- Tree-like structure with delegation
- Higher-level agents break down tasks
- Lower-level agents execute specific subtasks
- Master-worker relationships
</characteristics>

<when_to_use>
**Ideal for**:
- Large, complex problems requiring decomposition
- Tasks with natural hierarchy (system design → component design → implementation)
- Situations requiring oversight and quality control

**Example**:
```markdown
Task: Implement complete authentication system

Hierarchy:
- architect (top-level): Designs overall auth system, breaks into components
  ↓ delegates to:
  - backend-dev: Implements API endpoints
  - frontend-dev: Implements login UI
  - security-reviewer: Reviews both for vulnerabilities
  - test-writer: Creates integration tests
  ↑ reports back to:
- architect: Integrates components, ensures coherence
```
</when_to_use>

<implementation>
```markdown
<hierarchical_workflow>
Top-level agent (architect):
1. Analyze requirements
2. Break into subtasks
3. Delegate to specialized agents
4. Monitor progress
5. Integrate results
6. Validate coherence across components

Lower-level agents:
- Receive focused subtask
- Execute with deep expertise
- Report results to coordinator
- No awareness of other agents' work
</hierarchical_workflow>
```

**Benefits**: Handles complexity through decomposition, clear responsibility boundaries.
**Drawbacks**: Overhead in coordination, risk of misalignment between levels.
</implementation>
</hierarchical>

<coordinator>
**Coordinator pattern**: Central LLM agent routes tasks to specialized sub-agents.

<characteristics>
- Central decision-maker
- Dynamic routing (not hardcoded workflow)
- AI model orchestrates based on task characteristics
- Similar to hierarchical but focused on process flow
</characteristics>

<when_to_use>
**Ideal for**:
- Diverse task types requiring different expertise
- Dynamic workflows where next step depends on results
- User-facing systems with varied requests

**Example**:
```markdown
Task: "Help me improve my codebase"

Coordinator analyzes request → determines relevant agents:
- code-quality-analyzer: Assess overall code quality
  ↓ findings suggest security issues
- Coordinator: Route to security-reviewer
  ↓ security issues found
- Coordinator: Route to auto-fixer to generate patches
  ↓ patches ready
- Coordinator: Route to test-writer to create tests for fixes
  ↓
- Coordinator: Synthesize all work into improvement plan
```

**Dynamic routing** based on intermediate results, not predefined flow.
</when_to_use>

<implementation>
```markdown
<coordinator_workflow>
Coordinator agent prompt:

<role>
You are an orchestration coordinator. Route tasks to specialized agents based on:
- Task characteristics
- Available agents and their capabilities
- Results from previous agents
- User goals
</role>

<available_agents>
- security-reviewer: Security analysis
- performance-analyzer: Performance optimization
- test-writer: Test creation
- debugger: Bug investigation
- refactorer: Code improvement
</available_agents>

<decision_process>
1. Analyze incoming task
2. Identify relevant agents (may be multiple)
3. Determine execution strategy (sequential, parallel, conditional)
4. Launch agents with appropriate context
5. Analyze results
6. Decide next step (more agents, synthesis, completion)
7. Repeat until task complete
</decision_process>
```

**Benefits**: Flexible, adaptive to task requirements, efficient agent utilization.
**Drawbacks**: Coordinator is single point of failure, complexity in routing logic.
</implementation>
</coordinator>

<orchestrator_worker>
**Orchestrator-Worker pattern**: Central orchestrator assigns tasks, manages execution.

<characteristics>
- Centralized coordination with distributed execution
- Workers focus on specific, independent tasks
- Similar to distributed computing master-worker pattern
- Clear separation of planning (orchestrator) and execution (workers)
</characteristics>

<when_to_use>
**Ideal for**:
- Batch processing (process 100 files)
- Independent tasks that can be distributed (analyze multiple API endpoints)
- Load balancing across workers

**Example**:
```markdown
Task: Security review of 50 microservices

Orchestrator:
1. Identifies all 50 services
2. Breaks into batches of 5
3. Assigns batches to worker agents
4. Monitors progress
5. Aggregates results

Workers (5 concurrent instances of security-reviewer):
- Each reviews assigned services
- Reports findings to orchestrator
- Independent execution (no inter-worker communication)
```
</when_to_use>

<sonnet_haiku_orchestration>
**Sonnet 4.5 + Haiku 4.5 orchestration**: Optimal cost/performance pattern.

Research findings:
- Sonnet 4.5: "Best model in the world for agents", exceptional at planning and validation
- Haiku 4.5: "90% of Sonnet 4.5 performance", one of best coding models, fast and cost-efficient

**Pattern**:
```markdown
1. Sonnet 4.5 (Orchestrator):
   - Analyzes task
   - Creates plan
   - Breaks into subtasks
   - Identifies what can be parallelized

2. Multiple Haiku 4.5 instances (Workers):
   - Each completes assigned subtask
   - Executes in parallel for speed
   - Returns results to orchestrator

3. Sonnet 4.5 (Orchestrator):
   - Integrates results from all workers
   - Validates output quality
   - Ensures coherence
   - Delivers final output
```

**Cost/performance optimization**: Expensive Sonnet only for planning/validation, cheap Haiku for execution.
</sonnet_haiku_orchestration>
</orchestrator_worker>
</pattern_catalog>

<hybrid_approaches>


Real-world systems often combine patterns for different workflow phases.

<example name="sequential_then_parallel">
**Sequential for initial processing → Parallel for analysis**:

```markdown
Task: Comprehensive feature implementation review

Sequential phase:
1. requirements-validator: Check requirements completeness
   ↓
2. implementation-reviewer: Verify feature implemented correctly
   ↓

Parallel phase (once implementation validated):
3. Launch simultaneously:
   - security-reviewer
   - performance-analyzer
   - accessibility-checker
   - test-coverage-validator
   ↓

Sequential synthesis:
4. report-generator: Combine all findings
```

**Rationale**: Early stages have dependencies (can't validate implementation before requirements), later stages are independent analyses.
</example>

<example name="coordinator_with_hierarchy">
**Coordinator orchestrating hierarchical teams**:

```markdown
Top level: Coordinator receives "Build payment system"

Coordinator creates hierarchical teams:

Team 1 (Backend):
- Lead: backend-architect
  - Workers: api-developer, database-designer, integration-specialist

Team 2 (Frontend):
- Lead: frontend-architect
  - Workers: ui-developer, state-management-specialist

Team 3 (DevOps):
- Lead: infra-architect
  - Workers: deployment-specialist, monitoring-specialist

Coordinator:
- Manages team coordination
- Resolves inter-team dependencies
- Integrates deliverables
```

**Benefit**: Combines dynamic routing (coordinator) with team structure (hierarchy).
</example>
</hybrid_approaches>

<implementation_guidance>


<coordinator_subagent>
**Example coordinator implementation**:

```markdown
---
name: workflow-coordinator
description: Orchestrates multi-agent workflows. Use when task requires multiple specialized agents in coordination.
tools: all
model: sonnet
---

<role>
You are a workflow coordinator. Analyze tasks, identify required agents, orchestrate their execution.
</role>

<available_agents>
{list of specialized agents with capabilities}
</available_agents>

<orchestration_strategies>
**Sequential**: When agents depend on each other's outputs
**Parallel**: When agents can work independently
**Hierarchical**: When task needs decomposition with oversight
**Adaptive**: Choose pattern based on task characteristics
</orchestration_strategies>

<workflow>
1. Analyze incoming task
2. Identify required capabilities
3. Select agents and pattern
4. Launch agents (sequentially or parallel as appropriate)
5. Monitor execution
6. Handle errors (retry, fallback, escalate)
7. Integrate results
8. Validate coherence
9. Deliver final output
</workflow>

<error_handling>
If agent fails:
- Retry with refined context (1-2 attempts)
- Try alternative agent if available
- Proceed with partial results if acceptable
- Escalate to human if critical
</error_handling>
```
</coordinator_subagent>

<handoff_protocol>
**Clean handoffs between agents**:

```markdown
<agent_handoff_format>
From: {source_agent}
To: {target_agent}
Task: {specific task}
Context:
  - What was done: {summary of prior work}
  - Key findings: {important discoveries}
  - Constraints: {limitations or requirements}
  - Expected output: {what target agent should produce}

Attachments:
  - {relevant files, data, or previous outputs}
</agent_handoff_format>
```

**Why explicit format matters**: Prevents information loss, ensures target agent has full context, enables validation.
</handoff_protocol>

<synchronization>
**Handling parallel execution**:

```markdown
<parallel_synchronization>
Launch pattern:
1. Initiate all parallel agents with shared context
2. Track which agents have completed
3. Collect outputs as they arrive
4. Wait for all to complete OR timeout
5. Proceed with available results (flag missing if timeout)

Partial failure handling:
- If 1 of 3 agents fails: Proceed with 2 results, note gap
- If 2 of 3 agents fail: Consider retry or workflow failure
- Always communicate what was completed vs attempted
</parallel_synchronization>
```
</synchronization>
</implementation_guidance>

<anti_patterns>


<anti_pattern name="over_orchestration">
❌ Using multiple agents when single agent would suffice

**Example**: Three agents to review 10 lines of code (overkill).

**Fix**: Reserve multi-agent for genuinely complex tasks. Single capable agent often better than coordinating multiple simple agents.
</anti_pattern>

<anti_pattern name="no_coordination">
❌ Launching multiple agents with no coordination or synthesis

**Problem**: User gets conflicting reports, no coherent output, unclear which to trust.

**Fix**: Always synthesize multi-agent outputs into coherent final result.
</anti_pattern>

<anti_pattern name="sequential_when_parallel">
❌ Running independent analyses sequentially

**Example**: Security review → performance review → quality review (each independent, done sequentially).

**Fix**: Parallel execution for independent tasks. 3x speed improvement in this case.
</anti_pattern>

<anti_pattern name="unclear_handoffs">
❌ Agent outputs that don't provide sufficient context for next agent

**Example**:
```markdown
Agent 1: "Found issues"
Agent 2: Receives "Found issues" with no details on what, where, or severity
Agent 2: Can't effectively act on vague input
```

**Fix**: Structured handoff format with complete context.
</anti_pattern>

<anti_pattern name="no_error_recovery">
❌ Orchestration with no fallback when agent fails

**Problem**: One agent failure causes entire workflow failure.

**Fix**: Graceful degradation, retry logic, alternative agents, partial results (see [error-handling-and-recovery.md](error-handling-and-recovery.md)).
</anti_pattern>
</anti_patterns>

<best_practices>


<principle name="right_granularity">
**Agent granularity**: Not too broad, not too narrow.

Too broad: "general-purpose-helper" (defeats purpose of specialization)
Too narrow: "checks-for-sql-injection-in-nodejs-express-apps-only" (too specific)
Right: "security-reviewer specializing in web application vulnerabilities"
</principle>

<principle name="clear_responsibilities">
**Each agent should have clear, non-overlapping responsibility**.

Bad: Two agents both "review code for quality" (overlap, confusion)
Good: "security-reviewer" + "performance-analyzer" (distinct concerns)
</principle>

<principle name="minimize_handoffs">
**Minimize information loss at boundaries**.

Each handoff is opportunity for context loss. Structured handoff formats prevent this.
</principle>

<principle name="parallel_where_possible">
**Parallelize independent work**.

If agents don't depend on each other's outputs, run them concurrently.
</principle>

<principle name="coordinator_lightweight">
**Keep coordinator logic lightweight**.

Heavy coordinator = bottleneck. Coordinator should route and synthesize, not do deep work itself.
</principle>

<principle name="cost_optimization">
**Use model tiers strategically**.

- Planning/validation: Sonnet 4.5 (needs intelligence)
- Execution of clear tasks: Haiku 4.5 (fast, cheap, still capable)
- Highest stakes decisions: Sonnet 4.5
- Bulk processing: Haiku 4.5
</principle>
</best_practices>

<pattern_selection>


<decision_tree>
```markdown
Is task decomposable into independent subtasks?
├─ Yes: Parallel pattern (fastest)
└─ No: ↓

Do subtasks depend on each other's outputs?
├─ Yes: Sequential pattern (clear dependencies)
└─ No: ↓

Is task large/complex requiring decomposition AND oversight?
├─ Yes: Hierarchical pattern (structured delegation)
└─ No: ↓

Do task requirements vary dynamically?
├─ Yes: Coordinator pattern (adaptive routing)
└─ No: Single agent sufficient
```
</decision_tree>

<performance_vs_complexity>
**Performance**: Parallel > Hierarchical > Sequential > Coordinator (overhead)
**Complexity**: Coordinator > Hierarchical > Parallel > Sequential
**Flexibility**: Coordinator > Hierarchical > Parallel > Sequential

**Trade-off**: Choose simplest pattern that meets requirements.
</performance_vs_complexity>
</pattern_selection>
