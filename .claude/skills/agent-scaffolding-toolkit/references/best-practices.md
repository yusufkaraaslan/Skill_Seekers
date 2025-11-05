# Agent Development Best Practices (Layer 2)

## Overview

This document covers best practices for creating, maintaining, and evolving agents using the Agent Scaffolding Toolkit. Following these practices ensures agents are reliable, maintainable, and integrate well with Claude Code workflows.

## Agent Creation Best Practices

### 1. Define Clear Boundaries

**Do:**
```yaml
name: security-analyst
description: Analyzes code for security vulnerabilities and suggests fixes
```

**Don't:**
```yaml
name: security-performance-docs-agent
description: Analyzes security, optimizes performance, and writes documentation
```

**Why**: Single responsibility makes agents more reliable and easier to test.

### 2. Choose Appropriate Models

**Opus Model**: Use for agents that need:
- Complex reasoning and synthesis
- Prompt engineering for other agents
- Critical decision-making
- Creative problem-solving

**Sonnet Model**: Use for agents that need:
- Balanced performance and cost
- Analysis and implementation tasks
- Most specialized work
- Good reasoning without extreme complexity

**Haiku Model**: Use for agents that need:
- Fast, simple tasks
- Basic research and exploration
- Structured data extraction
- Cost-sensitive operations

### 3. Select Minimal Required Tools

**Good Tool Selection:**
```yaml
tools:
  - Read      # For understanding code
  - Grep      # For pattern searching
  - Task      # For delegation to specialists
```

**Avoid Tool Overload:**
```yaml
tools:
  - Task
  - Bash
  - Read
  - Write
  - Grep
  - SlashCommand  # Too many for focused role
```

**Why**: Fewer tools reduce complexity and improve reliability.

## Prompt Engineering Best Practices

### 1. Structure System Prompts Effectively

Use this template structure:

```markdown
You are [Agent Name], [concise role description].

Your primary responsibility is [main objective].

#### Core Expertise
- [Key skill 1]
- [Key skill 2]
- [Key skill 3]

#### Workflow Approach
1. [Step 1 with clear action]
2. [Step 2 with clear action]
3. [Step 3 with clear action]

#### Constraints and Guardrails
- [Important limitation 1]
- [Important limitation 2]

#### Output Format
[Specific format requirements]
```

### 2. Write Clear, Actionable Instructions

**Good:**
```
1. **Analyze**: Use Read tool to examine the target code files
2. **Identify**: Use Grep to search for specific vulnerability patterns
3. **Report**: Provide structured findings with severity levels
```

**Poor:**
```
Look at the code and find security issues.
```

**Why**: Clear instructions reduce ambiguity and improve consistency.

### 3. Include Specific Constraints

**Essential Constraints:**
- Scope limitations (what the agent should NOT do)
- Tool usage guidelines
- Output format requirements
- Error handling procedures

## Multi-Agent Workflow Best Practices

### 1. Design for Parallel Execution

**Good Pattern:**
```python
# Orchestrator launches parallel specialists
agents = [
    launch_agent("security-specialist", security_scope),
    launch_agent("performance-specialist", performance_scope),
    launch_agent("documentation-specialist", docs_scope)
]
results = collect_results(agents)
synthesized = synthesize_results(results)
```

**Benefits**: 3x faster execution, independent work, better resource utilization.

### 2. Implement Robust Error Handling

**Error Handling Pattern:**
1. **Timeout Protection**: Set reasonable timeouts for each agent
2. **Retry Logic**: Implement exponential backoff for failed agents
3. **Fallback Strategies**: Have alternative approaches when agents fail
4. **Clear Error Reporting**: Structured error information for debugging

### 3. Use Structured Communication

**Agent Output Format:**
```json
{
  "status": "SUCCESS|WARNING|FAILURE",
  "findings": [...],
  "recommendations": [...],
  "confidence_score": 0.95,
  "execution_time": "45s"
}
```

**Why**: Machine-readable outputs enable reliable agent orchestration.

## Validation and Testing Best Practices

### 1. Use the Validation Script

Always validate agents after creation:
```bash
python scripts/validate_agent.py --file .claude/agents/my-agent.md
```

Fix any structural issues before deployment.

### 2. Test Agent Behavior

**Testing Checklist:**
- [ ] Agent handles edge cases gracefully
- [ ] Output format is consistent and structured
- [ ] Agent stays within defined scope
- [ ] Tools are used appropriately
- [ ] Error conditions are handled well

### 3. Monitor Agent Performance

Track these metrics:
- Success rate (tasks completed without errors)
- Average response time
- Token consumption
- User satisfaction scores

## Maintenance and Evolution

### 1. Regular Agent Reviews

**Monthly Review Checklist:**
- Agent still meets user needs
- Performance is acceptable
- Tools are still appropriate
- Prompt clarity and effectiveness
- Integration with other agents

### 2. Version Control Best Practices

**Agent File Versioning:**
```bash
# Before major changes
cp .claude/agents/my-agent.md .claude/agents/my-agent.md.v1

# After validation
git add .claude/agents/my-agent.md
git commit -m "Enhance security-analyst with new vulnerability patterns"
```

### 3. Gradual Enhancement Process

1. **Start Simple**: Basic functionality with minimal scope
2. **Add Features**: Incrementally add capabilities based on user feedback
3. **Optimize**: Improve performance and reduce costs
4. **Integrate**: Enhance coordination with other agents

## Common Anti-Patterns and Solutions

### Anti-Pattern 1: Overly Broad Agent Scope

**Problem**: Agent tries to do everything
```yaml
name: full-stack-developer
description: Handles frontend, backend, database, DevOps, and testing
```

**Solution**: Split into focused specialists
```yaml
name: frontend-specialist
name: backend-specialist
name: database-specialist
name: devops-specialist
```

### Anti-Pattern 2: Insufficient Constraints

**Problem**: Agent goes beyond intended scope
```
You are a code reviewer. Look at the code and suggest improvements.
```

**Solution**: Add clear boundaries and constraints
```
You are a code reviewer focused on security and performance.
DO NOT suggest style changes or architectural modifications.
ONLY report security vulnerabilities and performance issues.
```

### Anti-Pattern 3: Poor Error Handling

**Problem**: Agent fails silently or with unclear errors
```
If you find problems, mention them.
```

**Solution**: Structured error handling
```
If no issues are found, report: "SUCCESS: No vulnerabilities found."
If issues are found, provide structured report with:
- Severity level (CRITICAL/HIGH/MEDIUM/LOW)
- File location and line numbers
- Specific vulnerability description
- Recommended fix with code example
```

## Performance Optimization

### 1. Model Selection Guidelines

- **Start with Sonnet** for most specialized tasks
- **Upgrade to Opus** only when complex reasoning is essential
- **Use Haiku** for simple, repetitive tasks

### 2. Token Optimization

- Use concise but clear prompts
- Avoid redundant instructions
- Leverage progressive disclosure
- Cache frequently used reference material

### 3. Parallel Execution Maximization

- Identify independent tasks that can run in parallel
- Use appropriate timeouts for parallel operations
- Implement efficient result collection and synthesis

By following these best practices, you'll create agents that are reliable, maintainable, and provide consistent value in multi-agent workflows.