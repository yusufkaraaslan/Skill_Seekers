---
description: Steelman both sides - show the tension
argument-hint: [concept or leave blank for current context]
---

<objective>
Explain $ARGUMENTS (or the current topic if no arguments provided) by presenting the strongest case for opposing views.

Don't just explain what something is - show why smart people disagree about it. Steelman both sides.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What topic/question is being debated
- What the opposing positions are
- Whether to take a side at the end
- How many positions to present

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If positions unclear:**
- "What are the sides?" with options: I'll describe them, Find the main opposing views, There are more than 2 sides, Other

**If verdict unclear:**
- "Should I take a side?" with options: Yes - give your assessment, No - stay neutral, Lean but acknowledge uncertainty, Other

**If scope unclear:**
- "How many positions?" with options: 2 opposing views, 3+ perspectives, Full spectrum of views, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to present the debate, or would you like me to ask more questions?"

Options:
1. **Start debating** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start debating" → proceed
</decision_gate>

</intake_gate>

<process>
1. Identify the concept and the core tension/debate
2. Present Side A (steelmanned):
   - Best arguments
   - Strongest evidence
   - What it gets right
3. Present Side B (steelmanned):
   - Best arguments
   - Strongest evidence
   - What it gets right
4. Identify where each side is strongest
5. Show where the real disagreement lies
6. Explain what would change minds
</process>

<output_format>
**The debate:**
[What's being contested, in neutral terms]

**Side A: [Position]**
*Strongest arguments:*
- [Argument]
- [Argument]

*Best evidence:*
- [Evidence]

*What this gets right:*
[The kernel of truth]

**Side B: [Position]**
*Strongest arguments:*
- [Argument]
- [Argument]

*Best evidence:*
- [Evidence]

*What this gets right:*
[The kernel of truth]

**The real disagreement:**
[What's actually being contested - values, facts, definitions?]

**What would change minds:**
- Side A would update if: [Evidence or argument]
- Side B would update if: [Evidence or argument]

**Where I land:**
[Your assessment, acknowledging the tension]
</output_format>

<constraints>
- Both sides must be steelmanned (strongest version)
- Don't strawman either position
- Identify real disagreement, not just talking past each other
- Must give your own assessment at the end
</constraints>

<success_criteria>
- Proponents of each side would recognize their position
- Both sides are presented with intellectual charity
- Reader understands why this is genuinely hard
- Your conclusion acknowledges legitimate disagreement
</success_criteria>
