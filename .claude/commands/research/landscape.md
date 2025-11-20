---
description: Map the space - tools, players, trends, gaps in a domain
argument-hint: [domain/space or leave blank for current context]
---

<objective>
Map the landscape of $ARGUMENTS (or the current topic if no arguments provided).

Understand the full space: who the players are, what tools exist, where things are heading, and where the gaps are.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- The domain/space to map
- Scope boundaries
- Known players or categories
- What you're trying to learn

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If scope unclear:**
- "How broad?" with options: Narrow niche, Specific category, Broad space, Entire industry, Other

**If focus unclear:**
- "What matters most?" with options: Key players, Available tools, Market trends, Gaps/opportunities, All of the above, Other

**If depth unclear:**
- "How comprehensive?" with options: Quick overview, Solid map, Exhaustive research, Other

**If use unclear:**
- "Why do you need this map?" with options: Find opportunities, Understand competition, Choose tools, Strategic planning, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to map the landscape, or would you like me to ask more questions?"

Options:
1. **Start mapping** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start mapping" → proceed to research
</decision_gate>

</intake_gate>

<process>
After intake complete:

1. Define the space/domain boundaries
2. Identify categories within the space
3. Map key players and tools per category
4. Identify trends and direction
5. Find gaps and emerging areas
6. Synthesize into strategic understanding
</process>

<output_format>
## Landscape Map: [Domain/Space]

### Strategic Summary
[2-3 sentences: shape of the space, key trend, main opportunity]

### Scope
[What's included and excluded from this landscape]

### Categories

**[Category 1: e.g., "Data Storage"]**
- **Established players:** [Names]
- **Emerging players:** [Names]
- **Key tools:** [Tools/products]
- **Trend:** [Where this category is heading]

**[Category 2: e.g., "Processing"]**
[Same structure...]

**[Category 3: e.g., "Visualization"]**
[Same structure...]

### Landscape Map
```
[Visual representation - can be ASCII or description]

Category 1          Category 2          Category 3
-----------         -----------         -----------
Player A            Player D            Player G
Player B            Player E            Player H
Player C            Player F
```

### Trends
- **[Trend 1]:** [What's happening, implications]
- **[Trend 2]:** [What's happening, implications]
- **[Trend 3]:** [What's happening, implications]

### Gaps & White Space
- **[Gap]:** [Why it's underserved, opportunity size]
- **[Gap]:** [Why it's underserved, opportunity size]

### Key Insights
1. [Strategic insight about the space]
2. [Strategic insight about the space]
3. [Strategic insight about the space]

### Implications for Us
- [What this means for our strategy/project]
- [Where we might fit/compete/differentiate]

### Implementation Context
<claude_context>
<positioning>
- opportunities: [where we could enter/compete]
- crowded: [areas to avoid unless differentiating significantly]
- emerging: [nascent areas with potential]
</positioning>
<technical>
- standard_stack: [common technical approaches in this space]
- integrations: [expected integrations/compatibility]
- tools_to_evaluate: [specific tools worth investigating]
</technical>
<trends>
- adopt: [trends to align with]
- watch: [trends to monitor]
- avoid: [declining approaches]
</trends>
</claude_context>

**Next Action:** Deep dive on specific area, competitive research on key players, or run /plan/brief to define our approach
</output_format>

<artifact_output>
Save the research to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/research/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-landscape.md`
   - Example: `music-production-tools-landscape.md`

3. Write the complete research to the file

4. Report to user: "Saved to `artifacts/research/[filename]`"
</artifact_output>

<success_criteria>
- Categories are mutually exclusive and collectively exhaustive
- Players are correctly positioned
- Trends are backed by evidence
- Gaps are genuine opportunities (not just missing features)
- Implementation context gives Claude strategic and technical direction
- Provides strategic clarity about the space
- Output saved to artifacts/research/ directory
</success_criteria>
