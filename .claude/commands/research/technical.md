---
description: Research how to implement something - approaches, libraries, tradeoffs
argument-hint: [what to implement or leave blank for current context]
---

<objective>
Research technical implementation approaches for $ARGUMENTS (or the current topic if no arguments provided).

Find concrete ways to build it - libraries, patterns, architectures - with honest tradeoffs for each.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What needs to be built
- Known constraints (must use X, can't use Y)
- Performance requirements
- Integration requirements

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If constraints unclear:**
- "Any technical constraints?" with options: Must use specific language/framework, Must integrate with existing system, Performance critical, No major constraints, Other

**If priorities unclear:**
- "What matters most?" with options: Simplicity/speed to build, Performance, Long-term maintainability, Flexibility, Other

**If scope unclear:**
- "How comprehensive?" with options: Quick overview (2-3 options), Thorough analysis (4-5 options), Deep dive on best options, Other

**If complexity unclear:**
- "How complex is this?" with options: Simple (straightforward implementation), Medium (some coordination), Complex (significant architecture), Not sure, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to research implementation approaches, or would you like me to ask more questions?"

Options:
1. **Start research** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start research" → proceed to research
</decision_gate>

</intake_gate>

<process>
After intake complete:

1. Clarify what needs to be built and constraints
2. Identify 2-4 viable implementation approaches
3. For each approach, research:
   - How it works
   - Libraries/tools involved
   - Complexity
   - Performance characteristics
   - Community/maintenance status
4. Compare tradeoffs honestly
5. Make a recommendation based on context
</process>

<output_format>
## Technical Research: [Topic]

### Strategic Summary
[2-3 sentences: the approaches, recommendation, key tradeoff]

### Requirements
- [Key requirement/constraint]
- [Key requirement/constraint]

### Approach 1: [Name]
**How it works:** [Brief explanation]
**Libraries/tools:** [Specific packages, versions]
**Pros:**
- [Advantage]
- [Advantage]
**Cons:**
- [Disadvantage]
- [Disadvantage]
**Best when:** [Use case fit]
**Complexity:** S/M/L

### Approach 2: [Name]
[Same structure...]

### Approach 3: [Name]
[Same structure...]

### Comparison
| Aspect | Approach 1 | Approach 2 | Approach 3 |
|--------|------------|------------|------------|
| Complexity | S/M/L | | |
| Performance | Good/OK/Poor | | |
| Maintainability | Good/OK/Poor | | |

### Recommendation
[Which approach and why, given the specific context]

### Implementation Context
<claude_context>
<chosen_approach>
- name: [approach name]
- libraries: [specific packages with versions]
- install: [installation commands]
</chosen_approach>
<architecture>
- pattern: [architectural pattern to follow]
- components: [main components to build]
- data_flow: [how data moves through system]
</architecture>
<files>
- create: [files to create with patterns]
- structure: [folder organization]
- reference: [existing code to use as patterns]
</files>
<implementation>
- start_with: [first thing to build]
- order: [implementation order]
- gotchas: [common mistakes, edge cases]
- testing: [how to test each component]
</implementation>
</claude_context>

**Next Action:** Prototype chosen approach, deeper research on specific aspect, or run /plan/sprint
</output_format>

<artifact_output>
Save the research to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/research/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-technical.md`
   - Example: `websocket-implementation-technical.md`

3. Write the complete research to the file

4. Report to user: "Saved to `artifacts/research/[filename]`"
</artifact_output>

<success_criteria>
- Approaches are genuinely different (not variations of same thing)
- Tradeoffs are honest, not salesy
- Libraries are specific and current
- Recommendation fits the stated constraints
- Implementation context has everything Claude needs to start building
- Enough detail to begin implementing immediately
- Output saved to artifacts/research/ directory
</success_criteria>
