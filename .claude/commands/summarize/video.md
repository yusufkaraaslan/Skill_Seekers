---
description: Summarize YouTube transcript - extract insights, remove filler
argument-hint: [transcript or leave blank for current context]
---

<objective>
Summarize video transcript from $ARGUMENTS (or the current context if no arguments provided).

Extract the actual insights and value. Remove filler, tangents, self-promotion, repetition, and verbal tics.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- Source (video title, channel, URL)
- What to focus on (insights, action items, quotes, data)
- Length preference (detailed vs quick)
- Intended use (reference, share, implement)

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If focus unclear:**
- "What matters most?" with options: Key insights, Actionable takeaways, Specific quotes/data, Everything important, Other

**If length unclear:**
- "How detailed?" with options: Quick overview (1-2 min read), Standard summary, Comprehensive (preserve nuance), Other

**If use unclear:**
- "What will you do with this?" with options: Reference later, Share with someone, Implement/act on it, Just understand it, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to summarize, or would you like me to ask more questions?"

Options:
1. **Start summarizing** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "Any specific sections to focus on?", "Anything to skip entirely?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start summarizing" → proceed to summary
</decision_gate>

</intake_gate>

<process>
1. Identify the core topic and thesis
2. Extract key insights and claims
3. Note any specific examples, data, or evidence
4. Identify actionable takeaways
5. Remove:
   - Filler ("um", "so", "like", "you know")
   - Repetition and restating
   - Self-promotion and calls to action
   - Tangents that don't support main points
   - Padding to hit video length
</process>

<output_format>
## Video Summary

**Main Thesis:**
[One sentence: what this video is actually about]

**Key Insights:**
1. [Insight]: [supporting detail or example]
2. [Insight]: [supporting detail or example]
3. [Insight]: [supporting detail or example]

**Notable Examples/Data:**
- [Specific example, statistic, or evidence worth remembering]

**Actionable Takeaways:**
- [Thing you can do with this information]
- [Thing you can do with this information]

**Skip If:**
[Who this video is NOT useful for]
</output_format>

<artifact_output>
Save the summary to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/summaries/`

2. Generate filename from topic:
   - Slugify the video title/topic (lowercase, hyphens for spaces)
   - Format: `[topic]-video.md`
   - Example: `how-git-works-internally-video.md`

3. Write the complete summary to the file

4. Report to user: "Saved to `artifacts/summaries/[filename]`"
</artifact_output>

<success_criteria>
- Core value extracted (10-20% of original length)
- All filler and fluff removed
- Insights are specific, not vague
- Preserves evidence and examples that matter
- Actionable takeaways are concrete
- Could get 90% of the value without watching
- Output saved to artifacts/summaries/ directory
</success_criteria>
