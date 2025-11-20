---
description: Explain by attacking it - find the weaknesses
argument-hint: [concept or leave blank for current context]
---

<objective>
Explain $ARGUMENTS (or the current topic if no arguments provided) by attacking it.

Understand something deeply by trying to break it. Find the weaknesses, limitations, and failure modes.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What concept/claim to attack
- How aggressive the attack should be
- What kind of weaknesses to focus on
- Purpose of the attack

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If intensity unclear:**
- "How hard should I attack?" with options: Fair critique (balanced), Aggressive (find all weaknesses), Devil's advocate (strongest possible attack), Other

**If focus unclear:**
- "What weaknesses to focus on?" with options: Logical flaws, Practical limitations, Edge cases, All of the above, Other

**If purpose unclear:**
- "Why attack this?" with options: Stress-test before committing, Understand limitations, Prepare for objections, Genuine skepticism, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to attack, or would you like me to ask more questions?"

Options:
1. **Start attacking** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start attacking" → proceed
</decision_gate>

</intake_gate>

<process>
1. State the concept or claim clearly
2. Identify its core assumptions
3. Attack each assumption:
   - When does it fail?
   - What does it ignore?
   - What's the strongest counterargument?
4. Find edge cases where it breaks down
5. Identify what it can't explain
6. Assess: is it still useful despite weaknesses?
</process>

<output_format>
**The claim:**
[Clear statement of concept/idea being examined]

**Core assumptions:**
- [Assumption 1]
- [Assumption 2]
- [Assumption 3]

**Attack points:**

*Assumption 1 fails when:*
[Conditions where this doesn't hold]

*Assumption 2 ignores:*
[What this leaves out]

*Strongest counterargument:*
[Best case against this concept]

**Edge cases that break it:**
- [Situation where it fails]
- [Situation where it fails]

**What it can't explain:**
[Phenomena this concept doesn't cover]

**Verdict:**
[Is it still useful? When should you trust it vs. be skeptical?]
</output_format>

<constraints>
- Attack it fairly (not strawman arguments)
- Find real weaknesses, not nitpicks
- Steelman the attacks - make them as strong as possible
- Still give a fair verdict at the end
</constraints>

<success_criteria>
- Attacks are genuine and substantive
- Reader understands when NOT to use this concept
- Limitations are clearly bounded
- Verdict helps reader know when to apply it
</success_criteria>
