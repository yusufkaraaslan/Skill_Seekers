---
description: Audit slash command file for YAML, arguments, dynamic context, tool restrictions, and content quality
argument-hint: <command-path>
---

<objective>
Invoke the slash-command-auditor subagent to audit the slash command at $ARGUMENTS for compliance with best practices.

This ensures commands follow security, clarity, and effectiveness standards.
</objective>

<process>
1. Invoke slash-command-auditor subagent
2. Pass command path: $ARGUMENTS
3. Subagent will read best practices and evaluate the command
4. Review detailed findings with file:line locations, compliance scores, and recommendations
</process>

<success_criteria>
- Subagent invoked successfully
- Arguments passed correctly to subagent
</success_criteria>
