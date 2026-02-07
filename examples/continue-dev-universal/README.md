# Continue.dev + Universal Context Example

Complete example showing how to use Skill Seekers to create IDE-agnostic context providers for Continue.dev across VS Code, JetBrains, and other IDEs.

## What This Example Does

- ✅ Generates framework documentation (Vue.js example)
- ✅ Creates HTTP context provider server
- ✅ Works across all IDEs (VS Code, IntelliJ, PyCharm, WebStorm, etc.)
- ✅ Single configuration, consistent results

## Quick Start

### 1. Generate Documentation

```bash
# Install Skill Seekers
pip install skill-seekers[mcp]

# Generate Vue.js documentation
skill-seekers scrape --config configs/vue.json
skill-seekers package output/vue --target markdown
```

### 2. Start Context Server

```bash
# Use the provided HTTP context server
python context_server.py

# Server runs on http://localhost:8765
# Serves documentation at /docs/{framework}
```

### 3. Configure Continue.dev

Edit `~/.continue/config.json`:

```json
{
  "contextProviders": [
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/vue",
        "title": "vue-docs",
        "displayTitle": "Vue.js Documentation",
        "description": "Vue.js framework expert knowledge"
      }
    }
  ]
}
```

### 4. Test in Any IDE

**VS Code:**
```bash
code my-vue-project/
# Open Continue panel (Cmd+L)
# Type: @vue-docs Create a Vue 3 component with Composition API
```

**IntelliJ IDEA:**
```bash
idea my-vue-project/
# Open Continue panel (Cmd+L)
# Type: @vue-docs Create a Vue 3 component with Composition API
```

**Result:** IDENTICAL suggestions in both IDEs!

## Expected Results

### Before (Without Context Provider)

**Prompt:** "Create a Vue component"

**Continue Output:**
```javascript
export default {
  name: 'MyComponent',
  data() {
    return {
      message: 'Hello'
    }
  }
}
```

❌ Uses Options API (outdated)
❌ No TypeScript
❌ No Composition API
❌ Generic patterns

### After (With Context Provider)

**Prompt:** "@vue-docs Create a Vue component"

**Continue Output:**
```typescript
<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  title: string
  count?: number
}

const props = withDefaults(defineProps<Props>(), {
  count: 0
})

const message = ref('Hello')
const displayCount = computed(() => props.count * 2)
</script>

<template>
  <div>
    <h2>{{ props.title }}</h2>
    <p>{{ message }} - Count: {{ displayCount }}</p>
  </div>
</template>

<style scoped>
/* Component styles */
</style>
```

✅ Composition API with `<script setup>`
✅ TypeScript interfaces
✅ Proper props definition
✅ Vue 3 best practices

## Files in This Example

- `context_server.py` - HTTP context provider server (FastAPI)
- `quickstart.py` - Automation script for setup
- `requirements.txt` - Python dependencies
- `config.example.json` - Sample Continue.dev configuration

## Multi-IDE Testing

This example demonstrates IDE consistency:

### Test 1: VS Code
```bash
cd examples/continue-dev-universal
python context_server.py &

code test-project/
# In Continue: @vue-docs Create a component
# Note the exact code generated
```

### Test 2: IntelliJ IDEA
```bash
# Same server still running
idea test-project/
# In Continue: @vue-docs Create a component
# Code should be IDENTICAL to VS Code
```

### Test 3: PyCharm
```bash
# Same server still running
pycharm test-project/
# In Continue: @vue-docs Create a component
# Code should be IDENTICAL to both above
```

**Why it works:** Continue.dev uses the SAME `~/.continue/config.json` across all IDEs!

## Context Server Architecture

The `context_server.py` implements a simple HTTP server:

```python
from fastapi import FastAPI
from skill_seekers.cli.doc_scraper import load_skill

app = FastAPI()

@app.get("/docs/{framework}")
async def get_framework_docs(framework: str):
    """
    Serve framework documentation as Continue context.

    Args:
        framework: Framework name (vue, react, django, etc.)

    Returns:
        JSON with contextItems array
    """
    # Load documentation
    docs = load_skill(f"output/{framework}-markdown/SKILL.md")

    return {
        "contextItems": [
            {
                "name": f"{framework.title()} Documentation",
                "description": f"Complete {framework} framework knowledge",
                "content": docs
            }
        ]
    }
```

## Multi-Framework Support

Add more frameworks easily:

```bash
# Generate React docs
skill-seekers scrape --config configs/react.json
skill-seekers package output/react --target markdown

# Generate Django docs
skill-seekers scrape --config configs/django.json
skill-seekers package output/django --target markdown

# Server automatically serves both at:
# http://localhost:8765/docs/react
# http://localhost:8765/docs/django
```

Update `~/.continue/config.json`:

```json
{
  "contextProviders": [
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/vue",
        "title": "vue-docs",
        "displayTitle": "Vue.js"
      }
    },
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/react",
        "title": "react-docs",
        "displayTitle": "React"
      }
    },
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/django",
        "title": "django-docs",
        "displayTitle": "Django"
      }
    }
  ]
}
```

Now you can use:
```
@vue-docs @react-docs @django-docs Create a full-stack app
```

## Team Deployment

### Option 1: Shared Server

```bash
# Run on team server
ssh team-server
python context_server.py --host 0.0.0.0 --port 8765

# Team members update config:
{
  "contextProviders": [
    {
      "name": "http",
      "params": {
        "url": "http://team-server.company.com:8765/docs/vue",
        "title": "vue-docs"
      }
    }
  ]
}
```

