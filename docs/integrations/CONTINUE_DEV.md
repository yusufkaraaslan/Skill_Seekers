# Using Skill Seekers with Continue.dev

**Last Updated:** February 7, 2026
**Status:** Production Ready
**Difficulty:** Easy ⭐

---

## 🎯 The Problem

Continue.dev is a powerful IDE-agnostic AI coding assistant, but:

- **Generic Knowledge** - AI doesn't know your project-specific frameworks or patterns
- **Manual Context** - Typing @-mentions for every framework detail is tedious
- **Multi-IDE Consistency** - Context varies between VS Code, JetBrains, and other IDEs
- **Limited Built-in Providers** - Few pre-configured documentation sources

**Example:**
> "When using Continue in VS Code and JetBrains simultaneously, you want consistent framework knowledge across both IDEs without manual setup duplication. Continue's built-in @docs provider requires manual indexing."

---

## ✨ The Solution

Use Skill Seekers to create **custom context providers** for Continue.dev:

1. **Generate structured docs** from any framework or codebase
2. **Package as HTTP context provider** - Continue's universal format
3. **MCP Integration** - Expose documentation via Model Context Protocol
4. **IDE-Agnostic** - Same context in VS Code, JetBrains, and future IDEs

**Result:**
Continue becomes an expert in your frameworks across all IDEs with consistent, automatic context.

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites

- Continue.dev installed in your IDE:
  - **VS Code:** https://marketplace.visualstudio.com/items?itemName=Continue.continue
  - **JetBrains:** Settings → Plugins → Search "Continue"
- Python 3.10+ (for Skill Seekers)

### Installation

```bash
# Install Skill Seekers with MCP support
pip install skill-seekers[mcp]

# Verify installation
skill-seekers --version
```

### Generate Documentation

```bash
# Example: Vue.js framework
skill-seekers scrape --config configs/vue.json

# Package for Continue (markdown format)
skill-seekers package output/vue --target markdown

# Extract documentation
# output/vue-markdown/SKILL.md
```

### Setup in Continue.dev

**Option 1: Custom Context Provider** (recommended)

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

**Option 2: MCP Server** (for dynamic access)

```bash
# Start Skill Seekers MCP server
skill-seekers mcp-server --port 8765

# Or as systemd service (Linux)
sudo systemctl enable skill-seekers-mcp
sudo systemctl start skill-seekers-mcp
```

Add to `~/.continue/config.json`:

```json
{
  "mcpServers": {
    "skill-seekers": {
      "command": "python",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp", "--transport", "stdio"]
    }
  }
}
```

**Option 3: Built-in @docs Provider**

```json
{
  "contextProviders": [
    {
      "name": "docs",
      "params": {
        "sites": [
          {
            "title": "Vue.js",
            "startUrl": "https://vuejs.org/guide/",
            "rootUrl": "https://vuejs.org/"
          }
        ]
      }
    }
  ]
}
```

### Test in Continue

1. Open any project in your IDE
2. Open Continue panel (Cmd+L or Ctrl+L)
3. Type @ and select your context provider:
   ```
   @vue-docs Create a Vue 3 component with Composition API
   ```
4. Verify Continue references your documentation

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
  "description": "Custom framework documentation for Continue.dev",
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

### Step 2: Optimize for Continue.dev

**HTTP Context Provider**

Continue supports HTTP-based context providers for maximum flexibility:

```python
# custom_context_server.py
from fastapi import FastAPI
from skill_seekers.cli.doc_scraper import load_skill

app = FastAPI()

# Load documentation
vue_docs = load_skill("output/vue-markdown/SKILL.md")

@app.get("/docs/{framework}")
async def get_framework_docs(framework: str, query: str = None):
    """
    Return framework documentation as context.

    Args:
        framework: Framework name (vue, react, django, etc.)
        query: Optional search query for filtering

    Returns:
        Context items for Continue.dev
    """
    if query:
        # Filter by query
        filtered = search_docs(vue_docs, query)
        content = "\n\n".join(filtered)
    else:
        # Return full docs
        content = vue_docs

    return {
        "contextItems": [
            {
                "name": f"{framework.title()} Documentation",
                "description": f"Complete {framework} framework knowledge",
                "content": content
            }
        ]
    }

# Run with: uvicorn custom_context_server:app --port 8765
```

**MCP Context Provider**

For advanced users, expose via MCP:

