---
description: Extract best quotes verbatim - key statements worth preserving exactly
argument-hint: [content or leave blank for current context]
---

<objective>
Extract the best quotes from $ARGUMENTS (or the current context if no arguments provided).

Pull statements worth preserving verbatim - insights, memorable phrases, key claims in the author's own words.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What content to extract from
- What kind of quotes (insights, data, memorable, controversial)
- How many quotes wanted
- How they'll be used

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If quote type unclear:**
- "What kind of quotes?" with options: Core insights/claims, Specific data/evidence, Memorable phrasing, Controversial/surprising, Other

**If quantity unclear:**
- "How many quotes?" with options: Just the best 3-5, Moderate collection (5-10), Comprehensive (all notable), Other

**If use unclear:**
- "What will you use these for?" with options: Citation in my work, Share with others, Personal reference, Support an argument, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to extract quotes, or would you like me to ask more questions?"

Options:
1. **Start extracting** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "Any specific topics to focus on?", "Any speakers to prioritize?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start extracting" → proceed to extraction
</decision_gate>

</intake_gate>

<process>
1. Identify statements that are:
   - Particularly well-phrased
   - Core claims or insights
   - Memorable or quotable
   - Evidence or specific data
2. Extract verbatim (exact wording)
3. Add brief context for why each quote matters
4. Organize by theme or importance
</process>

<output_format>
## Key Quotes

**On [Theme 1]:**

> "[Exact quote]"

Why it matters: [Brief context]

> "[Exact quote]"

Why it matters: [Brief context]

**On [Theme 2]:**

> "[Exact quote]"

Why it matters: [Brief context]

**Most Important Quote:**

> "[The single most significant quote]"

[Why this is the one to remember]
</output_format>

<constraints>
- Quotes must be verbatim (exact wording)
- Include enough context to understand standalone
- Don't over-extract (quality over quantity)
- Mark any edits with [...] or [word]
</constraints>

<artifact_output>
Save the summary to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/summaries/`

2. Generate filename from topic:
   - Slugify the source/topic (lowercase, hyphens for spaces)
   - Format: `[topic]-quotes.md`
   - Example: `paul-graham-essays-quotes.md`

3. Write the complete summary to the file

4. Report to user: "Saved to `artifacts/summaries/[filename]`"
</artifact_output>

<success_criteria>
- Quotes are exact (not paraphrased)
- Each quote earns its place (not filler)
- Context makes quotes useful standalone
- Best quote is genuinely the best
- Could cite these directly
- Output saved to artifacts/summaries/ directory
</success_criteria>
