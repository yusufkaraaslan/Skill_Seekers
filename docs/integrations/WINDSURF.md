# Using Skill Seekers with Windsurf IDE

**Last Updated:** February 7, 2026
**Status:** Production Ready
**Difficulty:** Easy ⭐

---

## 🎯 The Problem

Windsurf IDE (by Codeium) offers powerful AI flows and Cascade agent, but:

- **Generic Knowledge** - AI doesn't know your project-specific frameworks or internal patterns
- **Manual Context** - Copy-pasting documentation into chat is tedious and breaks flow
- **Limited Memory** - Memory feature requires manual teaching through conversations
- **Context Limits** - Rules files are limited to 12,000 characters combined

**Example:**
> "When building a FastAPI app in Windsurf, Cascade might suggest outdated patterns or miss framework-specific best practices. You want the AI to reference comprehensive documentation without hitting character limits."

---

## ✨ The Solution

Use Skill Seekers to create **custom rules** for Windsurf's Cascade agent:

1. **Generate structured docs** from any framework or codebase
2. **Package as .windsurfrules** - Windsurf's markdown rules format
3. **Automatic Context** - Cascade references your docs in AI flows
4. **Modular Rules** - Split large docs into multiple rule files (6K chars each)

**Result:**
Windsurf's Cascade becomes an expert in your frameworks with persistent, automatic context that fits within character limits.

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites

