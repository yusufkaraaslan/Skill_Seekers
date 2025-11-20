---
description: Explain like I'm 5 - simple language, no jargon, clear analogies
argument-hint: [concept or leave blank for current context]
---

<objective>
Explain $ARGUMENTS (or the current topic if no arguments provided) as if to a smart 5-year-old.

Strip away jargon and technical complexity. Use familiar concepts and simple cause-and-effect.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What concept to explain
- Who the actual audience is (literal child, non-technical adult, etc.)
- What familiar domains to draw from

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 1-2 questions based on actual gaps:

**If audience unclear:**
- "Who is this actually for?" with options: Literal child, Non-technical adult, Technical person in different field, Myself (check my understanding), Other

**If domain unclear:**
- "What familiar things should I use?" with options: Everyday objects (toys, food, cars), Nature (animals, weather, plants), Social situations (family, school, games), Whatever works best, Other

Skip questions where $ARGUMENTS already provides the answer. ELI5 is simple - don't over-ask.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to explain simply, or need to clarify something?"

Options:
1. **Start explaining** - I have enough context
2. **Ask more questions** - There's something to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 1-2 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start explaining" → proceed
</decision_gate>

</intake_gate>

<process>
1. Identify the core concept to explain
2. Find a familiar real-world analogy (toys, food, playground, family)
3. Explain using only common words (avoid all technical terms)
4. Use concrete examples, not abstractions
5. Keep sentences short and direct
6. End with "So basically..." one-sentence summary
</process>

<output_format>
**Simple version:**
[Explanation using everyday language and familiar analogies]

**So basically:**
[One sentence a child could repeat back]
</output_format>

<constraints>
- No jargon or technical terms
- No acronyms
- No "it's like X but for Y" (find direct analogies)
- Max 3 sentences before the summary
- If you can't explain it simply, you don't understand it well enough
</constraints>

<success_criteria>
- A non-technical person could understand and repeat it
- Uses concrete, tangible analogies
- No terms that require prior technical knowledge
- Core concept accurately conveyed despite simplification
</success_criteria>
