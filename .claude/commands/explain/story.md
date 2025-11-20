---
description: Explain as narrative - characters, conflict, resolution
argument-hint: [concept or leave blank for current context]
---

<objective>
Explain $ARGUMENTS (or the current topic if no arguments provided) as a story.

Narrative is how humans naturally understand the world. Give the concept characters, conflict, stakes, and resolution.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What concept to explain via story
- What kind of story (historical, hypothetical, metaphorical)
- Tone (serious, playful, dramatic)
- Length/detail level

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If story type unclear:**
- "What kind of story?" with options: Historical (real events), Hypothetical scenario, Metaphorical/allegorical, Whatever fits best, Other

**If tone unclear:**
- "What tone?" with options: Serious/dramatic, Light/playful, Matter-of-fact, Epic/sweeping, Other

**If length unclear:**
- "How long?" with options: Brief (paragraph), Medium (page), Extended (full narrative), Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to tell the story, or would you like me to ask more questions?"

Options:
1. **Start storytelling** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start storytelling" → proceed
</decision_gate>

</intake_gate>

<process>
1. Identify the concept to explain
2. Find the narrative elements:
   - Character(s): Who or what is the protagonist?
   - Setting: What's the context/world?
   - Conflict: What problem or tension exists?
   - Stakes: Why does it matter?
   - Resolution: How does it resolve?
3. Tell the story with these elements
4. Extract the lesson/insight at the end
</process>

<output_format>
**[Title: evocative name for the story]**

*Setting:*
[The world/context where this takes place]

*The character:*
[Who/what this is about - can be a person, object, idea, or force]

*The problem:*
[What conflict or challenge they face]

*What's at stake:*
[Why it matters, what could be lost]

*The journey:*
[How they attempt to solve it, what happens]

*The resolution:*
[How it ends - success, failure, transformation, or ongoing]

**The insight:**
[What this story teaches us about the concept]

**Why this story structure:**
[What the narrative reveals that straight explanation wouldn't]
</output_format>

<constraints>
- Must have genuine narrative arc (not just description with characters)
- Conflict must be real and meaningful
- Story must actually illuminate the concept (not just decorate it)
- Can be historical, hypothetical, or metaphorical
</constraints>

<success_criteria>
- Reader remembers the story
- Narrative makes abstract concept concrete
- Emotional stakes make it stick
- Insight emerges naturally from the story
</success_criteria>
