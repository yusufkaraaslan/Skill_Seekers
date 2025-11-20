---
description: Write technical specification - what to build and how
argument-hint: [feature/project or leave blank for current context]
---

<objective>
Write a technical specification for $ARGUMENTS (or the current topic if no arguments provided).

Define what to build clearly enough that someone could implement it without asking questions.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- Feature/project name
- Problem being solved
- Technical constraints
- Target audience (engineers only, mixed team, etc.)
- Scope boundaries

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If problem unclear:**
- "What problem does this solve?" with options for common problem types + "Other"

**If scope unclear:**
- "What's the scope?" with options: MVP/minimal, Full feature, Platform/infrastructure

**If audience unclear:**
- "Who will read this spec?" with options: Engineers only, Engineers + PM, Mixed stakeholders

**If constraints unclear:**
- "Any technical constraints?" with options: Must integrate with existing system, Greenfield, Performance critical, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to write the spec, or would you like me to ask more questions?"

Options:
1. **Start writing** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated answers, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start writing" → proceed to writing
</decision_gate>

</intake_gate>

<writing_process>
After intake complete:

1. Define the problem and motivation
2. Describe the solution at a high level
3. Detail the technical approach:
   - Architecture/components
   - Data models
   - APIs/interfaces
   - Key algorithms or logic
4. Specify acceptance criteria
5. Note out of scope, risks, and open questions
</writing_process>

<output_format>
## Spec: [Feature/Project Name]

### Overview
**Problem:** [What problem this solves]
**Solution:** [High-level approach in 2-3 sentences]

### Goals
- [Specific goal]
- [Specific goal]

### Non-Goals
- [Explicitly out of scope]

### Technical Design

**Architecture:**
[Components and how they interact]

**Data Model:**
```
[Schema, types, or data structures]
```

**API/Interface:**
```
[Endpoints, function signatures, or protocols]
```

**Key Logic:**
[Important algorithms, business rules, or flows]

### Acceptance Criteria
- [ ] [Testable criterion]
- [ ] [Testable criterion]
- [ ] [Testable criterion]

### Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| [Risk] | [How to address] |

### Open Questions
- [ ] [Decision needed]
- [ ] [Uncertainty to resolve]

### References
- [Related docs, prior art, dependencies]
</output_format>

<artifact_output>
Save the spec to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/writing/`

2. Generate filename from topic:
   - Slugify the feature/topic (lowercase, hyphens for spaces)
   - Format: `[topic]-spec.md`
   - Example: `user-authentication-spec.md`

3. Write the complete spec to the file

4. Report to user: "Saved to `artifacts/writing/[filename]`"
</artifact_output>

<success_criteria>
- Someone could implement without asking clarifying questions
- Technical details are specific (not hand-wavy)
- Acceptance criteria are testable
- Scope is clear (goals AND non-goals)
- Risks are acknowledged with mitigations
- Output saved to artifacts/writing/ directory
</success_criteria>
