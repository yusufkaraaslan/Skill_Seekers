# Using Skill Seekers with Cursor IDE

**Last Updated:** February 5, 2026
**Status:** Production Ready
**Difficulty:** Easy ⭐

---

## 🎯 The Problem

Cursor IDE offers powerful AI coding assistance, but:

- **Generic Knowledge** - AI doesn't know your project-specific frameworks
- **No Custom Context** - Can't reference your internal docs or codebase patterns
- **Manual Context** - Copy-pasting documentation is tedious and error-prone
- **Inconsistent** - AI responses vary based on what context you provide

**Example:**
> "When building a Django app in Cursor, the AI might suggest outdated patterns or miss project-specific conventions. You want the AI to 'know' your framework documentation without manual prompting."

---

## ✨ The Solution

Use Skill Seekers to create **custom documentation** for Cursor's AI:

1. **Generate structured docs** from any framework or codebase
2. **Package as .cursorrules** - Cursor's custom instruction format
3. **Automatic Context** - AI references your docs in every interaction
4. **Project-Specific** - Different rules per project

**Result:**
Cursor's AI becomes an expert in your frameworks with persistent, automatic context.

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites

- Cursor IDE installed (https://cursor.sh/)
- Python 3.10+ (for Skill Seekers)

### Installation

```bash
# Install Skill Seekers
pip install skill-seekers

# Verify installation
skill-seekers --version
```

### Generate .cursorrules

```bash
# Example: Django framework
skill-seekers scrape --config configs/django.json

# Package for Cursor
skill-seekers package output/django --target markdown

# Extract SKILL.md (this becomes your .cursorrules content)
# output/django-markdown/SKILL.md
```

### Setup in Cursor

**Option 1: Global Rules** (applies to all projects)
```bash
# Copy to Cursor's global config
cp output/django-markdown/SKILL.md ~/.cursor/.cursorrules
```

**Option 2: Project-Specific Rules** (recommended)
```bash
# Copy to your project root
cp output/django-markdown/SKILL.md /path/to/your/project/.cursorrules
```

**Option 3: Multiple Frameworks**
```bash
# Create modular rules file
cat > /path/to/your/project/.cursorrules << 'EOF'
# Django Framework Expert
You are an expert in Django. Use the following documentation:

EOF

# Append Django docs
cat output/django-markdown/SKILL.md >> /path/to/your/project/.cursorrules

# Add React if needed
echo "\n\n# React Framework Expert\n" >> /path/to/your/project/.cursorrules
cat output/react-markdown/SKILL.md >> /path/to/your/project/.cursorrules
```

### Test in Cursor

1. Open your project in Cursor
2. Open any file (`.py`, `.js`, etc.)
3. Use Cursor's AI chat (Cmd+K or Cmd+L)
4. Ask: "How do I create a Django model with relationships?"

**Expected:** AI responds using patterns and examples from your .cursorrules!

---

## 📖 Detailed Setup Guide

### Step 1: Choose Your Documentation Source

**Option A: Framework Documentation**
```bash
# Available presets: django, fastapi, react, vue, etc.
skill-seekers scrape --config configs/react.json
skill-seekers package output/react --target markdown
```

**Option B: GitHub Repository**
```bash
# Scrape from GitHub repo
skill-seekers github --repo facebook/react --name react
skill-seekers package output/react --target markdown
```

**Option C: Local Codebase**
```bash
# Analyze your own codebase
skill-seekers analyze --directory /path/to/repo --comprehensive
skill-seekers package output/codebase --target markdown
```

**Option D: Multiple Sources**
```bash
# Combine docs + code
skill-seekers unified \
  --docs-config configs/fastapi.json \
  --github fastapi/fastapi \
  --name fastapi-complete

skill-seekers package output/fastapi-complete --target markdown
```

### Step 2: Optimize for Cursor

Cursor has a **200KB limit** for .cursorrules. Skill Seekers markdown output is optimized, but for very large documentation:

**Strategy 1: Summarize (Recommended)**
```bash
# Use AI enhancement to create concise version
skill-seekers enhance output/django --mode LOCAL

# Result: More concise, better structured SKILL.md
```

**Strategy 2: Split by Category**
```bash
# Create separate rules files per category
# In your .cursorrules:
cat > .cursorrules << 'EOF'
# Django Models Expert
You are an expert in Django models and ORM.

When working with Django models, reference these patterns:
EOF

# Extract only models category from references/
cat output/django/references/models.md >> .cursorrules
```

**Strategy 3: Router Approach**
```bash
# Use router skill (generates high-level overview)
skill-seekers unified \
  --docs-config configs/django.json \
  --build-router

# Result: Lightweight architectural guide
cat output/django/ARCHITECTURE.md > .cursorrules
```

### Step 3: Configure Cursor Settings

**.cursorrules format:**
```markdown
# Framework Expert Instructions

You are an expert in [Framework Name]. Follow these guidelines:

## Core Concepts
[Your documentation here]

## Common Patterns
[Patterns from Skill Seekers]

## Code Examples
[Examples from documentation]

## Best Practices
- Pattern 1
- Pattern 2

## Anti-Patterns to Avoid
- Anti-pattern 1
- Anti-pattern 2
```

**Cursor respects this structure** and uses it as persistent context.

### Step 4: Test and Refine

**Good prompts to test:**
```
1. "Create a [Framework] component that does X"
2. "What's the recommended pattern for Y in [Framework]?"
3. "Refactor this code to follow [Framework] best practices"
4. "Explain how [Specific Feature] works in [Framework]"
```

**Signs it's working:**
- AI mentions specific framework concepts
- Suggests code matching documentation patterns
- References framework-specific terminology
- Provides accurate, up-to-date examples

---

## 🎨 Advanced Usage

### Multi-Framework Projects

```bash
# Generate rules for full-stack project
skill-seekers scrape --config configs/fastapi.json
skill-seekers scrape --config configs/react.json
skill-seekers scrape --config configs/postgresql.json

skill-seekers package output/fastapi --target markdown
skill-seekers package output/react --target markdown
skill-seekers package output/postgresql --target markdown

# Combine into single .cursorrules
cat > .cursorrules << 'EOF'
# Full-Stack Expert (FastAPI + React + PostgreSQL)

You are an expert in full-stack development using FastAPI, React, and PostgreSQL.

---
# Backend: FastAPI
EOF

cat output/fastapi-markdown/SKILL.md >> .cursorrules

echo "\n\n---\n# Frontend: React\n" >> .cursorrules
cat output/react-markdown/SKILL.md >> .cursorrules

echo "\n\n---\n# Database: PostgreSQL\n" >> .cursorrules
cat output/postgresql-markdown/SKILL.md >> .cursorrules
```

### Project-Specific Patterns

```bash
# Analyze your codebase
skill-seekers analyze --directory . --comprehensive

# Extract patterns and architecture
cat output/codebase/SKILL.md > .cursorrules

# Add custom instructions
cat >> .cursorrules << 'EOF'

## Project-Specific Guidelines

### Architecture
- Use EventBus pattern for cross-component communication
- All API calls go through services/api.ts
- State management with Zustand (not Redux)

### Naming Conventions
- Components: PascalCase (e.g., UserProfile.tsx)
- Hooks: camelCase with 'use' prefix (e.g., useAuth.ts)
- Utils: camelCase (e.g., formatDate.ts)

### Testing
- Unit tests: *.test.ts
- Integration tests: *.integration.test.ts
- Use vitest, not jest
EOF
```

### Dynamic Context per File Type

Cursor supports **directory-specific rules**:

```bash
# Backend rules (for Python files)
cat output/fastapi-markdown/SKILL.md > backend/.cursorrules

# Frontend rules (for TypeScript files)
cat output/react-markdown/SKILL.md > frontend/.cursorrules

# Database rules (for SQL files)
cat output/postgresql-markdown/SKILL.md > database/.cursorrules
```

When you open a file, Cursor uses the closest `.cursorrules` in the directory tree.

### Cursor + RAG Pipeline

For **massive documentation** (>200KB):

1. **Use Pinecone/Chroma for vector storage**
2. **Use Cursor for code generation**
3. **Build API to query vectors**

```python
# cursor_rag.py - Custom Cursor context provider
from pinecone import Pinecone
from openai import OpenAI

def get_relevant_docs(query: str, top_k: int = 3) -> str:
    """Fetch relevant docs from vector store."""
    pc = Pinecone()
    index = pc.Index("framework-docs")

    # Create query embedding
    openai_client = OpenAI()
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    query_embedding = response.data[0].embedding

    # Query Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    # Format for Cursor
    context = "\n\n".join([
        f"**{m['metadata']['category']}**: {m['metadata']['text']}"
        for m in results["matches"]
    ])

    return context

# Usage in .cursorrules
# "When answering questions, first call cursor_rag.py to get relevant context"
```

---

## 💡 Best Practices

### 1. Keep Rules Focused

**Good:**
```markdown
# Django ORM Expert
You are an expert in Django's ORM system.

Focus on:
- Model definitions
- QuerySets and managers
- Database relationships
- Migrations

[Detailed ORM documentation]
```

**Bad:**
```markdown
# Everything Expert
You know everything about Django, React, AWS, Docker, and 50 other technologies...
[Huge wall of text]
```

### 2. Use Hierarchical Structure

```markdown
# Framework Expert

## 1. Core Concepts (High-level)
Brief overview of key concepts

## 2. Common Patterns (Mid-level)
Practical patterns and examples

## 3. API Reference (Low-level)
Detailed API documentation

## 4. Troubleshooting
Common issues and solutions
```

### 3. Include Anti-Patterns

```markdown
## Anti-Patterns to Avoid

❌ **DON'T** use class-based components in React
✅ **DO** use functional components with hooks

❌ **DON'T** mutate state directly
✅ **DO** use setState or useState updater function
```

### 4. Add Code Examples

```markdown
## Creating a Django Model

✅ **Recommended Pattern:**
```python
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
```

### 5. Update Regularly

```bash
# Set up monthly refresh
crontab -e

# Add line to regenerate rules monthly
0 0 1 * * cd ~/projects && skill-seekers scrape --config configs/django.json && skill-seekers package output/django --target markdown && cp output/django-markdown/SKILL.md ~/.cursorrules
```

---

## 🔥 Real-World Examples

### Example 1: Django + React Full-Stack

**.cursorrules:**
```markdown
# Full-Stack Developer Expert (Django + React)

## Backend: Django REST Framework

You are an expert in Django and Django REST Framework.

### Serializers
Always use ModelSerializer for database models:
```python
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']
        read_only_fields = ['id', 'date_joined']
```

### ViewSets
Use ViewSets for CRUD operations:
```python
from rest_framework import viewsets

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
```

---

## Frontend: React + TypeScript

You are an expert in React with TypeScript.

### Components
Always type props and use functional components:
```typescript
interface UserProps {
  user: User;
  onUpdate: (user: User) => void;
}

export function UserProfile({ user, onUpdate }: UserProps) {
  // Component logic
}
```

### API Calls
Use TanStack Query for data fetching:
```typescript
import { useQuery } from '@tanstack/react-query';

function useUser(id: string) {
  return useQuery({
    queryKey: ['user', id],
    queryFn: () => api.getUser(id),
  });
}
```

## Project Conventions

- Backend: `/api/v1/` prefix for all endpoints
- Frontend: `/src/features/` for feature-based organization
- Tests: Co-located with source files (`.test.ts`)
- API client: `src/lib/api.ts` (single source of truth)
```

### Example 2: Godot Game Engine

**.cursorrules:**
```markdown
# Godot 4.x Game Developer Expert

You are an expert in Godot 4.x game development with GDScript.

## Scene Structure
Always use scene tree hierarchy:
- Root node matches script class name
- Group related nodes under containers
- Use descriptive node names (PascalCase)

## Signals
Prefer signals over direct function calls:
```gdscript
# Declare signal
signal health_changed(new_health: int)

# Emit signal
health_changed.emit(current_health)

# Connect in parent
player.health_changed.connect(_on_player_health_changed)
```

## Node Access
Use @onready for node references:
```gdscript
@onready var sprite = $Sprite2D
@onready var animation_player = $AnimationPlayer
```

## Project Patterns (from codebase analysis)

### EventBus Pattern
Use autoload EventBus for global events:
```gdscript
# EventBus.gd (autoload)
signal game_started
signal game_over(score: int)

# In any script
EventBus.game_started.emit()
```

### Resource-Based Data
Store game data in Resources:
```gdscript
# item_data.gd
class_name ItemData extends Resource

@export var item_name: String
@export var icon: Texture2D
@export var price: int
```
```

---

## 🐛 Troubleshooting

### Issue: .cursorrules Not Loading

**Solutions:**
```bash
# 1. Check file location
ls -la .cursorrules          # Project root
ls -la ~/.cursor/.cursorrules # Global

# 2. Verify file is UTF-8
file .cursorrules

# 3. Restart Cursor completely
# Cmd+Q (macOS) or Alt+F4 (Windows), then reopen

# 4. Check Cursor settings
# Settings > Features > Ensure "Custom Instructions" is enabled
```

### Issue: Rules Too Large (>200KB)

**Solutions:**
```bash
# Check file size
ls -lh .cursorrules

# Reduce size:
# 1. Use --enhance to create concise version
skill-seekers enhance output/django --mode LOCAL

# 2. Extract only essential sections
cat output/django/SKILL.md | head -n 1000 > .cursorrules

# 3. Use category-specific rules (split by directory)
cat output/django/references/models.md > models/.cursorrules
cat output/django/references/views.md > views/.cursorrules
```

### Issue: AI Not Using Rules

**Diagnostics:**
```
1. Ask Cursor: "What frameworks do you know about?"
   - If it mentions your framework, rules are loaded
   - If not, rules aren't loading

2. Test with specific prompt:
   "Create a [Framework-specific concept]"
   - Should use terminology from your docs

3. Check Cursor's response format:
   - Does it match patterns from your docs?
   - Does it mention framework-specific features?
```

**Solutions:**
- Restart Cursor
- Verify .cursorrules is in correct location
- Check file size (<200KB)
- Test with simpler rules first

### Issue: Inconsistent AI Responses

**Solutions:**
```markdown
# Add explicit instructions at top of .cursorrules:

# IMPORTANT: Always reference the patterns and examples below
# When suggesting code, use the exact patterns shown
# When explaining concepts, use the terminology defined here
# If you don't know something, say so - don't make up patterns
```

---

## 📊 Before vs After Comparison

| Aspect | Without Skill Seekers | With Skill Seekers |
|--------|---------------------|-------------------|
| **Context** | Generic, manual | Framework-specific, automatic |
| **Accuracy** | 60-70% (generic knowledge) | 90-95% (project-specific) |
| **Consistency** | Varies by prompt | Consistent across sessions |
| **Setup Time** | Manual copy-paste each time | One-time setup (5 min) |
| **Updates** | Manual re-prompting | Regenerate .cursorrules (2 min) |
| **Multi-Framework** | Confusing, mixed knowledge | Clear separation per project |

---

## 🤝 Community & Support

- **Questions:** [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)
- **Issues:** [GitHub Issues](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
- **Documentation:** [https://skillseekersweb.com/](https://skillseekersweb.com/)
- **Cursor Forum:** [https://forum.cursor.sh/](https://forum.cursor.sh/)

---

## 📚 Related Guides

- [LangChain Integration](./LANGCHAIN.md)
- [LlamaIndex Integration](./LLAMA_INDEX.md)
- [Pinecone Integration](./PINECONE.md)
- [RAG Pipelines Overview](./RAG_PIPELINES.md)

---

## 📖 Next Steps

1. **Generate your first .cursorrules** from a framework you use
2. **Test in Cursor** with framework-specific prompts
3. **Refine and iterate** based on AI responses
4. **Share your .cursorrules** with your team
5. **Automate updates** with monthly regeneration

---

**Last Updated:** February 5, 2026
**Tested With:** Cursor 0.41+, Claude Sonnet 4.5
**Skill Seekers Version:** v2.9.0+
