---
description: Research what's been tried before - past attempts, lessons learned
argument-hint: [problem/approach or leave blank for current context]
---

<objective>
Research historical attempts at $ARGUMENTS (or the current topic if no arguments provided).

Find what's been tried before - internally and externally - and extract lessons to avoid repeating mistakes.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- The problem/approach to investigate
- Known past attempts
- How far back to look
- Internal vs external focus

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If scope unclear:**
- "What kind of history?" with options: Industry attempts, Internal past projects, Academic/research, All of the above, Other

**If timeframe unclear:**
- "How far back?" with options: Recent (1-2 years), Medium (3-5 years), Long (5+ years), All time, Other

**If focus unclear:**
- "What do you want to learn?" with options: Why things failed, Success patterns, What's changed since then, All of the above, Other

**If context unclear:**
- "Any known past attempts?" with options: Yes (I'll list them), No (find them), Some internal knowledge, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to research history, or would you like me to ask more questions?"

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

1. Define what problem/approach we're investigating
2. Find past attempts (internal projects, industry examples, academic)
3. For each attempt, document:
   - What they tried
   - What worked
   - What failed and why
   - What's different now
4. Extract patterns and lessons
5. Identify what to adopt and what to avoid
</process>

<output_format>
## History Research: [Problem/Approach]

### Strategic Summary
[2-3 sentences: key historical pattern, main lesson, what's different now]

### What we're investigating
[The problem or approach we want to learn from]

### Past Attempts

**[Attempt 1: Name/Company/Project]**
- **When:** [Timeframe]
- **What they tried:** [Approach]
- **What worked:** [Successes]
- **What failed:** [Failures and root causes]
- **Why:** [Analysis of success/failure factors]

**[Attempt 2: Name/Company/Project]**
[Same structure...]

**[Attempt 3: Name/Company/Project]**
[Same structure...]

### Patterns

**Common success factors:**
- [Factor that correlates with success]
- [Factor that correlates with success]

**Common failure modes:**
- [Why things typically fail]
- [Why things typically fail]

### What's Different Now
- [Technology/market/context change]: [implication]
- [Technology/market/context change]: [implication]

### Lessons to Apply
**Do:**
- [Lesson to adopt]
- [Lesson to adopt]

**Don't:**
- [Mistake to avoid]
- [Mistake to avoid]

**Open question:**
[What we still don't know from history]

### Implementation Context
<claude_context>
<adopt>
- patterns: [successful patterns to follow]
- approaches: [technical approaches that worked]
- validations: [things to validate early based on past failures]
</adopt>
<avoid>
- antipatterns: [approaches that failed repeatedly]
- assumptions: [false assumptions that caused failures]
- shortcuts: [shortcuts that backfired]
</avoid>
<changed>
- now_possible: [things that are feasible now but weren't before]
- still_hard: [things that remain challenging]
- new_risks: [new risks that didn't exist before]
</changed>
</claude_context>

**Next Action:** Apply lessons to planning, research specific aspect deeper, or validate key assumptions
</output_format>

<artifact_output>
Save the research to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/research/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-history.md`
   - Example: `real-time-sync-history.md`

3. Write the complete research to the file

4. Report to user: "Saved to `artifacts/research/[filename]`"
</artifact_output>

<success_criteria>
- Past attempts are relevant (similar problem/context)
- Failure analysis goes to root cause (not surface)
- Lessons are actionable (not just "be careful")
- Acknowledges what's changed since then
- Implementation context gives Claude specific patterns to adopt/avoid
- Informs current approach concretely
- Output saved to artifacts/research/ directory
</success_criteria>
