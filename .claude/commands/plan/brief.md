---
description: Create project brief - problem, goals, constraints, success criteria
argument-hint: [idea/goal or leave blank for current context]
---

<objective>
Create a project brief for $ARGUMENTS (or the current discussion if no arguments provided).

Transform a vague idea into a clear problem statement with defined goals, constraints, and success criteria. This becomes the foundation for project planning.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- The idea or goal
- Who it's for
- Known constraints (budget, API limits, external dependencies)
- What sparked this (pain point, opportunity)

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If problem unclear:**
- "What's the core problem?" with options: Pain point to fix, Opportunity to capture, Improvement to existing thing, Exploration/experiment, Other

**If audience unclear:**
- "Who is this for?" with options: Myself, Specific user group, Customers/clients, Public/open source, Other

**If constraints unclear:**
- "Any hard constraints?" with options: Must integrate with existing system, Budget limits for external services, Specific tech requirements, No major constraints, Other

**If scope unclear:**
- "How complex is this?" with options: Small (few components), Medium (multiple systems), Large (significant architecture), Not sure yet, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to create the brief, or would you like me to ask more questions?"

Options:
1. **Create brief** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "What does success look like?", "What's been tried before?", "Any external dependencies?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Create brief" → proceed to creating
</decision_gate>

</intake_gate>

<process>
After intake complete:

1. Clarify the core problem being solved (not the solution)
2. Define who has this problem and why it matters
3. Articulate specific, measurable goals
4. Identify constraints (budget, tech, external dependencies)
5. Define success criteria (how we know we're done)
6. Note open questions that need answering
</process>

<output_format>
## Project Brief: [Name]

### Strategic Summary
[2-3 sentences: the problem, who it affects, why it matters now]

### Problem Statement
[What problem are we solving? For whom? Why does it matter?]

### Goals
- [ ] Goal 1 (measurable)
- [ ] Goal 2 (measurable)
- [ ] Goal 3 (measurable)

### Non-Goals (explicitly out of scope)
- [Thing we're NOT doing]
- [Thing we're NOT doing]

### Constraints
- Technical: [must integrate with X, can't use Y]
- External: [API limits, third-party dependencies]
- Budget: [costs for services, APIs, infrastructure]

### Success Criteria
- [Specific, measurable outcome]
- [Specific, measurable outcome]

### Open Questions
- [ ] [Question that needs answering before/during project]
- [ ] [Question that needs answering before/during project]

### Implementation Context
<claude_context>
<scope>
- complexity: [S/M/L/XL]
- systems: [what systems/components are involved]
- integrations: [external APIs, services]
</scope>
<approach>
- likely_patterns: [architectural approaches that fit]
- existing_code: [relevant existing implementations to reference]
- tech_stack: [languages, frameworks, tools]
</approach>
<risks>
- technical: [what could go wrong technically]
- external: [dependencies on things outside our control]
</risks>
</claude_context>

**Next Action:** Run /plan/project to create full project plan, or /research/feasibility if technical approach is uncertain
</output_format>

<artifact_output>
Save the brief to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/plans/`

2. Generate filename from topic:
   - Slugify the project/topic name (lowercase, hyphens for spaces)
   - Format: `[topic]-brief.md`
   - Example: `user-auth-system-brief.md`

3. Write the complete brief to the file

4. Report to user: "Saved to `artifacts/plans/[filename]`"
</artifact_output>

<success_criteria>
- Problem is clearly stated (not solution-focused)
- Goals are specific and measurable
- Non-goals prevent scope creep
- Constraints are realistic and acknowledged
- Success criteria are unambiguous
- Implementation context gives Claude enough to estimate approach
- Ready to feed into /plan/project
- Output saved to artifacts/plans/ directory
</success_criteria>
