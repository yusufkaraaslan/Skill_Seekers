---
description: TL;DR - 2-3 sentences maximum
argument-hint: [content or leave blank for current context]
---

<objective>
Create TL;DR of $ARGUMENTS (or the current context if no arguments provided).

Maximum 2-3 sentences. Capture the essence someone needs to decide if they should read more.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What content to summarize
- Who it's for (self, sharing)
- What aspect to emphasize

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 1-2 questions based on actual gaps:

**If audience unclear:**
- "For who?" with options: Myself (quick reference), Someone else (share), Decision-maker (sell them), Other

**If emphasis unclear:**
- "What to emphasize?" with options: The main point, Why it matters, What to do about it, Other

Skip questions where $ARGUMENTS already provides the answer. TL;DR is intentionally minimal - don't over-ask.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to create TL;DR, or need to clarify something?"

Options:
1. **Create TL;DR** - I have enough context
2. **Ask more questions** - There's something to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 1-2 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Create TL;DR" → proceed
</decision_gate>

</intake_gate>

<process>
1. Identify the single most important point
2. Add critical context (who, what, why)
3. Include the "so what" - why it matters
4. Cut everything else
</process>

<output_format>
**TL;DR:**
[2-3 sentences maximum. No bullet points. Just the essence.]
</output_format>

<constraints>
- Maximum 3 sentences
- No bullet points
- No hedging ("it seems", "arguably")
- No meta-commentary ("this document discusses")
- Must stand alone without additional context
</constraints>

<artifact_output>
Save the summary to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/summaries/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-tldr.md`
   - Example: `quarterly-report-tldr.md`

3. Write the complete summary to the file

4. Report to user: "Saved to `artifacts/summaries/[filename]`"
</artifact_output>

<success_criteria>
- Someone could decide whether to read more based on this
- Captures the actual point, not just the topic
- 3 sentences or fewer
- No filler words
- Output saved to artifacts/summaries/ directory
</success_criteria>
