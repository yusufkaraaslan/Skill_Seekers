# Skill Architecture Guide: Layering and Splitting

Complete guide for architecting complex multi-skill systems using the router/dispatcher pattern.

---

## Table of Contents

- [Overview](#overview)
- [When to Split Skills](#when-to-split-skills)
- [The Router Pattern](#the-router-pattern)
- [Manual Skill Architecture](#manual-skill-architecture)
- [Best Practices](#best-practices)
- [Complete Examples](#complete-examples)
- [Implementation Guide](#implementation-guide)
- [Troubleshooting](#troubleshooting)

---

## Overview

### The 500-Line Guideline

Claude recommends keeping skill files under **500 lines** for optimal performance. This guideline exists because:

- ✅ **Better parsing** - AI can more effectively understand focused content
- ✅ **Context efficiency** - Only relevant information loaded per task
- ✅ **Maintainability** - Easier to debug, update, and manage
- ✅ **Single responsibility** - Each skill does one thing well

### The Problem with Monolithic Skills

As applications grow complex, developers often create skills that:

- ❌ **Exceed 500 lines** - Too much information for effective parsing
- ❌ **Mix concerns** - Handle multiple unrelated responsibilities
- ❌ **Waste context** - Load entire file even when only small portion is relevant
- ❌ **Hard to maintain** - Changes require careful navigation of large file

### The Solution: Skill Layering

**Skill layering** involves:

1. **Splitting** - Breaking large skill into focused sub-skills
2. **Routing** - Creating master skill that directs queries to appropriate sub-skill
3. **Loading** - Only activating relevant sub-skills per task

**Result:** Build sophisticated applications while maintaining 500-line guideline per skill.

---

## When to Split Skills

### Decision Matrix

| Skill Size | Complexity | Recommendation |
|-----------|-----------|----------------|
| < 500 lines | Single concern | ✅ **Keep monolithic** |
| 500-1000 lines | Related concerns | ⚠️ **Consider splitting** |
| 1000+ lines | Multiple concerns | ❌ **Must split** |

### Split Indicators

**You should split when:**

- ✅ Skill exceeds 500 lines
- ✅ Multiple distinct responsibilities (CRUD, workflows, etc.)
- ✅ Different team members maintain different sections
- ✅ Only portions are relevant to specific tasks
- ✅ Context window frequently exceeded

**You can keep monolithic when:**

- ✅ Under 500 lines
- ✅ Single, cohesive responsibility
- ✅ All content frequently relevant together
- ✅ Simple, focused use case

---

## The Router Pattern

### What is a Router Skill?

A **router skill** (also called **dispatcher** or **hub** skill) is a lightweight master skill that:

1. **Analyzes** the user's query
2. **Identifies** which sub-skill(s) are relevant
3. **Directs** Claude to activate appropriate sub-skill(s)
4. **Coordinates** responses from multiple sub-skills if needed

### How It Works

```
User Query: "How do I book a flight to Paris?"
     ↓
Router Skill: Analyzes keywords → "flight", "book"
     ↓
Activates: flight_booking sub-skill
     ↓
Response: Flight booking guidance (only this skill loaded)
```

### Router Skill Structure

```markdown
# Travel Planner (Router)

## When to Use This Skill

Use for travel planning, booking, and itinerary management.

This is a router skill that directs your questions to specialized sub-skills.

## Sub-Skills Available

### flight_booking
For booking flights, searching airlines, comparing prices, seat selection.
**Keywords:** flight, airline, booking, ticket, departure, arrival

### hotel_reservation
For hotel search, room booking, amenities, check-in/check-out.
**Keywords:** hotel, accommodation, room, reservation, stay

### itinerary_generation
For creating travel plans, scheduling activities, route optimization.
**Keywords:** itinerary, schedule, plan, activities, route

## Routing Logic

Based on your question keywords:
- Flight-related → Activate `flight_booking`
- Hotel-related → Activate `hotel_reservation`
- Planning-related → Activate `itinerary_generation`
- Multiple topics → Activate relevant combination

## Usage Examples

**"Find me a flight to Paris"** → flight_booking
**"Book hotel in Tokyo"** → hotel_reservation
**"Create 5-day Rome itinerary"** → itinerary_generation
**"Plan Paris trip with flights and hotel"** → flight_booking + hotel_reservation + itinerary_generation
```

---

## Manual Skill Architecture

### Example 1: E-Commerce Platform

**Problem:** E-commerce skill is 2000+ lines covering catalog, cart, checkout, orders, and admin.

**Solution:** Split into focused sub-skills with router.

#### Sub-Skills

**1. `ecommerce.md` (Router - 150 lines)**
```markdown
# E-Commerce Platform (Router)

## Sub-Skills
- product_catalog - Browse, search, filter products
- shopping_cart - Add/remove items, quantities
- checkout_payment - Process orders, payments
- order_management - Track orders, returns
- admin_tools - Inventory, analytics

## Routing
product/catalog/search → product_catalog
cart/basket/add/remove → shopping_cart
checkout/payment/billing → checkout_payment
order/track/return → order_management
admin/inventory/analytics → admin_tools
```

**2. `product_catalog.md` (350 lines)**
```markdown
# Product Catalog

## When to Use
Product browsing, searching, filtering, recommendations.

## Quick Reference
- Search products: `search(query, filters)`
- Get details: `getProduct(id)`
- Filter: `filter(category, price, brand)`
...
```

**3. `shopping_cart.md` (280 lines)**
```markdown
# Shopping Cart

## When to Use
Managing cart items, quantities, totals.

## Quick Reference
- Add item: `cart.add(productId, quantity)`
- Update quantity: `cart.update(itemId, quantity)`
...
```

**Result:**
- Router: 150 lines ✅
- Each sub-skill: 200-400 lines ✅
- Total functionality: Unchanged
- Context efficiency: 5x improvement

---

### Example 2: Code Assistant

**Problem:** Code assistant handles debugging, refactoring, documentation, testing - 1800+ lines.

**Solution:** Specialized sub-skills with smart routing.

#### Architecture

```
code_assistant.md (Router - 200 lines)
├── debugging.md (450 lines)
├── refactoring.md (380 lines)
├── documentation.md (320 lines)
└── testing.md (400 lines)
```

#### Router Logic

```markdown
# Code Assistant (Router)

## Routing Keywords

### debugging
error, bug, exception, crash, fix, troubleshoot, debug

### refactoring
refactor, clean, optimize, simplify, restructure, improve

### documentation
docs, comment, docstring, readme, api, explain

### testing
test, unit, integration, coverage, assert, mock
```

---

### Example 3: Data Pipeline

**Problem:** ETL pipeline skill covers extraction, transformation, loading, validation, monitoring.

**Solution:** Pipeline stages as sub-skills.

```
data_pipeline.md (Router)
├── data_extraction.md - Source connectors, API calls
├── data_transformation.md - Cleaning, mapping, enrichment
├── data_loading.md - Database writes, file exports
├── data_validation.md - Quality checks, error handling
└── pipeline_monitoring.md - Logging, alerts, metrics
```

---

## Best Practices

### 1. Single Responsibility Principle

**Each sub-skill should have ONE clear purpose.**

❌ **Bad:** `user_management.md` handles auth, profiles, permissions, notifications
✅ **Good:**
- `user_authentication.md` - Login, logout, sessions
- `user_profiles.md` - Profile CRUD
- `user_permissions.md` - Roles, access control
- `user_notifications.md` - Email, push, alerts

### 2. Clear Routing Keywords

**Make routing keywords explicit and unambiguous.**

❌ **Bad:** Vague keywords like "data", "user", "process"
✅ **Good:** Specific keywords like "login", "authenticate", "extract", "transform"

### 3. Minimize Router Complexity

**Keep router lightweight - just routing logic.**

❌ **Bad:** Router contains actual implementation code
✅ **Good:** Router only contains:
- Sub-skill descriptions
- Routing keywords
- Usage examples
- No implementation details

### 4. Logical Grouping

**Group by responsibility, not by code structure.**

❌ **Bad:** Split by file type (controllers, models, views)
✅ **Good:** Split by feature (user_auth, product_catalog, order_processing)

### 5. Avoid Over-Splitting

**Don't create sub-skills for trivial distinctions.**

❌ **Bad:** Separate skills for "add_user" and "update_user"
✅ **Good:** Single "user_management" skill covering all CRUD

### 6. Document Dependencies

**Explicitly state when sub-skills work together.**

```markdown
## Multi-Skill Operations

**Place order:** Requires coordination between:
1. product_catalog - Validate product availability
2. shopping_cart - Get cart contents
3. checkout_payment - Process payment
4. order_management - Create order record
```

### 7. Maintain Consistent Structure

**Use same SKILL.md structure across all sub-skills.**

Standard sections:
```markdown
# Skill Name

## When to Use This Skill
[Clear description]

## Quick Reference
[Common operations]

## Key Concepts
[Domain terminology]

## Working with This Skill
[Usage guidance]

## Reference Files
[Documentation organization]
```

---

## Complete Examples

### Travel Planner (Full Implementation)

#### Directory Structure

```
skills/
├── travel_planner.md (Router - 180 lines)
├── flight_booking.md (420 lines)
├── hotel_reservation.md (380 lines)
├── itinerary_generation.md (450 lines)
├── travel_insurance.md (290 lines)
└── budget_tracking.md (340 lines)
```

#### travel_planner.md (Router)

```markdown
---
name: travel_planner
description: Travel planning, booking, and itinerary management router
---

# Travel Planner (Router)

## When to Use This Skill

Use for all travel-related planning, bookings, and itinerary management.

This router skill analyzes your travel needs and activates specialized sub-skills.

## Available Sub-Skills

### flight_booking
**Purpose:** Flight search, booking, seat selection, airline comparisons
**Keywords:** flight, airline, plane, ticket, departure, arrival, airport, booking
**Use for:** Finding and booking flights, comparing prices, selecting seats

### hotel_reservation
**Purpose:** Hotel search, room booking, amenities, check-in/out
**Keywords:** hotel, accommodation, room, lodging, reservation, stay, check-in
**Use for:** Finding hotels, booking rooms, checking amenities

### itinerary_generation
**Purpose:** Travel planning, scheduling, route optimization
**Keywords:** itinerary, schedule, plan, route, activities, sightseeing
**Use for:** Creating day-by-day plans, organizing activities

### travel_insurance
**Purpose:** Travel insurance options, coverage, claims
**Keywords:** insurance, coverage, protection, medical, cancellation, claim
**Use for:** Insurance recommendations, comparing policies

### budget_tracking
**Purpose:** Travel budget planning, expense tracking
**Keywords:** budget, cost, expense, price, spending, money
**Use for:** Estimating costs, tracking expenses

## Routing Logic

The router analyzes your question and activates relevant skills:

| Query Pattern | Activated Skills |
|--------------|------------------|
| "Find flights to [destination]" | flight_booking |
| "Book hotel in [city]" | hotel_reservation |
| "Plan [duration] trip to [destination]" | itinerary_generation |
| "Need travel insurance" | travel_insurance |
| "How much will trip cost?" | budget_tracking |
| "Plan complete Paris vacation" | ALL (coordinated) |

## Multi-Skill Coordination

Some requests require multiple skills working together:

### Complete Trip Planning
1. **budget_tracking** - Set budget constraints
2. **flight_booking** - Find flights within budget
3. **hotel_reservation** - Book accommodation
4. **itinerary_generation** - Create daily schedule
5. **travel_insurance** - Recommend coverage

### Booking Modification
1. **flight_booking** - Check flight change fees
2. **hotel_reservation** - Verify cancellation policy
3. **budget_tracking** - Calculate cost impact

## Usage Examples

**Simple (single skill):**
- "Find direct flights to Tokyo" → flight_booking
- "5-star hotels in Paris under $200/night" → hotel_reservation
- "Create 3-day Rome itinerary" → itinerary_generation

**Complex (multiple skills):**
- "Plan week-long Paris trip for 2, budget $3000" → budget_tracking → flight_booking → hotel_reservation → itinerary_generation
- "Cheapest way to visit London next month" → budget_tracking + flight_booking + hotel_reservation

## Quick Reference

### Flight Booking
- Search flights by route, dates, airline
- Compare prices across carriers
- Select seats, meals, baggage

### Hotel Reservation
- Filter by price, rating, amenities
- Check availability, reviews
- Book rooms with cancellation policy

### Itinerary Planning
- Generate day-by-day schedules
- Optimize routes between attractions
- Balance activities with free time

### Travel Insurance
- Compare coverage options
- Understand medical, cancellation policies
- File claims if needed

### Budget Tracking
- Estimate total trip cost
- Track expenses vs budget
- Optimize spending

## Working with This Skill

**Beginners:** Start with single-purpose queries ("Find flights to Paris")
**Intermediate:** Combine 2-3 aspects ("Find flights and hotel in Tokyo")
**Advanced:** Request complete trip planning with multiple constraints

The router handles complexity automatically - just ask naturally!
```

#### flight_booking.md (Sub-Skill)

```markdown
---
name: flight_booking
description: Flight search, booking, and airline comparisons
---

# Flight Booking

## When to Use This Skill

Use when searching for flights, comparing airlines, booking tickets, or managing flight reservations.

## Quick Reference

### Searching Flights

**Search by route:**
```
Find flights from [origin] to [destination]
Examples:
- "Flights from NYC to London"
- "JFK to Heathrow direct flights"
```

**Search with dates:**
```
Flights from [origin] to [destination] on [date]
Examples:
- "Flights from LAX to Paris on June 15"
- "Return flights NYC to Tokyo, depart May 1, return May 15"
```

**Filter by preferences:**
```
[direct/nonstop] flights from [origin] to [destination]
[airline] flights to [destination]
Cheapest/fastest flights to [destination]

Examples:
- "Direct flights from Boston to Dublin"
- "Delta flights to Seattle"
- "Cheapest flights to Miami next month"
```

### Booking Process

1. **Search** - Find flights matching criteria
2. **Compare** - Review prices, times, airlines
3. **Select** - Choose specific flight
4. **Customize** - Add seat, baggage, meals
5. **Confirm** - Book and receive confirmation

### Price Comparison

Compare across:
- Airlines (Delta, United, American, etc.)
- Booking sites (Expedia, Kayak, etc.)
- Direct vs connections
- Dates (flexible date search)
- Classes (Economy, Business, First)

### Seat Selection

Options:
- Window, aisle, middle
- Extra legroom
- Bulkhead, exit row
- Section preferences (front, middle, rear)

## Key Concepts

### Flight Types
- **Direct** - No stops, same plane
- **Nonstop** - Same as direct
- **Connecting** - One or more stops, change planes
- **Multi-city** - Different return city
- **Open-jaw** - Different origin/destination cities

### Fare Classes
- **Basic Economy** - Cheapest, most restrictions
- **Economy** - Standard coach
- **Premium Economy** - Extra space, amenities
- **Business** - Lie-flat seats, premium service
- **First Class** - Maximum luxury

### Booking Terms
- **Fare rules** - Cancellation, change policies
- **Baggage allowance** - Checked and carry-on limits
- **Layover** - Time between connecting flights
- **Codeshare** - Same flight, different airline numbers

## Working with This Skill

### For Beginners
Start with simple searches:
1. State origin and destination
2. Provide travel dates
3. Mention any preferences (direct, airline)

The skill will guide you through options step-by-step.

### For Intermediate Users
Provide more details upfront:
- Preferred airlines or alliances
- Class of service
- Maximum connections
- Price range
- Specific times of day

### For Advanced Users
Complex multi-city routing:
- Multiple destinations
- Open-jaw bookings
- Award ticket searches
- Specific aircraft types
- Detailed fare class codes

## Reference Files

All flight booking documentation is in `references/`:

- `flight_search.md` - Search strategies, filters
- `airline_policies.md` - Carrier-specific rules
- `booking_process.md` - Step-by-step booking
- `seat_selection.md` - Seating guides
- `fare_classes.md` - Ticket types, restrictions
- `baggage_rules.md` - Luggage policies
- `frequent_flyer.md` - Loyalty programs
```

---

## Implementation Guide

### Step 1: Identify Split Points

**Analyze your monolithic skill:**

1. List all major responsibilities
2. Group related functionality
3. Identify natural boundaries
4. Count lines per group

**Example:**

```
user_management.md (1800 lines)
├── Authentication (450 lines) ← Sub-skill
├── Profile CRUD (380 lines) ← Sub-skill
├── Permissions (320 lines) ← Sub-skill
├── Notifications (280 lines) ← Sub-skill
└── Activity logs (370 lines) ← Sub-skill
```

### Step 2: Extract Sub-Skills

**For each identified group:**

1. Create new `{subskill}.md` file
2. Copy relevant content
3. Add proper frontmatter
4. Ensure 200-500 line range
5. Remove dependencies on other groups

**Template:**

```markdown
---
name: {subskill_name}
description: {clear, specific description}
---

# {Subskill Title}

## When to Use This Skill
[Specific use cases]

## Quick Reference
[Common operations]

## Key Concepts
[Domain terms]

## Working with This Skill
[Usage guidance by skill level]

## Reference Files
[Documentation structure]
```

### Step 3: Create Router

**Router skill template:**

```markdown
---
name: {router_name}
description: {overall system description}
---

# {System Name} (Router)

## When to Use This Skill
{High-level description}

This is a router skill that directs queries to specialized sub-skills.

## Available Sub-Skills

### {subskill_1}
**Purpose:** {What it does}
**Keywords:** {routing, keywords, here}
**Use for:** {When to use}

### {subskill_2}
[Same pattern]

## Routing Logic

Based on query keywords:
- {keyword_group_1} → {subskill_1}
- {keyword_group_2} → {subskill_2}
- Multiple matches → Coordinate relevant skills

## Multi-Skill Operations

{Describe when multiple skills work together}

## Usage Examples

**Single skill:**
- "{example_query_1}" → {subskill_1}
- "{example_query_2}" → {subskill_2}

**Multiple skills:**
- "{complex_query}" → {subskill_1} + {subskill_2}
```

### Step 4: Define Routing Keywords

**Best practices:**

- Use 5-10 keywords per sub-skill
- Include synonyms and variations
- Be specific, not generic
- Test with real queries

**Example:**

```markdown
### user_authentication
**Keywords:**
- Primary: login, logout, signin, signout, authenticate
- Secondary: password, credentials, session, token
- Variations: log-in, log-out, sign-in, sign-out
```

### Step 5: Test Routing

**Create test queries:**

```markdown
## Test Routing (Internal Notes)

Should route to user_authentication:
✓ "How do I log in?"
✓ "User login process"
✓ "Authentication failed"

Should route to user_profiles:
✓ "Update user profile"
✓ "Change profile picture"

Should route to multiple skills:
✓ "Create account and set up profile" → user_authentication + user_profiles
```

### Step 6: Update References

**In each sub-skill:**

1. Link to router for context
2. Reference related sub-skills
3. Update navigation paths

```markdown
## Related Skills

This skill is part of the {System Name} suite:
- **Router:** {router_name} - Main entry point
- **Related:** {related_subskill} - For {use case}
```

---

## Troubleshooting

### Router Not Activating Correct Sub-Skill

**Problem:** Query routed to wrong sub-skill

**Solutions:**
1. Add missing keywords to router
2. Use more specific routing keywords
3. Add disambiguation examples
4. Test with variations of query phrasing

### Sub-Skills Too Granular

**Problem:** Too many tiny sub-skills (< 200 lines each)

**Solution:**
- Merge related sub-skills
- Use sections within single skill instead
- Aim for 300-500 lines per sub-skill

### Sub-Skills Too Large

**Problem:** Sub-skills still exceeding 500 lines

**Solution:**
- Further split into more granular concerns
- Consider 3-tier architecture (router → category routers → specific skills)
- Move reference documentation to separate files

### Cross-Skill Dependencies

**Problem:** Sub-skills frequently need each other

**Solutions:**
1. Create shared reference documentation
2. Use router to coordinate multi-skill operations
3. Reconsider split boundaries (may be too granular)

### Router Logic Too Complex

**Problem:** Router has extensive conditional logic

**Solution:**
- Simplify to keyword-based routing
- Create intermediate routers (2-tier)
- Document explicit routing table

**Example 2-tier:**

```
main_router.md
├── user_features_router.md
│   ├── authentication.md
│   ├── profiles.md
│   └── permissions.md
└── admin_features_router.md
    ├── analytics.md
    ├── reporting.md
    └── configuration.md
```

---

## Adapting Auto-Generated Routers

Skill Seeker auto-generates router skills for large documentation using `generate_router.py`.

**You can adapt this for manual skills:**

### 1. Study the Pattern

```bash
# Generate a router from documentation configs
python3 cli/split_config.py configs/godot.json --strategy router
python3 cli/generate_router.py configs/godot-*.json

# Examine generated router SKILL.md
cat output/godot/SKILL.md
```

### 2. Extract the Template

The generated router has:
- Sub-skill descriptions
- Keyword-based routing
- Usage examples
- Multi-skill coordination notes

### 3. Customize for Your Use Case

Replace documentation-specific content with your application logic:

```markdown
# Generated (documentation):
### godot-scripting
GDScript programming, signals, nodes
Keywords: gdscript, code, script, programming

# Customized (your app):
### order_processing
Process customer orders, payments, fulfillment
Keywords: order, purchase, payment, checkout, fulfillment
```

---

## Summary

### Key Takeaways

1. ✅ **500-line guideline** is important for optimal Claude performance
2. ✅ **Router pattern** enables sophisticated applications while staying within limits
3. ✅ **Single responsibility** - Each sub-skill does one thing well
4. ✅ **Context efficiency** - Only load what's needed per task
5. ✅ **Proven approach** - Already used successfully for large documentation

### When to Apply This Pattern

**Do use skill layering when:**
- Skill exceeds 500 lines
- Multiple distinct responsibilities
- Different parts rarely used together
- Team wants modular maintenance

**Don't use skill layering when:**
- Skill under 500 lines
- Single, cohesive responsibility
- All content frequently relevant together
- Simplicity is priority

### Next Steps

1. Review your existing skills for split candidates
2. Create router + sub-skills following templates above
3. Test routing with real queries
4. Refine keywords based on usage
5. Iterate and improve

---

## Additional Resources

- **Auto-Generated Routers:** See `docs/LARGE_DOCUMENTATION.md` for automated splitting of scraped documentation
- **Router Implementation:** See `src/skill_seekers/cli/generate_router.py` for reference implementation
- **Examples:** See configs in `configs/` for real-world router patterns

**Questions or feedback?** Open an issue on GitHub!
