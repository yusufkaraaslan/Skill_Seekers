---
description: Extract 5-7 most important points, ranked by significance
argument-hint: [content or leave blank for current context]
---

<objective>
Extract key points from $ARGUMENTS (or the current context if no arguments provided).

5-7 most important points, ranked from most to least significant. Quality over quantity.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What content to extract from
- Criteria for "key" (impact, novelty, actionability)
- How many points wanted
- What the points will be used for

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If criteria unclear:**
- "What makes a point 'key'?" with options: High impact, Surprising/novel, Actionable, Most evidence-backed, Other

**If count unclear:**
- "How many points?" with options: Just top 3, Standard 5-7, Up to 10, Other

**If use unclear:**
- "What will you do with these?" with options: Make a decision, Share key findings, Guide further reading, Personal reference, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to extract key points, or would you like me to ask more questions?"

Options:
1. **Start extracting** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "Any topics to prioritize?", "Anything to exclude?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start extracting" → proceed to extraction
</decision_gate>

</intake_gate>

<process>
1. Read/review entire content
2. Identify all candidate points
3. Rank by:
   - Impact (how much does this matter?)
   - Novelty (is this new/surprising?)
   - Actionability (can you do something with it?)
4. Select top 5-7
5. Order from most to least important
</process>

<output_format>
## Key Points

1. **[Most important point]**
   [One sentence of context or evidence]

2. **[Second most important]**
   [One sentence of context or evidence]

3. **[Third most important]**
   [One sentence of context or evidence]

4. **[Fourth point]**
   [One sentence of context or evidence]

5. **[Fifth point]**
   [One sentence of context or evidence]

[6-7 if warranted]

**Notable omission:**
[Important thing NOT in the source that you'd expect]
</output_format>

<artifact_output>
Save the summary to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/summaries/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-key-points.md`
   - Example: `strategy-presentation-key-points.md`

3. Write the complete summary to the file

4. Report to user: "Saved to `artifacts/summaries/[filename]`"
</artifact_output>

<success_criteria>
- 5-7 points maximum (ruthlessly prioritized)
- Ranked by actual importance, not order in source
- Each point is substantive (not obvious/generic)
- Context makes point useful standalone
- Notable omissions surface gaps
- Output saved to artifacts/summaries/ directory
</success_criteria>
