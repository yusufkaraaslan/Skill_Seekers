<overview>
Standard SUMMARY.md structure for all prompt outputs. Every executed prompt creates this file for human scanning.
</overview>

<template>
```markdown
# {Topic} {Purpose} Summary

**{Substantive one-liner describing outcome}**

## Version
{v1 or "v2 (refined from v1)"}

## Changes from Previous
{Only include if v2+, otherwise omit this section}

## Key Findings
- {Most important finding or action}
- {Second key item}
- {Third key item}

## Files Created
{Only include for Do prompts}
- `path/to/file.ts` - Description

## Decisions Needed
{Specific actionable decisions requiring user input, or "None"}

## Blockers
{External impediments preventing progress, or "None"}

## Next Step
{Concrete forward action}

---
*Confidence: {High|Medium|Low}*
*Iterations: {n}*
*Full output: {filename.md}* (omit for Do prompts)
```
</template>

<field_requirements>

<one_liner>
Must be substantive - describes actual outcome, not status.

**Good**: "JWT with jose library and httpOnly cookies recommended"
**Bad**: "Research completed"

**Good**: "4-phase implementation: types → JWT core → refresh → tests"
**Bad**: "Plan created"

**Good**: "JWT middleware complete with 6 files in src/auth/"
**Bad**: "Implementation finished"
</one_liner>

<key_findings>
Purpose-specific content:
- **Research**: Key recommendations and discoveries
- **Plan**: Phase overview with objectives
- **Do**: What was implemented, patterns used
- **Refine**: What improved from previous version
</key_findings>

<decisions_needed>
Actionable items requiring user judgment:
- Architectural choices
- Tradeoff confirmations
- Assumption validation
- Risk acceptance

Must be specific: "Approve 15-minute token expiry" not "review recommended"
</decisions_needed>

<blockers>
External impediments (rare):
- Access issues
- Missing dependencies
- Environment problems

Most prompts have "None" - only flag genuine problems.
</blockers>

<next_step>
Concrete action:
- "Create auth-plan.md"
- "Execute Phase 1 prompt"
- "Run tests"

Not vague: "proceed to next phase"
</next_step>

</field_requirements>

<purpose_variations>

<research_summary>
Emphasize: Key recommendation, decision readiness
Next step typically: Create plan
</research_summary>

<plan_summary>
Emphasize: Phase breakdown, assumptions needing validation
Next step typically: Execute first phase
</plan_summary>

<do_summary>
Emphasize: Files created, test status
Next step typically: Run tests or execute next phase
</do_summary>

<refine_summary>
Emphasize: What improved, version number
Include: Changes from Previous section
</refine_summary>

</purpose_variations>
