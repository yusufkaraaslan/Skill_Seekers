# Using Skill Seekers with Cline (VS Code Extension)

**Last Updated:** February 7, 2026
**Status:** Production Ready
**Difficulty:** Medium ⭐⭐

---

## 🎯 The Problem

Cline (formerly Claude Dev) is a powerful autonomous coding agent for VS Code, but:

- **Generic Knowledge** - AI doesn't know your project-specific frameworks or internal patterns
- **Manual Context** - Copy-pasting documentation into chat breaks autonomous workflow
- **No Framework Memory** - Cline forgets framework details between sessions
- **Custom Instructions Limit** - Built-in custom instructions are limited in scope

**Example:**
> "When using Cline to build a Django app, the agent might use outdated patterns or miss framework-specific conventions. You want Cline to automatically reference comprehensive framework documentation without manual prompting."

---

## ✨ The Solution

Use Skill Seekers to create **custom rules and MCP tools** for Cline:

1. **Generate structured docs** from any framework or codebase
2. **Package as .clinerules** - Cline's markdown rules format
3. **MCP Integration** - Expose documentation via Model Context Protocol
4. **Memory Bank** - Persistent framework knowledge across sessions

**Result:**
Cline becomes an expert in your frameworks with automatic context and autonomous access to documentation via MCP tools.

---

## 🚀 Quick Start (10 Minutes)

### Prerequisites