- Windsurf IDE installed (https://windsurf.com/)
- Python 3.10+ (for Skill Seekers)

### Installation

```bash
# Install Skill Seekers
pip install skill-seekers

# Verify installation
skill-seekers --version
```

### Generate .windsurfrules

```bash
# Example: FastAPI framework
skill-seekers scrape --config configs/fastapi.json

# Package for Windsurf (markdown format)
skill-seekers package output/fastapi --target markdown

# Extract SKILL.md
# output/fastapi-markdown/SKILL.md
```

### Setup in Windsurf

**Option 1: Project-Specific Rules** (recommended)

```bash
# Create rules directory
mkdir -p /path/to/your/project/.windsurf/rules

# Copy as rules.md
cp output/fastapi-markdown/SKILL.md /path/to/your/project/.windsurf/rules/fastapi.md
```

**Option 2: Legacy .windsurfrules** (single file)

```bash
# Copy to project root (legacy format)
cp output/fastapi-markdown/SKILL.md /path/to/your/project/.windsurfrules
```

**Option 3: Split Large Documentation** (for >6K char files)

```bash
# Skill Seekers automatically splits large files
skill-seekers package output/react --target markdown --split-rules

# This creates multiple rule files:
# output/react-markdown/rules/
#   ├── core-concepts.md      (5,800 chars)
#   ├── hooks-reference.md    (5,400 chars)
#   ├── components-guide.md   (5,900 chars)
#   └── best-practices.md     (4,200 chars)

# Copy all rules
cp -r output/react-markdown/rules/* /path/to/your/project/.windsurf/rules/
```

### Test in Windsurf

1. Open your project in Windsurf
2. Start Cascade (Cmd+L or Ctrl+L)
3. Test knowledge:
   ```
   "Create a FastAPI endpoint with async database queries using best practices"
   ```
4. Verify Cascade references your documentation

---

## 📖 Detailed Setup Guide

### Step 1: Choose Your Documentation Source

**Option A: Use Preset Configs** (24+ frameworks)

```bash
# List available presets
ls configs/

# Popular presets:
# - react.json, vue.json, angular.json (Frontend)
# - django.json, fastapi.json, flask.json (Backend)
# - godot.json, unity.json (Game Development)
# - kubernetes.json, docker.json (Infrastructure)
```

**Option B: Custom Documentation**

Create `myframework-config.json`:

```json
{
  "name": "myframework",
  "description": "Custom framework documentation for Windsurf",
  "base_url": "https://docs.myframework.com/",
  "selectors": {
    "main_content": "article",
    "title": "h1",
    "code_blocks": "pre code"
  },
  "categories": {
    "getting_started": ["intro", "quickstart", "installation"],
    "core_concepts": ["concepts", "architecture", "patterns"],
    "api": ["api", "reference", "methods"],
    "guides": ["guide", "tutorial", "how-to"],
    "best_practices": ["best-practices", "tips", "patterns"]
  }
}
```

**Option C: GitHub Repository**

```bash
# Analyze open-source codebase
skill-seekers github --repo facebook/react

# Or local codebase
skill-seekers analyze --directory /path/to/repo --comprehensive
```

### Step 2: Optimize for Windsurf

**Character Limit Awareness**

Windsurf has strict limits:
- **Per rule file:** 6,000 characters max
- **Combined global + local:** 12,000 characters max

**Use split-rules flag:**

```bash
# Automatically split large documentation
skill-seekers package output/django --target markdown --split-rules

# This creates modular rules:
# - core-concepts.md      (Always On)
# - api-reference.md      (Model Decision)
# - best-practices.md     (Always On)
# - troubleshooting.md    (Manual @mention)
```

**Rule Activation Modes**

Configure each rule file's activation mode in frontmatter:

```markdown
---
name: "FastAPI Core Concepts"
activation: "always-on"
priority: "high"
---

# FastAPI Framework Expert

You are an expert in FastAPI...
```

Activation modes:
- **Always On** - Applied to every request (use for core concepts)
- **Model Decision** - AI decides when to use (use for specialized topics)
- **Manual** - Only when @mentioned (use for troubleshooting)
- **Scheduled** - Time-based activation (use for context switching)

### Step 3: Configure Windsurf Settings

**Enable Rules**

1. Open Windsurf Settings (Cmd+, or Ctrl+,)
2. Search for "rules"
3. Enable "Use Custom Rules"
4. Set rules directory: `.windsurf/rules`

**Memory Integration**

Combine rules with Windsurf's Memory feature:

```bash
# Generate initial rules from docs
skill-seekers package output/fastapi --target markdown

# Windsurf Memory learns from your usage:
# - Coding patterns you use frequently
# - Variable naming conventions
# - Architecture decisions
# - Team-specific practices

# Rules provide documentation, Memory provides personalization
```

**MCP Server Integration**

For live documentation access:

```bash
# Install Skill Seekers MCP server
pip install skill-seekers[mcp]

# Configure in Windsurf's mcp_config.json
{
  "mcpServers": {
    "skill-seekers": {
      "command": "python",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp", "--transport", "stdio"]
    }
  }
}
```

### Step 4: Test and Refine

**Test Cascade Knowledge**

```bash
# Start Cascade (Cmd+L)
# Ask framework-specific questions:

"Show me FastAPI async database patterns"
"Create a React component with TypeScript best practices"
"Implement Django REST framework viewset with pagination"
```

**Refine Rules**

```bash
# Add project-specific patterns
cat >> .windsurf/rules/project-conventions.md << 'EOF'
---
name: "Project Conventions"
activation: "always-on"
priority: "highest"
---

# Project-Specific Patterns

## Database Models
- Always use async SQLAlchemy
- Include created_at/updated_at timestamps
- Add __repr__ for debugging

## API Endpoints
- Use dependency injection for database sessions
- Return Pydantic models, not ORM instances
- Include OpenAPI documentation strings
EOF

# Reload Windsurf window (Cmd+Shift+P → "Reload Window")
```

**Monitor Character Usage**

```bash
# Check rule file sizes
find .windsurf/rules -name "*.md" -exec wc -c {} \;

# Ensure no file exceeds 6,000 characters
# If too large, split further:
skill-seekers package output/react --target markdown --split-rules --max-chars 5000
```

---

## 🎨 Advanced Usage

### Multi-Framework Projects

**Backend + Frontend Stack**

```bash
# Generate backend rules (FastAPI)
skill-seekers scrape --config configs/fastapi.json
skill-seekers package output/fastapi --target markdown --split-rules

# Generate frontend rules (React)
skill-seekers scrape --config configs/react.json
skill-seekers package output/react --target markdown --split-rules

# Organize rules directory:
.windsurf/rules/
├── backend/
│   ├── fastapi-core.md          (Always On)
│   ├── fastapi-database.md      (Model Decision)
│   └── fastapi-testing.md       (Manual)
├── frontend/
│   ├── react-hooks.md           (Always On)
│   ├── react-components.md      (Model Decision)
│   └── react-performance.md     (Manual)
└── project/
    └── conventions.md           (Always On, Highest Priority)
```

### Dynamic Context per Workflow

**Context Switching Based on Task**

```markdown
---
name: "Testing Context"
activation: "model-decision"
description: "Use when user is writing or debugging tests"
keywords: ["test", "pytest", "unittest", "mock", "fixture"]
---

# Testing Best Practices

When writing tests, follow these patterns...
```

**Scheduled Rules for Time-Based Context**

```markdown
---
name: "Code Review Mode"
activation: "scheduled"
schedule: "0 14 * * 1-5"  # 2 PM on weekdays
priority: "high"
---

# Code Review Checklist

During code review, verify:
- Type annotations are complete
- Tests cover edge cases
- Documentation is updated
```

### Windsurf + RAG Pipeline

**Combine Rules with Vector Search**

```python
# Use Skill Seekers to create both:
# 1. Windsurf rules (for Cascade context)
# 2. RAG chunks (for deep search)

from skill_seekers.cli.doc_scraper import main as scrape
from skill_seekers.cli.package_skill import main as package
from skill_seekers.cli.adaptors import get_adaptor

# Scrape documentation
scrape(["--config", "configs/react.json"])

# Create Windsurf rules
package(["output/react", "--target", "markdown", "--split-rules"])

# Also create RAG pipeline for deep search
package(["output/react", "--target", "langchain", "--chunk-for-rag"])

# Now you have:
# - .windsurf/rules/*.md (for Cascade)
# - output/react-langchain/ (for custom RAG search)
```

**MCP Tool for Dynamic Context**

Create custom MCP tool that queries RAG pipeline:

```python
# mcp_custom_search.py
from skill_seekers.mcp.tools import search_docs

@mcp.tool()
def search_react_docs(query: str) -> str:
    """Search React documentation for specific patterns."""
    # Query your RAG pipeline
    results = vector_store.similarity_search(query, k=5)
    return "\n\n".join([doc.page_content for doc in results])
```

Register in `mcp_config.json`:

```json
{
  "mcpServers": {
    "custom-search": {
      "command": "python",
      "args": ["mcp_custom_search.py"]
    }
  }
}
```

---

## 💡 Best Practices

### 1. Keep Rules Focused

**Bad: Single Monolithic Rule (15,000 chars - exceeds limit!)**

```markdown
---
name: "Everything React"
---
# React Framework (Complete Guide)
[... 15,000 characters of documentation ...]
```

**Good: Modular Rules (5,000 chars each)**

```markdown
<!-- react-core.md (5,200 chars) -->
---
name: "React Core Concepts"
activation: "always-on"
---
# React Fundamentals
[... focused on hooks, components, state ...]

<!-- react-performance.md (4,800 chars) -->
---
name: "React Performance"
activation: "model-decision"
description: "Use when optimizing React performance"
---
# Performance Optimization
[... focused on memoization, lazy loading ...]

<!-- react-testing.md (5,100 chars) -->
---
name: "React Testing"
activation: "manual"
---
# Testing React Components
[... focused on testing patterns ...]
```

### 2. Use Activation Modes Wisely

| Mode | Use Case | Example |
|------|----------|---------|
| **Always On** | Core concepts, common patterns | Framework fundamentals, project conventions |
| **Model Decision** | Specialized topics | Performance optimization, advanced patterns |
| **Manual** | Troubleshooting, rare tasks | Debugging guides, migration docs |
| **Scheduled** | Time-based context | Code review checklists, release procedures |

### 3. Prioritize Rules

```markdown
---
name: "Project Conventions"
activation: "always-on"
priority: "highest"  # This overrides framework defaults
---

# Project-Specific Rules

Always use:
- Async/await for all database operations
- Pydantic V2 (not V1)
- pytest-asyncio for async tests
```

### 4. Include Code Examples

**Don't just describe patterns:**

```markdown
## Creating Database Models

Use SQLAlchemy with async patterns.
```

**Show actual code:**

```markdown
## Creating Database Models

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User(email='{self.email}')>"

# Usage in endpoint
async def create_user(email: str, db: AsyncSession):
    user = User(email=email)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
```
\```

Use this pattern in all endpoints.
```

### 5. Update Rules Regularly

```bash
# Framework updates quarterly
skill-seekers scrape --config configs/react.json
skill-seekers package output/react --target markdown --split-rules

# Check what changed
diff -r .windsurf/rules/react-old/ .windsurf/rules/react-new/

# Merge updates
cp -r .windsurf/rules/react-new/* .windsurf/rules/

# Test with Cascade
# Ask: "What's new in React 19?"
```

---

## 🔥 Real-World Examples

### Example 1: FastAPI + PostgreSQL Microservice

**Project Structure:**

```
my-api/
├── .windsurf/
│   └── rules/
│       ├── fastapi-core.md       (5,200 chars, Always On)
│       ├── fastapi-database.md   (5,800 chars, Always On)
│       ├── fastapi-testing.md    (4,100 chars, Manual)
│       └── project-conventions.md (3,500 chars, Always On, Highest)
├── app/
│   ├── models.py
│   ├── schemas.py
│   └── routers/
└── tests/
```

**fastapi-core.md**

```markdown
---
name: "FastAPI Core Patterns"
activation: "always-on"
priority: "high"
---

# FastAPI Expert

You are an expert in FastAPI. Use these patterns:

## Endpoint Structure

Always use dependency injection:

\```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/api/v1")

@router.post("/users/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user."""
    # Implementation
\```

## Error Handling

Use HTTPException with proper status codes:

\```python
from fastapi import HTTPException

if not user:
    raise HTTPException(
        status_code=404,
        detail="User not found"
    )
\```
```

**project-conventions.md**

```markdown
---
name: "Project Conventions"
activation: "always-on"
priority: "highest"
---

# Project-Specific Patterns

## Database Sessions

ALWAYS use async sessions with context managers:

\```python
async with get_session() as db:
    result = await db.execute(query)
\```

## Response Models

NEVER return ORM instances directly. Use Pydantic:

\```python
# BAD
return user  # SQLAlchemy model

# GOOD
return UserResponse.model_validate(user)
\```

## Testing

All tests MUST use pytest-asyncio:

\```python
import pytest

@pytest.mark.asyncio
async def test_create_user():
    # Test implementation
\```
```

**Result:**

When you ask Cascade:
> "Create an endpoint to list all users with pagination"

Cascade will:
1. ✅ Use async/await (from project-conventions.md)
2. ✅ Add dependency injection (from fastapi-core.md)
3. ✅ Return Pydantic models (from project-conventions.md)
4. ✅ Use proper database patterns (from fastapi-database.md)

### Example 2: Godot Game Engine

**Godot-Specific Rules**

```bash
# Generate Godot documentation + codebase analysis
skill-seekers github --repo godotengine/godot-demo-projects
skill-seekers package output/godot-demo-projects --target markdown --split-rules

# Create rules structure:
.windsurf/rules/
├── godot-core.md           (GDScript syntax, node system)
├── godot-signals.md        (Signal patterns, EventBus)
├── godot-scenes.md         (Scene tree, node access)
└── project-patterns.md     (Custom patterns from codebase)
```

**godot-signals.md**

```markdown
---
name: "Godot Signal Patterns"
activation: "model-decision"
description: "Use when working with signals and events"
keywords: ["signal", "connect", "emit", "EventBus"]
---

# Godot Signal Patterns

## Signal Declaration

\```gdscript
signal health_changed(new_health: int, max_health: int)
signal item_collected(item_type: String, quantity: int)
\```

## Connection Pattern

\```gdscript
func _ready():
    player.health_changed.connect(_on_health_changed)

func _on_health_changed(new_health: int, max_health: int):
    health_bar.value = (new_health / float(max_health)) * 100
\```

## EventBus Pattern (from codebase analysis)

\```gdscript
# EventBus.gd (autoload singleton)
extends Node

signal game_started
signal game_over(score: int)
signal player_died

# Usage in game scenes:
EventBus.game_started.emit()
EventBus.game_over.emit(final_score)
\```
```

---

## 🐛 Troubleshooting

### Issue: Rules Not Loading

**Symptoms:**
- Cascade doesn't reference documentation
- Rules directory exists but ignored

**Solutions:**

1. **Check rules directory location**
   ```bash
   # Must be exactly:
   .windsurf/rules/

   # Not:
   .windsurf/rule/  # Missing 's'
   windsurf/rules/  # Missing leading dot
   ```

2. **Verify file extensions**
   ```bash
   # Rules must be .md files
   ls .windsurf/rules/
   # Should show: fastapi.md, react.md, etc.
   # NOT: fastapi.txt, rules.json
   ```

3. **Check Windsurf settings**
   ```
   Cmd+, → Search "rules" → Enable "Use Custom Rules"
   ```

4. **Reload Windsurf**
   ```
   Cmd+Shift+P → "Reload Window"
   ```

5. **Verify frontmatter syntax**
   ```markdown
   ---
   name: "Rule Name"
   activation: "always-on"
   ---

   # Content starts here
   ```

### Issue: Rules Exceeding Character Limit

**Error:**
> "Rule file exceeds 6,000 character limit"

**Solutions:**

1. **Use split-rules flag**
   ```bash
   skill-seekers package output/react --target markdown --split-rules
   ```

2. **Set custom max-chars**
   ```bash
   skill-seekers package output/django --target markdown --split-rules --max-chars 5000
   ```

3. **Manual splitting**
   ```bash
   # Split SKILL.md by sections
   csplit SKILL.md '/^## /' '{*}'

   # Rename files
   mv xx00 core-concepts.md
   mv xx01 api-reference.md
   mv xx02 best-practices.md
   ```

4. **Use activation modes strategically**
   ```markdown
   <!-- Keep core concepts Always On -->
   ---
   name: "Core Concepts"
   activation: "always-on"
   ---

   <!-- Make specialized topics Manual -->
   ---
   name: "Advanced Patterns"
   activation: "manual"
   ---
   ```

### Issue: Cascade Not Using Rules

**Symptoms:**
- Rules loaded but AI doesn't reference them
- Generic responses despite custom documentation

**Solutions:**

1. **Check activation mode**
   ```markdown
   # Change from Model Decision to Always On
   ---
   activation: "always-on"  # Not "model-decision"
   ---
   ```

2. **Increase priority**
   ```markdown
   ---
   priority: "highest"  # Override framework defaults
   ---
   ```

3. **Add explicit instructions**
   ```markdown
   # FastAPI Expert

   You MUST follow these patterns in all FastAPI code:
   - Use async/await
   - Dependency injection for database
   - Pydantic response models
   ```

4. **Test with explicit mention**
   ```
   In Cascade chat:
   "@fastapi Create an endpoint with async database access"
   ```

5. **Combine with Memory**
   ```
   Ask Cascade to remember:
   "Remember to always use the patterns from fastapi.md rules file"
   ```

### Issue: Conflicting Rules

**Symptoms:**
- AI mixes patterns from different frameworks
- Inconsistent code suggestions

**Solutions:**

1. **Use priority levels**
   ```markdown
   <!-- project-conventions.md -->
   ---
   priority: "highest"
   ---

   <!-- framework-defaults.md -->
   ---
   priority: "medium"
   ---
   ```

2. **Make project conventions always-on**
   ```markdown
   ---
   name: "Project Conventions"
   activation: "always-on"
   priority: "highest"
   ---

   These rules OVERRIDE all framework defaults:
   - [List project-specific patterns]
   ```

3. **Use model-decision for conflicting patterns**
   ```markdown
   <!-- rest-api.md -->
   ---
   activation: "model-decision"
   description: "Use when creating REST APIs (not GraphQL)"
   ---

   <!-- graphql-api.md -->
   ---
   activation: "model-decision"
   description: "Use when creating GraphQL APIs (not REST)"
   ---
   ```

---

## 📊 Before vs After Comparison

| Aspect | Before Skill Seekers | After Skill Seekers |
|--------|---------------------|---------------------|
| **Context Source** | Copy-paste docs into chat | Automatic rules files |
| **Character Limits** | Hit 12K limit easily | Modular rules fit perfectly |
| **AI Knowledge** | Generic framework patterns | Project-specific best practices |
| **Setup Time** | Manual doc curation (hours) | Automated scraping (5 min) |
| **Consistency** | Varies per conversation | Persistent across all flows |
| **Updates** | Manual doc editing | Re-run scraper for latest docs |
| **Multi-Framework** | Context switching confusion | Separate rule files |
| **Code Quality** | Hit-or-miss | Follows documented patterns |

---

## 🤝 Community & Support

- **Questions:** [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)
- **Issues:** [GitHub Issues](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
- **Website:** [skillseekersweb.com](https://skillseekersweb.com/)
- **Windsurf Docs:** [docs.windsurf.com](https://docs.windsurf.com/)
- **Windsurf Rules Directory:** [windsurf.com/editor/directory](https://windsurf.com/editor/directory)

---

## 📚 Related Guides

- [Cursor Integration](CURSOR.md) - Similar IDE, different rules format
- [Cline Integration](CLINE.md) - VS Code extension with MCP
- [Continue.dev Integration](CONTINUE_DEV.md) - IDE-agnostic AI assistant
- [LangChain Integration](LANGCHAIN.md) - Build RAG pipelines
- [RAG Pipelines Guide](RAG_PIPELINES.md) - End-to-end RAG setup

---

## 📖 Next Steps

1. **Try another framework:** `skill-seekers scrape --config configs/vue.json`
2. **Combine multiple frameworks:** Create modular rules for full-stack projects
3. **Integrate with MCP:** Add live documentation access via MCP servers
4. **Build RAG pipeline:** Use `--target langchain` for deep search
5. **Share your rules:** Contribute to [awesome-windsurfrules](https://github.com/SchneiderSam/awesome-windsurfrules)

---

**Sources:**
- [Windsurf Official Site](https://windsurf.com/)
- [Windsurf Documentation](https://docs.windsurf.com/windsurf/getting-started)
- [Windsurf MCP Setup Guide](https://www.braingrid.ai/blog/windsurf-mcp)
- [Awesome Windsurfrules Repository](https://github.com/SchneiderSam/awesome-windsurfrules)
- [Windsurf Rules Directory](https://windsurf.com/editor/directory)
- [Mastering .windsurfrules Guide](https://blog.stackademic.com/mastering-windsurfrules-react-typescript-projects-aee1e3fe4376)
