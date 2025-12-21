# Skill Seekers Config API

FastAPI backend for discovering and downloading Skill Seekers configuration files.

## 🚀 Endpoints

### Base URL
- **Production**: `https://skillseekersweb.com`
- **Local**: `http://localhost:8000`

### Available Endpoints

#### 1. **GET /** - API Information
Returns API metadata and available endpoints.

```bash
curl https://skillseekersweb.com/
```

**Response:**
```json
{
  "name": "Skill Seekers Config API",
  "version": "1.0.0",
  "endpoints": {
    "/api/configs": "List all available configs",
    "/api/configs/{name}": "Get specific config details",
    "/api/categories": "List all categories",
    "/docs": "API documentation"
  },
  "repository": "https://github.com/yusufkaraaslan/Skill_Seekers",
  "website": "https://skillseekersweb.com"
}
```

---

#### 2. **GET /api/configs** - List All Configs
Returns list of all available configs with metadata.

**Query Parameters:**
- `category` (optional) - Filter by category (e.g., `web-frameworks`)
- `tag` (optional) - Filter by tag (e.g., `javascript`)
- `type` (optional) - Filter by type (`single-source` or `unified`)

```bash
# Get all configs
curl https://skillseekersweb.com/api/configs

# Filter by category
curl https://skillseekersweb.com/api/configs?category=web-frameworks

# Filter by tag
curl https://skillseekersweb.com/api/configs?tag=javascript

# Filter by type
curl https://skillseekersweb.com/api/configs?type=unified
```

**Response:**
```json
{
  "version": "1.0.0",
  "total": 24,
  "filters": null,
  "configs": [
    {
      "name": "react",
      "description": "React framework for building user interfaces...",
      "type": "single-source",
      "category": "web-frameworks",
      "tags": ["javascript", "frontend", "documentation"],
      "primary_source": "https://react.dev/",
      "max_pages": 300,
      "file_size": 1055,
      "last_updated": "2025-11-30T09:26:07+00:00",
      "download_url": "https://skillseekersweb.com/api/download/react.json",
      "config_file": "react.json"
    }
  ]
}
```

---

#### 3. **GET /api/configs/{name}** - Get Specific Config
Returns detailed information about a specific config.

```bash
curl https://skillseekersweb.com/api/configs/react
```

**Response:**
```json
{
  "name": "react",
  "description": "React framework for building user interfaces...",
  "type": "single-source",
  "category": "web-frameworks",
  "tags": ["javascript", "frontend", "documentation"],
  "primary_source": "https://react.dev/",
  "max_pages": 300,
  "file_size": 1055,
  "last_updated": "2025-11-30T09:26:07+00:00",
  "download_url": "https://skillseekersweb.com/api/download/react.json",
  "config_file": "react.json"
}
```

---

#### 4. **GET /api/categories** - List Categories
Returns all available categories with config counts.

```bash
curl https://skillseekersweb.com/api/categories
```

**Response:**
```json
{
  "total_categories": 5,
  "categories": {
    "web-frameworks": 7,
    "game-engines": 2,
    "devops": 2,
    "css-frameworks": 1,
    "uncategorized": 12
  }
}
```

---

#### 5. **GET /api/download/{config_name}** - Download Config File
Downloads the actual config JSON file.

```bash
# Download react config
curl -O https://skillseekersweb.com/api/download/react.json

# Download with just name (auto-adds .json)
curl -O https://skillseekersweb.com/api/download/react
```

---

#### 6. **GET /health** - Health Check
Health check endpoint for monitoring.

```bash
curl https://skillseekersweb.com/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "skill-seekers-api"
}
```

---

#### 7. **GET /docs** - API Documentation
Interactive OpenAPI documentation (Swagger UI).

Visit: `https://skillseekersweb.com/docs`

---

## 📦 Metadata Fields

Each config includes the following metadata:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Config identifier (e.g., "react") |
| `description` | string | What the config is used for |
| `type` | string | "single-source" or "unified" |
| `category` | string | Auto-categorized (e.g., "web-frameworks") |
| `tags` | array | Relevant tags (e.g., ["javascript", "frontend"]) |
| `primary_source` | string | Main documentation URL or repo |
| `max_pages` | int | Estimated page count for scraping |
| `file_size` | int | Config file size in bytes |
| `last_updated` | string | ISO 8601 date of last update |
| `download_url` | string | Direct download link |
| `config_file` | string | Filename (e.g., "react.json") |

---

## 🏗️ Categories

Configs are auto-categorized into:

- **web-frameworks** - Web development frameworks (React, Django, FastAPI, etc.)
- **game-engines** - Game development engines (Godot, Unity, etc.)
- **devops** - DevOps tools (Kubernetes, Ansible, etc.)
- **css-frameworks** - CSS frameworks (Tailwind, etc.)
- **development-tools** - Dev tools (Claude Code, etc.)
- **gaming** - Gaming platforms (Steam, etc.)
- **uncategorized** - Other configs

---

## 🏷️ Tags

Common tags include:

- **Language**: `javascript`, `python`, `php`
- **Domain**: `frontend`, `backend`, `devops`, `game-development`
- **Type**: `documentation`, `github`, `pdf`, `multi-source`
- **Tech**: `css`, `testing`, `api`

---

## 🚀 Local Development

### Setup

```bash
# Install dependencies
cd api
pip install -r requirements.txt

# Run server
python main.py
```

API will be available at `http://localhost:8000`

### Testing

```bash
# Test health check
curl http://localhost:8000/health

# List all configs
curl http://localhost:8000/api/configs

# Get specific config
curl http://localhost:8000/api/configs/react

# Download config
curl -O http://localhost:8000/api/download/react.json
```

---

## 📝 Deployment

### Render

This API is configured for Render deployment via `render.yaml`.

1. Push to GitHub
2. Connect repository to Render
3. Render auto-deploys from `render.yaml`
4. Configure custom domain: `skillseekersweb.com`

---

## 🔗 Links

- **API Documentation**: https://skillseekersweb.com/docs
- **GitHub Repository**: https://github.com/yusufkaraaslan/Skill_Seekers
- **Main Project**: https://github.com/yusufkaraaslan/Skill_Seekers#readme
