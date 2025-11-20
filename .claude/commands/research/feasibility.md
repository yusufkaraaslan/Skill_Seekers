---
description: Reality check - can we actually do this with our constraints?
argument-hint: [idea/project or leave blank for current context]
---

<objective>
Assess feasibility of $ARGUMENTS (or the current topic if no arguments provided).

Honest reality check: can we actually do this given technical, resource, and external constraints?
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What's being assessed
- Known constraints (budget, API limits, external dependencies)
- Technical requirements
- Risk tolerance

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If constraints unclear:**
- "Any hard constraints?" with options: Budget limits, API/service restrictions, Must use specific tech, No major constraints, Other

**If complexity unclear:**
- "How complex is this?" with options: Small (few components), Medium (multiple systems), Large (significant architecture), Not sure, Other

**If dependencies unclear:**
- "External dependencies?" with options: Third-party APIs, External services, Other projects, None significant, Other

**If risk tolerance unclear:**
- "How certain do you need to be?" with options: High confidence required, Moderate risk OK, Willing to experiment, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to assess feasibility, or would you like me to ask more questions?"

Options:
1. **Start assessment** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start assessment" → proceed to research
</decision_gate>

</intake_gate>

<process>
After intake complete:

1. Define what we're assessing
2. Evaluate technical feasibility
3. Evaluate resource feasibility
4. Evaluate external dependency feasibility
5. Identify blockers and de-risking strategies
6. Make go/no-go recommendation
</process>

<output_format>
## Feasibility Assessment: [Project/Idea]

### Strategic Summary
[2-3 sentences: verdict, main concern, key condition for success]

### What we're assessing
[Clear description of the proposed project/feature]

### Technical Feasibility
**Can we build it?**
- Known approaches: [Yes/Partial/No] - [details]
- Technology maturity: [Proven/Emerging/Experimental]
- Technical risks: [List with severity]
- **Technical verdict:** Feasible / Risky / Not feasible

### Resource Feasibility
**Do we have what we need?**
- Skills: [Have/Need to learn]
- Budget: [Sufficient/Tight/Insufficient]
- Tools/infrastructure: [Have/Need to acquire]
- **Resource verdict:** Feasible / Risky / Not feasible

### External Dependency Feasibility
**Are external factors reliable?**
- APIs/services: [Available/Reliable/Rate limits]
- Third-party integrations: [Stable/Risky]
- External data: [Accessible/Restricted]
- **External verdict:** Feasible / Risky / Not feasible

### Blockers
| Blocker | Severity | Mitigation |
|---------|----------|------------|
| [Blocker] | High/Med/Low | [How to address] |

### De-risking Options
- [Option]: [How it reduces risk, what it costs]
- [Option]: [How it reduces risk, what it costs]

### Overall Verdict
**[Go / Go with conditions / No-go]**

[Reasoning and key conditions]

### Implementation Context
<claude_context>
<if_go>
- approach: [recommended technical approach]
- start_with: [first thing to build/validate]
- critical_path: [what must work for this to succeed]
</if_go>
<risks>
- technical: [main technical risks]
- external: [main dependency risks]
- mitigation: [how to address each]
</risks>
<alternatives>
- if_blocked: [fallback approaches if primary fails]
- simpler_version: [reduced scope that's definitely feasible]
</alternatives>
</claude_context>

**Next Action:** Address blockers, reduce scope, prototype critical path, or proceed to /plan/project
</output_format>

<artifact_output>
Save the research to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/research/`

2. Generate filename from topic:
   - Slugify the topic (lowercase, hyphens for spaces)
   - Format: `[topic]-feasibility.md`
   - Example: `native-app-migration-feasibility.md`

3. Write the complete research to the file

4. Report to user: "Saved to `artifacts/research/[filename]`"
</artifact_output>

<success_criteria>
- Assessment is honest (not optimistic or pessimistic)
- All dimensions evaluated (technical, resource, external)
- Blockers are specific and addressable
- De-risking options are actionable
- Verdict is clear with reasoning
- Implementation context gives Claude clear path forward
- Enables informed go/no-go decision
- Output saved to artifacts/research/ directory
</success_criteria>