- VS Code installed (https://code.visualstudio.com/)
- Cline extension installed (https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev)
- Python 3.10+ (for Skill Seekers)
- Claude API key (recommended) or other LLM

### Installation

```bash
# Install Skill Seekers with MCP support
pip install skill-seekers[mcp]

# Verify installation
skill-seekers --version
```

### Generate .clinerules

```bash
# Example: Django framework
skill-seekers scrape --config configs/django.json

# Package for Cline (markdown format)
skill-seekers package output/django --target markdown

# Extract SKILL.md (this becomes your .clinerules content)
# output/django-markdown/SKILL.md
```

### Setup in Cline

**Option 1: Project-Specific Rules** (recommended)

```bash
# Copy to project root as .clinerules
cp output/django-markdown/SKILL.md /path/to/your/project/.clinerules
```

**Option 2: Custom Instructions** (per-project settings)

1. Open Cline settings in VS Code (Cmd+, → search "Cline")
2. Find "Custom Instructions"
3. Add framework knowledge:

```
You are an expert in Django. Follow these patterns:

[Paste contents of SKILL.md here]
```

**Option 3: MCP Server** (for dynamic access)

```bash
# Configure Cline's MCP settings
# In Cline panel → Settings → MCP Servers → Add Server

# Add Skill Seekers MCP server:
{
  "skill-seekers": {
    "command": "python",
    "args": ["-m", "skill_seekers.mcp.server_fastmcp", "--transport", "stdio"],
    "env": {}
  }
}
```

### Test in Cline

1. Open your project in VS Code
2. Open Cline panel (click Cline icon in sidebar)
3. Start a new task:
   ```
   Create a Django model for users with email authentication
   ```
4. Verify Cline references your documentation patterns

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
# - kubernetes.json, docker.json (Infrastructure)
```

**Option B: Custom Documentation**

Create `myframework-config.json`:

```json
{
  "name": "myframework",
  "description": "Custom framework documentation for Cline",
  "base_url": "https://docs.myframework.com/",
  "selectors": {
    "main_content": "article",
    "title": "h1",
    "code_blocks": "pre code"
  },
  "categories": {
    "getting_started": ["intro", "quickstart"],
    "core_concepts": ["concepts", "architecture"],
    "api": ["api", "reference"],
    "best_practices": ["best-practices", "patterns"]
  }
}
```

**Option C: GitHub Repository**

```bash
# Analyze codebase patterns
skill-seekers github --repo facebook/react

# Or local codebase
skill-seekers analyze --directory /path/to/repo --comprehensive
```

### Step 2: Optimize for Cline

**File-Based Rules**

Cline rules are markdown files with NO special syntax required:

```markdown
<!-- .clinerules -->
# Django Expert

You are an expert in Django. Follow these patterns:

## Models

Always include these fields in models:

\```python
from django.db import models

class MyModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
\```

## Views

Use class-based views for CRUD operations:

\```python
from django.views.generic import ListView, DetailView

class UserListView(ListView):
    model = User
    template_name = 'users/list.html'
    context_object_name = 'users'
\```
```

**Hierarchical Rules**

Create multiple rules files for organization:

```
my-django-project/
├── .clinerules                    # Core framework patterns
├── .clinerules.models             # Model-specific rules
├── .clinerules.views              # View-specific rules
├── .clinerules.testing            # Testing patterns
└── .clinerules.project            # Project-specific conventions
```

Cline automatically loads all `.clinerules*` files.

**Memory Bank Integration**

Combine rules with Cline's Memory Bank:

```bash
# Create memory bank structure
mkdir -p .cline/memory-bank

# Initialize memory bank
echo "# Project Memory Bank

## Tech Stack
- Django 5.x
- PostgreSQL 16
- Redis for caching

## Architecture
- Modular apps structure
- API-first design
- Async views for I/O-bound operations

## Conventions
- All models include timestamps
- Use class-based views
- pytest for testing
" > .cline/memory-bank/README.md

# Ask Cline to initialize
# In Cline chat: "Initialize a memory bank for this Django project"
```

### Step 3: Configure MCP Integration

**MCP Server Setup** (for dynamic documentation access)

1. **Install Skill Seekers MCP server:**

```bash
pip install skill-seekers[mcp]
```

2. **Configure in Cline settings:**

Open Cline panel → Settings → MCP Servers → Configure

Add this configuration:

```json
{
  "mcpServers": {
    "skill-seekers": {
      "command": "python",
      "args": [
        "-m",
        "skill_seekers.mcp.server_fastmcp",
        "--transport",
        "stdio"
      ],
      "env": {}
    }
  }
}
```

3. **Restart VS Code**

4. **Verify MCP tools available:**

In Cline panel, check "Available Tools" - you should see:
- `list_configs` - List preset configurations
- `scrape_docs` - Scrape documentation dynamically
- `package_skill` - Package skills for Cline
- ... (18 total MCP tools)

**Using MCP Tools**

Now Cline can access documentation on-demand:

```
In Cline chat:

"Use the skill-seekers MCP tool to scrape React documentation
and generate .clinerules for this project"

Cline will:
1. Call list_configs to find react.json
2. Call scrape_docs with config
3. Call package_skill to create .clinerules
4. Load rules automatically
```

### Step 4: Test and Refine

**Test Cline's Knowledge**

Start autonomous tasks:

```
"Create a complete Django REST API for blog posts with:
- Post model with author foreign key
- Serializers with nested author data
- ViewSets with filtering and pagination
- URL routing
- Tests with pytest"
```

Verify Cline follows your documented patterns.

**Refine Rules**

Add project-specific patterns:

```markdown
<!-- .clinerules.project -->
# Project-Specific Conventions

## Database Queries

ALWAYS use select_related/prefetch_related for foreign keys:

\```python
# BAD
posts = Post.objects.all()  # N+1 queries

# GOOD
posts = Post.objects.select_related('author').all()
\```

## API Responses

NEVER return sensitive fields:

\```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        # Exclude: password, is_staff, etc.
\```
```

**Monitor Cline's Behavior**

Watch for:
- ✅ Cline references rules in explanations
- ✅ Generated code follows patterns
- ✅ Autonomous decisions align with documentation
- ❌ Generic patterns not from your rules (needs refinement)

---

## 🎨 Advanced Usage

### Multi-Framework Projects

**Full-Stack Django + React**

```bash
# Generate backend rules
skill-seekers scrape --config configs/django.json
cp output/django-markdown/SKILL.md .clinerules.backend

# Generate frontend rules
skill-seekers scrape --config configs/react.json
cp output/react-markdown/SKILL.md .clinerules.frontend

# Add project conventions
cat > .clinerules.project << 'EOF'
# Project Conventions

## Backend
- Django REST framework for API
- JWT authentication
- Async views for heavy operations

## Frontend
- React 18 with TypeScript
- Tanstack Query for API calls
- Zustand for state management

## Communication
- Backend exposes /api/v1/* endpoints
- Frontend proxies to localhost:8000 in dev
EOF

# Now Cline knows both Django AND React patterns
```

**Testing with Multiple Frameworks**

```bash
# Backend testing rules
cat > .clinerules.testing-backend << 'EOF'
# Django Testing Patterns

Use pytest with pytest-django:

\```python
import pytest
from django.test import Client

@pytest.mark.django_db
def test_create_post(client: Client):
    response = client.post('/api/v1/posts/', {
        'title': 'Test Post',
        'content': 'Test content'
    })
    assert response.status_code == 201
\```
EOF

# Frontend testing rules
cat > .clinerules.testing-frontend << 'EOF'
# React Testing Patterns

Use React Testing Library:

\```typescript
import { render, screen } from '@testing-library/react';
import { Post } from './Post';

test('renders post title', () => {
  render(<Post title="Test" />);
  expect(screen.getByText('Test')).toBeInTheDocument();
});
\```
EOF
```

### Dynamic Context with MCP Tools

**Custom MCP Tool for Framework Search**

Create `custom_mcp_tool.py`:

```python
from fastmcp import FastMCP

mcp = FastMCP("Custom Framework Search")

@mcp.tool()
def search_framework_docs(framework: str, query: str) -> str:
    """
    Search framework documentation dynamically.

    Args:
        framework: Framework name (django, react, etc.)
        query: Search query

    Returns:
        Relevant documentation snippets
    """
    # Use Skill Seekers to search
    from skill_seekers.cli.adaptors import get_adaptor

    adaptor = get_adaptor('markdown')
    results = adaptor.search(framework, query)

    return results
```

Register in Cline's MCP config:

```json
{
  "mcpServers": {
    "skill-seekers": {
      "command": "python",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp", "--transport", "stdio"]
    },
    "custom-search": {
      "command": "python",
      "args": ["custom_mcp_tool.py"]
    }
  }
}
```

Now Cline can search docs on-demand:

```
In Cline: "Use custom-search MCP tool to find Django async views best practices"
```

### Cline + RAG Pipeline

**Combine Rules with Vector Search**

```python
# setup_cline_rag.py
from skill_seekers.cli.doc_scraper import main as scrape
from skill_seekers.cli.package_skill import main as package

# Scrape documentation
scrape(["--config", "configs/django.json"])

# Create Cline rules
package(["output/django", "--target", "markdown"])

# Also create RAG pipeline
package(["output/django", "--target", "langchain", "--chunk-for-rag"])

# Now you have:
# 1. .clinerules for Cline's context
# 2. LangChain documents for deep vector search
```

**MCP Tool for RAG Query**

```python
# mcp_rag_tool.py
from fastmcp import FastMCP
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

mcp = FastMCP("RAG Search")

# Load vector store
embeddings = OpenAIEmbeddings()
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

@mcp.tool()
def rag_search(query: str, k: int = 5) -> str:
    """
    Search documentation using RAG.

    Args:
        query: Search query
        k: Number of results

    Returns:
        Top-k relevant documentation snippets
    """
    results = vectorstore.similarity_search(query, k=k)
    return "\n\n".join([doc.page_content for doc in results])
```

---

## 💡 Best Practices

### 1. Keep Rules Focused

**Bad: Everything in One File**

```markdown
<!-- .clinerules (20,000 chars!) -->
# Django Complete Guide
[... massive unstructured documentation ...]
```

**Good: Modular Rules**

```markdown
<!-- .clinerules (core concepts, 5,000 chars) -->
# Django Core Patterns
[... focused on common patterns ...]

<!-- .clinerules.models (database, 3,000 chars) -->
# Django Models Best Practices
[... focused on database patterns ...]

<!-- .clinerules.api (REST API, 4,000 chars) -->
# Django REST Framework
[... focused on API patterns ...]
```

### 2. Use Hierarchical Loading

Cline loads all `.clinerules*` files. Use naming for precedence:

```
.clinerules                    # Core framework (loaded first)
.clinerules.01-models          # Database patterns
.clinerules.02-views           # View patterns
.clinerules.03-testing         # Testing patterns
.clinerules.99-project         # Project overrides (loaded last)
```

### 3. Include Code Examples

Don't just describe patterns - show them:

```markdown
## Creating Django Models

\```python
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.username
\```

Use this exact pattern for all models.
```

### 4. Leverage MCP for Dynamic Context

**Static Rules** (in .clinerules):
- Core patterns that rarely change
- Framework conventions
- Code style preferences

**Dynamic MCP Tools**:
- Search latest documentation
- Query GitHub for code examples
- Fetch API references on-demand

```
In Cline:
"Use skill-seekers MCP to search Django 5.0 async views documentation"

Cline calls MCP tool → gets latest docs → applies to task
```

### 5. Update Rules Regularly

```bash
# Quarterly framework updates
skill-seekers scrape --config configs/django.json
cp output/django-markdown/SKILL.md .clinerules

# Check what changed
diff .clinerules.old .clinerules

# Test with Cline
# Ask: "What's new in Django 5.0?"
```

---

## 🔥 Real-World Examples

### Example 1: Django REST API with Cline

**Project Structure:**

```
my-django-api/
├── .clinerules                    # Core Django patterns
├── .clinerules.api                # DRF patterns
├── .clinerules.testing            # pytest patterns
├── .clinerules.project            # Project conventions
├── app/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
└── tests/
```

**.clinerules (Core Django)**

```markdown
# Django Expert

You are an expert in Django 5.0. Follow these patterns:

## Models

Always include timestamps and __str__:

\```python
from django.db import models

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Post(BaseModel):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    def __str__(self):
        return self.title
\```

## Queries

Use select_related/prefetch_related:

\```python
# BAD
posts = Post.objects.all()

# GOOD
posts = Post.objects.select_related('author').all()
\```
```

**.clinerules.api (Django REST Framework)**

```markdown
# Django REST Framework Patterns

## Serializers

Use nested serializers for relationships:

\```python
from rest_framework import serializers

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'created_at']
\```

## ViewSets

Use ViewSets with filtering:

\```python
from rest_framework import viewsets, filters

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related('author').all()
    serializer_class = PostSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'content']
\```
```

**Using Cline:**

```
Start Cline task:

"Create a complete blog API with posts and comments:
- Post model with author, title, content, created_at
- Comment model with author, post foreign key, content
- Serializers with nested data
- ViewSets with filtering
- URL routing
- Full test suite with pytest"

Cline will:
1. ✅ Use BaseModel with timestamps (from .clinerules)
2. ✅ Add __str__ methods (from .clinerules)
3. ✅ Use select_related in viewsets (from .clinerules)
4. ✅ Create nested serializers (from .clinerules.api)
5. ✅ Add filtering (from .clinerules.api)
6. ✅ Write pytest tests (from .clinerules.testing)

Result: Production-ready API following all your patterns!
```

### Example 2: React + TypeScript with Cline

**Project Structure:**

```
my-react-app/
├── .clinerules                    # Core React patterns
├── .clinerules.typescript         # TypeScript patterns
├── .clinerules.testing            # Testing Library patterns
├── src/
│   ├── components/
│   ├── hooks/
│   └── utils/
└── tests/
```

**.clinerules (Core React)**

```markdown
# React 18 + TypeScript Expert

## Components

Use functional components with TypeScript:

\```typescript
import { FC } from 'react';

interface PostProps {
  title: string;
  content: string;
  author: {
    name: string;
    email: string;
  };
}

export const Post: FC<PostProps> = ({ title, content, author }) => {
  return (
    <article>
      <h2>{title}</h2>
      <p>{content}</p>
      <footer>By {author.name}</footer>
    </article>
  );
};
\```

## Hooks

Use custom hooks for logic:

\```typescript
import { useState, useEffect } from 'react';

interface UseFetchResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

export function useFetch<T>(url: string): UseFetchResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetch(url)
      .then(res => res.json())
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [url]);

  return { data, loading, error };
}
\```
```

---

## 🐛 Troubleshooting

### Issue: .clinerules Not Loading

**Symptoms:**
- Cline doesn't reference documentation
- Rules file exists but ignored

**Solutions:**

1. **Check file location**
   ```bash
   # Must be at project root
   ls -la .clinerules

   # Not in subdirectory
   # NOT: src/.clinerules
   ```

2. **Verify file format**
   ```bash
   # Must be plain markdown
   file .clinerules
   # Should show: ASCII text

   # Not binary or encoded
   ```

3. **Reload VS Code**
   ```
   Cmd+Shift+P → "Developer: Reload Window"
   ```

4. **Check Cline logs**
   ```
   In Cline panel → Settings → Show Logs
   # Look for "Loaded rules from .clinerules"
   ```

### Issue: MCP Server Not Connecting

**Error:**
> "Failed to connect to MCP server: skill-seekers"

**Solutions:**

1. **Verify installation**
   ```bash
   pip show skill-seekers
   # Check [mcp] extra is installed
   ```

2. **Test MCP server directly**
   ```bash
   python -m skill_seekers.mcp.server_fastmcp --transport stdio
   # Should start without errors
   ```

3. **Check Python path**
   ```json
   // MCP config - use absolute path
   {
     "mcpServers": {
       "skill-seekers": {
         "command": "/usr/local/bin/python3",  // Absolute path
         "args": ["-m", "skill_seekers.mcp.server_fastmcp", "--transport", "stdio"]
       }
     }
   }
   ```

4. **Check environment variables**
   ```json
   {
     "mcpServers": {
       "skill-seekers": {
         "command": "python",
         "args": ["-m", "skill_seekers.mcp.server_fastmcp", "--transport", "stdio"],
         "env": {
           "ANTHROPIC_API_KEY": "${env:ANTHROPIC_API_KEY}"
         }
       }
     }
   }
   ```

### Issue: Cline Not Using Rules

**Symptoms:**
- Rules loaded but Cline ignores them
- Generic code patterns

**Solutions:**

1. **Add explicit instructions**
   ```markdown
   # Django Expert

   You MUST follow these patterns in ALL Django code:
   - Use timestamps in all models
   - Use select_related for foreign keys
   - Write tests for all views

   Never deviate from these patterns.
   ```

2. **Use memory bank**
   ```
   In Cline chat:
   "Remember to ALWAYS follow the patterns in .clinerules"
   ```

3. **Reference rules explicitly**
   ```
   In Cline task:
   "Create a Django model following the patterns in .clinerules"
   ```

4. **Check custom instructions**
   ```
   Cline Settings → Custom Instructions
   # Should NOT conflict with .clinerules
   ```

---

## 📊 Before vs After Comparison

| Aspect | Before Skill Seekers | After Skill Seekers |
|--------|---------------------|---------------------|
| **Context Source** | Copy-paste into chat | Auto-loaded .clinerules |
| **AI Knowledge** | Generic patterns | Framework-specific patterns |
| **Setup Time** | Manual curation (hours) | Automated scraping (10 min) |
| **Consistency** | Varies per task | Persistent across tasks |
| **Updates** | Manual editing | Re-run scraper |
| **MCP Integration** | Manual tool creation | Pre-built MCP tools |
| **Multi-Framework** | Context confusion | Modular rules per framework |
| **Autonomous Workflow** | Frequent interruptions | Autonomous with correct patterns |

---

## 🤝 Community & Support

- **Questions:** [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)
- **Issues:** [GitHub Issues](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
- **Website:** [skillseekersweb.com](https://skillseekersweb.com/)
- **Cline Docs:** [docs.cline.bot](https://docs.cline.bot/)
- **Cline GitHub:** [github.com/cline/cline](https://github.com/cline/cline)

---

## 📚 Related Guides

- [Cursor Integration](CURSOR.md) - Similar IDE, different approach
- [Windsurf Integration](WINDSURF.md) - Alternative AI IDE
- [Continue.dev Integration](CONTINUE_DEV.md) - IDE-agnostic assistant
- [LangChain Integration](LANGCHAIN.md) - Build RAG pipelines
- [MCP Setup Guide](../MCP_SETUP.md) - Detailed MCP configuration

---

## 📖 Next Steps

1. **Try another framework:** `skill-seekers scrape --config configs/fastapi.json`
2. **Set up MCP server:** Dynamic documentation access
3. **Create memory bank:** Persistent project knowledge
4. **Build RAG pipeline:** Deep documentation search with `--target langchain`
5. **Contribute examples:** Share your .clinerules patterns

---

**Sources:**
- [Cline VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev)
- [Cline GitHub Repository](https://github.com/cline/cline)
- [Cline Documentation](https://docs.cline.bot/getting-started/installing-cline)
- [Cline Rules Documentation](https://deepwiki.com/cline/cline/7.1-cline-rules)
- [Cline Prompt Engineering Guide](https://medium.com/@evanmusick.dev/cline-prompt-engineering-crash-course-custom-instructions-that-actually-work-520ef1162fc2)
- [VS Code MCP Integration](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)
- [MCP Developer Guide](https://code.visualstudio.com/api/extension-guides/ai/mcp)
- [Cline MCP Setup Guide](https://4sysops.com/archives/install-mcp-server-with-vs-code-extension-cline-for-ai-driven-aws-automation/)