```json
{
  "contextProviders": [
    {
      "name": "mcp",
      "params": {
        "serverName": "skill-seekers",
        "contextItem": {
          "type": "docs",
          "name": "Framework Documentation"
        }
      }
    }
  ],
  "mcpServers": {
    "skill-seekers": {
      "command": "python",
      "args": ["-m", "skill_seekers.mcp.server_fastmcp", "--transport", "stdio"]
    }
  }
}
```

**Built-in @docs Provider**

Simplest approach for public documentation:

```json
{
  "contextProviders": [
    {
      "name": "docs",
      "params": {
        "sites": [
          {
            "title": "Vue.js",
            "startUrl": "https://vuejs.org/guide/",
            "rootUrl": "https://vuejs.org/"
          },
          {
            "title": "Pinia",
            "startUrl": "https://pinia.vuejs.org/",
            "rootUrl": "https://pinia.vuejs.org/"
          }
        ]
      }
    }
  ]
}
```

### Step 3: Configure for Multiple IDEs

**VS Code Configuration**

Location: `~/.continue/config.json` (global) or `.vscode/continue.json` (project)

```json
{
  "models": [
    {
      "title": "Claude Sonnet 4.5",
      "provider": "anthropic",
      "model": "claude-sonnet-4-5-20250929",
      "apiKey": "${ANTHROPIC_API_KEY}"
    }
  ],
  "contextProviders": [
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/vue",
        "title": "vue-docs",
        "displayTitle": "Vue.js Docs",
        "description": "Vue.js framework knowledge"
      }
    }
  ]
}
```

**JetBrains Configuration**

Location: `~/.continue/config.json` (same file!)

Continue.dev uses the SAME config file across all IDEs:

```bash
# Edit once, works everywhere
vim ~/.continue/config.json

# Test in VS Code
code my-vue-project/

# Test in IntelliJ IDEA
idea my-vue-project/

# Same context providers in both!
```

**Per-Project Configuration**

```bash
# Create project-specific config
mkdir -p /path/to/project/.continue
cp ~/.continue/config.json /path/to/project/.continue/config.json

# Edit for project needs
vim /path/to/project/.continue/config.json

# Add project-specific context:
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
        "title": "project-conventions",
        "displayTitle": "Project Conventions",
        "description": "Company-specific patterns"
      }
    }
  ]
}
```

### Step 4: Test and Refine

**Test Context Access**

In Continue panel:

```
@vue-docs Show me how to create a Vue 3 component with Composition API and TypeScript

Expected: Continue references your documentation, shows correct patterns
```

**Verify Multi-IDE Consistency**

```bash
# Open same project in VS Code
code my-project/
# Type: @vue-docs Create a component
# Note the response

# Open same project in IntelliJ
idea my-project/
# Type: @vue-docs Create a component
# Response should be IDENTICAL
```

**Monitor Context Usage**

Check Continue logs:

```bash
# VS Code
Cmd+Shift+P → "Continue: Show Logs"

# JetBrains
Tools → Continue → Show Logs

# Look for:
# "Loaded context from http://localhost:8765/docs/vue"
# "Context items: 1, tokens: 5420"
```

---

## 🎨 Advanced Usage

### Multi-Framework Projects

**Full-Stack Vue + FastAPI**

```bash
# Generate frontend context
skill-seekers scrape --config configs/vue.json
# Generate backend context
skill-seekers scrape --config configs/fastapi.json

# Start context server with both
python custom_multi_context_server.py
```

**custom_multi_context_server.py:**

```python
from fastapi import FastAPI
from skill_seekers.cli.doc_scraper import load_skill

app = FastAPI()

# Load multiple frameworks
vue_docs = load_skill("output/vue-markdown/SKILL.md")
fastapi_docs = load_skill("output/fastapi-markdown/SKILL.md")

@app.get("/docs/{framework}")
async def get_docs(framework: str):
    docs = {
        "vue": vue_docs,
        "fastapi": fastapi_docs
    }

    if framework not in docs:
        return {"error": "Framework not found"}

    return {
        "contextItems": [
            {
                "name": f"{framework.title()} Documentation",
                "description": f"Expert knowledge for {framework}",
                "content": docs[framework]
            }
        ]
    }
```

**Continue config:**

```json
{
  "contextProviders": [
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/vue",
        "title": "vue-docs",
        "displayTitle": "Vue.js Frontend"
      }
    },
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/fastapi",
        "title": "fastapi-docs",
        "displayTitle": "FastAPI Backend"
      }
    }
  ]
}
```

