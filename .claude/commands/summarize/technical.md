---
description: Technical summary - preserve implementation details, architecture, specs
argument-hint: [content or leave blank for current context]
---

<objective>
Create technical summary of $ARGUMENTS (or the current context if no arguments provided).

Preserve implementation details, architecture decisions, and specifications. For engineers who need to understand or build on this.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What system/feature to summarize
- Level of detail (overview vs deep dive)
- Purpose (handoff, reference, onboarding)
- Audience technical level

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If detail level unclear:**
- "How detailed?" with options: Architecture overview, Key implementation details, Everything (full reference), Other

**If purpose unclear:**
- "What's this for?" with options: Handoff to another engineer, Personal reference, Onboarding docs, Decision documentation, Other

**If focus unclear:**
- "What to emphasize?" with options: Architecture/design, Implementation gotchas, Dependencies/constraints, All equally, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to create technical summary, or would you like me to ask more questions?"

Options:
1. **Start summarizing** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "Any specific components to focus on?", "Known issues to highlight?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start summarizing" → proceed to summary
</decision_gate>

</intake_gate>

<process>
1. Identify the technical system/feature being described
2. Extract:
   - Architecture and components
   - Data flow and interfaces
   - Key implementation details
   - Constraints and limitations
   - Dependencies and requirements
3. Preserve specific values, configs, and code references
4. Note gotchas and edge cases
</process>

<output_format>
## Technical Summary: [System/Feature]

**What it does:**
[One sentence functional description]

**Architecture:**
- Components: [list]
- Data flow: [description or diagram]
- Key interfaces: [APIs, protocols]

**Implementation Details:**
- [Specific technical detail]
- [Specific technical detail]
- [Specific technical detail]

**Dependencies:**
- [Dependency]: [version/requirement]

**Constraints/Limitations:**
- [Constraint]: [implication]

**Gotchas:**
- [Edge case or non-obvious behavior]

**Key Code/Config:**
```
[Relevant snippets, commands, or config]
```
</output_format>

<artifact_output>
Save the summary to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/summaries/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-technical.md`
   - Example: `auth-system-technical.md`

3. Write the complete summary to the file

4. Report to user: "Saved to `artifacts/summaries/[filename]`"
</artifact_output>

<success_criteria>
- Another engineer could understand and extend this
- Specific values preserved (not "configure the timeout" but "timeout: 30s")
- Architecture is clear
- Gotchas are surfaced
- No implementation details lost to abstraction
- Output saved to artifacts/summaries/ directory
</success_criteria>
