---
description: Write a quick pitch - explain your thing compellingly
argument-hint: [project/idea or leave blank for current context]
---

<objective>
Write a pitch for $ARGUMENTS (or the current topic if no arguments provided).

Explain your thing clearly and compellingly. Make them want to know more.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What you're pitching (project, product, idea, yourself)
- Target audience
- Context (cold intro, warm intro, presentation, written)
- What you want from them

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If audience unclear:**
- "Who are you pitching to?" with options: Potential user/customer, Investor/funder, Collaborator/partner, Employer, Other

**If context unclear:**
- "What's the context?" with options: Cold intro (never met), Warm intro (mutual connection), Presentation/demo, Written (email/message), Other

**If ask unclear:**
- "What do you want from them?" with options: Try it out, Meeting/call, Investment/funding, Collaboration, Other

**If differentiator unclear:**
- "What makes this different?" with options: Novel approach, Better execution, Unique access/insight, Specific niche focus, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to write the pitch, or would you like me to ask more questions?"

Options:
1. **Start writing** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "What's their likely objection?", "What proof points do you have?", "What's the urgency?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start writing" → proceed to writing
</decision_gate>

</intake_gate>

<writing_process>
After intake complete:

1. Identify the audience (who are you pitching to?)
2. Structure:
   - Problem: What pain exists?
   - Solution: What do you do about it?
   - How: What's the approach/mechanism?
   - Why you: What's your unfair advantage?
   - Ask: What do you want from them?
3. Cut to absolute minimum
4. Make it conversational, not corporate
</writing_process>

<output_format>
## Pitch: [Project/Idea]

**For:** [Target audience]

---

**The pitch:**

[Problem - one sentence pain point]

[Solution - what you built/do]

[How it works - one sentence mechanism]

[Why it's different - your edge]

[Ask - what you want]

---

**Even shorter (one sentence):**
[Entire pitch in one sentence]

**Tagline:**
[Memorable phrase that captures it]
</output_format>

<constraints>
- No jargon
- Specific problem, not vague category
- "Why you" must be defensible
- Ask must be specific and reasonable
</constraints>

<artifact_output>
Save the pitch to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/writing/`

2. Generate filename from topic:
   - Slugify the product/idea (lowercase, hyphens for spaces)
   - Format: `[topic]-pitch.md`
   - Example: `sequins-native-app-pitch.md`

3. Write the complete pitch to the file

4. Report to user: "Saved to `artifacts/writing/[filename]`"
</artifact_output>

<success_criteria>
- Anyone can understand it (no domain knowledge required)
- Creates genuine curiosity
- Problem resonates with audience
- Differentiation is clear and believable
- They know exactly what you want from them
- Output saved to artifacts/writing/ directory
</success_criteria>