Now use both:

```
@vue-docs @fastapi-docs Create a full-stack feature:
- Vue component for user registration
- FastAPI endpoint with validation
- Database model with SQLAlchemy
```

### Dynamic Context with RAG

**Combine with Vector Search**

```python
# rag_context_server.py
from fastapi import FastAPI
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from skill_seekers.cli.package_skill import main as package

app = FastAPI()

# Load RAG pipeline
embeddings = OpenAIEmbeddings()
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

@app.get("/docs/search")
async def search_docs(query: str, k: int = 5):
    """
    Search documentation using RAG.

    Args:
        query: Search query
        k: Number of results

    Returns:
        Top-k relevant snippets as context
    """
    results = vectorstore.similarity_search(query, k=k)

    return {
        "contextItems": [
            {
                "name": f"Result {i+1}",
                "description": doc.metadata.get("source", "Documentation"),
                "content": doc.page_content
            }
            for i, doc in enumerate(results)
        ]
    }
```

**Continue config:**

```json
{
  "contextProviders": [
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/search?query={query}",
        "title": "rag-search",
        "displayTitle": "RAG Search",
        "description": "Search all documentation"
      }
    }
  ]
}
```

### TypeScript Custom Context Provider

**For Advanced Customization**

Create `~/.continue/context/custom-rag.ts`:

```typescript
import { ContextProvider, ContextItem } from "@continuedev/core";

class CustomRAGProvider implements ContextProvider {
  title = "rag";
  displayTitle = "RAG Search";
  description = "Search internal documentation";

  async getContextItems(
    query: string,
    extras: any
  ): Promise<ContextItem[]> {
    // Query your RAG pipeline
    const response = await fetch(
      `http://localhost:8765/docs/search?query=${encodeURIComponent(query)}`
    );

    const data = await response.json();

    return data.contextItems.map((item: any) => ({
      name: item.name,
      description: item.description,
      content: item.content,
    }));
  }
}

export default CustomRAGProvider;
```

Register in `config.json`:

```json
{
  "contextProviders": [
    {
      "name": "custom",
      "params": {
        "modulePath": "~/.continue/context/custom-rag.ts"
      }
    }
  ]
}
```

### Continue + Skill Seekers MCP Integration

**Full MCP Setup**

```bash
# Install Skill Seekers with MCP
pip install skill-seekers[mcp]

# Start MCP server
python -m skill_seekers.mcp.server_fastmcp --transport stdio
```

**Continue config with MCP:**

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
      "env": {
        "ANTHROPIC_API_KEY": "${env:ANTHROPIC_API_KEY}"
      }
    }
  },
  "contextProviders": [
    {
      "name": "mcp",
      "params": {
        "serverName": "skill-seekers",
        "contextItem": {
          "type": "docs",
          "name": "Framework Documentation"
        }
      }
    }
  ]
}
```

Now Continue can:
- Query documentation via MCP
- Scrape docs on-demand
- Package skills dynamically

---

## 💡 Best Practices

### 1. Use IDE-Agnostic Configuration

**Bad: Duplicate Configs**

```bash
# Different configs for each IDE
~/.continue/vscode-config.json
~/.continue/jetbrains-config.json
~/.continue/vim-config.json
```

**Good: Single Source of Truth**

```bash
# One config for all IDEs
~/.continue/config.json

# Continue automatically loads from here in:
# - VS Code
# - JetBrains (IntelliJ, PyCharm, WebStorm)
# - Vim/Neovim (with Continue plugin)
```

### 2. Organize Context Providers

```json
{
  "contextProviders": [
    // Core frameworks (always needed)
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/vue",
        "title": "vue-core",
        "displayTitle": "Vue.js Core"
      }
    },
    // Ecosystem libraries (optional)
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/pinia",
        "title": "pinia",
        "displayTitle": "Pinia State Management"
      }
    },
    // Project-specific (highest priority)
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/project/conventions",
        "title": "conventions",
        "displayTitle": "Project Conventions"
      }
    }
  ]
}
```

### 3. Cache Documentation Locally

```python
# cached_context_server.py
from fastapi import FastAPI
from functools import lru_cache
import hashlib

app = FastAPI()

@lru_cache(maxsize=100)
def get_cached_docs(framework: str) -> str:
    """Cache documentation in memory."""
    return load_skill(f"output/{framework}-markdown/SKILL.md")

@app.get("/docs/{framework}")
async def get_docs(framework: str):
    # Returns cached version (fast!)
    content = get_cached_docs(framework)

    return {
        "contextItems": [{
            "name": f"{framework.title()} Docs",
            "content": content
        }]
    }
```

