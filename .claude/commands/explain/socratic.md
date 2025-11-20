---
description: Explain via questions that lead to understanding
argument-hint: [concept or leave blank for current context]
---

<objective>
Explain $ARGUMENTS (or the current topic if no arguments provided) through Socratic questioning.

Guide understanding through questions rather than statements. Let the reader discover the answer.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What concept to explore
- Starting knowledge level
- Where to lead the questioning
- Depth of inquiry

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If starting point unclear:**
- "What do you already know?" with options: Nothing - start from scratch, Basic familiarity, Know it but want deeper understanding, Other

**If destination unclear:**
- "Where should the questions lead?" with options: Core insight about the concept, A specific conclusion, Expose a flaw in my thinking, Wherever it goes, Other

**If depth unclear:**
- "How deep should we go?" with options: Surface understanding, Working knowledge, Deep mastery, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to begin Socratic exploration, or would you like me to ask more questions?"

Options:
1. **Start questioning** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start questioning" → proceed
</decision_gate>

</intake_gate>

<process>
1. Identify the concept to explain
2. Start with what the reader likely already knows
3. Ask questions that:
   - Build on previous answers
   - Expose contradictions in naive thinking
   - Lead toward the key insight
4. After key questions, provide the synthesis
5. End with a question that extends understanding
</process>

<output_format>
**Let's think about [topic]:**

Start with what you know:
- [Question about familiar starting point]

Now consider:
- [Question that introduces complexity]
- [Follow-up that deepens]

Here's the tension:
- [Question exposing contradiction or puzzle]

So what does this tell us?
- [Question leading to insight]

**The key insight:**
[Synthesis of where the questions led]

**To go deeper:**
[Question that extends beyond this explanation]
</output_format>

<constraints>
- Questions must actually lead somewhere (not just rhetorical)
- Each question builds on previous ones
- Don't ask questions you then ignore
- Provide synthesis after the questioning - don't leave hanging
</constraints>

<success_criteria>
- Reader could answer each question before moving on
- Questions expose genuine tensions or puzzles
- Insight feels earned/discovered, not handed down
- Reader understands the "why" not just the "what"
</success_criteria>
