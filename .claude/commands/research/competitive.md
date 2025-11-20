---
description: Research competitors - who else does this, how, strengths/weaknesses
argument-hint: [product/feature or leave blank for current context]
---

<objective>
Research competitive landscape for $ARGUMENTS (or the current topic if no arguments provided).

Understand who else solves this problem, how they do it, and where the opportunities are.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- The product/feature space
- Known competitors
- Dimensions that matter (features, pricing, UX)
- What you're trying to learn

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If competitors unclear:**
- "Any specific competitors to include?" with options: I have a list, Find the main ones, Direct competitors only, Include indirect competitors, Other

**If dimensions unclear:**
- "What dimensions matter?" with options: Features/capabilities, Pricing/business model, UX/design, Technical approach, All of the above, Other

**If goal unclear:**
- "What are you trying to learn?" with options: How to differentiate, Market positioning, Feature gaps, Technical approaches, Other

**If depth unclear:**
- "How many competitors?" with options: Top 3, Top 5, Comprehensive (7+), Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to research competitors, or would you like me to ask more questions?"

Options:
1. **Start research** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start research" → proceed to research
</decision_gate>

</intake_gate>

<process>
After intake complete:

1. Define what problem/space we're competing in
2. Identify 3-5 key competitors (direct and indirect)
3. For each competitor, analyze:
   - How they solve the problem
   - Target audience
   - Strengths and weaknesses
   - Pricing/business model
4. Identify patterns across competitors
5. Find gaps and opportunities
</process>

<output_format>
## Competitive Research: [Space/Problem]

### Strategic Summary
[2-3 sentences: the competitive landscape, key insight, main opportunity]

### Problem Being Solved
[What job are all these products doing for users]

### Competitors

**[Competitor 1]**
- **Solution:** [How they solve it]
- **Target:** [Who they serve]
- **Strengths:** [What they do well]
- **Weaknesses:** [Where they fall short]
- **Pricing:** [Model and range]

**[Competitor 2]**
[Same structure...]

**[Competitor 3]**
[Same structure...]

### Comparison Matrix
| Aspect | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| [Key feature] | Y/N | Y/N | Y/N |
| [Key feature] | Y/N | Y/N | Y/N |
| [Key feature] | Y/N | Y/N | Y/N |

### Patterns
[What most/all competitors do - table stakes]

### Gaps & Opportunities
- [Gap]: [Why it's underserved, opportunity]
- [Gap]: [Why it's underserved, opportunity]

### Differentiation Options
1. [Way to differentiate]: [tradeoff]
2. [Way to differentiate]: [tradeoff]

### Implementation Context
<claude_context>
<insights>
- table_stakes: [features we must have to compete]
- differentiators: [features that would set us apart]
- avoid: [approaches that don't work in this space]
</insights>
<technical>
- common_patterns: [technical approaches competitors use]
- opportunities: [technical approaches no one uses yet]
- integrations: [common integrations in this space]
</technical>
<positioning>
- underserved: [user segments not well served]
- overserved: [segments with too many options]
</positioning>
</claude_context>

**Next Action:** Deep dive on specific competitor, validate gaps with user research, or run /plan/brief to define our approach
</output_format>

<artifact_output>
Save the research to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/research/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-competitive.md`
   - Example: `midi-sequencers-competitive.md`

3. Write the complete research to the file

4. Report to user: "Saved to `artifacts/research/[filename]`"
</artifact_output>

<success_criteria>
- Competitors are genuinely relevant (not just big names)
- Analysis is honest (not dismissive of competition)
- Gaps are real opportunities (not just missing features)
- Differentiation options are actionable
- Implementation context identifies technical patterns to adopt or avoid
- Informs strategic decisions
- Output saved to artifacts/research/ directory
</success_criteria>
