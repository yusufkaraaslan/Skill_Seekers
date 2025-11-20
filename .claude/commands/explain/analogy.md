---
description: Explain through mapped analogies - bridge unfamiliar to familiar
argument-hint: [concept or leave blank for current context]
---

<objective>
Explain $ARGUMENTS (or the current topic if no arguments provided) through carefully mapped analogies.

Find a familiar domain that shares structural similarity, then explicitly map the relationships.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What concept to explain
- What familiar domains the audience knows well
- How detailed the mapping should be

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If familiar domain unclear:**
- "What domains do you know well?" with options: Software/computing, Business/finance, Sports/games, Cooking/food, Biology/nature, Other

**If specificity unclear:**
- "Specific analogy or find one?" with options: I have one in mind - I'll tell you, Find the best analogy, Give me multiple options, Other

**If detail unclear:**
- "How detailed should the mapping be?" with options: High-level (capture the gist), Detailed (map most components), Comprehensive (map everything), Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to create the analogy, or would you like me to ask more questions?"

Options:
1. **Start mapping** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start mapping" → proceed
</decision_gate>

</intake_gate>

<process>
1. Identify the concept and its key components/relationships
2. Find a familiar domain with similar structure (not just surface similarity)
3. Map each component to its analog explicitly
4. Explain the concept using the familiar domain's language
5. Note where the analogy breaks down (all analogies have limits)
</process>

<output_format>
**The analogy:**
[Concept] is like [familiar thing] because...

**Mapping:**
- [Technical component] → [Familiar equivalent]
- [Technical component] → [Familiar equivalent]
- [Technical component] → [Familiar equivalent]

**How it works (in analogy terms):**
[Explain the process/concept using only the familiar domain's language]

**Where this breaks down:**
[Limits of the analogy - what it doesn't capture]
</output_format>

<success_criteria>
- Analogy is structurally similar, not just superficially similar
- Explicit mapping between domains
- Explanation works entirely within familiar domain
- Honestly notes where analogy fails
- Reader gains genuine intuition for the concept
</success_criteria>
