---
description: Start with conclusion and work backwards to premises
argument-hint: [concept or leave blank for current context]
---

<objective>
Explain $ARGUMENTS (or the current topic if no arguments provided) in reverse - start with the conclusion and work backwards.

Begin with what we know to be true, then unpack why. Reveal the reasoning by tracing back through the chain.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What conclusion to trace back from
- How deep to trace (to what foundations)
- What kind of reasoning (logical, causal, historical)

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If depth unclear:**
- "How far back should we trace?" with options: To immediate reasons, To foundational premises, To first principles, As far as it goes, Other

**If reasoning type unclear:**
- "What kind of chain?" with options: Logical (premises → conclusion), Causal (cause → effect), Historical (how we got here), Other

**If purpose unclear:**
- "Why trace backwards?" with options: Find hidden assumptions, Understand the reasoning, Find weak links, See the full picture, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to trace backwards, or would you like me to ask more questions?"

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
1. State the conclusion or current understanding
2. Ask "why is this true?" or "how did we get here?"
3. Identify the immediate supporting reasons
4. For each reason, ask "why?" again
5. Continue until you reach foundational premises
6. Show the complete chain from conclusion to foundations
</process>

<output_format>
**The conclusion:**
[What we know/accept/observe to be true]

**Why? (Level 1)**
Because: [Immediate reason]

**Why? (Level 2)**
Because: [Deeper reason]

**Why? (Level 3)**
Because: [Even deeper]

**Foundations:**
[The base premises or observations this all rests on]

**The chain:**
[Foundation] → [builds to] → [which leads to] → [which explains] → [Conclusion]

**The key link:**
[The most important or non-obvious step in the chain]
</output_format>

<constraints>
- Start with something concrete and accepted
- Each "why" must actually answer the previous level
- Don't skip steps in the chain
- Identify where the reasoning is weakest
</constraints>

<success_criteria>
- Reader can trace from conclusion back to foundations
- Each step logically connects to the next
- No gaps in reasoning
- Reveals assumptions that are usually hidden
</success_criteria>
