---
description: Write a personal reflection - process experiences and extract lessons
argument-hint: [experience/topic or leave blank for current context]
---

<objective>
Write a reflection on $ARGUMENTS (or the current topic if no arguments provided).

Process an experience, project, or period to extract lessons and meaning. For yourself, possibly to share.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What experience/topic to reflect on
- Timeframe or scope
- Whether it's for private processing or sharing
- Initial feelings or outcomes

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If scope unclear:**
- "What are you reflecting on?" with options: Specific project, Time period, Decision I made, Experience/event, Other

**If purpose unclear:**
- "Is this for sharing?" with options: Just for me (private processing), Might share later, Definitely sharing (blog/post), Other

**If depth unclear:**
- "How deep?" with options: Quick capture, Thorough analysis, Deep excavation, Other

**If outcome unclear:**
- "How did it go?" with options: Went well overall, Mixed results, Didn't go as planned, Still processing, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to write the reflection, or would you like me to ask more questions?"

Options:
1. **Start writing** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "What surprised you most?", "What would you do differently?", "What are you still uncertain about?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start writing" → proceed to writing
</decision_gate>

</intake_gate>

<writing_process>
After intake complete:

1. Describe what happened (facts, not judgments)
2. Explore how you felt and why
3. Identify what worked and what didn't
4. Extract lessons and insights
5. Consider what you'd do differently
6. Note what this means going forward
</writing_process>

<output_format>
## Reflection: [Topic/Experience]

**What happened:**
[Factual description of the experience or situation]

**How it felt:**
[Honest emotional response - what surprised you, challenged you, energized you]

**What worked:**
- [Thing that went well]: [why]
- [Thing that went well]: [why]

**What didn't:**
- [Thing that didn't work]: [why, and what you learned]
- [Thing that didn't work]: [why, and what you learned]

**Key insights:**
- [Lesson or realization]
- [Lesson or realization]

**What I'd do differently:**
- [Change]: [why]

**Going forward:**
[How this changes your thinking or behavior]
</output_format>

<constraints>
- Honest, not performative
- Specific examples, not vague feelings
- Lessons are actionable, not just "try harder"
- Distinguish between external factors and your choices
</constraints>

<artifact_output>
Save the reflection to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/writing/`

2. Generate filename from topic:
   - Slugify the subject (lowercase, hyphens for spaces)
   - Format: `[topic]-reflection.md`
   - Example: `first-year-freelancing-reflection.md`

3. Write the complete reflection to the file

4. Report to user: "Saved to `artifacts/writing/[filename]`"
</artifact_output>

<success_criteria>
- Clearly articulates what happened
- Honest about feelings and failures
- Extracts specific, actionable lessons
- Shows growth or changed perspective
- Useful to future you (or others)
- Output saved to artifacts/writing/ directory
</success_criteria>
