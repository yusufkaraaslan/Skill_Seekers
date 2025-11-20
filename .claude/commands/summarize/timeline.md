---
description: Chronological timeline of events
argument-hint: [content or leave blank for current context]
---

<objective>
Extract timeline from $ARGUMENTS (or the current context if no arguments provided).

Chronological sequence of events with dates/times when available. Shows what happened when.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What content to extract timeline from
- Time granularity (days, weeks, years)
- What to include (just events, or context/causes)
- Focus period

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If granularity unclear:**
- "What granularity?" with options: High-level phases/eras, Key milestones, Detailed events, Day-by-day where available, Other

**If scope unclear:**
- "What to include?" with options: Just events/facts, Events + causes, Events + consequences, Full context, Other

**If period unclear:**
- "Any time period to focus on?" with options: Entire timespan, Recent events, Beginning/origins, Key transition period, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to create timeline, or would you like me to ask more questions?"

Options:
1. **Start creating timeline** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "Any events to highlight?", "Specific people/entities to track?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start creating timeline" → proceed to timeline
</decision_gate>

</intake_gate>

<process>
1. Identify all events mentioned
2. Determine temporal order (dates, times, sequence words)
3. Note duration and gaps between events
4. Identify cause-and-effect relationships
5. Mark uncertain timing
</process>

<output_format>
## Timeline: [Topic]

**[Date/Time or Period 1]**
- [Event]: [Brief description and significance]

**[Date/Time or Period 2]**
- [Event]: [Brief description and significance]

**[Date/Time or Period 3]**
- [Event]: [Brief description and significance]
- [Related event]: [Brief description]

**[Date/Time or Period 4]**
- [Event]: [Brief description and significance]

---

**Key Inflection Points:**
- [Event that changed trajectory]
- [Event that changed trajectory]

**Gaps/Unknowns:**
- [Period with missing information]
</output_format>

<constraints>
- Strict chronological order
- Mark uncertain dates with ~ or "circa"
- Note gaps in timeline
- Include cause-effect where clear
</constraints>

<artifact_output>
Save the summary to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/summaries/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-timeline.md`
   - Example: `company-founding-timeline.md`

3. Write the complete summary to the file

4. Report to user: "Saved to `artifacts/summaries/[filename]`"
</artifact_output>

<success_criteria>
- Events in correct temporal order
- Dates/times included when known
- Cause-effect relationships clear
- Gaps acknowledged
- Shows the "story" of what happened
- Output saved to artifacts/summaries/ directory
</success_criteria>
