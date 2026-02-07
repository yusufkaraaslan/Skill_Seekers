# Cline + Django Assistant Example

Complete example showing how to use Skill Seekers to generate Cline rules for Django development with MCP integration.

## What This Example Does

- ✅ Generates Django documentation skill
- ✅ Creates .clinerules for Cline agent
- ✅ Sets up MCP server for dynamic documentation access
- ✅ Shows autonomous Django code generation

## Quick Start

### 1. Generate Django Skill

```bash
# Install Skill Seekers with MCP support
pip install skill-seekers[mcp]

# Generate Django documentation skill
skill-seekers scrape --config configs/django.json

# Package for Cline (markdown format)
skill-seekers package output/django --target markdown
```

### 2. Copy to Django Project

```bash
# Copy rules to project root
cp output/django-markdown/SKILL.md my-django-project/.clinerules

# Or use the automation script
python generate_clinerules.py --project my-django-project
```

### 3. Configure MCP Server

```bash
# In VS Code Cline panel:
# Settings → MCP Servers → Add Server

# Add this configuration:
{
  "skill-seekers": {
    "command": "python",
    "args": ["-m", "skill_seekers.mcp.server_fastmcp", "--transport", "stdio"],
    "env": {}
  }
}

# Reload VS Code
```

### 4. Test in Cline

```bash
# Open project in VS Code
code my-django-project/

# Open Cline panel (sidebar icon)
# Start autonomous task:

"Create a Django blog app with:
- Post model with author, title, content, created_at
- Comment model with post foreign key
- Admin registration
- REST API with DRF
- Full test suite with pytest"

# Cline will autonomously generate code following Django best practices
```

## Expected Results

### Before (Without .clinerules)

**Cline Task:** "Create a Django user model"

**Output:**
```python
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
```

❌ Missing timestamps
❌ No __str__ method
❌ No Meta class
❌ Not using AbstractUser

### After (With .clinerules)

**Cline Task:** "Create a Django user model"

**Output:**
```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username
```

✅ Uses AbstractUser
✅ Includes timestamps
✅ Has __str__ method
✅ Proper Meta class
✅ Email uniqueness

## Files in This Example

- `generate_clinerules.py` - Automation script
- `mcp_config.json` - MCP server configuration
- `requirements.txt` - Python dependencies
- `example-project/` - Minimal Django project
  - `manage.py`
  - `app/models.py`
  - `app/views.py`
  - `tests/`

## MCP Integration Benefits

With MCP server configured, Cline can:

1. **Search documentation dynamically**
   ```
   Cline task: "Use skill-seekers MCP to search Django async views"
   ```

2. **Generate fresh rules**
   ```
   Cline task: "Use skill-seekers MCP to scrape latest Django 5.0 docs"
   ```

3. **Package skills on-demand**
   ```
   Cline task: "Use skill-seekers MCP to package React docs for this project"
   ```

## Rule Files Structure

After setup, your project has:

```
my-django-project/
├── .clinerules                    # Core Django patterns (auto-loaded)
├── .clinerules.models             # Model-specific patterns (optional)
├── .clinerules.views              # View-specific patterns (optional)
├── .clinerules.testing            # Testing patterns (optional)
├── .clinerules.project            # Project conventions (highest priority)
└── .cline/
    └── memory-bank/               # Persistent project knowledge
        └── README.md
```

Cline automatically loads all `.clinerules*` files.

## Customization

### Add Project-Specific Patterns

Create `.clinerules.project`:

```markdown
# Project-Specific Conventions

## Database Queries

ALWAYS use select_related/prefetch_related:

\```python
# BAD
posts = Post.objects.all()  # N+1 queries!

# GOOD
posts = Post.objects.select_related('author').prefetch_related('comments').all()
\```

## API Responses

NEVER expose sensitive fields:

\```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'bio']
        # NEVER include: password, is_staff, is_superuser
\```
```

### Memory Bank Setup

