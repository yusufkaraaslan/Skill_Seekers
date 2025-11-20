---
description: Hierarchical bullet point summary
argument-hint: [content or leave blank for current context]
---

<objective>
Summarize $ARGUMENTS (or the current context if no arguments provided) as hierarchical bullet points.

Scannable, structured, easy to reference later.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What content to summarize
- Depth of detail needed
- What to emphasize
- How it will be used

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If depth unclear:**
- "How much detail?" with options: High-level only (main points), Moderate (key supporting details), Comprehensive (all significant points), Other

**If emphasis unclear:**
- "What to emphasize?" with options: Actions/decisions, Concepts/ideas, Facts/data, Structure/relationships, Other

**If use unclear:**
- "How will you use this?" with options: Quick reference, Share with others, Decision support, Learning/understanding, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to create bullet summary, or would you like me to ask more questions?"

Options:
1. **Start summarizing** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "Any sections to skip?", "Specific order preference?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start summarizing" → proceed to summary
</decision_gate>

</intake_gate>

<process>
1. Identify main sections or themes
2. For each section, extract key points
3. Nest supporting details under key points
4. Keep bullets concise (one idea per bullet)
5. Order by importance or logic flow
</process>

<output_format>
## Summary

- **[Main Point 1]**
  - [Supporting detail]
  - [Supporting detail]
    - [Sub-detail if needed]

- **[Main Point 2]**
  - [Supporting detail]
  - [Supporting detail]

- **[Main Point 3]**
  - [Supporting detail]
  - [Supporting detail]
</output_format>

<constraints>
- Bold the main points for scannability
</constraints>

<artifact_output>
Save the summary to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/summaries/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-bullet.md`
   - Example: `meeting-notes-bullet.md`

3. Write the complete summary to the file

4. Report to user: "Saved to `artifacts/summaries/[filename]`"
</artifact_output>

<success_criteria>
- Scannable in 30 seconds
- Hierarchy reflects importance
- Can find specific info quickly
- Captures all key points
- No redundancy
- Output saved to artifacts/summaries/ directory
</success_criteria>
