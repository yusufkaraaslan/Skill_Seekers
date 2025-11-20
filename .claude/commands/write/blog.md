---
description: Write a blog post - share ideas, teach, tell stories
argument-hint: [topic or leave blank for current context]
---

<objective>
Write a blog post about $ARGUMENTS (or the current topic if no arguments provided).

Share something worth reading. Inform, teach, or provoke thought.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- Core topic/idea
- Angle or thesis
- Target audience
- Tone (educational, conversational, provocative, personal)
- Desired length

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If audience unclear:**
- "Who's this for?" with options: General audience, Technical readers, People in specific field, Your existing followers, Other

**If tone unclear:**
- "What tone?" with options: Educational/informative, Conversational/personal, Provocative/challenging, Storytelling, Other

**If angle unclear:**
- "What's the main point?" with options: Here's how to do X, Here's why X matters, Here's what I learned, Here's what's wrong with X, Other

**If length unclear:**
- "How long?" with options: Short (500-800 words), Medium (1000-1500 words), Long-form (2000+ words), Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to write the post, or would you like me to ask more questions?"

Options:
1. **Start writing** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "What's your personal experience with this?", "What's the counterargument?", "What should readers do after reading?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start writing" → proceed to writing
</decision_gate>

</intake_gate>

<writing_process>
After intake complete:

1. Clarify the core idea (one sentence)
2. Identify the hook (why should anyone care?)
3. Structure:
   - Opening: hook + promise
   - Body: deliver on the promise
   - Closing: takeaway + resonance
4. Add specific examples, stories, or evidence
5. Cut everything that doesn't serve the core idea
</writing_process>

<output_format>
# [Title - specific, intriguing, not clickbait]

[Opening hook - make them want to keep reading]

[Thesis/promise - what they'll get from this post]

---

## [Section 1]
[Point with examples or evidence]

## [Section 2]
[Point with examples or evidence]

## [Section 3]
[Point with examples or evidence]

---

[Closing - key takeaway, call to action, or resonant ending]
</output_format>

<constraints>
- Specific examples > abstract claims
- Personal voice (not corporate speak)
- Title is specific and honest (no clickbait)
</constraints>

<artifact_output>
Save the blog post to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/writing/`

2. Generate filename from topic:
   - Slugify the title/topic (lowercase, hyphens for spaces)
   - Format: `[topic]-blog.md`
   - Example: `why-we-switched-to-rust-blog.md`

3. Write the complete blog post to the file

4. Report to user: "Saved to `artifacts/writing/[filename]`"
</artifact_output>

<success_criteria>
- Hook makes reader want to continue
- Core idea is clear and interesting
- Examples make abstract concrete
- Reader takes away something useful or thought-provoking
- You'd actually want to read this
- Output saved to artifacts/writing/ directory
</success_criteria>