### 4. Use Environment Variables

```json
{
  "models": [
    {
      "title": "Claude Sonnet",
      "provider": "anthropic",
      "model": "claude-sonnet-4-5-20250929",
      "apiKey": "${ANTHROPIC_API_KEY}"  // From environment
    }
  ],
  "contextProviders": [
    {
      "name": "http",
      "params": {
        "url": "${CONTEXT_SERVER_URL}/docs/vue",  // Configurable
        "title": "vue-docs"
      }
    }
  ]
}
```

### 5. Update Documentation Regularly

```bash
# Quarterly update script
#!/bin/bash

# Update Vue docs
skill-seekers scrape --config configs/vue.json
skill-seekers package output/vue --target markdown

# Update FastAPI docs
skill-seekers scrape --config configs/fastapi.json
skill-seekers package output/fastapi --target markdown

# Restart context server
systemctl restart skill-seekers-context-server

echo "✅ Documentation updated!"
```

---

## 🔥 Real-World Examples

### Example 1: Vue.js Full-Stack Development

**Project Structure:**

```
my-vue-app/
├── .continue/
│   └── config.json           # Project-specific Continue config
├── frontend/                 # Vue 3 app
└── backend/                  # FastAPI server
```

**.continue/config.json:**

```json
{
  "models": [
    {
      "title": "Claude Sonnet",
      "provider": "anthropic",
      "model": "claude-sonnet-4-5-20250929",
      "apiKey": "${ANTHROPIC_API_KEY}"
    }
  ],
  "contextProviders": [
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/vue",
        "title": "vue-docs",
        "displayTitle": "Vue.js 3",
        "description": "Vue 3 Composition API patterns"
      }
    },
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/pinia",
        "title": "pinia-docs",
        "displayTitle": "Pinia",
        "description": "State management patterns"
      }
    },
    {
      "name": "http",
      "params": {
        "url": "http://localhost:8765/docs/fastapi",
        "title": "fastapi-docs",
        "displayTitle": "FastAPI",
        "description": "Backend API patterns"
      }
    }
  ]
}
```

**Using in Continue (Any IDE):**

```
In Continue panel:

@vue-docs @pinia-docs Create a Vue component:
- User profile display
- Load data from Pinia store
- Composition API with TypeScript
- Responsive design

Continue will:
1. ✅ Use Composition API (from vue-docs)
2. ✅ Access Pinia store correctly (from pinia-docs)
3. ✅ Add TypeScript types (from vue-docs)
4. ✅ Follow Vue 3 best practices

Then:

@fastapi-docs Create backend endpoint:
- GET /api/v1/users/:id
- Async database query
- Pydantic response model

Continue will:
1. ✅ Use async/await (from fastapi-docs)
2. ✅ Dependency injection (from fastapi-docs)
3. ✅ Pydantic models (from fastapi-docs)
```

### Example 2: Multi-IDE Consistency

**Scenario:** Team uses different IDEs

**Team Members:**
- Alice: VS Code
- Bob: IntelliJ IDEA
- Charlie: PyCharm

**Setup (Once):**

```bash
# 1. Generate documentation
skill-seekers scrape --config configs/django.json
skill-seekers package output/django --target markdown

# 2. Start context server (team server)
python context_server.py --host 0.0.0.0 --port 8765

# 3. Share config (Git repository)
cat > .continue/config.json << 'EOF'
{
  "contextProviders": [
    {
      "name": "http",
      "params": {
        "url": "http://team-server:8765/docs/django",
        "title": "django-docs",
        "displayTitle": "Django",
        "description": "Team Django patterns"
      }
    }
  ]
}
EOF

git add .continue/config.json
git commit -m "Add Continue.dev configuration"
git push
```

**Result:**

- ✅ Alice (VS Code) gets Django patterns
- ✅ Bob (IntelliJ) gets SAME Django patterns
- ✅ Charlie (PyCharm) gets SAME Django patterns
- ✅ One config file, three IDEs, consistent AI suggestions

---

## 🐛 Troubleshooting

### Issue: Context Provider Not Loading

**Symptoms:**
- @mention doesn't show your provider
- Continue ignores documentation

**Solutions:**

