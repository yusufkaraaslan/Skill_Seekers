---
description: Plan sprint-sized work - tasks, acceptance criteria, complexity
argument-hint: [phase/feature or leave blank for current context]
---

<objective>
Create a sprint plan for $ARGUMENTS (or the current discussion if no arguments provided).

Break a phase or feature into actionable tasks with clear acceptance criteria. Output is ready to execute.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What phase/feature to plan
- Scope boundaries
- Known blockers or dependencies
- Priority level

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If scope unclear:**
- "How much to include in this sprint?" with options: Minimal (core only), Standard (complete feature), Extended (feature + polish), Other

**If granularity unclear:**
- "Preferred task granularity?" with options: Fine (very small tasks), Medium (coherent units), Coarse (larger chunks), Mix, Other

**If blockers unclear:**
- "Any known blockers?" with options: Waiting on decision, Need info from external source, Technical uncertainty to resolve, None known, Other

**If constraints unclear:**
- "Any constraints?" with options: Must integrate with specific system, API/service limitations, None significant, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to create the sprint plan, or would you like me to ask more questions?"

Options:
1. **Create sprint plan** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "What's the most important task?", "Any tasks you want to skip?", "Definition of done for the sprint?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Create sprint plan" → proceed to creating
</decision_gate>

</intake_gate>

<context>
If a project plan exists, reference the relevant phase for scope and dependencies.
</context>

<process>
After intake complete:

1. Clarify the sprint goal (what's "done" for this sprint)
2. Break into tasks (each a coherent unit of work)
3. Define acceptance criteria for each task
4. Identify task dependencies and ordering
5. Flag blockers or questions that need resolving
6. Rate complexity (not time)
</process>

<output_format>
## Sprint Plan: [Phase/Feature Name]

### Strategic Summary
[2-3 sentences: what this sprint delivers, key challenges, what to watch for]

### Sprint Goal
[One sentence describing what's shippable at sprint end]

### Tasks

**1. [Task name]**
- Acceptance criteria:
  - [ ] [Specific, testable criterion]
  - [ ] [Specific, testable criterion]
- Complexity: S/M/L
- Dependencies: none

**2. [Task name]**
- Acceptance criteria:
  - [ ] [Specific, testable criterion]
  - [ ] [Specific, testable criterion]
- Complexity: S/M/L
- Dependencies: [Task 1]

**3. [Task name]**
[Continue pattern...]

### Task Order
```
[1] → [2] → [3]
       ↓
      [4]
```

### Blockers / Questions
- [ ] [Blocker or question that must be resolved]
- [ ] [Blocker or question that must be resolved]

### Definition of Done
- [ ] All acceptance criteria met
- [ ] [Tests passing / builds / deploys / etc.]

### Implementation Context
<claude_context>
<files>
- create: [new files to create with patterns]
- modify: [existing files to modify]
- reference: [files to use as patterns]
</files>
<approach>
- tools: [specific packages, libraries]
- patterns: [coding patterns to follow]
- testing: [how to verify each task]
</approach>
<gotchas>
- [Common mistake to avoid]
- [Edge case to handle]
</gotchas>
</claude_context>

### Execution Plan
<execution>
<order>
1. [Task] - [what it unblocks]
2. [Task] - [what it unblocks]
3. [Task] - [final deliverable]
</order>
<checkpoints>
After task [X]: [what should be verifiable]
After task [Y]: [what should be verifiable]
</checkpoints>
</execution>

**Next Action:** Execute Task 1: [specific task name]
</output_format>

<artifact_output>
Save the sprint plan to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/plans/`

2. Generate filename from topic:
   - Slugify the phase/feature name (lowercase, hyphens for spaces)
   - Format: `[topic]-sprint.md`
   - Example: `auth-flow-sprint.md`

3. Write the complete sprint plan to the file

4. Report to user: "Saved to `artifacts/plans/[filename]`"
</artifact_output>

<success_criteria>
- Tasks are coherent units completable without context loss
- Acceptance criteria are specific and testable
- Dependencies create clear execution order
- Blockers are surfaced upfront
- Sprint goal is achievable and valuable
- Implementation context gives Claude everything needed to start
- Ready to execute immediately
- Output saved to artifacts/plans/ directory
</success_criteria>
