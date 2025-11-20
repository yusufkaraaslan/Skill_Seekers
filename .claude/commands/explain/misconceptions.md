---
description: Explain by clearing up what people get wrong
argument-hint: [concept or leave blank for current context]
---

<objective>
Explain $ARGUMENTS (or the current topic if no arguments provided) by addressing common misconceptions.

Sometimes the fastest path to understanding is clearing away the wrong ideas first.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What concept to clear up
- Who holds these misconceptions (general public, beginners, experts)
- How many misconceptions to address
- Specific misconceptions to focus on

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If audience unclear:**
- "Whose misconceptions?" with options: General public, Beginners in the field, Intermediate practitioners, Even experts, Other

**If scope unclear:**
- "How many to address?" with options: Top 3 most common, Comprehensive list, Just the most damaging one, Other

**If specific misconceptions known:**
- "Any specific misconceptions to address?" with options: I'll list them, Find the most common ones, Focus on ones I might hold, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to clear up misconceptions, or would you like me to ask more questions?"

Options:
1. **Start clearing** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start clearing" → proceed
</decision_gate>

</intake_gate>

<process>
1. Identify the concept to explain
2. List common misconceptions about it
3. For each misconception:
   - State what people think
   - Explain why it's wrong
   - Provide the correct understanding
4. Explain why these misconceptions are so common
5. Give the clean, correct mental model
</process>

<output_format>
**Common misconceptions about [topic]:**

**Misconception 1:** "[What people think]"
- Why it's wrong: [Explanation]
- Actually: [Correct understanding]

**Misconception 2:** "[What people think]"
- Why it's wrong: [Explanation]
- Actually: [Correct understanding]

**Misconception 3:** "[What people think]"
- Why it's wrong: [Explanation]
- Actually: [Correct understanding]

**Why these stick:**
[Why these wrong ideas are so common/intuitive]

**Clean mental model:**
[How to think about this correctly]
</output_format>

<constraints>
- Address real misconceptions (not strawmen)
- Explain why the misconception is intuitive
- Don't just say "wrong" - explain why
- End with correct understanding, not just negation
</constraints>

<success_criteria>
- Reader recognizes misconceptions they held
- Explanations of "why it's wrong" are clear and convincing
- Correct understanding fills the gap left by cleared misconceptions
- Reader can now spot these misconceptions in others
</success_criteria>
