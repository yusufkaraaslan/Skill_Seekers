---
description: Progressive disclosure - surface to deep
argument-hint: [concept or leave blank for current context]
---

<objective>
Explain $ARGUMENTS (or the current topic if no arguments provided) in progressive layers of depth.

Start simple, add complexity. Reader can stop at any layer and have a complete (if simplified) understanding.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What concept to explain
- How many layers needed
- Target audience for each layer
- What the explanation is for

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If depth unclear:**
- "How many layers?" with options: 2 layers (simple + detailed), 3 layers (simple + working + deep), 4 layers (full progression), Other

**If audience unclear:**
- "Who's the main audience?" with options: Complete beginners, Technical people in adjacent field, Practitioners wanting depth, Mixed audience, Other

**If purpose unclear:**
- "What's this for?" with options: Teaching/onboarding, Documentation, Personal understanding, Explaining to different stakeholders, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to create layered explanation, or would you like me to ask more questions?"

Options:
1. **Start layering** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start layering" → proceed
</decision_gate>

</intake_gate>

<process>
1. Identify the concept to explain
2. Create 3-4 layers of increasing depth:
   - Layer 1: One-sentence essence (anyone can understand)
   - Layer 2: Key mechanism (how it works)
   - Layer 3: Nuances and edge cases
   - Layer 4: Expert-level details and implications
3. Each layer should be complete on its own
4. Later layers add detail, not contradict earlier ones
</process>

<output_format>
## [Topic] in Layers

**Layer 1 - The essence (10 seconds):**
[One sentence anyone can understand]

**Layer 2 - How it works (1 minute):**
[Key mechanism, main components, basic flow]

**Layer 3 - Nuances (5 minutes):**
[Important exceptions, edge cases, common variations, tradeoffs]

**Layer 4 - Deep dive (for experts):**
[Technical details, advanced implications, connections to other concepts, current debates]

**Stop here if:**
- Layer 1: You just need to know what it is
- Layer 2: You need to work with it at a basic level
- Layer 3: You need to make decisions about it
- Layer 4: You need to master or teach it
</output_format>

<constraints>
- Each layer must stand alone as complete
- Later layers add detail, don't contradict
- Layer 1 must be genuinely simple (no jargon)
- Don't frontload complexity - earn it
</constraints>

<success_criteria>
- Reader can stop at any layer with useful understanding
- Complexity increases smoothly between layers
- No layer requires knowledge from a later layer
- Expert finds value in Layer 4, novice isn't lost at Layer 1
</success_criteria>
