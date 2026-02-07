# Windsurf + FastAPI Context Example

Complete example showing how to use Skill Seekers to generate Windsurf rules for FastAPI development.

## What This Example Does

- ✅ Generates FastAPI documentation skill
- ✅ Creates modular .windsurfrules for Windsurf IDE
- ✅ Shows Cascade AI-powered FastAPI code generation
- ✅ Handles character limits with split rules

## Quick Start

### 1. Generate FastAPI Skill

```bash
# Install Skill Seekers
pip install skill-seekers

# Generate FastAPI documentation skill
skill-seekers scrape --config configs/fastapi.json

# Package for Windsurf with split rules (respects 6K char limit)
skill-seekers package output/fastapi --target markdown --split-rules
```

### 2. Copy to Windsurf Project

```bash
# Create rules directory
mkdir -p my-fastapi-project/.windsurf/rules

# Copy all rule files
cp -r output/fastapi-markdown/rules/* my-fastapi-project/.windsurf/rules/

# Or use the automation script
python generate_windsurfrules.py --project my-fastapi-project
```

### 3. Test in Windsurf

```bash
# Open project in Windsurf
windsurf my-fastapi-project/

# Start Cascade (Cmd+L or Ctrl+L)
# Try these prompts:
# - "Create a FastAPI endpoint with async database queries"
# - "Add Pydantic models with validation for user registration"
# - "Implement JWT authentication with dependencies"
```

## Expected Results

### Before (Without Rules)

**Prompt:** "Create a FastAPI user endpoint with database"

**Cascade Output:**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    # Generic sync code
    users = db.query(User).all()
    return users
```

❌ Uses sync code (not async)
❌ No dependency injection
❌ Returns ORM instances (not Pydantic)

### After (With Rules)

**Prompt:** "Create a FastAPI user endpoint with database"

**Cascade Output:**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import UserResponse

router = APIRouter(prefix="/api/v1")

@router.get("/users", response_model=list[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all users with pagination."""
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    return [UserResponse.model_validate(user) for user in users]
```

✅ Async/await pattern
✅ Dependency injection
✅ Pydantic response models
✅ Proper pagination
✅ OpenAPI documentation

## Files in This Example

- `generate_windsurfrules.py` - Automation script for generating rules
- `requirements.txt` - Python dependencies
- `example-project/` - Minimal FastAPI project structure
  - `app/main.py` - FastAPI application
  - `app/models.py` - SQLAlchemy models
  - `app/schemas.py` - Pydantic schemas
  - `app/database.py` - Database connection

## Rule Files Generated

After running the script, you'll have:

```
my-fastapi-project/.windsurf/rules/
├── fastapi-core.md           (5,200 chars, Always On)
├── fastapi-database.md       (5,800 chars, Always On)
├── fastapi-authentication.md (4,900 chars, Model Decision)
├── fastapi-testing.md        (4,100 chars, Manual)
└── fastapi-best-practices.md (3,500 chars, Always On)
```

## Rule Activation Modes

| File | Activation | When Used |
|------|-----------|-----------|
| `fastapi-core.md` | Always On | Every request - core patterns |
| `fastapi-database.md` | Always On | Database-related code |
| `fastapi-authentication.md` | Model Decision | When Cascade detects auth needs |
| `fastapi-testing.md` | Manual | Only when @mentioned for testing |
| `fastapi-best-practices.md` | Always On | Code quality, error handling |

## Customization

### Add Project-Specific Patterns

Create `project-conventions.md`:

```markdown
---
name: "Project Conventions"
activation: "always-on"
priority: "highest"
---

# Project-Specific Patterns

## Database Sessions

ALWAYS use this pattern:

\```python
async with get_session() as db:
    result = await db.execute(query)
\```

## API Versioning

All endpoints MUST use `/api/v1` prefix:

\```python
router = APIRouter(prefix="/api/v1")
\```
```

### Adjust Character Limits

```bash
# Generate smaller rule files (5K chars each)
skill-seekers package output/fastapi --target markdown --split-rules --max-chars 5000

# Generate larger rule files (5.5K chars each)
skill-seekers package output/fastapi --target markdown --split-rules --max-chars 5500
```

## Troubleshooting

### Issue: Rules not loading

**Solution 1:** Verify directory structure
```bash
# Must be exactly:
my-project/.windsurf/rules/*.md

# Check:
ls -la my-project/.windsurf/rules/
```

**Solution 2:** Reload Windsurf
```
Cmd+Shift+P → "Reload Window"
```

### Issue: Character limit exceeded

**Solution:** Re-generate with smaller max-chars
```bash
skill-seekers package output/fastapi --target markdown --split-rules --max-chars 4500
```

### Issue: Cascade not using rules

**Solution:** Check activation mode in frontmatter
```markdown
---
activation: "always-on"  # Not "model-decision"
priority: "high"
---
```

## Advanced Usage

### Combine with MCP Server

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

Now Cascade can query documentation dynamically via MCP tools.

### Multi-Framework Project

```bash
# Generate backend rules (FastAPI)
skill-seekers package output/fastapi --target markdown --split-rules

# Generate frontend rules (React)
skill-seekers package output/react --target markdown --split-rules

# Organize rules:
.windsurf/rules/
├── backend/
│   ├── fastapi-core.md
│   └── fastapi-database.md
└── frontend/
    ├── react-hooks.md
    └── react-components.md
```

## Related Examples

- [Cursor Example](../cursor-react-skill/) - Similar IDE, different format
- [Cline Example](../cline-django-assistant/) - VS Code extension with MCP
- [Continue.dev Example](../continue-dev-universal/) - IDE-agnostic
- [LangChain RAG Example](../langchain-rag-pipeline/) - Build RAG systems

## Next Steps

1. Customize rules for your project patterns
2. Add team-specific conventions
3. Integrate with MCP for live documentation
4. Build RAG pipeline with `--target langchain`
5. Share your rules at [Windsurf Rules Directory](https://windsurf.com/editor/directory)

## Support

- **Skill Seekers Issues:** [GitHub](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
- **Windsurf Docs:** [docs.windsurf.com](https://docs.windsurf.com/)
- **Integration Guide:** [WINDSURF.md](../../docs/integrations/WINDSURF.md)
