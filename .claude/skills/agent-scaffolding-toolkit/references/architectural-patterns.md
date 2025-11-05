# Agent Architectural Patterns (Layer 2)

## Overview

This document provides detailed guidance on when and how to use different agent types in multi-agent workflows. Understanding these patterns is crucial for effective agent orchestration and eliminating human-in-the-loop dependencies.

## Core Agent Types

### 1. Orchestrator Agent (@orchestrator-agent)

**Purpose**: Chief-of-staff role for coordinating multiple agents and parallel execution workflows.

**Development Methodology Applied**:
- Created using first principles (single interface pattern)
- Addresses second order effects (context consumption optimization)
- Manages interdependencies (R&D Framework: Reduce and Delegate)
- Systems thinking approach (holistic workflow orchestration)
- Inversion principle (what to avoid: direct execution, state management)

**When to Use:**
- Complex tasks requiring multiple specialized perspectives
- Parallel execution of independent subtasks
- Workflows that need coordination and synthesis
- Large-scale projects with multiple moving parts

**Key Characteristics:**
- Uses **Opus** model for complex reasoning and prompt engineering
- Requires **Task** tool for delegation
- Maintains **context isolation** (doesn't get polluted by subagent work)
- Focuses on **supervision and synthesis**, not execution

**Anti-Patterns:**
❌ Don't use for simple, single-agent tasks
❌ Don't let it get bogged down in implementation details
❌ Don't use when tasks are purely sequential

### 2. Referee Agent (@referee-agent-csp)

**Purpose**: Deterministic synthesis and objective selection from multiple parallel outputs.

**Development Methodology Applied**:
- First principles: Objective metric-driven selection
- Second order effects: Autonomous decision making reduces human bottlenecks
- Interdependencies: Programmatic JSON output for orchestrator integration
- Systems thinking: Complete audit trail for reproducibility
- Inversion: What to avoid (subjective input, stateful decisions)

**When to Use:**
- "Best of N" scenarios where multiple agents produce different solutions
- Automated quality gates and compliance checking
- Metric-driven evaluation and selection
- Eliminating human review bottlenecks

**Key Characteristics:**
- Uses **Opus** model for critical decision-making
- Requires **Read**, **Bash**, **Task**, **Grep** tools
- Operates **autonomously** without human input
- Provides **auditable, objective** decisions

**Anti-Patterns:**
❌ Don't use for subjective or creative decisions
❌ Don't use when only one solution exists
❌ Don't use without clear evaluation criteria

### 3. Specialist Agent (@domain-specialist)

**Purpose**: Domain-specific expertise and focused problem-solving.

**When to Use:**
- Tasks requiring deep domain knowledge
- Specialized technical areas (security, performance, etc.)
- When specific expertise is needed beyond general capabilities
- Focused, well-defined problem domains

**Key Characteristics:**
- Typically uses **Sonnet** model (balanced performance)
- Tool selection varies by domain needs
- **Focused scope** with deep domain knowledge
- Applies **industry best practices** and patterns

**Anti-Patterns:**
❌ Don't use for general coordination tasks
❌ Don't use when domain expertise isn't critical
❌ Don't create overly narrow specializations

## Workflow Patterns

### Pattern 1: Parallel Exploration → Referee Selection

```
User Request → Orchestrator → Parallel Specialists → Referee → Final Result
```

**Use Case**: Generating multiple solutions and selecting the best one
**Example**: Code refactoring with multiple approaches, best implementation selected

### Pattern 2: Sequential Specialization

```
User Request → Orchestrator → Specialist A → Specialist B → Synthesis
```

**Use Case**: Multi-stage processes requiring different expertise
**Example**: Security audit → Performance analysis → Final recommendations

### Pattern 3: Hierarchical Orchestration

```
User Request → Chief Orchestrator → Domain Orchestrators → Specialists → Synthesis
```

**Use Case**: Very large, complex projects with multiple domains
**Example**: Complete system redesign with frontend, backend, and DevOps components

## Agent Interaction Rules

### 1. Context Isolation
- Subagents operate in isolated contexts
- Orchestrator maintains clean primary context
- No cross-contamination between agent contexts

### 2. Communication Protocol
- Subagents report back to orchestrator, not user
- Structured reporting formats (JSON when possible)
- Clear success/failure indicators and reasoning

### 3. Tool Delegation
- Use the least expensive model sufficient for the task
- Haiku for simple exploration/research
- Sonnet for analysis and implementation
- Opus for synthesis and critical decisions

### 4. State Management
- Assume all agents are stateless
- Required state must be passed explicitly
- Use files for persistent state between agents

## Best Practices

### Agent Design
1. **Single Responsibility**: Each agent has one clear purpose
2. **Clear Boundaries**: Well-defined scope and capabilities
3. **Tool Appropriateness**: Only include necessary tools
4. **Output Consistency**: Standardized output formats for integration

### Workflow Design
1. **Parallel When Possible**: Maximize parallel execution for speed
2. **Clear Success Criteria**: Define objective measures for success
3. **Error Recovery**: Plan for agent failures and retries
4. **Resource Management**: Consider token costs and model selection

### Integration Patterns
1. **Progressive Disclosure**: Start simple, add complexity as needed
2. **Validation Layers**: Verify outputs at each stage
3. **Feedback Loops**: Use results to improve future agent behavior
4. **Monitoring**: Track performance and success rates

## Common Pitfalls and Solutions

### Problem: Agent Scope Creep
**Solution**: Regular agent scope reviews and refactoring

### Problem: Over-Orchestration
**Solution**: Let specialists work autonomously, only coordinate when necessary

### Problem: Context Pollution
**Solution**: Strict context isolation and clean handoff protocols

### Problem: Unclear Success Metrics
**Solution**: Define objective criteria before agent execution

### Problem: Excessive Costs
**Solution**: Intelligent model selection and parallel execution optimization

## Evolution Guidelines

Start simple and evolve complexity based on actual needs:

1. **Begin**: Single specialist agent for clear problem domain
2. **Add**: Orchestrator when coordination becomes necessary
3. **Introduce**: Referee when multiple solutions need objective selection
4. **Scale**: Hierarchical orchestration for very complex workflows

This progressive approach ensures you only add complexity when it provides clear value.