1. **Check config location**
   ```bash
   # Global config
   cat ~/.continue/config.json

   # Project config (takes precedence)
   cat .continue/config.json

   # Verify contextProviders array exists
   ```

2. **Verify HTTP server is running**
   ```bash
   curl http://localhost:8765/docs/vue

   # Should return JSON with contextItems
   ```

3. **Check Continue logs**
   ```
   VS Code: Cmd+Shift+P → "Continue: Show Logs"
   JetBrains: Tools → Continue → Show Logs

   Look for errors like:
   "Failed to load context from http://localhost:8765/docs/vue"
   ```

4. **Reload Continue**
   ```
   VS Code: Cmd+Shift+P → "Developer: Reload Window"
   JetBrains: File → Invalidate Caches → Restart
   ```

### Issue: MCP Server Not Connecting

**Error:**
> "Failed to start MCP server: skill-seekers"

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
   # Ctrl+C to exit
   ```

3. **Check Python path**
   ```json
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
   ```bash
   echo $ANTHROPIC_API_KEY
   # Should be set for AI enhancement features
   ```

### Issue: Different Results in Different IDEs

**Symptoms:**
- VS Code suggestions differ from JetBrains
- Context inconsistent across IDEs

**Solutions:**

1. **Use same config file**
   ```bash
   # Ensure both IDEs use ~/.continue/config.json
   # NOT project-specific configs

   # Check VS Code
   ls ~/.continue/config.json

   # Check JetBrains (uses same file!)
   ls ~/.continue/config.json
   ```

2. **Verify context server URL**
   ```bash
   # Must be accessible from all IDEs
   # Use localhost or team server IP

   # Test from both IDEs:
   curl http://localhost:8765/docs/vue
   ```

3. **Clear Continue cache**
   ```bash
   # Remove cached context
   rm -rf ~/.continue/cache/

   # Restart IDEs
   ```

---

## 📊 Before vs After Comparison

| Aspect | Before Skill Seekers | After Skill Seekers |
|--------|---------------------|---------------------|
| **Context Source** | Manual @-mentions | Automatic context providers |
| **IDE Consistency** | Different across IDEs | Same config, all IDEs |
| **Setup Time** | Manual per IDE (hours) | One config (5 min) |
| **AI Knowledge** | Generic patterns | Framework-specific best practices |
| **Updates** | Manual editing | Re-scrape + restart |
| **Multi-Framework** | Context juggling | Multiple providers |
| **Team Sharing** | Manual duplication | Git-tracked config |
| **Documentation** | Built-in @docs only | Custom HTTP providers + MCP |

---

## 🤝 Community & Support

- **Questions:** [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)
- **Issues:** [GitHub Issues](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
- **Website:** [skillseekersweb.com](https://skillseekersweb.com/)
- **Continue.dev Docs:** [docs.continue.dev](https://docs.continue.dev/)
- **Continue.dev GitHub:** [github.com/continuedev/continue](https://github.com/continuedev/continue)

---

## 📚 Related Guides

- [Cursor Integration](CURSOR.md) - IDE-specific approach
- [Windsurf Integration](WINDSURF.md) - Alternative IDE
- [Cline Integration](CLINE.md) - VS Code extension with MCP
- [LangChain Integration](LANGCHAIN.md) - Build RAG pipelines
- [Context Providers Reference](https://docs.continue.dev/customization/context-providers)

---

## 📖 Next Steps

1. **Try another framework:** `skill-seekers scrape --config configs/react.json`
2. **Set up team server:** Share context across team
3. **Build RAG pipeline:** Deep search with `--target langchain`
4. **Create custom TypeScript provider:** Advanced customization
5. **Multi-IDE setup:** Test consistency across VS Code + JetBrains

---

**Sources:**
- [Continue.dev Documentation](https://docs.continue.dev/)
- [config.json Reference](https://docs.continue.dev/reference/config)
- [Context Providers Guide](https://docs.continue.dev/customization/context-providers)
- [MCP with Continue.dev](https://medium.com/@ashfaqbs/model-context-protocol-mcp-with-continue-dev-95f04752299a)
- [Continue.dev Configuration Guide](https://www.askcodi.com/documentation/integrations/continue/complete-guide-to-continue-dev)
- [MCP Server Implementation Guide](https://skywork.ai/skypage/en/Model-Context-Protocol-(MCP)-Server-A-Comprehensive-Guide-to-Continue-MCP-Server-for-AI-Engineers/1972129737880076288)
