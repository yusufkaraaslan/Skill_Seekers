---
description: Extract platform-agnostic UI/UX design patterns from codebase for reimplementation
argument-hint: [path to codebase or leave blank for current directory]
---

<objective>
Extract a platform-agnostic UI/UX specification from $ARGUMENTS (or current directory if no arguments provided).

Separate the *visual design and interaction patterns* from the *specific implementation* (CSS, SwiftUI, Qt, etc.). Produce a document that captures enough detail to rebuild the UI in any technology while preserving the look and feel.
</objective>

<intake_gate>

<context_analysis>
First, analyze $ARGUMENTS and any context to extract what's already provided:
- Path to codebase
- UI framework (React, SwiftUI, Qt, Juce, vanilla JS, etc.)
- Type of interface (canvas-based, form-based, document editor, etc.)
- Target platform for reimplementation
- What's most important to preserve (visual fidelity, interaction feel, accessibility)

Only ask about genuine gaps - don't re-ask what's already stated.
</context_analysis>

<initial_questions>
Use AskUserQuestion to ask 2-4 questions based on actual gaps:

**If UI type unclear:**
- "What type of interface is this?" with options: Canvas/drawing-based, Form/data entry, Document editor, Dashboard/analytics, Media player/editor, Other

**If priority unclear:**
- "What's most important to preserve?" with options: Visual design (exact look), Interaction patterns (how it feels), Accessibility, Performance/responsiveness, All equally, Other

**If target unclear:**
- "What will you rebuild in?" with options: SwiftUI/AppKit, React/web, Qt/C++, Flutter, Just documenting, Other

**If scope unclear:**
- "What scope?" with options: Entire UI, Specific view/screen, Component library, Design system only, Other

Skip questions where $ARGUMENTS or context already provides the answer.
</initial_questions>

<decision_gate>
After receiving answers, use AskUserQuestion:

Question: "Ready to extract UI patterns, or would you like me to ask more questions?"

Options:
1. **Start extracting** - I have enough context
2. **Ask more questions** - There are details to clarify
3. **Let me add context** - I want to provide additional information

If "Ask more questions" → generate 2-3 contextual follow-ups based on accumulated context (e.g., "Any interactions to skip?", "Specific animations to focus on?", "Known accessibility requirements?"), then present decision gate again
If "Let me add context" → receive input, then present decision gate again
If "Start extracting" → proceed to extraction
</decision_gate>

</intake_gate>

<extraction_process>
After intake complete:

1. **Explore the codebase UI layer**
   - Find stylesheets, theme files, design tokens
   - Identify component structure
   - Locate interaction handlers (mouse, keyboard, touch)
   - Find animation/transition definitions
   - Map state management for UI state

2. **Extract design tokens**
   - Color palette (with semantic names where possible)
   - Spacing scale
   - Typography system (fonts, sizes, weights, line heights)
   - Border system (widths, radii, styles)
   - Shadow system
   - Animation timing functions and durations
   - Z-index/layering hierarchy
   - Breakpoints (if responsive)

3. **Document visual hierarchy**
   - Layout patterns (grid, flex, absolute positioning)
   - Component nesting and composition
   - Visual weight and emphasis patterns
   - Whitespace usage
   - Alignment principles

4. **Catalog component states**
   For each significant component, document:
   - Default state
   - Hover state
   - Active/pressed state
   - Focused state
   - Selected state
   - Disabled state
   - Loading state
   - Error state
   - Any custom states (muted, editing, etc.)

5. **Map interaction patterns**
   - Mouse/touch interactions (click, drag, hover, scroll)
   - Keyboard shortcuts and navigation
   - Selection patterns (single, multi, range)
   - Drag and drop behaviors
   - Context menus and their triggers
   - Modal/popover behaviors

6. **Document feedback mechanisms**
   - Visual feedback (color changes, scale, opacity)
   - Audio feedback (if any)
   - Haptic feedback (if applicable)
   - Progress indicators
   - Status indicators
   - Toast/notification patterns
   - Validation feedback

7. **Capture motion design**
   - What animates and when
   - Easing functions used
   - Duration patterns (quick vs slow actions)
   - Entrance/exit animations
   - State transition animations
   - Loading animations
   - Micro-interactions

8. **Note accessibility patterns**
   - Focus management
   - Screen reader considerations
   - Keyboard navigation order
   - Color contrast requirements
   - Touch target sizes
</extraction_process>

<output_format>
# UI Specification: [Project Name]

## Overview
[One paragraph: what this UI is, primary interaction model, design philosophy]

## Design Philosophy
[Core principles - e.g., "minimalist with high contrast", "soft and friendly", "data-dense but scannable"]

- [Principle 1]
- [Principle 2]
- [Principle 3]

## Design Tokens

### Colors
```
Primary:      [hex] - [usage]
Secondary:    [hex] - [usage]
Background:   [hex]
Surface:      [hex]
Text:         [hex]
Text Muted:   [hex]
Border:       [hex]
Error:        [hex]
Success:      [hex]
Warning:      [hex]
[Custom semantic colors...]
```

### Spacing Scale
```
2xs:  [value] - [usage]
xs:   [value] - [usage]
sm:   [value] - [usage]
md:   [value] - [usage]
lg:   [value] - [usage]
xl:   [value] - [usage]
2xl:  [value] - [usage]
```

### Typography
```
Font Family:
- Primary: [font stack]
- Monospace: [font stack]

Size Scale:
- xs:  [value]
- sm:  [value]
- md:  [value]
- lg:  [value]
- xl:  [value]

Weights:
- normal:   [value]
- medium:   [value]
- semibold: [value]
- bold:     [value]

Line Heights:
- tight:  [value]
- normal: [value]
- relaxed: [value]
```

