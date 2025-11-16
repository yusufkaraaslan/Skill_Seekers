# 🤖 Agent Cheatsheet for Interns

## Quick Reference Guide

### Core Specialist Agents

| Agent | Best For | When to Use | Key Output |
|-------|-----------|-------------|------------|
| **@code-analyzer** | Code quality review | Pre-commit, PR review, code health checks | Complexity metrics, anti-patterns, refactoring recommendations |
| **@architectural-critic** | System design review | Architecture decisions, technical debt assessment | Phase boundaries, structural patterns, intervention strategies |
| **@security-analyst** | Security review | Security audits, vulnerability assessment | Security findings, vulnerability reports, remediation steps |
| **@performance-auditor** | Performance optimization | Slow APIs, memory issues, bottlenecks | Performance metrics, optimization suggestions, ROI calculations |
| **@test-generator** | Test creation | New features, test coverage gaps | Unit/integration tests, CI/CD integration, coverage reports |

### Advanced Specialist Agents

| Agent | Best For | When to Use | Key Output |
|-------|-----------|-------------|------------|
| **@cognitive-resonator** | Developer experience | Code readability, team productivity | Mental model alignment, cognitive flow improvements |
| **@precision-editor** | Surgical code changes | Targeted fixes, minimal side effects | Precise edits, architectural integrity preservation |
| **@possibility-weaver** | Creative problem solving | Innovation, breaking local optima | Novel perspectives, solution space expansion |

### Orchestrator Agents

| Agent | Best For | When to Use | Key Output |
|-------|-----------|-------------|------------|
| **@orchestrator-agent** | Team management | Parallel tasks, delegation | Coordinated multi-agent results |
| **@referee-agent-csp** | Decision making | Conflicting recommendations, synthesis | Deterministic evaluation, autonomous selection |
| **@intelligence-orchestrator** | System enhancement | Intelligence improvement, workflow optimization | Enhanced ecosystem, optimized workflows |

## 🎯 Invocation Scenarios

### Common Development Workflows

#### **Code Review**
```bash
@code-analyzer
# "Review this PR for complexity and anti-patterns"
```

#### **Security Audit**
```bash
@security-analyst
# "Check this authentication system for vulnerabilities"
```

#### **Performance Issue**
```bash
@performance-auditor
# "This API is slow, identify bottlenecks"
```

#### **New Feature Testing**
```bash
@test-generator
# "Create comprehensive tests for this new feature"
```

#### **Architecture Decision**
```bash
@architectural-critic
# "Evaluate this microservice design"
```

### Complex Multi-Step Tasks

#### **Pre-Release Quality Check**
```bash
@code-analyzer
@security-analyst
@performance-auditor
@test-generator
# "Complete quality assessment before release"
```

#### **System Refactoring**
```bash
@architectural-critic
@precision-editor
@test-generator
# "Refactor this module with minimal risk"
```

#### **Performance Optimization**
```bash
@performance-auditor
@precision-editor
@code-analyzer
# "Optimize this codebase systematically"
```

#### **Innovation Session**
```bash
@possibility-weaver
@architectural-critic
@code-analyzer
# "Explore novel solutions for this problem"
```

### Orchestrated Workflows

#### **Team Coordination**
```bash
@orchestrator-agent
# "Coordinate parallel analysis of this system"
# Delegates to multiple agents automatically
```

#### **Decision Synthesis**
```bash
@referee-agent-csp
# "Choose best approach from conflicting recommendations"
# Provides metric-driven selection
```

#### **Ecosystem Enhancement**
```bash
@intelligence-orchestrator
# "Improve our development workflow"
# Enhances entire system intelligence
```

## 🚨 Quick Decision Tree

**1. Is this about code quality?**
   → Yes: `@code-analyzer`

**2. Is this about security?**
   → Yes: `@security-analyst`

**3. Is this about performance?**
   → Yes: `@performance-auditor`

**4. Is this about tests?**
   → Yes: `@test-generator`

**5. Is this about architecture?**
   → Yes: `@architectural-critic`

**6. Is this a complex multi-agent task?**
   → Yes: `@orchestrator-agent` or `@referee-agent-csp`

**7. Need creative solutions?**
   → Yes: `@possibility-weaver`

**8. Need precise changes?**
   → Yes: `@precision-editor`

**9. Is this about developer experience?**
   → Yes: `@cognitive-resonator`

**10. System-wide improvement?**
    → Yes: `@intelligence-orchestrator`

## 💡 Pro Tips

### **For Interns**
- Start with single agents, not orchestrators
- `@code-analyzer` is your most common use case
- Always provide context about what you're trying to achieve
- Don't be afraid to try multiple agents for the same problem

### **For Complex Problems**
- Use `@orchestrator-agent` for coordination
- Use `@referee-agent-csp` for decision making
- Combine specialist agents for comprehensive analysis

### **Best Practices**
- Be specific about your goals
- Provide relevant context about your project
- Ask follow-up questions if recommendations aren't clear
- Use agent recommendations to learn, not just to implement

## 🆘 Getting Help

If you're unsure which agent to use:
1. Start with this cheatsheet
2. Ask yourself the decision tree questions
3. When in doubt, `@code-analyzer` is usually a safe starting point
4. For truly complex problems, use `@orchestrator-agent`

---

*Last updated: Based on Skill Seekers Agent Registry*
*For full agent details, see `.claude/agents/` directory*