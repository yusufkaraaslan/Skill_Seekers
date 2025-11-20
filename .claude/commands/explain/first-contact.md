---
description: Explain to someone with zero cultural context
argument-hint: [concept or leave blank for current context]
---

<objective>
Explain $ARGUMENTS (or the current topic if no arguments provided) as if to an intelligent being with zero cultural context.

No shared references. No "it's like X" where X requires Earth knowledge. Pure explanation from first principles.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS to extract what's already provided:
- What concept to explain
- What baseline knowledge to assume (physics? biology? logic only?)
- Purpose of this stripped-down explanation

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-3 questions based on actual gaps:

**If baseline unclear:**
- "What can I assume they know?" with options: Only logic/math, Basic physics, Biology of living things, Nothing - pure first principles, Other

**If purpose unclear:**
- "Why this approach?" with options: Force myself to truly understand, Explain to someone very different, Strip away assumptions, See it fresh, Other

**If scope unclear:**
- "How complete should this be?" with options: Core concept only, Full working explanation, Everything needed to use it, Other

Skip questions where $ARGUMENTS already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to explain from first principles, or would you like me to ask more questions?"

Options:
1. **Start explaining** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups, then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start explaining" → proceed
</decision_gate>

</intake_gate>

<process>
1. Identify what you're explaining
2. Strip away ALL cultural references
3. Identify the fundamental concepts needed to understand it
4. Build up from physics/logic/mathematics if needed
5. Explain the human context that makes this relevant
6. Describe what problem it solves or need it fills
</process>

<output_format>
**Explaining [topic] from scratch:**

**Fundamental concepts required:**
[What base knowledge is needed - stated without cultural reference]

**What it is:**
[Description using only universal concepts - no metaphors requiring shared experience]

**Why it exists:**
[The problem or need it addresses, in universal terms]

**How it works:**
[Mechanism, using only previously established concepts]

**Why humans care about this:**
[The context that makes this important to our species/situation]

**In one sentence:**
[Stripped-down essence that requires no Earth knowledge]
</output_format>

<constraints>
- No cultural references (no "like a car" or "like money")
- No idioms or figures of speech
- No references to Earth-specific institutions
- Must be understandable from pure logic + stated premises
- Can reference physics, math, logic, biology basics
</constraints>

<success_criteria>
- Explanation works without shared cultural knowledge
- Each concept is either fundamental or built from previous concepts
- Reader sees familiar things in a new light
- Forces clarity that metaphors often obscure
</success_criteria>
