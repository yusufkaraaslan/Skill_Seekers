---
description: Write an X/Twitter thread - break down ideas for social
argument-hint: [topic or leave blank for current context]
---

<objective>
Write a thread about $ARGUMENTS (or the current topic if no arguments provided).

Break down an idea into a compelling sequence of tweets. Each tweet stands alone but builds to something larger.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- Core topic/insight
- Tone (educational, spicy, storytelling, personal)
- Goal (teach, persuade, share experience, start conversation)
- Any specific points to include

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If tone unclear:**
- "What tone?" with options: Educational/informative, Spicy/provocative, Personal story, Analytical breakdown, Other

**If goal unclear:**
- "What's the goal?" with options: Teach something, Challenge an assumption, Share an experience, Start a discussion, Other

**If length unclear:**
- "How long?" with options: Short (5-7 tweets), Medium (8-12 tweets), Long (15+ tweets), Other

**If hook unclear:**
- "What's the hook?" with options: Surprising claim, Question, Story opening, Contrarian take, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to write the thread, or would you like me to ask more questions?"

Options:
1. **Start writing** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "What's the most surprising part?", "What evidence do you have?", "What do you want people to do after reading?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start writing" → proceed to writing
</decision_gate>

</intake_gate>

<writing_process>
After intake complete:

1. Identify the core insight or story
2. Hook tweet: make them want to read the rest
3. Break into atomic tweets (one idea each)
4. Each tweet should:
   - Make sense standalone
   - Create curiosity for the next
   - Be under 280 characters
5. End with takeaway or call to action
</writing_process>

<output_format>
**Thread: [Topic]**

---

**1/** [Hook tweet - provocative claim, question, or story opening]

**2/** [Setup or context]

**3/** [First key point]

**4/** [Second key point or example]

**5/** [Third key point or example]

**6/** [Insight or turn]

**7/** [Conclusion or takeaway]

**8/** [Call to action: follow, reply, retweet, link]

---

**Alt hooks:**
- [Alternative opening if first doesn't land]
- [Another angle]
</output_format>

<constraints>
- Hook tweet is everything (80% of success)
- Each tweet < 280 characters
- One idea per tweet
- No tweet should require previous context to make sense
- Don't start with "Thread:" or "🧵" (overplayed)
- Use line breaks within tweets for readability
</constraints>

<artifact_output>
Save the thread to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/writing/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-thread.md`
   - Example: `lessons-from-startup-failure-thread.md`

3. Write the complete thread to the file

4. Report to user: "Saved to `artifacts/writing/[filename]`"
</artifact_output>

<success_criteria>
- Hook stops the scroll
- Each tweet could be screenshot and shared alone
- Thread teaches something or shifts perspective
- Natural flow (not just listicle in tweet form)
- Ending is memorable or actionable
- Output saved to artifacts/writing/ directory
</success_criteria>
