---
description: Draw out consequences - "if this is true, then..."
argument-hint: [concept or leave blank for current context]
---

<objective>
Explain $ARGUMENTS (or the current topic if no arguments provided) by drawing out its implications.

Most explanations stop too early. This one asks: if this is true, what else must be true? What follows from this?
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What concept/claim to analyze
- How many levels deep (first-order, second-order, etc.)
- Domain to focus implications on
- What to do with the implications

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If depth unclear:**
- "How deep should we trace?" with options: First-order only (direct), Second-order (consequences of consequences), As deep as it goes, Other

**If domain unclear:**
- "What domain to focus on?" with options: Personal/individual, Professional/work, Societal/broad, All domains, Other

**If purpose unclear:**
- "What will you do with this?" with options: Make a decision, Challenge an assumption, Understand fully, Persuade someone, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to trace implications, or would you like me to ask more questions?"

Options:
1. **Start tracing** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start tracing" → proceed
</decision_gate>

</intake_gate>

<process>
1. State the core claim or concept clearly
2. Identify first-order implications (direct consequences)
3. Trace second-order implications (consequences of consequences)
4. Surface non-obvious or counterintuitive implications
5. Note implications that conflict with common assumptions
6. Identify what this rules out or makes impossible
</process>

<output_format>
**The claim:**
[Clear statement of the concept/idea]

**If this is true, then:**

*First-order (direct):*
- [Immediate consequence]
- [Immediate consequence]

*Second-order (downstream):*
- [Consequence of the above]
- [Consequence of the above]

**This rules out:**
- [What can't be true if this is true]

**Non-obvious implication:**
[The surprising thing that follows but people miss]

**The tension:**
[Where this conflicts with something commonly believed]
</output_format>

<constraints>
- Don't just restate the concept - draw out what follows
- Include at least one non-obvious implication
- Show second-order effects, not just direct ones
- Surface contradictions with common beliefs
</constraints>

<success_criteria>
- Reader sees consequences they hadn't considered
- Implications are logically valid (actually follow from the premise)
- At least one "I hadn't thought of that" moment
- Makes the concept more real by showing its effects
</success_criteria>
