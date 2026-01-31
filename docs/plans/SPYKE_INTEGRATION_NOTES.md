# Spyke Games - Skill Seekers Integration Notes

> Discussion notes for Claude Code + Skill Seekers integration at Spyke Games
> Date: 2026-01-06

---

## Current State Analysis

### What They Have (Excellent Foundation)

```
knit-game-client/docs/
├── workflows/
│   └── feature-development-workflow.md    # Complete dev workflow
├── templates/
│   ├── ANALYSIS-CHECKLIST.md              # 13-section feature analysis
│   ├── DESIGN-TEMPLATE.md                 # Feature design template
│   ├── TDD-TEMPLATE.md                    # Technical design doc
│   ├── PR-CHECKLIST.md                    # Review checklist with pitfalls
│   └── ISSUE-TEMPLATE.md                  # GitHub issue structure
└── features/
    └── area-cover-blocker/                # Example complete feature
        ├── DESIGN.md                      # 549 lines, comprehensive
        ├── EDGE-CASES.md
        ├── TASKS.md
        └── TDD.md
```

### Key Observations

1. **Already using Claude Code skill references** in docs:
   - `/knitgame-core` - Core gameplay patterns
   - `/threadbox-blocker` - Grid blocker patterns

2. **Documented Common Pitfalls** (PR-CHECKLIST.md):
   - UnityEngine in Controller/Model (MVC violation)
   - Stale references after async
   - Memory leaks from events (missing Dispose)
   - Animation ID leaks (missing try-finally)
   - Missing PrepareForReuse state reset
   - Double-despawn race conditions
   - Play-on under-restoration

3. **MVC Layer Rules** (CRITICAL):
   | Layer | UnityEngine | Purpose |
   |-------|-------------|---------|
   | Model | NO | Pure C# data, state, logic |
   | Controller | NO | Business logic, orchestration |
   | View | YES | MonoBehaviour, visuals |
   | Service | YES | Business logic needing Unity APIs |

4. **Test Patterns**:
   - Reflection-based DI injection (no Zenject in tests)
   - NSubstitute for mocking
   - Real models, mocked dependencies

---

## Proposed Skill Layer Architecture

### Layer 1: Workflow Skills (HOW to develop)

| Skill | Source | Purpose |
|-------|--------|---------|
| `yarn-flow-workflow` | `docs/workflows/` | Feature development lifecycle |
| `yarn-flow-analysis` | `ANALYSIS-CHECKLIST.md` | Feature analysis patterns |
| `yarn-flow-pr-review` | `PR-CHECKLIST.md` | Review checklist, pitfalls |
| `yarn-flow-testing` | Test files + templates | Test patterns, reflection DI |

### Layer 2: Pattern Skills (WHAT to implement)

| Skill | Source | Purpose |
|-------|--------|---------|
| `yarn-flow-mvc` | Workflow docs + code | MVC layer rules |
| `yarn-flow-blockers` | Blocker implementations | Grid/Yarn/Bottom patterns |
| `yarn-flow-boosters` | Booster implementations | Booster patterns |
| `yarn-flow-async` | Code patterns | UniTask, cancellation, safety |
| `yarn-flow-pooling` | Generators | ObjectPool, PrepareForReuse |
| `yarn-flow-events` | Controllers | Event lifecycle (Init/Dispose) |
| `yarn-flow-di` | Installers | Zenject binding patterns |

### Layer 3: Reference Skills (Examples to follow)

| Skill | Source | Purpose |
|-------|--------|---------|
| `yarn-flow-threadbox` | ThreadBox implementation | Reference grid blocker |
| `yarn-flow-mystery` | Mystery implementation | Reference yarn blocker |
| `yarn-flow-areacover` | AreaCover + DESIGN.md | Recent, fully documented |

---

## Proposed Agent Architecture

### 1. Feature Analysis Agent

```
Trigger: "analyze feature {X}" or "what base class for {X}"
Skills: yarn-flow-analysis, yarn-flow-blockers, yarn-flow-boosters
Action:
  - Runs ANALYSIS-CHECKLIST programmatically
  - Identifies feature type (Grid/Yarn/Bottom Blocker, Booster)
  - Suggests base class
  - Maps system interactions
  - Identifies edge cases
  - Outputs gap analysis
```

### 2. Design Document Agent

