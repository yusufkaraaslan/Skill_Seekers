---
description: Cut to minimum viable scope - ruthlessly prioritize what ships
argument-hint: [project/feature or leave blank for current context]
---

<objective>
Define MVP scope for $ARGUMENTS (or the current discussion if no arguments provided).

Ruthlessly cut to the smallest thing that delivers value and validates assumptions. Everything else is "later."
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What project/feature to scope
- Core value proposition
- Known must-haves
- What needs to be validated

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If core value unclear:**
- "What's the one thing this must do?" with options: Solve specific pain, Validate assumption, Generate revenue, Get feedback, Other

**If validation goal unclear:**
- "What do you want to learn from MVP?" with options: Will people use it?, Does the tech work?, Is there demand?, Can it integrate properly?, Other

**If cut tolerance unclear:**
- "How ruthless should I be?" with options: Extremely (bare minimum), Moderate (usable but minimal), Light (ship something solid), Other

**If constraints unclear:**
- "Any hard requirements?" with options: Must have specific feature, Must integrate with X, Must handle Y scale, No hard requirements, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to define MVP scope, or would you like me to ask more questions?"

Options:
1. **Define MVP** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "What's absolutely non-negotiable?", "What can be faked for now?", "Who's the first user?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Define MVP" → proceed to creating
</decision_gate>

</intake_gate>

<context>
If a project plan exists, use it as the starting point for cutting.
</context>

<process>
After intake complete:

1. Identify the core value proposition (one sentence)
2. List all planned features/components
3. For each, ask: "Can we ship and learn without this?"
4. Cut everything that isn't essential to core value
5. Identify what can be faked/hardcoded/manual for now
6. Define what "done" looks like for MVP
</process>

<output_format>
## MVP Scope: [Name]

### Strategic Summary
[2-3 sentences: what we're shipping, what we're cutting, what we'll learn]

### Core Value Proposition
[One sentence: what problem does this solve for whom]

### Must Have (ship blocker)
- [Feature/component] - because [why essential to core value]
- [Feature/component] - because [why essential to core value]

### Fake It For Now
- [Thing] - hardcode/mock instead of building
- [Thing] - manual process instead of automation

### Cut (do later)
- [Feature] - why it's not essential for MVP
- [Feature] - why it's not essential for MVP
- [Feature] - why it's not essential for MVP

### MVP Definition of Done
- [ ] [Minimum success criterion]
- [ ] [Minimum success criterion]

### What We'll Learn
[What assumption does this MVP validate? What will we know after shipping?]

### Post-MVP Priority
1. [First thing to add after MVP validates]
2. [Second thing to add]
3. [Third thing to add]

### Implementation Context
<claude_context>
<scope>
- complexity: [S/M/L]
- files: [rough count of files/components]
- integrations: [external services needed for MVP]
</scope>
<approach>
- shortcuts: [acceptable shortcuts for MVP - hardcoded values, manual steps, etc.]
- patterns: [keep it simple patterns to use]
- avoid: [over-engineering to avoid]
</approach>
<fakes>
- [what to mock/hardcode]: [how to fake it]
</fakes>
</claude_context>

### Execution Plan
<execution>
<phases>
1. [Core functionality]
2. [Minimal UI/interface]
3. [Basic integration]
</phases>
<cut_triggers>
If scope creeps, cut in this order:
1. [First thing to cut]
2. [Second thing to cut]
</cut_triggers>
</execution>

**Next Action:** Run /plan/sprint to plan MVP implementation
</output_format>

<artifact_output>
Save the MVP scope to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/plans/`

2. Generate filename from topic:
   - Slugify the project name (lowercase, hyphens for spaces)
   - Format: `[topic]-mvp.md`
   - Example: `sequins-native-mvp.md`

3. Write the complete MVP scope to the file

4. Report to user: "Saved to `artifacts/plans/[filename]`"
</artifact_output>

<success_criteria>
- Scope is genuinely minimal (uncomfortable cuts)
- Core value proposition is preserved
- "Fake it" options reduce complexity significantly
- Cut items have clear "why not now" reasoning
- MVP validates a specific assumption
- Implementation context shows shortcuts Claude should take
- Output saved to artifacts/plans/ directory
</success_criteria>