### Borders
```
Width:
- thin:   [value]
- normal: [value]
- thick:  [value]

Radius:
- none:   0
- sm:     [value]
- md:     [value]
- lg:     [value]
- full:   [value]
```

### Shadows
```
[Shadow definitions or "None - depth achieved through [alternative]"]
```

### Animation
```
Durations:
- instant: [value] - [usage]
- fast:    [value] - [usage]
- normal:  [value] - [usage]
- slow:    [value] - [usage]

Easings:
- default:    [function]
- enter:      [function]
- exit:       [function]
- bounce:     [function]
```

### Z-Index Layers
```
base:     [value]
elevated: [value]
dropdown: [value]
modal:    [value]
toast:    [value]
tooltip:  [value]
```

## Layout Structure

### Overall Layout
[Describe the main layout pattern - sidebar + content, header + body + footer, etc.]

### Grid System
[If applicable - column count, gutter size, breakpoints]

### Responsive Behavior
[How layout changes across breakpoints, if applicable]

## Components

### [Component 1 Name]
**Purpose:** [what it's for]

**Anatomy:**
- [Part 1]: [description]
- [Part 2]: [description]
- [Part 3]: [description]

**States:**
| State | Background | Border | Text | Other |
|-------|------------|--------|------|-------|
| Default | [value] | [value] | [value] | |
| Hover | [value] | [value] | [value] | |
| Active | [value] | [value] | [value] | |
| Disabled | [value] | [value] | [value] | |
| [Custom] | [value] | [value] | [value] | |

**Dimensions:**
- Height: [value]
- Min/max width: [value]
- Padding: [value]

### [Component 2 Name]
...

## Interaction Patterns

### Mouse/Touch
- **Click**: [what happens]
- **Double-click**: [what happens]
- **Right-click**: [what happens]
- **Drag**: [what happens]
- **Scroll**: [what happens]
- **Hover**: [what happens]

### Keyboard Shortcuts
| Key | Action | Context |
|-----|--------|---------|
| [key] | [action] | [when it applies] |
| [key] | [action] | [when it applies] |

### Selection Patterns
- **Single select**: [how]
- **Multi-select**: [how, e.g., Cmd+click]
- **Range select**: [how, e.g., Shift+click]
- **Select all**: [how]

### Context Menus
- **Trigger**: [right-click, long-press, etc.]
- **Items vary by**: [selection type, state, etc.]
- **Submenu behavior**: [hover delay, position logic]

## Feedback Patterns

### Visual Feedback
- **Action confirmation**: [how success is shown]
- **State change**: [how transitions are visualized]
- **Selection**: [how selected items are indicated]
- **Progress**: [how ongoing actions are shown]

### Transient Feedback
- **Toast/notification**: [position, duration, animation]
- **Tooltip**: [delay, position logic, content]
- **Error messages**: [inline vs toast, styling]

### Real-time Feedback
- **Input validation**: [when, how shown]
- **Live updates**: [what pulses/animates with data changes]

## Motion Design

### Transition Patterns
- **Page/view transitions**: [type, duration, easing]
- **Component enter**: [animation]
- **Component exit**: [animation]
- **State changes**: [how properties animate between states]

### Micro-interactions
- **Button press**: [scale, color shift]
- **Toggle flip**: [animation]
- **Menu open/close**: [animation]
- **Item delete**: [animation]

### Data-driven Animation
- **On data update**: [what animates]
- **On notification**: [what animates]

## Platform Considerations

### Current Implementation
[What's specific to current platform - e.g., CSS Grid, SwiftUI stacks, Canvas API]

### Target Equivalents
| Current | Purpose | [Target Platform] Equivalent |
|---------|---------|------------------------------|
| [impl] | [purpose] | [equivalent] |
| [impl] | [purpose] | [equivalent] |

### Requires Redesign
[Patterns that don't translate directly and need rethinking]

## Accessibility Notes

- **Focus indicators**: [how focus is shown]
- **Screen reader labels**: [naming conventions]
- **Touch targets**: [minimum sizes]
- **Color contrast**: [requirements met]
- **Motion preferences**: [reduced motion support]

## Reimplementation Notes

- [Insight about recreating the feel]
- [Common pitfall to avoid]
- [What can be simplified in target platform]
- [What's essential vs nice-to-have]
</output_format>

<constraints>
- Document visual patterns, not code structure
- Use platform-agnostic descriptions (not "CSS grid" but "12-column grid with 16px gutters")
- Include actual values (hex colors, pixel values, timing) not just descriptions
- Capture the "feel" through specific details (easing functions, delays, etc.)
- Document what's intentional vs incidental (e.g., "sharp corners are a design choice" vs "just using defaults")
- Include enough detail that someone could recreate the same visual/interaction experience
- Note accessibility patterns even if poorly implemented - they're part of the spec
</constraints>

<artifact_output>
Save the specification to a file:

1. Create directory structure if it doesn't exist:
   - `[current-working-directory]/artifacts/ui-specs/`

2. Generate filename from topic:
   - Slugify the project/topic name (lowercase, hyphens for spaces)
   - Format: `[topic]-ui-spec.md`
   - Example: `sequins-ui-spec.md`

3. Write the complete specification to the file

4. Report to user: "Saved to `artifacts/ui-specs/[filename]`"
</artifact_output>

<success_criteria>
- Someone could recreate the visual design in a different framework using this doc
- Design tokens are complete and specific (actual values)
- Component states are fully documented
- Interaction patterns cover all user input methods
- Motion design includes timing and easing details
- Feedback patterns explain how the UI responds
- Platform dependencies are identified with suggested equivalents
- The "feel" of the UI is captured, not just the structure
- Output saved to artifacts/ui-specs/ directory
</success_criteria>
