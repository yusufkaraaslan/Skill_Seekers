---
description: Summarize as if teaching the concept - build understanding
argument-hint: [content or leave blank for current context]
---

<objective>
Summarize $ARGUMENTS (or the current context if no arguments provided) as if teaching the concept.

Transform information into understanding. Build from foundations, connect to familiar concepts, make it stick.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What content/concept to learn
- Current knowledge level
- How deep to go
- What familiar domains to connect to

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If knowledge level unclear:**
- "What's your starting point?" with options: Complete beginner, Some familiarity, Intermediate (know basics), Just need specifics filled in, Other

**If depth unclear:**
- "How deep should we go?" with options: Just the core concept, Solid working understanding, Deep enough to explain to others, Comprehensive mastery, Other

**If connection unclear:**
- "What domains are you familiar with?" with options: Software/tech, Business/finance, Science, Everyday analogies, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to create learning summary, or would you like me to ask more questions?"

Options:
1. **Start teaching** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "Any specific aspects to focus on?", "Misconceptions you want cleared up?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start teaching" → proceed to learning summary
</decision_gate>

</intake_gate>

<process>
1. Identify the core concept being taught
2. Find prerequisite knowledge needed
3. Build explanation from simple to complex:
   - Start with "why this matters"
   - Connect to familiar concepts
   - Introduce terminology with definitions
   - Layer in complexity gradually
4. Include examples that illuminate
5. End with "you now understand X"
</process>

<output_format>
## Learning Summary: [Concept]

**Why this matters:**
[Motivation - why should I care about this?]

**Prerequisites:**
[What you need to know first, or "none"]

**Core Concept:**
[Fundamental idea in simple terms, connected to familiar concepts]

**Key Terms:**
- **[Term]**: [Plain language definition]
- **[Term]**: [Plain language definition]

**How it works:**
[Step-by-step explanation building complexity]

**Example:**
[Concrete example that makes it click]

**Common Misconceptions:**
- [Wrong assumption]: [Correction]

**Now you understand:**
[One sentence confirming what they learned and can now do]
</output_format>

<artifact_output>
Save the summary to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/summaries/`

2. Generate filename from topic:
   - Slugify the concept/topic (lowercase, hyphens for spaces)
   - Format: `[topic]-teach-me.md`
   - Example: `distributed-consensus-teach-me.md`

3. Write the complete summary to the file

4. Report to user: "Saved to `artifacts/summaries/[filename]`"
</artifact_output>

<success_criteria>
- Starts with "why" not "what"
- Builds from simple to complex
- Technical terms defined when introduced
- Example makes abstract concrete
- Learner could explain it to someone else
- Output saved to artifacts/summaries/ directory
</success_criteria>