```bash
# Initialize memory bank
mkdir -p .cline/memory-bank

# Add project context
cat > .cline/memory-bank/README.md << 'EOF'
# Project Memory Bank

## Tech Stack
- Django 5.0
- PostgreSQL 16
- Redis for caching
- Celery for background tasks

## Architecture
- Modular apps (users, posts, comments)
- API-first with Django REST Framework
- Async views for I/O-bound operations

## Conventions
- All models inherit from BaseModel (timestamps)
- Use pytest for testing
- API versioning: /api/v1/
EOF

# Ask Cline to initialize
# In Cline: "Initialize memory bank from README"
```

## Troubleshooting

### Issue: .clinerules not loading

**Solution:** Check file location
```bash
# Must be at project root
ls -la .clinerules

# Reload VS Code
# Cmd+Shift+P → "Developer: Reload Window"
```

### Issue: MCP server not connecting

**Solution 1:** Verify installation
```bash
pip show skill-seekers
# Should show: [mcp] extra installed
```

**Solution 2:** Test MCP server directly
```bash
python -m skill_seekers.mcp.server_fastmcp --transport stdio
# Should start without errors
```

**Solution 3:** Use absolute Python path
```json
{
  "skill-seekers": {
    "command": "/usr/local/bin/python3",
    "args": ["-m", "skill_seekers.mcp.server_fastmcp", "--transport", "stdio"]
  }
}
```

### Issue: Cline not using rules

**Solution:** Add explicit instructions
```markdown
# Django Expert

You MUST follow these patterns in ALL Django code:
- Include timestamps in models
- Use select_related for queries
- Write tests with pytest

NEVER deviate from these patterns.
```

## Advanced Usage

### Multi-Framework Project (Django + React)

```bash
# Backend rules
skill-seekers package output/django --target markdown
cp output/django-markdown/SKILL.md .clinerules.backend

# Frontend rules
skill-seekers package output/react --target markdown
cp output/react-markdown/SKILL.md .clinerules.frontend

# Now Cline knows BOTH Django AND React patterns
```

### Cline + RAG Pipeline

```python
# Create both .clinerules and RAG pipeline
from skill_seekers.cli.doc_scraper import main as scrape
from skill_seekers.cli.package_skill import main as package

# Scrape
scrape(["--config", "configs/django.json"])

# For Cline
package(["output/django", "--target", "markdown"])

# For RAG search
package(["output/django", "--target", "langchain", "--chunk-for-rag"])

# Now you have:
# 1. .clinerules (for Cline context)
# 2. LangChain docs (for deep search)
```

## Real-World Workflow

### Complete Blog API with Cline

**Task:** "Create production-ready blog API"

**Cline Autonomous Steps:**

1. ✅ Creates models (Post, Comment) with timestamps, __str__, Meta
2. ✅ Adds select_related to querysets (from .clinerules)
3. ✅ Creates serializers with nested data (from .clinerules)
4. ✅ Implements ViewSets with filtering (from .clinerules)
5. ✅ Sets up URL routing (from .clinerules)
6. ✅ Writes pytest tests (from .clinerules.testing)
7. ✅ Adds admin registration (from .clinerules)

**Result:** Production-ready API in minutes, following all best practices!

## Related Examples

- [Cursor Example](../cursor-react-skill/) - Similar IDE approach
- [Windsurf Example](../windsurf-fastapi-context/) - Windsurf IDE
- [Continue.dev Example](../continue-dev-universal/) - IDE-agnostic
- [LangChain RAG Example](../langchain-rag-pipeline/) - RAG integration

## Next Steps

1. Add more frameworks (React, Vue) for full-stack
2. Create memory bank for project knowledge
3. Build RAG pipeline with `--target langchain`
4. Share your .clinerules patterns with community
5. Integrate custom MCP tools for project-specific needs

## Support

- **Skill Seekers Issues:** [GitHub](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
- **Cline Docs:** [docs.cline.bot](https://docs.cline.bot/)
- **Integration Guide:** [CLINE.md](../../docs/integrations/CLINE.md)
