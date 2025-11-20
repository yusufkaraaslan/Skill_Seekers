---
description: Create full project plan - phases, milestones, dependencies, risks
argument-hint: [project or leave blank for current context]
---

<objective>
Create a project plan for $ARGUMENTS (or the current discussion if no arguments provided).

Break down a project into phases with clear milestones, dependencies, and risks. Each phase becomes a candidate for sprint planning.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- Project name/description
- Goals and constraints (from brief or stated)
- Known dependencies (external APIs, other systems)
- Priority level

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If complexity unclear:**
- "How complex is this project?" with options: Small (few components), Medium (multiple systems), Large (significant architecture), XL (major initiative), Other

**If dependencies unclear:**
- "Any external dependencies?" with options: External APIs/services, Other projects must complete first, Decisions/approvals needed, Nothing external, Other

**If risk tolerance unclear:**
- "How should I approach risks?" with options: Conservative (mitigate everything), Balanced, Aggressive (move fast), Other

**If constraints unclear:**
- "Any hard constraints?" with options: Must use specific tech, Must integrate with existing system, Budget limits, No major constraints, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to create the project plan, or would you like me to ask more questions?"

Options:
1. **Create plan** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "Any phases that must happen in order?", "What's the riskiest part?", "Any milestones already committed?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Create plan" → proceed to creating
</decision_gate>

</intake_gate>

<context>
If a project brief exists, reference it for goals, constraints, and success criteria.
</context>

<process>
After intake complete:

1. Review project goals and constraints (from brief or discussion)
2. Identify major phases (logical chunks of work)
3. Define milestones for each phase (what "done" looks like)
4. Map dependencies between phases
5. Identify risks and mitigation strategies
6. Note decision points and unknowns
</process>

<output_format>
## Project Plan: [Name]

### Strategic Summary
[2-3 sentences: what we're building, the approach, key dependencies or risks]

### Overview
[1-2 sentence summary of what we're building and why]

### Phases

**Phase 1: [Name]**
- Milestone: [What's done when this phase completes]
- Key deliverables:
  - [Deliverable 1]
  - [Deliverable 2]
- Dependencies: [What must exist before starting]
- Complexity: S/M/L

**Phase 2: [Name]**
- Milestone: [What's done when this phase completes]
- Key deliverables:
  - [Deliverable 1]
  - [Deliverable 2]
- Dependencies: [Phase 1, external dependency, etc.]
- Complexity: S/M/L

**Phase 3: [Name]**
[Continue pattern...]

### Dependencies
```
Phase 1 → Phase 2 → Phase 3
              ↓
          Phase 4
```

### Risks
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| [Risk] | High/Med/Low | High/Med/Low | [Strategy] |

### Decision Points
- [ ] [Decision needed] - by [phase]
- [ ] [Decision needed] - by [phase]

### Implementation Context
<claude_context>
<architecture>
- pattern: [overall architectural approach]
- systems: [major components/services]
- data: [data storage, flow]
</architecture>
<tech_stack>
- languages: [primary languages]
- frameworks: [key frameworks]
- services: [external services/APIs]
</tech_stack>
<files>
- structure: [high-level file/folder organization]
- reference: [existing code to use as patterns]
</files>
<risks>
- technical: [what could block progress]
- mitigation: [how to address if it happens]
</risks>
</claude_context>

### Execution Plan
<execution>
<order>
Phase 1 → Phase 2 → Phase 3
</order>
<critical_path>
[Which phases are on the critical path - delays here delay everything]
</critical_path>
<parallel>
[Phases that can run in parallel, if any]
</parallel>
</execution>

**Next Action:** Run /plan/sprint for Phase 1, or /plan/mvp to cut scope first
</output_format>

<artifact_output>
Save the project plan to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/plans/`

2. Generate filename from topic:
   - Slugify the project name (lowercase, hyphens for spaces)
   - Format: `[topic]-project.md`
   - Example: `user-auth-system-project.md`

3. Write the complete project plan to the file

4. Report to user: "Saved to `artifacts/plans/[filename]`"
</artifact_output>

<success_criteria>
- Phases are logical, sequential chunks
- Each phase has clear "done" milestone
- Dependencies are explicit
- Risks are identified with mitigations
- Phases are sized appropriately for sprint planning
- Implementation context gives Claude architectural direction
- Ready to feed into /plan/sprint or /plan/mvp
- Output saved to artifacts/plans/ directory
</success_criteria>
