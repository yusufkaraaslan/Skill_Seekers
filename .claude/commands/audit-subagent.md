---
description: Audit subagent configuration for role definition, prompt quality, tool selection, XML structure compliance, and effectiveness
argument-hint: <subagent-path>
---

<objective>
Invoke the subagent-auditor subagent to audit the subagent at $ARGUMENTS for compliance with best practices, including pure XML structure standards.

This ensures subagents follow proper structure, configuration, pure XML formatting, and implementation patterns.
</objective>

<process>
1. Invoke subagent-auditor subagent
2. Pass subagent path: $ARGUMENTS
3. Subagent will read best practices and evaluate the configuration
4. Review detailed findings with file:line locations, compliance scores, and recommendations
</process>

<success_criteria>
- Subagent invoked successfully
- Arguments passed correctly to subagent
</success_criteria>
