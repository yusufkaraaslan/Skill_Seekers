---
description: Audit skill for YAML compliance, pure XML structure, progressive disclosure, and best practices
argument-hint: <skill-path>
---

<objective>
Invoke the skill-auditor subagent to audit the skill at $ARGUMENTS for compliance with Agent Skills best practices.

This ensures skills follow proper structure (pure XML, required tags, progressive disclosure) and effectiveness patterns.
</objective>

<process>
1. Invoke skill-auditor subagent
2. Pass skill path: $ARGUMENTS
3. Subagent will read updated best practices (including pure XML structure requirements)
4. Subagent evaluates XML structure quality, required/conditional tags, anti-patterns
5. Review detailed findings with file:line locations, compliance scores, and recommendations
</process>

<success_criteria>
- Subagent invoked successfully
- Arguments passed correctly to subagent
- Audit includes XML structure evaluation
</success_criteria>