### Option 2: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY context_server.py .
COPY output/ output/

EXPOSE 8765
CMD ["python", "context_server.py", "--host", "0.0.0.0"]
```

```bash
# Build and run
docker build -t skill-seekers-context .
docker run -d -p 8765:8765 skill-seekers-context

# Team uses: http://your-server:8765/docs/vue
```

### Option 3: Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: skill-seekers-context
spec:
  replicas: 3
  selector:
    matchLabels:
      app: skill-seekers-context
  template:
    metadata:
      labels:
        app: skill-seekers-context
    spec:
      containers:
      - name: context-server
        image: skill-seekers-context:latest
        ports:
        - containerPort: 8765
---
apiVersion: v1
kind: Service
metadata:
  name: skill-seekers-context
spec:
  selector:
    app: skill-seekers-context
  ports:
  - port: 80
    targetPort: 8765
  type: LoadBalancer
```

## Customization

### Add Project-Specific Context

```python
# In context_server.py

@app.get("/project/conventions")
async def get_project_conventions():
    """Serve company-specific patterns."""
    return {
        "contextItems": [{
            "name": "Project Conventions",
            "description": "Company coding standards",
            "content": """
# Company Coding Standards

## Vue Components
- Always use Composition API
- TypeScript is required
- Props must have interfaces
- Use Pinia for state management

## API Calls
- Use axios with interceptors
- All endpoints must be typed
- Error handling with try/catch
- Loading states required
"""
        }]
    }
```

Add to Continue config:

```json
{
  "contextProviders": [
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/vue",
        "title": "vue-docs"
      }
    },
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/project/conventions",
        "title": "conventions",
        "displayTitle": "Company Standards"
      }
    }
  ]
}
```

Now use both:
```
@vue-docs @conventions Create a component following our standards
```

## Troubleshooting

### Issue: Context provider not showing

**Solution:** Check server is running
```bash
curl http://localhost:8765/docs/vue
# Should return JSON

# If not running:
python context_server.py
```

### Issue: Different results in different IDEs

**Solution:** Verify same config file
```bash
# All IDEs use same config
cat ~/.continue/config.json

# NOT project-specific configs
# (those would cause inconsistency)
```

### Issue: Documentation outdated

**Solution:** Re-generate and restart
```bash
skill-seekers scrape --config configs/vue.json
skill-seekers package output/vue --target markdown

# Restart server (will load new docs)
pkill -f context_server.py
python context_server.py
```

## Advanced Usage

### RAG Integration

```python
# rag_context_server.py
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# Load vector store
embeddings = OpenAIEmbeddings()
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)

@app.get("/docs/search")
async def search_docs(query: str, k: int = 5):
    """RAG-powered search."""
    results = vectorstore.similarity_search(query, k=k)

    return {
        "contextItems": [
            {
                "name": f"Result {i+1}",
                "description": doc.metadata.get("source", "Docs"),
                "content": doc.page_content
            }
            for i, doc in enumerate(results)
        ]
    }
```

Continue config:

```json
{
  "contextProviders": [
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/search?query={query}",
        "title": "rag-search",
        "displayTitle": "RAG Search"
      }
    }
  ]
}
```

### MCP Integration

```bash
# Install MCP support
pip install skill-seekers[mcp]

# Continue config with MCP
{
  "mcpServers": {
    "skill-seekers": {
      "command": "python",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp", "--transport", "stdio"]
    }
  },
  "contextProviders": [
    {
      "name": "mcp",
      "params": {
        "serverName": "skill-seekers"
      }
    }
  ]
}
```

## Performance Tips

### 1. Cache Documentation

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def load_cached_docs(framework: str) -> str:
    """Cache docs in memory."""
    return load_skill(f"output/{framework}-markdown/SKILL.md")
```

### 2. Compress Responses

```python
from fastapi.responses import JSONResponse
import gzip

@app.get("/docs/{framework}")
async def get_docs(framework: str):
    docs = load_cached_docs(framework)

    # Compress if large
    if len(docs) > 10000:
        docs = gzip.compress(docs.encode()).decode('latin1')

    return JSONResponse(...)
```

### 3. Load Balancing

```bash
# Run multiple instances
python context_server.py --port 8765 &
python context_server.py --port 8766 &
python context_server.py --port 8767 &

# Configure Continue with failover
{
  "contextProviders": [
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/vue",
        "fallbackUrls": [
          "http://localhost:8766/docs/vue",
          "http://localhost:8767/docs/vue"
        ]
      }
    }
  ]
}
```

## Related Examples

- [Cursor Example](../cursor-react-skill/) - IDE-specific approach
- [Windsurf Example](../windsurf-fastapi-context/) - Windsurf IDE
- [Cline Example](../cline-django-assistant/) - VS Code extension
- [LangChain RAG Example](../langchain-rag-pipeline/) - RAG integration

## Next Steps

1. Add more frameworks for full-stack development
2. Deploy to team server for shared access
3. Integrate with RAG for deep search
4. Create project-specific context providers
5. Set up CI/CD for automatic documentation updates

## Support

- **Skill Seekers Issues:** [GitHub](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
- **Continue.dev Docs:** [docs.continue.dev](https://docs.continue.dev/)
- **Integration Guide:** [CONTINUE_DEV.md](../../docs/integrations/CONTINUE_DEV.md)
