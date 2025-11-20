---
description: Compare multiple options side-by-side with recommendation
argument-hint: [what to compare or leave blank for current context]
---

<objective>
Compare options for $ARGUMENTS (or the current topic if no arguments provided).

Structured side-by-side comparison to make an informed decision. Works for tools, approaches, vendors, architectures.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What decision is being made
- Known options to compare
- Decision criteria
- Must-haves vs nice-to-haves

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If criteria unclear:**
- "What matters most?" with options: Simplicity, Performance, Flexibility, Maintenance burden, Let me specify, Other

**If options unclear:**
- "Which options to compare?" with options: I have a list, Find the main contenders, Compare everything, Other

**If weighting unclear:**
- "Any deal-breakers?" with options: Must have specific feature, Must be simple, Must be performant, No deal-breakers, Other

**If constraints unclear:**
- "Any constraints?" with options: Must integrate with existing system, Budget limits, Specific tech requirements, None significant, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to compare options, or would you like me to ask more questions?"

Options:
1. **Start comparison** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start comparison" → proceed to research
</decision_gate>

</intake_gate>

<process>
After intake complete:

1. Define decision criteria (what matters for this choice)
2. List all viable options
3. Evaluate each option against each criterion
4. Weight criteria by importance
5. Make recommendation with reasoning
</process>

<output_format>
## Options Comparison: [Decision]

### Strategic Summary
[2-3 sentences: the options, recommendation, key tradeoff]

### Context
[Brief description of what we're deciding and why it matters]

### Decision Criteria
1. [Criterion] - [why it matters] - Weight: High/Med/Low
2. [Criterion] - [why it matters] - Weight: High/Med/Low
3. [Criterion] - [why it matters] - Weight: High/Med/Low

### Options

**Option A: [Name]**
- [Criterion 1]: [Rating + brief note]
- [Criterion 2]: [Rating + brief note]
- [Criterion 3]: [Rating + brief note]
- **Score: X/10**

**Option B: [Name]**
- [Criterion 1]: [Rating + brief note]
- [Criterion 2]: [Rating + brief note]
- [Criterion 3]: [Rating + brief note]
- **Score: X/10**

**Option C: [Name]**
[Same structure...]

### Comparison Matrix
| Criterion | Option A | Option B | Option C |
|-----------|----------|----------|----------|
| [Criterion 1] | Good/OK/Poor | | |
| [Criterion 2] | Good/OK/Poor | | |
| [Criterion 3] | Good/OK/Poor | | |

### Recommendation
[Option X] because [reasoning tied to weighted criteria]

### Runner-up
[Option Y] - choose this if [specific condition]

### Implementation Context
<claude_context>
<chosen>
- option: [chosen option name]
- install: [how to install/set up]
- config: [configuration needed]
- patterns: [usage patterns]
- docs: [documentation reference]
</chosen>
<runner_up>
- option: [runner-up name]
- when: [conditions where this becomes better choice]
- switch_cost: [effort to switch later if needed]
</runner_up>
<integration>
- existing_code: [how it fits with current codebase]
- gotchas: [common issues with this option]
- testing: [how to verify it works]
</integration>
</claude_context>

**Next Action:** Implement chosen option, prototype to validate, or gather more info on specific option
</output_format>

<artifact_output>
Save the research to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/research/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-options.md`
   - Example: `auth-providers-options.md`

3. Write the complete research to the file

4. Report to user: "Saved to `artifacts/research/[filename]`"
</artifact_output>

<success_criteria>
- Criteria reflect what actually matters for this decision
- Options are genuinely comparable (apples to apples)
- Ratings are justified, not arbitrary
- Recommendation follows from analysis
- Runner-up provides contingency
- Implementation context gives Claude everything needed to proceed
- Output saved to artifacts/research/ directory
</success_criteria>
