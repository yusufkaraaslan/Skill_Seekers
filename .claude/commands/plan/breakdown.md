---
description: Break big thing into smaller tasks - works at any level
argument-hint: [task/feature/epic or leave blank for current context]
---

<objective>
Break down $ARGUMENTS (or the current discussion if no arguments provided) into smaller, actionable pieces.

Take something too big to start and make it approachable. Works for epics, features, tasks, or any chunk of work.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What to break down
- Desired granularity level
- Known constraints or dependencies
- Priority relative to other work

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If granularity unclear:**
- "How granular should pieces be?" with options: Very small (single focused change), Small (one component/feature), Medium (coherent unit of work), Flexible, Other

**If dependencies matter:**
- "Do dependencies matter?" with options: Yes (show execution order), No (all independent), Some dependencies, Other

**If scope unclear:**
- "What kind of work is this?" with options: Building/implementing, Research/exploration, Configuration/setup, Mixed, Other

**If done criteria unclear:**
- "How precise should 'done' be?" with options: Very specific (testable assertions), General (obvious when complete), Mix, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to break this down, or would you like me to ask more questions?"

Options:
1. **Break it down** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "Any pieces you already know?", "What's the most complex part?", "Anything that can be parallelized?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Break it down" → proceed to creating
</decision_gate>

</intake_gate>

<process>
After intake complete:

1. State the thing being broken down
2. Identify natural seams (where it splits cleanly)
3. Break into pieces that are:
   - Independent (can be done separately)
   - Testable (know when it's done)
   - Appropriately scoped (completable without context loss)
4. Order by dependencies
5. Identify the first piece to start
</process>

<output_format>
## Breakdown: [Thing]

### Strategic Summary
[2-3 sentences: what we're breaking down, why this decomposition makes sense, key insight about the structure]

### Pieces

**1. [Piece name]**
- What: [specific deliverable]
- Done when: [testable criterion]
- Complexity: S/M/L
- Dependencies: none

**2. [Piece name]**
- What: [specific deliverable]
- Done when: [testable criterion]
- Complexity: S/M/L
- Dependencies: [Piece 1]

**3. [Piece name]**
- What: [specific deliverable]
- Done when: [testable criterion]
- Complexity: S/M/L
- Dependencies: [Piece 1]

**4. [Piece name]**
- What: [specific deliverable]
- Done when: [testable criterion]
- Complexity: S/M/L
- Dependencies: [Pieces 2, 3]

[Continue as needed...]

### Implementation Context
<claude_context>
<files>
- pattern: [glob patterns for files involved]
- reference: [existing similar implementations to follow]
</files>
<approach>
- tools: [libraries, APIs, packages to use]
- patterns: [architectural patterns to follow]
- avoid: [anti-patterns, things that won't work here]
</approach>
</claude_context>

### Execution Plan
<execution>
<order>
[1] → [2] → [4]
  ↘ [3] ↗
</order>
<parallel>
- [Pieces that can run in parallel, if any]
</parallel>
<start>
[First piece to execute and why]
</start>
</execution>

**Next Action:** Execute piece 1, or run /plan/sprint to plan the first coherent batch
</output_format>

<artifact_output>
Save the breakdown to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/plans/`

2. Generate filename from topic:
   - Slugify the task/feature name (lowercase, hyphens for spaces)
   - Format: `[topic]-breakdown.md`
   - Example: `payment-integration-breakdown.md`

3. Write the complete breakdown to the file

4. Report to user: "Saved to `artifacts/plans/[filename]`"
</artifact_output>

<success_criteria>
- Each piece is scoped to be completable without losing context
- "Done when" is specific and testable
- Dependencies create clear execution order
- No piece requires further breakdown
- Starting point is obvious
- Original scope is fully covered by pieces
- Implementation context is specific enough for Claude to execute
- Output saved to artifacts/plans/ directory
</success_criteria>