```
Trigger: "create design doc for {X}" or when starting new feature
Skills: yarn-flow-workflow, yarn-flow-blockers, yarn-flow-reference
Action:
  - Creates docs/features/{feature}/DESIGN.md from template
  - Pre-populates interaction matrix based on feature type
  - Suggests edge cases from similar features
  - Creates EDGE-CASES.md skeleton
```

### 3. PR Review Agent

```
Trigger: PR created, "review PR", or pre-commit hook
Skills: yarn-flow-pr-review, yarn-flow-mvc, yarn-flow-async
Action:
  - Scans for UnityEngine imports in Controller/Model
  - Verifies IInitializable + IDisposable pair
  - Checks event subscription/unsubscription balance
  - Validates PrepareForReuse resets all state
  - Checks async safety (CancellationToken, try-finally)
  - Verifies test coverage for public methods
Output: Review comments with specific line numbers
```

### 4. Code Scaffold Agent

```
Trigger: "implement {type} {name}" after design approved
Skills: yarn-flow-blockers, yarn-flow-di, yarn-flow-pooling
Action:
  - Generates Model extending correct base class
  - Generates Controller with IInitializable, IDisposable
  - Generates ModelGenerator with ObjectPool
  - Generates View (MonoBehaviour)
  - Adds DI bindings to installer
  - Creates test file skeletons
Output: Complete scaffold following all patterns
```

---

## New Grad Pipeline Vision

```
FEATURE REQUEST
      ↓
┌─────────────────────────────────────────┐
│ 1. ANALYSIS AGENT                       │
│    "Analyze feature ThreadCutter"       │
│    → Suggests GridBlockerBaseModel      │
│    → Maps interactions                  │
│    → Identifies 12 edge cases           │
└─────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────┐
│ 2. DESIGN AGENT                         │
│    "Create design doc"                  │
│    → Generates DESIGN.md (80% complete) │
│    → New grad fills in specifics        │
└─────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────┐
│ 3. CODE SCAFFOLD AGENT                  │
│    "Implement ThreadCutter"             │
│    → Generates 6 files with patterns    │
│    → All boilerplate correct            │
│    → New grad fills in business logic   │
└─────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────┐
│ 4. NEW GRAD CODES                       │
│    Has correct structure                │
│    Just writes the actual logic         │
│    Skills loaded = answers questions    │
└─────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────┐
│ 5. PR REVIEW AGENT                      │
│    "Review my PR"                       │
│    → Catches MVC violations             │
│    → Verifies async safety              │
│    → Checks test coverage               │
│    → Feedback before human review       │
└─────────────────────────────────────────┘
      ↓
SENIOR-QUALITY CODE FROM JUNIOR DEV
```

---

## Implementation Priority

### Phase 1: Core Skills (Week 1)
1. Generate skill from `knit-game-client` repo (full codebase)
2. Generate skill from `docs/` folder specifically
3. Install to Claude Code for all devs

### Phase 2: Specialized Skills (Week 2)
1. Split into workflow vs pattern skills
2. Create reference skills from best implementations
3. Test with actual feature development

### Phase 3: Agents (Week 3-4)
1. PR Review Agent (highest ROI - catches common pitfalls)
2. Analysis Agent (helps new devs start correctly)
3. Code Scaffold Agent (reduces boilerplate time)

### Phase 4: CI/CD Integration (Week 5+)
1. PR Review Agent as GitHub Action
2. Auto-regenerate skills when docs change
3. Team-wide skill distribution

---

## Questions to Resolve

1. **Confluence Integration**
   - How stale is Confluence vs docs/ folder?
   - Should we scrape Confluence or focus on in-repo docs?
   - Can we set up sync from Confluence → docs/ → skills?

2. **Skill Granularity**
   - One big `yarn-flow` skill vs many small skills?
   - Recommendation: Start with 2-3 (workflow, patterns, reference)
   - Split more if Claude context gets overloaded

3. **Agent Deployment**
   - Local per-developer vs team server?
   - GitHub Actions integration?
   - Slack/Teams notifications?

4. **SDK Skills**
   - Which SDKs cause most pain?
   - Firebase? Analytics? Ads? IAP?
   - Prioritize based on integration frequency

---

## Related Discussions

- Layered skill architecture (game → framework → external → base)
- New grad onboarding goal: "produce code near our standard"
- Manual review → automated agent review pipeline
- Confluence freshness concerns

---

## Next Steps

1. [ ] Generate skill from knit-game-client repo
2. [ ] Test with actual feature development
3. [ ] Identify highest-pain SDK for skill creation
4. [ ] Design PR Review Agent prompt
5. [ ] Pilot with 1-2 developers
