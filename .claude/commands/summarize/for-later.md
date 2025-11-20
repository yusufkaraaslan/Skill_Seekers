---
description: Capture enough context to reconstruct understanding later
argument-hint: [content or leave blank for current context]
---

<objective>
Summarize $ARGUMENTS (or the current context if no arguments provided) for future reference.

Capture enough that you can reconstruct the context weeks or months later without re-reading the original.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What content to save
- Why it's being saved
- What it connects to
- Future use case

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If purpose unclear:**
- "What will you use this for later?" with options: Reference for a project, Follow up on an idea, Share with someone, Possible future action, Other

**If connection unclear:**
- "What does this relate to?" with options: Current project, Ongoing interest, Future goal, General knowledge, Other

**If time horizon unclear:**
- "When will you need this?" with options: Within a week, Within a month, Months from now, Indefinite future, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to capture for later, or would you like me to ask more questions?"

Options:
1. **Start capturing** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "Any specific details critical to preserve?", "Tags you'd want to find this by?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start capturing" → proceed to summary
</decision_gate>

</intake_gate>

<process>
1. Identify what you'll need to remember
2. Capture:
   - What this is about (topic, source)
   - Why it mattered (relevance to you)
   - Key insights (the actual value)
   - Specific references (quotes, links, page numbers)
   - Open questions or follow-ups
3. Write as if for yourself in 6 months who forgot everything
</process>

<output_format>
## For Later: [Topic]

**Source:** [Where this came from, date accessed]

**What this is:**
[One sentence description]

**Why I saved this:**
[Relevance to current projects, interests, or questions]

**Key Insights:**
- [Insight worth remembering]
- [Insight worth remembering]
- [Insight worth remembering]

**Specific References:**
- [Quote, data point, or specific claim with location]
- [Quote, data point, or specific claim with location]

**Related To:**
- [Other topics, projects, or saved items this connects to]

**Follow-up:**
- [ ] [Question to explore later]
- [ ] [Action to take]

**Tags:** [topic], [topic], [topic]
</output_format>

<artifact_output>
Save the summary to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/summaries/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-for-later.md`
   - Example: `interesting-paper-on-llms-for-later.md`

3. Write the complete summary to the file

4. Report to user: "Saved to `artifacts/summaries/[filename]`"
</artifact_output>

<success_criteria>
- Future you can understand without original source
- "Why I saved this" triggers memory of relevance
- Specific references can be cited or found
- Follow-ups are actionable
- Tags enable rediscovery
- Output saved to artifacts/summaries/ directory
</success_criteria>
