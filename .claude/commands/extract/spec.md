---
description: Extract platform-agnostic specification from codebase for reimplementation
argument-hint: [path to codebase or leave blank for current directory]
---

<objective>
Extract a platform-agnostic specification from $ARGUMENTS (or current directory if no arguments provided).

Separate the *what* (behavior, logic, data flow) from the *how* (specific languages, frameworks, APIs). Produce a document that could be used to reimplement in any technology.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS and any context to extract what's already provided:
- Path to codebase
- Type of codebase (web app, CLI, library, etc.)
- Primary complexity (algorithms, integrations, data/domain, UI/UX)
- Target platform for reimplementation
- What's most important to preserve

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If complexity type unclear:**
- "What's the primary complexity?" with options: Algorithms/computation, External integrations (APIs, services), Data/domain logic, UI/UX patterns, Everything (comprehensive), Other

**If target unclear:**
- "What will you rebuild in?" with options: Different language (specify later), Different framework, Native app (iOS/macOS/Android), Just documenting for reference, Other

**If preservation priority unclear:**
- "What's most important to preserve?" with options: Exact behavior, Performance characteristics, Architecture/patterns, User experience, All equally, Other

**If scope unclear:**
- "What scope?" with options: Entire codebase, Specific module/feature, Core functionality only, Other

Skip questions where $ARGUMENTS or context already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to extract specification, or would you like me to ask more questions?"

Options:
1. **Start extracting** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "Any modules to skip?", "Specific behaviors to focus on?", "Known gotchas to document?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start extracting" → proceed to extraction
</decision_gate>

</intake_gate>

<extraction_process>
After intake complete:

1. **Explore the codebase**
   - Read entry points, main modules, configuration
   - Identify architecture and module boundaries
   - Find documentation (README, CLAUDE.md, comments)
   - Map dependencies and data flow

2. **Identify core abstractions**
   - What are the main concepts/entities?
   - What operations exist on each?
   - How do they relate to each other?

3. **Extract based on complexity type:**

   **If Algorithms/computation:**
   - Document algorithms in pseudocode
   - Capture mathematical relationships
   - Note performance characteristics
   - Identify edge cases

   **If External integrations:**
   - Map all external service interactions
   - Document data contracts (request/response shapes)
   - Capture authentication flows
   - Note webhook/callback patterns
   - Document error handling and retries

   **If Data/domain logic:**
   - Entity relationships and schemas
   - Validation rules
   - Business rules and constraints
   - State transitions
   - Authorization logic

   **If UI/UX patterns:**
   - User flows and interactions
   - State management patterns
   - Component hierarchy
   - Event handling

   **If Everything (comprehensive):**
   - All of the above, organized by section

4. **Document platform dependencies**
   - What's specific to current platform
   - Suggested equivalents for target platform
   - What has no direct equivalent (needs redesign)

5. **Capture implicit knowledge**
   - Why certain approaches were chosen
   - Known limitations and workarounds
   - Edge cases and gotchas
   - Things that aren't obvious from code
</extraction_process>

<output_format>
# Specification: [Project Name]

## Overview
[One paragraph: what this is, what it does, core value proposition]

## Core Concepts
[The main abstractions - what are the "nouns" in this system?]

### [Concept 1]
- What it is
- Properties/attributes
- Operations it supports
- Relationships to other concepts

### [Concept 2]
...

## Data Structures
[Schemas, shapes, types - platform agnostic]

```
[Pseudocode or generic schema notation]
```

## State Management
[What state exists, where it lives, how it changes]

- **[State category]**: [description]
  - Lives in: [where]
  - Changes when: [triggers]
  - Affects: [what depends on it]

## Algorithms
[Core logic in pseudocode - the actual "secret sauce"]

### [Algorithm 1 name]
**Purpose:** [what it does]
**Input:** [what it takes]
**Output:** [what it produces]

```pseudocode
[Step-by-step algorithm]
```

**Key insight:** [why this approach, what makes it work]

### [Algorithm 2 name]
...

## Behaviors
[User/system actions and their effects]

### [Behavior 1]
**Trigger:** [what initiates this]
**Process:** [what happens]
**Result:** [outcome]
**Edge cases:** [exceptions, errors]

## External Integrations
[If applicable - APIs, services, protocols]

### [Integration 1]
- **Service:** [what it connects to]
- **Purpose:** [why]
- **Data flow:** [in/out]
- **Auth:** [how authenticated]
- **Errors:** [failure modes]

## Platform Dependencies
[What's tied to current implementation]

| Current | Purpose | Target Equivalent | Notes |
|---------|---------|-------------------|-------|
| [Web MIDI API] | [MIDI output] | [CoreMIDI] | [direct mapping] |
| [Canvas] | [drawing] | [Metal/Core Graphics] | [different paradigm] |

## Configuration
[All configurable values, defaults, magic numbers]

## Known Limitations & Gotchas
[Things that aren't obvious from the code]

- [Gotcha 1]: [explanation]
- [Gotcha 2]: [explanation]

## Reimplementation Notes
[Specific guidance for rebuilding]

- [Note about approach]
- [Note about what to watch out for]
- [Note about what can be simplified]
</output_format>

<constraints>
- Stay platform-agnostic in algorithms and logic
- Use pseudocode, not language-specific syntax
- Capture the WHY, not just the WHAT
- Include edge cases and failure modes
- Note performance characteristics where relevant
- Don't just describe - document enough to rebuild
</constraints>

<artifact_output>
Save the specification to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/specs/`

2. Generate filename from topic:
   - Slugify the project/topic name (lowercase, hyphens for spaces)
   - Format: `[topic]-spec.md`
   - Example: `sequins-midi-app-spec.md`

3. Write the complete specification to the file

4. Report to user: "Saved to `artifacts/specs/[filename]`"
</artifact_output>

<success_criteria>
- Someone could reimplement in a different language/framework using this doc
- Core algorithms are clear and complete
- Data structures are fully specified
- Behaviors cover happy path AND edge cases
- Platform dependencies are identified with suggested equivalents
- Implicit knowledge is surfaced and documented
- Nothing important is lost to abstraction
- Output saved to artifacts/specs/ directory
</success_criteria>
